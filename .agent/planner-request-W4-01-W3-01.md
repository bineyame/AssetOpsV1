# Planner request: W4-01 and W3-01 task packets

You are the AssetOps Planner. First read:
- `.ai/ROLE_CONFIG.md`, in full;
- `.agent/post-W2-sequence.md`, which binds D-2026-10-20-post-w2-sequence;
- `tasks/README.md`;
- the format of one recent packet, `tasks/W2-06-ev-assessment.md`;
- `frontend/docs/architecture/site-first-execution-plan.md`, its W3 and W4 parts;
- the v69 registry entries for the named screens;
- the v69 screens themselves, in `frontend/mockups/v69/`.

Write two task packets.

1. `tasks/W4-01-work-case-core.md`, for Lane A step 1. It covers the shared Incident, MaintenanceWorkRequest/Record/Plan, WorkEvent and OperationalRecord identity, plus the lifecycle, attestation and case APIs. It also covers the thin Site lists for `sitework-incidents` and `sitework-maintenance`. The migration is the one allocated in the sequence.
2. `tasks/W3-01-estate-claim-action-roots.md`, for Lane B step 1. It covers the scoped global indexes over existing Site rows, for `findings`, `findings-cost`, `findings-risks`, `findings-opportunities` and `actions`.

Each packet must state:
- the exit criteria;
- the phases;
- the exact v69 screens and panels, with an honest-missing state for any panel that has no source;
- the dependencies;
- the shared-file ownership from the sequence;
- USER_REVIEW_REQUIRED.

Add both rows to `tasks/README.md`, marked "planned; build spec pending".

Write only those three files. Do not commit.
