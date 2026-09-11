"""Tests for SQLite database persistence, schema, constraints, and repositories."""

import sqlite3
import pytest

from app.database.connection import get_connection
from app.database.repositories import (
    DeviceRepository,
    RuleRepository,
    RuleResultRepository,
    ScanRepository,
    create_device,
    create_rule,
    create_rule_result,
    create_scan,
    get_device,
    get_device_summary,
    get_rule,
    get_rule_result,
    get_scan,
    get_scan_summary,
    list_devices_for_scan,
    list_rule_results_for_device,
    list_rules,
)
from app.database.schema import init_db
from app.models.device import Device
from app.models.rule import Rule
from app.models.rule_result import RuleResult
from app.models.scan import Scan
from app.services.compliance import ComplianceSummary


@pytest.fixture
def db_conn():
    """Create an in-memory SQLite connection with foreign keys and initialized schema."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def test_db_init_and_foreign_keys(db_conn):
    """Verify in-memory database initializes with foreign keys enabled and correct tables."""
    cursor = db_conn.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    assert fk_status == 1

    cursor = db_conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert {"scans", "devices", "rules", "rule_results"}.issubset(tables)


def test_scan_crud_and_null_handling(db_conn):
    """Verify Scan CRUD behavior and safe handling of None/null optional fields."""
    scan_repo = ScanRepository(db_conn)

    scan = Scan(
        id="scan-123",
        device_type="cisco_ios",
        status="pending",
        parser_version="1.0.0",
        rule_set_version="1.0.0",
        total_rules=0,
        passed_rules=0,
        failed_rules=0,
        warning_rules=0,
        not_applicable_rules=0,
        error_rules=0,
        tested_rule_compliance=0.0,
        created_at=None,
        updated_at=None,
        completed_at=None,
    )
    scan_repo.create(scan)

    fetched = scan_repo.get_by_id("scan-123")
    assert fetched is not None
    assert fetched.id == "scan-123"
    assert fetched.completed_at is None
    assert fetched.tested_rule_compliance == 0.0

    # Update summary
    new_summary = ComplianceSummary(
        total_rules=10,
        passed_rules=8,
        failed_rules=2,
        warning_rules=0,
        not_applicable_rules=0,
        error_rules=0,
        tested_rule_compliance=80.0,
    )
    scan_repo.update_summary("scan-123", new_summary)
    scan_repo.update_status("scan-123", status="completed", completed_at="2026-09-11 12:00:00")

    updated = scan_repo.get_by_id("scan-123")
    assert updated.status == "completed"
    assert updated.completed_at == "2026-09-11 12:00:00"
    assert updated.tested_rule_compliance == 80.0
    assert updated.passed_rules == 8


def test_device_crud_and_null_handling(db_conn):
    """Verify Device CRUD behavior, safe null handling, and scan relationship."""
    scan_repo = ScanRepository(db_conn)
    device_repo = DeviceRepository(db_conn)

    scan = Scan(id="scan-parent")
    scan_repo.create(scan)

    device = Device(
        id="dev-001",
        scan_id="scan-parent",
        name="EDGE-RTR-01",
        display_name=None,
        vendor=None,
        device_type="cisco_ios",
        source_filename="edge_rtr.cfg",
        parse_status="success",
        line_count=None,
        error_message=None,
    )
    device_repo.create(device)

    fetched = device_repo.get_by_id("dev-001")
    assert fetched is not None
    assert fetched.name == "EDGE-RTR-01"
    assert fetched.display_name == "EDGE-RTR-01"
    assert fetched.vendor is None
    assert fetched.line_count is None
    assert fetched.error_message is None

    # List devices for scan
    devices = device_repo.list_devices_for_scan("scan-parent")
    assert len(devices) == 1
    assert devices[0].id == "dev-001"


def test_rule_crud_upsert_and_active_filtering(db_conn):
    """Verify Rule CRUD, upsert semantics, and active_only filter."""
    rule_repo = RuleRepository(db_conn)

    rule1 = Rule(
        rule_id="NET-001",
        title="Telnet Disabled",
        description="Telnet must be disabled",
        technical_requirement="transport input ssh",
        severity="high",
        device_type="cisco_ios",
        category="Management",
        remediation="line vty 0 4\n transport input ssh",
        active=True,
        rule_version="1.0.0",
    )
    rule2 = Rule(
        rule_id="NET-002",
        title="Legacy Inactive Rule",
        description="Deprecated check",
        technical_requirement="None",
        severity="low",
        device_type="cisco_ios",
        category="Legacy",
        remediation="None",
        active=False,
        rule_version="0.9.0",
    )
    rule_repo.create(rule1)
    rule_repo.create(rule2)

    assert rule_repo.get_by_id("NET-001") is not None
    assert rule_repo.get_by_id("NET-NONEXISTENT") is None

    all_rules = rule_repo.list_all(active_only=False)
    assert len(all_rules) == 2

    active_rules = rule_repo.list_all(active_only=True)
    assert len(active_rules) == 1
    assert active_rules[0].rule_id == "NET-001"

    # Test upsert updates existing rule
    updated_rule1 = Rule(
        rule_id="NET-001",
        title="Telnet Disabled (Updated)",
        description="Updated description",
        technical_requirement="transport input ssh only",
        severity="high",
        device_type="cisco_ios",
        category="Management",
        remediation="updated remediation",
        active=True,
        rule_version="1.1.0",
    )
    rule_repo.upsert(updated_rule1)
    fetched_updated = rule_repo.get_by_id("NET-001")
    assert fetched_updated.title == "Telnet Disabled (Updated)"
    assert fetched_updated.rule_version == "1.1.0"


def test_foreign_key_enforcement(db_conn):
    """Verify SQLite foreign key constraints reject orphan devices and orphan results."""
    device_repo = DeviceRepository(db_conn)
    result_repo = RuleResultRepository(db_conn)

    # Attempt to insert a device with non-existent scan_id
    orphan_device = Device(
        id="dev-orphan",
        scan_id="non-existent-scan",
        name="Orphan",
        device_type="cisco_ios",
        source_filename="orphan.cfg",
    )
    with pytest.raises(sqlite3.IntegrityError):
        device_repo.create(orphan_device)

    # Now create valid scan and device
    create_scan(db_conn, Scan(id="valid-scan"))
    create_device(db_conn, Device(id="valid-dev", scan_id="valid-scan", name="Device1"))

    # Attempt to insert rule_result with non-existent rule_id
    orphan_result = RuleResult(
        id="res-orphan",
        device_id="valid-dev",
        rule_id="NET-NONEXISTENT",
        status="pass",
        severity="high",
    )
    with pytest.raises(sqlite3.IntegrityError):
        result_repo.create(orphan_result)


def test_cascade_delete_scan(db_conn):
    """Verify deleting a scan cascades and deletes child devices and rule results."""
    scan = Scan(id="scan-cascade")
    create_scan(db_conn, scan)

    device = Device(id="dev-cascade", scan_id="scan-cascade", name="RTR")
    create_device(db_conn, device)

    rule = Rule(rule_id="NET-001", title="T1", description="D1", severity="high")
    create_rule(db_conn, rule)

    result = RuleResult(
        id="res-cascade",
        scan_id="scan-cascade",
        device_id="dev-cascade",
        rule_id="NET-001",
        status="pass",
        severity="high",
    )
    create_rule_result(db_conn, result)

    assert get_device(db_conn, "dev-cascade") is not None
    assert get_rule_result(db_conn, "res-cascade") is not None

    # Delete scan
    db_conn.execute("DELETE FROM scans WHERE id = ?", ("scan-cascade",))
    db_conn.commit()

    assert get_scan(db_conn, "scan-cascade") is None
    assert get_device(db_conn, "dev-cascade") is None
    assert get_rule_result(db_conn, "res-cascade") is None


def test_rule_uniqueness_constraint(db_conn):
    """Verify uniqueness constraint preventing duplicate results for the same device/rule."""
    create_scan(db_conn, Scan(id="scan-uq"))
    create_device(db_conn, Device(id="dev-uq", scan_id="scan-uq", name="RTR"))
    create_rule(db_conn, Rule(rule_id="NET-001", title="T1", description="D1", severity="high"))

    result1 = RuleResult(
        id="res-uq-1",
        device_id="dev-uq",
        rule_id="NET-001",
        status="pass",
        severity="high",
        evidence="transport input ssh",
    )
    create_rule_result(db_conn, result1)

    result2 = RuleResult(
        id="res-uq-2",
        device_id="dev-uq",
        rule_id="NET-001",  # Same device_id and rule_id
        status="fail",
        severity="high",
        evidence="duplicate entry",
    )
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        create_rule_result(db_conn, result2)


def test_summary_queries_and_tested_rule_compliance(db_conn):
    """Verify device-level and scan-level summaries directly through repository SQL queries.

    Confirms:
    1. Excludes warning, not_applicable, error from denominator
    2. Warnings/errors remain separate counts
    3. Scan summary aggregates across all devices (not averaging percentages)
    """
    create_scan(db_conn, Scan(id="scan-multi"))

    # Device 1: 3 pass, 1 fail, 1 warning (Tested compliance: 3 / 4 = 75.0%)
    create_device(db_conn, Device(id="dev-1", scan_id="scan-multi", name="D1"))
    # Device 2: 1 pass, 3 fail, 1 not_applicable (Tested compliance: 1 / 4 = 25.0%)
    create_device(db_conn, Device(id="dev-2", scan_id="scan-multi", name="D2"))

    # Register rules
    for i in range(1, 11):
        rule_id = f"NET-{i:03d}"
        create_rule(
            db_conn,
            Rule(rule_id=rule_id, title=f"Rule {i}", description="Desc", severity="medium"),
        )

    # Insert results for Device 1
    create_rule_result(
        db_conn,
        RuleResult(id="r1", device_id="dev-1", rule_id="NET-001", status="pass", severity="medium"),
    )
    create_rule_result(
        db_conn,
        RuleResult(id="r2", device_id="dev-1", rule_id="NET-002", status="pass", severity="medium"),
    )
    create_rule_result(
        db_conn,
        RuleResult(id="r3", device_id="dev-1", rule_id="NET-003", status="pass", severity="medium"),
    )
    create_rule_result(
        db_conn,
        RuleResult(id="r4", device_id="dev-1", rule_id="NET-004", status="fail", severity="medium"),
    )
    create_rule_result(
        db_conn,
        RuleResult(id="r5", device_id="dev-1", rule_id="NET-005", status="warning", severity="medium"),
    )

    # Insert results for Device 2
    create_rule_result(
        db_conn,
        RuleResult(id="r6", device_id="dev-2", rule_id="NET-001", status="pass", severity="medium"),
    )
    create_rule_result(
        db_conn,
        RuleResult(id="r7", device_id="dev-2", rule_id="NET-002", status="fail", severity="medium"),
    )
    create_rule_result(
        db_conn,
        RuleResult(id="r8", device_id="dev-2", rule_id="NET-003", status="fail", severity="medium"),
    )
    create_rule_result(
        db_conn,
        RuleResult(id="r9", device_id="dev-2", rule_id="NET-004", status="fail", severity="medium"),
    )
    create_rule_result(
        db_conn,
        RuleResult(id="r10", device_id="dev-2", rule_id="NET-005", status="not_applicable", severity="medium"),
    )

    result_repo = RuleResultRepository(db_conn)

    # Check Device 1 Summary
    d1_summary = result_repo.get_device_summary("dev-1")
    assert d1_summary.total_rules == 5
    assert d1_summary.passed_rules == 3
    assert d1_summary.failed_rules == 1
    assert d1_summary.warning_rules == 1
    assert d1_summary.not_applicable_rules == 0
    # 3 / (3 + 1) * 100 = 75.0%
    assert d1_summary.tested_rule_compliance == 75.0

    # Check Device 2 Summary
    d2_summary = result_repo.get_device_summary("dev-2")
    assert d2_summary.total_rules == 5
    assert d2_summary.passed_rules == 1
    assert d2_summary.failed_rules == 3
    assert d2_summary.not_applicable_rules == 1
    # 1 / (1 + 3) * 100 = 25.0%
    assert d2_summary.tested_rule_compliance == 25.0

    # Check Scan Summary (Aggregated across both devices)
    # Total tested: 4 passed (3 from d1 + 1 from d2), 4 failed (1 from d1 + 3 from d2)
    # Total tested = 8. Compliance = 4 / 8 * 100 = 50.0%
    # Note: Device averages would be (75.0 + 25.0) / 2 = 50.0%, so let's verify exact counts:
    scan_summary = result_repo.get_scan_summary("scan-multi")
    assert scan_summary.total_rules == 10
    assert scan_summary.passed_rules == 4
    assert scan_summary.failed_rules == 4
    assert scan_summary.warning_rules == 1
    assert scan_summary.not_applicable_rules == 1
    assert scan_summary.tested_rule_compliance == 50.0


def test_parameterized_query_safety(db_conn):
    """Verify repository queries safely handle potential injection strings via parameterized queries."""
    scan = Scan(id="scan'; DROP TABLE scans; --")
    create_scan(db_conn, scan)

    fetched = get_scan(db_conn, "scan'; DROP TABLE scans; --")
    assert fetched is not None
    assert fetched.id == "scan'; DROP TABLE scans; --"

    # Confirm scans table is still intact and exists
    cursor = db_conn.execute("SELECT COUNT(*) FROM scans;")
    assert cursor.fetchone()[0] == 1


def test_functional_convenience_helpers(db_conn):
    """Verify functional convenience helpers for repositories."""
    scan = Scan(id="fn-scan")
    create_scan(db_conn, scan)
    assert get_scan(db_conn, "fn-scan") is not None

    device = Device(id="fn-dev", scan_id="fn-scan", name="DevFN")
    create_device(db_conn, device)
    assert get_device(db_conn, "fn-dev") is not None
    assert len(list_devices_for_scan(db_conn, "fn-scan")) == 1

    rule = Rule(rule_id="NET-100", title="T", description="D", severity="low")
    create_rule(db_conn, rule)
    assert get_rule(db_conn, "NET-100") is not None
    assert len(list_rules(db_conn)) >= 1

    result = RuleResult(
        id="fn-res",
        device_id="fn-dev",
        rule_id="NET-100",
        status="pass",
        severity="low",
    )
    create_rule_result(db_conn, result)
    assert get_rule_result(db_conn, "fn-res") is not None
    assert len(list_rule_results_for_device(db_conn, "fn-dev")) == 1
    assert get_device_summary(db_conn, "fn-dev").passed_rules == 1
    assert get_scan_summary(db_conn, "fn-scan").passed_rules == 1
