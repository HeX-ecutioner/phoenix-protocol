"""Tests for Cisco-like configuration parser."""

import pytest

from app.models.normalized_config import NormalizedConfig
from app.parsers.cisco_like import CiscoLikeParser, parse_cisco_like


def test_parser_signature_and_return_type():
    """Verify parse_cisco_like adheres to function contract."""
    sample = "hostname TEST-RTR\n"
    res = parse_cisco_like(sample)
    assert isinstance(res, NormalizedConfig)


def test_parser_class_instance():
    """Verify CiscoLikeParser instance contract."""
    parser = CiscoLikeParser()
    res = parser.parse("hostname TEST-RTR\n")
    assert isinstance(res, NormalizedConfig)


def test_hostname_and_device_metadata_extraction():
    """Verify hostname and device metadata are properly extracted."""
    config_text = """
    hostname EDGE-ROUTER-99
    version 15.6
    """
    res = parse_cisco_like(config_text)
    assert res.device_name == "EDGE-ROUTER-99"
    assert res.vendor == "Cisco"
    assert res.device_type == "cisco_ios"
    assert res.version == "15.6"
    assert res.device_metadata["hostname"] == "EDGE-ROUTER-99"
    assert "hostname" in res.evidence_map
    assert res.evidence_map["hostname"].line_number == 2


def test_version_extraction():
    """Verify version command extraction."""
    config_text = "version 15.2(4)M\n"
    res = parse_cisco_like(config_text)
    assert res.version == "15.2(4)M"
    assert "version" in res.evidence_map
    assert res.evidence_map["version"].line_number == 1


def test_ssh_detection_and_options():
    """Verify detection of SSH version, timeouts, and authentication retries."""
    config_text = """
    ip domain-name corp.internal
    ip ssh version 2
    ip ssh time-out 60
    ip ssh authentication-retries 3
    """
    res = parse_cisco_like(config_text)
    ssh = res.settings["ssh"]
    assert ssh["enabled"] is True
    assert ssh["version"] == 2
    assert ssh["timeout"] == 60
    assert ssh["authentication_retries"] == 3
    assert "ip_ssh_version" in res.evidence_map
    assert res.evidence_map["ip_ssh_version"].line_number == 3


def test_telnet_detection_and_transport_modes():
    """Verify transport input modes on management lines."""
    config_text = """
    line vty 0 4
     transport input telnet
    """
    res = parse_cisco_like(config_text)
    vty = res.management["vty"][0]
    assert vty["telnet_enabled"] is True
    assert vty["ssh_enabled"] is False
    assert vty["ssh_only"] is False


def test_password_encryption_detection():
    """Verify service password-encryption detection and negation warning."""
    config_on = "service password-encryption\n"
    res_on = parse_cisco_like(config_on)
    assert res_on.settings["service_password_encryption"]["enabled"] is True
    assert "service_password_encryption" in res_on.evidence_map

    config_off = "no service password-encryption\n"
    res_off = parse_cisco_like(config_off)
    assert res_off.settings["service_password_encryption"]["enabled"] is False
    assert any("no service password-encryption" in w for w in res_off.warnings)


def test_login_failure_protection():
    """Verify login block-for brute force protection parsing."""
    config_text = "login block-for 300 attempts 3 within 60\n"
    res = parse_cisco_like(config_text)
    lfp = res.settings["login_failure_protection"]
    assert lfp["enabled"] is True
    assert lfp["block_for"] == 300
    assert lfp["attempts"] == 3
    assert lfp["within"] == 60
    assert "login_block_for" in res.evidence_map
    assert res.evidence_map["login_block_for"].line_number == 1


def test_logging_configuration():
    """Verify logging host, trap level, buffer, and timestamps."""
    config_text = """
    service timestamps log datetime msec
    service timestamps debug datetime msec
    logging trap warnings
    logging host 10.10.100.50
    logging buffered 64000
    """
    res = parse_cisco_like(config_text)
    logging_cfg = res.settings["logging"]
    assert logging_cfg["enabled"] is True
    assert "10.10.100.50" in logging_cfg["hosts"]
    assert logging_cfg["trap_level"] == "warnings"
    assert logging_cfg["buffered"] == 64000
    assert logging_cfg["timestamps_log"] is True
    assert logging_cfg["timestamps_debug"] is True
    assert "service_timestamps_log" in res.evidence_map


def test_ntp_server_and_peer_detection():
    """Verify NTP server (trusted) vs NTP peer detection."""
    config_text = """
    ntp server 10.1.1.1 prefer
    ntp peer 10.1.1.2
    """
    res = parse_cisco_like(config_text)
    ntp = res.settings["ntp"]
    assert ntp["enabled"] is True
    assert "10.1.1.1" in ntp["servers"]
    assert "10.1.1.2" in ntp["peers"]
    assert ntp["has_trusted_server"] is True
    assert "ntp_server_1" in res.evidence_map
    assert "ntp_peer_1" in res.evidence_map


