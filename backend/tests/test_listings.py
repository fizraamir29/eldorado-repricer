import pytest


@pytest.mark.asyncio
async def test_create_and_list_listing(client, auth_headers):
    resp = await client.post(
        "/listings",
        json={"marketplace_listing_id": "eld-123", "game_name": "WoW Gold", "title": "1000 Gold", "current_price": 12.50},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "1000 Gold"
    assert body["current_price"] == 12.50

    resp = await client.get("/listings", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_new_listing_gets_a_default_disabled_rule(client, auth_headers):
    create = await client.post(
        "/listings",
        json={"marketplace_listing_id": "eld-124", "game_name": "WoW Gold", "title": "2000 Gold", "current_price": 20.00},
        headers=auth_headers,
    )
    listing_id = create.json()["id"]

    resp = await client.get(f"/listings/{listing_id}/rule", headers=auth_headers)
    assert resp.status_code == 200
    rule = resp.json()
    assert rule["enabled"] is False
    assert rule["min_price"] == pytest.approx(14.0)  # 20 * 0.7
    assert rule["max_price"] == pytest.approx(26.0)  # 20 * 1.3


@pytest.mark.asyncio
async def test_update_rule_rejects_min_greater_than_max(client, auth_headers):
    create = await client.post(
        "/listings",
        json={"marketplace_listing_id": "eld-125", "game_name": "WoW Gold", "title": "500 Gold", "current_price": 5.00},
        headers=auth_headers,
    )
    listing_id = create.json()["id"]

    resp = await client.put(
        f"/listings/{listing_id}/rule",
        json={"enabled": True, "min_price": 10.0, "max_price": 5.0, "undercut_step": 0.01, "check_interval_minutes": 5},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_user_cannot_see_another_users_listing(client, auth_headers):
    create = await client.post(
        "/listings",
        json={"marketplace_listing_id": "eld-126", "game_name": "WoW Gold", "title": "Private listing", "current_price": 9.99},
        headers=auth_headers,
    )
    listing_id = create.json()["id"]

    # A second, different user should not be able to see the first user's listing.
    await client.post("/auth/signup", json={"email": "otheruser@example.com", "password": "password123"})
    login = await client.post(
        "/auth/login",
        data={"username": "otheruser@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(f"/listings/{listing_id}/rule", headers=other_headers)
    assert resp.status_code == 404

    resp = await client.get("/listings", headers=other_headers)
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_listing(client, auth_headers):
    create = await client.post(
        "/listings",
        json={"marketplace_listing_id": "eld-127", "game_name": "WoW Gold", "title": "To delete", "current_price": 3.00},
        headers=auth_headers,
    )
    listing_id = create.json()["id"]

    resp = await client.delete(f"/listings/{listing_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get("/listings", headers=auth_headers)
    assert resp.json() == []
