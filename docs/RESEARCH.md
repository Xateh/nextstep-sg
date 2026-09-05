# Why this MVP: evidence and existing tools

Research snapshot: 5 September 2026. This is a targeted narrative synthesis, not a statistical meta-analysis, systematic review, market validation or proof of benefit for this prototype. Product capabilities were checked on official pages, not through paid trials. Clinical and employment outcomes were not measured here.

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

## Existing capabilities to complement

| Tool/service | Advertised or published overlap | MVP implication |
|---|---|---|
| [Mentra partner platform](https://www.mentra.com/partners) | Profiles, upskilling, matches, partner progress tracking | Broad platform combination already exists; do not claim novelty or access to its data |
| [Inclusively](https://inclusively.com/) | Employer support/resource navigation | Learn the resource-navigation pattern; enterprise access and effectiveness remain unverified |
| [SG Enable School-to-Work](https://www.enablingguide.sg/im-looking-for-disability-support/training-employment/school-to-work-%28s2w%29-transition-programme) | School-mediated transition pathways and support | Prepare questions and link to providers; never promise referral, eligibility or a place |
| [SG Enable Sector Train-and-Place](https://www.sgenable.sg/your-first-stop/training-consultancy/enabling-academy/training/persons-with-disabilities/sector-train-and-place) | Training/employment support with published criteria including full-time-student exclusion | Deterministic life-stage checks matter; missing criteria require provider verification |
| [CareersFinder / Careers & Skills Passport](https://www.swda.gov.sg/about-swda/career-health-individuals) | Career/upskilling recommendations and credentials | Link out; no new credential-verification system |
| [Career Kaki](https://careerkaki.gov.sg/) | Singapore-focused conversational career guidance | Generic career chat is not enough differentiation |
| [SIMmersion youth interview training](https://www.simmersion.com/jobinterviewtraining) | Structured virtual interview practice | Coaching is a real alternative; do not copy proprietary curricula |

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
