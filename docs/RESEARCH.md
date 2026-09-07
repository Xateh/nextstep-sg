# Why NextStep SG: evidence and existing services

Research snapshot: 5 September 2026. Singapore service localisation was updated on 7 September from the official pages represented in the current catalog. This remains a targeted narrative synthesis, not a statistical meta-analysis, systematic review, market validation or proof of benefit for this prototype. Product capabilities were checked on official pages, not through paid trials. Clinical and employment outcomes were not measured here.

## Ranked anchors

Deadline-fit judgment used weights: delivery 25%, useful outcome 20%, evidence 15%, safety/agency 15%, accessible data 15%, differentiation 5%, demo clarity 5%. Ratings were 1–5; weighted score = sum(weight × rating / 5). Scores are subjective engineering assessments, not probabilities or efficacy measurements.

| Rank | Anchor | Score /100 | Decision |
|---|---|---|---|
| 1 | Supported transition planner | 79 | Selected: complete reviewed artifact, authored catalog, no employer integrations |
| 2 | Narrow interview-practice coach | 72 | Stronger direct intervention evidence, but needs suitable curriculum and supervised validation |
| 3 | Employer-facing matcher | 46 | Needs real partner data, fairness validation and stronger privacy safeguards |
| 4 | Full profiles/courses/credits/matching/media platform | 32 | Too broad for a reliable first slice; unsupported proxies for employability |

This ranking is sensitive to priorities: increasing evidence weight to 40% and lowering delivery/data/differentiation makes coaching first (76 versus planner 68). The planner is the delivery-first choice, not an evidence-based claim of superior outcomes.

Architecture ranking: (1) bounded Python workflow, (2) the same workflow in LangGraph if the team already has working expertise or needs persisted pauses, (3) open-ended multi-agent orchestration. Framework complexity is not a measure of agentic quality. [LangGraph workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents), [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview).

## Singapore services to complement

NextStep SG is a co-planning layer around Singapore's existing service ecosystem, not a replacement for it. The reviewed local services span school transition, sector training, career and skills guidance, employment support and course discovery. The MVP helps a participant and supporter compare a few source-backed possibilities, retain unknowns and decide what to verify next. It does not apply, enrol, determine eligibility or claim a place.

The current agency name used for the career-and-skills service is **Skills and Workforce Development Agency (SWDA)**. MOM's [24 June 2026 press release](https://www.mom.gov.sg/newsroom/press-releases/2026/0624-appointment-of-inaugural-board-for-swda) records the appointment of its inaugural Board. The catalog links CareersFinder and Careers & Skills Passport to the official [MySkillsFuture service page](https://www.myskillsfuture.gov.sg/csp), replacing the previously blocked SWDA career-health page.

