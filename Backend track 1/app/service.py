import uuid
from datetime import datetime, timezone

from app.models import (
    ParserInfo,
    ScanRequest,
    ScanResult,
    ScanSummary,
    SourceInfo,
    Status,
    Diagnostic,
)
from app.parser import GenericKeyValueParser, ParserException
from app.repository import ScanRepository
from app.rules import evaluate_all


def _calculate_summary(results, warning_count: int) -> ScanSummary:
    total_rules = len(results)
    compliant = sum(1 for r in results if r.status == Status.COMPLIANT)
    failing = sum(1 for r in results if r.status == Status.FAILING)
    ambiguous = sum(1 for r in results if r.status == Status.AMBIGUOUS)
    not_applicable = sum(1 for r in results if r.status == Status.NOT_APPLICABLE)
    error = sum(1 for r in results if r.status == Status.ERROR)

    tested_rules = compliant + failing + ambiguous

    if tested_rules > 0:
        compliance_percent = (compliant / tested_rules) * 100
    else:
        compliance_percent = None

    return ScanSummary(
        total_rules=total_rules,
        tested_rules=tested_rules,
        compliant=compliant,
        failing=failing,
        ambiguous=ambiguous,
        not_applicable=not_applicable,
        error=error,
        warning_count=warning_count,
        compliance_percent=compliance_percent,
        compliance_basis="tested_rules",
    )


def run_scan(request: ScanRequest, db: ScanRepository) -> ScanResult:
    scan_id = f"scan_{uuid.uuid4().hex}"
    created_at = datetime.now(timezone.utc).isoformat()

    source = SourceInfo(
        original_filename=request.upload.original_filename,
        sha256=request.upload.sha256,
        size_bytes=request.upload.size_bytes,
        format=request.upload.format_hint or "generic-kv",
    )

    parser_info = ParserInfo(
        parser_id=GenericKeyValueParser.PARSER_ID,
        parser_version=GenericKeyValueParser.PARSER_VERSION,
        normalized_setting_count=0,
    )

    db.create_scan(scan_id, created_at, "processing", source, parser_info)

    parser = GenericKeyValueParser()

    try:
        settings, parser_diagnostics = parser.parse(request.upload.content)

        parser_info = ParserInfo(
            parser_id=parser.PARSER_ID,
            parser_version=parser.PARSER_VERSION,
            normalized_setting_count=len(settings),
        )

        db.save_normalized_settings(scan_id, settings)
        db.save_diagnostics(scan_id, parser_diagnostics)

        settings_map = {s.key: s for s in settings}

        results = evaluate_all(settings_map)

        db.save_rule_results(scan_id, results)

        warning_count = sum(1 for d in parser_diagnostics if d.severity == "warning")
        summary = _calculate_summary(results, warning_count)
        scan_status = "completed" if summary.error == 0 else "error"

        db.save_summary(scan_id, summary, scan_status)
        db.conn.commit()

    except ParserException as e:
        db.conn.rollback()

        scan_status = "failed"
        db.create_scan(scan_id, created_at, scan_status, source, parser_info)

        error_diag = Diagnostic(
            code=str(e),
            message="Unrecoverable parser error",
            severity="error",
            source_line_start=None,
            source_line_end=None,
            field=None,
        )
        db.save_diagnostics(scan_id, [error_diag])

        summary = _calculate_summary([], 0)
        db.save_summary(scan_id, summary, scan_status)
        db.conn.commit()

    except Exception as e:
        db.conn.rollback()
        raise e

    final_result = db.get_scan(scan_id)
    if not final_result:
        raise RuntimeError("Failed to retrieve saved scan from database")

    return final_result
