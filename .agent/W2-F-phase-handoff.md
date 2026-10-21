# W2-F phase handoff

Branch `task/W2-F-structural-fixes` (from main `7cfcb751`). W4-03 merges before W2-F; `navigation-truthfulness.ps1`
and the unavailable-tab multiset are untouched (unit 4, after W4-03 is on main).

## 1a: cold backend truth (H1), commit `8028d57d`

Landed (`backend/assetops_backend/analytics/cold_site_reads.py`):
- `COOLING_TEXT` (~:77): `LIMITED` = `Cooling recovery is not established by the selected start chain.`; no `SUPPORTED`
  key (S2). New `COOLING_LIMITATION`, `PRODUCT_LIMITATION` (:84-86), exact S1 text.
- `_capabilities` (`chain_contradictory`, ~:462): cooling CONTRADICTORY / LIMITED (selected chain) / UNAVAILABLE (no
  chain); product CONTRADICTORY (selected excursion assessment state) / else UNAVAILABLE. `PROVED_LEVELS` removed
  (unused). Claim limitation set at ~:483.
- `evidence()` (~:411-417): `selected_excursion_present` (S5) = `bool(exc.result.excursions)`; `false` with no
  selection or no selected excursion analytic. Frontend type/consumer is unit 1b.

Tests (`backend/tests/test_w204_cold_reads.py`): `test_run5_exact_copy` pins new copy; S3 supersessions in
`test_capability_needs_qualifying_points`; no-selection flag in `test_missing_probe_and_empty_window`; new
`test_w2f_recovery_and_exposure_capability_vectors` (pure, `_capabilities(None, snap)`) and
`test_w2f_recovery_and_exposure_truth_across_selected_reads[excursion|normal]` (replay; same revision IDs, window,
`known_at` across Overview/Evidence/Backup).

Checks: `test_w204_cold_reads.py` 21 passed (Postgres `w2fa_test`, since dropped). Non-vacuous: cooling predicate
set back to `SUPPORTED` fails the vector test; reverted via `git checkout`. `check-all.ps1`: all 11 guards passed.

Readings (no ruling requested; flag if wrong):
1. "selected chain/step is CONTRADICTORY" = any selected chain result or any chain step CONTRADICTORY (W2-03 only
   ever marks `START_RESULT`; previously only a COMPRESSOR step counted).
2. Claim limitation is carried on every non-CONTRADICTORY state of the two claims (LIMITED and UNAVAILABLE), so 1b
   never needs the `Nothing required for this claim` fallback; CONTRADICTORY keeps the analytic limitations.
3. Product CONTRADICTORY keeps the existing predicate (selected excursion assessment `state == CONTRADICTORY`).
4. S5's flag is built here because S5 assigns it to unit 1a, though the 1a read index omits S5.
5. Cooling SUPPORTED text removed from `COOLING_TEXT` rather than kept unreachable.

Open for 1b: type and consume `selected_excursion_present`; all frontend copy (Overview `Recovery comparison not
assessed`, Evidence missing column, Financials rename). Frontend mocks still carry old cooling copy.

## 1b: cold truth UI (H1 S1/S2/S5/S7/S8/S12, N0/M4, M6, M7/N6, cold M13), commit `f3ccb41c`

Landed:
- `coldSiteClient.ts`: `ColdEvidenceRead.selected_excursion_present: boolean` (S5).
- `coldSiteViews.tsx`: Evidence `What is missing` for cooling/exposure = missing roles, then capability `limitation`,
  never `Nothing required` (S1); exposure appends `Required basis: ...` (`PRODUCT_REQUIRED_BASIS`). Stock prompt and
  `Next evidence not identified` keyed to `selected_excursion_present` (`excursionPresent`). Overview cooling chip has
  no SUPPORTED mapping (S2); money card adds `data-cold-money-basis` `Consequence basis: ...` (S8). Financials tile and
  basis label `Chamber thermal exposure`, row th `Chamber thermal exposure · Consequence basis: ...`, basis note
  `data-cold-thermal-basis-note` (S7/S8). `coldAssumptionRows` shared by Financials and Assumptions (M7/N6).
