# Phoenix Protocol — Authoritative Integration Contract

This document specifies the authoritative HTTP REST API contract exposed by the Phoenix Protocol backend under `/api/...`. It serves as the formal integration target for the Phoenix Protocol frontend.

---

## 1. Architectural Principles & Boundaries

1. **Deterministic Compliance Authority**:
   - The compliance engine (`NET-001` through `NET-010`) is authoritative. Compliance verdicts, severity, evidence lines, and scores are determined by deterministic rule evaluation, never overridden by AI.
2. **Read-Only / Air-Gapped**:
   - Configuration files are analyzed statically offline. No active network discovery or direct device execution (no SSH/Paramiko/Netmiko) occurs.
3. **Zero Configuration Persistence**:
   - Complete raw configuration files are never stored in SQLite or logs. Only normalized tokens, extracted evidence, and audit metadata are retained.
4. **Secret Sanitization**:
   - Plaintext passwords, type 7 credentials, private hashes, SNMP communities, and pre-shared keys are redacted (`[REDACTED]`) before evaluation, in API responses, and in exported CSV reports.
5. **Hackathon MVP Scope**:
   - Current device support: `cisco_ios` (with aliases `cisco-like-router`, `cisco`, `cisco-like`).
   - Authentication: Unauthenticated local service for hackathon MVP.

---

## 2. Global Envelopes & Conventions

### 2.1 Success Envelope
All `/api/...` endpoints return an HTTP status in the `2xx` range wrapped in:
```json
{
  "data": { ... },
  "error": null,
  "request_id": "req-9a3b4c5d6e7f"
}
```

### 2.2 Error Envelope
All client and server errors on `/api/...` endpoints return an HTTP status in the `4xx` or `5xx` range wrapped in:
```json
{
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of error.",
    "details": []
  },
  "request_id": "req-9a3b4c5d6e7f"
}
```

Standard error codes:
- `UNSUPPORTED_DEVICE_TYPE` (400)
- `MISSING_FILES` (400)
- `EMPTY_FILE` (400)
- `FILE_TOO_LARGE` (413)
- `PAYLOAD_TOO_LARGE` (413)
- `UNSUPPORTED_FILE_FORMAT` (422)
- `SCAN_FAILED` (422)
- `SCAN_NOT_FOUND` (404)
- `DEVICE_NOT_FOUND` (404)
- `DEVICE_SCAN_MISMATCH` (404)
- `RULE_NOT_FOUND` (404)
- `NOT_FOUND` (404)
- `INTERNAL_ERROR` (500)

---

## 3. CORS Configuration

- Allowed development origins by default:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- Configurable via `CORS_ALLOWED_ORIGINS` environment variable (comma-separated).
- Methods allowed: `GET, POST, OPTIONS`.
- Headers allowed: `Content-Type, Authorization, X-Requested-With`.
- Pre-flight `OPTIONS` requests receive an immediate `204 No Content` with appropriate CORS headers.

---

## 4. Endpoints Specification

### 4.1 GET /api/device-types
Returns list of supported device profiles.

- **Method**: `GET`
- **Frontend Method**: `api.getDeviceTypes()`
- **Request**: No body
- **Response Shape (200 OK)**:
```json
{
  "data": {
    "device_types": [
      {
        "id": "cisco_ios",
        "name": "Cisco IOS",
        "vendor": "Cisco",
        "supported": true,
        "parser_version": "1.0.0"
      }
    ]
  },
  "error": null,
  "request_id": "req-..."
}
```

---

### 4.2 POST /api/scans
Uploads one or more configuration files and executes compliance audit.

- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Frontend Method**: `api.createScan(deviceType, files)`
- **Parameters**:
  - `device_type` (form field, optional): Target device profile (defaults to `"cisco_ios"`; accepts aliases `"cisco-like-router"`, `"cisco"`).
  - `files` (form file, required): One or more text configuration files (also supports legacy form field `file`).
