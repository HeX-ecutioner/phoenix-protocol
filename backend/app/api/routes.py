"""Flask API routes for Phoenix Protocol.

Provides both the authoritative /api/... REST contract for the frontend
and backward-compatible legacy routes (/health, /scan, /scans/<scan_id>).
"""

import csv
from datetime import datetime, timezone
import io
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
from flask import Blueprint, Response, current_app, jsonify, make_response, request
from werkzeug.utils import secure_filename

from app.database.connection import get_connection
from app.database.repositories import (
    DeviceRepository,
    RuleRepository,
    RuleResultRepository,
    ScanRepository,
    get_full_scan_dict,
)
from app.rules.definitions import INITIAL_RULES, RULES_BY_ID
from app.security.sanitization import sanitize_evidence
from app.services.scanner import (
    DEFAULT_DEVICE_TYPE,
    PARSER_VERSION,
    RULE_SET_VERSION,
    SUPPORTED_DEVICE_TYPES,
    run_scan,
)

api_bp = Blueprint("api", __name__)

MAX_SINGLE_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file limit

DEFAULT_ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}


# ============================================================================
# Helpers & Envelope Utilities
# ============================================================================


def _generate_request_id() -> str:
    """Generate a clean trace request ID."""
    return f"req-{uuid.uuid4().hex[:12]}"


def api_envelope(
    data: Any, status_code: int = 200, request_id: Optional[str] = None
) -> Tuple[Response, int]:
    """Return a standard success envelope matching frontend expectations."""
    req_id = request_id or _generate_request_id()
    return (
        jsonify(
            {
                "data": data,
                "error": None,
                "request_id": req_id,
            }
        ),
        status_code,
    )


def api_error(
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[List[Any]] = None,
    request_id: Optional[str] = None,
) -> Tuple[Response, int]:
    """Return a standard error envelope matching frontend expectations."""
    req_id = request_id or _generate_request_id()
    return (
        jsonify(
            {
                "data": None,
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or [],
                },
                "request_id": req_id,
            }
        ),
        status_code,
    )


def _get_allowed_origins() -> set:
    """Retrieve allowed CORS origins from app config or environment."""
    configured = current_app.config.get("CORS_ALLOWED_ORIGINS")
    if not configured:
        env_val = os.environ.get("CORS_ALLOWED_ORIGINS")
        if env_val:
            configured = [o.strip() for o in env_val.split(",") if o.strip()]
    if configured:
        return set(configured)
    return set(DEFAULT_ALLOWED_ORIGINS)


@api_bp.before_request
def handle_preflight():
    """Intercept and answer pre-flight CORS OPTIONS requests."""
    if request.method == "OPTIONS":
        response = make_response("", 204)
        origin = request.headers.get("Origin")
        allowed = _get_allowed_origins()
        if origin and ("*" in allowed or origin in allowed):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With"
            )
            response.headers["Access-Control-Max-Age"] = "86400"
        return response


@api_bp.after_request
def add_cors_headers(response: Response) -> Response:
    """Attach explicit CORS headers for authorized origins."""
    origin = request.headers.get("Origin")
    allowed = _get_allowed_origins()
    if origin and ("*" in allowed or origin in allowed):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With"
        )
        response.headers["Access-Control-Max-Age"] = "86400"
    return response


def _csv_escape(val: Any) -> str:
    """Sanitize string for CSV injection safety and string representation."""
    if val is None:
        return ""
    s = str(val)
    # Check for formula injection triggers: =, +, -, @, \t, \r
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


