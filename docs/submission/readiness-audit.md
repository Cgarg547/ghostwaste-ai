# Arbiter Hacks V1 readiness audit

Audit date: 2026-11-09 (America/Toronto). Source of event requirements: [official Arbiter Hacks V1 rules](https://arbiter-hacks-v1.devpost.com/rules) and [official event page](https://arbiter-hacks-v1.devpost.com/). Recheck both immediately before submission because the event page can change.

## Official requirements verified

The official page states that the Theme Track is for projects that meaningfully reduce, sort, or recycle waste; it scores **Impact 35%, Technical execution 25%, Feasibility 20%, Presentation/demo clarity 20%**. It requires a public repository, a 2–3 minute working demo video uploaded to YouTube or Vimeo, and a written description covering what it does, how it was built, and what is next. Theme submissions additionally require a paragraph naming the waste problem and how success would be measured. Missing repository or video makes a submission ineligible. It allows 1–4 people (including solo), says participants must be students age 13+, excludes companies/professional organizations, and restricts participation in standard excluded territories. The listed deadline is **December 20, 2026, 9:00 PM PST**, which is **December 21, 2026, 12:00 AM EST** in Toronto. One submission may enter one track only.

## Readiness matrix

| Area | Status | Evidence / missing item | Next concrete step | User action? |
|---|---|---|---|---|
| Theme fit | PASS | Core product concerns food-inventory expiry risk; Theme Track measurement paragraph is drafted. | Keep waste impact central in final writeup/video. | No |
| Working local demo | PASS | API, web UI, synthetic loader, fixed fixtures, and demo script documented. | Run against fresh DB before recording. | No |
| Reproducible modeled evidence | PASS | Fixed seeds/inputs and expected fixture values documented; experiment script exists. | Re-run after any engine change. | No |
| Impact claim integrity | PASS | Docs distinguish modeled, hypothetical, observed, unknown; no savings claimed. | Maintain wording in final form/video. | No |
| Technical execution | PASS | Forecast/backtest, FEFO simulation, OR-Tools planner, persisted scenario/approval paths and tests are implemented. | Complete final test/build verification. | No |
| Feasibility | PARTIAL | Local workflow is coherent and human-gated, but no pilot, integrations, security hardening, or deployment exists. | Describe pilot/production gaps honestly. | No |
| Presentation package | PASS | Pitch, walkthroughs, detailed script, FAQ, storyboard, screenshot shortlist, copy, and diagram source are local. | Capture/verify screenshots. | Yes |
| Demo video | FAIL | No video exists or was verified. Required for eligibility. | Record 2–3 minute demo; verify; upload to YouTube/Vimeo; add URL. | Yes |
| Public repository | FAIL | No public repository URL has been provided/verified. Required for eligibility. | Choose license, make approved repo public, verify anonymous access, add URL. | Yes |
| Written fields | PARTIAL | Draft text is ready; team name/credits/repository/video fields remain placeholders. | Fill verified URLs and team details in Devpost. | Yes |
| Student/age/territory eligibility | UNKNOWN | The project files cannot verify people’s age, student status, team membership, or territory. | Each entrant confirms eligibility against official rules. | Yes |
| Team size / track selection | UNKNOWN | Team roster and Devpost registration state are not in the repository. | Confirm 1–4 entrants and Theme Track only. | Yes |
| Deadline/time zone | PASS | Official page lists Dec 20, 2026 at 9:00 PM PST. | Recheck official page and submit early. | Yes |
| License | FAIL | No license file is present. | Obtain team decision/permissions; add license before public release. | Yes |
| Public access | FAIL | No deployed URL is required by the official submission list located, but required public repo/video are absent. | Do not claim a live demo; publish only after approval. | Yes |
| External dependencies | PARTIAL | Open-source dependencies are listed; optional LightGBM is guarded; no paid API used. License/security review not evidenced. | Review dependency licenses and lockfiles before public release. | Yes |

## Submission blockers

1. A required, verified 2–3 minute public YouTube/Vimeo demo URL does not exist.
2. A required, verified public code repository URL does not exist.
3. No repository license has been selected or added.
4. Personal eligibility and team/track registration cannot be proven from project files.

## Recommendation

**Do not submit yet.** The package is locally ready for a credible Theme Track recording and written submission, but eligibility requires the public repository and verified demo video, and the team must first resolve licensing and personal eligibility. Do not deploy, publish, upload, or submit without explicit authorization.
