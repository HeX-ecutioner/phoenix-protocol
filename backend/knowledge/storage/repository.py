"""Isolated SQLite repository for knowledge mappings."""

from datetime import datetime, timezone
import sqlite3
from typing import Any, List, Optional

try:
    from ..models.knowledge_mapping import (
        ALLOWED_APPROVAL_STATUSES,
        ApprovalStatus,
        KnowledgeMapping,
    )
except ImportError:
    from models.knowledge_mapping import (
        ALLOWED_APPROVAL_STATUSES,
        ApprovalStatus,
        KnowledgeMapping,
    )


class DuplicateMappingError(ValueError):
    """Raised when attempting to store or approve a duplicate knowledge mapping."""

    def __init__(self, vendor: str, platform: str, normalized_command: str):
        super().__init__(
            f"An approved mapping already exists for vendor '{vendor}', "
            f"platform '{platform}', command '{normalized_command}'."
        )
        self.vendor = vendor
        self.platform = platform
        self.normalized_command = normalized_command


class KnowledgeMappingRepository:
    """Repository handling CRUD, lookup, and lifecycle queries for knowledge mappings."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _row_to_model(self, row: sqlite3.Row) -> KnowledgeMapping:
        return KnowledgeMapping(
            id=row["id"],
            vendor=row["vendor"],
            platform=row["platform"],
            command_pattern=row["command_pattern"],
            normalized_command=row["normalized_command"],
            meaning=row["meaning"],
            security_control=row["security_control"],
            mapped_rule_id=row["mapped_rule_id"],
            explanation=row["explanation"] or "",
            confidence=float(row["confidence"]),
            source=row["source"],
            approval_status=row["approval_status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            version=row["version"],
        )

    def create(self, mapping: KnowledgeMapping) -> KnowledgeMapping:
        """Insert a knowledge mapping record using parameterized SQL.

        Raises DuplicateMappingError if an approved mapping already exists for the command.
        """
        if mapping.approval_status == ApprovalStatus.APPROVED.value:
            existing = self.find_mapping(
                vendor=mapping.vendor,
                platform=mapping.platform,
                normalized_command=mapping.normalized_command,
                approval_status=ApprovalStatus.APPROVED.value,
            )
            if existing is not None:
                raise DuplicateMappingError(
                    mapping.vendor, mapping.platform, mapping.normalized_command
                )

        query = """
        INSERT INTO knowledge_mappings (
            id, vendor, platform, command_pattern, normalized_command,
            meaning, security_control, mapped_rule_id, explanation,
            confidence, source, approval_status, created_at, updated_at, version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            mapping.id,
            mapping.vendor,
            mapping.platform,
            mapping.command_pattern,
            mapping.normalized_command,
            mapping.meaning,
            mapping.security_control,
            mapping.mapped_rule_id,
            mapping.explanation,
            mapping.confidence,
            mapping.source,
            mapping.approval_status,
            mapping.created_at,
            mapping.updated_at,
            mapping.version,
        )

        try:
            self.conn.execute(query, params)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            if "uq_km_approved" in str(e) or "UNIQUE constraint failed" in str(e):
                raise DuplicateMappingError(
                    mapping.vendor, mapping.platform, mapping.normalized_command
                )
            raise e

        return mapping

    def get_by_id(self, mapping_id: str) -> Optional[KnowledgeMapping]:
        """Fetch a single mapping record by primary ID."""
        cursor = self.conn.execute(
            "SELECT * FROM knowledge_mappings WHERE id = ?", (mapping_id,)
        )
        row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def find_mapping(
        self,
        vendor: str,
        platform: str,
        normalized_command: str,
        approval_status: str = ApprovalStatus.APPROVED.value,
    ) -> Optional[KnowledgeMapping]:
        """Find mapping by exact vendor, platform, and normalized command.

        By default, searches ONLY approved records.
        """
        query = """
        SELECT * FROM knowledge_mappings
        WHERE vendor = ? AND platform = ? AND normalized_command = ? AND approval_status = ?
        ORDER BY updated_at DESC LIMIT 1
        """
        cursor = self.conn.execute(
            query, (vendor, platform, normalized_command, approval_status)
        )
        row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def list_mappings(
        self,
        vendor: Optional[str] = None,
        platform: Optional[str] = None,
        approval_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KnowledgeMapping]:
        """List mappings with optional filtering."""
        conditions: List[str] = []
        params: List[Any] = []

        if vendor:
            conditions.append("vendor = ?")
            params.append(vendor)
        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if approval_status:
            conditions.append("approval_status = ?")
            params.append(approval_status)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM knowledge_mappings {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(query, tuple(params))
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def update_approval_status(
        self, mapping_id: str, new_status: str
    ) -> Optional[KnowledgeMapping]:
        """Update approval lifecycle state.

        If transitioning to 'approved', ensures no duplicate approved mapping exists.
        """
        if new_status not in ALLOWED_APPROVAL_STATUSES:
            raise ValueError(
                f"Invalid approval_status '{new_status}'. Allowed: {sorted(ALLOWED_APPROVAL_STATUSES)}."
            )

        mapping = self.get_by_id(mapping_id)
        if not mapping:
            return None

        if new_status == ApprovalStatus.APPROVED.value:
            existing = self.find_mapping(
                vendor=mapping.vendor,
                platform=mapping.platform,
                normalized_command=mapping.normalized_command,
                approval_status=ApprovalStatus.APPROVED.value,
            )
            if existing and existing.id != mapping_id:
                raise DuplicateMappingError(
                    mapping.vendor, mapping.platform, mapping.normalized_command
                )

        now_utc = datetime.now(timezone.utc).isoformat()
        query = """
        UPDATE knowledge_mappings
        SET approval_status = ?, updated_at = ?
        WHERE id = ?
        """
        try:
            self.conn.execute(query, (new_status, now_utc, mapping_id))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            if "uq_km_approved" in str(e):
                raise DuplicateMappingError(
                    mapping.vendor, mapping.platform, mapping.normalized_command
                )
            raise e

        return self.get_by_id(mapping_id)

    def delete(self, mapping_id: str) -> bool:
        """Delete mapping record by ID."""
        cursor = self.conn.execute(
            "DELETE FROM knowledge_mappings WHERE id = ?", (mapping_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def count(
        self,
        vendor: Optional[str] = None,
        platform: Optional[str] = None,
        approval_status: Optional[str] = None,
    ) -> int:
        """Count mappings matching filters."""
        conditions: List[str] = []
        params: List[Any] = []

        if vendor:
            conditions.append("vendor = ?")
            params.append(vendor)
        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if approval_status:
            conditions.append("approval_status = ?")
            params.append(approval_status)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT COUNT(*) as cnt FROM knowledge_mappings {where_clause}"
        cursor = self.conn.execute(query, tuple(params))
        row = cursor.fetchone()
        return row["cnt"] if row else 0
