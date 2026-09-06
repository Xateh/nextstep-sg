# Domain and planner implementation report

Date: 5 September 2026

Last domain fix: 6 September 2026

## Outcome

The first MVP domain slice is implemented in `planner.py`, backed by a versioned `catalog.json` and standard-library tests in `tests/test_planner.py`.

`create_plan(profile, mode="offline", client=None)` returns the planned contract fields: `mode`, `status`, `profile`, `actions`, `questions`, and `trace`. `load_catalog()` returns validated catalog records.

## Behavior implemented

- Profile validation rejects non-synthetic data, unknown fields, wrong types, negative integer constraints, oversized text, and unsupported modes with `ValueError`.
- A missing goal or differing participant/supporter goals returns `needs_clarification` without choosing for the participant.
- Offline planning is deterministic, visibly labelled `offline fixture mode`, limited to three catalog-backed actions, and does not claim a model run.
- A full-time student cannot receive the catalog programme whose published general criteria exclude full-time students. The result retains a visible question about future or school-mediated routes.
- Catalog records carry structured `required_weekly_hours` and `cost_sgd` constraints. Known time or budget conflicts are filtered in both offline selection and Bedrock `finish_plan`; unknown real-resource values remain visible checks rather than claimed matches.
- Missing weekly availability or budget produces a clarification question. Profile input is capped at 168 weekly hours and S$100,000.
- Every action's ID, title, next step, URL, and checks are hydrated from the catalog. Bedrock may select resource IDs but cannot supply these facts.
- Bedrock Converse uses only four allowlisted tools: `search_resources`, `inspect_resource`, `finish_plan`, and `clarification`. Search is local catalog search; there is no web, messaging, submission, execution, or arbitrary-URL tool.
- Outbound tool-input schemas use only the Nova v1-supported top-level fields `type`, `properties`, and `required`, following the [official Amazon Nova tool-definition documentation](https://docs.aws.amazon.com/nova/latest/userguide/tool-use-definition.html). Exact-key and type checks remain enforced by application code, including rejection of unknown arguments.
- Model arguments are validated with exact keys, bounded strings and catalog IDs. One invalid response may be repaired; a second stops with `partial`.
- Model-authored question text is never returned. `finish_plan` and `clarification` accept only allowlisted question keys, which the server hydrates to trusted text; generated links, email addresses, or requests for identity data cannot pass through those tools.
- Constraint question keys are accepted only when the corresponding profile value is `null`. Boolean `false` and numeric `0` are treated as known values in both `clarification` and `finish_plan`, preventing contradictory questions after a live model call.
- `clarification` exposes only the three null-capable participant inputs: student status, weekly hours, and budget. Provider access, participant priority, and supporter preference remain available as nonblocking `finish_plan` follow-ups for compatibility; catalog-hydrated action checks retain provider uncertainty.
- Outbound tool specs are request-local. Complete profiles omit `clarification`; incomplete profiles expose exactly the keys whose mapped values are `null`. The global specs are deep-copied, so one profile cannot change another request's schema. Search, inspect, finish, runtime validation, and execution limits are unchanged.
- Unknown tool names and unknown resource IDs are recorded only as generic failure types, so invented or adversarial labels are not echoed into the plan trace.
- Limits are global per plan: four model requests and six tool calls. Reaching either limit returns an honest `partial` result.
- Bedrock client/request failures raise a sanitized `RuntimeError("Bedrock planning request failed")`. They never fall back to offline output. Client construction failures raise `RuntimeError("Bedrock client is unavailable")`.
- Malformed Converse response, content, tool-use, usage, and metrics shapes stop through a bounded `partial` result or sanitized `RuntimeError`, never an unhandled shape-specific exception. Invalid assistant blocks are not retained in the repair transcript.
- When the module creates the AWS client, SDK retries are disabled and connection/read timeouts are finite. `boto3` remains a lazy runtime dependency, so offline mode and tests need only the Python standard library.

## Catalog

The catalog contains six reviewed public records drawn from the reviewed MVP research plus two explicitly fictional demonstration slots. Fictional records say so in their titles, providers, summaries, eligibility, checks, and `.invalid` URLs. The office-skills slot requires two weekly hours and costs S$0; a second paid fixture makes budget filtering executable in tests. Public summaries are short original summaries; no proprietary text was copied.

Reviewed links represented:

- SG Enable School-to-Work Transition Programme
- SG Enable Sector-specific Train-and-Place Programme
- CareersFinder and Careers & Skills Passport
- Career Kaki
- Mentra Partner Platform
- Inclusively Retain Navigator

Catalog facts were checked for this prototype on 5 September 2026. They must be refreshed before real-world use. The catalog and planner do not determine eligibility, availability, accessibility, fees, or suitability.

## Verification

Test-first cycle was used. The initial planner suite failed because the module did not exist; the implementation then made it green. Later malformed-tool-ID and Nova-schema tests failed against their preceding implementations, followed by narrow fixes and green reruns. One live regression was reproduced with Nova-shaped `clarification` and `finish_plan` calls: known `budget_sgd=0`, `weekly_hours=0`, and `full_time_student=false` were incorrectly accepted as unanswered. The shared applicability guard fixed both tool paths while retaining questions for `null` values. Package `f916` then produced the requested fictional rehearsal draft in two model calls, before the final dynamic-schema package; that case has not been rerun against the final package. The original broad office-skills profile still returned `partial` under the static schema after Nova twice selected clarification keys that runtime validation rejected. Red tests captured that schema/validator mismatch; request-local omission or narrowing made them green.

The final dynamic-schema package, identified by deployment prefix `50dad254`, was deployed and tested with the broad profile. It still returned `partial` with no actions. The trace recorded one search, then three resource inspections plus another search for five tool calls total, followed by an invalid `finish_plan` as the sixth tool call. On the fourth model request, the application stopped at `tool_limit` before executing a seventh tool. The trace intentionally does not store raw invalid arguments, so the exact `finish_plan` validation failure is unknown. The clarification loop was removed and all configured call, tool, validation, and no-fallback guards behaved as designed, but general live-AI acceptance remains unresolved.

Final commands:

```text
python -m unittest discover -s tests -p test_planner.py -v
python -m py_compile planner.py tests/test_planner.py
```

Result after request-local schema alignment: 34 tests passed. Tests cover catalog provenance and structured constraints, profile validation and upper bounds, missing inputs, supporter conflict, student/time/budget exclusions, offline labelling, source hydration, Nova-compatible outbound tool schemas, complete-profile clarification omission, exact null-key subsets, cross-request schema isolation, broad-profile schema-aware completion, clarification-versus-finish key separation, exact search-repair-finish behavior for fictional rehearsal, retained provider checks, allowlisted and profile-applicable question hydration, known `false`/`0` versus unknown `null`, rejection of model-authored phishing/identity prompts, non-echoing unknown tools/resources, strict model arguments including unknown and unhashable values, malformed response shapes and repair transcripts, global call/tool caps, explicit model configuration, and sanitized live failure.

## Integration notes and remaining checks

- Required profile fields are `strengths`, `interests`, `full_time_student`, `weekly_hours`, `budget_sgd`, and `synthetic`; `goal` may be absent or blank to trigger clarification; `supporter_goal` is optional.
- The API should map domain `ValueError` to HTTP 400 and Bedrock `RuntimeError` to HTTP 503, as agreed with the API owner.
- Live mode requires an explicit `BEDROCK_MODEL_ID` before creating an SDK client. Deployment should set the organizer-approved model or inference-profile ID only after account, region, access, and budget verification; there is no implicit model fallback.
- No model-routing layer was added. The domain implementation work did not invoke a live model; the deployment owner performed the bounded Nova Lite deployment checks described above.
- Package and runtime guards are complete for the current MVP. General AI-plan acceptance is not established: the explicit fictional case passed on pre-final package `f916`, while the broad case remained partial on final dynamic package `50dad254`.
- Do not raise the four-model or six-tool caps to conceal this failure. The next diagnostic, if work resumes, is to record a bounded trusted validation-failure category without retaining raw model arguments, then reproduce that category with a captured test fixture before considering any code change or another live request.
