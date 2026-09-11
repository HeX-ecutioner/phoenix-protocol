"""Isolated SQLite database initialization and connection management."""

import sqlite3
from typing import Optional

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS knowledge_mappings (
    id TEXT PRIMARY KEY,
    vendor TEXT NOT NULL,
    platform TEXT NOT NULL,
    command_pattern TEXT NOT NULL,
    normalized_command TEXT NOT NULL,
    meaning TEXT NOT NULL,
    security_control TEXT NOT NULL,
    mapped_rule_id TEXT,
    explanation TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    source TEXT NOT NULL DEFAULT 'human',
    approval_status TEXT NOT NULL DEFAULT 'proposed',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0'
);

-- Partial unique index strictly preventing duplicate approved knowledge for the same command
CREATE UNIQUE INDEX IF NOT EXISTS uq_km_approved
ON knowledge_mappings(vendor, platform, normalized_command)
WHERE approval_status = 'approved';

-- Indices for fast exact lookup and status filtering
CREATE INDEX IF NOT EXISTS idx_km_lookup
ON knowledge_mappings(vendor, platform, normalized_command, approval_status);

CREATE INDEX IF NOT EXISTS idx_km_status
ON knowledge_mappings(approval_status);
"""


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return an isolated SQLite connection with foreign keys enabled."""
    target_path = db_path if db_path is not None else ":memory:"
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize schema tables and indexes on the connection."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
