# Verification record — 6 September 2026

## Current deployment — constrained workflow, AI acceptance pending

On 6 September 2026, the user resumed the existing in-app AWS session. The assigned account and role matched the intended sandbox; the lease was active. A refreshed portal balance before deployment and again before the attempted paid check showed $0 of $30. The organizer's **US$20 usable cap** remains controlling; billing may lag. No new lease, permanent credentials or permissions were created.

The exact four-file ZIP below was uploaded through CloudShell's file chooser and its SHA-256 matched. The previous `50dad254...` hash and `Active` / `Successful` state were read before the revision-guarded code-only update. Subsequent AWS readback confirmed `Active`, `Successful` and `CodeSha256=Uyi8sz7KsP5+8JlhrfezEXDd0w573AynMAvPIwWJiu8=`. This deploys source commit `aec4030b86e10332afe12d9d5928eb6f9cb99ce6`, including the catalog correction. The URL remained the same `AWS_IAM` / `BUFFERED` endpoint. Environment configuration, signing key, IAM and URL settings were not changed. No CloudShell environment restart or deletion was needed.

Current-package checks completed at approximately 19:00–19:06 SGT:

| Check | Observed result |
|---|---|
| Unsigned health | 403 |
| Signed health | 200; version 0.1.0, synthetic-only, default Bedrock |
| Signed resource list | 200; eight records |
| Explicit offline create | 200; three catalog-backed actions, including updated provider checks |
| Export before review | 409 |
| Inspect exact offline draft, then review/export | 200 / 200; 2,139-character Markdown with all selected titles |
| Tampered reviewed envelope export | 400 |

**Paid-check blocker:** auto-review rejected the first broad Bedrock request before execution because explicit approval for that case was required. The user was asked to approve one broad and one narrow synthetic Nova Lite request, at most two model calls each, within the existing US$20 usable budget. No model call occurred during this deployment continuation, and no alternate execution path was used after the rejection. Current AI behavior remains unknown; HTTP/API baseline success is not model acceptance. Teammate-session and rendered UI/keyboard acceptance also remain open.

The CloudShell API client and baseline fixture matched the current repository after accounting for the existing CRLF source archive. Fresh release preflight passed all 72 Python and two interface-state tests, verified a clean source tree, ZIP integrity, the four-file allowlist and exact current-file byte equality.

## Local constrained-source verification — before deployment

At approximately 16:00 SGT on 6 September 2026, fresh root verification passed **72 Python tests and two interface-state tests**. The implementation replaces the free-choice search/inspection loop with an application-generated top-three catalog shortlist, exact shortlist-ID validation and applicable question enums. It permits one initial model call and one repair; malformed, truncated or multiple-tool responses cannot be accepted as complete. Empty shortlists stop without a model call. Participant/supporter, synthetic-only, provenance and exact-plan review/export safeguards remain covered. Automated model tests use doubles, not paid calls or evidence of live model quality.

Deployed ZIP: `dist/simplifynext-mvp-constrained.zip`. SHA-256: `5328bcb33ecab0fe7ef09961adf7b31170ddd30e7bdc0ca7300bcf2305898aef`; base64 digest: `Uyi8sz7KsP5+8JlhrfezEXDd0w573AynMAvPIwWJiu8=`. The archive contains only `app.py`, `catalog.json`, `lambda_function.py` and `planner.py`. Before deployment, an isolated extraction imported those modules, created an offline draft with three catalog-backed actions and rejected unreviewed export with 409. No model call occurred. The full suite separately exercises actual loopback HTTP create/review/export, tampering and caller boundaries.

Independent code review reported no Important findings. Its fresh 39 planner tests and 62 additional checks passed, including all eight null/false/zero schema combinations, malformed-response repair shape, terminal stops and no-client-creation gates. Both named-finish and any-tool request variants passed installed botocore parameter validation. These checks establish local contract compatibility, not a live Nova acceptance result.

During the earlier afternoon source-only continuation, the in-app browser was unavailable and no AWS write or paid validation occurred. That access blocker was subsequently resolved, and the deployment above supersedes the earlier source-only status. Pulling source still does not itself deploy it.

