# Packet: declutter step 5 (Docs and tools) plus step-4 notes L1-L5

- Branch `task/declutter-05-docs-tools`, from `main` `d05bf668c`; 12 commits `f1f3866c9..HEAD`.
- Spec: `specs/DECLUTTER/repo-declutter-recommendation-2026-11-18.md` §1.5, §1.7, §3.4-3.5, §4.2 step 5, §5.
  Owner: `owner/owner-repo-declutter-request-2026-11-18.md` ("go ahead with declutter step 5 after the review";
  O5 deferred: no worktree pruning, no history rewrite). Step-4 review: `specs/DECLUTTER/review-declutter-04.md`.
- USER_REVIEW_REQUIRED: false (repo organisation; no product behaviour). `owner/SUMMARY.md` not touched.

## What moved (`tools/declutter/step5_map.py`; `move_step5.py --verify`: 49/49 hold the base bytes plus at most one header)

| Group | From -> to | Header |
| --- | --- | --- |
| 9 superseded Sept designs (simulator v1-v3, two alignments, two multi-vertical, mini-grid roadmap, declared-capability reflection) | `Docs/` -> `Docs/archive/2026-09/` | "Superseded by X on 2026-11-18" |
| 3 owner texts (`multi-vertical-brief-verbatim`, `queue-review-feedback-verbatim`, owner draft `lab-cockpit-proposal`) | same | none: owner words are never edited; status in `Docs/archive/README.md` (Known deviation 1) |
| 2 owner-facing HTML (`convertion_potential`, `decision-intelligence-mechanism-2026-11-14`) | `.agent/` -> `Docs/demo-sprint/` (step-4 KEEP said "its home is step 5") | none (live) |
| 4 retired guards + 2 JSON only they read | `frontend/docs/architecture/` -> `archive/frontend/docs/architecture/` | "Retired ..." (JSON: none; README) |
| S1-S7 queue tables | `tasks/README.md` -> `tasks/archive/site-first-2026-10/queue-tables.md`; new short `tasks/README.md` | Superseded |
| 28 finished one-off probes/evidence scripts | `tools/` -> `archive/tools/` | "Finished; historical." (2 shebang files: header on line 2) |

Kept in `Docs/`: `simulator_design_v4.md` and `simulator-scenario-authoring-and-runtime.md` (normative per
`.ai/ARCHITECTURE.md`; no `simulator/` docstring cites any version), the owner's
`AssetOps_MiniGrid_Technical_Walkthrough.md`, `Product/` (v6.9 PDF), `Site_Line_Diagrams/`, `UI Design/`,
`engineering/`, all of `demo-sprint/` (cited as current by NOW, the live plan, backlog and owner documents).

**Why `archive/tools/`, not `tools/archive/`:** `archive/` is already outside default reads and grep (RULES 9),
selects no tests in `select-tests.py` (`archive/*`), and is outside the `tools/*.mjs` browser-script inventory in
`tools/checks/test_evidence_checks.mjs`; `tools/archive/` would be on all three paths.

**Tools method (reference check first).** A script was kept when any live file names it (basename or module
stem): check-all and `tools/check*`, `tools/checks/**`, backend/host/frontend code and tests, config,
docker-compose, `.gitattributes`, README/TESTING/RULES/NOW/START_HERE, `.claude/`, every kept `.agent/` file
(W1-UX owner walkthrough, live plan, backlog, page-load), `Docs/engineering`, `Docs/demo-sprint`, or a kept
script (transitive closure). Finished packets, specs, archive, decisions and state did not count. 110 kept, 32
candidates; 4 candidates kept on judgement: `check-split-preservation.py` (L2), `vps-setup-ubuntu.sh` (machine
setup), `profile-summary.py` (pairs with the live `profile-tests-in-container.*`), `walk1_4_identity_gate.sh`
(walkthrough lane, still open). Kisiwa probes stay (host/backend tests import them). The evidence-width inventory
still finds 28 browser scripts (needs >= 20; all 14 named ones kept).

## Guards retired (check-all)

Before (`d05bf668c`, this worktree): `All 37 guards passed (blocking; 3 advisory, 0 warned)`, 40 `[PASS]` lines,
228.9 s. After (`9f5c99661`): `All 36 guards passed (blocking; 0 advisory, 0 warned)`, 43.0 s. The 3 advisory
guards are gone; the blocking set is unchanged: the 37th, the estate self-tests, ran before because the branch
equalled `main`, and now SKIPs as designed (writer guard unchanged against main; it runs with `-Full` and on main). Retired: "v69 dependency registry and S1-S7 queue (advisory)", "Delivery checker fixtures,
S1-S7 (advisory)", "v69 screen ledger (advisory)". Readers checked first: `check_mock_gaps.cjs`/`test_mock_gaps.cjs`
read only `mock_gaps.cjs` and the registry, panel-contract and screen-ledger JSON (all stay; blocking, 13/13
fixtures pass); `delivery_next_work.cjs` was required only by the two retired scripts; nothing else in tools,
backend, host or frontend/src reads the moved files or `tasks/README.md` (`check-agent-workflow.ps1` reads
`tasks/T*.md` only). README "Guards" no longer documents the retired next-work commands.

