"""Remediation Agent for Phoenix Protocol.

Generates structured, vendor-specific remediation recommendations for deterministic findings.
Enforces strict trust and safety boundaries:
- Remediation is strictly ADVISORY.
- ZERO automatic execution (no subprocess, no os.system, no SSH, no paramiko).
- Mandatory human review required (requires_human_approval = True).
- Curated reference to existing Phoenix rules only (no invented rule IDs).
- Sensitive credentials/secrets are never reproduced.
"""

import os
from typing import Any, Callable, Dict, Optional

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents.schemas import KNOWN_PHOENIX_RULES, RemediationSuggestion
from app.security.sanitization import sanitize_evidence

REMEDIATION_AGENT_INSTRUCTION = """You are the Remediation Agent of Phoenix Protocol.

Your job is to provide actionable, vendor-specific configuration remediation guidance for
failed network compliance audit findings.

For each finding:
1. Explain WHAT is currently wrong with the configuration.
2. Recommend the EXACT vendor-specific configuration commands needed to correct the issue.
3. Provide an example configuration snippet illustrating the fix.
4. Explain WHY the change is necessary from a security perspective.
5. Detail the residual RISK if left unaddressed.
6. Provide an interpretation confidence score (0.0 to 1.0).

STRICT SAFETY RULES:
- You are strictly ADVISORY.
- Never execute commands or pretend to deploy changes.
- Never invent rule IDs. Only reference valid Phoenix rules (NET-001 through NET-010).
- Never include sensitive credentials, cleartext passwords, or private keys in recommendations.
- Set requires_human_approval to True.
"""

