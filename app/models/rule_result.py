"""Rule result model and evaluation contract."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

ALLOWED_STATUSES = {"pass", "fail", "warning", "not_applicable", "error"}
ALLOWED_SEVERITIES = {"high", "medium", "low"}


@dataclass
class RuleResult:
    """Represents a rule evaluation finding for a device.

    Standard Rule Result Contract:
    {
        "status": "pass|fail|warning|not_applicable|error",
        "severity": "high|medium|low",
        "evidence": "...",
        "message": "...",
        "remediation": "..."
    }

    Stores:
    - id
    - device_id
    - rule_id
    - status
    - severity snapshot
    - evidence
    - evidence line range
    - message
    - remediation snapshot
    - evaluation timestamp
    - engine version
    - error message if needed
    - scan_id (optional contextual link)
    """

    id: str  # UUID-style text ID
    device_id: str  # Foreign key to devices
    rule_id: str  # Stable rule ID e.g., NET-001
    status: str  # pass | fail | warning | not_applicable | error
    severity: str  # high | medium | low
    evidence: str = ""
    evidence_line_range: Optional[str] = None
    message: str = ""
    remediation: str = ""
    evaluation_timestamp: Optional[str] = None
    engine_version: str = "1.0.0"
    error_message: Optional[str] = None
    scan_id: Optional[str] = None  # Optional scan-level foreign key / context
    created_at: Optional[str] = None  # Backward compatibility alias

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid status '{self.status}'. Allowed values: {sorted(ALLOWED_STATUSES)}"
            )

        if self.severity not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{self.severity}'. Allowed values: {sorted(ALLOWED_SEVERITIES)}"
            )

        if self.created_at is not None and self.evaluation_timestamp is None:
            self.evaluation_timestamp = self.created_at
        elif self.evaluation_timestamp is not None and self.created_at is None:
            self.created_at = self.evaluation_timestamp

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_contract_dict(self) -> Dict[str, Any]:
        """Convert to the standard rule result contract format."""
        return {
            "status": self.status,
            "severity": self.severity,
            "evidence": self.evidence,
            "message": self.message,
            "remediation": self.remediation,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert result instance to a dictionary."""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "device_id": self.device_id,
            "rule_id": self.rule_id,
            "status": self.status,
            "severity": self.severity,
            "evidence": self.evidence,
            "evidence_line_range": self.evidence_line_range,
            "message": self.message,
            "remediation": self.remediation,
            "evaluation_timestamp": self.evaluation_timestamp,
            "created_at": self.created_at,
            "engine_version": self.engine_version,
            "error_message": self.error_message,
        }
