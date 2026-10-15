# S4-04 — Site FindingIndex and list

Status: outline (S incremental closeout); refine after S4-01, before activation
USER_REVIEW_REQUIRED: true
Depends on: S4-01 reviewed Finding revision and `A-finding-index` contract
Branch when activated: task/S4-04-site-finding-index

## Visible outcome

`sitefindings:1` shows a Site/window scoped list with separate honest zero-row and positive persisted Finding rows. This is not a global Findings index.

## Acceptance

- Implement resolved `A-finding-index` (`D-2026-10-15-a-finding-index`): `I-finding-index` returns scoped rows, selection watermark, stable Finding ID and exact revision link. Bound the selectable window to 31 UTC days and prove discovery through current selection seq for every intersected UTC day and 20-minute continuity neighbour. Add a new read without changing the existing `findings_over` helper. `I-site-findings-ui` opens the detail route after reload.
- `D-site-finding-index-empty` proves a watermarked zero-row result and a closed S3 source-gate 409 `PERFORMANCE_CUTOVER_CLOSED` with its reason and no current/no-Findings claim; `D-site-finding-index-rows` proves persisted positive rows. Test that the first index row equals the S5-01 card Finding and selected revision on the same Site/window/basis. Both variants are required for W1 core completion.
- Compare app/mock `sitefindings` at desktop and narrow widths, including selected Site/window, keyboard navigation and an exact detail drill-down. Independent review and owner checkpoint close this packet.