- `coldFormat.ts::degreeMinutes` (open upper -> `upper bound not established`; null -> `Not assessed`).
- `ColdAssessmentViews.tsx`: panel 3 `Claim boundary` (N0); Temperature exposure card and excursion Finding labelled
  `Observed excursion estimate` (S8); `FindingStatus` = lifecycle, `Confidence: {claimWord}`, `Selected source: ...`.
- `v69PanelTitles.ts`: `temperature:3` override and deviation-18 comment removed.
Tests: `coldRoutes.test.tsx` `w2f_temperature_claim_boundary_title` (loaded/none/refused), `w2f_temperature_bound_is_labelled`,
`w2f_finding_strip_confidence`, `w2f_backup_recovery_parity`; `coldSiteViews.test.tsx` `w2f_recovery_and_exposure_copy`,
`w2f_stock_prompt_follows_selected_excursion`, `w2f_consequence_bound_is_labelled`, `w2f_assumption_rows_match`.
Checks: cold files 50 + 51 passed; tsc clean; full frontend 2420/2421 - one failure in untouched
`s404SiteFindingIndex.test.tsx` ("changing the dates", got 2026-10-25), passes 37/37 alone (load flake);
check-all 11/11. Non-vacuous: S5 prompt reverted to the capability predicate fails `w2f_stock_prompt...`; reverted.

Readings (flag if wrong):
1. **Vocabulary glosses added** (`productVocabulary.json` top-level `glosses`): exact `Claim boundary` and exact
   `Ordered compressor running after the interruption`. Both mandated texts hit T028 terms `claim`/`running`; glosses
   are exact-phrase, so the words stay flagged elsewhere. Reviewer should confirm this is acceptable vs a ruling.
2. Contradictory cooling with no limitation shows `Coverage or claim basis incomplete`.
3. Currency label comes from the unit-value item's `currency` (else any item's); `No assumption in use` note only when
   all three rows are `Not declared`.
4. Temperature card value is the bound; its note carries `Observed excursion estimate`.
5. Cold Finding refused state unchanged (existing page refusal; no strip), since S12's neutral refused strip is EV.

## 2: cold frame and counts (M3, cold M5/M10; N1, N7, N9), commit `672671d4`

Landed (`frontend/src/sites/coldSiteViews.tsx`):
- `RequestedWindowBar`, `RefusedStrip`, `RefusedTiles`, `WINDOW_CANNOT_BE_READ` (above `stateSentence`). Refused
  Overview/Evidence/Financials: requested date line (none for 422 or unparseable dates; cutoff only when requested),
  `Window cannot be read` strip, `Not assessed` tiles (Overview 5, Financials 4 + chip `Not assessed`, Evidence none).
- Evidence footer (`data-cold-evidence-footer` refused/no-link/link): `...cannot be read for this window.`; null
  Analysis target -> `...are on Evidence › Analysis. No linked page for this item.`
- Financials: `count = exposures + start row` (`data-cold-line-count`), strip adds `Displayed rows include unpriced
  context`; Findings unread -> `data-cold-start-context="unread"` paragraph after the table.
- Analysis Record cell: `REC {full UUID}` in `code.cold-site-id` (aria-label = exact UUID); `Open record` link gets
  aria-label `Open record REC {UUID}`. CSS `.cold-site-clip` replaced by wrapping `.cold-site-id`.
Tests (`coldSiteViews.test.tsx`): new `w2f_refused_frames_and_footer`, `w2f_consequence_chip_equals_bridge_rows`,
`w2f_analysis_record_ids_distinct`; superseded `1 consequence line` -> 2 and `Record {id}` -> `REC {id}`; `Reads`
gains optional `findings` override.
Checks: cold files 104/104; tsc clean; full frontend 98 files / 2424 passed; check-all 11/11. Non-vacuous: count
reverted to `f.consequences.length` fails the chip test; reverted via `git checkout`.

