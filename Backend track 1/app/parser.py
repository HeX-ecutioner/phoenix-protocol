import re
from typing import Any, List, Tuple

from app.models import Diagnostic, NormalizedSetting


class ParserException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class GenericKeyValueParser:
    PARSER_ID = "generic-kv-parser"
    PARSER_VERSION = "1.0.0"

    def __init__(self):
        # We define a few settings that should be considered sensitive
        self.sensitive_keys = {
            "authentication.password",
            "authentication.secret",
            "network.ssh.private_key",
        }

    def _parse_value(self, raw_value: str) -> Tuple[Any, str]:
        # Normalize boolean
        lower_val = raw_value.lower()
        if lower_val in ["true", "yes", "enabled", "on"]:
            return True, "boolean"
        if lower_val in ["false", "no", "disabled", "off"]:
            return False, "boolean"

        # Normalize integer
        if re.match(r"^-?\d+$", raw_value):
            return int(raw_value), "integer"

        # Normalize list (comma separated)
        if "," in raw_value:
            return [v.strip() for v in raw_value.split(",")], "list"

        return raw_value, "string"

    def parse(self, content: bytes) -> Tuple[List[NormalizedSetting], List[Diagnostic]]:
        if not content:
            raise ParserException("EMPTY_INPUT")

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise ParserException("UNSUPPORTED_FORMAT")

        lines = text.splitlines()

        settings: List[NormalizedSetting] = []
        diagnostics: List[Diagnostic] = []
        seen_keys = set()

        for idx, line in enumerate(lines):
            line_num = idx + 1
            stripped = line.strip()

            # Ignore comments and blank lines
            if not stripped or stripped.startswith("#"):
                continue

            # Expect key = value or key : value
            match = re.match(r"^([\w.-]+)\s*[:=]\s*(.*)$", stripped)
            if not match:
                # Also support just "key value"
                match = re.match(r"^([\w.-]+)\s+(.*)$", stripped)

            if not match:
                diagnostics.append(
                    Diagnostic(
                        code="MALFORMED_LINE",
                        message="Line does not match key-value format",
                        severity="warning",
                        source_line_start=line_num,
                        source_line_end=line_num,
                        field=None,
                    )
                )
                continue

            key = match.group(1).lower()
            raw_value = match.group(2).strip()

            if key in seen_keys:
                diagnostics.append(
                    Diagnostic(
                        code="CONFLICTING_VALUE",
                        message=f"Duplicate key '{key}' found",
                        severity="warning",
                        source_line_start=line_num,
                        source_line_end=line_num,
                        field=key,
                    )
                )
                # Remove the original setting to produce ambiguity
                settings = [s for s in settings if s.key != key]
                continue

            seen_keys.add(key)

            parsed_val, val_type = self._parse_value(raw_value)

            is_sensitive = key in self.sensitive_keys

            settings.append(
                NormalizedSetting(
                    key=key,
                    value=parsed_val,
                    value_type=val_type,
                    source_line_start=line_num,
                    source_line_end=line_num,
                    source_text=stripped,
                    confidence="high",
                    sensitive=is_sensitive,
                )
            )

            if is_sensitive:
                diagnostics.append(
                    Diagnostic(
                        code="SENSITIVE_EVIDENCE_REDACTED",
                        message=f"Sensitive value for key '{key}' was redacted.",
                        severity="warning",
                        source_line_start=line_num,
                        source_line_end=line_num,
                        field=key,
                    )
                )

        if not settings and not diagnostics:
            # Maybe it wasn't a valid format at all, just noise
            pass

        return settings, diagnostics
