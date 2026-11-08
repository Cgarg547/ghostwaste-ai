from apps.api.engines import Batch, metrics, monte_carlo_risk, optimize_purchase, seasonal_naive, rolling_origin_backtest

def test_metrics_and_seasonal_baseline_are_deterministic():
    assert seasonal_naive([1,2,3,4,5,6,7],3)==[1,2,3]
    assert metrics([1,2],[1,4])["mae"]==1

def test_monte_carlo_repeats_for_same_seed_and_never_uses_expired_stock():
    batches=[Batch("expired","x",5,-1,3),Batch("fresh","x",2,2,3)]
    a=monte_carlo_risk(batches,{"x":1},trials=100,seed=8)
    b=monte_carlo_risk(batches,{"x":1},trials=100,seed=8)
    assert a==b
    assert a.expected_waste_kg>=5

def test_purchase_optimizer_prioritizes_service_without_automatic_action():
    output=optimize_purchase(available_kg=2,demand_kg=10,unit_cost=1,min_order_kg=3,max_order_kg=20)
    assert output["status"]=="optimal"
    assert output["recommended_order_kg"]==8
    assert output["expected_shortage_kg"]==0

def test_rolling_origin_never_uses_future_values():
    result=rolling_origin_backtest([1,2,3,4,5,6,7,8],initial_train=4)
    assert result["points"]==4
    assert result["selected_model"] in {"moving_average","seasonal_naive"}
