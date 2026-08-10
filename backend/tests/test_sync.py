# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["name"] == "Eldorado Automated Repricing API"


@pytest.mark.asyncio
async def test_manual_sync_endpoint(client, auth_headers):
    # 1. Create a listing
    create_res = await client.post(
        "/listings",
        json={
            "marketplace_listing_id": "test-sync-101",
            "game_name": "World of Warcraft",
            "title": "100k WOW Gold",
            "current_price": 25.00,
        },
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    listing = create_res.json()
    listing_id = listing["id"]

    # 2. Trigger manual sync
    sync_res = await client.post(f"/listings/{listing_id}/sync", headers=auth_headers)
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["status"] == "synced"
    assert sync_data["listing_id"] == listing_id
