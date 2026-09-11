"""Security and sanitization helpers for configuration processing.

Ensures evidence is sanitized, sensitive secrets (passwords, keys, hashes)
are masked, and complete raw configurations are never retained or logged.
"""

import re

# Patterns for masking sensitive configuration values in evidence
SENSITIVE_PATTERNS = [
    (re.compile(r"(password\s+\d+\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(secret\s+\d+\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(community\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(key-string\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(pre-shared-key\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
]


def sanitize_evidence(line_content: str) -> str:
    """Mask credentials and dangerous content from evidence strings."""
    sanitized = line_content.strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
