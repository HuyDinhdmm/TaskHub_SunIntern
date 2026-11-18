import pytest
from httpx import AsyncClient


async def _register_and_login(
    client: AsyncClient,
    email: str = "user@example.com",
    full_name: str = "Test User",
    password: str = "password123",
) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": full_name, "password": password},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()


@pytest.mark.asyncio
async def test_get_my_profile(client: AsyncClient):
    # Khong co token -> 401
    unauth_resp = await client.get("/api/v1/users/me")
    assert unauth_resp.status_code == 401

    tokens = await _register_and_login(client, email="me@example.com", full_name="Huy Intern")

    # Dung refresh token thay cho access token -> 401
    wrong_type_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert wrong_type_resp.status_code == 401

    # Dung access token -> 200
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Huy Intern"


@pytest.mark.asyncio
async def test_update_my_profile(client: AsyncClient):
    tokens = await _register_and_login(client, email="update@example.com", full_name="Old Name")
    await _register_and_login(client, email="other@example.com", full_name="Other User")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Update thanh cong
    resp = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "New Name", "email": "updated@example.com"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"
    assert resp.json()["email"] == "updated@example.com"

    # Update trung email cua nguoi khac -> 400
    dup_resp = await client.patch(
        "/api/v1/users/me",
        json={"email": "other@example.com"},
        headers=headers,
    )
    assert dup_resp.status_code == 400


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient):
    tokens = await _register_and_login(client, email="pw@example.com", password="oldpassword")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Sai mat khau hien tai -> 400
    bad_resp = await client.patch(
        "/api/v1/users/me/password",
        json={"current_password": "wrong", "new_password": "newpassword123"},
        headers=headers,
    )
    assert bad_resp.status_code == 400

    # Doi mat khau thanh cong
    ok_resp = await client.patch(
        "/api/v1/users/me/password",
        json={"current_password": "oldpassword", "new_password": "newpassword123"},
        headers=headers,
    )
    assert ok_resp.status_code == 200

    # Refresh token cu bi thu hoi sau khi doi mat khau
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 401

    # Login bang mat khau cu -> fail, mat khau moi -> ok
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "pw@example.com", "password": "oldpassword"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "pw@example.com", "password": "newpassword123"},
    )
    assert new_login.status_code == 200
