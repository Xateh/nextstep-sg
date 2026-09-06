# Guarded AWS deployment

## Status and boundary

**Current constrained artifact deployed:** source revision `aec4030`; deterministic four-file ZIP SHA-256 `5328bcb33ecab0fe7ef09961adf7b31170ddd30e7bdc0ca7300bcf2305898aef`. The CloudShell checksum matched before a revision-guarded code-only update. AWS readback reported `Active` / `Successful` and base64 `CodeSha256` `Uyi8sz7KsP5+8JlhrfezEXDd0w573AynMAvPIwWJiu8=`. The same URL, `AWS_IAM`, `BUFFERED`, Python 3.12 runtime, 90-second timeout, 256 MB memory, environment, signing key and IAM configuration were preserved. Organizer login and CloudShell access recovered without credential extraction or environment restart/deletion. See [VERIFICATION.md](VERIFICATION.md) for the evidence boundary.

Current signed health/resources and the full offline create-review-export guard path passed. No model calls ran in this update turn. The first broad paid request was blocked before execution because explicit case approval was insufficient. One broad and one narrow synthetic case, each capped at two model calls, await explicit approval. Deployment success is not live-model acceptance.

The approved source and scoped AWS resources were initially deployed through organizer CloudShell on 6 September 2026. The verified `AWS_IAM` Function URL remains `https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/`. Historical `f916c959...` completed the narrow fictional Bedrock create-review-export path. Historical `50dad254...` returned a broad non-actionable `partial` at its four-call/six-tool limits. No offline fallback or cap increase occurred. Neither historical result is current-artifact live acceptance.

Deployment evidence:

- Initial published source revision: `bf0d12b`
- Reviewed source archive SHA-256: `98d449ffb246b143d568a38567a289aac91615261aa16ea402918b321da05d02`; the CloudShell upload matched
- Initial CloudShell Lambda package SHA-256: `6be5c23482d7c16190e686ca3819458c33b9d49fa5c103a0756640bbe4f86f4c`
- Post-fix code artifact SHA-256: `c0c611d3d97b222834d9edace88811aa0659ec4a91e78febb3323ad7a19daa31`; the code-only update preserved environment configuration
- Prior question-routing code artifact SHA-256: `f916c95927691192572070a85bb9804ba28e26c7f1af420aa6b41ee22a6de79c`; the narrow fictional end-to-end test passed on this revision
- Historical dynamic-schema code artifact SHA-256: `50dad2544250a554d150515534e0fd737bfce784ec279e8bb2d9a48d948843d2`; AWS reported the function `Active` and the update `Successful` with code SHA-256 `UNrSVEJQpVTRUFFVNOD9c3v854TsJ56LstmkjZSIQ9I=`
- Current constrained-flow source revision: `aec4030`; deployed artifact SHA-256 `5328bcb33ecab0fe7ef09961adf7b31170ddd30e7bdc0ca7300bcf2305898aef`; AWS base64 `CodeSha256` `Uyi8sz7KsP5+8JlhrfezEXDd0w573AynMAvPIwWJiu8=`
- Initial CloudShell verification: 58 Python tests passed using Python 3.13.15 and boto3 1.43.38
- Historical local Windows verification: 67 Python and 2 JavaScript tests passed
- Historical independent review: 34 planner tests and an eight-case schema matrix passed
- Current local verification: 72 Python and 2 JavaScript tests passed; independent review found no Important findings after 39 planner checks, 62 additional checks and tool-choice botocore validation
- Read-only preflight: fixed names were available, the selected Nova US system profile was active, and the account concurrency limit was 10

The historical initial CloudShell package hash differed from a package built from an LF checkout because the uploaded source archive used CRLF files. The current constrained ZIP was uploaded unchanged and its local, CloudShell and deployed hashes match.

The deployment path is create-only. The role and function now exist, so do not rerun `--apply`; it must halt rather than overwrite them. Packaging remains the default and makes no AWS session, authentication, or network call.

The package contains only `app.py`, `catalog.json`, `lambda_function.py`, and `planner.py`, with stable ordering and timestamps. It intentionally does not package dependencies: the Lambda Python 3.12 runtime supplies the AWS SDK used for Bedrock.

