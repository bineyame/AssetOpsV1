# T2 rulings

Architect (Claude), 2026-11-20. Index line: `.ai/decisions/index-rulings-7.md`.

## D-T2.1 The neutral packages' tests are a check-all guard, not a new runner tier

- **Ruling.** `simulator/tests` and `contracts/tests` run as one blocking check-all guard. `select-tests` names them
  for a change that can affect them. The Docker merge runner does not change.
- **Why.**
  - Check-all runs where the gap is: on every branch before review, and on `main` after every merge (RULES §7).
  - The tests need no database and take about 10 s.
  - A new tier in the Docker runner would add an image, a JUnit file and a zero-skip rule for 461 fast tests.
  - It also closes the class for both packages at once, which D-2A.10 (moving `2a`'s tests into `backend/tests`)
    could not do for the simulator.

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
proposed answer is the ruling. The unit grows from 0.5 to 1 unit (two more small files and a self-test).

- **R1 (the defect): adopted.**
  - The script sets `os.environ["PYTHONPATH"]` to the tree's six roots, followed by any inherited value, before
    `pytest.main`. It also inserts them on `sys.path`. Child processes then import the tree:
    `test_history.py:362` starts a child with `env=os.environ.copy()`.
  - The packet records both the in-process and a child's `assetops_simulator.__file__`, each resolving inside the tree.
  - **New ruling D-T2.2.**
- **R2: adopted. A proof that can fail.**
  - From the worktree, the guard is run with `PYTHONPATH=/opt/assetecon/AssetOpsV1/simulator:/opt/assetecon/AssetOpsV1/contracts`
    first.
  - A deliberate one-line edit in the worktree's `simulator/assetops_simulator/world/history.py` makes a known test
    fail, including through the child test. The guard must go red. The edit is then reverted.
  - The self-test (R10) checks the message form `FAIL neutral tests: <name> loads from <path>, outside this tree
    <root>` and exit code 1.
- **R3: adopted.**
  - The script uses whichever interpreter check-all passes, and needs nothing from check-all's `PYTHONPATH`.
  - Its first lines import `pytest` and `yaml`. A missing module gives exit 1 and `FAIL neutral tests: missing module
    <name>`.
- **R4: adopted.**
  - pytest's code is returned unless it is 0. Code 5 returns 1 with `FAIL neutral tests: no neutral tests collected`.
  - Each of `simulator/tests` and `contracts/tests` must exist. Otherwise the result is exit 1 and `FAIL neutral tests:
    missing <dir>`.
  - Floors are named constants: `MIN_PASSED = {"simulator/tests": 400, "contracts/tests": 1}`, with a comment to raise
    them, never lower them, and only with a deliberate change.
  - Passed tests are counted per directory by a small plugin object (`pytest_runtest_logreport`, `when == "call"` and
    passed). A count below a floor gives exit 1 and `FAIL neutral tests: <dir> passed <n>, below <floor>`.
- **R5: adopted.** The `TESTING.md` bullet says the guard runs the two folders whole, and that `contracts/tests` alone
  is `pytest contracts/tests`. A `-k` on `simulator/tests` trips its own session anti-vacuity test, by design.
- **R6: adopted.** The packet shows the combined run's per-directory counts equal the two separate runs' (455 and 6
  today) and states that the test-module basenames are unique across the two folders.
- **R7: confirmed and adopted.**
  - `simulator/tests/conftest.py` has no slot or database logic at all (checked 20 Nov), so no tripwire can fire.
  - The guard is neither `-Alone` nor pooled.
  - The packet records its seconds from check-all output on an idle and a loaded machine. The spec says "about 10 s
    idle", including two CLI-subprocess tests and a 1 s-timeout child.
  - No `-Jobs` change: a 10 s guard is not the longest in the pool (dependency-direction takes about 39 s).
- **R8: adopted.**
  - The triggers are `simulator/*`, `contracts/*`, `tools/world_history.py`, `tools/checks/neutral_tests.py`,
    `tools/checks/test_select_tests_neutral.py` and the pack manifest. `*.md` files and anything under
    `*.egg-info/` are excluded.
  - `fnmatch` `*` crosses `/`, as intended.
  - `tools/world_history.py` keeps `mode: full` and adds `neutral: true`. That is what "the backend selection does not
    change" means; do not "fix" it.
- **R9: adopted.**
  - A new file, `tools/checks/test_select_tests_neutral.py` (pytest, no database), registered in check-all.
  - Its cases:
    - a simulator path gives true;
    - a contracts path gives true;
    - `tools/world_history.py` gives true and `mode: full`;
    - `backend/assetops_backend/perf.py` gives false;
    - `simulator/README.md` gives false;
    - the JSON always has the `neutral` key.
- **R10: adopted.**
  - `neutral_tests.py --self-test` is registered as "Neutral package tests self-test (T2)".
  - It runs the script's runner function on a temporary directory holding one failing test and requires 1, and on an
    empty directory and requires 1 (the exit-5 rule).
  - It checks the import-root message form.
  - It runs in under 2 s.
  - The packet also records one full check-all red run naming the guard.
- **R11: adopted.** The run-time count rises by three: the guard, its self-test and the `select-tests` test. The packet
  quotes check-all's own summary line before and after, not a number from the spec.
- **R12: adopted.**
  - `TESTING.md` and spec §5 say that a new package folder with its own tests needs a line in the script's directory
    list.
  - The script fails when either folder is missing (R4).
  - After T2 merges, DS1b's branch merges `main` and reruns check-all before its review and merge.

**Evidence already merged (the coordinator's question).** No re-check is needed beyond T2's first run on `main`.
- DS1a, DS1p and `2a` were run with the lane rules' `export PYTHONPATH=<worktree roots>`, in their specs' commands.
  The `test_history.py:362` child inherits that environment, so it imported the worktree.
- `test_cli.py` drops `PYTHONPATH`, but the CLI inserts its own tree's `simulator` (DS1b P1 adds `contracts`).
- `2a`'s tests import no simulator.
- The only gap would be a run that set `sys.path` alone, and none of the specs did that.
- That code is now on `main`, so T2's first check-all on `main` reruns all 461 tests against it. The coordinator
  records that run's summary line as the re-check.

**Open after round 1:** none.

## D-T2.2 The guard sets `PYTHONPATH` for its children

- **Ruling.** As R1.
- **Why.** A path fix that reaches only the parent process leaves the D-1 class open for every test that starts a
  child.
