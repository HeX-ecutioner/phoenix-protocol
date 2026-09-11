"""Independent test suite for the Teach-the-Auditor intelligence layer (Developer 1).

Tests the schemas, KnowledgeProvider interface, ADK agent tool integration,
confidence boundaries, rule-mapping constraints, and human approval boundaries
without requiring network calls or the full Flask API.
"""

import os
import pydantic
import pytest

from app.agents.knowledge import MockKnowledgeProvider
from app.agents.schemas import (
    KNOWN_PHOENIX_RULES,
    CommandInterpretation,
    TeachingProposal,
    UnknownCommand,
)
from app.agents.teach_auditor import (
    TeachAuditorService,
    build_teach_auditor_agent,
    make_lookup_tool,
)


def test_1_command_with_clear_security_meaning() -> None:
    """1. Test a command with clear security meaning (SSH transport version)."""
    service = TeachAuditorService()
    cmd = UnknownCommand(
        vendor="Cisco",
        platform="IOS",
        command="ip ssh version 2",
        context=["ip domain-name enterprise.internal", "crypto key generate rsa"],
    )

    proposal = service.interpret_command(cmd)
    interp = proposal.interpretation

    assert interp.command == "ip ssh version 2"
    assert interp.mapped_rule_id == "NET-002"
    assert interp.security_control == "transport_security"
    assert interp.confidence >= 0.90
    assert "ssh" in interp.meaning.lower() or "secure shell" in interp.meaning.lower()
    assert proposal.requires_human_approval is True
    assert proposal.source == "ai_agent"


def test_2_command_related_to_management_access() -> None:
    """2. Test a command related to management access filtering (access-class on VTY)."""
    service = TeachAuditorService()
    cmd = UnknownCommand(
        vendor="Cisco",
        platform="IOS",
        command="access-class ADMIN_ACL in",
        context=["line vty 0 4", "transport input ssh"],
    )

    proposal = service.interpret_command(cmd)
    interp = proposal.interpretation

    assert interp.command == "access-class ADMIN_ACL in"
    assert interp.mapped_rule_id == "NET-007"
    assert interp.security_control == "access_control"
    assert interp.confidence >= 0.85
    assert "access" in interp.meaning.lower()
    assert proposal.requires_human_approval is True


def test_3_unfamiliar_synthetic_command() -> None:
    """3. Test a deliberately unfamiliar synthetic command that does not map to baseline rules."""
    service = TeachAuditorService()
    cmd = UnknownCommand(
        vendor="SyntheticVendor",
        platform="NextGenOS",
        command="set forwarding-options packet-capture rate 1000",
        context=["set system host-name EDGE-01"],
    )

    proposal = service.interpret_command(cmd)
    interp = proposal.interpretation

    assert interp.command == "set forwarding-options packet-capture rate 1000"
    # Agent must NOT invent a rule ID when there is no matching baseline rule
    assert interp.mapped_rule_id is None
    assert 0.0 <= interp.confidence <= 1.0
    assert len(interp.explanation) > 0
    assert proposal.requires_human_approval is True


def test_4_garbage_nonsense_input() -> None:
    """4. Test garbage/nonsense input; must produce low confidence and unmapped rule."""
    service = TeachAuditorService()
    cmd = UnknownCommand(
        vendor="Unknown",
        platform="Unknown",
        command="banana banana banana random text 1234",
    )

    proposal = service.interpret_command(cmd)
    interp = proposal.interpretation

    assert interp.mapped_rule_id is None
    # Low confidence on unrecognizable garbage
    assert interp.confidence <= 0.20
    assert interp.security_control == "unclassified"
    assert proposal.requires_human_approval is True


