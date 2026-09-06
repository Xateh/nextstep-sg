# API reference — v0.1.0

Status: the local API and shared AWS engineering endpoint were verified on 6 September 2026. Signed health, resources, baseline offline create-review-export, unreviewed rejection and tamper rejection were checked against the deployed function. On the prior `f916c959...` revision, the [fully specified fictional Bedrock smoke request](../examples/fictional-bedrock-request.json) completed create, explicit review and export successfully; it was not rerun on the final revision. The final revision's broader Bedrock test returned HTTP 200 `partial` without an actionable plan after reaching its unchanged limits. No offline result was substituted. General AI and general-purpose MVP acceptance remain unresolved.

## Connection

Local base: `http://127.0.0.1:8765`. All POST requests require `Content-Type: application/json` and `X-SimplifyNext-Client: 1`. The local server rejects cross-origin POSTs and unexpected Host headers. It is a single-user development server, not public hosting.

Shared base: `https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/`. All calls require AWS SigV4 for service `lambda` in `us-east-1`, using temporary organizer credentials. Use `scripts/aws_client.py`; do not put credentials in frontend JavaScript or manually share signed headers. Both `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` must be permitted. Access from a teammate's own session is not yet verified. [AWS Function URL authentication](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html)

Live checks returned: unsigned `GET /health` 403; signed `GET /health` 200 with version `0.1.0`, `synthetic-only`, and default mode `bedrock`; signed `GET /v1/resources` 200 with eight records. Baseline offline create, review and export each returned 200. Export before review returned 409, and a changed envelope returned 400.

JSON object responses, UTF-8, no caching. Maximum request body: 65,536 bytes. No streaming, pagination, database, uploads, arbitrary URLs or outbound messaging.

| Method and path | Input | Success body |
|---|---|---|
| `GET /health` | None | `status`, `version`, `data_policy`, `default_mode` |
| `GET /v1/resources` | None | `{ "resources": [...] }`, reviewed catalog plus clearly marked fictional record |
| `POST /v1/plans` | `{ "profile": {...}, "mode": "offline" }` | Signed plan envelope, initially `reviewed: false` |
| `POST /v1/plans/review` | `{ "envelope": <unchanged envelope>, "approved": true }` | Same plan, signed with `reviewed: true` |
| `POST /v1/plans/export` | `{ "envelope": <reviewed envelope> }` | `{ "filename": "transition-plan.md", "content": "...Markdown..." }` |

All successful routes return 200. The export response is JSON containing text, not a binary download. Browser and mobile clients should call their own trusted backend; permissive CORS is intentionally not configured on the AWS function.

## Create a plan

Use [the complete synthetic example](../examples/create-request.json). `mode` is `offline` or `bedrock`. If omitted, the server uses its configured default. Offline uses deterministic catalog search. Bedrock performs actual model-selected bounded tool calls; failure never switches to offline success.

| Profile field | Type and meaning |
|---|---|
| `goal` | Optional string, up to 500 characters; empty requests clarification |
| `strengths` | String, up to 1,000 characters; may be empty |
| `interests` | Array of up to 20 nonempty strings, each up to 200 characters |
| `full_time_student` | Boolean or `null` for unknown |
| `weekly_hours` | Integer 0–168 or `null` for unknown |
| `budget_sgd` | Integer 0–100,000 or `null` for unknown; a practical cap, not a financial assessment |
| `supporter_goal` | Optional string, up to 500 characters; differing text requests participant clarification |
| `synthetic` | Must be the JSON boolean `true` |

Unknown fields are rejected. Do not include names, contact details, diagnoses, documents or real personal information. The synthetic flag is an explicit usage boundary, not a reliable automatic detector of personal data.

Local PowerShell example:

```powershell
$request = Get-Content -Raw examples\create-request.json
$draft = Invoke-RestMethod -Uri http://127.0.0.1:8765/v1/plans -Method Post -ContentType application/json -Headers @{'X-SimplifyNext-Client'='1'} -Body $request
$reviewBody = @{envelope=$draft; approved=$true} | ConvertTo-Json -Depth 30
# Run the following only after inspecting $draft.plan and approving that exact document.
$reviewed = Invoke-RestMethod -Uri http://127.0.0.1:8765/v1/plans/review -Method Post -ContentType application/json -Headers @{'X-SimplifyNext-Client'='1'} -Body $reviewBody
$exportBody = @{envelope=$reviewed} | ConvertTo-Json -Depth 30
$export = Invoke-RestMethod -Uri http://127.0.0.1:8765/v1/plans/export -Method Post -ContentType application/json -Headers @{'X-SimplifyNext-Client'='1'} -Body $exportBody
$export.content
```

