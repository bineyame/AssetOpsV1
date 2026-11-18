# Review packet: DIESEL-K7-D (Kisiwa story days, build phase)

Branch `task/DIESEL-K7-kisiwa-story`. Card: build sheet §9l.3, amended by §9m.5 (R3m) and §9n.3 (R3k2).
Status: code complete; the Kisiwa-only scratch prepare ran and passed KIS-3/4/9 (see its section). K7-F (plan freeze, evaluation, default `--sites`) is not started.

## Commits (this round)
- `3b6895f27` Merge main (K4a, K6a). Conflicts in `test_out_b2_vocabulary.py` and `tools/demo_combined_rows.py` resolved by keeping both sides.
- `a898c5ed0` The pending steps and the R3k2 L2 carry.

## What landed
- `tools/demo_combined_kisiwa.py`
  - `raise_night(url, tenant, site, night, instant, k)`: K4a `worker.main(["raise", ...], finding_service=build_fuel_finding_service(url, test_db_clock_override=<story instant>))`; night 4 must print OPENED, others NO_FINDING (stop S-6).
  - `record_action`: `create_action` with `"domain": "FUEL_BALANCE"` (R3m), key `kisiwa-fuel-action`, domain clock at `raised_at`; MAINTENANCE_REQUEST case (key `kisiwa-fuel-request`), ASSIGN, record + COMPLETE on a second StepClock from `change_recorded_from`, the SITE_VISIT citing the case (recorded `S-4d 12:15`), then `post_case_link` at `case_link_at`. A refusal is stop S-7 (a K6a defect), never worked around.
  - `cli_raise_check`: the raise CLI as known now; night 4 UNCHANGED, others NO_FINDING.
  - `check` now builds the app client (when `keys.json` exists) so KIS-4 can read the served summary.
- `tools/demo_combined_finish.py`: `_kisiwa_finding` and `_kisiwa_action` read stored rows (Finding latest revision, window id/revision, thread mechanisms, consequence state and price revision, diesel v1 revision; Action origin, linked cases, case state as the latest work event kind).
- `tools/demo_combined_rows.py`: `KISIWA_MISSING_BODY`, `KisiwaMissing`, `failed_result`.

## Carry R3k2 L2
- `tools/demo_combined_finish.py`: KIS-4 (`kis_4`), KIS-3 (`kis_3`) and KIS-9 (`kis_9`) each `raise KisiwaMissing()` where they returned the "not in this dataset" skip. The row is marked failed and its `check.json` entry carries `read: {"kisiwa": "missing: no KISIWA-001 Site in this dataset", "checked": 0}`.
- `tools/demo_combined_rows.py`: `KISIWA_MISSING_BODY`, `KisiwaMissing`, `failed_result`; `run()` and `demo_combined_kisiwa.check` use `failed_result`.
- `backend/tests/test_k7_kisiwa_story.py`: L0 `test_carry_r3k2_l2_a_summary_with_no_kisiwa_fails_every_kis_row` (the fail body), `..._no_kis_row_keeps_the_skip_branch` (no "not in this dataset" text; three `raise KisiwaMissing()`), and a wiring test. No existing self-test expected the skip (none found by grep). Mutation proof: restoring the KIS-3 skip makes the second test fail; reverted.
- **Stop condition, reported:** the default `--sites` stays the three core Sites in K7-D (§9l.3), and the three-Site prepare runs the finish check, so on this branch a default three-Site prepare would now fail KIS-3/4/9. That dataset legitimately lacks Kisiwa until K7-F flips the default to include it. Resolution is K7-F's default flip (the carry says "once K7 merges"); K7-D must not merge alone.

## Deviation
- ASSIGN is recorded on a clock starting at `assign_at` (13:20), not on the request's StepClock from 13:10 (§9m.5): occurred 13:20 against a recorded 13:11 exceeds the Work API's 5 minute future slack (`model.py:36`) and would be refused. The request stays recorded at 13:10; the ASSIGN is recorded at 13:20. Not run against a database yet.

## Demo path note
The fuel Action's request link has no href until K6b. Nothing in the demo path (story links, KIS rows) follows it.

