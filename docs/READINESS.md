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
- [x] AWS account-verification denial resolved; bounded Nova calls succeeded. Haiku was not invoked because its model agreement was unavailable; no new agreement was accepted.
- [x] User explicitly approved sanitized source transfer and action-time creation of the scoped execution role/function/authenticated URL. Browser upload then succeeded after session renewal; no restriction was bypassed.
- [x] Uploaded preflight and 58 initial-source tests passed in CloudShell; live budget was checked before creation. Leader caller permissions verified by signed endpoint calls.
- [x] Deployed one `AWS_IAM` Function URL. Unsigned rejection, signed health/resources, offline baseline and review/tamper guards passed. A prior code revision also passed the fictional Bedrock draft-review-export fixture; it was not rerun on the final artifact. See [VERIFICATION.md](VERIFICATION.md).
- [ ] Verify a teammate's organizer session can use that exact endpoint. Do not infer access from the leader's session.
- [x] Actual verified endpoint recorded in team docs; no credentials in repository.
- [ ] Resolve and verify the original broad synthetic goal: after request-local schema alignment, the final run still returned non-actionable `partial` after invalid finish arguments and the tool limit. Stop paid retries; first isolate the trusted validation category and review the bounded workflow. Do not raise caps to conceal the failure.
- [ ] Visually verify browser workflow, keyboard focus, narrow layout and export. Automated in-app navigation to the local URL was blocked by the browser client; HTTP/state tests are not a substitute for rendered UI testing.
- [ ] Operator usability/accessibility, beneficiary agency and comparative value evaluation. Not required to run a synthetic engineering demo, but required before stronger claims.

The shared API/offline engineering demo is live. A fully specified fictional AI create-review-export workflow passed on an earlier revision, but the final deployed revision's broad-goal test failed; full AI MVP acceptance is incomplete. Teammate/browser acceptance remains open: each teammate must test their own organizer session, and the rendered interface still needs visual/keyboard checks. This is not readiness for real participant use. Login silence does not authorize credential extraction, password resets, public unauthenticated access or personal paid-provider substitution.
