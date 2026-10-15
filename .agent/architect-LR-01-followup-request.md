# Architect follow-up — LR-01 overlap definition (plan review M1)

You are the AssetOps Architect (Codex). Read `.agent/LR-01-plan-review.md` finding M1 and your rulings `.agent/architect-LR-01-answers.md` Q1/Q2 (and `D-2026-10-15-lr01-source-time-cohort` in `.ai/DECISIONS.md`).

M1: power data are back-to-back 5-minute means. If each reading's *measurement interval* is widened by the clock error (Q1 text "Widen each source or measurement interval by that error") and any overlap is ambiguous (Q2), neighbouring in-order readings always overlap, so ordinary attested data (including the 15.8125 USD positive case) becomes ambiguous. Reviewer recommends: order on each reading's instant (measurement interval end, else source time) +/- the attested error; intervals that only touch are not overlap; ambiguity applies where the widened instants of two readings in one channel overlap, or where gateway sequence and attested source order disagree beyond the error.

Rule: accept, amend, or replace, in a few lines. Append the ruling to `.agent/architect-LR-01-answers.md` as "## Follow-up M1 (2026-10-15)" and amend the `D-2026-10-15-lr01-source-time-cohort` entry in `.ai/DECISIONS.md` in place (UTF-8, ASCII hyphens). No code, no packet edits. Print a short summary.
