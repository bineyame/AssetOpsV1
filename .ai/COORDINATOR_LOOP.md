# Coordinator loop instruction (W1–W6 delivery loop)

Startup prerequisite 6 of `D-2026-10-09-owner-delivery-strategy`. The rules live in `.ai/WORKFLOW.md` ("Coordinator transition for the W1–W6 delivery loop"), `.ai/ROLE_CONFIG.md` and the decision itself; this file is the operating sequence. Where they differ, the decision and `WORKFLOW.md` win.

## Before each cycle

1. Read the top of `.agent/coordinator-handoff.md`, including "Ranking notices".
2. Start only after the pre-S3 planning branch and its required reviews/guards are merged. Work from current `main`; run `tools/check-all.ps1`. A failure stops selection for correction.
3. Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs --next-work --out .agent/next-work-<date>.json`, then `--verify-report .agent/next-work-<date>.json` before acting. Read the decision, blockers, scores and paths; regenerate after any input change.
   - `refused` → stop and route the stated technical/mapping defect to its owner; ask the owner only for a genuine owner decision or checkpoint.
   - `stop` → take the stated action: owner for a ≤5% contest, XL exception or missing owner choice; finish an active/in-review packet and its recorded review before another selection.
   - 5–10% → apply the published tie-break, append the two scores and reason under "Ranking notices" in `.agent/coordinator-handoff.md`, continue.
   - `select` → continue with the selected candidate.

## One cycle

4. **Route and refine.** A selected architecture node goes to the bound Architect for a recorded decision; a data, implementation or visual node goes through its owned reviewable packet and the bound Planner if refinement is needed. Do not dispatch an Implementer for a pure Architect decision or treat an `enables` edge as technical readiness. Batch genuine Architect questions; fail-closed defaults do not waive a named gate.
5. **Activate.** For a build slice, create its task branch from current `main`, set its packet Status to `active`, and record that single active task in the handoff. For an Architect decision, record/review the decision and registry closeout on a planning branch; do not invent a product task branch.
6. **Build.** Use the Implementer binding in `.ai/ROLE_CONFIG.md`; phase handoffs follow the packet's actual reviewable cuts. The coordinator keeps the tree stable for review and avoids overlapping edits.
7. **Review.** Dispatch an independent Reviewer under `.ai/ROLE_CONFIG.md` and any *specific* owner instruction; the S2 Claude-per-slice/Codex-batch arrangement was scoped to S2 and is not an automatic S3–S7 rule. The coordinator reads all review files before recording the verdict, routes a block to a bounded fix and fresh independent re-review, and records carries in `.ai/MILESTONE_REVIEW_BACKLOG.md`. A second rejection of the same task stops for owner direction.
8. **Owner checkpoint.** If the packet is `USER_REVIEW_REQUIRED: true`, prepare a plain-language walkthrough and stop for the owner before merge. Save the owner's words verbatim under `.agent/`.
9. **Close and merge.** The coordinator records the review outcome and Status `done (…)` from the evidence, verifies any owner checkpoint and lineage, then merges the reviewed branch `--no-ff` into `main` (a temporary worktree may protect another agent's tree). Rerun guards and a fresh verified report on merged `main`; update the handoff. Nothing is pushed.
10. Return to step 1.

## Always

- Decisions go to the Architect bound in `.ai/ROLE_CONFIG.md`; the coordinator records the resulting transition and commits reviewed edits.
- Owner text is relayed verbatim via a saved file.
- Never infer approval from silence, a proposed tier or a report; never mark a panel Real without recorded lineage and V-01 acceptance.
- Product screens stay plain-language (`D-2026-10-04-plain-language-analysis-views`).
- Keep agents from editing the same files concurrently; stop leftover servers that agents started, never the owner's.
- Before the owner restarts a session, update `.agent/coordinator-handoff.md`.
