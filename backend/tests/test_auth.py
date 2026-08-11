import pytest


@pytest.mark.asyncio
async def test_signup_creates_user(client):
    resp = await client.post("/auth/signup", json={"email": "new@example.com", "password": "password123"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "id" in body


@pytest.mark.asyncio
async def test_signup_rejects_duplicate_email(client):
    await client.post("/auth/signup", json={"email": "dupe@example.com", "password": "password123"})
    resp = await client.post("/auth/signup", json={"email": "dupe@example.com", "password": "password123"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_succeeds_with_correct_password(client):
    await client.post("/auth/signup", json={"email": "login@example.com", "password": "password123"})
    resp = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_fails_with_wrong_password(client):
    await client.post("/auth/signup", json={"email": "login2@example.com", "password": "password123"})
    resp = await client.post(
        "/auth/login",
        data={"username": "login2@example.com", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_requires_token(client):
    resp = await client.get("/listings")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_signup_with_metadata_and_get_me(client):
    signup_resp = await client.post(
        "/auth/signup",
        json={
            "email": "meta@example.com",
            "password": "password123",
            "full_name": "Eldorado Admin",
            "username": "eldorado_bot_admin",
            "age": 28,
        },
    )
    assert signup_resp.status_code == 201
    data = signup_resp.json()
    assert data["full_name"] == "Eldorado Admin"
    assert data["username"] == "eldorado_bot_admin"
    assert data["age"] == 28

    login_resp = await client.post(
        "/auth/login",
        data={"username": "eldorado_bot_admin", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "meta@example.com"
    assert me_data["full_name"] == "Eldorado Admin"
    assert me_data["last_login_at"] is not None


@pytest.mark.asyncio
async def test_marketplace_credentials_are_not_returned_in_responses(client, auth_headers):
    resp = await client.post(
        "/auth/marketplace-credentials",
        json={"client_id": "client-12345", "client_secret": "super-secret-eldorado-key"},
        headers=auth_headers,
    )
    assert resp.status_code == 204
    resp = await client.get("/listings", headers=auth_headers)
    assert "super-secret-eldorado-key" not in resp.text

