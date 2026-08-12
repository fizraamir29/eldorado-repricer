"""
Database models.

users              -> one row per client account
listings           -> one row per marketplace listing being tracked
automation_rules   -> per-listing pricing configuration (1:1 with listings)
price_history      -> append-only log of every price change (audit trail)
"""
import uuid
from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from sqlalchemy import String, Numeric, Boolean, ForeignKey, DateTime, Integer, Text, UniqueConstraint
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Encrypted at the application layer (see app/security.py) before storage.
    marketplace_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    marketplace_client_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    marketplace_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    listings: Mapped[list["Listing"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    marketplace_listing_id: Mapped[str] = mapped_column(String(128), nullable=False)  # id on Eldorado's side
    game_name: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    current_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    __table_args__ = (
        UniqueConstraint('user_id', 'marketplace_listing_id', name='uq_listing_user_marketplace'),
    )

    owner: Mapped["User"] = relationship(back_populates="listings")
    rule: Mapped["AutomationRule"] = relationship(back_populates="listing", uselist=False, cascade="all, delete-orphan")
    history: Mapped[list["PriceHistory"]] = relationship(back_populates="listing", cascade="all, delete-orphan")


class AutomationRule(Base):
    """One row per listing — the pricing configuration the user controls from the dashboard."""
    __tablename__ = "automation_rules"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), unique=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    min_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    undercut_step: Mapped[float] = mapped_column(Numeric(10, 2), default=0.01)
    check_interval_minutes: Mapped[int] = mapped_column(Integer, default=5)
    auto_greeting_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_greeting_message: Mapped[str] = mapped_column(Text, default="Hello! Thanks for choosing our store. Your order is being processed automatically.")
    
    pending_target_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    listing: Mapped["Listing"] = relationship(back_populates="rule")


class PriceHistory(Base):
    """Append-only audit log — never updated, only inserted."""
    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)

    old_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    new_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    lowest_competitor_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "undercut", "clamped_to_min", "no_change"
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    listing: Mapped["Listing"] = relationship(back_populates="history")


class Notification(Base):
    """
    Follow-up messages shown to the user — e.g. 'price updated', 'held at your
    minimum', 'API call failed 3 times in a row'. Pushed live over WebSocket
    and also readable later from the bell icon in the dashboard.
    """
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    listing_id: Mapped[str | None] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=True)

    level: Mapped[str] = mapped_column(String(20), default="info")  # "info" | "warning" | "error"
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
