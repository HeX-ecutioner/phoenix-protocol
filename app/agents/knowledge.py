"""Knowledge provider abstractions for Teach-the-Auditor.

Defines the pluggable KnowledgeProvider interface enabling Teach-the-Auditor to check
whether an unfamiliar command has already been learned and verified by humans.
Provides MockKnowledgeProvider for fast, deterministic unit testing and offline development.
Dev2's persistent KnowledgeService will eventually plug in behind this exact interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from app.agents.schemas import CommandInterpretation


def _normalize_key(vendor: str, platform: str, command: str) -> Tuple[str, str, str]:
    """Normalize lookup keys for case- and whitespace-insensitive matching."""
    norm_cmd = " ".join(command.strip().lower().split())
    return (vendor.strip().lower(), platform.strip().lower(), norm_cmd)


class KnowledgeProvider(ABC):
    """Abstract interface for querying previously learned network command interpretations."""

    @abstractmethod
    def lookup_command(
        self, vendor: str, platform: str, command: str
    ) -> Optional[CommandInterpretation]:
        """Look up an existing verified interpretation for a command.

        Args:
            vendor: Target device vendor (e.g. 'Cisco', 'Arista').
            platform: Operating platform (e.g. 'IOS', 'EOS').
            command: The configuration command string.

        Returns:
            CommandInterpretation if found in the knowledge base, None otherwise.
        """
        raise NotImplementedError


class MockKnowledgeProvider(KnowledgeProvider):
    """In-memory, dictionary-backed KnowledgeProvider for testing and offline execution."""

    def __init__(
        self, initial_mappings: Optional[List[CommandInterpretation]] = None
    ) -> None:
        self._mappings: Dict[Tuple[str, str, str], CommandInterpretation] = {}
        if initial_mappings:
            for mapping in initial_mappings:
                self.add_mapping(mapping)

    def add_mapping(self, interpretation: CommandInterpretation) -> None:
        """Register a known command mapping in memory."""
        key = _normalize_key(
            interpretation.vendor, interpretation.platform, interpretation.command
        )
        self._mappings[key] = interpretation

    def lookup_command(
        self, vendor: str, platform: str, command: str
    ) -> Optional[CommandInterpretation]:
        """Look up a command in memory using normalized key comparison."""
        key = _normalize_key(vendor, platform, command)
        return self._mappings.get(key)

    def clear(self) -> None:
        """Clear all stored mappings."""
        self._mappings.clear()

    def count(self) -> int:
        """Return the number of stored mappings."""
        return len(self._mappings)

    def all_mappings(self) -> List[CommandInterpretation]:
        """Return a copy of all stored interpretations."""
        return list(self._mappings.values())
