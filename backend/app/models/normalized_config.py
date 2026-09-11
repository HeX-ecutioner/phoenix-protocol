"""Normalized configuration and evidence models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConfigEvidence:
    """Safe configuration snippet and line reference.

    Safely represents:
    - field/property
    - evidence text
    - source line or line range
    Never retains complete raw configuration.
    """

    field_name: str = ""
    evidence_text: str = ""
    line_number: Optional[int] = None
    line_range: Optional[str] = None
    content: Optional[str] = None  # Backward compatibility alias for evidence_text

    def __post_init__(self) -> None:
        if self.content is not None and not self.evidence_text:
            self.evidence_text = self.content
        elif self.evidence_text and self.content is None:
            self.content = self.evidence_text

        if self.line_number is not None and self.line_range is None:
            self.line_range = str(self.line_number)


@dataclass
class NormalizedConfig:
    """Normalized security configuration model extracted from device configurations.

    Adheres to the contract:
    - device_name
    - vendor
    - device_type
    - optional platform/version fields
    - normalized security settings
    - scoped/hierarchical management information where needed
    - source line references
    - parser warnings
    - parser errors
    - never preserves complete raw configuration
    """

    device_name: Optional[str] = None
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    platform: Optional[str] = None
    version: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    management: Dict[str, Any] = field(default_factory=dict)
    evidence_map: Dict[str, ConfigEvidence] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    device_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Synchronize device_metadata with top-level attributes if provided
        if self.device_metadata:
            if not self.device_name and "hostname" in self.device_metadata:
                self.device_name = self.device_metadata["hostname"]
            if not self.vendor and "vendor" in self.device_metadata:
                self.vendor = self.device_metadata["vendor"]
            if not self.device_type and "device_type" in self.device_metadata:
                self.device_type = self.device_metadata["device_type"]
            if not self.version and "version" in self.device_metadata:
                self.version = self.device_metadata["version"]
