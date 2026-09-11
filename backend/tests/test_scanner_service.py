"""Comprehensive tests for Track 2 scan-processing service (Checkpoint 4)."""

import io
from pathlib import Path
import sqlite3
from typing import Generator
import pytest

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"

from app.database.connection import get_connection
from app.database.repositories import (
    DeviceRepository,
    RuleRepository,
    RuleResultRepository,
    ScanRepository,
)
from app.database.schema import init_db
from app.models.scan import Scan
from app.rules.definitions import INITIAL_RULES
from app.services.compliance import calculate_compliance_score, calculate_scan_summary
from app.services.scanner import run_scan


@pytest.fixture
def memory_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide an isolated in-memory SQLite database connection with schema initialized."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def test_run_scan_contract_signature(memory_db):
    """Verify run_scan adheres to required contract signature."""
    res = run_scan(
        scan_id="scan-uuid-123",
        device_type="cisco_ios",
        uploaded_files=[
            {"filename": "router.txt", "content": "hostname RTR-01\n"}
        ],
        conn=memory_db,
    )
    assert isinstance(res, dict)
    assert res["scan_id"] == "scan-uuid-123"
    assert res["device_type"] == "cisco_ios"
    assert res["status"] == "completed"
    assert "compliance_score" in res
    assert "summary" in res
    assert "devices" in res
    assert len(res["devices"]) == 1


def test_scan_single_compliant_configuration(memory_db):
    """1. Single compliant config -> completed scan, 100% compliance, all rules pass."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        content = f.read()

    res = run_scan(
        scan_id="scan-comp-01",
        device_type="cisco_ios",
        uploaded_files=[{"filename": "compliant_router.txt", "content": content}],
        conn=memory_db,
    )

    assert res["status"] == "completed"
    assert res["summary"]["total_rules"] == 10
    assert res["summary"]["passed_rules"] == 10
    assert res["summary"]["failed_rules"] == 0
    assert res["summary"]["warning_rules"] == 0
    assert res["summary"]["error_rules"] == 0
    assert res["summary"]["tested_rule_compliance"] == 100.0
    assert res["compliance_score"] == 100.0

    dev = res["devices"][0]
    assert dev["name"] == "CORE-RTR-01"
    assert dev["parse_status"] == "success"
    assert dev["summary"]["tested_rule_compliance"] == 100.0
    assert dev["summary"]["passed_rules"] == 10
    assert dev["line_count"] > 10


def test_scan_single_failing_configuration(memory_db):
    """2. Single failing config -> completed scan with 10 failures and 0.0% compliance."""
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "r", encoding="utf-8") as f:
        content = f.read()

    res = run_scan(
        scan_id="scan-fail-01",
        device_type="cisco_ios",
        uploaded_files=[{"filename": "failing_router.txt", "content": content}],
        conn=memory_db,
    )

    assert res["status"] == "completed"
    assert res["summary"]["total_rules"] == 10
    assert res["summary"]["passed_rules"] == 0
    assert res["summary"]["failed_rules"] == 10
    assert res["summary"]["tested_rule_compliance"] == 0.0

    dev = res["devices"][0]
    assert dev["name"] == "DEFAULT-RTR"
    assert dev["summary"]["failed_rules"] == 10
    assert dev["summary"]["tested_rule_compliance"] == 0.0


def test_scan_ambiguous_configuration_preserves_warnings(memory_db):
    """3. Ambiguous config -> warnings preserved and excluded from score denominator."""
    with open(SAMPLE_DATA_DIR / "ambiguous_router.txt", "r", encoding="utf-8") as f:
        content = f.read()

    res = run_scan(
        scan_id="scan-ambi-01",
        device_type="cisco_ios",
        uploaded_files=[{"filename": "ambiguous_router.txt", "content": content}],
        conn=memory_db,
    )

    assert res["status"] == "completed"
    summary = res["summary"]
    assert summary["warning_rules"] >= 4
    # Compliance score formula: passed / (passed + failed) * 100
    expected_score = calculate_compliance_score(
        summary["passed_rules"], summary["failed_rules"]
    )
    assert summary["tested_rule_compliance"] == expected_score

    # Check device results contain warning findings
    dev = res["devices"][0]
    warnings = [r for r in dev["results"] if r["status"] == "warning"]
    assert len(warnings) >= 4


def test_scan_multiple_configurations_multiple_devices(memory_db):
    """4. Multiple config files -> multiple Device records and correct summaries."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        comp_content = f.read()
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "r", encoding="utf-8") as f:
        fail_content = f.read()
    with open(SAMPLE_DATA_DIR / "ambiguous_router.txt", "r", encoding="utf-8") as f:
        ambi_content = f.read()

    res = run_scan(
        scan_id="scan-multi-01",
        device_type="cisco_ios",
        uploaded_files=[
            {"filename": "compliant.cfg", "content": comp_content},
            {"filename": "failing.cfg", "content": fail_content},
            {"filename": "ambiguous.cfg", "content": ambi_content},
        ],
        conn=memory_db,
    )

    assert res["status"] == "completed"
    assert len(res["devices"]) == 3

    dev_names = [d["name"] for d in res["devices"]]
    assert "CORE-RTR-01" in dev_names
    assert "DEFAULT-RTR" in dev_names

    # Check persistence in database
    dev_repo = DeviceRepository(memory_db)
    persisted_devs = dev_repo.list_by_scan_id("scan-multi-01")
    assert len(persisted_devs) == 3


