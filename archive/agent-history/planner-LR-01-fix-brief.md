# Planner fix round 1 — LR-01

You are the AssetOps Planner (Codex). Amend `tasks/LR-01-late-reading-series-and-money-limit.md` on `plan/late-reading-series` in this worktree. No code. The coordinator commits.

Inputs:
- Plan review `.agent/LR-01-plan-review.md` (RETURN: M1-M5 Medium, L1-L5 Low, Info).
- Architect rulings `.agent/architect-LR-01-answers.md` (Q1-Q4 accepted; "Packet changes for the Planner" items 1-3; and "Follow-up M1" which rules the overlap definition) and decision `D-2026-10-15-lr01-source-time-cohort` in `.ai/DECISIONS.md`.

Apply all of:
1. Architect packet changes 1-3, and replace the Architect-questions section with a short "Architect rulings" section citing the answers file and decision.
2. M1 exactly as the Architect's Follow-up M1 ruling states (it governs over the reviewer's wording where they differ).
3. M2: an explicit outcome table (inputs -> S3 status/limits, Finding revision/end reason, consequence amount/IDs, money_eligibility) used in both phases' proof, including run 1 *with* a valid simulated attestation: withheld -> attestation recorded -> reassessment -> eligible at 15.8125, with old run/selection IDs and the 7.5625 revision kept. Add that sequence to the owner walkthrough.
4. M3: the attestation write path: SYSTEM-only server-authorized route/CLI for labelled simulated attestations, no real-source write path in this slice; refuse gateway credentials and clients; append-only with supersede/revoke; reads as of the run's knowledge time so `backend/tests/test_s3_dispatch_assessment_postgres.py:139-143` replay digests hold; reassessment on revocation (and expiry/replacement per Architect item 1).
5. M4: an owner-reachable UI path: a `serve` mode (new or extended) with the exact backend and frontend commands, the source-gate precondition, DB-prefix rules, and a browser-evidence run at 1440 and 390 px. Verify against `tools/s402b_fuel_cost_walkthrough.py:257` how serve works today and cite it.
6. M5: gate `presented_as_current` / `current_amount_shown` in `backend/assetops_backend/financials/consequence_read.py:202-214` on the same eligibility (no UI-only predicate), and assert run 1 on both the Finding API and Financials API.
7. Lows: L1 citation fix; L2 registry node `task` = `"LR-01"`; L3 name `test_s4_finding_api.py`, `siteFinancials.test.tsx`, add `tsc` and frontend tests to phase 2, widen phase-2 focused backend set (S4 consequence, recompute, tick, health); L4 rename the "real source without clock" case to "simulated data without attestation" and state whether the simulated gateway's normal late path gets an attestation in this slice (recommend: walkthrough records one explicitly; no automatic attestation); L5 define "latest selected window" as every selected day window overlapping the episode plus its bracket. Info: note expected revision churn in existing assertions from the new model/matcher versions.

Re-verify every new `path:line` you add against the code. Keep the packet tight, keep Status `implementation-ready`, keep registry valid (`node frontend/docs/architecture/check_v69_dependency_registry.cjs`). Add a one-paragraph "Plan fix round 1" note listing what changed. Print a short summary.
