"""
Pricing engine — the core business logic requested by the client:

  "If someone has put a price of $12.50, my bot automatically puts $12.49.
   Reduce by one cent only. Don't reduce too much."

This module is pure logic with no I/O, so it's trivial to unit test.
"""
from dataclasses import dataclass


@dataclass
class PricingDecision:
    new_price: float
    lowest_competitor_price: float | None
    reason: str  # "undercut" | "clamped_to_min" | "clamped_to_max" | "no_change" | "no_competitors"


def calculate_price(
    current_price: float,
    competitor_prices: list[float],
    min_price: float,
    max_price: float,
    undercut_step: float = 0.01,
) -> PricingDecision:
    """
    Decide the next price for a listing.
    """
    if not competitor_prices:
        return PricingDecision(current_price, None, "no_competitors")

    # Filter out our own current price so we don't undercut ourselves.
    other_prices = [p for p in competitor_prices if p != current_price]
    
    if not other_prices:
        # We are the only seller left on the market! Maximize profit by jumping to max_price.
        if current_price < max_price:
            return PricingDecision(max_price, None, "clamped_to_max")
        return PricingDecision(current_price, None, "no_competitors")

    lowest = min(other_prices)
    
    # We want to be exactly `undercut_step` below the lowest competitor.
    candidate = round(lowest - undercut_step, 2)
    
    # If the candidate is exactly our current price, we are perfectly positioned.
    if candidate == current_price:
        return PricingDecision(current_price, lowest, "no_change")

    if candidate < min_price:
        return PricingDecision(min_price, lowest, "clamped_to_min")
    if candidate > max_price:
        return PricingDecision(max_price, lowest, "clamped_to_max")

    return PricingDecision(candidate, lowest, "undercut")
