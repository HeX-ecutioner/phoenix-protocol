import json
import sqlite3
from typing import List, Optional

from app.models import (
    Diagnostic,
    Evidence,
    NormalizedSetting,
    ParserInfo,
    RuleResult,
    ScanResult,
    ScanSummary,
    SourceInfo,
)


class ScanRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_scan(
        self,
        scan_id: str,
        created_at: str,
        status: str,
        source: SourceInfo,
        parser: ParserInfo,
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO scans (scan_id, created_at, status, original_filename, sha256, size_bytes, format, parser_id, parser_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                scan_id,
                created_at,
                status,
                source.original_filename,
                source.sha256,
                source.size_bytes,
                source.format,
                parser.parser_id,
                parser.parser_version,
            ),
        )

    def save_normalized_settings(self, scan_id: str, settings: List[NormalizedSetting]):
        cursor = self.conn.cursor()
        for setting in settings:
            cursor.execute(
                """
                INSERT INTO normalized_settings (
                    scan_id, setting_key, value_json, value_type,
                    source_line_start, source_line_end, source_text, confidence, sensitive
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scan_id,
                    setting.key,
                    json.dumps(setting.value),
                    setting.value_type,
                    setting.source_line_start,
                    setting.source_line_end,
                    setting.source_text,
                    setting.confidence,
                    setting.sensitive,
                ),
            )

    def save_rule_results(self, scan_id: str, results: List[RuleResult]):
        cursor = self.conn.cursor()
        for res in results:
            # Rule Version isn't directly on RuleResult in models currently, assume "1.0"
            rule_version = "1.0"
            cursor.execute(
                """
                INSERT INTO rule_results (
                    scan_id, rule_id, title, category, severity,
                    rule_version, status, rationale
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scan_id,
                    res.rule_id,
                    res.title,
                    res.category,
                    res.severity,
                    rule_version,
                    res.status,
                    res.rationale,
                ),
            )

            # Save evidence for this rule
            for ev in res.evidence:
                cursor.execute(
                    """
                    INSERT INTO evidence (
                        scan_id, rule_id, setting_key, observed_value_json,
                        expected_value_json, source_line_start, source_line_end,
                        source_text, safe_to_display
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        scan_id,
                        res.rule_id,
                        ev.setting_key,
                        json.dumps(ev.observed_value),
                        json.dumps(ev.expected_value),
                        ev.source_line_start,
                        ev.source_line_end,
                        ev.source_text,
                        ev.safe_to_display,
                    ),
                )

            # Save diagnostics for this rule
            for diag in res.diagnostics:
                cursor.execute(
                    """
                    INSERT INTO diagnostics (
                        scan_id, rule_id, code, severity, message,
                        source_line_start, source_line_end, field
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        scan_id,
                        res.rule_id,
                        diag.code,
                        diag.severity,
                        diag.message,
                        diag.source_line_start,
                        diag.source_line_end,
                        diag.field,
                    ),
                )

    def save_diagnostics(
        self, scan_id: str, diagnostics: List[Diagnostic], rule_id: Optional[str] = None
    ):
        cursor = self.conn.cursor()
        for diag in diagnostics:
            cursor.execute(
                """
                INSERT INTO diagnostics (
                    scan_id, rule_id, code, severity, message,
                    source_line_start, source_line_end, field
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scan_id,
                    rule_id,
                    diag.code,
                    diag.severity,
                    diag.message,
                    diag.source_line_start,
                    diag.source_line_end,
                    diag.field,
                ),
            )

    def save_summary(self, scan_id: str, summary: ScanSummary, status: str):
        cursor = self.conn.cursor()
        summary_dict = {
            "total_rules": summary.total_rules,
            "tested_rules": summary.tested_rules,
            "compliant": summary.compliant,
            "failing": summary.failing,
            "ambiguous": summary.ambiguous,
            "not_applicable": summary.not_applicable,
            "error": summary.error,
            "warning_count": summary.warning_count,
            "compliance_percent": summary.compliance_percent,
            "compliance_basis": summary.compliance_basis,
        }
        cursor.execute(
            """
            UPDATE scans
            SET summary_json = ?, status = ?
            WHERE scan_id = ?
        """,
            (json.dumps(summary_dict), status, scan_id),
        )

    def get_scan(self, scan_id: str) -> Optional[ScanResult]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
        scan_row = cursor.fetchone()
        if not scan_row:
            return None

        source = SourceInfo(
            original_filename=scan_row["original_filename"],
            sha256=scan_row["sha256"],
            size_bytes=scan_row["size_bytes"],
            format=scan_row["format"],
        )
        parser = ParserInfo(
            parser_id=scan_row["parser_id"],
            parser_version=scan_row["parser_version"],
            normalized_setting_count=0,  # Could be derived from count(*)
        )

        summary = None
        if scan_row["summary_json"]:
            s_dict = json.loads(scan_row["summary_json"])
            summary = ScanSummary(
                total_rules=s_dict["total_rules"],
                tested_rules=s_dict["tested_rules"],
                compliant=s_dict["compliant"],
                failing=s_dict["failing"],
                ambiguous=s_dict["ambiguous"],
                not_applicable=s_dict["not_applicable"],
                error=s_dict["error"],
                warning_count=s_dict["warning_count"],
                compliance_percent=s_dict["compliance_percent"],
                compliance_basis=s_dict["compliance_basis"],
            )

        cursor.execute("SELECT * FROM rule_results WHERE scan_id = ?", (scan_id,))
        rule_rows = cursor.fetchall()

        cursor.execute("SELECT * FROM evidence WHERE scan_id = ?", (scan_id,))
        ev_rows = cursor.fetchall()

        cursor.execute("SELECT * FROM diagnostics WHERE scan_id = ?", (scan_id,))
        diag_rows = cursor.fetchall()

        results = []
        for rr in rule_rows:
            r_id = rr["rule_id"]

            rule_evidence = []
            for ev in ev_rows:
                if ev["rule_id"] == r_id:
                    rule_evidence.append(
                        Evidence(
                            setting_key=ev["setting_key"],
                            observed_value=(
                                json.loads(ev["observed_value_json"])
                                if ev["observed_value_json"]
                                else None
                            ),
                            expected_value=(
                                json.loads(ev["expected_value_json"])
                                if ev["expected_value_json"]
                                else None
                            ),
                            source_line_start=ev["source_line_start"],
                            source_line_end=ev["source_line_end"],
                            source_text=ev["source_text"],
                            safe_to_display=bool(ev["safe_to_display"]),
                        )
                    )

            rule_diags = []
            for diag in diag_rows:
                if diag["rule_id"] == r_id:
                    rule_diags.append(
                        Diagnostic(
                            code=diag["code"],
                            message=diag["message"],
                            severity=diag["severity"],
                            source_line_start=diag["source_line_start"],
                            source_line_end=diag["source_line_end"],
                            field=diag["field"],
                        )
                    )

            results.append(
                RuleResult(
                    rule_id=r_id,
                    title=rr["title"],
                    category=rr["category"],
                    severity=rr["severity"],
                    status=rr["status"],
                    rationale=rr["rationale"],
                    evidence=rule_evidence,
                    diagnostics=rule_diags,
                )
            )

        scan_warnings = [
            Diagnostic(
                code=d["code"],
                message=d["message"],
                severity=d["severity"],
                source_line_start=d["source_line_start"],
                source_line_end=d["source_line_end"],
                field=d["field"],
            )
            for d in diag_rows
            if d["rule_id"] is None and d["severity"] == "warning"
        ]

        scan_errors = [
            Diagnostic(
                code=d["code"],
                message=d["message"],
                severity=d["severity"],
                source_line_start=d["source_line_start"],
                source_line_end=d["source_line_end"],
                field=d["field"],
            )
            for d in diag_rows
            if d["rule_id"] is None and d["severity"] == "error"
        ]

        return ScanResult(
            scan_id=scan_row["scan_id"],
            status=scan_row["status"],
            source=source,
            parser=parser,
            summary=summary,
            results=results,
            warnings=scan_warnings,
            errors=scan_errors,
            created_at=scan_row["created_at"],
        )