def _format_rule_result(r: Any) -> Dict[str, Any]:
    """Format a rule result with line references and title for frontend components."""
    rule_id = getattr(r, "rule_id", None) or (
        r.get("rule_id") if isinstance(r, dict) else None
    )
    status = getattr(r, "status", None) or (
        r.get("status") if isinstance(r, dict) else None
    )
    severity = getattr(r, "severity", None) or (
        r.get("severity") if isinstance(r, dict) else None
    )
    evidence = getattr(r, "evidence", None) or (
        r.get("evidence") if isinstance(r, dict) else ""
    )
    evidence_line_range = getattr(r, "evidence_line_range", None) or (
        r.get("evidence_line_range") if isinstance(r, dict) else None
    )
    message = getattr(r, "message", None) or (
        r.get("message") if isinstance(r, dict) else ""
    )
    remediation = getattr(r, "remediation", None) or (
        r.get("remediation") if isinstance(r, dict) else ""
    )
    timestamp = getattr(r, "evaluation_timestamp", None) or (
        r.get("evaluation_timestamp") if isinstance(r, dict) else None
    )
    engine_ver = getattr(r, "engine_version", None) or (
        r.get("engine_version") if isinstance(r, dict) else None
    )

    start_line = None
    end_line = None
    if evidence_line_range:
        if isinstance(evidence_line_range, (list, tuple)) and len(evidence_line_range) >= 2:
            start_line, end_line = evidence_line_range[0], evidence_line_range[1]
        elif isinstance(evidence_line_range, str):
            nums = re.findall(r"\d+", evidence_line_range)
            if len(nums) >= 2:
                start_line, end_line = int(nums[0]), int(nums[1])
            elif len(nums) == 1:
                start_line = end_line = int(nums[0])

    rule_meta = RULES_BY_ID.get(rule_id)
    title = rule_meta.title if rule_meta else (rule_id or "Compliance Rule")

    return {
        "rule_id": rule_id,
        "title": title,
        "status": status,
        "severity": severity,
        "evidence": evidence,
        "evidence_line_range": evidence_line_range,
        "evidence_start_line": start_line,
        "evidence_end_line": end_line,
        "message": message,
        "remediation": remediation,
        "evaluation_timestamp": timestamp,
        "evaluated_at": timestamp,
        "rule_version": rule_meta.rule_version if rule_meta else (engine_ver or "1.0.0"),
    }


def _enrich_device_summary(
    dev_summary_dict: Dict[str, Any], dev_results: List[Any]
) -> Dict[str, Any]:
    """Augment device summary dictionary with frontend metric keys."""
    high_failures = sum(
        1
        for r in dev_results
        if (
            (getattr(r, "status", None) == "fail" and getattr(r, "severity", None) == "high")
            or (
                isinstance(r, dict)
                and r.get("status") == "fail"
                and r.get("severity") == "high"
            )
        )
    )
    enriched = dict(dev_summary_dict)
    enriched.update(
        {
            "pass_count": dev_summary_dict.get("passed_rules", 0),
            "fail_count": dev_summary_dict.get("failed_rules", 0),
            "warning_count": dev_summary_dict.get("warning_rules", 0),
            "not_applicable_count": dev_summary_dict.get("not_applicable_rules", 0),
            "error_count": dev_summary_dict.get("error_rules", 0),
            "high_severity_failures": high_failures,
            "compliance_percentage": dev_summary_dict.get("tested_rule_compliance", 0.0),
        }
    )
    return enriched


def _enrich_scan_summary(
    scan_summary_dict: Dict[str, Any], device_count: int, all_results: List[Any]
) -> Dict[str, Any]:
    """Augment scan-level summary with frontend metric keys."""
    high_failures = sum(
        1
        for r in all_results
        if (
            (getattr(r, "status", None) == "fail" and getattr(r, "severity", None) == "high")
            or (
                isinstance(r, dict)
                and r.get("status") == "fail"
                and r.get("severity") == "high"
            )
        )
    )
    enriched = dict(scan_summary_dict)
    enriched.update(
        {
            "device_count": device_count,
            "total_rules_evaluated": scan_summary_dict.get("total_rules", 0),
            "pass_count": scan_summary_dict.get("passed_rules", 0),
            "fail_count": scan_summary_dict.get("failed_rules", 0),
            "warning_count": scan_summary_dict.get("warning_rules", 0),
            "not_applicable_count": scan_summary_dict.get("not_applicable_rules", 0),
            "error_count": scan_summary_dict.get("error_rules", 0),
            "high_severity_failures": high_failures,
            "compliance_percentage": scan_summary_dict.get("tested_rule_compliance", 0.0),
        }
    )
    return enriched


# ============================================================================
# 1. /api/device-types
# ============================================================================


@api_bp.route("/api/device-types", methods=["GET"])
def get_device_types():
    """Return supported device profiles based on actual backend capability."""
    return api_envelope(
        {
            "device_types": [
                {
                    "id": "cisco_ios",
                    "name": "Cisco IOS",
                    "vendor": "Cisco",
                    "supported": True,
                    "parser_version": PARSER_VERSION,
                }
            ]
        },
        200,
    )


# ============================================================================
# 2. /api/scans (POST)
# ============================================================================


