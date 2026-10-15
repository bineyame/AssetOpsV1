# Architect follow-up - S4-05 plan review M1 (delegated, owner absent)

You are the AssetOps Architect (Codex). Read `.agent/S4-05-plan-review.md` (M1 especially, also M2/M3) and your rulings `.agent/architect-S4-05-answers.md` / `D-2026-10-15-s405-stored-demo-provenance`.

M1: with "no designation = UNKNOWN = no current amount", every ordinary simulated Site Finding (simulator/gateway data that is not an authored demonstration fixture) and every real Site Finding loses its current amount and gains "Source not confirmed"; no positive designation exists for pilot/real data, so real data can never show an amount; `tasks/S5-01-site-overview.md:39` goes stale; and resolving `I-stored-demo-provenance` would tick a `real_pilot_requires` item while pilot money is still impossible.

Rule, short and implementable:
1. Is the blanket UNKNOWN default intended for ordinary simulated (non-authored) data and for real data? If not, define the source classes and which may show a current amount (e.g. simulator-run data whose server-recorded run identity is known vs authored demonstration vs real unattested), and what designation each needs. Keep it fail-closed for genuinely unknown/mixed inputs.
2. The pilot/real designation: name the follow-on (registry node or checkpoint item) and whether `I-stored-demo-provenance` may resolve before it, given `real_pilot_requires` and `tools/schedule-install-gate.py:32`.
3. How the S5-01 packet must be amended (whichever slice merges second).

Append "## Follow-up (plan review M1)" to `.agent/architect-S4-05-answers.md` and amend the decision entry in place (UTF-8, ASCII hyphens). No code, no packet edits. Print a short summary.
