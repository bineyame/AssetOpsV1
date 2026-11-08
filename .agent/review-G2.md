# Review OWN-G2 — automatic diesel-night check

Reviewer: fresh Claude (Opus), independent of the builder. Branch `task/OWN-G2-diesel-night-check` at `e33d8f113`,
base `9916fdbc1` (= main HEAD at review time). Diff reviewed: `git diff main...task/OWN-G2-diesel-night-check`
(23 files). Spec: `AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md` §1, §2, Rev 1, R2-G2, R3.1-R3.7 (D-R3.7).

## Verdict: REJECT (one Medium, spec-level; route to the Architect)

The code does what the card says, and every merge-condition run passed for me (below). The one blocking item is a
re-check gap in the card's own record-set rule (§2.4 step 4) that the builder implemented faithfully: a correction
that moves a fuel record **out of** a night older than the base set never re-checks that night, so a stale
"unexplained fuel" Finding can stay open after the operator fixed the record. Under the owner's "no corners on
fundamentals" this should be ruled before merge. If the Architect rules it out of scope (logged beside the §2.4
"out of scope" list), the slice is otherwise ACCEPT WITH NOTES.

## Findings

### M1 (Medium, acceptance/spec gap) — a correction that moves a record out of an old night never re-checks it
- Where: `backend/assetops_backend/fuel_balance/scheduled.py:89-97` (record set: `night = _night_holding(occurred_at)`
  of the **current head**); membership comes from `work/adapters/postgres_fuel_records.py:23-33` (the HEAD's kind,
  tank and `occurred_at` in `[lo, hi)`).
- What: the record set maps each record to the night holding its *current* head `occurred_at`. When a delivery or dip
  on night N (8-31 nights back, outside `[L-6, L]`) is corrected so its head occurs in daytime, on another night, or
  becomes another kind/tank, nothing maps to N any more, so N is never re-assessed. Its latest window keeps the old
  record in `record_ids` and its state (e.g. UNEXPLAINED with an OPEN Finding). The night the record moves *to* is
  re-checked; the night it left is not.
- Why it matters: this is the realistic operator flow (a delivery keyed with the wrong date, then corrected). Inside
  the 7-night base set it works only because every base night is re-assessed every tick, which is exactly what P4c
  exercises (N1 is a base night) — so the tests do not cover the old-night case. The result is a client-visible
  unexplained-fuel Finding that the data no longer supports, and it is not in §2.4's listed out-of-scope items
  (Foundation corrections and late readings older than 7 nights).
- Fix (Architect to rule; a builder must not design it): e.g. have `schedule_inputs` also return, per latest window in
  range, its stored `(root_id, head_id)` pairs, read the current head of each such root regardless of occurrence, and
  make the night due when any root's current head differs from the stored head (or no longer exists as a fuel record
  of that tank). A Postgres case like P5 on N9 with a correction moving the dip out of the night would prove it.

### L1 (Low, doc) — §2.4 still shows the half-open bucket
`build-sheet-OWN-GAPS-2026-11-08.md:504` (`lt::time < '12:30'`) and `:511` (`[start − 30 min, end + 30 min)`) still
read open-ended; R3.7 (`:1436`) rules them closed and the code is closed. Doc only; not edited.

### L2 (Low, residual) — "quiet" looks only at tank `fuel_level` decisions
`schedule_inputs` (`postgres_fuel_balance_store.py:261-268`) buckets only the tank's `fuel_level`, while the
assessment also reads generator roles (`service.py:108`). If generator readings for a night land in a later batch than
its tank readings, the night can be assessed early and then revised (possibly OPENED then WITHDRAWN) within the base
window. Self-heals, matches the card; worth a line in the after-demo list.

### L3 (Low, residual, spec-mandated) — one persistently refused night stalls the Site
Any refusal other than WINDOW_OPEN/ASSETS_UNSUPPORTED re-raises (`scheduled.py:125`). Nights are processed ascending,
so a `CLOCK_BACKWARDS` (e.g. a night assessed by the CLI at a future virtual instant) on the oldest due night fails the
stage every tick, blocks later nights, and puts the whole Site (all stages) into schedule back-off until the clock
passes. KIS-11 would catch it on the demo build; real sites should never assess at future instants.

