# Phoenix Protocol Frontend Testing and Handoff Checklist

## Purpose

Use this document to verify that the frontend is ready to connect to the backend and present a reliable hackathon demo.

## Critical user journey

The most important path is:

```text
Open upload page
    ↓
Select device type
    ↓
Select three sample files
    ↓
Run compliance scan
    ↓
See dashboard
    ↓
Open failing device
    ↓
Inspect evidence and remediation
    ↓
Open ambiguous device
    ↓
See warning
    ↓
Download CSV report
```

This path must work without editing code during the demo.

## Functional checklist

### Upload page

- [ ] Phoenix Protocol name is visible.
- [ ] Product description is understandable.
- [ ] Read-only safety notice is visible.
- [ ] Device types load from the backend.
- [ ] Device-type loading state is visible.
- [ ] Device-type API errors are understandable.
- [ ] Multiple files can be selected.
- [ ] Selected filenames are visible.
- [ ] File size is visible when useful.
- [ ] Files can be removed before scanning.
- [ ] Unsupported files are rejected or clearly marked.
- [ ] Too many files are rejected or clearly marked.
- [ ] Scan button is disabled when input is incomplete.

### Scan loading state

- [ ] Scan button disables after click.
- [ ] A loading indicator appears.
- [ ] Duplicate submissions are prevented.
- [ ] The user sees that files are being analyzed.
- [ ] The loading state ends after success.
- [ ] The loading state ends after failure.

### Dashboard

- [ ] Scan timestamp is displayed.
- [ ] Device type is displayed.
- [ ] Device count matches the API.
- [ ] Total rules evaluated matches the API.
- [ ] Pass count matches the API.
- [ ] Fail count matches the API.
- [ ] Warning count matches the API.
- [ ] Not-applicable count is visible when present.
- [ ] Error count is visible when present.
- [ ] High-severity failure count is prominent.
- [ ] Tested-rule compliance is clearly labeled.
- [ ] The page says the percentage is not complete security.
- [ ] High-priority findings are displayed.
- [ ] Device list loads.
- [ ] Device parser status is displayed.
- [ ] Report download buttons work.

### Device details

- [ ] Device name is displayed safely.
- [ ] Vendor and device type are displayed.
- [ ] Parser status is displayed.
- [ ] Rule results load.
- [ ] Results include status text.
- [ ] Results include severity text.
- [ ] Results include rule ID and title.
- [ ] Evidence is displayed safely.
- [ ] Source line numbers are displayed when available.
- [ ] Explanation is displayed.
- [ ] Remediation guidance is displayed.
- [ ] Production-change warning is displayed.
- [ ] High-severity failures appear first.
- [ ] Status filter works.
- [ ] Severity filter works.
- [ ] Empty filtered state is understandable.

## Negative test cases

### No files

Expected result: The scan action remains disabled or a clear validation message appears.

### No device type

Expected result: The scan action remains disabled or a clear validation message appears.

### Unsupported file

Expected result: The user sees which file is invalid and why.

### Too many files

Expected result: The user sees the configured limit and can remove files.

### Large file

Expected result: The user sees a size-limit message.

### Empty file

Expected result: The backend returns a clear warning or error without crashing the page.

### Mixed valid and invalid files

Expected result: Valid files are processed when supported by the backend, and the invalid file is identified.

### Backend unavailable

Expected result: The page shows a friendly connection error and the user can retry.

### Scan not found

Expected result: The page shows that the scan is unavailable and provides a way to return to upload.

### Device not found

Expected result: The page shows a friendly not-found state.

### Report failure

Expected result: The page shows a report-generation error without losing the scan view.

## Accessibility checklist

- [ ] All inputs have visible labels.
- [ ] Help text is associated with the relevant input.
- [ ] Buttons have meaningful names.
- [ ] Keyboard users can complete the upload flow.
- [ ] Focus indicators are visible.
- [ ] Modal or drawer details can be closed with keyboard.
- [ ] Tables have headings.
- [ ] Status is not communicated only by color.
- [ ] Contrast is readable.
- [ ] Text remains readable at larger browser zoom.
- [ ] No important information appears only on hover.

## Responsive checklist

Test at desktop, tablet, and mobile widths.

- [ ] Summary cards stack cleanly.
- [ ] Tables remain usable.
- [ ] Evidence does not overflow the screen.
- [ ] Upload controls remain reachable.
- [ ] Buttons remain large enough to tap.
- [ ] Navigation does not overlap content.
- [ ] Long filenames wrap or truncate safely.

## Security checklist

- [ ] No real secrets appear in sample data.
- [ ] Raw evidence is not inserted using unsafe HTML.
- [ ] Files are not uploaded before the user starts a scan.
- [ ] The frontend does not execute configuration text.
- [ ] API stack traces are not shown.
- [ ] Sensitive values are not written to browser console logs.
- [ ] API base URL does not contain secrets.
- [ ] No authentication secret is committed to source control.

## Mock-data checklist

Before the backend is ready, create mock data for:

- Mostly compliant device.
- Failing device.
- Ambiguous device.
- Parser error.
- Empty scan.
- High-severity failure.
- Mixed statuses.

Mock data must match the real API response contract exactly.

## Browser testing matrix

| Browser or environment | Minimum check |
|---|---|
| Chrome or Chromium | Complete demo flow |
| Firefox or Edge | Upload, dashboard, and report |
| Mobile-width browser | Responsive layout |
| Keyboard only | Upload and details navigation |
| Slow network simulation | Loading and retry behavior |

## Bug-report template

```text
Title:
Severity: Blocker / High / Medium / Low
Environment:
Steps to reproduce:
Expected result:
Actual result:
Screenshot or response:
Owner:
Status:
Verification after fix:
```

## Handoff package

Give the backend owner:

- Exact fields required by each screen.
- API errors that need special messages.
- Mock data examples.
- Any CORS or URL assumptions.

Give the integration owner:

- Critical user flows.
- Test results.
- Known UI limitations.
- Deployment preview URL if available.
- Instructions for reproducing frontend issues.

## Final sign-off

The frontend can be marked ready when:

- The critical journey passes three consecutive times.
- The dashboard and device details match backend responses.
- Invalid input produces understandable feedback.
- The report download works.
- Accessibility and responsive checks pass.
- No sensitive data appears in the repository or browser logs.
- The team can explain the frontend’s API calls and limitations.
