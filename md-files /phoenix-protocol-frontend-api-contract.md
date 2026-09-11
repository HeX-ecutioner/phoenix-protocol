# Phoenix Protocol Frontend API Integration Contract

## Purpose

This document defines how the frontend communicates with the Phoenix Protocol backend. The frontend should use this contract instead of guessing endpoint names or response fields.

The backend is the source of truth for device parsing, compliance results, evidence, severity, remediation, and summary calculations.

## Base URL

Use an environment variable for the API base URL:

```text
VITE_API_BASE_URL=http://localhost:5000
```

If the frontend and backend are served by the same Flask application, the base URL may be empty and requests can use relative paths.

Example API helper:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const message = body?.error?.message || "The request could not be completed.";
    const error = new Error(message);
    error.status = response.status;
    error.code = body?.error?.code;
    error.details = body?.error?.details || [];
    throw error;
  }

  return body;
}
```

## Common response shapes

### Success

```json
{
  "data": {},
  "error": null,
  "request_id": "req-123"
}
```

### Error

```json
{
  "data": null,
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "Only text configuration files are accepted.",
    "details": []
  },
  "request_id": "req-124"
}
```

The frontend should show `error.message` to the user when it is safe and useful. It should not show stack traces or raw backend internals.

## Endpoint 1: Health check

### Request

```text
GET /health
```

### Use

This can be used for a developer diagnostics screen or deployment verification. It is not required in the main user workflow.

## Endpoint 2: Load device types

### Request

```text
GET /api/device-types
```

### Response

```json
{
  "data": {
    "device_types": [
      {
        "id": "cisco-like-router",
        "name": "Cisco-like router configuration",
        "vendor": "cisco-like",
        "parser_version": "1.0.0"
      }
    ]
  },
  "error": null,
  "request_id": "req-125"
}
```

### Frontend behavior

- Show a loading state in the selector.
- Select the first option only if the product decision allows it.
- Show a friendly error if no device types can be loaded.
- Do not hard-code a device type when the endpoint is available.

## Endpoint 3: Create a scan

### Request

```text
POST /api/scans
Content-Type: multipart/form-data
```

Form fields:

- `device_type`: selected device-type ID.
- `files`: one or more configuration files.

Example:

```javascript
const formData = new FormData();
formData.append("device_type", deviceType);
selectedFiles.forEach((file) => formData.append("files", file));

