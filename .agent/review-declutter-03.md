# Review: declutter step 3 (untrack evidence)

Branch `task/declutter-03-untrack-evidence` at `9c37f1bd1` (5 commits on `main` 5945fd490). Reviewer: a fresh Claude
reviewer that did not write this work, 2026-11-18. Discovery depth (W5): I formed my own view before reading the packet.

## Verdict: REVISE (small fix round)

The untracking is correct and complete. Nothing that code, tests, guards or indexes read was untracked. The copy is
exact: all 22,300 rows pass `sha256sum -c`, and a 700-row sample matches the git blobs on `main`. The fixture moves are
byte-identical and every reader was updated. The guard works.

Four Medium findings block the merge. Two are acceptance gaps in the retention tool (M1, M2). Two are gaps in the lane
and merge story (M3, M4). The G6 re-pin (L1) should land in the same round. All of them are small.

## Findings (ranked)

### M1 (Medium, acceptance gap). The retention tool can delete outside `/opt/assetecon/evidence/`, including the backup
- Where: `tools/evidence-retention.py:80` (`--root`, which takes any value) and `:70` (the containment check tests
  against `args.root`, not against the fixed `ROOT`).
- What is wrong: with `--root /opt/assetecon/evidence-backup-2026-11-18` or `--root /`, the tool lists and, after the
  typed confirmation, deletes there. I ran it in list mode against the backup: it accepted the root and found 0 items,
  only because the copied files' mtimes are recent.
- Why it matters: the brief says the tool must not be able to touch the backup or anything outside
  `/opt/assetecon/evidence/`.
- Fix: resolve `--root` and refuse unless it is `ROOT` or a folder under it. Keep the per-path check against
  `ROOT.resolve()` as well. Optionally, refuse any path with `evidence-backup` in it. If a scratch root is needed for
  tests, put it behind an explicit test-only flag or an environment variable.

### M2 (Medium, acceptance gap). Retention counts from the commit date, so the whole batch is purgeable today
- Where: `tools/evidence-retention.py:41-43` and `:86`; `.ai/RULES.md` §9, the line "Retention: 2 weeks from capture".
- What is wrong: today the default listing shows 245 items, 22,204 files and 1,694.9 MB as past 14 days, which is
  almost the whole batch.
- Why it matters: the owner's O3 ("outside the repo, needed only for 2 weeks") was given at the moment of the
  copy-out. Read in that context, it means "keep it reachable for 2 weeks from now". As built, the first `--delete`
  would remove the batch on day 0.
- Fix (recommended): this batch counts from its copy-out date. An item's retention date should be
  `max(last_commit_date, copied_at)`. Record `copied_at` once per manifest folder, for example as a `COPIED-AT` file
  or a manifest header holding `2026-11-18`. The earliest purge of this batch is then 2026-12-02. New evidence written
  under `<task>/<run>/` keeps its mtime clock.
- Also: reword the RULES line to say so. Keep the existing rule that the coordinator asks the owner before the first
  purge.

### M3 (Medium). The new guard will fail the Layer 4 and GTM lanes after they merge `main`
- Where: on both `task/product-direction-layer4-design` and `task/gtm-documents`, the lane added
  `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/tools/rebase-log.txt` (2.1 KB) after the merge
  base. It matches `-(log|last)\.txt$` (`tools/checks/tracked_evidence.py:35`), and that rule has no `Docs/`
  exemption.
- What is wrong: the file is cited as the record of the mockup's re-based edits, in `README.md:31`,
  `CHANGE-REGISTER.md:5` and `derivation-register.md:2462` on the lane. So `check-all` will go red in both lanes as
  soon as they merge `main`, and the packet does not mention it.
- What I checked: a scripted per-lane check of every path the lane added since the merge base, run through the
  guard's own `problems()`, plus a check for modify/delete conflicts.
  - Layer 4: 127 paths added, 1 flagged, 0 modify/delete conflicts.
  - GTM: 142 paths added, 1 flagged, 0 modify/delete conflicts.
  - `task/WALK-1113-build` is already an ancestor of `main`: 0 flagged.
