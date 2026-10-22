# W2-F final review: W2 structural corrections

Reviewer: independent Claude reviewer (did not author any W2-F unit). Branch `task/W2-F-structural-fixes`, head
`626e0171` (code head `fe3915ad`; `626e0171` touches only `.agent/`). Diff reviewed: `git diff main...HEAD` (main
`f26d3bd3` is an ancestor of HEAD). Contract: `.agent/W2-F-build-spec.md`, including the ledger, "Review closure
(2026-10-21)" B1-B2/S1-S12/N0-N9, and "Copy rulings (q1)". Also read: `.agent/W2-F-pending-rulings.md` (both items
RESOLVED), `.agent/W2-F-review-packet.md`, and `.agent/W2-F-phase-handoff.md`.

## Verdict: ACCEPT

All 14 findings are closed as ruled, and each has a named test that I ran and saw pass. M12 is closed by unit 4b
(`fe3915ad`): the guard and the rail fixture changed in the same commit, and the fixture is non-vacuous. The panel
set, order and prominence match v69 on the W2-F screens I viewed. Code changes stay inside the files the spec names.
There are no High or Medium findings. The two Low findings below do not block the merge.

## Findings

**L1 (Low; a gap against the literal ledger, not misleading).** The refused cold Finding page has no neutral Unknown
strip. `frontend/src/sites/ColdAssessmentViews.tsx:1081-1085` still renders the existing `PageRefusal` and skeleton.
The M13 ledger state table lists `refused→unknown strip` for both strips. The builder read S12's last sentence
("refused strip is neutral Unknown") as covering EV only and recorded this as reading 1b(5). The page states the
refusal honestly, so nothing false is shown. However, the Finding-state strip slot is missing on cold but present on
EV (`Unknown` / `Confidence: Unknown`). The fix is either an Architect confirmation of reading 1b(5), or a
`StatusBar label="Finding state"` with `Unknown` / `Confidence: Unknown` above the `PageRefusal`, plus one assertion
in `coldRoutes.test.tsx::w2f_finding_strip_confidence`.

**L2 (Low; evidence provenance).** The top level of `.agent/W2-F-evidence/evidence.json` says
`"revision": "fe3915ad"`. Only the 4 EV Financials/Assumptions pairs were recaptured at that revision. The other 68
pairs come from `4d4fa252`, which is before the W4-03 main merge `f40dfebe`. Those older captures still show the shell
rail's `Evidence` and `Financials` as `Not available yet`, but both are live at head (W3-02/W4-03 shell changes; see the
recaptured `ev-financials-interrupted-1440-app.png`). No W2-F screen code changed between `4d4fa252` and `fe3915ad`
except the 4b Scenarios literal. I checked this with `git diff --stat 4d4fa252 fe3915ad -- frontend/src`. The W2-F
panel content in those captures is therefore still valid. The fix is to record the capture revision per pair (or per
phase) in `evidence.json`, or to state the split in the packet.

## The 14 findings, checked against code and tests

