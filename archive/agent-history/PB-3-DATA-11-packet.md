# PB-3 + DATA-11 review packet

Branch `task/PB-3-DATA-11` (worktree `AssetOpsV1-pb3`), from main `b685975c7`. Cards: `.agent/architect-answer-non-kobo-sites-2026-11-10.md`
PB-3 (261-267), DATA-11 (303) and D-E5.37 (188-191); owner "raise DATA-11" (`.agent/owner-answers-17nov-scope-2026-11-11.md`).

## Outcome

- **PB-3.** `charging_kwh` is graded on connector-status-known time. The basis is declared per measure in
  `config/chain/coverage-policy-v1.json` (`measures.charging_kwh.covered = connector_status_known`); every other measure
  keeps interval coverage. Rule (`chain/grading.py` `status_known_spans`): per connector, a reported zero-energy state
  (UNPLUGGED, PLUGGED, AUTHORIZING, FAULTED) is known at zero energy; CHARGING is known only under a SUPPORT meter
  interval; the Site is known only where every connector is. The builder applies the declared basis
  (`chain/builder.py`); the fingerprint carries the basis only when it is not the default, so every non-EV
  snapshot fingerprint is byte-equal and EV rows re-revision once.
- **DATA-11.** The v4 day list gives Cold an ordinary day (`ordinary` kind = `cold-normal`, 16:00-17:05Z, received
  17:05, assess build) on S-6, S-5, S-4, S-2 and S-1, so Cold has a built day on every day S-7..S. Each Cold (and EV) day
  is its own recording session: `SESSION_PER_DAY_SITES` in `tools/demo_story_days.py` keeps one epoch per Site-day.

## Files

- `backend/assetops_backend/chain/{grading,policy,ports,builder,measure_impls}.py`, `chain/adapters/postgres_chain_inputs.py`
  (`ev_window` adds `connectors`), `analytics/ev_availability.py` (`status_spans`, `status_spans_on`;
  `_observations` takes a classifier, default unchanged), `config/chain/coverage-policy-v1.json`.
- `backend/conversions/demo-story-days-v4.json`, `tools/demo_story_days.py`.
- Tests: new `backend/tests/test_pb3_ev_status_grading.py`, `backend/tests/test_data11_story_week.py`; updated
  `test_demo_story_days.py` (`test_v2_epoch_guards`, `test_v4_story_week_one_missed_one_partial`) and
  `k7_story_pins.py` (v4 three-Site pins; the v3 pins are unchanged and still pass).

## Acceptance

| Item | Status |
|---|---|
| PB-3 covered time = connector-status-known time, idle known = zero energy | Met: pure tests, builder test, adapter test |
| PB-3 in `chain/grading.py` + EV delivered-energy entry in the coverage policy | Met |
| PB-3 on real stored rows | Met: Postgres `complete` replay, every second of the window known; equals the prior coverage |
| DATA-11 Cold 2, 3, 4, 6, 7 Nov (S-6, S-5, S-4, S-2, S-1) | Met (offsets; S moves with the prepare date) |
| DATA-11 EV S-6..S-1, one ordinary session a day; EV status heartbeat | **Not built**: Known Deviation 1 |
| Story event days keep their values | Met at plan level: every pre-existing run's payload is equal but its `epoch` label (test) |
| Tests first (fail before) | Met: PB-3 9 failed before; DATA-11 10 failed before |

## Checks (worktree, revision `0f799572c` + packet and the Postgres test commit)

One file at a time, python `AssetOpsV1-plan2\.venv`, DB `assetops_pb3_test` (pg_stat_activity < 150 checked):
- `test_pb3_ev_status_grading.py` 10 passed, 0 skipped (Postgres). `test_ch1a_grading.py` 25 passed;
  `test_ch1a_reassessment.py` 11 passed; `test_ch6b_estate_chain.py` 20 passed (Postgres).
- `test_data11_story_week.py` 14 passed; `test_demo_story_days.py` 92 passed; `test_k7_kisiwa_story.py` 101 passed;
  `test_demo_combined_links.py` 12; `test_demo_combined_finish_days.py` 1; `test_demo_combined_finish_rows.py` 77;
  `test_demo_combined_mill.py` 15; `test_own_g1_add_dates.py` 49; `test_k1_kisiwa_fixtures.py` 19;
  `test_demo_combined_ex1.py` 9 - all passed.
