"""Create a deterministic Lambda package; optionally perform a guarded create-only deployment."""

from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
import time
import zipfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


ROOT = Path(__file__).resolve().parents[1]
FILES = ("app.py", "catalog.json", "lambda_function.py", "planner.py")
FUNCTION_NAME = "simplifynext-mvp"
ROLE_NAME = "simplifynext-mvp-execution"
POLICY_NAME = "simplifynext-mvp-bedrock-logs"
ALLOWED_REGIONS = ("us-east-1", "us-east-2", "us-west-2")
TAGS = {"Project": "simplifynext-mvp", "ManagedBy": "scripts/deploy.py"}
_MODEL_ID = re.compile(r"^us\.[a-z0-9][a-z0-9._:-]{1,196}$")


def build_package(output=ROOT / "dist" / "simplifynext-mvp.zip"):
    """Write a reproducible, dependency-free Lambda zip from the explicit allowlist."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in FILES:
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            archive.writestr(info, (ROOT / name).read_bytes(), compresslevel=9)
    return output


def _validate_scope(expected_account, region, model_id, account_concurrency_ceiling=None):
    if not isinstance(expected_account, str) or not re.fullmatch(r"\d{12}", expected_account):
        raise ValueError("--expected-account must be exactly 12 digits.")
    if region not in ALLOWED_REGIONS:
        raise ValueError("--region must be us-east-1, us-east-2, or us-west-2.")
    if not isinstance(model_id, str) or not _MODEL_ID.fullmatch(model_id):
        raise ValueError("--model-id must be one explicit us.* geographic system inference profile ID.")
    if account_concurrency_ceiling is not None and (
        type(account_concurrency_ceiling) is not int or not 1 <= account_concurrency_ceiling <= 10
    ):
        raise ValueError("--account-concurrency-ceiling must be an integer from 1 through 10.")


def _validate_apply(expected_account, region, model_id, budget_verified, account_concurrency_ceiling=None):
    _validate_scope(expected_account, region, model_id, account_concurrency_ceiling)
    if budget_verified is not True:
        raise ValueError("--budget-verified is required after a manual live balance check.")


def execution_policy(account, region, profile_arn, model_arns):
    """Return least-privilege logging and exact-model Bedrock permissions."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "WriteOwnLogs",
                "Effect": "Allow",
                "Action": ["logs:CreateLogGroup"],
                "Resource": [f"arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{FUNCTION_NAME}"],
            },
            {
                "Sid": "WriteOwnLogStreams",
                "Effect": "Allow",
                "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": [f"arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{FUNCTION_NAME}:*"],
            },
            {
                "Sid": "InvokeApprovedProfile",
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": [profile_arn],
            },
            {
                "Sid": "InvokeProfileDestinations",
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": list(model_arns),
                "Condition": {"StringEquals": {"bedrock:InferenceProfileArn": profile_arn}},
            },
        ],
    }


def _temporary_credentials(session):
    try:
        credentials = session.get_credentials()
        frozen = credentials.get_frozen_credentials() if credentials else None
    except Exception:
        raise RuntimeError("Temporary AWS credentials are unavailable or expired.") from None
    if not frozen or not frozen.access_key or not frozen.secret_key or not frozen.token:
        raise RuntimeError("Temporary AWS credentials are required; permanent keys are not accepted.")


def _missing(error, code):
    return isinstance(error, ClientError) and error.response.get("Error", {}).get("Code") == code


def _ownership(tags):
    if isinstance(tags, dict):
        values = tags
    else:
        values = {tag.get("Key"): tag.get("Value") for tag in tags or [] if isinstance(tag, dict)}
    return all(values.get(key) == value for key, value in TAGS.items())


def _reject_existing(iam, lambda_client):
    existing = []
    try:
        iam.get_role(RoleName=ROLE_NAME)
        tags = iam.list_role_tags(RoleName=ROLE_NAME).get("Tags", [])
        existing.append(("role", _ownership(tags)))
    except ClientError as error:
        if not _missing(error, "NoSuchEntity"):
            raise RuntimeError("Could not verify whether the deployment role already exists.") from None

    try:
        function = lambda_client.get_function(FunctionName=FUNCTION_NAME)
        existing.append(("function", _ownership(function.get("Tags", {}))))
    except ClientError as error:
        if not _missing(error, "ResourceNotFoundException"):
            raise RuntimeError("Could not verify whether the Lambda function already exists.") from None

    if existing:
        kind, owned = existing[0]
        owner = "owned" if owned else "unrelated"
        raise RuntimeError(f"{owner} existing {kind} exists; create-only deployment halted without overwrite.")


