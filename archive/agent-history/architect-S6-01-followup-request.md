# Architect follow-up - S6-01 plan review M1 and M3 (delegated, owner absent)

You are the AssetOps Architect (Codex). Read `.agent/S6-01-plan-review.md` findings M1 and M3 (and M2 for context), your rulings `.agent/architect-S6-01-answers.md`, `D-2026-10-15-s601-action-store-and-ui`, and how S4-02d's eighth writer was ratified (`D-2026-10-14-s402d-schedule-storage-and-install-gate` in `.ai/DECISIONS.md`; guard `tools/checks/configuration-persistence.ps1:590-700`).

Rule:
1. M1: ratify (or not) a ninth PostgreSQL writer - a new Action adapter as the sole writer of `action`, `action_event`, `action_policy_change` (and the M2 accepted-recommendation snapshot if you agree with M2) - and define the transaction seam with `publish_configuration` (`backend/assetops_backend/.../postgres_foundation_store.py:607-656`, which opens its own transaction and takes the Site lock) so the Action lock is taken before the Site lock and APPLIED commits in the same transaction. State the rule-8 guard additions required.
2. M3: either name one bounded event kind with an explicit earlier `occurred_at` (and its bounds/authority) or defer the backdated-occurred_at fixture case explicitly.
3. M2: confirm the fix direction (Foundation basis in the recommendation key, immutable accepted-recommendation snapshot, `GET recommendation` after an Action exists) or amend.

Append "## Follow-up (plan review M1-M3)" to `.agent/architect-S6-01-answers.md` and amend `D-2026-10-15-s601-action-store-and-ui` in `.ai/DECISIONS.md` in place (UTF-8, ASCII hyphens). No code, no packet edits. Print a short summary.
