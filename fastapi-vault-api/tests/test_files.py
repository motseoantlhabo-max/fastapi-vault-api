"""Tests for upload, pagination/filtering, download, delete, and cross-user privacy."""

import io


def _register_and_login(client, username: str):
    email = f"{username}@example.com"
    client.post("/auth/register", json={"email": email, "username": username, "password": "hunter2ok"})
    resp = client.post("/auth/login", data={"username": username, "password": "hunter2ok"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload_pdf(client, headers, filename="doc.pdf"):
    file_bytes = io.BytesIO(b"%PDF-1.4 fake pdf content")
    return client.post(
        "/files/upload",
        headers=headers,
        files={"upload": (filename, file_bytes, "application/pdf")},
    )


def test_upload_requires_auth(client):
    file_bytes = io.BytesIO(b"data")
    response = client.post("/files/upload", files={"upload": ("a.pdf", file_bytes, "application/pdf")})
    assert response.status_code == 401


def test_upload_rejects_disallowed_content_type(client, auth_headers):
    file_bytes = io.BytesIO(b"executable-ish content")
    response = client.post(
        "/files/upload",
        headers=auth_headers,
        files={"upload": ("script.exe", file_bytes, "application/x-msdownload")},
    )
    assert response.status_code == 415


def test_upload_and_list_own_files(client, auth_headers):
    resp = _upload_pdf(client, auth_headers, "report.pdf")
    assert resp.status_code == 201
    body = resp.json()
    assert body["original_filename"] == "report.pdf"
    assert body["content_type"] == "application/pdf"

    list_resp = client.get("/files/", headers=auth_headers)
    assert list_resp.status_code == 200
    listing = list_resp.json()
    assert listing["total"] == 1
    assert listing["items"][0]["original_filename"] == "report.pdf"


def test_pagination_limit_offset(client, auth_headers):
    for i in range(5):
        _upload_pdf(client, auth_headers, f"file{i}.pdf")

    page1 = client.get("/files/?limit=2&offset=0", headers=auth_headers).json()
    page2 = client.get("/files/?limit=2&offset=2", headers=auth_headers).json()

    assert page1["total"] == 5
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    assert {i["id"] for i in page1["items"]}.isdisjoint({i["id"] for i in page2["items"]})


def test_download_own_file(client, auth_headers):
    upload_resp = _upload_pdf(client, auth_headers)
    file_id = upload_resp.json()["id"]

    download_resp = client.get(f"/files/{file_id}/download", headers=auth_headers)
    assert download_resp.status_code == 200
    assert download_resp.content.startswith(b"%PDF")


def test_cross_user_access_returns_404(client):
    alice_headers = _register_and_login(client, "alice2")
    bob_headers = _register_and_login(client, "bob2")

    upload_resp = _upload_pdf(client, alice_headers, "alice-secret.pdf")
    file_id = upload_resp.json()["id"]

    # Bob must not be able to download Alice's file.
    download_resp = client.get(f"/files/{file_id}/download", headers=bob_headers)
    assert download_resp.status_code == 404

    # Bob's own file listing must not include Alice's file.
    listing = client.get("/files/", headers=bob_headers).json()
    assert listing["total"] == 0

    # Bob must not be able to delete Alice's file.
    delete_resp = client.delete(f"/files/{file_id}", headers=bob_headers)
    assert delete_resp.status_code == 404


def test_delete_own_file(client, auth_headers):
    upload_resp = _upload_pdf(client, auth_headers)
    file_id = upload_resp.json()["id"]

    delete_resp = client.delete(f"/files/{file_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    download_resp = client.get(f"/files/{file_id}/download", headers=auth_headers)
    assert download_resp.status_code == 404