def test_scan_level_and_device_level_counts(memory_db):
    """5 & 6. Correct device-level counts and aggregated scan-level counts."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        comp_content = f.read()
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "r", encoding="utf-8") as f:
        fail_content = f.read()

    res = run_scan(
        scan_id="scan-counts-01",
        device_type="cisco_ios",
        uploaded_files=[
            {"filename": "c1.cfg", "content": comp_content},
            {"filename": "f1.cfg", "content": fail_content},
        ],
        conn=memory_db,
    )

    # Device 1: 10 passed, 0 failed
    dev1 = res["devices"][0]
    assert dev1["summary"]["total_rules"] == 10
    assert dev1["summary"]["passed_rules"] == 10
    assert dev1["summary"]["failed_rules"] == 0

    # Device 2: 0 passed, 10 failed
    dev2 = res["devices"][1]
    assert dev2["summary"]["total_rules"] == 10
    assert dev2["summary"]["passed_rules"] == 0
    assert dev2["summary"]["failed_rules"] == 10

    # Scan level aggregated counts
    scan_sum = res["summary"]
    assert scan_sum["total_rules"] == 20
    assert scan_sum["passed_rules"] == 10
    assert scan_sum["failed_rules"] == 10
    assert scan_sum["tested_rule_compliance"] == 50.0


def test_scan_score_uses_aggregated_pass_fail_not_average_percentages(memory_db):
    """8. Scan score uses aggregated pass/fail counts rather than average device percentages.

    Example from specification:
    Device A: 100% from 10 tested rules (10 pass, 0 fail)
    Device B: 50% from 2 tested rules (1 pass, 1 fail)
    Scan score must be 11 / 12 * 100 = 91.67%, NOT (100 + 50) / 2 = 75.0%.
    """
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        comp_content = f.read()
    with open(SAMPLE_DATA_DIR / "ambiguous_router.txt", "r", encoding="utf-8") as f:
        ambi_content = f.read()

    res = run_scan(
        scan_id="scan-agg-check",
        device_type="cisco_ios",
        uploaded_files=[
            {"filename": "comp.cfg", "content": comp_content},
            {"filename": "ambi.cfg", "content": ambi_content},
        ],
        conn=memory_db,
    )

    dev_a_score = res["devices"][0]["summary"]["tested_rule_compliance"]
    dev_b_score = res["devices"][1]["summary"]["tested_rule_compliance"]
    avg_of_scores = round((dev_a_score + dev_b_score) / 2.0, 2)

    total_passed = (
        res["devices"][0]["summary"]["passed_rules"]
        + res["devices"][1]["summary"]["passed_rules"]
    )
    total_failed = (
        res["devices"][0]["summary"]["failed_rules"]
        + res["devices"][1]["summary"]["failed_rules"]
    )
    aggregated_score = round(total_passed / (total_passed + total_failed) * 100.0, 2)

    assert res["summary"]["tested_rule_compliance"] == aggregated_score
    # In this dataset, aggregated_score != average of percentages
    assert res["summary"]["tested_rule_compliance"] != avg_of_scores

    # Direct mathematical verification of the 10 vs 2 rules example from specification
    summary = calculate_scan_summary(
        [
            [{"status": "pass"}] * 10,
            [{"status": "pass"}, {"status": "fail"}],
        ]
    )
    assert summary.passed_rules == 11
    assert summary.failed_rules == 1
    assert summary.tested_rule_compliance == 91.67  # 11 / 12 * 100 = 91.67%, not 75.0%


def test_scan_persists_devices_and_rule_results(memory_db):
    """9 & 10. Scan, Devices, and RuleResults are all persisted with valid foreign keys."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        content = f.read()

    scan_id = "scan-fk-test"
    run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "router.cfg", "content": content}],
        conn=memory_db,
    )

    scan_repo = ScanRepository(memory_db)
    dev_repo = DeviceRepository(memory_db)
    res_repo = RuleResultRepository(memory_db)

    # Verify Scan
    scan = scan_repo.get_by_id(scan_id)
    assert scan is not None
    assert scan.status == "completed"
    assert scan.passed_rules == 10

    # Verify Device
    devs = dev_repo.list_by_scan_id(scan_id)
    assert len(devs) == 1
    device = devs[0]
    assert device.scan_id == scan_id
    assert device.name == "CORE-RTR-01"

    # Verify RuleResults
    results = res_repo.list_by_device_id(device.id)
    assert len(results) == 10
    for r in results:
        assert r.scan_id == scan_id
        assert r.device_id == device.id
        assert r.status == "pass"


