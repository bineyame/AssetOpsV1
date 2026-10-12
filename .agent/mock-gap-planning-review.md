# Review: mock-gap closure planning branch (`planning/mock-gap-closure`)

Reviewer: fresh Claude reviewer (independent; did not author any of this work), 2026-10-13.
Scope: `git diff main...planning/mock-gap-closure` (b33fbe1, d7565e2, 59d478e, 6518042, 6fabcc7 merge of main, 5a4847a).
Authority checked against: `.agent/owner-mock-gap-mechanism-2026-10-12.md`, `.agent/owner-mock-gap-confirmation-2026-10-12.md`, `.agent/architect-mock-gap-mechanism-answers.md`, `D-2026-10-12-mock-gap-closure-mechanism`.

## Verdict

**Accept with carries. Ready to merge to `main`.** No blocking finding. The carries below are planning-precision items that must be settled before G-01 activation (F1, F2, F3) or at G-02 refinement (F4), not before this planning merge, because merging activates nothing and changes no scoring.

## Checks run (results as observed)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 212 nodes, 11 linked pilot panels".
- `node frontend/docs/architecture/test_delivery_next_work.cjs`: fail 0.
- `check_v69_dependency_registry.cjs --next-work --out <scratch>/nw.json`: exit 0. Decision `select V-01b` (2.47 vs A-S4-financial 2.215, gap 10.3%, above 10%). `--verify-report <scratch>/nw.json`: exit 0. The scratch report is byte-identical to the committed `.agent/next-work-gap-planning.json` (same decision). No `G-0x`/`I-G-0x` string appears anywhere in the report.
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1 -Python python`: all 6 guards passed (architecture, navigation truthfulness, agent workflow, dependency registry, delivery fixtures, screen ledger: 110 screens / 88 models / 258 panels).
- Not run: frontend Vitest/build (planning-only diff, no frontend source touched); backend pytest (no backend change). Nothing in the diff needs them.

## What I verified as correct

- **Decision scope.** The `.ai/DECISIONS.md` entry's header records exactly the owner's words ("confirm gap catalogue and orphan guard now, defer ranking to W1 exit"), confirms sections 1-2 only, defers non-core ranking and the per-screen completion mechanism to W1 exit (consistent with the owner's earlier accepted "do 1 and 4 now; decide 2 and 3 at W1 exit"), keeps W1 core scoring/K=10/≤5% contest unchanged, and says the mechanism does not gate V-01a. It does not overstate the confirmation. The confirmation file's second paragraph (section 4 migration "proceeds via reviewable packets") is a coordinator gloss, not owner words; the decision itself does not claim owner confirmation of section 4, so this is acceptable.
- **Merge resolution.** `git diff 8d499a7 planning/mock-gap-closure -- .ai/DECISIONS.md` shows only the two added mock-gap paragraphs; main's V-01a owner-visual, round-3 and round-3 addendum decisions are intact and unaltered.
- **Faithfulness to the Architect answer.** G-01 carries: versioned `mock_gaps` schema with the decided fields/values; checker validation (unique/unknown IDs, references, wave/status/source combinations, DAG, placement-or-reason, no unevidenced `resolved`); typed missing-state component with `gapId` as metadata only; `check-all` source scan with file/line output and a dated, enumerated, non-expanding legacy baseline; Vitest for rendering/conditional/reload/`data-gap-id`; mutation tests for unknown ID, unused open ID, untagged copy and baseline expansion; `delivery_next_work.cjs` reads but ignores the catalogue; conditional visual pass cannot promote. G-02 carries the four-screen pilot, separate signal/firmware absent-source gaps, no Lab truth or mock value as Site evidence, partial status preserved, 1440/390 comparison, and the V-01a carries C1-C4 as classification inputs. G-03..G-05 are outlines only, each M, with refinement/split stops.
- **Registry/ledger/README.** `A-mock-gap-catalogue` (resolved, evidence = the decision) and `I-G-01`..`I-G-05` are added; G-02 requires `I-G-01`, G-03..G-05 require `I-G-02`. `gap_backfill_task` is set on exactly the 27 W1 `manifest_ids` (none missing, none extra) and partitioned 4/3/6/14 across G-02..G-05. README table and prose match the packets.
- **Cannot be selected early.** The G nodes reach no panel, so `next-work` never lists them as candidates; current W1 scoring is unchanged (report reproduces identically).
- Packets are 24/8 lines, well within WORKFLOW ceilings; `USER_REVIEW_REQUIRED: true` on all.

## Findings

### F1 (carry, medium; before G-01 activation) - no selection path exists for the G queue
`tasks/README.md` lines added under "Mock-gap closure queue"; registry `I-G-01`..`I-G-05` (`v69-dependency-registry-pilot.json` line ~229-234).
The Planner brief asked for nodes "so next-work can select them". In fact `next-work` cannot select them at all: they reach no panel, so they are not candidates and do not appear in the report (and `outside_ranking` would not surface them either, because it only annotates candidates). This is safe (cannot be selected early) and the README states it honestly, but `.ai/COORDINATOR_LOOP.md` activates only on a `select` decision, so G-01, which the owner confirmed "now", has no defined activation trigger. The README's "Coordinate the batches after their dependencies and the active-wave gate" does not say who decides or when. Fix: record (coordinator/Architect, owner-visible) an explicit activation rule for G packets, e.g. "G-01 activates outside competitive ranking at the next free single-active slot after V-01b closes, like PRE-S3-04", in the README and handoff.

### F2 (carry, medium; before G-01 activation) - G-01 leaves enforcement scope and the first placement ambiguous
`tasks/G-01-mock-gap-catalogue-and-guard.md` acceptance bullets 2 and 5, and "Review and checks".
(a) Bullet 2 says the checker validates `gap_ids` "on every non-core/open `w1_panel_mapping` portion" but also "as batches populate them" and "G-01 **can** seed explicit unplaced inventory". An implementer cannot tell whether the checker must fail at G-01 close on any unmapped non-core portion (forcing G-01 to seed all W1 portions) or enforce only on portions of closed batches (with a named enrolment list). The Architect answer says every non-core portion receives a gap node; pick one rule and state it. Also note the example `unplaced_reason` "screen not built until W5" does not fit W1 screens that are already built.
(b) The Vitest non-vacuity check and "show one populated and one missing state ... where the first typed placement is introduced" imply G-01 tags at least one real placement, but the packet does not name it, and tagging V-01a placements is G-02's mapping. Name the first placement (e.g. one Readiness gateway metric) or state that G-01 baselines all existing V-01a strings and proves the component on a test fixture only.

### F3 (carry, low-medium; G-01) - "reads but ignores" lacks a direct proof
G-01 bullet 6 requires preserving existing ranking/refusal fixtures but no fixture that adds `mock_gaps` entries (including ones linked to W1 core portions) and asserts an identical decision/score set. Existing fixtures would pass even if the new reader were never exercised. Add that fixture to the acceptance.

### F4 (carry, low; G-02 refinement) - stale sentence and prose-only gate dependencies
- `tasks/G-02-v01a-gap-pilot.md` bullet 1 still says "The referenced round-3 addendum is absent from this worktree"; after the main merge it is present (`.agent/architect-V-01a-round3-answers.md` line 48), and bullet 6 (added in 5a4847a) already cites it. Remove the stale sentence.
- `I-G-02` encodes V-01a via `I-S1-03`, and `I-G-03` encodes V-01b via `I-S2-02`; neither encodes the visual gate itself (nodes cannot `require` a `visual_gates` entry). V-01a is merged, so G-02 is fine in fact; G-03's "after V-01b merge" is prose-only. Harmless while G nodes are unselectable (F1), but the F1 activation rule should name the V-01b gate for G-03.

### F5 (carry, low; housekeeping) - decision wording
`.ai/DECISIONS.md` mock-gap entry: the header is confirmed, but the body keeps proposal wording ("Codex Architect proposal", "This proposed mechanism", "No ... change takes effect from this proposal before owner confirmation"), and it uses `Decision — ...: \`D-...\`` rather than the file's usual `Decision: \`D-...\`` prefix, which hurts grep-based lookup. Optional tidy; meaning is not wrong.

Not findings: G-01/G-02 omit explicit "Why next" / "Scope limits" headings, but the content is present inline (V-01a non-blocking, no scoring change, carries not in scope), which passes the WORKFLOW "can start without asking" test apart from F2.

## Residual risk not named in the packets

- The 14,644-line committed `.agent/next-work-gap-planning.json` is reproducible today but goes stale on the next input change; treat it as a dated record, not a current ranking.
- Once G-01 lands, the source-scan scope ("equivalent missing-capability copy") is a judgement call; a too-narrow pattern set would make the orphan guard pass vacuously. G-01 review should check the pattern list against the V-01a addendum copy, not only the mutation fixture.
