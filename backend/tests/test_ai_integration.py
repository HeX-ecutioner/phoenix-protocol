"""Comprehensive integration tests for the AI intelligence layer, Dev2 adapter, and remediation.

Covers:
A. Dev2 adapter
B. known mapping lookup
C. unknown mapping
D. approval flow
E. rejected mapping
F. persistence across restart
G. vendor isolation
H. platform isolation
I. AI structured output
J. invalid AI output
K. hallucinated rule ID
L. confidence bounds
M. remediation schema
N. remediation safety
O. AI failure
P. deterministic compliance unaffected by AI failure
Q. secret sanitization
R. end-to-end learning loop
"""

import os
import sqlite3
import tempfile
from typing import Any, Dict

import pydantic
import pytest

from app.agents.audit_bridge import AuditorLearningBridge
from app.agents.explanation import FindingExplainer
from app.agents.knowledge import Dev2KnowledgeProvider, MockKnowledgeProvider
from app.agents.orchestrator import PhoenixAuditorOrchestrator
from app.agents.remediation import RemediationService, heuristic_remediation_generator
from app.agents.schemas import (
    KNOWN_PHOENIX_RULES,
    CommandInterpretation,
    FindingExplanation,
    RemediationSuggestion,
    TeachingProposal,
    UnknownCommand,
)
from app.agents.teach_auditor import TeachAuditorService
from app.services.scanner import run_scan


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing persistence across instances."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        path = tf.name
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


# A. Dev2 Adapter
def test_a_dev2_adapter_initialization():
    """A. Dev2 adapter initializes and connects to isolated SQLite database."""
    provider = Dev2KnowledgeProvider(db_path=":memory:")
    assert provider.service is not None
    assert provider.lookup_command("Cisco", "cisco_ios", "test command") is None
    provider.close()


# B. Known Mapping Lookup
def test_b_known_mapping_lookup():
    """B. Approved mapping in Dev2 service is successfully looked up and converted to CommandInterpretation."""
    provider = Dev2KnowledgeProvider(db_path=":memory:")
    interp = CommandInterpretation(
        command="transport input ssh",
        vendor="Cisco",
        platform="cisco_ios",
        meaning="Enforces SSH management protocol",
        security_control="transport_security",
        mapped_rule_id="NET-001",
        confidence=0.99,
        explanation="Standard baseline setting",
    )
    # Propose then approve
    prop = provider.propose_mapping(interp)
    provider.approve_mapping(prop.id)

    found = provider.lookup_command("Cisco", "cisco_ios", "transport input ssh")
    assert found is not None
    assert isinstance(found, CommandInterpretation)
    assert found.command == "transport input ssh"
    assert found.mapped_rule_id == "NET-001"
    assert found.confidence == 0.99
    provider.close()


# C. Unknown Mapping
def test_c_unknown_mapping():
    """C. Unknown command returns None from knowledge provider and falls through to TeachAuditorService."""
    provider = Dev2KnowledgeProvider(db_path=":memory:")
    service = TeachAuditorService(knowledge_provider=provider)

    unknown = UnknownCommand(
        vendor="Cisco",
        platform="cisco_ios",
        command="logging host 198.51.100.99",
    )
    proposal = service.interpret_command(unknown)
    assert proposal.source == "ai_agent"
    assert proposal.requires_human_approval is True
    assert proposal.interpretation.mapped_rule_id == "NET-005"
    provider.close()


# D. Approval Flow
def test_d_approval_flow():
    """D. Proposed mapping cannot be found until explicitly approved by human auditor."""
    provider = Dev2KnowledgeProvider(db_path=":memory:")
    interp = CommandInterpretation(
        command="no ip http server",
        vendor="Cisco",
        platform="cisco_ios",
        meaning="Disables cleartext HTTP",
        security_control="service_hardening",
        mapped_rule_id="NET-008",
        confidence=0.95,
        explanation="Verified hardening",
    )
    prop = provider.propose_mapping(interp)
    assert prop.approval_status == "proposed"

    # Before approval: lookup MUST return None
    assert provider.lookup_command("Cisco", "cisco_ios", "no ip http server") is None

    # After human approval: lookup returns the mapping
    approved = provider.approve_mapping(prop.id)
    assert approved.approval_status == "approved"

    match = provider.lookup_command("Cisco", "cisco_ios", "no ip http server")
    assert match is not None
    assert match.mapped_rule_id == "NET-008"
    provider.close()


# E. Rejected Mapping
def test_e_rejected_mapping():
    """E. Rejected mapping is preserved for audit history but excluded from lookups."""
    provider = Dev2KnowledgeProvider(db_path=":memory:")
    interp = CommandInterpretation(
        command="snmp-server community [REDACTED]",
        vendor="Cisco",
        platform="cisco_ios",
        meaning="Sets community",
        security_control="snmp",
        mapped_rule_id=None,
        confidence=0.8,
        explanation="Untrusted",
    )
    prop = provider.propose_mapping(interp)
    provider.reject_mapping(prop.id, reason="Security concern")

    # Rejected record must NOT be returned on lookup
    assert provider.lookup_command("Cisco", "cisco_ios", "snmp-server community [REDACTED]") is None
    provider.close()


