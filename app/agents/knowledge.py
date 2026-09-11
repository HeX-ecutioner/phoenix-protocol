"""Knowledge provider abstractions for Teach-the-Auditor.

Defines the pluggable KnowledgeProvider interface enabling Teach-the-Auditor to check
whether an unfamiliar command has already been learned and verified by humans.
Provides MockKnowledgeProvider for fast, deterministic unit testing and offline development.
Dev2's persistent KnowledgeService will eventually plug in behind this exact interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

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


def _ensure_dev2_on_path() -> None:
    """Ensure the Developer 2 package directory ('dev 2 part') is in sys.path."""
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent
    dev2_dir = repo_root / "dev 2 part"
    if dev2_dir.is_dir() and str(dev2_dir) not in sys.path:
        sys.path.insert(0, str(dev2_dir))


class Dev2KnowledgeProvider(KnowledgeProvider):
    """Adapter connecting Teach-the-Auditor to Dev2's persistent KnowledgeService.

    Architecture:
      TeachAuditorService -> KnowledgeProvider -> Dev2KnowledgeProvider -> KnowledgeService -> SQLite

    Invariants strictly enforced:
    - Only APPROVED mappings are ever returned as trusted knowledge.
    - Proposed and rejected mappings return None on lookup.
    - The ADK layer interacts exclusively through KnowledgeService, never raw SQLite queries.
    """

    def __init__(
        self,
        service: Optional[Any] = None,
        conn: Optional[Any] = None,
        db_path: Optional[str] = None,
    ) -> None:
        """Initialize adapter with an existing KnowledgeService or create a new one.

        Args:
            service: Optional pre-configured KnowledgeService instance.
            conn: Optional SQLite connection to pass to KnowledgeService.
            db_path: Optional file path for the knowledge SQLite database.
        """
        _ensure_dev2_on_path()
        from services.knowledge_service import KnowledgeService

        if service is not None:
            self._service = service
            self._own_service = False
        else:
            if conn is not None and getattr(conn, "row_factory", None) is None:
                import sqlite3
                conn.row_factory = sqlite3.Row
            self._service = KnowledgeService(conn=conn, db_path=db_path)
            self._own_service = True

    @property
    def service(self) -> Any:
        """Access the underlying Dev2 KnowledgeService."""
        return self._service

    def lookup_command(
        self, vendor: str, platform: str, command: str
    ) -> Optional[CommandInterpretation]:
        """Look up an approved command interpretation via Dev2's KnowledgeService.

        Returns None if no approved mapping exists (or if only proposed/rejected exist).
        """
        mapping = self._service.lookup_command(
            vendor=vendor, platform=platform, command=command
        )
        if mapping is None:
            return None

        # Convert Dev2 KnowledgeMapping to ADK CommandInterpretation
        return CommandInterpretation(
            command=mapping.command_pattern,
            vendor=mapping.vendor,
            platform=mapping.platform,
            meaning=mapping.meaning,
            security_control=mapping.security_control,
            mapped_rule_id=mapping.mapped_rule_id,
            confidence=mapping.confidence,
            explanation=mapping.explanation,
        )

    def propose_mapping(
        self, interpretation: CommandInterpretation, source: str = "ai_agent"
    ) -> Any:
        """Submit a newly interpreted command mapping to Dev2's service as 'proposed'.

        Enforces Dev2's validation, normalization, and secret sanitization pipeline.
        Returns the created KnowledgeMapping record (with status='proposed').
        """
        return self._service.propose_mapping(
            vendor=interpretation.vendor,
            platform=interpretation.platform,
            command_pattern=interpretation.command,
            meaning=interpretation.meaning,
            security_control=interpretation.security_control,
            mapped_rule_id=interpretation.mapped_rule_id,
            explanation=interpretation.explanation,
            confidence=interpretation.confidence,
            source=source,
        )

    def approve_mapping(self, mapping_id: str) -> Any:
        """Approve a proposed mapping, making it active and retrievable via lookup_command()."""
        return self._service.approve_mapping(mapping_id)

    def reject_mapping(self, mapping_id: str, reason: Optional[str] = None) -> Any:
        """Reject a proposed mapping, excluding it from lookup while retaining audit history."""
        return self._service.reject_mapping(mapping_id, reason=reason)

    def list_approved(
        self, vendor: Optional[str] = None, platform: Optional[str] = None
    ) -> List[Any]:
        """List currently active and approved knowledge mappings."""
        return self._service.list_approved_knowledge(vendor=vendor, platform=platform)

    def list_proposals(
        self, vendor: Optional[str] = None, platform: Optional[str] = None
    ) -> List[Any]:
        """List proposals awaiting human review and approval."""
        return self._service.list_proposals(vendor=vendor, platform=platform)

    def close(self) -> None:
        """Close database connection if owned by this provider."""
        if self._own_service and hasattr(self._service, "close"):
            self._service.close()

