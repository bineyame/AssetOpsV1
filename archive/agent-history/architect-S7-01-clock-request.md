# Architect request - S7-01a review L2/L3 (2026-10-16)

You are the AssetOps Architect (Codex); decide within your remit, owner wants W1 progress. Read `.agent/S7-01a-review.md` (L2, L3, L5 and residual risks), `D-2026-10-16-a-s7-health`, and `backend/assetops_backend/evidence/source_health.py` (around lines 38 and 173).

1. L2: the implementer chose a 5000 ms reported-clock offset tolerance (beyond it the gateway clock is UNTRUSTED), also used as the "observed after receipt" allowance. Confirm, amend, or set the value(s), and say whether the two uses should be separate constants.
2. L3/L5 and residual risks: should `summary` carry `NO_ENABLED_GATEWAY` when only disabled gateways exist; must fact/contact ages be null when trust is UNTRUSTED; should `ALL_CURRENT` be labelled a contact summary rather than Site health. Short rulings that S7-01b (UI) and a small S7-01a follow-up can implement.

Write `.agent/architect-S7-01-clock-answers.md` and `D-2026-10-16-s701-clock` in `.ai/DECISIONS.md` (UTF-8, ASCII hyphens). No code, no packet edits. Print a short summary.
