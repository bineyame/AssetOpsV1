# Start Here

A router. It says where the current truth is; it does not hold it.

Current milestone: demo sprint (live product on `main`) running alongside the
Layer 4 product-direction design, which awaits owner decisions. Repo declutter
in progress (step 2 of 5). Detail: `.ai/NOW.md`.

Planning status: the S1-S7 queue is built; new product work waits on the owner's
Layer 4 decisions (Q1-Q16, D1-D12). Demo-sprint fixes are sequenced by the
coordinator (`.agent/coordinator-handoff.md`). To confirm: whether any
demo-sprint unit is still open after the 17 Nov client demo.

## Direction and its boundary (owner O1, 2026-11-18)

- **Live product: S1-S7 / Site-first stays authoritative.** Work on the
  running product follows
  `frontend/docs/architecture/production-shaped-mvp.md`,
  `frontend/docs/architecture/production-shaped-mvp-technical-design.md` and
  `frontend/docs/architecture/site-first-execution-plan.md` (read by section),
  plus the demo-sprint rulings `.ai/NOW.md` names.
- **Destination: Layer 4** (on branch `task/product-direction-layer4-design` until it merges to
  `main`). `Docs/demo-sprint/product-direction-layer4/` is
  where the product is going. Entry point:
  `Docs/demo-sprint/product-direction-layer4/product-transition-and-roadmap.md`
  (decisions in its §6; open questions in
  `Docs/demo-sprint/product-direction-layer4/design-questions-and-decisions.md`).
  It **supersedes S1-S7 once the owner approves Q1**. Until then it is a
  design under review, not build authority.
- Lookup files in the pack (`derivation-register.md`,
  `outcome-lever-capability-traceability.csv`, the `.html` twins) are
  searched, never read whole.

## Which mock governs which work (owner O2, 2026-11-18)

| Work | Reference |
| --- | --- |
| Screens and content of the live product | `frontend/mockups/v70/index.html` and `frontend/mockups/v70/screen-manifest.json`, by the named screen |
| Visual style, and its four hi-fi pages | `frontend/mockups/v72/` (`foundation-sheet.html`, `portfolio-hifi.html`, `site-overview-hifi.html`, `upload-readings.html`) |
| Layer 4 destination (still changing) | `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/` |

Do not read `frontend/mockups/v69/` or `frontend/mockups/v71/`. Guards still
use the `frontend/docs/architecture/v69-*` registries by name; that is guard
plumbing, not mock authority. A mock is an interaction and content reference:
it does not authorise a claim the data cannot support. Show a missing source as
"not available yet".

## Authority order

1. The owner's instructions (verbatim files `.agent/owner-*.md`).
2. The active spec's acceptance criteria and rulings.
3. `.ai/RULES.md` and `.ai/ROLE_CONFIG.md`.
4. The direction documents above, inside the O1 boundary.
5. `.ai/PRODUCT.md` and `.ai/ARCHITECTURE.md`, where compatible with 4.
6. Existing code and tests.

When two conflict, follow the higher one and record the consequence as a
decision (`.ai/decisions/`, or the active rulings file, plus an index line).

## Where things are (find on demand)

- Active work: `.ai/NOW.md`. Coordinator state: `.agent/coordinator-handoff.md`.
- Decisions, every ID family (dated, D-SR, D-E5, D-ANY ...): grep the ID in
  `.ai/decisions/index-*.md`; how-to in `.ai/decisions/INDEX.md`.
- Built state: `.ai/state/INDEX.md`; grep the slice ID in `.ai/state/index-*.md`.
- Specs (build sheets and specs, still in `.agent/`): `specs/INDEX.md`.
- Owner feedback by status: `owner/INDEX.md` (current files listed there).
- S1-S7 queue tables (machine-read by guards): `tasks/README.md`.
- UI defaults: `frontend/docs/architecture/ui-ux-decision-guide.md`.
- Tests: `backend/TESTING.md`. Guards: `tools/check-all.ps1`.

`python tools/check-decision-index.py` (in check-all) keeps the indexes whole.
