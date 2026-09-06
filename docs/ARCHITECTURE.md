# First-MVP architecture

Decision: one Python domain/API application, a native HTML/JavaScript interface, and one AWS Lambda function. The shared IAM-authenticated API is deployed; the deterministic offline baseline remains separately labelled. This implements the highest-ranked bounded-workflow direction; it does not implement a marketplace or general autonomous agent.

```text
Teammate browser (no AWS credentials)
       | same-origin HTTP, loopback only
app.py + local AWS signing client
       | HTTPS + SigV4, temporary organizer identity
Lambda Function URL (AWS_IAM)
       | deterministic validation and catalog tools
planner.py ---- reviewed catalog.json
       |
Bedrock Converse (explicit permitted model; bounded calls)
       |
Signed draft -> exact-document review -> Markdown export
```

Without `MVP_API_URL`, the local server runs the same domain/API directly. Without live mode, no model is called. The deployed Lambda package excludes the interface and local signing client. Teammates run that thin interface locally and use the common authenticated endpoint.

## Boundaries

- Domain logic selects resources, not people. It checks known student, time and budget conflicts; unknown facts remain checks for providers.
- Catalog text is team-authored, with source URL, checked date and provenance. Fictional slots are visibly labelled. No crawler, embeddings, participant database or uploaded proof documents.
- The model can search, inspect, ask approved clarification questions and select known IDs. Final actions are hydrated from catalog facts, not model-written URLs or claims.
- Model-requested blocking clarification is restricted to unknown (`null`) student status, weekly hours or budget. `false` and `0` are known values. Provider access/eligibility uncertainty stays in catalog action checks or nonblocking draft questions; it never becomes an eligibility decision. Missing goals and conflicting supporter goals are still handled before model calls.
- Outgoing tool schemas are isolated per request. A complete profile is not offered a clarification tool; otherwise its question enum contains only the participant constraints that are actually unknown. Runtime validation still applies if a model attempts an unavailable question.
- Up to four model requests, six tool calls and one repair. Timeouts and malformed outputs stop honestly. Traces contain observable tool activity, not hidden reasoning.
- The frontend renders text with `textContent`, not model-controlled HTML. No third-party scripts/assets, permissive CORS or credentials in browser storage.
- Temporary AWS IAM access protects the endpoint. The function execution role is distinct from caller permissions and limited to the selected Bedrock model and function logs.
- No tools exist for applications, messages, bookings, payments or submission.

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
