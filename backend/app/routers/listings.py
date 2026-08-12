# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Listing, User, AutomationRule
from app.schemas import ListingCreate, ListingOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=list[ListingOut])
async def list_listings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(Listing.user_id == current_user.id))
    return result.scalars().all()


@router.post("", response_model=ListingOut, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: ListingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = Listing(user_id=current_user.id, **payload.model_dump())
    db.add(listing)
    await db.flush()  # get listing.id before creating the rule

    # Every listing gets a disabled-by-default automation rule so the dashboard
    # always has something to configure — the client turns it on explicitly.
    rule = AutomationRule(
        listing_id=listing.id,
        enabled=False,
        min_price=payload.current_price * 0.7,
        max_price=payload.current_price * 1.3,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(listing_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(Listing.id == listing_id, Listing.user_id == current_user.id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    await db.delete(listing)
    await db.commit()


@router.post("/{listing_id}/sync")
async def sync_listing(listing_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(Listing.id == listing_id, Listing.user_id == current_user.id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    rule_result = await db.execute(select(AutomationRule).where(AutomationRule.listing_id == listing_id))
    rule = rule_result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=400, detail="Listing has no automation rule configured")

    from app.scheduler import process_listing
    from app.security import decrypt_secret
    from app.config import settings

    client_id = settings.eldorado_client_id or current_user.marketplace_client_id
    client_secret = settings.eldorado_client_secret or (decrypt_secret(current_user.marketplace_client_secret_encrypted) if current_user.marketplace_client_secret_encrypted else None)
    api_key = decrypt_secret(current_user.marketplace_api_key_encrypted) if current_user.marketplace_api_key_encrypted else None

    await process_listing(db, listing, rule, client_id=client_id, client_secret=client_secret, api_key=api_key)
    await db.refresh(listing)

    return {
        "status": "synced",
        "listing_id": listing.id,
        "current_price": float(listing.current_price),
        "last_checked_at": listing.last_checked_at.isoformat() if listing.last_checked_at else None,
    }

