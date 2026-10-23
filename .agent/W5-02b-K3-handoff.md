# W5-02b K3a + K3b handoff (cold Incidents and Maintenance tabs)

Branch `task/W5-02b-K3-cold-cases` from main `f164c49d`, with main merged at `e0c1c40c` (the K3 pre-flight rulings 1-8 and register rows R92-R94). Scope is K3a and K3b only. K4 and K5 are not touched.

## Pre-flight

`.agent/W5-02b-K3-questions.md` (Q1-Q8, `dd325a97`) was ruled in `.agent/W5-02-build-spec.md` "K3 pre-flight rulings" (:317-328). One point still contradicts code; see Open item 1.

## Commits

| Commit | Unit | What |
|---|---|---|
| `12a5d77b` | K3a | `siteWorkCases.tsx`: `site` prop and COLDCHAIN presentation. Covers the mock strip, `Manage in … →`, R91 notice, `siteWindowText`, `coldAssetLabel` and `coldRequestHref`. Also R65/R66 Findings, R68 WR link, R70/R71/R89 cells, coverage line hidden on cold, R92/R93 kept, and the domain foot notice. `SiteAnalyticsFrames.tsx` passes `site`. `panelStructure.ts` admits the notice on the two case screens. New `coldWorkCases.test.tsx`. |
| `d4e93f64` | K3b | `tools/w502_cold_work_walkthrough.py`: `worstcase` gets four more INC/WR+record (ruling 7 literals, `pad160`, the ruled minutes and keys). Adds W4 case reads per read window and returned cutoff, plus the ruled `[D-8d, D-1d)` case-zero window. Adds the case-read 403/503 router in `SERVE_ENTRY` for `forbidden`/`unavailable` only (`W502B_CASE_GATE`). Attest checks case reads and served case refusals. Fixes the backlog attest gap: a no-reads mode now appends a failure. |
| `2d007369` | K3b | Ledger rows `cold-work`, `cold-work-incidents`, `cold-work-maintenance` and their three panel contracts, using the spec :88-90 literals. `A-cold-work-projections` and `P-work-cases` are untouched, and pilot JSON is unchanged. |
| `85911703` | K3b | `tools/w502-cold-work-evidence.mjs`: `W502B_EVIDENCE=cases` mode, with the states and claims listed below. Writes `w502b-k3-measurements.json`. |
| `895b020b` | K3b | `w1f4-action.css`: cold case-cell rules under `[data-cold-cases]`. `Body` gets `data-cold-cases` on COLDCHAIN. |

## Runs (code-only phase, machine constraint)

- `npx tsc --noEmit`: clean.
- Focused vitest: `coldWorkCases.test.tsx` 24/24. Adjacent tests: `siteWorkCases`, `coldWorkActions`, `w1f4ChangesWorkStructure`, `operatorSiteTabs`, `operatorRouteFrames`, `siteDetailRoute`, 6 files, 152/152, all green after the last code change. That covers 52/52 across `w1f4ChangesWorkStructure` and `coldWorkActions`, and 36/36 across `coldWorkCases` and `siteWorkCases`.
- Guard non-vacuity: removing the `cold-work-incidents` `SCREEN_LEADING` entry fails 5 tests. Reverted with `git checkout`.
- `tools/check-all.ps1`: 11/11 on `12a5d77b`. Re-run on the final head: see the report.
- Ledger checker and dependency-registry checker pass on `2d007369`.
- `python -c ast` parse check of the tool and its three templates: OK. `node --check` on the evidence tool: OK.
- **Not run (held for the coordinator's batch signal):** Postgres tests, full vitest, build, `prepare/serve/attest` and captures. Evidence dir `.agent/W5-02b-K3-evidence/` is not yet produced.

## Capture states (K3b, run in the batch)

Per width (1440, 390) and per tab (incidents, maintenance), against CASE_CAPS page 1400/1800, panel 440/650, strip 100/150, notice 110/160:
- positive
- historical
- zero (ruled window)
- worstcase (5 rows)
- worstcase-one-open
- worstcase-all-open
- pending, stale, unknown (the notice must follow the returned case status)
- forbidden-403 and unavailable-503 (W4 refusal inside the case panel, Site read healthy)

Claims cover no document overflow, the caps, per-cell containment, a preview of at most two lines, the sticky first column, the mock columns, strip literals, Site-local Window, plain Findings, the R89 asset, the R68 WR href, the R72 gap, the R92/R93 blocks, a single date form and no banner. All-open keeps the panel cap (ruling 7); if it fails I will report the measurement and not clip.

## Judgment calls (each one follows a ruling's letter; please confirm)

1. **WR Overview `known_at`.** Only the explicit URL cutoff (`scope.knownAt`) is carried, per P-G-4 ("selected explicit cutoff when present"). The loaded list's `known_at` is not used.
2. **Extra worst-case WR shape.** No literal was given for it. It mirrors the fixture WR: the selected Finding link (`flink`), `incident_id` set to its own extra INC, and the W4 default narrative (not displayed).
3. **Nested long text in disclosures.** Ruling 7 applies `Read full text` to the "Activity recorded body and Outcome note body". The disclosure body therefore holds a two-line preview with its own `Read full text`, which nests one disclosure inside another. This is the literal reading.
4. **Case-zero window.** The case zero uses the ruled `[D-8 days, D-1 day)` with `D` = the shifted source day. The K2 Actions zero stays at its existing `[day-8, day-1)`.
5. **Long-text component.** `CaseLongText` in `siteWorkCases.tsx` duplicates K2's private `LongText`, with the same data attributes and behaviour. `SiteWorkActions.tsx` is outside K3's file lists and already imports `siteWorkCases.tsx`, so reusing it would mean editing that file and creating a circular import.
6. **Untouched ledger fields.** `follow_on`, `interaction` and `unknown_or_empty` are left as they were, following the W5-03a precedent. The spec names only the fields that were changed.

## Rulings 9-16 (main `ee99f940`, merged)

- Ruling 9 resolves the open refusal item with option (a): W4 `Refused` stays unchanged. The tests and capture tool assert the title, its fixed sentence, the refusal kind and code, and that neither the server message nor Retry appears.
- Rulings 10-15 confirm judgment calls 1-6 with no code change. For ruling 12, the test and the capture tool also assert that nested summaries are native, focusable and unclipped.
- Ruling 16: the capture tool exempts only the five-row all-open state from the case panel cap. It logs that panel height as INFO, and every other gate still applies.

## Shared plumbing

- `frontend/src/test/panelStructure.ts`: a guard extension only, granted by ruling 5.
- `SiteWorkCases` gains an optional `site` prop; MINIGRID and EV pass through the same W4 code paths unchanged.
- No backend, `App.tsx`, `NavRail`, `SiteWorkActions.tsx` or W4 golden edits.
