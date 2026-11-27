import pytest
from httpx import AsyncClient


async def _create_user_and_token(client: AsyncClient, email: str) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return login_resp.json()


@pytest.mark.asyncio
async def test_workspace_crud_and_rbac(client: AsyncClient):
    owner = await _create_user_and_token(client, "owner@example.com")
    member = await _create_user_and_token(client, "member@example.com")
    other = await _create_user_and_token(client, "other@example.com")

    owner_hdr = {"Authorization": f"Bearer {owner['access_token']}"}
    member_hdr = {"Authorization": f"Bearer {member['access_token']}"}
    other_hdr = {"Authorization": f"Bearer {other['access_token']}"}

    # 1. Tao workspace
    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Engineering Workspace"},
        headers=owner_hdr,
    )
    assert ws_resp.status_code == 201
    ws = ws_resp.json()
    ws_id = ws["id"]

    # 2. Lay profile user member de lay ID
    user_me = await client.get("/api/v1/users/me", headers=member_hdr)
    member_id = user_me.json()["id"]

    # 3. Invite member voi role EDITOR
    inv_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": member_id, "role": "EDITOR"},
        headers=owner_hdr,
    )
    assert inv_resp.status_code == 201
    assert inv_resp.json()["role"] == "EDITOR"

    # 4. Member xem duoc workspace
    get_resp = await client.get(f"/api/v1/workspaces/{ws_id}", headers=member_hdr)
    assert get_resp.status_code == 200

    # 5. User ngoai khong xem duoc -> 403
    other_resp = await client.get(f"/api/v1/workspaces/{ws_id}", headers=other_hdr)
    assert other_resp.status_code == 403

    # 6. Member sua workspace -> 403 (chi OWNER moi sua duoc)
    patch_ws = await client.put(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "Hacked Name"},
        headers=member_hdr,
    )
    assert patch_ws.status_code == 403

    # 7. Owner sua workspace -> 200
    owner_update = await client.put(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "Updated Engineering"},
        headers=owner_hdr,
    )
    assert owner_update.status_code == 200
    assert owner_update.json()["name"] == "Updated Engineering"

    # 8. Phan quyen lai member thanh VIEWER
    role_update = await client.patch(
        f"/api/v1/workspaces/{ws_id}/members/{member_id}",
        json={"role": "VIEWER"},
        headers=owner_hdr,
    )
    assert role_update.status_code == 200
    assert role_update.json()["role"] == "VIEWER"

    # 9. Remove member
    del_mem = await client.delete(
        f"/api/v1/workspaces/{ws_id}/members/{member_id}",
        headers=owner_hdr,
    )
    assert del_mem.status_code == 204


@pytest.mark.asyncio
async def test_project_crud_and_rbac(client: AsyncClient):
    owner = await _create_user_and_token(client, "proj_owner@example.com")
    editor = await _create_user_and_token(client, "proj_editor@example.com")
    viewer = await _create_user_and_token(client, "proj_viewer@example.com")

    owner_hdr = {"Authorization": f"Bearer {owner['access_token']}"}
    editor_hdr = {"Authorization": f"Bearer {editor['access_token']}"}
    viewer_hdr = {"Authorization": f"Bearer {viewer['access_token']}"}

    # Tao workspace
    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Product Workspace"},
        headers=owner_hdr,
    )
    ws_id = ws_resp.json()["id"]

    # Add editor & viewer
    editor_info = (await client.get("/api/v1/users/me", headers=editor_hdr)).json()
    viewer_info = (await client.get("/api/v1/users/me", headers=viewer_hdr)).json()

    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": editor_info["id"], "role": "EDITOR"},
        headers=owner_hdr,
    )
    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": viewer_info["id"], "role": "VIEWER"},
        headers=owner_hdr,
    )

    # VIEWER tao project -> 403
    bad_proj = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Unauthorized Project"},
        headers=viewer_hdr,
    )
    assert bad_proj.status_code == 403

    # EDITOR tao project -> 201
    proj_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "TaskHub API v2", "description": "Core services"},
        headers=editor_hdr,
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    # VIEWER xem project -> 200
    view_proj = await client.get(f"/api/v1/projects/{proj_id}", headers=viewer_hdr)
    assert view_proj.status_code == 200

    # EDITOR archive project -> 200
    arch_proj = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"status": "ARCHIVED"},
        headers=editor_hdr,
    )
    assert arch_proj.status_code == 200
    assert arch_proj.json()["status"] == "ARCHIVED"

    # EDITOR xoa project -> 403 (chi OWNER duoc xoa)
    del_by_editor = await client.delete(f"/api/v1/projects/{proj_id}", headers=editor_hdr)
    assert del_by_editor.status_code == 403

    # OWNER xoa project -> 204
    del_by_owner = await client.delete(f"/api/v1/projects/{proj_id}", headers=owner_hdr)
    assert del_by_owner.status_code == 204
