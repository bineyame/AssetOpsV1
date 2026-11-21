# 3B4 handoff (partial: units 1-3 done; the check.py commit and unit 4 next)

Branch `task/3B4-observer`, worktree `/opt/assetecon/AssetOpsV1-3b4`. Main (4a, 3B6, DS3 at `2ef8e9769`) is merged
in (`5aa5b0e0f`); the fixture follows 3B6's excluded reason (`STRUCTURE_OTHER_KEY`; a COLDCHAIN Site now has a
structure, so `declare_tolerance` answers it `FACTOR_NOT_OBSERVED`, not `SITE_UNKNOWN`).

## Done

- Units 1-3 built and committed (`acd4b18b4`, `9a76b83d6`, `8dad430c7`, `f605f4524`); packet `packet.md` (written at
  `8dad430c7`, before the merge); spec status `in_review` (partial); built state in `.ai/state/data.md` (index line 173).
- Plants P6-P20, P22 and P23 each fail their named test. 10 regression failures are identical on main (environmental).

## Next (the coordinator cleared it: 4a and 3B6 are merged)

1. `git merge-base --is-ancestor` for 4a's and 3B6's merges -> record them in the packet's gate line.
2. The `check.py` commit (spec §2.3): `OBSERVE_CODES`, `check_observed` (codes KEY, COVER, LEAF, SOURCE, DIRECTION,
   KIND in that order, D-3B4.16; `SOURCE` reads `row.filled_by.family` and `row.absent`, `KIND` reads `row.home`, D-3B4.26;
   `TARGET_RULE` by a function-local `from assetops_backend.structure.targets import rules`, D-3B4.20), and its call
   in `check_all`, written on top of 3B6's `check_all`. `KEY` runs over `OBSERVED`'s keys only, so COLD and EV
   registries are not a fault (D-3B4.25). Check 4a's registry v4: the observed leaves and `NOT_OBSERVED` must still
   cover every MINI_GRID leaf exactly once (4a added stated kWh nodes); a leaf added by 4a that is not covered is a
   mid-build question to the Architect, with the default "not observed, reason DECLARED_SOURCE" if it is stated.
3. Tests 1, 1b and 3 in `backend/tests/test_3b4_observer.py` (spec §7); then plants P1-P5 and P21 (reviewer guide), each
   alone, on a throwaway `git worktree` (a plain copy is refused by the slot pool for Postgres; these are pure).
4. Unit 4: re-run the regression set (`regress.txt` list in the packet's tests table), `check-all.ps1`,
   `check-architecture.ps1` (set `ASSETOPS_GUARD_PYTHON` to the venv python), `check-agent-workflow.ps1`; update the
   packet (gates, plants table, tests table, acceptance 2 and 8) and the spec status line (drop "partial").

## Risks

- The served snapshot's code digest moves with `check.py` (reason `RULES`); rebuild after merge.
- Gate B: renumber 0071 if main's head moved (`test_10_single_head_on_0066` pins the parent).
- `check-all` still fails on `D-DS3.23` in `.agent/backlog-post-demo.md` (from main, not 3B4).
