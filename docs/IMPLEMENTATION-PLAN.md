# First MVP implementation plan

Goal: deliver a working, synthetic-data transition planner with teammate-friendly authenticated AWS endpoints and reference documentation.

Architecture: continue the bounded single-Python-application recommendation. Keep deterministic resource facts, explicit tool selection, human review, and export. A local interface can call a shared AWS Lambda Function URL using temporary organizer AWS credentials on the local server; credentials never enter frontend code. Lambda URL authentication remains AWS_IAM. No new teammate IAM users or permanent keys.

Tech stack: Python 3.12 standard library for validation, HTTP, domain logic and tests; boto3 only for Bedrock and AWS request signing. This deliberately replaces the suggested Pydantic dependency with small explicit validators so the Lambda artifact needs no platform-specific packages. Spec: `../../outputs/simplifynext-hackathon-2026/ARCHITECTURE.md` plus this deployment refinement. User authorized implementation and organizer-resource deployment on 5 September.

That existing deployment authorization remains in force. Two execution gates are separate: the upload reviewer requires explicit permission to transfer the sanitized source to organizer CloudShell, and this browser-automation workflow requires action-time confirmation immediately before creating the execution role/access permissions and authenticated endpoint. Neither gate is a request to redesign the project or expand its budget.

## Global constraints

- Fictional profiles only; no diagnoses, certificates, real identities or employer records.
- Existing organizer lease only, US$20 usable total budget, live balance must be checked before deployment/model tests.
- At most four model requests and six tool calls per plan; finite timeouts; no web search, arbitrary URLs, execution or message sending.
- Source URLs come from reviewed catalog records, never generated text.
- Participant approval must bind the exact plan content; edits require fresh approval.
- AWS credentials only in SDK credential chain/environment; never files committed to Git, API docs, browser JavaScript or logs.

## File ownership and contracts

- `planner.py`, `catalog.json`, `tests/test_planner.py`: domain/agent owner. `create_plan(profile: dict, mode='offline', client=None) -> dict`. Modes `offline` and `bedrock`; offline output explicitly labelled. Response fields: `mode`, `status` (`needs_clarification`, `draft`, `partial`), `profile`, `actions` (each `resource_id`, `title`, `next_step`, `source_url`, `checks`), `questions`, `trace`. Inputs: `goal`, `strengths` (string), `interests` (list of strings), `full_time_student` (boolean or null), `weekly_hours` (integer or null), `budget_sgd` (nonnegative integer or null), `supporter_goal` (optional string), `synthetic` (must be true). Domain raises `ValueError` for invalid input; never silently falls back after live-model failure. `load_catalog() -> list[dict]`.
- `app.py`, `lambda_function.py`, `tests/test_api.py`: root owner. `GET /health`, `GET /v1/resources`, `POST /v1/plans`, `POST /v1/plans/review`, `POST /v1/plans/export`. Signed plan envelopes allow stateless Lambda operation. Authentication enforced at AWS_IAM boundary; local bind only to loopback. Return JSON errors without stack traces or credentials.
- `static/index.html`: interface owner. Same-origin calls to endpoints above. Evidence cards, editable profile, explicit review, download, visible mode/trace/errors. No external assets/frameworks.
- `scripts/deploy.py`, `scripts/aws_client.py`, `docs/API.md`, `docs/TEAM-AWS.md`, `README.md`: root owner. Package source, deploy only to authenticated intended organizer account, record actual endpoint only after smoke test. Documentation includes temporary credential expiry, region, signed requests, errors and rollback.

## Execution checklist

1. [x] Domain: red-green tests and independent review completed; 25 domain tests cover constraints, trusted questions, Nova-compatible tool schemas and bounded failures. Model behavior is replaced by deterministic test responses, not claimed live.
2. [x] API: signed document envelopes and local HTTP/Lambda adapters implemented. Real HTTP create-review-export, tamper, expiry, caller binding and origin/header checks pass.
3. [ ] Interface: create native labelled controls and review/export flow against documented contracts. Browser-test happy path, unknown eligibility, edit invalidation, error and keyboard flow.
4. [ ] AWS: access organizer portal through saved browser sign-in; verify balance/role/region; deploy minimal Lambda+AWS_IAM URL if permitted. Do not create public unauthenticated model endpoints. Test unsigned rejection plus signed health, resource listing and one live planner request.
5. [ ] Handoff: teammate/API/deployment/reference docs complete with explicit pending endpoint. Private GitHub publication tracked in README; live endpoint documentation requires actual verification. Private coordination records stay outside repository.
6. [x] Review: independent security/domain review found no remaining Critical/Important local-scope findings after fixes. Fresh suite on 6 September: 58 Python tests plus 2 UI-state tests pass. Rendered browser and live AWS verification remain separate unchecked gates.

Interface implementation in step 3 is complete and served in the HTTP test. Browser client blocked local navigation, so rendered/keyboard checks remain pending. Step 4 advanced on 6 September: organizer login, active lease and CloudShell verified; existing Lambda account concurrency is 10. A minimal Nova request was denied because the AWS account is still being verified. No successful live model response, IAM/Lambda creation, or endpoint test has occurred. Sanitized source upload to organizer CloudShell was stopped pending explicit destination/file approval; finish that approval and resource-creation approval before proceeding.

Deliberate engineering refinement for this minimal slice: review is bound to an immutable expiring document snapshot. UI edits discard the active review, but retained older reviewed snapshots are not revoked server-side. This narrows the research skeleton's latest-revision-only guarantee; see `docs/ARCHITECTURE.md` and `docs/API.md`.

## Blocker policy

Login/MFA/required security confirmation cannot be bypassed after silence. Continue all local implementation, tests, API docs and deployment packaging while waiting. After 30 minutes without optional preference input, use these defaults: bounded Python implementation, organizer Bedrock, existing AWS identity, authenticated Lambda URL, offline mode only when live access is unavailable. Do not substitute a paid personal provider or claim offline output is live AI.
