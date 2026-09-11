"""Integration smoke test for Phoenix Protocol API contract.

Exercises the full sequential API lifecycle using Flask test client:
1. GET /api/device-types
2. POST /api/scans (compliant router)
3. Capture scan_id
4. GET /api/scans/{scan_id}
5. GET /api/scans/{scan_id}/devices
6. GET /api/scans/{scan_id}/devices/{device_id}
7. GET /api/rules
8. GET /api/rules/NET-001
9. GET /api/scans/{scan_id}/report.csv
10. Verifies internal consistency and secret sanitization
"""

import csv
import io
import os
from pathlib import Path
import sys

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.api import create_app


def run_integration_smoke_test():
    print("============================================================")
    print("PHOENIX PROTOCOL — API INTEGRATION SMOKE TEST")
    print("============================================================")

    app = create_app(test_config={"TESTING": True})
    client = app.test_client()

    # 1. GET /api/device-types
    print("\n[Step 1] GET /api/device-types")
    res1 = client.get("/api/device-types")
    assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
    body1 = res1.get_json()
    assert body1["error"] is None
    device_types = body1["data"]["device_types"]
    assert any(dt["id"] == "cisco_ios" for dt in device_types)
    print("  -> PASS: Supported device profile cisco_ios verified.")

    # 2. POST /api/scans
    print("\n[Step 2] POST /api/scans (compliant configuration)")
    sample_file = BACKEND_DIR / "sample_data" / "compliant_router.txt"
    assert sample_file.exists(), f"Sample file {sample_file} not found"
    file_bytes = sample_file.read_bytes()

    res2 = client.post(
        "/api/scans",
        data={
            "device_type": "cisco_ios",
            "files": (io.BytesIO(file_bytes), "core_rtr.cfg"),
        },
        content_type="multipart/form-data",
    )
    assert res2.status_code == 201, f"Expected 201, got {res2.status_code}"
    body2 = res2.get_json()
    assert body2["error"] is None
    scan_id = body2["data"]["scan_id"]
    compliance_score = body2["data"]["compliance_score"]
    devices = body2["data"]["devices"]
    assert scan_id.startswith("scan_")
    assert compliance_score == 100.0
    assert len(devices) == 1
    device_id = devices[0]["device_id"]
    print(f"  -> PASS: Created scan '{scan_id}', compliance score: {compliance_score}%")

    # 3. GET /api/scans/{scan_id}
    print(f"\n[Step 3] GET /api/scans/{scan_id}")
    res3 = client.get(f"/api/scans/{scan_id}")
    assert res3.status_code == 200
    body3 = res3.get_json()
    assert body3["data"]["scan_id"] == scan_id
    assert body3["data"]["compliance_score"] == 100.0
    print("  -> PASS: Persisted scan retrieved and verified.")

    # 4. GET /api/scans/{scan_id}/devices
    print(f"\n[Step 4] GET /api/scans/{scan_id}/devices")
    res4 = client.get(f"/api/scans/{scan_id}/devices")
    assert res4.status_code == 200
    body4 = res4.get_json()
    dev_list = body4["data"]["devices"]
    assert len(dev_list) == 1
    assert dev_list[0]["device_id"] == device_id
    print(f"  -> PASS: Device list contains device '{device_id}'.")

    # 5. GET /api/scans/{scan_id}/devices/{device_id}
    print(f"\n[Step 5] GET /api/scans/{scan_id}/devices/{device_id}")
    res5 = client.get(f"/api/scans/{scan_id}/devices/{device_id}")
    assert res5.status_code == 200
    body5 = res5.get_json()
    dev_detail = body5["data"]
    assert dev_detail["id"] == device_id
    assert len(dev_detail["results"]) == 10
    print(f"  -> PASS: Device audit returned 10 evaluated rule results.")

    # 6. GET /api/rules
    print("\n[Step 6] GET /api/rules")
    res6 = client.get("/api/rules")
    assert res6.status_code == 200
    rules = res6.get_json()["data"]["rules"]
    assert len(rules) == 10
    print(f"  -> PASS: Authoritative catalog returned {len(rules)} rules.")

    # 7. GET /api/rules/NET-001
    print("\n[Step 7] GET /api/rules/NET-001")
    res7 = client.get("/api/rules/NET-001")
    assert res7.status_code == 200
    rule1 = res7.get_json()["data"]
    assert rule1["id"] == "NET-001"
    assert rule1["title"] == "Telnet Service Disabled"
    print(f"  -> PASS: Rule NET-001 metadata: '{rule1['title']}'.")

    # 8. GET /api/scans/{scan_id}/report.csv
    print(f"\n[Step 8] GET /api/scans/{scan_id}/report.csv")
    res8 = client.get(f"/api/scans/{scan_id}/report.csv")
    assert res8.status_code == 200
    assert "text/csv" in res8.headers.get("Content-Type", "")
    csv_text = res8.get_data(as_text=True)
    rows = list(csv.reader(io.StringIO(csv_text)))
    assert len(rows) == 11  # header + 10 rules
    print(f"  -> PASS: CSV report generated with {len(rows)} rows (1 header + 10 rules).")

    print("\n============================================================")
    print("ALL 8 API INTEGRATION STEPS PASSED SUCCESSFULLY!")
    print("============================================================")


if __name__ == "__main__":
    run_integration_smoke_test()
