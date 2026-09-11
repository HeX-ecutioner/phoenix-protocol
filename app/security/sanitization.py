"""Security and sanitization helpers for configuration processing.

Ensures evidence is sanitized, sensitive secrets (passwords, keys, hashes)
are masked, and complete raw configurations are never retained or logged.
"""

import re

# Regex patterns for masking sensitive configuration credentials and keys
SENSITIVE_PATTERNS = [
    # Matches: (password|secret) <digit(s)> <hash/secret> -> \1 \2 [REDACTED]
    (re.compile(r"\b(password|secret)\s+(\d+)\s+\S+", re.IGNORECASE), r"\1 \2 [REDACTED]"),
    # Matches: (password|secret) <secret without digit> -> \1 [REDACTED]
    (re.compile(r"\b(password|secret)\s+(?!\d+\b)(?!\[REDACTED\])\S+", re.IGNORECASE), r"\1 [REDACTED]"),
    # Matches: snmp-server community <string>
    (re.compile(r"(\bcommunity\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    # Matches: key-string <string>
    (re.compile(r"(\bkey-string\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    # Matches: pre-shared-key [hex|0|6] <key>
    (re.compile(r"(\bpre-shared-key\s+(?:(?:hex|unencrypted|0|6)\s+)?)\S+", re.IGNORECASE), r"\1[REDACTED]"),
]


def sanitize_evidence(line_content: str) -> str:
    """Mask credentials and dangerous secrets from evidence strings."""
    if not line_content:
        return ""
    sanitized = line_content.strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
