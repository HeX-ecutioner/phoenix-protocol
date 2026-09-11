"""Repository interfaces for database persistence using parameterized queries."""

import sqlite3
from typing import Any, Dict, List, Optional

from app.models.device import Device
from app.models.rule import Rule
from app.models.rule_result import RuleResult
from app.models.scan import Scan
from app.services.compliance import ComplianceSummary, calculate_compliance_score


class ScanRepository:
    """Repository managing scan records."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, scan: Scan) -> None:
        """Insert a scan record using parameterized query."""
        self.conn.execute(
            """
            INSERT INTO scans (
                id, device_type, status, parser_version, rule_set_version,
                total_rules, passed_rules, failed_rules, warning_rules,
                not_applicable_rules, error_rules, tested_rule_compliance,
                created_at, updated_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan.id,
                scan.device_type,
                scan.status,
                scan.parser_version,
                scan.rule_set_version,
                scan.total_rules,
                scan.passed_rules,
                scan.failed_rules,
                scan.warning_rules,
                scan.not_applicable_rules,
                scan.error_rules,
                scan.tested_rule_compliance,
                scan.created_at,
                scan.updated_at,
                scan.completed_at,
            ),
        )
        self.conn.commit()

    def get_by_id(self, scan_id: str) -> Optional[Scan]:
        """Fetch a scan record by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM scans WHERE id = ?",
            (scan_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Scan(
            id=row["id"],
            device_type=row["device_type"],
            status=row["status"],
            parser_version=row["parser_version"],
            rule_set_version=row["rule_set_version"],
            total_rules=row["total_rules"],
            passed_rules=row["passed_rules"],
            failed_rules=row["failed_rules"],
            warning_rules=row["warning_rules"],
            not_applicable_rules=row["not_applicable_rules"],
            error_rules=row["error_rules"],
            tested_rule_compliance=row["tested_rule_compliance"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )

    def update_summary(self, scan_id: str, summary: ComplianceSummary) -> None:
        """Update summary counts and tested-rule compliance for a scan."""
        self.conn.execute(
            """
            UPDATE scans SET
                total_rules = ?,
                passed_rules = ?,
                failed_rules = ?,
                warning_rules = ?,
                not_applicable_rules = ?,
                error_rules = ?,
                tested_rule_compliance = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                summary.total_rules,
                summary.passed_rules,
                summary.failed_rules,
                summary.warning_rules,
                summary.not_applicable_rules,
                summary.error_rules,
                summary.tested_rule_compliance,
                scan_id,
            ),
        )
        self.conn.commit()

    def update_status(
        self, scan_id: str, status: str, completed_at: Optional[str] = None
    ) -> None:
        """Update scan status and optional completed_at timestamp."""
        self.conn.execute(
            """
            UPDATE scans SET
                status = ?,
                completed_at = COALESCE(?, completed_at),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, completed_at, scan_id),
        )
        self.conn.commit()


class DeviceRepository:
    """Repository managing device records."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, device: Device) -> None:
        """Insert a device record using parameterized query."""
        self.conn.execute(
            """
            INSERT INTO devices (
                id, scan_id, name, display_name, vendor, device_type,
                source_filename, parse_status, line_count, error_message,
                total_rules, passed_rules, failed_rules, warning_rules,
                not_applicable_rules, error_rules, tested_rule_compliance,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device.id,
                device.scan_id,
                device.name,
                device.display_name,
                device.vendor,
                device.device_type,
                device.source_filename,
                device.parse_status,
                device.line_count,
                device.error_message,
                device.total_rules,
                device.passed_rules,
                device.failed_rules,
                device.warning_rules,
                device.not_applicable_rules,
                device.error_rules,
                device.tested_rule_compliance,
                device.created_at,
            ),
        )
        self.conn.commit()

    def get_by_id(self, device_id: str) -> Optional[Device]:
        """Fetch a device record by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM devices WHERE id = ?",
            (device_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Device(
            id=row["id"],
            scan_id=row["scan_id"],
            name=row["name"],
            display_name=row["display_name"],
            vendor=row["vendor"],
            device_type=row["device_type"],
            source_filename=row["source_filename"],
            parse_status=row["parse_status"],
            line_count=row["line_count"],
            error_message=row["error_message"],
            total_rules=row["total_rules"],
            passed_rules=row["passed_rules"],
            failed_rules=row["failed_rules"],
            warning_rules=row["warning_rules"],
            not_applicable_rules=row["not_applicable_rules"],
            error_rules=row["error_rules"],
            tested_rule_compliance=row["tested_rule_compliance"],
            created_at=row["created_at"],
        )

    def list_by_scan_id(self, scan_id: str) -> List[Device]:
        """List all devices associated with a given scan."""
        cursor = self.conn.execute(
            "SELECT * FROM devices WHERE scan_id = ? ORDER BY created_at ASC",
            (scan_id,),
        )
        devices: List[Device] = []
        for row in cursor.fetchall():
            devices.append(
                Device(
                    id=row["id"],
                    scan_id=row["scan_id"],
                    name=row["name"],
                    display_name=row["display_name"],
                    vendor=row["vendor"],
                    device_type=row["device_type"],
                    source_filename=row["source_filename"],
                    parse_status=row["parse_status"],
                    line_count=row["line_count"],
                    error_message=row["error_message"],
                    total_rules=row["total_rules"],
                    passed_rules=row["passed_rules"],
                    failed_rules=row["failed_rules"],
                    warning_rules=row["warning_rules"],
                    not_applicable_rules=row["not_applicable_rules"],
                    error_rules=row["error_rules"],
                    tested_rule_compliance=row["tested_rule_compliance"],
                    created_at=row["created_at"],
                )
            )
        return devices

    def list_devices_for_scan(self, scan_id: str) -> List[Device]:
        """Alias for list_by_scan_id."""
        return self.list_by_scan_id(scan_id)

    def update_summary(self, device_id: str, summary: ComplianceSummary) -> None:
        """Update device-level summary counts and compliance score."""
        self.conn.execute(
            """
            UPDATE devices SET
                total_rules = ?,
                passed_rules = ?,
                failed_rules = ?,
                warning_rules = ?,
                not_applicable_rules = ?,
                error_rules = ?,
                tested_rule_compliance = ?
            WHERE id = ?
            """,
            (
                summary.total_rules,
                summary.passed_rules,
                summary.failed_rules,
                summary.warning_rules,
                summary.not_applicable_rules,
                summary.error_rules,
                summary.tested_rule_compliance,
                device_id,
            ),
        )
        self.conn.commit()


class RuleRepository:
    """Repository managing rule definitions."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, rule: Rule) -> None:
        """Insert a rule definition."""
        self.upsert(rule)

    def upsert(self, rule: Rule) -> None:
        """Upsert a rule definition."""
        self.conn.execute(
            """
            INSERT INTO rules (
                rule_id, title, description, technical_requirement,
                severity, device_type, category, remediation, active, rule_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rule_id) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                technical_requirement = excluded.technical_requirement,
                severity = excluded.severity,
                device_type = excluded.device_type,
                category = excluded.category,
                remediation = excluded.remediation,
                active = excluded.active,
                rule_version = excluded.rule_version
            """,
            (
                rule.rule_id,
                rule.title,
                rule.description,
                rule.technical_requirement,
                rule.severity,
                rule.device_type,
                rule.category,
                rule.remediation,
                1 if rule.active else 0,
                rule.rule_version,
            ),
        )
        self.conn.commit()

    def get_by_id(self, rule_id: str) -> Optional[Rule]:
        """Fetch a rule by its rule_id."""
        cursor = self.conn.execute(
            "SELECT * FROM rules WHERE rule_id = ?",
            (rule_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Rule(
            rule_id=row["rule_id"],
            title=row["title"],
            description=row["description"],
            technical_requirement=row["technical_requirement"],
            severity=row["severity"],
            device_type=row["device_type"],
            category=row["category"],
            remediation=row["remediation"],
            active=bool(row["active"]),
            rule_version=row["rule_version"],
        )

    def list_all(self, active_only: bool = False) -> List[Rule]:
        """List all rules, optionally filtering by active flag."""
        if active_only:
            cursor = self.conn.execute(
                "SELECT * FROM rules WHERE active = 1 ORDER BY rule_id ASC"
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM rules ORDER BY rule_id ASC"
            )
        rules: List[Rule] = []
        for row in cursor.fetchall():
            rules.append(
                Rule(
                    rule_id=row["rule_id"],
                    title=row["title"],
                    description=row["description"],
                    technical_requirement=row["technical_requirement"],
                    severity=row["severity"],
                    device_type=row["device_type"],
                    category=row["category"],
                    remediation=row["remediation"],
                    active=bool(row["active"]),
                    rule_version=row["rule_version"],
                )
            )
        return rules

    def list_rules(self, active_only: bool = False) -> List[Rule]:
        """Alias for list_all."""
        return self.list_all(active_only)


class RuleResultRepository:
    """Repository managing rule evaluation results."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, result: RuleResult) -> None:
        """Insert a single rule result."""
        self.create_batch([result])

    def create_batch(self, results: List[RuleResult]) -> None:
        """Insert rule results using parameterized batch query."""
        self.conn.executemany(
            """
            INSERT INTO rule_results (
                id, scan_id, device_id, rule_id, status, severity,
                evidence, evidence_line_range, message, remediation,
                evaluation_timestamp, engine_version, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r.id,
                    r.scan_id,
                    r.device_id,
                    r.rule_id,
                    r.status,
                    r.severity,
                    r.evidence,
                    r.evidence_line_range,
                    r.message,
                    r.remediation,
                    r.evaluation_timestamp,
                    r.engine_version,
                    r.error_message,
                )
                for r in results
            ],
        )
        self.conn.commit()

    def get_by_id(self, result_id: str) -> Optional[RuleResult]:
        """Fetch a rule result by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM rule_results WHERE id = ?",
            (result_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return RuleResult(
            id=row["id"],
            scan_id=row["scan_id"],
            device_id=row["device_id"],
            rule_id=row["rule_id"],
            status=row["status"],
            severity=row["severity"],
            evidence=row["evidence"],
            evidence_line_range=row["evidence_line_range"],
            message=row["message"],
            remediation=row["remediation"],
            evaluation_timestamp=row["evaluation_timestamp"],
            engine_version=row["engine_version"],
            error_message=row["error_message"],
        )

    def list_by_device_id(self, device_id: str) -> List[RuleResult]:
        """List all rule results for a device."""
        cursor = self.conn.execute(
            "SELECT * FROM rule_results WHERE device_id = ? ORDER BY rule_id ASC",
            (device_id,),
        )
        results: List[RuleResult] = []
        for row in cursor.fetchall():
            results.append(
                RuleResult(
                    id=row["id"],
                    scan_id=row["scan_id"],
                    device_id=row["device_id"],
                    rule_id=row["rule_id"],
                    status=row["status"],
                    severity=row["severity"],
                    evidence=row["evidence"],
                    evidence_line_range=row["evidence_line_range"],
                    message=row["message"],
                    remediation=row["remediation"],
                    evaluation_timestamp=row["evaluation_timestamp"],
                    engine_version=row["engine_version"],
                    error_message=row["error_message"],
                )
            )
        return results

    def list_rule_results_for_device(self, device_id: str) -> List[RuleResult]:
        """Alias for list_by_device_id."""
        return self.list_by_device_id(device_id)

    def list_by_scan_id(self, scan_id: str) -> List[RuleResult]:
        """List all rule results for a scan across all its devices."""
        cursor = self.conn.execute(
            """
            SELECT r.*
            FROM rule_results r
            JOIN devices d ON r.device_id = d.id
            WHERE d.scan_id = ?
            ORDER BY d.id ASC, r.rule_id ASC
            """,
            (scan_id,),
        )
        results: List[RuleResult] = []
        for row in cursor.fetchall():
            results.append(
                RuleResult(
                    id=row["id"],
                    scan_id=row["scan_id"],
                    device_id=row["device_id"],
                    rule_id=row["rule_id"],
                    status=row["status"],
                    severity=row["severity"],
                    evidence=row["evidence"],
                    evidence_line_range=row["evidence_line_range"],
                    message=row["message"],
                    remediation=row["remediation"],
                    evaluation_timestamp=row["evaluation_timestamp"],
                    engine_version=row["engine_version"],
                    error_message=row["error_message"],
                )
            )
        return results

    def get_device_summary(self, device_id: str) -> ComplianceSummary:
        """Calculate compliance summary for a device directly via parameterized SQL."""
        cursor = self.conn.execute(
            """
            SELECT status, COUNT(*) as cnt
            FROM rule_results
            WHERE device_id = ?
            GROUP BY status
            """,
            (device_id,),
        )
        counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
        passed = counts.get("pass", 0)
        failed = counts.get("fail", 0)
        warning = counts.get("warning", 0)
        not_applicable = counts.get("not_applicable", 0)
        error = counts.get("error", 0)
        total = sum(counts.values())
        score = calculate_compliance_score(passed, failed)

        return ComplianceSummary(
            total_rules=total,
            passed_rules=passed,
            failed_rules=failed,
            warning_rules=warning,
            not_applicable_rules=not_applicable,
            error_rules=error,
            tested_rule_compliance=score,
        )

    def get_scan_summary(self, scan_id: str) -> ComplianceSummary:
        """Calculate scan-level summary by aggregating all device results."""
        cursor = self.conn.execute(
            """
            SELECT r.status, COUNT(*) as cnt
            FROM rule_results r
            JOIN devices d ON r.device_id = d.id
            WHERE d.scan_id = ?
            GROUP BY r.status
            """,
            (scan_id,),
        )
        counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
        passed = counts.get("pass", 0)
        failed = counts.get("fail", 0)
        warning = counts.get("warning", 0)
        not_applicable = counts.get("not_applicable", 0)
        error = counts.get("error", 0)
        total = sum(counts.values())
        score = calculate_compliance_score(passed, failed)

        return ComplianceSummary(
            total_rules=total,
            passed_rules=passed,
            failed_rules=failed,
            warning_rules=warning,
            not_applicable_rules=not_applicable,
            error_rules=error,
            tested_rule_compliance=score,
        )


# Functional convenience helpers
def create_scan(conn: sqlite3.Connection, scan: Scan) -> None:
    ScanRepository(conn).create(scan)


def get_scan(conn: sqlite3.Connection, scan_id: str) -> Optional[Scan]:
    return ScanRepository(conn).get_by_id(scan_id)


def create_device(conn: sqlite3.Connection, device: Device) -> None:
    DeviceRepository(conn).create(device)


def get_device(conn: sqlite3.Connection, device_id: str) -> Optional[Device]:
    return DeviceRepository(conn).get_by_id(device_id)


def list_devices_for_scan(conn: sqlite3.Connection, scan_id: str) -> List[Device]:
    return DeviceRepository(conn).list_by_scan_id(scan_id)


def create_rule(conn: sqlite3.Connection, rule: Rule) -> None:
    RuleRepository(conn).create(rule)


def get_rule(conn: sqlite3.Connection, rule_id: str) -> Optional[Rule]:
    return RuleRepository(conn).get_by_id(rule_id)


def list_rules(conn: sqlite3.Connection, active_only: bool = False) -> List[Rule]:
    return RuleRepository(conn).list_all(active_only)


def create_rule_result(conn: sqlite3.Connection, result: RuleResult) -> None:
    RuleResultRepository(conn).create(result)


def get_rule_result(conn: sqlite3.Connection, result_id: str) -> Optional[RuleResult]:
    return RuleResultRepository(conn).get_by_id(result_id)


def list_rule_results_for_device(
    conn: sqlite3.Connection, device_id: str
) -> List[RuleResult]:
    return RuleResultRepository(conn).list_by_device_id(device_id)


def get_device_summary(conn: sqlite3.Connection, device_id: str) -> ComplianceSummary:
    return RuleResultRepository(conn).get_device_summary(device_id)


def get_scan_summary(conn: sqlite3.Connection, scan_id: str) -> ComplianceSummary:
    return RuleResultRepository(conn).get_scan_summary(scan_id)