- Recommended lane procedure:
  1. Before merging `main`, the lane renames the file to a non-log name (e.g. `rebase-record.txt`, keeping
     `tools/rebase_v70.py`'s output path in step) and updates the three citations, or moves it out to
     `/opt/assetecon/evidence/`.
  2. The lane commits any pending edits to evidence files first. An uncommitted local edit to an untracked-on-`main`
     path blocks the merge, and a committed one becomes a modify/delete conflict. None exist today.
  3. The lane merges `main` and runs `tools/check-all.ps1`.
- Alternative: narrow the LOG rule so it exempts `Docs/`, as the image rule already does. I prefer the rename: the
  file is a record, so it should not be named like a log.

### M4 (Medium). The packet's residual-risk claim is wrong: merging deletes the files from the worktree
- Where: `.agent/packet-declutter-03.md`, "Residual risk": "Other worktrees and lanes still have the files on disk".
- What is wrong: a checkout or merge that moves from a commit tracking a file to one that untracks it removes the
  file from that working tree. I reproduced this in a scratch repo: a lane merges `main` after `git rm --cached` and
  `.agent/x-evidence/f.png` disappears. This will happen to `/opt/assetecon/AssetOpsV1` when `main` advances, to
  `AssetOpsV1-walk`, and to every lane that merges `main`.
- Why it matters: nothing is lost, because the copy and the backup hold everything. But a person or script that reads
  local `.agent/<ID>-evidence/...` paths will find them gone. That includes walkthrough prep, coordinator handoffs that
  cite capture paths, and capture tools that diff against a previous run.
- Fix: correct the packet and the NOW/RULES line to say that after the merge, evidence is read from
  `/opt/assetecon/evidence/repo-untracked-2026-11-18/.agent/...` (same relative path). Tell the lane owners before
  they merge.

### L1 (Low). Re-pin the DIESEL-1 G6 result on this branch
- Where: `host/fixtures/diesel-d0/probe-result.json:67`.
- What I checked: I ran `tools/probe_kisiwa_nights.py` in print mode (no write) and diffed the output with the
  committed file.
  - Exactly one line differs: `"template": ".agent/DIESEL-D0/..."` against `"host/fixtures/diesel-d0/..."`.
  - `template_sha256_lf` and every measured value are identical.
  - `probe_kisiwa_fuel.py --check` (F8) prints "probe result current".
  - No code reads D0's `assumptions.template`.
- Recommendation: run `python tools/probe_kisiwa_nights.py --write` on this branch in the fix round. Confirm that
  `git diff` shows only line 67 and that `--check` prints "current". That follows DIESEL-1's "re-pin by `--write`,
  never by hand", and it keeps G6 from landing red on `main`. It is a path-only change, and the move itself caused it.

### L2 (Low, preference). `.gitignore` and the guard do not cover the same shapes
- Where: `.gitignore:6-18` against `tools/checks/tracked_evidence.py:35-38`.
- What is wrong: the guard fails on `*.out`, `*-log.txt`, `*-last.txt`, `*.jsonl`, `*-wip/` and `*-probe/`, but none
  of these is ignored. Outside `.agent/`, such a file shows up as untracked and can be committed, and then
  `check-all` fails. That is the right outcome, but it comes late.
- Fix: consider adding `*.out`, `**/*-wip/` and `*-log.txt` to `.gitignore`.

### L3 (Low, preference). The size cap and the fixtures exemption are broad
- Where: `tools/checks/tracked_evidence.py:29-32`.
- The 1 MiB cap is a justified deviation from §5.5's 300 KB. Outside the allowed folders, the largest legitimate files
  are `build-sheet-DIESEL-1.md` (684 KB) and `build-sheet-OWN-GAPS` (537 KB). 300 KB would block live specs before
  step 4 moves them. The packet labels this deviation.
- Recommendation: lower the cap to 300-512 KB once step 4 has condensed and moved the specs.
- Note: any path segment named `fixtures` exempts images and size. That is acceptable, but it is the loophole to watch
  in reviews.
- Not built: "router files over their caps" (§5.5, last bullet), which belongs with §5.3 and a later step.

### L4 (Low). Capture scripts cited by tests now live only outside the repo and are subject to purge
- Where:
  - `frontend/src/estate/__tests__/estateFinancials.test.tsx:624` cites `.agent/W3-02-evidence/capture-financials.mjs`.
  - `frontend/src/sites/__tests__/coldScenarios.test.tsx:410` cites `.agent/W5-01b-C5-evidence/capture.mjs`.
  - `frontend/src/ui/__tests__/DataTable.test.tsx:5` cites `.agent/W5-03b-ui-evidence/capture.mjs`.
- These are provenance comments, not runtime reads. But the tests' measured fixtures came from those scripts, and
  after a purge nobody can regenerate them.
- Fix: when the purge runs, keep the `*.mjs`, `*.py` and `*.sh` files from the batch (about 400 small files), or
  decide in step 5 whether any of them belongs in `tools/archive/`.

## What I verified (commands run at `9c37f1bd1`)

1. **Nothing wrongly untracked.**
   - `git ls-tree -r --name-only main` against `HEAD`: 22,309 removed and 12 added.
   - Removed = 22,300 class a/b paths + 9 renames (R100). Every removed path is under `.agent/`.
   - 85 subdirectories were removed whole. The only `.agent/` subdirectory still tracked is `delivery-drafts/`.
   - The 197 removed root files are 104 `*-log.txt`, 3 `*-last.txt`, 1 `.log`, and 89 outputs (`next-work-*.json`,
     parity/probe/DD JSON, layout-evidence and run txt, 1 png, 1 jsonl).
   - What stays tracked under `.agent/`: 2,095 files (2,081 md, 9 py, 4 html, 1 sh).
   - I sampled 50 random manifest rows. Each was a capture png or json, a log, err or pid, or a capture tool inside an
     evidence folder, and each matched its class.
   - Runtime reads: I grepped tracked code for `.agent` path construction (`open`, `read_text`, `readFileSync`,
     `join`, `Path`, `glob`, `".agent"`). The only remaining reads are `mock-deviation-labels.mjs:94` and
     `test_evidence_checks.mjs:191` (both target files are still tracked), `check-decision-index.py` (reads tracked
     text), `select-tests.py` and `validate-test-selection.py` (patterns and history diffs), and
     `w5f1-d3-evidence.mjs` (an output directory).
   - Citations: every other hit against a removed prefix is a docstring or comment citation, a usage line naming an
     output path (`tools/dd1b2a_*.py`), or text in `.ai/state`, `tasks` or `.agent` (historical).
   - `python tools/check-decision-index.py`: OK (470 IDs; every named file exists).
2. **Copy.**
   - `MANIFEST.tsv` has 22,300 rows, and its path set equals the removed (a)+(b) set exactly.
   - `sha256sum -c` passed on all 22,300 rows in 18 s.
   - Manifest sha256 against `git show main:<path>` on a 700-row random sample: 0 mismatches.
   - Backup `/opt/assetecon/evidence-backup-2026-11-18/agent/`: 1.7 GB and 24,404 files. Spot-checked 4 paths;
     `DIESEL-F0/probe-result.json` there compares equal (`cmp`) to the moved fixture.
3. **Fixtures.**
   - 9 renames at R100.
   - No reference to the old `.agent/DIESEL-*` or `.agent/W3-02-evidence` paths remains in tracked code. The only
     other hit is the G6 line (L1).
   - `.gitattributes` LF pins and `run-backend-suite-in-container.sh` were updated (`./host` is still copied).
   - The two frontend tests read the new path with a hard `readDisk`, so a missing file fails the test.
   - Test results:

     | Tests | Result |
     | --- | --- |
     | Host `test_k0_kisiwa_actions`, `test_k1_registered_kisiwa`, `test_k3_fuel_balance_parity` | 30 passed, 9 skipped (all skips are DB: `ASSETOPS_TEST_DATABASE_URL` not set; no DBs by rule) |
     | Backend `test_k0_operational_actions`, `test_k1_kisiwa_fixtures`, `test_k3_fuel_balance_rules`, `test_k4a_fuel_finding_rules`, `test_k5_fuel_night_text` | 121 passed |
     | Vitest `estateEvidence` and `estateFinancials` | 33 passed (with a temporary `node_modules` symlink, removed afterwards) |

4. **`.gitignore`.**
   - `git ls-files -ci --exclude-standard` lists 2,095 paths, all of them already-ignored `.agent/` text. Outside
     `.agent/`: 0.
   - On `main`, the new rules ignore no tracked path outside `.agent/`.
   - Probes:
     - `backend/assetops_backend/evidence/*.py`, `tools/layout-evidence.mjs` and the `__tests__` evidence-deltas JSON
       are not ignored.
     - `evidence/`, `*-evidence/`, `*-evidence-x/`, `*-shots/`, `.log`, `.pid` and `Docs/**/*.html.tmp` are ignored.
5. **Guard.**
   - At the tip: 0 problems. Self-test: pass.
   - With a scratch `GIT_INDEX_FILE`, I planted 10 violations of my own: an evidence-folder png, a jpg in `src`, a
     `.log`, a `.out`, a `-captures` dir, `-log.txt`, a root `.agent` json, a 1.48 MB blob in backend source, a
     `-shots` dir and a `-probe` dir. All 10 were flagged (13 problems, exit 1).
   - With 4 clean planted paths, including a 1.48 MB `__tests__` JSON and a new module under
     `backend/assetops_backend/evidence/`: 0 problems, exit 0.
   - Registered as blocking: `tools/check-all.ps1:287-288` uses `Add-Guard` without `-Advisory`.
   - Side effect: the plant wrote two small unreachable blobs into the shared object store. They are harmless and gc
     removes them.
6. **Retention.** The tool lists by default. `--delete` needs the exact typed phrase, and a non-TTY run aborts. The
   default root is safe because `evidence-backup-*` is not under `evidence/` by path component. The gaps are M1 and M2.
7. **G6.** See L1. The only difference is line 67.
8. **Full guard runs.**
   - `pwsh -NoProfile -File tools/check-all.ps1`: "All 36 guards passed (blocking; 3 advisory, 0 warned)", 50.3 s,
     rc 0.
   - `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: "Agent workflow check passed", rc 0.

## Not verified
- The DB-gated host tests (9 skips), by rule.
- The demo serve smoke test (§4.2 step 3, last bullet): no ports, by rule.
- `inventory.py` and `copyout.py` were not re-run. I verified their outputs independently instead.

## Residual risk the packet does not name
- M3 and M4 above.
- The tests' measured layout fixtures (W3-02) are now frozen copies. Regenerating them depends on capture scripts that
  live only in the evidence folder (L4).
