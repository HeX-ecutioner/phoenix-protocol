"""Deterministic compliance rule evaluation engine."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.models.normalized_config import NormalizedConfig
from app.models.rule import Rule
from app.models.rule_result import RuleResult
from app.rules.checks import check_rule
from app.rules.definitions import INITIAL_RULES

ENGINE_VERSION = "1.0.0"


def evaluate_rule(
    rule: Rule,
    config: NormalizedConfig,
    device_id: Optional[str] = None,
    scan_id: Optional[str] = None,
) -> RuleResult:
    """Evaluate a single compliance rule against a normalized configuration.

    Pure, deterministic evaluation producing a RuleResult instance.
    Does NOT require database access or network calls.
    """
    check_finding = check_rule(rule.rule_id, config)

    now_iso = datetime.now(timezone.utc).isoformat()
    status = check_finding.get("status", "error")
    severity = check_finding.get("severity", rule.severity)
    evidence = check_finding.get("evidence", "")
    evidence_line_range = check_finding.get("evidence_line_range")
    message = check_finding.get("message", "")
    remediation = check_finding.get("remediation", rule.remediation)
    error_message = check_finding.get("error_message") if status == "error" else None

    return RuleResult(
        id=str(uuid.uuid4()),
        device_id=device_id or "",
        scan_id=scan_id,
        rule_id=rule.rule_id,
        status=status,
        severity=severity,
        evidence=evidence,
        evidence_line_range=evidence_line_range,
        message=message,
        remediation=remediation,
        evaluation_timestamp=now_iso,
        engine_version=ENGINE_VERSION,
        error_message=error_message,
    )


def evaluate_all(
    config: NormalizedConfig,
    rules: Optional[List[Rule]] = None,
    device_id: Optional[str] = None,
    scan_id: Optional[str] = None,
) -> List[RuleResult]:
    """Evaluate multiple compliance rules against a normalized configuration."""
    target_rules = rules if rules is not None else list(INITIAL_RULES)
    results: List[RuleResult] = []
    for rule in target_rules:
        results.append(
            evaluate_rule(
                rule=rule,
                config=config,
                device_id=device_id,
                scan_id=scan_id,
            )
        )
    return results


class RuleEngine:
    """Evaluates normalized device configurations against compliance rules."""

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules: List[Rule] = rules if rules is not None else list(INITIAL_RULES)

    def evaluate_rule(
        self,
        rule: Rule,
        config: NormalizedConfig,
        device_id: Optional[str] = None,
        scan_id: Optional[str] = None,
    ) -> RuleResult:
        """Evaluate a single rule."""
        return evaluate_rule(rule, config, device_id=device_id, scan_id=scan_id)

    def evaluate_all(
        self,
        config: NormalizedConfig,
        rules: Optional[List[Rule]] = None,
        device_id: Optional[str] = None,
        scan_id: Optional[str] = None,
    ) -> List[RuleResult]:
        """Evaluate all configured or provided rules."""
        target_rules = rules if rules is not None else self.rules
        return evaluate_all(
            config=config,
            rules=target_rules,
            device_id=device_id,
            scan_id=scan_id,
        )

    def evaluate(
        self,
        config: NormalizedConfig,
        scan_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> List[RuleResult]:
        """Backward-compatible evaluation interface."""
        return self.evaluate_all(
            config=config,
            scan_id=scan_id,
            device_id=device_id,
        )
