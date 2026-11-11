# KD-COVERAGE packet (D-E5.40)

Branch `task/KD-COVERAGE`, tool-only (no product code). `tools/demo_combined_finish.py`:
- `KNOWN_DEFECTS = {"CO-6": "D-E5.38", "WK-GAP": "D-E5.38"}`, `KnownDefect` exception.
- CO-6: only the signature "Kobo coverage state not PARTIAL and no gaps" skips the coverage block (state, gaps,
  requested/checked, text, Portfolio status, finding listed); every other CO-6 assertion still runs, then
  `KnownDefect` is raised. WK-GAP: only `gaps == []` while a missed day exists is deferred; all other assertions run.
- `run`: row status `known_defect` (check.json carries `known_defect`, error text, read); not in `failed`, exit 0;
  summary line prints "KNOWN DEFECT D-E5.38 (DATA-12 fixes it)" and the count; a listed row that passes prints
  "known defect no longer reproduces; remove the marker". An unlisted row raising KnownDefect fails.
- add-dates: `finish_check` uses the exit code, so the marker gives "PASS"; `failed_rows` ignores `known_defect`.

Tests (`backend/tests/test_demo_combined_finish_rows.py`, 2 new): both signatures reported; wrong gap day, CO-6 with
board mismatch and PARTIAL with wrong gaps still fail; `run` exit codes and check.json.
Run: finish_rows + test_own_g1_add_dates: 124 passed. Not run: the sheet's one-off CO-6-after-492 read on client6
(forbidden here); the deferred-block design runs those assertions on every build instead.

## Frozen tree
`add_dates` -> `finish_check` runs `self.tree / "tools" / "demo_combined_finish.py"` (cwd tree/backend/tests), where
`self.tree = work/"tree"` (`tools/demo_combined.py:719,1455`). So the frozen snapshot's finish script runs, not the
checkout's. Same for the `demo_combined.py` that parses check.json: that is the checkout's `failed_rows` (reads
status "fail" only). For Wednesday without replacing the tree: the snapshot's `tools/demo_combined_finish.py` must
carry the marker (copy this one file over `var/polish_client6/tree/tools/`, an owner decision against R6.3), or
accept FAIL CO-6,WK-GAP from add-dates. The checkout alone changes nothing.
