# T2: the neutral packages' tests run at every merge (implementer spec)

Architect (Claude), 2026-11-20. **Rev 2**: handshake round 1 is folded in (`rulings.md` "Handshake answers (round
1)", D-T2.2). Tools only, non-screen, **1 unit**. Rev 1 was 0.5; the self-test and the select-tests test added the
rest. Decisions: D-T2.1, D-T2.2. Raised by DS1b's handshake R8, and a precondition of DS1b's merge. Standard review
(W5).

## 0. Before you start

- **Branch** `task/T2-neutral-package-tests` off `main`, after this ruling branch merges; worktree
  `/opt/assetecon/AssetOpsV1-t2`. No dependency.
- **Read:** `tools/check-all.ps1:225-236` and `:300-345`; `tools/checks/import_root_probe.py`;
  `tools/select-tests.py:30-60` and `:166-215`; `simulator/tests/conftest.py`;
  `simulator/tests/world/test_history.py:340-370` (the child process); `backend/TESTING.md` §"When to run what".
- **Databases:** none, and not pooled. `simulator/tests/conftest.py` has no slot or database logic (R7). Never touch
  ports 5490 or 8990, the walkthrough DB or Docker.
- **Collisions:** `tools/check-all.ps1` and `tools/select-tests.py` are shared, but no open lane edits them. Merge
  `main` before review. After T2 merges, DS1b merges `main` and reruns check-all (R12).

## 1. Outcome and why

`simulator/tests` (455 tests) and `contracts/tests` (6) run in check-all against this tree's packages, both
in-process and in every child process they start. Builders run check-all before review, and the coordinator runs it on
`main` after every merge. `select-tests` names the neutral tests when a change can affect them. Today no tool runs
them (DS1b R8).

## 2. What to build

### 2.1 `tools/checks/neutral_tests.py` (new)

- **Dependencies first** (R3). Import `pytest` and `yaml`. If either fails, print
  `FAIL neutral tests: missing module <name>` and return 1.
- **The tree's packages, everywhere** (R1, D-T2.2):
  - `ROOT = Path(__file__).resolve().parents[2]`;
  - `ROOTS` = `simulator`, `contracts`, `backend`, `gateway`, `host`, `field` under `ROOT`, in that order;
  - insert them at the front of `sys.path`;
  - set `os.environ["PYTHONPATH"]` to them joined by `os.pathsep`, followed by any inherited value;
  - remove `ASSETOPS_TEST_DATABASE_URL` from `os.environ`.
- **Import roots.** `assetops_simulator` and `assetops_contracts` must load from inside `ROOT`. Otherwise print
  `FAIL neutral tests: <name> loads from <path>, outside this tree <ROOT>` and return 1.
- **Directories.** `DIRS = ("simulator/tests", "contracts/tests")`. If one is missing, print
  `FAIL neutral tests: missing <dir>` and return 1 (R12).
- **Floors.** `MIN_PASSED = {"simulator/tests": 400, "contracts/tests": 1}`, with the comment "raise, never lower, only
  with a deliberate change" (R4).
- **`run(dirs, floors, cwd) -> int`.** It calls `pytest.main([*dirs, "-q", "-p", "no:cacheprovider"],
  plugins=[counter])` with `cwd` as the working directory. `counter` counts passed call-phase reports per directory,
  using the `nodeid` prefix. Then:
  - exit code 5: print `FAIL neutral tests: no neutral tests collected` and return 1;
  - any other non-zero code: return it unchanged;
  - code 0, but a directory below its floor: print `FAIL neutral tests: <dir> passed <n>, below <floor>` and return 1;
  - otherwise: print `neutral tests: <dir> <n> passed` for each directory and return 0.
- **`main()`**: the checks above, then `run(DIRS, MIN_PASSED, ROOT)`.
- **`--self-test`** (R10). It works in a `tempfile.TemporaryDirectory` and takes under 2 s. It exits 0 only if all
  four cases hold:
  - `run` on a folder with one failing test returns 1;
  - `run` on an empty folder returns 1, through the exit-5 rule;
  - `run` on a folder with one passing test and a floor of 2 returns 1;
  - the import-root message for a fake out-of-tree path has the exact form above.

### 2.2 `tools/checks/test_select_tests_neutral.py` (new; pytest, no database; R9)

It runs `python3 tools/select-tests.py --files <path> --json` as a subprocess and asserts:

