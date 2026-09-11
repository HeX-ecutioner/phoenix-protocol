"""Tests for configuration parser contract (scaffolding)."""

from app.models.normalized_config import NormalizedConfig
from app.parsers.cisco_like import CiscoLikeParser, parse_cisco_like


def test_parser_signature_and_return_type():
    """Verify parse_cisco_like adheres to function contract."""
    sample = "hostname TEST-RTR\n"
    res = parse_cisco_like(sample)
    assert isinstance(res, NormalizedConfig)


def test_parser_class_instance():
    """Verify CiscoLikeParser instance contract."""
    parser = CiscoLikeParser()
    res = parser.parse("hostname TEST-RTR\n")
    assert isinstance(res, NormalizedConfig)
