"""Storage subpackage for isolated SQLite persistence."""

from .database import get_connection, init_db
from .repository import DuplicateMappingError, KnowledgeMappingRepository

__all__ = [
    "get_connection",
    "init_db",
    "DuplicateMappingError",
    "KnowledgeMappingRepository",
]
