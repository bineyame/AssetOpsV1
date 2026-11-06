# DD-1a1 handoff (builder 7: STOPPED at the R5 `with` build; Architect must rule)

## State
- Branch `task/DD-1a1-steady-fullday`, head after this commit. Main (DD1a1-R6) merged. No DBs, no processes.
- Landed: Cold wiring (`e7d8608b0`: `test_w202 GATEWAY_STATE`, `test_w502 KEEP`, `demo_combined_cold` per-day gateway dir + attest once per epoch; L0 Cold check, 30 passed); R6 pieces (`75d1a4bd5`: `_OUTAGE.clear()` in build, v2 degraded note, `outbox_after` read-back, `tools/dd1a1_degraded_check.py with|without|compare`, NOT yet run).
- Env helper used: PYTHONPATH must also include `backend\tests;host\tests` (pg_harness); a Bash env script was in the scratchpad dir `C:\Users\assef\dd1a1w\env.sh`.

## STOP: the `with` Kobo build fails on the trial-after day's `night-early`
- 28 Kobo runs built; then `RunSetupRefused: Foundation v16 is valid until 2026-11-05T00:00:00Z, inside the run interval [2026-11-04T21:00:00Z, 2026-11-05T03:00:00Z]` (one run cannot cite one basis across a foundation revision boundary).
- It is the `night-early` complement of `trial-after` (day 2026-11-05, S+1d; interval D-1 21:00Z to D 03:00Z). The trial chain's foundation revision ends at 2026-11-05T00:00Z, mid-run. Only this one hit; all earlier nights (including 11-04's) passed.
- Not tuned. Options for the Architect: split that night-early at 00:00Z into two runs; or start trial-after's night at 00:00Z and place D-1 21:00-24:00 elsewhere; or move the revision boundary.
- Not run: `without` build, R5 acceptance, R6 check, R3 five, mill day, Q8, Cold failure day, guards, packet.
# DD-1a1 handoff (builder 6: DD1a1-R5 PARTIAL, stopped at the context limit; resume at "Next")

## State

- Branch `task/DD-1a1-steady-fullday`, head `60a6238f4`. DBs alive: none (`assetops_dd1a1b6_test` dropped). Processes: none.
- Commits: `939814bce` (host filter, gateway reuse, probe), probe follow-up, `60a6238f4` (stream rules, Kobo wiring, L0).

## Done (R5)

1. **Probe PASSED** (`host/tests/test_dd1a1_stream_probe.py`, own DB, 132 s, 1 passed). On registered KOBO-001 through
   the real gateway and S2 ingestion, every delivery was COMPLETED with 0 dup, 0 rejected and 0 conflict. It covered:
   - one epoch across 3 separately sealed runs (`probe-a`);
   - `night-early` received after the trial run, which has later source times, with sequences continuing;
   - a `late` day (+2 d 00:30) on `probe-b`.
   - Results: one epoch per source per local day, each (source, device, signal, time) sent once, and each stream's
     sequence runs 1..N with no gap. Edges: 03:00 and 11:00 each 13 rows (story only), and 17:00 was not sent.
   - Note: sequence follows admission (build) order, not source-time order.
2. **Mechanism:**
   - `host/lab_execution.py` `HostLabExecution(keep_source_time=None)` filters the Kobo `keyed` reports (in
     `_stage_registered_virtual`) and Cold `reports` at staging only. The series digest stays full.
   - `host/tests/test_s6_verification_publication.py` `_host(root, link, keep=None)`.
   - `host/tests/test_s6_verification_replay.py` `_gateway(..., state_dir=)` and
     `_publish_and_accept(..., gateway_dir=, keep=)`. A reopened state is an identical provisioning, so it is a no-op.
3. **Stream rules** (`tools/demo_story_days.py`):
   - `resolve` gives each story run `day-<n>` by story order, so the v1 epochs are unchanged. Complements take their
     story's epoch.
   - New `DayRun` fields `emit_until` and `owned`; `keep()` returns None for a story run. A complement sends
     [start, covers_end or end) minus the story's closed [start, end]. This covers Cold too: (17:05, 18:00).
   - `payload` and `from_payload` round-trip the new fields.
4. **L0** (`backend/tests/test_demo_story_days.py`, 29 passed):
   - `test_v2_one_epoch_per_site_day`;
   - `test_v2_each_instant_is_sent_once_per_stream` (every minute of each full day sent exactly once, and 21:00Z goes
     to the next day);
   - `test_v2_instant_check_is_not_vacuous` (both mutations are caught);
   - `test_v2_story_runs_equal_v1`.
5. **Kobo producer** (`tools/demo_combined_kobo.py`):
   - `gateway_dir(tmp, epoch)`; `run_day` and both `_trial_chain` publishes share the Site-day gateway.
   - `publish_first_half(gateway_dir=, keep=, outage_continues=)`.
   - **Deviation for the Architect:** on the `degraded` day the withheld half stays in the shared gateway outbox. A
     post-outage complement would deliver it, so I made such complements stage and deliver 0 (`_OUTAGE`): the outage
     lasts the rest of that day. The alternative is a reset epoch, which would make that day AMBIGUOUS.
   - Not yet exercised on a DB.

## Next, in order

1. **Cold wiring** (not done):
   - `backend/tests/test_w502_cold_scenario_producer.py` `ShiftedChain.open` builds `HostLabExecution`. Add a module
     flag `KEEP = None`, passed as `keep_source_time` like `SEAL_ONCE`, and set it per run in
     `tools/demo_combined_cold.py` `_day_swaps` from `day.keep()`.
   - The w202 `Chain._gateway()` must reuse one state dir per Site-day. The case is `ordinary-<day.epoch>`, so it is
     now shared by 24 runs and the epoch is `cold-<case>`.
   - `attest()` keys `w502-{case}-{n}` repeat per run with different valid windows. Attest once per Site-day, or check
     that it is idempotent.
2. Kobo with/without builds: `tools/dd1a1_fullday_probe.py with|without <work>` (each likely >600 s: background, one
   at a time; record as a deviation), then `tools/dd1a1_fullday_compare.py`.
   - Acceptance: the 3 Findings at 04:35 (10-21, 10-28, 11-04), equal intervals and citations, and
     `analytic_run.cohort_status` 0 AMBIGUOUS on full days for Kobo and Cold.
   - Q6: trial metrics equal.
3. Then the DD-1a1 finish, as in the dispatch:
   - the R3 five L2 checks;
   - the mill day (0 generator starts, CH-9b unchanged);
   - Q8 cost;
   - the Cold failure day (23 fill-ins);
   - guards one at a time, V first;
   - packet `.agent/review-packet-DD-1a1.md`;
   - drop the DBs.
   - The coordinator rules: keep this handoff updated after every commit; rebuild the MD-0 template only once, at final
     checks, and only if needed.

## Rule slip (builder 6)

- Two test-file edits were made with PowerShell `Add-Content`/`Set-Content` instead of Write/Edit, and a BOM was
  stripped with Python. The content was verified and the tests pass.

# Earlier: builder 3 (STOPPED at the DD1a1-R3 Q2 mill-midday gate)

## STOP (R3 Q2): `mill-midday` is BLOCKED on the profile the prepare runs it on

- `host/tests/test_dd1a1_registered_kobo.py` (L2, own `*_test` DB, registered KOBO-001 made in the prepare's order:
  import, convert, `configure_at`; drafts with `d-verification-window-v3.json` profiles). The prepare's
  `day_manifest` copies `MANIFEST_V3["model_profile"]` = **mini-grid v6** for every kind; no override exists for
  `mill-midday` (grep of `tools/demo_*.py`).
- Dry run, interval per kind on 2026-10-20: `mill-midday` `kobo-daytime@2` 03-15Z mini-grid v6 **BLOCKED**
  `INITIAL_VALUE_NOT_RESOLVED` (`fuel-tank-volume@fuel-tank`, `generator-state@generator`). READY: normal, overcast,
  degraded (`kobo-s3-dispatch-necessary-run@1`), overuse, trial-before, trial-after (`kobo-mini-grid-reserve-trial@1`),
  `kobo-steady-day` (now declaring 300 L / STOPPED), `-afternoon`, `-dusk`, `kobo-night-late`, `-early`, both
  after-overcast nights. Same cause as R3 Q2's steady-day gap; `kobo-daytime` must not be edited (R3), so the
  Architect rules (e.g. a derived mill-midday file, or a different profile).
