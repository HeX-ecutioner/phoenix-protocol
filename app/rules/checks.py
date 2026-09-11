"""Deterministic compliance rule check implementations.

Provides discrete, deterministic evaluation functions for rules NET-001 through NET-010.
Adheres strictly to the rule contracts:
- Uses only normalized configuration data
- Preserves sanitized line evidence and line numbers
- Never exposes secrets in evidence or messages
- Returns structured evaluation findings
- Never silently converts warnings or errors into passes
"""

from typing import Any, Dict, List, Optional

from app.models.normalized_config import NormalizedConfig
from app.models.rule import Rule
from app.rules.definitions import RULES_BY_ID


def check_net_001_telnet_disabled(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-001: Telnet Service Disabled.

    Fail when any relevant VTY block permits Telnet.
    Pass when all applicable VTY blocks are SSH-only.
    Warning/error where the parser cannot determine the state.
    """
    vty_blocks = config.management.get("vty", [])
    if not vty_blocks:
        return {
            "status": "warning",
            "severity": rule.severity,
            "evidence": "No line vty configuration blocks found",
            "evidence_line_range": None,
            "message": "Unable to verify Telnet status: no VTY line blocks found in configuration.",
            "remediation": rule.remediation,
        }

    telnet_blocks: List[str] = []
    first_telnet_block: Optional[Dict[str, Any]] = None

    for block in vty_blocks:
        brange = block.get("range", "unknown")
        if block.get("telnet_enabled"):
            telnet_blocks.append(f"line vty {brange}")
            if first_telnet_block is None:
                first_telnet_block = block

    if telnet_blocks:
        slug = first_telnet_block.get("range", "").replace(" ", "_") if first_telnet_block else ""
        ev = config.evidence_map.get(f"vty_{slug}_transport")
        ev_text = ev.evidence_text if ev else f"{telnet_blocks[0]} permits telnet"
        ev_range = ev.line_range if ev else str(first_telnet_block.get("start_line")) if first_telnet_block else None

        return {
            "status": "fail",
            "severity": rule.severity,
            "evidence": ev_text,
            "evidence_line_range": ev_range,
            "message": f"Telnet is permitted for administrative access on: {', '.join(telnet_blocks)}.",
            "remediation": rule.remediation,
        }

    if all(block.get("ssh_only") for block in vty_blocks):
        first_b = vty_blocks[0]
        slug = first_b.get("range", "").replace(" ", "_")
        ev = config.evidence_map.get(f"vty_{slug}_transport")
        ev_text = ev.evidence_text if ev else "transport input ssh"
        ev_range = ev.line_range if ev else str(first_b.get("start_line"))

        return {
            "status": "pass",
            "severity": rule.severity,
            "evidence": ev_text,
            "evidence_line_range": ev_range,
            "message": "Telnet is disabled on all administrative VTY line blocks (SSH-only enforced).",
            "remediation": rule.remediation,
        }

    return {
        "status": "warning",
        "severity": rule.severity,
        "evidence": "VTY transport input configuration is ambiguous or incomplete",
        "evidence_line_range": None,
        "message": "VTY transport configuration is ambiguous or does not explicitly restrict protocols.",
        "remediation": rule.remediation,
    }


def check_net_002_ssh_enabled(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-002: Secure Administration (SSH Enabled).

    Pass when SSH is enabled and version 2 is configured.
    Fail when SSH is explicitly disabled, unavailable, or running version 1.
    """
    ssh_cfg = config.settings.get("ssh", {})
    enabled = ssh_cfg.get("enabled", False)
    version = ssh_cfg.get("version")

    ev = config.evidence_map.get("ip_ssh_version") or config.evidence_map.get("ip_ssh")

    if enabled and version == 2:
        return {
            "status": "pass",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else "ip ssh version 2",
            "evidence_line_range": ev.line_range if ev else str(ssh_cfg.get("line_number")),
            "message": "SSH version 2 is configured and active for remote management.",
            "remediation": rule.remediation,
        }

    if enabled and version is not None and version != 2:
        return {
            "status": "fail",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else f"ip ssh version {version}",
            "evidence_line_range": ev.line_range if ev else str(ssh_cfg.get("line_number")),
            "message": f"SSH is enabled but configured for legacy/insecure version '{version}' instead of version 2.",
            "remediation": rule.remediation,
        }

    return {
        "status": "fail",
        "severity": rule.severity,
        "evidence": "No 'ip ssh' configuration statement detected",
        "evidence_line_range": None,
        "message": "SSH is not enabled for secure administrative access.",
        "remediation": rule.remediation,
    }


def check_net_003_password_encryption(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-003: Strong Password Encryption.

    Fail when plaintext credentials or Cisco Type 7 reversible credentials are detected.
    Pass when credentials use robust password hashing and encryption is active.
    """
    svc_pw = config.settings.get("service_password_encryption", {})
    pw_encryption_enabled = svc_pw.get("enabled", False)
    plaintext_secrets = config.settings.get("plaintext_secrets_found", [])
    weak_secrets = config.settings.get("weak_secrets_found", [])

    if plaintext_secrets or weak_secrets:
        first_issue = plaintext_secrets[0] if plaintext_secrets else weak_secrets[0]
        line_num = first_issue.get("line")
        ev_text = "Weak or unencrypted credentials detected in configuration"
        ev_range = str(line_num) if line_num else None

        for v in config.evidence_map.values():
            if v.line_number == line_num:
                ev_text = v.evidence_text
                ev_range = v.line_range
                break

        reasons: List[str] = []
        if plaintext_secrets:
            reasons.append(f"{len(plaintext_secrets)} plaintext credential(s)")
        if weak_secrets:
            reasons.append(f"{len(weak_secrets)} reversible Type 7 credential(s)")

        return {
            "status": "fail",
            "severity": rule.severity,
            "evidence": ev_text,
            "evidence_line_range": ev_range,
            "message": f"Credentials stored insecurely: {', '.join(reasons)}.",
            "remediation": rule.remediation,
        }

    if not pw_encryption_enabled:
        ev = config.evidence_map.get("service_password_encryption")
        return {
            "status": "fail",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else "no service password-encryption",
            "evidence_line_range": ev.line_range if ev else None,
            "message": "Global 'service password-encryption' is not enabled.",
            "remediation": rule.remediation,
        }

    ev = config.evidence_map.get("service_password_encryption")
    return {
        "status": "pass",
        "severity": rule.severity,
        "evidence": ev.evidence_text if ev else "service password-encryption",
        "evidence_line_range": ev.line_range if ev else str(svc_pw.get("line_number")),
        "message": "Service password-encryption is active and all credentials use robust hashing.",
        "remediation": rule.remediation,
    }


def check_net_004_login_failure_protection(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-004: Login Failure Protection.

    Pass when appropriate login rate limiting / quiet mode is configured.
    Fail when absent or disabled where configuration provides enough information.
    """
    lfp = config.settings.get("login_failure_protection", {})
    enabled = lfp.get("enabled", False)

    if enabled:
        ev = config.evidence_map.get("login_block_for")
        b_for = lfp.get("block_for")
        att = lfp.get("attempts")
        wit = lfp.get("within")
        return {
            "status": "pass",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else f"login block-for {b_for} attempts {att} within {wit}",
            "evidence_line_range": ev.line_range if ev else str(lfp.get("line_number")),
            "message": f"Login failure protection is configured (block-for {b_for}s on {att} attempts within {wit}s).",
            "remediation": rule.remediation,
        }

    # Check for warnings on ambiguous login configuration
    ambiguous_warning = next((w for w in config.warnings if "login block-for" in w), None)
    if ambiguous_warning:
        return {
            "status": "warning",
            "severity": rule.severity,
            "evidence": "Ambiguous login rate-limiting syntax detected",
            "evidence_line_range": None,
            "message": ambiguous_warning,
            "remediation": rule.remediation,
        }

    return {
        "status": "fail",
        "severity": rule.severity,
        "evidence": "No 'login block-for' configuration statement detected",
        "evidence_line_range": None,
        "message": "Login failure protection (login block-for) is not configured against brute-force attacks.",
        "remediation": rule.remediation,
    }


def check_net_005_system_logging(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-005: System Logging Configured.

    Pass when remote syslog host is configured.
    Warning when only local logging buffer is configured without a remote host.
    Fail when system logging is completely absent.
    """
    logging_cfg = config.settings.get("logging", {})
    hosts = logging_cfg.get("hosts", [])
    buffered = logging_cfg.get("buffered")

    if hosts:
        ev = config.evidence_map.get("logging_host_1") or config.evidence_map.get("logging_host")
        host_str = ", ".join(hosts)
        return {
            "status": "pass",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else f"logging host {hosts[0]}",
            "evidence_line_range": ev.line_range if ev else None,
            "message": f"Remote system logging is configured to syslog host(s): {host_str}.",
            "remediation": rule.remediation,
        }

    if buffered:
        ev = config.evidence_map.get("logging_buffered")
        return {
            "status": "warning",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else "logging buffered",
            "evidence_line_range": ev.line_range if ev else None,
            "message": "Local logging buffer is configured, but no remote syslog host is specified.",
            "remediation": rule.remediation,
        }

    return {
        "status": "fail",
        "severity": rule.severity,
        "evidence": "No logging host or logging timestamps configuration detected",
        "evidence_line_range": None,
        "message": "System logging is not configured.",
        "remediation": rule.remediation,
    }


def check_net_006_trusted_time_source(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-006: Trusted Time Source (NTP).

    Pass when at least one authoritative NTP server is configured.
    Warning when only NTP peers exist without an authoritative server.
    Fail when NTP is completely absent.
    """
    ntp_cfg = config.settings.get("ntp", {})
    servers = ntp_cfg.get("servers", [])
    peers = ntp_cfg.get("peers", [])

    if servers:
        ev = config.evidence_map.get("ntp_server_1") or config.evidence_map.get("ntp_server")
        server_str = ", ".join(servers)
        return {
            "status": "pass",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else f"ntp server {servers[0]}",
            "evidence_line_range": ev.line_range if ev else None,
            "message": f"Authoritative NTP server(s) configured: {server_str}.",
            "remediation": rule.remediation,
        }

    if peers and not servers:
        ev = config.evidence_map.get("ntp_peer_1") or config.evidence_map.get("ntp_peer")
        peer_str = ", ".join(peers)
        return {
            "status": "warning",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else f"ntp peer {peers[0]}",
            "evidence_line_range": ev.line_range if ev else None,
            "message": f"NTP peer(s) configured ({peer_str}), but no authoritative 'ntp server' statement found.",
            "remediation": rule.remediation,
        }

    return {
        "status": "fail",
        "severity": rule.severity,
        "evidence": "No 'ntp server' or 'ntp peer' configuration statements detected",
        "evidence_line_range": None,
        "message": "No trusted time source (NTP) configured.",
        "remediation": rule.remediation,
    }


def check_net_007_admin_access_list(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-007: Approved Administrative Access List.

    Evaluate ALL applicable VTY blocks.
    Pass only if every applicable VTY block has an access-class.
    Fail if one or more VTY blocks lack the required restriction.
    Warning if the parser cannot confidently determine applicability.
    """
    vty_blocks = config.management.get("vty", [])
    if not vty_blocks:
        return {
            "status": "warning",
            "severity": rule.severity,
            "evidence": "No VTY lines found to verify access-class restrictions",
            "evidence_line_range": None,
            "message": "Unable to verify administrative access list: no line vty blocks found in configuration.",
            "remediation": rule.remediation,
        }

    missing_ac: List[str] = []
    first_missing_line: Optional[int] = None
    configured_ac: List[str] = []

    for block in vty_blocks:
        brange = block.get("range", "unknown")
        acl = block.get("access_class")
        if acl:
            configured_ac.append(f"line vty {brange} (ACL: {acl})")
        else:
            missing_ac.append(f"line vty {brange}")
            if first_missing_line is None:
                first_missing_line = block.get("start_line")

    if missing_ac:
        return {
            "status": "fail",
            "severity": rule.severity,
            "evidence": f"VTY line block(s) without access-class: {', '.join(missing_ac)}",
            "evidence_line_range": str(first_missing_line) if first_missing_line else None,
            "message": f"Administrative access list restriction is missing on: {', '.join(missing_ac)}.",
            "remediation": rule.remediation,
        }

    first_b = vty_blocks[0]
    slug = first_b.get("range", "").replace(" ", "_")
    ev = config.evidence_map.get(f"vty_{slug}_access_class")
    ev_text = ev.evidence_text if ev else configured_ac[0]
    ev_range = ev.line_range if ev else str(first_b.get("access_class_line"))

    return {
        "status": "pass",
        "severity": rule.severity,
        "evidence": ev_text,
        "evidence_line_range": ev_range,
        "message": f"Administrative access-class configured across all VTY line blocks: {', '.join(configured_ac)}.",
        "remediation": rule.remediation,
    }


def check_net_008_insecure_services(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-008: Unused Insecure Services Disabled.

    Fail if HTTP server, small TCP servers, or small UDP servers are enabled.
    Pass if relevant services are explicitly disabled.
    Warning when information is incomplete.
    """
    insec = config.settings.get("insecure_services", {})
    enabled_services: List[str] = []

    if insec.get("http_server_enabled"):
        enabled_services.append("HTTP server (ip http server)")
    if insec.get("tcp_small_servers_enabled"):
        enabled_services.append("TCP small servers (service tcp-small-servers)")
    if insec.get("udp_small_servers_enabled"):
        enabled_services.append("UDP small servers (service udp-small-servers)")

    if enabled_services:
        first_ev = (
            config.evidence_map.get("ip_http_server")
            or config.evidence_map.get("service_tcp_small_servers")
            or config.evidence_map.get("service_udp_small_servers")
        )
        return {
            "status": "fail",
            "severity": rule.severity,
            "evidence": first_ev.evidence_text if first_ev else enabled_services[0],
            "evidence_line_range": first_ev.line_range if first_ev else None,
            "message": f"Insecure or obsolete service(s) explicitly enabled: {', '.join(enabled_services)}.",
            "remediation": rule.remediation,
        }

    no_http = config.evidence_map.get("no_ip_http_server")
    no_tcp = config.evidence_map.get("no_service_tcp_small_servers")
    no_udp = config.evidence_map.get("no_service_udp_small_servers")

    if no_http or no_tcp or no_udp:
        ev = no_http or no_tcp or no_udp
        return {
            "status": "pass",
            "severity": rule.severity,
            "evidence": ev.evidence_text if ev else "Insecure services explicitly disabled",
            "evidence_line_range": ev.line_range if ev else None,
            "message": "Insecure services (HTTP server, small TCP/UDP servers, source routing) are explicitly disabled.",
            "remediation": rule.remediation,
        }

    return {
        "status": "warning",
        "severity": rule.severity,
        "evidence": "No explicit service disabling statements found",
        "evidence_line_range": None,
        "message": "Insecure services are neither explicitly enabled nor explicitly disabled in configuration.",
        "remediation": rule.remediation,
    }


def check_net_009_device_identification_banner(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-009: Device Identification and Banner Metadata.

    Pass when hostname and MOTD/login warning banner are properly configured.
    Fail when legal security banners are absent.
    Warning when hostname is missing or ambiguous.
    """
    hostname = config.device_name
    banners = config.settings.get("banners", {})
    motd_configured = banners.get("motd_configured", False)
    login_configured = banners.get("login_configured", False)

    if not hostname:
        return {
            "status": "warning",
            "severity": rule.severity,
            "evidence": "Hostname is missing or not configured",
            "evidence_line_range": None,
            "message": "Device hostname statement is missing in configuration.",
            "remediation": rule.remediation,
        }

    if not motd_configured and not login_configured:
        ev_host = config.evidence_map.get("hostname")
        return {
            "status": "fail",
            "severity": rule.severity,
            "evidence": ev_host.evidence_text if ev_host else f"hostname {hostname}",
            "evidence_line_range": ev_host.line_range if ev_host else None,
            "message": (
                f"Device identification configured (hostname '{hostname}'), "
                "but legal security warning banner (banner motd/login) is missing."
            ),
            "remediation": rule.remediation,
        }

    ev = config.evidence_map.get("banner_motd") or config.evidence_map.get("banner_login")
    return {
        "status": "pass",
        "severity": rule.severity,
        "evidence": ev.evidence_text if ev else f"banner configured on {hostname}",
        "evidence_line_range": ev.line_range if ev else None,
        "message": f"Device identification (hostname '{hostname}') and security warning banner are properly configured.",
        "remediation": rule.remediation,
    }


def check_net_010_plaintext_secrets(config: NormalizedConfig, rule: Rule) -> Dict[str, Any]:
    """NET-010: Obvious Plaintext Secret Detection.

    Fail when obvious plaintext credentials are identified.
    Pass when no plaintext credentials are identified.
    Never exposes raw secrets in evidence or message.
    """
    plaintext_secrets = config.settings.get("plaintext_secrets_found", [])

    if plaintext_secrets:
        first_item = plaintext_secrets[0]
        line_num = first_item.get("line")
        ev_text = "Plaintext credential detected"
        ev_range = str(line_num) if line_num else None

        for v in config.evidence_map.values():
            if v.line_number == line_num:
                ev_text = v.evidence_text
                ev_range = v.line_range
                break

        contexts = ", ".join(p.get("context", "credential") for p in plaintext_secrets)
        return {
            "status": "fail",
            "severity": rule.severity,
            "evidence": ev_text,
            "evidence_line_range": ev_range,
            "message": f"Obvious plaintext credentials detected in: {contexts}.",
            "remediation": rule.remediation,
        }

    return {
        "status": "pass",
        "severity": rule.severity,
        "evidence": "No plaintext credentials detected in configuration",
        "evidence_line_range": None,
        "message": "No obvious plaintext credentials identified in configuration.",
        "remediation": rule.remediation,
    }


CHECK_HANDLERS = {
    "NET-001": check_net_001_telnet_disabled,
    "NET-002": check_net_002_ssh_enabled,
    "NET-003": check_net_003_password_encryption,
    "NET-004": check_net_004_login_failure_protection,
    "NET-005": check_net_005_system_logging,
    "NET-006": check_net_006_trusted_time_source,
    "NET-007": check_net_007_admin_access_list,
    "NET-008": check_net_008_insecure_services,
    "NET-009": check_net_009_device_identification_banner,
    "NET-010": check_net_010_plaintext_secrets,
}


def check_rule(rule_id: str, config: NormalizedConfig) -> Dict[str, Any]:
    """Dispatch evaluation to the appropriate deterministic rule check function.

    Returns standard finding dictionary:
    {
        "status": "pass|fail|warning|not_applicable|error",
        "severity": "high|medium|low",
        "evidence": "...",
        "evidence_line_range": "...",
        "message": "...",
        "remediation": "..."
    }
    """
    rule = RULES_BY_ID.get(rule_id)
    if not rule:
        return {
            "status": "error",
            "severity": "medium",
            "evidence": "",
            "evidence_line_range": None,
            "message": f"Rule ID '{rule_id}' not found in rule definitions.",
            "remediation": "",
        }

    handler = CHECK_HANDLERS.get(rule_id)
    if not handler:
        return {
            "status": "warning",
            "severity": rule.severity,
            "evidence": "",
            "evidence_line_range": None,
            "message": f"No check implementation available for rule '{rule_id}'.",
            "remediation": rule.remediation,
        }

    try:
        return handler(config, rule)
    except Exception as exc:
        return {
            "status": "error",
            "severity": rule.severity,
            "evidence": "",
            "evidence_line_range": None,
            "message": f"Error executing check for rule '{rule_id}': {str(exc)}",
            "remediation": rule.remediation,
        }
