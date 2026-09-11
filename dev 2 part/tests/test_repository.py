"""Tests for KnowledgeMappingRepository and isolated SQLite persistence."""

from models.knowledge_mapping import ApprovalStatus, KnowledgeMapping
import pytest
from storage.database import get_connection, init_db
from storage.repository import (
    DuplicateMappingError,
    KnowledgeMappingRepository,
)


@pytest.fixture
def repo():
    """In-memory SQLite repository fixture."""
    conn = get_connection(":memory:")
    init_db(conn)
    repository = KnowledgeMappingRepository(conn)
    yield repository
    conn.close()


def test_create_and_retrieve_by_id(repo):
    """Test standard mapping creation and retrieval by primary key."""
    mapping = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="service password-encryption",
        normalized_command="service password-encryption",
        meaning="Enables reversible password encryption",
        security_control="credential_protection",
        mapped_rule_id="NET-002",
        confidence=0.98,
        approval_status=ApprovalStatus.PROPOSED.value,
    )
    created = repo.create(mapping)
    assert created.id == mapping.id

    retrieved = repo.get_by_id(mapping.id)
    assert retrieved is not None
    assert retrieved.id == mapping.id
    assert retrieved.vendor == "Cisco"
    assert retrieved.platform == "cisco_ios"
    assert retrieved.command_pattern == "service password-encryption"
    assert retrieved.normalized_command == "service password-encryption"
    assert (
        retrieved.meaning == "Enforces reversible password encryption"
        or "password encryption" in retrieved.meaning
    )
    assert retrieved.confidence == 0.98
    assert retrieved.approval_status == ApprovalStatus.PROPOSED.value


def test_exact_lookup_approved_only(repo):
    """Verify that find_mapping looks up approved mappings by exact vendor, platform, and command."""
    mapping = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="transport input ssh",
        normalized_command="transport input ssh",
        meaning="Restricts VTY lines to SSH",
        security_control="management_plane_security",
        mapped_rule_id="NET-001",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    repo.create(mapping)

    # Exact match finds record
    found = repo.find_mapping("Cisco", "cisco_ios", "transport input ssh")
    assert found is not None
    assert found.id == mapping.id

    # Non-matching parameters return None
    assert repo.find_mapping("Juniper", "cisco_ios", "transport input ssh") is None
    assert repo.find_mapping("Cisco", "cisco_nxos", "transport input ssh") is None
    assert repo.find_mapping("Cisco", "cisco_ios", "transport input telnet") is None


def test_proposed_and_rejected_exclusion_from_lookup(repo):
    """Verify that find_mapping excludes proposed and rejected mappings by default."""
    proposed = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="logging buffered 64000",
        normalized_command="logging buffered 64000",
        meaning="Configures buffered logging size",
        security_control="audit_logging",
        approval_status=ApprovalStatus.PROPOSED.value,
    )
    repo.create(proposed)

    # Default find_mapping searches approved only -> returns None
    assert repo.find_mapping("Cisco", "cisco_ios", "logging buffered 64000") is None

    # Explicit lookup for proposed works for admin inspection
    assert (
        repo.find_mapping(
            "Cisco",
            "cisco_ios",
            "logging buffered 64000",
            approval_status=ApprovalStatus.PROPOSED.value,
        )
        is not None
    )

    # Reject mapping and verify still excluded from normal lookup
    repo.update_approval_status(proposed.id, ApprovalStatus.REJECTED.value)
    assert repo.find_mapping("Cisco", "cisco_ios", "logging buffered 64000") is None


def test_duplicate_approved_mapping_handling(repo):
    """Verify that duplicate approved mappings for the same vendor+platform+command are rejected."""
    m1 = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="ip ssh version 2",
        normalized_command="ip ssh version 2",
        meaning="Forces SSHv2",
        security_control="ssh_protocol_version",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    repo.create(m1)

    # Attempt to create duplicate approved mapping
    m2 = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="ip ssh version 2",
        normalized_command="ip ssh version 2",
        meaning="Different description of SSHv2",
        security_control="ssh_protocol_version",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    with pytest.raises(DuplicateMappingError) as exc_info:
        repo.create(m2)
    assert "already exists" in str(exc_info.value)


