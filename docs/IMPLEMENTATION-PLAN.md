# First MVP implementation plan

Goal: deliver a working, synthetic-data transition planner with teammate-friendly authenticated AWS endpoints and reference documentation.

Architecture: continue the bounded single-Python-application recommendation. Keep deterministic resource facts, explicit tool selection, human review, and export. A local interface can call a shared AWS Lambda Function URL using temporary organizer AWS credentials on the local server; credentials never enter frontend code. Lambda URL authentication remains AWS_IAM. No new teammate IAM users or permanent keys.

Tech stack: Python 3.12 standard library for validation, HTTP, domain logic and tests; boto3 only for Bedrock and AWS request signing. This deliberately replaces the suggested Pydantic dependency with small explicit validators so the Lambda artifact needs no platform-specific packages. Spec: `../../outputs/simplifynext-hackathon-2026/ARCHITECTURE.md` plus this deployment refinement. User authorized implementation and organizer-resource deployment on 5 September.

The user explicitly approved both remaining execution gates on 6 September: sanitized source transfer to organizer CloudShell and action-time creation of the scoped execution role/authenticated endpoint. Creation and bounded code-only updates are complete; no budget, quota or public-access expansion occurred.

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

1. [x] Domain: red-green tests and independent review completed; 34 domain tests cover constraints, trusted questions, request-local Nova-compatible tool schemas and bounded failures. Unit tests use deterministic model responses; actual live checks are recorded separately.
2. [x] API: signed document envelopes and local HTTP/Lambda adapters implemented. Real HTTP create-review-export, tamper, expiry, caller binding and origin/header checks pass.
3. [ ] Interface: create native labelled controls and review/export flow against documented contracts. Browser-test happy path, unknown eligibility, edit invalidation, error and keyboard flow.
4. [x] AWS: organizer sign-in, balance/role/region and preflight verified; one Lambda+AWS_IAM URL deployed. Unsigned rejection, signed health/resources and baseline offline flow passed. A prior revision passed fictional Bedrock draft-review-export; current broad-goal AI acceptance remains failed/open. No public unauthenticated access.
5. [x] Handoff: teammate/API/deployment/reference docs contain the verified endpoint and reproducible examples. Private coordination records remain outside the repository. Teammate's own-session access is an explicitly pending acceptance check, not inferred from leader access.
6. [x] Review: independent security/domain review found no remaining Critical/Important code findings in the scoped fixes. Fresh suite on 6 September: 67 Python tests plus 2 UI-state tests pass. Live model quality and rendered browser acceptance remain separate.

Interface implementation in step 3 is complete and served in the HTTP test. Browser client blocked local navigation, so rendered/keyboard checks remain pending. On 6 September, AWS account verification resolved, explicit transfer/creation approvals were obtained, and the scoped deployment succeeded using existing account-wide concurrency 10. Regression-tested code-only fixes preserve known inputs, keep provider uncertainty nonblocking and align offered clarification tools to unknown profile fields. A fully specified fictional request completed the live AI workflow on the previous revision. The final broad-goal test still stopped after invalid finish arguments and six tools; full AI acceptance remains incomplete. Further paid tuning stopped pending a bounded diagnostic/design review. No smoke case is a comparative quality benchmark.

Deliberate engineering refinement for this minimal slice: review is bound to an immutable expiring document snapshot. UI edits discard the active review, but retained older reviewed snapshots are not revoked server-side. This narrows the research skeleton's latest-revision-only guarantee; see `docs/ARCHITECTURE.md` and `docs/API.md`.

## Blocker policy

Login/MFA/required security confirmation cannot be bypassed after silence. Continue all local implementation, tests, API docs and deployment packaging while waiting. After 30 minutes without optional preference input, use these defaults: bounded Python implementation, organizer Bedrock, existing AWS identity, authenticated Lambda URL, offline mode only when live access is unavailable. Do not substitute a paid personal provider or claim offline output is live AI.
