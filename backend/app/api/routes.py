"""Flask API routes for Phoenix Protocol."""

from typing import Any, Dict, List
import uuid
from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from app.database.connection import get_connection
from app.database.repositories import get_full_scan_dict
from app.services.scanner import SUPPORTED_DEVICE_TYPES, run_scan

api_bp = Blueprint("api", __name__)

MAX_SINGLE_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file limit


@api_bp.route("/health", methods=["GET"])
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
    """Upload network configuration files and run compliance scan.

    Accepts multipart/form-data with one or more files in 'file' or 'files' fields.
    Optionally accepts 'device_type' (defaults to 'cisco_ios').
    """
    # 1. Validate device type
    device_type = request.form.get("device_type", "cisco_ios").strip()
    device_type_norm = device_type.lower()
    if device_type_norm not in SUPPORTED_DEVICE_TYPES:
        return (
            jsonify(
                {
                    "error": "Unsupported device type",
                    "detail": f"Device type '{device_type}' is not supported. Supported: {sorted(SUPPORTED_DEVICE_TYPES)}.",
                }
            ),
            400,
        )

    # 2. Collect all uploaded file items from request.files
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
                    "detail": "No files provided in upload request. Please provide at least one configuration file.",
                }
            ),
            400,
        )

    # 3. Read, validate, and safely decode uploaded configuration files
    processed_files: List[Dict[str, Any]] = []
    for f in uploaded_items:
        safe_filename = secure_filename(f.filename) or "device.cfg"
        raw_bytes = f.read()

        # Reject empty files
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

        # Enforce per-file size limit
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

        # Safely decode text
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

    # 4. Generate scan ID and execute scan via authoritative Track 2 scanner
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

    # 5. Return standardized Track 2 contract response
    if scan_result.get("status") == "failed":
        return jsonify(scan_result), 422

    return jsonify(scan_result), 201


@api_bp.route("/scans/<scan_id>", methods=["GET"])
def get_scan(scan_id: str):
    """Retrieve scan results by scan ID."""
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
