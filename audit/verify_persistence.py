"""Persistence audit verification script."""

import json
from pathlib import Path
import sqlite3

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "backend" / "phoenix_protocol.db"

if not DB_PATH.exists():
    print(f"Database not found at {DB_PATH}")
    exit(1)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# PRAGMA checks
cur.execute("PRAGMA foreign_keys")
fk = cur.fetchone()[0]

cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
tables = {row["name"]: row["sql"] for row in cur.fetchall()}

counts = {}
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    counts[t] = cur.fetchone()[0]

# Check columns of scans, devices, rule_results to verify no raw config columns exist
columns = {}
for t in ["scans", "devices", "rule_results"]:
    if t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        columns[t] = [row["name"] for row in cur.fetchall()]

# Verify no raw config is stored
has_raw_config_column = any("raw" in col.lower() or "config_text" in col.lower() for cols in columns.values() for col in cols)

# Check sample scans
cur.execute("SELECT id, status, tested_rule_compliance, total_rules, passed_rules, failed_rules, warning_rules FROM scans LIMIT 5")
sample_scans = [dict(row) for row in cur.fetchall()]

result = {
    "foreign_keys_pragma": fk,
    "table_counts": counts,
    "columns": columns,
    "has_raw_config_column": has_raw_config_column,
    "sample_scans": sample_scans,
}

(REPO_ROOT / "audit" / "persistence_audit_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"Foreign keys PRAGMA: {fk}")
print(f"Table counts: {counts}")
print(f"Has raw config column: {has_raw_config_column}")
print(f"Sample scans retrieved: {len(sample_scans)}")
conn.close()
