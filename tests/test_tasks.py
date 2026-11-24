import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task_and_rbac(client: AsyncClient, sample_project: dict):
    headers = sample_project["headers"]
    proj_id = sample_project["project"]["id"]
    user_id = sample_project["user"]["id"]

    # 1. Tao task
    payload = {
        "title": "Build Redis Cache",
        "description": "Cache GET /projects/{id}/tasks",
        "status": "TODO",
        "priority": "HIGH",
        "assignee_id": user_id,
    }
    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    task = resp.json()
    assert task["title"] == "Build Redis Cache"
    assert task["project_id"] == proj_id

    # 2. Tao user khac khong o trong workspace -> 403
    await client.post(
        "/api/v1/auth/register",
        json={"email": "stranger@example.com", "full_name": "Stranger", "password": "password123"},
    )
    login_stranger = (await client.post(
        "/api/v1/auth/login",
        json={"email": "stranger@example.com", "password": "password123"},
    )).json()
    stranger_hdr = {"Authorization": f"Bearer {login_stranger['access_token']}"}

    bad_resp = await client.get(
        f"/api/v1/projects/{proj_id}/tasks",
        headers=stranger_hdr,
    )
    assert bad_resp.status_code == 403


@pytest.mark.asyncio
async def test_filtering_and_pagination(client: AsyncClient, sample_project: dict):
    headers = sample_project["headers"]
    proj_id = sample_project["project"]["id"]

    await client.post(f"/api/v1/projects/{proj_id}/tasks", json={"title": "Task 1", "status": "TODO", "priority": "LOW"}, headers=headers)
    await client.post(f"/api/v1/projects/{proj_id}/tasks", json={"title": "Task 2", "status": "DONE", "priority": "HIGH"}, headers=headers)
    await client.post(f"/api/v1/projects/{proj_id}/tasks", json={"title": "Task 3 Search", "status": "TODO", "priority": "URGENT"}, headers=headers)

    # Phan trang
    p_resp = await client.get(f"/api/v1/projects/{proj_id}/tasks?page=1&page_size=2", headers=headers)
    assert p_resp.status_code == 200
    data = p_resp.json()
    assert data["total"] == 3
    assert data["total_pages"] == 2
    assert len(data["items"]) == 2

    # Loc status
    st_resp = await client.get(f"/api/v1/projects/{proj_id}/tasks?status=DONE", headers=headers)
    assert st_resp.json()["total"] == 1
    assert st_resp.json()["items"][0]["title"] == "Task 2"

    # Loc search
    q_resp = await client.get(f"/api/v1/projects/{proj_id}/tasks?search=Search", headers=headers)
    assert q_resp.json()["total"] == 1
    assert q_resp.json()["items"][0]["title"] == "Task 3 Search"


@pytest.mark.asyncio
async def test_labels_and_comments_flow(client: AsyncClient, sample_project: dict):
    headers = sample_project["headers"]
    proj_id = sample_project["project"]["id"]

    # 1. Tao task
    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"title": "Task with Labels and Comments"},
        headers=headers,
    )
    task_id = t_resp.json()["id"]

    # 2. Tao label
    lbl_resp = await client.post(
        f"/api/v1/projects/{proj_id}/labels",
        json={"name": "backend", "color": "#10B981"},
        headers=headers,
    )
    assert lbl_resp.status_code == 201
    label_id = lbl_resp.json()["id"]

    # 3. Gan label cho task
    add_lbl = await client.post(
        f"/api/v1/tasks/{task_id}/labels/{label_id}",
        headers=headers,
    )
    assert add_lbl.status_code == 200
    assert len(add_lbl.json()["labels"]) == 1

    # 4. Comment tren task
    cm_resp = await client.post(
        f"/api/v1/tasks/{task_id}/comments",
        json={"content": "Great work on this task!"},
        headers=headers,
    )
    assert cm_resp.status_code == 201
    comment_id = cm_resp.json()["id"]

    # 5. Lay detail task co day du labels va comments
    detail = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["labels"]) == 1
    assert len(detail.json()["comments"]) == 1

    # 6. Xoa comment
    del_cm = await client.delete(f"/api/v1/comments/{comment_id}", headers=headers)
    assert del_cm.status_code == 204

    # 7. Bo label khoi task
    rem_lbl = await client.delete(f"/api/v1/tasks/{task_id}/labels/{label_id}", headers=headers)
    assert rem_lbl.status_code == 200
    assert len(rem_lbl.json()["labels"]) == 0
