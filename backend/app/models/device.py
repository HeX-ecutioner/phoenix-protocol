"""Device model representing an inspected device within a scan."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Device:
    """Represents a network device record created per uploaded file.

    Stores:
    - id
    - scan_id
    - display name
    - vendor
    - device type
    - parse status
    - line count if available
    - safe error message if needed
    - device-level summary/compliance fields
    """

    id: str  # UUID-style text ID
    scan_id: str  # Foreign key to scans
    name: str = ""  # Device identifier or hostname
    display_name: Optional[str] = None
    vendor: Optional[str] = None
    device_type: str = "cisco_ios"
    source_filename: str = ""
    parse_status: str = "success"  # success | partial | failed
    line_count: Optional[int] = None
    error_message: Optional[str] = None
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_rules: int = 0
    not_applicable_rules: int = 0
    error_rules: int = 0
    tested_rule_compliance: float = 0.0
    created_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.display_name is None and self.name:
            self.display_name = self.name
        elif not self.name and self.display_name:
            self.name = self.display_name

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> Dict[str, Any]:
        """Convert device instance to a dictionary."""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "name": self.name,
            "display_name": self.display_name,
            "vendor": self.vendor,
            "device_type": self.device_type,
            "source_filename": self.source_filename,
            "parse_status": self.parse_status,
            "line_count": self.line_count,
            "error_message": self.error_message,
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "warning_rules": self.warning_rules,
            "not_applicable_rules": self.not_applicable_rules,
            "error_rules": self.error_rules,
            "tested_rule_compliance": self.tested_rule_compliance,
            "created_at": self.created_at,
        }
