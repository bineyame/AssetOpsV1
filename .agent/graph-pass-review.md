# Planner graph pass + scoring fixtures review (fresh Claude reviewer, 2026-10-11)

A fresh Claude reviewer produced this review. It did not author the graph pass, the fixtures, or any earlier mapping review. It covers branch `plan/pre-S3-startup`: commit `cb09657` (the Planner graph pass) and commit `152f903` (`test_delivery_next_work.cjs` fixtures).

The review was judged against `.agent/architect-batch-answers-6.md` (C1, C5, C6 and the C2/C3/C4/C8 carries) and `D-2026-10-11-w1-loop-and-mapping-boundaries`. It also checked against `.agent/architect-batch-answers-5.md` and the earlier `.agent/W1-mapping-review.md` and `.agent/W1-mapping-fix-rereview.md`.

I did not switch branches, edit the repo, or commit. All simulations and mutations ran in a scratch copy or in memory.

## Verdict

**Accept.** There are no block findings. Five low carries are listed below. None of them changes a path closure, a reach count or a score.

**All 22 panels may be marked `reviewed_mapping:true`, citing this review:**

- `finding-evidence:1`, `finding-evidence:2`
- `mini:1`, `mini:2`, `mini:3`, `mini:4`
- `changes:1`, `changes:2`
- `recommendation:1`, `recommendation:2`, `recommendation:3`
- `verification:1`, `verification:2`, `verification:3`
- `sitework:1`
- `action-overview:1`
- `sitefindings:1`
- `finding-history:1`
- `action-plan:1`, `action-execution:1`, `action-evidence:1`, `action-history:1`

**Would-be ranking, confirmed:** `select I-sim-dispatch-cases` at **3.028**. The runner-up is `A-finding-episode` at **2.691**, a gap of **11.1%** (above 10%, so no notice), with `user_review_required: true`. This is advice only, not authorization. The C9 and merge-order steps in batch 6 still apply.

## Method

I compared the registry at `cb09657~1` with `cb09657` structurally: node by node, panel by panel, and portion by portion. For every core portion I computed the **open technical `requires` closure**, which is what the checker scores, using the distance `|needed| - 1`. I then compared those closures, old against new.

## What was verified

### Exactly the 22 panels flipped

- The panels set from `reviewed_mapping` true to false are exactly the 22 listed in the fixtures notes.
- Every **reviewed panel that stayed true** has an identical open closure on every core portion, before and after. This covers the dispatch, analysis, `evidence-analysis:2`, finding, financials, assumptions, health and asset panels.
- On those unchanged panels, the only edits are text: C3 claim and `mapping_target` wording, and the C8 boundaries on `finding:2` and `recommendation:3`. I read every reworded claim. None of them overclaims beyond the panel contract, and none adds a gate.
- No node changed `status`. No `panel_status` changed: the values are still only `partial` and `gap`. No core portion carries `proposed_gates`, and no `technical_requires` ID is unknown.

### C1: the S4 and S5 split

- **`I-S4-03`** now requires `A-finding-episode`, `I-S4-01`, `I-finding-evidence-ui`, `I-finding-history-ui` and `D-finding-revisions`. This matches C1 item 1.
- **`finding-evidence:1-2` and `finding-history:1`:**
  - Their closures lose exactly `A-finding-index`, `I-finding-index`, `I-site-findings-ui` and both Site-index fixtures.
  - They add nothing.
- **`I-S4-04`** requires `A-finding-index`, `I-S4-01`, `I-finding-index`, `I-site-findings-ui` and both fixtures. The three implementation/data nodes and `A-finding-index` now have task `S4-04`, and their own `requires` and efforts are unchanged.
- **`sitefindings:1`:** both `#a` (unknown/empty) and `#b` (positive) map to `I-S4-04`, each with its own fixture. Their closures lose only the S4-03 Evidence/History nodes.
- **`I-S5-01`** no longer requires `I-S4-03`.
  - `mini:1/2/4` lose the whole S4-03 and Site-index set and gain nothing.
  - The S5-01 packet now states that `mini:3` is honestly unavailable until S5-02.
  - `sequenced_after: ["I-S4-04"]` is queue order only. The registry checker forces it from the README predecessor (line 127), and scoring ignores it.
- **`I-S5-02`** requires `I-S5-01`, `I-S4-04`, `A-S5-overview` and `I-overview-finding-list-ui`.
- **`mini:3`:**
  - `#a` is now `variant:"unknown"`, with an explicit empty/Unknown claim and the empty fixture. This closes C2.
  - `#b` is positive, with the rows fixture.
  - Both variants reach `I-S5-02` and `I-S4-04`. Neither is closed by S5-01 alone.
- **`A-finding-index` reach:** only `sitefindings:1#a/#b` and `mini:3#a/#b`. It remains in `outside_ranking`.

### C5: ActionIndex scoped to the Site list