def test_scan_lifecycle_status_transitions(memory_db):
    """11. Scan status transitions correctly: pre-existing pending -> processing -> completed."""
    scan_repo = ScanRepository(memory_db)
    scan_id = "scan-lifecycle-01"

    # Pre-create scan in pending state
    initial_scan = Scan(id=scan_id, device_type="cisco_ios", status="pending")
    scan_repo.create(initial_scan)

    fetched = scan_repo.get_by_id(scan_id)
    assert fetched.status == "pending"

    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        content = f.read()

    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "comp.cfg", "content": content}],
        conn=memory_db,
    )

    assert res["status"] == "completed"
    completed_scan = scan_repo.get_by_id(scan_id)
    assert completed_scan.status == "completed"
    assert completed_scan.completed_at is not None


def test_unsupported_device_type_handled_safely(memory_db):
    """13. Unsupported device type transitions scan to failed and returns controlled error."""
    scan_id = "scan-unsupported-dev"
    res = run_scan(
        scan_id=scan_id,
        device_type="juniper_junos",
        uploaded_files=[{"filename": "junos.cfg", "content": "system { host-name j1; }"}],
        conn=memory_db,
    )

    assert res["status"] == "failed"
    assert "Unsupported device type" in res.get("error_message", "")
    assert res["devices"] == []

    scan_repo = ScanRepository(memory_db)
    scan = scan_repo.get_by_id(scan_id)
    assert scan is not None
    assert scan.status == "failed"


def test_invalid_uploaded_files_input_handled_safely(memory_db):
    """Invalid uploaded_files type is handled gracefully without an unhandled crash."""
    scan_id = "scan-bad-input"
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files="not-a-list-or-tuple",  # type: ignore
        conn=memory_db,
    )

    assert res["status"] == "failed"
    assert "Invalid uploaded_files input" in res.get("error_message", "")

    scan_repo = ScanRepository(memory_db)
    scan = scan_repo.get_by_id(scan_id)
    assert scan.status == "failed"


def test_empty_and_malformed_configuration(memory_db):
    """11 & 12. Empty/malformed config is handled safely and not marked as compliant."""
    scan_id = "scan-empty-cfg"
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "empty.cfg", "content": ""}],
        conn=memory_db,
    )

    assert res["status"] == "completed"
    dev = res["devices"][0]
    assert dev["parse_status"] == "failed"
    assert dev["error_message"] is not None
    assert "empty" in dev["error_message"].lower()

    # Rule compliance must NOT be marked compliant
    assert dev["summary"]["tested_rule_compliance"] == 0.0
    assert res["summary"]["tested_rule_compliance"] == 0.0


