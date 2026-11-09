# Reproducible synthetic demo data

## Data policy

All values below are isolated synthetic fixtures. They are designed to demonstrate product behavior, not to represent a restaurant, partnership, observed waste, or savings. The built-in loader is idempotent but writes to its target SQLite database; use a fresh path for recording. The extra fixture in this document is a request payload only and does not modify application data.

## Built-in Garden Salad dataset

Load with `POST /demo/load` into a fresh demo database. The loader namespaces every name with `Demo` and does not delete/update existing rows.

| Menu item / recipe | Yield | Ingredient | kg per serving | On hand kg | Unit cost | Received | Use-by |
|---|---:|---|---:|---:|---:|---|---|
| Demo Garden Salad | 1 serving | Demo Romaine Hearts | 0.18 | 7.5 | $5.20/kg | 2026-11-06 | 2026-11-10 |
|  |  | Demo Cherry Tomatoes | 0.12 | 6.0 | $4.80/kg | 2026-11-05 | 2026-11-11 |
|  |  | Demo Feta | 0.05 | 3.0 | $12.50/kg | 2026-11-03 | 2026-11-15 |
|  |  | Demo Citrus Dressing | 0.04 | 2.5 | $8.00/kg | 2026-11-01 | 2026-11-18 |

Supplier: `Demo Market Cooperative`, lead time 2 days, minimum order 2 kg, explicitly linked at the unit costs above.

Sales history for 2026-10-25 through 2026-11-07: `28, 31, 29, 34, 38, 42, 36, 32, 35, 39, 44, 47, 41, 37` daily salads. With the current code and `initial_train=7`, moving average is selected; the next seven daily forecasts are 39.286 servings with interval [31.229, 47.343].

## Default workflow and honest zero-waste explanation

Use the saved forecast run, then invoke `POST /workflows/forecast/{run_id}` with:

```json
{"as_of":"2026-11-08","horizon_days":7,"trials":500,"seed":42,"storage_capacity_kg":1000}
```

This translates the forecast into approximately 49.500 kg romaine, 33.000 kg tomatoes, 13.750 kg feta, and 11.000 kg dressing across seven days. The expiry-window simulation reports **0 kg expected waste / 0% waste probability** for the stocked batches, while it can report a stockout risk because it does not simulate incoming proposed purchases. That zero is meaningful only under the supplied high modeled demand, dates, FEFO allocation, and fixed assumptions: all expiry-window stock is consumed in the simulation. It does **not** mean actual waste is zero, food is safe, or the restaurant has saved anything.

The planner uses the separate forecast-derived horizon demand and recommends quantities subject to supplier constraints; it does not feed orders into the Monte Carlo simulation and does not execute them. This separation is intentional and should be narrated.

## Separate nonzero-risk API fixture

Use this in Scenario Lab or `POST /risk/simulate`; do not import it into the persistent demo database.

```json
{
  "as_of":"2026-11-08",
  "horizon_days":2,
  "trials":500,
  "seed":42,
  "batches":[{
    "id":"fixture-spinach-A",
    "ingredient":"Fixture Spinach",
    "quantity_kg":10,
    "unit_cost":4,
    "received_on":"2026-11-07",
    "use_by":"2026-11-10"
  }],
  "demand":[{"ingredient":"Fixture Spinach","expected_daily_kg":2}]
}
```

With the current engine, this fixture returns 6.023 kg expected modeled waste, 100% modeled waste probability, $24.09 modeled cost at risk, p10 5.304 kg, p90 6.795 kg, and 0% stockout probability. These figures are reproducible with the stated 500 trials and seed. They are not a projected restaurant outcome or savings figure.

For the same fixture, deterministic `POST /scenario` reports 6 kg expiry exposure and $24 potential cost, because it uses constant rather than randomly drawn daily demand. Showing both values teaches the distinction between an explainable point estimate and an uncertainty model.

## Human review demonstration

`POST /recommendations/from-scenario` against the nonzero fixture creates a local, pending review card. In Action Center, choose Approve locally or Reject and provide a real reason such as “Demo manager reviewed modeled fixture.” The final status is stored locally; no inventory, supplier, order, or payment is changed. For a clean re-recording, use a new temporary SQLite file rather than attempting to reset a database.
