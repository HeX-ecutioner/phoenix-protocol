# Phoenix Protocol Premium Visual Design System

## Design goal

Build Phoenix Protocol as an original, premium cybersecurity product website with the confidence of an established global security firm and the clarity of a modern security platform.

The visual direction is inspired by the high-level qualities of [o-scs.com](https://o-scs.com): oversized editorial typography, dark cinematic sections, restrained color, generous whitespace, confident messaging, and strong visual rhythm.

Do not copy the reference site’s logo, wording, images, branding, or exact composition. Use the design mood as inspiration and create an original Phoenix Protocol identity.

## Brand character

Phoenix Protocol should feel:

- **Authoritative:** It understands security operations.
- **Quiet:** It does not shout with excessive effects or badges.
- **Precise:** Every element has a purpose.
- **Editorial:** Sections feel composed rather than auto-generated.
- **Technical:** Evidence, rules, and device data are visible.
- **Human:** Explanations are understandable to non-experts.
- **Trustworthy:** The product clearly states that it is read-only.

Avoid the visual language of a generic SaaS template, gaming dashboard, crypto website, or AI-generated landing page.

## Core design principles

### Use fewer, stronger elements

Every section should have one clear idea. Prefer one large statement and one strong interaction over many small cards.

### Build contrast through scale

Use large headlines, small labels, quiet body copy, and oversized metrics. The variation in scale should create hierarchy without requiring excessive decoration.

### Let negative space create quality

Use generous padding and clear vertical separation. Do not fill every empty area with icons, gradients, or feature cards.

### Keep technical detail available but controlled

The landing page should be editorial and welcoming. The dashboard should become denser and more operational after the scan begins.

### Make the product feel deliberate

Use consistent spacing, carefully aligned edges, restrained borders, and purposeful animation. Avoid random floating elements and excessive rounded cards.

## Color system

Use a dark foundation with an off-white reading surface and one controlled acid accent.

```css
:root {
  --ink: #0d1012;
  --black: #080a0c;
  --navy: #111a24;
  --navy-soft: #1b2936;
  --paper: #f1f1eb;
  --paper-warm: #e9e9e1;
  --line-dark: rgba(255, 255, 255, 0.18);
  --line-light: rgba(13, 16, 18, 0.15);
  --muted-dark: #9ca5a8;
  --muted-light: #697275;
  --accent: #d9ff52;
  --accent-soft: #efffb0;
  --blue: #67a9e8;
  --pass: #86d99d;
  --warning: #e7bd68;
  --fail: #ed7770;
  --error: #f06464;
}
```

Use the accent only for primary actions, active navigation, selected states, and small highlights. Do not make every component bright green.

## Typography

Use one strong display typeface and one neutral interface typeface. If external fonts are unavailable, use a system fallback stack.

```css
:root {
  --font-display: "Arial Narrow", "Helvetica Neue", Arial, sans-serif;
  --font-body: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}
```

### Type hierarchy

| Element | Direction |
|---|---|
| Hero headline | 8–15vw, tight line-height, uppercase or sentence case with restraint |
| Section heading | 4–7rem on desktop, responsive on mobile |
| Eyebrow label | 0.7–0.8rem, uppercase, letter spacing, muted color |
| Body copy | 1–1.25rem, relaxed line-height, limited width |
| Metric number | 3–7rem, condensed or bold |
| Metric label | Small uppercase label with tracking |
| Technical evidence | Monospace, slightly smaller, high contrast |

Do not use too many font weights. Use regular, medium, semibold, and bold only when needed.

## Layout system

Use a responsive content container:

```css
.container {
  width: min(100% - 3rem, 1440px);
  margin-inline: auto;
}
```

Use a generous spacing scale:

```css
--space-1: 0.5rem;
--space-2: 1rem;
--space-3: 1.5rem;
--space-4: 2.5rem;
--space-5: 4rem;
--space-6: 6rem;
--space-7: 9rem;
--space-8: 13rem;
```

Use large vertical sections on desktop and reduce them gracefully on mobile.

## Landing-page structure

### Header

The header should be minimal:

- Phoenix Protocol wordmark.
- Small product descriptor.
- Optional navigation link to Rules.
- Primary action: Start a scan.

Use a transparent header over the hero and a solid or blurred background after scrolling.

### Hero

Suggested original copy:

> **NETWORK SECURITY.**  
> **CLEARLY VERIFIED.**

Supporting copy:

> Read-only configuration compliance for teams that need to understand risk before it becomes an incident.

Include:

- A short eyebrow such as `CONFIGURATION COMPLIANCE / 01`.
- A single primary action.
- A subtle read-only label.
- An abstract device-node visual or animated line system.

Do not put a huge list of features inside the hero.

### Trust strip

Use a quiet strip under the hero:

```text
READ-ONLY BY DESIGN     EVIDENCE-FIRST RESULTS     DETERMINISTIC RULES
```

This should build confidence without using fake customer logos or unverified claims.

### Capability section

Use five editorial blocks:

1. Upload configurations.
2. Extract evidence.
3. Prioritize risk.
4. Explain findings.
5. Export the record.

Each block should use an index number and concise copy. Avoid identical card layouts repeated five times.

### Network visibility section

Create an original abstract topology showing sample devices connected through lines and nodes. Use labels such as:

- Edge router.
- Branch switch.
- Core firewall.
- Wireless controller.
- Virtual gateway.

Label the visual `SAMPLE ENVIRONMENT` so users do not mistake it for live infrastructure.

### Scan notes section

Use editorial insight cards based on demo data:

- `04` HIGH-SEVERITY FINDINGS.
- `12` CONFIGURATIONS REVIEWED.
- `03` MANUAL REVIEWS NEEDED.

Each metric must be labeled and explained. Do not invent real customer data.

### Call to action

End with a simple statement:

> **SEE WHAT PASSED.**  
> **UNDERSTAND WHAT DIDN’T.**

Primary button: `Start a scan`.

## Dashboard visual direction

The dashboard should feel like the operational version of the landing page.

Use:

- Dark header area.
- Large scan metrics.
- Thin dividers.
- Off-white reading area for tables.
- Strong high-risk finding treatment.
- Compact but readable rule details.

Avoid turning the dashboard into a grid of identical rounded cards. Use a mixture of metrics, lists, tables, and editorial headings.

## UI surfaces

Use restrained borders rather than heavy shadows. Use rounded corners sparingly:

- Buttons: small radius.
- Upload zone: medium radius.
- Evidence panel: small radius.
- Main sections: mostly square or subtly rounded.

Do not use glassmorphism everywhere. One translucent overlay in the hero is enough.

## Buttons

Primary button:

- Dark background on light sections or accent background on dark sections.
- Strong label.
- Small arrow or directional indicator.
- Subtle hover movement.

Secondary button:

- Transparent background.
- Visible border.
- Muted until hover.

Do not use gradient buttons.

## Status design

Always show status as text:

| Status | Color | Text |
|---|---|---|
| Pass | Green | PASS |
| Fail | Red | FAIL |
| Warning | Amber | WARNING |
| Not applicable | Gray | NOT APPLICABLE |
| Error | Red | ERROR |

Color is a supporting signal, never the only signal.

## Responsive design

At desktop widths, use large typography, split layouts, and generous spacing.

At tablet widths, reduce headline size and stack complex split sections.

At mobile widths:

- Keep the hero headline large but readable.
- Stack buttons.
- Make upload controls full width.
- Convert metric rows to a vertical list or two-column grid.
- Allow technical tables to scroll horizontally.
- Keep high-risk findings visible without excessive interaction.

## Anti-AI visual checklist

Before finalizing, remove:

- Generic gradient blobs.
- Excessive pill-shaped UI.
- Repeated cards with identical copy length.
- Random decorative icons.
- Unnecessary glowing borders.
- Excessive rounded containers.
- Fake testimonials.
- Fake customer logos.
- Generic “revolutionize your workflow” language.
- Unexplained animated counters.

The result should look like a designer made intentional decisions for a security product.
