"""Tests for normalization, validation, and secret sanitization routines."""

import pytest

from validation.mapping_validator import (
    ValidationError,
    normalize_command,
    sanitize_secret_command,
    validate_and_prepare_mapping,
    validate_mapping_payload,
)


def test_command_normalization():
    """Verify whitespace stripping, internal run collapsing, and lowercasing."""
    raw = "   IP   SSH   VERSION   2   "
    expected = "ip ssh version 2"
    assert normalize_command(raw) == expected

    tabs_and_newlines = "line\tvty\n\n0   4"
    assert normalize_command(tabs_and_newlines) == "line vty 0 4"


def test_secret_sanitization_patterns():
    """Verify credentials and secret hashes are redacted while command structure remains intact."""
    samples = [
        (
            "username admin password 0 PlaintextPassword123!",
            "username admin password 0 [REDACTED]",
        ),
        (
            "enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7x0",
            "enable secret 5 [REDACTED]",
        ),
        (
            "snmp-server community MySecretCommunityString RO",
            "snmp-server community [REDACTED] RO",
        ),
        (
            "tacacs-server key MyTacacsSecretKey",
            "tacacs-server key [REDACTED]",
        ),
        (
            "radius-server host 10.1.1.1 key 7 0822455D0A16",
            "radius-server host 10.1.1.1 key 7 [REDACTED]",
        ),
        (
            "set system authentication-token SecretToken999",
            "set system authentication-token [REDACTED]",
        ),
    ]

    for raw, expected in samples:
        sanitized = sanitize_secret_command(raw)
        assert sanitized == expected
        assert "PlaintextPassword123!" not in sanitized
        assert "MySecretCommunityString" not in sanitized
        assert "MyTacacsSecretKey" not in sanitized
        assert "0822455D0A16" not in sanitized


def test_non_secret_syntax_preservation():
    """Verify non-secret commands with keywords like 'password-encryption' are not destroyed."""
    assert (
        sanitize_secret_command("service password-encryption")
        == "service password-encryption"
    )
    assert (
        sanitize_secret_command("no service password-encryption")
        == "no service password-encryption"
    )
    assert (
        sanitize_secret_command("login block-for 300 attempts 3 within 60")
        == "login block-for 300 attempts 3 within 60"
    )


def test_validation_payload_missing_fields():
    """Verify validation raises ValidationError on missing fields."""
    with pytest.raises(ValidationError, match="Required field"):
        validate_mapping_payload(
            {
                "vendor": "Cisco",
                "platform": "cisco_ios",
                "command_pattern": "service password-encryption",
                # Missing meaning and security_control
            }
        )


def test_validation_payload_string_length_limits():
    """Verify overlong fields are rejected."""
    payload = {
        "vendor": "Cisco",
        "platform": "cisco_ios",
        "command_pattern": "cmd",
        "meaning": "x" * 1500,  # Exceeds max 1000
        "security_control": "ctrl",
    }
    with pytest.raises(ValidationError, match="exceeds maximum allowed length"):
        validate_mapping_payload(payload)


def test_validate_and_prepare_workflow():
    """Verify complete validate -> normalize -> sanitize workflow."""
    raw_payload = {
        "vendor": "  Cisco  ",
        "platform": "  cisco_ios  ",
        "command_pattern": "   USERNAME admin PASSWORD 0 SecretPlainText123   ",
        "meaning": "  Creates local admin user  ",
        "security_control": "  account_management  ",
        "confidence": 0.95,
        "mapped_rule_id": "NET-010",
    }

    prepared = validate_and_prepare_mapping(raw_payload)

    assert prepared["vendor"] == "Cisco"
    assert prepared["platform"] == "cisco_ios"
    # Command pattern sanitized
    assert prepared["command_pattern"] == "USERNAME admin PASSWORD 0 [REDACTED]"
    # Normalized command normalized and sanitized
    assert prepared["normalized_command"] == "username admin password 0 [redacted]"
    assert prepared["meaning"] == "Creates local admin user"
    assert prepared["security_control"] == "account_management"
    assert prepared["confidence"] == 0.95
    assert prepared["approval_status"] == "proposed"
    assert "SecretPlainText123" not in str(prepared)
