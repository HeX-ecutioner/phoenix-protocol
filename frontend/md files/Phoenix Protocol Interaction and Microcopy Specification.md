# Phoenix Protocol Interaction and Microcopy Specification

## Purpose

This document defines the small interaction and writing decisions that make Phoenix Protocol feel polished, trustworthy, and human-designed.

The interface should not sound like generic AI-generated SaaS copy. Use specific, concise language connected to the actual user task.

## Voice

Phoenix Protocol’s voice is:

- Clear.
- Calm.
- Precise.
- Confident without exaggeration.
- Technical when necessary.
- Helpful when explaining risk.

Avoid:

- Hype.
- Empty claims.
- Excessive exclamation marks.
- Fake urgency.
- “Revolutionary” or “game-changing” language.
- Claims that a passing scan proves complete security.

## Core messages

### Product statement

> Configuration compliance, made visible.

### Read-only statement

> Read-only by design. Phoenix Protocol analyzes exported configurations and does not modify network devices.

### Evidence statement

> Every finding has a reason.

### Compliance caveat

> Tested-rule compliance is not the same as complete security.

### Primary call to action

> Start a scan

### Secondary actions

- Explore the rules.
- View scan results.
- Inspect finding.
- Download report.
- Start another scan.
- Return to dashboard.

## Upload interactions

### Before files are selected

> Drop configuration files here or choose files from your device.

### File guidance

> Supported text configurations only. Use sanitized or synthetic data.

### File accepted

> Ready to analyze.

### File removed

> Removed from this scan.

### Empty submission

> Select at least one configuration file to start a scan.

### Missing device type

> Select a device type before scanning.

### File too large

> This file is larger than the allowed limit. Choose a smaller configuration file.

### Too many files

> This scan accepts a limited number of files. Remove some files and try again.

### Unsupported file

> This file is not a supported text configuration.

## Loading copy

### Initial scan loading

> Reading configuration files.

### Rule evaluation

> Comparing settings with security rules.

### Evidence preparation

> Preparing evidence and remediation guidance.

### Generic loading

> Analyzing configurations.

Do not rotate through many messages rapidly. One or two truthful messages are enough.

## Dashboard copy

### Tested-rule compliance label

> Tested-rule compliance

### Supporting text

> Based only on the rules evaluated in this scan.

### High-risk section

> High-priority findings

### No high-risk failures

> No high-severity failures were found among the tested rules.

### Findings exist

> Review these findings before making production changes.

### Device section

> Devices in this scan

### No devices

> No processed devices are available for this scan.

## Status explanations

| Status | Explanation |
|---|---|
| Pass | The available evidence satisfies this rule. |
| Fail | The available evidence appears to violate this rule. |
| Warning | The system could not determine the result confidently. Manual review is recommended. |
| Not applicable | This rule does not apply to the selected device type. |
| Error | The rule could not be evaluated because of a processing error. |

## Severity explanations

| Severity | Explanation |
|---|---|
| High | Investigate this finding before lower-priority issues. |
| Medium | Review this setting after high-severity issues. |
| Low | Useful improvement or information-level finding. |

## Evidence copy

Use:

> Evidence used for this result

When evidence exists:

> Source lines {start}–{end}

When evidence does not exist:

> No safe source evidence was available.

Never imply that missing evidence means a pass.

## Remediation copy

Use:

> Suggested next step

Always include:

> Review and test any change before applying it to a production device.

Do not display an automatic-fix button in the MVP.

## Rule-library copy

Section title:

> The rules behind the result

Supporting copy:

> Phoenix Protocol uses transparent, deterministic checks. Open a rule to see what it evaluates and why it matters.

## Error handling copy

### Backend unavailable

> The analysis service could not be reached. Check that the backend is running and try again.

### Scan not found

> This scan is no longer available. Start a new scan.

### Device not found

> This device result could not be found. Return to the scan dashboard.

### Report failure

> The report could not be generated. Try again after the scan is complete.

### Generic failure

> Something went wrong while processing this request. Try again.

Do not show raw exceptions, stack traces, or internal file paths.

## Empty states

### First visit

Headline:

> See what your configurations are saying.

Supporting text:

> Upload a sanitized configuration file to begin a read-only compliance scan.

### No filtered rules

> No findings match these filters.

Action:

> Reset filters

### No rules available

> No supported rules are available for this device type.

## Accessibility microcopy

- Use visible labels instead of placeholder-only inputs.
- Use `aria-label` only when a visible label is not sufficient.
- Give icon-only buttons a descriptive accessible name.
- Announce scan completion and errors to screen readers.
- Make filter names explicit.
- Ensure every expandable evidence panel communicates expanded or collapsed state.

## Human-quality writing checklist

Before shipping the UI:

- Remove generic filler copy.
- Keep one idea per sentence.
- Use the same term consistently: choose “configuration file” instead of switching between “config,” “file,” and “asset.”
- Use “finding” for an identified issue.
- Use “rule result” for the result of an evaluation.
- Use “evidence” for supporting configuration text.
- Use “remediation guidance” for a suggested next step.
- Avoid claiming certainty when the status is warning.
- Avoid saying “secure” when the product only checked selected rules.
