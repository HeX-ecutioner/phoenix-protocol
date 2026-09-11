"""Automated verification tests for expanded sample_data QA fixtures."""

import pathlib
import uuid

from app.parsers.cisco_like import parse_cisco_like
from app.services.scanner import run_scan

FIXTURES_DIR = pathlib.Path(__file__).resolve().parent.parent / "sample_data"


def test_garbage_fixture_does_not_crash_parser_or_service() -> None:
    """Garbage non-network input does not crash the parser or scanner."""
    garbage_path = FIXTURES_DIR / "edge_cases" / "garbage.txt"
    content = garbage_path.read_text(encoding="utf-8")

    cfg = parse_cisco_like(content)
    assert cfg.device_name is None
    assert "Missing hostname statement in configuration" in cfg.warnings
    assert len(cfg.errors) == 0

    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "garbage.txt", "content": content}],
    )
    assert res["status"] == "completed"
    dev = res["devices"][0]
    assert dev["parse_status"] == "success"
    assert res["summary"]["total_rules"] == 10
    # NET-010 passes (no plaintext found), 5 rules fail, 4 warn
    assert res["summary"]["passed_rules"] == 1
    assert res["summary"]["failed_rules"] == 5
    assert res["summary"]["warning_rules"] == 4


def test_empty_fixture_handled_safely() -> None:
    """Empty configuration file is safely flagged without raising exceptions."""
    empty_path = FIXTURES_DIR / "edge_cases" / "empty.txt"
    content = empty_path.read_text(encoding="utf-8")

    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "empty.txt", "content": content}],
    )
    assert res["status"] == "completed"
    dev = res["devices"][0]
    assert dev["parse_status"] == "failed"
    assert "Configuration input is empty" in dev["error_message"]
    assert res["summary"]["error_rules"] == 10
    assert res["summary"]["tested_rule_compliance"] == 0.0


def test_multiple_vty_blocks_preserved_and_evaluated() -> None:
    """Scoped multi-range VTY blocks (0-4 and 5-15) are kept separate and not flattened."""
    vty_path = FIXTURES_DIR / "edge_cases" / "multiple_vty_blocks.txt"
    content = vty_path.read_text(encoding="utf-8")

    cfg = parse_cisco_like(content)
    vty_blocks = cfg.management["vty"]
    assert len(vty_blocks) == 2
    assert vty_blocks[0]["range"] == "0 4"
    assert vty_blocks[1]["range"] == "5 15"
    assert vty_blocks[0]["ssh_only"] is True
    assert vty_blocks[1]["ssh_only"] is True

    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "multiple_vty_blocks.txt", "content": content}],
    )
    assert res["status"] == "completed"
    assert res["summary"]["passed_rules"] == 10
    assert res["summary"]["tested_rule_compliance"] == 100.0


def test_partial_vty_failure_detected() -> None:
    """When one VTY block is secure and another is insecure, overall evaluation fails."""
    split_path = FIXTURES_DIR / "edge_cases" / "partial_vty_failure.txt"
    content = split_path.read_text(encoding="utf-8")

    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "partial_vty_failure.txt", "content": content}],
    )
    assert res["status"] == "completed"
    dev = res["devices"][0]
    rules_by_id = {r["rule_id"]: r for r in dev["results"]}

    # NET-001 and NET-007 should fail due to insecure block 5-15
    assert rules_by_id["NET-001"]["status"] == "fail"
    assert "line vty 5 15" in rules_by_id["NET-001"]["message"]
    assert rules_by_id["NET-007"]["status"] == "fail"
    assert "line vty 5 15" in rules_by_id["NET-007"]["message"]
    assert res["summary"]["failed_rules"] == 2
    assert res["summary"]["passed_rules"] == 8
    assert res["summary"]["tested_rule_compliance"] == 80.0


def test_malformed_banner_handled_safely() -> None:
    """Unclosed delimiter banner at EOF produces parser error safely without crashing."""
    malformed_path = FIXTURES_DIR / "edge_cases" / "malformed_banner.txt"
    content = malformed_path.read_text(encoding="utf-8")

    cfg = parse_cisco_like(content)
    assert any("Unclosed banner motd delimiter" in err for err in cfg.errors)

    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "malformed_banner.txt", "content": content}],
    )
    assert res["status"] == "completed"
    dev = res["devices"][0]
    assert dev["parse_status"] == "partial"


