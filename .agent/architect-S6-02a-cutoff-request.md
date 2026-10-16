# Architect request - S6-02a phase-1 review F3 (and two small format calls)

You are the AssetOps Architect (Codex). The owner is away until 11:00 and asked for maximum W1 progress; decide on the owner's behalf only within the Architect's remit. Read `.agent/S6-02a-phase-1-review.md` (findings F2, F3, F7), the packet `tasks/S6-02a-verification-core.md`, `D-2026-10-16-s602-questions` (Q3: the plan cannot be frozen once the later run has begun) and `.agent/architect-S6-02-answers.md`.

Rule, short and implementable:
1. F3: the central database has no Lab run table. Accept "the first accepted later-window report (any role, any asset, interval ending at or after later_start)" as the observable "later run has begun" cutoff, OR name a different public signal that exists centrally today (for example any received batch whose envelope falls inside the later window, accepted or not). Say which, and what the test must show.
2. F2: confirm that freeze refuses unless every baseline day's S3 selection is CURRENT, that later-selection binding refuses before later_end has passed and the day is CURRENT, and that the evaluator returns REASSESSMENT_PENDING unless both pinned windows are CURRENT. Amend if needed.
3. F7: pick one timestamp serialisation for verification API payloads (`+00:00` or `Z`).

Write `.agent/architect-S6-02a-cutoff-answers.md` and a short `D-2026-10-16-s602a-cutoff` entry in `.ai/DECISIONS.md` (UTF-8, ASCII hyphens). No code, no packet edits. Print a short summary.
