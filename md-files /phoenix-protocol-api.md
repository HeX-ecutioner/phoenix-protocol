# Phoenix Protocol API Specification

**Document status:** Hackathon MVP API design  
**API style:** REST over HTTP  
**Base path:** `/api`  
**Primary purpose:** Accept sanitized network-device configuration files, evaluate deterministic security rules, and return evidence-based compliance results

## 1. API overview

Phoenix Protocol is a read-only network-configuration compliance scanner. The API provides the connection between the browser interface and the Flask backend.

The main workflow is:

```text
Upload files and device type
        ↓
Create scan
        ↓
Parse configurations
        ↓
Evaluate compliance rules
        ↓
Store scan and results
        ↓
Return dashboard data
        ↓
Download a report
```

The MVP processes a small batch synchronously. A request can upload three to five small configuration files and receive the completed results in the response. A background job system is not required for the hackathon.

## 2. API design principles

- The API is **read-only** with respect to network devices.
- Uploaded files are treated as untrusted text.
- Compliance decisions come from deterministic backend rules.
- Every result should include a status, severity, explanation, and evidence when available.
- Warnings and errors must remain visible.
- The API must not require production-device credentials.
- The API should return predictable JSON structures.
- The API should use clear HTTP status codes.

## 3. Base URL and content types

### Local development

```text
http://localhost:5000/api
```

### Hosted deployment

```text
https://your-phoenix-protocol-host.example/api
```

Requests containing files use:

```text
Content-Type: multipart/form-data
```

Normal requests and responses use:

```text
Content-Type: application/json
```

Report downloads use either:

```text
text/csv
```

or:

```text
text/html
```

## 4. Authentication approach

The private hackathon MVP does not need application-level authentication. It should run locally or behind private hosting access and should use sanitized configuration files.

If the hosting platform requires protection, use its built-in access control or a single password stored as an environment variable. Do not build user registration, password reset, role management, or multi-tenant authorization during the hackathon.

A future production API would require authentication, authorization, audit logging, rate limiting, secure file storage, and tenant isolation.

## 5. Common response format

### Successful response

```json
{
  "data": {},
  "error": null,
  "request_id": "req-123"
}
```

### Error response

```json
{
  "data": null,
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "One or more uploaded files are not supported.",
    "details": [
      {
        "filename": "router.pdf",
        "reason": "Only text configuration files are accepted."
      }
    ]
  },
  "request_id": "req-124"
}
```

The `request_id` helps developers find a request in application logs without logging sensitive configuration contents.

## 6. Endpoint summary

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check that the service is running |
| `GET` | `/api/device-types` | List supported device types |
| `POST` | `/api/scans` | Upload files and create a scan |
| `GET` | `/api/scans/{scan_id}` | Get scan summary |
| `GET` | `/api/scans/{scan_id}/devices` | List devices in a scan |
| `GET` | `/api/scans/{scan_id}/devices/{device_id}` | Get results for one device |
| `GET` | `/api/rules` | List compliance rules |
| `GET` | `/api/rules/{rule_id}` | Get one rule’s details |
| `GET` | `/api/scans/{scan_id}/report.csv` | Download a CSV report |
| `GET` | `/api/scans/{scan_id}/report.html` | Download an HTML report |

## 7. Health endpoint

### `GET /health`

Checks whether the API process is running.

#### Success response: `200 OK`

```json
{
  "status": "ok",
  "service": "phoenix-protocol-api",
  "version": "1.0.0"
}
```

This endpoint should not expose database passwords, environment variables, or detailed internal errors.

## 8. List supported device types

### `GET /api/device-types`

Returns the device types that the MVP can parse.

#### Success response: `200 OK`

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

The MVP can return one device type. A dropdown in the frontend can use this endpoint instead of hard-coding the value.

## 9. Create and run a scan

### `POST /api/scans`

Uploads one or more configuration files and evaluates them against the selected rule set.

### Request format

Use `multipart/form-data` with these fields:

| Field | Type | Required? | Description |
|---|---|---:|---|
| `device_type` | Text | Yes | Supported parser ID |
| `files` | File, repeated | Yes | One or more text configuration files |

Example command:

```bash
curl -X POST http://localhost:5000/api/scans \
  -F "device_type=cisco-like-router" \
  -F "files=@sample_data/compliant_router.txt" \
  -F "files=@sample_data/failing_router.txt" \
  -F "files=@sample_data/ambiguous_router.txt"
```

### Validation rules

The backend should reject or clearly report:

- No files supplied.
- Unsupported file type.
- File larger than the configured limit.
- Too many files in one scan.
- File that cannot be read as text.
- Unsupported device type.
- Unsafe filename.

One invalid file should not prevent valid files from being processed. The response should identify the invalid file and continue when safe to do so.

