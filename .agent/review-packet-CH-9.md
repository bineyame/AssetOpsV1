# Review packet: CH-9 measured daylight (builder 7; BLOCKING finding F1 for the Architect)

Branch `task/CH-9-measured-daylight`. Sheet `AssetOpsV1-plan2\.agent\build-sheet-CH-9.md` §9 (OWN-1104), §10 (CH9-R2),
§11 (CH9-R3). `main` (`fd03ae6b0`, CH-5a2b) merged at `c37fe981b` (clean). Size 4.5 units (CH9-R3).

## Outcome delivered
- Renewable work and the opportunity study read Kobo's **measured daylight hours** over the declared operating day
  (0046 `mini_renewable_hour`; `daylight_hours`/`DaylightHours.study_hours`), not the 12:00 hour. A Site with no
  `pv_available_power` binding keeps the noon hour (unchanged).
- Study model `mini-opportunity/2` (per-hour pins, day fold, `window_hours`, `hours[]`); `/1` stays readable.
- Day measures `daylight_headroom_kw` (replaces `noon_headroom_kw`, period operating_hours) and `critical_served`
  (u3; MG-5 "{kwh} kWh not served over the whole day" / PARTIAL copy).
- Value line "{lo}–{hi} kW over {h} on every eligible day", `{h}` = "1 daylight hour" / "N daylight hours"
  (server `vocabulary.daylight_hours_text`; the Portfolio unit "kW over 1 daylight hour" likewise, `54431f5dd`).
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

## Findings (builder 7; reported, not adapted)
- **F1 (High, blocks merge; Architect). `critical_served` is NO_DATA on every Kobo day of every dataset, so every
  Kobo day grade drops to NO_DATA.**
  - Cause, read from the stored heads: the adapter (`chain/measure_impls.py` `CriticalServed.inputs`) counts an
    hour only when the hour's `cards.unserved_kwh` is stated. `mini_depth/rules.py:607` states it only when *every*
    load row is SUPPORTED, and the UNCLASSIFIED load never has request evidence.
  - So no stored `service` head on the polish clone (165) or on MD-0 states (332) states `unserved_kwh`, although
    the CRITICAL row is SUPPORTED on 64 (polish) and 249 (MD-0) hours. The stored rows carry no per-row
    `unserved_kwh` (`mini_depth/projection.py` `_service`), so the critical-only demand cannot be read from the
    heads (Q7, "no new reading query") without a `mini-service` model change.
  - This misses the sheet's L2m "`critical_served` COMPLETE on delivered days" and CH5a2b-R2's "every built, non-gap
    MD-0 day grades complete". P8 said "if there is no served/unserved signal, stop"; on real data there is none.
  - The L0/L2 tests pass because their fixtures make every row SUPPORTED. No code was tuned.
  - Options for the Architect: (a) store the CRITICAL row's unserved (`mini-service/2`, re-derive) and read it;
    (b) take critical demand from the critical channels in the adapter (a reading query; reverses Q7); (c) keep
    `critical_served` out of the day grade until (a).
- **F2 (Medium). Two headroom ranges on MD-0 states.** The estate summary row reads "2–20 kW of daytime solar
  unused" / "2–20 kW unused" (was 14–20). The study value line and Portfolio read "2–8 kW over 12 daylight hours on
  every eligible day" (was "14–20 kW at midday on every eligible day"). The summary row takes the per-hour range over
  the daylight hours, and the study takes `headroom_on_every_eligible_day`. It is the same opportunity with two
  numbers on screen, and COH does not judge it.
- **F3 (Medium, perf).** CH-9 makes the Kobo board ~0.5 s slower (see Perf).

## Polish clone L3 (after the CH-5a2b merge)
- `assetops_chainclone_ch9_test`: create --migrate (0046), backfill a 179 / b 9 / c 3 / d 6, settle (S2 permitted,
  tick COMPLETED in 68 s, performance permitted). Collect B: 85 x 200, `PGOPTIONS` read-only, `--work` the scratch
  copy `polish_work_ch9`.
- Check `--expect expected-today.json`: COH-2 2/2 and COH-7 8/8 expected, **COH-17 0, every other rule 0, 0 new**,
  self-check 10 pass. **No `expected-today.json` change was needed.**
