# TaskHub - Task Management API

Dự án thực tập TaskHub Backend sử dụng FastAPI, SQLAlchemy 2.x async và Alembic.

## Cấu trúc thư mục (Layered Architecture)
```
alembic/             # Alembic async migrations
app/
├── api/             # Routing và Dependency Injection
│   ├── deps.py
│   └── v1/
│       ├── endpoints/
│       │   ├── health.py
│       │   ├── projects.py
│       │   ├── tasks.py
│       │   ├── users.py
│       │   └── workspaces.py
│       └── router.py
├── core/            # Config, Async Database & Lifespan
│   ├── config.py
│   ├── database.py
│   └── lifespan.py
├── models/          # SQLAlchemy 2.x Models & Relationships
│   ├── base.py
│   ├── comment.py
│   ├── enums.py
│   ├── label.py
│   ├── project.py
│   ├── task.py
│   ├── user.py
│   └── workspace.py
├── repositories/    # BaseRepository[T] và Async Repositories
│   ├── base.py
│   ├── project_repository.py
│   ├── task_repository.py
│   ├── user_repository.py
│   └── workspace_repository.py
├── schemas/         # Pydantic v2 schemas
├── services/        # Business logic (async)
└── main.py          # FastAPI app instance
tests/               # Async unit/integration tests (pytest-asyncio)
```

## Database Schema (8 bảng chính)
- `users`: `id`, `email`, `full_name`, `hashed_password`, `role`, `is_active`, `created_at`
- `workspaces`: `id`, `name`, `owner_id`, `created_at`
- `workspace_members`: `workspace_id`, `user_id`, `role`
- `projects`: `id`, `workspace_id`, `name`, `description`, `status`, `created_at`
- `tasks`: `id`, `project_id`, `assignee_id`, `title`, `description`, `status`, `priority`, `due_date`, `created_by`, `created_at`
- `labels`: `id`, `project_id`, `name`, `color`
- `task_labels`: `task_id`, `label_id`
- `comments`: `id`, `task_id`, `author_id`, `content`, `created_at`

## Hướng dẫn cài đặt và chạy

1. Tạo môi trường ảo và cài thư viện:
```bash
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

2. Chạy Alembic migration để tạo các bảng trong database:
```bash
alembic upgrade head
```
*(Tạo migration mới khi sửa model: `alembic revision --autogenerate -m "message"`)*

3. Chạy server:
```bash
uvicorn app.main:app --reload
```
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

4. Chạy kiểm thử:
```bash
python -m pytest -v
```
