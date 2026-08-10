from typing import Dict, Any, List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy import select, func
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Listing, AutomationRule, PriceHistory, User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    # 1. Total & Active Listings
    listings_query = await db.execute(select(Listing).where(Listing.user_id == current_user.id))
    user_listings = listings_query.scalars().all()
    listing_ids = [l.id for l in user_listings]

    if not listing_ids:
        return {
            "total_listings": 0,
            "active_bots": 0,
            "total_price_changes": 0,
            "undercut_count": 0,
            "clamped_count": 0,
            "no_change_count": 0,
            "success_rate": 100.0,
            "history_trend": [],
        }

    rules_query = await db.execute(
        select(AutomationRule)
        .where(AutomationRule.listing_id.in_(listing_ids), AutomationRule.enabled == True)  # noqa: E712
    )
    active_bots = len(rules_query.scalars().all())

    # 2. History Metrics
    history_query = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.listing_id.in_(listing_ids))
        .order_by(PriceHistory.created_at.desc())
        .limit(100)
    )
    history_rows = history_query.scalars().all()

    total_changes = len(history_rows)
    undercut_count = sum(1 for h in history_rows if h.reason == "undercut")
    clamped_count = sum(1 for h in history_rows if h.reason in ("clamped_to_min", "clamped_to_max"))
    no_change_count = sum(1 for h in history_rows if h.reason == "no_change")
    successful = sum(1 for h in history_rows if h.success)

    success_rate = round((successful / total_changes * 100), 1) if total_changes > 0 else 100.0

    history_trend = [
        {
            "id": h.id,
            "listing_id": h.listing_id,
            "time": h.created_at.strftime("%H:%M"),
            "old_price": float(h.old_price) if h.old_price is not None else float(h.new_price),
            "new_price": float(h.new_price),
            "lowest_competitor": float(h.lowest_competitor_price) if h.lowest_competitor_price is not None else float(h.new_price) + 0.01,
            "reason": h.reason,
            "created_at": h.created_at.isoformat(),
        }
        for h in reversed(history_rows[:20])
    ]

    return {
        "total_listings": len(user_listings),
        "active_bots": active_bots,
        "total_price_changes": total_changes,
        "undercut_count": undercut_count,
        "clamped_count": clamped_count,
        "no_change_count": no_change_count,
        "success_rate": success_rate,
        "history_trend": history_trend,
    }
