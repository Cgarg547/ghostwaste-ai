# GhostWaste AI demo playbook

Use a fresh temporary SQLite path for any recorded demo; never reset a shared database. Load the built-in synthetic scenario, or use the isolated nonzero API fixture in [demo-data.md](../demo-data.md). Say “synthetic,” “modeled,” and “recommendation” out loud whenever those distinctions matter.

## 30-second elevator pitch

Restaurants do not just need to know what is in the fridge—they need to know whether specific batches will be used before their dates under uncertain demand. GhostWaste AI combines dated batch inventory, sales-based demand baselines, recipes, and supplier constraints. It allocates demand first-expiring-first-out, simulates expiry risk with a reproducible seed, and proposes constrained purchases for a manager to review. It is not an autopilot: no order is placed, no food-safety decision is made, and we claim no real-world savings yet.

## Two-minute walkthrough narration

**0:00–0:20 — Problem.** “A restaurant manager may see total stock, but that does not answer which batch expires first, whether predicted menu demand will consume it, or whether a reorder creates new surplus. Doing this by hand across spreadsheets, recipes, and supplier constraints is slow and hard to audit.”

**0:20–0:40 — Inputs.** “This is our synthetic Garden Salad demo. We have dated romaine, tomatoes, feta, and dressing; a recipe; 14 local synthetic daily-sales records; and one explicitly linked supplier. No real restaurant data is shown.”

**0:40–1:05 — Forecast.** “GhostWaste compares simple demand baselines with chronological rolling-origin evaluation, then persists the selected run. Here moving average wins on this tiny fixture. That is transparent baseline forecasting, not a claim of production model accuracy.”

**1:05–1:30 — Risk.** “The workflow turns forecast servings into ingredient demand, then allocates batches FEFO. The Monte Carlo simulation uses 500 seeded demand draws. In the default fixture, modeled expiry waste is zero because high forecast demand consumes the near-expiry stock; that is not observed zero waste. Here is a separate, isolated Spinach fixture with nonzero modeled exposure.”

**1:30–1:50 — Plan and approval.** “The planner respects explicit supplier links, lead times, minimum orders, and storage capacity. It produces a recommendation only. In Action Center, a manager must approve or reject it; the decision is auditable and nothing is purchased.”

**1:50–2:00 — Close.** “The value is an explainable path from inventory facts to a human decision. Next we would validate the workflow in a consented pilot and measure discarded kilograms against a baseline.”

## Detailed 4–5 minute demonstration

| Time | Screen/action | Narration and proof point |
|---|---|---|
| 0:00–0:35 | Title then Overview | “Food waste planning fails when expiry dates, menu demand, and buying constraints live separately. GhostWaste is decision support, not food-safety software.” Point to local/synthetic labeling. |
| 0:35–1:05 | Inventory | Show four batches and use-by dates. “A total inventory number hides whether romaine expires first. Batches preserve received date, use-by, quantity, and supplied cost.” |
| 1:05–1:30 | Data & Settings | Show recipe and supplier association. “A recipe converts forecast servings into kg. Supplier constraints are explicit; no price or supplier is inferred.” |
| 1:30–2:05 | Sales/Forecast + Analytics | Show synthetic 14-day history and selected model metrics. “The system makes one-step predictions at chronological cutoffs, selects lowest MAE, and saves evidence. These metrics are fixture results, not restaurant validation.” |
| 2:05–2:40 | Waste Radar, built-in workflow | Show seed 42, 500 trials, FEFO drivers. “Default Garden Salad has zero modeled waste because modeled demand consumes the expiring stock. This can coexist with stockout risk because the risk model evaluates current inventory, not proposed replenishment.” |
| 2:40–3:20 | Scenario Lab / nonzero fixture | Paste or show `fixture-spinach-A` payload. “With the same seed and 500 trials: 6.023 kg expected modeled waste, p10 5.304, p90 6.795. This is an isolated synthetic calculation; it is not an avoided-waste claim.” |
| 3:20–3:55 | Optimization | “CBC handles the either-zero-or-minimum supplier decision and respects lead time/storage. The output is a planning quantity; it never sends an order.” |
| 3:55–4:25 | Action Center | Create/review an isolated fixture recommendation, approve or reject locally. “The user—not the algorithm—makes the final decision. The local audit records it and inventory stays unchanged.” |
| 4:25–5:00 | Safety/limitations | “We have no partnership, pilot, observed savings, or food-safety certification. The next evidence is a consented pilot with pre-registered baseline measures.” |

## Screen-by-screen recording sequence

1. Start API against a fresh temp DB and start the web app.
2. Load synthetic demo data once. Confirm the loader says existing records were not changed.
3. Capture Overview and Inventory; do not imply an expiry alert is actual waste.
4. Show Data & Settings to establish recipe/supplier provenance.
5. Select the persisted forecast, show Metrics/Evidence, and state the fixture label.
6. Run or restore default workflow with 2026-11-08, 7 days, 500 trials, seed 42.
7. Explicitly explain the default zero-waste result and separate stockout risk.
8. Run the separate nonzero API fixture with the documented fixed payload; display its seed/trials/output.
9. Show Optimization; point to no-order and human-approval copy.
10. Show Action Center and audit history. Close on limitations/roadmap.

## Judge FAQ

**Is this real restaurant data?** No. Bundled records and experiment fixtures are synthetic. The application supports locally entered records, but this submission has no restaurant pilot.

**Did GhostWaste save food or money?** Unknown. The project has no observed savings. “Cost at risk” is remaining modeled quantity times supplied unit cost, not revenue, profit, or measured savings.

**Why call it AI?** It uses data-driven forecasting candidates and stochastic simulation, but the current implementation deliberately uses transparent baselines and does not claim a trained production model. The title should not be interpreted as a claim of validated AI performance.

**What prevents unsafe recommendations?** It never makes a food-safety determination. Use-by is a supplied hard modeling boundary, and a human must follow their own food-safety process.

**Why is modeled waste zero in the default demo?** Under its high forecast-derived demand, FEFO consumes the expiry-window stock. That says nothing about actual restaurant waste; the separate fixture demonstrates nonzero modeled risk.

**Why does the simulation show stockout risk while the planner has a purchase proposal?** The simulation evaluates the current snapshot only; the planner separately evaluates potential replenishment under constraints. It does not assume orders arrive or execute.

**Can it buy from suppliers?** No. Supplier details are local planning inputs. No purchase/order/contact integration exists.

**How is it reproducible?** Scenario records save inputs and seed; the same run/input/seed is restored instead of duplicated. The fixture request and expected result are in [demo-data.md](../demo-data.md).

**What would make this production-ready?** Validated data ingestion and forecasting, a consented pilot, measured impact, secure multi-user infrastructure, authenticated roles, durable storage, integrations, and operational safety review.

## Recording instructions and local-video status

Record at 1080p, use browser zoom so numbers are legible, keep the cursor still while explaining metrics, and show only synthetic data. Record a single clean take, then verify audio, screen legibility, and runtime of 2–3 minutes before uploading. No local video was generated or verified by this submission package; video remains pending user recording and upload.
