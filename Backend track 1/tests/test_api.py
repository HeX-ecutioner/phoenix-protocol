import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_upload_compliant():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "fixtures", "compliant.txt")

    with open(path, "rb") as f:
        response = client.post(
            "/scan", files={"file": ("compliant.txt", f, "text/plain")}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["summary"]["compliant"] == 8


def test_api_upload_empty():
    response = client.post("/scan", files={"file": ("empty.txt", b"", "text/plain")})
    assert response.status_code == 400


def test_api_unsupported_format():
    response = client.post(
        "/scan",
        files={"file": ("bad.bin", b"\xff\xfe\x00", "application/octet-stream")},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "failed"
    assert any(e["severity"] == "error" for e in data["errors"])


def test_api_upload_too_large():
    large_content = b"0" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/scan", files={"file": ("large.txt", large_content, "text/plain")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large"


def test_api_upload_failing():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "fixtures", "failing.txt")

    with open(path, "rb") as f:
        response = client.post(
            "/scan", files={"file": ("failing.txt", f, "text/plain")}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["summary"]["failing"] == 8


def test_api_upload_ambiguous():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "fixtures", "ambiguous.txt")

    with open(path, "rb") as f:
        response = client.post(
            "/scan", files={"file": ("ambiguous.txt", f, "text/plain")}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["summary"]["ambiguous"] > 0


def test_api_repeated_scans_unique_ids():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "fixtures", "compliant.txt")

    with open(path, "rb") as f:
        content = f.read()

    res1 = client.post(
        "/scan", files={"file": ("compliant.txt", content, "text/plain")}
    )
    res2 = client.post(
        "/scan", files={"file": ("compliant.txt", content, "text/plain")}
    )

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["scan_id"] != res2.json()["scan_id"]


def test_api_persistence_round_trip():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "fixtures", "compliant.txt")

    with open(path, "rb") as f:
        post_response = client.post(
            "/scan", files={"file": ("compliant.txt", f, "text/plain")}
        )

    assert post_response.status_code == 201
    original_data = post_response.json()
    scan_id = original_data["scan_id"]

    get_response = client.get(f"/scans/{scan_id}")
    assert get_response.status_code == 200
    retrieved_data = get_response.json()

    assert original_data["scan_id"] == retrieved_data["scan_id"]
    assert original_data["status"] == retrieved_data["status"]
    assert original_data["summary"] == retrieved_data["summary"]
