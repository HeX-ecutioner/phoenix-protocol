from pathlib import Path

from app.models.normalized_config import ConfigEvidence, NormalizedConfig

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"
from app.models.rule import Rule
from app.models.rule_result import ALLOWED_SEVERITIES, ALLOWED_STATUSES, RuleResult
from app.parsers.cisco_like import BlockList, parse_cisco_like
from app.rules.checks import check_rule
from app.rules.definitions import INITIAL_RULES, RULES_BY_ID
from app.rules.engine import RuleEngine, evaluate_all, evaluate_rule
from app.services.compliance import calculate_summary


def test_rule_definitions_catalog_stability():
    """Verify rule definitions remain stable, active, and indexed from NET-001 to NET-010."""
    assert len(INITIAL_RULES) == 10
    expected_ids = [f"NET-{i:03d}" for i in range(1, 11)]
    actual_ids = [r.rule_id for r in INITIAL_RULES]
    assert actual_ids == expected_ids

    for rule in INITIAL_RULES:
        assert rule.rule_id in RULES_BY_ID
        assert rule.severity in ALLOWED_SEVERITIES
        assert len(rule.title) > 0
        assert len(rule.description) > 0
        assert len(rule.technical_requirement) > 0
        assert len(rule.remediation) > 0
        assert rule.active is True


def test_net_001_telnet_disabled_logic():
    """Verify NET-001 passes when all VTY lines are SSH-only, and fails if any permits Telnet."""
    rule = RULES_BY_ID["NET-001"]

    # All SSH-only VTY blocks -> PASS
    cfg_pass = NormalizedConfig(
        management={
            "vty": BlockList([
                {"range": "0 4", "ssh_only": True, "telnet_enabled": False, "start_line": 40},
                {"range": "5 15", "ssh_only": True, "telnet_enabled": False, "start_line": 45},
            ])
        }
    )
    res_pass = evaluate_rule(rule, cfg_pass)
    assert res_pass.status == "pass"

    # One VTY block permits Telnet -> FAIL
    cfg_fail = NormalizedConfig(
        management={
            "vty": BlockList([
                {"range": "0 4", "ssh_only": True, "telnet_enabled": False, "start_line": 40},
                {"range": "5 15", "ssh_only": False, "telnet_enabled": True, "start_line": 45},
            ])
        }
    )
    res_fail = evaluate_rule(rule, cfg_fail)
    assert res_fail.status == "fail"
    assert "line vty 5 15" in res_fail.message

    # Empty VTY blocks -> WARNING
    cfg_empty = NormalizedConfig()
    res_empty = evaluate_rule(rule, cfg_empty)
    assert res_empty.status == "warning"


def test_net_002_ssh_enabled_logic():
    """Verify NET-002 passes for SSH v2, fails for v1 or disabled."""
    rule = RULES_BY_ID["NET-002"]

    cfg_v2 = NormalizedConfig(settings={"ssh": {"enabled": True, "version": 2, "line_number": 20}})
    assert evaluate_rule(rule, cfg_v2).status == "pass"

    cfg_v1 = NormalizedConfig(settings={"ssh": {"enabled": True, "version": 1, "line_number": 20}})
    res_v1 = evaluate_rule(rule, cfg_v1)
    assert res_v1.status == "fail"
    assert "insecure version '1'" in res_v1.message

    cfg_none = NormalizedConfig(settings={"ssh": {"enabled": False}})
    assert evaluate_rule(rule, cfg_none).status == "fail"