def preflight_deployment(
    expected_account, region, model_id, *, account_concurrency_ceiling=None, session=None
):
    """Run all credential, account, name, quota, and model checks without writes."""
    _validate_scope(expected_account, region, model_id, account_concurrency_ceiling)
    session = session or boto3.Session(region_name=region)
    _temporary_credentials(session)
    try:
        account = session.client("sts").get_caller_identity().get("Account")
    except Exception:
        raise RuntimeError("Could not verify the current AWS account.") from None
    if account != expected_account:
        raise RuntimeError("Current AWS account does not match --expected-account; no resources were changed.")

    iam = session.client("iam")
    lambda_client = session.client("lambda")
    _reject_existing(iam, lambda_client)

    try:
        limits = lambda_client.get_account_settings()["AccountLimit"]
        concurrent = limits["ConcurrentExecutions"]
        unreserved = limits["UnreservedConcurrentExecutions"]
    except Exception:
        raise RuntimeError("Lambda account concurrency could not be verified; no resources were changed.") from None
    if type(concurrent) is not int or concurrent <= 0 or type(unreserved) is not int or unreserved < 0:
        raise RuntimeError("Lambda account concurrency is invalid; no resources were changed.")
    if account_concurrency_ceiling is None and unreserved < 101:
        raise RuntimeError("Lambda unreserved concurrency must be at least 101 to reserve 1; no resources were changed.")
    if account_concurrency_ceiling is not None and concurrent > account_concurrency_ceiling:
        raise RuntimeError("Lambda account concurrency exceeds the acknowledged ceiling; no resources were changed.")

    expected_profile_arn = f"arn:aws:bedrock:{region}:{account}:inference-profile/{model_id}"
    try:
        profile = session.client("bedrock").get_inference_profile(
            inferenceProfileIdentifier=model_id
        )
    except Exception:
        raise RuntimeError("Bedrock inference profile could not be verified; no resources were changed.") from None

    base_model = model_id[3:]
    model_by_region = {}
    models = profile.get("models") if isinstance(profile, dict) else None
    if not isinstance(models, list) or not models:
        raise RuntimeError("Bedrock inference profile destinations are invalid; no resources were changed.")
    for item in models:
        model_arn = item.get("modelArn") if isinstance(item, dict) else None
        match = re.fullmatch(
            rf"arn:aws:bedrock:({'|'.join(ALLOWED_REGIONS)})::foundation-model/{re.escape(base_model)}",
            model_arn or "",
        )
        if not match or match.group(1) in model_by_region:
            raise RuntimeError("Bedrock inference profile destinations are invalid; no resources were changed.")
        model_by_region[match.group(1)] = model_arn
    if (
        not isinstance(profile, dict)
        or profile.get("inferenceProfileId") != model_id
        or profile.get("inferenceProfileArn") != expected_profile_arn
        or profile.get("status") != "ACTIVE"
        or profile.get("type") != "SYSTEM_DEFINED"
        or region not in model_by_region
        or not model_by_region
    ):
        raise RuntimeError("Bedrock inference profile is not an active exact US system profile; no resources were changed.")

    destination_regions = [item for item in ALLOWED_REGIONS if item in model_by_region]
    result = {
        "status": "ok",
        "account_match": True,
        "region": region,
        "role_name_available": True,
        "function_name_available": True,
        "unreserved_concurrency": unreserved,
        "model_profile_id": model_id,
        "model_profile_status": "ACTIVE",
        "destination_regions": destination_regions,
        "profile_arn": expected_profile_arn,
        "model_arns": [model_by_region[item] for item in destination_regions],
    }
    if account_concurrency_ceiling is None:
        result["concurrency_control"] = "reserved"
        result["reserved_concurrency_requested"] = 1
    else:
        result["concurrency_control"] = "account_limit"
        result["account_concurrency_limit"] = concurrent
        result["account_concurrency_ceiling"] = account_concurrency_ceiling
    return result


def _safe_preflight(checks):
    return {key: value for key, value in checks.items() if key not in {"profile_arn", "model_arns"}}


