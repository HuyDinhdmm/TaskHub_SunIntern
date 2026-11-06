from fastapi.testclient import TestClient


def test_create_task_success(client: TestClient):
    payload = {
        "title": "Setup Layered Architecture",
        "description": "Router -> Service -> Repository -> Model",
        "status": "TODO",
        "priority": "HIGH",
    }
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == payload["title"]
    assert data["status"] == "TODO"
    assert data["priority"] == "HIGH"


def test_create_task_validation_error(client: TestClient):
    # Title trong la loi validate 422
    payload = {"title": ""}
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 422


def test_get_task_by_id(client: TestClient):
    create_resp = client.post(
        "/api/v1/tasks",
        json={"title": "Task Test", "status": "IN_PROGRESS"},
    )
    task_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Task Test"


def test_get_task_not_found(client: TestClient):
    response = client.get("/api/v1/tasks/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_tasks_and_filter(client: TestClient):
    client.post("/api/v1/tasks", json={"title": "Task 1", "status": "TODO", "priority": "LOW"})
    client.post("/api/v1/tasks", json={"title": "Task 2", "status": "DONE", "priority": "HIGH"})
    client.post("/api/v1/tasks", json={"title": "Task 3 Special", "status": "TODO", "priority": "MEDIUM"})

    # Test lay tat ca
    resp = client.get("/api/v1/tasks")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3

    # Test filter status
    resp_filter = client.get("/api/v1/tasks?status=DONE")
    assert resp_filter.json()["total"] == 1
    assert resp_filter.json()["items"][0]["title"] == "Task 2"

    # Test search
    resp_search = client.get("/api/v1/tasks?search=Special")
    assert resp_search.json()["total"] == 1
    assert resp_search.json()["items"][0]["title"] == "Task 3 Special"


def test_update_task_put(client: TestClient):
    create_resp = client.post("/api/v1/tasks", json={"title": "Old Task", "status": "TODO"})
    task_id = create_resp.json()["id"]

    update_payload = {
        "title": "Updated Task",
        "description": "New description",
        "status": "DONE",
        "priority": "HIGH",
    }
    response = client.put(f"/api/v1/tasks/{task_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Task"
    assert response.json()["status"] == "DONE"


def test_patch_task(client: TestClient):
    create_resp = client.post(
        "/api/v1/tasks",
        json={"title": "Patch Task", "description": "Keep this", "status": "TODO"},
    )
    task_id = create_resp.json()["id"]

    response = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "IN_PROGRESS"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["description"] == "Keep this"


def test_delete_task(client: TestClient):
    create_resp = client.post("/api/v1/tasks", json={"title": "Delete me"})
    task_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/tasks/{task_id}")
    assert del_resp.status_code == 204

    # Kiem tra lai xem da xoa chua
    get_resp = client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 404