| Finding | Code verified | Proof run |
| --- | --- | --- |
| H1 | `cold_site_reads.py::_capabilities`: cooling is CONTRADICTORY (chain result or step) / LIMITED (selected chain) / UNAVAILABLE. Product is CONTRADICTORY / UNAVAILABLE, never SUPPORTED. The exact q1 cooling and product limitations are on non-contradictory states. `PROVED_LEVELS` and the SUPPORTED cooling text are removed. `selected_excursion_present` (S5) is `False` when nothing is selected. UI: Evidence shows roles, then the limitation, then `Required basis: ...`. Cooling/exposure never fall back to `Nothing required`. The Overview chip has no Supported. | `test_w2f_recovery_and_exposure_capability_vectors` (apparent complete chain -> LIMITED; no chain; contradictions; no selection) and `..._truth_across_selected_reads[excursion,normal]` (replay; same revision IDs/window/`known_at` across Overview/Evidence/Backup). Superseded S3 assertions updated. Frontend `w2f_recovery_and_exposure_copy`, `w2f_stock_prompt_follows_selected_excursion`, `w2f_backup_recovery_parity`. |
| M2 | Cold and EV `needed()`: readiness messages first, deduped, then `Commissioning record` while `evidence_ids` is empty. `Nothing further recorded` appears only on a configured row. | `w2f_unconfirmed_needs_commissioning` (cold and EV) |
| M3 | `RequestedWindowBar` (N7: invalid window gives no date line), `RefusedStrip`, and 5 Overview / 4 Financials `Not assessed` tiles. Evidence has a strip and no tiles. The refused footer uses the q1 literal with no link. The null-target sentence is separate. | `w2f_refused_frames_and_footer` (valid refusal, malformed and 422 windows, footer W1 scans) |
| M4 | The heading is `Claim boundary`, in slot 3, with its id retained. The `temperature:3` override is removed. There is exactly one gloss. | `w2f_temperature_claim_boundary_title` x3; `w1Vocabulary` `w2f_q1` |
| M5 | Cold count = displayed exposures + start row. Findings refused gives a context line outside the table. EV `bridgeRows` excludes the `none` placeholder. Refused shows `Not assessed` or no count, never zero. | `w2f_consequence_chip_equals_bridge_rows` (cold and EV) |
| M6 | `degreeMinutes()`. Temperature and Finding say `Observed excursion estimate`. Overview and Financials say `Consequence basis`. The Financials disclosure carries the two S7/M6 sentences. Tile and bridge read `Chamber thermal exposure` (S7). | `w2f_temperature_bound_is_labelled`, `w2f_consequence_bound_is_labelled` |
| M7 | One `coldAssumptionRows()` serves both panels: three rows in mock order, no multiplication. | `w2f_assumption_rows_match` |
| M8 | `evSiteRoutes.sld` = `siteFoundationViewHref(.., "sld", at)`. Selected uses `o.window.to`. Refused/UNKNOWN uses the requested `to`. No `to` gives `No linked page for this item`. The cutoff-loss label is shown. | `w2f_overview_sld_link_is_real` (includes navigation) |
| M9 | `overviewStatusWord` / `overviewConfidenceWord` follow the S9 priority. The interrupted vector selects BOUNDED -> Limited, and OBSERVED -> Bounded. The provenance badge is kept. | `w2f_overview_status_confidence` |
| M10 | `REC {uuid}` in cold Analysis, EV timeline, EV Analysis and EV Finding. `F {uuid}`. `SES {external or uuid}`. The full UUID is in `aria-label`. Cells wrap through CSS (`.cold-site-clip` replaced). | `w2f_analysis_record_ids_distinct`, `w2f_finding_record_ids_distinct`, `w2f_timeline_analysis_ids_distinct` |
| M11 | One `missingBasis()` serves the table and the request details, with S10 precedence. `No required role missing` is gone. | `w2f_limited_rows_name_missing_basis` |
| M12 | One literal `<UnavailableTab label="Scenarios" />` in the financial branch of `Subtabs`. `$expectedTabs` has two Scenarios, and the S11 multiset matches exactly. The new rail fixture drops that literal and expects a failure. `Set-ModuleLines` throws if the pattern is missing, so the fixture is non-vacuous. | `w2f_ev_scenarios_slot_unavailable`; `check-architecture` (rail fixtures) and navigation-truthfulness passed |
| M13 | Cold: `Confidence: {claimWord}` + `Selected source: ...`. EV: selected lifecycle, the `Confidence` mapping (no Limited), a separate `Observed interruption` phrase and a pending notice. The EV refused strip shows Unknown / Confidence: Unknown. Cold refused: see L1. | `w2f_finding_strip_confidence`, `w2f_finding_strip_lifecycle_confidence` |
| M14 | `${label(undefined, 0)} · Not declared` uses the slot index (`Charger ${slot+1}`). No CHG-002 is invented. | `w2f_undeclared_charger_slot_keeps_name` |

