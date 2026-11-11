# Auth, Role & Permission Service API

An asynchronous RESTful API for Authentication, User Management, and Role-Based Access Control (RBAC), built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **Alembic**, and backed by **Supabase PostgreSQL**.

---

## Features

- **Supabase PostgreSQL Integration**: Fully asynchronous engine supporting Supabase connection poolers (port `6543`) and direct connections (port `5432`).
- **Authentication**: JWT access tokens (HS256) and refresh tokens with PBKDF2 HMAC SHA-256 secure password hashing.
- **RBAC (Role-Based Access Control)**:
  - Granular permissions with categories (`Dashboard`, `User Management`, `Role & Permissions`, `System Settings`).
  - Roles with dynamic permission assignments (`super_admin`, `admin`, `staff`, `teacher`, `student`).
  - Declarative route guards (`require_permission(...)`).
- **Database Migrations**: Pre-configured async Alembic migrations.

---

## Database Schema (Auth Only)

1. **`roles`**: System roles (`id`, `name`, `description`, `created_at`, `updated_at`).
2. **`permissions`**: Permission catalog (`id`, `codename`, `name`, `group`, `created_at`).
3. **`role_permissions`**: Mapping table linking roles to permissions with cascade deletion.
4. **`users`**: User accounts (`id`, `email`, `full_name`, `hashed_password`, `role_id`, `status`, `surface`, `is_verified`, `last_login_at`, timestamps).

---

## Quickstart

### 1. Environment Setup
Create or update `.env`:
```env
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
JWT_SECRET=your-secure-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
ENVIRONMENT=development
```

### 2. Run Database Migrations
```bash
./venv/bin/alembic upgrade head
```

### 3. Start the API Server
```bash
./venv/bin/uvicorn app.main:app --reload --port 8000
```

- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## API Endpoints

All endpoints are mounted under `/api/v1`.

### 1. Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and receive JWT access & refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Exchange a refresh token for a new access token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile |

### 2. Users (`/api/v1/users`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/users` | List users with pagination, role, and search filters |
| `POST` | `/api/v1/users` | Create user with explicit role assignment |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `PUT` | `/api/v1/users/{id}` | Update user details or reassign role |
| `DELETE` | `/api/v1/users/{id}` | Delete a user |

### 3. Roles & Role Permissions (`/api/v1/roles`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/roles` | List all roles with associated permissions |
| `POST` | `/api/v1/roles` | Create a new role with optional initial permissions |
| `GET` | `/api/v1/roles/{id}` | Get role details by ID |
| `PUT` | `/api/v1/roles/{id}` | Update role name or description |
| `DELETE` | `/api/v1/roles/{id}` | Delete a role |
| `POST` | `/api/v1/roles/seed-defaults` | Seed default roles (`super_admin`, `admin`, `staff`, etc.) |
| `GET` | `/api/v1/roles/{role_id}/permissions` | List permissions assigned to a role |
| `POST` | `/api/v1/roles/{role_id}/permissions` | Batch-replace permissions for a role |
| `POST` | `/api/v1/roles/{role_id}/permissions/{perm_id}` | Attach a single permission to a role |
| `DELETE` | `/api/v1/roles/{role_id}/permissions/{perm_id}` | Detach a permission from a role |

### 4. Permissions (`/api/v1/permissions`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/permissions` | List all system permissions |
| `POST` | `/api/v1/permissions` | Create a custom permission |
| `GET` | `/api/v1/permissions/{id}` | Get permission by ID |
| `DELETE` | `/api/v1/permissions/{id}` | Delete a permission |
| `POST` | `/api/v1/permissions/seed` | Seed default permission catalog |