@api_bp.route("/api/scans", methods=["POST"])
def api_upload_and_scan():
    """Upload network configuration files and run compliance scan via /api contract."""
    # 1. Validate device type
    raw_device_type = request.form.get("device_type", DEFAULT_DEVICE_TYPE).strip()
    device_type_norm = raw_device_type.lower()
    # Normalize common aliases
    if device_type_norm in ("cisco-like-router", "cisco-like", "cisco_like", "cisco"):
        device_type_norm = "cisco_ios"

    if device_type_norm not in SUPPORTED_DEVICE_TYPES:
        return api_error(
            "UNSUPPORTED_DEVICE_TYPE",
            f"Device type '{raw_device_type}' is not supported. Supported: ['cisco_ios'].",
            400,
        )

    # 2. Collect uploaded files
    uploaded_items = []
    for key in request.files:
        for f in request.files.getlist(key):
            if f and f.filename:
                uploaded_items.append(f)

    if not uploaded_items:
        return api_error(
            "MISSING_FILES",
            "No configuration files provided in upload request. Please provide at least one configuration file.",
            400,
        )

    # 3. Read, validate, and decode uploaded configuration files
    processed_files: List[Dict[str, Any]] = []
    for f in uploaded_items:
        safe_filename = secure_filename(f.filename) or "device.cfg"
        raw_bytes = f.read()

        if not raw_bytes or len(raw_bytes.strip()) == 0:
            return api_error(
                "EMPTY_FILE",
                f"Uploaded file '{safe_filename}' is empty.",
                400,
            )

        if len(raw_bytes) > MAX_SINGLE_FILE_SIZE:
            return api_error(
                "FILE_TOO_LARGE",
                f"Uploaded file '{safe_filename}' exceeds the 10 MB limit.",
                413,
            )

        try:
            content_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return api_error(
                "UNSUPPORTED_FILE_FORMAT",
                f"Uploaded file '{safe_filename}' cannot be decoded as UTF-8 text.",
                422,
            )

        processed_files.append(
            {
                "filename": safe_filename,
                "content": content_str,
            }
        )

    # 4. Execute scan via authoritative compliance engine
    scan_id = f"scan_{uuid.uuid4().hex}"
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path) if db_path else None

    try:
        scan_result = run_scan(
            scan_id=scan_id,
            device_type=device_type_norm,
            uploaded_files=processed_files,
            conn=conn,
        )
    finally:
        if conn is not None:
            conn.close()

    if scan_result.get("status") == "failed":
        return api_error(
            "SCAN_FAILED",
            "Scan processing failed on the provided configuration.",
            422,
            details=[scan_result],
        )

    # 5. Format payload with dual compatibility
    enriched_devices = []
    all_results = []
    for dev in scan_result.get("devices", []):
        dev_results = [_format_rule_result(r) for r in dev.get("results", [])]
        all_results.extend(dev_results)
        enriched_dev_summary = _enrich_device_summary(dev.get("summary", {}), dev_results)
        enriched_devices.append(
            {
                "id": dev["device_id"],
                "device_id": dev["device_id"],
                "scan_id": scan_id,
                "name": dev["name"],
                "display_name": dev.get("display_name")
                or dev.get("source_filename")
                or dev["name"],
                "vendor": dev["vendor"],
                "device_type": dev["device_type"],
                "source_filename": dev["source_filename"],
                "parse_status": dev["parse_status"],
                "line_count": dev["line_count"],
                "error_message": dev.get("error_message"),
                "summary": enriched_dev_summary,
                "compliance_score": dev.get("compliance_score", 0.0),
                "results": dev_results,
            }
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    enriched_scan_summary = _enrich_scan_summary(
        scan_result.get("summary", {}),
        len(enriched_devices),
        all_results,
    )

    scan_payload = {
        "id": scan_id,
        "scan_id": scan_id,
        "status": scan_result["status"],
        "device_type": scan_result["device_type"],
        "parser_version": scan_result["parser_version"],
        "rule_set_version": scan_result["rule_set_version"],
        "created_at": now_iso,
        "completed_at": now_iso,
        "summary": enriched_scan_summary,
        "compliance_score": scan_result["compliance_score"],
        "devices": enriched_devices,
    }

    data_payload = {
        "scan_id": scan_id,
        "id": scan_id,
        "scan": scan_payload,
        **scan_payload,
    }
    return api_envelope(data_payload, 201)


# ============================================================================
# 3. /api/scans/{scan_id} (GET)
# ============================================================================


@api_bp.route("/api/scans/<scan_id>", methods=["GET"])
def api_get_scan(scan_id: str):
    """Retrieve persisted scan results matching the frontend envelope contract."""
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path)
    try:
        scan_dict = get_full_scan_dict(conn, scan_id)
        scan_entity = ScanRepository(conn).get_by_id(scan_id)
    finally:
        conn.close()

    if scan_dict is None or scan_entity is None:
        return api_error(
            "SCAN_NOT_FOUND",
            f"No scan found with ID '{scan_id}'.",
            404,
        )

    enriched_devices = []
    all_results = []
    for dev in scan_dict.get("devices", []):
        dev_results = [_format_rule_result(r) for r in dev.get("results", [])]
        all_results.extend(dev_results)
        enriched_dev_summary = _enrich_device_summary(dev.get("summary", {}), dev_results)
        enriched_devices.append(
            {
                "id": dev["device_id"],
                "device_id": dev["device_id"],
                "scan_id": scan_id,
                "name": dev["name"],
                "display_name": dev.get("display_name")
                or dev.get("source_filename")
                or dev["name"],
                "vendor": dev["vendor"],
                "device_type": dev["device_type"],
                "source_filename": dev["source_filename"],
                "parse_status": dev["parse_status"],
                "line_count": dev["line_count"],
                "error_message": dev.get("error_message"),
                "summary": enriched_dev_summary,
                "compliance_score": dev.get("compliance_score", 0.0),
                "results": dev_results,
            }
        )

    enriched_scan_summary = _enrich_scan_summary(
        scan_dict.get("summary", {}),
        len(enriched_devices),
        all_results,
    )

    scan_payload = {
        "id": scan_entity.id,
        "scan_id": scan_entity.id,
        "status": scan_entity.status,
        "device_type": scan_entity.device_type,
        "parser_version": scan_entity.parser_version,
        "rule_set_version": scan_entity.rule_set_version,
        "created_at": scan_entity.created_at,
        "completed_at": scan_entity.completed_at or scan_entity.updated_at,
        "summary": enriched_scan_summary,
        "compliance_score": scan_dict.get("compliance_score", 0.0),
        "devices": enriched_devices,
    }

    data_payload = {
        "scan_id": scan_entity.id,
        "id": scan_entity.id,
        "scan": scan_payload,
        **scan_payload,
    }
    return api_envelope(data_payload, 200)


