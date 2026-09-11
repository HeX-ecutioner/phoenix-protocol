"""Tests for domain models and compliance scoring logic."""

import pytest

from app.models.device import Device
from app.models.normalized_config import ConfigEvidence, NormalizedConfig
from app.models.rule import Rule
from app.models.rule_result import ALLOWED_SEVERITIES, ALLOWED_STATUSES, RuleResult
from app.models.scan import Scan
from app.services.compliance import (
    ComplianceSummary,
    calculate_compliance_score,
    calculate_device_summary,
    calculate_scan_summary,
    calculate_summary,
)


def test_config_evidence_fields_and_aliases():
    """Verify ConfigEvidence safely represents line ranges, fields, and aliases."""
    ev = ConfigEvidence(
        field_name="line_vty_transport",
        evidence_text="transport input ssh",
        line_number=42,
    )
    assert ev.field_name == "line_vty_transport"
    assert ev.evidence_text == "transport input ssh"
    assert ev.content == "transport input ssh"
    assert ev.line_range == "42"

    ev2 = ConfigEvidence(
        field_name="motd",
        content="banner motd Authorized Only",
        line_range="10-12",
    )
    assert ev2.evidence_text == "banner motd Authorized Only"
    assert ev2.line_range == "10-12"


def test_normalized_config_fields():
    """Verify NormalizedConfig supports required fields and hierarchical management."""
    ev = ConfigEvidence(field_name="ssh", evidence_text="ip ssh version 2", line_number=15)
    config = NormalizedConfig(
        device_name="CORE-RTR-01",
        vendor="Cisco",
        device_type="cisco_ios",
        platform="c7200",
        version="15.7",
        settings={"ssh_version": 2, "password_encryption": True},
        management={
            "vty": {"0-4": {"transport_input": "ssh", "access_class": "10"}},
            "console": {"0": {"exec_timeout": "10 0"}},
        },
        evidence_map={"ssh": ev},
        warnings=["Ambiguous NTP peer statement"],
        errors=[],
    )

    assert config.device_name == "CORE-RTR-01"
    assert config.vendor == "Cisco"
    assert config.device_type == "cisco_ios"
    assert config.management["vty"]["0-4"]["transport_input"] == "ssh"
    assert "ssh" in config.evidence_map
    assert config.warnings[0] == "Ambiguous NTP peer statement"
    assert config.errors == []


def test_rule_model_validation_and_fields():
    """Verify Rule model validates severity and synchronizes aliases."""
    rule = Rule(
        rule_id="NET-001",
        title="Telnet Disabled",
        description="Telnet must be disabled",
        technical_requirement="transport input ssh required",
        severity="high",
        device_type="cisco_ios",
        remediation="line vty 0 4\n transport input ssh",
    )
    assert rule.rule_id == "NET-001"
    assert rule.id == "NET-001"
    assert rule.remediation == rule.remediation_template
    assert rule.active is True
    assert rule["rule_id"] == "NET-001"

    # Invalid severity should raise ValueError
    with pytest.raises(ValueError, match="Invalid severity"):
        Rule(
            rule_id="NET-BAD",
            title="Bad Rule",
            description="desc",
            severity="critical",  # Not in high, medium, low
        )


def test_rule_result_model_validation_and_contract():
    """Verify RuleResult validates status, severity, and generates contract dictionary."""
    res = RuleResult(
        id="res-1",
        device_id="dev-1",
        rule_id="NET-001",
        status="pass",
        severity="high",
        evidence="transport input ssh",
        evidence_line_range="45-46",
        message="Telnet disabled on all lines",
        remediation="line vty 0 4\n transport input ssh",
    )

    contract = res.to_contract_dict()
    assert contract == {
        "status": "pass",
        "severity": "high",
        "evidence": "transport input ssh",
        "message": "Telnet disabled on all lines",
        "remediation": "line vty 0 4\n transport input ssh",
    }
    assert res["status"] == "pass"

    # Verify invalid status raises ValueError
    with pytest.raises(ValueError, match="Invalid status"):
        RuleResult(
            id="res-2",
            device_id="dev-1",
            rule_id="NET-001",
            status="unknown_status",
            severity="high",
        )

    # Verify invalid severity raises ValueError
    with pytest.raises(ValueError, match="Invalid severity"):
        RuleResult(
            id="res-3",
            device_id="dev-1",
            rule_id="NET-001",
            status="pass",
            severity="urgent",
        )


