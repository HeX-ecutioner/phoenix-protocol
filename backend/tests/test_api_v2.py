"""Comprehensive test suite for the authoritative /api/... REST contract."""

import csv
import io
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Generator
import pytest
from flask.testing import FlaskClient

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"

from app.api import create_app
from app.database.connection import get_connection
from app.database.repositories import DeviceRepository, ScanRepository
from app.database.schema import init_db
from app.models.device import Device
from app.models.scan import Scan


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Provide a Flask test client configured with an isolated temporary SQLite database."""
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app = create_app(db_path=temp_db_path, test_config={"TESTING": True})
    with app.test_client() as c:
        yield c

    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


# ============================================================================
# 1. /api/device-types
# ============================================================================


def test_get_device_types(client: FlaskClient):
    """GET /api/device-types returns supported device profiles in standard envelope."""
    res = client.get("/api/device-types")
    assert res.status_code == 200
    body = res.get_json()

    assert body["error"] is None
    assert body["request_id"].startswith("req-")
    data = body["data"]
    assert "device_types" in data

    types = data["device_types"]
    assert len(types) >= 1
    cisco = next((t for t in types if t["id"] == "cisco_ios"), None)
    assert cisco is not None
    assert cisco["name"] == "Cisco IOS"
    assert cisco["vendor"] == "Cisco"
    assert cisco["supported"] is True
    assert "parser_version" in cisco

    # Verify no fabricated profiles are advertised as supported
    assert not any(t["id"] in ("palo_alto", "fortinet", "juniper") for t in types)


# ============================================================================
# 2. /api/scans (POST)
# ============================================================================


def test_post_api_scans_single_file_compliant(client: FlaskClient):
    """POST /api/scans with compliant configuration yields 201 and 100% compliance."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    res = client.post(
        "/api/scans",
        data={
            "device_type": "cisco_ios",
            "files": (io.BytesIO(content), "core_rtr.cfg"),
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    body = res.get_json()
    assert body["error"] is None
    assert body["request_id"].startswith("req-")

    data = body["data"]
    assert data["scan_id"].startswith("scan_")
    assert data["id"] == data["scan_id"]
    assert data["status"] == "completed"
    assert data["compliance_score"] == 100.0

    # Summary checks: both standard and frontend compatibility keys
    summary = data["summary"]
    assert summary["total_rules"] == 10
    assert summary["passed_rules"] == 10
    assert summary["failed_rules"] == 0
    assert summary["pass_count"] == 10
    assert summary["fail_count"] == 0
    assert summary["warning_count"] == 0
    assert summary["device_count"] == 1
    assert summary["compliance_percentage"] == 100.0
    assert summary["high_severity_failures"] == 0

    # Device checks
    assert len(data["devices"]) == 1
    dev = data["devices"][0]
    assert dev["name"] == "CORE-RTR-01"
    assert dev["display_name"] == "CORE-RTR-01"
    assert dev["source_filename"] == "core_rtr.cfg"
    assert dev["parse_status"] == "success"
    assert dev["compliance_score"] == 100.0
    assert len(dev["results"]) == 10

    # Rule result check for frontend
    r0 = dev["results"][0]
    assert "rule_id" in r0
    assert "title" in r0
    assert "status" in r0
    assert "severity" in r0
    assert "remediation" in r0
    assert "evidence" in r0


def test_post_api_scans_single_file_failing(client: FlaskClient):
    """POST /api/scans with failing configuration yields 201, 0% compliance, high severity failures."""
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "rb") as f:
        content = f.read()

    res = client.post(
        "/api/scans",
        data={
            "device_type": "cisco_ios",
            "files": (io.BytesIO(content), "failing_rtr.cfg"),
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["compliance_score"] == 0.0
    assert data["summary"]["failed_rules"] == 10
    assert data["summary"]["fail_count"] == 10
    assert data["summary"]["high_severity_failures"] > 0


def test_post_api_scans_multiple_files(client: FlaskClient):
    """POST /api/scans supports multi-device file uploads."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f1:
        c1 = f1.read()
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "rb") as f2:
        c2 = f2.read()

    res = client.post(
        "/api/scans",
        data={
            "device_type": "cisco_ios",
            "files": [
                (io.BytesIO(c1), "compliant.cfg"),
                (io.BytesIO(c2), "failing.cfg"),
            ],
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    data = res.get_json()["data"]
    assert len(data["devices"]) == 2
    assert data["summary"]["device_count"] == 2
    assert data["summary"]["total_rules"] == 20
    assert data["summary"]["pass_count"] == 10
    assert data["summary"]["fail_count"] == 10
    assert data["compliance_score"] == 50.0


def test_post_api_scans_device_type_alias_normalization(client: FlaskClient):
    """POST /api/scans normalizes 'cisco-like-router' and 'cisco' aliases to cisco_ios."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    res = client.post(
        "/api/scans",
        data={
            "device_type": "cisco-like-router",
            "files": (io.BytesIO(content), "alias_rtr.cfg"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 201
    assert res.get_json()["data"]["device_type"] == "cisco_ios"


def test_post_api_scans_unsupported_device_type(client: FlaskClient):
    """POST /api/scans rejects unsupported device type with 400 and structured error envelope."""
    res = client.post(
        "/api/scans",
        data={
            "device_type": "juniper_junos",
            "files": (io.BytesIO(b"hostname j1\n"), "junos.cfg"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "UNSUPPORTED_DEVICE_TYPE"
    assert "not supported" in body["error"]["message"]


def test_post_api_scans_missing_files(client: FlaskClient):
    """POST /api/scans rejects request with no files provided."""
    res = client.post(
        "/api/scans",
        data={"device_type": "cisco_ios"},
        content_type="multipart/form-data",
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "MISSING_FILES"


def test_post_api_scans_empty_file_rejected(client: FlaskClient):
    """POST /api/scans rejects empty file with 400 and error envelope."""
    res = client.post(
        "/api/scans",
        data={
            "device_type": "cisco_ios",
            "files": (io.BytesIO(b"   \n  "), "empty.cfg"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "EMPTY_FILE"


# ============================================================================
# 3. /api/scans/{scan_id} (GET)
# ============================================================================


def test_get_api_scan_by_id_success_and_not_found(client: FlaskClient):
    """GET /api/scans/{scan_id} retrieves persisted scan identically to POST result."""
    # 1. 404 for unknown scan
    res_404 = client.get("/api/scans/non-existent-scan-id")
    assert res_404.status_code == 404
    body_404 = res_404.get_json()
    assert body_404["data"] is None
    assert body_404["error"]["code"] == "SCAN_NOT_FOUND"

    # 2. Create scan
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    post_res = client.post(
        "/api/scans",
        data={
            "device_type": "cisco_ios",
            "files": (io.BytesIO(content), "core.cfg"),
        },
        content_type="multipart/form-data",
    )
    scan_id = post_res.get_json()["data"]["scan_id"]

    # 3. Retrieve scan
    get_res = client.get(f"/api/scans/{scan_id}")
    assert get_res.status_code == 200
    body_get = get_res.get_json()
    assert body_get["error"] is None
    data = body_get["data"]
    assert data["scan_id"] == scan_id
    assert data["id"] == scan_id
    assert data["status"] == "completed"
    assert data["compliance_score"] == 100.0
    assert data["summary"]["pass_count"] == 10
    assert len(data["devices"]) == 1


# ============================================================================
# 4. /api/scans/{scan_id}/devices (GET)
# ============================================================================


def test_get_api_scan_devices(client: FlaskClient):
    """GET /api/scans/{scan_id}/devices lists all devices in the scan."""
    # 404 on non-existent scan
    res_404 = client.get("/api/scans/unknown-scan-id/devices")
    assert res_404.status_code == 404
    assert res_404.get_json()["error"]["code"] == "SCAN_NOT_FOUND"

    # Create multi-device scan
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f1:
        c1 = f1.read()
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "rb") as f2:
        c2 = f2.read()

    post_res = client.post(
        "/api/scans",
        data={
            "device_type": "cisco_ios",
            "files": [
                (io.BytesIO(c1), "dev1.cfg"),
                (io.BytesIO(c2), "dev2.cfg"),
            ],
        },
        content_type="multipart/form-data",
    )
    scan_id = post_res.get_json()["data"]["scan_id"]

    # Fetch device list
    devs_res = client.get(f"/api/scans/{scan_id}/devices")
    assert devs_res.status_code == 200
    body = devs_res.get_json()
    assert body["error"] is None
    devs_data = body["data"]
    assert devs_data["scan_id"] == scan_id
    assert len(devs_data["devices"]) == 2

    d1 = devs_data["devices"][0]
    assert "id" in d1
    assert "device_id" in d1
    assert "display_name" in d1
    assert "vendor" in d1
    assert "device_type" in d1
    assert "parse_status" in d1
    assert "compliance_score" in d1
    assert "summary" in d1
    assert "pass_count" in d1["summary"]


# ============================================================================
# 5. /api/scans/{scan_id}/devices/{device_id} (GET)
# ============================================================================


def test_get_api_scan_device_detail(client: FlaskClient):
    """GET /api/scans/{scan_id}/devices/{device_id} returns device audit details."""
    # Upload scan
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    post_res = client.post(
        "/api/scans",
        data={
            "device_type": "cisco_ios",
            "files": (io.BytesIO(content), "core.cfg"),
        },
        content_type="multipart/form-data",
    )
    scan_id = post_res.get_json()["data"]["scan_id"]
    device_id = post_res.get_json()["data"]["devices"][0]["device_id"]

    # 1. Fetch valid device
    res = client.get(f"/api/scans/{scan_id}/devices/{device_id}")
    assert res.status_code == 200
    body = res.get_json()
    assert body["error"] is None
    data = body["data"]
    assert data["device"]["id"] == device_id
    assert data["display_name"] == "CORE-RTR-01"
    assert data["source_filename"] == "core.cfg"
    assert len(data["results"]) == 10
    assert data["results"][0]["rule_id"].startswith("NET-")
    assert "title" in data["results"][0]
    assert "evidence" in data["results"][0]

    # 2. Fetch unknown device under valid scan -> 404
    res_dev_404 = client.get(f"/api/scans/{scan_id}/devices/non-existent-device-id")
    assert res_dev_404.status_code == 404
    assert res_dev_404.get_json()["error"]["code"] == "DEVICE_NOT_FOUND"

    # 3. Fetch device under non-existent scan -> 404
    res_scan_404 = client.get(f"/api/scans/non-existent-scan/devices/{device_id}")
    assert res_scan_404.status_code == 404
    assert res_scan_404.get_json()["error"]["code"] == "SCAN_NOT_FOUND"


def test_get_api_scan_device_detail_cross_scan_mismatch_404(client: FlaskClient):
    """GET /api/scans/{scan_id}/devices/{device_id} returns 404 if device belongs to another scan."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    # Create scan 1
    res1 = client.post(
        "/api/scans",
        data={"device_type": "cisco_ios", "files": (io.BytesIO(content), "s1.cfg")},
        content_type="multipart/form-data",
    )
    scan1_id = res1.get_json()["data"]["scan_id"]
    dev1_id = res1.get_json()["data"]["devices"][0]["device_id"]

    # Create scan 2
    res2 = client.post(
        "/api/scans",
        data={"device_type": "cisco_ios", "files": (io.BytesIO(content), "s2.cfg")},
        content_type="multipart/form-data",
    )
    scan2_id = res2.get_json()["data"]["scan_id"]

    # Request dev1 under scan2
    cross_res = client.get(f"/api/scans/{scan2_id}/devices/{dev1_id}")
    assert cross_res.status_code == 404
    assert cross_res.get_json()["error"]["code"] == "DEVICE_SCAN_MISMATCH"


# ============================================================================
# 6. /api/rules & 7. /api/rules/{rule_id}
# ============================================================================


def test_get_api_rules_catalog(client: FlaskClient):
    """GET /api/rules returns authoritative catalog of NET-001 through NET-010."""
    res = client.get("/api/rules")
    assert res.status_code == 200
    body = res.get_json()
    assert body["error"] is None

    rules = body["data"]["rules"]
    assert len(rules) == 10
    rule_ids = [r["id"] for r in rules]
    expected_ids = [f"NET-{i:03d}" for i in range(1, 11)]
    assert rule_ids == expected_ids

    r1 = next(r for r in rules if r["id"] == "NET-001")
    assert r1["title"] == "Telnet Service Disabled"
    assert r1["severity"] == "high"
    assert r1["device_type"] == "cisco_ios"
    assert r1["is_active"] is True
    assert "remediation" in r1


def test_get_api_rule_by_id_success_and_not_found(client: FlaskClient):
    """GET /api/rules/{rule_id} returns rule metadata or 404."""
    # 1. Valid rule
    res = client.get("/api/rules/NET-001")
    assert res.status_code == 200
    body = res.get_json()
    assert body["error"] is None
    assert body["data"]["id"] == "NET-001"
    assert body["data"]["title"] == "Telnet Service Disabled"

    # 2. Unknown rule -> 404
    res_404 = client.get("/api/rules/NET-999")
    assert res_404.status_code == 404
    assert res_404.get_json()["error"]["code"] == "RULE_NOT_FOUND"


# ============================================================================
# 8. /api/scans/{scan_id}/report.csv
# ============================================================================


def test_get_api_report_csv_success(client: FlaskClient):
    """GET /api/scans/{scan_id}/report.csv returns valid downloadable CSV report."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    post_res = client.post(
        "/api/scans",
        data={"device_type": "cisco_ios", "files": (io.BytesIO(content), "core.cfg")},
        content_type="multipart/form-data",
    )
    scan_id = post_res.get_json()["data"]["scan_id"]

    res = client.get(f"/api/scans/{scan_id}/report.csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("Content-Type", "")
    assert f'filename="scan_{scan_id}_report.csv"' in res.headers.get("Content-Disposition", "")

    csv_text = res.get_data(as_text=True)
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    # Check header
    header = rows[0]
    expected_header = [
        "scan_id",
        "device_id",
        "device_name",
        "vendor",
        "device_type",
        "rule_id",
        "status",
        "severity",
        "evidence",
        "evidence_line_range",
        "message",
        "remediation",
    ]
    assert header == expected_header

    # Check 10 evaluated rule rows
    data_rows = rows[1:]
    assert len(data_rows) == 10
    for row in data_rows:
        assert row[0] == scan_id
        assert row[4] == "cisco_ios"
        assert row[5].startswith("NET-")
        assert row[6] == "pass"


def test_get_api_report_csv_not_found(client: FlaskClient):
    """GET /api/scans/{scan_id}/report.csv returns 404 for unknown scan."""
    res = client.get("/api/scans/non-existent-scan/report.csv")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "SCAN_NOT_FOUND"


def test_get_api_report_csv_secret_sanitization(client: FlaskClient):
    """Verify secrets are sanitized in the exported CSV report."""
    with open(SAMPLE_DATA_DIR / "security/mixed_secrets.txt", "rb") as f:
        content = f.read()

    post_res = client.post(
        "/api/scans",
        data={"device_type": "cisco_ios", "files": (io.BytesIO(content), "secrets.cfg")},
        content_type="multipart/form-data",
    )
    scan_id = post_res.get_json()["data"]["scan_id"]

    res = client.get(f"/api/scans/{scan_id}/report.csv")
    assert res.status_code == 200
    csv_text = res.get_data(as_text=True)

    # Ensure known raw secrets from mixed_secrets.txt never appear
    forbidden_secrets = [
        "Cisco1234!",
        "SuperSecretKey99",
        "RadiusSecret2026",
        "SecretTacacsKey",
        "readcommunity99",
    ]
    for secret in forbidden_secrets:
        assert secret not in csv_text, f"Raw secret '{secret}' leaked into CSV report!"


# ============================================================================
# 9. CORS & Preflight Support
# ============================================================================


def test_cors_preflight_and_headers(client: FlaskClient):
    """Verify CORS preflight OPTIONS and response headers for development origin."""
    origin = "http://localhost:5173"

    # 1. Preflight OPTIONS
    opt_res = client.open(
        "/api/device-types",
        method="OPTIONS",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    assert opt_res.status_code == 204
    assert opt_res.headers.get("Access-Control-Allow-Origin") == origin
    assert "GET" in opt_res.headers.get("Access-Control-Allow-Methods", "")

    # 2. Actual GET with Origin
    get_res = client.get("/api/device-types", headers={"Origin": origin})
    assert get_res.status_code == 200
    assert get_res.headers.get("Access-Control-Allow-Origin") == origin

    # 3. Disallowed origin does not get CORS headers
    disallowed_res = client.get(
        "/api/device-types", headers={"Origin": "http://malicious-site.com"}
    )
    assert disallowed_res.status_code == 200
    assert disallowed_res.headers.get("Access-Control-Allow-Origin") is None
