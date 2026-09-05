# Teammate access to the shared AWS MVP

## Current status

The team uses the existing organizer-provided AWS SSO identity. A Lambda Function URL has not yet been verified, so this repository does not contain or claim an endpoint. Add `MVP_API_URL` only after the organizer account, region, deployment, `AWS_IAM` configuration, and signed smoke test have been checked.

Do not create or share permanent IAM access keys. Do not assume that every organizer user or role can invoke the function. The deployed function must remain private with Function URL authentication type `AWS_IAM`.

AWS documents that a caller needs both `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` permissions for `AWS_IAM` Function URLs. The applicable resource policy and identity policy must allow the intended call: [AWS Lambda Function URL security and authentication](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html).

## Private temporary-credential setup

1. Sign in through the organizer AWS access portal using the existing team identity and MFA. Never send passwords, MFA codes, portal links, account IDs, or credentials in chat or commit them.
2. Obtain temporary credentials privately from the portal, or use AWS CLI SSO if the organizer environment supports it. Follow the organizer's role and region instructions; this repository does not assume a role name or permission set.
3. Keep credentials in the standard AWS SDK credential chain. The client calls `boto3.Session` and requires a session token, so permanent access-key pairs are rejected.
4. Set `MVP_API_URL` locally to the verified root HTTPS Lambda Function URL. The client rejects other hosts, ports, embedded credentials, paths, query strings, fragments, and unsupported regions.
5. Refresh the AWS session when its temporary credentials expire.

Example using a locally configured AWS CLI SSO profile:

```powershell
aws sso login --profile YOUR_ORGANIZER_PROFILE
$env:AWS_PROFILE = 'YOUR_ORGANIZER_PROFILE'
$env:MVP_API_URL = 'VERIFIED_FUNCTION_URL'
.\.venv\Scripts\python.exe scripts\aws_client.py health
```

`VERIFIED_FUNCTION_URL` is a placeholder, not a deployed endpoint. Do not save credentials in `.env` files or source code.

## Supported calls

Run commands from the repository root:

```powershell
New-Item -ItemType Directory -Force private | Out-Null
.\.venv\Scripts\python.exe scripts\aws_client.py health
.\.venv\Scripts\python.exe scripts\aws_client.py resources
.\.venv\Scripts\python.exe scripts\aws_client.py create --body private\create-request.json --output private\draft-envelope.json
.\.venv\Scripts\python.exe scripts\aws_client.py review --body private\draft-envelope.json --output private\reviewed-envelope.json
.\.venv\Scripts\python.exe scripts\aws_client.py export --body private\reviewed-envelope.json
.\.venv\Scripts\python.exe scripts\aws_client.py GET /health
```

The named routes are exactly:

- `GET /health`
- `GET /v1/resources`
- `POST /v1/plans`
- `POST /v1/plans/review`
- `POST /v1/plans/export`

For a generic request, use `METHOD PATH --body private\request.json`. `create` expects a complete `/v1/plans` request object. `review` and `export` expect a saved signed envelope; the client adds the route wrapper, including explicit approval for `review`.

Files passed to `--output` can contain only signed envelopes whose profile is marked `synthetic: true`. They never contain AWS credentials. Store request and envelope files under `private\`; that directory is gitignored, but still treat its contents as private participant working data. Console output may contain the same synthetic plan data.

## Browser boundary and failures

The browser interface calls only the loopback application in `app.py`. That local server signs and forwards requests. AWS credentials must never appear in frontend JavaScript, browser storage, URLs, plan files, or logs.

The client uses a 90-second timeout and never follows redirects with signed headers. Refresh temporary credentials after expiry. A `403` usually means that the current role or a function resource policy does not permit both required invoke actions. A rejected endpoint value means `MVP_API_URL` is not the exact verified root Function URL. HTTP error output is reduced to a bounded JSON error and does not include response debug fields or credential material.