## Checks run
- `pytest test_k7_kisiwa_story, test_k4a_fuel_finding_rules, test_out_b2_vocabulary`: 109 passed.
- `pytest test_demo_combined_finish_rows/_days/_co1, test_demo_combined_links, test_demo_story_days, test_k3_fuel_balance_rules, test_k6a_fuel_action_origin`: 159 passed.
- `tools/probe_kisiwa_fuel.py --check`: "probe result current", exit 0. `tools/probe_kisiwa_nights.py --check`: "probe result current (G6 pass)", exit 0.
- Not run: Postgres-backed tests (`test_k4a_fuel_finding_postgres`, `test_k6a_fuel_action_origin_postgres`), the Kisiwa scratch prepare, any layout evidence (none applies).

## Residual risk
- `raise_night`, `record_action`, `cli_raise_check` and the KIS-9 SQL reads are unexercised against a database until the gated scratch prepare. Column names were taken from migrations 0027, 0033, 0042, 0056, 0010.
- `case_state` is the latest work event kind (`COMPLETE`), not a stored state column.

## Kisiwa-only scratch prepare (run 2026-11-08, code 9dcba4b98)
- Command: `python tools/demo_combined.py --db assetops_demo3_kisiwa_test --work var/demo3_kisiwa prepare --sites kisiwa --cap-seconds 5400`. Keep-awake was already running (pid 23744).
- Gate samples (free RAM, 30 s apart, 5 samples): 3.14, 3.30, 3.49, 3.23, 3.25 GB; all at least 2.5 GB.
- Wall time: "Prepared in 4199.5 s (cap 5400 s)". Build step 3567.7 s (`wall_seconds` 3551.0); register 2.0 s. Per-day seconds 314.6-381.7 (mean about 353), above the card's 150-200 s estimate; no cap or stall stop fired (the redirected stdout was block-buffered, so the log showed no step lines for about 60 min while the child CPU time kept rising).
- Lowest free RAM during the run (60 s watcher): 1.91 GB (floor 1.0 GB never reached). Peak working set not sampled.
- Checks (read-only, from `kisiwa.json` and the database):
  - `raise_night`: night 4 (2026-10-31) OPENED, finding `bddd2f26`, revision `0ff2781c`; nights 1-3 and 5-10 NO_FINDING. Pass.
  - `record_action`: ACT-000001 (FUEL_BALANCE) raised/recorded 2026-11-01 13:00; request CREATED 13:10; ASSIGN 13:20 (Work API accepted it, work_event stored, assignee "Site lead"); site visit REC-000014 recorded 2026-11-02 12:15; COMPLETE occurred 12:05 and recorded 12:10:01; case link recorded 12:20. All at story times. Pass.
  - `cli_raise_check`: night 4 UNCHANGED, the other nine NO_FINDING. Pass. `cli_assess_check`: ten REUSED, revision 1. Pass.
  - Finish rows (`demo_combined_kisiwa.py check`, exit 0): KIS-3 pass (10 nights, night 4 UNEXPLAINED, the rest WITHIN_MARGIN; matches F0 terms); KIS-4 pass (supported 1, priced 1, 5 sums, 124 served strings); KIS-9 pass (13 records, 11 dips, 15 placed, finding `bddd2f26`, case `fb7d8277`).
  - Stored night-4 Finding: "Unexplained fuel overnight", SUPPORTED, UNEXPLAINED_FUEL, created 2026-11-01 12:31 (run end + 31 min). Litres 95.657-144.343 (PRICED, 1.25 USD per L); money 119.57-180.43 USD. Within the expected 95.7-144.3 L and 119.57-180.43 USD.
- Observations (no code changed): the prepare's later shared steps, run with Kisiwa only, printed "performance: Site 'KOBO-001' is not registered in tenant 'demo'." and a prebuild line `code: FAILED` (404s on `/api/sites/KOBO-001/...`). These steps assume Kobo is registered. The coordinator should confirm they are acceptable for a Kisiwa-only scratch (they did not affect the KIS rows). The prepare's own exit code was not captured.
- Kept: database `assetops_demo3_kisiwa_test` and `var/demo3_kisiwa` (K5 captures). Nothing dropped.

## User review
Not required by this phase; K7-F and the owner walkthrough follow.
