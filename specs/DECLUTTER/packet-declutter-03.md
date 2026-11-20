# Packet: declutter step 3, generated evidence out of the repo

Branch `task/declutter-03-untrack-evidence` (from `main` 5945fd490; tag `pre-declutter-3-2026-11-18`).
Spec: `.agent/repo-declutter-recommendation-2026-11-18.md` §1.3, §2.4-2.5, §3.5, §4.1, §4.2 step 3, §5.1-5.2, §5.5.
Owner: O3 (outside the repo, 2 weeks) and "go ahead with declutter step 3 after the review"
(`.agent/owner-repo-declutter-request-2026-11-18.md`). USER_REVIEW_REQUIRED: false (repo hygiene, no product
behaviour). One owner question stays open: the first purge.

## Commits

| Commit | What |
| --- | --- |
| 721e4b293 | Code-read data moved to tracked fixtures; readers updated (14 files, 9 renames at 100%) |
| dcaadcae2 | `git rm --cached` of 22,300 class a/b files (working-tree files kept) |
| f87bb76cb | `.gitignore` entries; `tools/checks/tracked_evidence.py`; check-all registration |
| 0fb414f6c | `tools/evidence-retention.py`; RULES §9 (where evidence goes, retention) |
| (last) | built state `.ai/state/tools.md` + index line, NOW/START_HERE lane line, this packet |

## 1. Inventory (tracked `.agent/` on main: 24,403 files, 1,723.7 MB)

| Class | Files | MB | Contents |
| --- | --- | --- | --- |
| a generated evidence | 19,828 | 1,608.6 | 86 evidence/capture/recapture/screens/wip dirs (19,739 files: 16,903 png, 2,005 json, capture scripts, run notes) + 89 root outputs (next-work-*.json, parity/probe/DD json, layout-evidence/run txt, 1 png, 1 jsonl) |
| b logs and transcripts | 2,472 | 92.5 | 1,836 .log, 459 .err, 34 .pid, 30 .out, 104 `*-log.txt` (80.5 MB codex transcripts), 3 `*-last.txt`, 5 .wip, 1 .done |
| c text, stays tracked | 2,092 | 22.2 | 2,075 root md, 4 root html, 10 root py/sh scripts, `delivery-drafts/` (3 md) |
| d read by code | 11 | 0.4 | 9 data files moved (below); 2 root md read in place |

Largest folders (class a): post-W6-audit 3,667 files 293.7 MB; post-W6-final-recapture 3,704 / 273.2;
post-W6-W6-evidence 3,398 / 254.8; post-W6-shell-recapture 1,040 / 83.7; post-W6-W4-recapture 737 / 78.1.
Full per-file list with class and reason: `/opt/assetecon/evidence/repo-untracked-2026-11-18/inv.tsv`
(script `inventory.py` beside it, re-runnable against `main`).

Outside `.agent/`: no generated evidence is tracked. Images are only in `frontend/mockups/v69|v70` (113, mock
references) and `Docs/` (7 design diagrams); `backend/assetops_backend/evidence/` is source code. Nothing untracked
outside `.agent/`.

## 2. Fixture moves (byte-identical, `git diff -M100%`)

| From | To | Readers updated |
| --- | --- | --- |
| `.agent/DIESEL-F0/{probe-result.json, kisiwa-001-bindings.draft.json, kisiwa-001-operational-actions.draft.yaml}` | `host/fixtures/diesel-f0/` | host `test_k0_kisiwa_actions`, `test_k1_registered_kisiwa`, `test_k3_fuel_balance_parity`; backend `test_k0_operational_actions`, `test_k1_kisiwa_fixtures`, `test_k3_fuel_balance_rules`, `test_k4a_fuel_finding_rules`, `test_k5_fuel_night_text`; `tools/probe_kisiwa_fuel.py` |
| `.agent/DIESEL-D0/{probe-result.json, kisiwa-diesel-hybrid-60kw.draft.yaml}` | `host/fixtures/diesel-d0/` | `tools/probe_kisiwa_nights.py`, `tools/probe_kisiwa_fuel.py`, backend `test_k1_kisiwa_fixtures` |
| `.agent/W3-02-evidence/app-{positive,partial}.json`, `app-financials-{positive,partial}.json` | `frontend/src/estate/__tests__/fixtures/w3-02/` | `estateEvidence.test.tsx`, `estateFinancials.test.tsx` |