- `I-action-read.requires` is now `[I-action-store, A-claim-work-routes]`. `A-claim-work-routes` is resolved.
- Nodes that still require `A-action-index`:
  - W1 nodes: `I-site-action-index-read` and `I-S6-03` only.
  - Later-wave architecture nodes, unchanged and not on any W1 panel: `A-estate-action-summary`, `A-cold-work-projections` and `A-ev-work-projections`.
- Panel reach of `A-action-index`: **`sitework:1#a` only**. The 13 other Action, Recommendation, Changes and Verification panels each lose exactly `A-action-index` from their closure.
- The new nodes match the ruling:
  - `I-site-action-index-read` (projection, S6-03) requires `A-action-index` and `I-action-store`.
  - `I-sitework-ui` requires the index read and `I-action-read`.
  - `I-S6-03` requires `A-action-index`, `I-S6-01`, `I-sitework-ui` and `D-action-records`, and has `sequenced_after: [I-S6-02]`.
- `I-S6-02`'s closure does not contain `I-S6-03`.
- The S6-01 packet drops Site Work list completion and says "`sitework:1` closes only in S6-03".

### C6: one Finding closeout gate for S6

- `I-S6-01.requires` drops `I-finding-read` and adds `I-S4-01`.
- The direct `A-finding-episode`, `I-finding-store/read/ui` and `D-finding-revisions` gates are removed from 10 Action panel portions. They are still inherited through `I-S6-01 → I-S4-01`, so no closure lost them.
- `action-plan/execution/evidence/history` gain `I-S4-01`, `I-finding-ui` and `D-finding-revisions`, as C6 intends.
- No Action panel reaches `I-S4-03`, `I-S4-04`, `A-finding-index` or any S5 node.
- `I-recommendation-read` now requires `I-S4-01` instead of `I-finding-read`. This is a consistent Planner extension of C6 and changes no panel closure.

### C4: effort semantics

- `delivery_plan.scoring.task_effort_semantics` defines task-node S as incremental final integration, review and owner closeout after independently sized subnodes.
- Every open task node set to S has open sized subnodes in its `requires`. I checked all 13: S3-01, S3-02, S4-01 to S4-04, S5-01, S5-02, S6-01 to S6-03 and S7-01.
- The scoring code (`delivery_next_work.cjs:305-311`) uses effort only in the candidate's own E term and in the tie-break. Distance is the size of the closure. Re-sizing task nodes therefore cannot move the top two, which are not task nodes.
- `I-S3-01` changed from L to S. It stays blocked at 3.228, and at L it would be 2.828. No selection effect.

### Packets and queue

- The README links S4-03 (renamed `S4-03-finding-evidence-history.md`), S4-04, S5-02 and S6-03. No stale reference to `S4-03-site-finding-index-history` remains anywhere in the repo.
- Every new packet has `USER_REVIEW_REQUIRED: true`, an owner checkpoint, a branch, an "outline (S incremental closeout)" status, and acceptance that requires both positive and empty states where the ruling asks for them.
- S4-01, S5-01 and S6-01 cross-reference the split correctly.
- The `recommendation:3` panel contract now reads VerificationPlanVersion in lane S6-02. This matches the registry path and C8.

## Checks run (my own runs)

- **`tools/check-all.ps1`:** all 6 guards PASS (architecture, navigation truthfulness, agent workflow, dependency registry, delivery fixtures, and the ledger with 110 screens, 88 models and 258 panels).
- **`node test_delivery_next_work.cjs`:** 32/32 pass.
- **Live `check_v69_dependency_registry.cjs --next-work`:** refused with `[unmapped_approved_panel]` for exactly the 22 panels.
  - Fingerprints: registry `40314ec899f7f939`, queue `81ab83be42b2270f`, packet_status `613b49b424fa249b`, panel_contracts `c6f0009bbbf68f61`, manifest `468bd0cf06b26749`, owner_input `f902d15082e24067`.
  - These match the fixtures notes.
- **In-memory ranking:** an `fs.readFileSync` preload marked the 22 panels reviewed, and the real CLI then ran.
  - Status `ranked`, no global stop.
  - `I-sim-dispatch-cases`: M, 35 panels, 3.028.
  - `A-finding-episode`: M, 29 panels, 2.691.
  - Gap 0.111. Decision `select I-sim-dispatch-cases`.
  - Also eligible: V-01a 2.655, V-01b 2.463, `A-action-lifecycle` 1.968, `A-S7-health` and `D-edge-health-cases` 1.542.
  - `I-S3-01` scores 3.228 but is blocked on open prerequisites.
- **Fixture mutation testing.** The fixtures implementer could not run this, so I did. I copied `delivery_next_work.cjs`, the test file, the registry and `tasks/*.md` into the scratchpad. The unmutated copy passes 32/32. Each mutant below ran on a fresh copy:

