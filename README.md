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
│       │   ├── auth.py
│       │   ├── health.py
│       │   ├── projects.py
│       │   ├── tasks.py
│       │   ├── users.py
│       │   └── workspaces.py
│       └── router.py
├── core/            # Config, Security (JWT/bcrypt), Async DB & Lifespan
│   ├── config.py
│   ├── database.py
│   ├── lifespan.py
│   └── security.py
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
- `refresh_tokens`: `id`, `user_id`, `jti`, `expires_at`, `is_revoked`, `created_at`

## Auth & User Profile Endpoints
- `POST /api/v1/auth/register` - Đăng ký tài khoản (bcrypt)
- `POST /api/v1/auth/login` - Đăng nhập nhận JWT access + refresh token
- `POST /api/v1/auth/refresh` - Cấp lại token mới (refresh token rotation)
- `POST /api/v1/auth/logout` - Đăng xuất và thu hồi refresh token
- `GET /api/v1/users/me` - Xem thông tin cá nhân (Bearer token)
- `PATCH /api/v1/users/me` - Cập nhật hồ sơ (full_name, email)
- `PATCH /api/v1/users/me/password` - Đổi mật khẩu và thu hồi refresh token cũ

## Workspace & Project Endpoints (RBAC)
- `POST /api/v1/workspaces` - Tạo workspace (tự gán OWNER)
- `GET /api/v1/workspaces/{id}` - Xem thông tin workspace
- `PUT /api/v1/workspaces/{id}` - Sửa workspace (chỉ OWNER)
- `DELETE /api/v1/workspaces/{id}` - Xóa workspace (chỉ OWNER)
- `POST /api/v1/workspaces/{id}/members` - Mời member (OWNER gán OWNER/EDITOR/VIEWER)
- `DELETE /api/v1/workspaces/{id}/members/{user_id}` - Xóa member (chỉ OWNER)
- `PATCH /api/v1/workspaces/{id}/members/{user_id}` - Phân quyền lại member
- `POST /api/v1/workspaces/{id}/projects` - Tạo project trong workspace (OWNER/EDITOR)
- `GET /api/v1/projects/{id}` - Xem project
- `PATCH /api/v1/projects/{id}` - Cập nhật/archive project (OWNER/EDITOR)
- `DELETE /api/v1/projects/{id}` - Xóa project (chỉ OWNER)

## Task, Label & Comment Endpoints (Redis Caching & Filter)
- `GET /api/v1/projects/{id}/tasks` - Lấy danh sách task (lọc status, priority, assignee, search, phân trang, có cache Redis)
- `POST /api/v1/projects/{id}/tasks` - Tạo task trong project (invalidate cache)
- `GET /api/v1/tasks/{id}` - Chi tiết task kèm labels và comments
- `PATCH /api/v1/tasks/{id}` - Sửa task (status, priority, assignee, due_date)
- `DELETE /api/v1/tasks/{id}` - Xóa task
- `POST /api/v1/projects/{id}/labels` - Tạo label trong project
- `GET /api/v1/projects/{id}/labels` - Danh sách label của project
- `POST /api/v1/tasks/{id}/labels/{label_id}` - Gán label cho task
- `DELETE /api/v1/tasks/{id}/labels/{label_id}` - Bỏ label khỏi task
- `POST /api/v1/tasks/{id}/comments` - Thêm comment vào task
- `DELETE /api/v1/comments/{id}` - Xóa comment (tác giả hoặc owner)

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