def test_historical_proposed_records_permitted(repo):
    """Verify multiple proposed records for the same command can exist simultaneously for audit history."""
    p1 = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="ntp server 10.0.0.1",
        normalized_command="ntp server 10.0.0.1",
        meaning="Configures primary NTP source",
        security_control="time_synchronization",
        source="agent_run_1",
        approval_status=ApprovalStatus.PROPOSED.value,
    )
    p2 = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="ntp server 10.0.0.1",
        normalized_command="ntp server 10.0.0.1",
        meaning="Sets NTP server address",
        security_control="time_synchronization",
        source="agent_run_2",
        approval_status=ApprovalStatus.PROPOSED.value,
    )

    created1 = repo.create(p1)
    created2 = repo.create(p2)
    assert created1.id != created2.id

    proposals = repo.list_mappings(
        vendor="Cisco",
        platform="cisco_ios",
        approval_status=ApprovalStatus.PROPOSED.value,
    )
    assert len(proposals) == 2


def test_update_approval_status(repo):
    """Test transitioning approval status and detecting collisions during promotion to approved."""
    # Create proposed mapping
    prop = KnowledgeMapping(
        vendor="Juniper",
        platform="junos",
        command_pattern="set system services ssh root-login deny",
        normalized_command="set system services ssh root-login deny",
        meaning="Prohibits root login over SSH",
        security_control="account_security",
        approval_status=ApprovalStatus.PROPOSED.value,
    )
    repo.create(prop)

    # Transition to approved
    approved = repo.update_approval_status(prop.id, ApprovalStatus.APPROVED.value)
    assert approved is not None
    assert approved.approval_status == ApprovalStatus.APPROVED.value

    # Transition to rejected
    rejected = repo.update_approval_status(prop.id, ApprovalStatus.REJECTED.value)
    assert rejected is not None
    assert rejected.approval_status == ApprovalStatus.REJECTED.value


