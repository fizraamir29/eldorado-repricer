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
async def test_marketplace_credentials_are_not_returned_in_responses(client, auth_headers):
    resp = await client.post(
        "/auth/marketplace-credentials",
        json={"client_id": "client-12345", "client_secret": "super-secret-eldorado-key"},
        headers=auth_headers,
    )
    assert resp.status_code == 204
    resp = await client.get("/listings", headers=auth_headers)
    assert "super-secret-eldorado-key" not in resp.text

