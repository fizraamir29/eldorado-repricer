from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Notification, User
from app.schemas import NotificationOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.read == False)  # noqa: E712
    query = query.order_by(Notification.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/unread-count")
async def unread_count(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.id, Notification.read == False  # noqa: E712
        )
    )
    return {"count": result.scalar_one()}


@router.patch("/{notification_id}/read", status_code=204)
async def mark_read(notification_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read = True
    db.add(notification)
    await db.commit()


@router.post("/mark-all-read", status_code=204)
async def mark_all_read(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification).where(Notification.user_id == current_user.id, Notification.read == False)  # noqa: E712
    )
    for n in result.scalars().all():
        n.read = True
        db.add(n)
    await db.commit()