def test_5_known_command_lookup_using_mock_knowledge_provider() -> None:
    """5. Test known command lookup using MockKnowledgeProvider (pre-learned mapping)."""
    kp = MockKnowledgeProvider()
    known = CommandInterpretation(
        command="transport input ssh",
        vendor="Cisco",
        platform="IOS",
        meaning="Restricts terminal management access to SSH only",
        security_control="management_access",
        mapped_rule_id="NET-001",
        confidence=0.99,
        explanation="Previously human-verified mapping in knowledge base",
    )
    kp.add_mapping(known)

    service = TeachAuditorService(knowledge_provider=kp)
    cmd = UnknownCommand(
        vendor="Cisco",
        platform="IOS",
        command="transport input ssh",
    )

    proposal = service.interpret_command(cmd)
    assert proposal.source == "knowledge_base"
    # Known, already approved mappings do NOT require re-approval
    assert proposal.requires_human_approval is False
    assert proposal.interpretation.mapped_rule_id == "NET-001"
    assert proposal.interpretation.confidence == 0.99


def test_6_unknown_command_falling_through_to_ai_interpretation() -> None:
    """6. Unknown command not in knowledge base falls through to AI interpretation."""
    kp = MockKnowledgeProvider()  # Empty knowledge base
    assert kp.count() == 0

    service = TeachAuditorService(knowledge_provider=kp)
    cmd = UnknownCommand(
        vendor="Cisco",
        platform="IOS",
        command="logging host 198.51.100.50",
    )

    proposal = service.interpret_command(cmd)
    assert proposal.source == "ai_agent"
    assert proposal.requires_human_approval is True
    assert proposal.interpretation.mapped_rule_id == "NET-005"
    assert proposal.interpretation.security_control == "logging"


def test_7_structured_output_validation() -> None:
    """7. Verify Pydantic structured output serialization and field completeness."""
    interp = CommandInterpretation(
        command="ntp server 198.51.100.123",
        vendor="Cisco",
        platform="IOS",
        meaning="Configures an authoritative network time server",
        security_control="time_synchronization",
        mapped_rule_id="NET-006",
        confidence=0.95,
        explanation="Points device to an external trusted NTP reference clock",
    )
    d = interp.to_dict()
    assert d["command"] == "ntp server 198.51.100.123"
    assert d["vendor"] == "Cisco"
    assert d["platform"] == "IOS"
    assert d["meaning"] == "Configures an authoritative network time server"
    assert d["security_control"] == "time_synchronization"
    assert d["mapped_rule_id"] == "NET-006"
    assert d["confidence"] == 0.95
    assert "explanation" in d

    proposal = TeachingProposal(interpretation=interp, requires_human_approval=True)
    p_dict = proposal.to_dict()
    assert p_dict["requires_human_approval"] is True
    assert p_dict["source"] == "ai_agent"
    assert p_dict["interpretation"]["mapped_rule_id"] == "NET-006"


def test_8_confidence_bounds_enforced() -> None:
    """8. Confidence must strictly satisfy 0.0 <= confidence <= 1.0."""
    # Negative confidence rejected
    with pytest.raises(pydantic.ValidationError):
        CommandInterpretation(
            command="test",
            vendor="v",
            platform="p",
            meaning="m",
            security_control="s",
            confidence=-0.1,
            explanation="exp",
        )

    # Confidence > 1.0 rejected
    with pytest.raises(pydantic.ValidationError):
        CommandInterpretation(
            command="test",
            vendor="v",
            platform="p",
            meaning="m",
            security_control="s",
            confidence=1.01,
            explanation="exp",
        )

    # Valid boundary values succeed
    c0 = CommandInterpretation(
        command="test",
        vendor="v",
        platform="p",
        meaning="m",
        security_control="s",
        confidence=0.0,
        explanation="exp",
    )
    assert c0.confidence == 0.0

    c1 = CommandInterpretation(
        command="test",
        vendor="v",
        platform="p",
        meaning="m",
        security_control="s",
        confidence=1.0,
        explanation="exp",
    )
    assert c1.confidence == 1.0