- **Mini-depth job growth against the CH-1b stage bound.**
  - The tick's MINI stage processed 0, deferred 0 and failed 0, against the 10-job / 120 s bound
    (`TickLimits.mini_jobs_per_site`, `mini_seconds`). Mini job rows are unchanged (renewable 10, service 165,
    fuel 165, backup 170).
  - The clone ingests no new reading, so 0046's per-daylight-hour enqueue is not exercised here: polish's jobs were
    enqueued when it was built.
  - OPPORTUNITY processed +2 jobs (the `/2` re-projection; main processed 0). The tick took 68 s on both the main
    and the branch clones, against the 240 s tick bound.
- **A side.** Main code is `fd03ae6b0`; its code dirs are identical to CH-5a2b `3122c2d1d`.
  - Polish A is the CH-5a2b review collect `rv5a2b_bundle`: a fresh clone of the same source, settled by that code.
  - MD-0 A is CH-5a2b's `l3m-states` / `l3m-close` bundles.
  - B is this slice's `ch9_B`, `mech-bundle` and `mechc-bundle`.
  - For the perf A, a fresh main clone `assetops_chainclone_ch9a_test` was created from a temporary main worktree
    and settled the same way.
  - Both clones were dropped and the worktree was removed.

## CH5a2b-R2 per-window table
Named days are by `window_days`. Day counts are complete/low/partial/no_data.

| Dataset | Window (named days) | A days | B days | Non-complete days and why (B) |
|---|---|---|---|---|
| polish | S 31 Oct (1) | 0/1/1/0 of 2 | 0/1/0/1 of 2 | Kobo 31 Oct NO_DATA (F1; was PARTIAL); Cold/EV LOW as before |
| polish | week 25-31 Oct (7) | 0/3/3/9 of 15 | 0/3/0/12 of 15 | Kobo 7/7 NO_DATA (was 3 PARTIAL, 4 NO_DATA) |
| polish | month 3 Oct-2 Nov (31) | 0/5/8/68 of 81 | 0/5/0/76 of 81 | Kobo 31/31 NO_DATA (was 8 PARTIAL) |
| MD-0 states | S 31 Oct (1) | 1/0/0/0 of 1 | 0/0/0/1 of 1 | 31 Oct built, not a gap: **F1** |
| MD-0 states | week (7) | 4/0/0/3 | 0/0/0/7 | 25 Oct declared gap; 26-27 Oct outside the day set; 28-31 Oct built: **F1** |
| MD-0 states | month (31) | 10/0/0/21 | 0/0/0/31 | 10 built non-gap days (19-23 and 28-31 Oct, 1 Nov): **F1**; GAP-K7; the rest outside the set |
| MD-0 close | S (1) | 1/0/0/0 | 0/0/0/1 | built: **F1** |
| MD-0 close | week (7) | 7/0/0/0 | 0/0/0/7 | all built: **F1** |
| MD-0 close | month (31) | 14/0/0/17 | 0/0/0/31 | 14 built days (19 Oct-1 Nov): **F1**; the rest outside the set |

- Every Kobo day-window body (polish 8, states 10 plus the gap, close 14) goes from PARTIAL or COMPLETE in A to
  NO_DATA in B. On MD-0 the only non-COMPLETE measure is `critical_served` NO_DATA.
- Polish Kobo days also read `daylight_headroom_kw` LOW and `avoidable_gen_min`/`productive_kwh` PARTIAL, as before.
- Polish per-grade totals (month, all Sites): 0 complete, 5 low, 0 partial, 76 no_data.

