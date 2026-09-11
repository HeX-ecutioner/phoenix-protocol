# Phoenix Protocol — Backend Track 1: API and Application Integration

## Role

**Owner:** Backend developer 1  
**Main responsibility:** Build the Flask API, handle requests and uploads, connect the frontend to backend services, and provide stable API responses.

This track owns the communication layer of Phoenix Protocol. It receives requests from the browser and returns predictable JSON or report files. It should not contain the detailed compliance logic; that belongs to Backend Track 2.

## Main workflow owned by this track

```text
Browser request
    ↓
Flask route
    ↓
Request validation
    ↓
Call scan service
    ↓
Return JSON response
```

## Recommended technology

- Python 3.10 or newer.
- Flask.
- SQLite connection through a shared database module.
- Python standard library for request handling and CSV downloads.
- Pytest for endpoint tests.
- Git and GitHub.

Do not introduce microservices, GraphQL, Redis, background queues, or live device connections for the MVP.

## Responsibilities

### 1. Flask application setup

Create the application entry point and route structure.

Required endpoints:

```text
GET  /health
GET  /api/device-types
POST /api/scans
GET  /api/scans/{scan_id}
GET  /api/scans/{scan_id}/devices
GET  /api/scans/{scan_id}/devices/{device_id}
GET  /api/rules
GET  /api/rules/{rule_id}
GET  /api/scans/{scan_id}/report.csv
GET  /api/scans/{scan_id}/report.html
```

### 2. Upload request handling

The `POST /api/scans` endpoint must accept `multipart/form-data`:

- `device_type`.
- Repeated `files` fields.

Validate:

- At least one file exists.
- The device type is supported.
- The file count is within the limit.
- Each file is within the size limit.
- The file is readable as text.
- The filename is safe to display and store.

The backend must validate independently of the frontend.

### 3. Calling the scan service

Do not place parsing and rule logic directly inside the Flask route. The route should call a service owned by Backend Track 2, for example:

```python
scan_result = scan_service.run_scan(
    device_type=device_type,
    uploaded_files=validated_files
)
```

This keeps HTTP handling separate from application logic.

### 4. Response format

Use a consistent success response:

```json
{
  "data": {},
  "error": null,
  "request_id": "req-123"
}
```

Use a consistent error response:

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

Do not return stack traces or raw configuration contents.

### 5. Scan endpoints

#### `POST /api/scans`

Return `201 Created` with:

- Scan ID.
- Scan status.
- Device type.
- Parser version.
- Rule-set version.
- Summary counts.
- Device summaries.

#### `GET /api/scans/{scan_id}`

Return scan metadata and summary counts.

#### `GET /api/scans/{scan_id}/devices`

Return device names, parse statuses, and summary counts.

#### `GET /api/scans/{scan_id}/devices/{device_id}`

Return rule-level results including status, severity, evidence, message, and remediation.

Verify that the requested device belongs to the requested scan.

### 6. Rules endpoints

`GET /api/rules` returns the visible rule catalog.

`GET /api/rules/{rule_id}` returns one rule’s details.

The route should read rule metadata from the rule service or database. It should not duplicate rule descriptions in multiple files.

### 7. Report endpoints

Implement CSV first:

```text
GET /api/scans/{scan_id}/report.csv
```

If time permits, add:

```text
GET /api/scans/{scan_id}/report.html
```

The report must use the same stored results as the dashboard. Do not create a separate compliance calculation in the report route.

For HTML reports, escape all evidence before rendering it.

### 8. Error handling

Return suitable status codes:

| Status | Use |
|---:|---|
| `200` | Successful read request |
| `201` | Scan created |
| `400` | Invalid request or upload |
| `404` | Scan, device, or rule not found |
| `413` | Request or file too large |
| `422` | Parser or input interpretation problem |
| `500` | Unexpected server error |

Handle errors without exposing internals.

## Suggested files owned by this track

```text
app.py
phoenix_protocol/
├── __init__.py
├── routes.py
├── api_errors.py
├── request_schemas.py
├── validators.py
├── services/
│   └── api_scan_adapter.py
└── reports/
    ├── csv_report.py
    └── html_report.py

tests/
├── test_api_health.py
├── test_api_scans.py
├── test_api_errors.py
└── test_reports.py
```

Shared files should be agreed with Backend Track 2 before editing.

## API contract for the frontend

Provide the frontend owner with:

- Endpoint paths.
- Request field names.
- Example success JSON.
- Example error JSON.
- Status values.
- Severity values.
- Report URLs.
- Local run command.

The frontend owner should never need to guess the response structure.

## Security responsibilities

- Enforce upload size and file-count limits.
- Sanitize filenames.
- Store temporary files outside the public directory.
- Do not execute uploaded content.
- Do not log full configurations.
- Use parameterized database queries through the shared database layer.
- Escape HTML report content.
- Do not return secret-like evidence unmasked.
- Keep debug mode disabled in public deployment.

## Testing responsibilities

Write endpoint tests for:

- Health response.
- Device-type response.
- Successful scan.
- Missing file.
- Unsupported file type.
- Oversized file.
- Unsupported device type.
- Scan not found.
- Device not found.
- Rule not found.
- Report download.
- Unexpected service error.

Use small test fixtures. Do not put real configuration secrets into tests.

## Coordination with Backend Track 2

Request from Track 2:

- `run_scan` input contract.
- Scan result object shape.
- Database query functions.
- Parser and rule error format.
- Report data structure.

Provide to Track 2:

- API requirements.
- Expected frontend fields.
- Validation rules.
- Endpoint test failures.
- Integration bug reports.

## Coordination with the frontend developer

Provide:

- API documentation.
- Example requests and responses.
- Error messages.
- Local API URL.
- Report download behavior.

Request:

- List of screens and fields needed.
- UI expectations for warnings and errors.
- Confirmation that API responses render correctly.

## Acceptance criteria

This track is complete when:

- The Flask application starts reliably.
- The frontend can upload files through `POST /api/scans`.
- The API returns a scan ID and summary.
- The frontend can load scan and device details.
- Errors have predictable JSON responses.
- CSV report download works.
- Endpoint tests pass.
- No parser or rule logic is duplicated inside routes.

## What not to build

- Live SSH or SNMP collection.
- Automatic device changes.
- Authentication screens.
- GraphQL.
- WebSockets.
- Background job infrastructure.
- Microservices.
- A separate API rule engine.

## Final responsibility statement

You own the reliable communication layer. The browser should be able to call the API without guessing, and every API response should make the frontend’s work straightforward.
