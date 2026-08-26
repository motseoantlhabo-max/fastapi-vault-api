"""Tests for registration, login, and the protected /users/me route."""


def test_register_new_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "bob@example.com", "username": "bob", "password": "hunter2ok"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "bob@example.com"
    assert body["username"] == "bob"
    assert "hashed_password" not in body
    assert "password" not in body


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "username": "dup1", "password": "hunter2ok"}
    client.post("/auth/register", json=payload)

    payload["username"] = "dup2"
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_login_success_returns_jwt(client):
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "username": "carol", "password": "hunter2ok"},
    )
    response = client.post(
        "/auth/login", data={"username": "carol", "password": "hunter2ok"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_wrong_password_rejected(client):
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "username": "dave", "password": "hunter2ok"},
    )
    response = client.post(
        "/auth/login", data={"username": "dave", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
