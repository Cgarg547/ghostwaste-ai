# Arbiter Hacks V1 submission package

## Project description

**GhostWaste AI** is a local-first planning prototype that helps restaurant managers see which perishable inventory batches may expire before forecast demand consumes them. It combines dated inventory, local sales, recipes, supplier constraints, FEFO allocation, seeded Monte Carlo simulation, and OR-Tools planning—then requires a person to review every proposal. It never automatically orders food or makes food-safety decisions.

## Problem statement

Restaurants make purchasing and prep decisions while demand changes and ingredients expire at different times. A static inventory count cannot show whether a specific batch is likely to be used before its supplied use-by date, whether demand uncertainty changes that risk, or how purchasing constraints trade off shortage and surplus. Manual spreadsheet work is fragmented, hard to reproduce, and easy to over-trust.

## Solution summary

GhostWaste turns local batch, sales, recipe, and supplier records into an auditable planning sequence: evaluate a short-horizon demand baseline; convert servings to ingredient kg; allocate demand FEFO; simulate expiry-window outcomes with an explicit seed; prepare a constrained purchase proposal; and route it to a manager for a final local decision. Outputs are labeled as observed inputs, modeled estimates, or unknown—not as measured savings.

## Technical implementation

Next.js 16 provides the operational interface. FastAPI/Pydantic supplies typed endpoints. SQLAlchemy + SQLite locally persist inventory, sales, recipes, suppliers, forecasts, scenarios, recommendations, and audit events. Forecast candidates use leakage-free rolling-origin evaluation; simulation uses reproducible NumPy draws; OR-Tools uses GLOP for a single item and CBC mixed-integer planning for multi-item supplier minimums. See [architecture](../architecture.md) and [methodology](../methodology.md).

## Impact explanation and measurement paragraph (Theme Track)

GhostWaste targets preventable food-inventory expiry exposure by making the relationship among batch dates, expected demand, and purchase constraints visible before a manager acts. In a future consented pilot, success would be measured as kilograms and cost of discarded inventory per sales volume against a pre-registered baseline, alongside stockouts, adoption, and forecast calibration. This submission reports no observed waste reduction or savings: its outputs are synthetic modeled estimates only.

## Feasibility explanation

The prototype is feasible as a decision-support layer because it relies on ordinary restaurant records—inventory batches, daily sales, recipes, and supplier constraints—and keeps humans in control. Its current local design intentionally excludes automatic procurement. Deploying responsibly requires authenticated access, durable storage, validated integrations, staff workflow testing, and a consented measurement pilot.

## Feature list

- Dated batch inventory and expiry attention
- CSV validation/import and formula-safe export
- Sales history, recipes, and ingredient demand translation
- Backtested baseline forecasting with transparent metrics
- Deterministic FEFO expiry exposure
- Seeded Monte Carlo risk simulation with p10/p90 and stockout probability
- Multi-ingredient OR-Tools constrained planning
- Persisted scenarios, approval/rejection workflow, and audit events
- Explicit synthetic/provenance and limitation labels

## Credits and acknowledgements

Built with Next.js, React, FastAPI, Pydantic, SQLAlchemy, SQLite, NumPy, OR-Tools, Alembic, and pytest. Optional LightGBM support is guarded in code but is not required for the demo. All demo data was authored as synthetic project fixtures; no restaurant data, partner data, or paid API is used. Add team-member names, roles, and any permitted asset/source attributions before submission.

## Architecture illustration source

The editable Mermaid source is in [architecture.md](../architecture.md). Render it locally in a Markdown viewer or export it to a PNG/SVG before upload if the submission form needs an image.

## Screenshot shortlist

1. Overview dashboard with synthetic/demo label and expiry attention.
2. Forecast/Evidence page with selected baseline and model comparison.
3. Waste Radar with seed, trials, zero-risk explanation **or** nonzero fixture results labeled modeled.
4. Optimization page showing supplier constraints and “no orders executed.”
5. Action Center showing a pending review, then an audit-recorded decision.

Do not use screenshots that imply live restaurant usage, safety certification, or actual savings.

## Suggested 2–3 minute video storyboard

| Time | Shot | Message |
|---|---|---|
| 0:00–0:20 | Title + dashboard | The problem is batch expiry under uncertain demand, not just counting stock. |
| 0:20–0:45 | Inventory / recipe / sales | Show the synthetic Garden Salad inputs and explain they are synthetic. |
| 0:45–1:15 | Forecast/Evidence | Forecast is selected by chronological baseline evaluation; it is not a claimed production AI accuracy result. |
| 1:15–1:45 | Waste Radar + nonzero fixture | FEFO plus seeded Monte Carlo exposes modeled risk; show seed/trials and label modeled, not observed. |
| 1:45–2:15 | Optimization | Constraints determine a recommendation; no order is sent. |
| 2:15–2:40 | Action Center | A manager accepts/rejects locally; decision is audited. |
| 2:40–3:00 | Limitations / close | Explain no pilots/savings claim, then how a real pilot would measure impact. |

## Submission checklist

- [ ] Confirm each team member is a student, age 13+, in an eligible territory, and not entering as a company/professional organization.
- [ ] Confirm team has 1–4 members and selects only Theme Track: Rethinking Waste.
- [ ] Add a license and confirm every dependency/asset license is acceptable.
- [ ] Run tests and web build from a clean environment; capture actual output/date.
- [ ] Record and verify a 2–3 minute working demo video; upload to YouTube/Vimeo and obtain a public URL.
- [ ] Create a public code repository and verify clone/read access without credentials.
- [ ] Add the public repository URL, video URL, team credits, and any required profile data in Devpost.
- [ ] Paste the description and Theme Track measurement paragraph above; proofread claims.
- [ ] Recheck official rules and deadline immediately before submitting.

## Video status

**Pending.** No video was created or verified by this package. The storyboard, narration, and recording instructions are in [README.md](README.md).
