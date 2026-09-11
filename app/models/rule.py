"""Rule definition model."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

ALLOWED_SEVERITIES = {"high", "medium", "low"}


@dataclass
class Rule:
    """Represents a deterministic compliance rule definition.

    Stores:
    - rule_id (stable human-readable rule ID such as NET-001)
    - title
    - description
    - technical_requirement
    - severity (high | medium | low)
    - device_type
    - remediation
    - active flag
    - rule version
    """

    rule_id: str = ""
    title: str = ""
    description: str = ""
    technical_requirement: str = ""
    severity: str = "medium"
    device_type: str = "cisco_ios"
    category: str = "General"
    remediation: str = ""
    active: bool = True
    rule_version: str = "1.0.0"
    id: Optional[str] = None  # Backward compatibility alias for rule_id
    remediation_template: Optional[str] = None  # Backward compatibility alias

    def __post_init__(self) -> None:
        if self.id and not self.rule_id:
            self.rule_id = self.id
        elif self.rule_id and not self.id:
            self.id = self.rule_id

        if self.remediation_template and not self.remediation:
            self.remediation = self.remediation_template
        elif self.remediation and not self.remediation_template:
            self.remediation_template = self.remediation

        if self.severity not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{self.severity}'. Allowed values: {sorted(ALLOWED_SEVERITIES)}"
            )

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule instance to a dictionary."""
        return {
            "rule_id": self.rule_id,
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "technical_requirement": self.technical_requirement,
            "severity": self.severity,
            "device_type": self.device_type,
            "category": self.category,
            "remediation": self.remediation,
            "remediation_template": self.remediation_template,
            "active": self.active,
            "rule_version": self.rule_version,
        }
