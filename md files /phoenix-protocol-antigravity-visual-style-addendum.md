# Phoenix Protocol — Antigravity Visual Style Addendum

Use this document together with the main Phoenix Protocol Antigravity frontend master prompt.

## Visual direction

Create an original Phoenix Protocol interface inspired by the high-level qualities of https://o-scs.com:

- Premium editorial security aesthetic.
- Very large confident typography.
- Dark neutral or deep navy hero sections.
- Off-white content surfaces.
- Generous whitespace.
- Restrained bright accent color.
- Strong section rhythm.
- Large metrics.
- Minimal, precise interaction design.
- Clear high-trust language.

Do not copy the reference website’s text, logo, images, brand identity, exact layout, or visual assets. Translate the mood into an original cybersecurity compliance product.

## Product-specific hero

Use a hero direction similar to:

```text
NETWORK SECURITY.
CLEARLY VERIFIED.
```

Supporting text:

```text
Read-only configuration compliance for teams that need to understand risk before it becomes an incident.
```

Primary action:

```text
Start a scan
```

Secondary action:

```text
Explore the rules
```

The hero must clearly communicate that Phoenix Protocol scans configuration files and does not change devices.

## Color direction

Use CSS variables similar to:

```css
:root {
  --ink: #101214;
  --deep-navy: #111a25;
  --paper: #f4f4ef;
  --soft-gray: #c7cbc8;
  --muted: #7f8786;
  --accent: #d7ff4f;
  --blue: #5aa8ff;
  --success: #80d69b;
  --warning: #f2c66d;
  --danger: #ff7d78;
}
```

Use the accent color sparingly. The interface should not look like a gaming dashboard.

## Landing-page composition

Implement the upload page as a polished product landing page with functional scanning controls:

1. Minimal header and Phoenix Protocol wordmark.
2. Large hero headline.
3. Short supporting copy.
4. Read-only and sanitized-data notice.
5. Primary start-scan action.
6. Upload panel with device-type selector.
7. Selected-file list.
8. Capabilities section.
9. Network-visibility visual using an original abstract device-node grid.
10. Final call-to-action section.

The upload controls must remain usable and visible. Do not hide the actual product workflow behind decorative content.

## Capability section

Use large editorial blocks for:

- Upload configurations.
- Extract evidence.
- Prioritize high-risk findings.
- Explain remediation.
- Export a defensible report.

Each block should have a short title and one concise explanation.

## Network visibility section

Instead of copying a geographic map, create an original sample network topology or device-node grid. Label it clearly as a sample environment.

Use synthetic nodes such as:

- Edge router.
- Branch switch.
- Data-center firewall.
- Wireless controller.
- Virtual gateway.

Do not imply live production monitoring.

## Scan notes section

Add an editorial-style section with scan insight cards using real scan data when available or clearly labeled mock data during development:

- Telnet detected on 4 devices.
- Logging configuration needs manual review.
- High-severity findings concentrated in branch routers.
- Evidence captured from lines 24–26.

## Dashboard style

Use a dark or high-contrast dashboard header with large metric typography:

```text
03        DEVICES SCANNED
30        RULES EVALUATED
06        FAILURES FOUND
04        HIGH-SEVERITY FAILURES
77.8%     TESTED-RULE COMPLIANCE
```

Below the metrics, keep the operational sections clear:

- High-priority findings.
- Device table.
- Rule-result details.
- Evidence.
- Remediation.
- Report downloads.

## Motion

Use subtle hover and entrance transitions only. Respect `prefers-reduced-motion`. Do not implement fake scan progress or heavy parallax.

## Accessibility

- Keep all status labels visible as text.
- Ensure high contrast.
- Provide visible focus states.
- Keep controls keyboard accessible.
- Do not make important content hover-only.
- Make tables usable on small screens.

## Visual acceptance criteria

The final interface should look like a premium editorial cybersecurity product rather than a generic admin dashboard. It must still satisfy every functional requirement in the main master prompt: upload files, select device type, call the API, show dashboard results, inspect evidence, handle errors, and download reports.
