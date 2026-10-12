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

**Unscored mock-gap packets.** The verified report separately lists `I-G-01`–`I-G-05` with their outside-ranking reason and current packet status; they are not candidates and do not inherit scores. After V-01b's independent review, owner checkpoint and merge, and only at a free single-active slot, activate G-01 before acting on a normal `select`; after its reviewed and merged closeout, activate G-02 at the next free slot once merged/accepted V-01a is verified. First resolve any `refused` checker result, ≤5% owner contest, outstanding owner checkpoint or active/in-review packet. A 5–10% ranking notice is still recorded and does not by itself block a due G packet. After G-02, resume core ranking; refine/run G-03–G-05 at a free slot only after their owning UI is reviewed and merged, their technical prerequisites close and no ready active-wave core candidate is waiting, otherwise carry them to W1-exit backfill review. G-03 specifically requires accepted and merged V-01b, beyond S2-02. Record each due/deferred reason in the handoff, never convert an unscored packet into an implicit core candidate, and regenerate the report after each merge. This is the Architect's implementation-order ruling in `D-2026-10-13-g-gap-packet-activation`; it changes no W1 scoring parameter.

## One cycle

4. **Route and refine.** A selected architecture node goes to the bound Architect for a recorded decision; a data, implementation or visual node goes through its owned reviewable packet and the bound Planner if refinement is needed. Do not dispatch an Implementer for a pure Architect decision or treat an `enables` edge as technical readiness. Batch genuine Architect questions; fail-closed defaults do not waive a named gate.
5. **Activate.** For a build slice, create its task branch from current `main`, set its packet Status to `active`, and record that single active task in the handoff. For an Architect decision, record/review the decision and registry closeout on a planning branch; do not invent a product task branch.
6. **Build.** Use the Implementer binding in `.ai/ROLE_CONFIG.md`; phase handoffs follow the packet's actual reviewable cuts. The coordinator keeps the tree stable for review and avoids overlapping edits.
7. **Review.** Owner rule (2026-10-11, `.agent/owner-review-routing-and-merge-2026-10-11.md`): keep the S2 arrangement for all later work — a fresh Claude reviewer reviews each slice, re-reviews go to a fresh Claude reviewer, small written-list fix rounds run on Sonnet, and one batched Codex review covers each milestone (S3, S4, …) at its end; Codex questions are batched. The coordinator reads all review files before recording the verdict, routes a block to a bounded fix and fresh independent re-review, and records carries in `.ai/MILESTONE_REVIEW_BACKLOG.md`. A second rejection of the same task stops for owner direction.
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
