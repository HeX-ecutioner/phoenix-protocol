"""Knowledge service acting as the primary integration boundary for Teach the Auditor."""

import sqlite3
from typing import Any, Dict, List, Optional

try:
    from ..models.knowledge_mapping import ApprovalStatus, KnowledgeMapping
    from ..storage.database import get_connection, init_db
    from ..storage.repository import KnowledgeMappingRepository
    from ..validation.mapping_validator import (
        normalize_command,
        validate_and_prepare_mapping,
    )
except ImportError:
    from models.knowledge_mapping import ApprovalStatus, KnowledgeMapping
    from storage.database import get_connection, init_db
    from storage.repository import KnowledgeMappingRepository
    from validation.mapping_validator import (
        normalize_command,
        validate_and_prepare_mapping,
    )


class KnowledgeService:
    """Service layer orchestrating mapping validation, normalization, approval, and lookup.

    This service is the primary integration contract for Developer 1.
    Callers must interact through this service rather than writing directly to SQLite.
    """

    def __init__(
        self, conn: Optional[sqlite3.Connection] = None, db_path: Optional[str] = None
    ):
        self._own_conn = False
        if conn is not None:
            self.conn = conn
        else:
            self.conn = get_connection(db_path)
            self._own_conn = True

        init_db(self.conn)
        self.repo = KnowledgeMappingRepository(self.conn)

    def close(self) -> None:
        """Close database connection if owned by service."""
        if self._own_conn and self.conn:
            self.conn.close()

    def propose_mapping(
        self,
        vendor: str,
        platform: str,
        command_pattern: str,
        meaning: str,
        security_control: str,
        mapped_rule_id: Optional[str] = None,
        explanation: str = "",
        confidence: float = 1.0,
        source: str = "ai_agent",
    ) -> KnowledgeMapping:
        """Propose a new command meaning mapping (defaults to 'proposed' status).

        Workflow enforced:
        validate -> normalize -> sanitize -> persist
        """
        raw_payload: Dict[str, Any] = {
            "vendor": vendor,
            "platform": platform,
            "command_pattern": command_pattern,
            "meaning": meaning,
            "security_control": security_control,
            "mapped_rule_id": mapped_rule_id,
            "explanation": explanation,
            "confidence": confidence,
            "source": source,
            "approval_status": ApprovalStatus.PROPOSED.value,
        }

        # Strict validation, normalization, and secret sanitization
        prepared = validate_and_prepare_mapping(raw_payload)

        mapping = KnowledgeMapping.from_dict(prepared)
        return self.repo.create(mapping)

    def approve_mapping(self, mapping_id: str) -> KnowledgeMapping:
        """Promote a proposed or rejected mapping to 'approved'.

        Raises ValueError if mapping does not exist.
        Raises DuplicateMappingError if an approved mapping already exists for this exact command.
        """
        existing = self.repo.get_by_id(mapping_id)
        if not existing:
            raise ValueError(f"Mapping with ID '{mapping_id}' not found.")

        updated = self.repo.update_approval_status(
            mapping_id, ApprovalStatus.APPROVED.value
        )
        if not updated:
            raise ValueError(f"Failed to update mapping with ID '{mapping_id}'.")
        return updated

    def reject_mapping(
        self, mapping_id: str, reason: Optional[str] = None
    ) -> KnowledgeMapping:
        """Transition a mapping to 'rejected' state.

        Rejected mappings are preserved for historical audit trails, but excluded from lookup.
        """
        existing = self.repo.get_by_id(mapping_id)
        if not existing:
            raise ValueError(f"Mapping with ID '{mapping_id}' not found.")

        updated = self.repo.update_approval_status(
            mapping_id, ApprovalStatus.REJECTED.value
        )
        if not updated:
            raise ValueError(f"Failed to reject mapping with ID '{mapping_id}'.")
        return updated

    def lookup_command(
        self,
        vendor: str,
        platform: str,
        command: str,
    ) -> Optional[KnowledgeMapping]:
        """Look up an approved command meaning by vendor, platform, and command.

        Deterministically normalizes command syntax before searching.
        Returns ONLY approved knowledge records.
        Returns None if no approved mapping exists (or if only proposed/rejected exist).
        """
        if not command or not vendor or not platform:
            return None

        clean_vendor = str(vendor).strip()
        clean_platform = str(platform).strip()
        normalized_cmd = normalize_command(str(command))

        return self.repo.find_mapping(
            vendor=clean_vendor,
            platform=clean_platform,
            normalized_command=normalized_cmd,
            approval_status=ApprovalStatus.APPROVED.value,
        )

    def list_approved_knowledge(
        self,
        vendor: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[KnowledgeMapping]:
        """List all currently approved knowledge mappings."""
        return self.repo.list_mappings(
            vendor=vendor,
            platform=platform,
            approval_status=ApprovalStatus.APPROVED.value,
        )

    def list_proposals(
        self,
        vendor: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[KnowledgeMapping]:
        """List all pending proposed mappings awaiting human approval."""
        return self.repo.list_mappings(
            vendor=vendor,
            platform=platform,
            approval_status=ApprovalStatus.PROPOSED.value,
        )
