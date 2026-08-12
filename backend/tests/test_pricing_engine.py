import pytest
from app.pricing_engine import calculate_price, PricingDecision

def test_undercut():
    decision = calculate_price(
        current_price=2.00,
        competitor_prices=[1.90, 2.10],
        min_price=1.80,
        max_price=3.90,
        undercut_step=0.01
    )
    assert decision.new_price == 1.89
    assert decision.reason == "undercut"

def test_clamped_to_min():
    decision = calculate_price(
        current_price=2.00,
        competitor_prices=[1.70, 2.10],
        min_price=1.80,
        max_price=3.90,
        undercut_step=0.01
    )
    assert decision.new_price == 1.80
    assert decision.reason == "clamped_to_min"

def test_clamped_to_max():
    decision = calculate_price(
        current_price=3.50,
        competitor_prices=[4.50, 4.60],
        min_price=1.80,
        max_price=3.90,
        undercut_step=0.01
    )
    assert decision.new_price == 3.90
    assert decision.reason == "clamped_to_max"

def test_no_change_at_min():
    # If the candidate price hits exactly the min, and current_price is exactly the min,
    # the reason should be no_change
    decision = calculate_price(
        current_price=1.80,
        competitor_prices=[1.70, 2.10],
        min_price=1.80,
        max_price=3.90,
        undercut_step=0.01
    )
    assert decision.new_price == 1.80
    assert decision.reason == "no_change"

def test_no_change_undercut():
    decision = calculate_price(
        current_price=1.89,
        competitor_prices=[1.90, 2.10],
        min_price=1.80,
        max_price=3.90,
        undercut_step=0.01
    )
    assert decision.new_price == 1.89
    assert decision.reason == "no_change"

def test_no_competitors_jumps_to_max():
    decision = calculate_price(
        current_price=2.00,
        competitor_prices=[2.00],  # only us
        min_price=1.80,
        max_price=3.90,
        undercut_step=0.01
    )
    assert decision.new_price == 3.90
    assert decision.reason == "clamped_to_max"