const response = await apiRequest("/api/scans", {
  method: "POST",
  body: formData,
});
```

Do not manually set `Content-Type` when using `FormData`. The browser adds the multipart boundary.

### Success response

Status: `201 Created`

```json
{
  "data": {
    "scan": {
      "id": "scan-001",
      "created_at": "2026-09-11T09:00:00Z",
      "completed_at": "2026-09-11T09:00:03Z",
      "device_type": "cisco-like-router",
      "status": "completed",
      "parser_version": "1.0.0",
      "rule_set_version": "1.0.0",
      "summary": {
        "device_count": 3,
        "total_rules_evaluated": 30,
        "pass_count": 21,
        "fail_count": 6,
        "warning_count": 3,
        "not_applicable_count": 0,
        "error_count": 0,
        "compliance_percentage": 77.78,
        "high_severity_failures": 4
      },
      "devices": [
        {
          "id": "dev-001",
          "display_name": "compliant_router.txt",
          "parse_status": "parsed"
        }
      ]
    }
  },
  "error": null,
  "request_id": "req-126"
}
```

### Frontend behavior

- Disable the scan button before making the request.
- Set `isScanning` to `true`.
- On success, save the scan ID.
- Navigate to the dashboard using the scan ID.
- On failure, show a friendly message and allow retry.
- Always reset the loading state in a `finally` block.

## Endpoint 4: Get scan summary

### Request

```text
GET /api/scans/{scan_id}
```

### Frontend behavior

Use this endpoint to refresh dashboard summary data. Do not calculate summary counts independently from device rows unless the backend contract explicitly requires it.

## Endpoint 5: List devices

### Request

```text
GET /api/scans/{scan_id}/devices
```

### Response shape

```json
{
  "data": {
    "scan_id": "scan-001",
    "devices": [
      {
        "id": "dev-001",
        "display_name": "compliant_router.txt",
        "vendor": "cisco-like",
        "device_type": "cisco-like-router",
        "parse_status": "parsed",
        "summary": {
          "pass_count": 9,
          "fail_count": 0,
          "warning_count": 0,
          "error_count": 0,
          "high_severity_failures": 0
        }
      }
    ]
  },
  "error": null,
  "request_id": "req-127"
}
```

## Endpoint 6: Get device results

### Request

```text
GET /api/scans/{scan_id}/devices/{device_id}
```

Optional query parameters:

```text
?status=fail&severity=high
```

### Response shape

```json
{
  "data": {
    "device": {
      "id": "dev-002",
      "scan_id": "scan-001",
      "display_name": "failing_router.txt",
      "vendor": "cisco-like",
      "device_type": "cisco-like-router",
      "parse_status": "parsed",
      "results": [
        {
          "rule_id": "NET-001",
          "title": "Telnet is disabled",
          "status": "fail",
          "severity": "high",
          "evidence": "line 24: transport input telnet",
          "evidence_start_line": 24,
          "evidence_end_line": 24,
          "message": "Telnet appears to be enabled.",
          "remediation": "Disable Telnet after confirming that secure administration is available.",
          "evaluated_at": "2026-09-11T09:00:02Z",
          "rule_version": "1.0.0"
        }
      ]
    }
  },
  "error": null,
  "request_id": "req-128"
}
```

The frontend must render evidence as escaped text. Do not use raw HTML rendering for backend-provided evidence.

## Endpoint 7: List rules

### Request

```text
GET /api/rules
```

Optional query parameters:

```text
?device_type=cisco-like-router&severity=high&active=true
```

Use this data for the rule-library view. Do not duplicate rule descriptions manually in multiple components.

## Endpoint 8: Get one rule

### Request

```text
GET /api/rules/{rule_id}
```

Use this endpoint when the user opens detailed rule information.

## Endpoint 9: Download CSV

### Request

```text
GET /api/scans/{scan_id}/report.csv
```

Use a normal browser navigation or an anchor link when possible:

```javascript
window.location.href = `${API_BASE_URL}/api/scans/${scanId}/report.csv`;
```

The backend should return a downloadable file.

## Endpoint 10: Download HTML

### Request

```text
GET /api/scans/{scan_id}/report.html
```

Only display this button if the backend supports it. The frontend should not fail if HTML export is not implemented.

## HTTP error handling

| Status | Frontend message |
|---:|---|
| `400` | Check the selected device type and files, then try again. |
| `404` | The requested scan, device, or rule could not be found. |
| `413` | The upload is too large. Choose fewer or smaller files. |
| `422` | Phoenix Protocol could not interpret one of the configurations. Review the warning. |
| `500` | The analysis service encountered a problem. Try again or contact the backend owner. |
| Network failure | The analysis service could not be reached. Check that the backend is running. |

## API service module

Suggested functions:

```javascript
export async function getDeviceTypes() {}
export async function createScan(deviceType, files) {}
export async function getScan(scanId) {}
export async function getDevices(scanId) {}
export async function getDevice(scanId, deviceId, filters = {}) {}
export async function getRules(filters = {}) {}
export async function getRule(ruleId) {}
export function getCsvReportUrl(scanId) {}
export function getHtmlReportUrl(scanId) {}
```

Keep URL construction, fetch calls, JSON parsing, and error conversion in this module. UI components should focus on rendering and user interaction.

## Mock data requirement

Before the backend is available, use local mock data that matches this contract exactly. When the backend arrives, changing from mock mode to real mode should require changing only the API service configuration.

Do not create a second frontend-only result format.

## Integration checklist

- Device type endpoint loads.
- File upload uses `FormData`.
- `Content-Type` is not manually set for multipart requests.
- Scan button disables during request.
- Scan ID is saved after success.
- Dashboard uses API summary values.
- Device table uses API device summaries.
- Device detail uses API rule results.
- Filters work without changing compliance decisions.
- CSV URL uses the correct scan ID.
- Error messages do not reveal backend internals.
- Secret-like evidence is displayed only as returned by the backend.
