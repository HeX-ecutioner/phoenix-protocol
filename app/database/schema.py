"""Database schema definitions and initialization."""

import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scans (
    id TEXT PRIMARY KEY,
    device_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    parser_version TEXT NOT NULL DEFAULT '1.0.0',
    rule_set_version TEXT NOT NULL DEFAULT '1.0.0',
    total_rules INTEGER NOT NULL DEFAULT 0,
    passed_rules INTEGER NOT NULL DEFAULT 0,
    failed_rules INTEGER NOT NULL DEFAULT 0,
    warning_rules INTEGER NOT NULL DEFAULT 0,
    not_applicable_rules INTEGER NOT NULL DEFAULT 0,
    error_rules INTEGER NOT NULL DEFAULT 0,
    tested_rule_compliance REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT,
    vendor TEXT,
    device_type TEXT NOT NULL,
    source_filename TEXT NOT NULL,
    parse_status TEXT NOT NULL DEFAULT 'success',
    line_count INTEGER,
    error_message TEXT,
    total_rules INTEGER NOT NULL DEFAULT 0,
    passed_rules INTEGER NOT NULL DEFAULT 0,
    failed_rules INTEGER NOT NULL DEFAULT 0,
    warning_rules INTEGER NOT NULL DEFAULT 0,
    not_applicable_rules INTEGER NOT NULL DEFAULT 0,
    error_rules INTEGER NOT NULL DEFAULT 0,
    tested_rule_compliance REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rules (
    rule_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    technical_requirement TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL,
    device_type TEXT NOT NULL DEFAULT 'cisco_ios',
    category TEXT NOT NULL DEFAULT 'General',
    remediation TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    rule_version TEXT NOT NULL DEFAULT '1.0.0'
);

CREATE TABLE IF NOT EXISTS rule_results (
    id TEXT PRIMARY KEY,
    scan_id TEXT,
    device_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    evidence TEXT NOT NULL DEFAULT '',
    evidence_line_range TEXT,
    message TEXT NOT NULL DEFAULT '',
    remediation TEXT NOT NULL DEFAULT '',
    evaluation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    engine_version TEXT NOT NULL DEFAULT '1.0.0',
    error_message TEXT,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES rules(rule_id) ON DELETE RESTRICT,
    CONSTRAINT uq_device_rule UNIQUE (device_id, rule_id)
);

CREATE INDEX IF NOT EXISTS idx_devices_scan_id ON devices(scan_id);
CREATE INDEX IF NOT EXISTS idx_rule_results_scan_id ON rule_results(scan_id);
CREATE INDEX IF NOT EXISTS idx_rule_results_device_id ON rule_results(device_id);
CREATE INDEX IF NOT EXISTS idx_rule_results_rule_id ON rule_results(rule_id);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize SQLite database tables and indexes."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
