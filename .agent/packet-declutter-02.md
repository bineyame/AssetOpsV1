# Packet: declutter step 2 (indexes; DECISIONS and CODE_STATE split)

Branch `task/declutter-02-indexes` (worktree `/opt/assetecon/AssetOpsV1-declutter`, from `main` `e0b911b45` plus the owner's step-2 file `944b0d4fb`).
Spec: `.agent/repo-declutter-recommendation-2026-11-18.md` §2.2-2.3, §4.2 step 2, §5.3-5.6; owner words
`.agent/owner-repo-declutter-request-2026-11-18.md` ("go ahead with declutter step 2"). USER_REVIEW_REQUIRED: false
(text moves and indexes only; the owner-file status column feeds the later O4 summary, which the owner confirms).

## Commits
- `916d317f2` split verbatim into `.ai/decisions/` and `.ai/state/`; `tools/check-split-preservation.py`
- `15622acc6` `.ai/DECISIONS.md`, `.ai/CODE_STATE.md` become redirect stubs
- `5abdf6938` indexes + `tools/check-decision-index.py`, blocking in `tools/check-all.ps1` with a self-test
- `6abb065f1` fix: guard skips its own planted IDs; a drifted `file:line` is a note (see below)
- `3326c4d85` AGENTS, START_HERE, NOW, RULES §9, implementer brief, agent-workflow required files
- this packet

## What moved where
- Decisions (505 KB): four contiguous parts that concatenate to the original: `2026-10-late.md` (10-07..10-23,
  newest first, as it was prepended; 83 KB), `old-index-2026-10.md` (the old in-file index; 17 KB), `2026-09.md`
  (182 KB), `2026-10-early.md` (211 KB). Month split, contiguity kept so plain concatenation proves preservation.
- Built state (525 KB): 138 `## ` sections into 11 area files: overview 15, tools 7, shell 41, lab 208, data 41,
  findings-money 44, work 20, cold-ev 18, estate 21, demo 19, sites 78 (KB). Each file keeps its sections in
  original relative order; `index-*.md` numbers give the original global order.
- Each split file has one 2-line header ("Moved verbatim from ... part N of M").

## Indexes (cap 2k tokens; measured bytes/4, all multi-byte punctuation counted as bytes)
| Index | Lines | Max size |
| --- | --- | --- |
| `.ai/decisions/INDEX.md` + 11 `index-*.md` | 470 IDs: 173 dated in the parts (+1 external, `D-2026-10-19-w2-03-followup`), 297 index-only rulings (D-SR 97, D-E5 52, D-W1 23, D-UQFI 18, D-ANY 13, D-E2 13, D-AW 11, D-UP 12, D-E4 11, D-WARM 8, D-E3 4, others) | 6.6 KB, ~1.65k tok |
| `.ai/state/INDEX.md` + 2 `index-*.md` | 138 sections | 6.3 KB, ~1.57k tok |
| `specs/INDEX.md` | 54 sheets/specs: 2 live (OWN-GAPS, DIESEL-1), 52 finished, 0 superseded (partial replacements in notes); 24 over the 15k-token spec cap | 6.5 KB, ~1.63k tok |
| `owner/INDEX.md` + 5 `index-*.md` | 187 owner files: 48 current (22 "to confirm"), 11 superseded, 128 historical; INDEX lists the current ones | 6.4 KB, ~1.6k tok |

Decision status: `live` unless the text says so. Five explicit supersessions recorded (e.g.
`D-2026-09-17-client-demo-readiness` by `D-2026-09-24-v4-roadmap-replan`); "amended xN" from amendment lines; for
rulings, a search for supersedes/reverses/narrows near the ID gives "<verb> in part? see file:line" (22 such).
45 early decisions have no ID; the index says to find them by date heading. Locations: §2.2 as proposed
(`specs/INDEX.md`, `owner/INDEX.md`); the files they list stay in `.agent/` until step 4.
Spec and owner status columns came from two read-only classification subagents; the rows they were least sure of are
marked "to confirm" in the notes.

## Checks (real output)
- `python tools/check-split-preservation.py` (original from `916d317f2^`):
  `OK decisions: 4 parts, 504986 bytes vs original 504986 bytes`;
  `OK state: 138 sections in 11 area files, 525239 bytes vs original 525239 bytes`.
- `python tools/check-decision-index.py`: `OK (470 indexed decision IDs; every cited ID resolves; every named file
  exists)`, 1.8-2.9 s. It scans all tracked text (`git grep`, including `.agent/`); dated prefixes resolve wrapped
  and bare-date citations; file names such as `D-SR63-67-review.md` are skipped.
- Planted failures in the tree (then `git checkout`/restored): a line citing `D-SR.9999` and
  `D-2026-12-01-no-such-decision` in `.ai/NOW.md`, and `.agent/build-sheet-CH-6.md` moved away, gave exit 1 with
  `FAIL specs/INDEX.md:41: names a missing file build-sheet-CH-6.md` and two `unresolved decision ID` lines.
  `--self-test` (in check-all) plants an ID and a missing file in memory, writes nothing.
- First run flagged the guard's own self-test strings; fixed by excluding the script. A line inserted at the top of
  the OWN-GAPS sheet showed every pointer below it drifting: live sheets grow, so a drifted line is a printed note,
  and only an ID missing from its named file fails.
- `pwsh -NoProfile -File tools/check-all.ps1` at `3326c4d85`: `All 34 guards passed (blocking; 3 advisory, 0 warned)`,
  40.4 s. First run failed 2 guards (missing-claim scan + fixtures) with `MODULE_NOT_FOUND typescript`: this
  worktree has no `frontend/node_modules`. Rerun with a temporary symlink to the main checkout's `node_modules`,
  removed afterwards. Not a change of this branch.
- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: `Agent workflow check passed.`
- No test suite, DB, Docker or port touched.

## Readers of the old files (kept working)
- `tools/check-agent-workflow.ps1`: required-file list (stubs kept; now also requires both INDEX files; its
  cap message points to `.ai/state/`).
- `frontend/docs/architecture/v69-dependency-registry-pilot.json`: 21 `../../../.ai/DECISIONS.md#<ID>` evidence
  links; no guard opens them (`check_v69_dependency_registry.cjs` only checks evidence is non-empty). Unchanged;
  the stub says such links resolve through the index.
- `backend/assetops_backend/evidence/public_provenance.py:3` docstring; `.ai/ARTIFACT_INDEX.md`, `.ai/ARCHITECTURE.md`,
  `.ai/PLANNING_GUIDANCE.md`, `.ai/FEATURE_MAP.md`, `.ai/MILESTONE_REVIEW_BACKLOG.md`,
  `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`, `.ai/history/*`, ~40 `tasks/` files, 5 `Docs/` files: text mentions, served
  by the stubs. 380 `.agent/` files mention them (history).
- Updated: `AGENTS.md`, `.ai/START_HERE.md`, `.ai/NOW.md`, `.ai/RULES.md` §9, `.claude/agents/assetops-implementer.md`.

## Router load
AGENTS + START_HERE + NOW: 8,529 B (~2.1k tok) before, 8,913 B (~2.2k tok) after; each under 1.5k. RULES 12.6 KB
(~3.1k, cap 4k). A decision lookup was a grep in a 505 KB file; it is now a grep in 6.5 KB index parts.

## Known deviations
- State area files are not a plain concatenation of the original (areas interleave in time). The proof checks
  whole sections in order and full byte coverage instead.
- Titles are extracted from each ID's defining line or the old index row, cut to 8-9 words; rulings without a
  definition line point to the first line citing them ("read at the cited line", 20) or, for D-AW-*, to the
  demo-plan handoff because the away log is not tracked.

## Residual risk / review focus
- The guard now fails when a lane cites a new decision ID without an index line (intended, RULES §9); lanes
  writing D-* rulings in `.agent/` must add the line. Tell active lanes.
- Status columns are inference; owner "to confirm" rows and the "in part?" ruling rows need a human read.
- Area mapping of CODE_STATE sections (regexes in the split; list in `.ai/state/index-*.md`).

## Follow-ups
- Layer 4 pack README (pack not on `main`): when it merges.
- Step 4: move specs/owner files, refresh `file:line` pointers, rewrite the 21 registry anchors and code citations.
- 45 unnamed early decisions are not individually indexed.
- Provision `frontend/node_modules` in this worktree (environment).
