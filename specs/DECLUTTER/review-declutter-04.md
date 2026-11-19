# Review: declutter step 4a (specs, owner files, history)

- Branch `task/declutter-04-specs-history` at `d300464b8` (11 commits after the owner note `bae760425`).
- Reviewer: fresh Claude reviewer, independent of the author. Discovery review (W5). I formed my view from
  the spec, the owner file and the diff before I read the packet.
- Spec: `specs/DECLUTTER/repo-declutter-recommendation-2026-11-18.md` §2.2-2.4, §3.3-3.4, §4.2 step 4, §4.3,
  §5. Owner: `owner/owner-repo-declutter-request-2026-11-18.md` (O4: owner files are moved, not archived or
  edited).

## Verdict: ACCEPT WITH NOTES

The moves are byte-exact and fully covered. The code rewrite changes comments only. Every `file:line` pointer
the rewrite produced lands on identical text. The guards fail on planted violations. Both lanes merge `main` as
the packet describes. Nothing live was archived. No finding is High or Medium. The five Low findings below can
be fixed on this branch or at the start of step 5; none blocks the merge.

## Summary

- Owner files: 186 pure renames (`R100` at `-M100%`), no edits. No owner file was archived.
  `owner-walkthrough-notes-2026-11-01.md` stays in `.agent/`.
- 24 split sheets rebuild byte-for-byte from their parts. 35 other spec files are R100 moves. Each of the
  1,840 archived files is its base bytes plus exactly one header line. The handoff history copy is the old
  handoff plus one header line.
- The citation rewrite changed comments and docstrings only, across all 347 code files. All 316 `:line`
  pointers produced land on the same text. All 72 title-routed split-sheet citations land in the part that
  holds that heading.
- `specs/CITATION_MAP.md` resolves all 2,096 base `.agent/` files.
- check-all passes (36/36). `check_links.py` finds 0 links broken by this step.

## Findings (ranked)

### L1 (Low): RULES §9 says more about `.agent/` than any guard enforces, and the briefs still write there
`.ai/RULES.md:181-184` says the only tracked files in `.agent/` are the step-4 KEEP list. Two things contradict
it:
- `.ai/RULES.md:173` still allows `git add -f` on a named `.agent/` file.
- `.claude/agents/assetops-implementer.md:65` still writes `.agent/<task-id>-review-packet.md`.

No guard checks KEEP. I planted a tracked `.agent/review-PLANT-new.md`, and both `check-decision-index.py` and
`tracked_evidence.py` passed it. Only owner files, build sheets and nested paths are caught. As a result,
`.agent/` will grow again from the next slice, against recommendation §5.1 and §5.5 ("never force-add";
"fail on tracked files under `.agent/` except an allow-list"). Packet deviation 5 defers aligning the briefs to
step 5, but the RULES sentence is inaccurate now.

Fix: reword the RULES sentence to match current practice, or check root-level `.agent/` files against
`step4_map.KEEP` in `tracked_evidence.py` (rule 5) once the briefs move packets to `specs/<ID>/`. Either one
suffices for this step; the guard can wait for step 5.

### L2 (Low): the step-2 "verbatim split" claim is now false, and its proof tool fails silently
`.ai/decisions/INDEX.md:3-4` still says the four parts "concatenate, in this order, to the original". The
rewrite changed citations in `.ai/decisions/<month>.md` and `.ai/state/<area>.md` (packet deviation 3).
`python tools/check-split-preservation.py` now reports
`FAIL decisions: 4 parts, 506100 bytes vs original 504986` and FAIL on the state sections. The tool is not in
check-all, so nothing shows the failure.

Fix: amend the INDEX.md sentence ("verbatim at `10bae7ff9^`... except step-4 path rewrites"), and either
point the tool's docstring at a revision where the proof holds or make it undo the step-4 path rewrite
before it compares.

### L3 (Low): the handoff trim drops a few operational items that still matter
`.agent/coordinator-handoff.md` (4,353 bytes) keeps the active lanes, worktree paths, the walk DB and ports,
the pending owner decisions (page-load D1-D6, the Grow card, D-SR.81, whether the demo happened), the evidence
root, DB rules, the network rule and the check-all rule. These items are only in
`.ai/history/coordinator-handoff-to-2026-11-18.md`:
- Owner access to the walkthrough: the Tailscale server and owner-device addresses, and the SSH tunnel for
  5490 (history line 226).
- How to restart the walk serve and Vite: `setsid -f <scratchpad>/walk-serve.sh`, the log path, and
  `npm run dev -- --port 5490 --strictPort` with `ASSETOPS_API_PORT=8990`.