Readings (flag if wrong):
1. M3 applied to Overview/Evidence/Financials only (ledger scope); Analysis/Assumptions refusal frames unchanged.
2. `Window cannot be read` is used for every refusal kind (403/404/503/422), per the literal closure text.
3. Refused date line keeps the `Selected window` label; cutoff span omitted when no `known_at` was requested.
4. 390 proof is jsdom content + stylesheet rule; rendered 390 capture is unit 5.
5. Refused footer contains W1 term `claim limits`; recorded under pending 1b-q1, no exemption added.

## 3: EV configuration and Overview (M2, M8, M9, M14, EV Overview M10; B2, S9, N3, N8), commit `d0f8abd9`

Landed:
- `ColdFoundationViews.tsx` / `EvFoundationViews.tsx` `needed(items, configured)`: readiness messages first (deduped),
  then `Commissioning record` while `commissioning.evidence_ids` is empty; empty list -> `Nothing further recorded` for a
  configured row, else `—`. Constants `COMMISSIONING_RECORD`, `NOTHING_FURTHER_RECORDED` (exported from cold).
- `EvFoundationViews.tsx::ChargerRow` empty slot: Part `Charger {slot+1} · Not declared` via existing `label` (N8).
- `evSiteRoutes.tsx`: `sld: (at) => siteFoundationViewHref(siteId, "sld", at)`; `EvSiteRoutes.sld` typed in `EvSiteViews.tsx`.
- `EvSiteViews.tsx`: `overviewStatusWord` / `overviewConfidenceWord` (S9) as first two strip chips; refused Overview
  renders a strip with `Unknown` / `Confidence: Unknown`. SLD link `data-ev-sld-link` at selected `o.window.to`
  (requested `p.window.to` when refused or currentness `UNKNOWN`; no `to` -> `No linked page for this item`) with
  `SLD_CUTOFF_NOTE`. Timeline record label `REC {full UUID}` in `code.ev-site-id` (CSS wraps).
Tests: `evFoundation.test.tsx` `w2f_unconfirmed_needs_commissioning`, `w2f_undeclared_charger_slot_keeps_name` (+2
superseded `Not declared` slot assertions); `coldFoundation.test.tsx` `w2f_unconfirmed_needs_commissioning`;
`evSiteMoneyRoutes.test.tsx` `w2f_overview_sld_link_is_real` (incl. click to SLD), `w2f_overview_status_confidence`,
`w2f_timeline_analysis_ids_distinct` (timeline part; EV Analysis/Finding IDs are unit 4); superseded `:593`/`:603`.
Checks: focused 3 files 63/63; tsc clean; full frontend 98 files / 2430 passed; check-all 11/11. Non-vacuous: dropping
the commissioning append and mapping BOUNDED -> Bounded fail the two named tests; reverted via `git checkout`.

Readings (flag if wrong):
1. SLD href is built in the shell (`routes.sld`) because the site-substrate guard forbids `sites/` importing `shell/`;
   it calls `siteFoundationViewHref(siteId, "sld", at)` exactly as B2 names.
2. "No selected version" = Overview `currentness.state === "UNKNOWN"`.
3. Refused Overview strip has no window line or action (only the two Unknown chips).
4. `Commissioning record` is appended to every unconfirmed row, including the optional cold manual-log row; a
   confirmed but unconfigured row with no message keeps `—`.
5. New copy passes the vocabulary guard; nothing added to 1b-q1. EV Evidence `Record {short}` (~:1050) is unit 4.

Next: 4

## 4a: copy ruling q1, commit `83971293`

`cold_site_reads.py::COOLING_LIMITATION` = ruled sentence (`We cannot confirm that the compressor switched on ...`);
`productVocabulary.json` keeps only the exact `Claim boundary` gloss (ruled `why`); `Ordered compressor...` gloss gone.
Evidence footer (`coldSiteViews.tsx`, `data-cold-evidence-footer`): `how each limit is set` in refused/loaded/no-link;
null target is its own `data-cold-evidence-footer-target="none"` span. `LEDGER_CLAIM` exemption for the old footer
removed. Tests: `w1Vocabulary.test.tsx::w2f_q1`, heading scan in `w2f_temperature_claim_boundary_title`, footer scans in
`w2f_refused_frames_and_footer`, `Q1_COOLING_LIMITATION` literal in `test_w204_cold_reads.py` (21 passed, `w2fd_test`,
dropped). 1b-q1 marked RESOLVED.

