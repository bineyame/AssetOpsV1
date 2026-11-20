# Packet: declutter step 4a, specs, owner files and history out of `.agent/`

- Branch `task/declutter-04-specs-history` (worktree `/opt/assetecon/AssetOpsV1-declutter4`), from `bae760425`
  (main `a87224025` + owner note). Spec: `specs/DECLUTTER/repo-declutter-recommendation-2026-11-18.md` §2.2-2.4,
  §3.3-3.4, §4.2 step 4, §4.3 option (b), §4.4, §5; owner O4 and "go ahead with declutter step 4"
  (`owner/owner-repo-declutter-request-2026-11-18.md`).
- This packet lives in `specs/DECLUTTER/` under the new RULES §9 (a spec's packets go in its folder).
- USER_REVIEW_REQUIRED: false (no product behaviour; owner files moved, not edited or archived, per O4).

## Commits

| Commit | What |
| --- | --- |
| `2bb07c2e6` | 186 owner files `.agent/` -> `owner/` (R100) |
| `d92b9c3f2` | 54 sheets/specs -> `specs/<ID>/spec.md`, 6 declutter files -> `specs/DECLUTTER/` (R100); `tools/declutter/step4_map.py`, `move_step4.py` |
| `6f87fb199` | 24 over-cap sheets split by their headings; `split_specs.py`; `specs/<ID>/README.md` line maps |
| `b81b226c5` | 1,840 finished-work files -> `archive/agent-history/` (R100) |
| `6dd360644` | one header line per archived file (`archive_headers.py`) |
| `454b44294` | coordinator handoff trimmed to one block (4.3 KB); full text verbatim in `.ai/history/coordinator-handoff-to-2026-11-18.md` |
| `3f978b096` | `tools/declutter/rewrite_citations.py` |
| `43dde2ca5` | mechanical: output of the rewrite script, nothing else |
| `10bae7ff9` | RULES §9, indexes, guards, `specs/CITATION_MAP.md`, START_HERE/AGENTS/ROLE_CONFIG/NOW wording |
| `4b9b5c3fc` | `check_links.py`, rewrite `--verify`, step-3 lane-note addendum, built state |
| (last) | this packet |

## Moves and proof (re-run each)

- `git ls-files .agent | wc -l`: 2,096 before, 10 after.
- `python tools/declutter/move_step4.py --verify`: `2096 BASE files {'archive': 1840, 'keep': 10, 'specs': 60,
  'owner': 186}; all byte-identical` (archived: BASE bytes after the one header line; `packet-declutter-03.md`:
  BASE bytes as prefix of the step-4 addendum; the two must-not-change kept files byte-identical). The pure move
  commits show as R100 in `git show -M --stat`.
- `python tools/declutter/split_specs.py --verify`: `24 verified, 0 problem(s)`; each sheet is reassembled from its
  parts through its README map and compared with the `bae760425` blob (e.g. OWN-GAPS 10 parts, 524 KB; DIESEL-1
  15 parts, 668 KB). Rule: a level-1/2 heading section (level 3 inside a section over 60 KB, keeping its parent's
  kind) goes to `rulings*.md` when its heading names a ruling/closure/amendment/answer/pre-flight/revision/stop/
  question round or starts with a decision ID; else `spec*.md`; parts packed to at most 60 KB in order.
- Handoff archive: `tail -c +<len(header)+1>` of the history file equals `bae760425:.agent/coordinator-handoff.md`.

## What stays in `.agent/` (10 tracked; reasons in `step4_map.py` KEEP)

`coordinator-handoff.md` (live coordination state), `lane-rules-vps-2026-11-12.md` (live lane rules),
`architect-sequence-client-scope-2026-11-11.md` (live demo-sprint plan, NOW cites it), `backlog-post-demo.md`
(owner picks after the demo), `page-load-architecture-review-2026-11-14.html` (owner D1-D6 pending),
`convertion_potential.html` and `decision-intelligence-mechanism-2026-11-14.html` (owner documents; home is step 5),
`mock-departure-register.md` (read by `mock-deviation-labels.mjs`), `W1-UX-combined-owner-walkthrough.md` (read by
`test_evidence_checks.mjs`; left in place so the reader is unchanged), `owner-walkthrough-notes-2026-11-01.md`
(pending: uncommitted change in the main checkout; not moved, byte-identical).

## Citations

- `python tools/declutter/rewrite_citations.py`: 2,489 rewritten in 502 files (1,316 -> `archive/agent-history/`,
  380 -> `owner/`, 496 -> `specs/`, 297 bare names in `.ai/decisions/index-*.md`); `:line` mapped exactly (archive
  +1; split sheets through the README map; the index guard now reports 0 stale line pointers). A split-sheet
  citation without a line goes to the part its quoted section titles name, else to the folder `specs/<ID>/`.
- `--verify 43dde2ca5`: `347 code files, 347 changed only in comments/docstrings`. Re-running the rewrite: 0 changes.
- Not rewritten (in `specs/CITATION_MAP.md`): 10 runtime string values (`fuel_cost.py`, `fuel_cost_v2.py`
  model-card `source`/`reviewer`; Kisiwa probe output; `w502_cold_work_walkthrough.py`), data JSON
  (`backend/conversions/`, `config/chain/`, `host/fixtures/`, `productVocabulary.json`), v71/v72 mocks, verbatim
  records (archive, owner files, spec parts, `.ai/history/`).
- `python tools/declutter/check_links.py`: 3,001 distinct cited paths; 333 exist, 2,038 resolve through the map,
  277 are step-3 evidence; **0 broken by this step**; 353 pre-existing unresolved, absent at `bae760425` too
  (prose like `owner/assignee`, files never committed, `owner/SUMMARY.md` from step 4b).

## Guards and rules

- RULES §9: new owner files -> `owner/` with an index row; new specs and rulings -> `specs/<ID>/`; finished text ->
  `archive/agent-history/` or `.ai/history/`; old paths -> `specs/CITATION_MAP.md`.
- `check-decision-index.py`: owner files and spec folders need rows; an owner file or build sheet tracked in
  `.agent/` fails (PENDING allow-lists the notes file); full paths resolve from the root. Self-test 9 faults.
- `tracked_evidence.py`: `owner/` md only, `specs/` md/html/txt, `archive/` md/html/py/sh/txt; delivery-drafts
  allowance removed; cap 1 MiB -> 512 KiB (largest outside fixtures now 0.49 MB). Self-test 16/12 pass.
- `check-agent-workflow.ps1`: requires `specs/CITATION_MAP.md` and the handoff; handoff over 8000 bytes fails.
- `select-tests.py`/`validate-test-selection.py`: `specs/`, `owner/`, `archive/`, `tools/declutter/` need no backend run.
- Fail-on-violation proof (committed first, then `git reset --hard`): an owner file moved back into `.agent/` and an
  unindexed `specs/ZZ-PROBE/` -> index guard 2 FAIL; a png in `specs/` -> evidence guard problems; a 13 KB
  handoff -> workflow guard fails.

## Checks (at `4b9b5c3fc`; node_modules symlinked from main and removed after)

- `pwsh -NoProfile -File tools/check-all.ps1`: `All 36 guards passed (blocking; 3 advisory, 0 warned).` 41.6 s.
- `tools/check-agent-workflow.ps1`: passed. `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` = main .venv): passed.
- `python tools/check-decision-index.py`: OK, 470 IDs, every named file exists, 0 notes.
- `node tools/checks/test_evidence_checks.mjs`: 12/12. `node tools/checks/mock-deviation-labels.mjs`: OK 183 files.
- `pytest backend/tests/test_s4_schedule_install_gate.py` (reads the rewritten registry): 4 passed.
- `npx tsc --noEmit` (frontend): exit 0, 38 s. Changed `.py`: `py_compile` all OK. No full suite.

