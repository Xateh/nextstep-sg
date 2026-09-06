# Demo and readiness checklist

Primary demo operators are parents, guardians and educators supporting young adults with disabilities. The young adult is the beneficiary, and their stated goals and preferences control the plan; supporter input remains context and never overrides them. Continue to use invented profiles only.

## First local demo

1. Start `python app.py`, open `http://127.0.0.1:8765`, select **Load fictional example**.
2. Keep **Offline demo** selected. Generate a draft; show the mode badge, resource source and unresolved checks.
3. Review and download the plan. Explain that no application or message is sent.
4. Change available hours to `0`. Regenerate; the fictional two-hour slot must not appear.
5. Clear the goal. Regenerate; show the question instead of an invented goal.
6. Enter a different supporter goal. Show participant clarification, not automatic supporter override.
7. Show the trace; offline is a deterministic baseline, not an AI run.

For the model-assisted demonstration, replace only the mode with Bedrock after current-artifact acceptance, access, model and budget verification. Show actual tool decisions and token metadata. If live access fails, label the blocker; do not record offline output as a live AI result.

## Engineering checks

- Unit/domain tests: input bounds; missing goals; supporter conflict; known time/cost/student conflicts; unknown constraints; catalog provenance; model/tool caps; malformed responses; trusted questions.
- API/HTTP tests: real local create-review-export; approval/tamper/expiry/caller binding; cross-origin/header/path boundaries; static assets and response headers.
- Client tests: strict AWS endpoint/route validation; temporary credentials; exact payload signing/hash; no redirects; sanitized errors.
- Deployment tests: deterministic package allowlist; explicit scope/budget gates; account mismatch; existing-resource refusal; read-only preflight; verified account-concurrency fallback; exact US inference-profile permissions; bounded IAM-only function configuration. These are mocks, not live deployment proof.
- JavaScript tests: profile edits discard reviewed envelopes; stale responses cannot restore them; export needs current reviewed actions.

## Open verification gates

- [x] Implement and locally verify the constrained source: 72 Python tests and two interface-state tests passed. The extracted four-file package imports and creates a guarded offline draft without model calls.
- [x] Deploy the reviewed `5328bcb3...` package with a revision-guarded code-only update. AWS readback is `Active` / `Successful`; same IAM-authenticated URL and unchanged environment/signing-key configuration.
- [x] Restore the in-app browser and CloudShell session; verify current signed routes, offline create-review-export, unsigned rejection and tamper/review guards on the new package.
- [x] Obtain explicit approval and run one broad and one narrow synthetic Nova Lite request on the current artifact. Both passed once, with one model call each and no repairs/retries/fallback. The earlier approval blocker is resolved; its rejected attempt made no model call. These results do not authorize extra paid calls or establish general reliability.

- [x] Complete organizer sign-in; verify access to the existing active lease and CloudShell on 6 September 2026.
- [x] Inspect account limits and candidate profile: Lambda total/unreserved concurrency 10; Nova Lite US profile active. These observations do not prove model invocation or deployment permission.
- [x] AWS account-verification denial resolved; bounded Nova calls succeeded. Haiku was not invoked because its model agreement was unavailable; no new agreement was accepted.
- [x] User explicitly approved sanitized source transfer and action-time creation of the scoped execution role/function/authenticated URL. Browser upload then succeeded after session renewal; no restriction was bypassed.
- [x] Uploaded preflight and 58 initial-source tests passed in CloudShell; live budget was checked before creation. Leader caller permissions verified by signed endpoint calls.
- [x] Deployed one `AWS_IAM` Function URL. Unsigned rejection, signed health/resources and offline baseline passed. Current broad and narrow Bedrock drafts each passed unreviewed rejection, inspected review/export and tamper rejection. See [VERIFICATION.md](VERIFICATION.md).
- [ ] Verify a teammate's organizer session can use that exact endpoint. Do not infer access from the leader's session.
- [x] Actual verified endpoint recorded in team docs; no credentials in repository.
- [x] Verify the original broad synthetic goal on the new artifact. It returned a Bedrock draft in one call, selecting the fictional taster and one permitted but unnecessary provider-access question. The historical `50dad254...` failure remains historical; this single current pass is not a measured reliability comparison.
- [ ] Evaluate repeatability and real-resource recommendation quality before general-planner claims. Both approved live cases selected only a fictional resource; real-provider selection was not validated. No additional paid evaluation is authorized by the completed two-case check.
- [ ] Visually verify browser workflow, keyboard focus, narrow layout and export. Automated in-app navigation to the local URL was blocked by the browser client; HTTP/state tests are not a substitute for rendered UI testing.
- [ ] Operator usability/accessibility, beneficiary agency and comparative value evaluation. Not required to run a synthetic engineering demo, but required before stronger claims.

The constrained shared API and its two-case synthetic AI smoke path are verified. Full team-facing MVP acceptance remains incomplete: each teammate must test their own organizer session, and the rendered interface still needs visual/keyboard checks. Two single-run fictional selections do not establish general reliability or real-provider suitability. This is not readiness for real participant use. Login silence does not authorize credential extraction, password resets, public unauthenticated access or personal paid-provider substitution.
