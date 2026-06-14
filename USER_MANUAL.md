# Job Finders Sierra Leone — User Manual

## Overview
Job Finders Sierra Leone is a REST API that connects youth with job opportunities. It is built with FastAPI and supports PostgreSQL (production) or SQLite (development). The API provides authentication, role-based access control, job listings, applications, and secure resume uploads.

---

## Quick Links
- Health: `GET /health` — `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Installation
Prerequisites: Python 3.8+, Git, PostgreSQL (optional for prod).

1. Clone the repository and enter the project folder.

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration
Copy `.env.example` to `.env` and edit values or create `.env` with the following minimum keys:

```
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>:5432/JobFinders_SL
SECRET_KEY=<strong-random-string>
# Optional overrides:
# UPLOAD_DIR=uploads
# MAX_FILE_SIZE_MB=5
```

- For quick local development you can use SQLite:

```
DATABASE_URL=sqlite+aiosqlite:///./joblinkus.db
SECRET_KEY=dev-secret-key
```

See `config.py` for all settings loaded from environment.

---

## Running the App (Development)

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

The server will start on port `8000` by default.

---

## API Overview
Base path: `/api/v1`

Resources:
- Authentication: `/api/v1/auth` (register, login, me, profile, resume upload)
- Jobs: `/api/v1/jobs` (list, retrieve, create, update, delete, apply)
- Applications: `/api/v1/applications` (view, patch status)

### Authentication & JWT
- Login uses OAuth2 password flow and issues a JWT.
- Include token in requests using header: `Authorization: Bearer <token>`

---

## Examples

### Register (public)
Request (JSON):

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123"}'
```

Successful response: `201 Created` with user metadata (no password returned).

Field validation (schema `UserCreate`):
- `username`: required, 3–50 chars
- `email`: required, valid email
- `password`: required, min 6 chars
- `role`: optional, defaults to `seeker` (allowed: `seeker`, `employer`, `admin`)

If you receive `422 Unprocessable Entity`, ensure `Content-Type: application/json` and required fields are present.

### Login (form data)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -F "username=alice" -F "password=secret123"
```

Response includes: `access_token`, `token_type`, `role`, `username`.

Use the token in protected requests:

```
-H "Authorization: Bearer <access_token>"
```

---

## Seeker Profile & Resume Upload
- Endpoint: `POST /api/v1/auth/profile/resume` (authenticated seeker)
- Accepts only PDF (`application/pdf`) and enforces `MAX_FILE_SIZE_MB` (default 5MB).
- Files are saved under the `UPLOAD_DIR` and served at `/uploads/<filename>`.

Example upload with `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/profile/resume \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/resume.pdf;type=application/pdf"
```

---

## Database Schema Summary
Key tables (see `models.py`):
- `users` — id, username, email, hashed_password, role, created_at
- `seeker_profiles` — id, user_id, full_name, bio, resume_url, skills, education
- `job_listings` — id, employer_id, title, description, requirements, location, job_type, salary_range, is_active
- `applications` — id, job_id, seeker_id, resume_url, cover_letter, status, applied_at

Sample SQL queries:

- View all users (includes hashed_password):
```sql
SELECT * FROM users;
```

- View public user columns only:
```sql
SELECT id, username, email, role, created_at
FROM users
ORDER BY created_at DESC;
```

---

## Deployment
### Docker

```bash
docker build -t job-api .
docker run -d -p 8000:8000 --env-file .env --name job-api-instance job-api
```

### Production notes
- Use a managed PostgreSQL or secure server for `DATABASE_URL`.
- Set `SECRET_KEY` to a cryptographically secure random value.
- Run with a process manager (systemd, supervisor) or inside a container orchestration system.

---

## Verification & Tests
Run the provided verification script which performs 20 validation scenarios:

```bash
source .venv/bin/activate
python verify_api.py
```

---

## Troubleshooting
- 422 on register: confirm `Content-Type: application/json` and required fields.
- Port in use: find and kill process:

```bash
lsof -i tcp:8000 -sTCP:LISTEN -t
kill <pid>
```

- Missing env vars: ensure `.env` exists or export variables in shell.
- Postgres connection errors: verify credentials and that the DB exists.

---

## Appendix
- Main files: `main.py`, `config.py`, `database.py`, `models.py`, `schemas.py`, `routers/*`
- Change Swagger UI title: edit the `title` parameter in `FastAPI(...)` within `main.py` and restart the server.

---

If you want this manual converted to PDF, split into separate quickstart/admin manuals, or tailored with screenshots, tell me which format you prefer.
