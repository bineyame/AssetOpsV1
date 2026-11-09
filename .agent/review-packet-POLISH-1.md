# Review packet: OWN-POLISH-1

Branch `task/OWN-POLISH-1` from main `575c13222`. Worktree `AssetOpsV1-polish1`. No product decisions were needed.

## Outcome
- **G3b L1** `OperationalRecords.tsx` `submit`: `setResult([])` when a valid send starts, so a repeated identical outcome is a DOM change. `globalWork.css`: the `.global-work-form-result:empty { display:none }` rule is removed (the region stays in the accessibility tree; the `p` margin already collapses it when empty).
- **G3b L2** `submit`: a refused Submit focuses the first invalid field in form order (Site, Value, Taken at, Ticket).
- **G3b L3** `.agent/mock-departure-register.md` R651 row quotes the current banner literal.
- **G3b L4 (banner test)** `sitesIndexRoute.test.tsx` asserts the `role="note"` text is exactly "Demonstration · example sites and records".
- **G1 L-A** `tools/demo_combined_kisiwa.py` `plan_night`: the stuck-earlier-night check now runs before the PUBLISHED-resume return (after DUPLICATE_DAY).
- **G1 L-B** `tools/demo_combined.py` `--dry-run` help, and build sheet R1.5: dry run runs the read-only preflight, needs the build's DB and serve environment reachable, writes only the child's log under `<work>/logs`.

## Tests
- vitest `src/work` + `sitesIndexRoute`: 11 files, 227 passed. `tsc --noEmit`: clean.
- Backend `test_own_g1_add_dates.py` + `test_k7_kisiwa_story.py` (plan2 `.venv`, PYTHONPATH of all eight worktree dirs): 144 passed (143 + 1 new).
- New tests: `test_child_refuses_to_resume_a_later_published_night_over_an_earlier_one`; two form tests (focus order; region cleared at send start, repeat result re-appears); one banner test.

## Mutation proofs (all reverted, tree clean)
- L-A: reverted `demo_combined_kisiwa.py` to main: new G1 test fails (1 failed, 44 passed in that file).
- L1/L2: reverted `OperationalRecords.tsx` and CSS to main: both new form tests fail (2 failed, 12 passed).
- Banner: set the old literal in `OperatorShellLayout.tsx`: the banner test fails (1 failed, 22 passed).

## Not run / deviations
- `check-architecture.ps1` and `check-agent-workflow.ps1`: **not run**. Without `-ExecutionPolicy` PowerShell refuses with `UnauthorizedAccess`; merge check-all must cover them.
- `npm run lint` does not exist in this project (no script); tsc is the static check.
- The CSS half of L1 (no `display:none`) has no automated test: jsdom does not apply the stylesheet and the `?raw` import has no type declaration. Verified by inspection only.
- No `lint`, layout evidence, or full suites run (instructed).
- `frontend/node_modules` in the worktree is a junction to plan2's (git-ignored).