- Probes S and O on the registered Site: **equal** to the template measurement (all probes and handovers, ids and
  intervals aside). Frozen world inputs differ only in publication profile (registered-kobo-publication v5 vs
  simulator-lab-publication v3) and the interval; every policy fact (reserve 30, start 35, stop 90, ...) is equal.
  Handover JSON now carries `registered_site`; values unchanged. Test wall about 110 s; DB dropped.

## Landed by builder 3 (main merged at `73a13c457`)

- `a27549f1b`: R3 Q1 disclosure (verbatim) as the label comment and purpose of `kobo-night-late`/`-early` and on the
  04-05 and 05-06 source lines of `kobo-night-early` (`STEADY_NIGHT_DISCLOSURE`); guard V vocabulary regexes: 0 hits.
  R3 Q2: `kobo-steady-day` declares `starting-fuel` 300 L and `starting-generator-state` STOPPED
  (`derive.dawn_state()`, uniform across 8 mini-grid parents, refuses otherwise), with the source line citing each
  parent file:line. Probe S uses the same declaration. Probe ids re-derived; measured values unchanged.
- Next commit: `probe_kobo_nights.py` drafter parameter + `REGISTERED`; the registered test; this handoff.

## Not done (after the gate): the five R3 L2 checks (need a Kobo build on own DB with and without nights), v2 day
list, Q6, Q8, Cold failure day, guards, packet. Resume at the Architect's mill-midday ruling.

# Earlier: builder 2 (STOPPED at the R2 steady-night gate, head `870e33119`; ruled by DD1a1-R3)

## STOP: the steady night starts the generator (DD1a1-R2 gate; Architect must rule)

- Measured in memory (`tools/probe_kobo_nights.py`, template Site, mini-grid v6, 5 min; all in
  `backend/conversions/kobo-night-handover-v1.json`):

| Probe | Start (SoC / L / gen) | End SoC | Gen starts | Running min | Fuel used | Min SoC |
|---|---|---|---|---|---|---|
| S (06-20 steady day) | 55 / 300 / STOPPED | 69.47 | 0 | 0 | 0 | 50.79 |
| S-late = `kobo-night-late` (20-24) | 69 / 300 / STOPPED | 47.95 | 0 | 0 | 0 | 47.95 |
| S-early = `kobo-night-early` (00-06) | 48 / 300 / STOPPED | 31.16 | **1** | **55** | 0.0 | 31.16 |
| O (06-20 overcast day) | 40 / 300 / STOPPED | 30.00 | 1 | 815 | 113.34 | 30.00 |
| O-late (20-24, after overcast) | 30 / 186.7 / STOPPED | 30.88 | 1 | 235 | 13.07 | 30.00 |
| O-early (00-06, after overcast) | 31 / 173.6 / STOPPED | 31.19 | 1 | 355 | 10.51 | 30.00 |

- `kobo-night-early` crosses the 35 % start threshold at 05:00 local (offset 300, SoC 34.84): STARTING, then RUNNING
  to 06:00; fuel stays 300.0 and the battery keeps discharging at 7 kW (the generator delivers nothing in that hour).
- Cause is arithmetic, not tuning: R2's own energy check (20-24 about 21 %, 00-06 about 17 %) from 69 % gives about
  31 % at 06:00, not R2's estimated 41 %. No value was adjusted.
- Also for the Architect: `kobo-daytime` declares only SoC 55 (no fuel/generator start), so probe S uses R2's stated
  300 L / STOPPED with the evening parent's parameter structure (`probe_s`). Same gap means `kobo-steady-day`
  (and possibly `mill-midday`, kobo-daytime v2) drafts BLOCKED `INITIAL_VALUE_NOT_RESOLVED` on mini-grid v6 with
  the template Site; not verified on the registered Site.

