"""Cisco-like configuration parser.

Deterministic, line-by-line configuration parser that extracts security-relevant
settings, preserves source line numbers, sanitizes sensitive evidence,
maintains scoped hierarchical blocks, and reports warnings and errors without
storing complete raw configurations.
"""

from typing import Any, Dict, List, Optional
import re

from app.models.normalized_config import ConfigEvidence, NormalizedConfig
from app.parsers.base import BaseParser
from app.security.sanitization import sanitize_evidence


class BlockList(list):
    """List of scoped configuration blocks supporting iteration, indexing, and range lookup."""

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            # Lookup by exact range string (e.g. "0 4") or hyphenated (e.g. "0-4")
            for block in self:
                brange = block.get("range", "")
                if brange == item or brange.replace(" ", "-") == item or brange.replace(" ", "_") == item:
                    return block
            raise KeyError(f"Block with range '{item}' not found in {self}")
        return super().__getitem__(item)

    def get(self, item: str, default: Any = None) -> Any:
        """Safe lookup by range key."""
        try:
            return self[item]
        except (KeyError, IndexError, TypeError):
            return default


class CiscoLikeParser(BaseParser):
    """Parser targeting Cisco IOS and Cisco-like configuration syntax."""

    def parse(self, config_text: str) -> NormalizedConfig:
        """Parse Cisco-like configuration text into a NormalizedConfig instance."""
        return parse_cisco_like(config_text)


