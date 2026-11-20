# Review: declutter step 5 (Docs and tools) plus step-4 notes L1-L5

Branch `task/declutter-05-docs-tools`, 12 commits `f1f3866c9..792bcc064`, base `main` `d05bf668c`.
Fresh reviewer; it did not author the work. Discovery review: the whole diff was read, and the checks were run
independently before the packet was read.

## Summary (verdict: ACCEPT WITH NOTES)

- Nothing live was archived. None of the 28 tools is referenced by check-all, `tools/checks`, code, tests,
  configs, how-to sections, `.claude/`, the kept `.agent/` files, or the two active lane branches. The only
  references left are history, state, backlog and finished-packet records, plus one stale `.ai/` file (N4).
- None of the 12 Docs is cited as current. `.ai/ARCHITECTURE.md:5-7` and `.ai/PRODUCT.md:15-16` now say "was
  ... archived". The normative files kept in place (`simulator_design_v4.md`, the scenario document, the
  Site-first trio and the Layer 4 pack) cite none of them.
- Bytes: 49 of 49 moves are byte-identical or carry exactly one header line, checked independently against
  `d05bf668c`. All 7 header-less moves (the 3 owner texts, the 2 live HTML documents and the 2 JSON files) are
  byte-identical. No owner file is changed on the branch.
- Guards: the blocking set is identical. The `check-all.ps1` diff removes only the three `-Advisory` `Add-Guard`
  lines, plus comment edits. `check_mock_gaps.cjs` is still blocking: the catalogue is valid with 36 gaps, and
  `node --test test_mock_gaps.cjs` passes 13 of 13. No code reads the archived JSON files or `tasks/README.md`.
- Step-4 follow-ups L1-L5 are all closed and verified. Two notes: one L3 line is a paraphrase, and the L2 tool
  has a small argument bug (N1).
- Findings: 3 Low and 3 Info. None of them blocks the merge.

## Findings

### N1 (Low): `check-split-preservation.py --rev REV` breaks unless REV ends in `^`
- **Where:** `tools/check-split-preservation.py:69`, which reads
  `PARTS_REV = ... if "--parts" in sys.argv else rev[:-1]`.
- **What is wrong:** the default path is fine, because there `rev` is `<sha>^`. With an explicit `--rev`, the
  last character is cut off:
  - `--rev HEAD` fails with `git show HEA:.ai/decisions/2026-10-late.md` (`CalledProcessError`). I reproduced
    this.
  - `--rev <sha>` silently becomes a shorter sha.
  - `--rev X~1` becomes `X~`, which git also reads as `X~1`, by luck.
- **Why it matters:** the L2 proof tool is documented as taking `--rev REV`.
- **Fix:** derive the parts revision separately (the commit that added `.ai/decisions/2026-09.md`), or strip
  only a trailing `^`, or require `--parts` whenever `--rev` is given.
- **Type:** acceptance gap for L2, though minor.

### N2 (Low): the packet calls the `check-split-preservation.py` edit a comment edit
- **Where:** packet, Checks, the `select-tests.py` bullet.
- **What is wrong:**
  - The two gap-check `.cjs` diffs are comment-only. I checked every changed line; all are `//` lines.
  - `tools/check-split-preservation.py` is a functional change: the new `PARTS_REV`, `--parts` and
    `--worktree` options, and a new `body()` reader. It is the L2 fix.
