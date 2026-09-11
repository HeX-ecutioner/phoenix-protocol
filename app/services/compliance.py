"""Compliance scoring and summary calculation helpers."""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Union


@dataclass
class ComplianceSummary:
    """Summary counts and tested-rule compliance score."""

    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_rules: int = 0
    not_applicable_rules: int = 0
    error_rules: int = 0
    tested_rule_compliance: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "warning_rules": self.warning_rules,
            "not_applicable_rules": self.not_applicable_rules,
            "error_rules": self.error_rules,
            "tested_rule_compliance": self.tested_rule_compliance,
        }

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


def calculate_compliance_score(passed: int, failed: int) -> float:
    """Calculate tested-rule compliance percentage: passed / (passed + failed) * 100.

    Excludes warning, not_applicable, and error from denominator.
    Returns 0.0 if no rules were tested (passed + failed == 0).
    Rounds consistently to two decimal places.
    """
    tested = passed + failed
    if tested <= 0:
        return 0.0
    return round((passed / tested) * 100.0, 2)


def calculate_summary(results: Iterable[Any]) -> ComplianceSummary:
    """Calculate compliance summary from an iterable of rule results.

    Supports RuleResult objects, sqlite3.Row, or dictionary mappings.
    Warnings and errors remain separate counts and are never converted to passes.
    """
    total = 0
    passed = 0
    failed = 0
    warning = 0
    not_applicable = 0
    error = 0

    for item in results:
        total += 1
        if isinstance(item, dict):
            status = item.get("status")
        else:
            status = getattr(item, "status", None)
            if status is None and hasattr(item, "__getitem__"):
                try:
                    status = item["status"]
                except (KeyError, TypeError, IndexError):
                    status = None

        if status == "pass":
            passed += 1
        elif status == "fail":
            failed += 1
        elif status == "warning":
            warning += 1
        elif status == "not_applicable":
            not_applicable += 1
        elif status == "error":
            error += 1
        else:
            # Unrecognized status is classified as error
            error += 1

    score = calculate_compliance_score(passed, failed)
    return ComplianceSummary(
        total_rules=total,
        passed_rules=passed,
        failed_rules=failed,
        warning_rules=warning,
        not_applicable_rules=not_applicable,
        error_rules=error,
        tested_rule_compliance=score,
    )


def calculate_device_summary(results: Iterable[Any]) -> ComplianceSummary:
    """Calculate compliance summary for a single device's results."""
    return calculate_summary(results)


def calculate_scan_summary(
    results_or_device_collections: Iterable[Any],
) -> ComplianceSummary:
    """Calculate compliance summary for a scan based on aggregated rule results.

    The scan-level summary must be based on aggregated individual rule results,
    not by averaging device percentages.
    """
    flattened: List[Any] = []
    for item in results_or_device_collections:
        if item is None:
            continue
        # If the item is a collection/list of results from a device, flatten it
        if isinstance(item, (list, tuple, set)):
            flattened.extend(item)
        else:
            flattened.append(item)

    return calculate_summary(flattened)
