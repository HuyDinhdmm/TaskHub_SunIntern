import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_duplicate_email(client: AsyncClient):
    payload = {
        "email": "alice@example.com",
        "full_name": "Alice Nguyen",
        "password": "secret123",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["role"] == "MEMBER"
    assert "hashed_password" not in data

    # Dang ky trung email
    dup_resp = await client.post("/api/v1/auth/register", json=payload)
    assert dup_resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success_and_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "full_name": "Bob Tran",
            "password": "password123",
        },
    )

    # Sai mat khau
    bad_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "wrongpassword"},
    )
    assert bad_resp.status_code == 401

    # Dung mat khau
    ok_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "password123"},
    )
    assert ok_resp.status_code == 200
    tokens = ok_resp.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_token_and_logout_revoke(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "charlie@example.com",
            "full_name": "Charlie Le",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@example.com", "password": "password123"},
    )
    old_refresh = login_resp.json()["refresh_token"]

    # Refresh token -> ra cap token moi
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_resp.status_code == 200
    new_refresh = refresh_resp.json()["refresh_token"]
    assert new_refresh != old_refresh

    # Dung lai refresh token cu phai bi tu choi (token rotation)
    reuse_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reuse_resp.status_code == 401

    # Logout thu hoi refresh token moi
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout_resp.status_code == 200

    # Sau logout khong refresh duoc nua
    after_logout_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert after_logout_resp.status_code == 401
