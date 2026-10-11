# Coordinator loop instruction (W1–W6 delivery loop)

Startup prerequisite 6 of `D-2026-10-09-owner-delivery-strategy`. The rules live in `.ai/WORKFLOW.md` ("Coordinator transition for the W1–W6 delivery loop"), `.ai/ROLE_CONFIG.md` and the decision itself; this file is the operating sequence. Where they differ, the decision and `WORKFLOW.md` win.

## Before each cycle

1. Read the top of `.agent/coordinator-handoff.md`, including "Ranking notices".
2. Work from an up-to-date `main` (merged work only). Run `tools/check-all.ps1`; any failure stops the loop.
3. Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs --next-work --out .agent/next-work-<date>.json` and read the Decision line and raw facts.
   - `refused` → stop and report the refusal reasons to the owner; do not select around it.
   - `stop` (≤5% contest, XL, owner input missing, active/in-review packet) → stop for the owner or finish the active task first.
   - 5–10% → apply the published tie-break, append the two scores and reason under "Ranking notices" in `.agent/coordinator-handoff.md`, continue.
   - `select` → continue with the selected candidate.

## One cycle

4. **Refine.** If the selected node's packet is not implementation-ready, send it to the Planner (Codex, `codex exec resume … <planner-session>`), then to the Architect only for real decisions. Batch Architect questions per the owner's rule; implementers proceed on fail-closed defaults.
5. **Activate.** Create `task/<ID>-<slug>` from `main`, set the packet Status to `active`, record it in the handoff.
6. **Build.** Dispatch a fresh Claude implementer per phase (default model for new slices; Sonnet for written-list fix rounds and mechanical closeouts). Hand off at ~120k context. Implementers write questions with fail-closed defaults instead of stopping.
7. **Review.** A fresh Claude reviewer per slice; fix rounds on Sonnet; re-reviews by a fresh Claude reviewer. Codex reviews are batched across a milestone as the owner directs (S2 precedent: one Codex review across the remaining slices). Sort findings into block or carry; carries go to `.ai/MILESTONE_REVIEW_BACKLOG.md`. A second rejection of the same task stops for the owner.
8. **Owner checkpoint.** If the packet is `USER_REVIEW_REQUIRED: true`, prepare a plain-language walkthrough and stop for the owner before merge. Save the owner's words verbatim under `.agent/`.
9. **Close and merge.** Record the review outcome and Status `done (…)` from the evidence, merge `--no-ff` into `main` (temporary worktree if agents are using the working tree), recompute the registry/report on the merged tree, update the handoff. Nothing is pushed.
10. Return to step 1.

## Always

- Decisions go to the Codex Architect (`.ai/ROLE_CONFIG.md`); Codex cannot write `.git`, so the coordinator commits its edits.
- Owner text is relayed verbatim via a saved file.
- Never infer approval from silence, a proposed tier or a report; never mark a panel Real without recorded lineage and V-01 acceptance.
- Product screens stay plain-language (`D-2026-10-04-plain-language-analysis-views`).
- Keep agents from editing the same files concurrently; stop leftover servers that agents started, never the owner's.
- Before the owner restarts a session, update `.agent/coordinator-handoff.md`.
