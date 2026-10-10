# Architect request: review the Planner's W1 owner-input proposal (2026-10-10)

Owner instruction (verbatim, 2026-10-10): "let the codex architect review the recommednation by the planner before i do"

Context: the owner asked whether some W1 screens are already built (e.g. SLD). Seven are, from S1/S2: `sites`, `foundation`, `readiness`, `sld`, `lab`, `evidence`, `evidence-analysis` (all merged to main at `82ba6cd`; S2-02 owner checkpoint passed). The Planner's registry (`frontend/docs/architecture/v69-dependency-registry-pilot.json`, `delivery_plan.w1_panel_mapping`) marks all 58 W1 panels `panel_status: "gap"`, `reviewed_mapping: false`, including those S1/S2 already deliver — so ranking would treat delivered work as remaining.

Please review `.agent/W1-owner-input-proposal.md` (commit `376486e` on `plan/pre-S3-startup`) against `D-2026-10-09-owner-delivery-strategy`, the pre-S3 decisions, the panel contracts, the v6.9 manifest and what S1/S2 actually built:
1. Are the recommended core panels right per screen (too broad / too narrow; any claim portion that needs a technical gate the proposal glosses over)?
2. Are the demo values sensible for a client-facing demo story? Consider especially already-built technical surfaces (e.g. `lab`) versus client journey screens.
3. How should already-delivered S1/S2 panels be represented (status, reviewed mapping, remaining gaps incl. V-01) so the score does not count delivered work and the owner sees what each built screen still lacks? Give the exact rule for the `PRE-S3-03` implementer (`tasks/PRE-S3-03-delivery-checker-report.md`).
4. Anything in the proposal that would mislead the owner.

Amend `.agent/W1-owner-input-proposal.md` in place with your corrections (mark "Reviewed by Codex Architect" and list changes at the top, keeping the one-reply confirmation line), and amend `tasks/PRE-S3-03-delivery-checker-report.md` if item 3 changes it. Keep owner fields in the registry empty. No product code; leave edits uncommitted.
