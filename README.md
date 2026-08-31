# VaultAPI

A secure, multi-user RESTful backend for uploading, listing, downloading, and managing personal media/document files — built with **FastAPI, SQLAlchemy 2.0, Pydantic v2, and JWT authentication**.

Built as a capstone project synthesizing routing, database modeling, JWT security, parameter validation, dependency injection, and file handling into a single production-shaped microservice.

## Features

* **JWT Authentication** — register/login with bcrypt-hashed passwords and OAuth2 password bearer flow.
* **Separated Authentication Architecture** — authentication responsibilities are organized into `auth/authentication.py` and `auth/oauth2.py` for clearer separation of login, JWT handling, and current-user validation.
* **Per-user file isolation** — every file is owned by exactly one user; all read/write/delete operations are scoped to the authenticated user and return `404` (not `403`) for other users' files, so file existence isn't leaked.
* **UUID-based storage** — uploaded files are renamed to a UUID on disk to prevent filename collisions and path guessing.
* **Streamed uploads/downloads** — files are streamed to disk in chunks with a size cap enforced during upload and served back via `FileResponse`.
* **Pagination & filtering** — `GET /files/` supports `limit`, `offset`, `content_type`, and `filename_contains`.
* **Modular architecture** — separate `auth/`, `routers/`, `models/`, `schemas/`, and `utils/` packages with dependency-injected database sessions.
* **Password security** — passwords are hashed using bcrypt and plaintext passwords are never stored.
* **Test suite** — `pytest` tests covering authentication, uploads, pagination, downloads, deletion, and cross-user privacy.

## Project Structure

```text
fastapi-vault-api/

├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entrypoint & OpenAPI metadata
│   ├── config.py               # Environment/application settings
│   ├── database.py             # SQLAlchemy engine, Base & DB session
│   ├── deps.py                 # Shared dependencies / get_current_user
│   │
│   ├── auth/                   # Authentication & OAuth2 logic
│   │   ├── __init__.py
│   │   ├── authentication.py   # Login and JWT token generation
│   │   └── oauth2.py           # OAuth2 scheme, JWT validation & current user
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py             # User model
│   │   └── user_file.py        # UserFile model
│   │
│   ├── schemas/                # Pydantic v2 validation schemas
│   │   ├── __init__.py
│   │   ├── auth.py              # Token / authentication schemas
│   │   ├── user.py              # User request/response schemas
│   │   └── file.py              # File request/response schemas
│   │
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py              # User registration
│   │   ├── users.py             # User profile endpoints
│   │   └── files.py             # File upload/access management
│   │
│   └── utils/                  # Reusable security/file utilities
│       ├── __init__.py
│       ├── security.py          # Password hashing & verification
│       └── file_helpers.py      # File storage/helper functions
│
├── uploads/                    # Local file storage (gitignored)
├── tests/                      # Pytest test suite
├── .env.example                # Example environment configuration
├── requirements.txt             # Python dependencies
└── README.md                   # Project documentation
```

## Authentication Architecture

Authentication is separated into dedicated modules to keep responsibilities clear.

### `app/auth/authentication.py`

Responsible for the **login process**.

```text
Client
   │
   │ username + password
   ▼
/auth/login
   │
   ▼
authentication.py
   │
   ├── Find user
   ├── Verify password
   ├── Check account status
   │
   ▼
oauth2.py
   │
   ▼
Create JWT
   │
   ▼
Access token returned
```

### `app/auth/oauth2.py`

Responsible for the OAuth2/JWT functionality:

* Defines the OAuth2 bearer token scheme.
* Creates JWT access tokens.
* Decodes and validates JWTs.
* Extracts the user ID from the JWT `sub` claim.
* Loads the authenticated user from the database.
* Rejects invalid, expired, or inactive-user tokens.

### `app/utils/security.py`

Responsible only for password security:

* `hash_password()` — hashes plaintext passwords using bcrypt.
* `verify_password()` — verifies a supplied password against the stored hash.

JWT functionality is kept separate from password hashing.

### `app/deps.py`

Provides shared dependencies to the rest of the application.

`get_current_user` is imported from `app.auth.oauth2` and re-exported through `deps.py`, allowing protected routers to use:

```python
from app.deps import get_current_user
```

without needing to know the internal location of the authentication implementation.

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/<your-username>/fastapi-vault-api.git

cd fastapi-vault-api

python -m venv .venv

source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Generate a strong `SECRET_KEY`:

```bash
openssl rand -hex 32
```

Paste the generated value into `.env`:

```env
SECRET_KEY=your-generated-secret-key
```

The default `DATABASE_URL` uses SQLite and requires no additional database server.

A PostgreSQL connection can be configured by changing `DATABASE_URL` in `.env`.

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Tables are created automatically when the application starts.

The API is available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

### 5. Run the tests

```bash
pytest -v
```

Tests use an isolated in-memory SQLite database and temporary upload directory, so they do not modify the real database or `uploads/` directory.

## API Reference

### Authentication

