# EV-HB review packet

Branch `task/EV-HB` (worktree `AssetOpsV1-evhb`), from main `700469706`. Card: D-E5.48 (2) "Card EV-HB" in
`AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md` (commit e1d586860); BL-72 keeps the weekday calendar.
Plus PB-3 review Low: AVAILABLE/DISABLED are known zero-energy status.

## Outcome

- Every EV story day (v4 `normal` S-14, S-7 and `fault` S, each on its Tuesday) records the declared charging hours
  08:00-16:00 UTC, received 16:30 (was 08:00-09:00, received 09:30). Sessions, kWh, fault and USD are unchanged.
- One source for the window: the day-list entry. `tools/demo_combined_ev.py` `story_window(day)` (it must open where
  the registered scenario opens and may only run longer) feeds the shifted scenario document, `ev_parsing.EV_WINDOW`
  (`story_definition`, swapped for the call only), the w205b `WINDOW` and the w504 `E_START/E_END`. The clocks tied
  to the window's close (`FIRST/LATE_DECISION`, `RELEASE`, `ATTESTED_AT`) move with the close.
- `host/ev_lab.py` `parse_ev_artifact`: an EV artifact may be 61 to 481 boundaries (1 h to the ruled 8 h schedule),
  complete (`completed == total`, `offset == total - 1`). Before: exactly 61. Without this the 8-hour run reads
  `ARTIFACT_UNREADABLE` and nothing is released (found by the Postgres test).
- `chain/grading.ZERO_ENERGY_STATES` and `analytics/ev_availability.REPORTED_STATES` include AVAILABLE and DISABLED.
  Availability `CATEGORY` is unchanged.
- `late` kind (add-day only, never a story day) keeps 08:00-09:00: its record is held to a 09:05 release, which a
  16:00 first cutoff would no longer make late.

## Files

`tools/demo_combined_ev.py`, `tools/demo_story_days.py` (comment), `backend/conversions/demo-story-days-v4.json`,
`host/ev_lab.py`, `backend/assetops_backend/chain/grading.py`, `backend/assetops_backend/analytics/ev_availability.py`.
Tests: new `backend/tests/test_evhb_ev_window.py`; `backend/tests/k7_story_pins.py` (story text +186 chars: notes;
times are same length); `backend/tests/test_demo_story_days.py` (v4-vs-v3 diff restores the EV hour, as DATA-11 did).

## Acceptance (card items)

| Item | Status |
|---|---|
| 1. Registered window, w205b/w504 constants, received_at, analysis window = 08:00-16:00; one source | Met (`story_window`; pure swap test) |
| 2. Sessions 08:01-08:31 and fault values byte-for-byte; idle minutes are heartbeats | Met: every public record of the first hour equals the one-hour day's (but the per-document session token, already distinct per day); session/fault/energy records equal; after 09:00 c1/c2 UNPLUGGED (fault day: c1 FAULTED, the latch) |
| 3a. Pure: full-window day grades COMPLETE | Met: generated day 28800/28800 COMPLETE; the one-hour day 3600/28800 LOW |
| 3b. Plan pins: kWh, USD, fault findings unchanged | Met: 30 / 15 kWh pure and stored; USD 9.00 / 4.50 stored; one fault-day Finding anchored 08:01 |
| 3c. One EV worker run of the 8-hour window, day not LOW | Met at test scale (Postgres, producer `run_day`, see below); scratch prepare still to do (gate) |
| 4. Finish rows that change | See "Rows that change" |
| 5. Prepare-time delta | Test scale only: two 8-hour days through `run_day` ~50-60 s together (fresh DB); 1-hour baseline not measured. Prepare must record it |
| Tests first | `76b6634ec`: 11 failed before (Postgres one skipped there, then failed on ARTIFACT_UNREADABLE before the host fix) |

## Checks (one file at a time, plan2 venv, DB `assetops_evhb_test`, pg_stat_activity < 150 checked)

- `test_evhb_ev_window.py` 12 passed, 0 skipped (Postgres, 150 s). Postgres test: S-7 normal COMPLETE 28800 kwh
  30.000 USD 9.00; S fault COMPLETE 28800 kwh 15.000 USD 4.50; dispositions ACCEPTED only; sessions COMPLETED
  08:01-08:31 30.000 / OBSERVED_ABORT 08:01-08:16 15.000; whole-UTC-day read shows the period 08:00-16:05.
- Pure: `test_k7_kisiwa_story` 101, `test_demo_story_days` 92, `test_data11_story_week` 14, `test_demo_combined_links`
  12, `test_demo_combined_finish_rows` 77, `test_demo_combined_finish_days` 1, `test_own_g1_add_dates` 49,
  `test_ch1a_grading` 25, `test_demo_combined_ex1` 9, `test_demo_combined_mill` 15, `host/tests/test_ev_lab_execution`
  44, `host/tests/test_ev_publication` 28, `simulator/tests/test_ev_pack` 78, `test_ev_public_transform` 10: all passed.
- Generated days (simulator, host side): `host/tests/test_evhb_generated_days.py` 5 passed (moved out of the backend
  file at `a5b6f6fad`: the dependency-direction guard bans simulator imports in backend tests; they failed before
  the change while still in `76b6634ec`). Backend file afterwards: 6 passed + the Postgres test (12 passed earlier
  in its combined form).
- Postgres adjacent (0 skipped): `test_pb3_ev_status_grading` 10 passed (53 s); `test_pb1b_ev_periods_postgres` 9
  (322 s); `test_w205b_ev_replay_postgres` 13 (606 s; one-hour registered replays unchanged under the host change);
  `test_w503_ev_availability_postgres` 15 (154 s).
