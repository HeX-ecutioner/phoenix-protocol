"""Validation, normalization, and sanitization routines for Teach the Auditor."""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from ..models.knowledge_mapping import ALLOWED_APPROVAL_STATUSES, RULE_ID_PATTERN
except ImportError:
    from models.knowledge_mapping import ALLOWED_APPROVAL_STATUSES, RULE_ID_PATTERN


class ValidationError(ValueError):
    """Raised when knowledge mapping payload fails validation checks."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or [message]


# Defensive regex patterns to sanitize secrets in command patterns
SECRET_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # Matches: (password|secret) <digit(s)> <hash/secret> -> \1 \2 [REDACTED]
    (
        re.compile(r"\b(password|secret)\s+(\d+)\s+(?!\[REDACTED\])\S+", re.IGNORECASE),
        r"\1 \2 [REDACTED]",
    ),
    # Matches: (password|secret) <secret string without digit> -> \1 [REDACTED]
    # Negative lookahead ensures we don't clobber 'password-encryption', 'secret [REDACTED]', etc.
    (
        re.compile(
            r"\b(password|secret)\s+(?!\d+\b)(?!-)(?!\[REDACTED\])\S+",
            re.IGNORECASE,
        ),
        r"\1 [REDACTED]",
    ),
    # Matches: community <string>
    (
        re.compile(r"(\bcommunity\s+)(?!\[REDACTED\])\S+", re.IGNORECASE),
        r"\1[REDACTED]",
    ),
    # Matches: key-string <string>
    (
        re.compile(r"(\bkey-string\s+)(?!\[REDACTED\])\S+", re.IGNORECASE),
        r"\1[REDACTED]",
    ),
    # Matches: pre-shared-key [hex|0|6] <key>
    (
        re.compile(
            r"(\bpre-shared-key\s+(?:(?:hex|unencrypted|0|6)\s+)?)(?!\[REDACTED\])\S+",
            re.IGNORECASE,
        ),
        r"\1[REDACTED]",
    ),
    # Matches: (tacacs-server|radius-server) [host <ip>] key [0|7] <key>
    (
        re.compile(
            r"(\b(?:tacacs-server|radius-server)\s+(?:.*?\s+)?key\s+(?:\d+\s+)?)(?!\[REDACTED\])\S+",
            re.IGNORECASE,
        ),
        r"\1[REDACTED]",
    ),
    # Matches: (token|auth-token|api-key) <string>
    (
        re.compile(
            r"(\b(?:token|auth-token|api-key)\s+)(?!\[REDACTED\])\S+",
            re.IGNORECASE,
        ),
        r"\1[REDACTED]",
    ),
]


def normalize_command(command: str) -> str:
    """Deterministically normalize command string for exact lookup.

    Rules:
    1. Trim leading and trailing whitespace.
    2. Collapse internal runs of multiple whitespace characters to single spaces.
    3. Convert to lowercase for case-insensitive vendor matching.
    """
    if not command:
        return ""
    # Collapse multiple whitespace characters
    collapsed = re.sub(r"\s+", " ", command.strip())
    return collapsed.lower()


def sanitize_secret_command(command: str) -> str:
    """Mask credentials and dangerous secrets from command text without destroying syntax."""
    if not command:
        return ""
    sanitized = command.strip()
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def validate_mapping_payload(payload: Dict[str, Any]) -> None:
    """Perform strict structural and field validation on mapping input payload.

    Raises ValidationError if any check fails.
    """
    if not isinstance(payload, dict):
        raise ValidationError("Mapping payload must be a dictionary.")

    errors: List[str] = []

    # Required field presence and non-empty checks
    required_fields = [
        "vendor",
        "platform",
        "command_pattern",
        "meaning",
        "security_control",
    ]
    for req in required_fields:
        val = payload.get(req)
        if val is None or not str(val).strip():
            errors.append(f"Required field '{req}' is missing or empty.")

    # Bounded string lengths
    max_lengths = {
        "vendor": 100,
        "platform": 100,
        "command_pattern": 1000,
        "meaning": 1000,
        "security_control": 200,
        "explanation": 2000,
        "source": 100,
        "version": 50,
    }
    for field_name, max_len in max_lengths.items():
        if field_name in payload and payload[field_name] is not None:
            if len(str(payload[field_name])) > max_len:
                errors.append(
                    f"Field '{field_name}' exceeds maximum allowed length of {max_len} characters."
                )

    # Confidence validation
    if "confidence" in payload and payload["confidence"] is not None:
        conf = payload["confidence"]
        if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
            errors.append(
                f"Field 'confidence' must be a numeric value between 0.0 and 1.0, got: {conf}"
            )

    # Approval status validation
    status = payload.get("approval_status", "proposed")
    if status not in ALLOWED_APPROVAL_STATUSES:
        errors.append(
            f"Invalid approval_status '{status}'. Allowed: {sorted(ALLOWED_APPROVAL_STATUSES)}"
        )

    # Mapped rule ID validation
    mapped_rule = payload.get("mapped_rule_id")
    if mapped_rule:
        clean_rule = str(mapped_rule).strip()
        if not RULE_ID_PATTERN.match(clean_rule):
            errors.append(
                f"Invalid mapped_rule_id format '{mapped_rule}'. Must be alphanumeric with hyphens (2-50 chars)."
            )

    # Timestamp format validation
    for ts_field in ["created_at", "updated_at"]:
        ts_val = payload.get(ts_field)
        if ts_val:
            try:
                datetime.fromisoformat(str(ts_val).replace("Z", "+00:00"))
            except ValueError:
                errors.append(
                    f"Invalid ISO timestamp in field '{ts_field}': '{ts_val}'."
                )

    if errors:
        raise ValidationError(
            f"Validation failed with {len(errors)} error(s): {'; '.join(errors)}",
            errors=errors,
        )


def validate_and_prepare_mapping(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the strict workflow: validate -> normalize -> sanitize -> return clean data."""
    # 1. Validate raw inputs
    validate_mapping_payload(payload)

    # 2. Normalize and sanitize command text
    raw_cmd = str(payload["command_pattern"]).strip()
    sanitized_cmd = sanitize_secret_command(raw_cmd)
    normalized_cmd = normalize_command(sanitized_cmd)

    # 3. Clean string fields
    prepared = dict(payload)
    prepared["vendor"] = str(payload["vendor"]).strip()
    prepared["platform"] = str(payload["platform"]).strip()
    prepared["command_pattern"] = sanitized_cmd
    prepared["normalized_command"] = normalized_cmd
    prepared["meaning"] = str(payload["meaning"]).strip()
    prepared["security_control"] = str(payload["security_control"]).strip()

    if "explanation" in payload and payload["explanation"]:
        prepared["explanation"] = str(payload["explanation"]).strip()
    else:
        prepared["explanation"] = ""

    if "confidence" in payload and payload["confidence"] is not None:
        prepared["confidence"] = float(payload["confidence"])
    else:
        prepared["confidence"] = 1.0

    if "mapped_rule_id" in payload and payload["mapped_rule_id"]:
        prepared["mapped_rule_id"] = str(payload["mapped_rule_id"]).strip()
    else:
        prepared["mapped_rule_id"] = None

    if "source" in payload and payload["source"]:
        prepared["source"] = str(payload["source"]).strip()
    else:
        prepared["source"] = "human"

    if "approval_status" in payload and payload["approval_status"]:
        prepared["approval_status"] = str(payload["approval_status"]).strip()
    else:
        prepared["approval_status"] = "proposed"

    return prepared