# ============================================================================
# 4. /api/scans/{scan_id}/devices (GET)
# ============================================================================


@api_bp.route("/api/scans/<scan_id>/devices", methods=["GET"])
def api_get_scan_devices(scan_id: str):
    """Return the list of devices belonging to a scan."""
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path)
    try:
        scan_entity = ScanRepository(conn).get_by_id(scan_id)
        if scan_entity is None:
            return api_error(
                "SCAN_NOT_FOUND",
                f"No scan found with ID '{scan_id}'.",
                404,
            )

        devices = DeviceRepository(conn).list_by_scan_id(scan_id)
        res_repo = RuleResultRepository(conn)

        devices_list = []
        for dev in devices:
            dev_results = res_repo.list_by_device_id(dev.id)
            dev_summary = res_repo.get_device_summary(dev.id)
            enriched_sum = _enrich_device_summary(dev_summary.to_dict(), dev_results)
            devices_list.append(
                {
                    "id": dev.id,
                    "device_id": dev.id,
                    "scan_id": dev.scan_id,
                    "name": dev.name,
                    "display_name": dev.display_name or dev.source_filename or dev.name,
                    "vendor": dev.vendor,
                    "device_type": dev.device_type,
                    "source_filename": dev.source_filename,
                    "parse_status": dev.parse_status,
                    "line_count": dev.line_count,
                    "error_message": dev.error_message,
                    "compliance_score": dev_summary.tested_rule_compliance,
                    "summary": enriched_sum,
                }
            )
    finally:
        conn.close()

    return api_envelope(
        {
            "scan_id": scan_id,
            "devices": devices_list,
        },
        200,
    )


# ============================================================================
# 5. /api/scans/{scan_id}/devices/{device_id} (GET)
# ============================================================================


