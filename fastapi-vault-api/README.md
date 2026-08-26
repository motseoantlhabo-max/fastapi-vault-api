# VaultAPI

A secure, multi-user RESTful backend for uploading, listing, downloading, and
managing personal media/document files — built with FastAPI, SQLAlchemy 2.0,
Pydantic v2, and JWT authentication.

Built as a capstone project synthesizing routing, database modeling, JWT
security, parameter validation, and async file handling into a single
production-shaped microservice.

## Features

- **JWT Authentication** — register/login with bcrypt-hashed passwords, OAuth2 password bearer flow.
- **Per-user file isolation** — every file is owned by exactly one user; all read/write/delete operations are scoped to the authenticated user and return `404` (not `403`) for other users' files, so existence isn't leaked.
- **UUID-based storage** — uploaded files are renamed to a UUID on disk to prevent filename collisions and path guessing.
- **Streamed uploads/downloads** — files are streamed to disk in chunks (with a size cap enforced mid-stream) and served back via `FileResponse`.
- **Pagination & filtering** — `GET /files/` supports `limit`, `offset`, `content_type`, and `filename_contains`.
- **Modular architecture** — separate `routers/`, `models/`, `schemas/`, `utils/` packages with dependency-injected DB sessions.
- **Test suite** — `pytest` tests covering auth, uploads, pagination, downloads, deletion, and cross-user privacy.

## Project Structure

```
fastapi-vault-api/
├── app/
│   ├── main.py          # FastAPI entrypoint & OpenAPI metadata
│   ├── config.py         # Environment settings (Pydantic BaseSettings)
│   ├── database.py       # SQLAlchemy engine & session dependency
│   ├── deps.py            # Shared dependencies (get_current_user)
│   ├── models/            # ORM models (User, UserFile)
│   ├── schemas/           # Pydantic validation schemas
│   ├── routers/           # auth.py, users.py, files.py
│   └── utils/              # Password hashing, JWT, file helpers
├── uploads/                # Local file storage (gitignored)
├── tests/                  # Pytest suite
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/<your-username>/fastapi-vault-api.git
cd fastapi-vault-api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Generate a strong `SECRET_KEY`:

```bash
openssl rand -hex 32
```

Paste the result into `.env` as `SECRET_KEY=...`. The default `DATABASE_URL`
uses SQLite and requires no further setup; swap it for a PostgreSQL URL if
preferred (see the commented example in `.env.example`).

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Tables are created automatically on startup. The API is now available at
`http://127.0.0.1:8000`, with interactive docs at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 5. Run the tests

```bash
pytest -v
```

Tests use an isolated in-memory SQLite database and a temp upload directory,
so they never touch your real `.env` database or `uploads/` folder.

## API Reference

### Authentication

| Method | Endpoint         | Auth | Description                                      |
|--------|------------------|------|---------------------------------------------------|
| POST   | `/auth/register` | No   | Create a new account.                              |
| POST   | `/auth/login`    | No   | Exchange credentials (OAuth2 form) for a JWT.       |

### Users

| Method | Endpoint     | Auth | Description               |
|--------|--------------|------|----------------------------|
| GET    | `/users/me`  | Yes  | Get the current user's profile. |

### Files

| Method | Endpoint                     | Auth | Description                                              |
|--------|-------------------------------|------|-------------------------------------------------------------|
| POST   | `/files/upload`               | Yes  | Upload an image or PDF (size-limited, UUID-named on disk).   |
| GET    | `/files/`                     | Yes  | List your files. Query params: `limit`, `offset`, `content_type`, `filename_contains`. |
| GET    | `/files/{file_id}/download`   | Yes  | Download one of your files.                                  |
| DELETE | `/files/{file_id}`            | Yes  | Delete one of your files.                                      |

### Example: register, log in, upload

```bash
# Register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","username":"alice","password":"supersecret1"}'

# Log in
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=alice&password=supersecret1"
# -> {"access_token": "...", "token_type": "bearer"}

# Upload a file
curl -X POST http://127.0.0.1:8000/files/upload \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "upload=@report.pdf;type=application/pdf"

# List files (paginated)
curl "http://127.0.0.1:8000/files/?limit=10&offset=0" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Download a file
curl -OJ "http://127.0.0.1:8000/files/<FILE_ID>/download" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Security Notes

- Passwords are hashed with `bcrypt` via `passlib`; plaintext passwords are never stored or logged.
- JWTs are signed with `HS256` using `SECRET_KEY` and expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60).
- File access is authorization-checked by ownership (`owner_id`) on every read/download/delete — not just by valid token.
- Uploaded filenames are never trusted for disk storage; a UUID-derived name is generated server-side.
- Only `image/jpeg`, `image/png`, `image/gif`, and `application/pdf` are accepted by default (configurable via `ALLOWED_CONTENT_TYPES`).

## Git Workflow (per project guidelines)

- Do not commit directly to `main`.
- Use feature branches per phase, e.g. `feat/db-setup`, `feat/jwt-auth`, `feat/file-handling`.
- Open a Pull Request per phase for review before merging.

Suggested commit sequence:

1. `feat/db-setup` — project scaffold, `.env.example`, `User`/`UserFile` models, DB session dependency.
2. `feat/jwt-auth` — password hashing, `/auth/register`, `/auth/login`, `get_current_user`.
3. `feat/file-handling` — `/files/upload`, UUID storage, `/files/` pagination & filtering.
4. `feat/file-access-docs-tests` — `/files/{id}/download`, cross-user privacy checks, OpenAPI descriptions, test suite.

## License

Provided for educational/internship evaluation purposes.
