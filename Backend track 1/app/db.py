import sqlite3


def get_connection(db_path: str = "phoenix.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        scan_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        format TEXT NOT NULL,
        parser_id TEXT NOT NULL,
        parser_version TEXT NOT NULL,
        summary_json TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS normalized_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT NOT NULL,
        setting_key TEXT NOT NULL,
        value_json TEXT,
        value_type TEXT NOT NULL,
        source_line_start INTEGER,
        source_line_end INTEGER,
        source_text TEXT,
        confidence TEXT NOT NULL,
        sensitive BOOLEAN NOT NULL,
        FOREIGN KEY(scan_id) REFERENCES scans(scan_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rule_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT NOT NULL,
        rule_id TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        severity TEXT NOT NULL,
        rule_version TEXT NOT NULL,
        status TEXT NOT NULL,
        rationale TEXT NOT NULL,
        FOREIGN KEY(scan_id) REFERENCES scans(scan_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT NOT NULL,
        rule_id TEXT NOT NULL,
        setting_key TEXT NOT NULL,
        observed_value_json TEXT,
        expected_value_json TEXT,
        source_line_start INTEGER,
        source_line_end INTEGER,
        source_text TEXT,
        safe_to_display BOOLEAN NOT NULL,
        FOREIGN KEY(scan_id) REFERENCES scans(scan_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diagnostics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT NOT NULL,
        rule_id TEXT,
        code TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        source_line_start INTEGER,
        source_line_end INTEGER,
        field TEXT,
        FOREIGN KEY(scan_id) REFERENCES scans(scan_id)
    )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_rule_results_scan_id ON rule_results(scan_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_diagnostics_scan_id ON diagnostics(scan_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_evidence_scan_id ON evidence(scan_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_normalized_settings_scan_id ON normalized_settings(scan_id)"
    )

    conn.commit()