Also: `.gitattributes` LF pins follow the DIESEL files; `tools/run-backend-suite-in-container.sh` no longer copies
`.agent/DIESEL-*` (they are under `host/`, already copied). `host/fixtures/` was chosen over `host/tests/fixtures/`
because `host/tests/fixtures.py` is an importable module of that name.

Kept in place (class c and d): `.agent/mock-departure-register.md` (`tools/checks/mock-deviation-labels.mjs`) and
`.agent/W1-UX-combined-owner-walkthrough.md` (`tools/checks/test_evidence_checks.mjs`). Both are live text (a
register agents append to; an owner walkthrough file) whose home is step 4; moving them here would move text, not
evidence. `tools/check-decision-index.py` reads `.agent` text by design.

## 3. Copy-out and manifest

`/opt/assetecon/evidence/repo-untracked-2026-11-18/` (it did not exist; created beside `PIPE-1/`). Paths are
preserved (`.agent/...`). `MANIFEST.tsv`: path, size, sha256, class, last_commit_date, 22,300 rows, 1,701,090,665
bytes. Verification: `copyout.py` hashed source and copy per file (0 mismatches); then an independent
`sha256sum -c` of the manifest against the worktree (exit 0) and against the copy (exit 0). One date came from a merge
commit (`architect-W2-layout-log.txt`, 2026-10-17) and was filled from `git log -1`. Dates span 2026-09-30 to
2026-11-13.

## 4. Counts and size

- `git ls-files | wc -l`: 27,492 on main, 5,194 now (target 3k-7k). `.agent/` tracked: 24,403 to 2,094 (22.5 MB).
- Tracked bytes at the tree tip: 1,803.0 MB on main to 101.9 MB. `.git` is unchanged (1.2 GB; no history rewrite, O5).
- Tracked-list diff vs main: 22,309 removed = the 22,300 class a/b paths in the manifest + the 9 class d old paths
  (now at the fixture paths, 100% renames); 11 added = 9 fixtures + 2 tools. Every class c path and both in-place d
  files are still tracked (scripted `comm` check: empty).

## 5. Guard (recommendation §5.5)

`tools/checks/tracked_evidence.py`, blocking in `tools/check-all.ps1` with a `--self-test` (12 planted violations,
10 clean paths). Fails on tracked: `*.log|err|pid|out`, `*-log.txt|*-last.txt`, `*.jsonl` outside fixtures; any file
in a `*-captures*|*-evidence*|*-recapture*|*-screens|*-shots|*-wip|*-probe` folder; images outside
`frontend/mockups/`, `frontend/public/`, `Docs/`, `fixtures/`, `__fixtures__/`; files over 1 MiB outside those and
`contract-fixtures/` and `__tests__/`; any `.agent/` path other than root md/html/py/sh or `delivery-drafts/*.md`.
Threshold 1 MiB: the largest legitimate tracked file outside fixtures and mocks is 0.68 MB (`build-sheet-DIESEL-1.md`);
transcripts reach 4.4 MB; 300 KB (§5.5) would flag 5 live build sheets and the v69 registry. Sizes come from the index.

Evidence: planted `.agent/ZZ-plant-evidence/shot.png`, `.agent/zz-plant.pid`, a 1.6 MB `tools/zz-plant-dump.txt`
(`git add -f`): exit 1, 6 problems (evidence folder, image, .agent shape, pid, size). Unstaged and removed: exit 0,
"5194 tracked files, 0 problem(s)". Against `main`'s tree the path rules report 58,839 problems. `check-agent-workflow.ps1`
needed no change (check-all carries the rule).

`.gitignore` adds `/evidence/` (root only: `backend/assetops_backend/evidence/` is source), `**/*-captures/`,
`**/*-captures-*/`, `**/*-evidence/`, `**/*-evidence-*/`, `**/*-recapture/`, `**/*-screens/`, `**/*-shots/`,
`*.pid`, `*.err`, `*.log`, `Docs/**/*.html.tmp`. `git ls-files -ci --exclude-standard` outside `.agent/`: 0. Probe:
new files in `x-evidence/`, `tools/foo-captures/`, `run.log`, `Docs/a.html.tmp` are ignored; a new file in
`backend/assetops_backend/evidence/` is not.