- `ASSETOPS_GUARD_PYTHON` for `check-architecture.ps1`.
- "Restart only when no agents are running".
- Test debt: rerun `test_ch5c2_real_composers_postgres.py` with a DB URL.
- The page-load re-review's P1/P2 detail (the review is now in `archive/agent-history/`; the handoff names
  P1/P2 but not where they are).

All but the last are absent from RULES, ROLE_CONFIG, NOW, the lane rules and `backend/TESTING.md`. The owner
walkthrough is still pending, so the first two are the ones a resuming coordinator would need.

Fix: add 3-5 lines to the current block (it has about 3.6 KB of headroom under the 8,000-byte cap).

### L4 (Low): live decisions now sit in files headed "Finished; historical"
39 index lines with status `live` name an archived source. Examples:
- `archive/agent-history/architect-handoff-demo-plan-2026-11-04.md` (11 IDs);
- `architect-plan-pre-client-2026-11-10.md` (5);
- `SR-4c-review.md` (2).

The live backlog and plan (`.agent/backlog-post-demo.md`, `.agent/architect-sequence-client-scope-2026-11-11.md`)
also cite archived architect answers as their design basis (money snapshot, price-it, any-range speed).
`.ai/decisions/INDEX.md` explains that rulings live in archive files. Still, an agent that opens one of these
files reads "Finished; historical" above a decision that is still live.

Fix (optional): use a header variant for archived files that a `live` index line names, for example
"Finished work; holds decisions still indexed as live in .ai/decisions/".

### L5 (Low/Info): stale line pointers into the trimmed handoff
The kept, owner-facing `.agent/page-load-architecture-review-2026-11-14.html` cites
`.agent/coordinator-handoff.md:110` (line 301) and `:61, 105-132` (line 405). The handoff now has 80 lines.
These citations resolve only through CITATION_MAP rule 5 (+1 to
`.ai/history/coordinator-handoff-to-2026-11-18.md`). The rewrite skipped them because the handoff path is
"kept".

Fix: rewrite the two pointers to the history file at +1, or accept them under rule 5.

### Info
- `tools/declutter/move_step4.py --verify` reads the working tree, so it fails as soon as an owner file
  legitimately changes. During this review, someone else appended a "step 5" owner instruction to
  `owner/owner-repo-declutter-request-2026-11-18.md` in this worktree; it is uncommitted, and I left it alone
  and did not commit it. The verify then reported
  `FAIL bytes differ: owner/owner-repo-declutter-request-2026-11-18.md`. At HEAD the file is R100. To make the
  proof durable, read blobs from the move commits rather than the working tree.
- `archive/agent-history/T026-phase-2-probes.sh`: the header line pushes the shebang to line 2. The file is
  archived and never run.
- `tools/vps-setup-ubuntu.sh:70`: an `echo` runtime string was rewritten, because `.sh` files are rewritten
  everywhere. The new text is correct and the change is harmless.
- The `archive/*.html` header sits before `<!doctype>` (packet deviation 4). Accepted.

## What I verified, and how (own scripts, not the author's)

1. **Owner files.** `git diff -M100% --name-status bae760425 HEAD`: 186 `R100 .agent/owner-* -> owner/`. The
   only `M` entries under `owner/` are the six index files, which change path wording only. 28 `.agent/*owner*`
   files that are not owner words (walkthrough scripts, proposals, architect replies) went to the archive;
   I spot-checked them and they are agent-authored.
2. **Splits.** I wrote my own reassembler. It parses each `specs/<ID>/README.md` table, concatenates the part
   line ranges in row order, and compares the result with the `bae760425` blob. It also checks that every part
   is covered contiguously and that no extra file exists. Result: 24/24 identical. The 35 other spec moves are
   R100. No `specs/` file exceeds 60 KB.
3. **Archive.** Using `git cat-file --batch` on all 1,840 files: everything after the first line is identical to
   `bae760425:.agent/<same path>`. Each header names its own source path. The header kinds are:
   - 1,827 `> Finished; historical`;
   - 10 `#` (py/sh);
   - 1 `<!-- -->` (html);
   - 2 `Superseded by` (`lane-rules-2026-11-12` superseded by the VPS rules; `current-plan-pointer` superseded
     by NOW).
4. **Handoff history.** `tail -n +2` of the history file is identical to `bae760425:.agent/coordinator-handoff.md`.
5. **Rewrite.**
   - `rewrite_citations.py --verify 43dde2ca5`: 347/347 code files changed only in comments or docstrings.
   - Python: all 246 changed `.py` files have an identical AST once docstrings are removed.
   - TS/JS/mjs/css: every changed line in the 98 files is inside `//`, `/* */` or `*` comment lines. The TS
     scanner flagged 9 files; I read their hunks and each is a misparse of comment-only edits.
   - Not rewritten, and unchanged since base: the `fuel_cost.py` and `fuel_cost_v2.py` `source`/`reviewer`
     values, the probe output strings, `backend/conversions/*.json`, `config/chain`, `host/fixtures`,
     `productVocabulary.json`.
   - No code reads a moved path. The only remaining runtime `.agent` reads are the KEEP files
     (`mock-departure-register.md`, `W1-UX-combined-owner-walkthrough.md`) and the `W5-F1` output dir.