def parse_cisco_like(config_text: str) -> NormalizedConfig:
    """Parse Cisco-like configuration text into a NormalizedConfig instance.

    Contract:
    - Line-by-line processing.
    - Never executes commands.
    - Never stores complete raw configuration.
    - Preserves source line numbers and sanitized evidence.
    - Keeps scoped line blocks (e.g. separate VTY ranges) separate and unflattened.
    - Produces warnings for ambiguous/missing syntax and errors for malformed syntax.
    - 100% deterministic: repeated parses produce identical output.
    """
    if not isinstance(config_text, str):
        raise TypeError(f"config_text must be a str, got {type(config_text).__name__}")

    warnings: List[str] = []
    errors: List[str] = []
    evidence_map: Dict[str, ConfigEvidence] = {}

    if not config_text.strip():
        errors.append("Configuration input is empty")
        return NormalizedConfig(
            vendor="Cisco",
            device_type="cisco_ios",
            errors=errors,
        )

    # State tracking
    device_name: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None

    # Global security settings structure
    settings: Dict[str, Any] = {
        "ssh": {
            "enabled": False,
            "version": None,
            "timeout": None,
            "authentication_retries": None,
            "line_number": None,
        },
        "service_password_encryption": {
            "enabled": False,
            "line_number": None,
        },
        "login_failure_protection": {
            "enabled": False,
            "block_for": None,
            "attempts": None,
            "within": None,
            "line_number": None,
        },
        "logging": {
            "enabled": False,
            "hosts": [],
            "trap_level": None,
            "buffered": None,
            "timestamps_log": False,
            "timestamps_debug": False,
            "line_numbers": [],
        },
        "ntp": {
            "enabled": False,
            "servers": [],
            "peers": [],
            "has_trusted_server": False,
            "line_numbers": [],
        },
        "insecure_services": {
            "http_server_enabled": False,
            "http_secure_server_enabled": False,
            "tcp_small_servers_enabled": False,
            "udp_small_servers_enabled": False,
            "ip_source_route_enabled": True,  # Default on Cisco unless disabled
        },
        "banners": {
            "motd": None,
            "motd_configured": False,
            "motd_line_range": None,
            "login": None,
            "login_configured": False,
            "login_line_range": None,
        },
        "users": [],
        "enable_secret": {
            "configured": False,
            "algorithm_type": None,
            "is_plaintext": False,
            "is_weak": False,
            "line_number": None,
        },
        "enable_password": {
            "configured": False,
            "algorithm_type": None,
            "is_plaintext": False,
            "is_weak": False,
            "line_number": None,
        },
        "plaintext_secrets_found": [],
        "weak_secrets_found": [],
    }

    # Scoped management line blocks
    vty_blocks = BlockList()
    con_blocks = BlockList()
    aux_blocks = BlockList()

    current_line_block: Optional[Dict[str, Any]] = None

    # Banner multiline tracking
    in_banner = False
    banner_type = ""
    banner_delimiter = ""
    banner_start_line = 0
    banner_accumulated_lines: List[str] = []

    lines = config_text.splitlines()

    for line_idx, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip()

        # Handle active multi-line banner
        if in_banner:
            banner_accumulated_lines.append(line)
            if banner_delimiter and banner_delimiter in line:
                # Banner terminated
                in_banner = False
                banner_range = f"{banner_start_line}-{line_idx}"
                sanitized_banner = sanitize_evidence(line)

                if banner_type == "motd":
                    settings["banners"]["motd_configured"] = True
                    settings["banners"]["motd_line_range"] = banner_range
                    settings["banners"]["motd"] = f"Banner MOTD ({banner_range})"
                    evidence_map["banner_motd"] = ConfigEvidence(
                        field_name="banner_motd",
                        evidence_text=f"banner motd {banner_delimiter} ... {banner_delimiter}",
                        line_number=banner_start_line,
                        line_range=banner_range,
                    )
                elif banner_type == "login":
                    settings["banners"]["login_configured"] = True
                    settings["banners"]["login_line_range"] = banner_range
                    settings["banners"]["login"] = f"Banner login ({banner_range})"
                    evidence_map["banner_login"] = ConfigEvidence(
                        field_name="banner_login",
                        evidence_text=f"banner login {banner_delimiter} ... {banner_delimiter}",
                        line_number=banner_start_line,
                        line_range=banner_range,
                    )
            continue

        stripped = line.strip()

        # Ignore comments and blank lines outside of banners
        if not stripped or stripped.startswith("!") or stripped.startswith("#"):
            continue

        if stripped.lower() in ("exit", "end"):
            if current_line_block is not None:
                current_line_block = _close_line_block(
                    current_line_block, line_idx, vty_blocks, con_blocks, aux_blocks
                )
            continue

        # Check for sub-block vs top-level command
        is_indented = len(line) > len(line.lstrip())
        is_line_subcmd = stripped.lower().startswith((
            "transport ", "access-class ", "login", "exec-timeout ", "password "
        ))
        is_top_level = stripped.lower().startswith((
            "line ", "hostname ", "interface ", "ip ", "version ", "service ",
            "banner ", "username ", "enable ", "ntp ", "logging "
        ))

        if (is_indented or is_line_subcmd) and current_line_block is not None and not is_top_level:
            # Subcommand inside an active scoped line block
            _parse_line_subcommand(
                stripped=stripped,
                line_idx=line_idx,
                block=current_line_block,
                settings=settings,
                evidence_map=evidence_map,
                warnings=warnings,
            )
            continue

        # Top-level or unindented command: closes any open line block
        if current_line_block is not None:
            current_line_block = _close_line_block(
                current_line_block, line_idx - 1, vty_blocks, con_blocks, aux_blocks
            )

        # 1. Hostname
        if stripped.lower().startswith("hostname "):
            parts = stripped.split(None, 1)
            if len(parts) == 2 and parts[1].strip():
                device_name = parts[1].strip()
                evidence_map["hostname"] = ConfigEvidence(
                    field_name="hostname",
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            continue

        # 2. Version
        if stripped.lower().startswith("version "):
            parts = stripped.split(None, 1)
            if len(parts) == 2 and parts[1].strip():
                version = parts[1].strip()
                evidence_map["version"] = ConfigEvidence(
                    field_name="version",
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            continue

        # 3. Service password-encryption
        if stripped.lower() == "service password-encryption":
            settings["service_password_encryption"]["enabled"] = True
            settings["service_password_encryption"]["line_number"] = line_idx
            evidence_map["service_password_encryption"] = ConfigEvidence(
                field_name="service_password_encryption",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "no service password-encryption":
            settings["service_password_encryption"]["enabled"] = False
            settings["service_password_encryption"]["line_number"] = line_idx
            warnings.append(
                f"Password encryption is explicitly disabled (no service password-encryption) on line {line_idx}"
            )
            evidence_map["service_password_encryption"] = ConfigEvidence(
                field_name="service_password_encryption",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        # 4. IP SSH commands
        if stripped.lower().startswith("ip ssh "):
            settings["ssh"]["enabled"] = True
            if settings["ssh"]["line_number"] is None:
                settings["ssh"]["line_number"] = line_idx

            ssh_sub = stripped[len("ip ssh ") :].strip()
            if ssh_sub.lower().startswith("version "):
                ver_token = ssh_sub.split()[1]
                settings["ssh"]["version"] = int(ver_token) if ver_token.isdigit() else ver_token
                evidence_map["ip_ssh_version"] = ConfigEvidence(
                    field_name="ip_ssh_version",
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            elif ssh_sub.lower().startswith("time-out "):
                timeout_val = ssh_sub.split()[1]
                if timeout_val.isdigit():
                    settings["ssh"]["timeout"] = int(timeout_val)
                evidence_map["ip_ssh_timeout"] = ConfigEvidence(
                    field_name="ip_ssh_timeout",
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            elif ssh_sub.lower().startswith("authentication-retries "):
                retries_val = ssh_sub.split()[1]
                if retries_val.isdigit():
                    settings["ssh"]["authentication_retries"] = int(retries_val)
                evidence_map["ip_ssh_authentication_retries"] = ConfigEvidence(
                    field_name="ip_ssh_authentication_retries",
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            else:
                evidence_map["ip_ssh"] = ConfigEvidence(
                    field_name="ip_ssh",
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            continue

        # 5. Login block-for brute force protection
        if stripped.lower().startswith("login block-for "):
            match = re.match(
                r"login\s+block-for\s+(\d+)\s+attempts\s+(\d+)\s+within\s+(\d+)",
                stripped,
                re.IGNORECASE,
            )
            if match:
                b_for, att, wit = match.groups()
                settings["login_failure_protection"]["enabled"] = True
                settings["login_failure_protection"]["block_for"] = int(b_for)
                settings["login_failure_protection"]["attempts"] = int(att)
                settings["login_failure_protection"]["within"] = int(wit)
                settings["login_failure_protection"]["line_number"] = line_idx
                evidence_map["login_block_for"] = ConfigEvidence(
                    field_name="login_block_for",
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            else:
                warnings.append(
                    f"Ambiguous or non-standard 'login block-for' syntax on line {line_idx}: {stripped}"
                )
            continue

        # 6. Logging commands
        if stripped.lower().startswith("logging host "):
            parts = stripped.split()
            if len(parts) >= 3:
                host = parts[2]
                settings["logging"]["hosts"].append(host)
                settings["logging"]["enabled"] = True
                settings["logging"]["line_numbers"].append(line_idx)
                evidence_key = f"logging_host_{len(settings['logging']['hosts'])}"
                evidence_map[evidence_key] = ConfigEvidence(
                    field_name=evidence_key,
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            continue

        if stripped.lower().startswith("logging trap "):
            parts = stripped.split()
            if len(parts) >= 3:
                settings["logging"]["trap_level"] = parts[2]
                settings["logging"]["line_numbers"].append(line_idx)
                evidence_map["logging_trap"] = ConfigEvidence(
                    field_name="logging_trap",
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            continue

        if stripped.lower().startswith("logging buffered"):
            parts = stripped.split()
            settings["logging"]["enabled"] = True
            settings["logging"]["line_numbers"].append(line_idx)
            if len(parts) >= 3 and parts[2].isdigit():
                settings["logging"]["buffered"] = int(parts[2])
            else:
                settings["logging"]["buffered"] = True
            evidence_map["logging_buffered"] = ConfigEvidence(
                field_name="logging_buffered",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower().startswith("service timestamps log "):
            settings["logging"]["timestamps_log"] = True
            evidence_map["service_timestamps_log"] = ConfigEvidence(
                field_name="service_timestamps_log",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower().startswith("service timestamps debug "):
            settings["logging"]["timestamps_debug"] = True
            evidence_map["service_timestamps_debug"] = ConfigEvidence(
                field_name="service_timestamps_debug",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        # 7. NTP commands
        if stripped.lower().startswith("ntp server "):
            parts = stripped.split()
            if len(parts) >= 3:
                server = parts[2]
                settings["ntp"]["servers"].append(server)
                settings["ntp"]["enabled"] = True
                settings["ntp"]["has_trusted_server"] = True
                settings["ntp"]["line_numbers"].append(line_idx)
                evidence_key = f"ntp_server_{len(settings['ntp']['servers'])}"
                evidence_map[evidence_key] = ConfigEvidence(
                    field_name=evidence_key,
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            continue

        if stripped.lower().startswith("ntp peer "):
            parts = stripped.split()
            if len(parts) >= 3:
                peer = parts[2]
                settings["ntp"]["peers"].append(peer)
                settings["ntp"]["enabled"] = True
                settings["ntp"]["line_numbers"].append(line_idx)
                evidence_key = f"ntp_peer_{len(settings['ntp']['peers'])}"
                evidence_map[evidence_key] = ConfigEvidence(
                    field_name=evidence_key,
                    evidence_text=stripped,
                    line_number=line_idx,
                )
            continue

        # 8. Insecure Services & Service Hardening
        if stripped.lower() == "ip http server":
            settings["insecure_services"]["http_server_enabled"] = True
            evidence_map["ip_http_server"] = ConfigEvidence(
                field_name="ip_http_server",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "no ip http server":
            settings["insecure_services"]["http_server_enabled"] = False
            evidence_map["no_ip_http_server"] = ConfigEvidence(
                field_name="no_ip_http_server",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "ip http secure-server":
            settings["insecure_services"]["http_secure_server_enabled"] = True
            evidence_map["ip_http_secure_server"] = ConfigEvidence(
                field_name="ip_http_secure_server",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "no ip http secure-server":
            settings["insecure_services"]["http_secure_server_enabled"] = False
            evidence_map["no_ip_http_secure_server"] = ConfigEvidence(
                field_name="no_ip_http_secure_server",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "service tcp-small-servers":
            settings["insecure_services"]["tcp_small_servers_enabled"] = True
            evidence_map["service_tcp_small_servers"] = ConfigEvidence(
                field_name="service_tcp_small_servers",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "no service tcp-small-servers":
            settings["insecure_services"]["tcp_small_servers_enabled"] = False
            evidence_map["no_service_tcp_small_servers"] = ConfigEvidence(
                field_name="no_service_tcp_small_servers",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "service udp-small-servers":
            settings["insecure_services"]["udp_small_servers_enabled"] = True
            evidence_map["service_udp_small_servers"] = ConfigEvidence(
                field_name="service_udp_small_servers",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "no service udp-small-servers":
            settings["insecure_services"]["udp_small_servers_enabled"] = False
            evidence_map["no_service_udp_small_servers"] = ConfigEvidence(
                field_name="no_service_udp_small_servers",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        if stripped.lower() == "no ip source-route":
            settings["insecure_services"]["ip_source_route_enabled"] = False
            evidence_map["no_ip_source_route"] = ConfigEvidence(
                field_name="no_ip_source_route",
                evidence_text=stripped,
                line_number=line_idx,
            )
            continue

        # 9. Banners
        if stripped.lower().startswith("banner motd ") or stripped.lower().startswith("banner login "):
            b_type = "motd" if "banner motd" in stripped.lower() else "login"
            after_cmd = stripped[len(f"banner {b_type}") :].strip()
            if after_cmd:
                delim = after_cmd[0]
                remainder = after_cmd[1:]
                if delim in remainder:
                    # Single-line banner
                    settings["banners"][f"{b_type}_configured"] = True
                    settings["banners"][f"{b_type}_line_range"] = str(line_idx)
                    settings["banners"][b_type] = f"Banner {b_type.upper()} ({line_idx})"
                    evidence_map[f"banner_{b_type}"] = ConfigEvidence(
                        field_name=f"banner_{b_type}",
                        evidence_text=sanitize_evidence(stripped),
                        line_number=line_idx,
                        line_range=str(line_idx),
                    )
                else:
                    # Multi-line banner begins
                    in_banner = True
                    banner_type = b_type
                    banner_delimiter = delim
                    banner_start_line = line_idx
                    banner_accumulated_lines = [stripped]
            continue

        # 10. User accounts & passwords
        if stripped.lower().startswith("username "):
            _parse_username_command(
                stripped=stripped,
                line_idx=line_idx,
                settings=settings,
                evidence_map=evidence_map,
                warnings=warnings,
            )
            continue

        # 11. Enable secret
        if stripped.lower().startswith("enable secret"):
            _parse_enable_secret(
                stripped=stripped,
                line_idx=line_idx,
                settings=settings,
                evidence_map=evidence_map,
            )
            continue

        # 12. Enable password
        if stripped.lower().startswith("enable password"):
            _parse_enable_password(
                stripped=stripped,
                line_idx=line_idx,
                settings=settings,
                evidence_map=evidence_map,
                warnings=warnings,
            )
            continue

        # 13. Line configuration blocks
        if stripped.lower().startswith("line vty ") or stripped.lower().startswith("line con ") or stripped.lower().startswith("line aux "):
            parts = stripped.split()
            l_type = parts[1].lower()
            if l_type == "console":
                l_type = "con"
            r_str = " ".join(parts[2:]) if len(parts) >= 3 else "0"

            current_line_block = {
                "line_type": l_type,
                "range": r_str,
                "start_line": line_idx,
                "end_line": line_idx,
                "transport_input": [],
                "transport_output": None,
                "ssh_enabled": False,
                "telnet_enabled": False,
                "ssh_only": False,
                "access_class": None,
                "access_class_direction": None,
                "access_class_line": None,
                "login_mode": None,
                "login_line": None,
                "exec_timeout": None,
                "password_configured": False,
                "password_type": None,
            }
            continue

    # Close any unclosed line block at EOF
    if current_line_block is not None:
        _close_line_block(current_line_block, len(lines), vty_blocks, con_blocks, aux_blocks)

    # Check for unclosed banner at EOF
    if in_banner:
        errors.append(f"Unclosed banner {banner_type} delimiter starting at line {banner_start_line}")

    # Post-parsing audits and warnings
    if not device_name:
        warnings.append("Missing hostname statement in configuration")

    # Check NTP configuration
    if settings["ntp"]["peers"] and not settings["ntp"]["servers"]:
        peer_str = ", ".join(settings["ntp"]["peers"])
        warnings.append(
            f"NTP peer configured ({peer_str}), but no authoritative 'ntp server' statement found"
        )

    # Check logging configuration
    if settings["logging"]["buffered"] and not settings["logging"]["hosts"]:
        warnings.append(
            "Local logging buffer configured, but no remote syslog host specified"
        )

    # Check VTY range completeness
    if vty_blocks:
        ranges = [b["range"] for b in vty_blocks]
        if "0 4" in ranges and not any("5" in r for r in ranges):
            warnings.append(
                "VTY lines partially configured: vty 0 4 found but default upper range (vty 5 15) is missing"
            )

    # Compile hierarchical management dictionary
    management: Dict[str, Any] = {
        "vty": vty_blocks,
        "vty_blocks": vty_blocks,
        "console": con_blocks,
        "aux": aux_blocks,
        "lines": {
            "vty": vty_blocks,
            "console": con_blocks,
            "aux": aux_blocks,
        },
    }

    # Compile device metadata
    device_metadata: Dict[str, Any] = {
        "hostname": device_name,
        "vendor": "Cisco",
        "device_type": "cisco_ios",
        "platform": platform,
        "version": version,
    }

    return NormalizedConfig(
        device_name=device_name,
        vendor="Cisco",
        device_type="cisco_ios",
        platform=platform,
        version=version,
        settings=settings,
        management=management,
        evidence_map=evidence_map,
        warnings=warnings,
        errors=errors,
        device_metadata=device_metadata,
    )


def _close_line_block(
    block: Dict[str, Any],
    end_line: int,
    vty_blocks: BlockList,
    con_blocks: BlockList,
    aux_blocks: BlockList,
) -> None:
    """Close an active line block and store it in the corresponding BlockList."""
    block["end_line"] = max(block["start_line"], end_line)
    l_type = block.get("line_type")
    if l_type == "vty":
        vty_blocks.append(block)
    elif l_type == "con":
        con_blocks.append(block)
    elif l_type == "aux":
        aux_blocks.append(block)
    return None


def _parse_line_subcommand(
    stripped: str,
    line_idx: int,
    block: Dict[str, Any],
    settings: Dict[str, Any],
    evidence_map: Dict[str, ConfigEvidence],
    warnings: List[str],
) -> None:
    """Parse a subcommand belonging to a scoped management line block."""
    l_type = block.get("line_type", "line")
    range_slug = block.get("range", "").replace(" ", "_")

    # 1. Transport input
    if stripped.lower().startswith("transport input"):
        tokens = [t.lower() for t in stripped.split()[2:]]
        block["transport_input"] = tokens

        if "all" in tokens:
            block["ssh_enabled"] = True
            block["telnet_enabled"] = True
            block["ssh_only"] = False
            warnings.append(
                f"Ambiguous transport input 'all' on line {l_type} {block.get('range')} at line {line_idx} (permits insecure Telnet)"
            )
        elif "none" in tokens:
            block["ssh_enabled"] = False
            block["telnet_enabled"] = False
            block["ssh_only"] = False
        else:
            block["ssh_enabled"] = "ssh" in tokens
            block["telnet_enabled"] = "telnet" in tokens
            block["ssh_only"] = block["ssh_enabled"] and not block["telnet_enabled"]

        evidence_key = f"{l_type}_{range_slug}_transport"
        evidence_map[evidence_key] = ConfigEvidence(
            field_name=evidence_key,
            evidence_text=stripped,
            line_number=line_idx,
        )
        return

    # 2. Access-class
    if stripped.lower().startswith("access-class "):
        parts = stripped.split()
        if len(parts) >= 2:
            acl_name = parts[1]
            direction = parts[2].lower() if len(parts) >= 3 else "in"
            block["access_class"] = acl_name
            block["access_class_direction"] = direction
            block["access_class_line"] = line_idx

            evidence_key = f"{l_type}_{range_slug}_access_class"
            evidence_map[evidence_key] = ConfigEvidence(
                field_name=evidence_key,
                evidence_text=stripped,
                line_number=line_idx,
            )
        return

    # 3. Login modes
    if stripped.lower().startswith("login"):
        if "local" in stripped.lower():
            block["login_mode"] = "local"
        else:
            block["login_mode"] = "login"
        block["login_line"] = line_idx
        return

    if stripped.lower() == "no login":
        block["login_mode"] = "none"
        block["login_line"] = line_idx
        warnings.append(
            f"Authentication disabled ('no login') on line {l_type} {block.get('range')} at line {line_idx}"
        )
        return

    # 4. Exec-timeout
    if stripped.lower().startswith("exec-timeout "):
        parts = stripped.split()
        if len(parts) >= 2:
            block["exec_timeout"] = " ".join(parts[1:])
        return

    # 5. Line password
    if stripped.lower().startswith("password "):
        block["password_configured"] = True
        parts = stripped.split()
        if len(parts) >= 3 and parts[1].isdigit():
            algo_type = int(parts[1])
        elif len(parts) >= 2 and not parts[1].isdigit():
            algo_type = 0
        else:
            algo_type = 0

        block["password_type"] = algo_type
        sanitized = sanitize_evidence(stripped)
        evidence_key = f"{l_type}_{range_slug}_password"
        evidence_map[evidence_key] = ConfigEvidence(
            field_name=evidence_key,
            evidence_text=sanitized,
            line_number=line_idx,
        )

        if algo_type == 0:
            settings["plaintext_secrets_found"].append(
                {"context": f"line {l_type} {block.get('range')}", "line": line_idx}
            )
            warnings.append(
                f"Plaintext line password detected on line {l_type} {block.get('range')} at line {line_idx}"
            )
        elif algo_type == 7:
            settings["weak_secrets_found"].append(
                {"context": f"line {l_type} {block.get('range')}", "line": line_idx}
            )
            warnings.append(
                f"Weak reversible Cisco Type 7 password detected on line {l_type} {block.get('range')} at line {line_idx}"
            )
        return


def _parse_username_command(
    stripped: str,
    line_idx: int,
    settings: Dict[str, Any],
    evidence_map: Dict[str, ConfigEvidence],
    warnings: List[str],
) -> None:
    """Parse a global 'username' definition command."""
    parts = stripped.split()
    # username <user> [privilege <lvl>] (secret|password) [<type>] <secret>
    if len(parts) < 3:
        return

    uname = parts[1]
    privilege: Optional[int] = None
    auth_type: str = "password"
    algo_type: Any = None

    idx = 2
    while idx < len(parts):
        token = parts[idx].lower()
        if token == "privilege" and idx + 1 < len(parts):
            if parts[idx + 1].isdigit():
                privilege = int(parts[idx + 1])
            idx += 2
            continue
        elif token in ("secret", "password"):
            auth_type = token
            if idx + 1 < len(parts):
                next_token = parts[idx + 1]
                if next_token.isdigit():
                    algo_type = int(next_token)
                else:
                    algo_type = 0 if auth_type == "password" else 5
            else:
                algo_type = 0 if auth_type == "password" else 5
            break
        idx += 1

    is_plaintext = (auth_type == "password" and algo_type == 0)
    is_weak = (auth_type == "password" and algo_type == 7)

    user_info = {
        "username": uname,
        "privilege": privilege,
        "auth_type": auth_type,
        "algorithm_type": algo_type,
        "is_plaintext": is_plaintext,
        "is_weak": is_weak,
        "line_number": line_idx,
    }
    settings["users"].append(user_info)

    evidence_key = f"username_{uname}"
    evidence_map[evidence_key] = ConfigEvidence(
        field_name=evidence_key,
        evidence_text=sanitize_evidence(stripped),
        line_number=line_idx,
    )

    if is_plaintext:
        settings["plaintext_secrets_found"].append(
            {"context": f"username {uname}", "line": line_idx}
        )
        warnings.append(
            f"Plaintext password detected for user '{uname}' on line {line_idx}"
        )
    elif is_weak:
        settings["weak_secrets_found"].append(
            {"context": f"username {uname}", "line": line_idx}
        )
        warnings.append(
            f"Weak reversible Cisco Type 7 password detected for user '{uname}' on line {line_idx}"
        )


def _parse_enable_secret(
    stripped: str,
    line_idx: int,
    settings: Dict[str, Any],
    evidence_map: Dict[str, ConfigEvidence],
) -> None:
    """Parse 'enable secret' global command."""
    parts = stripped.split()
    algo_type: Any = 5
    if len(parts) >= 4 and parts[2].isdigit():
        algo_type = int(parts[2])

    settings["enable_secret"] = {
        "configured": True,
        "algorithm_type": algo_type,
        "is_plaintext": False,
        "is_weak": False,
        "line_number": line_idx,
    }
    evidence_map["enable_secret"] = ConfigEvidence(
        field_name="enable_secret",
        evidence_text=sanitize_evidence(stripped),
        line_number=line_idx,
    )


def _parse_enable_password(
    stripped: str,
    line_idx: int,
    settings: Dict[str, Any],
    evidence_map: Dict[str, ConfigEvidence],
    warnings: List[str],
) -> None:
    """Parse 'enable password' global command."""
    parts = stripped.split()
    algo_type: Any = 0
    if len(parts) >= 4 and parts[2].isdigit():
        algo_type = int(parts[2])

    is_plaintext = (algo_type == 0)
    is_weak = (algo_type == 7)

    settings["enable_password"] = {
        "configured": True,
        "algorithm_type": algo_type,
        "is_plaintext": is_plaintext,
        "is_weak": is_weak,
        "line_number": line_idx,
    }
    evidence_map["enable_password"] = ConfigEvidence(
        field_name="enable_password",
        evidence_text=sanitize_evidence(stripped),
        line_number=line_idx,
    )

    if is_plaintext:
        settings["plaintext_secrets_found"].append(
            {"context": "enable password", "line": line_idx}
        )
        warnings.append(
            f"Plaintext enable password detected on line {line_idx}"
        )
    elif is_weak:
        settings["weak_secrets_found"].append(
            {"context": "enable password", "line": line_idx}
        )
        warnings.append(
            f"Weak reversible Cisco Type 7 enable password detected on line {line_idx}"
        )
