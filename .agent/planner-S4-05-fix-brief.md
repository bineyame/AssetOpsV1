# Planner fix round 1 - S4-05

You are the AssetOps Planner (Codex). Amend `tasks/S4-05-stored-demo-provenance.md` (and `tasks/README.md`, registry) on `plan/stored-demo-provenance` in this worktree. No code; the coordinator commits.

Inputs: plan review `.agent/S4-05-plan-review.md` (RETURN M1-M3, L1-L4, residual risk); Architect rulings `.agent/architect-S4-05-answers.md` (Q1-Q3 packet changes, rule-8 section, and "Follow-up (plan review M1)"); decision `D-2026-10-15-s405-stored-demo-provenance`.

Apply:
1. The follow-up's source classes: AUTHORED_DEMONSTRATION and REGISTERED_SIMULATION positive pre-admission bindings (exact contract, server-recorded run identity/digest for simulation, refusals), resolution truth table incl. MIXED/UNKNOWN precedence, exact IDs/reasons in responses. Add the new open registry node `I-attested-real-source-provenance` (proper fields, sensible requires) and add it to `real_pilot_requires`; update `tools/schedule-install-gate.py`'s checked set in the packet's build scope; state the S5-01 amendment obligation (whichever merges second) precisely.
2. Q1-Q3 packet changes and the rule-8 insert-only + DB immutability (trigger if the binding lives on `ingestion_batch.publication_id`, since the ledger updates that table at line ~291).
3. M1: state plainly the effect on unbound/historical rows (no current amount) and on owner-visible copy.
4. M2: producers register first: `tools/s402b_power_cases.py`, `tools/s402b_fuel_cost_walkthrough.py`, `tools/s402c_late_power_walkthrough.py` (and the simulator run path for REGISTERED_SIMULATION); P02 late-power fixture handled; `test_s4_power_demo_case_postgres.py` named; a reproducible owner walkthrough (tool, private DB prefix, ports, exact command order, what to see).
5. M3: name every read surface and field carrying provenance (Finding detail `finding_read.py:350`, Evidence `:446`, consequences, Financials) and the frontend impact (`FindingConsequence.tsx:115,443`): either unchanged response shape with frontend unchanged, or named frontend files plus `tsc`, `npm.cmd test` and layout evidence.
6. Lows L1-L4 and the residual risk (measure the admission-lock cost in phase-1 tests).
7. Re-size honestly: if this is now larger than M (two phases), split into S4-05a (bindings + resolver, non-UI if possible) and S4-05b (producers, reads/UI copy, owner walkthrough), each at most two phases, each with its own README row and USER_REVIEW_REQUIRED.

Verify every new path:line. Status `implementation-ready`; registry valid (`node frontend/docs/architecture/check_v69_dependency_registry.cjs`). Add a "Plan fix round 1" note. Print a short summary.
