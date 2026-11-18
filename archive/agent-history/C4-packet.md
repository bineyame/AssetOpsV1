# E4-C4 packet: Performance comparison only on change (D-E4.8)

Branch `task/E4-C4-performance-on-change`, cut from main c0362bdcd (includes C2). Tool only.

## Delivered
- `tools/demo_combined.py`: `read_marks`, `write_marks` (temp file in the same folder, then `os.replace`), pure
  `performance_due(site, mark, marks, report_dir)`; `Demo.read_site_mark` (one short read-only psycopg connection;
  tenant `demo` plus Site, `count(*)` of `chain_input_change` with the `_WATERMARK` predicate for that one Site);
  `performance_and_prebuild` reads the mark before the run, skips with `performance: skipped (no change since mark N)`,
  records the mark only after exit 0. Marks live in `<work>/performance-marks.json`. Prebuild still runs every tick.
- Report dir checked: `<tree>/var/evidence/migration-performance/<site code lower-case>` (the child's
  `EVIDENCE_STORE_ROOT` is the tree's `var/evidence`).
- New `backend/tests/test_e4_performance_on_change.py` (6 tests, no DB).

## Tests (venv python, one file at a time)
new 6 passed; finish_rows 63; mill 15; own_g1_add_dates 45; ch5c_env_parity 3; prebuilt_routes_generator 10;
prebuilt_routes_source 5. Non-vacuity: with `tools/demo_combined.py` reverted to main, all 6 new tests failed; restored.

## Changed assertions / fixtures in existing tests
Four existing tests used fakes that now meet the mark read; each gets a stub `read_site_mark` returning None (no
mark: run is due, behaviour unchanged): `test_demo_combined_finish_rows` (also `tmp_path`, `work`, `tree`),
`test_demo_combined_mill` (`Recording`), `test_ch5c_env_parity`, `test_e4_prebuilt_routes_generator`. No assertion
values changed.

## Deviations
- An unreadable mark (None: no DB row for the Site) is treated as due and records nothing (safe direction).
- A `.json` file glob decides "report present" (any file in the Site's folder).
