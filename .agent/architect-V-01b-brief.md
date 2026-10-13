# Architect brief: V-01b questions batch (2026-10-13)

Role: Architect (Codex). Branch `task/V-01b-evidence-lab-visual` (HEAD after `e6e1ba1`). V-01b is built and fresh-reviewed ACCEPT (`.agent/V-01b-fix2-rereview.md`); owner walkthrough pending. Do not edit product code. Codex cannot write .git: write your answers file; the coordinator commits.

Read: `.agent/V-01b-questions-1.md` (Q1-Q8, each with the default shipped), `.agent/V-01b-review.md` (carry C1), `tasks/V-01b-evidence-lab-visual-fidelity.md`, and the relevant decisions in `.ai/DECISIONS.md` (S1-03 shell scoping, D-2026-10-12-v01a-owner-visual-rulings, D-2026-10-12-mock-gap-closure-mechanism, D-2026-10-13-g-gap-packet-activation).

Answer:
1. Q1-Q8: ratify the shipped default or rule otherwise; for each, say whether anything must change before the owner walkthrough/merge, or is a carry (and to which slice: G-03, a backend slice, etc.).
2. C1: `tools/checks/shell-overflow.ps1` section 2b amends the S1-03 Architect scoping rule (narrow-width shell rules may name `.app-frame--operator` or `.app-frame--lab`; each part must start with the shell class; at least one rule per shell required). Reviewer proved it stricter (four probes). Ratify or rule otherwise.
3. Note anything the owner must decide (the coordinator will put it to the owner).

Write `.agent/architect-V-01b-answers.md`. If a recorded decision is warranted, draft its DECISIONS.md entry text inside that file.
