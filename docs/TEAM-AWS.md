# Teammate access to the shared AWS MVP

## NextStep SG rename and local Singapore update — 7 September

The private repository is now [Xateh/nextstep-sg](https://github.com/Xateh/nextstep-sg), still on `mvp`. Update an existing clone with `git remote set-url origin https://github.com/Xateh/nextstep-sg.git`; keep local changes safe when updating the checkout. No local-folder move, collaborator invitation, AWS-resource rename or credential change is required.

The new local app is v0.1.1. The shared API below remains source `aec4030` / v0.1.0: its catalogue and exports have **not** received the Singapore update. A different-content-version warning appears in the new UI when it connects to that service. For the updated synthetic Singapore rehearsal, unset `MVP_API_URL` in the local shell, restart `app.py`, confirm v0.1.1 and keep Offline demo selected. Merely selecting Offline demo does not stop a configured server from forwarding requests to AWS.

The existing endpoint and approved inference profile remain US-based. Singapore English, S$ amounts and SGT display are content choices, not a Singapore data-residency guarantee. Never enter real NRIC/FIN numbers, Singpass details or participant documents. No deployment or paid call was made for this update.

## Existing AWS deployment — evidence from 6 September

The constrained four-file package from source revision `aec4030` is deployed at the existing shared endpoint. Its ZIP SHA-256 `5328bcb33ecab0fe7ef09961adf7b31170ddd30e7bdc0ca7300bcf2305898aef` matched after upload; AWS readback reported `Active` / `Successful` with matching base64 `CodeSha256` `Uyi8sz7KsP5+8JlhrfezEXDd0w573AynMAvPIwWJiu8=`. The same URL, `AWS_IAM`, `BUFFERED`, Python 3.12 runtime, 90-second timeout and 256 MB memory remain. Normal organizer SSO renewal restored CloudShell access without extracting credentials or restarting/deleting the environment.

Current signed health/resources and offline create-review-export guards passed. After explicit approval, one broad and one narrow current-artifact Bedrock smoke test each returned an actionable draft on model call one. Both passed unreviewed-export rejection, inspected review/export and tamper rejection. Total usage was two model calls, 2,896 input and 69 output tokens; no repair, retry or fallback. These are two exact synthetic smoke passes, not general AI reliability, real-provider suitability or full-MVP acceptance. No further paid tests are planned. Teammate-own-session and local rendered-interface checks remain unverified.

The team uses the existing organizer-provided AWS identity. The verified endpoint is `https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/`. Fresh AWS readback remained `Active` / `Successful` with the same `AWS_IAM` URL and configuration. Current checks returned unsigned health 403; signed health 200, signed resources 200 with eight records, and offline create 200 with three actions including the corrected catalog record. Unreviewed export returned 409; after inspection, review/export returned 200/200 with 2,139 Markdown characters; tampered export returned 400.

For the current Bedrock checks, both exact profiles used known `full_time_student: false`, `weekly_hours: 3` and `budget_sgd: 0`. The broad request selected only the fictional office-skills taster and returned one permitted but unnecessary provider-access question; its export was 664 characters. The committed narrow request selected the same fictional action with no questions; its export was 717 characters. Labels and warnings remained intact. Historical `f916c959...` passed the narrow path, while historical `50dad254...` returned a broad non-actionable partial.

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

The example above is deliberately offline; it checks the authenticated API workflow without invoking a model. This baseline create-review-export flow is verified on the current deployment. The current broad and committed narrow Bedrock smoke cases also passed as bounded evidence after explicit approval and fresh budget checks. No further paid tests are planned. CloudShell is the API-check route; use the local setup below for the browser interface.

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

Files passed to `--output` can contain only signed envelopes whose profile is marked `synthetic: true`. They never contain AWS credentials. Store request and envelope files under `private\`; that directory is gitignored, but still treat its contents as private synthetic working data. Console output may contain the same synthetic plan data.

## Browser boundary and failures

The browser interface calls only the loopback application in `app.py`. That local server signs and forwards requests. AWS credentials must never appear in frontend JavaScript, browser storage, URLs, plan files, or logs.

The earlier 7 September UI-only refinement did not require Lambda redeployment. The later Singapore localisation also changes the backend catalogue and export text; that content remains local until a separately approved deployment. Edit profile retains inputs but clears the draft/review; Start over clears local data and restores offline mode. Downloaded files are not deleted. Expiry is shown with the date in SGT; an expired draft remains readable.

Browser requests time out after 95 seconds and are never automatically retried. If a Bedrock creation times out or loses its connection, the server may still complete it. Check with the team before generating again because another request may incur another charge. Malformed responses/downloads are rejected, and expired review/export requests require a fresh plan. This UI update does not verify access from a teammate's own session.

The client uses a 90-second timeout and never follows redirects with signed headers. Refresh temporary credentials after expiry. A `403` usually means that the current role or a function resource policy does not permit both required invoke actions. A rejected endpoint value means `MVP_API_URL` is not the exact verified root Function URL. HTTP error output is reduced to a bounded JSON error and does not include response debug fields or credential material.
