"""Risk and Finding Explanation Layer for Phoenix Protocol.

Transforms deterministic rule results and evidence into plain-language security explanations.
Enforces the core principle:
- Curated deterministic rules evaluate compliance (pass/fail) and severity.
- AI explains what the finding means, why it matters, and recommended actions.
- Does NOT mutate deterministic status or compliance scores.
"""

from typing import Any, Dict, Optional

from app.agents.schemas import FindingExplanation, KNOWN_PHOENIX_RULES
from app.security.sanitization import sanitize_evidence

EXPLANATION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "NET-001": {
        "summary": "Cleartext Telnet protocol permitted on administrative VTY management lines.",
        "why_it_matters": "Telnet does not encrypt session traffic. Anyone positioned on the local segment or network transit path can read usernames, passwords, and commands in cleartext.",
        "evidence_explanation": "The line configuration specifies Telnet or allows all protocols, failing the requirement to enforce SSH exclusively.",
        "recommended_action": "Enforce 'transport input ssh' under all line vty blocks to restrict administrative sessions to encrypted SSH.",
    },
    "NET-002": {
        "summary": "SSH version 2 is not enforced for encrypted remote management.",
        "why_it_matters": "SSHv1 contains structural design flaws that permit session hijacking, man-in-the-middle attacks, and insertion of arbitrary commands.",
        "evidence_explanation": "Global configuration lacks 'ip ssh version 2', allowing the device to negotiate insecure legacy protocols.",
        "recommended_action": "Generate a strong RSA key pair (>= 2048 bits) and configure 'ip ssh version 2'.",
    },
    "NET-003": {
        "summary": "Insecure or reversible password storage configured on device.",
        "why_it_matters": "Type 7 passwords use a trivial Vigenère-like cipher that can be instantly decrypted by anyone with read access to the configuration file.",
        "evidence_explanation": "Password strings use weak Type 7 obfuscation or 'service password-encryption' is disabled.",
        "recommended_action": "Enable 'service password-encryption' and migrate all accounts to Type 8 (PBKDF2) or Type 9 (scrypt) hashes.",
    },
    "NET-004": {
        "summary": "Device management lines lack login rate-limiting and lockout protection.",
        "why_it_matters": "Without rate-limiting, attackers can perform automated online dictionary attacks or credential stuffing against management lines without being throttled.",
        "evidence_explanation": "Configuration lacks 'login block-for' directives defining maximum failed attempts within a sliding time window.",
        "recommended_action": "Configure 'login block-for <seconds> attempts <count> within <window>' to lock out consecutive failed login attempts.",
    },
    "NET-005": {
        "summary": "Device is not configured to send security event logs to a remote syslog server.",
        "why_it_matters": "Local logging buffers are volatile and get overwritten when full or wiped upon device reboot. Centralized syslog is required for incident forensics and compliance auditing.",
        "evidence_explanation": "No authoritative 'logging host' directive was detected in the active configuration.",
        "recommended_action": "Configure one or more remote syslog collector IP addresses using 'logging host <ip>' and enable millisecond timestamps.",
    },
    "NET-006": {
        "summary": "Authoritative Network Time Protocol (NTP) synchronization is missing.",
        "why_it_matters": "Unsynchronized system clocks make cross-device log correlation during security incident investigations impossible and can invalidate TLS certificate checks.",
        "evidence_explanation": "No authoritative 'ntp server' reference clock directive was found in the configuration.",
        "recommended_action": "Configure at least two trusted internal NTP servers using 'ntp server <ip>'.",
    },
    "NET-007": {
        "summary": "Administrative VTY management lines lack source IP access-class filtering.",
        "why_it_matters": "Exposing management lines to all IP networks permits any host that can route packets to the device to attempt administrative logins.",
        "evidence_explanation": "Line vty blocks do not include an 'access-class <ACL> in' directive restricting inbound connections.",
        "recommended_action": "Create a dedicated administrative ACL and apply it inbound using 'access-class <ACL> in' under all VTY blocks.",
    },
    "NET-008": {
        "summary": "Insecure or obsolete legacy services are enabled on the network device.",
        "why_it_matters": "Legacy services like HTTP server and small servers introduce unnecessary listening ports, potential denial-of-service vulnerabilities, and cleartext web administration.",
        "evidence_explanation": "Unencrypted 'ip http server' or small servers were detected as active.",
        "recommended_action": "Explicitly disable insecure services using 'no ip http server', 'no service tcp-small-servers', and 'no service udp-small-servers'.",
    },
    "NET-009": {
        "summary": "Mandatory legal warning / identification banner (MOTD or login) is missing.",
        "why_it_matters": "Banners provide legally required notification that access is restricted to authorized personnel only, which is required for legal action against unauthorized access.",
        "evidence_explanation": "Neither 'banner motd' nor 'banner login' warning text was configured.",
        "recommended_action": "Configure a standard MOTD banner warning that unauthorized access is prohibited and activities are monitored.",
    },
    "NET-010": {
        "summary": "Plaintext or unhashed credentials detected in configuration.",
        "why_it_matters": "Plaintext passwords can be read directly by anyone who views the running-config, configuration backups, or TFTP transit traffic.",
        "evidence_explanation": "One or more passwords or enable secrets are stored without cryptographic hashing.",
        "recommended_action": "Remove all plaintext password directives and replace them with salted cryptographic secrets ('secret 9').",
    },
}


class FindingExplainer:
    """Explains deterministic findings using plain language security context."""

    def explain(
        self,
        rule_id: str,
        severity: str,
        evidence: str = "",
        vendor: str = "Cisco",
        platform: str = "cisco_ios",
    ) -> FindingExplanation:
        """Generate a FindingExplanation for a given rule result."""
        clean_rule = rule_id.strip().upper()
        if clean_rule not in KNOWN_PHOENIX_RULES:
            clean_rule = "NET-001"

        clean_evidence = sanitize_evidence(evidence) if evidence else ""

        template = EXPLANATION_TEMPLATES.get(
            clean_rule,
            {
                "summary": f"Configuration violates security control {clean_rule}.",
                "why_it_matters": "Non-compliant network device configurations increase overall attack surface and vulnerability to exploitation.",
                "evidence_explanation": f"Evidence: {clean_evidence}" if clean_evidence else "No specific evidence snippet provided.",
                "recommended_action": "Review device configuration against baseline security standard.",
            },
        )

        ev_text = template.get("evidence_explanation", "")
        if clean_evidence:
            ev_text = f"{ev_text} (Evidence: {clean_evidence})"

        return FindingExplanation(
            rule_id=clean_rule,
            severity=severity,
            summary=template["summary"],
            why_it_matters=template["why_it_matters"],
            evidence_explanation=ev_text,
            recommended_action=template["recommended_action"],
            confidence=0.95,
        )
