# Five-minute demo rehearsal script

## Evidence boundary

Use invented profiles only. Default to the explicitly labelled **Offline demo**. The constrained package is deployed, its API/offline path is verified, and two approved synthetic live smoke cases passed. These do not establish repeatability, general AI reliability or real-provider quality. Teammate-session and rendered-interface verification remain pending. Do not claim real-user acceptance, eligibility decisions, applications, enrolment or messages.

Young adults with disabilities are the beneficiaries. Parents, guardians and educators are the primary operators or supporters. The participant's stated goal, strengths, interests and constraints remain in charge.

## 0:00–0:35 — Problem and promise

**Show:** SimplifyNext home screen.

**Say:**

> A young adult and their supporter may have strengths and a goal, but still face a scattered set of courses, services and eligibility details. SimplifyNext turns those inputs into a small, source-backed set of next steps for them to review together. It supports the conversation; it does not decide eligibility or act for the participant.

## 0:35–1:15 — Load a safe profile

**Show:** Select **Load fictional example**. Keep **Offline demo** selected. Briefly point to the participant goal, strengths, interests, student status, weekly hours and budget.

**Say:**

> This profile is fictional. The young adult is the beneficiary, while a parent, guardian or educator can help operate the tool. We ask only for a few planning inputs. Do not enter names, diagnoses, certificates, contact details or proof documents; the free-text fields are not an automatic personal-data detector.

## 1:15–2:20 — Explore source-backed options

**Show:** Select **Explore next steps**. Point to the offline badge, the small action list, source links, checks and trace.

**Say:**

> Offline mode is a deterministic, tested baseline. It searches the reviewed catalog and returns catalog-backed actions. Each option keeps its source and unresolved provider checks visible. A source link is not a promise of access, suitability or a place; the participant or supporter must verify current details with the provider.

> The trace shows what the workflow did. This output is not being presented as a live model result, and the system never silently relabels offline output as AI.

## 2:20–3:25 — Human review before export

**Show:** Inspect the draft. Point out that export is unavailable before review. Select the review checkbox, choose **Confirm review**, then **Download reviewed plan**.

**Say:**

> The draft cannot be exported as reviewed until a person inspects and explicitly approves this exact plan. Editing the profile discards the displayed approval, so changed inputs require a fresh draft and review. Export creates a Markdown planning artifact only. Nothing is sent, booked, applied for or enrolled in.

## 3:25–4:15 — Meaningful failure

**Show:** Change the supporter goal so it conflicts with the participant's goal, then explore again. Show the clarification state rather than an action plan.

**Say:**

> A supporter can help, but cannot silently override the participant. When their goals conflict, SimplifyNext stops and asks for clarification instead of inventing agreement or producing actions. This failure is meaningful: preserving participant agency matters more than forcing a complete-looking answer.

## 4:15–5:00 — Limits and close

**Show:** Return to the main result or summary screen. Keep the offline label visible.

**Say:**

> What is verified today is the deployed constrained package's shared authenticated API and offline engineering path with source-backed selection, human review and guarded export. A narrow fictional AI workflow passed on an earlier code revision, while a broad AI run on the older free-choice package ended with a non-actionable partial result. On the current package, one broad and one narrow synthetic smoke case each returned a one-action fictional draft in one model call. The narrow case had no questions; the broad case kept an unnecessary provider-access question, which is a quality limitation. Two smoke passes do not establish repeatability, general AI reliability or real-provider quality.

> Teammates must use their own temporary organizer session; access from a teammate's own session has not yet been verified. Browser access for rendered, keyboard and accessibility verification is currently unavailable, so those acceptance checks remain pending. This remains a synthetic prototype, not readiness for real participant use.

> The deployed constrained workflow has the application select up to three catalog records with no known recorded constraint conflict, then gives those detailed records to the model without source-search or resource-inspection tools. The model can only choose valid shortlist IDs or clarify a genuinely unknown participant constraint. Shortlisting is not an eligibility, access or suitability decision. One repair and two model calls are the maximum. Local, independent and deployed API/offline checks pass, and two synthetic live smoke cases passed without repair, retry or fallback. Comparative benefit has not been measured. The evidence is recorded in [VERIFICATION.md](VERIFICATION.md).

## Optional live substitution — not planned and gated

No live substitution is currently planned. If the team later reconsiders it, do not use Bedrock in place of the offline segment unless a later verification record confirms all of these:

- The deployed fixed-flow artifact remains the artifact that passed the approved broad and narrow synthetic smoke cases.
- The presenting teammate has verified the endpoint from their own temporary organizer session.
- Current model access and budget have been checked, and the team has approved a paid live call.
- The exact live path has been rehearsed without changing API, review or safety boundaries.

If every gate passes, change only the mode to **Bedrock**, identify it explicitly as a live model-backed run, and show its actual trace. If the call fails or returns a partial plan, state that result as observed. Never substitute offline output or claim completion. Otherwise, retain the offline script above.

## Rehearsal checks

- Finish within five minutes without skipping the conflicting-goal stop or limitations.
- Keep fictional/synthetic and offline labels visible whenever claimed.
- Inspect sources and the exact draft before review.
- Do not click external application, booking, enrolment or messaging actions; none exist in the MVP.
- Do not claim model quality, outcome improvement, accessibility conformance, provider eligibility or submission readiness.
