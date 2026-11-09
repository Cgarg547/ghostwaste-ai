# 2–3 minute judge demo script

1. **0:00–0:20 — Problem.** “Restaurants see stock totals, but not whether a particular batch will expire before forecast demand consumes it. This demo uses synthetic local data.”
2. **0:20–0:50 — Inputs.** Load demo data; show dated inventory, recipe mapping and sales-derived forecast.
3. **0:50–1:20 — Risk.** Open Waste Radar and Use-First Planner. Explain FEFO, the explicit use-by boundary and that expired stock is never recommended.
4. **1:20–1:50 — Decision support.** Open Supplier Intelligence first: select an ingredient and explain on-time, price, lead-time, and minimum-order trade-offs. Then open Scenario Studio and Impact Studio. Change an assumption, run the seeded model, and point out results are modeled—not observed savings.
5. **1:50–2:20 — Human control.** Show Optimization and Action Center. A manager can review/approve/reject locally; no order is sent.
6. **2:20–2:45 — Intelligence and limitations.** Ask GhostWaste Intelligence why a batch is at risk. In the public demo, explain that it is a deterministic browser-local fixture assistant, not a live LLM, and Reset Demo clears its current-session conversation. Close with local-first, synthetic data, no food-safety claims, and the need for an authenticated pilot.

For the Vercel public-demo build, say “browser-local synthetic demo” instead of “persisted local run.” Scenario Studio and Impact Studio use labeled precomputed synthetic examples; Action Center approval is browser-local simulation and resets with the demo.

Suggested screenshots: Overview, Forecasting, Waste Radar/Use-First, Impact Studio, and Action Center with the synthetic/local labels visible.

## Recording checklist

- Start with a fresh temporary SQLite database and load only synthetic demo data.
- Keep the “no orders or supplier contact” language visible at least once.
- Record actual browser interactions; do not overlay fabricated metrics.
- Inspect the final 2–3 minute video and its accessibility/captions before upload.
