# Demo and readiness checklist

## First local demo

1. Start `python app.py`, open `http://127.0.0.1:8765`, select **Load fictional example**.
2. Keep **Offline demo** selected. Generate a draft; show the mode badge, resource source and unresolved checks.
3. Review and download the plan. Explain that no application or message is sent.
4. Change available hours to `0`. Regenerate; the fictional two-hour slot must not appear.
5. Clear the goal. Regenerate; show the question instead of an invented goal.
6. Enter a different supporter goal. Show participant clarification, not automatic supporter override.
7. Show the trace; offline is a deterministic baseline, not an AI run.

For the agentic demonstration, replace only the mode with Bedrock after access, model and budget verification. Show actual tool decisions and token metadata. If live access fails, label the blocker; do not record offline output as a live AI result.

## Engineering checks

- Unit/domain tests: input bounds; missing goals; supporter conflict; known time/cost/student conflicts; unknown constraints; catalog provenance; model/tool caps; malformed responses; trusted questions.
- API/HTTP tests: real local create-review-export; approval/tamper/expiry/caller binding; cross-origin/header/path boundaries; static assets and response headers.
- Client tests: strict AWS endpoint/route validation; temporary credentials; exact payload signing/hash; no redirects; sanitized errors.
- Deployment tests: deterministic package allowlist; explicit scope/budget gates; account mismatch; existing-resource refusal; read-only preflight; verified account-concurrency fallback; exact US inference-profile permissions; bounded IAM-only function configuration. These are mocks, not live deployment proof.
- JavaScript tests: profile edits discard reviewed envelopes; stale responses cannot restore them; export needs current reviewed actions.

## Open verification gates

- [x] Complete organizer sign-in; verify access to the existing active lease and CloudShell on 6 September 2026.
- [x] Inspect account limits and candidate profile: Lambda total/unreserved concurrency 10; Nova Lite US profile active. These observations do not prove model invocation or deployment permission.
- [ ] Resolve AWS account-verification denial and pass one bounded Nova invocation. Haiku was not invoked because its model agreement was unavailable; no new agreement was accepted.
- [ ] Obtain explicit approval to upload the sanitized project source to organizer CloudShell and create the scoped execution role/function/authenticated URL. Automated source upload was stopped by the approval reviewer; no workaround was attempted.
- [ ] Run the uploaded read-only preflight, recheck the live usable budget immediately before writes, and verify caller permissions.
- [ ] Deploy one `AWS_IAM` Function URL; verify unsigned rejection, signed health/resources, one live synthetic plan, review/export and failure handling.
- [ ] Verify a teammate's organizer session can use that exact endpoint. Do not infer access from the leader's session.
- [ ] Record the actual endpoint privately and in team docs only after verification; no credentials in repository.
- [ ] Visually verify browser workflow, keyboard focus, narrow layout and export. Automated in-app navigation to the local URL was blocked by the browser client; HTTP/state tests are not a substitute for rendered UI testing.
- [ ] Intended-user usability/accessibility and comparative value evaluation. Not required to run a synthetic engineering demo, but required before stronger claims.

The first local software slice is available; the shared cloud/agentic MVP is not release-ready until its AWS and browser gates pass. Login silence does not authorize credential extraction, password resets, public unauthenticated access or personal paid-provider substitution.