## `count_basis` old -> new and the screen text it changes
| Dataset | Window | Portfolio `count_basis` A -> B | Claim text A -> B |
|---|---|---|---|
| polish | S / week / month | CHECKED_DAYS -> CHECKED_DAYS | unchanged ("1 open on the days checked" etc.) |
| polish | Kobo day windows 3, 10, 17 and 30 Oct | CHECKED_DAYS -> NOT_KNOWN | all three claims, e.g. "None open on the days checked" (17 Oct "1 open ...") -> "Not known yet" |
| MD-0 states | S | COMPLETE -> NOT_KNOWN | "0 open findings", "1 opportunity", "0 fixes confirmed" -> "Not known yet" (x3) |
| MD-0 states | week / month | CHECKED_DAYS -> NOT_KNOWN | "... on the days checked" -> "Not known yet" (x3 each) |
| MD-0 close | S / week | COMPLETE -> NOT_KNOWN | "1 open finding", "0 opportunities", "0 fixes confirmed" -> "Not known yet" |
| MD-0 close | month | CHECKED_DAYS -> NOT_KNOWN | "... on the days checked" -> "Not known yet" |

Every NOT_KNOWN move comes from F1. The board's finding-gap text also moves: "N of the last 31 days have no checked
readings yet" becomes "31 of the last 31 ..." on every Kobo board and board summary (polish and MD-0).

## MD-0 and polish values old -> new (besides F1)
- **MD-0 states opportunity.**
  - The value line "14–20 kW at midday on every eligible day" becomes "2–8 kW over 12 daylight hours on every
    eligible day".
  - The Portfolio headroom goes 14–20 -> 2–8, and `study.window_hours` 1 -> 12.
  - The summary row "14–20 kW of daytime solar unused" becomes "2–20 kW ..." (F2).
  - The seen line is unchanged ("Seen on 2 of 5 well-observed days · 28 Oct–1 Nov").
- **Day measures.** `noon_headroom_kw` (COMPLETE) is replaced by `daylight_headroom_kw` (COMPLETE on MD-0, LOW on
  polish). `critical_served` is added (NO_DATA, F1).
- **Polish.**
  - The study's `window_hours` goes 1 -> null: 8 h story days are missing study days (CH9-R2 Q2; DD-1).
  - The limit line is unchanged (mixed sources).
  - The estate summary Kobo row at S and week, "25–31 kW of daytime solar unused", becomes "No productive-use sales
    on this day: Grain mill not used". At month the row is gone, along with the missing study days.
- **MD-0 close.** There is no opportunity in A or B.

## Perf: Kobo board `kobo_board_31oct` (`tools/chain_perf_probe.py --runs 5`, ms, medians, polish clones)
| Code / clone | cold run 1 | cold run 2 | warm run 1 | warm run 2 |
|---|---|---|---|---|
| main / main-settled `ch9a` | 4930 | 3992 | 2953 | 2847 |
| CH-9 / branch-settled `ch9` | 4771 | 5459 | 3157 | 3612 |

- Averages: cold ~4460 -> ~5115 (+~650 ms, +15%); warm ~2900 -> ~3385 (+~485 ms, +17%). Run-to-run noise is
  about ±500 ms.
- The ledger names the cause: `read.mini_depth` (4 calls) goes from ~530 ms to ~1050-1160 ms. The renewable page
  now reads every operating hour, plus `daylight_hours` per study day.
- No obvious defect was found, so nothing was fixed here.
- Main code on the branch clone is not a fair A. It skips `money_head` because it finds no settled day under the
  renamed measure.

## Checks run (builder 7, on `54431f5dd`)
- L0 `test_ch4_opportunities.py`: 16 passed. L2 `test_ch4_opportunity_postgres.py -k backfill_places_one_thread`:
  1 passed (33 s). Vitest `estatePortfolio.test.tsx`: 58 passed. `tsc --noEmit`: 0 errors.
- Guards (`check-all.ps1 -Python <plan2 venv>`): **14/14 PASS**, exit 0 (1097 s; estate self-tests 867 s). Includes
  architecture seams, agent workflow, mock-deviation labels and client vocabulary (V), chain coherence (103), event register (12).

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
- Kobo board and chain reads take ~9.3-9.9 s on the MD-0 L3m DB; on polish CH-9 adds ~0.5 s to the board (F3).
- Lane-1 conflicts in `chain/vocabulary.py`, `site_outcomes/mini.py`: resolved by the merge (clean).

## User-review focus
- Portfolio unit copy "kW over N daylight hours" (vs v69 "kW at midday"); "1 daylight hour" in both.
- F1 (every Kobo day NO_DATA, claims "Not known yet") and F2 (two headroom ranges) before any merge.
- USER_REVIEW_REQUIRED: per the task file; W1-style walkthrough is deferred (owner rule).

