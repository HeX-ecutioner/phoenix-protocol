# Phoenix Protocol Frontend Implementation Plan

## Purpose

This document is the execution plan for the frontend engineer building the Phoenix Protocol web interface.

The frontend must support this complete user journey:

```text
Select device type → Choose configuration files → Run scan → View dashboard → Inspect findings → Download report
```

The frontend is responsible for presentation and interaction. The backend remains responsible for parsing files, evaluating compliance rules, calculating results, and storing scan data.

## Recommended frontend stack

Use the stack already selected by the team if the project has been initialized. If the frontend has not been initialized, use:

- React.
- Vite.
- Plain CSS or a small CSS framework.
- Browser `fetch` for API requests.
- No state-management library unless the application genuinely needs one.
- No charting library until the tables and core workflow work.

Do not add a second frontend framework or rewrite the backend.

## Frontend screens

### Screen 1: Upload page

The upload page must include:

- Phoenix Protocol branding.
- Short product description.
- Read-only safety notice.
- Device-type selector.
- Multi-file upload control.
- Selected-file list.
- File-level validation messages.
- Run compliance scan button.
- Link or expandable section explaining supported rules.

### Screen 2: Scan loading state

While the scan request is active:

- Disable the scan button.
- Show a visible loading state.
- Explain that files are being validated and analyzed.
- Prevent duplicate submissions.
- Allow recovery from an API failure.

The MVP uses a normal request and loading state. Do not build WebSockets.

### Screen 3: Dashboard

The dashboard must show:

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
- Scan timestamp and device type.
- CSV and optional HTML report buttons.

Use this explanation near the percentage:

> This percentage covers only the rules tested by Phoenix Protocol. It does not prove complete security.

### Screen 4: Device details

Show:

- Safe display name.
- Vendor and device type.
- Parser status.
- Result filters.
- Rule ID and title.
- Status.
- Severity.
- Evidence and source lines.
- Plain-language message.
- Remediation guidance.

Sort high-severity failures first by default.

### Screen 5: Rule details

Use a page, drawer, or modal to show:

- Rule ID.
- Rule title.
- Severity.
- What the rule checks.
- Why it matters.
- Meaning of a warning.
- Suggested next step.

## Component plan

| Component | Responsibility |
|---|---|
| `AppShell` | Shared page layout, header, navigation, and safety notice |
| `UploadPage` | Device-type selection, file selection, and scan start |
| `FileUpload` | Multiple file selection, filename list, client-side validation |
| `LoadingState` | Scan progress message and disabled controls |
| `DashboardPage` | Scan summary, high-risk findings, devices, report actions |
| `SummaryCard` | One dashboard metric |
| `PriorityFindings` | High-severity failed rules |
| `DeviceTable` | Device list and summary statuses |
| `DevicePage` | One device’s metadata and rule results |
| `RuleResultTable` | Results table, sorting, status filter, severity filter |
| `StatusBadge` | Text and visual status indicator |
| `SeverityBadge` | High, medium, or low label |
| `EvidencePanel` | Safe evidence and line references |
| `RemediationPanel` | Guidance and production-change warning |
| `ErrorAlert` | User-friendly API or validation error |
| `EmptyState` | No scan, no devices, or no filtered results |

## Frontend state

Keep state simple:

```text
selectedDeviceType
selectedFiles
fileErrors
isScanning
scanError
scanSummary
devices
selectedDevice
selectedStatusFilter
selectedSeverityFilter
```

Use URL state for the scan ID and device ID when practical. This makes refreshes and browser navigation easier.

## Work phases

### Phase 1: Confirm contracts

- Read the API specification.
- Ask the backend owner for actual endpoint URLs.
- Confirm the device-type value.
- Confirm response field names.
- Confirm maximum file size and file count.

### Phase 2: Build with mock data

- Create the upload page.
- Create the dashboard using local mock JSON.
- Create the device details screen.
- Create status and severity components.
- Add responsive styling.

Do not wait for the backend to start the UI.

### Phase 3: Add API service

Create one API module that contains all HTTP requests. Components should call service functions instead of constructing URLs throughout the UI.

### Phase 4: Integrate the real backend

- Connect device types.
- Connect scan creation.
- Connect summary and device requests.
- Connect report downloads.
- Test all error responses.

### Phase 5: Quality and demo readiness

- Test keyboard navigation.
- Test small-screen layout.
- Test invalid files and backend errors.
- Confirm that data in summary cards matches detail data.
- Rehearse the upload-to-report flow.

## Frontend definition of done

The frontend is complete when:

- A user can select a supported device type.
- A user can select multiple files.
- Selected filenames are visible before scanning.
- Client-side validation gives useful messages.
- A user can start one scan without duplicate submissions.
- Loading and failure states are visible.
- Dashboard values come from the API.
- High-severity failures are easy to locate.
- Device details show evidence, explanation, severity, and remediation.
- Status is represented with visible text, not only color.
- CSV download works.
- The complete demo works without editing source code.

## Ownership boundaries

### Do build

- Browser interface.
- Frontend validation for user experience.
- API calls.
- Loading, empty, success, and error states.
- Dashboard and detail views.
- Styling and accessibility.

### Do not build

- Parser logic.
- Compliance decisions.
- Database queries.
- Backend authentication.
- Live network-device access.
- Automatic remediation.
- AI-generated pass/fail results.

## Coordination outputs

Give the backend owner:

- Required response fields.
- Example UI screenshots or wireframes.
- Friendly messages needed for errors.
- Any missing API information.

Give the QA/integration owner:

- Critical user flows.
- UI test steps.
- Known limitations.
- Instructions for reproducing frontend bugs.

## Suggested git commits

```text
feat: add Phoenix Protocol upload screen
feat: add dashboard with mock scan data
feat: add API service layer
feat: connect dashboard to scan API
feat: add device rule details and filters
feat: add report download actions
test: add frontend validation and error states
style: improve responsive security dashboard
```

Keep each commit focused and easy to revert.
