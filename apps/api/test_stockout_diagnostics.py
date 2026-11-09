from engines import Batch, monte_carlo_risk

def test_shortage_diagnostics():
    result=monte_carlo_risk(
        [Batch("a","Romaine",1.0,10,5.0)],
        {"Romaine":10.0},
        horizon_days=2,trials=20,seed=42
    )
    assert result.stockout_probability == 1.0
    assert result.ingredient_shortages[0]["shortage_probability"] == 1.0
    assert result.ingredient_shortages[0]["expected_unmet_demand_kg"] > 0

def test_sufficient_inventory():
    result=monte_carlo_risk(
        [Batch("a","Romaine",1000.0,10,5.0)],
        {"Romaine":1.0},
        horizon_days=2,trials=20,seed=42
    )
    assert result.stockout_probability == 0.0
    assert result.ingredient_shortages[0]["shortage_probability"] == 0.0
    assert result.ingredient_shortages[0]["expected_unmet_demand_kg"] == 0.0