## What I checked and found sound
- Placement/order: `fuel_night` after `mini`, before `opportunity`, under `stage("MINI")`, failure tuple
  `("FUEL_NIGHT", code, error)`, later stages still run (`tick.py:468-477`; `test_own_g2_fuel_night_tick.py`).
- Limits/lease: `fuel_nights_per_site=10`, `fuel_night_seconds=90`, both validated, joins the statement-timeout min,
  `site_lease_seconds` + 90, `STAGE_LIMIT_FIELDS`, `eligible` in the report. Matches §2.2 exactly.
- Idempotency: base nights REUSE on equal `input_sha256`; `raise_night` returns NO_FINDING/UNCHANGED without writes;
  proven on Postgres (P1 tick 2 counts equal across window, finding_revision, consequence tables).
- Late inputs: late readings within 7 nights re-checked via the base set (digest changes); deliveries/dips up to 31 d
  via the record set when their head is recorded after the night's latest window (P5 proven at 9 nights; 40-day record
  not read). See M1 for the inverse.
- Bucket SQL == Python: one SQL constant `NIGHT_BUCKET_SQL`, bounds from `bucket_bounds()`, `<=` on both sides;
  record nights use `rules.night_window` `[start,end)`, which is exactly the assessment's record read
  (`service.py:91`). Q1 proved per reading and with 11 synthetic instants.
- DB time: `clock_timestamp()` in `schedule_inputs` and the stores have no override in the stage (P7 proven).
- Story: P6 (CLI-assessed night gives REUSED/same raise, no row). KIS-11 reads story nights only
  (`demo_combined_finish.py:1395` filter), one fuel Finding, Kobo zero windows. Kobo: eligible, 0 nights, no rows (P3).
  Cold/EV take the early return (one read, no assess/raise; no-DB test 7).
- Demo tool: `Demo.tick` writes/removes `last-tick.json` and returns the last report; finish retries at most two
  extra ticks 30 s apart only for Kisiwa stories. Wording: no "theft"-family words in the diff.

## Runs (mine, on this revision)
1. No-DB set (11 files: 3 G2, ch0 tick timing, ch1b drain, cold_drain_stage, w402/w403 stage, finish rows, k3 rules,
   k4a rules): **203 passed in 11.5 s**.
2. `backend/tests/test_own_g2_fuel_night_tick_postgres.py`, whole file, one process, file order, `-s`, no `-k`/`-n`,
   base DB `assetops_g2rev_test` (run DB `assetops_g2rev_pt7934366e_main_test`), only heavy job, 4.4 GB free RAM at
   start: **5 passed in 1062 s (17:42)**. Lines: Q1 `readings 376 minutes [0,15,30,45] edges ['12:30','17:30']`,
   reading nights 10-29, 11-05, 11-06, 11-07 == want; tick 1 `processed 3, appended 2, reused 1, NO_FINDING 3`;
   P3 Kobo `eligible True, nights [], processed 0, elapsed_ms 1598`; P4a rev 2 `DIP_SENSOR_CONFLICT`; P4b 85 L
   `APPENDED OPENED UNEXPLAINED`; P4c rev 3 `WITHDRAWN WITHIN_MARGIN`; P5 records 3, night 10-29 rev 2.
   (A first attempt errored in 5 s because the base DB did not exist; I created it and reran.)
3. MAIN (`AssetOpsV1-plan2` at `9916fdbc1`, = branch base), `test_fix_cold_drain_tick_postgres.py::test_p1_...`
   alone, DB `assetops_g2revmain_test`: **1 failed in 13.3 s at `test_fix_cold_drain_tick_postgres.py:101`**
   (`assert jobs`, `AssertionError: []`) — the same line as on the branch. Pre-existing; R3.4 stands, not G2's.
4. `tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv: passed on the branch and on
   main. (Without it the chain-structure guard refuses to run in this worktree, which has no `.venv`.)
   `tools/check-agent-workflow.ps1`: passed.

Not run / not verified: `test_w402_mini_stage_postgres.py` and cold_drain p4 (R3.6 item 3: shown by the builder,
no stage/tick/limits change since); KIS-11 on a real prepared build (no prepare in this review); frontend (no frontend
change in the diff).
