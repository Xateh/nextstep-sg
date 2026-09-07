# NextStep SG — five-minute demo rehearsal

## Evidence boundary

Use invented profiles only. Unset `MVP_API_URL`, restart `python app.py`, confirm service **v0.1.1**, and select **Offline demo**. This is the updated local Singapore version, not the older AWS content. Selecting offline mode without removing a configured forwarding URL still uses that remote catalogue. The shared v0.1.0 API and its two approved synthetic AI smoke cases were verified on 6 September; they do not validate this newer content. Teammate-session and rendered-interface verification remain pending. No eligibility decisions, applications, enrolment or messages.

Young adults with disabilities in Singapore are the beneficiaries. Parents, caregivers, guardians and educators they choose can operate or support the tool. The participant's stated goal, strengths, interests and constraints remain in charge. NextStep SG is an independent SimplifyNext hackathon prototype, not a government service or provider partnership.

## 0:00–0:35 — Problem and promise

**Show:** NextStep SG home screen.

**Say:**

> A young adult and their supporter may have strengths and a goal, but still face a scattered set of courses, services and eligibility details in Singapore. NextStep SG turns those inputs into a few source-backed next steps to review together. It supports the conversation; it does not decide eligibility or act for the participant.

## 0:35–1:15 — Load a safe profile

**Show:** Select **Load fictional example**. Keep **Offline demo** selected. Briefly point to the participant goal, strengths, interests, student status, weekly hours and budget.

**Say:**

> This profile is fictional. The young adult chooses their goal and supporter. We ask only for a few planning inputs. Budget is in Singapore dollars: zero means S$0 available, while blank means not sure. Never enter real names, NRIC/FIN, Singpass details, diagnoses, certificates or contact details. Free-text fields do not automatically detect personal data.

## 1:15–2:20 — Explore source-backed options

**Show:** Select **Explore next steps**. Point to the offline badge, the small action list, source links, checks and trace.

**Say:**

> Offline mode is a deterministic, tested baseline. The catalogue contains six reviewed Singapore public services and two clearly fictional demonstration slots. Each option keeps its source and unresolved checks visible. A listing is not a promise of eligibility, suitability, subsidy or a place. Confirm current intake, hours, fees and support with the provider.

> The trace shows what the workflow did. This output is not being presented as a live model result, and the system never silently relabels offline output as AI.

## 2:20–3:25 — Human review before export

**Show:** Inspect the draft. Point out that export is unavailable before review. Select the review checkbox, choose **Confirm review**, then **Download reviewed plan**.

Point to the three numbered stages and the expiry notice. **Edit profile** returns to the retained inputs and clears approval; **Start over** also clears the local inputs and restores offline mode. Neither deletes already downloaded files. Rehearse actual keyboard focus and downloading on an allowed browser before presenting; simulated interaction tests do not establish that acceptance.

Point out the expiry's Singapore date/time (**SGT**) and the downloaded plan's **S$** budget and explicit unknowns. No citizenship/residency or supporting-document proof is collected. For a separate school-transition rehearsal, use the invented API fixture [singapore-school-transition.json](../examples/singapore-school-transition.json), which keeps unknown hours and budget as `null`.

**Say:**

> The draft cannot be exported as reviewed until a person inspects and explicitly approves this exact plan. Editing the profile discards the displayed approval, so changed inputs require a fresh draft and review. Export creates a Markdown planning artifact only. Nothing is sent, booked, applied for or enrolled in.

## 3:25–4:15 — Meaningful failure

**Show:** Change the supporter goal so it conflicts with the participant's goal, then explore again. Show the clarification state rather than an action plan.

**Say:**

> A supporter can help, but cannot silently override the participant. When their goals conflict, NextStep SG stops and asks for clarification. The young adult stays in control of the plan.

## 4:15–5:00 — Limits and close

**Show:** Return to the main result or summary screen. Keep the offline label visible.

**Say:**

> This Singapore update passes 76 Python and 28 JavaScript checks locally. It keeps source-backed selection, explicit unknowns, human review and guarded export. It is not yet on the shared AWS endpoint. Two earlier fictional AI smoke cases passed on the older deployed content; that is not evidence of reliability, real-provider suitability or benefit from this update.

> Shared AWS access still needs a teammate's own temporary organiser session check. Actual browser, keyboard and accessibility checks remain pending. Singapore content does not mean Singapore hosting: the existing AWS region and inference profile are US-based. This is a synthetic prototype, not readiness for real participant use.

> Model mode remains bounded: the application shortlists at most three records, and the model can choose only from those records or clarify an unknown constraint. It cannot apply, book or message. One repair and two model calls are the maximum; no new paid test was run for this update. Comparative benefit has not been measured. See [VERIFICATION.md](VERIFICATION.md) for the separate local and historical AWS evidence.

## Optional live substitution — not planned and gated

No live substitution is currently planned. If the team later reconsiders it, do not use Bedrock in place of the offline segment unless a later verification record confirms all of these:

- The exact intended content version has an approved deployment and current-artifact acceptance; the historical v0.1.0 smoke passes alone do not validate v0.1.1.
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
