# Verification record — 6 September 2026

## Current verification

Fresh root verification after the deployment-preflight and Nova-schema changes: **58 Python tests and 2 interface-state tests passed**. Independent review of the changed deployment and planner paths reported no actionable Important findings. Whitespace checks passed. Tests still use test doubles for cloud operations.

Current deterministic Lambda archive SHA-256: `8715edab2cd8c2985966052c3d25fb4dc46a787bc5a7201803cefa57589fa336`. The archive contains only the same four allowlisted application files.

Live observations from the signed-in organizer account on 6 September, before 06:50 SGT:

- Existing organizer lease active; portal displayed $0 spent before the single bounded model probe. Retain the organizer's previously documented US$20 usable cap despite the portal's larger displayed lease allocation. The display is not a real-time billing guarantee.
- Organizer console and CloudShell work without extracting credentials. Target region selected: `us-east-1`.
- Lambda account limits: total concurrency 10, unreserved 10, function count 0. Default reserved-concurrency-one deployment cannot use this quota; the explicit verified account-ceiling mode is prepared. It is not a per-function-one or monetary cap.
- `us.amazon.nova-lite-v1:0` profile reported active across the three allowed US destinations. One synthetic Converse request, capped at 8 output tokens, returned `AccessDeniedException`: the account is currently being verified. No model answer or usage result was returned. AWS's error says verification normally takes less than two hours; that is not a promised completion time.
- Haiku's US profile was active, but its access agreement reported `NOT_AVAILABLE`. No Haiku invocation, new agreement acceptance or provider substitution occurred.
- Automated upload of the reviewed preflight script to organizer CloudShell was blocked by the approval reviewer because exporting that private source file to that destination needs explicit approval. The upload was not bypassed. The complete deployment script has therefore **not run in CloudShell**, even in preflight mode.
- No IAM role, Lambda function or Function URL was created. Deployment write permissions, endpoint authentication and a teammate session remain unverified.

Readiness remains **local synthetic demo available; shared cloud/agentic MVP incomplete**. The current blockers are AWS account verification and explicit approval for source upload/resource creation. Browser rendering remains unverified for the reason below.

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

Tests with fake AWS clients prove selected request construction and guard behavior, not service availability or platform acceptance. The guarded deployment helper is **prepared, not deployed**. The first shared cloud MVP remains incomplete until the open gates in [READINESS.md](READINESS.md) pass.