## Build locally

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\deploy.py
Get-FileHash dist\simplifynext-mvp.zip -Algorithm SHA256
```

`--package` is an explicit synonym for the default. Use `--output PATH` to choose another package path.

## Preflight controls used for the initial deployment

For an update of the existing function, use the code-only procedure below instead of this initial-create path.

Deployment changes the shared organizer AWS account. Before running it, verify all of these from current organizer sources:

1. The temporary organizer AWS session is active and includes a session token. Permanent access keys are rejected.
2. The exact intended 12-digit account ID is known privately. Do not commit or paste it into shared documentation.
3. The intended region is `us-east-1`, `us-east-2`, or `us-west-2`.
4. The exact organizer-approved US geographic system inference profile ID is known. It must start with `us.`; direct model IDs, global profiles, application profiles, wildcards, and ARNs are rejected.
5. The live shared balance has been manually checked immediately before deployment. `--budget-verified` records that manual check; it does not enforce or guarantee a budget.
6. The caller already has the required read-only preflight and deployment permissions. The script does not broaden the caller's permissions.

For any future clean redeployment after an approved rollback, run the read-only preflight before requesting approval to create resources. It does not build a package or write to AWS. It checks the STS account, fixed-name availability, Lambda account concurrency, and the exact active Bedrock profile and destination model ARNs. It prints no account ID, credentials, or ARNs. Running it against the current deployment will halt because the fixed names already exist.

```powershell
.\.venv\Scripts\python.exe scripts\deploy.py --preflight `
  --expected-account YOUR_12_DIGIT_ACCOUNT_ID `
  --region us-east-1 `
  --model-id us.APPROVED_SYSTEM_PROFILE_ID `
  --account-concurrency-ceiling 10
```

By default, preflight requires at least 101 unreserved concurrency units so the function can reserve 1 while AWS leaves 100 unreserved. On 6 September 2026, the organizer account was separately observed with a total and unreserved concurrency limit of 10. Recheck it each time; do not request a quota increase for this MVP. The explicit `--account-concurrency-ceiling 10` mode acknowledges that verified account-level limit, requires the live positive account limit to be no higher than the supplied integer from 1 through 10, and skips per-function reserved concurrency. It does not claim the function itself is limited to one concurrent execution: all functions in the account can collectively use up to the account limit.

The initial deployment used the following guarded shape after budget and action-time approval. It is retained for reproducibility, not as a rerun instruction:

```powershell
.\.venv\Scripts\python.exe scripts\deploy.py --apply `
  --expected-account YOUR_12_DIGIT_ACCOUNT_ID `
  --region us-east-1 `
  --model-id us.APPROVED_SYSTEM_PROFILE_ID `
  --account-concurrency-ceiling 10 `
  --budget-verified
```

The script verifies the current STS account before any AWS write. It halts if the fixed role or function name already exists, whether owned by this project or unrelated. It never updates or overwrites existing resources. This makes reruns intentionally fail until the existing deployment is inspected and rolled back.

## Code-only update of the existing function

This manual runbook was used for the current constrained artifact and remains the guarded procedure for future updates. Confirm the existing organizer account/region privately, check the current lease balance against the US$20 usable cap, review the code, and run all local checks first. Do not run `scripts/deploy.py --apply` against the existing resources.

1. In the prepared Python environment, build the four-file allowlisted package with `python scripts/deploy.py --package --output dist/simplifynext-mvp-constrained.zip`. Record its SHA-256 in the verification record. Upload only that ZIP through organizer CloudShell's file-upload control; never upload credentials or the entire workspace.
2. In CloudShell, verify the uploaded file with `sha256sum simplifynext-mvp-constrained.zip`. It must exactly match the locally verified artifact.
3. Read current function state without printing environment variables or the signing key:

```bash
aws lambda get-function-configuration --function-name simplifynext-mvp --region us-east-1 --query '{State:State,Update:LastUpdateStatus,RevisionId:RevisionId,CodeSha256:CodeSha256}' --output json --no-cli-pager
```

Proceed only when state is `Active`, the previous update is `Successful`, and the observed code matches the last recorded deployment. Any unexpected revision or code change requires inspection before continuing. Copy the freshly read revision into the placeholder below; never reuse a historical revision ID.

```bash
aws lambda update-function-code --function-name simplifynext-mvp --region us-east-1 --zip-file fileb://simplifynext-mvp-constrained.zip --revision-id FRESH_REVISION_ID --query '{State:State,Update:LastUpdateStatus,CodeSha256:CodeSha256}' --output json --no-cli-pager
```

AWS documents the [revision guard for code updates](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html). A conflict means stop and inspect, not retry without the guard. This command does not update environment configuration, IAM, Function URL settings or the signing key.

