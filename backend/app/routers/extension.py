import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import select
from pydantic import BaseModel

from app.database import AsyncSessionLocal
from app.models import User, Listing, AutomationRule, PriceHistory
from app.routers.auth import get_current_user
from app.realtime import manager

router = APIRouter()
logger = logging.getLogger(__name__)

class ExtensionUpdateResponse(BaseModel):
    id: str
    marketplace_listing_id: str
    game_name: str
    title: str
    pending_target_price: float

class SuccessRequest(BaseModel):
    listing_id: str

@router.get("/pending-updates", response_model=list[ExtensionUpdateResponse])
async def get_pending_updates(user: User = Depends(get_current_user)):
    """
    Called by the Chrome Extension every few seconds to check if any prices need to be updated.
    Returns listings where pending_target_price is not null.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Listing, AutomationRule)
            .join(AutomationRule, AutomationRule.listing_id == Listing.id)
            .where(Listing.user_id == user.id)
            .where(AutomationRule.pending_target_price != None)
        )
        rows = result.all()
        
        updates = []
        for listing, rule in rows:
            updates.append(
                ExtensionUpdateResponse(
                    id=listing.id,
                    marketplace_listing_id=listing.marketplace_listing_id,
                    game_name=listing.game_name,
                    title=listing.title,
                    pending_target_price=float(rule.pending_target_price),
                )
            )
        return updates

@router.post("/update-success")
async def mark_update_success(req: SuccessRequest, user: User = Depends(get_current_user)):
    """
    Called by the Chrome Extension after it successfully updates the price on Eldorado.
    We then update the current_price and clear the pending_target_price.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Listing, AutomationRule)
            .join(AutomationRule, AutomationRule.listing_id == Listing.id)
            .where(Listing.user_id == user.id)
            .where(Listing.id == req.listing_id)
        )
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Listing not found")
            
        listing, rule = row
        
        if rule.pending_target_price is None:
            # Already cleared or nothing was pending
            return {"status": "ok"}
            
        new_price = float(rule.pending_target_price)
        
        # Clear the pending flag and update the actual current price
        rule.pending_target_price = None
        listing.current_price = new_price
        
        session.add(rule)
        session.add(listing)
        await session.commit()
        
        # Push real-time update to dashboard to show it was successfully updated by extension
        await manager.send_to_user(user.id, {
            "type": "price_update_success",
            "listing_id": listing.id,
            "new_price": new_price,
            "status": "active"
        })
        
        return {"status": "ok"}
