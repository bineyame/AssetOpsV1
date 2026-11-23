# DD3b handoff (PARTIAL: DD3b1, DD3b2 in_review; DD3b3 built, its `M` commit held for the Architect)

Branch `task/DD3b-mini-plant`, worktree `/opt/assetecon/AssetOpsV1-dd3b`, main merged up to D-DD.149. Packet:
`packet-DD3b.md` (section "DD3b3" and Known Deviations 12-15).

## Done (DD3b3)

- Reorder rule and notes file: `tools/dd3_pure_run.py --restate-notes [--check] --site CODE`, `config/world/fuel-notes.json`.
- `exports.py` reads the notes file (`build_exports(fuel_notes=)`, `read_fuel_notes`); C-DD4 drops mini-grid fuel nodes.
- `--leaves --site CODE`: D-DD.131's table, bridge closure (exit 4 when it does not close).
- `dd_check --pure`: `fuel_tolerances` (from `M`), `judge_candidate_share`, `judge_kisiwa_failure`.
- Tests `simulator/tests/world/test_dd3b3_notes.py` (12, all shown failing first); exports tests restated; plants.
- Full Jul-Oct pure DIR written (strict writer, no bound hit); `dd_check --pure` C-DD20 PASS, C-DD8/C-DD17 FAIL
  (deviations 13-14).

## Next

1. The Architect on deviations 12 (Kisiwa/Mto bridge has no candidate line), 13 (Kisiwa candidate share Aug/Oct),
   14 (C-DD17 with 0 L burned).
2. Then the `M` commit: write `--leaves` output into `M` October `period.actual`, `variance`, `bridge`,
   `fuel_balance`, `findings_expected` (and OR-MG-2, Kisiwa's "95 %" -> peak 41.87 kW / 60, BATTERY_NEAR_RESERVE by the
   product's rule) for all three Sites; a test that `M` equals the tool's output; rev bump; the D-DD.30 chain
   (portfolio totals, `derived-values.json`, `missing-records.json`, mock fixtures); `worked-portfolios.md:74`.
3. Rerun the reach set after the `M` commit, then DD3b's one review.

## Risks

- Every `--leaves` / `--restate-notes --check` is a full span run (70-220 s per Site).
- Notes after 31 Oct are not placed. On 1 Nov Kisiwa holds 1,559 L and Kobo 1,019 L (thresholds 1,250 and 625), so a run to 6 Nov may cross at Kisiwa near its end; not run.
