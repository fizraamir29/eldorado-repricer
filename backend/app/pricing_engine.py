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

    # competitor_prices ONLY contains ACTUAL competitors now, 
    # because market_client.py filters out our own offer id.
    other_prices = competitor_prices
    
    if not other_prices:
        # We are the only seller left on the market, OR we only saw ourselves!
        # If we only saw ourselves in a limited list (like TopUp groups), 
        # jumping to max_price is dangerous. We should just stay put.
        if competitor_prices and min(competitor_prices) == current_price:
            return PricingDecision(current_price, current_price, "no_change")
            
        # We are the only seller left on the market! Maximize profit by jumping to max_price.
        if current_price < max_price:
            return PricingDecision(max_price, None, "clamped_to_max")
        return PricingDecision(current_price, None, "no_competitors")

    lowest_competitor_price = min(other_prices)
    
    target_price = round(lowest_competitor_price - undercut_step, 2)
    
    if target_price < min_price:
        target_price = min_price
        reason = "clamped_to_min"
    elif target_price > max_price:
        target_price = max_price
        reason = "clamped_to_max"
    else:
        reason = "undercut"
        
    if target_price == current_price:
        reason = "no_change"

    return PricingDecision(target_price, lowest_competitor_price, reason)
