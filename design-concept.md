# Ezzystore Redesign Concept (Detailed)

Direction: Bold dark-fluid aesthetic with neon accent gradients (teal/sky/emerald) on layered glass panels. Priorities: clarity, generous spacing, strong hierarchy, consistent components across login/admin/manager.

## Global Tokens
- Typography: Inter (headlines 900/800, subheads 700, body 500/600). Labels use letter-spacing +0.12em, uppercase.
- Palette:
  - Backgrounds: `#050a18` → `#0b132b`
  - Surfaces: `#0f1f3d` (cards), `#111a30` (panels), glass overlays with `rgba(255,255,255,.04–.08)`
  - Accents: `#0ea5e9` (primary), `#10b981` (success), `#f59e0b` (warn), `#ef4444` (danger)
  - Text: `#e8ecf5` primary, muted `#9aa8c1`
  - Borders: `rgba(255,255,255,.08–.14)`
  - Shadows: `0 28px 70px rgba(5,8,20,.35)`, softer `0 12px 30px rgba(5,8,20,.25)`
- Radii: 18–24px for cards/modals; pills 999px.
- Focus ring: `0 0 0 6px rgba(14,165,233,.24)`; focus-visible on links/buttons/inputs.
- Gradients/glow: Use subtle radial glows behind key CTAs (not full-screen noise).

## Components & Layout
- Shell: Max width 1100–1200px; vertical rhythm 20–28px; keep breathing room on mobile.
- Hero: Split hero (logo + text + CTA); background blur gradient; logo in neon badge.
- Cards: Glass panels with light sweep, accent edge; consistent padding 20–24px; minimal borders.
- Navigation (manager/admin): Pill tab bar with icons; active pill uses accent gradient + inner glow; hover lift -1/2px.
- Stats:
  - Mini stats: Accent gradient tile, bright numerals, small label with increased letter-spacing; optional icon chip.
  - Stat cards: Dark gradient surface with accent border; eyebrow + numeric + helper text.
- Tables: Dark surface; zebra hover `rgba(14,165,233,.06)`; table headers muted; IDs in pill badges; actions as icon buttons or compact pills.
- Forms/Inputs: Dark input background, thin border; primary CTA gradient (teal→emerald); secondary ghost with thin border; radios/checkbox accent color teal.
- Buttons: Primary gradient, secondary glass, ghost bordered; mini pills for inline actions; disabled state with reduced opacity.
- Modals: Glass background, accent top border; shadow; close button as ghost icon.
- Alerts/Toasts: Glass tile with colored border/background tint per status; icon + text; slide/fade in.

## Page-Specific Notes
- Login: Centered glass card; neon ring around logo; background with dual radial glows; single CTA; concise errors.
- Admin: Hero with owner info + stats row; two-column grid for actions/insights; timeline with glowing dots; tables for shops/managers.
- Manager:
  - Landing shows module cards only (no overview stats section); each card has title, short copy, metrics, CTA.
  - Module pages (products, stock, sales, reports, customers, brands, categories) each get: hero + key actions bar + optional mini-stat row relevant to module.
  - Tables and forms follow shared styles; keep modals glassy.

## Motion & Micro-interactions
- Hover: 120–180ms translateY(-1px) + shadow lift.
- Focus-visible: Accent outline; no outline removal.
- Toasts: Slide up + fade (180ms).
- Buttons: Active state slight press (scale .99).

## Implementation Plan
1) Update shared tokens in `style.css` (colors, radii, shadows, focus rings).
2) Apply palette/radii/shadows to `login.css`, `admin.css`, `manager.css`; remove leftover light backgrounds.
3) Rebuild nav/tab and stat styles per spec; ensure text contrast on dark surfaces.
4) Restyle tables, forms, buttons, modals, alerts to glass/dark theme.
5) Adjust templates to drop obsolete inline styles and keep consistent hero + module cards; keep module pages separate (no overview).
6) Quick manual pass in browser to confirm contrast, spacing, responsive behavior.
