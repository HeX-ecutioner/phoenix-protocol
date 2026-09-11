# Phoenix Protocol — Antigravity Frontend Master Prompt

Copy everything below and provide it to Antigravity as one master instruction. If Antigravity asks questions, it should inspect the repository first and only ask about decisions that materially affect the implementation.

---

## ROLE

You are a senior frontend engineer and UX engineer working with a beginner hackathon team. You are implementing the frontend for **Phoenix Protocol**, a read-only network-device configuration compliance scanner.

You must work carefully, explain important choices, keep the code understandable, and avoid unnecessary technologies. Do not generate a large unstructured codebase. Build a small, polished, reliable MVP.

## PRODUCT CONTEXT

Phoenix Protocol allows a network administrator or security analyst to upload exported network-device configuration files, select the device type, run deterministic backend security checks, inspect evidence-based results, and download a compliance report.

The frontend workflow is:

```text
Select device type → Upload configuration files → Run scan → View dashboard → Inspect findings → Download report
```

The product is read-only. It does not connect to live production devices and does not automatically change configurations.

The frontend must not decide whether a device is compliant. The backend is the source of truth for parsing, rule evaluation, severity, evidence, remediation, and summary values.

## IMPORTANT SCOPE LIMITS

Build only the frontend MVP.

Do not build:

- A frontend compliance-rule engine.
- A second parser.
- Live SSH, SNMP, or device API connections.
- Automatic remediation.
- Authentication pages unless the existing repository already requires them.
- WebSockets or fake real-time progress.
- Complex charting before tables and the core workflow work.
- A second frontend framework.
- Unnecessary state-management libraries.
- A new backend implementation.

Use mock data only as a development fallback. The final UI must be ready to call the real API.

## FIRST ACTIONS: INSPECT BEFORE EDITING

Before writing code:

1. Inspect the repository structure.
2. Identify whether the project uses React, Vite, Flask templates, or another existing frontend setup.
3. Read the existing README, package files, environment examples, and frontend source files.
4. Preserve the existing project structure when reasonable.
5. Do not replace a working setup with a new framework.
6. Identify the backend API base URL configuration.
7. Identify how the application is currently started and tested.
8. Summarize the existing structure and proposed frontend changes before making major edits.

If the repository is empty, use React with Vite only if a frontend framework is needed. Otherwise use the existing project’s simplest supported approach.

## FRONTEND TECHNOLOGY RULES

Prefer:

- React and Vite if already present.
- Plain JavaScript if the existing project is plain HTML.
- CSS modules or one maintainable stylesheet.
- Browser `fetch` for API calls.
- Small reusable components.
- Local component state.

Avoid adding packages unless they provide clear value. Do not add a charting library, state-management library, router, icon package, or UI framework if the current project can complete the MVP without it.

If a router is already present, use it. If not, simple conditional rendering or minimal URL handling is acceptable for the MVP.

## REQUIRED SCREENS

### 1. Upload screen

Create a polished upload screen with:

- Phoenix Protocol name.
- Short description: “Evidence-based network configuration compliance scanning.”
- Read-only safety notice.
- Device-type selector loaded from the API.
- Multiple-file picker.
- Optional drag-and-drop behavior.
- Selected-file list.
- Filename and size display.
- File removal controls.
- Client-side file count and size validation.
- Run compliance scan button.
- Link or expandable section describing supported rules.

Use this safety notice:

> Read-only prototype. Use only sanitized or synthetic configuration files. Phoenix Protocol does not modify network devices.

Use this upload help text:

> Select one or more supported text configuration files. Do not upload passwords, keys, tokens, or production secrets.

### 2. Loading state

When the scan starts:

- Disable the scan button.
- Prevent duplicate submissions.
- Show a visible loading indicator.
- Show text explaining that files are being validated and analyzed.
- Preserve a clear error recovery path.

Do not show fake numerical progress.

### 3. Dashboard screen

Display:

- Scan timestamp.
- Device type.
- Scan status.
- Devices scanned.
- Total rules evaluated.
- Pass count.
- Fail count.
- Warning count.
- Not-applicable count.
- Error count.
- High-severity failure count.
- Tested-rule compliance percentage.
- High-priority findings.
- Device list with per-device summaries.
- CSV report download.
- HTML report download only if supported.
- Start another scan action.

Show this explanation near the percentage:

> This percentage covers only the rules tested by Phoenix Protocol. It does not prove complete security.

