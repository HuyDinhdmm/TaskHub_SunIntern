# TaskHub - Task Management API

Dự án thực tập TaskHub Backend sử dụng FastAPI, SQLAlchemy và SQLite.

## Cấu trúc thư mục (Layered Architecture)
```
app/
├── api/             # Routing và Dependency Injection
│   ├── deps.py
│   └── v1/
│       ├── endpoints/
│       │   ├── health.py
│       │   └── tasks.py
│       └── router.py
├── core/            # Config và Lifespan database
│   ├── config.py
│   ├── database.py
│   └── lifespan.py
├── models/          # SQLAlchemy Models
│   ├── base.py
│   └── task.py
├── repositories/    # Truy vấn cơ sở dữ liệu
│   └── task_repository.py
├── schemas/         # Pydantic v2 schemas
│   └── task.py
├── services/        # Xử lý business logic
│   └── task_service.py
└── main.py          # FastAPI app instance
tests/               # Unit test với pytest
```

## Hướng dẫn cài đặt và chạy

1. Cài đặt môi trường ảo:
```bash
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate
```

2. Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

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