- **Response Shape (201 Created)**:
```json
{
  "data": {
    "scan_id": "scan_5b6c6f39dda346d99f4263c3a1df969a",
    "id": "scan_5b6c6f39dda346d99f4263c3a1df969a",
    "status": "completed",
    "device_type": "cisco_ios",
    "parser_version": "1.0.0",
    "rule_set_version": "1.0.0",
    "created_at": "2026-09-12T01:00:00Z",
    "completed_at": "2026-09-12T01:00:01Z",
    "compliance_score": 100.0,
    "summary": {
      "device_count": 1,
      "total_rules": 10,
      "total_rules_evaluated": 10,
      "passed_rules": 10,
      "failed_rules": 0,
      "warning_rules": 0,
      "not_applicable_rules": 0,
      "error_rules": 0,
      "pass_count": 10,
      "fail_count": 0,
      "warning_count": 0,
      "error_count": 0,
      "high_severity_failures": 0,
      "compliance_percentage": 100.0,
      "tested_rule_compliance": 100.0
    },
    "devices": [
      {
        "id": "dd91f630-991f-4d73-bc85-707bff4dcff0",
        "device_id": "dd91f630-991f-4d73-bc85-707bff4dcff0",
        "scan_id": "scan_5b6c6f39dda346d99f4263c3a1df969a",
        "name": "CORE-RTR-01",
        "display_name": "CORE-RTR-01",
        "vendor": "Cisco",
        "device_type": "cisco_ios",
        "source_filename": "compliant_router.txt",
        "parse_status": "success",
        "line_count": 45,
        "compliance_score": 100.0,
        "summary": {
          "total_rules": 10,
          "passed_rules": 10,
          "failed_rules": 0,
          "warning_rules": 0,
          "error_rules": 0,
          "pass_count": 10,
          "fail_count": 0,
          "warning_count": 0,
          "error_count": 0,
          "high_severity_failures": 0,
          "compliance_percentage": 100.0
        },
        "results": [
          {
            "rule_id": "NET-001",
            "title": "Telnet Service Disabled",
            "status": "pass",
            "severity": "high",
            "evidence": "line 24: transport input ssh",
            "evidence_line_range": [24, 24],
            "evidence_start_line": 24,
            "evidence_end_line": 24,
            "message": "Telnet is disabled on all management lines.",
            "remediation": "line vty 0 4\n transport input ssh",
            "evaluation_timestamp": "2026-09-12T01:00:01Z",
            "evaluated_at": "2026-09-12T01:00:01Z",
            "rule_version": "1.0.0"
          }
        ]
      }
    ],
    "scan": { ... }
  },
  "error": null,
  "request_id": "req-..."
}
```

*Frontend Notes*:
- `ScannerConsole.jsx` navigates to `/scans/${response.data.scan_id}`.
- Both `data.scan_id` and `data.id` are provided at top level and nested in `data.scan`.

---

### 4.3 GET /api/scans/{scan_id}
Retrieves persisted scan results.

- **Method**: `GET`
- **Frontend Method**: `api.getScan(scanId)`
- **Response Shape (200 OK)**: Identical to the `data` object returned by `POST /api/scans`.
- **Error (404 Not Found)**:
```json
{
  "data": null,
  "error": {
    "code": "SCAN_NOT_FOUND",
    "message": "No scan found with ID 'scan_123'.",
    "details": []
  },
  "request_id": "req-..."
}
```

---

### 4.4 GET /api/scans/{scan_id}/devices
Retrieves list of devices belonging to a scan.

- **Method**: `GET`
- **Frontend Method**: `api.getDevices(scanId)`
- **Response Shape (200 OK)**:
```json
{
  "data": {
    "scan_id": "scan_5b6c6f39dda346d99f4263c3a1df969a",
    "devices": [
      {
        "id": "dd91f630-991f-4d73-bc85-707bff4dcff0",
        "device_id": "dd91f630-991f-4d73-bc85-707bff4dcff0",
        "scan_id": "scan_5b6c6f39dda346d99f4263c3a1df969a",
        "name": "CORE-RTR-01",
        "display_name": "CORE-RTR-01",
        "vendor": "Cisco",
        "device_type": "cisco_ios",
        "source_filename": "compliant_router.txt",
        "parse_status": "success",
        "line_count": 45,
        "compliance_score": 100.0,
        "summary": {
          "total_rules": 10,
          "passed_rules": 10,
          "failed_rules": 0,
          "warning_rules": 0,
          "error_rules": 0,
          "pass_count": 10,
          "fail_count": 0,
          "warning_count": 0,
          "error_count": 0,
          "high_severity_failures": 0,
          "compliance_percentage": 100.0
        }
      }
    ]
  },
  "error": null,
  "request_id": "req-..."
}
```

*Frontend Notes*:
- `DashboardPage.jsx` sets devices using `devicesResponse.data.devices`.
- Table columns map: `device.display_name`, `device.parse_status`, `device.summary.pass_count`, `device.summary.fail_count`, `device.summary.warning_count`, `device.summary.high_severity_failures`.

---

### 4.5 GET /api/scans/{scan_id}/devices/{device_id}
Retrieves complete device audit results and rule findings.

