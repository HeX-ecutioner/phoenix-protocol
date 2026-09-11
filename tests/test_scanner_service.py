"""Tests for scan-processing service contract (scaffolding)."""

from app.services.scanner import run_scan


def test_run_scan_contract_signature():
    """Verify run_scan adheres to required contract signature."""
    res = run_scan(
        scan_id="scan-uuid-123",
        device_type="cisco_ios",
        uploaded_files=[
            {"filename": "router.txt", "content": "hostname RTR-01\n"}
        ],
    )
    assert isinstance(res, dict)
    assert res["scan_id"] == "scan-uuid-123"
    assert res["device_type"] == "cisco_ios"
    assert "status" in res
    assert "compliance_score" in res