- `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv) at `a5b6f6fad`: "Architecture check passed.",
  exit 0 (the first run failed on the simulator import, fixed by the move).

## Rows that change (each with its reason)

- **E5** (Overview EV estimated income): no longer "1 with too little data"; the EV days grade COMPLETE (8 h of 8 h
  status-known), so the week's EV income is counted (USD 4.50 on the fault day S, 9.00 on S-7).
- **WK-1** (EV Grow row, S board): `known` true now, headline money present (the row adapts; its docstring comment
  "the fault run is 1 h of the session, so no day counts" is now stale - not edited, a comment only).
- **CO-6** `cold_ev_coverage`: a recorded read, not asserted; EV coverage may read more checked time.
- **EV `charging_kwh` pins**: no finish row pins the EV grade; only `k7_story_pins` (story text) moved.
- **PB-1b shown period** on an EV day: 08:00-16:05 (was 08:00-09:05; the worker's job window closes 5 min after).
  The DATA-2 "analysed period" link reads `HH:MM` from the day entry: now "08:00-16:00Z".
- EV availability on the fault day: c1 is FAULTED (known unavailable) 08:16-16:00 instead of 08:16-09:00.
- **D-E5.49 (sanctioned exception to "every other row stays equal")**: on the fault day clients read c1 "out of
  service for 7 h 44 min" (464 min, 0 min unknown) with one CONNECTOR_OUT_OF_SERVICE warning ("7 h 44 min out on
  3 Nov"; was "44 min out and 16 min unknown"). Pinned in `backend/tests/test_out_c4_mini_ev.py::
  test_ev_fault_day_connector_out_7h44_with_no_unknown_time` (warning title/seen, Protect contributor "Connector c1:
  7 h 44 min out, 0 min unknown", subline) and in finish row CO-10 (`tools/demo_combined_finish.py`: exactly one
  CONNECTOR_OUT_OF_SERVICE, `seen` starts "7 h 44 min out", no "unknown"; returned as `connector_out`).
- Script-refresh strings (DS-1f/DS-1b, NOT edited; replace with "out of service from 08:16 for the rest of the
  charging day (7 h 44 min); repair still pending"): `Docs/demo-sprint/demo-script-img/e5/text/01-portfolio-week-{390,1440}.txt:260`
  "Depot - Protect asset and capital - 44 min out and 16 min unknown on 3 Nov"; `.../10-ev-board-fault-1103-{390,1440}.txt:42`
  "Connector c1 was out of service for 44 min; ..." and `:49` "Connector c1: 44 min out, 16 min unknown";
  `frontend/src/sites/__tests__/evFindingIndex.test.tsx:148,157` use "44 min out and 16 min unknown on 6 Oct" as a fixture
  string only (independent of the data; may stay). `implementation-logic-portfolio-sites-findings-actions.html:709,1031`
  already updated here on this branch. Captured pngs of those screens are stale too.

## Known deviations

1. `host/ev_lab.py` strictness relaxed (61 -> 61..481 boundaries): a product-side change the card did not name, but
   item 1 cannot run without it. Reviewer to confirm.
2. `late` kind kept at one hour (reason above).
3. Fault day: the latched fault keeps c1 FAULTED to 16:00 (honest; no CLEAR in `ev-interrupted`). Availability
   and any downtime figure on that day grow accordingly.

## Scratch prepare (Thursday afternoon; green by Fri 13 Nov 18:00 or EV-HB is dropped) must verify

1. `days.json`/`ev.json`: 3 EV runs, each `evidence_window` 08:00-16:00Z on its Tuesday, received 16:30; dispositions
   ACCEPTED; `ev day ... ASSESSED` x3; no ARTIFACT_UNREADABLE / COMMIT_NOT_READY in the EV log.
2. Chain snapshots `charging_kwh` (EV-LAB-001), each EV day: grade COMPLETE, required = covered = 28800; value kWh
   30.000 (S-14, S-7) and 15.000 (S); money USD 9.00 / 9.00 / 4.50.
3. Overview E5: EV estimated income counted, not "with too little data"; the fault-day USD 4.50 reads as before.
4. Fault day S: the one Finding (session start 08:01, fault 08:16), Action, intent, the two connector visits and the
   plan as before; EV Site whole-day read shows the period 08:00-16:05; WK-1 green.
5. CO-6 green; record `cold_ev_coverage` and compare EV with the last build (expected more known time, no failure).
6. Cold: session counts on any client page that shows them (8 daily uploads S-7..S, DATA-11) unchanged by EV-HB.
6a. Fault day S (D-E5.49): c1 out of service 7 h 44 min, 0 min unknown, one Finding, Action Pending, USD 9.00 / 4.50;
   E5 / WK-1 count 9.00 / 9.00 / 4.50; CO-10 `connector_out` reads "7 h 44 min out on 3 Nov".
7. All other finish rows green and equal; record the prepare time and the EV step's seconds (`EXPECTED_SECONDS["ev"]`
   is 200) against the last build.

## Fix round (D-E5.49 + review Lows)

Merged main. Added: 7 h 44 min pins (above); `host/tests/test_ev_lab_execution.py::test_ev_artifact_window_boundary_edges`
(481 and 61 pass the window check; 482, 60 and an incomplete window are refused with the window reason); stale comments
fixed (`host/ev_publication.py:146`, `tools/demo_combined_finish.py` WK-1); the implementation-logic html updated.

Checks: `test_out_c4_mini_ev` 13, `test_ev_lab_execution` 49, `test_demo_combined_finish_rows` 77 passed;
`test_evhb_ev_window.py` (Postgres, 0 skipped) run twice, 7 passed both times (257 s, 224 s); no failure recurred.

## User review

Not required for the code (owner-delegated D-E5.48); the owner sees E5 at the rehearsal.