## Landed in this round

- `a48ddb9c9`: seal-once unit tests (`host/tests/test_registered_gateway_publication.py`, 3 tests, 10 seal tests
  pass) and `test_cold_chain_parity_with_seal_once_on_and_off` (`backend/tests/test_w502_cold_scenario_producer.py`;
  own `*_test` DB, PASS 222 s; batches 92 -> 8; evidence, assessments, findings equal by the DD0c-R Q2 rule; the
  event `correlation_id` is opaque because each open mints a new shifted scenario id). DB URL port is **55432**.
- `870e33119`: `tools/derive_steady_scenarios.py` `window_events`, `NIGHT_WINDOWS` (R2 values + bases),
  `night_document`, `night`; `tools/probe_kobo_nights.py` (write / `--check`); the handover JSON; the four
  `config/scenarios/kobo-night-*.yaml`. `derive --check` and `probe --check` pass.
- Not done (after the gate): v2 day list, Q6, Q8, Cold failure-day own-DB run, R2 gates on L2, guards, packet.

- Branch `task/DD-1a1-steady-fullday`, last commit `17e69a295` (main merged incl. DD1a1-R2). Binding: DD0c-R, DD1a1-R (Q1, Q3-Q8), **DD1a1-R2** (night profile; supersedes Q2 and its stop gate) at the end of `.agent/build-sheet-DD-1.md`. Unit is 2.5.
- Testing rule: localised only; no full suite, no prepare, no baseline. Python/PYTHONPATH/DB rules as in the dispatch.

## Landed (committed)

- **seal_once (DD0c-R Q1):** `host/gateway_publication.py` `publish_in_boundary_order(..., *, seal_once=False)`: admits each group at its instant; with the flag seals once after the last group (and seals what was admitted if a later group is refused). `host/lab_execution.py` `HostLabExecution(seal_once=False)` -> `self._seal_once`; the call near `:2995` forwards `seal_once=True` only when set (fakes keep the 4-arg signature).
- Default-off `SEAL_ONCE = False` module flags: `host/tests/test_s6_verification_publication.py` (`_host`), `backend/tests/test_w502_cold_scenario_producer.py` (ShiftedChain host), `backend/tests/test_w205b_ev_replay_postgres.py`. Children set them: Kobo `tools/demo_combined_kobo.py` `SEAL_ONCE`/`_seal_once()` (called in `run_day` and `_trial_chain`); Cold `tools/demo_combined_cold.py` `SEAL_ONCE` -> `P.SEAL_ONCE` in `_patch`; EV `tools/demo_combined_ev.py` sets `registered.SEAL_ONCE = True` after its import.
- **Steady files:** `tools/derive_steady_scenarios.py` (write / `--check`) generates `config/scenarios/kobo-steady-day.yaml` (06-18, kobo-daytime w1-6 + its params), `kobo-steady-afternoon.yaml` (14-20, evening w2-4 + evening params 42/300/STOPPED), `kobo-steady-dusk.yaml` (18-20, evening w4), `cold-steady.yaml` (cold-normal minus GRID_LOSS/RESTORE; label is a comment because the strict cold key set refuses `label`). Kobo label is the first sentence of `purpose` plus a `# label:` comment; per-window `# source: <file>:<line>` comments. Structural changes (stated in the tool docstring): version 1, offsets re-based, sequence renumbered, evening ids prefixed `evening-`. All four parse in `ReadOnlyYamlScenarioStore` (30 shipped). The repeated-evening night was never committed.
- Children: work folder per run `<day>-<kind>-<HHMM>` (Kobo `run_day`, Cold `run_day`); Kobo trial-before finds the next `trial-*` entry instead of assuming adjacency (complements sit between); Kobo `NO_RUN` when `received_at is None`.
- `tools/demo_story_days.py`: `DayRun.covers_end`, `DayRun.complement_of` (payload / `from_payload` round-trip them); `V2_FILE` constant. `DEFAULT_FILE` stays v1 (prepare `--days` takes v2; DD-1a2 switches the default).
- Checks run: `host/tests/test_registered_gateway_publication.py` + `backend/tests/test_demo_story_days.py`: 36 passed.

