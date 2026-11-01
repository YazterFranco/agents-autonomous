---
name: frontend-design-direction
description: Set an ECC-specific frontend design direction for production UI work. Use when building or improving websites, dashboards, applications, components, landing pages, visual tools, or any web UI that needs stronger product-specific design judgment.
metadata:
  origin: community
---

# Frontend Design Direction

Use this skill when the work is not just making UI function, but making it feel
purposeful, polished, and appropriate to the product domain.

Source: salvaged from stale community PR #1659 by `linus707`.

Note: ECC intentionally does not rebundle the canonical Anthropic
`frontend-design` skill. Install that from `anthropics/skills` when you want the
official upstream skill. This skill is the ECC-specific design-direction salvage
of the useful local guidance from #1659.

## When to Use

- The user asks to build a web page, app, dashboard, artifact, component, or UI.
- The user asks to make an interface more polished, distinctive, beautiful, or
  less generic.
- The implementation needs visual hierarchy, typography, color, motion, layout,
  and interaction choices.
- The current UI works but reads as flat, generic, templated, or mismatched to
  the audience.

## Design Direction

Before coding, choose a specific direction:

1. Purpose: what job does the interface do?
2. Audience: who repeats this workflow, and what do they need to scan first?
3. Tone: utilitarian, editorial, playful, industrial, refined, technical,
   maximal, minimal, dense, calm, or another explicit direction.
4. Memorable detail: one design idea that makes the result feel intentional.
5. Constraints: framework, accessibility, performance, responsiveness, and
   existing design system.

Match the direction to the domain. A SaaS operations tool should usually be
dense, quiet, and scannable. A portfolio, launch page, game, or editorial piece
can be more expressive. Do not force a landing-page composition onto a tool that
needs repeated daily use.

## Implementation Guidance

### Evidence contract and content states

Before implementation, record the product surface, user's job, primary action,
hierarchy, target viewports and the reference observation behind each important
choice. Make these constraints checkable; a palette alone is not evidence.
Use local product references when external research is unnecessary or unavailable.

For each relevant state, record its trigger, visible feedback and safe next action:

| State | Check |
| --- | --- |
| Loading | Stable structure and progress; cancellation where supported |
| Empty | Explain missing data and offer a useful next action |
| Error | Specific failure and a recovery path |
| Partial | Show available data and clearly mark unavailable portions |
| Success | Confirm completion and show the next action or supported undo |
| Permission | Explain the access boundary and a safe request/return path |

Record a reason when a state does not apply. Unavailable test access is an
untested state, not a reason to mark it not applicable.

### Build from the contract

- Build the actual usable experience as the first screen unless the user
  explicitly asks for marketing copy.
- Use existing project components, tokens, icon libraries, and routing patterns
  before introducing a new visual system.
- Use real or generated visual assets when the interface depends on images,
  products, places, people, gameplay, charts, or inspectable media.
- Prefer contextual typography and spacing over generic oversized hero text.
- Keep palettes multi-dimensional: avoid a UI dominated by one hue family.
- Use CSS variables or existing design tokens so the direction remains
  coherent across states.
- Design responsive constraints explicitly: grids, aspect ratios, min/max
  sizes, stable toolbars, and fixed-format controls should not shift when labels
  or hover states appear.
- Use motion sparingly but deliberately. Prefer high-signal transitions that
  clarify state over decorative animation.
- Verify text fit on mobile and desktop. Long labels must wrap or resize
  cleanly rather than overflowing.

## Anti-Patterns

- Do not default to common generated patterns: purple gradients, decorative
  blobs, oversized cards, vague hero copy, or stock-like atmospheric media.
- Do not add UI cards inside other cards.
- Do not use a single decorative style everywhere when the domain calls for
  restraint.
- Do not hide the primary product, tool, object, or workflow behind generic
  marketing sections.
- Do not add a new dependency for a design flourish unless it clearly pays for
  itself.
- Do not describe the UI's features inside the UI when the controls can speak
  for themselves.

## Review Checklist

- The first viewport immediately communicates the product, workflow, or object.
- The visual hierarchy supports scanning and repeated use.
- Typography fits the container and does not overlap adjacent content.
- Color choices have contrast and do not collapse into a one-note palette.
- Icons are used for familiar tool actions where available.
- Responsive layout has stable dimensions for boards, grids, toolbars,
  controls, tiles, and counters.
- Assets render and carry the subject matter instead of acting as filler.
- Motion improves orientation and does not mask sluggishness.
- The result matches the repo's existing frontend conventions unless there is a
  clear reason to depart.

### Rendered finish gate

Inspect the rendered interface at the contract's target viewports. Check keyboard
navigation, visible focus, labels, contrast, reduced motion and touch targets;
check narrow/wide layouts with long content; exercise each applicable content
state, including partial data. Source inspection alone cannot pass this gate.
Keep screenshots or browser-test artifacts in the workspace and record what each
shows. Fix failures, then repeat affected checks after structural changes.


> POC note: excerpt vendored from ECC for the local autonomous agent. Load full references only as needed.
