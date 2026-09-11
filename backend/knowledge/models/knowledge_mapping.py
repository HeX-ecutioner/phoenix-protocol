"""Knowledge mapping domain model for Teach the Auditor knowledge layer."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, Optional
import uuid


class ApprovalStatus(str, Enum):
    """Explicit approval states for Teach the Auditor knowledge mappings."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


ALLOWED_APPROVAL_STATUSES = {s.value for s in ApprovalStatus}
RULE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,50}$")


@dataclass
class KnowledgeMapping:
    """Represents a learned or proposed command meaning mapping.

    Stores:
    - id: Unique mapping identifier (UUID)
    - vendor: Target device vendor (e.g. Cisco, Juniper, Fortinet, Palo Alto)
    - platform: Target operating system / platform (e.g. cisco_ios, junos, fortios, panos)
    - command_pattern: Original synthetic or extracted command syntax
    - normalized_command: Canonical, whitespace/case-normalized command string for lookup
    - meaning: Human-readable interpretation of what the command does
    - security_control: Canonical security capability or control tag
    - mapped_rule_id: Optional compliance rule identifier associated with this control (e.g. NET-007)
    - explanation: Contextual explanation of the security impact
    - confidence: Confidence score for the interpretation (0.0 - 1.0)
    - source: Provenance of proposal (e.g. human, ai_agent)
    - approval_status: Current lifecycle state (proposed | approved | rejected)
    - created_at: Timezone-aware UTC timestamp of creation
    - updated_at: Timezone-aware UTC timestamp of last modification
    - version: Schema version
    """

    vendor: str
    platform: str
    command_pattern: str
    meaning: str
    security_control: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    normalized_command: str = ""
    mapped_rule_id: Optional[str] = None
    explanation: str = ""
    confidence: float = 1.0
    source: str = "human"
    approval_status: str = ApprovalStatus.PROPOSED.value
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        now_utc = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now_utc
        if not self.updated_at:
            self.updated_at = self.created_at

        # Validate required fields
        if not self.vendor or not self.vendor.strip():
            raise ValueError("Field 'vendor' must be a non-empty string.")
        if not self.platform or not self.platform.strip():
            raise ValueError("Field 'platform' must be a non-empty string.")
        if not self.command_pattern or not self.command_pattern.strip():
            raise ValueError("Field 'command_pattern' must be a non-empty string.")
        if not self.meaning or not self.meaning.strip():
            raise ValueError("Field 'meaning' must be a non-empty string.")
        if not self.security_control or not self.security_control.strip():
            raise ValueError("Field 'security_control' must be a non-empty string.")

        # Default normalized_command if not pre-populated
        if not self.normalized_command:
            self.normalized_command = " ".join(self.command_pattern.strip().split())

        # Validate confidence range
        if not isinstance(self.confidence, (int, float)) or not (
            0.0 <= float(self.confidence) <= 1.0
        ):
            raise ValueError(
                f"Confidence must be a float between 0.0 and 1.0 inclusive, got {self.confidence}."
            )
        self.confidence = float(self.confidence)

        # Validate approval status
        if self.approval_status not in ALLOWED_APPROVAL_STATUSES:
            raise ValueError(
                f"Invalid approval_status '{self.approval_status}'. Allowed: {sorted(ALLOWED_APPROVAL_STATUSES)}."
            )

        # Validate mapped_rule_id format if provided
        if self.mapped_rule_id is not None:
            clean_rule_id = self.mapped_rule_id.strip()
            if clean_rule_id and not RULE_ID_PATTERN.match(clean_rule_id):
                raise ValueError(
                    f"Invalid mapped_rule_id '{self.mapped_rule_id}'. Must be alphanumeric with hyphens/underscores (2-50 chars)."
                )
            self.mapped_rule_id = clean_rule_id if clean_rule_id else None

        # Validate timestamp formats if present
        for ts_field, ts_val in [
            ("created_at", self.created_at),
            ("updated_at", self.updated_at),
        ]:
            if ts_val:
                try:
                    datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                except ValueError as e:
                    raise ValueError(
                        f"Invalid timestamp format for '{ts_field}': {ts_val}. Error: {e}"
                    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert mapping model to a deterministic dictionary."""
        return {
            "id": self.id,
            "vendor": self.vendor,
            "platform": self.platform,
            "command_pattern": self.command_pattern,
            "normalized_command": self.normalized_command,
            "meaning": self.meaning,
            "security_control": self.security_control,
            "mapped_rule_id": self.mapped_rule_id,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "source": self.source,
            "approval_status": self.approval_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeMapping":
        """Recreate mapping model from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            vendor=data["vendor"],
            platform=data["platform"],
            command_pattern=data["command_pattern"],
            normalized_command=data.get("normalized_command", ""),
            meaning=data["meaning"],
            security_control=data["security_control"],
            mapped_rule_id=data.get("mapped_rule_id"),
            explanation=data.get("explanation", ""),
            confidence=float(data.get("confidence", 1.0)),
            source=data.get("source", "human"),
            approval_status=data.get("approval_status", ApprovalStatus.PROPOSED.value),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            version=data.get("version", "1.0.0"),
        )