# Curated catalog of vendor-specific remediation templates for baseline rules
BASELINE_REMEDIATIONS: Dict[str, Dict[str, Any]] = {
    "NET-001": {
        "current_state": "Telnet administrative protocol is permitted or enabled on management lines.",
        "recommended_change": "Configure 'transport input ssh' under all line vty blocks to disallow cleartext Telnet.",
        "example_configuration": "line vty 0 4\n transport input ssh\nline vty 5 15\n transport input ssh",
        "explanation": "Telnet transmits authentication credentials and commands in unencrypted plaintext across the network.",
        "risk_if_unfixed": "Adversaries sniffing network traffic can intercept administrative credentials and gain full device control.",
        "confidence": 0.98,
    },
    "NET-002": {
        "current_state": "SSH version 2 is either not enforced or legacy SSH version 1 is permitted.",
        "recommended_change": "Enforce 'ip ssh version 2' and verify an RSA key pair of at least 2048 bits is generated.",
        "example_configuration": "ip domain-name enterprise.internal\ncrypto key generate rsa modulus 2048\nip ssh version 2",
        "explanation": "SSH version 1 suffers from known cryptographic vulnerabilities including session-hijacking and MITM flaws.",
        "risk_if_unfixed": "Attackers can intercept or downgrade SSH sessions, decrypting administrative management sessions.",
        "confidence": 0.98,
    },
    "NET-003": {
        "current_state": "Reversible Type 7 or unencrypted passwords exist, or global password encryption is disabled.",
        "recommended_change": "Enable 'service password-encryption' and migrate passwords to robust cryptographic hashes (e.g. secret type 8/9).",
        "example_configuration": "service password-encryption\nenable secret 9 [REDACTED_SCRYPT_HASH]",
        "explanation": "Type 7 passwords use weak XOR obfuscation easily decodable in milliseconds by offline cracking utilities.",
        "risk_if_unfixed": "Anyone with read access to backup configurations or logs can instantly recover privileged passwords.",
        "confidence": 0.95,
    },
    "NET-004": {
        "current_state": "Login brute-force rate limiting and lockout protection is missing.",
        "recommended_change": "Configure 'login block-for <seconds> attempts <count> within <window>'.",
        "example_configuration": "login block-for 120 attempts 3 within 60\nlogin quiet-mode access-class ADMIN_ALLOW",
        "explanation": "Without login rate limiting, network management interfaces can be targeted with automated credential-stuffing attacks.",
        "risk_if_unfixed": "Automated online dictionary attacks against administrative lines can compromise device accounts.",
        "confidence": 0.95,
    },
    "NET-005": {
        "current_state": "Centralized remote syslog logging is not configured.",
        "recommended_change": "Specify authoritative remote syslog servers using 'logging host <ip>' and enable timestamps.",
        "example_configuration": "logging host 198.51.100.50\nlogging trap informational\nservice timestamps log datetime msec",
        "explanation": "Local buffers are volatile and easily overwritten; centralized logging guarantees non-repudiation and auditability.",
        "risk_if_unfixed": "Security incidents cannot be investigated or audited if the device is rebooted or local logs wrap around.",
        "confidence": 0.95,
    },
    "NET-006": {
        "current_state": "Authoritative NTP network time servers are not configured.",
        "recommended_change": "Configure reliable NTP reference clocks using 'ntp server <ip>'.",
        "example_configuration": "ntp server 198.51.100.123\nntp server 198.51.100.124",
        "explanation": "Accurate, synchronized system clocks are essential for correlating security events and digital forensics across systems.",
        "risk_if_unfixed": "Inaccurate timestamps invalidate security logs during incident investigation and break cryptographic certificate validation.",
        "confidence": 0.95,
    },
    "NET-007": {
        "current_state": "Management lines (VTY) lack administrative source access filtering via access-class.",
        "recommended_change": "Apply an access-list restricting inbound administrative connections to authorized subnets.",
        "example_configuration": "ip access-list standard MGMT_ACL\n permit 198.51.100.0 0.0.0.255\n deny any log\nline vty 0 4\n access-class MGMT_ACL in",
        "explanation": "Exposing VTY lines to arbitrary networks allows any reachable host to attempt authentication.",
        "risk_if_unfixed": "Unauthorized network segments can access management ports, increasing attack surface for credential attacks.",
        "confidence": 0.95,
    },
    "NET-008": {
        "current_state": "Insecure legacy services (e.g. unencrypted HTTP server, small servers) are enabled.",
        "recommended_change": "Explicitly disable insecure services using 'no ip http server' and 'no service tcp-small-servers'.",
        "example_configuration": "no ip http server\nno service tcp-small-servers\nno service udp-small-servers",
        "explanation": "Legacy services transmit credentials and data in cleartext or present historical denial-of-service attack vectors.",
        "risk_if_unfixed": "Eavesdropping and resource exhaustion exploits targeting obsolete protocol daemons.",
        "confidence": 0.95,
    },
    "NET-009": {
        "current_state": "Mandatory legal warning / identification banner (MOTD or login) is absent or inadequate.",
        "recommended_change": "Configure a legally compliant MOTD warning banner explicitly stating authorized access only.",
        "example_configuration": "banner motd ^C\n=======================================================\nAUTHORIZED ACCESS ONLY. ALL ACTIVITIES ARE MONITORED.\n=======================================================^C",
        "explanation": "Legal advisory banners establish clear boundaries of authorized use required for prosecution and policy enforcement.",
        "risk_if_unfixed": "Potential legal difficulty taking administrative or law enforcement action against unauthorized intruders.",
        "confidence": 0.92,
    },
    "NET-010": {
        "current_state": "Cleartext/unhashed passwords or secrets are configured on the device.",
        "recommended_change": "Replace all plaintext passwords and enable secrets with cryptographic hashes (secret type 8/9 or scrypt).",
        "example_configuration": "no username admin password\nusername admin secret 9 [REDACTED_HASH]\nno enable password\nenable secret 9 [REDACTED_HASH]",
        "explanation": "Plaintext credentials in running-config allow anyone with read access to view passwords directly.",
        "risk_if_unfixed": "Immediate administrative compromise upon unauthorized config view, backup leak, or TFTP interception.",
        "confidence": 0.98,
    },
}