def test_parser_failure_isolated_from_other_devices(memory_db):
    """A parser failure for one device does not corrupt or abort other devices."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        comp_content = f.read()

    res = run_scan(
        scan_id="scan-isolation-test",
        device_type="cisco_ios",
        uploaded_files=[
            {"filename": "corrupt.cfg", "content": ""},
            {"filename": "compliant.cfg", "content": comp_content},
        ],
        conn=memory_db,
    )

    assert res["status"] == "completed"
    assert len(res["devices"]) == 2

    dev_corrupt = res["devices"][0]
    assert dev_corrupt["parse_status"] == "failed"
    assert dev_corrupt["summary"]["tested_rule_compliance"] == 0.0

    dev_comp = res["devices"][1]
    assert dev_comp["parse_status"] == "success"
    assert dev_comp["name"] == "CORE-RTR-01"
    assert dev_comp["summary"]["tested_rule_compliance"] == 100.0


def test_no_raw_configuration_stored_in_sqlite(memory_db):
    """14. Raw configuration text is never stored in SQLite."""
    unique_canary = "SUPER_SECRET_CANARY_STRING_NEVER_PERSIST_RAW_99182"
    cfg_text = f"""
    hostname CANARY-RTR
    ! {unique_canary}
    ip ssh version 2
    """

    scan_id = "scan-raw-check"
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "canary.cfg", "content": cfg_text}],
        conn=memory_db,
    )

    assert res["status"] == "completed"

    # Search every table and row in the database for the canary string
    cursor = memory_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        rows = memory_db.execute(f"SELECT * FROM {table}").fetchall()
        for row in rows:
            for val in row:
                assert unique_canary not in str(val), (
                    f"Canary string leaked into database table '{table}' column value!"
                )


def test_secrets_masked_in_returned_results_and_evidence(memory_db):
    """15. Plaintext secrets and passwords never appear in returned results or evidence."""
    secret_pass = "P@ssword987_UltraSecret"
    secret_enable = "CiscoEnableP@ss99"

    cfg_text = f"""
    hostname VAULT-RTR
    enable password 0 {secret_enable}
    username admin password 0 {secret_pass}
    line vty 0 4
     transport input ssh
    """

    res = run_scan(
        scan_id="scan-secrets-test",
        device_type="cisco_ios",
        uploaded_files=[{"filename": "vault.cfg", "content": cfg_text}],
        conn=memory_db,
    )

    # Check returned dictionary
    res_str = str(res)
    assert secret_pass not in res_str
    assert secret_enable not in res_str

    # Check persisted rule results
    res_repo = RuleResultRepository(memory_db)
    dev_id = res["devices"][0]["device_id"]
    results = res_repo.list_by_device_id(dev_id)

    for r in results:
        assert secret_pass not in r.evidence
        assert secret_pass not in r.message
        assert secret_enable not in r.evidence
        assert secret_enable not in r.message


def test_repeated_deterministic_scan_behavior(memory_db):
    """16. Repeated scans with identical input produce identical summaries and findings."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        content = f.read()

    files = [{"filename": "compliant.cfg", "content": content}]

    run1 = run_scan("scan-det-1", "cisco_ios", files, conn=memory_db)
    run2 = run_scan("scan-det-2", "cisco_ios", files, conn=memory_db)

    assert run1["summary"] == run2["summary"]
    assert len(run1["devices"]) == len(run2["devices"])

    d1_results = run1["devices"][0]["results"]
    d2_results = run2["devices"][0]["results"]

    for r1, r2 in zip(d1_results, d2_results):
        assert r1["rule_id"] == r2["rule_id"]
        assert r1["status"] == r2["status"]
        assert r1["severity"] == r2["severity"]
        assert r1["evidence"] == r2["evidence"]
        assert r1["message"] == r2["message"]
        assert r1["remediation"] == r2["remediation"]