| Method | Endpoint         | Auth | Description                                         |
| ------ | ---------------- | ---- | --------------------------------------------------- |
| POST   | `/auth/register` | No   | Create a new user account.                          |
| POST   | `/auth/login`    | No   | Exchange OAuth2 credentials for a JWT access token. |

### Users

| Method | Endpoint    | Auth | Description                                   |
| ------ | ----------- | ---- | --------------------------------------------- |
| GET    | `/users/me` | Yes  | Get the current authenticated user's profile. |

### Files

| Method | Endpoint                    | Auth | Description                          |
| ------ | --------------------------- | ---- | ------------------------------------ |
| POST   | `/files/upload`             | Yes  | Upload an image or PDF.              |
| GET    | `/files/`                   | Yes  | List the authenticated user's files. |
| GET    | `/files/{file_id}/download` | Yes  | Download one of the user's files.    |
| DELETE | `/files/{file_id}`          | Yes  | Delete one of the user's files.      |

### File listing query parameters

`GET /files/` supports:

```text
limit
offset
content_type
filename_contains
```

Example:

```text
GET /files/?limit=10&offset=0
```

or:

```text
GET /files/?content_type=application/pdf
```

## Example: Register, Login and Upload

### Register

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","username":"alice","password":"supersecret1"}'
```

### Login

The login endpoint uses the OAuth2 password form.

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=alice&password=supersecret1"
```

Response:

```json
{
  "access_token": "your-jwt-token",
  "token_type": "bearer"
}
```

### Authorize

Use the returned token as a Bearer token:

```text
Authorization: Bearer <ACCESS_TOKEN>
```

In Swagger UI, click **Authorize** and enter your credentials/token.

### Upload a file

```bash
curl -X POST http://127.0.0.1:8000/files/upload \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "upload=@report.pdf;type=application/pdf"
```

### List files

```bash
curl "http://127.0.0.1:8000/files/?limit=10&offset=0" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Download a file

```bash
curl -OJ "http://127.0.0.1:8000/files/<FILE_ID>/download" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Delete a file

```bash
curl -X DELETE \
  "http://127.0.0.1:8000/files/<FILE_ID>" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Security Notes

* Passwords are hashed with `bcrypt` through `passlib`; plaintext passwords are never stored.
* JWTs are signed using `HS256` and the application's `SECRET_KEY`.
* JWT expiration is controlled through `ACCESS_TOKEN_EXPIRE_MINUTES`.
* JWT authentication is implemented through FastAPI's OAuth2 password bearer flow.
* File access is authorization-checked using the authenticated user's `owner_id`.
* Users cannot access another user's files.
* Requests for another user's file return `404` rather than `403` to avoid revealing whether the file exists.
* Uploaded filenames are never trusted as physical storage names.
* Files are stored using UUID-generated names to prevent filename collisions and path guessing.
* Only configured content types are accepted by default:

  * `image/jpeg`
  * `image/png`
  * `image/gif`
  * `application/pdf`
* Upload size limits are enforced while the file is being streamed.
* Secrets such as `SECRET_KEY` are loaded from environment configuration and should never be committed to Git.

## Git Workflow

Per project guidelines, do not commit directly to `main`.

Use feature branches for each development phase.

Example:

```text
feat/db-setup
feat/jwt-auth
feat/file-handling
feat/file-access-docs-tests
```

### Suggested commit sequence

#### 1. Database setup

```text
feat(db): add database configuration and user/file models
```

Includes:

* Project scaffold
* `.env.example`
* SQLAlchemy configuration
* `User` model
* `UserFile` model
* Database session dependency

#### 2. JWT authentication

```text
feat(auth): implement modular JWT authentication
```

Includes:

* Password hashing
* User registration
* Login
* OAuth2 bearer authentication
* JWT creation
* JWT validation
* `get_current_user`
* `auth/authentication.py`
* `auth/oauth2.py`

#### 3. File handling

```text
feat(files): implement secure file handling
```

Includes:

* File uploads
* UUID-based storage
* File listing
* Pagination
* Filtering
* File size validation

#### 4. File access, documentation and tests

```text
feat(files): add secure file access and comprehensive tests
```

Includes:

* File downloads
* File deletion
* Cross-user privacy checks
* OpenAPI descriptions
* Test suite
* Documentation

## Development Principles

VaultAPI follows several principles designed to make the application easier to maintain and extend:

### Separation of concerns

Each package has a specific responsibility:

```text
auth/       → authentication and JWT
routers/    → HTTP endpoints
schemas/    → request/response validation
models/     → database representation
utils/      → reusable utilities
deps.py     → shared FastAPI dependencies
database.py → database configuration
config.py   → application configuration
```

### Dependency injection

Database sessions and authentication dependencies are provided through FastAPI's dependency injection system.

For example:

```python
db: Session = Depends(get_db)
```

and:

```python
current_user: User = Depends(get_current_user)
```

### User isolation

Every protected file operation identifies the authenticated user before accessing the file.

Conceptually:

```text
JWT
 ↓
User ID
 ↓
Current User
 ↓
UserFile.owner_id
 ↓
Authorized file operation
```

This ensures that authentication alone is not enough to access another user's resources.

## License

Provided for educational/internship evaluation purposes.