4. Read the same selected configuration fields again until the update reports `Successful` and state `Active`; stop and investigate if it fails or remains incomplete. Compare `CodeSha256` with the **base64 encoding of the ZIP's SHA-256 digest**, not the hexadecimal string.
5. Read Function URL configuration and require the same URL, `AWS_IAM`, and `BUFFERED`. Check unsigned rejection, signed health/resources and explicit offline create/review/export guards before any paid validation. Preserve the exact draft for review and never approve a non-actionable partial result.
6. Only after a fresh budget check and explicit approval for each paid case, run the agreed broad and narrow synthetic Bedrock cases, each capped at two model calls. Record actual status, selected IDs, call counts and failure categories. Do not infer success from HTTP 200 or substitute offline output. The current update's first broad attempt was blocked before execution for insufficient explicit case approval; no model call occurred.

Keep the prior verified package for recovery. If rollback is authorized, use the same guarded code-update procedure with that exact prior ZIP; do not delete/recreate the function or rotate its signing key merely to undo a code change.

## Resources created

Exact names and bounds:

- Lambda function: `simplifynext-mvp`
- Execution role: `simplifynext-mvp-execution`
- Inline role policy: `simplifynext-mvp-bedrock-logs`
- Runtime: Python 3.12
- Timeout: 90 seconds
- Memory: 256 MB
- Concurrency: no per-function reservation; deployment explicitly acknowledged the verified account-wide ceiling of 10
- Function URL authentication: `AWS_IAM`
- Ownership tags: `Project=simplifynext-mvp`, `ManagedBy=scripts/deploy.py`

The execution role can write only the function's CloudWatch logs and invoke the selected US geographic inference profile. Preflight calls `GetInferenceProfile`, requires an active `SYSTEM_DEFINED` profile whose exact ARN matches the account and source region, and accepts only matching foundation-model ARNs in the three allowed US regions. The policy is built from the returned destinations, includes the source region, and binds destination-model access to the exact profile ARN with `bedrock:InferenceProfileArn`. It does not permit arbitrary models. An organizer SCP that blocks any profile destination can still prevent invocation and is not changed by this script.

The plan signing key is generated securely only when the function is created. It is placed in the Lambda environment and never printed or written to the package. This deployment path performs no updates. Code-only updates must omit environment/configuration changes so AWS preserves the existing key without retrieving or printing it. Any broader configuration update needs a separate scoped plan; replacing the key invalidates every outstanding signed plan envelope.

IAM role propagation retries are bounded to six Lambda-create attempts and at most 25 seconds of delay. Lambda activation is separately bounded to ten checks and at most 37 seconds of delay before URL configuration. Partial AWS creation can remain after a later failure; inspect exact names and use the rollback sequence below.

The script never calls `AddPermission` and never creates a public function resource policy. Before teammates can use the `AWS_IAM` URL, their existing identity and, when applicable, the function resource policy must grant both `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction`: [AWS Lambda Function URL security and authentication](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html).

The current update changed code only and preserved the existing endpoint, `AWS_IAM`/`BUFFERED` settings, IAM permissions, environment configuration and signing key. Current checks returned signed health 200 (`synthetic-only`, default `bedrock`), resources 200 with eight records, offline create 200 with three actions including the corrected catalog record, unreviewed export 409, inspected review/export 200/200 with 2,139 Markdown characters, tampered export 400 and unsigned health 403. No model call tested the current artifact. General AI acceptance and teammate access from a separate temporary organizer session remain unverified.

## Cost monitoring

Reserved concurrency, when available, limits simultaneous executions; the explicit account-ceiling fallback relies only on the verified account-wide limit and does not impose a per-function limit. Neither mechanism caps total spend. Before the blocked paid attempt, the lease was refreshed as Active and displayed `$0 of $30`; retain the organizer's US$20 usable cap, and allow for billing lag. Check again before each approved model test, then monitor current AWS cost and usage through organizer-provided tools. `--budget-verified` remains mandatory for `--apply` in either concurrency mode. Configure a low cost alert only if the lease permits it. Stop testing and coordinate with the team if usage differs from the expected synthetic scope.

## Finite rollback

Rollback deletes shared AWS resources. First export anything needed, confirm the account and region again, and obtain team approval. Then use the same temporary organizer session and exact deployment region:

```powershell
aws lambda delete-function-url-config --function-name simplifynext-mvp --region YOUR_REGION
aws lambda delete-function --function-name simplifynext-mvp --region YOUR_REGION
aws iam delete-role-policy --role-name simplifynext-mvp-execution --policy-name simplifynext-mvp-bedrock-logs
aws iam delete-role --role-name simplifynext-mvp-execution
```

After confirming no logs must be retained, optionally remove the exact log group:

```powershell
aws logs delete-log-group --log-group-name /aws/lambda/simplifynext-mvp --region YOUR_REGION
```

If an `--apply` attempt fails partway, run read-only `get-function`, `get-role`, and `get-function-url-config` checks first. Delete only resources carrying both ownership tags above; do not delete an unrelated resource with the same name.
