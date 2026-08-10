from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Listing, PriceHistory, User
from app.schemas import PriceHistoryOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/listings/{listing_id}/history", tags=["history"])


@router.get("", response_model=list[PriceHistoryOut])
async def get_history(
    listing_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = await db.execute(select(Listing).where(Listing.id == listing_id, Listing.user_id == current_user.id))
    if not owned.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Listing not found")

    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.listing_id == listing_id)
        .order_by(PriceHistory.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
