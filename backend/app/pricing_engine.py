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

    Rules (from the client's spec):
      1. Find the lowest competitor price.
      2. Undercut it by exactly `undercut_step` (default $0.01) — never more.
      3. Never go below min_price or above max_price.
      4. If we are already the lowest, don't keep racing ourselves down —
         hold the current price.
    """
    if not competitor_prices:
        return PricingDecision(current_price, None, "no_competitors")

    lowest = min(competitor_prices)

    # We're already at or below the market lowest — no need to undercut further.
    if current_price <= lowest:
        return PricingDecision(current_price, lowest, "no_change")

    candidate = round(lowest - undercut_step, 2)

    if candidate < min_price:
        return PricingDecision(min_price, lowest, "clamped_to_min")
    if candidate > max_price:
        return PricingDecision(max_price, lowest, "clamped_to_max")

    return PricingDecision(candidate, lowest, "undercut")