def test_tacacs_and_radius_secrets_are_redacted() -> None:
    """TACACS and RADIUS pre-shared keys are sanitized with [REDACTED]."""
    secrets_path = FIXTURES_DIR / "security" / "tacacs_radius_secrets.txt"
    content = secrets_path.read_text(encoding="utf-8")

    cfg = parse_cisco_like(content)
    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "tacacs_radius_secrets.txt", "content": content}],
    )
    assert res["status"] == "completed"

    # Verify that raw secret strings never appear in scan dictionary
    res_str = str(res)
    for raw_secret in (
        "DEMO_TACACS_SHARED_KEY",
        "DEMO_TACACS_ZERO_KEY",
        "DEMO_HOST_TACACS_KEY",
        "DEMO_RADIUS_SHARED_KEY",
        "DEMO_RADIUS_ZERO_KEY",
        "DEMO_HOST_RADIUS_KEY",
    ):
        assert raw_secret not in res_str
        assert raw_secret not in str(cfg.evidence_map)


def test_plaintext_credentials_are_redacted() -> None:
    """Plaintext user, enable, and line passwords are never leaked verbatim."""
    plain_path = FIXTURES_DIR / "security" / "plaintext_credentials.txt"
    content = plain_path.read_text(encoding="utf-8")

    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "plaintext_credentials.txt", "content": content}],
    )
    assert res["status"] == "completed"
    res_str = str(res)

    for secret in (
        "DEMO_ADMIN_PASSWORD_999",
        "DEMO_OPERATOR_PASSWORD_888",
        "DEMO_ENABLE_PASSWORD_PLAIN",
        "DEMO_CONSOLE_PASSWORD",
        "DEMO_VTY_PASSWORD",
    ):
        assert secret not in res_str


def test_insecure_services_enabled_and_disabled() -> None:
    """Explicit insecure services trigger NET-008 failure, explicit disables trigger pass."""
    en_path = FIXTURES_DIR / "services" / "insecure_services_enabled.txt"
    dis_path = FIXTURES_DIR / "services" / "insecure_services_disabled.txt"

    en_res = run_scan(
        scan_id=str(uuid.uuid4()),
        device_type="cisco_ios",
        uploaded_files=[{"filename": "insecure_services_enabled.txt", "content": en_path.read_text(encoding="utf-8")}],
    )
    en_rules = {r["rule_id"]: r for r in en_res["devices"][0]["results"]}
    assert en_rules["NET-008"]["status"] == "fail"

    dis_res = run_scan(
        scan_id=str(uuid.uuid4()),
        device_type="cisco_ios",
        uploaded_files=[{"filename": "insecure_services_disabled.txt", "content": dis_path.read_text(encoding="utf-8")}],
    )
    dis_rules = {r["rule_id"]: r for r in dis_res["devices"][0]["results"]}
    assert dis_rules["NET-008"]["status"] == "pass"


def test_multi_device_secondary_and_aggregate_scoring() -> None:
    """Uploading compliant, failing, and secondary routers computes accurate device and scan scores."""
    comp_path = FIXTURES_DIR / "compliant_router.txt"
    fail_path = FIXTURES_DIR / "failing_router.txt"
    sec_path = FIXTURES_DIR / "scenarios" / "multi_device_secondary.txt"

    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[
            {"filename": "compliant.txt", "content": comp_path.read_text(encoding="utf-8")},
            {"filename": "failing.txt", "content": fail_path.read_text(encoding="utf-8")},
            {"filename": "secondary.txt", "content": sec_path.read_text(encoding="utf-8")},
        ],
    )
    assert res["status"] == "completed"
    assert len(res["devices"]) == 3

    dev_by_name = {d["name"]: d for d in res["devices"]}
    assert "CORE-RTR-01" in dev_by_name
    assert "DEFAULT-RTR" in dev_by_name
    assert "BRANCH-RTR-02" in dev_by_name

    assert dev_by_name["CORE-RTR-01"]["compliance_score"] == 100.0
    assert dev_by_name["DEFAULT-RTR"]["compliance_score"] == 0.0
    assert dev_by_name["BRANCH-RTR-02"]["compliance_score"] == 70.0

    # Aggregate: (10 + 0 + 7) / (10 + 10 + 10) * 100 = 17 / 30 * 100 = 56.67%
    assert res["summary"]["passed_rules"] == 17
    assert res["summary"]["failed_rules"] == 13
    assert res["summary"]["tested_rule_compliance"] == 56.67


def test_remediation_demo_produces_all_remediations() -> None:
    """Remediation demo fixture triggers all 10 rule failures with distinct actionable remediations."""
    remed_path = FIXTURES_DIR / "scenarios" / "remediation_demo.txt"
    content = remed_path.read_text(encoding="utf-8")

    scan_id = str(uuid.uuid4())
    res = run_scan(
        scan_id=scan_id,
        device_type="cisco_ios",
        uploaded_files=[{"filename": "remediation_demo.txt", "content": content}],
    )
    assert res["status"] == "completed"
    assert res["summary"]["failed_rules"] == 10
    assert res["summary"]["tested_rule_compliance"] == 0.0

    for rule in res["devices"][0]["results"]:
        assert rule["status"] == "fail"
        assert rule["remediation"] is not None
        assert len(rule["remediation"].strip()) > 0
