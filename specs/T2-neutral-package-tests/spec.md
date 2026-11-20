# T2: the neutral packages' tests run at every merge (implementer spec)

Architect (Claude), 2026-11-20. Rev 1, spec handshake step 1. Tools only; non-screen; 0.5 unit. Decision:
`rulings.md` D-T2.1. Raised by DS1b's handshake R8 (`specs/DS1b-canonical-writers/rulings.md`); a precondition of
DS1b's merge. Standard review (W5): a guard, no schema or money.

## 0. Before you start

- **Branch** `task/T2-neutral-package-tests` off `main`; worktree `/opt/assetecon/AssetOpsV1-t2`. No dependency: it can
  start now, on any free lane or as a quick fix.
- **Read:** `tools/check-all.ps1:225-236` (the run-wide `PYTHONPATH`) and `:300-345` (`Add-Guard` and the Python
  guards); `tools/checks/import_root_probe.py`; `tools/select-tests.py:30-60`, `:166-215`; `backend/TESTING.md` §"When
  to run what".
- **Databases:** none. The guard runs pytest with no database URL, so it is not pooled (T1). Never touch ports 5490 or
  8990, the walkthrough DB or Docker.
- **Collisions:** `tools/check-all.ps1` and `tools/select-tests.py` are shared tools. No open lane edits them today;
  `2a`, `DS1b` and `3C1` do not. Merge `main` before review.

## 1. Outcome and why

`simulator/tests` (455 tests, 7 s measured 20 Nov) and `contracts/tests` (6 tests) run in check-all, which builders
run before review and the coordinator runs on `main` after every merge. `select-tests` names them when a change can
affect them. Today no tool runs them, so DS1a's tests, DS1b's parity with the manifest and any contract test are
unguarded after their own slice (DS1b R8).

## 2. What to build

1. **`tools/checks/neutral_tests.py`** (new):
   - It puts this tree's `simulator`, `contracts`, `backend`, `gateway`, `host` and `field` first on `sys.path`
     (repository root = `Path(__file__).resolve().parents[2]`).
   - It asserts that `assetops_simulator` and `assetops_contracts` load from this tree. Otherwise it exits 1 with the
     import-root probe's message form (the D-1 class).
   - It then runs `pytest.main(["simulator/tests", "contracts/tests", "-q", "-p", "no:cacheprovider"])` with the
     repository root as the working directory, and returns its exit code.
   - It removes `ASSETOPS_TEST_DATABASE_URL` from its own environment before pytest starts, so no test can route to a
     database.
   - A run that collects no tests (exit 5) is a failure.
2. **`tools/check-all.ps1`**: one line after the "Fuel wording guard" line:
   `Add-Guard "Neutral package tests (T2)" $Python @("tools/checks/neutral_tests.py")`, with the comment
   `# T2 (DS1b R8): simulator/tests and contracts/tests run on every branch and on main after every merge.` It is
   blocking, not `-Alone`, and has no environment override (the script sets its own path).
3. **`tools/select-tests.py`**: when a changed file matches `simulator/*`, `contracts/*`, `tools/world_history.py` or
   `Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml`:
   - the result gains `"neutral": true`, and the printout adds the line
     `neutral: python tools/checks/neutral_tests.py   (also run by check-all)`;
   - the backend selection does not change;
   - the JSON output gains the `neutral` key, false when no such file changed.
4. **`backend/TESTING.md`** §"When to run what": one bullet saying the neutral packages' tests run in check-all
   (T2), and how to run them alone.

## 3. Tests and proof

- **Planted failures, each reverted and recorded in the packet:**
  - a failing assertion added to a `simulator/tests/world` test fails the guard;
  - a failing assertion added to a `contracts/tests` test fails the guard;
  - with `PYTHONPATH` pointing at main's checkout first, the guard still imports this tree (its own path wins).
- **`select-tests`:**
  - `python3 tools/select-tests.py --files simulator/assetops_simulator/world/history.py --json` shows `neutral: true`;
  - with `--files backend/assetops_backend/perf.py`, it shows `neutral: false`.
  - Add these two cases to `tools/validate-test-selection.py` if that file asserts cases; otherwise record them in the
    packet.
- **Check-all:** fast mode passes on the branch (38 guards), and the new guard's time is in the output, about 10 s.

## 4. Done (questions)

1. Does check-all fail when a simulator or contracts test fails, on a branch and on `main`?
2. Does the guard test this tree's packages, never main's?
3. Does `select-tests` name the neutral tests for a simulator, contracts, world-CLI or manifest change?
4. Is nothing else changed (`git diff --stat main...HEAD`: the four files, the packet and the finish bookkeeping)?

## 5. Out of scope

The Docker merge runner (`run-backend-suite-in-container.*`): check-all already runs at every merge, so the runner
does not change. Moving tests between folders. `gateway/tests` and `host/tests` (they have their own runners).