## Prior deployed verification — request-local schema alignment

Fresh root verification after request-local schema alignment: **67 Python tests and 2 interface-state tests passed**. Independent review reported no Important code findings; its 34 planner tests and separate eight-combination schema matrix passed. Earlier question-applicability review also passed. Whitespace checks passed. Automated tests use cloud doubles; the live observations below are separate evidence.

Prior deployed deterministic Lambda archive SHA-256: `50dad2544250a554d150515534e0fd737bfce784ec279e8bb2d9a48d948843d2`. AWS readback then reported `Active` / `Successful` and matching base64 `CodeSha256` (`UNrSVEJQpVTRUFFVNOD9c3v854TsJ56LstmkjZSIQ9I=`). The archive contains only `app.py`, `catalog.json`, `lambda_function.py` and `planner.py`.

## Historical live deployment and API checks — before constrained flow

Observed on 6 September 2026 through the organizer's in-app browser CloudShell, using its existing temporary session:

- Existing lease active; budget checked before creation and refreshed at approximately 11:43 SGT after the successful fictional workflow: portal displayed $0 of $30. Retain the organizer's documented **US$20 usable cap**. Billing can lag; this is not evidence that the calls were free.
- The user explicitly approved the sanitized source transfer and scoped resource creation. An expired upload session was renewed and the upload retried through the same browser flow. No credential extraction or access-control bypass occurred.
- Uploaded source archive SHA-256: `98d449ffb246b143d568a38567a289aac91615261aa16ea402918b321da05d02`. The initial 58-test suite and read-only preflight passed inside CloudShell, using its supplied Python 3.13.15 and boto3 1.43.38. Local reference runtime is Python 3.12.14/boto3 1.43.89; Lambda runtime is Python 3.12.
- Created one `simplifynext-mvp` Lambda, a scoped `simplifynext-mvp-execution` role and its exact-model/own-logs policy in `us-east-1`. Memory 256 MB, timeout 90 seconds. No permanent keys, public resource policy, new lease or quota increase.
- Existing account-wide Lambda concurrency is 10; explicit account-ceiling mode was used without a per-function reservation. This is neither a per-function-one nor monetary cap.
- Function URL verified as `AWS_IAM`, `BUFFERED`; no CORS added. Actual endpoint is recorded in [TEAM-AWS.md](TEAM-AWS.md). Leader invocation succeeded; a teammate's own session remains unverified.
- Nova Lite `us.amazon.nova-lite-v1:0` was active across the allowed US destinations and actual Converse calls succeeded. Earlier account-verification denial is resolved. Haiku agreement was unavailable; no Haiku call or agreement acceptance occurred.
- Three revision-guarded code-only updates addressed question routing and schema alignment. No environment, signing key, URL or IAM policy update was made. A baseline reviewed envelope remained exportable after the first code update, confirming signing continuity at that point.

| Deployed API check | Result |
|---|---|
| Unsigned `GET /health` | 403 |
| Signed `GET /health` | 200; version 0.1.0, synthetic-only, default bedrock |
| Signed `GET /v1/resources` | 200; eight records |
| Explicit offline create, review, export | All 200; three catalog-backed actions |
| Offline export before review / after tampering | 409 / 400 |
| Prior `f916c959` revision: live fictional Bedrock create | 200; `draft`, one fictional action, no questions |
| Prior `f916c959` revision: live export before review | 409 |
| Prior `f916c959` revision: inspected live draft, explicit review, export | 200 / 200; `transition-plan.md`, 717 characters |
| Historical `50dad254` revision: original broader goal, mode Bedrock | 200; non-actionable `partial`, tool limit reached |

Regression checks on historical revision `50dad254` were repeated after its code update, without model calls: signed health/resources/offline create each 200; eight resources and three source-backed actions; export before review 409; inspected offline draft review/export both 200 (1,883-character Markdown); tampered export 400; review of the non-actionable live partial plan 409; unsigned health 403. URL readback remained the same `AWS_IAM`/`BUFFERED` endpoint. These establish API/baseline guard behavior at that revision, not current live-AI success.

