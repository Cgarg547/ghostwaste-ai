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
