# Phoenix Protocol Reference-Inspired UI/UX Brief

## Purpose

This brief translates the visual qualities of the reference website at [o-scs.com](https://o-scs.com) into an original Phoenix Protocol interface.

Phoenix Protocol should not copy the reference site’s text, logo, images, brand, or exact layout. It should borrow only high-level design ideas such as strong editorial typography, restrained colors, generous spacing, confident messaging, and a premium security feel.

## Desired visual character

Phoenix Protocol should feel:

- Calm rather than noisy.
- Precise rather than decorative.
- Premium rather than generic.
- Secure rather than intimidating.
- Editorial rather than dashboard-heavy.
- Clear enough for a beginner to use.

The product is technical, but the first screen should communicate confidence and simplicity before showing detailed scan controls.

## Reference-inspired design principles

### 1. Strong editorial hero

Use a large headline with a short, confident message. Suggested Phoenix Protocol copy:

> NETWORK SECURITY.  
> CLEARLY VERIFIED.

Supporting copy:

> Read-only configuration compliance for teams that need to understand risk before it becomes an incident.

The hero should include a clear action such as **Start a scan** and a secondary action such as **Explore the rules**.

### 2. Dark neutral foundation

Use a near-black or deep navy background for the hero and major sections. Use an off-white content surface for readable tables and details.

Suggested colors:

```css
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
```

Use the bright accent sparingly for primary actions, selected navigation, and small data highlights. Do not make the entire interface neon.

### 3. Oversized typography

Use a bold sans-serif display font for hero headlines and a highly readable sans-serif for body content. If external font loading is not appropriate, use system fonts.

Recommended hierarchy:

- Hero headline: very large, tight line height.
- Section heading: large and confident.
- Body text: short paragraphs with generous line height.
- Metrics: large numbers with small labels.
- Technical results: compact but readable table typography.

Avoid putting long technical paragraphs in the hero.

### 4. Large whitespace and clear rhythm

Use generous vertical spacing between sections. Each section should have one clear purpose.

Suggested landing-page rhythm:

```text
Hero
↓
Trust statement and read-only promise
↓
Key scan metrics or capabilities
↓
How the scan works
↓
Security rules
↓
Dashboard preview
↓
Final start-scan call to action
```

### 5. Horizontal capability sections

Present the product’s main capabilities as a sequence of strong blocks rather than a crowded grid:

- Upload configurations.
- Detect evidence.
- Prioritize high-risk findings.
- Explain remediation.
- Export a defensible report.

Each block should have a short title, one sentence, and a simple visual treatment such as a number, line, icon, or small mock data panel.

### 6. Global operations translated into network visibility

The reference site uses worldwide presence as a visual storytelling device. Phoenix Protocol should use a **network visibility** concept instead of copying a geographic map.

Possible section title:

> EVERY DEVICE. ONE CLEAR VIEW.

Show a stylized network topology or abstract grid with device nodes. The visual should be original and should not imply that Phoenix Protocol has real global offices or live production access.

Use sample labels such as:

- Edge router.
- Branch switch.
- Data-center firewall.
- Wireless controller.
- Virtual gateway.

Clearly mark the visual as a demo or sample environment.

### 7. Field notes translated into scan insights

The reference includes editorial “field notes.” Phoenix Protocol can include a section called **Scan Notes** or **Evidence Log**.

Example cards:

- “Telnet detected on 4 devices.”
- “Logging configuration needs manual review.”
- “High-severity findings concentrated in branch routers.”
- “Evidence captured from lines 24–26.”

These cards should come from the selected scan or use clearly labeled demo data.

## Recommended page structure

### Landing / upload page

1. Minimal header with Phoenix Protocol wordmark.
2. Hero headline and supporting statement.
3. Primary **Start a scan** button.
4. Small read-only and sanitized-data note.
5. Upload panel with device-type selector.
6. Capability section.
7. Sample dashboard preview or scan process explanation.
8. Final call to action.

### Results dashboard

Keep the same visual language, but make the dashboard functional:

1. Compact header.
2. Scan identity and timestamp.
3. Large summary metrics.
4. High-priority findings.
5. Device list.
6. Rule-result details.
7. Report actions.

The dashboard must prioritize clarity over visual theatrics.

## Interaction style

- Use subtle hover transitions.
- Use smooth but short section transitions.
- Avoid heavy parallax or animation that distracts from the scan.
- Use clear focus styles.
- Keep loading states honest; do not show fake progress percentages.
- Use expandable evidence panels for technical details.
- Make the primary scan action visually distinct.

## Original Phoenix Protocol copy direction

Use concise, confident copy such as:

- “Configuration compliance, made visible.”
- “Know what passed. See what failed.”
- “Evidence before assumptions.”
- “Read-only by design.”
- “Every finding has a reason.”
- “From configuration files to clear security actions.”

Avoid claiming:

- Complete security.
- Guaranteed compliance.
- Automatic protection.
- Live global monitoring.

## Dashboard visual language

Use large metric numbers inspired by editorial data presentation:

```text
03        DEVICES SCANNED
30        RULES EVALUATED
06        FAILURES FOUND
04        HIGH-SEVERITY FAILURES
77.8%     TESTED-RULE COMPLIANCE
```

Always pair numbers with labels and explanatory context.

## Technical result styling

Status must be visible as text:

- `PASS` in green.
- `FAIL` in red.
- `WARNING` in amber.
- `NOT APPLICABLE` in neutral gray.
- `ERROR` in red with an error icon or supporting message.

Use a monospace block for evidence and source lines. Use a readable sans-serif for explanations and remediation.

## Images and assets

Do not use unrelated stock photography as the primary visual. The product can use:

- Abstract network topology diagrams.
- Original line-based device-node illustrations.
- Subtle grid textures.
- Configuration text fragments with synthetic data.
- Minimal icons.

Do not display real credentials, real production configuration, or fabricated customer logos.

## Performance and accessibility

- Prefer CSS and SVG over heavy media.
- Optimize any image assets.
- Keep the first screen fast.
- Maintain keyboard navigation.
- Keep contrast readable.
- Do not use color alone for statuses.
- Support reduced-motion preferences.
- Test mobile widths.

## Design acceptance criteria

The UI is successful if:

1. The first screen communicates what Phoenix Protocol does within a few seconds.
2. The design feels premium and security-focused without being confusing.
3. The user can begin a scan quickly.
4. The dashboard looks visually distinctive but remains operationally clear.
5. A judge can understand the product without reading the technical architecture first.
6. The visual design is inspired by high-level editorial security aesthetics but is original to Phoenix Protocol.
7. The interface still works when the backend returns real pass, fail, warning, and error results.
