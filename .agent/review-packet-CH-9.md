# Review packet: CH-9 measured daylight (DRAFT, builder 6; open items marked OPEN)

Branch `task/CH-9-measured-daylight`. Sheet `AssetOpsV1-plan2\.agent\build-sheet-CH-9.md` §9 (OWN-1104), §10 (CH9-R2),
§11 (CH9-R3). `main` (`fd03ae6b0`, CH-5a2b) merged at `c37fe981b` (clean). Size 4.5 units (CH9-R3).

## Outcome delivered
- Renewable work and the opportunity study read Kobo's **measured daylight hours** over the declared operating day
  (0046 `mini_renewable_hour`; `daylight_hours`/`DaylightHours.study_hours`), not the 12:00 hour. A Site with no
  `pv_available_power` binding keeps the noon hour (unchanged).
- Study model `mini-opportunity/2` (per-hour pins, day fold, `window_hours`, `hours[]`); `/1` stays readable.
- Day measures `daylight_headroom_kw` (replaces `noon_headroom_kw`, period operating_hours) and `critical_served`
  (u3; MG-5 "{kwh} kWh not served over the whole day" / PARTIAL copy).
- Value line "{lo}–{hi} kW over {h} daylight hours on every eligible day" (server `VALUE_LINE`).
- Portfolio opportunity card unit (CH9-R3 Q2): "kW over {window_hours} daylight hours" from the server's
  `study.window_hours`, else the one constant `OPPORTUNITY_HEADROOM_UNIT` "kW over daylight hours"
  (`EstatePortfolio.tsx` `opportunityHeadroomUnit`), MOCK DEVIATION candidate (v69 "kW at midday").
- u4 story-day kind `mill-midday` (`backend/conversions/demo-story-days-v1.json`) with an L2 resolve/validate test.

## Architect rulings (CH9-R3, §11) as applied
- **u5 Action: deferred to CH-9b R0 "Actions from an opportunity" (Known Deviation KD-1).** No stub built.
- **Q2 Portfolio label:** fixed here (above); test change owned (`estatePortfolio.test.tsx`).
- **Q3 `kobo-daytime` v2:** confirmed as the only registered version; a fact, not a deviation.
- **Q4 SCENARIO_BASIS_MISMATCH:** not demo-visible on today's data (below). No copy change, no pin re-cut.

## SCENARIO_BASIS_MISMATCH demo visibility (CH9-R3 Q4)
- Emitted only at `mini_decisions/opportunities.py:369-385`: when a study has a visible scenario link (`links`) and
  the newest one is incompatible (`_compatible`). With no link it cannot occur.
- Today's data (read-only queries): `mini_scenario` 0 rows and `mini_opportunity_scenario_link` 0 rows on
  `assetops_polish_full_test` (polish; 4 studies) and on `assetops_mechanism_test` (MD-0; 3 studies). No demo
  producer creates scenarios or links (only `tools/w403_mini_decisions_walkthrough.py`, a walkthrough tool).
- Rendering: `frontend/src/sites/MiniOpportunity.tsx` never renders `limitations` codes; an incompatible link gives
  `scenario_id: null`, so the cards say "No what-if linked" / "No what-if for a new use" (plain, existing copy).
  The Portfolio card (`EstatePortfolio.tsx`) and the Opportunities index (`findingIndex.tsx`, server `value_line`)
  read no scenario fields. Estate `financials.py:208` limitation text is Finding consequence, not opportunity.
- Surface list: none on today's data. If a Kobo what-if enters the demo script it goes back to the Architect (DS-1).

## Owned test changes (no assertion weakened)
- `test_w402_reads_postgres.py` `_dark_hours` (builder 3): 0 kW means for the other operating hours.
- `test_w403_scenarios_postgres.py` `mg_published` seeds `_dark_hours`; `test_u2c_row_gate...` keys `by_day`
  `(local_day, window_start)` and gives each fake revision its `window_start` (`08a5c0988`).
- `test_w403_opportunity_read_postgres.py`: OBJECT/DAY keys + `/2` shape (builder 5); `pv_reading()` ingests 5 Oct's
  24 hourly pv means late (noon positive, others 0 kW) at the DB clock before the renewable enqueue, which 0046
  requires; received now so the earlier `k_clean` cutoff never sees it (`2064fcb7b`).
- `test_ch1a_snapshot_postgres.py`: `required_seconds` 24*3600 (operating day), was 3600 (`a830b2d0c`).
- `test_ch5a2_contract.py` goldens `site_kobo_2026-10-31/11-01.json`: + `critical_served: COMPLETE` in the day
  measures after merging CH-5a2b; grades unchanged (`a8f115f84`).