Shared AWS example, after authentication and setting `MVP_API_URL`:

```powershell
New-Item -ItemType Directory -Force private | Out-Null
.\.venv\Scripts\python.exe scripts\aws_client.py create --body examples\create-request.json --output private\draft.json
# Inspect the draft before explicitly reviewing it:
.\.venv\Scripts\python.exe scripts\aws_client.py review --body private\draft.json --output private\reviewed.json
.\.venv\Scripts\python.exe scripts\aws_client.py export --body private\reviewed.json
```

The first example requests offline mode even against AWS. On the prior `f916c959...` revision, the committed Bedrock example returned 200 with `mode: "bedrock"`, status `draft`, one fictional office-skills taster action and no questions; review and export returned 200 after inspection. Export before review returned 409. The 717-character Markdown export remained labelled synthetic/Bedrock and stated that nothing was sent, enrolled or booked. That historical run used two bounded model calls and was not repeated on the final revision.

The final revision's broader live test used the existing `examples/create-request.json` profile with only the mode changed to `bedrock`. It returned HTTP 200 with status `partial` and no actionable plan. The trace reached all six allowed tools: `search_resources`, three `inspect_resource` calls, another `search_resources`, then an invalid `finish_plan`; model call four stopped at `tool_limit`. No offline fallback was used and neither the four-model-call nor six-tool cap was raised. This application-level failure means the deployed shared API is an engineering demo, not an accepted general-purpose planner. No more paid model tests are planned for this handoff; check budget before any future model request.

## Plan and approval contracts

Envelope fields are `plan`, `reviewed`, `expires_at` (Unix seconds), `principal` (one-way caller binding), and `signature`. Keep the entire envelope unchanged. Clients must not construct or modify it. It expires 30 minutes after creation; review does not extend its life.

`plan` contains `mode`, `status`, normalized `profile`, `actions`, `questions` and `trace`. Status is `draft`, `needs_clarification` or `partial`. Actions contain catalog-derived `resource_id`, `title`, `next_step`, `source_url` and `checks`. A partial or clarification result can have no actions and cannot be reviewed/exported until an actionable draft exists. Questions and source facts are not eligibility decisions.

Review binds the exact signed document, not a mutable server session. The interface discards its envelope when a profile changes, so the new draft requires fresh approval. An independently retained, previously reviewed snapshot remains exportable until its original expiry. **There is no server-side latest-revision revocation**, cross-device participant identity, or approval of all future changes. Restarting the local server invalidates local envelopes; rotating the cloud signing key invalidates cloud envelopes. AWS caller binding uses the IAM user ARN provided by Lambda; shared organizer identities are not separate participant identities.

## Errors

Application errors are `{ "error": "human-readable explanation" }`. Authentication-layer AWS errors may have a different AWS shape; the supplied client reduces them to safe error output.

| Status | Meaning / recovery |
|---|---|
| 400 | Invalid input or changed envelope; correct input or generate again |
| 401 | Lambda adapter sees no IAM identity; configuration defense, normally AWS rejects unsigned calls before invoking it |
| 403 | AWS permissions/session, wrong caller binding, or local origin/header rejection |
| 404 | Unsupported route or method/path pair |
| 409 | Plan not reviewed or no actionable plan; resolve questions and review |
| 410 | Envelope expired; create and review a new plan |
| 413 | Request exceeds body limit |
| 415 | POST requires JSON content type |
| 429 | AWS throttling may reject concurrent calls; coordinate tests, do not hammer retries |
| 503 | Model, credentials or service unavailable; no fabricated live success |

Live calls are capped at four model requests and six tools per plan. This is not a shared monetary cap. User-approved exports can be repeated without sending anything externally. Failed create requests have no idempotency key; a retry can incur a new model call, so inspect errors before retrying.