def test_vty_scoped_blocks_and_access_class():
    """Verify access-class and login mode under a VTY block."""
    config_text = """
    line vty 0 4
     access-class ADMIN_ACL in
     login local
     exec-timeout 10 0
     transport input ssh
    """
    res = parse_cisco_like(config_text)
    assert len(res.management["vty"]) == 1
    vty = res.management["vty"][0]
    assert vty["range"] == "0 4"
    assert vty["access_class"] == "ADMIN_ACL"
    assert vty["access_class_direction"] == "in"
    assert vty["login_mode"] == "local"
    assert vty["exec_timeout"] == "10 0"
    assert vty["ssh_only"] is True


def test_multiple_vty_blocks_remain_separate():
    """CRITICAL: Verify multiple separate VTY blocks are not flattened into one global value."""
    config_text = """
    line vty 0 4
     access-class MGMT_IN in
     transport input ssh
    !
    line vty 5 15
     transport input telnet
    """
    res = parse_cisco_like(config_text)
    vty_blocks = res.management["vty"]
    assert len(vty_blocks) == 2

    # Block 1 (lines 0 4)
    b1 = vty_blocks[0]
    assert b1["range"] == "0 4"
    assert b1["ssh_only"] is True
    assert b1["telnet_enabled"] is False
    assert b1["access_class"] == "MGMT_IN"

    # Block 2 (lines 5 15)
    b2 = vty_blocks[1]
    assert b2["range"] == "5 15"
    assert b2["ssh_only"] is False
    assert b2["telnet_enabled"] is True
    assert b2["access_class"] is None

    # Lookup by range key also works
    assert vty_blocks["0 4"]["access_class"] == "MGMT_IN"
    assert vty_blocks["5 15"]["telnet_enabled"] is True

    # Rule evaluation can check whether ALL blocks are compliant
    all_ssh_only = all(b["ssh_only"] for b in vty_blocks)
    assert all_ssh_only is False, "Must detect that block 5 15 is non-compliant!"


def test_http_and_small_servers_detection():
    """Verify HTTP server and small services detection (enabled vs disabled)."""
    config_failing = """
    ip http server
    service tcp-small-servers
    service udp-small-servers
    """
    res_fail = parse_cisco_like(config_failing)
    sec_fail = res_fail.settings["insecure_services"]
    assert sec_fail["http_server_enabled"] is True
    assert sec_fail["tcp_small_servers_enabled"] is True
    assert sec_fail["udp_small_servers_enabled"] is True

    config_compliant = """
    no ip http server
    no service tcp-small-servers
    no service udp-small-servers
    no ip source-route
    """
    res_comp = parse_cisco_like(config_compliant)
    sec_comp = res_comp.settings["insecure_services"]
    assert sec_comp["http_server_enabled"] is False
    assert sec_comp["tcp_small_servers_enabled"] is False
    assert sec_comp["udp_small_servers_enabled"] is False
    assert sec_comp["ip_source_route_enabled"] is False


def test_banner_motd_and_login_detection():
    """Verify single-line and multi-line banners with line range preservation."""
    config_text = """
    banner motd ^C
    Authorized Access Only!
    Violators will be prosecuted.
    ^C
    banner login # Welcome to Router #
    """
    res = parse_cisco_like(config_text)
    banners = res.settings["banners"]
    assert banners["motd_configured"] is True
    assert banners["motd_line_range"] == "2-5"
    assert "banner_motd" in res.evidence_map
    assert res.evidence_map["banner_motd"].line_range == "2-5"

    assert banners["login_configured"] is True
    assert banners["login_line_range"] == "6"


def test_plaintext_secret_masking_in_evidence():
    """Verify plaintext secrets and hashes are redacted from evidence and categorized."""
    config_text = """
    username admin privilege 15 password 0 PlaintextSecret123!
    username auditor privilege 5 secret 9 ScryptHashString999
    enable password cisco
    enable secret 5 Md5HashString555
    line con 0
     password 7 0822455D0A16
    """
    res = parse_cisco_like(config_text)

    # 1. Plaintext secrets detected
    assert len(res.settings["plaintext_secrets_found"]) >= 2
    assert len(res.settings["weak_secrets_found"]) >= 1

    # 2. Check evidence sanitization (raw secrets must NEVER appear)
    for key, ev in res.evidence_map.items():
        assert "PlaintextSecret123!" not in ev.evidence_text
        assert "ScryptHashString999" not in ev.evidence_text
        assert "cisco" not in ev.evidence_text
        assert "0822455D0A16" not in ev.evidence_text

    # 3. Check specific redacted evidence strings
    assert "[REDACTED]" in res.evidence_map["username_admin"].evidence_text
    assert "[REDACTED]" in res.evidence_map["enable_password"].evidence_text
    assert "[REDACTED]" in res.evidence_map["con_0_password"].evidence_text