## Citations

`move_step5.py rewrite`: 49 citations in 37 files, 0 left in code values (step-4 language-aware spans: code
changed only in comments/docstrings). `specs/CITATION_MAP.md` "Step 5" maps the rest (`:N` -> `:N+1` where a
header was added). `check_links.py` now also covers `tools/` and `frontend/docs/` paths, the step-5 map, and
`.agent/` folder citations whose files moved together (`--base` option).

## Step-4 follow-ups

- **L1:** RULES 8/9 now agree: `.agent/` tracks only `AGENT_KEEP` in `tools/checks/tracked_evidence.py`
  (8 files); rule 5 fails anything else. Planted `.agent/review-PLANT-new.md` (staged with `-f`): `1 problem(s)`;
  self-test adds 3 bad and 3 good paths (19/15, pass). Briefs (implementer, reviewer, planner, architect) send
  packets, reviews, handoffs and rulings to `specs/<ID>/`; no `.agent/` write path remains in `.claude/`.
- **L2:** `.ai/decisions/INDEX.md` and `.ai/state/INDEX.md` say the split was verbatim at the split commit, with
  path rewrites (and new state entries) since. `check-split-preservation.py` reads the parts at the split commit
  by default: `OK decisions ... 504986 bytes`, `OK state: 138 sections`; `--worktree` is documented to FAIL.
- **L3:** handoff (5,131 bytes, cap 8,000) gains, copied from the history file: serve and Vite commands, owner
  Tailscale/SSH-tunnel access, `ASSETOPS_GUARD_PYTHON`, "Restart only when no agents are running.", the ch5c2
  rerun debt, and P1/P2 at `archive/agent-history/page-load-architecture-review-2026-11-14-review.md:331`, `:342`.
- **L4:** chose the header over index annotations: the misleading text is where the agent reads it, index lines
  stay under cap, and it also covers the 5 archived architect answers the live plan/backlog build on. 30 files
  (25 from 38 live index rows + 5) now read "Finished work; its decisions remain live per
  `.ai/decisions/INDEX.md`." (`step4_map.DECISION_BEARING`; same line count). `move_step4.py --verify` now
  follows step-5 moves and accepts append-only owner files (review Info): `2096 BASE files ... 1 owner file(s)
  appended to; all byte-identical`.
- **L5:** the page-load HTML pointers were written against the handoff at `bc8fe7077`, so the +1 rule would land
  3 lines early; they now cite `.ai/history/coordinator-handoff-to-2026-11-18.md:114` and `:65, 109-136`
  (range checked by diff).

## Checks (HEAD `9f5c99661` for content; packet commit follows)

- check-all (fast, node_modules symlinked from the main checkout, link removed after): `All 36 guards passed
  (blocking; 0 advisory, 0 warned)`, 0 FAIL/WARN, exit 0; log in the session scratchpad.
- `check-agent-workflow.ps1`: `Agent workflow check passed.`
- `check-decision-index.py`: `OK (470 indexed decision IDs; every cited ID resolves; every named file exists)`.
- `check_links.py --base d05bf668c`: `3306 distinct cited paths; 529 exist, 2086 resolve through the step-4/5 maps,
  277 are step-3 evidence; 0 broken since d05bf668c; 414 pre-existing`. Default base (step 4): 0 broken.
  Planted (removed `Docs/archive/2026-09/simulator_design.md`): `1 broken`, restored.
- `select-tests.py --files` (Docs archive, archive/tools, archived guard, tasks/README, a brief): `mode: none`;
  `--files tools/checks/tracked_evidence.py`: none. `--base d05bf668c`: full (comment edits in `mock_gaps.cjs`,
  `check_mock_gaps.cjs`, and `check-split-preservation.py`); no full suite run (owner rule).
- Focused: `node --test test_mock_gaps.cjs` 13/13; `check_mock_gaps.cjs` valid (36 gaps); tracked-evidence
  self-test pass. `npx vitest related` on the two cjs files: not run to completion (vitest tries to parse a
  backend `.py` file; comment-only change, no frontend import).
- `git ls-files | wc -l`: 5,316 -> 5,321 (+5 new: two READMEs, two declutter scripts, short `tasks/README.md`;
  moves keep the count). `tools/` root files 142 -> 114; `Docs/` root entries 20 -> 9.

## Known deviations

1. Owner verbatim texts and the owner draft have no "Superseded" header (owner files are never edited, O4
   practice in step 4); their status is in `Docs/archive/README.md`.
2. Two JSON files have no header (no comment form); `tracked_evidence.py` allows JSON only under
   `archive/frontend/docs/architecture/`, and archive scripts (mjs/cjs/js).
3. The two moved owner HTML files and `tasks/README.md` change paths that the Layer 4 and GTM branches may cite;
   CITATION_MAP resolves them.
4. `.ai/ARTIFACT_INDEX.md`, `FEATURE_MAP.md` and other stale `.ai/` planning files were only path-rewritten
   (out of step-5 scope).

## Review focus

The keep/archive call per tool (method above); the retired-guard reader check; L4 file set; the relabel keeping
`move_step4.py --verify` exact; `AGENT_KEEP` against what lanes still force-add.