@api_bp.route("/api/scans/<scan_id>/devices/<device_id>", methods=["GET"])
def api_get_scan_device_detail(scan_id: str, device_id: str):
    """Return the complete persisted device-level audit result."""
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path)
    try:
        scan_entity = ScanRepository(conn).get_by_id(scan_id)
        if scan_entity is None:
            return api_error(
                "SCAN_NOT_FOUND",
                f"No scan found with ID '{scan_id}'.",
                404,
            )

        dev_repo = DeviceRepository(conn)
        device = dev_repo.get_by_id(device_id)
        if device is None:
            return api_error(
                "DEVICE_NOT_FOUND",
                f"No device found with ID '{device_id}'.",
                404,
            )

        # Verify device actually belongs to this scan
        if device.scan_id != scan_id:
            return api_error(
                "DEVICE_SCAN_MISMATCH",
                f"Device '{device_id}' does not belong to scan '{scan_id}'.",
                404,
            )

        res_repo = RuleResultRepository(conn)
        results = res_repo.list_by_device_id(device_id)
        dev_summary = res_repo.get_device_summary(device_id)
        formatted_results = [_format_rule_result(r) for r in results]
        enriched_sum = _enrich_device_summary(dev_summary.to_dict(), results)

        device_payload = {
            "id": device.id,
            "device_id": device.id,
            "scan_id": device.scan_id,
            "name": device.name,
            "display_name": device.display_name or device.source_filename or device.name,
            "vendor": device.vendor,
            "device_type": device.device_type,
            "source_filename": device.source_filename,
            "parse_status": device.parse_status,
            "line_count": device.line_count,
            "error_message": device.error_message,
            "summary": enriched_sum,
            "compliance_score": dev_summary.tested_rule_compliance,
            "results": formatted_results,
        }
    finally:
        conn.close()

    # Deliver both nested under 'device' and top-level for maximum frontend component compatibility
    return api_envelope(
        {
            "device": device_payload,
            **device_payload,
        },
        200,
    )


# ============================================================================
# 6. /api/rules (GET)
# ============================================================================


@api_bp.route("/api/rules", methods=["GET"])
def api_get_rules():
    """Return the authoritative rule catalog from definitions / database."""
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path) if db_path else None
    try:
        if conn is not None:
            rules = RuleRepository(conn).list_all()
        else:
            rules = INITIAL_RULES
    finally:
        if conn is not None:
            conn.close()

    if not rules:
        rules = INITIAL_RULES

    rule_list = []
    for r in rules:
        rule_list.append(
            {
                "id": r.rule_id,
                "rule_id": r.rule_id,
                "name": r.title,
                "title": r.title,
                "description": r.description,
                "technical_requirement": r.technical_requirement,
                "severity": r.severity,
                "device_type": r.device_type,
                "category": r.category,
                "remediation": r.remediation,
                "is_active": r.active,
                "active": r.active,
                "rule_version": r.rule_version,
            }
        )

    return api_envelope({"rules": rule_list}, 200)


# ============================================================================
# 7. /api/rules/{rule_id} (GET)
# ============================================================================


@api_bp.route("/api/rules/<rule_id>", methods=["GET"])
def api_get_rule(rule_id: str):
    """Return detailed metadata for one rule."""
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path) if db_path else None
    rule = None
    try:
        if conn is not None:
            rule = RuleRepository(conn).get_by_id(rule_id)
    finally:
        if conn is not None:
            conn.close()

    if rule is None:
        rule = RULES_BY_ID.get(rule_id)

    if rule is None:
        return api_error(
            "RULE_NOT_FOUND",
            f"Rule with ID '{rule_id}' not found.",
            404,
        )

    rule_dict = {
        "id": rule.rule_id,
        "rule_id": rule.rule_id,
        "name": rule.title,
        "title": rule.title,
        "description": rule.description,
        "technical_requirement": rule.technical_requirement,
        "severity": rule.severity,
        "device_type": rule.device_type,
        "category": rule.category,
        "remediation": rule.remediation,
        "is_active": rule.active,
        "active": rule.active,
        "rule_version": rule.rule_version,
    }
    return api_envelope(rule_dict, 200)


# ============================================================================
# 8. /api/scans/{scan_id}/report.csv (GET)
# ============================================================================


