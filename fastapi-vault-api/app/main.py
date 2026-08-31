"""
VaultAPI entrypoint.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth import authentication
from app.config import settings
from app.database import Base, engine
from app.routers import auth, files, users


tags_metadata = [
    {
        "name": "Authentication",
        "description": (
            "Register new accounts and authenticate users "
            "using JWT access tokens."
        ),
    },
    {
        "name": "Users",
        "description": "Authenticated user profile operations.",
    },
    {
        "name": "Files",
        "description": (
            "Upload, list, download, and delete personal files. "
            "All routes are scoped to the authenticated user."
        ),
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Create upload directory.
    os.makedirs(
        settings.UPLOAD_DIR,
        exist_ok=True,
    )

    # Create database tables.
    Base.metadata.create_all(
        bind=engine
    )

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "VaultAPI is a secure, multi-user REST API for uploading, "
        "listing, downloading, and managing personal media and document files. "
        "Every file operation is authenticated using JWT bearer tokens "
        "and scoped to the requesting user."
    ),
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)


# Authentication routes
app.include_router(auth.router)
app.include_router(authentication.router)

# User routes
app.include_router(users.router)

# File routes
app.include_router(files.router)


@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
)
def health_check() -> dict:

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }