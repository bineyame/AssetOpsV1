# Pre-flight G2 — automatic diesel-night check (`fuel_night` tick stage)

Implementer (Claude), branch `task/OWN-G2-diesel-night-check` from main `59a89397a`. Read-only; no Postgres run.
Spec: `.agent/build-sheet-OWN-GAPS-2026-11-08.md` Revision 1, §1, §2. Every anchor in §2 was checked against the code.

## Anchors confirmed (no question)

- `scheduling/tick.py`: `_site` 406-537 (mini 450-457, opportunity 459-467, `chain_threads` under `stage("S4")` 483-490);
  `TickLimits` 60-121 (`__post_init__` "at least 1" `min(...)` 89-92, statement-timeout `min(...)` 107-111,
  `site_lease_seconds` 114-117); `TickReport.as_json` key tuple 194-196; `_deadline_at` 266-269;
  `STAGE_LIMIT_FIELDS` 272-276; docstring point 5 at 19-24.
- `scheduling/stages.py`: docstring stage list 5-6 and `OK` list 14; `_uuid` 83; `_deadline` 195-200; `_dispose`
  349-353; `STAGES` 472-476; `main` handler → `classify` 513-526.
- `fuel_balance/composition.py` 17-46: `build_fuel_balance_store(url)` and `build_fuel_finding_service(url)` exist, DB
  clock by default; `FuelFindingService.dispose` exists (`findings_service.py:70`).
- `fuel_balance/model.py:24-26`: `WINDOW_OPEN`, `ASSETS_UNSUPPORTED`, `CLOCK_BACKWARDS` codes;
  `service.py:68-125` one transaction per assess, closed rule `known_at < end + EDGE` → `WINDOW_OPEN`, digest reuse.
- `findings_service.py:22-23`: `OPENED, REVISED, WITHDRAWN, UNCHANGED, NO_FINDING, NO_WINDOW`; `RaiseResult.status`.
- `rules.py:52,57`: `EDGE_SEARCH_MIN = 30`, `NIGHT_START, NIGHT_END = time(18), time(12)`; `night_window` 107-118;
  `DIP_SENSOR_CONFLICT` 257; `balance` 216-237.
- `actions/adapters/postgres_action_store.py:600-608` `window_readings` join/filter (returns `d.decided_at`).
- `work/model.py:37` `BACKDATE_LIMIT = timedelta(days=30)`; `work/adapters/postgres_fuel_records.py:40-48`
  (`[lo, hi)` on the head's `occurred_at`, as known at `known_at`; `recorded_at` is the head's).
- Migrations: `0044_chain_events.py:66` (`finding.revised`), `0030_w4_mini_decisions.py:233` (stage CHECK, `MINI`
  allowed), `0013_schedule_state.py:80` (`last_failure_stage text`), `0058` input-table triggers; head stays `0058`.
- `scheduling/health.py:142`, `:291` show `last_failure_stage`.
- `fuel_balance/worker.py:8` holds the exact sentence the spec replaces.
- `tools/demo_combined.py` `Demo.tick` 623-629 (tick child stdout, last line is `report.as_json()`,
  `scheduling/run.py:92`); `after_children` 541-571 ("No tick may run before the mill step" 543); `finish` ticks 592.
- `tools/demo_combined_kisiwa.py:803-830` `cli_assess_check` / `cli_raise_check`; `demo_combined_finish.py` KIS
  windows filtered to story nights 1379-1395; KIS-4 992-1034.
- Tests the spec lists as pinning the stage list or lease sum all exist and are exactly the files that pin them
  (`test_ch0_tick_timing.py:37`, `test_ch1b_drain.py:395-418`, `test_fix_cold_drain_stage.py:21,61-64`,
  `test_fix_cold_drain_tick_postgres.py:106,199`, `test_w402_mini_stage.py:84,101,116,124,133`,
  `test_w402_mini_stage_postgres.py:147`, `test_w403_opportunity_stage.py:24-26,42,58`). No other test pins them.

Informational only (no ruling needed): `tick.py:31-33` cited for "every stage runs even after an earlier stage
failed" is now `tick.py:27-28`. `rules.NIGHT_START − EDGE` is `time − timedelta` (not defined in Python); I compute it
with `datetime.combine(...)` and pass `time` values as bound parameters.

## Questions (each: spec ref, code, question, proposed answer)