### Success response: `201 Created`

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
        },
        {
          "id": "dev-002",
          "display_name": "failing_router.txt",
          "parse_status": "parsed"
        },
        {
          "id": "dev-003",
          "display_name": "ambiguous_router.txt",
          "parse_status": "warning"
        }
      ]
    }
  },
  "error": null,
  "request_id": "req-126"
}
```

The compliance percentage represents only the tested rules. The frontend should label it **tested-rule compliance**, not overall security.

## 10. Get scan summary

### `GET /api/scans/{scan_id}`

Returns summary information for one scan.

#### Success response: `200 OK`

```json
{
  "data": {
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
    }
  },
  "error": null,
  "request_id": "req-127"
}
```

#### Not found response: `404 Not Found`

```json
{
  "data": null,
  "error": {
    "code": "SCAN_NOT_FOUND",
    "message": "The requested scan does not exist."
  },
  "request_id": "req-128"
}
```

## 11. List devices in a scan

### `GET /api/scans/{scan_id}/devices`

Returns the processed configuration files associated with a scan.

### Optional query parameters

| Parameter | Example | Purpose |
|---|---|---|
| `status` | `warning` | Filter by parser status |
| `sort` | `name` | Sort by device display name |
| `page` | `1` | Optional pagination page |
| `limit` | `50` | Maximum records returned |

#### Success response: `200 OK`

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
      },
      {
        "id": "dev-002",
        "display_name": "failing_router.txt",
        "vendor": "cisco-like",
        "device_type": "cisco-like-router",
        "parse_status": "parsed",
        "summary": {
          "pass_count": 6,
          "fail_count": 3,
          "warning_count": 1,
          "error_count": 0,
          "high_severity_failures": 3
        }
      }
    ]
  },
  "error": null,
  "request_id": "req-129"
}
```

## 12. Get one device’s rule results

### `GET /api/scans/{scan_id}/devices/{device_id}`

Returns rule-level results, evidence, explanations, and remediation guidance for one device.

### Optional query parameters

| Parameter | Example | Purpose |
|---|---|---|
| `status` | `fail` | Show only one result status |
| `severity` | `high` | Show only one severity |
| `sort` | `priority` | Put high-severity failures first |