def test_line_number_and_evidence_preservation():
    """Verify source line numbers are accurately preserved across all extracted settings."""
    config_text = """! Line 1
hostname CORE-RTR
! Line 3
version 15.7
! Line 5
ip ssh version 2
"""
    res = parse_cisco_like(config_text)
    assert res.evidence_map["hostname"].line_number == 2
    assert res.evidence_map["version"].line_number == 4
    assert res.evidence_map["ip_ssh_version"].line_number == 6


def test_warnings_for_ambiguous_or_unsupported_syntax():
    """Verify warnings generated for ambiguous configurations."""
    # Ambiguous transport input 'all', missing hostname, NTP peer without server
    config_text = """
    ntp peer 192.168.1.1
    line vty 0 4
     transport input all
    logging buffered 64000
    """
    res = parse_cisco_like(config_text)
    assert len(res.warnings) >= 3
    assert any("transport input 'all'" in w for w in res.warnings)
    assert any("Missing hostname" in w for w in res.warnings)
    assert any("NTP peer configured" in w for w in res.warnings)
    assert any("Local logging buffer" in w for w in res.warnings)


def test_malformed_input_handling():
    """Verify errors for unclosed banner delimiters, empty input, and type checking."""
    # 1. Non-string input raises TypeError
    with pytest.raises(TypeError, match="config_text must be a str"):
        parse_cisco_like(None)  # type: ignore

    # 2. Empty input produces controlled error
    empty_res = parse_cisco_like("   \n   \n")
    assert len(empty_res.errors) >= 1
    assert "empty" in empty_res.errors[0].lower()

    # 3. Unclosed banner delimiter produces controlled error
    unclosed_banner = """
    hostname RTR-ERR
    banner motd ^C
    Some unclosed message without delimiter...
    """
    err_res = parse_cisco_like(unclosed_banner)
    assert len(err_res.errors) >= 1
    assert "unclosed banner" in err_res.errors[0].lower()


def test_parser_never_stores_complete_raw_configuration():
    """Verify NormalizedConfig does not retain complete raw configuration text."""
    secret_marker = "UNIQUE_PROPRIETARY_STRING_NOT_SAVED"
    config_text = f"""
    hostname EDGE-01
    description {secret_marker}
    interface GigabitEthernet0/0
     ip address 192.168.1.1 255.255.255.0
    """
    res = parse_cisco_like(config_text)

    # Convert entire NormalizedConfig data to string representation
    serialized_repr = repr(res) + str(res.__dict__)
    assert secret_marker not in serialized_repr, "Raw configuration lines must not be stored in NormalizedConfig!"
    assert not hasattr(res, "raw_config")
    assert not hasattr(res, "raw_text")


def test_determinism_repeated_parses():
    """Verify identical input generates exactly equal output across repeated runs."""
    sample = """
    hostname DETERMINISTIC-RTR
    version 15.4
    service password-encryption
    ip ssh version 2
    login block-for 300 attempts 3 within 60
    line vty 0 4
     access-class ADMIN_ACL in
     transport input ssh
    """
    run1 = parse_cisco_like(sample)
    run2 = parse_cisco_like(sample)

    assert run1 == run2
    assert run1.settings == run2.settings
    assert run1.management == run2.management
    assert run1.evidence_map == run2.evidence_map
    assert run1.warnings == run2.warnings
    assert run1.errors == run2.errors


def test_sample_fixtures_parsing():
    """Verify parsing against all three project sample fixtures."""
    # 1. Compliant Router
    with open("sample_data/compliant_router.txt") as f:
        comp = parse_cisco_like(f.read())
    assert comp.device_name == "CORE-RTR-01"
    assert comp.settings["ssh"]["version"] == 2
    assert len(comp.management["vty"]) == 2
    assert all(b["ssh_only"] for b in comp.management["vty"])
    assert all(b["access_class"] == "ADMIN_MGMT_ACL" for b in comp.management["vty"])
    assert comp.errors == []
    assert comp.warnings == []

    # 2. Failing Router
    with open("sample_data/failing_router.txt") as f:
        fail = parse_cisco_like(f.read())
    assert fail.device_name == "DEFAULT-RTR"
    assert fail.settings["ssh"]["enabled"] is False
    assert fail.management["vty"][0]["telnet_enabled"] is True
    assert len(fail.settings["plaintext_secrets_found"]) >= 2
    assert len(fail.warnings) >= 4

    # 3. Ambiguous Router
    with open("sample_data/ambiguous_router.txt") as f:
        ambi = parse_cisco_like(f.read())
    assert ambi.device_name is None
    assert len(ambi.warnings) >= 4
    assert ambi.errors == []
