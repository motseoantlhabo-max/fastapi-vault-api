"""
Shared pytest fixtures.

Each test gets a fresh in-memory SQLite database (via StaticPool so the
single in-memory connection is shared across the app's dependency-injected
sessions) and a TestClient with `get_db` overridden to use it.
"""

import shutil

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def test_db_session(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Redirect uploaded files to a temp dir so tests don't touch the real uploads/ folder.
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    from app.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))

    yield TestingSessionLocal

    Base.metadata.drop_all(bind=engine)
    shutil.rmtree(upload_dir, ignore_errors=True)


@pytest.fixture()
def client(test_db_session):
    def override_get_db():
        db = test_db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Register + log in a user, returning Authorization headers for it."""
    client.post(
        "/auth/register",
        json={"email": "alice@example.com", "username": "alice", "password": "supersecret1"},
    )
    login_resp = client.post(
        "/auth/login",
        data={"username": "alice", "password": "supersecret1"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