**Q1. Where the night bucket is tested.** Spec §2.4 puts the bucket in the `schedule_inputs` SQL; §2.7 file
`test_own_g2_fuel_night_due.py` (no DB) case 1 tests bucket edges, and Rev 1 asks for a unit test that changing
`NIGHT_START` moves the bucket. A no-DB test cannot run the SQL. *Question:* how are case 1 and the Rev 1 pin made?
*Proposal:* `scheduled.py` exports `bucket_bounds() -> (time, time)` computed from `rules.NIGHT_START/NIGHT_END` and
`EDGE` (the SQL's two bound parameters) and a pure `night_of(local_dt) -> date | None` that mirrors the SQL `CASE`.
No-DB case 1 tests `night_of`; the Rev 1 pin monkeypatches `rules.NIGHT_START` and asserts `bucket_bounds` and
`night_of` move. The Postgres file adds one case that seeds readings at local 17:29/17:30/12:29/12:30 and asserts
`schedule_inputs.reading_nights` equals `night_of` on each (SQL and Python agree).

**Q2. Where `ScheduleInputs` lives.** §2.6 puts `ScheduleInputs` in `fuel_balance/adapters/postgres_fuel_balance_store.py`,
but the pure `due_nights` in `fuel_balance/scheduled.py` consumes it. `tools/checks/configuration-persistence.ps1:8,199`
("adapters are imported only by their own domain's composition module"; fuel_balance: "Only its composition imports the
adapter") would fail if `scheduled.py` imported the adapter. *Proposal:* define `ScheduleInputs` (frozen dataclass) in
`fuel_balance/model.py`; the adapter imports it from there (as it already imports `FuelBalanceWindow`). Also add
`schedule_inputs` to the `FuelBalanceReadPort` Protocol (`model.py:73`) so the fake stores type against it.

**Q3. The `latest` read: which nights, and which transaction.** §2.4 says `schedule_inputs` runs in **one** read-only
transaction and `latest` comes "from the existing `windows(...)` read over the same nights". `windows()`
(`postgres_fuel_balance_store.py:217-227`) opens its **own** `_read` transaction, and "the same nights" is undefined
(readings span `known_at − 32 d`, records `known_at − 31 d`). *Proposal:* factor the `windows` SQL into a
`_windows_on(c, ...)` helper used by both `windows()` and `schedule_inputs` (same connection, same snapshot, unchanged
`windows()` behaviour), over night dates `[local date of (known_at − record_lookback − 1 day), L + 1)`. The
`base_nights` parameter of `schedule_inputs` is then unused by the read; keep it in the signature only if you want it
(I would drop it).

**Q4. The deadline type.** §2.4 `run_site` loops "while `time.time() < deadline`"; §2.3 passes `_deadline(args)`, which
returns a `chain.drain.Deadline` callable or `None` (`stages.py:195-200`, `chain/drain.py:85-97`; it also reserves the
slowest item seen), not a float. *Proposal:* `run_site(..., deadline: Callable[[], bool] | None)`; before each night
`if deadline is not None and deadline(): break` (the `chain_threads` idiom). The unit "a passed deadline starts no
night" passes a callable that returns True.

**Q5. Postgres test fixtures (biggest gap).** §2.7 says "reuse the Site, readings and record fixtures of
`test_k4a_fuel_finding_postgres.py`". That file has **no readings**: it appends synthetic windows on a virtual clock
(`Fuel.put`, `test_k4a...:84-104`), dated 2027-01 / 2026-10 (`:29-31`). `test_k3_fuel_balance_postgres.py` likewise has
no tank readings (Kobo, NOT_ASSESSED). The stage runs on the real DB clock (no override), so P1/P2/P4/P7 need **tank
`fuel_level` (and generator) readings on nights within the last 7 real nights**, with `decided_at ≤ now − 5 min`.
The only real reading path is K1's (`test_k1_kisiwa_site_postgres.py:42-110`: `kis.register`, `draft_day` with
`probe_kisiwa_nights.day_document`, `rp._publish_and_accept`), dated fixed in 2026-10. The ledger has a
`test_decision_clock_override` (`evidence/adapters/postgres_evidence_ledger.py:525-528`). *Question:* which fixture?
*Proposal:* one module-scoped Kisiwa Site via K1's path, registered at DB now − 12 d; draft and publish 3 runs ending
at the last three real-night ends (12:00 local + 0), accepted with the decision clock at DB now − 10 min (quiet holds
without waiting); P2 is a night with no run; P3 imports Kobo (`test_s1_bindings_postgres.imported`); P5's old night is
a 4th run ~10 nights back; P6 assesses/raises one night through the CLI on a virtual instant before the ticks. Real
`StageRunner` children as §2.7 says. Cost estimate: K1's day publish dominates, roughly 3-6 min for the file.

**Q6. P4's "delivery turns UNEXPLAINED into WITHIN_MARGIN" is backwards.** `rules.balance` (`rules.py:225-227`):
`low = drop + d − d_tol − use_high − margin`. A recorded delivery `d` **raises** the residual; it cannot turn an
UNEXPLAINED night WITHIN_MARGIN, and a dip only adds a limitation (`:251-257`). With the K1 day document (no draw)
there is no sensor-drop night either. *Proposal:* invert it with the product's own paths: post a `FUEL_DELIVERY`
of ~200 L that the sensor does not show on a WITHIN_MARGIN night → next tick appends revision 2 UNEXPLAINED and the
raise is `OPENED` (the fixture's one UNEXPLAINED night); then post a **correction** of that record moving
`occurred_at` out of the night (records are root/head, "a correction may move it", `work/fuel_records.py:28`) → next
tick appends revision 3 WITHIN_MARGIN and the raise is `WITHDRAWN`. The DIP_SENSOR_CONFLICT half of P4 stays as
written (a dip far from the sensor level → revision with the record in `record_ids` and the limitation).

**Q7. P5's "a record 40 days back is not read".** `WorkService` refuses `occurred_at` older than
`BACKDATE_LIMIT = 30 d` (`work/model.py:37`) at the work clock. *Proposal:* post it with the work store on a
`VirtualDbClock` set to occurred + 29 d (so `recorded_at` ≈ 11 days ago, which is later than the night's window,
assessed via the CLI at a virtual instant just after the night closed), on a night that has readings; assert the tick
adds no row for that night. Its night must then also have readings 40 days back (a 5th run) — or, cheaper, prove the
40-day exclusion only at the read level (`schedule_inputs(...).records` excludes it) and keep the no-row proof for the
10-day case. I would take the cheaper form; please choose.

**Q8. "Units (no DB) ... `test_s4_schedule_*` style (`InProcessRunner`)".** `InProcessRunner`
(`test_s4_schedule_tick_postgres.py:61-81`) calls the real stages against the Postgres URL; it is not a no-DB helper.
The no-DB pattern is `FakeStore` + a fake runner (`test_fix_cold_drain_stage.py:21-103`,
`test_w402_mini_stage.py:84-135`). *Proposal:* put the five tick-wiring units in a new no-DB file
`backend/tests/test_own_g2_fuel_night_tick.py` using `test_fix_cold_drain_stage.py`'s `FakeStore`/runner pattern.

**Q9. KIS-11's shape.** §2.5/§2.6 name only `demo_combined_finish.py` and `Demo.tick`. The KIS rows delegate their
judgement to pure `demo_rows.kisN(...)` in `tools/demo_combined_rows.py` with no-DB tests in
`backend/tests/test_demo_combined_finish_rows.py`; row order is pinned there (`:788-794`). *Proposals:*
(a) `demo_rows.kis11(tick_report, story_windows, kisiwa_fuel_findings, kobo_window_count)` pure, raising
`AssertionError` with the failing facts, plus 2-3 no-DB cases (pass; Kisiwa `eligible: false`; a story night at
revision 2); (b) KIS-11 registered right after KIS-9 (end of the K7 block), no change to the pinned K9 order;
(c) `Demo.tick` writes `<work>/last-tick.json` from the last stdout line that parses as a JSON object; if none parses
(tick child failed), it **removes** a stale `last-tick.json` so KIS-11 fails honestly ("no tick report") rather than
reading an older tick; (d) KIS-11 uses the last-written file (the second finish tick).

**Q10. `schedule_inputs` and the test-only clock.** The store has `test_db_clock_override` honoured by `transaction`
and `night_window_on` (`postgres_fuel_balance_store.py:196-202,275-280`). *Proposal:* `schedule_inputs` honours it
too (production composition never passes it; the stage builds the store without it, so P7's DB-time proof is
unaffected). This lets the no-override path and a virtual-instant path share one read.

**Q11. OPEN nights in the stage result.** §2.4 says skip a `WINDOW_OPEN` night but lists `"assess": "OPEN"` in the
night record, and `deferred = len(due) − n`. *Proposal:* an OPEN night is recorded `{"assess": "OPEN", "revision":
None, "state": None, "raise": None}`, no raise call, and **counts as processed** (it used its turn), so
`processed + deferred == len(due)` always holds. (OPEN should be unreachable since `due_nights` uses the same closed
rule with an earlier `known_at`; this is only the accounting.)

**Q12. Test 7 "no further reads (the fake store counts calls)".** "The read stops there" is inside the Postgres
adapter's single `schedule_inputs` call; a fake store cannot observe it. *Proposal:* the no-DB case asserts that for
0 tanks / 2 generators `run_site` makes exactly one store call (`schedule_inputs`), no `transaction`/assess and no
`raise_night`; the Postgres file asserts that a Cold-like Site (no tank) gets `ScheduleInputs` with empty
`reading_nights`, `records` and `latest`.

## Not in G2 (confirming scope)

No migration, no frontend, no HTTP route, no change to the fuel verdict (stays explicit), no change to KIS-3/4/9 or COH,
no `TickLimits` field beyond the two named. G2 and G3a both touch `tools/demo_combined.py` (different functions).
