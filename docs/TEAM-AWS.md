# Teammate access to the shared AWS MVP

## Current status

The team uses the existing organizer-provided AWS identity. On 6 September 2026, the leader deployed and verified `https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/` with Function URL authentication type `AWS_IAM`. Unsigned health returned 403; signed health and resource listing returned 200. On the prior `f916c959...` revision, the [fully specified fictional Bedrock request](../examples/fictional-bedrock-request.json) returned one actionable draft and passed explicit review and export; it was not rerun after the final update. On the final revision, a broader synthetic request returned HTTP 200 `partial` after reaching the unchanged four-model-call/six-tool limits, without an actionable plan. No offline result was substituted and no cap was raised. The shared API and offline engineering demo are deployed; general AI and general-purpose MVP acceptance remain unresolved.

Access from a teammate's own temporary organizer session has not yet been tested. Leader CloudShell success does not prove a teammate has both required invoke permissions.

Do not create or share permanent IAM access keys. Do not assume that every organizer user or role can invoke the function. The deployed function must require authorization with Function URL authentication type `AWS_IAM`; its URL is internet-addressable, not private-network hosting.

AWS documents that a caller needs both `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` permissions for `AWS_IAM` Function URLs. The applicable resource policy and identity policy must allow the intended call: [AWS Lambda Function URL security and authentication](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html).

Use the local loopback interface below for the main teammate experience once that teammate has their own temporary organizer credentials. CloudShell is an optional direct API check, not a shared workspace.

## Optional direct API check: organizer CloudShell

Each CloudShell environment and session is separate. Do not assume a teammate can access the leader's uploaded repository copy or credentials. To check the existing endpoint without moving credentials:

1. Open the organizer AWS account using the intended existing role, then open CloudShell in `us-east-1`. Use your organizer-issued access; do not create new IAM users or share a personal password.
2. Obtain the approved sanitized source archive from the private GitHub repository. This requires the teammate's own repository access; never share a personal GitHub token. Upload only that archive through CloudShell **Actions > Upload file**. Never upload the whole workspace, `.aws`, `.env`, private chats or credentials.
3. Extract the archive into a fresh directory and change into the extracted repository. Do not use or document a temporary path from another person's session. CloudShell supplies the current console session's temporary AWS credentials; never export or copy them elsewhere.
4. Run the checks below. An access-denied response requires inspection of the existing role permissions, not public access or permanent keys.

```bash
export MVP_API_URL='https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/'
python3 scripts/aws_client.py health
python3 scripts/aws_client.py resources
mkdir -p private
python3 scripts/aws_client.py create --body examples/create-request.json --output private/draft.json
# Inspect the draft before explicitly approving that exact plan:
python3 scripts/aws_client.py review --body private/draft.json --output private/reviewed.json
python3 scripts/aws_client.py export --body private/reviewed.json
```

The example above is deliberately offline; it checks the authenticated API workflow without invoking a model. This baseline create-review-export flow is live-verified. The separate committed Bedrock example passed only on the prior revision and was not rerun on the final revision; the final broad-goal result above prevents a general live-planner readiness claim. Do not rerun paid model checks without a fresh reason and budget check. CloudShell is the API-check route; use the local setup below for the browser interface.

## Local browser interface: private temporary-credential setup

1. Sign in through the organizer AWS access portal using the existing team identity and MFA. Never send passwords, MFA codes, portal links, account IDs, or credentials in chat or commit them.
2. Obtain temporary credentials privately from the portal, or use AWS CLI SSO if the organizer environment supports it. Follow the organizer's role and region instructions; this repository does not assume a role name or permission set.
3. Keep credentials in the standard AWS SDK credential chain. The client calls `boto3.Session` and requires a session token, so permanent access-key pairs are rejected.
4. Set `MVP_API_URL` locally to the verified root HTTPS Lambda Function URL. The client rejects other hosts, ports, embedded credentials, paths, query strings, fragments, and unsupported regions.
5. Refresh the AWS session when its temporary credentials expire.

Example using a locally configured AWS CLI SSO profile:

```powershell
aws sso login --profile YOUR_ORGANIZER_PROFILE
$env:AWS_PROFILE = 'YOUR_ORGANIZER_PROFILE'
$env:MVP_API_URL = 'https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/'
.\.venv\Scripts\python.exe scripts\aws_client.py health
```

Do not save credentials in `.env` files or source code. Each teammate must use their own temporary organizer session; never copy the leader's CloudShell credentials.

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
