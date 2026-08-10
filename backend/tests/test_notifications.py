import pytest

from app.models import Notification
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_unread_count_starts_at_zero(client, auth_headers):
    resp = await client.get("/notifications/unread-count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read(client, auth_headers):
    # Look up the just-created user id via the listings owner check isn't
    # exposed directly, so we insert notifications straight into the test DB.
    me = await client.post(
        "/listings",
        json={"marketplace_listing_id": "eld-200", "game_name": "WoW Gold", "title": "Notif test", "current_price": 5.00},
        headers=auth_headers,
    )
    listing = me.json()
    user_resp = await client.get("/listings", headers=auth_headers)
    assert user_resp.status_code == 200

    async with TestSessionLocal() as session:
        # Fetch the listing's owning user id through the listing row itself
        from sqlalchemy import select
        from app.models import Listing
        result = await session.execute(select(Listing).where(Listing.id == listing["id"]))
        db_listing = result.scalar_one()

        session.add(Notification(
            user_id=db_listing.user_id,
            listing_id=db_listing.id,
            level="info",
            title="Test notification",
            message="Price updated to stay competitive.",
        ))
        await session.commit()

    resp = await client.get("/notifications/unread-count", headers=auth_headers)
    assert resp.json()["count"] == 1

    resp = await client.post("/notifications/mark-all-read", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get("/notifications/unread-count", headers=auth_headers)
    assert resp.json()["count"] == 0
