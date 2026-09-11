"""Black-box audit test runner for Phoenix Protocol backend.

Sends requests to the live running Flask service on http://127.0.0.1:5000,
captures full requests and responses, validates response schemas, and saves
structured evidence files for audit reporting.
"""

import json
import os
from pathlib import Path
import sys
import requests

BASE_URL = "http://127.0.0.1:5000"
REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = REPO_ROOT / "backend" / "sample_data"
RESPONSES_DIR = REPO_ROOT / "audit" / "api_responses"
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

test_manifest = [
    # Baseline
    ("compliant.json", [SAMPLE_DATA / "baseline" / "compliant_router.txt"], "compliant_router.txt"),
    ("failing.json", [SAMPLE_DATA / "baseline" / "failing_router.txt"], "failing_router.txt"),
    ("ambiguous.json", [SAMPLE_DATA / "baseline" / "ambiguous_router.txt"], "ambiguous_router.txt"),
    # Edge Cases
    ("garbage.json", [SAMPLE_DATA / "edge_cases" / "garbage.txt"], "garbage.txt"),
    ("malformed_banner.json", [SAMPLE_DATA / "edge_cases" / "malformed_banner.txt"], "malformed_banner.txt"),
    ("empty.json", [SAMPLE_DATA / "edge_cases" / "empty.txt"], "empty.txt"),
    ("multiple_vty_blocks.json", [SAMPLE_DATA / "edge_cases" / "multiple_vty_blocks.txt"], "multiple_vty_blocks.txt"),
    ("partial_vty_failure.json", [SAMPLE_DATA / "edge_cases" / "partial_vty_failure.txt"], "partial_vty_failure.txt"),
    ("ambiguous_transport.json", [SAMPLE_DATA / "edge_cases" / "ambiguous_transport.txt"], "ambiguous_transport.txt"),
    ("local_logging_only.json", [SAMPLE_DATA / "edge_cases" / "local_logging_only.txt"], "local_logging_only.txt"),
    ("no_banner.json", [SAMPLE_DATA / "edge_cases" / "no_banner.txt"], "no_banner.txt"),
    ("ntp_peer_only.json", [SAMPLE_DATA / "edge_cases" / "ntp_peer_only.txt"], "ntp_peer_only.txt"),
    ("partial_config.json", [SAMPLE_DATA / "edge_cases" / "partial_config.txt"], "partial_config.txt"),
    # Security fixtures
    ("plaintext_credentials.json", [SAMPLE_DATA / "security" / "plaintext_credentials.txt"], "plaintext_credentials.txt"),
    ("type7_credentials.json", [SAMPLE_DATA / "security" / "type7_credentials.txt"], "type7_credentials.txt"),
    ("tacacs_radius_secrets.json", [SAMPLE_DATA / "security" / "tacacs_radius_secrets.txt"], "tacacs_radius_secrets.txt"),
    ("mixed_secrets.json", [SAMPLE_DATA / "security" / "mixed_secrets.txt"], "mixed_secrets.txt"),
    # Services
    ("insecure_services_enabled.json", [SAMPLE_DATA / "services" / "insecure_services_enabled.txt"], "insecure_services_enabled.txt"),
    ("insecure_services_disabled.json", [SAMPLE_DATA / "services" / "insecure_services_disabled.txt"], "insecure_services_disabled.txt"),
    # Scenarios
    ("remediation_demo.json", [SAMPLE_DATA / "scenarios" / "remediation_demo.txt"], "remediation_demo.txt"),
    ("multi_device_secondary.json", [SAMPLE_DATA / "scenarios" / "multi_device_secondary.txt"], "multi_device_secondary.txt"),
    ("net001_telnet.json", [SAMPLE_DATA / "scenarios" / "net001_telnet.txt"], "net001_telnet.txt"),
    ("net002_no_ssh.json", [SAMPLE_DATA / "scenarios" / "net002_no_ssh.txt"], "net002_no_ssh.txt"),
    ("net003_weak_credentials.json", [SAMPLE_DATA / "scenarios" / "net003_weak_credentials.txt"], "net003_weak_credentials.txt"),
    ("net004_no_login_protection.json", [SAMPLE_DATA / "scenarios" / "net004_no_login_protection.txt"], "net004_no_login_protection.txt"),
    ("net005_no_logging.json", [SAMPLE_DATA / "scenarios" / "net005_no_logging.txt"], "net005_no_logging.txt"),
    ("net006_no_ntp.json", [SAMPLE_DATA / "scenarios" / "net006_no_ntp.txt"], "net006_no_ntp.txt"),
    ("net007_no_access_class.json", [SAMPLE_DATA / "scenarios" / "net007_no_access_class.txt"], "net007_no_access_class.txt"),
    ("net008_insecure_services.json", [SAMPLE_DATA / "scenarios" / "net008_insecure_services.txt"], "net008_insecure_services.txt"),
    ("net009_no_banner.json", [SAMPLE_DATA / "scenarios" / "net009_no_banner.txt"], "net009_no_banner.txt"),
    ("net010_plaintext_secret.json", [SAMPLE_DATA / "scenarios" / "net010_plaintext_secret.txt"], "net010_plaintext_secret.txt"),
    ("all_security_controls.json", [SAMPLE_DATA / "scenarios" / "all_security_controls.txt"], "all_security_controls.txt"),
    # Multi-file batch
    ("multi_device.json", [
        SAMPLE_DATA / "baseline" / "compliant_router.txt",
        SAMPLE_DATA / "baseline" / "failing_router.txt",
        SAMPLE_DATA / "scenarios" / "multi_device_secondary.txt",
    ], "multi-file batch (3 devices)")
]

