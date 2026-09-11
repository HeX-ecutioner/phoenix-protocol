"""Black-box HTTP verification script testing the live running Flask server.

Exercises every endpoint over real HTTP (http://127.0.0.1:5000):
1. GET /health
2. GET /api/device-types
3. POST /api/scans (compliant_router.txt)
4. POST /api/scans (failing_router.txt)
5. POST /api/scans (mixed_secrets.txt)
6. POST /api/scans (multi-file scan)
7. GET /api/scans/{scan_id}
8. GET /api/scans/{scan_id}/devices
9. GET /api/scans/{scan_id}/devices/{device_id}
10. GET /api/rules
11. GET /api/rules/NET-001
12. GET /api/scans/{scan_id}/report.csv
13. Verifies secret redaction in both JSON and CSV
"""

import csv
import io
import json
from pathlib import Path
import socket
import sys
import threading
import time
import requests

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.api import create_app

BASE_URL = "http://127.0.0.1:5000"
REPO_ROOT = BACKEND_DIR
SAMPLE_DATA = REPO_ROOT / "sample_data"


def is_server_running(host="127.0.0.1", port=5000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def test_live_http():
    print("============================================================")
    print("PHOENIX PROTOCOL — LIVE HTTP BLACK-BOX VERIFICATION")
    print(f"Target Server: {BASE_URL}")
    print("============================================================")

    server = None
    if not is_server_running():
        from werkzeug.serving import make_server
        app = create_app()
        server = make_server("127.0.0.1", 5000, app)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        time.sleep(0.5)
        print("  [INFO] Auto-started background test server on 127.0.0.1:5000")

    # 1. GET /health
    print("\n[1] Testing GET /health ...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    print(f"    Status: {r.status_code}, Body: {r.json()}")

    # 2. GET /api/device-types
    print("\n[2] Testing GET /api/device-types ...")
    r = requests.get(f"{BASE_URL}/api/device-types")
    assert r.status_code == 200
    body = r.json()
    assert body["error"] is None
    print(f"    Status: {r.status_code}, Supported Profiles: {[p['id'] for p in body['data']['device_types']]}")

    # 3. POST /api/scans (compliant)
    print("\n[3] Testing POST /api/scans (compliant_router.txt) ...")
    f_comp = SAMPLE_DATA / "compliant_router.txt"
    files = {"files": ("compliant_router.txt", f_comp.read_bytes(), "text/plain")}
    data = {"device_type": "cisco_ios"}
    r = requests.post(f"{BASE_URL}/api/scans", files=files, data=data)
    assert r.status_code == 201
    comp_scan = r.json()["data"]
    comp_scan_id = comp_scan["scan_id"]
    comp_dev_id = comp_scan["devices"][0]["device_id"]
    print(f"    Status: {r.status_code}, Scan ID: {comp_scan_id}, Score: {comp_scan['compliance_score']}%")

    # 4. POST /api/scans (failing)
    print("\n[4] Testing POST /api/scans (failing_router.txt) ...")
    f_fail = SAMPLE_DATA / "failing_router.txt"
    files = {"files": ("failing_router.txt", f_fail.read_bytes(), "text/plain")}
    r = requests.post(f"{BASE_URL}/api/scans", files=files, data=data)
    assert r.status_code == 201
    fail_scan = r.json()["data"]
    print(f"    Status: {r.status_code}, Scan ID: {fail_scan['scan_id']}, Score: {fail_scan['compliance_score']}%, High Failures: {fail_scan['summary']['high_severity_failures']}")

    # 5. POST /api/scans (mixed_secrets)
    print("\n[5] Testing POST /api/scans (mixed_secrets.txt) ...")
    f_sec = SAMPLE_DATA / "security" / "mixed_secrets.txt"
    files = {"files": ("mixed_secrets.txt", f_sec.read_bytes(), "text/plain")}
    r = requests.post(f"{BASE_URL}/api/scans", files=files, data=data)
    assert r.status_code == 201
    sec_scan = r.json()["data"]
    sec_scan_id = sec_scan["scan_id"]
    print(f"    Status: {r.status_code}, Scan ID: {sec_scan_id}")
    # Verify no raw secrets in returned JSON
    json_text = r.text
    forbidden = ["Cisco1234!", "SuperSecretKey99", "RadiusSecret2026", "SecretTacacsKey", "readcommunity99"]
    for s in forbidden:
        assert s not in json_text, f"Secret '{s}' found in API JSON response!"
    print("    Secret Sanitization: PASS (no raw credentials leaked in JSON)")

    # 6. POST /api/scans (multi-file scan)
    print("\n[6] Testing POST /api/scans (multi-file scan) ...")
    multi_files = [
        ("files", ("comp.cfg", f_comp.read_bytes(), "text/plain")),
        ("files", ("fail.cfg", f_fail.read_bytes(), "text/plain")),
    ]
    r = requests.post(f"{BASE_URL}/api/scans", files=multi_files, data=data)
    assert r.status_code == 201
    multi_scan = r.json()["data"]
    print(f"    Status: {r.status_code}, Devices: {len(multi_scan['devices'])}, Score: {multi_scan['compliance_score']}%")

    # 7. GET /api/scans/{scan_id}
    print(f"\n[7] Testing GET /api/scans/{comp_scan_id} ...")
    r = requests.get(f"{BASE_URL}/api/scans/{comp_scan_id}")
    assert r.status_code == 200
    retrieved = r.json()["data"]
    assert retrieved["scan_id"] == comp_scan_id
    print(f"    Status: {r.status_code}, Verified scan retrieval: {retrieved['scan_id']}")

    # 8. GET /api/scans/{scan_id}/devices
    print(f"\n[8] Testing GET /api/scans/{comp_scan_id}/devices ...")
    r = requests.get(f"{BASE_URL}/api/scans/{comp_scan_id}/devices")
    assert r.status_code == 200
    devs = r.json()["data"]["devices"]
    assert len(devs) == 1
    print(f"    Status: {r.status_code}, Device ID: {devs[0]['device_id']}, Display: {devs[0]['display_name']}")

    # 9. GET /api/scans/{scan_id}/devices/{device_id}
    print(f"\n[9] Testing GET /api/scans/{comp_scan_id}/devices/{comp_dev_id} ...")
    r = requests.get(f"{BASE_URL}/api/scans/{comp_scan_id}/devices/{comp_dev_id}")
    assert r.status_code == 200
    dev_detail = r.json()["data"]
    assert dev_detail["id"] == comp_dev_id
    assert len(dev_detail["results"]) == 10
    print(f"    Status: {r.status_code}, Evaluated Rules: {len(dev_detail['results'])}, First Rule: {dev_detail['results'][0]['title']}")

    # 10. GET /api/rules
    print("\n[10] Testing GET /api/rules ...")
    r = requests.get(f"{BASE_URL}/api/rules")
    assert r.status_code == 200
    rules = r.json()["data"]["rules"]
    assert len(rules) == 10
    print(f"    Status: {r.status_code}, Rule Count: {len(rules)}, IDs: {[r['id'] for r in rules]}")

    # 11. GET /api/rules/NET-001
    print("\n[11] Testing GET /api/rules/NET-001 ...")
    r = requests.get(f"{BASE_URL}/api/rules/NET-001")
    assert r.status_code == 200
    rule = r.json()["data"]
    assert rule["id"] == "NET-001"
    print(f"    Status: {r.status_code}, Title: {rule['title']}, Severity: {rule['severity']}")

    # 12. GET /api/scans/{scan_id}/report.csv
    print(f"\n[12] Testing GET /api/scans/{sec_scan_id}/report.csv ...")
    r = requests.get(f"{BASE_URL}/api/scans/{sec_scan_id}/report.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("Content-Type", "")
    assert f'filename="scan_{sec_scan_id}_report.csv"' in r.headers.get("Content-Disposition", "")
    csv_text = r.text
    rows = list(csv.reader(io.StringIO(csv_text)))
    print(f"    Status: {r.status_code}, Header: {rows[0]}")
    print(f"    Total Rows in CSV: {len(rows)} (1 header + {len(rows)-1} rule findings)")

    # 13. CSV secret sanitization verification
    for s in forbidden:
        assert s not in csv_text, f"Secret '{s}' leaked in CSV report!"
    print("    CSV Secret Sanitization: PASS (zero credentials in CSV report)")

    print("\n============================================================")
    print("ALL LIVE HTTP BLACK-BOX VERIFICATIONS PASSED!")
    print("============================================================")


if __name__ == "__main__":
    test_live_http()