## 4: EV evidence, money and Finding (M5, M10, M11, M13; S10, S12, N1), commit `fbb197db`

Landed:
- `EvSiteViews.tsx::FinancialsScreen`: `bridgeRows` model (scenario | interruption | repair); chip `data-ev-line-count`
  = `bridgeRows.length`; strip adds `Displayed rows include unpriced context`. `missingBasis(cap)` + `NOTHING_REQUIRED`
  (exported, above `contactDetail`) used by the Evidence table (`data-ev-missing-basis`) and request details
  (`data-ev-request-basis`). Analysis Record cell `code.ev-site-id` `REC {UUID}`; unused `short` removed.
- `EvAssessmentViews.tsx`: `SessionId` (`SES {external | UUID}`), Finding strip `F {UUID}`, record line `REC {UUID}`
  (`code.ev-id`, CSS in `w2-ev-assessment.css`); `EV_FINDING_CONFIDENCE`; strip = lifecycleWord + `Confidence: ...` +
  separate `Observed interruption` (SUPPORTED only) + pending notice; refused strip `Unknown` / `Confidence: Unknown`.
Tests: `evSiteMoneyRoutes.test.tsx` `w2f_consequence_chip_equals_bridge_rows`, `w2f_limited_rows_name_missing_basis`,
`w2f_timeline_analysis_ids_distinct` (+ Analysis); `evAssessmentRoutes.test.tsx` `w2f_finding_record_ids_distinct`,
`w2f_finding_strip_lifecycle_confidence`; superseded: pending strip, `Finding/Record {8 chars}`, pending `0 lines`->1.
Checks: EV files 47/47; tsc clean; full frontend 98 files / 2435 passed; check-all 11/11. Non-vacuous: old count and
removed fault rule fail the two new money tests; reverted via `git checkout`.

NOT built: M12/S11/N4 (EV Scenarios tab + guard + rail fixture) - held for W4-03, pending `4-q1`.

Readings (flag if wrong):
1. The `none` placeholder row (no consequence) is not counted; a withheld/unpriced scenario row is counted.
2. EV refused Financials keeps no strip, so no count (not a zero) is shown; no new refused frame added (M3 is cold).
3. `FAULT_ASSOCIATION` always takes `Charger diagnostics and vehicle request not recorded` after contradiction/roles,
   since no W2 role carries diagnostics or a vehicle request; non-Full with no limitation shows exact selected coverage;
   no capability -> `Not assessed`.
4. Sessions list and excluded-records lines (W2-06 Sessions screen) keep their short IDs; M10 scope lists only EV
   overview timeline, Analysis and Finding.

Next: 5

## 5: integration (captures, re-audit, packet), commit `a869805f`

Landed (no feature behavior): `.agent/W2-F-evidence/` (`seed.py`, `capture.mjs`, `evidence.json`, 116 PNGs; 72 pairs,
22 screens, 1440/390; cold excursion stocked/no-selection/refused, cold normal, EV interrupted/refused) and
`.agent/W2-F-review-packet.md` (all builder readings, 14-finding re-audit: 13 closed, M12 open). Private DB `w2fe_test`
re-created per phase and dropped. Panel set/order equal on all 72 pairs; 8 title differences are data-derived names.
Checks at `4d4fa252` code: frontend 98 files / 2435 passed; tsc 0; build 0; check-all 11/11.
4-q1 RESOLVED: M12 (EV Scenarios tab, guard `$expectedTabs`, rail fixture, `w2f_ev_scenarios_slot_unavailable`) lands as
unit 4b AFTER W4-03 merges. The EV Financials (and Assumptions) captures are re-taken after 4b
(`node .agent/W2-F-evidence/capture.mjs <out> <rev> ev finding=<uuid>` after `seed.py ev interrupted`).
Full backend suite deferred to the final post-4b revision (same-revision rule).

Next: 4b (M12) after W4-03 merges, then final review