- **Method**: `GET`
- **Frontend Method**: `api.getDevice(scanId, deviceId)`
- **Response Shape (200 OK)**:
```json
{
  "data": {
    "device": {
      "id": "dd91f630-991f-4d73-bc85-707bff4dcff0",
      "device_id": "dd91f630-991f-4d73-bc85-707bff4dcff0",
      "scan_id": "scan_5b6c6f39dda346d99f4263c3a1df969a",
      "name": "CORE-RTR-01",
      "display_name": "CORE-RTR-01",
      "vendor": "Cisco",
      "device_type": "cisco_ios",
      "source_filename": "compliant_router.txt",
      "parse_status": "success",
      "line_count": 45,
      "error_message": null,
      "summary": { ... },
      "compliance_score": 100.0,
      "results": [
        {
          "rule_id": "NET-001",
          "title": "Telnet Service Disabled",
          "status": "pass",
          "severity": "high",
          "evidence": "line 24: transport input ssh",
          "evidence_line_range": [24, 24],
          "evidence_start_line": 24,
          "evidence_end_line": 24,
          "message": "Telnet is disabled on all management lines.",
          "remediation": "line vty 0 4\n transport input ssh",
          "evaluation_timestamp": "2026-09-12T01:00:01Z",
          "evaluated_at": "2026-09-12T01:00:01Z",
          "rule_version": "1.0.0"
        }
      ]
    }
  },
  "error": null,
  "request_id": "req-..."
}
```

*Frontend Notes*:
- `DevicePage.jsx` does `setDeviceData(response.data.device)`.
- The endpoint supports both `response.data.device` and `response.data` attributes directly.
- Returns `404` with code `DEVICE_SCAN_MISMATCH` if device exists but belongs to another scan.

---

### 4.6 GET /api/rules
Retrieves rule catalog (`NET-001` through `NET-010`).

- **Method**: `GET`
- **Frontend Method**: `api.getRules()`
- **Response Shape (200 OK)**:
```json
{
  "data": {
    "rules": [
      {
        "id": "NET-001",
        "rule_id": "NET-001",
        "name": "Telnet Service Disabled",
        "title": "Telnet Service Disabled",
        "description": "Ensure Telnet service is disabled on all management lines.",
        "technical_requirement": "Management lines (line vty) must enforce 'transport input ssh' or equivalent and disallow telnet.",
        "severity": "high",
        "device_type": "cisco_ios",
        "category": "Management Plane Security",
        "remediation": "line vty 0 4\n transport input ssh",
        "is_active": true,
        "active": true,
        "rule_version": "1.0.0"
      }
    ]
  },
  "error": null,
  "request_id": "req-..."
}
```

---

### 4.7 GET /api/rules/{rule_id}
Retrieves detailed metadata for a single rule.

- **Method**: `GET`
- **Frontend Method**: `api.getRule(ruleId)`
- **Response Shape (200 OK)**:
```json
{
  "data": {
    "id": "NET-001",
    "rule_id": "NET-001",
    "title": "Telnet Service Disabled",
    "description": "Ensure Telnet service is disabled on all management lines.",
    "technical_requirement": "...",
    "severity": "high",
    "device_type": "cisco_ios",
    "category": "Management Plane Security",
    "remediation": "...",
    "is_active": true,
    "active": true,
    "rule_version": "1.0.0"
  },
  "error": null,
  "request_id": "req-..."
}
```
- **Error (404 Not Found)**: Code `RULE_NOT_FOUND`.

---

### 4.8 GET /api/scans/{scan_id}/report.csv
Downloads full compliance report in CSV format.

- **Method**: `GET`
- **Headers**:
  - `Content-Type: text/csv; charset=utf-8`
  - `Content-Disposition: attachment; filename="scan_{scan_id}_report.csv"`
- **CSV Columns**:
  1. `scan_id`
  2. `device_id`
  3. `device_name`
  4. `vendor`
  5. `device_type`
  6. `rule_id`
  7. `status`
  8. `severity`
  9. `evidence` (sanitized)
  10. `evidence_line_range`
  11. `message`
  12. `remediation`
- **CSV Security Safeguards**:
  - All credentials, secrets, hashes, and keys are scrubbed with `sanitize_evidence`.
  - Values starting with spreadsheet formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) are escaped with a leading apostrophe (`'`) to protect against CSV formula injection.

---

## 5. Legacy Compatibility Routes

The following legacy endpoints remain active for backwards compatibility:
- `GET /health` and `GET /api/health`: Service health check.
- `POST /scan`: Legacy upload and scan route.
- `GET /scans/{scan_id}`: Legacy scan lookup route.
