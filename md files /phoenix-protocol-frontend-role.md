# Phoenix Protocol — Frontend Developer Work Plan

## Role

**Owner:** Frontend developer  
**Main responsibility:** Build the browser interface that lets a user upload configuration files, start a scan, understand results, inspect evidence, and download a report.

The frontend is the visible part of Phoenix Protocol. It should be simple, clear, accessible, and easy to demonstrate. The frontend should not contain compliance decisions. The backend remains the source of truth for parser and rule results.

## Product understanding

Phoenix Protocol scans exported network-device configuration files against security rules. The frontend should make this flow easy:

```text
Select device type → Upload files → Run scan → View dashboard → Inspect findings → Download report
```

The user may be a network administrator or security analyst. The interface must also be understandable to a beginner who does not know every networking term.

## Recommended frontend technology

Use the simplest stack the team can complete reliably:

- HTML for page structure.
- CSS for layout and visual styling.
- JavaScript for interaction and API requests.
- Bootstrap or a small CSS utility library if it speeds up development.
- Git for version control.

React and Vite are acceptable if the team already knows them. Do not introduce React only because it is popular. A few server-rendered Flask templates plus JavaScript are enough for the MVP.

## Frontend responsibilities

### 1. Upload page

Build a page containing:

- Phoenix Protocol name and short description.
- Read-only safety notice.
- Device-type selector.
- File picker or drag-and-drop area.
- List of selected filenames.
- File validation messages.
- **Run compliance scan** button.
- Link to supported rules or a short explanation.

The page should explain that users must upload sanitized or synthetic configurations and should not upload real secrets.

### 2. Scan progress state

When the user starts a scan:

- Disable the scan button temporarily.
- Show a loading message.
- Display that files are being validated and analyzed.
- Prevent accidental duplicate submissions.
- Show a friendly error if the request fails.

For the synchronous hackathon MVP, a simple loading state is enough. Do not build WebSockets or real-time progress unless the backend later requires them.

### 3. Dashboard page

Display:

- Number of devices scanned.
- Total rules evaluated.
- Pass count.
- Fail count.
- Warning count.
- Not-applicable count.
- Error count.
- High-severity failure count.
- Clearly labeled tested-rule compliance percentage.
- High-priority findings.
- Device list with status summary.

Do not present the percentage as a complete security score. Add a short explanation such as: “This percentage covers only the rules tested by Phoenix Protocol.”

### 4. Device details page or panel

For each device, show:

- Safe display name.
- Device type and vendor.
- Parser status.
- Rule results.
- Filters for status and severity.
- Rule ID and title.
- Pass, fail, warning, not-applicable, or error status.
- Severity.
- Evidence or source line.
- Plain-language explanation.
- Remediation guidance.

High-severity failures should appear first by default.

### 5. Rule details

Create a small rule information view or modal showing:

- Rule title.
- Rule ID.
- Severity.
- What the rule checks.
- Why it matters.
- What a warning means.
- Suggested next step.

### 6. Report download

Add buttons for:

- Download CSV report.
- Download HTML report if the backend supports it.

The frontend should call the backend report endpoint. It should not create a second version of the report using different data.

## API integration

Use the API specification as the contract between frontend and backend.

| Frontend action | Request |
|---|---|
| Load device types | `GET /api/device-types` |
| Start scan | `POST /api/scans` using `multipart/form-data` |
| Load scan summary | `GET /api/scans/{scan_id}` |
| Load devices | `GET /api/scans/{scan_id}/devices` |
| Load device results | `GET /api/scans/{scan_id}/devices/{device_id}` |
| Load rules | `GET /api/rules` |
| Download CSV | `GET /api/scans/{scan_id}/report.csv` |
| Download HTML | `GET /api/scans/{scan_id}/report.html` |

The frontend should handle these API outcomes:

- `200`: Display the requested data.
- `201`: Scan created and results returned.
- `400`: Show an input or upload error.
- `404`: Show that the scan, device, or rule was not found.
- `413`: Explain that the request is too large.
- `422`: Explain that a file could not be interpreted.
- `500`: Show a generic error and suggest trying again.

Do not display backend stack traces or raw sensitive error details.

## Suggested frontend files

If using Flask templates:

```text
templates/
├── base.html
├── upload.html
├── dashboard.html
├── device.html
└── rules.html

static/
├── styles.css
└── app.js
```

