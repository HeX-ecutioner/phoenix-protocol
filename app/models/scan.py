"""Scan model representing a scan execution record."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Scan:
    """Represents a compliance scan record in persistence.

    Stores:
    - id
    - created_at
    - completed_at
    - device_type
    - status
    - parser_version
    - rule_set_version
    - summary counts (total, passed, failed, warning, not_applicable, error)
    - tested_rule_compliance
    """

    id: str  # UUID-style text ID
    device_type: str = "cisco_ios"
    status: str = "pending"  # pending | running | completed | failed
    parser_version: str = "1.0.0"
    rule_set_version: str = "1.0.0"
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_rules: int = 0
    not_applicable_rules: int = 0
    error_rules: int = 0
    tested_rule_compliance: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    compliance_score: Optional[float] = None  # Backward compatibility alias

    def __post_init__(self) -> None:
        if self.compliance_score is not None and self.tested_rule_compliance == 0.0:
            self.tested_rule_compliance = self.compliance_score
        else:
            self.compliance_score = self.tested_rule_compliance

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> Dict[str, Any]:
        """Convert scan instance to a dictionary."""
        return {
            "id": self.id,
            "device_type": self.device_type,
            "status": self.status,
            "parser_version": self.parser_version,
            "rule_set_version": self.rule_set_version,
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "warning_rules": self.warning_rules,
            "not_applicable_rules": self.not_applicable_rules,
            "error_rules": self.error_rules,
            "tested_rule_compliance": self.tested_rule_compliance,
            "compliance_score": self.compliance_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }
