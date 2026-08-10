# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Listing, AutomationRule, User
from app.schemas import AutomationRuleUpdate, AutomationRuleOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/listings/{listing_id}/rule", tags=["automation-rules"])


async def _get_owned_listing(listing_id: str, current_user: User, db: AsyncSession) -> Listing:
    result = await db.execute(select(Listing).where(Listing.id == listing_id, Listing.user_id == current_user.id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("", response_model=AutomationRuleOut)
async def get_rule(listing_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _get_owned_listing(listing_id, current_user, db)  # ownership check
    result = await db.execute(select(AutomationRule).where(AutomationRule.listing_id == listing_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    return rule


@router.put("", response_model=AutomationRuleOut)
async def update_rule(
    listing_id: str,
    payload: AutomationRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_listing(listing_id, current_user, db)  # ownership check

    if payload.min_price >= payload.max_price:
        raise HTTPException(status_code=400, detail="min_price must be lower than max_price")

    result = await db.execute(select(AutomationRule).where(AutomationRule.listing_id == listing_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")

    rule.enabled = payload.enabled
    rule.min_price = payload.min_price
    rule.max_price = payload.max_price
    rule.undercut_step = payload.undercut_step
    rule.check_interval_minutes = payload.check_interval_minutes
    rule.auto_greeting_enabled = payload.auto_greeting_enabled
    rule.auto_greeting_message = payload.auto_greeting_message

    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule
