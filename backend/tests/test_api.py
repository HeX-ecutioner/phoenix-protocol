"""Tests for the Phoenix Protocol Flask API layer."""

import io
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Generator
import pytest
from flask.testing import FlaskClient

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"

from app.api import create_app
from app.database.connection import get_connection
from app.database.repositories import (
    DeviceRepository,
    RuleResultRepository,
    ScanRepository,
)
from app.database.schema import init_db


@pytest.fixture
def app_and_db() -> Generator[FlaskClient, None, None]:
    """Provide a Flask test client configured with an isolated temporary SQLite database."""
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app = create_app(db_path=temp_db_path, test_config={"TESTING": True})
    with app.test_client() as client:
        yield client

    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


@pytest.fixture
def db_path() -> Generator[str, None, None]:
    """Provide a temporary database path for direct repository assertions."""
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield temp_db_path
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


# 1. Health check
def test_get_health(app_and_db):
    """Verify GET /health returns 200 with service metadata."""
    res = app_and_db.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "phoenix-protocol"
    assert "version" in data


# 2. Compliant config upload
def test_post_scan_compliant_config(app_and_db):
    """Verify POST /scan with compliant router yields 201 and 100% compliance."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    res = app_and_db.post(
        "/scan",
        data={
            "device_type": "cisco_ios",
            "file": (io.BytesIO(content), "core_rtr.cfg"),
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "completed"
    assert data["device_type"] == "cisco_ios"
    assert data["summary"]["total_rules"] == 10
    assert data["summary"]["passed_rules"] == 10
    assert data["summary"]["failed_rules"] == 0
    assert data["summary"]["tested_rule_compliance"] == 100.0
    assert data["compliance_score"] == 100.0

    # Device verification
    assert len(data["devices"]) == 1
    dev = data["devices"][0]
    assert dev["name"] == "CORE-RTR-01"
    assert dev["parse_status"] == "success"
    assert len(dev["results"]) == 10


# 3. Failing config upload
def test_post_scan_failing_config(app_and_db):
    """Verify POST /scan with failing router yields 201 and 0% compliance."""
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "rb") as f:
        content = f.read()

    res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(content), "edge_rtr.cfg")},
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "completed"
    assert data["summary"]["total_rules"] == 10
    assert data["summary"]["passed_rules"] == 0
    assert data["summary"]["failed_rules"] == 10
    assert data["summary"]["tested_rule_compliance"] == 0.0


# 4. Ambiguous config upload
def test_post_scan_ambiguous_config(app_and_db):
    """Verify POST /scan with ambiguous router preserves warnings and excludes from denominator."""
    with open(SAMPLE_DATA_DIR / "ambiguous_router.txt", "rb") as f:
        content = f.read()

    res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(content), "ambiguous_rtr.cfg")},
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "completed"
    summary = data["summary"]
    assert summary["warning_rules"] >= 4
    # Compliance formula: passed / (passed + failed) * 100
    expected_score = round(
        summary["passed_rules"] / (summary["passed_rules"] + summary["failed_rules"]) * 100.0,
        2,
    )
    assert summary["tested_rule_compliance"] == expected_score


# 5. Multiple config files upload
def test_post_scan_multiple_configs(app_and_db):
    """Verify POST /scan accepts multiple configuration files and aggregates results."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        comp_bytes = f.read()
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "rb") as f:
        fail_bytes = f.read()

    res = app_and_db.post(
        "/scan",
        data={
            "files": [
                (io.BytesIO(comp_bytes), "rtr1.cfg"),
                (io.BytesIO(fail_bytes), "rtr2.cfg"),
            ]
        },
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "completed"
    assert len(data["devices"]) == 2
    assert data["summary"]["total_rules"] == 20
    assert data["summary"]["passed_rules"] == 10
    assert data["summary"]["failed_rules"] == 10
    assert data["summary"]["tested_rule_compliance"] == 50.0


# 6. Empty file validation
def test_post_scan_empty_file_rejected(app_and_db):
    """Verify POST /scan rejects empty files with HTTP 400."""
    res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(b""), "empty.cfg")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 400
    data = res.get_json()
    assert "empty" in data["error"].lower()


# 7. Malformed non-text binary file validation
def test_post_scan_malformed_binary_rejected(app_and_db):
    """Verify POST /scan rejects non-UTF-8 binary files with HTTP 422."""
    res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(b"\xff\xfe\x00\x12\x34"), "binary.bin")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 422
    data = res.get_json()
    assert "Unsupported file format" in data["error"]


# 8. Unsupported device type validation
def test_post_scan_unsupported_device_type(app_and_db):
    """Verify POST /scan rejects unsupported device types with HTTP 400."""
    res = app_and_db.post(
        "/scan",
        data={
            "device_type": "juniper_junos",
            "file": (io.BytesIO(b"hostname j1\n"), "junos.cfg"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 400
    data = res.get_json()
    assert "Unsupported device type" in data["error"]


# 9. Missing file payload validation
def test_post_scan_missing_file_rejected(app_and_db):
    """Verify POST /scan rejects request with missing file payload."""
    res = app_and_db.post(
        "/scan",
        data={"device_type": "cisco_ios"},
        content_type="multipart/form-data",
    )
    assert res.status_code == 400
    data = res.get_json()
    assert "Missing configuration files" in data["error"]


# 10. File size limit enforcement
def test_post_scan_payload_size_limit(app_and_db):
    """Verify POST /scan rejects files exceeding 10 MB limit with HTTP 413."""
    large_payload = b"!" * (10 * 1024 * 1024 + 1024)
    res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(large_payload), "huge.cfg")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 413


# 11 & 12. GET /scans/<scan_id> retrieval and 404 behavior
def test_get_scan_by_id_and_not_found(app_and_db):
    """Verify GET /scans/<scan_id> retrieves persisted scan or returns 404 for unknown ID."""
    # 1. 404 for non-existent scan
    res_not_found = app_and_db.get("/scans/non-existent-uuid-999")
    assert res_not_found.status_code == 404
    assert "Scan not found" in res_not_found.get_json()["error"]

    # 2. Upload scan
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    create_res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(content), "core.cfg")},
        content_type="multipart/form-data",
    )
    assert create_res.status_code == 201
    scan_id = create_res.get_json()["scan_id"]

    # 3. Retrieve scan
    get_res = app_and_db.get(f"/scans/{scan_id}")
    assert get_res.status_code == 200
    retrieved = get_res.get_json()

    assert retrieved["scan_id"] == scan_id
    assert retrieved["status"] == "completed"
    assert retrieved["summary"]["tested_rule_compliance"] == 100.0
    assert len(retrieved["devices"]) == 1
    assert retrieved["devices"][0]["name"] == "CORE-RTR-01"


# 13 & 14. Response schema verification
def test_scan_response_schema_contract(app_and_db):
    """Verify response schema contains all required top-level and device-level contract keys."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(content), "cisco.cfg")},
        content_type="multipart/form-data",
    )
    data = res.get_json()

    # Top-level contract keys
    assert "scan_id" in data
    assert "status" in data
    assert "device_type" in data
    assert "parser_version" in data
    assert "rule_set_version" in data
    assert "summary" in data
    assert "compliance_score" in data
    assert "devices" in data

    # Summary keys
    sum_keys = {
        "total_rules",
        "passed_rules",
        "failed_rules",
        "warning_rules",
        "not_applicable_rules",
        "error_rules",
        "tested_rule_compliance",
    }
    assert sum_keys.issubset(data["summary"].keys())

    # Device keys
    dev = data["devices"][0]
    dev_keys = {
        "device_id",
        "name",
        "display_name",
        "vendor",
        "device_type",
        "source_filename",
        "parse_status",
        "line_count",
        "error_message",
        "summary",
        "compliance_score",
        "results",
    }
    assert dev_keys.issubset(dev.keys())

    # Result keys
    res_item = dev["results"][0]
    res_keys = {
        "rule_id",
        "status",
        "severity",
        "evidence",
        "evidence_line_range",
        "message",
        "remediation",
    }
    assert res_keys.issubset(res_item.keys())


# 15 & 16. Security: Secrets and raw configs never leak in API response
def test_secrets_and_raw_config_never_appear_in_response(app_and_db):
    """Verify raw secrets and raw config text are sanitized and not leaked in JSON response."""
    secret_pass = "SuperSecretPlainTextPassword123!"
    secret_hash = "$1$mERr$hx5rVt7rPNoS4wqbXKX7x0"
    canary = "UNIQUE_CANARY_NEVER_LEAK_998877"

    cfg_text = f"""
    hostname VAULT-RTR
    ! {canary}
    enable secret {secret_hash}
    username admin password 0 {secret_pass}
    line vty 0 4
     transport input ssh
    """

    res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(cfg_text.encode("utf-8")), "vault.cfg")},
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    resp_text = res.get_data(as_text=True)

    # Asserts: raw secrets, raw hashes, and canary comment never appear in JSON
    assert secret_pass not in resp_text
    assert secret_hash not in resp_text
    assert canary not in resp_text


# 17 & 18. Multi-file to multi-device correspondence
def test_one_file_one_device_mapping(app_and_db):
    """Verify 1 uploaded file creates exactly 1 device, 3 files create 3 devices."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        c1 = f.read()
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "rb") as f:
        c2 = f.read()
    with open(SAMPLE_DATA_DIR / "ambiguous_router.txt", "rb") as f:
        c3 = f.read()

    # 1 file -> 1 device
    r1 = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(c1), "dev1.cfg")},
        content_type="multipart/form-data",
    )
    assert len(r1.get_json()["devices"]) == 1

    # 3 files -> 3 devices
    r3 = app_and_db.post(
        "/scan",
        data={
            "files": [
                (io.BytesIO(c1), "dev1.cfg"),
                (io.BytesIO(c2), "dev2.cfg"),
                (io.BytesIO(c3), "dev3.cfg"),
            ]
        },
        content_type="multipart/form-data",
    )
    assert len(r3.get_json()["devices"]) == 3


