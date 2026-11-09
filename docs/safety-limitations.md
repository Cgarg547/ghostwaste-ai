# Safety, limitations, and roadmap

## Safety boundary

GhostWaste is local decision-support software. It is not food-safety advice, a HACCP system, an ERP, a point-of-sale integration, a procurement system, or a claim that food is safe to serve. A supplied use-by date is modeled as a hard allocation boundary only. Managers remain responsible for inspection, local law, storage/handling requirements, allergen controls, and all operational decisions.

No endpoint executes a purchase, contacts a supplier, sends a message, moves money, or automatically removes predicted inventory. Approval records a local decision and audit event only.

## Claim taxonomy

| Label | Meaning in this project | What may be claimed |
|---|---|---|
| Observed fact | A locally stored input or recorded stock event | “The demo inventory contains 7.5 kg of synthetic romaine.” |
| Modeled outcome | Deterministic calculation or seeded simulation | “The fixture models 6.023 kg expected expiry-window waste.” |
| Hypothetical savings | A future comparison under stated assumptions | “A pilot could measure avoided waste against a pre-registered baseline.” |
| Observed savings | Measured before/after outcome from a defined pilot | **None available; do not claim any.** |
| Unknown | Required evidence not collected | Adoption, actual waste avoided, food-safety outcome, ROI, model accuracy in a restaurant |

## Known limitations

- All bundled demo records and experiment inputs are synthetic; there are no restaurant partnerships, pilots, or real-world savings.
- Forecasts have small local histories and simple baseline candidates. The optional LightGBM path is not a dependency guarantee and is not validated for this use.
- The demand distribution (normal, 20% CV), use-by treatment, and unit costs are assumptions. Results are sensitive to them.
- Simulation does not model deliveries, substitutions, promotions, weather, events, spoilage dynamics, handling losses, or intra-day timing.
- The planner omits pack sizes, supplier availability, budget, carbon, recipes substitutions, procurement contracts, taxes, delivery windows, and food-safety constraints.
- SQLite, auto-schema creation, no user authentication, and local-only audit records are unsuitable for multi-user production operations.
- “Potential cost at risk” is remaining quantity times provided unit cost—not revenue, savings, avoided disposal cost, or profit.

## Future roadmap

1. Run a consented, privacy-reviewed pilot with a pre-registered baseline and measured waste-event definitions.
2. Validate data ingestion, unit normalization, recipe governance, and batch reconciliation with staff.
3. Compare forecast methods on chronological held-out restaurant data; monitor calibration, drift, bias, and operational consequences.
4. Add role-based authentication, durable PostgreSQL storage, reviewed migrations, secure secrets, backups, observability, and audit retention.
5. Add human-reviewed integrations for POS, inventory, and procurement only after safety, security, and pilot evidence support them.
6. Evaluate real impact as measured kilograms/cost of discarded inventory against a documented baseline—not simulated values.