I checked the builder readings flagged for review:
- 3.4 (commissioning on every unconfirmed row) matches M2's "every unconfirmed row".
- 4.1 (`none` placeholder not counted) is consistent with M5 `empty→0 rows/0 lines`.
- 4.3 (FAULT_ASSOCIATION always gives the diagnostics text) holds because no W2 role carries diagnostics or the vehicle request.
- 5.2 (interrupted Overview shows Bounded because the selected level is OBSERVED) follows S9 exactly.

The 8 title differences are the data-derived gateway codes and SLD names. I confirmed them in `evidence.json`.

## Mock comparison (viewed)

I viewed these app/mock pairs:
- `cold-evidence` stocked at 1440: 4 rows, 5 columns, 3 panels, footer.
- `cold-financials` stocked at 1440, and refused at 390: strip, 4 tiles, 3 panel gaps, subtabs Overview, Assumptions,
  then `Scenarios · Not available yet`.
- `ev-financials` interrupted at 1440: 3 lines and 3 rows; the Scenarios slot is in the mock's position.
- `ev-assumptions` interrupted at 390.
- `ev` interrupted at 1440: the status and confidence chips are first in the strip; the SLD link and label are in the
  Charging activity panel.
- `ev-evidence` interrupted at 1440.

Panel set, order and prominence match the mock. From `evidence.json` I recomputed: 72 pairs, 0 panel-count mismatches,
8 title differences (all data-derived), 0 horizontal overflow, 0 clipped cells.

## Scope

The code diff touches only the spec-named seams:
- `cold_site_reads.py` and its test;
- the cold/EV view files the spec names;
- `evSiteRoutes.tsx` (B2);
- `coldFormat.ts` and `coldSiteClient.ts`;
- three CSS files (N1);
- `productVocabulary.json` (q1) and `v69PanelTitles.ts` (N0);
- the guard and rail fixture (N4/S11).

There is no migration, route, manifest or DTO change beyond `selected_excursion_present` (S5, authorized). I found no
implementer design decision outside the recorded readings.

## Checks I ran (worktree, head `626e0171`)

- Backend:
  - `pytest backend/tests/test_w204_cold_reads.py`: 21 passed (121 s), on a private `assetops_w2frev_test` base DB
    that I created and then dropped.
  - Adjacent `test_w302_evidence_api.py` and `test_w204_cold_consequence.py`: 54 passed. These cover the estate
    evidence projection that reads the cold capabilities.
  - The worktree's `.venv` resolves packages to the main checkout. I set `PYTHONPATH` to the worktree's `backend`,
    `contracts`, `simulator`, `gateway` and root.
- Frontend:
  - `npx.cmd vitest run --minWorkers=1 --maxWorkers=2` on coldSiteViews, coldRoutes, coldFoundation, evFoundation,
    evAssessmentRoutes, evSiteMoneyRoutes and w1Vocabulary: 7 files, 216 passed.
  - `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-all.ps1`: all 11 guards passed (architecture including the rail fixtures, navigation truthfulness,
  agent workflow, registry, screen ledger, ...).

## Not verified by me

- **Full backend suite.** It runs separately, and the packet records it as not yet run at the final revision. Merge
  readiness also depends on that same-revision run.
- **Full frontend suite and production build.** I did not rerun them. The packet reports 105 files / 2504 passed and
  a build exit 0 at `fe3915ad`.
- **Layout captures.** I did not rerun them (Chrome/dev server). I reviewed the committed captures and `evidence.json`.

## Residual risk not named in the packet

- EV Sessions still shows shortened IDs: `Record ${short(id)}` in the excluded-records disclosure
  (`EvAssessmentViews.tsx:352`) and `ShortId` for session codes (`:299`). This is the same prefix-collision class as
  M10. It was outside M10's ruled scope and existed before this slice. Consider it for the W1-conclusion UI pass.
- The EV Evidence footer still reads `Record-level detail and each claim limit are in Evidence › Analysis.` The q1
  ruling covered only the cold footer. This copy existed before the slice and was not touched here.
