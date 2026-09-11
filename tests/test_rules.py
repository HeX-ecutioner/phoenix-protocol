"""Tests for deterministic compliance rules contract (scaffolding)."""

from app.models.normalized_config import NormalizedConfig
from app.rules.definitions import INITIAL_RULES
from app.rules.engine import RuleEngine


def test_initial_rules_catalog_count():
    """Verify initial rule set contains approximately 10 baseline rules."""
    assert len(INITIAL_RULES) == 10
    rule_ids = [r.id for r in INITIAL_RULES]
    assert "NET-001" in rule_ids
    assert "NET-010" in rule_ids


def test_rule_engine_evaluation_contract():
    """Verify rule engine evaluation returns expected RuleResult models."""
    engine = RuleEngine()
    config = NormalizedConfig()
    results = engine.evaluate(config, scan_id="test-scan", device_id="test-device")

    assert len(results) == len(INITIAL_RULES)
    for r in results:
        contract_dict = r.to_contract_dict()
        assert "status" in contract_dict
        assert "severity" in contract_dict
        assert "evidence" in contract_dict
        assert "message" in contract_dict
        assert "remediation" in contract_dict
        assert contract_dict["status"] in {
            "pass",
            "fail",
            "warning",
            "not_applicable",
            "error",
        }