## 6. Retention

`tools/evidence-retention.py` lists items older than `--days` (14) by capture date: manifest groups (per top folder,
newest last_commit_date) or `<task>/<run>/` folders by newest mtime; prints the total. `--delete` asks to type
`delete <n> items`; anything else aborts (exit 1). Manifest lines stay; deletions go to `RETENTION-LOG.tsv`.
Superseded by revision 2 (dating by copy-out): today nothing is past 14 days. Delete path tested on a scratch tree only (abort and
confirm). RULES §9 now says where evidence is written and how retention runs.

## 7. Checks (revision 0fb414f6c unless noted)

- `pwsh -NoProfile -File tools/check-all.ps1`: All 36 guards passed (3 advisory, 0 warned), 54 s; estate self-tests
  skipped (unchanged writer guard). Same result in a clean temporary worktree of the branch (no ignored files), then
  removed.
- `tools/check-agent-workflow.ps1`: passed. `tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`): passed.
- `python tools/check-decision-index.py`: OK (470 IDs; every named file exists).
- host `test_k0_kisiwa_actions`, `test_k1_registered_kisiwa`, `test_k3_fuel_balance_parity`: 30 passed, 9 skipped
  (DB tests: `ASSETOPS_TEST_DATABASE_URL` not set; no DBs by rule).
- Adjacent: backend k0, k1 fixtures, k3, k4a, k5, k7 story; host k4a, probe band, probe metric: 232 passed, 4 skipped.
  In the clean worktree, all of these plus `tools/checks/test_fuel_wording.py`: 283 passed, 13 skipped.
- Frontend estate tests: 2 files, 33 passed (the two fixture-reading tests confirmed running).
- `node --test tools/checks/test_evidence_checks.mjs`: 12 pass; `node tools/checks/mock-deviation-labels.mjs`: OK.
- `probe_kisiwa_fuel.py --check`: current. `probe_kisiwa_nights.py --check`: see deviation 1.
- Layout evidence: not run (no UI change).

## Known deviations

1. `probe_kisiwa_nights.py --check` (DIESEL-1 G6) was "current" before the move and is now "stale": the fresh run
   writes `assumptions.template: host/fixtures/diesel-d0/...` while the committed, byte-identical result says
   `.agent/DIESEL-D0/...`. That line is the only difference (template sha256 unchanged). No test reads D0's result.
   The dispatch says to keep content identical; the fix is one `--write`, which is a coordinator call.
2. The destination folder did not exist (the brief said it did); `/opt/assetecon/evidence/` held only `PIPE-1/`.
3. The 10 root `.agent/*.py|sh` one-off scripts, the 4 root HTML pages and all `.agent/` text stay tracked: §3.5 makes
   scripts a reference-grep review (step 5) and step 4 gives text its homes. The guard allows exactly that shape.
4. No `tasks/` file exists for the declutter steps; status is in this packet and `.ai/NOW.md`.

## Residual risk and review focus

- Corrected in revision 2 (M4): merging this branch into a worktree makes git delete that worktree's copies of the
  22,300 untracked files (they leave the index, so a checkout that moves to the new `main` removes them). Nothing is
  lost: `/opt/assetecon/evidence/repo-untracked-2026-11-18/` (manifest, sha256-verified) and the coordinator's backup
  `/opt/assetecon/evidence-backup-2026-11-18/` hold everything. See "How lanes merge main after step 3".
- The spec counts about 580 comment citations; those pointing at `.agent/<ID>-evidence/...` now resolve under the evidence folder by the
  same relative path under `/opt/assetecon/evidence/repo-untracked-2026-11-18/` (provenance, not runtime).
- Review: the class rules in `inventory.py` (`classify`), the 9-path exception list, the guard regexes, and that
  nothing in classes c/d left the index.

## Revision 2 (review `.agent/review-declutter-03.md`, REVISE)