Never display wording such as “Your network is secure.”

### 4. Device details screen or panel

Display:

- Safe device display name.
- Vendor.
- Device type.
- Parser status.
- Status filter.
- Severity filter.
- Rule search.
- Rule ID.
- Rule title.
- Result status.
- Severity.
- Evidence.
- Evidence source line range.
- Plain-language message.
- Remediation guidance.
- Production-change review warning.

Sort high-severity failures first by default.

### 5. Rule details view

Create a modal, drawer, expandable section, or page showing:

- Rule ID.
- Title.
- Severity.
- Description.
- Technical requirement.
- Why it matters.
- Meaning of a warning.
- Remediation guidance.

### 6. Empty and error states

Implement clear states for:

- No files selected.
- No device type selected.
- No scan yet.
- No matching filters.
- Backend unavailable.
- Invalid file.
- Request too large.
- Parser warning.
- Scan not found.
- Device not found.
- Report failure.

Do not show raw stack traces.

## API CONTRACT

Use one API service module. Components should not construct fetch URLs independently.

Use an environment variable when appropriate:

```text
VITE_API_BASE_URL=http://localhost:5000
```

If the frontend and backend are served by the same application, relative paths are acceptable.

### Common success response

```json
{
  "data": {},
  "error": null,
  "request_id": "req-123"
}
```

### Common error response

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

### Endpoints

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

### Device types response

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

### Create scan request

Use `multipart/form-data`:

- `device_type`: selected device type.
- `files`: repeated file fields.

Important: when using `FormData`, do not manually set the `Content-Type` header. The browser must set the multipart boundary.

Example API function:

```javascript
async function createScan(deviceType, files) {
  const formData = new FormData();
  formData.append("device_type", deviceType);
  files.forEach((file) => formData.append("files", file));

  return apiRequest("/api/scans", {
    method: "POST",
    body: formData,
  });
}
```

### Scan summary shape

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

### Device result shape

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

## REQUIRED API FUNCTIONS

Create one API service module with functions equivalent to:

```javascript
getDeviceTypes()
createScan(deviceType, files)
getScan(scanId)
getDevices(scanId)
getDevice(scanId, deviceId, filters)
getRules(filters)
getRule(ruleId)
getCsvReportUrl(scanId)
getHtmlReportUrl(scanId)
```

The service layer must:

- Parse JSON safely.
- Convert non-2xx responses into useful errors.
- Preserve HTTP status and backend error code.
- Avoid logging sensitive payloads.
- Avoid leaking stack traces into the UI.

## STATUS AND SEVERITY DISPLAY

Supported result statuses:

- Pass.
- Fail.
- Warning.
- Not applicable.
- Error.

Supported severities:

- High.
- Medium.
- Low.

Every status must appear as visible text. Use color as a secondary signal only.

## SECURITY REQUIREMENTS

- Treat all backend evidence as untrusted text.
- Never use unsafe raw HTML rendering for evidence or filenames.
- Do not execute or interpret uploaded configuration text.
- Do not store uploaded configuration contents in browser local storage.
- Do not log full API responses if they may contain evidence.
- Do not commit API keys or credentials.
- Do not create frontend buttons that change live devices.
- Display the sanitized-data warning.

## COMPONENT STRUCTURE

Use the existing project structure where possible. If no structure exists, create a maintainable structure similar to:

```text
src/
├── components/
│   ├── AppShell.jsx
│   ├── ErrorAlert.jsx
│   ├── EmptyState.jsx
│   ├── FileUpload.jsx
│   ├── LoadingState.jsx
│   ├── RemediationPanel.jsx
│   ├── RuleResultTable.jsx
│   ├── SeverityBadge.jsx
│   ├── StatusBadge.jsx
│   ├── SummaryCard.jsx
│   └── DeviceTable.jsx
├── pages/
│   ├── UploadPage.jsx
│   ├── DashboardPage.jsx
│   ├── DevicePage.jsx
│   └── RulesPage.jsx
├── services/
│   └── api.js
├── data/
│   └── mockData.js
├── styles/
│   └── app.css
├── App.jsx
└── main.jsx
```

If the project uses Flask templates instead of React, use the equivalent existing templates and static JavaScript files. Do not migrate frameworks.

## DESIGN REQUIREMENTS

Make the interface:

- Professional.
- Calm and trustworthy.
- High contrast.
- Responsive.
- Beginner-friendly.
- Keyboard accessible.
- Clear about read-only behavior.