results = {}
created_scan_ids = []

print("--- Running API Health Check ---")
try:
    health_res = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"GET /health -> Status: {health_res.status_code}")
    (RESPONSES_DIR / "health.json").write_text(json.dumps(health_res.json(), indent=2), encoding="utf-8")
    results["health"] = {"status": health_res.status_code, "body": health_res.json()}
except Exception as e:
    print(f"Failed to query /health: {e}")
    sys.exit(1)

print("\n--- Running POST /scan for Test Fixtures ---")
for out_name, file_paths, label in test_manifest:
    files_payload = []
    opened_handles = []
    try:
        for p in file_paths:
            if not p.exists():
                print(f"WARNING: File not found: {p}")
                continue
            h = open(p, "rb")
            opened_handles.append(h)
            files_payload.append(("files", (p.name, h, "text/plain")))

        if not files_payload:
            continue

        res = requests.post(f"{BASE_URL}/scan", files=files_payload, timeout=10)
        print(f"POST /scan [{label}] -> Status: {res.status_code}")

        try:
            body_json = res.json()
        except Exception:
            body_json = {"raw_text": res.text}

        # Save exact response
        out_file = RESPONSES_DIR / out_name
        out_file.write_text(json.dumps(body_json, indent=2), encoding="utf-8")

        scan_id = body_json.get("scan_id")
        if scan_id:
            created_scan_ids.append(scan_id)

        results[out_name] = {
            "label": label,
            "status_code": res.status_code,
            "scan_id": scan_id,
            "compliance_score": body_json.get("compliance_score"),
            "summary": body_json.get("summary"),
            "device_count": len(body_json.get("devices", [])),
        }
    finally:
        for h in opened_handles:
            h.close()

# Test Input Validation Edge Cases
print("\n--- Testing Input Validation Edge Cases ---")

# 1. Missing files
res_missing = requests.post(f"{BASE_URL}/scan", data={"device_type": "cisco_ios"}, timeout=5)
print(f"POST /scan (missing file) -> Status: {res_missing.status_code}")
(RESPONSES_DIR / "err_missing_file.json").write_text(json.dumps(res_missing.json(), indent=2), encoding="utf-8")

# 2. Unsupported device type
res_dev = requests.post(f"{BASE_URL}/scan", data={"device_type": "juniper_junos"}, files=[("files", ("test.cfg", b"hostname router", "text/plain"))], timeout=5)
print(f"POST /scan (unsupported device type) -> Status: {res_dev.status_code}")
(RESPONSES_DIR / "err_unsupported_device.json").write_text(json.dumps(res_dev.json(), indent=2), encoding="utf-8")

# 3. Path traversal filename
res_trav = requests.post(f"{BASE_URL}/scan", files=[("files", ("../../../../etc/passwd", b"hostname router1\nservice password-encryption", "text/plain"))], timeout=5)
print(f"POST /scan (path traversal filename) -> Status: {res_trav.status_code}")
(RESPONSES_DIR / "path_traversal.json").write_text(json.dumps(res_trav.json(), indent=2), encoding="utf-8")

# 4. Long filename
long_name = ("a" * 300) + ".txt"
res_long = requests.post(f"{BASE_URL}/scan", files=[("files", (long_name, b"hostname router2\nservice password-encryption", "text/plain"))], timeout=5)
print(f"POST /scan (long filename) -> Status: {res_long.status_code}")
(RESPONSES_DIR / "long_filename.json").write_text(json.dumps(res_long.json(), indent=2), encoding="utf-8")

# 5. Non-UTF8 payload
res_non_utf8 = requests.post(f"{BASE_URL}/scan", files=[("files", ("binary.cfg", b"\x80\x81\xFF\xFE invalid utf8 \xAA", "application/octet-stream"))], timeout=5)
print(f"POST /scan (non-UTF8) -> Status: {res_non_utf8.status_code}")
(RESPONSES_DIR / "non_utf8.json").write_text(json.dumps(res_non_utf8.json(), indent=2), encoding="utf-8")

# 6. GET /scans/<scan_id> persistence test
print("\n--- Testing GET /scans/<scan_id> Persistence ---")
if created_scan_ids:
    target_scan_id = created_scan_ids[0]
    res_get = requests.get(f"{BASE_URL}/scans/{target_scan_id}", timeout=5)
    print(f"GET /scans/{target_scan_id} -> Status: {res_get.status_code}")
    (RESPONSES_DIR / "get_scan_valid.json").write_text(json.dumps(res_get.json(), indent=2), encoding="utf-8")

res_404 = requests.get(f"{BASE_URL}/scans/scan_does_not_exist_99999", timeout=5)
print(f"GET /scans/scan_does_not_exist_99999 -> Status: {res_404.status_code}")
(RESPONSES_DIR / "get_scan_404.json").write_text(json.dumps(res_404.json(), indent=2), encoding="utf-8")

# Save summary of all executed requests
(REPO_ROOT / "audit" / "blackbox_execution_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print("\nBlack-box execution completed successfully!")