If using React:

```text
src/
├── components/
│   ├── StatusBadge.jsx
│   ├── SummaryCard.jsx
│   ├── FileUpload.jsx
│   ├── RuleResultTable.jsx
│   └── DeviceTable.jsx
├── pages/
│   ├── UploadPage.jsx
│   ├── DashboardPage.jsx
│   └── DevicePage.jsx
├── services/
│   └── api.js
├── styles/
│   └── app.css
└── App.jsx
```

## Suggested UI components

### `FileUpload`

Responsibilities:

- Select multiple files.
- Display filenames.
- Show file-level errors.
- Enforce basic client-side size and count checks.

Client-side validation improves user experience, but the backend must validate again because browser validation can be bypassed.

### `StatusBadge`

Display status using text and color:

- Pass.
- Fail.
- Warning.
- Not applicable.
- Error.

Never use color alone. This is important for accessibility.

### `SeverityBadge`

Display High, Medium, or Low as text. High-severity failures should be visually prominent but not overwhelming.

### `SummaryCard`

Display one dashboard metric with a label and number.

### `RuleResultTable`

Display rule results with sorting and filters. Make the table usable on a smaller screen.

### `EvidencePanel`

Display safe evidence and source line numbers. If the backend masks evidence, show the masked value exactly as returned.

### `RemediationPanel`

Show suggested next steps and the warning that production changes require review.

## Visual design guidance

Use a professional security-tool style without making the interface complicated:

- Clear page hierarchy.
- High contrast.
- Large readable headings.
- Consistent spacing.
- Clear primary button.
- Tables with visible headings.
- Status text next to color indicators.
- Responsive layout for laptop and mobile widths.
- Avoid excessive animations.

A recommended dashboard layout is:

```text
Header and read-only notice

Summary cards: Devices | Pass | Fail | Warning | High-risk failures

High-priority findings

Devices table

Recent scan details and report buttons
```

## Frontend acceptance criteria

The frontend is complete when:

- A user can select a supported device type.
- A user can select multiple files.
- Selected filenames are visible before scanning.
- Invalid upload responses are understandable.
- A user can start one scan without duplicate submissions.
- The dashboard displays backend results accurately.
- High-severity failures are easy to find.
- Device details show evidence, explanation, severity, and remediation.
- Status is represented by text, not only color.
- CSV or HTML report download works.
- The complete demo flow works without manual code changes.

## Testing checklist

Test manually:

- No file selected.
- Unsupported file selected.
- Too many files selected.
- Large file response.
- One valid file.
- Multiple valid files.
- Mixed valid and invalid files.
- Completed scan.
- Backend unavailable.
- Scan not found.
- Device with pass results.
- Device with fail results.
- Device with warnings.
- Device with parser errors.
- Report download.
- Keyboard navigation.
- Small-screen layout.

## Work sequence

| Phase | Deliverable |
|---|---|
| 1 | Confirm API response shapes with backend owner |
| 2 | Create upload page with sample data |
| 3 | Add API service functions |
| 4 | Add dashboard using mock JSON |
| 5 | Add device details and filters |
| 6 | Connect to the real backend |
| 7 | Add report download |
| 8 | Test error states and accessibility |
| 9 | Polish the live demo |

## What not to build

Do not build:

- A separate frontend rule engine.
- Authentication screens for the MVP.
- A complex charting system before the tables work.
- Real-time WebSocket progress.
- A full admin portal.
- Automatic remediation buttons.
- A second frontend framework.

## Coordination with the other members

### Backend developer needs from you

Provide:

- The exact fields needed by each screen.
- Any missing or confusing API response fields.
- Examples of the UI using mock data.
- A list of API errors that need user-friendly messages.

### QA/integration member needs from you

Provide:

- A short list of critical user flows.
- Screenshots or a deployed preview.
- Known UI limitations.
- Instructions for reproducing frontend bugs.

### Your deliverables

- Working upload screen.
- Working dashboard.
- Working device detail view.
- Report download controls.
- Responsive and accessible styling.
- Frontend test checklist.
- Short explanation of how the frontend calls the backend.

## Final responsibility statement

You own the user experience. Your job is not only to make the interface attractive. Your job is to make the core workflow understandable, reliable, and easy for the judges to use.