# 19 & 20. Track 2 scanner invocation and summary alignment
def test_api_invokes_authoritative_track2_scanner(app_and_db):
    """Verify the API invokes the authoritative Track 2 engine with rules NET-001 through NET-010."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
        content = f.read()

    res = app_and_db.post(
        "/scan",
        data={"file": (io.BytesIO(content), "router.cfg")},
        content_type="multipart/form-data",
    )
    data = res.get_json()

    # Verify rule IDs are NET-001 through NET-010
    results = data["devices"][0]["results"]
    rule_ids = [r["rule_id"] for r in results]
    expected_ids = [f"NET-{i:03d}" for i in range(1, 11)]
    assert rule_ids == expected_ids


# 21. CRITICAL END-TO-END TEST
def test_critical_end_to_end_chain(db_path):
    """Critical End-to-End Test:

    POST /scan
        ↓
    Flask API
        ↓
    app.services.scanner.run_scan()
        ↓
    CiscoLikeParser
        ↓
    NormalizedConfig
        ↓
    NET-001..NET-010
        ↓
    SQLite
        ↓
    JSON response

    Proves the HTTP response and persisted SQLite records match 1:1.
    """
    app = create_app(db_path=db_path, test_config={"TESTING": True})
    with app.test_client() as client:
        with open(SAMPLE_DATA_DIR / "compliant_router.txt", "rb") as f:
            comp_content = f.read()
        with open(SAMPLE_DATA_DIR / "failing_router.txt", "rb") as f:
            fail_content = f.read()

        # 1. Execute HTTP upload
        response = client.post(
            "/scan",
            data={
                "device_type": "cisco_ios",
                "files": [
                    (io.BytesIO(comp_content), "core.cfg"),
                    (io.BytesIO(fail_content), "edge.cfg"),
                ],
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        json_data = response.get_json()
        scan_id = json_data["scan_id"]

        # 2. Query SQLite database directly
        conn = get_connection(db_path)
        scan_repo = ScanRepository(conn)
        dev_repo = DeviceRepository(conn)
        res_repo = RuleResultRepository(conn)

        # Assert Scan table matches JSON response
        db_scan = scan_repo.get_by_id(scan_id)
        assert db_scan is not None
        assert db_scan.status == json_data["status"] == "completed"
        assert db_scan.total_rules == json_data["summary"]["total_rules"] == 20
        assert db_scan.passed_rules == json_data["summary"]["passed_rules"] == 10
        assert db_scan.failed_rules == json_data["summary"]["failed_rules"] == 10
        assert (
            db_scan.tested_rule_compliance
            == json_data["summary"]["tested_rule_compliance"]
            == 50.0
        )

        # Assert Devices table matches JSON response
        db_devices = dev_repo.list_by_scan_id(scan_id)
        assert len(db_devices) == len(json_data["devices"]) == 2

        db_dev_map = {d.source_filename: d for d in db_devices}
        json_dev_map = {d["source_filename"]: d for d in json_data["devices"]}

        for filename in ["core.cfg", "edge.cfg"]:
            p_dev = db_dev_map[filename]
            j_dev = json_dev_map[filename]

            assert p_dev.id == j_dev["device_id"]
            assert p_dev.name == j_dev["name"]
            assert p_dev.parse_status == j_dev["parse_status"]
            assert p_dev.total_rules == j_dev["summary"]["total_rules"]
            assert p_dev.passed_rules == j_dev["summary"]["passed_rules"]
            assert p_dev.failed_rules == j_dev["summary"]["failed_rules"]
            assert (
                p_dev.tested_rule_compliance
                == j_dev["summary"]["tested_rule_compliance"]
            )

            # Assert RuleResults table matches JSON response
            db_results = res_repo.list_by_device_id(p_dev.id)
            assert len(db_results) == len(j_dev["results"]) == 10

            db_r_map = {r.rule_id: r for r in db_results}
            json_r_map = {r["rule_id"]: r for r in j_dev["results"]}

            for rule_id, j_res in json_r_map.items():
                db_res = db_r_map[rule_id]
                assert db_res.status == j_res["status"]
                assert db_res.severity == j_res["severity"]
                assert db_res.evidence == j_res["evidence"]
                assert db_res.message == j_res["message"]
                assert db_res.remediation == j_res["remediation"]

        conn.close()