@api_bp.route("/api/scans/<scan_id>/report.csv", methods=["GET"])
def api_get_scan_report_csv(scan_id: str):
    """Generate and download a deterministic CSV compliance report."""
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path)
    try:
        scan_entity = ScanRepository(conn).get_by_id(scan_id)
        if scan_entity is None:
            return api_error(
                "SCAN_NOT_FOUND",
                f"No scan found with ID '{scan_id}'.",
                404,
            )

        devices = DeviceRepository(conn).list_by_scan_id(scan_id)
        dev_map = {d.id: d for d in devices}
        results = RuleResultRepository(conn).list_by_scan_id(scan_id)

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            [
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
        )

        for r in results:
            dev = dev_map.get(r.device_id)
            dev_name = dev.display_name if dev else r.device_id
            vendor = dev.vendor if dev else "Cisco"
            dtype = dev.device_type if dev else "cisco_ios"

            clean_evidence = sanitize_evidence(r.evidence or "")
            line_range_str = (
                str(r.evidence_line_range) if r.evidence_line_range is not None else ""
            )

            writer.writerow(
                [
                    _csv_escape(scan_id),
                    _csv_escape(r.device_id),
                    _csv_escape(dev_name),
                    _csv_escape(vendor),
                    _csv_escape(dtype),
                    _csv_escape(r.rule_id),
                    _csv_escape(r.status),
                    _csv_escape(r.severity),
                    _csv_escape(clean_evidence),
                    _csv_escape(line_range_str),
                    _csv_escape(r.message),
                    _csv_escape(r.remediation),
                ]
            )

        csv_content = output.getvalue().encode("utf-8")
    finally:
        conn.close()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": f'attachment; filename="scan_{scan_id}_report.csv"',
        },
        status=200,
    )


# ============================================================================
# Legacy Compatibility Endpoints (/health, /scan, /scans/<scan_id>)
# ============================================================================


@api_bp.route("/health", methods=["GET"])
@api_bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "phoenix-protocol",
                "version": "1.0.0",
            }
        ),
        200,
    )


@api_bp.route("/scan", methods=["POST"])
def upload_and_scan():
    """Upload network configuration files and run compliance scan (Legacy route).

    Accepts multipart/form-data with one or more files in 'file' or 'files' fields.
    Optionally accepts 'device_type' (defaults to 'cisco_ios').
    """
    device_type = request.form.get("device_type", "cisco_ios").strip()
    device_type_norm = device_type.lower()
    if device_type_norm not in SUPPORTED_DEVICE_TYPES:
        return (
            jsonify(
                {
                    "error": "Unsupported device type",
                    "detail": (
                        f"Device type '{device_type}' is not supported. "
                        f"Supported: {sorted(SUPPORTED_DEVICE_TYPES)}."
                    ),
                }
            ),
            400,
        )

    uploaded_items = []
    for key in request.files:
        for f in request.files.getlist(key):
            if f and f.filename:
                uploaded_items.append(f)

    if not uploaded_items:
        return (
            jsonify(
                {
                    "error": "Missing configuration files",
                    "detail": (
                        "No files provided in upload request. "
                        "Please provide at least one configuration file."
                    ),
                }
            ),
            400,
        )

    processed_files: List[Dict[str, Any]] = []
    for f in uploaded_items:
        safe_filename = secure_filename(f.filename) or "device.cfg"
        raw_bytes = f.read()

        if not raw_bytes or len(raw_bytes.strip()) == 0:
            return (
                jsonify(
                    {
                        "error": "Empty configuration file",
                        "detail": f"Uploaded file '{safe_filename}' is empty.",
                    }
                ),
                400,
            )

        if len(raw_bytes) > MAX_SINGLE_FILE_SIZE:
            return (
                jsonify(
                    {
                        "error": "File too large",
                        "detail": f"Uploaded file '{safe_filename}' exceeds the 10 MB limit.",
                    }
                ),
                413,
            )

        try:
            content_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return (
                jsonify(
                    {
                        "error": "Unsupported file format",
                        "detail": f"Uploaded file '{safe_filename}' cannot be decoded as UTF-8 text.",
                    }
                ),
                422,
            )

        processed_files.append(
            {
                "filename": safe_filename,
                "content": content_str,
            }
        )

    scan_id = f"scan_{uuid.uuid4().hex}"
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path) if db_path else None

    try:
        scan_result = run_scan(
            scan_id=scan_id,
            device_type=device_type_norm,
            uploaded_files=processed_files,
            conn=conn,
        )
    finally:
        if conn is not None:
            conn.close()

    if scan_result.get("status") == "failed":
        return jsonify(scan_result), 422

    return jsonify(scan_result), 201


@api_bp.route("/scans/<scan_id>", methods=["GET"])
def get_scan(scan_id: str):
    """Retrieve scan results by scan ID (Legacy route)."""
    db_path = current_app.config.get("DATABASE_PATH")
    conn = get_connection(db_path)
    try:
        scan_dict = get_full_scan_dict(conn, scan_id)
    finally:
        conn.close()

    if scan_dict is None:
        return (
            jsonify(
                {
                    "error": "Scan not found",
                    "detail": f"No scan found with ID '{scan_id}'.",
                    "scan_id": scan_id,
                }
            ),
            404,
        )

    return jsonify(scan_dict), 200
