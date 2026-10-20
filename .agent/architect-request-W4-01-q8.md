# Architect request: W4-01 q8 (commit 5 guard conflicts and registry)

Read:
- `.agent/W4-01-build-spec.md`, all rulings;
- `.agent/W4-01-pending-rulings.md`, q8-1 to q8-3;
- `.agent/W4-01-review-packet.md`, which lists 13 commit-5 readings;
- `tools/checks/missing-claim-scan.mjs` and its baseline;
- `frontend/docs/architecture/check_v69_dependency_registry.cjs`.

Code: branch `task/W4-01-work-case-core` at `afa35e79`.

Rule with exact artifacts:
- q8-1. The missing-claim orphan scan and its fixture self-check reject two spec-literal strings: the context notice ending "not available yet", and "Manage in Incidents/Maintenance · Not available yet". Give the exact compliant mechanism, with no weakened guard: a baseline entry with its rationale format, the guard's sanctioned component, or a copy change that keeps the mock meaning. Reconcile this with W4-03 closure S31/N32, which uses plain-text Notice copy.
- q8-2. Registry panel paths for `sitework-incidents:1` and `sitework-maintenance:1` cascade into the screen-ledger rows and `P-work-cases` (pending owner). The owner now does one walkthrough after W6 (`.agent/owner-walkthrough-after-w6-2026-10-20.md`). Rule what W4-01 records now, and how the ledger and P-node state are written without claiming owner acceptance.
- q8-3. Confirm or replace the key readings listed there.

Append the result as "Run 8 rulings (q8)" to `.agent/W4-01-build-spec.md`. Write nothing else. Do not commit.