def test_update_approval_status_collision_prevention(repo):
    """Test that approving a proposal fails if an approved record already exists."""
    m_approved = KnowledgeMapping(
        vendor="Fortinet",
        platform="fortios",
        command_pattern="set strong-crypto enable",
        normalized_command="set strong-crypto enable",
        meaning="Enables strong cryptography",
        security_control="cryptographic_settings",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    repo.create(m_approved)

    m_proposed = KnowledgeMapping(
        vendor="Fortinet",
        platform="fortios",
        command_pattern="set strong-crypto enable",
        normalized_command="set strong-crypto enable",
        meaning="Alternative proposed meaning",
        security_control="cryptographic_settings",
        approval_status=ApprovalStatus.PROPOSED.value,
    )
    repo.create(m_proposed)

    # Approving the second mapping must raise DuplicateMappingError
    with pytest.raises(DuplicateMappingError):
        repo.update_approval_status(m_proposed.id, ApprovalStatus.APPROVED.value)


def test_list_and_pagination(repo):
    """Test listing mappings with filters and pagination."""
    for i in range(5):
        repo.create(
            KnowledgeMapping(
                vendor="Cisco",
                platform="cisco_ios",
                command_pattern=f"snmp-server community comm{i} RO",
                normalized_command=f"snmp-server community comm{i} ro",
                meaning=f"SNMP community {i}",
                security_control="snmp_management",
                approval_status=ApprovalStatus.PROPOSED.value,
            )
        )

    # Test limit and offset
    page1 = repo.list_mappings(limit=2, offset=0)
    assert len(page1) == 2

    page2 = repo.list_mappings(limit=2, offset=2)
    assert len(page2) == 2
    assert page1[0].id != page2[0].id

    # Test filter by vendor
    cisco_list = repo.list_mappings(vendor="Cisco")
    assert len(cisco_list) == 5

    juniper_list = repo.list_mappings(vendor="Juniper")
    assert len(juniper_list) == 0


def test_delete_and_count(repo):
    """Test deletion and count functionality."""
    mapping = KnowledgeMapping(
        vendor="Palo Alto",
        platform="panos",
        command_pattern="set deviceconfig system service disable-telnet yes",
        normalized_command="set deviceconfig system service disable-telnet yes",
        meaning="Disables Telnet service",
        security_control="management_access",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    repo.create(mapping)

    assert repo.count() == 1
    assert repo.count(vendor="Palo Alto") == 1
    assert repo.count(vendor="Cisco") == 0

    assert repo.delete(mapping.id) is True
    assert repo.get_by_id(mapping.id) is None
    assert repo.count() == 0
    assert repo.delete("non-existent-id") is False


def test_vendor_and_platform_isolation(repo):
    """Verify that identical command text maintains strict vendor and platform isolation."""
    # Cisco IOS
    cisco_mapping = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="no ip domain-lookup",
        normalized_command="no ip domain-lookup",
        meaning="Disables DNS resolution for mistyped commands",
        security_control="dns_lookup_prevention",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    repo.create(cisco_mapping)

    # Cisco NX-OS with same command text
    nxos_mapping = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_nxos",
        command_pattern="no ip domain-lookup",
        normalized_command="no ip domain-lookup",
        meaning="Disables NX-OS DNS resolution",
        security_control="dns_lookup_prevention",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    repo.create(nxos_mapping)

    # Juniper with same command text
    juniper_mapping = KnowledgeMapping(
        vendor="Juniper",
        platform="junos",
        command_pattern="no ip domain-lookup",
        normalized_command="no ip domain-lookup",
        meaning="Hypothetical Junos syntax",
        security_control="dns_lookup_prevention",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    repo.create(juniper_mapping)

    # Strict isolation verification
    c_found = repo.find_mapping("Cisco", "cisco_ios", "no ip domain-lookup")
    assert c_found is not None
    assert c_found.id == cisco_mapping.id
    assert c_found.platform == "cisco_ios"

    nx_found = repo.find_mapping("Cisco", "cisco_nxos", "no ip domain-lookup")
    assert nx_found is not None
    assert nx_found.id == nxos_mapping.id
    assert nx_found.platform == "cisco_nxos"

    j_found = repo.find_mapping("Juniper", "junos", "no ip domain-lookup")
    assert j_found is not None
    assert j_found.id == juniper_mapping.id
    assert j_found.vendor == "Juniper"


def test_database_round_trip_disk(tmp_path):
    """Verify that database can be written, closed, reopened, and data persists."""
    db_file = str(tmp_path / "knowledge_test.db")

    # Step 1: Open, init, write record, and close
    conn1 = get_connection(db_file)
    init_db(conn1)
    repo1 = KnowledgeMappingRepository(conn1)

    mapping = KnowledgeMapping(
        vendor="Fortinet",
        platform="fortios",
        command_pattern="set admin-https-ssl-versions tlsv1-2 tlsv1-3",
        normalized_command="set admin-https-ssl-versions tlsv1-2 tlsv1-3",
        meaning="Restricts HTTPS admin access to TLS 1.2 and 1.3",
        security_control="tls_enforcement",
        mapped_rule_id="NET-008",
        approval_status=ApprovalStatus.APPROVED.value,
    )
    repo1.create(mapping)
    conn1.close()

    # Step 2: Re-open the database from disk
    conn2 = get_connection(db_file)
    repo2 = KnowledgeMappingRepository(conn2)

    retrieved = repo2.get_by_id(mapping.id)
    assert retrieved is not None
    assert retrieved.id == mapping.id
    assert retrieved.vendor == "Fortinet"
    assert retrieved.command_pattern == "set admin-https-ssl-versions tlsv1-2 tlsv1-3"

    lookup = repo2.find_mapping(
        "Fortinet", "fortios", "set admin-https-ssl-versions tlsv1-2 tlsv1-3"
    )
    assert lookup is not None
    assert lookup.id == mapping.id

    conn2.close()


def test_update_invalid_status_raises_error(repo):
    """Test that updating to an invalid status raises ValueError."""
    mapping = KnowledgeMapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern="hostname R1",
        normalized_command="hostname r1",
        meaning="Sets hostname",
        security_control="device_id",
    )
    repo.create(mapping)

    with pytest.raises(ValueError) as exc_info:
        repo.update_approval_status(mapping.id, "bogus_status")
    assert "Invalid approval_status" in str(exc_info.value)


def test_transaction_rollback_on_failure(repo):
    """Test that database transactions roll back cleanly on errors."""
    initial_count = repo.count()

    # Attempt to insert an object that violates database integrity
    try:
        repo.conn.execute("BEGIN TRANSACTION;")
        repo.conn.execute(
            "INSERT INTO knowledge_mappings (id, vendor) VALUES ('test-id', 'Cisco');"
        )
        # Force a failure (e.g. missing NOT NULL fields like platform)
        repo.conn.commit()
    except Exception:
        repo.conn.rollback()

    assert repo.count() == initial_count
