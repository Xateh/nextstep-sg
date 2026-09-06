# Domain and planner implementation report

Date: 6 September 2026

## Outcome

The current source implementation in `planner.py` provides the first-MVP domain contract, backed by the versioned `catalog.json` and tests in `tests/test_planner.py`.

`create_plan(profile, mode="offline", client=None)` returns `mode`, `status`, `profile`, `actions`, `questions`, and `trace`. `load_catalog()` returns validated catalog records.

This constrained planner was deployed on 6 September 2026 from source revision `aec4030` using the deterministic archive identified below. Its shared API and offline behavior are verified. It has not yet been exercised against live Nova because the first paid broad case was blocked before execution pending explicit approval.

## Current behavior

- Profile validation requires the caller's explicit `synthetic: true` declaration and rejects unknown fields, wrong types, negative or oversized constraints, oversized text, and unsupported modes. It cannot detect real personal information in free text; invented inputs remain an operator responsibility.
- Missing participant goals and differing participant/supporter goals stop before catalog selection or any model/client work. Supporter input never overrides participant preferences.
- Offline planning remains deterministic, explicitly labelled, limited to three catalog-backed actions, and never represented as a model run.
- Known student, weekly-hours, and budget conflicts are removed before ranking. `false` and `0` are known values; `null` remains an unresolved participant constraint.
- Bedrock planning uses the existing deterministic catalog search to build a profile-grounded shortlist of at most three records with no known recorded constraint conflict before client creation. Inclusion does not establish eligibility or suitability. If no resource matches, it returns an honest `partial` result without requiring model configuration, constructing a client, or making a paid call.
- When a shortlist exists, live mode requires an explicit `BEDROCK_MODEL_ID`. Client/request failures remain sanitized `RuntimeError` values and never trigger an offline fallback.
- The model receives the fictional profile and detailed shortlisted catalog records. It cannot search or inspect the wider catalog.
- Outbound tools contain `finish_plan` only for a complete profile. Profiles with a null student-status, weekly-hours, or budget field also receive `clarification`, restricted to exactly the applicable null fields.
- Complete profiles force the named `finish_plan` tool. Profiles with an applicable clarification use Nova's `any` tool choice. Tool schemas are deep-copied per request.
- `finish_plan.resource_ids` is restricted in both its request-local schema and runtime validation to the exact shortlist. Applicable question-key enums are also request-local.
- Every returned action is hydrated from the selected catalog record. Model-authored titles, steps, URLs, checks, questions, identity requests, and external links cannot reach the plan.
- Responses must have `stopReason="tool_use"` and exactly one complete tool call. Malformed, text-only, multiple-tool, truncated, unknown-tool, out-of-shortlist, and invalid-question responses receive at most one repair. The entire plan uses at most two model calls.
- A malformed assistant response is discarded. Trusted repair text is appended to the existing user request, preserving one valid user turn with the original profile and shortlist. A valid tool-error repair retains the normal user/assistant/tool-result sequence.
- Trace and tool-result failures use trusted categories such as `invalid_model_response`, `invalid_tool_arguments`, `invalid_question_keys`, `resource_outside_shortlist`, `unknown_tool`, `no_shortlist`, and `repair_limit`. Raw invalid arguments, invented IDs, tool names, URLs, and identity prompts are not copied into the plan trace.
- Provider access, availability, eligibility, cost, time, and suitability uncertainty remains in catalog-hydrated checks or approved nonblocking follow-up questions. The planner does not make eligibility or suitability decisions and has no application, booking, messaging, payment, or submission tool.
- SDK retries remain disabled and connection/read timeouts remain finite. `boto3` is still lazy, so offline use needs only the Python standard library.

Outbound tool schemas retain only Nova v1-supported top-level fields `type`, `properties`, and `required`, following the [official Amazon Nova tool-definition documentation](https://docs.aws.amazon.com/nova/latest/userguide/tool-use-definition.html). Application validation remains stricter than the schema boundary.

## Catalog

The catalog contains six reviewed public resources and two explicitly fictional demonstration slots. Fictional records identify themselves in titles, providers, summaries, eligibility, checks, and `.invalid` URLs. The office-skills slot requires two weekly hours and costs S$0; the second fictional fixture supports budget filtering.

Reviewed public resources represented:

- SG Enable School-to-Work Transition Programme
- SG Enable Sector-specific Train-and-Place Programme
- CareersFinder and Careers & Skills Passport
- Career Kaki
- Mentra Partner Platform
- Inclusively Retain Navigator

The Sector-specific Train-and-Place record was corrected and checked on 6 September 2026. All other records retain their 5 September 2026 checked date. These dates are per-record review metadata, not a claim that current eligibility, intake, access, fees, availability, accessibility, or suitability is known.

## Verification

The constrained behavior was developed test-first. Red tests demonstrated that the preceding implementation exposed search/inspect tools, lacked shortlist ID enums, accepted an eligible fourth-ranked ID, called the model for an empty shortlist, accepted multiple tool calls, accepted a truncated `max_tokens` response, and created consecutive user turns after malformed output. Narrow production changes made those tests green.

Current results:

- Planner tests: 39 passed.
- Full Python suite: 72 passed.
- JavaScript state tests: 2 passed.
- Independent review: 62 checks passed; no Important findings.
- Both named-finish and any-tool request shapes passed installed botocore parameter validation.
- Deployed artifact readback: `Active`/`Successful`, with matching base64 SHA-256 `Uyi8sz7KsP5+8JlhrfezEXDd0w573AynMAvPIwWJiu8=` for archive SHA-256 `5328bcb33ecab0fe7ef09961adf7b31170ddd30e7bdc0ca7300bcf2305898aef`.
- Post-deployment API checks: unsigned request 403; signed health 200; signed resources 200 with eight records; offline create 200 with three actions; unreviewed export 409; inspected review/export 200 with a 2,139-character document; tampered envelope 400.

Tests cover deterministic shortlist order, detailed shortlist delivery, constraint filtering, request-local ID and question enums, cross-request isolation, named and any tool choice, strict shortlist membership, catalog hydration, participant/supporter preflight, known `false`/`0` versus unknown `null`, trusted questions, sanitized failures, exact response shape and stop reason, multiple/truncated/malformed responses, single-turn malformed repair, two-call repair limit, empty-shortlist no-call behavior, explicit model configuration when needed, and no silent offline fallback.

## Historical live evidence

Historical package `f916` produced the explicitly requested fictional rehearsal draft in two model calls. That case was not rerun on later packages.

Historical package `50dad254` preceded the current deployment. Its older free-choice loop exposed search and inspect tools with four-model/six-tool limits. In the recorded broad-profile run, it performed one search, then three inspections plus another search, followed by an invalid `finish_plan`; the next attempt reached the tool limit. Raw invalid arguments were intentionally not retained, so that exact validation failure remains unknown.

Those results describe older deployed code only. They do not verify or disprove the current constrained deployment. Current live-model behavior remains unknown until the user explicitly approves the proposed bounded broad and narrow synthetic cases. No model call was made during deployment or API/offline verification.

## Remaining boundary

No model-routing layer, database, participant login, or external-action capability was added. Deployment and API/offline checks do not establish AI-plan acceptance or real-participant readiness. Live Nova reliability, teammate access, rendered accessibility, and intended-user evaluation remain separate gates.