def heuristic_remediation_generator(
    rule_id: str,
    vendor: str = "Cisco",
    platform: str = "cisco_ios",
    evidence: str = "",
    severity: str = "medium",
) -> RemediationSuggestion:
    """Generate structured, deterministic remediation suggestion without calling external LLMs."""
    clean_rule = rule_id.strip().upper()
    if clean_rule not in KNOWN_PHOENIX_RULES:
        clean_rule = "NET-001"

    template = BASELINE_REMEDIATIONS.get(
        clean_rule,
        {
            "current_state": f"Device configuration violates security requirement {clean_rule}.",
            "recommended_change": f"Apply hardened vendor configuration conforming to baseline security standard {clean_rule}.",
            "example_configuration": "! Configure baseline security settings\n",
            "explanation": f"Non-compliance with security rule {clean_rule} increases network device vulnerability.",
            "risk_if_unfixed": "Unmitigated security exposure on network device.",
            "confidence": 0.85,
        },
    )

    # Sanitize evidence if provided
    sanitized_ev = sanitize_evidence(evidence) if evidence else ""
    current_state = template["current_state"]
    if sanitized_ev:
        current_state += f" (Evidence: {sanitized_ev})"

    return RemediationSuggestion(
        rule_id=clean_rule,
        vendor=vendor,
        platform=platform,
        current_state=current_state,
        recommended_change=template["recommended_change"],
        example_configuration=template["example_configuration"],
        explanation=template["explanation"],
        risk_if_unfixed=template["risk_if_unfixed"],
        confidence=template["confidence"],
        requires_human_approval=True,
    )


def build_remediation_agent(model: str = "gemini-2.0-flash") -> Agent:
    """Build the single Google ADK Remediation Agent."""
    return Agent(
        name="remediation_agent",
        description="Generates vendor-specific configuration remediation guidance for Phoenix Protocol.",
        model=model,
        instruction=REMEDIATION_AGENT_INSTRUCTION,
        output_schema=RemediationSuggestion,
    )


class RemediationService:
    """Service orchestrating remediation suggestion generation."""

    def __init__(
        self,
        agent: Optional[Agent] = None,
        model: str = "gemini-2.0-flash",
        prefer_adk_runner: bool = False,
    ) -> None:
        self.agent = agent if agent is not None else build_remediation_agent(model=model)
        self.prefer_adk_runner = prefer_adk_runner
        self.model = model

    def generate_remediation(
        self,
        rule_id: str,
        vendor: str = "Cisco",
        platform: str = "cisco_ios",
        evidence: str = "",
        severity: str = "medium",
    ) -> RemediationSuggestion:
        """Produce an advisory remediation suggestion for a failed compliance finding."""
        # Sanitize sensitive strings defensively
        clean_evidence = sanitize_evidence(evidence) if evidence else ""

        # Live ADK execution if API key configured and preferred
        api_key = os.environ.get("GEMINI_API_KEY")
        if self.prefer_adk_runner and api_key:
            try:
                suggestion = self._run_adk_agent(
                    rule_id=rule_id,
                    vendor=vendor,
                    platform=platform,
                    evidence=clean_evidence,
                    severity=severity,
                )
                if suggestion is not None:
                    return suggestion
            except Exception:
                pass

        # Deterministic offline fallback
        return heuristic_remediation_generator(
            rule_id=rule_id,
            vendor=vendor,
            platform=platform,
            evidence=clean_evidence,
            severity=severity,
        )

    def _run_adk_agent(
        self,
        rule_id: str,
        vendor: str,
        platform: str,
        evidence: str,
        severity: str,
    ) -> Optional[RemediationSuggestion]:
        """Execute ADK agent synchronously via InMemoryRunner."""
        import asyncio
        import uuid

        runner = InMemoryRunner(agent=self.agent)
        prompt = (
            f"Provide remediation guidance for compliance finding:\n"
            f"Rule ID: {rule_id}\n"
            f"Vendor: {vendor}\n"
            f"Platform: {platform}\n"
            f"Severity: {severity}\n"
            f"Evidence: {evidence}\n"
        )

        async def _exec() -> Optional[RemediationSuggestion]:
            session_id = str(uuid.uuid4())
            await runner.session_service.create_session(
                app_name=runner.app_name, user_id="phoenix_remediator", session_id=session_id
            )
            msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
            for event in runner.run(
                user_id="phoenix_remediator", session_id=session_id, new_message=msg
            ):
                if event.output and isinstance(event.output, RemediationSuggestion):
                    return event.output
            return None

        return asyncio.run(_exec())