| # | Mutation | Failing tests |
| --- | --- | --- |
| M1 | `I-S4-03` requires `A-finding-index` | 2 |
| M2 | `I-S5-01` requires `I-S4-04` | 2 |
| M3 | `I-action-read` requires `A-action-index` | 1 |
| M4 | `I-S4-01` removed from `I-S6-01` | 1 |
| M5 | `I-S6-02` requires `I-S6-03` | 2 |
| M6 | `mini:3#a` path cut to `I-S5-01` only | 1 |
| M7 | README S6-03 link retargeted | 1 |
| M8 | S5-02 packet Status set to `active` | 1 |
| M9 | `I-S6-03.sequenced_after` changed | 1 |
| M10 | `I-S6-03` requires `I-S6-02` | 1 |
| M11 | `I-S4-03` requires `I-S4-04` | 2 |
| M12 | `gateInfo` dropped from `activeTasks` in the checker | 4 |
| M13 | `I-recommendation-read` requires `A-action-index` | 1 |
| M14 | `sitefindings:1#a` path cut to `I-S4-01` | 1 |

All 14 mutants are killed, so the new fixtures are not vacuous.

**Not run:** the backend and frontend suites. This is a planning, registry and fixture-only change, with no product code.

## Findings

All of the findings below are **carries**. None blocks the 22 marks or the post-merge report.

**G1 (carry, low-medium): panel-contract `task_or_lane` is stale for the moved panels.**
- Where: `frontend/docs/architecture/v69-panel-contracts.json`.
- Stale values, with the registry owner in brackets:
  - `sitework:1` says S6-01 (now S6-03).
  - `mini:3` says S5-01 (now S5-02).
  - `sitefindings:1` says "W1 S5-01 outline refinement; technical mapping unreviewed" (now S4-04).
  - `finding-evidence:1-2` say S4-01 (S4-03).
  - `finding-history:1` says "W1 S4-01 … unreviewed" (S4-03).
  - `recommendation:2` says S6-01 (registry `I-S6-02`).
- Why it matters: no checker consumes this field, but a future Implementer reads the contract for ownership.
- Fix: align these lanes in the next Planner touch.

**G2 (carry, low): templated `mapping_target` and boundary text name the wrong fixture.**
- `mini:1#a` (assessment and timeline) and `mini:2#a` (operating context and coverage) say "using `D-financial-basis`". Batch 5 says the Overview fixture reuses the accepted S3/S4 selected-window fixture.
- `recommendation:2#a` and `recommendation:3#a` (S6-02 frozen plan and required evidence) say "using `D-action-records`".
- The `sitework:1#a` boundary still reads "existing pilot gate `I-action-read + I-action-ui + D-action-records`" and omits the Site index.
- Fix: correct the text only. No path changes.

**G3 (carry, low): `I-overview-finding-list-ui` requires `I-site-findings-ui`.**
- That node is a UI on another screen. Under the earlier B2 precedent, a UI on another screen is not a technical AND prerequisite.
- It is closure-neutral, because `I-S5-02 → I-S4-04` already contains it, so no score changes.
- Fix: drop the edge, or record that a shared list component is genuinely reused.

**G4 (carry, low): packet wording.**
- The S4-04 acceptance says "Decide `A-finding-index`". The decision rule routes architecture nodes to the Architect, so this should read "requires the recorded Architect `A-finding-index` decision".
- The S6-01 header still says "Depends on: S4-01 Finding identity/read". The body correctly names the reviewed `I-S4-01` closeout.

**G5 (carry, low): two open fixture nodes lack `acceptance_target`.**
- `I-sim-dispatch-cases` (the would-be selection) and `I-sim-verification-cases` have no `acceptance_target`. The C3 node list did not name them. The S3-01 packet's phase 1 carries the target.
- Fix: cite that target in the registry.

**Fixture note (no action required).** The new "stops when active or in review" test injects S4-03, S4-04, S5-02 and S6-03 through `ctx.gate_queue`. In production they are S-queue tasks that follow the `taskInfo` path. That path's stop is covered generically at tests ~200-205, and the live report's lack of a `queue_mismatch` shows `parseQueue` discovers all 19 S tasks.

## Residual risk

- The ranking margin is 11.1%, only about 1 point above the notice band. Any later reach or effort edit (G3 has none) should trigger a fresh comparison.
- `I-S3-01` is now S. Its closeout includes the Performance cutover comparison and the legacy-exception review, which may be more than S if that work is not inside `I-dispatch-ui`. This has no selection effect now, because the node is blocked and is the only closer on its path.
- `sitework:1` has one portion that covers both rows and the empty state, with no distinct empty-watermark fixture node. Q3 required split variants only for `mini:3` and `sitefindings:1`, and the S6-03 packet requires both states. The S6-03 reviewer must check both.
- This report does not clear C9 or the merge steps. Batch 6 still applies: the coordinator records the outcomes, the branch merges, and a fresh `--verify-report` runs on `main` before any activation.