| `--files` path | Expected |
|---|---|
| `simulator/assetops_simulator/world/history.py` | `neutral` true |
| `contracts/assetops_contracts/control.py` | `neutral` true |
| `tools/world_history.py` | `neutral` true, and `mode` `full` |
| `backend/assetops_backend/perf.py` | `neutral` false |
| `simulator/README.md` | `neutral` false |

Every output must have the `neutral` key.

### 2.3 `tools/check-all.ps1`

Add three lines after the "Fuel wording guard" line. All three are blocking, and none is `-Alone`:
- `Add-Guard "Neutral package tests (T2)" $Python @("tools/checks/neutral_tests.py")`
- `Add-Guard "Neutral package tests self-test (T2)" $Python @("tools/checks/neutral_tests.py", "--self-test")`
- `Add-Guard "Select-tests neutral cases (T2)" $Python @("-m", "pytest", "tools/checks/test_select_tests_neutral.py", "-q", "-p", "no:cacheprovider")`

Put this comment above them: `# T2 (DS1b R8; D-T2.1, D-T2.2): simulator/tests and contracts/tests on every branch and
on main after every merge, in-process and in child processes.`

### 2.4 `tools/select-tests.py` (R8)

- **Triggers.** `neutral` is true when a changed file matches any of:
  - `simulator/*`
  - `contracts/*`
  - `tools/world_history.py`
  - `tools/checks/neutral_tests.py`
  - `tools/checks/test_select_tests_neutral.py`
  - `Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml`
- **Exclusions.** Files matching `*.md` or `*.egg-info/*` never set it. `*` crosses `/`.
- **JSON output** always has a `neutral` key.
- **Text output** adds the line `neutral: python tools/checks/neutral_tests.py   (also run by check-all)` when
  `neutral` is true.
- **The backend selection does not change.** In particular, `tools/world_history.py` stays `mode: full` and also sets
  `neutral`.

### 2.5 `backend/TESTING.md` §"When to run what"

Add one bullet (R5, R12) saying that:
- the neutral packages' tests run in check-all (T2), with the two folders run whole;
- to run them alone, use `python tools/checks/neutral_tests.py`;
- to run `contracts/tests` alone, use `pytest contracts/tests`;
- a `-k` on `simulator/tests` trips its own session anti-vacuity test;
- a new package folder with its own tests needs a line in the script's `DIRS`.

## 3. Proof (in the packet)

1. **Red on a worktree edit, with main first** (R2).
   - From the worktree, make a one-line edit in `simulator/assetops_simulator/world/history.py` that makes a known
     test fail, including the child-process test of `test_history.py`.
   - Run `PYTHONPATH=/opt/assetecon/AssetOpsV1/simulator:/opt/assetecon/AssetOpsV1/contracts python tools/checks/neutral_tests.py`.
     It must exit non-zero.
   - Revert the edit and run it again. It must exit 0.
   - Record both outputs, and both the in-process and the child-process `assetops_simulator.__file__`. Both must
     resolve inside the worktree.
2. **Same counts** (R6). The combined run's per-directory counts equal those of two separate runs (455 and 6 today).
   State that the test module basenames are unique across the two folders.
3. **check-all red, then green.**
   - Plant a failing assertion in `simulator/tests/world/test_core.py`. Check-all fast must fail, naming "Neutral
     package tests (T2)".
   - Revert it. Check-all must pass.
   - Quote check-all's summary line before T2 and after; it should show three more guards (R11).
4. **Timing.** The guard's seconds from check-all output, once on an idle machine and once under load. About 10 s idle
   is expected (R7).
5. **select-tests.** `test_select_tests_neutral.py` passes.

## 4. Done (questions)

1. Does check-all fail when a simulator or contracts test fails, on a branch and on `main`, including through a
   test's child process?
2. Does the guard test this tree's packages, never main's, even with main first on `PYTHONPATH` (proof 1)?
3. Do a missing folder, an empty collection and a count below a floor each fail, and does the self-test prove it?
4. Does `select-tests` name the neutral tests for every trigger and not for markdown, with its cases guarded in
   check-all?
5. Is nothing else changed? `git diff --stat main...HEAD` should show only the five files of §2, the packet and the
   finish bookkeeping.

## 5. Out of scope

- The Docker merge runner: check-all already runs at every merge.
- Moving tests between folders.
- `gateway/tests` and `host/tests`, which have their own runners.
- A new neutral package folder: when one appears, it needs a line in `DIRS`.