def apply_deployment(
    expected_account,
    region,
    model_id,
    budget_verified,
    *,
    session=None,
    package=None,
    sleep=time.sleep,
    account_concurrency_ceiling=None,
):
    """Create guarded AWS resources once; never update or overwrite existing names."""
    _validate_apply(
        expected_account, region, model_id, budget_verified, account_concurrency_ceiling
    )
    if not isinstance(package, bytes) or not package:
        raise ValueError("A non-empty Lambda package is required.")
    session = session or boto3.Session(region_name=region)
    checks = preflight_deployment(
        expected_account,
        region,
        model_id,
        account_concurrency_ceiling=account_concurrency_ceiling,
        session=session,
    )
    account = expected_account
    iam = session.client("iam")
    lambda_client = session.client("lambda")

    trust = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}],
    }
    try:
        role = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust, sort_keys=True, separators=(",", ":")),
            Description="SimplifyNext MVP Lambda execution role",
            Tags=[{"Key": key, "Value": value} for key, value in TAGS.items()],
        )
        iam.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName=POLICY_NAME,
            PolicyDocument=json.dumps(
                execution_policy(account, region, checks["profile_arn"], checks["model_arns"]),
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
    except ClientError:
        raise RuntimeError("AWS rejected creation of the bounded execution role; inspect permissions before retrying.") from None

    create = {
        "FunctionName": FUNCTION_NAME,
        "Runtime": "python3.12",
        "Role": role["Role"]["Arn"],
        "Handler": "lambda_function.handler",
        "Code": {"ZipFile": package},
        "Description": "Synthetic-only SimplifyNext transition planner MVP",
        "Timeout": 90,
        "MemorySize": 256,
        "Publish": False,
        "Environment": {
            "Variables": {
                "PLANNER_MODE": "bedrock",
                "BEDROCK_MODEL_ID": model_id,
                "PLAN_SIGNING_KEY": secrets.token_urlsafe(48),
            }
        },
        "Tags": dict(TAGS),
    }
    for attempt in range(6):
        try:
            lambda_client.create_function(**create)
            break
        except ClientError as error:
            delayed = _missing(error, "InvalidParameterValueException")
            if not delayed or attempt == 5:
                raise RuntimeError("AWS rejected Lambda creation; use rollback instructions before retrying.") from None
            sleep(min(2**attempt, 10))

    for attempt in range(10):
        try:
            state = lambda_client.get_function_configuration(FunctionName=FUNCTION_NAME).get("State")
        except ClientError:
            raise RuntimeError("Could not verify Lambda activation; use rollback instructions.") from None
        if state == "Active":
            break
        if state == "Failed" or attempt == 9:
            raise RuntimeError("Lambda did not become active within the bounded wait; use rollback instructions.")
        sleep(min(2**attempt, 5))

    try:
        if account_concurrency_ceiling is None:
            lambda_client.put_function_concurrency(
                FunctionName=FUNCTION_NAME, ReservedConcurrentExecutions=1
            )
        lambda_client.create_function_url_config(
            FunctionName=FUNCTION_NAME, AuthType="AWS_IAM", InvokeMode="BUFFERED"
        )
        checked = lambda_client.get_function_url_config(FunctionName=FUNCTION_NAME)
    except ClientError:
        raise RuntimeError("Private Function URL configuration failed; use rollback instructions.") from None
    if checked.get("AuthType") != "AWS_IAM" or not checked.get("FunctionUrl"):
        raise RuntimeError("Function URL did not verify as AWS_IAM; do not publish or use it.")
    return checked["FunctionUrl"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--package", action="store_true", help="build package only; default and zero network")
    mode.add_argument("--preflight", action="store_true", help="run read-only AWS checks without packaging")
    mode.add_argument("--apply", action="store_true", help="create guarded AWS resources")
    parser.add_argument("--output", default=str(ROOT / "dist" / "simplifynext-mvp.zip"))
    parser.add_argument("--expected-account")
    parser.add_argument("--region")
    parser.add_argument("--model-id")
    parser.add_argument("--budget-verified", action="store_true")
    parser.add_argument("--account-concurrency-ceiling", type=int)
    args = parser.parse_args(argv)

    if args.apply:
        try:
            _validate_apply(
                args.expected_account,
                args.region,
                args.model_id,
                args.budget_verified,
                args.account_concurrency_ceiling,
            )
        except ValueError as error:
            parser.error(str(error))
    elif args.preflight:
        try:
            _validate_scope(
                args.expected_account, args.region, args.model_id, args.account_concurrency_ceiling
            )
        except ValueError as error:
            parser.error(str(error))
    elif any((
        args.expected_account,
        args.region,
        args.model_id,
        args.budget_verified,
        args.account_concurrency_ceiling,
    )):
        parser.error("AWS arguments require --preflight or --apply.")

    if args.preflight:
        try:
            checks = preflight_deployment(
                args.expected_account,
                args.region,
                args.model_id,
                account_concurrency_ceiling=args.account_concurrency_ceiling,
                session=boto3.Session(region_name=args.region),
            )
        except (RuntimeError, ValueError) as error:
            parser.exit(2, f"error: {error}\n")
        print(json.dumps(_safe_preflight(checks), indent=2, sort_keys=True))
        return 0

    output = build_package(args.output)
    print(f"Package: {output}")
    if not args.apply:
        return 0
    try:
        package = output.read_bytes()
        url = apply_deployment(
            args.expected_account,
            args.region,
            args.model_id,
            args.budget_verified,
            account_concurrency_ceiling=args.account_concurrency_ceiling,
            session=boto3.Session(region_name=args.region),
            package=package,
        )
    except (RuntimeError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(f"AWS_IAM Function URL created: {url}")
    print("Deployment is not ready until caller permissions and signed smoke tests are verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