# F. Persistence Across Restart
def test_f_persistence_across_restart(temp_db_path):
    """F. Approved mappings persist in SQLite and are accessible across distinct service instances."""
    # Instance 1: Create and approve mapping
    p1 = Dev2KnowledgeProvider(db_path=temp_db_path)
    interp = CommandInterpretation(
        command="login block-for 120 attempts 3 within 60",
        vendor="Cisco",
        platform="cisco_ios",
        meaning="Rate-limits login attempts",
        security_control="brute_force_protection",
        mapped_rule_id="NET-004",
        confidence=0.96,
        explanation="Brute force mitigation",
    )
    prop = p1.propose_mapping(interp)
    p1.approve_mapping(prop.id)
    p1.close()

    # Instance 2: New provider instance on same db file should retrieve the approved mapping
    p2 = Dev2KnowledgeProvider(db_path=temp_db_path)
    found = p2.lookup_command("Cisco", "cisco_ios", "login block-for 120 attempts 3 within 60")
    assert found is not None
    assert found.mapped_rule_id == "NET-004"
    p2.close()


# G. Vendor Isolation
def test_g_vendor_isolation():
    """G. Identical command syntax is strictly isolated across different vendors."""
    provider = Dev2KnowledgeProvider(db_path=":memory:")
    cisco_interp = CommandInterpretation(
        command="interface GigabitEthernet0/1",
        vendor="Cisco",
        platform="cisco_ios",
        meaning="Cisco port definition",
        security_control="interface_control",
        mapped_rule_id=None,
        confidence=0.9,
        explanation="Cisco specific",
    )
    prop = provider.propose_mapping(cisco_interp)
    provider.approve_mapping(prop.id)

    # Cisco lookup succeeds
    assert provider.lookup_command("Cisco", "cisco_ios", "interface GigabitEthernet0/1") is not None
    # Juniper lookup for same command returns None
    assert provider.lookup_command("Juniper", "junos", "interface GigabitEthernet0/1") is None
    provider.close()


# H. Platform Isolation
def test_h_platform_isolation():
    """H. Mappings for cisco_ios are isolated from cisco_nxos."""
    provider = Dev2KnowledgeProvider(db_path=":memory:")
    ios_interp = CommandInterpretation(
        command="banner motd ^C Authorized ^C",
        vendor="Cisco",
        platform="cisco_ios",
        meaning="IOS MOTD banner",
        security_control="device_banner",
        mapped_rule_id="NET-009",
        confidence=0.95,
        explanation="IOS specific",
    )
    prop = provider.propose_mapping(ios_interp)
    provider.approve_mapping(prop.id)

    assert provider.lookup_command("Cisco", "cisco_ios", "banner motd ^C Authorized ^C") is not None
    assert provider.lookup_command("Cisco", "cisco_nxos", "banner motd ^C Authorized ^C") is None
    provider.close()


# I. AI Structured Output Validation
def test_i_ai_structured_output():
    """I. CommandInterpretation serializes deterministically and validates fields."""
    interp = CommandInterpretation(
        command="ntp server 198.51.100.123",
        vendor="Cisco",
        platform="cisco_ios",
        meaning="Sets NTP server",
        security_control="time_synchronization",
        mapped_rule_id="NET-006",
        confidence=0.94,
        explanation="Synchronizes clocks",
    )
    d = interp.to_dict()
    assert d["rule_id"] is None if "rule_id" in d else d["mapped_rule_id"] == "NET-006"
    assert d["confidence"] == 0.94
    assert d["security_control"] == "time_synchronization"


# J. Invalid AI Output Handling
def test_j_invalid_ai_output():
    """J. Malformed AI outputs raise ValidationError and fail safely."""
    with pytest.raises(pydantic.ValidationError):
        # Missing required fields
        CommandInterpretation(
            command="test",
            vendor="Cisco",
            platform="cisco_ios",
            meaning="",  # min_length=1
            security_control="",
            confidence=0.5,
            explanation="",
        )


# K. Hallucinated Rule ID Rejection
def test_k_hallucinated_rule_id_rejection():
    """K. Unknown/invented rule IDs like NET-011 or NET-999 are rejected."""
    with pytest.raises(pydantic.ValidationError):
        CommandInterpretation(
            command="test",
            vendor="Cisco",
            platform="cisco_ios",
            meaning="valid meaning",
            security_control="security",
            mapped_rule_id="NET-011",  # Invalid
            confidence=0.9,
            explanation="invalid mapping",
        )

    with pytest.raises(pydantic.ValidationError):
        RemediationSuggestion(
            rule_id="NET-999",  # Invalid
            vendor="Cisco",
            platform="cisco_ios",
            current_state="bad",
            recommended_change="fix",
            example_configuration="snippet",
            explanation="reason",
            risk_if_unfixed="danger",
            confidence=0.9,
        )


