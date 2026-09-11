"""Teach the Auditor - Knowledge, Persistence, Validation, and Approval Layer.

Isolated Developer 2 component for Phoenix Protocol.
Stores command interpretation knowledge without making compliance decisions.
"""

# Dynamic exposure of core interfaces
try:
    from .models.knowledge_mapping import ApprovalStatus, KnowledgeMapping
    from .services.knowledge_service import KnowledgeService
    from .storage.database import get_connection, init_db
    from .storage.repository import DuplicateMappingError, KnowledgeMappingRepository
    from .validation.mapping_validator import (
        ValidationError,
        normalize_command,
        sanitize_secret_command,
    )

    __all__ = [
        "ApprovalStatus",
        "KnowledgeMapping",
        "KnowledgeService",
        "KnowledgeMappingRepository",
        "DuplicateMappingError",
        "ValidationError",
        "normalize_command",
        "sanitize_secret_command",
        "get_connection",
        "init_db",
    ]
except ImportError:
    pass

__version__ = "1.0.0"
