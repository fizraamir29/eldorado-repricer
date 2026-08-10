"""
Run with: pytest tests/test_pricing_engine.py -v
"""
from app.pricing_engine import calculate_price


def test_undercuts_by_exactly_one_cent():
    decision = calculate_price(
        current_price=13.00,
        competitor_prices=[12.50, 12.80, 13.20],
        min_price=5.00,
        max_price=20.00,
    )
    assert decision.new_price == 12.49
    assert decision.reason == "undercut"
    assert decision.lowest_competitor_price == 12.50


def test_does_not_undercut_when_already_lowest():
    decision = calculate_price(
        current_price=12.00,
        competitor_prices=[12.50, 12.80],
        min_price=5.00,
        max_price=20.00,
    )
    assert decision.new_price == 12.00
    assert decision.reason == "no_change"


def test_clamps_to_minimum_price():
    decision = calculate_price(
        current_price=10.00,
        competitor_prices=[5.00],
        min_price=5.00,
        max_price=20.00,
    )
    # lowest (5.00) - 0.01 = 4.99, which is below min_price (5.00) -> clamp
    assert decision.new_price == 5.00
    assert decision.reason == "clamped_to_min"


def test_clamps_to_maximum_price():
    decision = calculate_price(
        current_price=250.00,
        competitor_prices=[220.00],
        min_price=5.00,
        max_price=200.00,
    )
    # lowest (220.00) - 0.01 = 219.99, which is above max_price (200.00) -> clamp
    assert decision.new_price == 200.00
    assert decision.reason == "clamped_to_max"


def test_no_competitors_holds_current_price():
    decision = calculate_price(
        current_price=12.00,
        competitor_prices=[],
        min_price=5.00,
        max_price=20.00,
    )
    assert decision.new_price == 12.00
    assert decision.reason == "no_competitors"


def test_never_undercuts_by_more_than_step():
    decision = calculate_price(
        current_price=100.00,
        competitor_prices=[12.50],
        min_price=1.00,
        max_price=200.00,
        undercut_step=0.01,
    )
    assert decision.new_price == 12.49
    assert round(12.50 - decision.new_price, 2) == 0.01
