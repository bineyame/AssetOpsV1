# T2 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Reviewer (Claude), 2026-11-20, after checking spec §2-§3 against `tools/check-all.ps1`, `tools/select-tests.py`,
`backend/TESTING.md`, `simulator/tests` and `contracts/tests` on `main` (the venv probe run from `main` and from
`AssetOpsV1-2a`). Marked **(done)** where the answer changes what counts as done.

**R1 (done). `sys.path` does not reach the tests' child processes; the guard can still test main's simulator.**
Spec §2.1 puts the tree's packages first on `sys.path`. Two tests start a Python child with `sys.executable`:
`simulator/tests/world/test_history.py:362` (`-c "from assetops_simulator.world.history import ..."`,
`env=os.environ.copy()`) and `test_cli.py:15-19` (runs `tools/world_history.py`, which inserts its own tree's
`simulator`, so that one is safe). I checked that a parent with `sys.path.insert(0, <worktree>/simulator)` imports the
worktree, while its `sys.executable -c "import assetops_simulator"` child prints `/opt/assetecon/AssetOpsV1/simulator/...`
(main, through the venv editable install). The `test_history.py:362` child therefore exercises main's history generator
in a worktree, silently: the exact D-1 class the guard exists to close, and the §3 planted-failure proofs (which edit
a test, not the child's code) would not catch it. check-all sets `PYTHONPATH` for the same reason (`check-all.ps1:229`).
Proposed: the script also sets `os.environ["PYTHONPATH"]` to the tree's six roots (then any inherited value) before
`pytest.main`, so children inherit it, as well as `sys.path`. Add to §3: a planted-main proof for a child process
(set `PYTHONPATH` to main's `simulator` first and a one-line `print(assetops_simulator.__file__)` check through a
child, or make the planted failing assertion sit in `generate_history` in the worktree and run it under the
`test_history.py:362` test); and record in the packet that the guard's in-process and child imports both resolve in the tree.

**R2 (done). The "planted failure with PYTHONPATH at main first" proof is not specific enough to be checked.**
§3 bullet 3 says the guard "still imports this tree". Say how it is recorded: run
`PYTHONPATH=/opt/assetecon/AssetOpsV1/simulator:/opt/assetecon/AssetOpsV1/contracts python tools/checks/neutral_tests.py`
from the worktree, with a one-line change in the worktree's `simulator/assetops_simulator/` that makes a known test
fail; the guard must go red. Passing alone proves nothing, since main and the tree are identical until the branch
changes the packages. Proposed: replace bullet 3 with that red-on-worktree-edit run, plus a unit check that the
assertion message form matches `import_root_probe.py` (exit 1, text beginning `FAIL ` and naming the path).

**R3. Which `python` runs the guard, and "from any worktree".**
check-all passes `$Python`, which is this tree's `.venv` if present, else main's shared venv, and puts only
`backend` and `contracts` on `PYTHONPATH` (`check-all.ps1:229`). The simulator comes from main's editable install
unless the script overrides it; the script is the only thing that makes it the tree's. That is fine, but the spec
should say so, and that the script needs no `PYTHONPATH` from check-all. Also: the venv has `pytest`, and `yaml`
(used by `test_cli.py:62`, `tools/world_history.py:29`)? Proposed: the script's first lines import `pytest` and
`yaml` and exit 1 with a plain message naming the missing module, so a missing dependency is a failure and not a
collection error that reads like a test failure.

**R4 (done). Exit-code handling is incomplete.**
§2.1 makes exit 5 a failure; but exit codes 2, 3 and 4 (interrupted, internal error, usage) and any exception
(collection error is exit 2) are also red already because pytest returns nonzero. State: "return pytest's code
unless it is 0; code 5 returns 1 with the message `no neutral tests collected`." Also require a floor, because an
empty-but-not-zero collection can hide a deleted folder or a `-k`: assert at least 100 simulator tests and 1
contracts test ran (read through a collect-only plugin or `pytest.main` plugin object), or at least assert both
directories exist. Proposed: both directories must exist and the run must report at least 400 passed (today 455+6);
the floor is a named constant in the script, with a comment saying to raise it, never lower it, with a deliberate
change. If the Architect prefers no count floor, require that each directory contributes at least one test.

**R5. The simulator suite's session guard depends on running the whole simulator folder.**
`simulator/tests/conftest.py` ends with `test_every_execution_failure_kind_was_reached` (anti-vacuity over all
failure kinds). That is fine for the guard (it runs the whole folder), but a developer running the contracts tests
alone, or a `-k`, will see it fail. Not a build question; state in the TESTING.md bullet that the guard runs the two
folders whole and how to run the contracts tests alone (`pytest contracts/tests`). Proposed: add that sentence to §2.4.

**R6 (done). `pytest.main` with two folders: rootdir, conftest and module-name collisions.**
`simulator/tests` has `conftest.py` and `world/__init__.py` but no `tests/__init__.py`, so with `rootdir` mode
`prepend` the basenames of the test modules in `simulator/tests` and `contracts/tests` must stay unique across the
two folders in one process (a duplicate basename is a collection error). Today they are unique (the packet should
state the check). `simulator/pyproject.toml` sets `testpaths` and `rootdir` would be the repository root, so
`pyproject` options of `simulator` are not read. Proposed: the packet runs the script and also the two folders
separately and reports the same test counts (455 and 6), so the single-process run is proved equal to the two runs.

**R7. The DB and slot claim: confirm the tripwire does not fire.**
§0 says the guard is not pooled because there is no database URL. `simulator/tests/conftest.py` and
`backend/tests/conftest.py` open `pytest_configure` with the heavy-slot `require(` only when
`ASSETOPS_TEST_DATABASE_URL` is set (`test_heavy_slot_inventory.mjs:145`). Check the simulator conftest has the same
conditional form and not an unconditional one (if it is unconditional the guard fails with the slot refusal, or
needs a slot, and the run is not "about 10 s" under load). I could not confirm timing: `tools/heavy-slot.sh --
pytest` waited on a slot for more than two minutes with load average near 4, so I stopped it. Proposed: the packet
records the guard's seconds from check-all output on an idle machine and on a loaded one, and the spec says
"about 10 s idle; the 7 s figure is 20 Nov and 455 tests include two CLI subprocess tests (`test_cli.py`) and a
1 s-timeout child test." Also state whether the guard needs `-Jobs` slotting: it runs in the pool of 4 with 28 other
guards, so a 10 s guard raises the pool's wall time only if it is the longest; ask whether it is.

**R8 (done). `select-tests` triggers: the list is incomplete and the neutral key interacts with existing rules.**
Spec §2.3 lists `simulator/*`, `contracts/*`, `tools/world_history.py` and the manifest. Checked against code:
(a) `tools/world_history.py` already forces `mode: full` (a tool a test may run, `select-tests.py` TOOLS_EXEMPT
does not list it); with `neutral: true` added the output is "full backend and neutral", which is what "the backend
selection does not change" means; say so, so the implementer does not "fix" it. (b) The tests also read
`simulator/tests/world/fixtures/view_v1.json` and `golden/history_v1.json`; those are under `simulator/*`, covered.
(c) Not covered but affecting the neutral tests: `tools/checks/neutral_tests.py` itself, `tools/check-all.ps1`
(does the guard line), and `contracts/*` runtime data such as `gateway/` or `contract-fixtures/*` only if a
contracts test reads them (none today, by grep). Proposed: add `tools/checks/neutral_tests.py` to the triggers (a
change to the guard should name it), keep the rest, and say a `fnmatch` `simulator/*` also matches nested
paths (it does: `*` crosses `/`). (d) A changed `simulator/*.md` or `simulator/README.md` is in `NO_BACKEND` only for
`*.md`; the neutral trigger would still fire for it. Decide: markdown and `.egg-info` under those folders do not
trigger (proposed), pattern `simulator/*` minus `*.md`.

**R9 (done). The two `select-tests` cases have no automated home, and `validate-test-selection.py` does not assert cases.**
§3 says "add to `tools/validate-test-selection.py` if it asserts cases". It does not: it replays the last N merges
against a historical tree and has no case table, so the answer is "record in the packet", which is not a test and
leaves the trigger rule unguarded after the slice (the same class T2 exists to close). Proposed: add a small
`tools/checks/test_select_tests_neutral.py` (pytest, no database; four cases: simulator path true, contracts path
true, `tools/world_history.py` true plus `mode: full`, a `backend/assetops_backend/perf.py` false; and the JSON key
present) and register it in check-all next to the new guard, or fold the cases into `neutral_tests.py --self-test`.
This costs a fifth file (the spec's "four files" done-criterion §4.4 changes) and about 1 s. If the Architect declines,
§4.3 must read "recorded in the packet once" and be accepted as not guarded.

**R10 (done). "A planted failing test makes check-all fail" needs an automated self-test, not only a packet record.**
Done criterion §4.1 ("does check-all fail when a test fails, on a branch and on main") is proved by a manual plant
reverted in the packet. Other T2-class guards have a `--self-test` (`check-decision-index.py --self-test`,
`tracked_evidence.py --self-test`). Proposed: `neutral_tests.py --self-test` writes a temporary failing test
into a temporary directory, runs the guard's runner function on it and requires exit 1; then runs an empty
directory and requires exit 1 (the exit-5 case); registered as "Neutral package tests self-test (planted failure)".
Cost under 2 s. Without it, the empty-pass and the exit-5 rule of §2.1 (the key anti-vacuity item) have no proof.
Also record in the packet the full check-all red run with the guard name, per reviewer-guide bullet 2.

**R11. Guard count and the "38 guards" figure.**
§3 says fast mode passes with 38 guards. `grep -c 'Add-Guard "' tools/check-all.ps1` on `main` gives 28 call sites
(some are in loops or conditional on `$pool`/`$estate`, so the run-time count varies by branch and mode). Say
which count the spec means, and require the packet to quote the run's own summary line, not a number.
After R9 and R10 the count rises by two or three; state the expected final count.

**R12. Merge ordering with 2a, DS1b and 3C1 (the contracts tests location).**
`contracts/tests` has one file today; 2a (D-2A.10) builds its contracts tests in `backend/tests`, and DS1b may add
files under `contracts/tests`. The guard's directory list is fixed, so a later slice that adds `contracts/tests`
files is covered, and one that adds a new neutral package folder is not. Proposed: a line in `backend/TESTING.md`
and in the spec's out-of-scope: a new package with its own tests (for example `field/tests`) needs a line in the
script's directory list, and the script fails if `contracts/tests` or `simulator/tests` is missing. Also: DS1b's
merge precondition on T2 means T2 merges first; say whether DS1b's branch must merge `main` and rerun check-all after.

**Verified, no question:** `import_root_probe.py` covers `assetops_backend` and `assetops_contracts` only, so the
new script's own two-package assertion is not redundant; `assetops_simulator` and `assetops_contracts` do import from
`main` in this shared venv from any directory (probed from `/opt/assetecon/AssetOpsV1` and `/tmp`), so the in-process
`sys.path` insert is necessary; `simulator/tests` and `contracts/tests` import no `assetops_backend` and no database
(grep), so removing `ASSETOPS_TEST_DATABASE_URL` is a safety belt, not a need; `python3 tools/select-tests.py --files
tools/world_history.py simulator/assetops_simulator/world/history.py --json` today returns `mode: full` with no
`neutral` key, and a `simulator/tests/world/test_core.py` change returns `mode: none`, which is why the new key is needed.
Not verified: the guard's added time (the pooled pytest run waited on a slot), and a planted failure (no code exists).

## Implementer pre-flight questions

(none yet)
