"""Rule evaluation engine."""

from typing import List, Optional
import uuid

from app.models.normalized_config import NormalizedConfig
from app.models.rule import Rule
from app.models.rule_result import RuleResult
from app.rules.checks import check_rule
from app.rules.definitions import INITIAL_RULES


class RuleEngine:
    """Evaluates normalized device configurations against compliance rules."""

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules: List[Rule] = rules if rules is not None else list(INITIAL_RULES)

    def evaluate(
        self,
        config: NormalizedConfig,
        scan_id: str,
        device_id: str,
    ) -> List[RuleResult]:
        """Evaluate configuration against configured compliance rules.

        Returns a list of RuleResult instances adhering to the result contract.
        Guarantees that warning or error states are never silently converted to pass.
        """
        results: List[RuleResult] = []
        for rule in self.rules:
            res_dict = check_rule(rule.id, config)
            results.append(
                RuleResult(
                    id=str(uuid.uuid4()),
                    scan_id=scan_id,
                    device_id=device_id,
                    rule_id=rule.id,
                    status=res_dict.get("status", "error"),
                    severity=res_dict.get("severity", rule.severity),
                    evidence=res_dict.get("evidence", ""),
                    message=res_dict.get("message", ""),
                    remediation=res_dict.get("remediation", rule.remediation_template),
                )
            )
        return results
