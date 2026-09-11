"""Tests for KnowledgeService public integration boundary."""

from models.knowledge_mapping import ApprovalStatus
import pytest
from services.knowledge_service import KnowledgeService
from storage.repository import DuplicateMappingError
from validation.mapping_validator import ValidationError


@pytest.fixture
def service():
    """KnowledgeService with isolated in-memory database."""
    svc = KnowledgeService(db_path=":memory:")
    yield svc
    svc.close()


def test_propose_mapping_defaults_to_proposed(service):
    """Test proposing a command mapping defaults to 'proposed' status and does not appear in lookup."""
    proposal = service.propose_mapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="  ip ssh time-out 60  ",
        meaning="Sets SSH negotiation timeout to 60 seconds",
        security_control="ssh_timeout",
        mapped_rule_id="NET-009",
        confidence=0.92,
        explanation="Synthetic test proposal",
    )

    assert proposal.id is not None
    assert proposal.vendor == "Cisco"
    assert proposal.platform == "cisco_ios"
    assert proposal.approval_status == ApprovalStatus.PROPOSED.value
    assert proposal.normalized_command == "ip ssh time-out 60"
    assert proposal.confidence == 0.92

    # Verification: Lookup MUST return None before approval
    lookup_result = service.lookup_command("Cisco", "cisco_ios", "ip ssh time-out 60")
    assert lookup_result is None


def test_approval_workflow_enables_lookup(service):
    """Test proposal followed by human approval enables exact lookup."""
    proposal = service.propose_mapping(
        vendor="Juniper",
        platform="junos",
        command_pattern="set system login message [BANNER]",
        meaning="Configures unauthorized access warning banner",
        security_control="login_banner",
        mapped_rule_id="NET-010",
        confidence=0.97,
    )

    # Before approval: lookup returns None
    assert (
        service.lookup_command("Juniper", "junos", "set system login message [BANNER]")
        is None
    )

    # Human approval step
    approved = service.approve_mapping(proposal.id)
    assert approved.approval_status == ApprovalStatus.APPROVED.value

    # After approval: lookup succeeds and returns mapping
    retrieved = service.lookup_command(
        "Juniper", "junos", "set system login message [BANNER]"
    )
    assert retrieved is not None
    assert retrieved.id == proposal.id
    assert retrieved.meaning == "Configures unauthorized access warning banner"
    assert retrieved.mapped_rule_id == "NET-010"


def test_rejection_workflow_prevents_lookup(service):
    """Test proposal followed by rejection prevents lookup but preserves audit trail."""
    proposal = service.propose_mapping(
        vendor="Fortinet",
        platform="fortios",
        command_pattern="config system global",
        meaning="Generic system configuration context",
        security_control="system_management",
        confidence=0.40,
    )

    rejected = service.reject_mapping(
        proposal.id, reason="Too broad, does not configure a specific control"
    )
    assert rejected.approval_status == ApprovalStatus.REJECTED.value

    # Lookup returns None
    assert service.lookup_command("Fortinet", "fortios", "config system global") is None

    # Proposal remains in repository for historical inspection
    retrieved = service.repo.get_by_id(proposal.id)
    assert retrieved is not None
    assert retrieved.approval_status == ApprovalStatus.REJECTED.value


def test_lookup_command_normalization(service):
    """Verify that lookup_command normalizes whitespace and case to find approved mappings."""
    proposal = service.propose_mapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="ip http secure-server",
        meaning="Enables secure HTTPS management server",
        security_control="https_management",
        mapped_rule_id="NET-011",
    )
    service.approve_mapping(proposal.id)

    # Various non-canonical lookups should all match
    assert (
        service.lookup_command("Cisco", "cisco_ios", "  ip   http   secure-server  ")
        is not None
    )
    assert (
        service.lookup_command("Cisco", "cisco_ios", "IP HTTP SECURE-SERVER")
        is not None
    )
    assert (
        service.lookup_command("Cisco", "cisco_ios", "\tip http secure-server\n")
        is not None
    )


def test_vendor_and_platform_isolation(service):
    """Verify that lookups require exact vendor and platform matches."""
    proposal = service.propose_mapping(
        vendor="Palo Alto",
        platform="panos",
        command_pattern="set shared log-settings syslog SyslogServer",
        meaning="Configures centralized remote syslog forwarding",
        security_control="remote_syslog",
        mapped_rule_id="NET-012",
    )
    service.approve_mapping(proposal.id)

    cmd = "set shared log-settings syslog SyslogServer"
    # Exact match succeeds
    assert service.lookup_command("Palo Alto", "panos", cmd) is not None

    # Different vendor fails
    assert service.lookup_command("Fortinet", "panos", cmd) is None

    # Different platform fails
    assert service.lookup_command("Palo Alto", "panos_panorama", cmd) is None


def test_validation_failure_on_proposal(service):
    """Test that invalid proposals raise ValidationError and are not persisted."""
    # Missing required fields
    with pytest.raises(ValidationError):
        service.propose_mapping(
            vendor="",
            platform="cisco_ios",
            command_pattern="hostname Router1",
            meaning="Sets device name",
            security_control="device_identity",
        )

    # Invalid confidence score
    with pytest.raises(ValidationError):
        service.propose_mapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern="hostname Router1",
            meaning="Sets device name",
            security_control="device_identity",
            confidence=1.5,
        )


