"""Scan-processing service orchestrating parsing, compliance rule evaluation, and persistence."""

from datetime import datetime, timezone
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.database.connection import get_connection
from app.database.schema import init_db
from app.models.device import Device
from app.models.normalized_config import NormalizedConfig
from app.models.rule_result import RuleResult
from app.models.scan import Scan
from app.parsers.cisco_like import CiscoLikeParser
from app.rules.definitions import INITIAL_RULES
from app.rules.engine import evaluate_all
from app.services.compliance import ComplianceSummary

SUPPORTED_DEVICE_TYPES = {
    "cisco_ios",
    "cisco",
    "cisco-like",
    "cisco_like",
    "cisco_xe",
    "cisco_xr",
    "cisco_nxos",
}
DEFAULT_DEVICE_TYPE = "cisco_ios"
PARSER_VERSION = "1.0.0"
RULE_SET_VERSION = "1.0.0"


def _extract_file_data(item: Any, index: int) -> Tuple[str, str, Optional[str]]:
    """Safely extract (filename, content_str, extraction_error) from uploaded file item.

    Supports:
    - dicts with filename/name and content/text/data/file
    - 2-element tuples/lists (filename, content)
    - objects with filename/name and read() method
    - raw string content
    - bytes (safely decoded as utf-8)
    """
    filename = f"device_{index + 1}.cfg"
    content_str = ""
    extraction_error: Optional[str] = None

    try:
        if isinstance(item, dict):
            filename = (
                item.get("filename")
                or item.get("source_filename")
                or item.get("name")
                or filename
            )
            raw = item.get("content") or item.get("text") or item.get("data")
            if raw is not None and hasattr(raw, "read"):
                raw = raw.read()
            if raw is None and "file" in item:
                f = item["file"]
                raw = f.read() if hasattr(f, "read") else str(f)
            content_str = raw if raw is not None else ""
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            filename = str(item[0])
            raw = item[1]
            if hasattr(raw, "read"):
                raw = raw.read()
            content_str = raw if raw is not None else ""
        elif hasattr(item, "read"):
            filename = getattr(item, "filename", getattr(item, "name", filename))
            raw = item.read()
            content_str = raw if raw is not None else ""
        elif isinstance(item, str):
            content_str = item
        else:
            extraction_error = (
                f"Invalid uploaded file input item at index {index}: "
                f"expected dict, tuple, file-like object, or str, got {type(item).__name__}."
            )
            return filename, "", extraction_error

        if isinstance(content_str, bytes):
            content_str = content_str.decode("utf-8", errors="replace")
        elif not isinstance(content_str, str):
            content_str = str(content_str)

    except Exception as exc:
        extraction_error = f"Error reading uploaded file at index {index}: {exc}"
        return filename, "", extraction_error

    return filename, content_str, None


