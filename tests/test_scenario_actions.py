from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apps.api.main import StudioIn, studio_calculation


def fake_session():
    ingredient = SimpleNamespace(id="test-ingredient-id")
    supplier = SimpleNamespace(
        name="Test Supplier",
        lead_days=1,
        minimum_order_kg=0,
    )
    link = SimpleNamespace(
        supplier_id="test-supplier-id",
        purchase_unit_cost=1.0,
    )

    db = MagicMock()
    # First query fetches inventory batches; second fetches supplier links.
    db.scalars.side_effect = [[], [link]]
    db.scalar.return_value = ingredient
    db.get.return_value = supplier
    return db


def calculate_with_optimizer(optimizer_output):
    db = fake_session()

    with patch(
        "apps.api.main._recipe_requirements",
        return_value={"Test Ingredient": 10.0},
    ), patch(
        "apps.api.main.optimize_multi_ingredient",
        return_value=optimizer_output,
    ) as optimizer:
        result = studio_calculation(
            StudioIn(as_of="2026-11-08", seed=42),
            db,
        )

    optimizer.assert_called_once()
    return result


def test_suggested_actions_match_optimizer_and_are_read_only():
    output = {
        "status": "optimal",
        "items": [{
            "ingredient": "Test Ingredient",
            "supplier": "Test Supplier",
            "order_kg": 5.0,
            "shortage_kg": 2.0,
            "lead_time_blocks_order": False,
        }],
    }

    first = calculate_with_optimizer(output)
    second = calculate_with_optimizer(output)

    actions = first["optimization"]["suggested_actions"]

    assert len(actions) == 1
    assert actions[0]["recommended_order_kg"] == 5.0
    assert actions[0]["expected_remaining_shortage_kg"] == 2.0
    assert "still exceeds" in actions[0]["explanation"]
    assert first["optimization"] == second["optimization"]
    assert first["persistent"] is False
    assert "no order is created" in first["optimization"]["action_notice"]


def test_blocked_supplier_has_explanation():
    output = {
        "status": "optimal",
        "items": [{
            "ingredient": "Test Ingredient",
            "supplier": "Delayed Supplier",
            "order_kg": 0.0,
            "shortage_kg": 8.0,
            "lead_time_blocks_order": True,
        }],
    }

    result = calculate_with_optimizer(output)
    action = result["optimization"]["suggested_actions"][0]

    assert action["lead_time_blocks_order"] is True
    assert action["recommended_order_kg"] == 0
    assert "lead time exceeds" in action["explanation"]


def supplier_selection_result(supplier_specs, horizon_days=7, lead_delta=0):
    """Inspect the actual supplier input passed to the optimizer."""
    ingredient = SimpleNamespace(id="test-ingredient-id")
    suppliers = {}
    links = []

    for supplier_id, name, price, lead_days in supplier_specs:
        suppliers[supplier_id] = SimpleNamespace(
            name=name,
            lead_days=lead_days,
            minimum_order_kg=0,
        )
        links.append(SimpleNamespace(
            supplier_id=supplier_id,
            purchase_unit_cost=price,
        ))

    db = MagicMock()
    db.scalars.side_effect = [[], links]
    db.scalar.return_value = ingredient
    db.get.side_effect = lambda model, supplier_id: suppliers[supplier_id]

    with patch(
        "apps.api.main._recipe_requirements",
        return_value={"Test Ingredient": 10.0},
    ), patch(
        "apps.api.main.optimize_multi_ingredient",
        return_value={"status": "optimal", "items": []},
    ) as optimizer:
        result = studio_calculation(
            StudioIn(
                as_of="2026-11-08",
                horizon_days=horizon_days,
                lead_time_days_delta=lead_delta,
            ),
            db,
        )

    optimizer.assert_called_once()
    items = optimizer.call_args.args[0]
    assert len(items) == 1
    assert result["persistent"] is False
    db.add.assert_not_called()
    db.commit.assert_not_called()
    return items[0]


def test_supplier_selection_prefers_on_time_over_cheaper_late():
    item = supplier_selection_result([
        ("late", "Budget Supplier", 4.0, 10),
        ("fast", "Fast Supplier", 4.5, 2),
    ])

    assert item["supplier"] == "Fast Supplier"
    assert item["unit_cost"] == 4.5
    assert item["lead_days"] == 2


def test_supplier_selection_uses_cheapest_on_time_supplier():
    item = supplier_selection_result([
        ("expensive", "Premium Supplier", 6.0, 1),
        ("cheap", "Value Supplier", 4.0, 3),
    ])

    assert item["supplier"] == "Value Supplier"
    assert item["unit_cost"] == 4.0


def test_supplier_selection_preserves_late_constraint_when_all_late():
    item = supplier_selection_result([
        ("slower", "Slow Supplier", 4.0, 12),
        ("less_slow", "Other Supplier", 5.0, 9),
    ], horizon_days=7)

    assert item["supplier"] == "Slow Supplier"
    assert item["lead_days"] > 7
