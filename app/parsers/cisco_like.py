"""Cisco-like configuration parser."""

from app.models.normalized_config import NormalizedConfig
from app.parsers.base import BaseParser


class CiscoLikeParser(BaseParser):
    """Parser targeting Cisco-like configuration syntax."""

    def parse(self, config_text: str) -> NormalizedConfig:
        """Parse Cisco-like configuration text into NormalizedConfig."""
        # Minimal placeholder: will process line-by-line in full implementation
        return parse_cisco_like(config_text)


def parse_cisco_like(config_text: str) -> NormalizedConfig:
    """Parse Cisco-like configuration text into a NormalizedConfig instance.

    Design contract:
    - Process line by line
    - Extract security-relevant settings
    - Preserve source line numbers
    - Return safe evidence
    - Produce warnings for missing/ambiguous settings
    - Return controlled errors
    - Never execute configuration content
    - Never retain complete raw configuration
    """
    if not isinstance(config_text, str):
        raise TypeError("config_text must be a string")

    # Minimal scaffolding returning an empty/initial NormalizedConfig
    return NormalizedConfig()