- `estatePortfolio.test.tsx:435-436` unit text + a no-`window_hours` fallback case (`5761ba30a`).
- Earlier builders: worker/scenarios `/2` (`d4b26a299`), read shape (`4a2db4a80`, `f669eb067`), `test_md0_fixture`
  (busy window label), ch1a/ch1b/ch5a1/md0/ch5a2 literal renames, `test_out_d4_board.py` MG-5, `test_ch1b_register`.

## Checks run (builder 6, on `c37fe981b`+)
- Postgres (`tools/run-host-tests.ps1`, port 55432): `test_w403_opportunity_read` + `test_ch4_opportunity` 13 passed
  (982 s); `test_w403_scenarios` 10/10 (9 + fixed 1); `test_w402_reads` 7 passed (467 s); `test_ch1a_snapshot` +
  `test_ch9_daylight` 10/10 (9 + fixed 1); `test_ch1b_fix` + `test_w403_migration` 18 passed (158 s);
  `test_ch5a2_chain_api` + `test_out_b4_board` 11 passed (223 s). Builder 5: worker file 5/5.
- Unit after merge: ch5a2b_claims, ch5a2_contract (after regen 24), ch9_measures, ch9_no_noon_literal, out_d4_board,
  ch1b_register, ch5a1_board_contract, md0_fixture, chain_coherence tests, event_register: 295 passed.
- Frontend: `tsc --noEmit` 0 errors; vitest `estatePortfolio.test.tsx` 58 passed.
- MD-0: `status` usable false (both). `build --variant states --budget 540`: 3 parts (exit 3, 3, 0), seed 1087 s,
  `tpl_ca277a2e` (drain_mini 300 s). `ensure` auto selects close (reasons: `backend/tests/mechanism_dataset.py`,
  `config/chain/thread-lifecycle-v1.json`, `mechanism-v1.json variants.close`). `build --variant close`: 3 parts,
  seed 1281 s, `tplc_ca277a2e` (drain_mini 402 s). derive 52 s / 64 s.
- L3m states: collect 65 x 200; check `--threads var/mechanism/expected-threads.json --expect expected-mechanism.json
  --variant states`: every COH 0, 0 new, COH-17 0, self-check 0/0.
- L3m close: collect 77 x 200; COH-6 4/4 expected (MD0b-R:A2), every other rule 0, COH-17 0, self-check 4 pass.
- Guards: architecture PASS, agent-workflow PASS, mock-deviation labels (V) OK 153 files.
- Not run (owner rule): full suite, demo prepare, `test_demo_combined_postgres`, L2m `test_md0_mechanism_postgres`.

## OPEN for the next builder
- Polish clone re-collect after the CH-5a2b merge: `chain_clone.py create ch9 --migrate`, backfill a-d, settle,
  collect, check against `expected-today.json` (COH-17 = 0); owned `expected-today.json` changes (8 h Kobo days now
  missing study days, MG-5 PARTIAL; DD-1).
- Per-window table of named days, day counts and why each day is not complete (CH5a2b-R2); old -> new
  `count_basis` list; every MD-0 value old -> new (needs an A collect from main on the same inputs).
- Mini-depth job growth vs the CH-1b stage bound (polish settle tick).
- `check-all.ps1 -Python <plan2 venv>`.

## Known deviations
- **KD-1 u5 deferred (CH9-R3 Q1).** No Kobo `action` can attach to the opportunity-only headroom thread
  (`action.origin_finding_id` NOT NULL FK, `0016_action_store.py:55,74-76`; thread link by Finding). CH-9b R0 adds
  opportunity-origin Actions. The board and opportunity page render "no action" for the headroom thread.
- **KD-2 no prepare (owner rule).** `mill-midday` is proved by the L2 test only; the 12 h interval acceptance by
  the `kobo-daytime` model on a real prepare is unproven (end-game E3).
- **KD-3 covered dark day.** A day with no daylight and no missing hour keeps one missing noon head, so it reads as a
  missing study day and `daylight_headroom_kw` NO_DATA.
- **KD-4 scenario pins.** A one-pin-a-day scenario is incompatible with a `/2` study day of several hours
  (SCENARIO_BASIS_MISMATCH); the multi-hour pin contract is post-demo (CH9-R3 Q4).

## Residual risk
- Kobo board and chain reads take ~9.3-9.9 s on the MD-0 L3m DB (`read.mini_depth` 4 calls ~5.5-6.0 s,
  `read.action_facts` ~3.3 s); not compared with a main baseline yet.
- Lane-1 conflicts in `chain/vocabulary.py`, `site_outcomes/mini.py`: resolved by the merge (clean).

## User-review focus
- Portfolio unit copy "kW over N daylight hours" (vs v69 "kW at midday"); "1 daylight hours" matches the server line.
- USER_REVIEW_REQUIRED: per the task file; W1-style walkthrough is deferred (owner rule).