The exact earlier live fixture is [fictional-bedrock-request.json](../examples/fictional-bedrock-request.json). Its trace was `search_resources` then `finish_plan`, with two actual model calls: 2,693 input tokens and 265 output tokens in total. Export preserved the synthetic-only label, Bedrock mode, fictional source and warnings that the slot cannot be enrolled in/contacted. It was not rerun on the final schema-aligned artifact; do not treat the prior revision's result as current-artifact live acceptance. No application, message or booking occurred.

Earlier live requests exposed two real contract defects: a redundant budget question despite known zero, and provider-access clarification that unnecessarily blocked an exploratory draft. The fixes reject questions for known inputs and restrict model blocking clarification to three null participant constraints; provider uncertainties remain nonblocking action checks/follow-ups. Unit regressions and independent review preceded deployment. No raised call caps or silent offline fallback was used.

A subsequent broader-goal test used `examples/create-request.json` with only `mode` changed to `bedrock`. On the `f916c959` deployment it returned HTTP 200 `partial`, no actions/questions, after search and two invalid clarification attempts (three model calls; 4,500 input and 347 output tokens). This exposed an outbound contract mismatch: complete profiles were still offered clarification keys that runtime validation rejected.

After deployment of request-local schema alignment (`50dad254`), the same broad request avoided clarification but still returned non-actionable `partial`: search, three inspections, another search, then an invalid `finish_plan` consumed all six tools. The fourth model response was stopped at the tool limit. Usage: four model calls, 8,474 input and 580 output tokens. The result contained no actions and a bounded-stop explanation. Raw invalid arguments were intentionally not logged; the exact invalid finish field is unknown. No higher caps or fabricated fallback were introduced. Further model tuning was stopped for a design/diagnostic review, not declared successful.

This is a bounded engineering smoke test, not a model-quality benchmark, repeatability measurement, real-user acceptance or eligibility assessment. Readiness is **shared authenticated API/offline demo deployed; full AI MVP acceptance incomplete**. Next diagnosis should distinguish trusted finish-validation failure categories without logging model-authored values, reproduce the exact category locally, and review the bounded workflow before any more paid tests. Teammate-session and rendered UI/keyboard/accessibility checks also remain unverified.

## Earlier verification — 5 September 2026

Fresh local run after the independent review fixes:

| Check | Observed result |
|---|---|
| Python 3.12 unittest discovery | 51 tests passed |
| Node interface-state tests | 2 tests passed |
| Real loopback HTTP lifecycle | Create → reject unreviewed export → review → export → reject tampered document |
| Clean-start application health | HTTP 200, version `0.1.0`, synthetic-only, offline default |
| Deterministic deployment package | Built; four explicitly allowlisted files only |
| Staged whitespace check | Passed |
| Independent code review | No remaining Critical/Important findings in local synthetic-MVP scope |
| GitHub initial publication | Private repository, branch `mvp`; remote commit matched `a1de77078c1e587dddb062f86834aea50982f961` |

Deployment artifact SHA-256: `e406e888dceea7b8c26c34a7d946dd71a6c82d22b2e131efbd897a4e4293b164`. A future source change requires a rebuild and a new hash.

Windows PATH's `node` launcher was unusable on the build machine; the bundled Node executable ran the tests successfully. This is an environment issue, not a dependency of the running application. On teammates' machines, use an installed working Node executable only for those tests.

No live AWS write, model call, endpoint authentication test or teammate session test occurred. AWS sign-in remained at the password step; the browser's saved-password suggestion did not appear to automation. No password was extracted, reset, logged or stored in this repository. The 30-minute fallback selected the offline demo and organizer-AWS package, not a personal paid provider.

Automated in-app navigation to the local app returned `net::ERR_BLOCKED_BY_CLIENT`. No bypass was attempted. Static asset/HTTP/state tests passed, but rendered browser behavior, keyboard flow and visual accessibility were not verified. These remain explicit readiness gates.

These earlier observations are historical and superseded by the live deployment checks above. Tests with fake AWS clients prove request construction and guards, not service availability. The remaining acceptance gates are tracked in [READINESS.md](READINESS.md).
