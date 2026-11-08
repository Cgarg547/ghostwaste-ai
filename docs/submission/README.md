# GhostWaste AI — submission draft

**Title:** GhostWaste AI: Predict tomorrow's food waste. Prevent it today.

**Short pitch:** GhostWaste turns batch expiry dates and expected ingredient demand into an explainable FEFO waste-risk view, then gives managers approval-required actions before food becomes waste.

**Problem and solution:** Restaurants make preparation and purchasing decisions with perishable ingredients, uneven demand, and limited time. GhostWaste makes the near-term expiry risk visible at batch level. The demo’s deterministic FEFO engine never allocates expired stock and labels all scenario outputs as synthetic.

**Technical architecture:** Next.js 16 client; FastAPI/Pydantic API; SQLAlchemy and SQLite local persistence. Recorded local sales feed a clearly labeled moving-average baseline. Recommendation decisions write audit events. No automatic ordering or supplier communication occurs.

**Evidence and limitations:** The current release has API unit/integration tests and a production web build. It does not claim pilot savings, trained ML accuracy, or optimized purchasing outcomes. It requires validated restaurant data, chronological backtests, OR-Tools optimization, PostgreSQL/Alembic, auth, and a consented pilot before operational deployment.

**Team:** [Add team member names and eligibility confirmation]

**Repository:** [Add public repository URL after approval]

**Live demo:** [Add verified deployed URL after approval]

**Video:** [Add verified video URL after recording]

## Three-minute demo script

1. **0:00–0:20:** State the restaurant perishables problem and show the “synthetic demo” label.
2. **0:20–1:05:** Run Scenario Lab. Change demand and explain that batches are ordered first-expiring-first-out; show projected kilograms and cost at risk.
3. **1:05–1:40:** Open Waste Radar. Explain that an expired batch is never allocated and that each value is an estimate, not a safety decision or claimed saving.
4. **1:40–2:10:** Create review actions; show that actions require a manager approval and never send orders.
5. **2:10–2:40:** Show local inventory/sales/forecast API paths and explain the moving-average baseline honestly.
6. **2:40–3:00:** State limitations and roadmap: validated demand model, constrained optimization, pilot evaluation, production access control.

Recording checklist: start API and web app; verify demo API responds; use only synthetic/demo data; zoom text; show the limitations panel; do not state unmeasured impact; confirm every URL before submission.