def test_file_like_objects_and_tuples_supported(memory_db):
    """Verify uploaded_files accepts io.StringIO and 2-element tuples."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        content = f.read()

    file_obj = io.StringIO(content)
    setattr(file_obj, "filename", "stream_router.cfg")

    tuple_item = ("tuple_router.cfg", content)

    res = run_scan(
        scan_id="scan-stream-test",
        device_type="cisco_ios",
        uploaded_files=[file_obj, tuple_item],
        conn=memory_db,
    )

    assert res["status"] == "completed"
    assert len(res["devices"]) == 2
    assert res["devices"][0]["source_filename"] == "stream_router.cfg"
    assert res["devices"][1]["source_filename"] == "tuple_router.cfg"
    assert res["devices"][0]["parse_status"] == "success"
    assert res["devices"][1]["parse_status"] == "success"


def test_track2_end_to_end_integration(memory_db):
    """14. End-to-end Track 2 integration test:

    sample config
        ↓
    run_scan()
        ↓
    SQLite (Scan, Device, RuleResults)
        ↓
    returned dictionary

    Verify database records match returned summary and results exactly.
    """
    with open(SAMPLE_DATA_DIR / "compliant_router.txt", "r", encoding="utf-8") as f:
        comp_content = f.read()
    with open(SAMPLE_DATA_DIR / "failing_router.txt", "r", encoding="utf-8") as f:
        fail_content = f.read()

    scan_id = "scan-e2e-integ"
    returned = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[
            {"filename": "core_rtr.cfg", "content": comp_content},
            {"filename": "edge_rtr.cfg", "content": fail_content},
        ],
        conn=memory_db,
    )

    # 1. Query Scan table and verify
    scan_repo = ScanRepository(memory_db)
    persisted_scan = scan_repo.get_by_id(scan_id)
    assert persisted_scan is not None
    assert persisted_scan.status == returned["status"] == "completed"
    assert persisted_scan.device_type == returned["device_type"] == "cisco_ios"
    assert persisted_scan.total_rules == returned["summary"]["total_rules"] == 20
    assert persisted_scan.passed_rules == returned["summary"]["passed_rules"] == 10
    assert persisted_scan.failed_rules == returned["summary"]["failed_rules"] == 10
    assert (
        persisted_scan.tested_rule_compliance
        == returned["summary"]["tested_rule_compliance"]
        == 50.0
    )

    # 2. Query Devices table and verify
    dev_repo = DeviceRepository(memory_db)
    persisted_devices = dev_repo.list_by_scan_id(scan_id)
    assert len(persisted_devices) == len(returned["devices"]) == 2

    # Map persisted devices by filename
    dev_by_file = {d.source_filename: d for d in persisted_devices}
    ret_by_file = {d["source_filename"]: d for d in returned["devices"]}

    for fname in ["core_rtr.cfg", "edge_rtr.cfg"]:
        p_dev = dev_by_file[fname]
        r_dev = ret_by_file[fname]

        assert p_dev.id == r_dev["device_id"]
        assert p_dev.name == r_dev["name"]
        assert p_dev.parse_status == r_dev["parse_status"]
        assert p_dev.total_rules == r_dev["summary"]["total_rules"]
        assert p_dev.passed_rules == r_dev["summary"]["passed_rules"]
        assert p_dev.failed_rules == r_dev["summary"]["failed_rules"]
        assert (
            p_dev.tested_rule_compliance
            == r_dev["summary"]["tested_rule_compliance"]
        )

        # 3. Query RuleResults table and verify
        res_repo = RuleResultRepository(memory_db)
        persisted_results = res_repo.list_by_device_id(p_dev.id)
        assert len(persisted_results) == len(r_dev["results"]) == 10

        p_res_by_rule = {r.rule_id: r for r in persisted_results}
        r_res_by_rule = {r["rule_id"]: r for r in r_dev["results"]}

        for rule in INITIAL_RULES:
            p_res = p_res_by_rule[rule.rule_id]
            r_res = r_res_by_rule[rule.rule_id]

            assert p_res.status == r_res["status"]
            assert p_res.severity == r_res["severity"]
            assert p_res.evidence == r_res["evidence"]
            assert p_res.message == r_res["message"]
            assert p_res.remediation == r_res["remediation"]
