# Impact validation

## Method

Impact Studio calls the same ephemeral `StudioIn` calculation twice. It accepts comparison only when the as-of date, forecast run, horizon, seed, and trial count match. Both sides use the current read-only inventory snapshot, canonical kg quantities, FEFO allocation, seeded Monte Carlo and the same CBC planning methodology.

The interface's demo comparison holds inventory, horizon, storage and seed constant and applies a `0.8` demand multiplier. It displays expected modeled waste kg, modeled cost-at-risk and stockout probability deltas. It reports no percentage if baseline is zero. It never calls this a real saving, rescued food, or observed outcome.

## Reproduce

1. Run the isolated browser suite or start the local demo and load demo data.
2. Select the synthetic forecast, open **Impact Studio**, then choose **Compare baseline and lower-demand plan**.
3. Inspect returned seed, horizon, assumptions and baseline/proposed figures.

The isolated API test `test_impact_requires_compatible_inputs_and_omits_zero_percentage` verifies rejection of differing seeds and zero-denominator handling. Outputs are data-dependent and are deliberately not hardcoded into this document.

## Limitations

This measures a model under assumptions, not a restaurant pilot. Cost is exposure cost from batch unit cost where present, and demand/shelf-life changes are planning assumptions rather than food-safety advice.