6. **Line pointers.** I paired every `-`/`+` line in the rewrite diff and compared the cited text at
   `bae760425:<old>:N` with `HEAD:<new>:M`. 316/316 are identical, covering the archive (+1), split sheets
   through README maps, and bare names in the decision indexes. Three pairs could not be paired
   automatically; I read them by hand and they are correct (kept files left unchanged). All 72 title-routed
   citations into split sheets land in a part whose headings contain the quoted title.
7. **Citation map.** All 2,096 base `.agent/` files resolve: 10 kept, 186 owner, 1,840 archive, and 60 through
   the table, each target existing.
8. **Archive selection.**
   - I sampled 40 archived files at random (seed 4): all are finished handoffs, reviews, packets, briefs,
     questions or probes of merged work.
   - Live material stays outside the archive: the OWN-GAPS and DIESEL-1 rulings are in `specs/`, and every
     file NOW or START_HERE cites is kept. The newest archived items (WALK-perf ruling, AP-1, the
     page-load and decision-intelligence reviews) belong to merged work.
   - See L4 for the decision texts that indexes point to.
9. **Guards (planted, then removed; the tree is clean afterwards).**
   - `check-decision-index.py` failed six ways: an owner file in `.agent/`, a build sheet in `.agent/`, an
     unindexed owner file, and an unindexed spec folder.
   - `tracked_evidence.py` failed six ways: json in `specs/`, html in `owner/`, png in `archive/`, a 600,000-byte
     txt over the 524,288 cap, and `.agent/sub/x.md`.
   - `check-agent-workflow.ps1` failed on an 8,353-byte handoff.
   - Gap: a root `.agent/review-*.md` passes (L1).
   - Both self-tests pass.
10. **Lanes.** `git -c merge.renameLimit=20000 merge-tree --write-tree` (lane branches unchanged):
    - `task/product-direction-layer4-design` `adf49caab` merges cleanly.
    - `task/gtm-documents` `4e11030ad` conflicts only in `owner/owner-gtm-documents-request-2026-11-18.md`,
      the same conflict it has at the old path against `bae760425`.
    - Both merged trees keep `.agent/owner-grounded-transition-request-2026-11-18.md`; the index guard
      rejects it until it is moved as packet step 2 says.
    - `task/declutter-04b-owner-summary` also merges cleanly.
11. **`select-tests.py`.** No backend, host, contracts or gateway code or test reads `specs/`, `owner/`,
    `archive/` or `tools/declutter/`. Archive `.py` files are not on any import root, and `*.md` was already
    exempt. Skipping the backend for these paths is safe.
12. **Links.** `check_links.py`: 3,008 cited paths; 338 exist, 2,038 resolve through the map, 277 are step-3
    evidence; **0 broken by this step**; 355 were already unresolved at base.

## Checks run (at `d300464b8`)

- `pwsh -NoProfile -File tools/check-all.ps1` (node_modules symlinked from main, then removed):
  `All 36 guards passed (blocking; 3 advisory, 0 warned).` 43.1 s.
- `tools/check-agent-workflow.ps1`: passed. `check-decision-index.py`: OK (470 IDs); `--self-test`: 9 faults.
  `tracked_evidence.py`: 0 problems; `--self-test`: pass.
- `node tools/checks/test_evidence_checks.mjs`: pass. `node tools/checks/mock-deviation-labels.mjs`:
  `OK 183 files`.
- `pytest backend/tests/test_s4_schedule_install_gate.py -q`: 4 passed.
- `split_specs.py --verify`: 24 verified. `rewrite_citations.py --dry-run`: 0 rewritten (idempotent).
- `move_step4.py --verify`: 1 problem, caused only by the uncommitted foreign edit (Info).
- `tools/check-split-preservation.py`: FAIL (L2).

Not run: the full suite (policy), DBs, Docker and ports 5490/8990. I did not run `tsc`; the implementer reports
exit 0, and my token and comment checks cover the TS changes.

## Residual risk the packet does not name
- Other worktrees (53 in total) with uncommitted edits to moved `.agent/` files will stop on merge. The packet
  names only the main checkout's notes file. I did not survey the other worktrees.
- Live owner files can still receive verbatim appends, as happened during this review. Each append is a
  legitimate edit that the R100 history cannot show, so later "verbatim" proofs must pin a commit.