## Fix round CH9-R4 (builder 8; commits `e568e0354` F1, `c61be3a73` F2, `96f10df3e` L2m; branch NOT yet merged with main)
- **F1.** `mini_depth/projection.py` `_service` stores each row's `unserved_kwh` (null unless SUPPORTED);
  `store.py` `MODEL_VERSIONS["service"] = "mini-service/2"` (others `/1`). Readers of the version: `store.py:215`
  reuse key, `projection.py:214,232`, test `test_w402_projection.py` (updated per domain). `chain/measure_impls.py`
  `CriticalServed` reads only the one CRITICAL row: exactly one, SUPPORTED, `unserved_kwh` stated (a `/1` row has no
  key -> uncovered); served = `delivered_kw` x 1 h, demand = served + unserved, covered = row coverage minus gaps; no
  card read. Migration `0047_mini_service_v2` (on 0046): enqueue only, `mini_enqueue_hour(..,'mini_service',..,NULL,
  now())` for each hour whose selected service head is `/1`; cause NULL = the `mini_enqueue_configuration` convention;
  downgrade no-op. **Numbering: CH-5c merged `0047_chain_response` on 0044 first, so CH-9 must re-point (see handoff).**
- Tests: L0 `test_ch9_measures.py` truth table on the real polish row shape (key case CRITICAL SUPPORTED + UNCLASSIFIED
  UNKNOWN/no request counted; LIMITED, UNKNOWN, two/no CRITICAL, `/1`, unstated -> uncovered; gap -> half hour;
  demand = served + unserved) 7 passed; L0 `test_w402_projection.py` 8 passed (new `/2` row test). L2
  `test_ch9_service_v2_postgres.py` 2 passed (0047 enqueues only the `/1` service hour, NULL cause; drained -> `/2` head;
  `critical_served` COMPLETE over 24 `/2` hours with an unrequested UNCLASSIFIED row, real Postgres reader);
  `test_ch9_daylight_postgres.py` 6 passed (head assertions now 0047). L2m `test_md0_mechanism_postgres.py`
  kobo_grades (now also asserts `critical_served` COMPLETE on every delivered day, NO_DATA/PENDING on GAP-K7) and the F2
  test: passed; `test_w402_mini_stage_postgres.py` 3 passed.