Recommended dashboard layout:

```text
Header and safety notice

Summary cards: Devices | Rules | Pass | Fail | Warning | High-risk failures

Tested-rule compliance explanation

High-priority findings

Devices table

Report buttons
```

Avoid unnecessary animations and visual clutter.

## MOCK DATA MODE

Implement mock data only if the backend is unavailable during frontend development.

Mock data must include:

- One mostly compliant device.
- One failing device.
- One ambiguous device.
- Pass, fail, warning, not-applicable, and error examples.
- Evidence, severity, message, and remediation.

Mock data must use the same shape as the API contract. Switching to the real API should require only a configuration change, not a rewrite of components.

## VALIDATION RULES

Implement client-side checks for user experience:

- Device type is selected.
- At least one file is selected.
- File count is within the configured limit.
- File size is within the configured limit.
- File names are displayed safely.

The backend remains responsible for authoritative validation.

## ERROR MESSAGES

Use user-friendly messages:

| Situation | Message |
|---|---|
| No files | Select at least one configuration file to start a scan. |
| No device type | Select a device type before scanning. |
| Invalid file | This file is not a supported text configuration. |
| Too large | This file exceeds the allowed size limit. |
| Too many files | Remove some files and try again. |
| Backend unavailable | Phoenix Protocol could not reach the analysis service. Check that the backend is running and try again. |
| Scan not found | This scan could not be found. Start a new scan. |
| Device not found | This device result could not be found. Return to the scan dashboard. |
| Report failure | The report could not be generated. Try again after the scan is complete. |

## TESTING REQUIREMENTS

Before declaring the task complete, test:

1. No file selected.
2. No device type selected.
3. Unsupported file.
4. Too many files.
5. Large file.
6. One valid file.
7. Multiple valid files.
8. Mixed valid and invalid files.
9. Successful scan.
10. Backend unavailable.
11. Scan not found.
12. Device with pass results.
13. Device with fail results.
14. Device with warnings.
15. Device with parser errors.
16. Report download.
17. Keyboard navigation.
18. Responsive mobile layout.
19. Long filenames.
20. Long evidence text.

If tests cannot be automated, create a manual checklist and execute it.

## ACCEPTANCE CRITERIA

The implementation is complete only when:

- The app starts using the repository’s documented command.
- The upload screen is usable without developer assistance.
- Device types load from the API or an explicitly enabled mock mode.
- Multiple files can be selected and reviewed.
- The scan button prevents duplicate requests.
- Loading, success, empty, and error states are implemented.
- The dashboard displays backend values accurately.
- High-severity failures are prioritized.
- Device details show evidence, explanation, severity, and remediation.
- Status is represented by readable text and not only color.
- CSV report download works.
- HTML report download is shown only if supported.
- The critical flow works with the three demo files.
- No raw backend stack traces appear in the UI.
- No secrets are committed or logged.
- The code is understandable to a beginner developer.

## IMPLEMENTATION METHOD

Work in this order:

1. Inspect the repository.
2. Confirm the existing frontend framework.
3. Create or update the API service module.
4. Create mock data matching the API contract.
5. Build the upload page.
6. Build reusable status, severity, summary, and error components.
7. Build the dashboard.
8. Build device details and filters.
9. Add rule details.
10. Add report download actions.
11. Connect to the real backend.
12. Test all success and failure states.
13. Fix accessibility and responsive issues.
14. Run the project’s tests and build command.
15. Update the frontend README or setup notes.
16. Report exactly what was changed, how to run it, and any remaining backend assumptions.

## CODING RULES

- Keep components small and understandable.
- Use meaningful names.
- Avoid duplicated API calls.
- Avoid duplicated status-label logic.
- Keep API calls outside presentation components where practical.
- Add comments only when they explain a non-obvious decision.
- Do not silently swallow errors.
- Do not invent backend fields.
- Do not hard-code fake scan results in the production path.
- Preserve existing working code unless a change is necessary.
- Do not change backend behavior without explicit need.

## FINAL REPORT REQUIRED FROM YOU

After implementation, provide:

1. Summary of files created or changed.
2. How to run the frontend.
3. Environment variables required.
4. API endpoints used.
5. Test commands run and their results.
6. Manual test results.
7. Any assumptions about the backend.
8. Any remaining limitations.

Do not claim that a feature works unless you tested it or clearly label it as unverified.

---

## END OF MASTER PROMPT
