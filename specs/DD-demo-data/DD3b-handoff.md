# DD3b handoff (run 2 PARTIAL at slice end: DD3b3 built and committed; the reach set found 31 backend failures to re-pin; see below)

Branch `task/DD3b-mini-plant`, worktree `/opt/assetecon/AssetOpsV1-dd3b`, main merged at `98713f07a` (D-DD.150-152,
DD3c; Lakeside-alone site-inputs hash re-pinned `7d582e06...`). Packet: `packet-DD3b.md` (not yet updated for run 2).
Evidence: `/opt/assetecon/evidence/DD3b/` (tests-first log, leaves log, check_manifest log).

## Done (run 2)

- `6ea2b4cae` tests first: 11 new/restated tests in `simulator/tests/world/test_dd3b3_notes.py`, **11 of 11 failed**
  (`dd3b3-r2-tests-first.log`). Run with `PYTHONPATH=$PWD/simulator` (plain pytest imports main's code).
- `fbcb1d741` code: `dd3_pure_run.py` `restated_bridge` adds a missing CANDIDATE_RUNNING / UNEXPLAINED_RESIDUAL line
  (D-DD.150); `--leaves --write|--check` with `config/world/fuel-leaves.json` (the October ledger the test of `M`
  recomputes `october_leaves` from; builder choice, mirrors the notes file). `dd_check.py`: `judge_candidate_share`
  has no bound and fails only on a month without computed minutes (D-DD.151); C-DD17 `declared_draws` (history + `M`),
  `judge_unexplained_month` (>= 0, equals the draw to 0.1 L, tolerance only where burned), `within_tolerance` is the
  one seam the absolute floor joins (D-DD.152). R3 drops OR-MG-2; deviation 15 tidy (exports docstring + comment).
- `fuel-leaves.json` commit (M series 1/3): every bridge closes: Kobo 120.50, Kisiwa 1,759.80, Mto 255.00 (70-75 s each).
- `a46ba3255` (M series 2/3): `M` rev 16.20 leaves, bridges (three fuel lines each), fuel_balance, findings, OR-MG-2,
  GEN-KS-02 70 %, OR-MG-5 2,135.30, portfolio totals (actual 4,430.30, cost 5,257.70, cost variance 2,232.30,
  recorded 4,557.70 / 0.8669); derived-values, missing-records, fixtures.js, index.html regenerated.
  `test_dd3b3_notes.py` 23 passed. Test fix: the standby record is a YAML comment, so the test reads the raw line.

## Next (M series 3/3, then slice end)

1. `history.json`: `world_history.py check` exits 1 (`DS1_CHECK_DIFF meta`; H11 view digest). Regenerate per the
   D-DD.30 chain (view/generate, history/records/export goldens, pinned export digests), as `0aec5ea16` did.
2. Anchored-figure sweep (148 FAIL in `check_manifest-r2.log`): layer4-transformation-design, decision-loop-specification,
   worked-portfolios (incl. :74 fuel balance), economic-metric-and-effect-contracts, domain-and-decision-models,
   walkthroughs, delivery-plan, integration-source-to-canonical-design, go-to-market website/commercial, 6 more;
   then re-base H8/H10/K13 with a dated note. Target: main's count (4531 passed, 5 failed).
3. Pure DIR + `dd_check --pure` (must exit 0): `world_history.py exports`, `site-inputs`, `telemetry --site` x3 into
   `/opt/assetecon/evidence/DD3b/pure-r2`, then `dd_check.py --pure`. If C-DD17's 0.1 L draw equality misses, report
   the measured difference; do not widen it silently.
4. Plants for the new judges (introduce, fail, revert); packet run-2 section with moved figures (above); state entry
   **214** (main holds 210; DD3b1-3 renumbered 211-213 at the merge); spec status in_review; reach set once
   (`--db-lane`, cite `.agent/main-baseline/`); guards.
5. Units: run 2 adds 0.25 u; the `M` work is already its own commit series (1/3, 2/3; 3/3 = the sweep).

## Risks

- The sweep touches ~18 owner-facing docs by hand-typed figures; each must equal the check's value, nothing else.
- Exports for the pure DIR read `M` October; build the DIR after the sweep only if `M` moves again.


## Run 2 end state (supersedes the Next list above)

Done: M series 3/3 (`8ace02f64`), `dd_check --pure` exit 0, plants, packet run-2 section, state entry 214, spec status. check_manifest:
4,557 before history, the same 5 failed as main plus six H5 (packet deviation 17; main measured at `9c38b69ac`).
Reach set ran once at `8ace02f64` (`/opt/assetecon/evidence/DD3b/reach.log`, failures in `reach-failures.txt`): backend 31 failed,
1213 passed; **the host and simulator lines of the script did not report** (read the log; simulator/tests/world alone: 398 passed
at `8ace02f64`, `world-r2c.log`). Next: re-pin the 31 backend tests (hand figures: Kobo 883.00 -> 1,565.50, fuel 1,475.00 ->
792.50, Kisiwa fuel 3,120.00 -> 1,175.20; observer necessary_l FAVOURABLE not RAISED; DDR rehearsal gates), focused reruns only,
then guards (`tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON`, `tools/checks/statement_catalogue.py`,
`tools/check-agent-workflow.ps1`) and update the packet's reach paragraph. Fresh-session context was near its limit.


## Run 3 state (PARTIAL)

Done: reach re-pins (b) in `b9afc1a04`; tank test pins declared sizes only (D-DD.155); packet table + deviation 18 updated.
Open: (1) `git merge main` CONFLICTS (main has DD4b, M rev 16.21): 14 files (.ai/state/data.md, index-3.md, check_manifest.py x4,
manifest yaml, economic-metric md, history.json, fixtures.js, index.html, layer4-transformation-design, worked-portfolios,
golden/history_v1.json x2, test_dd4_thika_incident x2, spec.md, dd_check.py x4). Merge aborted; generated files need the
D-DD.30 regeneration after the text merge. (2) 7 DDR rehearsal tests (see packet table). (3) test_ds4 t12 (a). (4) rerun of the
affected files in one --db-lane call, host/simulator reach lines, guards.

## Run 4: main merged (M rev 16.22)

Done: `git merge main` resolved and regenerated (packet "Merge of main"); check_manifest = main's 6 + six H5; `dd_check --pure`
exit 0; guards pass. Open: 7 DDR rehearsal tests and ds4 t12 (Architect, fuel cost); main's own 7 world failures (packet).



## Fix round 1 (D-DD.164/165, review H1/M1/L1/L2): PARTIAL, blocked on the July fuel statement

Done (commits a66f39395..447a7cbdc; evidence `/opt/assetecon/evidence/DD3b/fix/`):
- D-DD.164: `scope.RUN_WRITTEN` + `period_input` (tests first 11 of 13 failed, `tests-first.log`); guard
  `test_scope_run_written.py` (13 passed; plant Kobo `delivered_kwh` re-seeds). Moved leaves at step 1: Lakeside Jul-Sep
  (all three Sites); cold history `actual.kwh` Mwea 1684/1622/1641 -> 1671/1635/1632, Thika 1690/1737/1784 -> 1700/1731/1809
  (Kirinyaga none); EV none. Cold and EV writer inputs unchanged: `exports --tenant harvest-cold --tenant metro-bus` byte-identical
  before and after (`exports-old/`, `exports-new/`). No STOP.
- Pass: notes restated (Kisiwa 1 Aug / 21 Aug / 16 Sep / 16 Oct; Kobo 26 Sep -> 25 Sep), leaves written, `M` rev 16.23,
  generate again. Step 1 vs step 5: 0 scope digests moved; only `meta.view_digest` and Kisiwa Jul-Sep scaled necessary/candidate
  (805/796/739 -> 802/793/737, 54/51/71 -> 56/53/73), the values D-DD.164 calls "not a loop" (`step1-vs-step5.txt`). Fixed
  point on the final `M`: all six `--check` exit 0 and a third generate is byte-identical (`d92fc9f1...`, `checks.log`).
- fuel-leaves record carries `inputs_sha256` of the run's live inputs; `test_the_fuel_leaves_record_was_run_on_the_live_world`
  (3 of 3 failed first). L1 tank test (plant Kobo 1300 fails). L2 doc 95% -> about 70%.
- D-DD.30 chain, sweep, re-bases; check_manifest 7,875 passed / 12 failed (main's 6 + six H5). `world_history.py check` exit 0.

BLOCKER (Architect): `world_history.py exports` now refuses Lakeside: `STATEMENT_INCOMPLETE 2026-07`
(`statements.figures_from_rows`: a month with revenue and no FUEL expense row is refused). The restated notes put no
Lakeside purchase in July (Kisiwa's 31 Jul note moved to 1 Aug; Kobo Sep/Oct; Mto none), so July has revenue and no
fuel bought. simulator/tests/world: 101 failed, 40 errors, 324 passed (`world-tests.log`, 134 tracebacks are this error).
Probe (statements.py patched to cost 0 for that month, reverted, not committed): 15 failed, 450 passed (7 main-identical +
8 re-pins of the re-seeded world; `world-tests-probe.log`). Not built until ruled: pure DIR, `dd_check --pure`, Kisiwa's
final candidate share (D-DD.165 needs it), re-pins, reach set, packet section, spec status. Next: Architect rules the
July statement (D-DD.163's "fuel bought" makes a month without purchases legitimate), then pure DIR, D-DD.165, re-pins.

## Fix round 2 (D-DD.175/176 + re-pins): PARTIAL, stopped at the context limit

Evidence `/opt/assetecon/evidence/DD3b/fix2/`. Done (commits b1476e387..HEAD):
- `b1476e387` merge main (D-DD.175/176, main simfix). One conflict, `golden/scope_seasons_main.json`; later re-drawn from the tool.
- `461cedfd6` D-DD.175: `statements.ZERO_WHEN_NONE`, `figures_from_rows(..., cost_key)` (fuel 0.00 when no purchase; energy
  absence and cost-without-revenue refused; unknown key `STATEMENT_COST_KEY`); `exports.py` passes `"fuel_cost"`. Four tests
  first in `test_dd2_nodes.py` (`tests-first.log`: 5 failed + 2 errors before the code). Lakeside July statement: fuel 0.00.
- World tests after D-DD.175 (`world-tests-pre-repin.log`): **12 failed, 458 passed**; every one a re-pin of the D-DD.164
  re-seed / restated notes (none main-identical any more: main's simfix fixed its 7). STOP condition not met.
- `4b00f2400` D-DD.176: `history.RUN_DERIVED` (MINI_GRID necessary_l/candidate_l; COLD_CHAIN kwh and EV_DEPOT's five metered
  leaves, because the code shows them: `cold_kwh` reads October kwh, EV leaves are October x weight), `WRITER_READS`, and an
  import-time check `_run_derived_is_never_read_back` (disjoint from PHYSICAL_READS and writer reads). Guard in
  `test_scope_run_written.py`: every run-written key of all nine Sites moves only RUN_DERIVED paths, no physical read moves;
  plant (delivered_kwh scaled by necessary_l) fails it; writers' books unchanged when every derived value is bumped. 27 passed.
- `step1-vs-step2.txt`: generate 1 (M at b3478de5f^, sha 0b09dd25...) vs generate 2 (history.json, d92fc9f1...): only
  `meta.view_digest` and Kisiwa Jul-Sep necessary 805/796/739 -> 802/793/737, candidate 54/51/71 -> 56/53/73; 0 STOP paths.
  Post-merge generate equals the committed history.json byte for byte.
- `e39c370a4` simulator re-pins (dated): export shas, Kisiwa 16 Oct and 903 L, Kobo July 8200 kWh / 3,280.00 / 3,016.30,
  482+19+12, C-DD4 plant 8201/8200, cold and seasons goldens re-drawn. Touched files: 107 passed.
- `138e09045` backend re-pins (b), dated: fixture Kisiwa 903 L 1,173.90; 4b portfolio fuel 1,966.40; 5b Kisiwa 1,696.10 /
  1,761.10 / 1,816.10, portfolio 4,431.60 / 2,136.60, cost and fuel 5,256.40 / 2,006.40 / 2,233.60, 8a 3,261.60 / 1,881.60;
  observer Kisiwa -1486 / 69, band 18.06; dd2_check Kobo July 8200 / 3280 / 3016.30 / 513 L / 641.25; 5b postgres 2,136.60.
  Non-DB reach files (`backend-nodb-1.log` before re-pins: 7 failed, 1172 passed): now only 3b1 t1 and 3b3 t6 fail, both
  pre-existing on main (`dispatch-3.3` vs `dispatch-3.2`).
- Six `--check`s and generate 3: `checks.log` (see the line appended below).

Next (in this order): full `simulator/tests/world` rerun (expect 0 failed); pure DIR + `dd_check --pure` (fix/pure-run.sh with
E=fix2); Kisiwa final candidate share per month three ways (accepted, run 2, final; D-DD.165); check_manifest (= main's 6 + six
H5); reach set ONCE (`tools/heavy-slot.sh --db-lane -- bash reach.sh`, cite `.agent/main-baseline/`; postgres files will show
the remaining DB-side re-pins: observer_postgres, money_leaves_postgres, ddr_rehearsal, ds4 t12); guards; packet section with
July's served standing (D-DD.175: Lakeside July fuel heading MATCHED / NONE_RECORDED_ZERO_STATED, gate opened by Aug/Sep),
final figures; spec in_review; state entry.
