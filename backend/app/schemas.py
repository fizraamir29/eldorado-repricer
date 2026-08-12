"""
Pydantic schemas — request/response shapes for the API.
"""
from datetime import datetime
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    username: str | None = None
    age: int | None = Field(default=None, ge=10, le=120)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    full_name: str | None = None
    username: str | None = None
    age: int | None = None
    created_at: datetime
    last_login_at: datetime | None = None


class MarketplaceCredentials(BaseModel):
    """Client submits their official Eldorado Seller API credentials through this endpoint."""
    client_id: str | None = None
    client_secret: str | None = None
    api_key: str | None = None  # Legacy fallback support



class ListingCreate(BaseModel):
    marketplace_listing_id: str
    game_name: str
    title: str
    current_price: float = Field(gt=0)


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    marketplace_listing_id: str
    game_name: str
    title: str
    current_price: float
    last_checked_at: datetime | None
    status: str


class AutomationRuleUpdate(BaseModel):
    enabled: bool
    min_price: float = Field(gt=0)
    max_price: float = Field(gt=0)
    undercut_step: float = Field(default=0.01, gt=0)
    check_interval_minutes: int = Field(default=5, ge=1, le=1440)
    auto_greeting_enabled: bool = Field(default=True)
    auto_greeting_message: str = Field(default="Hello! Thanks for choosing our store. Your order is being processed automatically.")


class AutomationRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    listing_id: str
    enabled: bool
    min_price: float
    max_price: float
    undercut_step: float
    check_interval_minutes: int
    auto_greeting_enabled: bool
    auto_greeting_message: str


class PriceHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    old_price: float | None
    new_price: float
    lowest_competitor_price: float | None
    reason: str
    success: bool
    error_message: str | None
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    listing_id: str | None
    level: str
    title: str
    message: str
    read: bool
    created_at: datetime