def test_duplicate_approval_prevention(service):
    """Test that two proposals for the same command cannot both be approved."""
    p1 = service.propose_mapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="line vty 0 4",
        meaning="Enters VTY configuration",
        security_control="vty_access",
    )
    p2 = service.propose_mapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="line vty 0 4",
        meaning="Alternative description of VTY",
        security_control="vty_access",
    )

    # First approval succeeds
    service.approve_mapping(p1.id)

    # Second approval fails with DuplicateMappingError
    with pytest.raises(DuplicateMappingError):
        service.approve_mapping(p2.id)


def test_list_approved_knowledge_and_proposals(service):
    """Test listing approved knowledge and pending proposals separately."""
    p1 = service.propose_mapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="enable secret [REDACTED]",
        meaning="Sets encrypted enable password",
        security_control="privileged_access",
    )
    p2 = service.propose_mapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="no service password-recovery",
        meaning="Disables password recovery procedure",
        security_control="physical_security",
    )
    assert p2.id is not None

    # Both are initially proposals
    assert len(service.list_proposals()) == 2
    assert len(service.list_approved_knowledge()) == 0

    # Approve one
    service.approve_mapping(p1.id)

    assert len(service.list_proposals()) == 1
    assert len(service.list_approved_knowledge()) == 1
    assert service.list_approved_knowledge()[0].id == p1.id


def test_service_only_integration_no_direct_sqlite():
    """Demonstrate end-to-end usage through KnowledgeService without direct SQL interaction."""
    # Caller only needs to instantiate service
    svc = KnowledgeService(db_path=":memory:")

    # 1. AI agent proposes mapping
    prop = svc.propose_mapping(
        vendor="Juniper",
        platform="junos",
        command_pattern="set system syslog file messages any notice",
        meaning="Captures system notice messages to log file",
        security_control="audit_logging",
        mapped_rule_id="NET-013",
        confidence=0.95,
        source="adk_agent_mock",
    )
    assert prop.approval_status == "proposed"

    # 2. Scanner lookup before approval finds nothing
    assert (
        svc.lookup_command(
            "Juniper", "junos", "set system syslog file messages any notice"
        )
        is None
    )

    # 3. Auditor approves proposal
    svc.approve_mapping(prop.id)

    # 4. Scanner lookup retrieves approved knowledge
    match = svc.lookup_command(
        "Juniper", "junos", "set system syslog file messages any notice"
    )
    assert match is not None
    assert match.mapped_rule_id == "NET-013"
    assert match.meaning == "Captures system notice messages to log file"

    svc.close()


def test_protocol_and_contract_conformance(service):
    """Verify that KnowledgeService conforms to the KnowledgeServiceInterface protocol."""
    from integration_contract import (
        AgentCommandInterpretation,
        KnowledgeServiceInterface,
    )

    # Verify protocol compliance
    assert isinstance(service, KnowledgeServiceInterface)

    # Verify agent contract helper
    agent_output = AgentCommandInterpretation(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="service timestamps log datetime msec",
        meaning="Enables millisecond timestamps for logging",
        security_control="audit_logging",
        mapped_rule_id="NET-014",
        confidence=0.99,
        explanation="Standard syslog hardening setting",
    )
    payload = agent_output.to_dict()
    assert payload["vendor"] == "Cisco"
    assert payload["mapped_rule_id"] == "NET-014"

    proposal = service.propose_mapping(**payload)
    assert proposal.approval_status == "proposed"
    assert proposal.confidence == 0.99


def test_nonexistent_id_handling(service):
    """Verify that approving or rejecting a nonexistent ID raises a clean ValueError."""
    nonexistent_id = "00000000-0000-0000-0000-000000000000"

    with pytest.raises(ValueError) as exc_approve:
        service.approve_mapping(nonexistent_id)
    assert f"Mapping with ID '{nonexistent_id}' not found." in str(exc_approve.value)

    with pytest.raises(ValueError) as exc_reject:
        service.reject_mapping(nonexistent_id)
    assert f"Mapping with ID '{nonexistent_id}' not found." in str(exc_reject.value)


def test_service_restart_persistence(tmp_path):
    """Verify knowledge persists across service instance destruction and restart."""
    db_file = str(tmp_path / "restart_test.db")

    # Service instance 1: Propose and approve
    svc1 = KnowledgeService(db_path=db_file)
    proposal = svc1.propose_mapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="transport input ssh",
        meaning="Enforces SSH management on terminal lines",
        security_control="management_plane_security",
        mapped_rule_id="NET-001",
        confidence=0.98,
        source="ai_agent",
    )
    svc1.approve_mapping(proposal.id)
    svc1.close()

    # Service instance 2: Re-open the database and lookup
    svc2 = KnowledgeService(db_path=db_file)
    mapping = svc2.lookup_command("Cisco", "cisco_ios", "transport input ssh")

    assert mapping is not None
    assert mapping.id == proposal.id
    assert mapping.mapped_rule_id == "NET-001"
    assert mapping.meaning == "Enforces SSH management on terminal lines"
    assert mapping.approval_status == "approved"

    svc2.close()
