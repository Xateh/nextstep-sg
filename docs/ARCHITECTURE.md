# First-MVP architecture

## Singapore content revision — 7 September 2026

**NextStep SG** is the supported transition planner for Singapore learning and work. Local **v0.1.1** uses six reviewed Singapore public services and two fictional Singapore slots, S$ amounts and dated SGT expiry notices. Young adults retain agency; parents, caregivers, guardians and educators are chosen supporters. International tools remain research comparators, not catalogue recommendations.

The architecture, JSON contracts, catalogue schema and dependencies are unchanged. The private repository is [Xateh/nextstep-sg](https://github.com/Xateh/nextstep-sg); legacy technical identifiers are retained for compatibility. AWS still serves **v0.1.0 / `aec4030`**; this content update is not deployed. Unset `MVP_API_URL` and restart to run the latest local version. The existing US region and inference profile are unchanged, with no Singapore data-residency claim. Current local evidence and separate live/browser gates are in [VERIFICATION.md](VERIFICATION.md).

## Existing architecture and 6 September deployment evidence

Decision: one Python domain/API application, a native HTML/JavaScript interface, and one AWS Lambda function. The shared IAM-authenticated API is deployed; the deterministic offline baseline remains separately labelled. This implements the highest-ranked bounded-workflow direction; it does not implement a marketplace or general autonomous agent.

**The diagram below describes the constrained implementation deployed on 6 September 2026. Its API and offline path are verified, and two approved synthetic live smoke cases passed. This does not establish general model reliability or real-provider plan quality. Teammate-session access remains unverified; rendered-browser verification remains blocked.**

```text
Teammate browser (no AWS credentials)
       | same-origin HTTP, loopback only
app.py + local AWS signing client
       | HTTPS + SigV4, temporary organizer identity
Lambda Function URL (AWS_IAM)
       | deterministic validation and recorded-constraint filtering
planner.py ---- reviewed catalog.json ---- top 3 detailed constraint-filtered records
       |                                      |
       +-------- Bedrock Converse ------------+
                  finish or null-field clarification
       |
Signed draft -> exact-document review -> Markdown export
```

Without `MVP_API_URL`, the local server runs the same domain/API directly. Without live mode, no model is called. The deployed Lambda package excludes the interface and local signing client. Teammates run that thin interface locally and use the common authenticated endpoint.

## Boundaries

- Primary operators are parents, guardians and educators supporting young adults with disabilities. The young adult is the beneficiary; their stated goals and preferences control the plan, while supporter input remains non-overriding context.
- Domain logic selects resources, not people. It checks known student, time and budget conflicts; unknown facts remain checks for providers.
- Catalog text is team-authored, with source URL, checked date and provenance. Fictional slots are visibly labelled. No crawler, embeddings, participant database or uploaded proof documents.
- The application deterministically builds up to three catalog candidates with no known recorded constraint conflict and supplies their detailed records to the model. This is not an eligibility, access or suitability determination. The model can finish with shortlist IDs or ask one approved clarification about a genuinely unknown participant constraint. No model-visible source-search or resource-inspection tools exist in this scope, and it cannot select an ID outside the shortlist. Final actions are hydrated from catalog facts, not model-written URLs or claims.
- Model-requested blocking clarification is restricted to unknown (`null`) student status, weekly hours or budget. `false` and `0` are known values. Provider access/eligibility uncertainty stays in catalog action checks or nonblocking draft questions; it never becomes an eligibility decision. Missing goals and conflicting supporter goals are still handled before model calls.
- A complete profile is not offered a clarification tool; otherwise its question enum contains only participant constraints that are actually `null`. Runtime validation rejects unavailable questions and non-shortlist IDs.
- The constrained planner allows one initial model call and at most one repair call. Timeouts, malformed outputs and a failed repair stop honestly. Traces contain observable workflow activity, not hidden reasoning.
- The frontend renders text with `textContent`, not model-controlled HTML. No third-party scripts/assets, permissive CORS or credentials in browser storage.
- Temporary AWS IAM access protects the endpoint. The function execution role is distinct from caller permissions and limited to the selected Bedrock model and function logs.
- No tools exist for applications, messages, bookings, payments or submission.

## Fixed model-assisted flow — deployed; bounded smoke verified

The implemented change keeps the API, request/response schema and review/export contract unchanged. Application code validates the profile, removes resources with known recorded constraint conflicts, ranks up to three remaining candidates, and passes those full records to one model call. Remaining on the shortlist does not establish provider eligibility, access or suitability. The model may return valid shortlist IDs or request clarification only for null student status, weekly hours or budget. One validation repair is allowed, for two model calls maximum.

Fresh local verification passed 72 Python tests and two JavaScript tests. The deterministic four-file archive has SHA-256 `5328bcb33ecab0fe7ef09961adf7b31170ddd30e7bdc0ca7300bcf2305898aef` and base64 SHA-256 `Uyi8sz7KsP5+8JlhrfezEXDd0w573AynMAvPIwWJiu8=`. It was deployed from source revision `aec4030` through the existing CloudShell code-only revision guard. AWS readback reported `Active`/`Successful` with matching base64 hash; the `AWS_IAM` endpoint, buffered invoke mode, function configuration and signing-key configuration were unchanged. Independent review found no Important findings; 39 planner checks, 62 additional checks and tool-choice botocore validation passed. Full evidence is in [VERIFICATION.md](VERIFICATION.md).

Post-deployment checks passed unsigned rejection, signed health and eight-resource listing, three-action offline creation, unreviewed-export rejection, inspected review/export and tamper rejection. After explicit approval, two synthetic Bedrock smoke cases ran at approximately 20:40–20:46 SGT against the same deployed artifact and retained the exact `false`, `3` and `0` constraints. Both returned HTTP 200 `bedrock` drafts in one model call with the fictional office-skills slot as the only action; the narrow case had no questions. The broad case retained the permitted nonblocking question “Which current access requirements should be confirmed with the provider?”, which was unnecessary for a fictional slot and remains a quality limitation. Both review/export guard sequences passed, including tamper rejection.

Across both smoke cases, Bedrock used 2,896 input tokens, 69 output tokens and 2,965 total tokens, with no repair, retry or fallback. These are two synthetic smoke passes only, not evidence of repeatability, general reliability, real-provider quality, benefit, eligibility, suitability or full-MVP readiness. No more model calls are planned. Keep the demo offline until the presenting teammate and rendered-interface rehearsal gates pass.

## Deliberate refinements from the research skeleton

Standard-library validators replace Pydantic for this small contract; tests guard the invariants. Native client-side rendering replaces a framework without introducing a build/runtime dependency. Boto3 is the only installed Python dependency for AWS use; offline execution is dependency-free.

Signed, expiring document snapshots replace a mutable session-revision store. This keeps Lambda stateless and avoids adding a database solely for the demo. UI edits discard the active approval, and signatures prevent altered content from being exported as reviewed. Older retained reviewed snapshots remain valid until expiry: this does **not** enforce server-side revocation of superseded revisions. Add an authenticated participant/revision store before claiming that guarantee or supporting real multi-user records.

The organizer's shared AWS identity is a team development boundary, not a production participant authentication system. The synthetic flag does not itself detect sensitive data. The local HTTP server is loopback-only and must not be deployed publicly.

## Deferred, with explicit triggers

- LangGraph/checkpointing: only if a real persisted pause/resume workflow is required or the team already has working code.
- AgentCore hosting: only if Lambda limits block the demonstrated workflow; not needed for architecture branding.
- Database, participant login and revision revocation: before real participant use, cross-device state or revocation guarantees.
- Retrieval index: only after the reviewed catalog outgrows simple search and retrieval quality is measured.
- Broader model routing: only after one permitted model passes the synthetic evaluation and cost is measured.

AWS describes fixed-function HTTPS invocation and IAM signing in [Function URL invocation](https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html). Bedrock's [Converse interface](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html) supports the bounded model/tool exchange. Actual leader-session access and the live synthetic workflow are recorded separately in [VERIFICATION.md](VERIFICATION.md); teammate-session access is not inferred from platform documentation.