| Tool/service | Advertised or published overlap | MVP implication |
|---|---|---|
| [SG Enable School-to-Work](https://www.enablingguide.sg/im-looking-for-disability-support/training-employment/school-to-work-%28s2w%29-transition-programme) | School-mediated transition pathways and support | Prepare questions and link to providers; never promise referral, eligibility or a place |
| [SG Enable Sector Train-and-Place](https://www.sgenable.sg/your-first-stop/training-consultancy/enabling-academy/training/persons-with-disabilities/sector-train-and-place) | Sector-focused training and employment support; current intake was closed when checked | Treat it only as a possible future route. Provider determines eligibility and suitability; confirm intake, full-time commitment, hours and fees |
| [CareersFinder and Careers & Skills Passport](https://www.myskillsfuture.gov.sg/csp) | Career and upskilling recommendations plus a repository for employment, skills, qualifications and certifications | Link to the official service; do not build a duplicate credential store or infer access and suitability |
| [Career Kaki](https://careerkaki.gov.sg/) | Singapore-focused AI career guidance and job-search support | Generic career chat is not a differentiator. Review data choices and guidance with the participant |
| [SG Enable Job Placement and Job Support](https://www.enablingguide.sg/im-looking-for-disability-support/training-employment/job-placement-and-job-support) | Job-readiness assessment, job matching, worksite accessibility assessment and short-term workplace coaching through appointed partners | Complement the official route with preparation and questions; never collect supporting documents or decide eligibility in the demo |
| [Enabling Academy courses](https://www.sgenable.sg/your-first-stop/training-consultancy/enabling-academy/training/persons-with-disabilities/programmes) | Directory of vocational, independent-living and work-readiness courses from listed providers | Let the participant choose interests, then verify the selected provider's intake, schedule, fees, subsidies, access and suitability |

Across these services, exact hours, payable fees, current intakes, access arrangements and accessibility support remain unknown unless a record says otherwise. A catalog listing is not an available place. Providers assess eligibility and suitability.

## International comparators, not local recommendations

These products informed the 5 September landscape review only. Their Singapore availability was not verified, they are not recommended as local resources, and they are not present in the current NextStep SG catalog.

| International comparator | Published overlap | Limited research implication |
|---|---|---|
| [Mentra partner platform](https://www.mentra.com/partners) | Profiles, upskilling, matches and partner progress tracking | Broad platform combinations already exist; do not claim novelty, Singapore availability, integration or access to its data |
| [Inclusively](https://inclusively.com/) | Employer support and resource navigation | Resource-navigation patterns have precedents; Singapore availability, enterprise access and effectiveness remain unverified |
| [SIMmersion youth interview training](https://www.simmersion.com/jobinterviewtraining) | Structured virtual interview practice | Coaching is an alternative product direction; Singapore availability is unverified and proprietary curricula must not be copied |

The differentiation hypothesis is participant-controlled co-planning: a few source-backed options, explicit unknowns, review and a human handoff. Each component has precedents. No claim of market uniqueness, patent novelty, superiority, vendor integration or partnership.

## What research does—and does not—support

- [Wehman et al., 2020](https://pubmed.ncbi.nlm.nih.gov/30825082/): a multisite randomized study of intensive employer-based Project SEARCH plus autism supports reported employment benefits. This is a multi-component supported-employment intervention, not evidence that an AI planner improves employment. Abstract-level appraisal.
- [Smith et al., 2021](https://pubmed.ncbi.nlm.nih.gov/33567883/): supervised virtual interview training for autistic transition-age youth supports the narrow coaching category. It does not validate unrestricted LLM advice or use across all disability groups. Disclosed company/royalty interests and limited full-text access require caution.
- [Fong et al., 2021 review update](https://pmc.ncbi.nlm.nih.gov/articles/PMC8354554/): promising supported-employment/virtual-interview results with a small eligible trial base and risk-of-bias concerns. Do not count trial results again through overlapping reviews.
- [Vocational-interventions review, 2021](https://pubmed.ncbi.nlm.nih.gov/34831840/): evidence varied sharply by population, with no intellectual-disability trials meeting that review's criteria. This is not proof no such research exists; it cautions against generalizing autism or psychosocial-disability findings to everyone.
- [Akemoğlu et al., 2026](https://pubmed.ncbi.nlm.nih.gov/42533285/): AI-intervention review quality was mixed and domains differed from employment planning. AI novelty alone does not establish benefit. Abstract-level appraisal.

Consequences: keep participant-provided strengths/preferences, source checks and chosen supporter involvement. Remove course-credit-based employer visibility, inferred employability scores and motivational media from this MVP. Do not collect diagnoses, certificates, photos, voices or actual youth profiles.

## Validation still needed

Compare directory search, the deterministic template and live bounded AI on identical authored scenarios and catalog records. Measure factual correctness, captured unknowns, constraint violations, time to a reviewable plan and human-rated clarity separately. Current automated tests establish selected engineering behaviors only; they are not that comparative study.

Intended-user testing, consent/safeguarding, accessibility testing and provider/data rights are separate gates before real deployment. No interviews or outreach were performed. Follow [W3C clear-content guidance](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o3-clear-content/) while treating accessibility as something to verify with users, not a property implied by simple styling.
