import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_summary_empty(client: AsyncClient, auth_headers: dict):
    response = await client.get("/analytics/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_listings"] == 0
    assert data["active_bots"] == 0
    assert data["total_price_changes"] == 0
    assert data["success_rate"] == 100.0


@pytest.mark.asyncio
async def test_analytics_summary_with_listings(client: AsyncClient, auth_headers: dict):
    # 1. Create a listing
    listing_resp = await client.post(
        "/listings",
        json={
            "marketplace_listing_id": "analytics-offer-1",
            "game_name": "FC 25",
            "title": "1,000,000 Coins",
            "current_price": 45.00,
        },
        headers=auth_headers,
    )
    assert listing_resp.status_code == 201

    # 2. Fetch summary
    response = await client.get("/analytics/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_listings"] == 1
    assert data["active_bots"] == 0  # disabled by default
