# Phoenix Protocol Loading and Motion Design Specification

## Motion goal

Motion should make Phoenix Protocol feel precise, responsive, and alive without becoming distracting. The product is a security tool, so animation should communicate state and progress honestly.

Use motion to:

- Explain transitions.
- Confirm user actions.
- Reveal information progressively.
- Make scan analysis feel tangible.
- Guide attention to important findings.

Do not use animation to hide slow work or simulate progress that the backend does not provide.

## Motion principles

### Calm and deliberate

Use short, smooth transitions. Avoid bouncing elements, excessive parallax, or rapid flashing.

### Purposeful hierarchy

The most important motion belongs to:

- Starting a scan.
- Showing that analysis is in progress.
- Revealing results.
- Highlighting high-risk findings.
- Opening evidence details.

### Consistent timing

Use a small timing scale:

```css
:root {
  --ease-standard: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-soft: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 180ms;
  --duration-normal: 360ms;
  --duration-slow: 700ms;
}
```

### Respect reduced motion

Implement:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

The application must remain understandable and usable with motion disabled.

## Page-load animations

### Hero entrance

On first load:

1. Header fades in and moves upward slightly.
2. Eyebrow appears.
3. Hero headline reveals line by line.
4. Supporting text fades in.
5. Primary action appears.
6. Network-node visual draws in quietly.

Use staggered animation, but keep the total entrance under approximately 1.2 seconds.

Suggested CSS behavior:

```css
.reveal {
  opacity: 0;
  transform: translateY(18px);
  animation: reveal-up 700ms var(--ease-standard) forwards;
}

@keyframes reveal-up {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

Do not delay the upload control so long that the page feels unresponsive.

## Scroll animations

Use subtle reveal-on-scroll for major sections:

- Capability blocks.
- Network topology visual.
- Scan insight cards.
- Dashboard preview.

Each section should animate once when it enters the viewport. Do not animate every small text node.

If using `IntersectionObserver`, disconnect observers when components unmount.

## Button interactions

### Primary button

On hover:

- Shift the arrow or directional indicator slightly.
- Change accent or background contrast.
- Avoid scaling more than 1–2%.

On press:

- Use a small downward movement.
- Return quickly.

### Disabled button

Do not animate disabled controls. Make the disabled reason understandable through nearby help text.

## File upload interactions

### Drag-over state

When files are dragged over the upload zone:

- Increase border contrast.
- Show a subtle accent background.
- Display “Drop configuration files here”.

When the drag leaves:

- Restore the default state smoothly.

### File added

When a file is accepted:

- Add its row with a short fade-and-slide animation.
- Show filename and size.
- Do not animate the entire list.

### File rejected

When a file is rejected:

- Show a clear inline error.
- Use a small shake only if it remains accessible and subtle.
- Do not use repeated flashing.

## Scan-start animation

When the user clicks **Run compliance scan**:

1. Button changes to a loading state.
2. Upload controls become disabled.
3. A status panel appears.
4. Abstract network lines or nodes can gently pulse.
5. Text explains that files are being validated and analyzed.

Use honest copy:

> Validating files and evaluating security rules.

Do not show fake “73% complete” values unless the backend provides real progress.

## Loading indicator options

Use one of these simple patterns:

### Spinner

A small circular spinner is appropriate for short synchronous requests.

### Scanning line

A horizontal line can move slowly across a small scan-status panel. Keep it decorative and pair it with truthful text.

### Pulsing nodes

For the network visual, let a small number of sample nodes pulse in sequence. Keep the animation slow and low contrast.

Do not combine all three patterns at once.

## Dashboard reveal

After results arrive:

1. Fade out the loading state.
2. Reveal the scan header.
3. Count or reveal summary metrics with a short stagger.
4. Reveal high-priority findings.
5. Reveal the device table.

Do not use fast count-up animations that make numbers difficult to read. If metrics animate, keep them under 700ms and ensure the final value is immediately accessible.

## Finding emphasis

When high-severity failures appear:

- Use a subtle border or accent line.
- Reveal the finding row with a short fade.
- Do not flash red or use alarming shaking.
- Keep the failure readable after the animation ends.

## Evidence expansion

When a rule-result row opens:

- Expand the evidence panel with height and opacity transition.
- Keep the row position stable where possible.
- Use a clear disclosure control with `aria-expanded`.
- Do not hide evidence behind hover.

## Modal or drawer motion

If using a modal or drawer for rule details:

- Fade the backdrop.
- Slide the panel from a predictable direction.
- Trap focus correctly.
- Close with Escape.
- Restore focus to the opening control.
- Disable motion when reduced motion is requested.

## Report download feedback

When the user selects a report:

- Show a short pressed state.
- If generation is asynchronous, show a truthful loading state.
- After the browser begins download, show a non-blocking confirmation such as “Report download started.”

Do not show a fake success message before the request is initiated.

## Error transitions

Errors should appear with a short fade or slide, not a dramatic animation. Keep the message visible until the user dismisses it or fixes the issue.

## Performance rules

- Prefer CSS transforms and opacity.
- Avoid animating layout-heavy properties repeatedly.
- Do not animate large images unnecessarily.
- Do not add a heavy animation library unless the existing project already uses one.
- Keep motion smooth on mid-range laptops and mobile devices.
- Test with browser throttling.

## Motion acceptance criteria

Motion is successful when:

1. It makes the interface feel polished but not distracting.
2. Loading states communicate actual application state.
3. Users can complete the scan with motion disabled.
4. Keyboard users can access all animated content.
5. The page remains fast.
6. Important security findings are emphasized without panic-inducing effects.
7. The experience feels designed rather than generated from a template.