def test_net_003_password_encryption_logic():
    """Verify NET-003 fails on plaintext/Type 7 credentials and passes on strong encryption."""
    rule = RULES_BY_ID["NET-003"]

    # Pass: service password-encryption enabled, no plaintext or weak secrets
    cfg_pass = NormalizedConfig(
        settings={
            "service_password_encryption": {"enabled": True, "line_number": 5},
            "plaintext_secrets_found": [],
            "weak_secrets_found": [],
        }
    )
    assert evaluate_rule(rule, cfg_pass).status == "pass"

    # Fail: plaintext credentials present
    cfg_plain = NormalizedConfig(
        settings={
            "service_password_encryption": {"enabled": True},
            "plaintext_secrets_found": [{"context": "username admin", "line": 10}],
            "weak_secrets_found": [],
        }
    )
    assert evaluate_rule(rule, cfg_plain).status == "fail"

    # Fail: weak Type 7 credentials present
    cfg_weak = NormalizedConfig(
        settings={
            "service_password_encryption": {"enabled": True},
            "plaintext_secrets_found": [],
            "weak_secrets_found": [{"context": "line vty 0 4", "line": 30}],
        }
    )
    assert evaluate_rule(rule, cfg_weak).status == "fail"

    # Fail: service password-encryption explicitly disabled
    cfg_no_enc = NormalizedConfig(
        settings={
            "service_password_encryption": {"enabled": False},
            "plaintext_secrets_found": [],
            "weak_secrets_found": [],
        }
    )
    assert evaluate_rule(rule, cfg_no_enc).status == "fail"


def test_net_004_login_failure_protection_logic():
    """Verify NET-004 passes when login block-for is configured, fails when absent."""
    rule = RULES_BY_ID["NET-004"]

    cfg_pass = NormalizedConfig(
        settings={"login_failure_protection": {"enabled": True, "block_for": 300, "attempts": 3, "within": 60, "line_number": 31}}
    )
    res_pass = evaluate_rule(rule, cfg_pass)
    assert res_pass.status == "pass"
    assert "block-for 300s" in res_pass.message

    cfg_fail = NormalizedConfig(
        settings={"login_failure_protection": {"enabled": False}}
    )
    assert evaluate_rule(rule, cfg_fail).status == "fail"

    cfg_ambi = NormalizedConfig(
        settings={"login_failure_protection": {"enabled": False}},
        warnings=["Ambiguous or non-standard 'login block-for' syntax on line 12"],
    )
    assert evaluate_rule(rule, cfg_ambi).status == "warning"


def test_net_005_system_logging_logic():
    """Verify NET-005 passes with remote host, warns with buffer only, fails with none."""
    rule = RULES_BY_ID["NET-005"]

    cfg_pass = NormalizedConfig(settings={"logging": {"hosts": ["10.0.0.1"]}})
    assert evaluate_rule(rule, cfg_pass).status == "pass"

    cfg_buf = NormalizedConfig(settings={"logging": {"hosts": [], "buffered": 64000}})
    res_buf = evaluate_rule(rule, cfg_buf)
    assert res_buf.status == "warning"
    assert "no remote syslog host" in res_buf.message

    cfg_fail = NormalizedConfig(settings={"logging": {"hosts": [], "buffered": None}})
    assert evaluate_rule(rule, cfg_fail).status == "fail"


def test_net_006_trusted_time_source_logic():
    """Verify NET-006 passes with NTP server, warns with peer only, fails with none."""
    rule = RULES_BY_ID["NET-006"]

    cfg_pass = NormalizedConfig(settings={"ntp": {"servers": ["10.1.1.1"]}})
    assert evaluate_rule(rule, cfg_pass).status == "pass"

    cfg_peer = NormalizedConfig(settings={"ntp": {"servers": [], "peers": ["192.168.1.1"]}})
    res_peer = evaluate_rule(rule, cfg_peer)
    assert res_peer.status == "warning"
    assert "no authoritative 'ntp server'" in res_peer.message

    cfg_fail = NormalizedConfig(settings={"ntp": {"servers": [], "peers": []}})
    assert evaluate_rule(rule, cfg_fail).status == "fail"


def test_net_007_admin_access_list_logic():
    """Verify NET-007 passes ONLY if all VTY blocks have an access-class."""
    rule = RULES_BY_ID["NET-007"]

    # Both blocks have ACL -> PASS
    cfg_pass = NormalizedConfig(
        management={
            "vty": BlockList([
                {"range": "0 4", "access_class": "MGMT_ACL", "access_class_line": 45},
                {"range": "5 15", "access_class": "MGMT_ACL", "access_class_line": 50},
            ])
        }
    )
    assert evaluate_rule(rule, cfg_pass).status == "pass"

    # Second block lacks ACL -> FAIL
    cfg_fail = NormalizedConfig(
        management={
            "vty": BlockList([
                {"range": "0 4", "access_class": "MGMT_ACL", "access_class_line": 45},
                {"range": "5 15", "access_class": None, "start_line": 48},
            ])
        }
    )
    res_fail = evaluate_rule(rule, cfg_fail)
    assert res_fail.status == "fail"
    assert "line vty 5 15" in res_fail.message

    # Empty VTY -> WARNING
    cfg_empty = NormalizedConfig()
    assert evaluate_rule(rule, cfg_empty).status == "warning"


