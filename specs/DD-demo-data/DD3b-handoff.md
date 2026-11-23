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
