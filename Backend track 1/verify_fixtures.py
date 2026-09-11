import json
from fastapi.testclient import TestClient
from app.main import app, get_db
from app.models import ScanRequest, UploadObject
from app.db import get_connection, init_db
from app.repository import ScanRepository
from app.service import run_scan
import hashlib

def verify_fixtures():
    # Setup test DB
    conn = get_connection()
    init_db(conn)
    repo = ScanRepository(conn)
    client = TestClient(app)

    fixtures = ["compliant.txt", "failing.txt", "ambiguous.txt"]
    
    for fname in fixtures:
        print(f"\n--- Verifying {fname} ---")
        with open(f"tests/fixtures/{fname}", "rb") as f:
            content = f.read()
            
        sha256 = hashlib.sha256(content).hexdigest()
        req = ScanRequest(
            upload=UploadObject(
                original_filename=fname,
                content=content,
                content_type="text/plain",
                size_bytes=len(content),
                sha256=sha256,
                format_hint=None
            )
        )
        
        # 1. Direct Service Result
        service_res = run_scan(req, repo)
        print(f"Service status: {service_res.status}, summary: {service_res.summary.compliance_percent}%")
        
        # 2. Persisted SQLite Result
        db_res = repo.get_scan(service_res.scan_id)
        print(f"DB status: {db_res.status}, summary: {db_res.summary.compliance_percent}%")
        
        assert service_res.status == db_res.status
        assert service_res.summary.compliance_percent == db_res.summary.compliance_percent
        
        # 3. API Response
        files = {"file": (fname, content, "text/plain")}
        api_res = client.post("/scan", files=files)
        api_data = api_res.json()
        print(f"API status: {api_data['status']}, summary: {api_data['summary']['compliance_percent']}%")
        
        assert api_data["status"] == service_res.status.value if hasattr(service_res.status, 'value') else service_res.status
        assert api_data["summary"]["compliance_percent"] == service_res.summary.compliance_percent
        
        print("PASS: Business fields agree across all 3 outputs.")

if __name__ == "__main__":
    verify_fixtures()
