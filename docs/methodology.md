# Forecasting, simulation, and optimization methodology

## Forecasting

For a menu item, GhostWaste reads chronologically ordered local daily-sale quantities. A persisted run needs more observations than `initial_train` (default 7). It evaluates one-step-ahead predictions at each subsequent cutoff; no future observation is included in a training slice.

Candidates:

- **Moving average:** mean of the most recent seven (or fewer) observations.
- **Seasonal naive:** repeats the observation from seven periods earlier, falling back to moving average when fewer than seven observations exist.
- **LightGBM:** optional local candidate using index, lag-one, and rolling-seven features. It is only included when the package is available and enough history exists; it is not guaranteed by `requirements.txt`.

The lowest MAE candidate is selected. The forecast interval half-width is the 90th percentile absolute residual of that selected rolling-origin evaluation. If sufficient history remains, the app also calculates coverage on a final untouched chronological holdout. This is a modest baseline evaluation, not proof of accuracy or calibrated uncertainty on restaurant operations.

The built-in synthetic Garden Salad history has 14 points. With `initial_train=7`, moving average is selected in the current engine: MAE 3.796, RMSE 4.8223, WAPE 9.6625%, bias -2.6123; seasonal naive has MAE 5.5714. The seven predicted daily servings are 39.286 with interval half-width 8.0574. These are fixture calculations, not observed restaurant results.

## Recipe demand translation

For each forecasted day, predicted servings are summed across the horizon. Ingredient requirement is:

`forecast servings ÷ recipe yield × ingredient kg per recipe yield`

The workflow assumes that the recipe name equals the menu-item name, recipe yield is fixed, and all ingredient units are canonical kilograms. Missing recipes or links fail visibly rather than being inferred.

## Deterministic expiry exposure

Within each ingredient, batches are ordered by use-by date and allocated at a constant supplied daily rate. A batch whose use-by is today or earlier receives no allocation. The remaining quantity at the hard use-by boundary is displayed as **expiry exposure**; it is not a statement that food is safe/unsafe and not an observed waste record.

The deterministic calculation ignores deliveries, substitutions, cancellations, handling loss, real consumption timing, and forecast error. It is deliberately explainable.

## Monte Carlo simulation

The simulation runs `trials` independent paths (default 500). On each simulated day and ingredient, demand is drawn from a normal distribution with mean equal to forecast-derived daily demand and standard deviation `max(0.01, mean × 0.2)`. Demand is allocated FEFO only to batches with `use_by_days > day`. After the horizon, any quantity in batches expiring in that horizon is counted as modeled waste.

Reported outputs are expected waste kg, probability of any waste, probability of any stockout, expected cost at risk, and p10/p90 waste quantities. A fixed NumPy seed makes identical inputs reproducible. The 20% coefficient of variation and normal distribution are synthetic modeling assumptions—not learned demand behavior. The simulated waste number excludes an incoming optimized order; it evaluates the inventory snapshot/demand risk separately from the purchase-plan proposal.

## Purchase planning

`/optimization/purchase` uses OR-Tools GLOP for one ingredient. It minimizes purchase cost plus configurable shortage and surplus penalties subject to a balance equation and bounds. A configured minimum order is a simple required lower bound in this one-item model.

The workflow uses OR-Tools CBC mixed-integer programming for multiple ingredients because “order zero or at least supplier minimum” is a disjunction. For every eligible ingredient it models an order quantity, an order-active binary, shortage, and surplus. It enforces available-stock balance, lead-time blocking when a supplier arrives after the horizon, supplier minimum/maximum quantities, aggregate storage capacity, and optional demand-side preparation capacity. It minimizes purchase cost + shortage penalty + waste/surplus penalty.

Only an explicitly linked supplier with a known purchase price may appear as purchasable. If a price is absent, GhostWaste preserves its unmet shortage with `purchase_unavailable=true`; it never invents a price. The plan is a recommendation only. No API endpoint sends a purchase order, contacts a supplier, charges money, or changes inventory.

## Reproducibility and evidence boundary

The fixed fixture command `python scripts/run_experiments.py` regenerates [evaluation-results.md](evaluation-results.md). Its forecast comparison, Monte Carlo result, and purchase comparison are synthetic code checks, not a benchmark, field trial, savings measurement, or accuracy claim.
# Planning methodology additions

Use-First ranks unexpired batches by FEFO use-by date and forecast-linked consumption; expired batches are reported for review and excluded from consumption recommendations. Impact Studio accepts a claim only when both inputs share date, forecast source, horizon, seed, and trial count. Percentage differences are omitted when their baseline is zero.