# L. Confidence Bounds
def test_l_confidence_bounds():
    """L. Confidence values outside [0.0, 1.0] are strictly rejected."""
    with pytest.raises(pydantic.ValidationError):
        CommandInterpretation(
            command="test",
            vendor="v",
            platform="p",
            meaning="m",
            security_control="s",
            confidence=1.05,
            explanation="e",
        )

    with pytest.raises(pydantic.ValidationError):
        CommandInterpretation(
            command="test",
            vendor="v",
            platform="p",
            meaning="m",
            security_control="s",
            confidence=-0.01,
            explanation="e",
        )


# M. Remediation Schema
def test_m_remediation_schema():
    """M. RemediationSuggestion includes required fields and enforces human approval."""
    rem = heuristic_remediation_generator(rule_id="NET-001", evidence="transport input all")
    assert rem.rule_id == "NET-001"
    assert rem.requires_human_approval is True
    assert "transport input ssh" in rem.recommended_change
    assert 0.0 <= rem.confidence <= 1.0
    d = rem.to_dict()
    assert d["requires_human_approval"] is True


# N. Remediation Safety (Zero Execution)
def test_n_remediation_safety():
    """N. Remediation service produces advisory content only and contains no execution primitives."""
    rem_service = RemediationService()
    # Verify no execution attributes exist on the service
    assert not hasattr(rem_service, "execute")
    assert not hasattr(rem_service, "apply")
    assert not hasattr(rem_service, "deploy")

    suggestion = rem_service.generate_remediation(rule_id="NET-002", evidence="no ip ssh version 2")
    assert suggestion.requires_human_approval is True
    assert isinstance(suggestion, RemediationSuggestion)


# O. AI Failure / Offline Resilience
def test_o_ai_failure_resilience():
    """O. Teach-the-Auditor and Remediation services fall back to deterministic generators when offline."""
    # Prefer ADK runner but simulate missing key
    service = TeachAuditorService(prefer_adk_runner=True)
    unknown = UnknownCommand(vendor="Cisco", platform="cisco_ios", command="ip ssh version 2")
    proposal = service.interpret_command(unknown)
    assert proposal is not None
    assert proposal.interpretation.mapped_rule_id == "NET-002"

    rem_service = RemediationService(prefer_adk_runner=True)
    rem = rem_service.generate_remediation(rule_id="NET-007")
    assert rem is not None
    assert rem.rule_id == "NET-007"


# P. Deterministic Compliance Unaffected by AI
def test_p_deterministic_compliance_unaffected_by_ai():
    """P. Running a compliance scan produces identical scores regardless of AI enhancements."""
    sample_cfg = "hostname CORE-RTR\nservice password-encryption\nno ip http server\nbanner motd ^C AUTH ^C\n"
    res1 = run_scan(
        scan_id="test-p1",
        device_type="cisco_ios",
        uploaded_files=[("router.cfg", sample_cfg)],
    )

    # Enhance scan with orchestrator
    orchestrator = PhoenixAuditorOrchestrator()
    enhanced = orchestrator.enhance_scan_results(res1)

    # Core scores and counts must remain identical
    assert enhanced["compliance_score"] == res1["compliance_score"]
    assert enhanced["summary"] == res1["summary"]
    assert len(enhanced["devices"]) == len(res1["devices"])


# Q. Secret Sanitization in Commands and Remediation
def test_q_secret_sanitization():
    """Q. Plaintext passwords and secrets are sanitized from unknown commands and remediation."""
    unknown = UnknownCommand(
        vendor="Cisco",
        platform="cisco_ios",
        command="enable secret 5 $1$MySecretPassword",
    )
    # Sanitizer replaces secret with [REDACTED]
    assert "$1$MySecretPassword" not in unknown.command
    assert "[REDACTED]" in unknown.command

    # TACACS key sanitization
    tacacs_cmd = UnknownCommand(
        vendor="Cisco",
        platform="cisco_ios",
        command="tacacs-server key 7 VerySecretKey123",
    )
    assert "VerySecretKey123" not in tacacs_cmd.command
    assert "[REDACTED]" in tacacs_cmd.command


# R. End-to-End Learning Loop
def test_r_end_to_end_learning_loop():
    """R. Complete two-stage learning loop: AI proposal -> approval -> cached retrieval."""
    provider = Dev2KnowledgeProvider(db_path=":memory:")
    bridge = AuditorLearningBridge(knowledge_provider=provider)

    demo_result = bridge.demonstrate_learning_loop(
        vendor="Cisco",
        platform="cisco_ios",
        command="ip ssh time-out 60",
        context=["line vty 0 4"],
    )

    # Pass 1 was generated by AI agent and required human approval
    assert demo_result["pass_1"]["source"] == "ai_agent"
    assert demo_result["pass_1"]["requires_human_approval"] is True

    # Approval step succeeded
    assert demo_result["approval_step"]["status"] == "approved"

    # Pass 2 was served from the approved knowledge base without AI
    assert demo_result["pass_2"]["source"] == "knowledge_base"
    assert demo_result["pass_2"]["requires_human_approval"] is False
    assert demo_result["pass_2"]["knowledge_hit"] is True

    provider.close()