## How lanes merge main after step 4

Lanes at writing: `task/product-direction-layer4-design` `adf49caab`, `task/gtm-documents` `4e11030ad`; both from
`9e77fb73a` (before steps 2-4), so also follow the step-3 note (`packet-declutter-03.md`, incl. M3 `rebase-log.txt`).

1. `git -c merge.renameLimit=20000 merge main`, so rename detection carries edits across ~2,100 renames.
   Simulated with `git merge-tree`: layer4 merges clean; gtm conflicts only in
   `owner/owner-gtm-documents-request-2026-11-18.md`, the same content conflict it has against `bae760425` at the
   old path (main holds a synced earlier copy). Resolve it there, as the lane would have at the old path.
2. Both lanes add `.agent/owner-grounded-transition-request-2026-11-18.md`; after the merge it is still in `.agent/`.
   In layer4: `git mv` it to `owner/` and add its row to `owner/index-5.md` (date, file, topic, status) in the same
   commit; gtm then takes it by merging layer4 (or does the identical move and row).
3. Any other `.agent/owner-*.md`, build sheet or spec the lane adds later: same rule (`owner/` or `specs/<ID>/` +
   index row); live packets may stay in `.agent/` by named path.
4. Optional, separate commit: `python tools/declutter/rewrite_citations.py` rewrites the lane's own old-path citations
   (idempotent); otherwise they resolve through `specs/CITATION_MAP.md`.
5. Run `python tools/check-decision-index.py`, `python tools/checks/tracked_evidence.py`,
   `python tools/declutter/check_links.py`, then check-all.

## Known deviations

1. No `review.md` parts: no over-cap sheet has a section headed as a review round (reviews were separate files, now in
   `archive/agent-history/`). Spec/rulings filing is by heading keywords; a misfiled section is still verbatim and mapped.
2. Finished packets/reviews/rulings go to one flat `archive/agent-history/`, not into `specs/<ID>/` (recommendation
   §3.4 allows either; mapping 1,840 files to IDs by hand was error-prone).
3. The rewrite also changed citation text in `.ai/decisions/<month>.md`, `.ai/state/<area>.md`, `tasks/` and the six
   live kept `.agent/` files; the step-2 "verbatim split" no longer holds byte for byte for those files (citations only).
4. Archived `.html` files carry the header as an HTML comment before `<!doctype>` (quirks mode if opened).
5. Role briefs still name `.agent/<task-id>-review-packet.md`; RULES §9 now allows that for work without a `specs/`
   folder. Aligning the briefs is left to step 5.

## Residual risk and review focus

- Re-run the five proofs above; spot-check `specs/OWN-GAPS/README.md` and a few rewritten docstrings.
- The KEEP list judgement (live vs finished) and the SUPERSEDED headers (two files).
- `tracked_evidence.py` `-probe$` folder rule would also flag a spec folder named `*-PROBE`.
- Other worktrees with uncommitted edits to moved files will stop on merge; none known besides the main checkout's
  notes file, which stays in place.
