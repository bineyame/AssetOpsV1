# UQ-0 packet: v7.2 design-foundation sheet (for owner approval, Thursday evening)

Branch `task/UQ-0-v72-sheet` (from main `db447d0e0`). No product code changed.
Sheet: `frontend/mockups/v72/foundation-sheet.html` (one page, self-contained, no network requests).
Sources: `.agent/architect-answer-ui-quality-2026-11-10.md` (stage 1, QW), `.agent/architect-plan-pre-client-2026-11-10.md` (UQ-0..UQ-4, section 3 font), BL-69, owner item 13.

## What the owner is approving

The **look** of the whole app: colours, type, spacing, corners, shadows and the shared states, in a light and a dark theme. It replaces the v6.9/v7.0 type scale and colours as the spec. It does **not** change layouts or words: v7.1 stays the layout spec for the Portfolio and the shared date range, and each page keeps its MOCK DEVIATION labels until its own v7.2 page lands. Approval gates UQ-1.

## Decisions embedded (each from owner item 13 or the Architect plan)

| Decision | Value on the sheet | Basis |
|---|---|---|
| Font | **Inter** (variable, OFL 1.1), self-hosted in UQ-1; fallback `system-ui, Segoe UI, Roboto, Noto Sans, …` with tabular figures | item 13.2 "lets have one"; Architect recommends Inter |
| Themes | **Light and Dark**, user-selectable; control in the top bar: System / Light / Dark | item 13.3 "dark and white for the user to select" |
| Default theme | **System** (follows the computer); choice kept per browser, System if storage is blocked; set before first paint | UQ-2 row |
| Smallest text | **12 px** floor (table heads, menu group names, chips were 9-10 px) | QW item 1 |
| Body | **14 px**; tables 14 px comfortable / 13 px compact | QW item 1, stage 1 |
| Type scale | 8 steps: 12 / 13 / 14 / 16 / 18 / 20 / 24 / 30 px; page title 27 → 24 px | stage 1 |
| Numbers | tabular figures on tables, card figures, money | stage 1 |
| Tokens | three tiers: primitive → semantic (light + dark values) → component | stage 1 |
| Spacing, radius | 4 px scale (4…64); radius 4 / 8 / 12 / pill | stage 1 |
| Elevation | light: soft shadows; dark: no card shadow (surface steps + border), deeper popover shadows | modern practice (Material 3, Atlassian) |
| Reading states | 8 D-E5.46 words, each one tone **and** one glyph shape (colour never the only signal): complete green, partial amber, too few / not enough orange, no readings grey, conflicting red, still processing blue, not analysed yet dashed neutral | D-E5.46, WCAG 1.4.1 |
| Pillars | marker colours: Grow teal, Optimize cost indigo, Protect plum, Assure cyan; always with the name | four outcome categories |
| Left menu | structure unchanged (groups, items, order, icons from v7.1/v7.0); only colours and the 12 px group names | owner item 4 |
| Focus | 2 px gap + 2 px ring in the accent, both themes | WCAG 2.4.7 / 2.4.11 |
| Motion | skeleton shimmer and retry spinner stop under `prefers-reduced-motion` | stage 1 |

## Evidence

- Contrast: 36 text/mark pairs, computed from the sheet's own token blocks (the in-page table and a Node re-check agree). **36/36 pass AA in both themes.** Lowest values: text-muted on page 4.89:1 (light); control border 3.44:1 (light, needs 3:1); partial-readings chip 5.44:1 (light).
- Layout: headless Chrome 1400 px and the narrowest headless width (526 px; Chrome would not go below it): 8 panes rendered, 0 elements overflow a pane, page has no sideways scroll. 390 px checked by eye from a screenshot only.
- Font: Inter is not installed on this machine, so the sheet rendered in the fallback; the sheet says which font renders. Letter shapes in Inter are therefore **not** shown on this computer.

## Open choices (recommendation first)

1. **Font file on the sheet.** The sheet uses Inter only if it is installed locally (no CDN, by rule). Rec: accept the sizes and colours on this sheet; UQ-1 vendors `InterVariable.woff2` + `OFL.txt` and its acceptance includes a glyph check for French accents (é…œ, « », the U+202F narrow space). If you want to see Inter's letter shapes before approving, install Inter (rsms.me/inter) and reload.
2. **Dark-theme rail.** Rec: a darker navy (`#0e1729`) with the current item as a muted navy (`#2a3d63`), not bright blue, so the dark theme is calm. Alternative: keep the light theme's blue highlight.
3. **Too few vs not enough readings** share the orange tone and differ by glyph (quarter circle vs minus). Rec: keep them together (both mean "not counted: too little data"). Alternative: give "not enough" its own hue (one more colour to learn).
4. **Table density.** Rec: 44 px rows (comfortable) by default, 36 px compact only on analyst tables (Evidence receipts, Operational records).
5. **French and Swahili samples** on the sheet are rough drafts for length only, marked "draft"; the real wording is UQ-8, and a language is offered only after its reviewer signs off.

## Known deviations

- The outcome card shows the stage-2 shape (one figure, one sentence, a basis chip) to show the new look; the v7.1/PF card content and layout remain the spec until a stage-2 Portfolio mockup is approved.
- Process: one edit was made with `sed -i` (later edits used Edit), against the session's "Write/Edit only" rule. File content is unaffected.

USER_REVIEW_REQUIRED: yes. The owner approves the sheet before UQ-1 starts.