- **F2.** `site_outcomes/mini.py`: new port `MiniPorts.opportunity` = `s.threads.opportunity_threads(t,[sid],lo,hi,
  known_at)` (`read.py`), the Portfolio's CH-4 read, over the board's renewable five days. Grow headline figure, short
  value and `SIGNAL:PRODUCTIVE_USE_HEADROOM` read that study; `renewable.cards.headroom_kw/eligible_days` reads removed
  from `compose`. The "Productive use" contributor keeps the renewable page's own day counts (read inside `_grow`).
  Owned test changes: fake `opportunity` port in `test_out_b2_mini.py` (mirrors the fake cards), fake thread port in
  `test_ch5a1_board_contract.py` (goldens unchanged), study on the `test_ch5a2_contract.py` item and its regenerated
  `estate_week_2026-10-25.json` (+ the item's `study` key only). New L0 `test_walk1_5_solar_window.py`: study 2-8 vs
  per-hour 2-20 -> headline "2–8"; no study -> no headline/signal. 339 L0 passed.
  Renewable page per-hour card label (`MiniPerformance.tsx:593`): **"Usable headroom"**, note "After retained margin
  and service checks" - it names the hour's physical headroom, not the opportunity; nothing to report.
- **F3.** The 4 `read.mini_depth` calls: (renewable, 5-day bounds), (fuel, noon hour), (service, noon hour), (backup,
  noon hour) - distinct; perf probe `max_per_key 1`. New `read.opportunity` 1 call, 13-87 ms.
- **L3 polish** (`ch9r4`, dropped): create+migrate (0047 enqueued 165 service jobs), backfill a 179/b 9/c 3/d 6, **17
  settles** (10 mini jobs per tick, CH-1b bound unchanged, ~59 s each) -> 165 `/2` heads, 0 pending, dirty 0. Collect
  85 x 200; check `expected-today.json`: COH-2 2/2, COH-7 8/8 expected, **COH-17 0, every other rule 0, 0 new**,
  self-check 10 pass. Kobo day windows (8 story days): `critical_served` **PARTIAL** on every one (8/24 h, as Q6), but
  the **day grade is LOW, not PARTIAL**: `daylight_headroom_kw` is LOW on those days (pre-existing from u2, also in
  builder 7's B); A was PARTIAL. Counts: Kobo S c0/l1/p0, week l3/p0/n4, month l8/p0/n23 (A p1; p3/n4; p8/n23); claim
  texts and `count_basis` unchanged (CHECKED_DAYS). Reported, not adapted.
- **L3m MD-0** (templates rebuilt `tpl_db4dbb60` 3 parts seed 1071 s, `tplc_db4dbb60` 4 parts): states 65 x 200, every
  COH 0, COH-17 0; built non-gap days COMPLETE (c1 S, c4/n3 week, c10/n21 month = A), 25 Oct gap NO_DATA; count_basis
  and texts = A. Close 77 x 200, COH-17 0, every built day COMPLETE (c14 month = A); **COH-6 x4 expected entries
  (MD0b-R:A2, owner CH-6a) now RESOLVED** - the board reads the study, so the board/lens disagreement is gone. The
  entries are left in `expected-mechanism.json` for the Architect/CH-6a to retire.
- **F2 on MD-0 states:** summary `short_value` "2–8 kW unused" (B7: "2–20"), month headline "2–8 kW of daytime solar
  unused", study value line "2–8 kW over 12 daylight hours on every eligible day", Portfolio headroom {2, 8} - S, week
  and month. Close: no opportunity anywhere. Polish: Portfolio FOUND with null headroom, no kW summary row.
- **Perf** (`kobo_board_31oct`, branch clone, 5 runs): cold median 4428 ms, warm 3053 ms (B7 B: ~5115/~3385; main A
  ~4460/~2900); `mini_depth` ~930-1185 ms.
- **Guards** (run individually; `check-all` exceeds the 600 s foreground cap): architecture PASS (needs
  `ASSETOPS_GUARD_PYTHON`), navigation, agent workflow, dependency registry, delivery, mock gaps, missing-claim scan +
  fixtures, evidence width, mock deviation/V, screen ledger, chain coherence, event register: all exit 0. **Estate guard
  self-tests not run** (~870 s; split with `-k` next).

## Merge with CH-5c (builder 9; `main` `9fe13ae3f` = CH-5c `ac29b6f95` + Lows)
- **Merge** `cd48c69f1`: `git merge main`, no conflicts.
- **Migrations** `df8562b97`: one linear head 0044 -> `0047_chain_response` -> `0048_daylight_enqueue` (was 0046,
  `down_revision` 0047_chain_response) -> `0049_mini_service_v2` (was 0047, `down_revision` 0048). Earlier sections
  of this packet say 0046/0047 for these two files. Head literals, downgrade targets and test names were updated in
  `test_ch9_daylight_postgres.py` (its downgrade test now targets `0047_chain_response`, the revision under 0048) and
  `test_ch9_service_v2_postgres.py` (downgrade to 0048, head 0049). Comments were updated in the w402/w403 tests.
  `var/mechanism*-tpl/seed-state.json` is a generated fingerprint and was refreshed by the rebuild.
- **Merge consequence, owned test change** `2b36a6de4`: `test_w402_migration_postgres.py` `catalog()` counted every
  `mini_depth_%` trigger. CH-5c's 0047 adds `<table>_cic_{ins,upd,del}` on the four mini tables, so the count went
  from 5 to 17 at head. Main should be red on this test too (same test file, same 0047); I inferred that and did not run it on main. The count now leaves out `%_cic_%`, which CH-5c's own tests cover.
  It is not vacuous: before the change, the same run read 17.
- **COH-6 retired** `4239b5f8b`: the four `MD0b-R:A2` / owner CH-6a close-variant entries in
  `tools/checks/fixtures/chain_coherence/expected-mechanism.json` were deleted. They are resolved by **CH9-R4 F2**:
  the board's Grow headline now reads the study, so the board and the lens agree. The list only shrinks. The L3m close
  check below is the proof: COH-6 0 findings, 0 new, 0 resolved. None of the four still matched.
- **Owned test change** `18c701ec2`: `test_md0_mechanism_postgres.py::test_late_fill_normal...` failed on the branch
  with `daylight_headroom_kw` and `critical_served` PENDING after the fill. This is a CH-9 consequence (u2/F1), not a
  merge one: the fill queues mini work for every measured daylight hour and every service hour, but `late_fill`
  reconciles only the noon hour. After `late_fill`, the test now runs `md.drain_mini` (the product worker, as the
  build's `drain_mini` step does), runs step 10 again and re-reads the D7 grades. No assertion changed. The harness
  (`mechanism_dataset.py`) was left alone so the templates stay fresh. It was red before the change and green after.

### Checks on the merged tree (`18c701ec2`)
- L0 `test_ch5c_store_off.py::test_exactly_one_alembic_head` passed; `test_ch9_no_noon_literal.py` 9 passed.
- Postgres (`tools/run-host-tests.ps1`, port 55432): `test_ch9_daylight_postgres` + `test_ch9_service_v2_postgres`
  8 passed (173 s); `test_w402_migration_postgres` 14 passed (100 s); `test_md0_mechanism_postgres` 8/8 passed
  (2 kobo_grades/grow_headroom + 5 others + late_fill_normal after the fix, in 3 runs).
- **Polish clone `ch9m`** (from `assetops_polish_full_test`, read-only source; dropped). Create+migrate (0049
  enqueued 165 service jobs) and backfill a 179 / b 9 / c 3 / d 6. Settles: 18, at 10 mini jobs per tick, ~56-81 s
  each. One tick hit the 480 s wall cap because the machine went into Modern Standby (08:55-10:11); keep-awake was on
  afterwards. Result: 165 `mini-service/2` heads, 0 pending, dirty 0, head `0049_mini_service_v2`.
  - **W6** `tools/chain_watermark_guard.py`: **PASS**. 23 requests, 0 non-200, 81 tables read, unresolved [],
    untracked [], `event_consumption` read True.
  - `chain_response_probe.py` with `ASSETOPS_RESPONSE_STORE=on`: `prebuild` OK, 23 requests (stored 20, hit 3,
    48 s); `fresh` **23/23 stored bodies equal a fresh compose**.
  - Collect 85 x 200 (`PGOPTIONS` read-only). Check against `expected-today.json`: COH-2 2/2 and COH-7 8/8 expected,
    **0 new, COH-17 0**, self-check 10 pass.
- **MD-0**: `status` showed the templates were stale after the merge. Rebuilt `tpl_df73aa8a` (states: 3 parts, seed
  1266 s) and `tplc_df73aa8a` (close: 5 parts, seed 1868 s). L3m states: 65 x 200, every COH 0, COH-17 0, 0 new,
  0 resolved. L3m close: 77 x 200, **COH-6 0**, COH-17 0, 0 new, **0 resolved** (no stale entry left).
- **Guards** (each run on its own, with `ASSETOPS_GUARD_PYTHON` = the plan2 venv): architecture (213 s), navigation,
  agent workflow, dependency registry, delivery fixtures, mock gaps, missing-claim scan + fixtures, evidence width,
  mock deviation/vocabulary, screen ledger, chain coherence (103), event register (12). **14/14 PASS.** The estate
  guard self-tests ran in 3 `-k` parts (280 / 217 / 304 s): 15/15 passed.

### Polish finding: Kobo day grade LOW (deviation, recorded honestly)
On polish, every Kobo story day grades **LOW**, not PARTIAL. The cause is that `daylight_headroom_kw` is LOW on the
8 h delivered days, while `critical_served` is PARTIAL as expected (8/24 h). This is the intended consequence of
**CH9-R2 Q2**: the measure counts over the declared operating hours (Kobo 24 h), and an 8 h delivery covers only
part of them. The numbers were not tuned. **DD-1 full-day deliveries cure it**, and the MD-0 full days already grade
COMPLETE.
