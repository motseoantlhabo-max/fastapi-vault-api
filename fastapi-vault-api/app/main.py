"""
VaultAPI entrypoint.

Wires together routers, creates database tables on startup (for local/dev
use — production deployments should use a real migration tool such as
Alembic instead of create_all), and configures OpenAPI/Swagger metadata.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers import auth, files, users

tags_metadata = [
    {"name": "Authentication", "description": "Register new accounts and exchange credentials for JWT access tokens."},
    {"name": "Users", "description": "Authenticated user profile operations."},
    {"name": "Files", "description": "Upload, list, download, and delete personal files. All routes are scoped to the authenticated user."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the upload directory and DB tables exist before serving requests.
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "VaultAPI is a secure, multi-user REST API for uploading, listing, "
        "downloading, and managing personal media and document files. "
        "Every file operation is authenticated via JWT bearer tokens and "
        "strictly scoped to the requesting user."
    ),
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)


@app.get("/", tags=["Health"], summary="Health check")
def health_check() -> dict:
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}