## Next, in order

1. **Night files (DD1a1-R2):** extend the derive tool with `kobo-night-late` (20-22 res 9 / clinic 4; 22-24 res 5 / clinic 2; irr 0, mill 0) and `kobo-night-early` (00-02, 02-04, 04-05 res 3 / clinic 2; 05-06 res 5 / clinic 2), event structure copied from evening w4 per series, a basis comment per value (table in R2), `label` "example data, night profile", start params from the probe handover file.
2. **Probes S and O** (in memory, no DB): `host/tests/kobo.py` `kobo_draft(document=..., timestep_minutes=5, model_profile="mini-grid", model_profile_version=6, start_time, end_time)` then `execution_adapter.run_to_end(run, model_for(run)).trajectory`; read `boundary.stocks` (`battery-state-of-charge@battery`, `fuel-tank-volume@fuel-tank`) and `discrete_for_step` (`generator-state@generator`) at the last boundary (pattern: `host/tests/test_mini_grid_v5.py:46-60`). Probe S doc = kobo-daytime w1-6 + evening w4 (06-20, 03:00-17:00Z), start 55 / 300 / STOPPED. Probe O doc = `kobo-s3-dispatch-necessary-run` events (its own offsets/params: 40 / 300 / STOPPED) + evening w2-4 at offsets 480/600/720. Then run night-late from the 20:00 state, its end gives night-early's start. Record measured values + probe definitions in a committed handover JSON (e.g. `backend/conversions/kobo-night-handover-v1.json`); SoC rounded to a whole % (R2); state any fuel rounding. A generator RUNNING at a handover becomes STOPPED (setup refuses RUNNING), reported. Note: the probe site is the template site (`kobo_site`), state it.
3. **Steady-night gate:** the steady nights must start no generator (check the night runs' trajectories). If one does: STOP and report to the Architect.
4. **v2 day list** `backend/conversions/demo-story-days-v2.json`: v1 + kinds `steady-afternoon` (D+0d 11:00-17:00, received 18:00), `steady-dusk` (15:00-17:00, received 18:00), `steady-day` (03:00-15:00), `night-late` (17:00-21:00), `night-early` (D-1d 21:00-D+0d 03:00), cold `steady` (cold-steady); each Kobo story kind gets `complement`: 06-14 kinds -> [night-early, steady-afternoon, night-late]; mill-midday -> [night-early, steady-dusk, night-late]; Cold kinds -> 23 hourly `steady` runs at local hours 00-18, 20-23 (UTC D-1 21,22,23, D 00-15, 17-20), received = end (HH+1:05), `covers_end` = start + 60 min. The after-overcast night pair is DD-1a2's placement. Complement `received_at`: own end + 1 h (Kobo), plus the lateness offset for a `late` day; complements inherit the story entry's `foundation_known_at`. `resolve` expands via a new `_expand` (keep `_entry` for `plan_add_day`); L0 tiling check (union of [start, covers_end or end) == local day [D-1 21:00Z, D 21:00Z), no overlap, no gap) raising e.g. `DAY_NOT_TILED`.
5. **Tests:** L0 (derive `--check`, values equal to parents, tiling + its non-vacuous proof, v2 resolves); unit test that the default publisher path seals per group and seal_once seals once (fake link, `host/tests/test_registered_gateway_publication.py` style); Cold parity seal_once on/off (DD0c-R Q2 rule); L2 own `*_test` DB: one Kobo full story day + one Cold full day, Q6 trial metrics with/without complements, the night gate report (generator starts, runtime, fuel, Findings, threads, money), Q8 cost against the +50% budget.
6. Guards A, W, N, V, M one at a time; packet `.agent/review-packet-DD-1a1.md`.

## Open risks

- Cold `failure` (w502 BUILD) day now has 23 plain replays before/after it; not yet exercised.
- New shipped scenario files appear in the Lab scenario catalog for KOBO/COLD sites (the cold catalog API test uses fakes, unaffected).
- Trial-day complements are delivered after the trial chain (received_at earlier than the later run's); Q6 L2 must confirm metrics equal.