def test_9_mapped_rule_id_may_be_null_and_rejects_invented_ids() -> None:
    """9. mapped_rule_id must be optional (null allowed) and reject invented/hallucinated rule IDs."""
    # None is valid and explicitly supported
    valid_null = CommandInterpretation(
        command="set snmp community public",
        vendor="Juniper",
        platform="JunOS",
        meaning="Sets SNMP read-only community string",
        security_control="snmp_monitoring",
        mapped_rule_id=None,
        confidence=0.75,
        explanation="Security control related to network telemetry; not mapped to baseline rules",
    )
    assert valid_null.mapped_rule_id is None

    # Known rule IDs pass validation
    for rule_id in KNOWN_PHOENIX_RULES:
        valid_rule = CommandInterpretation(
            command="cmd",
            vendor="v",
            platform="p",
            meaning="m",
            security_control="s",
            mapped_rule_id=rule_id,
            confidence=0.9,
            explanation="e",
        )
        assert valid_rule.mapped_rule_id == rule_id

    # Invented / hallucinated rule IDs are strictly rejected
    with pytest.raises(pydantic.ValidationError):
        CommandInterpretation(
            command="cmd",
            vendor="v",
            platform="p",
            meaning="m",
            security_control="s",
            mapped_rule_id="INVENTED-999",
            confidence=0.9,
            explanation="e",
        )


def test_10_agent_does_not_make_compliance_decision() -> None:
    """10. Trust boundary: models and service must never produce pass/fail compliance verdicts."""
    interp_fields = CommandInterpretation.model_fields.keys()
    proposal_fields = TeachingProposal.model_fields.keys()

    forbidden_verdict_fields = {"pass", "fail", "status", "compliance_status", "is_compliant"}

    # Ensure no compliance verdict field exists on CommandInterpretation
    assert not forbidden_verdict_fields.intersection(interp_fields)
    # Ensure no compliance verdict field exists on TeachingProposal
    assert not forbidden_verdict_fields.intersection(proposal_fields)

    service = TeachAuditorService()
    cmd = UnknownCommand(vendor="Cisco", platform="IOS", command="transport input ssh")
    proposal = service.interpret_command(cmd)

    # Verify returned dict has no pass/fail verdict
    d = proposal.to_dict()
    assert "status" not in d["interpretation"]
    assert "is_compliant" not in d["interpretation"]
    assert "compliance" not in d["interpretation"]


def test_11_adk_agent_configuration_and_tool_binding() -> None:
    """11. Verify Google ADK Agent initialization, tool binding, and output schema."""
    kp = MockKnowledgeProvider()
    known = CommandInterpretation(
        command="no ip http server",
        vendor="Cisco",
        platform="IOS",
        meaning="Disables plaintext HTTP administration",
        security_control="service_hardening",
        mapped_rule_id="NET-008",
        confidence=0.95,
        explanation="Standard service hardening directive",
    )
    kp.add_mapping(known)

    agent = build_teach_auditor_agent(knowledge_provider=kp, model="gemini-2.0-flash")
    assert agent.name == "teach_auditor_agent"
    assert len(agent.tools) == 1
    assert agent.output_schema == CommandInterpretation

    # Test the lookup tool directly
    lookup_fn = make_lookup_tool(kp)
    found_res = lookup_fn("cisco", "ios", "no ip http server")
    assert found_res["status"] == "found"
    assert found_res["mapped_rule_id"] == "NET-008"

    not_found_res = lookup_fn("cisco", "ios", "unknown command")
    assert not_found_res["status"] == "not_found"


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="Requires GEMINI_API_KEY environment variable for live model test",
)
def test_12_optional_live_adk_agent_smoke() -> None:
    """12. Optional smoke test executing the real ADK agent when GEMINI_API_KEY is available."""
    service = TeachAuditorService(prefer_adk_runner=True)
    cmd = UnknownCommand(
        vendor="Cisco",
        platform="IOS",
        command="transport input ssh",
        context=["line vty 0 4"],
    )
    proposal = service.interpret_command(cmd)
    assert isinstance(proposal, TeachingProposal)
    assert isinstance(proposal.interpretation, CommandInterpretation)
    assert proposal.requires_human_approval is True
    assert 0.0 <= proposal.interpretation.confidence <= 1.0