def test_allowed_status_and_severity_sets():
    """Verify standard status and severity sets match specification."""
    assert ALLOWED_STATUSES == {"pass", "fail", "warning", "not_applicable", "error"}
    assert ALLOWED_SEVERITIES == {"high", "medium", "low"}


def test_compliance_score_calculation_formula():
    """Verify tested-rule compliance is passed / (passed + failed) * 100."""
    # 8 pass, 2 fail -> 80.0%
    assert calculate_compliance_score(passed=8, failed=2) == 80.0

    # 10 pass, 0 fail -> 100.0%
    assert calculate_compliance_score(passed=10, failed=0) == 100.0

    # 0 pass, 5 fail -> 0.0%
    assert calculate_compliance_score(passed=0, failed=5) == 0.0

    # 0 pass, 0 fail -> 0.0%
    assert calculate_compliance_score(passed=0, failed=0) == 0.0

    # Test rounding to two decimal places (e.g. 1 pass out of 3 tested = 33.33%)
    assert calculate_compliance_score(passed=1, failed=2) == 33.33


def test_compliance_summary_excludes_warning_error_na_from_denominator():
    """Verify warnings, errors, and not_applicable are excluded from compliance score denominator."""
    results = [
        RuleResult(id="1", device_id="d1", rule_id="R1", status="pass", severity="high"),
        RuleResult(id="2", device_id="d1", rule_id="R2", status="pass", severity="high"),
        RuleResult(id="3", device_id="d1", rule_id="R3", status="fail", severity="medium"),
        RuleResult(id="4", device_id="d1", rule_id="R4", status="warning", severity="medium"),
        RuleResult(id="5", device_id="d1", rule_id="R5", status="not_applicable", severity="low"),
        RuleResult(id="6", device_id="d1", rule_id="R6", status="error", severity="high"),
    ]

    summary = calculate_device_summary(results)
    assert summary.total_rules == 6
    assert summary.passed_rules == 2
    assert summary.failed_rules == 1
    assert summary.warning_rules == 1
    assert summary.not_applicable_rules == 1
    assert summary.error_rules == 1

    # Formula: 2 / (2 + 1) * 100 = 66.67%
    assert summary.tested_rule_compliance == 66.67


def test_scan_summary_aggregates_results_not_device_averages():
    """Verify scan summary aggregates individual results, NOT by averaging device percentages.

    Example:
    Device A: 1 pass, 0 fail -> 100.0%
    Device B: 1 pass, 3 fail -> 25.0%
    Average of device percentages: (100.0 + 25.0) / 2 = 62.5%
    Aggregated rule results: 2 pass, 3 fail -> 2 / 5 * 100 = 40.0%
    """
    device_a_results = [
        RuleResult(id="a1", device_id="da", rule_id="R1", status="pass", severity="high")
    ]
    device_b_results = [
        RuleResult(id="b1", device_id="db", rule_id="R1", status="pass", severity="high"),
        RuleResult(id="b2", device_id="db", rule_id="R2", status="fail", severity="high"),
        RuleResult(id="b3", device_id="db", rule_id="R3", status="fail", severity="medium"),
        RuleResult(id="b4", device_id="db", rule_id="R4", status="fail", severity="low"),
    ]

    summary_a = calculate_device_summary(device_a_results)
    summary_b = calculate_device_summary(device_b_results)
    assert summary_a.tested_rule_compliance == 100.0
    assert summary_b.tested_rule_compliance == 25.0

    scan_summary = calculate_scan_summary([device_a_results, device_b_results])
    assert scan_summary.passed_rules == 2
    assert scan_summary.failed_rules == 3
    assert scan_summary.total_rules == 5
    # Must be 40.0, NOT 62.5
    assert scan_summary.tested_rule_compliance == 40.0
