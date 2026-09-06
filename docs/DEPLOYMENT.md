# Guarded AWS deployment

## Status and boundary

The approved source and scoped AWS resources were deployed through organizer CloudShell on 6 September 2026. The verified `AWS_IAM` Function URL is `https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/`. Unsigned health returned 403; signed health and resource listing returned 200. Baseline offline create-review-export and its review/tamper guards are verified. On the prior `f916c959...` revision, the [fully specified fictional Bedrock smoke request](../examples/fictional-bedrock-request.json) completed create, explicit review and export successfully; it was not rerun on the final revision. The final revision's broader Bedrock goal returned HTTP 200 `partial` without an actionable plan after reaching the unchanged four-model-call/six-tool limits. No offline fallback was used. The shared API and offline engineering demo are deployed; general AI and general-purpose MVP acceptance remain unresolved.

Deployment evidence:

- Initial published source revision: `bf0d12b`
- Reviewed source archive SHA-256: `98d449ffb246b143d568a38567a289aac91615261aa16ea402918b321da05d02`; the CloudShell upload matched
- Initial CloudShell Lambda package SHA-256: `6be5c23482d7c16190e686ca3819458c33b9d49fa5c103a0756640bbe4f86f4c`
- Post-fix code artifact SHA-256: `c0c611d3d97b222834d9edace88811aa0659ec4a91e78febb3323ad7a19daa31`; the code-only update preserved environment configuration
- Prior question-routing code artifact SHA-256: `f916c95927691192572070a85bb9804ba28e26c7f1af420aa6b41ee22a6de79c`; the narrow fictional end-to-end test passed on this revision
- Final dynamic-schema code artifact SHA-256: `50dad2544250a554d150515534e0fd737bfce784ec279e8bb2d9a48d948843d2`; AWS reported the function `Active` and the update `Successful` with code SHA-256 `UNrSVEJQpVTRUFFVNOD9c3v854TsJ56LstmkjZSIQ9I=`
- Initial CloudShell verification: 58 Python tests passed using Python 3.13.15 and boto3 1.43.38
- Final local Windows verification: 67 Python and 2 JavaScript tests passed
- Independent final review: 34 planner tests and an eight-case schema matrix passed
- Read-only preflight: fixed names were available, the selected Nova US system profile was active, and the account concurrency limit was 10

The CloudShell package hash differs from a package built from an LF checkout because the uploaded source archive used CRLF files. This is expected byte-level input variation, not an unexplained source mismatch.

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

The final update changed code only and preserved the existing endpoint, IAM permissions, environment configuration, and signing key. The URL was disclosed only after read-back confirmed `AuthType=AWS_IAM`. Unsigned rejection, signed health/resources, and the baseline offline workflow are verified. The fully actionable Nova create-review-export smoke case passed on the prior revision but was not rerun on the final revision. On the final revision, the broad test reached `search_resources`, three resource inspections, a second search, and an invalid `finish_plan`; model call four stopped at `tool_limit`, yielding a non-actionable partial result. No silent fallback or cap increase occurred. General AI acceptance remains unresolved, and teammate access from a separate temporary organizer session remains unverified.

## Cost monitoring

Reserved concurrency, when available, limits simultaneous executions; the explicit account-ceiling fallback relies only on the verified account-wide limit and does not impose a per-function limit. Neither mechanism caps total spend. Check the organizer portal balance before deployment and model tests, then monitor current AWS cost and usage through the organizer-provided tools. `--budget-verified` remains mandatory for `--apply` in either concurrency mode. Configure a low cost alert only if the lease permits it. Stop testing and coordinate with the team if usage differs from the expected synthetic smoke-test scope. No service price or remaining credit amount is asserted here because both require current verification.

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
