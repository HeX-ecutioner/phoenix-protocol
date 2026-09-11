"""Tests verifying secret sanitization and direct SQLite row content inspection."""

import pytest
from services.knowledge_service import KnowledgeService
from storage.database import get_connection


@pytest.fixture
def service_and_conn():
    """Returns KnowledgeService and underlying SQLite connection for raw inspection."""
    conn = get_connection(":memory:")
    svc = KnowledgeService(conn=conn)
    yield svc, conn
    svc.close()
    conn.close()


def test_sqlite_raw_contents_secret_redaction(service_and_conn):
    """Test that secret values NEVER survive in persisted SQLite database columns."""
    svc, conn = service_and_conn

    # Specific required test inputs from prompt
    secret_inputs = [
        {
            "command": "username admin password SuperSecret123",
            "secret": "SuperSecret123",
            "control": "local_user_authentication",
        },
        {
            "command": "tacacs-server key MyTacacsSecret",
            "secret": "MyTacacsSecret",
            "control": "tacacs_authentication",
        },
        {
            "command": "radius-server key MyRadiusSecret",
            "secret": "MyRadiusSecret",
            "control": "radius_authentication",
        },
        {
            "command": "snmp-server community MyCommunity",
            "secret": "MyCommunity",
            "control": "snmp_monitoring",
        },
        {
            "command": "authentication token SensitiveTokenValue",
            "secret": "SensitiveTokenValue",
            "control": "token_authentication",
        },
        {
            "command": "enable secret CiscoSecret456",
            "secret": "CiscoSecret456",
            "control": "privileged_mode",
        },
    ]

    for item in secret_inputs:
        svc.propose_mapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern=item["command"],
            meaning=f"Mapping for {item['control']}",
            security_control=item["control"],
        )

    # Directly query SQLite rows at the lowest level
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM knowledge_mappings")
    rows = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]

    assert len(rows) == len(secret_inputs)

    # Exhaustively inspect every cell of every row in SQLite
    for row in rows:
        row_dict = dict(zip(col_names, row))
        all_row_text = " ".join(str(val) for val in row_dict.values())

        # Check that none of the raw secrets exist anywhere in SQLite
        for item in secret_inputs:
            raw_secret = item["secret"]
            assert raw_secret not in all_row_text, (
                f"Security leak detected: Secret '{raw_secret}' was found in SQLite row! "
                f"Row data: {row_dict}"
            )
            assert raw_secret not in row_dict["command_pattern"]
            assert raw_secret not in row_dict["normalized_command"]

        # Confirm that [REDACTED] was inserted instead
        assert "[REDACTED]" in row_dict["command_pattern"]
        assert "[redacted]" in row_dict["normalized_command"].lower()


def test_legitimate_syntax_preservation(service_and_conn):
    """Test that legitimate command syntax is not unnecessarily destroyed or altered."""
    svc, conn = service_and_conn

    legitimate_commands = [
        ("service password-encryption", "password-encryption"),
        ("snmp-server enable traps", "enable traps"),
        ("tacacs-server host 10.1.1.5", "host 10.1.1.5"),
        ("radius-server host 10.1.1.6 auth-port 1812", "auth-port 1812"),
        ("username admin privilege 15", "privilege 15"),
        ("crypto isakmp policy 10", "isakmp policy 10"),
    ]

    for cmd, keyword in legitimate_commands:
        mapping = svc.propose_mapping(
            vendor="Cisco",
            platform="cisco_ios",
            command_pattern=cmd,
            meaning="Legitimate syntax test",
            security_control="general_hardening",
        )
        assert keyword in mapping.command_pattern
        assert keyword in mapping.normalized_command

        # Verify in raw SQLite
        cursor = conn.cursor()
        cursor.execute(
            "SELECT command_pattern, normalized_command FROM knowledge_mappings WHERE id = ?",
            (mapping.id,),
        )
        row = cursor.fetchone()
        assert keyword in row[0]
        assert keyword in row[1]


def test_serialized_responses_and_errors_contain_no_secrets(service_and_conn):
    """Confirm model dictionaries and serialization never expose redacted secrets."""
    svc, _ = service_and_conn

    raw_command = "tacacs-server host 10.2.2.2 key TopSecretP@ss"
    mapping = svc.propose_mapping(
        vendor="Cisco",
        platform="cisco_ios",
        command_pattern=raw_command,
        meaning="Tacacs key definition",
        security_control="tacacs_key",
    )

    mapping_dict = mapping.to_dict()
    assert "TopSecretP@ss" not in str(mapping_dict)
    assert "[REDACTED]" in mapping_dict["command_pattern"]
    assert "[redacted]" in mapping_dict["normalized_command"]
