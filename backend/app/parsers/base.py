"""Base parser interface."""

from abc import ABC, abstractmethod

from app.models.normalized_config import NormalizedConfig


class BaseParser(ABC):
    """Abstract base class for configuration parsers."""

    @abstractmethod
    def parse(self, config_text: str) -> NormalizedConfig:
        """Parse raw device configuration into a NormalizedConfig.

        Must:
        - Process line by line
        - Extract security-relevant settings
        - Preserve source line numbers
        - Return safe evidence
        - Produce warnings for missing/ambiguous settings
        - Return controlled errors
        - Never execute configuration content
        - Never retain complete raw configuration
        """
        raise NotImplementedError
