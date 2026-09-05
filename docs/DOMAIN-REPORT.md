# Domain and planner implementation report

Date: 5 September 2026

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
- Model arguments are validated with exact keys, bounded strings and catalog IDs. One invalid response may be repaired; a second stops with `partial`.
- Model-authored question text is never returned. `finish_plan` and `clarification` accept only allowlisted question keys, which the server hydrates to trusted text; generated links, email addresses, or requests for identity data cannot pass through those tools.
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

Test-first cycle was used. The initial planner suite failed because the module did not exist; the implementation then made it green. A later malformed-tool-ID test failed against the first implementation, followed by a narrow validation fix and a green rerun.

Final commands:

```text
python -m unittest discover -s tests -p test_planner.py -v
python -m py_compile planner.py tests/test_planner.py
```

Result after the constraint and safety review: 24 tests passed. Tests cover catalog provenance and structured constraints, profile validation and upper bounds, missing inputs, supporter conflict, student/time/budget exclusions, offline labelling, source hydration, allowlisted question hydration, rejection of model-authored phishing/identity prompts, non-echoing unknown tools/resources, strict model arguments including unhashable values, malformed response shapes and repair transcripts, global call/tool caps, explicit model configuration, and sanitized live failure.

## Integration notes and remaining checks

- Required profile fields are `strengths`, `interests`, `full_time_student`, `weekly_hours`, `budget_sgd`, and `synthetic`; `goal` may be absent or blank to trigger clarification; `supporter_goal` is optional.
- The API should map domain `ValueError` to HTTP 400 and Bedrock `RuntimeError` to HTTP 503, as agreed with the API owner.
- Live mode requires an explicit `BEDROCK_MODEL_ID` before creating an SDK client. Deployment should set the organizer-approved model or inference-profile ID only after account, region, access, and budget verification; there is no implicit model fallback.
- No live Bedrock request, AWS balance check, access check, deployment, UI test, or external write was performed in this domain task.
- A live smoke test still needs to confirm that the selected model accepts the tool schemas and that the chosen region/inference profile is available within the organizer lease and budget.