- `test_w303_portfolio_comparison_postgres.py`: whole file 1 failed / 3 passed (583 s, after `test_ch6b` on the same
  DB; failure text not captured); the failing test alone then passed (77 s). It touches no changed module
  (Kobo verification); recorded as order/DB-state dependent, not a pass of the file.
- Not run: `host/tests/test_dd1a2_r3_add_day_after_trial.py` (skipped without DB in the batch; a Kobo trial
  producer run, Kobo epochs grouping unchanged), `test_demo_combined_postgres.py` (prepare-sized).
- `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv): "Architecture check passed.", exit 0.

## Known deviations

1. **EV: no days added, no heartbeat.** ev-charger/1 runs only on a TUESDAY (`SITE_WEEKDAY`, `host/ev_publication.py`
   `ev_parameters`), and the operating calendar declares EV TUE 08:00-16:00 only. The story week S-6..S holds exactly
   one Tuesday, already the EV fault day, so "EV for S-6 to S-1" resolves every entry back onto an existing Tuesday
   (DUPLICATE_DAY). The model already reports connector state every minute (`observation/transform.py:600-603`); what
   is short is the run window: the EV registered window is pinned to one hour (`ev_parsing.EV_WINDOW`, the w205b
   constants the producer moves per day). A charging-day heartbeat means an 08:00-16:00 EV run, which needs the parser
   window, the w205b/w504 constants, received_at and the analysis window extended, and has never run through the EV
   worker: not provable without a prepare. **Architect call**: extend the ordinary EV `normal` days (S-14, S-7 Tuesdays;
   same 08:01-08:31 session, so kWh and USD 4.50 unchanged) to 08:00-16:00, or leave E5 honestly LOW. With PB-3 in place
   such a day grades COMPLETE (pure test `test_idle_known_status_counts_as_zero_energy_coverage`).
2. **One epoch per Cold day (DD1a1-R8 narrowed for Cold and EV).** Merging S-7..S into one stream would (a) refuse the
   week (`BUILT_DAY_AFTER_DEGRADED`: S-3 is Cold `degraded`) and (b) leave every later day unattested: the Cold
   producer attests once per epoch over the first run's window (`tools/demo_combined_cold.py:90-101`). `add-day`
   already mints a fresh epoch per added day. Kobo streams are unchanged (test). Architect to confirm.
3. Epoch labels `day-<n>` renumber after the first new Cold day in build order (labels only; values unchanged).

## Counts that legitimately change

- Cold built runs +5 (8 Cold runs); DATA-2 link rows +10 (each new Cold day: whole-day + analysed-period row).
- `F-THREADS` `boards_read` +5 (reads a board per built day; its "no board fault" assertion now covers the new days).
- `CO-6` recorded `cold_ev_coverage` (a read, not an assertion) may count more Cold days in the week.
- EV `charging_kwh` snapshot rows take one new revision (fingerprint carries the basis); covered seconds, grade and
  value unchanged on the 1-hour story windows (Postgres test). No other finish row value moves.

## Saturday rehearsal build must verify

1. `days.json`: 8 Cold runs S-7..S (S-6, S-5, S-4, S-2, S-1 `ordinary`), 8 distinct Cold epochs; EV 3 runs as before.
2. Cold build log: five `cold day <date> ordinary <run_id> 0 findings`; dispositions ACCEPTED; no
   CLOCK_UNATTESTED rows on the new days; prepare time delta (expected about +10 min: 5 x the last run's Cold `normal`
   day seconds) - record it.
3. All finish rows green; unchanged values: Cold 4.9 °C peak and "Stock may be at risk" (S failure), EV USD 4.50,
   F-COH, the Pending states, CO-5/SP-2 (still the S-7 `normal` day), CO-7, CO-9, CO-10.
4. Chain snapshots: every new Cold day has `chamber_temp_c`/`backup_start_chain` rows (LOW, 65 of 1440 min); EV
   `charging_kwh` covered_seconds per EV day equals the previous build's value; no Cold or EV thread closes or opens
   because of the new days.
5. Cold Site week window (PB-1a): analysed periods on all 8 days; the failure day is the shown period. Health,
   Performance and Financials on a Cold day window for one new day read an ordinary day, no blank view.
6. Overview E5 (EV estimated income) still reads "1 with too little data" (Deviation 1), with USD 4.50.
