"""Deterministic compliance rule check functions.

Each check evaluates a NormalizedConfig and returns evaluation findings.
Contract note:
- Do not silently convert warning/error states into pass.
"""

from typing import Any, Dict

from app.models.normalized_config import NormalizedConfig


def check_rule(rule_id: str, config: NormalizedConfig) -> Dict[str, Any]:
    """Placeholder check dispatch for compliance rules.

    Returns the contract dict:
    {
        "status": "pass|fail|warning|not_applicable|error",
        "severity": "high|medium|low",
        "evidence": "...",
        "message": "...",
        "remediation": "..."
    }
    """
    # Minimal scaffolding placeholder
    return {
        "status": "warning",
        "severity": "medium",
        "evidence": "Placeholder evidence",
        "message": f"Check logic for rule {rule_id} pending implementation.",
        "remediation": "Pending implementation.",
    }