def test_net_008_insecure_services_logic():
    """Verify NET-008 fails if insecure services are enabled and passes if disabled."""
    rule = RULES_BY_ID["NET-008"]

    cfg_fail = NormalizedConfig(
        settings={"insecure_services": {"http_server_enabled": True, "tcp_small_servers_enabled": False}}
    )
    assert evaluate_rule(rule, cfg_fail).status == "fail"

    cfg_pass = NormalizedConfig(
        settings={"insecure_services": {"http_server_enabled": False, "tcp_small_servers_enabled": False}},
        evidence_map={"no_ip_http_server": ConfigEvidence(field_name="no_ip_http_server", evidence_text="no ip http server")},
    )
    assert evaluate_rule(rule, cfg_pass).status == "pass"

    cfg_warn = NormalizedConfig(settings={"insecure_services": {}})
    assert evaluate_rule(rule, cfg_warn).status == "warning"


def test_net_009_device_identification_banner_logic():
    """Verify NET-009 requires hostname and MOTD banner."""
    rule = RULES_BY_ID["NET-009"]

    cfg_pass = NormalizedConfig(
        device_name="CORE-01",
        settings={"banners": {"motd_configured": True, "login_configured": False}},
    )
    assert evaluate_rule(rule, cfg_pass).status == "pass"

    cfg_no_banner = NormalizedConfig(
        device_name="CORE-01",
        settings={"banners": {"motd_configured": False, "login_configured": False}},
    )
    assert evaluate_rule(rule, cfg_no_banner).status == "fail"

    cfg_no_host = NormalizedConfig(
        device_name=None,
        settings={"banners": {"motd_configured": True}},
    )
    assert evaluate_rule(rule, cfg_no_host).status == "warning"


def test_net_010_plaintext_secrets_logic():
    """Verify NET-010 fails when plaintext credentials are identified."""
    rule = RULES_BY_ID["NET-010"]

    cfg_pass = NormalizedConfig(settings={"plaintext_secrets_found": []})
    assert evaluate_rule(rule, cfg_pass).status == "pass"

    cfg_fail = NormalizedConfig(
        settings={"plaintext_secrets_found": [{"context": "username admin", "line": 12}]},
        evidence_map={"username_admin": ConfigEvidence(field_name="username_admin", evidence_text="username admin password 0 [REDACTED]", line_number=12)},
    )
    res_fail = evaluate_rule(rule, cfg_fail)
    assert res_fail.status == "fail"
    assert "[REDACTED]" in res_fail.evidence
    assert "SuperSecret" not in res_fail.evidence


