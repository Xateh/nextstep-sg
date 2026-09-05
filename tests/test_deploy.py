import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from botocore.exceptions import ClientError
from botocore.credentials import Credentials


PROFILE_ID = "us.anthropic.claude-v1:0"
PROFILE_ARN = f"arn:aws:bedrock:us-east-1:123456789012:inference-profile/{PROFILE_ID}"
MODEL_ARNS = [
    f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-v1:0"
    for region in ("us-east-1", "us-east-2", "us-west-2")
]


def aws_error(code, operation):
    return ClientError({"Error": {"Code": code, "Message": "test"}}, operation)


class FakeSTS:
    def __init__(self, account="123456789012"):
        self.account = account

    def get_caller_identity(self):
        return {"Account": self.account, "Arn": "arn:aws:sts::123456789012:assumed-role/test/session"}


class FakeIAM:
    def __init__(self, existing=None):
        self.existing = existing
        self.created = None
        self.policy = None

    def get_role(self, **_):
        if self.existing is None:
            raise aws_error("NoSuchEntity", "GetRole")
        return {"Role": {"Arn": "arn:aws:iam::123456789012:role/simplifynext-mvp-execution"}}

    def list_role_tags(self, **_):
        return {"Tags": self.existing}

    def create_role(self, **kwargs):
        self.created = kwargs
        return {"Role": {"Arn": "arn:aws:iam::123456789012:role/simplifynext-mvp-execution"}}

    def put_role_policy(self, **kwargs):
        self.policy = kwargs


class FakeLambda:
    def __init__(self, existing=None, role_delay=False, auth_type="AWS_IAM", states=None, unreserved=101, concurrent=1000, quota_error=False):
        self.existing = existing
        self.role_delay = role_delay
        self.auth_type = auth_type
        self.created = None
        self.create_attempts = 0
        self.concurrency = None
        self.url_config = None
        self.public_permissions = []
        self.states = list(states or ["Active"])
        self.state_checks = 0
        self.unreserved = unreserved
        self.concurrent = concurrent
        self.quota_error = quota_error
        self.quota_checks = 0

    def get_function(self, **_):
        if self.existing is None:
            raise aws_error("ResourceNotFoundException", "GetFunction")
        return {"Tags": self.existing}

    def create_function(self, **kwargs):
        self.create_attempts += 1
        if self.role_delay and self.create_attempts == 1:
            raise aws_error("InvalidParameterValueException", "CreateFunction")
        self.created = kwargs
        return {"FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:simplifynext-mvp"}

    def get_account_settings(self):
        self.quota_checks += 1
        if self.quota_error:
            raise aws_error("AccessDeniedException", "GetAccountSettings")
        return {"AccountLimit": {
            "ConcurrentExecutions": self.concurrent,
            "UnreservedConcurrentExecutions": self.unreserved,
        }}

    def put_function_concurrency(self, **kwargs):
        self.concurrency = kwargs

    def get_function_configuration(self, **_):
        state = self.states[min(self.state_checks, len(self.states) - 1)]
        self.state_checks += 1
        return {"State": state}

    def create_function_url_config(self, **kwargs):
        self.url_config = kwargs

    def get_function_url_config(self, **_):
        return {"AuthType": self.auth_type, "FunctionUrl": "https://verified.lambda-url.us-east-1.on.aws/"}

    def add_permission(self, **kwargs):
        self.public_permissions.append(kwargs)


