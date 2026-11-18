import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient, sample_project: dict):
    project_id = sample_project["project"]["id"]
    user_id = sample_project["user"]["id"]

    payload = {
        "project_id": project_id,
        "assignee_id": user_id,
        "created_by": user_id,
        "title": "Setup SQLAlchemy Async",
        "description": "Chuyen tu sync sang async session",
        "status": "TODO",
        "priority": "HIGH",
    }
    response = await client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["project_id"] == project_id
    assert data["assignee_id"] == user_id
    assert data["title"] == payload["title"]
    assert data["status"] == "TODO"


@pytest.mark.asyncio
async def test_create_task_invalid_project(client: AsyncClient):
    payload = {
        "project_id": 9999,
        "title": "Task khong co project",
    }
    response = await client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_task_validation_error(client: AsyncClient, sample_project: dict):
    payload = {
        "project_id": sample_project["project"]["id"],
        "title": "",
    }
    response = await client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_task_by_id(client: AsyncClient, sample_project: dict):
    project_id = sample_project["project"]["id"]
    create_resp = await client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Task Test", "status": "IN_REVIEW"},
    )
    task_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Task Test"
    assert response.json()["status"] == "IN_REVIEW"


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    response = await client.get("/api/v1/tasks/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_tasks_pagination_and_filter(client: AsyncClient, sample_project: dict):
    project_id = sample_project["project"]["id"]
    await client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Task 1", "status": "TODO"})
    await client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Task 2", "status": "DONE"})
    await client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Task 3 Alembic", "status": "IN_PROGRESS"})

    # Test phan trang
    resp = await client.get("/api/v1/tasks?page=1&page_size=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2

    # Test filter status
    resp_filter = await client.get("/api/v1/tasks?status=DONE")
    assert resp_filter.json()["total"] == 1
    assert resp_filter.json()["items"][0]["title"] == "Task 2"

    # Test search
    resp_search = await client.get("/api/v1/tasks?search=Alembic")
    assert resp_search.json()["total"] == 1
    assert resp_search.json()["items"][0]["title"] == "Task 3 Alembic"


@pytest.mark.asyncio
async def test_update_and_patch_task(client: AsyncClient, sample_project: dict):
    project_id = sample_project["project"]["id"]
    create_resp = await client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Old Task", "description": "Keep me"},
    )
    task_id = create_resp.json()["id"]

    # PATCH
    patch_resp = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "IN_PROGRESS"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "IN_PROGRESS"
    assert patch_resp.json()["description"] == "Keep me"

    # PUT
    put_resp = await client.put(
        f"/api/v1/tasks/{task_id}",
        json={
            "project_id": project_id,
            "title": "Updated Task",
            "description": "New desc",
            "status": "DONE",
            "priority": "URGENT",
        },
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["title"] == "Updated Task"
    assert put_resp.json()["priority"] == "URGENT"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, sample_project: dict):
    project_id = sample_project["project"]["id"]
    create_resp = await client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Delete me"},
    )
    task_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/tasks/{task_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 404