def test_compliant_router_fixture_all_pass():
    """Verify compliant_router.txt produces 10/10 PASS findings and 100.0% compliance."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt") as f:
        config = parse_cisco_like(f.read())

    engine = RuleEngine()
    results = engine.evaluate(config, scan_id="scan-comp", device_id="dev-comp")

    assert len(results) == 10
    for r in results:
        assert r.status == "pass", f"Rule {r.rule_id} was expected to pass but was {r.status}: {r.message}"
        assert r.severity in ALLOWED_SEVERITIES
        assert r.remediation is not None

    summary = calculate_summary(results)
    assert summary.total_rules == 10
    assert summary.passed_rules == 10
    assert summary.failed_rules == 0
    assert summary.tested_rule_compliance == 100.0


def test_failing_router_fixture_all_fail():
    """Verify failing_router.txt produces 10/10 FAIL findings and 0.0% compliance."""
    with open(SAMPLE_DATA_DIR / "failing_router.txt") as f:
        config = parse_cisco_like(f.read())

    engine = RuleEngine()
    results = engine.evaluate(config, scan_id="scan-fail", device_id="dev-fail")

    assert len(results) == 10
    for r in results:
        assert r.status == "fail", f"Rule {r.rule_id} was expected to fail but was {r.status}: {r.message}"
        assert r.severity in ALLOWED_SEVERITIES

    summary = calculate_summary(results)
    assert summary.total_rules == 10
    assert summary.passed_rules == 0
    assert summary.failed_rules == 10
    assert summary.tested_rule_compliance == 0.0


def test_ambiguous_router_fixture_warnings_preserved():
    """Verify ambiguous_router.txt produces warnings/manual-review states rather than silently passing."""
    with open(SAMPLE_DATA_DIR / "ambiguous_router.txt") as f:
        config = parse_cisco_like(f.read())

    results = evaluate_all(config)
    status_by_rule = {r.rule_id: r.status for r in results}

    # Verify warnings are preserved for logging (NET-005), NTP (NET-006), banners (NET-009)
    assert status_by_rule["NET-005"] == "warning"
    assert status_by_rule["NET-006"] == "warning"
    assert status_by_rule["NET-008"] == "warning"
    assert status_by_rule["NET-009"] == "warning"

    # Warnings MUST NOT count as passes in compliance calculation
    summary = calculate_summary(results)
    assert summary.warning_rules >= 4
    assert summary.passed_rules < summary.total_rules
    # Score should exclude warnings from denominator: passed / (passed + failed) * 100
    expected_score = round(summary.passed_rules / (summary.passed_rules + summary.failed_rules) * 100.0, 2)
    assert summary.tested_rule_compliance == expected_score


def test_secrets_never_appear_in_evidence_or_messages():
    """CRITICAL: Verify secrets and hashes never appear in RuleResult evidence or messages."""
    raw_secret = "UltraSecretPassword123!"
    config_text = f"""
    hostname SEC-RTR
    enable password {raw_secret}
    username admin password 0 {raw_secret}
    """
    config = parse_cisco_like(config_text)
    results = evaluate_all(config)

    for r in results:
        assert raw_secret not in r.evidence
        assert raw_secret not in r.message
        assert raw_secret not in str(r.to_contract_dict())


def test_multiple_vty_blocks_single_insecure_fails_rule():
    """Verify a single insecure VTY block causes NET-001 and NET-007 to fail."""
    config_text = """
    hostname VTY-TEST-RTR
    line vty 0 4
     access-class SECURE_ACL in
     transport input ssh
    !
    line vty 5 15
     transport input telnet
    """
    config = parse_cisco_like(config_text)
    results = {r.rule_id: r for r in evaluate_all(config)}

    # NET-001 must FAIL because vty 5 15 allows Telnet
    assert results["NET-001"].status == "fail"
    assert "line vty 5 15" in results["NET-001"].message

    # NET-007 must FAIL because vty 5 15 has no access-class
    assert results["NET-007"].status == "fail"
    assert "line vty 5 15" in results["NET-007"].message


def test_engine_determinism():
    """Verify rule evaluation is completely deterministic across repeated invocations."""
    with open(SAMPLE_DATA_DIR / "compliant_router.txt") as f:
        config = parse_cisco_like(f.read())

    res1 = evaluate_all(config)
    res2 = evaluate_all(config)

    assert len(res1) == len(res2)
    for r1, r2 in zip(res1, res2):
        assert r1.rule_id == r2.rule_id
        assert r1.status == r2.status
        assert r1.severity == r2.severity
        assert r1.evidence == r2.evidence
        assert r1.message == r2.message
        assert r1.remediation == r2.remediation


def test_missing_normalized_fields_defensive_evaluation():
    """Verify empty/malformed NormalizedConfig does not crash the rule engine."""
    empty_config = NormalizedConfig()
    results = evaluate_all(empty_config)

    assert len(results) == 10
    for r in results:
        assert r.status in ALLOWED_STATUSES
        assert r.severity in ALLOWED_SEVERITIES
        assert len(r.message) > 0


def test_engine_does_not_require_database_or_network():
    """Verify RuleEngine operates purely in-memory without database or external connections."""
    engine = RuleEngine()
    config = NormalizedConfig(
        device_name="STANDALONE-RTR",
        settings={"ssh": {"enabled": True, "version": 2}},
    )
    result = engine.evaluate_rule(RULES_BY_ID["NET-002"], config)
    assert isinstance(result, RuleResult)
    assert result.status == "pass"