class FakeBedrock:
    def __init__(self, response=None, error=False):
        self.response = response or {
            "inferenceProfileId": PROFILE_ID,
            "inferenceProfileArn": PROFILE_ARN,
            "status": "ACTIVE",
            "type": "SYSTEM_DEFINED",
            "models": [{"modelArn": arn} for arn in MODEL_ARNS],
        }
        self.error = error
        self.calls = []

    def get_inference_profile(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise aws_error("AccessDeniedException", "GetInferenceProfile")
        return self.response


class FakeSession:
    def __init__(self, sts=None, iam=None, lambda_client=None, bedrock=None, token="temporary-token"):
        self.clients = {
            "sts": sts or FakeSTS(),
            "iam": iam or FakeIAM(),
            "lambda": lambda_client or FakeLambda(),
            "bedrock": bedrock or FakeBedrock(),
        }
        self.credentials = Credentials("ASIATEST", "secret", token)

    def get_credentials(self):
        return self.credentials

    def client(self, name):
        return self.clients[name]


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        try:
            from scripts import deploy
        except ImportError:
            deploy = None
        self.deploy = deploy
        self.assertIsNotNone(deploy, "Deployment helper has not been implemented")

    def test_package_is_deterministic_and_contains_only_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            self.deploy.build_package(first)
            self.deploy.build_package(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.namelist(), ["app.py", "catalog.json", "lambda_function.py", "planner.py"])
                self.assertTrue(all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in archive.infolist()))

    def test_default_package_mode_makes_no_aws_session(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            self.deploy.boto3, "Session", side_effect=AssertionError("AWS session created")
        ), redirect_stdout(io.StringIO()):
            status = self.deploy.main(["--output", str(Path(directory) / "bundle.zip")])
        self.assertEqual(status, 0)

    def test_apply_rejects_missing_gates_and_invalid_scope_before_session(self):
        invalid = [
            ["--apply"],
            ["--apply", "--expected-account", "123", "--region", "us-east-1", "--model-id", PROFILE_ID, "--budget-verified"],
            ["--apply", "--expected-account", "123456789012", "--region", "ap-southeast-1", "--model-id", PROFILE_ID, "--budget-verified"],
            ["--apply", "--expected-account", "123456789012", "--region", "us-east-1", "--model-id", "anthropic.claude-v1:0", "--budget-verified"],
            ["--apply", "--expected-account", "123456789012", "--region", "us-east-1", "--model-id", "global.anthropic.claude-v1:0", "--budget-verified"],
            ["--apply", "--expected-account", "123456789012", "--region", "us-east-1", "--model-id", PROFILE_ID, "--budget-verified", "--account-concurrency-ceiling", "11"],
        ]
        with patch.object(self.deploy.boto3, "Session", side_effect=AssertionError("AWS session created")), redirect_stderr(io.StringIO()):
            for argv in invalid:
                with self.subTest(argv=argv), self.assertRaises(SystemExit):
                    self.deploy.main(argv)

    def test_account_and_temporary_credentials_are_verified_before_writes(self):
        iam = FakeIAM()
        with self.assertRaisesRegex(RuntimeError, "account"):
            self.deploy.apply_deployment(
                "999999999999", "us-east-1", PROFILE_ID, True,
                session=FakeSession(sts=FakeSTS("123456789012"), iam=iam), package=b"zip",
            )
        self.assertIsNone(iam.created)

        with self.assertRaisesRegex(RuntimeError, "Temporary AWS credentials"):
            self.deploy.apply_deployment(
                "123456789012", "us-east-1", PROFILE_ID, True,
                session=FakeSession(iam=iam, token=None), package=b"zip",
            )
        self.assertIsNone(iam.created)

    def test_existing_resources_halt_without_writes(self):
        for tags in ([{"Key": "Project", "Value": "other"}], [{"Key": "Project", "Value": "simplifynext-mvp"}, {"Key": "ManagedBy", "Value": "scripts/deploy.py"}]):
            iam = FakeIAM(existing=tags)
            lambda_client = FakeLambda()
            with self.subTest(tags=tags), self.assertRaisesRegex(RuntimeError, "exists"):
                self.deploy.apply_deployment(
                    "123456789012", "us-east-1", PROFILE_ID, True,
                    session=FakeSession(iam=iam, lambda_client=lambda_client), package=b"zip",
                )
            self.assertIsNone(iam.created)
            self.assertIsNone(lambda_client.created)

        iam = FakeIAM()
        lambda_client = FakeLambda(existing={"Project": "other"})
        with self.assertRaisesRegex(RuntimeError, "unrelated existing function"):
            self.deploy.apply_deployment(
                "123456789012", "us-east-1", PROFILE_ID, True,
                session=FakeSession(iam=iam, lambda_client=lambda_client), package=b"zip",
            )
        self.assertIsNone(iam.created)

    def test_policy_limits_bedrock_to_selected_model_and_destinations(self):
        policy = self.deploy.execution_policy("123456789012", "us-east-1", PROFILE_ARN, MODEL_ARNS)
        profile = next(statement for statement in policy["Statement"] if statement["Sid"] == "InvokeApprovedProfile")
        destinations = next(statement for statement in policy["Statement"] if statement["Sid"] == "InvokeProfileDestinations")
        self.assertEqual(profile["Resource"], [PROFILE_ARN])
        self.assertEqual(destinations["Resource"], MODEL_ARNS)
        self.assertEqual(
            destinations["Condition"], {"StringEquals": {"bedrock:InferenceProfileArn": PROFILE_ARN}}
        )
        self.assertEqual(destinations["Action"], ["bedrock:InvokeModel"])
        create_logs = next(statement for statement in policy["Statement"] if statement["Sid"] == "WriteOwnLogs")
        self.assertEqual(
            create_logs["Resource"],
            ["arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/simplifynext-mvp"],
        )

    def test_create_only_apply_sets_bounded_private_configuration(self):
        iam = FakeIAM()
        lambda_client = FakeLambda(role_delay=True, states=["Pending", "Active"])
        sleeps = []
        url = self.deploy.apply_deployment(
            "123456789012", "us-east-1", PROFILE_ID, True,
            session=FakeSession(iam=iam, lambda_client=lambda_client), package=b"zip",
            sleep=sleeps.append,
        )

        self.assertEqual(url, "https://verified.lambda-url.us-east-1.on.aws/")
        self.assertEqual(lambda_client.create_attempts, 2)
        self.assertEqual(sleeps, [1, 1])
        self.assertEqual(lambda_client.state_checks, 2)
        self.assertEqual(lambda_client.created["Runtime"], "python3.12")
        self.assertEqual(lambda_client.created["Timeout"], 90)
        self.assertEqual(lambda_client.created["MemorySize"], 256)
        self.assertEqual(lambda_client.concurrency["ReservedConcurrentExecutions"], 1)
        self.assertEqual(lambda_client.url_config["AuthType"], "AWS_IAM")
        self.assertEqual(lambda_client.public_permissions, [])
        signing_key = lambda_client.created["Environment"]["Variables"]["PLAN_SIGNING_KEY"]
        self.assertGreaterEqual(len(signing_key), 48)
        policy_text = iam.policy["PolicyDocument"]
        self.assertNotIn(signing_key, policy_text)

    def test_quota_failure_halts_before_profile_or_writes(self):
        for lambda_client in (FakeLambda(unreserved=100), FakeLambda(unreserved=10, concurrent=10), FakeLambda(quota_error=True)):
            iam = FakeIAM()
            bedrock = FakeBedrock()
            with self.subTest(unreserved=lambda_client.unreserved), self.assertRaisesRegex(RuntimeError, "concurrency"):
                self.deploy.apply_deployment(
                    "123456789012", "us-east-1", PROFILE_ID, True,
                    session=FakeSession(iam=iam, lambda_client=lambda_client, bedrock=bedrock), package=b"zip",
                )
            self.assertIsNone(iam.created)
            self.assertEqual(bedrock.calls, [])

    def test_profile_must_be_active_exact_system_us_profile(self):
        invalid = [
            {"inferenceProfileId": PROFILE_ID, "inferenceProfileArn": PROFILE_ARN, "status": "INACTIVE", "type": "SYSTEM_DEFINED", "models": [{"modelArn": arn} for arn in MODEL_ARNS]},
            {"inferenceProfileId": PROFILE_ID, "inferenceProfileArn": PROFILE_ARN, "status": "ACTIVE", "type": "APPLICATION", "models": [{"modelArn": arn} for arn in MODEL_ARNS]},
            {"inferenceProfileId": PROFILE_ID, "inferenceProfileArn": PROFILE_ARN.replace("123456789012", "999999999999"), "status": "ACTIVE", "type": "SYSTEM_DEFINED", "models": [{"modelArn": arn} for arn in MODEL_ARNS]},
            {"inferenceProfileId": PROFILE_ID, "inferenceProfileArn": PROFILE_ARN, "status": "ACTIVE", "type": "SYSTEM_DEFINED", "models": [{"modelArn": MODEL_ARNS[0].replace("anthropic.claude-v1:0", "other.model-v1:0")}]},
            {"inferenceProfileId": PROFILE_ID, "inferenceProfileArn": PROFILE_ARN, "status": "ACTIVE", "type": "SYSTEM_DEFINED", "models": [{"modelArn": MODEL_ARNS[0].replace("us-east-1", "us-west-1")}]},
            {"inferenceProfileId": PROFILE_ID, "inferenceProfileArn": PROFILE_ARN, "status": "ACTIVE", "type": "SYSTEM_DEFINED", "models": [{"modelArn": MODEL_ARNS[1]}]},
        ]
        for response in invalid:
            iam = FakeIAM()
            with self.subTest(response=response), self.assertRaisesRegex(RuntimeError, "inference profile"):
                self.deploy.apply_deployment(
                    "123456789012", "us-east-1", PROFILE_ID, True,
                    session=FakeSession(iam=iam, bedrock=FakeBedrock(response=response)), package=b"zip",
                )
            self.assertIsNone(iam.created)

    def test_preflight_cli_is_read_only_and_prints_no_account_or_arns(self):
        iam = FakeIAM()
        lambda_client = FakeLambda(unreserved=135)
        bedrock = FakeBedrock()
        output = io.StringIO()
        argv = ["--preflight", "--expected-account", "123456789012", "--region", "us-east-1", "--model-id", PROFILE_ID]
        with patch.object(self.deploy.boto3, "Session", return_value=FakeSession(iam=iam, lambda_client=lambda_client, bedrock=bedrock)), patch.object(
            self.deploy, "build_package", side_effect=AssertionError("package built")
        ), redirect_stdout(output):
            status = self.deploy.main(argv)

        result = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(result["unreserved_concurrency"], 135)
        self.assertEqual(result["destination_regions"], ["us-east-1", "us-east-2", "us-west-2"])
        self.assertNotIn("123456789012", output.getvalue())
        self.assertNotIn("arn:aws", output.getvalue())
        self.assertIsNone(iam.created)
        self.assertIsNone(lambda_client.created)

    def test_explicit_account_ceiling_uses_verified_limit_without_reservation(self):
        iam = FakeIAM()
        lambda_client = FakeLambda(unreserved=10, concurrent=10)
        url = self.deploy.apply_deployment(
            "123456789012", "us-east-1", PROFILE_ID, True,
            account_concurrency_ceiling=10,
            session=FakeSession(iam=iam, lambda_client=lambda_client), package=b"zip",
            sleep=lambda _: None,
        )
        self.assertEqual(url, "https://verified.lambda-url.us-east-1.on.aws/")
        self.assertIsNone(lambda_client.concurrency)

    def test_account_limit_above_acknowledged_ceiling_halts_before_writes(self):
        iam = FakeIAM()
        lambda_client = FakeLambda(unreserved=10, concurrent=10)
        with self.assertRaisesRegex(RuntimeError, "ceiling"):
            self.deploy.apply_deployment(
                "123456789012", "us-east-1", PROFILE_ID, True,
                account_concurrency_ceiling=9,
                session=FakeSession(iam=iam, lambda_client=lambda_client), package=b"zip",
            )
        self.assertIsNone(iam.created)

    def test_preflight_cli_reports_explicit_account_limit_mode(self):
        output = io.StringIO()
        lambda_client = FakeLambda(unreserved=10, concurrent=10)
        argv = [
            "--preflight", "--expected-account", "123456789012", "--region", "us-east-1",
            "--model-id", PROFILE_ID, "--account-concurrency-ceiling", "10",
        ]
        with patch.object(
            self.deploy.boto3, "Session", return_value=FakeSession(lambda_client=lambda_client)
        ), patch.object(self.deploy, "build_package", side_effect=AssertionError("package built")), redirect_stdout(output):
            status = self.deploy.main(argv)
        result = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(result["concurrency_control"], "account_limit")
        self.assertEqual(result["account_concurrency_limit"], 10)
        self.assertEqual(result["account_concurrency_ceiling"], 10)
        self.assertNotIn("reserved_concurrency_requested", result)


if __name__ == "__main__":
    unittest.main()
