"""Tests for KnowledgeMapping domain model."""

from models.knowledge_mapping import ApprovalStatus, KnowledgeMapping
import pytest


def test_valid_mapping_creation():
    """Verify standard mapping creation with valid fields."""
    mapping = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="transport input ssh",
        meaning="Enforces SSH management",
        security_control="management_plane_security",
        mapped_rule_id="NET-001",
        confidence=0.95,
    )
    assert mapping.vendor == "Cisco"
    assert mapping.platform == "cisco_ios"
    assert mapping.command_pattern == "transport input ssh"
    assert mapping.normalized_command == "transport input ssh"
    assert mapping.meaning == "Enforces SSH management"
    assert mapping.security_control == "management_plane_security"
    assert mapping.mapped_rule_id == "NET-001"
    assert mapping.confidence == 0.95
    assert mapping.approval_status == ApprovalStatus.PROPOSED.value
    assert mapping.created_at is not None
    assert mapping.updated_at is not None


def test_missing_required_fields_raise_error():
    """Verify validation errors for missing or whitespace-only required fields."""
    with pytest.raises(ValueError, match="vendor"):
        KnowledgeMapping(
            vendor="   ",
            platform="cisco_ios",
            command_pattern="cmd",
            meaning="meaning",
            security_control="sec",
        )

    with pytest.raises(ValueError, match="platform"):
        KnowledgeMapping(
            vendor="Cisco",
            platform="",
            command_pattern="cmd",
            meaning="meaning",
            security_control="sec",
        )

    with pytest.raises(ValueError, match="command_pattern"):
        KnowledgeMapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern="",
            meaning="meaning",
            security_control="sec",
        )

    with pytest.raises(ValueError, match="meaning"):
        KnowledgeMapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern="cmd",
            meaning="  ",
            security_control="sec",
        )

    with pytest.raises(ValueError, match="security_control"):
        KnowledgeMapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern="cmd",
            meaning="meaning",
            security_control="",
        )


def test_confidence_validation_bounds():
    """Verify confidence must be between 0.0 and 1.0."""
    with pytest.raises(ValueError, match="Confidence"):
        KnowledgeMapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern="cmd",
            meaning="meaning",
            security_control="sec",
            confidence=-0.01,
        )

    with pytest.raises(ValueError, match="Confidence"):
        KnowledgeMapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern="cmd",
            meaning="meaning",
            security_control="sec",
            confidence=1.01,
        )

    # Valid bounds
    m0 = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="cmd",
        meaning="meaning",
        security_control="sec",
        confidence=0.0,
    )
    assert m0.confidence == 0.0

    m1 = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="cmd",
        meaning="meaning",
        security_control="sec",
        confidence=1.0,
    )
    assert m1.confidence == 1.0


def test_approval_status_validation():
    """Verify approval status must be proposed, approved, or rejected."""
    with pytest.raises(ValueError, match="Invalid approval_status"):
        KnowledgeMapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern="cmd",
            meaning="meaning",
            security_control="sec",
            approval_status="auto_trusted",
        )

    m = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="cmd",
        meaning="meaning",
        security_control="sec",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    assert m.approval_status == "approved"


def test_mapped_rule_id_format_validation():
    """Verify mapped_rule_id format constraints."""
    with pytest.raises(ValueError, match="Invalid mapped_rule_id"):
        KnowledgeMapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern="cmd",
            meaning="meaning",
            security_control="sec",
            mapped_rule_id="RULE; DROP TABLE;",
        )

    m = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="cmd",
        meaning="meaning",
        security_control="sec",
        mapped_rule_id="NET-007_v2",
    )
    assert m.mapped_rule_id == "NET-007_v2"


def test_serialization_determinism():
    """Verify to_dict and from_dict roundtrip determinism."""
    m = KnowledgeMapping(
        vendor="Juniper",
        platform="junos",
        command_pattern="set system services ssh",
        meaning="Enables SSH daemon",
        security_control="secure_shell",
        mapped_rule_id="NET-002",
        confidence=0.9,
        explanation="Synthetic test",
        approval_status=ApprovalStatus.PROPOSED.value,
    )
    d = m.to_dict()
    assert d["vendor"] == "Juniper"
    assert d["platform"] == "junos"
    assert d["mapped_rule_id"] == "NET-002"

    recreated = KnowledgeMapping.from_dict(d)
    assert recreated == m
    assert recreated.to_dict() == d
