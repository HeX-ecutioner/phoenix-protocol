"""SQLite database connection management."""

import os
import sqlite3
from typing import Optional

DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", "phoenix_protocol.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return an SQLite connection with foreign keys enabled."""
    target_path = db_path if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
