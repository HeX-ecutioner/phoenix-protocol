"""Validation script to evaluate all sample_data fixtures against parser and scanner."""

import pathlib
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.scanner import run_scan

import uuid

sample_dir = pathlib.Path(__file__).resolve().parent.parent / "sample_data"
files = sorted([f for f in sample_dir.rglob("*.txt")])

print(f"Total fixtures found: {len(files)}")
print(f"{'File':<42} | {'Device Name':<20} | {'Status':<7} | {'P':<2} {'F':<2} {'W':<2} {'E':<2} | {'Score':<6}")
print("-" * 94)

for f in files:
    rel = f.relative_to(sample_dir).as_posix()
    content = f.read_text(encoding="utf-8", errors="replace")
    scan_res = run_scan(
        scan_id=str(uuid.uuid4()),
        device_type="cisco_ios",
        uploaded_files=[{"filename": f.name, "content": content}],
    )
    summary = scan_res["summary"]
    dev = scan_res["devices"][0]
    dev_name = str(dev.get("name") or "None")
    status = dev.get("parse_status", "unknown")
    p = summary["passed_rules"]
    fl = summary["failed_rules"]
    w = summary["warning_rules"]
    e = summary["error_rules"]
    score = f"{summary['tested_rule_compliance']:.1f}%"
    print(f"{rel:<42} | {dev_name:<18} | {status:<7} | {p:<2} {fl:<2} {w:<2} {e:<2} | {score:<6}")
