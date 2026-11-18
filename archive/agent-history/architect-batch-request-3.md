# Architect request: owner delivery-strategy draft + batched S2-02 questions (2026-10-09)

Owner instructions (verbatim): 2026-10-09 "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use". The owner's new request is quoted verbatim at the top of the draft file below.

One batched call, two parts.

## Part A — owner delivery-strategy draft (owner request)

The owner asks the Architect to turn `.agent/owner-delivery-strategy-draft-2026-10-09.md` (verbatim owner text) into a proper decision `D-2026-10-09-owner-delivery-strategy` that the owner can review and confirm.

- Produce it as a **proposed** decision for owner confirmation, not a recorded accepted one: write it to `.agent/D-2026-10-09-owner-delivery-strategy-proposal.md`, in `.ai/DECISIONS.md` style, keeping the owner's intent and wording where sound. Do not add it to `.ai/DECISIONS.md` until the owner confirms.
- Resolve or explicitly surface the placeholders (‹…›: weights, the 10% / L thresholds, dropped/deferred screen lists) — propose values where the owner left defaults, and list exactly what the owner must supply at confirmation.
- Check it against existing records (`tasks/README.md` queue and owner checkpoints, `.ai/WORKFLOW.md`, `.ai/ROLE_CONFIG.md` including the owner's Codex-usage and decision-routing rules, the dependency registry and its checker, V-01, the v6.9 manifest, and current S2 state: S1, S2-01a, S2-01b and S2-01c are merged to main at `b4006d1`; S2-02 is in progress). Name conflicts, ambiguities and anything that would make the autonomy loop unsafe or a gate unenforceable, with your recommended resolution.
- For the six prerequisites: say what each requires, who owns it (Architect/Planner/Implementer/coordinator), rough size, and a proposed order. Do not execute them before the owner confirms.
- Give a short owner-facing summary at the top of the proposal: what the owner is confirming and the open choices.

## Part B — batched S2-02 questions

`.agent/S2-02-questions-3.md` (Q13-Q17 from phase 3a; built on fail-closed defaults). Q13 is material: this workspace has no file-backed KOBO-001 evidence (existing `var/evidence`, `var/commits` and dispatch claims are SITET26), so the required legacy replay comparison before switching imported KOBO-001 Evidence reads is an empty set; the implementer is recording it as an empty-set comparison and keeping the cutover gated. The owner Evidence walkthrough (S2-02 phase 3c) depends on this ruling. Rule on Q13-Q17, record material decisions in `.ai/DECISIONS.md`, amend `tasks/S2-02-ingestion-site-evidence.md` if needed, and write `.agent/architect-S2-batch-answers-3.md` with what phase 3b/3c must change.

Say whether you want the owner to weigh in on Part B. No product code; leave edits uncommitted (the coordinator commits). An implementer is working on the S2-02 branch concurrently; touch only decision/packet/agent files.
