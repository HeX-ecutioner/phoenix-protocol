# Phoenix Protocol Frontend UI and UX Specification

## Product experience goal

Phoenix Protocol should feel like a calm, trustworthy security inspection tool. The user should understand what to do immediately, see what the system found, and understand why a result matters.

The interface should avoid unnecessary complexity. The MVP does not need a large navigation system, authentication pages, advanced charts, or a multi-tenant administration area.

## Visual direction

Use a professional dark-blue or navy security-tool theme with a light content surface. Use one accent color for primary actions and distinct but accessible status colors.

| Purpose | Suggested treatment |
|---|---|
| Primary action | Strong blue button with clear text |
| Pass | Green accent plus “Pass” text |
| Fail | Red accent plus “Fail” text |
| Warning | Amber accent plus “Warning” text |
| Error | Dark red or red accent plus “Error” text |
| Not applicable | Neutral gray plus visible text |
| High severity | Strong text weight and high-contrast badge |
| Safety notice | Light amber information panel |

Do not rely on color alone. Every status must appear as readable text.

## Global layout

### Header

The header should include:

- Phoenix Protocol logo or wordmark.
- Short label: “Network configuration compliance scanner”.
- A small read-only indicator.
- Optional link to the rule library.

### Safety notice

Show a notice near the top of the upload and dashboard pages:

> Read-only prototype. Use only sanitized or synthetic configuration files. Phoenix Protocol does not modify network devices.

### Main content

Use a centered content area with a readable maximum width. Avoid full-width tables that become difficult to read on smaller screens.

### Footer

The footer can show:

- Prototype label.
- Current scan or rule-set version if available.
- Link to documentation.

## Upload page specification

### Page title

**Scan network configurations**

### Supporting text

> Upload exported configuration files and compare them with Phoenix Protocol’s security rules.

### Device-type selector

Label:

> Device type

Help text:

> Choose the configuration format that matches your files.

States:

- Loading supported types.
- Successful selection.
- No supported type available.
- API failure.

### File upload area

Label:

> Configuration files

Help text:

> Select one or more sanitized text configuration files. Do not upload passwords, keys, or production secrets.

The area should support both clicking and drag-and-drop if practical. Show accepted file type, maximum file size, and maximum file count.

### Selected file list

Each file row should show:

- Filename.
- File size.
- Validation status.
- Remove button.
- Error message when invalid.

### Primary action

Button label:

> Run compliance scan

Disabled when:

- No device type is selected.
- No file is selected.
- A scan is already running.
- Client-side validation fails.

## Loading state specification

Title:

> Analyzing configurations

Supporting text:

> Phoenix Protocol is validating your files and evaluating the selected security rules.

Show a spinner or progress indicator, but do not show fake percentage progress. The MVP uses a synchronous request and does not know exact backend progress.

## Dashboard specification

### Header area

Show:

- “Scan results” title.
- Scan timestamp.
- Device type.
- Scan status.
- Report download buttons.
- Button to start another scan.

### Summary cards

Recommended cards:

| Card | Meaning |
|---|---|
| Devices scanned | Number of configuration files processed |
| Rules evaluated | Total rule evaluations |
| Pass | Rules satisfied by available evidence |
| Fail | Rules that appear to be violated |
| Warning | Rules requiring manual review |
| High-risk failures | Failed rules with high severity |

The full counts for not-applicable and error results can appear in a secondary summary row or table.

### Compliance explanation

Show the tested-rule percentage with this supporting text:

> This is compliance with the rules tested in this scan. It is not a complete security score.

### High-priority findings

Show a compact list containing:

- Device name.
- Rule ID and title.
- Severity.
- One-line message.
- Link to device details.

If there are no high-priority findings, show a positive but cautious message:

> No high-severity failures were found among the tested rules.

Do not say “the network is secure.”

### Device table

Columns:

- Device.
- Parse status.
- Pass.
- Fail.
- Warning.
- High-risk failures.
- View details action.

On smaller screens, allow horizontal scrolling or switch to stacked device cards.

## Device details specification

### Device header

Show:

- Device display name.
- Vendor.
- Device type.
- Parser status.
- Back to results link.

### Filters

Provide:

- Status filter.
- Severity filter.
- Search by rule ID or title.
- Reset filters button.

Default sorting should be:

1. Failed high-severity results.
2. Warning high-severity results.
3. Failed medium-severity results.
4. Remaining results.

### Rule result row

Show:

- Rule ID.
- Rule title.
- Status text.
- Severity text.
- Short message.
- Expand or view details action.

### Expanded rule details

Show:

- What the rule checks.
- Why it matters.
- Evidence.
- Source line range.
- Plain-language message.
- Remediation guidance.
- Production-change warning.

Evidence should be rendered as escaped text in a monospace block. Never use `innerHTML` with raw backend evidence.

## Rule library specification

The rule library should be accessible from the upload or dashboard page.

Each rule card should contain:

- Rule ID.
- Title.
- Severity.
- Device type.
- Short description.
- Technical requirement.
- Why it matters.
- How warnings are produced.
- Remediation guidance.

## Empty and error states

### No files

> Select at least one configuration file to start a scan.

### No scan yet

> Upload configuration files to see compliance results.

### No filtered results

> No rules match the selected filters.

### Backend unavailable

> Phoenix Protocol could not reach the analysis service. Check that the backend is running and try again.

### Invalid file

> This file could not be accepted. Check that it is a supported text configuration file and within the size limit.

### Parser warning

> Phoenix Protocol could not determine this setting confidently. Review the configuration manually.

### Report error

> The report could not be generated. Please try again after the scan is complete.

## Accessibility requirements

- Use semantic headings in the correct order.
- Use visible labels for every input.
- Associate help text with inputs.
- Provide keyboard access to all buttons and controls.
- Show a visible focus outline.
- Use buttons for actions and links for navigation.
- Use status text in addition to color.
- Keep contrast high.
- Announce loading and major error states where possible.
- Do not trap keyboard users in modals.

## Responsive behavior

At laptop width, use summary cards in a row and tables with comfortable spacing.

At mobile width:

- Stack summary cards.
- Allow tables to scroll horizontally or become cards.
- Keep the primary scan button easy to reach.
- Keep evidence readable without overflowing the viewport.
- Do not hide important failure information behind hover-only behavior.

## UI acceptance criteria

The UI passes review when a new user can:

1. Understand what Phoenix Protocol does.
2. Identify which files are safe to upload.
3. Select a device type.
4. Select multiple files.
5. Start one scan.
6. Understand the loading state.
7. Find high-severity failures.
8. Open evidence and remediation.
9. Understand a warning.
10. Download a report.

## Visual testing checklist

Test the interface at:

- Desktop width.
- Tablet width.
- Mobile width.
- Keyboard-only navigation.
- Slow backend response.
- Backend failure.
- Long filenames.
- Long evidence text.
- Zero failures.
- Many failures.
- Mixed statuses.

## Out of scope

Do not add:

- Full authentication UI.
- Real-time charts.
- Complex animations.
- User-configurable compliance scoring.
- Automatic remediation buttons.
- Live network-device controls.
- A second design system.