#### Success response: `200 OK`

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
        },
        {
          "rule_id": "NET-005",
          "title": "System logging is enabled",
          "status": "warning",
          "severity": "high",
          "evidence": "No logging configuration found",
          "evidence_start_line": null,
          "evidence_end_line": null,
          "message": "The system could not confidently determine whether logging is enabled.",
          "remediation": "Review the device configuration manually and confirm the approved logging destination.",
          "evaluated_at": "2026-09-11T09:00:02Z",
          "rule_version": "1.0.0"
        }
      ]
    }
  },
  "error": null,
  "request_id": "req-130"
}
```

Evidence containing secrets must be masked before being returned by the API.

## 13. List compliance rules

### `GET /api/rules`

Returns the visible rule catalog.

### Optional query parameters

| Parameter | Example | Purpose |
|---|---|---|
| `device_type` | `cisco-like-router` | Filter rules by device type |
| `severity` | `high` | Filter rules by severity |
| `active` | `true` | Return active rules only |

#### Success response: `200 OK`

```json
{
  "data": {
    "rules": [
      {
        "id": "NET-001",
        "title": "Telnet is disabled",
        "description": "Telnet is an insecure administration method.",
        "technical_requirement": "No Telnet administration input should be enabled.",
        "severity": "high",
        "device_type": "cisco-like-router",
        "is_active": true,
        "rule_version": "1.0.0"
      }
    ]
  },
  "error": null,
  "request_id": "req-131"
}
```

## 14. Get one rule

### `GET /api/rules/{rule_id}`

Returns the full explanation of one rule.

#### Success response: `200 OK`

```json
{
  "data": {
    "id": "NET-001",
    "title": "Telnet is disabled",
    "description": "Telnet is an insecure administration method.",
    "technical_requirement": "No Telnet administration input should be enabled.",
    "severity": "high",
    "device_type": "cisco-like-router",
    "remediation": "Disable Telnet after confirming that secure administration is available.",
    "is_active": true,
    "rule_version": "1.0.0"
  },
  "error": null,
  "request_id": "req-132"
}
```

## 15. Download CSV report

### `GET /api/scans/{scan_id}/report.csv`

Generates a CSV report using the same stored results displayed in the dashboard.

### Response headers

```text
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="phoenix-protocol-scan-001.csv"
```

### Recommended CSV columns

```text
scan_id,scan_timestamp,device_name,device_type,rule_id,rule_title,status,severity,evidence,message,remediation
```

The report should escape commas, quotes, and line breaks correctly. Sensitive evidence should be masked.

## 16. Download HTML report

### `GET /api/scans/{scan_id}/report.html`

Generates a readable HTML report.

The server must escape configuration evidence before inserting it into HTML. Otherwise, a malicious uploaded text line could become browser-executable content.

### Recommended report sections

1. Scan metadata.
2. Tested-rule compliance explanation.
3. Summary counts.
4. High-severity failures.
5. Device-by-device results.
6. Evidence and remediation guidance.
7. Prototype limitations.

## 17. Error codes

| HTTP status | Error code | Meaning |
|---:|---|---|
| `400` | `INVALID_REQUEST` | Required input is missing or malformed |
| `400` | `INVALID_FILE_TYPE` | File is not a supported text configuration |
| `400` | `FILE_TOO_LARGE` | File exceeds the configured size limit |
| `400` | `TOO_MANY_FILES` | Upload exceeds the batch limit |
| `400` | `UNSUPPORTED_DEVICE_TYPE` | No parser exists for the selected type |
| `404` | `SCAN_NOT_FOUND` | Scan ID does not exist |
| `404` | `DEVICE_NOT_FOUND` | Device ID does not exist in the scan |
| `404` | `RULE_NOT_FOUND` | Rule ID does not exist |
| `409` | `SCAN_NOT_READY` | Report requested before scan completion |
| `413` | `REQUEST_TOO_LARGE` | Entire request exceeds the server limit |
| `422` | `PARSER_ERROR` | File could not be interpreted safely |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

The API should not return stack traces or sensitive file contents to the browser.

## 18. Data flow and backend responsibilities

### Upload request

1. Flask receives a multipart request.
2. The validator checks file count, size, extension, filename, and text readability.
3. The backend creates a scan row with status `running`.
4. The backend creates a device row for each accepted file.
5. The parser extracts normalized settings and safe evidence.
6. The rule engine evaluates the active rules.
7. The backend creates rule-result rows.
8. The backend updates scan counts and status.
9. The API returns the scan summary.

### Dashboard request

1. The frontend requests the scan ID.
2. The backend reads the scan summary.
3. The backend returns counts and high-severity totals.
4. The frontend renders cards and tables.

### Detail request

1. The frontend requests one device’s results.
2. The backend verifies that the device belongs to the requested scan.
3. The backend reads the rule results and rule metadata.
4. The backend returns safe evidence and remediation text.

### Report request

1. The frontend requests a report URL.
2. The backend verifies that the scan exists and is complete.
3. The backend queries the same rule results used by the dashboard.
4. The report generator creates CSV or escaped HTML.
5. The API returns the file as a download.

## 19. Security requirements for the API

- Do not execute uploaded content.
- Enforce upload size and count limits.
- Sanitize filenames.
- Store temporary files outside the public directory.
- Delete temporary files after processing when practical.
- Do not log complete configurations.
- Mask passwords, keys, and token-like evidence.
- Escape evidence in HTML responses and reports.
- Use parameterized SQL queries.
- Enable SQLite foreign-key enforcement.
- Generate non-guessable scan identifiers.
- Use HTTPS when hosted publicly.
- Keep debug mode disabled in public deployment.
- Return generic internal-error messages to users.
- Keep deterministic rule results separate from optional AI summaries.

## 20. Hackathon implementation order

| Order | API work | Completion check |
|---:|---|---|
| 1 | Add `/health` and Flask setup | Service responds |
| 2 | Add `POST /api/scans` | Files can be uploaded and validated |
| 3 | Connect parser and rule engine | Results are created |
| 4 | Add scan summary endpoint | Dashboard data is available |
| 5 | Add device detail endpoint | Evidence and remediation are visible |
| 6 | Add rules endpoints | Rule explanations can be displayed |
| 7 | Add CSV report | Download works in the demo |
| 8 | Add HTML report if time permits | Readable report is available |
| 9 | Test invalid files and warnings | Errors are safe and understandable |

## 21. What not to build in the API MVP

- Live SSH or SNMP collection.
- Automatic configuration changes.
- User registration and password management.
- API keys for multiple customers.
- Webhooks and event queues.
- Background job infrastructure.
- GraphQL.
- Microservices.
- Real-time WebSockets.
- Full vulnerability-scanning endpoints.
- AI-based pass/fail decisions.

## Final recommendation

Implement Phoenix Protocol as a small REST API with one important write endpoint, several read endpoints, and two report endpoints. Keep scan processing synchronous, use SQLite-backed results, and make deterministic rule results the source of truth.

The API is successful if a beginner can explain the main request clearly:

> **The browser uploads files to `POST /api/scans`; the backend parses them, evaluates rules, stores evidence-based results, and returns a scan ID that the browser uses to display details and download reports.**

## References

[1]: https://flask.palletsprojects.com/ "Flask Documentation"

[2]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status "HTTP response status codes"

[3]: https://owasp.org/www-project-api-security/ "OWASP API Security Top 10"

[4]: https://www.sqlite.org/foreignkeys.html "SQLite Foreign Key Support"

[5]: https://www.nist.gov/cyberframework "NIST Cybersecurity Framework"