- **Why it matters:** the test-selection question. Reverting the two `.cjs` comment edits would not move the
  branch off "full", because `tools/check-split-preservation.py` alone selects full ("a tool a test may run or
  read").
- **Recommendation:** keep all three edits.
  - Without the `.cjs` edits, the comments would claim that the retired checker still runs.
  - No backend, host, simulator or `frontend/src` test reads any of the three files (`git grep`, none).
  - So "full" here is the selector's conservative heuristic, not a real test need. Record that in the merge
    note. Under the owner's suite policy, run no full suite.
  - Correct the packet wording.
- **Type:** preference / accuracy.

### N3 (Low): the retirement rationale overstates O1
- **Where:**
  - `archive/frontend/docs/architecture/README.md:4-5` says "owner decisions O1 and O2 ... say the v69 mock and
    the S1-S7 queue are no longer read".
  - The archived guard header, from `tools/declutter/step5_map.py:56`, says "v69 and S1-S7 are not read, O1/O2".
- **What is wrong:** O1, as recorded in `.ai/START_HERE.md:14-20`, says Site-first/S1-S7 stays authoritative
  for the live product until Q1 is approved. The accurate grounds are:
  - O2: v69 is not read;
  - the S1-S7 queue is built (`START_HERE` planning status);
  - PIPE-1 A6: the guards were already advisory.
- **Why it matters:** an agent that reads the README could take it to mean the Site-first documents are not
  read. The risk is low because `archive/` is not a default read.
- **Fix:** reword the README line. The header line can stay; changing it would mean re-running the mover.
- **Type:** preference / accuracy.

### N4 (Info): citation rewriting turned one stale instruction into one that points into `archive/`
- **Where:**
  - `.ai/COORDINATOR_LOOP.md:9` now says "Run `node archive/frontend/docs/architecture/check_v69_dependency_registry.cjs --next-work ...`".
  - `.ai/state/tools.md:7` says, in the present tense, that the archived `delivery_next_work.cjs` "owns"
    next-work.
- **Why it is only Info:** neither file is on the start path. Packet deviation 4 already scopes out the stale
  `.ai/` planning files.
- **Suggestion:** move `COORDINATOR_LOOP.md` and its siblings (`ARTIFACT_INDEX`, `FEATURE_MAP`,
  `PLANNING_*`, `ARCHITECT_DEMO_RECOMMENDATION`) to `.ai/history/` in the follow-up that recommendation §3.4
  already lists.

### N5 (Info): two dangling same-folder pointers to an archived JSON file
- **Where:**
  - `frontend/docs/architecture/v69-dependency-registry-pilot.json:7`:
    `"subject_area_briefs": "v69-subject-area-briefs.json"`.
  - `frontend/docs/architecture/v69-dependency-registry-pilot.md:25`, a relative link to the same file.
- **Why it is only Info:** nothing reads the field (`check_mock_gaps.cjs` passes), and `CITATION_MAP` maps the
  path.

### N6 (Info): what lane merges will need (not caused by this branch)
- **Merge simulation** (`git -c merge.renameLimit=20000 merge-tree --write-tree`, run read-only):

  | Lane | Into `main` | Into this branch |
  | --- | --- | --- |
  | `task/product-direction-layer4-design` | clean | clean |
  | `task/gtm-documents` | 1 conflict | the same 1 conflict |

  The `gtm-documents` conflict is the content conflict in `owner/owner-gtm-documents-request-2026-11-18.md`,
  from the step-4 rename. Step 5 adds no conflict.
- **New guard failure after a lane merge:** both merged trees track
  `.agent/owner-grounded-transition-request-2026-11-18.md`, which `AGENT_KEEP` now fails. The lane should move
  it to `owner/` when it merges `main`.
- **Stale citations after a lane merge:** 9 Layer 4 pack files on the lanes cite
  `.agent/decision-intelligence-mechanism-2026-11-14.html` as their baseline. These resolve through
  `CITATION_MAP`. Re-running `move_step5.py rewrite` after the merge (it is idempotent) would update them.
- **Selector blind spot (pre-existing):** `tools/select-tests.py` uses `git diff --name-only`, which detects
  renames, so a tool moved out of `tools/` shows only its `archive/` path and selects nothing. It would miss a
  moved tool that a test reads. I checked by grep that no test reads any of the 28.

## Verification detail

1. **Nothing live archived.**
   - **Tools, by name:** I searched every basename and module stem of the 49 moves across `HEAD`, excluding
     `archive/`, `Docs/archive/`, `.ai/history/`, `specs/`, `tasks/archive` and `tools/declutter`.
   - **Tools, by slice prefix:** I also searched slice prefixes (`dd1a1_`, `dd1b2a_`, `w502-`, ...) across
     `HEAD` and both lane refs.
   - **What remained:**
     - state and backlog records: `.ai/state/*`, `.ai/MILESTONE_REVIEW_BACKLOG.md`;
     - finished `tasks/*` packets;
     - the self-test fixture paths in `tracked_evidence.py`;
     - N4 and N5.
   - **Look-alikes:** the kept `tools/dd1a2_mill3_dry_run.py` and `host/tests/test_dd1a1_registered_kobo.py`
     are different files. No kept tool imports an archived one.
   - **Archived scripts still parse.** `ast` passes on every `.py` file and `node --check` on every
     `.mjs`/`.cjs` file. Both shebang files keep the shebang on line 1.
   - **Docs:** the only citation of `declared-capability-and-what-checks-it.md` on `main` was in the stale
     `.ai/ARTIFACT_INDEX.md`.
   - **Moved HTML documents:** they link only to each other, and both moved together.
2. **Guard retirement.**
   - The `check-all.ps1` diff between `main` and the branch shows that only the three advisory guards are
     removed.
   - `check_mock_gaps.cjs` and `test_mock_gaps.cjs` read only `mock_gaps.cjs` and the registry, panel-contract
     and screen-ledger JSON, all still in place.
   - On `main`, nothing in `tools`, `backend`, `host`, `frontend/src`, `simulator`, `package.json` or `.claude`
     read the archived files, apart from the three removed `Add-Guard` lines.
3. **Step-4 follow-ups.**
   - **L1.** I planted `.agent/stray-PLANT-review.md` in a temporary index copy (`GIT_INDEX_FILE`); the real
     index was not touched.
     - The guard printed `1 problem(s)` and exited 1. The real index gave 0 problems.
     - The self-test passes 19 bad and 15 good paths.
     - The guard is blocking in check-all.
     - The only `.agent/` mentions in `.claude/` are "never" (implementer brief line 67, reviewer brief
       line 53).
   - **L2.** With default arguments the proof gives `OK decisions 504986 = 504986` and `OK state: 138
     sections`. `--worktree` fails, as documented. See N1.
   - **L3.** The handoff is 5,131 bytes, under the 8,000-byte cap.
     - Word-for-word from `.ai/history/coordinator-handoff-to-2026-11-18.md`:
       - the serve/Vite line (history line 219);
       - the owner-access line (history line 226);
       - "Restart only when no agents are running." (history line 210).
     - From inside history line 101: the ch5c2 debt, with a "Test debt:" lead-in added.
     - The `ASSETOPS_GUARD_PYTHON` line is new wording. The history has only "set ASSETOPS_GUARD_PYTHON"
       (line 60). Its claim "check-all sets it" is true (`tools/check-all.ps1:271`).
     - The P1/P2 pointers `:331` and `:342` land on the P1 and P2 headings.
   - **L4.** I compared all 30 re-headed files, not a sample of 10, with the index.
     - 25 are named by a `live` row in `.ai/decisions/index-*.md`.
     - 5 are the architect answers that the live plan and backlog cite.
     - One live-row file is not re-headed: `architect-S2-01b-answers-3.md`. That is correct, because its decision
       text is in `.ai/decisions/2026-10-early.md` and the file is only named in the title.
     - Every re-headed diff changes line 1 only.
   - **L5.**
     - I checked out the handoff at `a1957a47a`, the last commit before the page-load review (`bc8fe7077`).
     - Its lines 110, 61 and 105-132 equal history lines 114, 65 and 109-136. The +4 offset is right, and the
       step-4 review's "+1" was approximate.
4. **Moves and links.**
   - `move_step5.py --verify`: 49 moves, all 49 hold the `d05bf668c` bytes.
   - `move_step4.py --verify`: 2096 files, 1 owner file appended to, all byte-identical.
   - `check_links.py --base d05bf668c`: 3311 cited paths, 0 broken since `d05bf668c`, 415 pre-existing.
   - The `CITATION_MAP` "Step 5" table covers all 49 moves by name or unambiguous glob. No kept `tools/` file
     matches `dd1a1_*`, `dd1b2a_*`, `v01b*`, `pr2a-`/`pr3-` or `w502-`/`w504-`.
5. **Test selection.** On `main..HEAD`, `select-tests.py` gives full because of the three files in N2.
   Archive, `Docs`, `tasks` and `tracked_evidence` paths select none.
   - `node frontend/docs/architecture/check_mock_gaps.cjs`: valid, 36 gaps, exit 0.
   - `node --test frontend/docs/architecture/test_mock_gaps.cjs`: 13 of 13 pass.
6. **Full check run** at `792bcc064`, with `frontend/node_modules` symlinked from the main checkout and removed
   afterwards:
   - `tools/check-all.ps1`: `All 36 guards passed (blocking; 0 advisory, 0 warned)`, 45.3 s, exit 0. The only
     SKIP is the estate guard self-test, as designed (unchanged against `main`).
   - `tools/check-agent-workflow.ps1`: `Agent workflow check passed.`
   - `tools/check-decision-index.py`: `OK (470 indexed decision IDs; every cited ID resolves; every named file
     exists)`.

## Not verified / residual risk

- **Not run:**
  - no full suite (owner policy);
  - no DB, Docker or ports;
  - `npx vitest related` was not run; the packet records why.
- **Merge order:** the lane merge-tree results hold only for the lane heads `adf49caab` and `6992c461b` as they
  are now.
- **A leftover process that is not mine:** PID 1472309, about 22 minutes old at review time. It is a bash
  `until ! pgrep -f "tools/check-all.ps1"` waiter. Its own command line matches the pattern, so it will never
  exit. It belongs to whoever started it, and that session should stop it. I did not touch it.
