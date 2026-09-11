from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class Status(str, Enum):
    COMPLIANT = "compliant"
    FAILING = "failing"
    AMBIGUOUS = "ambiguous"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


@dataclass(frozen=True)
class UploadObject:
    original_filename: str
    content: bytes
    content_type: Optional[str]
    size_bytes: int
    sha256: str
    format_hint: Optional[str] = None


@dataclass(frozen=True)
class ScanRequest:
    upload: UploadObject
    requested_rule_ids: Optional[List[str]] = None


@dataclass(frozen=True)
class SourceInfo:
    original_filename: str
    sha256: str
    size_bytes: int
    format: str


@dataclass(frozen=True)
class ParserInfo:
    parser_id: str
    parser_version: str
    normalized_setting_count: int


@dataclass(frozen=True)
class ScanSummary:
    total_rules: int
    tested_rules: int
    compliant: int
    failing: int
    ambiguous: int
    not_applicable: int
    error: int
    warning_count: int
    compliance_percent: Optional[float]
    compliance_basis: str


@dataclass(frozen=True)
class Evidence:
    setting_key: str
    observed_value: Any
    expected_value: Any
    source_line_start: Optional[int]
    source_line_end: Optional[int]
    source_text: Optional[str]
    safe_to_display: bool


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    severity: str
    source_line_start: Optional[int]
    source_line_end: Optional[int]
    field: Optional[str]


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    title: str
    category: str
    severity: str
    status: str
    rationale: str
    evidence: List[Evidence] = field(default_factory=list)
    diagnostics: List[Diagnostic] = field(default_factory=list)


@dataclass(frozen=True)
class ScanResult:
    scan_id: str
    status: str
    source: SourceInfo
    parser: ParserInfo
    summary: Optional[ScanSummary]
    results: List[RuleResult]
    warnings: List[Diagnostic]
    errors: List[Diagnostic]
    created_at: str


@dataclass(frozen=True)
class NormalizedSetting:
    key: str
    value: Optional[Any]
    value_type: str
    source_line_start: Optional[int]
    source_line_end: Optional[int]
    source_text: Optional[str]
    confidence: str
    sensitive: bool
