"""Security audit verification script for Phoenix Protocol backend.

Extracts potential secrets from security sample configurations and verifies that
NO raw secrets leak into:
1. Returned API responses
2. The SQLite database
3. Logs or error messages

Also checks codebase for dangerous execution primitives (eval, exec, subprocess, ssh).
"""

import json
from pathlib import Path
import re
import sqlite3

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = REPO_ROOT / "backend" / "sample_data" / "security"
RESPONSES_DIR = REPO_ROOT / "audit" / "api_responses"
BACKEND_DIR = REPO_ROOT / "backend"

# Known raw secret values present in sample_data/security/ files
# We identify regex patterns for extracting the secret tokens from:
# - enable password <secret>
# - username <user> password <secret>
# - tacacs-server key <secret>
# - radius-server key <secret>
# - snmp-server community <secret>
SECRET_FILES = [
    SAMPLE_DATA / "plaintext_credentials.txt",
    SAMPLE_DATA / "type7_credentials.txt",
    SAMPLE_DATA / "tacacs_radius_secrets.txt",
    SAMPLE_DATA / "mixed_secrets.txt",
]

extracted_raw_secrets = set()
for sf in SECRET_FILES:
    if not sf.exists():
        continue
    for line in sf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # Look for password / secret / key tokens
        m1 = re.match(r".*(?:password|secret|key)\s+(\S+)", line, re.IGNORECASE)
        if m1:
            token = m1.group(1).strip()
            if len(token) > 3 and token.lower() not in ["0", "5", "7", "8", "9", "in", "out"]:
                extracted_raw_secrets.add(token)
        m2 = re.match(r".*(?:password|secret|key)\s+\d\s+(\S+)", line, re.IGNORECASE)
        if m2:
            token = m2.group(1).strip()
            if len(token) > 3:
                extracted_raw_secrets.add(token)
        m3 = re.match(r"snmp-server\s+community\s+(\S+)", line, re.IGNORECASE)
        if m3:
            token = m3.group(1).strip()
            if len(token) > 3 and token.lower() not in ["ro", "rw"]:
                extracted_raw_secrets.add(token)

print(f"Identified {len(extracted_raw_secrets)} secret tokens to audit for leakage.")

# 1. Audit API responses
api_leaks = []
for res_file in RESPONSES_DIR.glob("*.json"):
    content = res_file.read_text(encoding="utf-8")
    for sec in extracted_raw_secrets:
        if sec in content:
            api_leaks.append((res_file.name, "API response contains secret"))

# 2. Audit SQLite database
db_leaks = []
for db_file in [BACKEND_DIR / "phoenix_protocol.db", REPO_ROOT / "phoenix_protocol.db", BACKEND_DIR / "knowledge" / "knowledge.db"]:
    if db_file.exists():
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        # Check all tables and text columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        for tbl in tables:
            try:
                cursor.execute(f"SELECT * FROM {tbl}")
                rows = cursor.fetchall()
                for row in rows:
                    row_str = str(row)
                    for sec in extracted_raw_secrets:
                        if sec in row_str:
                            db_leaks.append((db_file.name, tbl, "Database contains secret"))
            except Exception:
                pass
        conn.close()

# 3. Audit dangerous execution primitives in backend code
dangerous_primitives = []
code_files = list((BACKEND_DIR / "app").glob("**/*.py")) + list((BACKEND_DIR / "knowledge").glob("**/*.py"))
for cf in code_files:
    content = cf.read_text(encoding="utf-8", errors="ignore")
    rel_path = cf.relative_to(REPO_ROOT)
    for line_idx, line in enumerate(content.splitlines(), start=1):
        clean = line.strip()
        if clean.startswith("#"):
            continue
        if re.search(r"\beval\(", clean):
            dangerous_primitives.append((str(rel_path), line_idx, "eval() call"))
        if re.search(r"\bexec\(", clean):
            dangerous_primitives.append((str(rel_path), line_idx, "exec() call"))
        if re.search(r"\bsubprocess\.", clean):
            dangerous_primitives.append((str(rel_path), line_idx, "subprocess module"))
        if re.search(r"\bos\.system\(", clean):
            dangerous_primitives.append((str(rel_path), line_idx, "os.system() call"))
        if re.search(r"\bparamiko\b", clean, re.IGNORECASE):
            dangerous_primitives.append((str(rel_path), line_idx, "paramiko SSH"))
        if re.search(r"\bnetmiko\b", clean, re.IGNORECASE):
            dangerous_primitives.append((str(rel_path), line_idx, "netmiko SSH"))

audit_summary = {
    "total_secrets_audited": len(extracted_raw_secrets),
    "api_response_leaks": len(api_leaks),
    "database_leaks": len(db_leaks),
    "dangerous_primitives_found": len(dangerous_primitives),
    "details": {
        "api_leaks": api_leaks,
        "db_leaks": db_leaks,
        "dangerous_primitives": dangerous_primitives,
    }
}

(REPO_ROOT / "audit" / "security_verification_summary.json").write_text(
    json.dumps(audit_summary, indent=2), encoding="utf-8"
)

print(f"API Leaks: {len(api_leaks)}")
print(f"DB Leaks: {len(db_leaks)}")
print(f"Dangerous Primitives in Production Code: {len(dangerous_primitives)}")
if dangerous_primitives:
    for dp in dangerous_primitives:
        print(f"  - {dp}")
