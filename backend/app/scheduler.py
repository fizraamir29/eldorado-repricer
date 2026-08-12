"""
Background scheduler.

APScheduler runs one lightweight "tick" every minute. On each tick, it asks
the database which listings are due for a check (based on each listing's own
check_interval_minutes) and processes only those — so listings can have
different intervals without needing a separate job per listing.
"""
import logging
from datetime import datetime, timedelta, timezone

# pyrefly: ignore [missing-import]
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# pyrefly: ignore [missing-import]
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Listing, AutomationRule, PriceHistory, User, Notification
from app.market_client import EldoradoClient, MarketplaceAPIError
from app.pricing_engine import calculate_price
from app.security import decrypt_secret
from app.realtime import manager

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()

# Human-readable follow-up messages shown to the user for each outcome.
_REASON_MESSAGES = {
    "undercut": "Price updated to stay one cent below the lowest competitor.",
    "clamped_to_min": "Competitor price would have gone below your minimum, so the price was held at your floor instead.",
    "clamped_to_max": "Held at your maximum price limit.",
    "no_change": "Your listing is already the lowest price — no change needed.",
    "no_competitors": "No competitor offers were found this cycle.",
}


async def process_listing(session, listing: Listing, rule: AutomationRule, client_id: str | None = None, client_secret: str | None = None, api_key: str | None = None):
    client = EldoradoClient(client_id=client_id, client_secret=client_secret, api_key=api_key)

    try:
        offers = await client.get_competitor_offers(
            game_id=listing.game_name, item_id=listing.marketplace_listing_id
        )
        # TODO: adjust once real field name is confirmed from Eldorado's docs.
        competitor_prices = [float(o["price"]) for o in offers if "price" in o]

        decision = calculate_price(
            current_price=float(listing.current_price),
            competitor_prices=competitor_prices,
            min_price=float(rule.min_price),
            max_price=float(rule.max_price),
            undercut_step=float(rule.undercut_step),
        )

        old_price = float(listing.current_price)
        price_changed = decision.reason in ("undercut", "clamped_to_min", "clamped_to_max") and decision.new_price != old_price

        history = PriceHistory(
            listing_id=listing.id,
            old_price=listing.current_price,
            new_price=decision.new_price,
            lowest_competitor_price=decision.lowest_competitor_price,
            reason=decision.reason,
            success=True,
        )

        if decision.reason in ("undercut", "clamped_to_min", "clamped_to_max"):
            await client.update_listing_price(listing.marketplace_listing_id, decision.new_price)
            listing.current_price = decision.new_price

        listing.last_checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.add(history)
        session.add(listing)

        # Only create a follow-up message when something actually happened —
        # don't spam the user every single minute with "no change" noise.
        notification = None
        if price_changed or decision.reason == "no_competitors":
            level = "warning" if decision.reason in ("clamped_to_min", "clamped_to_max", "no_competitors") else "info"
            notification = Notification(
                user_id=listing.user_id,
                listing_id=listing.id,
                level=level,
                title=f"{listing.title}",
                message=_REASON_MESSAGES.get(decision.reason, decision.reason),
            )
            session.add(notification)

        await session.commit()
        if notification:
            await session.refresh(notification)

        # Push live update to any open dashboard tab for this user.
        await manager.send_to_user(listing.user_id, {
            "type": "price_update",
            "listing_id": listing.id,
            "new_price": float(listing.current_price),
            "reason": decision.reason,
            "checked_at": listing.last_checked_at.isoformat() if listing.last_checked_at else "",
        })
        if notification:
            await manager.send_to_user(listing.user_id, {
                "type": "notification",
                "id": notification.id,
                "level": notification.level,
                "title": notification.title,
                "message": notification.message,
                "listing_id": notification.listing_id,
                "created_at": notification.created_at.isoformat(),
            })

    except MarketplaceAPIError as exc:
        logger.error("Failed to process listing %s: %s", listing.id, exc)
        listing.last_checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.add(listing)
        session.add(PriceHistory(
            listing_id=listing.id,
            old_price=listing.current_price,
            new_price=listing.current_price,
            lowest_competitor_price=None,
            reason="error",
            success=False,
            error_message=str(exc),
        ))
        notification = Notification(
            user_id=listing.user_id,
            listing_id=listing.id,
            level="error",
            title=f"{listing.title}",
            message=f"Couldn't reach the marketplace API this cycle: {exc}",
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)

        await manager.send_to_user(listing.user_id, {
            "type": "notification",
            "id": notification.id,
            "level": "error",
            "title": notification.title,
            "message": notification.message,
            "listing_id": notification.listing_id,
            "created_at": notification.created_at.isoformat(),
        })


async def run_due_listings():
    """Called every minute. Picks up only the listings whose interval has elapsed."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Listing, AutomationRule, User)
            .join(AutomationRule, AutomationRule.listing_id == Listing.id)
            .join(User, User.id == Listing.user_id)
            .where(AutomationRule.enabled == True)  # noqa: E712
        )
        rows = result.all()

        for listing, rule, user in rows:
            now_time = datetime.now(timezone.utc).replace(tzinfo=None)
            due = (
                listing.last_checked_at is None
                or now_time - listing.last_checked_at >= timedelta(minutes=rule.check_interval_minutes)
            )
            has_credentials = bool(user.marketplace_client_secret_encrypted or user.marketplace_api_key_encrypted)
            if not due or not has_credentials:
                continue

            client_id = user.marketplace_client_id
            client_secret = decrypt_secret(user.marketplace_client_secret_encrypted) if user.marketplace_client_secret_encrypted else None
            api_key = decrypt_secret(user.marketplace_api_key_encrypted) if user.marketplace_api_key_encrypted else None

            await process_listing(session, listing, rule, client_id=client_id, client_secret=client_secret, api_key=api_key)


def start_scheduler():
    scheduler.add_job(run_due_listings, "interval", minutes=1, id="repricing_tick", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — checking for due listings every minute.")