| Finding | Fix | Evidence |
| --- | --- | --- |
| M1 retention root | `EVIDENCE_ROOT` fixed at `/opt/assetecon/evidence`; `--root` must resolve to it or below; every deleted path is re-checked against `EVIDENCE_ROOT`, symlinks are skipped in manifests and refused on delete | `--root /`, `--root /opt/assetecon/evidence-backup-2026-11-18`, `--root /opt/assetecon/evidence/../evidence-backup-2026-11-18` and a symlink `evidence/ZZ-escape-link -> scratch` each exit 1 "refusing --root ... outside /opt/assetecon/evidence" (link removed) |
| M2 retention clock | Item date = max(newest last_commit_date, `COPIED_AT`); `COPIED_AT` = 2026-11-18 written once in the batch folder; an item is due at 14 or more days | Listing 2026-11-18: 0 items (282 checked, 368 capture scripts kept). `--today 2026-12-01`: 0. `--today 2026-12-02`: 282 items, 21,953 files, 1,698.9 MB (first possible purge; owner asked first) |
| M4 merge deletes files | Packet residual risk, RULES §9 and NOW say it plainly and give the read path | below |
| M3 (coordinator) | Not touched here | `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/tools/rebase-log.txt` on the Layer 4 and gtm lanes matches `*-log.txt` (guard and `.gitignore`) and must be renamed before those lanes merge `main` |
| L1 G6 | `probe_kisiwa_nights.py --write` | diff is only `host/fixtures/diesel-d0/probe-result.json:67` (`.agent/DIESEL-D0/...` to `host/fixtures/diesel-d0/...`); `--check`: "probe result current (G6 pass)"; fuel `--check`: current |
| L2 ignore = guard | `.gitignore` adds `*.out`, `*-log.txt`, `*-last.txt`, `**/*-wip/`, `**/*-probe/`, `*.jsonl` with negations for `fixtures/`, `__fixtures__/`, `contract-fixtures/` | `git ls-files -ci --exclude-standard` outside `.agent/`: 0 (the two `contract-fixtures` jsonl needed the third negation). New `zz-wip/`, `zz-x-probe/`, `s.out`, `a-log.txt`, `a-last.txt`, `t.jsonl` ignored; `backend/tests/fixtures/zz/ok.jsonl` not |
| L3 cap | 1 MiB kept; guard docstring says lower it after step 4 | - |
| L4 capture scripts | Batch `*.py`, `*.mjs`, `*.sh` kept by default (368); `--include-scripts` lists them | Delete test in a temporary `evidence/ZZ-retention-selftest/` (removed after): a wrong phrase aborts; the right phrase deleted `a.png`, kept `capture.mjs`, skipped a symlink to a scratch file (target intact), logged one line; test log removed |

### How lanes merge main after step 3

1. In the lane, list tracked files the new guard would reject: `python tools/checks/tracked_evidence.py`
   (after merging, or on the lane first with the guard file copied in). Rename or move any evidence-shaped file the
   lane added (a `*-log.txt`, `*.log`, png, or file in a `*-evidence*`/`*-captures*` folder) out of the tree, to
   `/opt/assetecon/evidence/<task>/<run>/`, and `git rm --cached` it.
2. Commit any edit the lane made to an untracked `.agent/` evidence file first (or copy it out); otherwise the merge
   stops on a modify/delete conflict for that path. Resolve such a conflict by keeping the deletion and copying the
   lane's version to the evidence folder.
3. `git merge main`. Git removes the lane's local copies of the untracked evidence; read them at
   `/opt/assetecon/evidence/repo-untracked-2026-11-18/.agent/...`.
4. `pwsh -NoProfile -File tools/check-all.ps1`; it must pass, including "Tracked evidence and logs".

### Step 4 addendum (2026-11-18, declutter step 4)

5. After step 4 merges, the same merge also moves `.agent/` specs, owner files and history (owner files to
   `owner/`, specs to `specs/<ID>/`, the rest to `archive/agent-history/`). Follow "How lanes merge main after
   step 4" in `specs/DECLUTTER/packet-declutter-04.md`: merge with `git -c merge.renameLimit=20000 merge main`
   so rename detection carries the lane's edits, then move any `.agent/owner-*.md` or build sheet the lane added
   (with its index row) before check-all.
