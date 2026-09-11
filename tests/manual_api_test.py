"""Manual API verification script testing live endpoints against fixtures."""

import requests

url = "http://127.0.0.1:5000/scan"

test_cases = [
    ("1. Compliant Router", [("files", ("compliant.txt", open("sample_data/compliant_router.txt", "rb"), "text/plain"))]),
    ("2. Failing Router", [("files", ("failing.txt", open("sample_data/failing_router.txt", "rb"), "text/plain"))]),
    ("3. Ambiguous Router", [("files", ("ambiguous.txt", open("sample_data/ambiguous_router.txt", "rb"), "text/plain"))]),
    ("4. Garbage Input", [("files", ("garbage.txt", open("sample_data/edge_cases/garbage.txt", "rb"), "text/plain"))]),
    ("5. Secret Fixture (Mixed)", [("files", ("mixed_secrets.txt", open("sample_data/security/mixed_secrets.txt", "rb"), "text/plain"))]),
    (
        "6. Multi-File Scan",
        [
            ("files", ("compliant.txt", open("sample_data/compliant_router.txt", "rb"), "text/plain")),
            ("files", ("failing.txt", open("sample_data/failing_router.txt", "rb"), "text/plain")),
            ("files", ("secondary.txt", open("sample_data/scenarios/multi_device_secondary.txt", "rb"), "text/plain")),
        ],
    ),
    ("7. Remediation Demo", [("files", ("remediation.txt", open("sample_data/scenarios/remediation_demo.txt", "rb"), "text/plain"))]),
]

print("=" * 80)
print("PHOENIX PROTOCOL MANUAL API TEST OBSERVATIONS")
print("=" * 80)

for label, files in test_cases:
    resp = requests.post(url, data={"device_type": "cisco_ios"}, files=files)
    print(f"\n[{label}] — HTTP {resp.status_code}")
    if resp.status_code in (200, 201):
        data = resp.json()
        print(f"  Scan ID:          {data.get('scan_id')}")
        print(f"  Status:           {data.get('status')}")
        print(f"  Compliance Score: {data.get('compliance_score')}%")
        print(f"  Devices Count:    {len(data.get('devices', []))}")
        for dev in data.get("devices", []):
            print(f"    * Device: {dev.get('name')} (source: {dev.get('source_filename')})")
            print(f"      Parse Status: {dev.get('parse_status')}")
            print(f"      Score:        {dev.get('compliance_score')}%")
            print(f"      Rules:        P:{dev.get('summary', {}).get('passed_rules')} F:{dev.get('summary', {}).get('failed_rules')} W:{dev.get('summary', {}).get('warning_rules')} E:{dev.get('summary', {}).get('error_rules')}")
    else:
        print(f"  Error: {resp.text}")