def run_scan(
    scan_id: str,
    device_type: str,
    uploaded_files: List[Any],
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Execute compliance scan across accepted uploaded configuration files.

    Design contract:
    1. Scan lifecycle: created/processing -> completed (or failed)
    2. Safely read each configuration without executing or storing raw config
    3. Parse configuration using deterministic parser
    4. Create exactly one Device record per uploaded file
    5. Evaluate all active baseline rules (NET-001 - NET-010) deterministically
    6. Persist RuleResults and update Device-level compliance summary
    7. Aggregate scan summary across all devices (pass/fail totals, not averaged percentages)
    8. Return predictable dictionary suitable for API serialization
    """
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        from app.database.repositories import (
            DeviceRepository,
            RuleRepository,
            RuleResultRepository,
            ScanRepository,
            ensure_rules_seeded,
        )

        init_db(conn)
        ensure_rules_seeded(conn)

        scan_repo = ScanRepository(conn)
        device_repo = DeviceRepository(conn)
        rule_repo = RuleRepository(conn)
        result_repo = RuleResultRepository(conn)

        now_iso = datetime.now(timezone.utc).isoformat()

        # Manage scan record in persistence: create or update to processing
        existing_scan = scan_repo.get_by_id(scan_id)
        if existing_scan is None:
            scan = Scan(
                id=scan_id,
                device_type=device_type or DEFAULT_DEVICE_TYPE,
                status="processing",
                parser_version=PARSER_VERSION,
                rule_set_version=RULE_SET_VERSION,
                created_at=now_iso,
                updated_at=now_iso,
            )
            scan_repo.create(scan)
        else:
            scan_repo.update_status(scan_id, status="processing")

        # Validate requested device type
        device_type_norm = (device_type or "").strip().lower()
        if device_type_norm not in SUPPORTED_DEVICE_TYPES:
            err_msg = (
                f"Unsupported device type: '{device_type}'. "
                f"Currently supported device types: {sorted(SUPPORTED_DEVICE_TYPES)}."
            )
            scan_repo.update_status(scan_id, status="failed", completed_at=now_iso)
            empty_summary = ComplianceSummary()
            return {
                "scan_id": scan_id,
                "status": "failed",
                "device_type": device_type,
                "parser_version": PARSER_VERSION,
                "rule_set_version": RULE_SET_VERSION,
                "summary": empty_summary.to_dict(),
                "compliance_score": 0.0,
                "devices": [],
                "error_message": err_msg,
            }

        # Validate uploaded_files input collection
        if not isinstance(uploaded_files, (list, tuple)):
            err_msg = (
                f"Invalid uploaded_files input: expected list or tuple, "
                f"got {type(uploaded_files).__name__}."
            )
            scan_repo.update_status(scan_id, status="failed", completed_at=now_iso)
            empty_summary = ComplianceSummary()
            return {
                "scan_id": scan_id,
                "status": "failed",
                "device_type": device_type,
                "parser_version": PARSER_VERSION,
                "rule_set_version": RULE_SET_VERSION,
                "summary": empty_summary.to_dict(),
                "compliance_score": 0.0,
                "devices": [],
                "error_message": err_msg,
            }

        # Fetch active baseline rules from the repository
        active_rules = rule_repo.list_all(active_only=True)
        if not active_rules:
            active_rules = list(INITIAL_RULES)

        devices_output: List[Dict[str, Any]] = []

        # Process each uploaded configuration file
        for idx, file_item in enumerate(uploaded_files):
            filename, content, extraction_err = _extract_file_data(file_item, idx)
            line_count = len(content.splitlines()) if content else 0

            parse_error: Optional[str] = None
            normalized_config: Optional[NormalizedConfig] = None

            if extraction_err:
                parse_error = extraction_err
                normalized_config = NormalizedConfig(
                    vendor="Cisco",
                    device_type=device_type,
                    errors=[extraction_err],
                )
            else:
                try:
                    parser = CiscoLikeParser()
                    normalized_config = parser.parse(content)
                except Exception as exc:
                    parse_error = f"Parser error: {exc}"
                    normalized_config = NormalizedConfig(
                        vendor="Cisco",
                        device_type=device_type,
                        errors=[parse_error],
                    )

            # Determine device attributes and parse status
            dev_name = (
                normalized_config.device_name
                or filename.rsplit(".", 1)[0]
                or f"device-{idx + 1}"
            )
            display_name = dev_name
            vendor = normalized_config.vendor or "Cisco"

            has_errors = bool(normalized_config.errors or parse_error)
            has_data = bool(
                normalized_config.settings
                or normalized_config.management
                or normalized_config.device_name
            )

            if parse_error or (has_errors and not has_data):
                parse_status = "failed"
            elif has_errors and has_data:
                parse_status = "partial"
            else:
                parse_status = "success"

            error_msg_parts = list(normalized_config.errors)
            if parse_error and parse_error not in error_msg_parts:
                error_msg_parts.append(parse_error)
            error_message = "; ".join(error_msg_parts) if error_msg_parts else None

            device_id = str(uuid.uuid4())
            device = Device(
                id=device_id,
                scan_id=scan_id,
                name=dev_name,
                display_name=display_name,
                vendor=vendor,
                device_type=device_type,
                source_filename=filename,
                parse_status=parse_status,
                line_count=line_count,
                error_message=error_message,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            device_repo.create(device)

            # Deterministic rule evaluation
            if parse_status == "failed":
                rule_results = [
                    RuleResult(
                        id=str(uuid.uuid4()),
                        device_id=device_id,
                        scan_id=scan_id,
                        rule_id=rule.rule_id,
                        status="error",
                        severity=rule.severity,
                        evidence="",
                        evidence_line_range=None,
                        message=f"Rule evaluation aborted due to device parse error: {error_message}",
                        remediation=rule.remediation,
                        evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
                        engine_version=PARSER_VERSION,
                        error_message=error_message,
                    )
                    for rule in active_rules
                ]
            else:
                rule_results = evaluate_all(
                    config=normalized_config,
                    rules=active_rules,
                    device_id=device_id,
                    scan_id=scan_id,
                )

            # Persist RuleResults using repository batch insert
            result_repo.create_batch(rule_results)

            # Compute and persist device summary
            device_summary = result_repo.get_device_summary(device_id)
            device_repo.update_summary(device_id, device_summary)

            # Format device results adhering to standard contract
            formatted_results = [
                {
                    "rule_id": r.rule_id,
                    "status": r.status,
                    "severity": r.severity,
                    "evidence": r.evidence,
                    "evidence_line_range": r.evidence_line_range,
                    "message": r.message,
                    "remediation": r.remediation,
                }
                for r in rule_results
            ]

            devices_output.append(
                {
                    "device_id": device.id,
                    "name": device.name,
                    "display_name": device.display_name,
                    "vendor": device.vendor,
                    "device_type": device.device_type,
                    "source_filename": device.source_filename,
                    "parse_status": device.parse_status,
                    "line_count": device.line_count,
                    "error_message": device.error_message,
                    "summary": device_summary.to_dict(),
                    "compliance_score": device_summary.tested_rule_compliance,
                    "results": formatted_results,
                }
            )

        # Aggregate scan summary across all devices (pass/fail totals across all rules)
        scan_summary = result_repo.get_scan_summary(scan_id)
        scan_repo.update_summary(scan_id, scan_summary)
        completed_at = datetime.now(timezone.utc).isoformat()
        scan_repo.update_status(scan_id, status="completed", completed_at=completed_at)

        return {
            "scan_id": scan_id,
            "status": "completed",
            "device_type": device_type,
            "parser_version": PARSER_VERSION,
            "rule_set_version": RULE_SET_VERSION,
            "summary": scan_summary.to_dict(),
            "compliance_score": scan_summary.tested_rule_compliance,
            "devices": devices_output,
        }

    except Exception as exc:
        try:
            scan_repo.update_status(
                scan_id,
                status="failed",
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception:
            pass
        return {
            "scan_id": scan_id,
            "status": "failed",
            "device_type": device_type,
            "parser_version": PARSER_VERSION,
            "rule_set_version": RULE_SET_VERSION,
            "summary": ComplianceSummary().to_dict(),
            "compliance_score": 0.0,
            "devices": [],
            "error_message": f"Scan execution failed: {exc}",
        }
    finally:
        if own_conn and conn is not None:
            conn.close()
