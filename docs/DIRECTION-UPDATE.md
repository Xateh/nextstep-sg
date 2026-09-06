# SWE direction update — 6 September 2026

## Evidence basis

This refresh uses live checks completed at approximately 14:35 SGT on 6 September 2026. The Google document **simplifyNext Hackathon Brainstorm** was last modified on 4 September at 05:55 UTC; revision 1063 was current, after revision 1062. All four tabs were read, comments were empty, and no newer accessible related document was found. This records the latest accessible direction, not proof that no private or inaccessible update exists.

The team-chat snapshot shows one member offering to prepare the pitch deck and two members coding. Frontend/backend ownership remains unresolved. Names, account identifiers, private links and raw chat details are intentionally omitted.

Existing research in [RESEARCH.md](RESEARCH.md) was not newly reviewed for this update. No new evidence, model-performance or user-benefit claim is inferred.

A separate catalog spot-check on 6 September found one material omission: SG Enable's [Sector Train-and-Place page](https://www.sgenable.sg/your-first-stop/training-consultancy/enabling-academy/training/persons-with-disabilities/sector-train-and-place) states that the current intake is closed and describes a full-time commitment. The catalog now surfaces both facts as provider checks and a possible future route, not a current opening or a confirmed fit for a few weekly hours. Exact hours and cost remain unknown because they vary by pathway. The SWDA source could not be freshly read because of an access gate; its earlier checked date remains unchanged. This is a source correction, not evidence that the page itself changed after the previous review.

## Product direction

Young adults with disabilities are the beneficiaries. Parents, guardians and educators are the primary operators. The product should help them start from the young adult's stated strengths and interests, find bounded upskilling or opportunity options, surface unknowns, and review a next-step plan together. Operators support the decision; they do not replace the participant's preferences or make eligibility decisions.

Brainstorm ideas include credential proof, course credits, employer visibility, motivational media and an employer database. These are possible longer-term directions, not mandatory MVP requirements. They add sensitive-data, ranking, rights, integration and validation work that the current deadline does not support.

## Implemented now

- Synthetic-only profile, reviewed catalog, resource search/inspection, explicit plan review and Markdown export.
- Deterministic offline workflow with tested API, validation and review guards.
- Shared `AWS_IAM` Lambda API using the organizer-approved Nova access path. Standard-library validators keep the small contract explicit.
- No applications, messages, bookings, payments, participant database, employer integration or sensitive proof collection.

Current status is a deployed shared API/offline engineering demo. A narrow fictional AI workflow passed on a prior revision but was not rerun on the final artifact. The final broad-goal AI test returned a non-actionable partial result at unchanged tool/model-call limits, with no silent offline fallback. General AI acceptance remains unresolved.

The audience wording, catalog correction and rehearsal script in this refresh were checked locally; 67 Python tests and two JavaScript tests passed after these changes. The catalog correction also appeared in a generated offline plan. These edits have not yet been deployed to the shared endpoint. Rendered-interface, teammate-session and general AI acceptance remain open.

The technical notes favor a predictable LangGraph-style flow, AgentCore, Haiku or Sonnet, and Pydantic. These are proposals, not mandatory requirements. Current Lambda, Nova and standard-library validation are documented deadline- and verified-access substitutions. They are not approval to add new services.

## Proposed smallest next slice

Pending the user's design response, constrain the existing planner rather than expand the stack:

1. Deterministically produce a small catalog shortlist from the validated profile.
2. Give the model only those resource IDs and require it to select valid IDs or return a bounded, validated reason.
3. Hydrate selected actions from catalog facts, preserving the existing schema, API routes, synthetic-data boundary, call limits, exact-document review and export guards.
4. Test broad and constrained fictional cases locally before considering another paid model run.

This proposal adds no service, model, datastore, messaging path, sensitive field or fallback. Implementation remains pending the user's design response or the user's previously authorized 30-minute no-response fallback; neither permits new services or relaxed safeguards.

The fixed pipeline should be described as a **model-assisted workflow**, not a fully autonomous agent. The [official event page](https://hackathon.simplifynext.com/) was read again on 6 September and still describes agents that plan, reason and act. That is a competition-fit risk to state openly, not an acceptance claim. [LangGraph's workflow/agent distinction](https://docs.langchain.com/oss/python/langgraph/workflows-agents) supports this terminology, not hackathon eligibility.

## Priority map

| Priority | Direction | Current mapping | Next action |
|---|---|---|---|
| P0 | Strengths-to-opportunity navigation | Profile, catalog and offline plan exist | Confirm constrained-shortlist design; then fix broad-goal reliability inside current contract |
| P0 | Safe operator-led review | Exact-plan review/export guards exist | Keep participant preference, synthetic-only and no-action boundaries visible in demo |
| P0 | Submission readiness | Engineering demo exists | Resolve frontend/backend ownership; assign deck/video work; run rendered interface and five-minute demo rehearsal |
| P1 | Pitch narrative | Volunteer identified | Build story around beneficiary, operator journey, source-backed shortlist, review and limitations |
| Later | Credential proof, credits and employer visibility | Not implemented | Revisit only with consent, data-rights, fairness and partner requirements |
| Later | Motivational media and employer database | Not implemented | Revisit only after content rights, safety, moderation and maintenance plans |

## Explicit MVP exclusions

Per user direction, do not add messaging, real participant data, sensitive proof uploads, credit-based ranking, model-generated media, employer matching, autonomous applications or new cloud services. Do not imply eligibility, employability, clinical benefit, accessibility conformance or model superiority.

## Submission and coordination facts

- Organizer confirmation received 5 September at 16:34 SGT states the deadline is **7 September 2026, 11:59 AM SGT**, not PM.
- Deck limit: ten content slides, excluding cover and references.
- Video limit: five minutes, per the previously checked 5 September form.
- Today's FAQ question about minimum font size remains unanswered. Do not invent a font rule; use a clearly readable size and update only if the organizer answers.
- The NUS Outlook qualification thread was re-read on 6 September; the 27 and 31 August messages remain the latest relevant organizer mail found by the scoped search. The official event page still requests documentation, prototype, solution video and pitch deck. The form could not be freshly read because access was blocked, so form-specific limits remain dated 5 September.
- Frontend/backend split remains open. Resolve it before parallel edits to avoid duplicated work.

Immediate decision needed: approve, revise or reject the constrained shortlist-to-model-ID-to-review flow. Until then, preserve the deployed API/schema/guards and prepare the verified offline demo, pitch structure and submission assets without expanding scope.
