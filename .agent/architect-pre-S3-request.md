# Architect request: S2 leftovers + mandatory pre-S3 shared-contract decisions (2026-10-09)

Owner instructions (verbatim): 2026-10-09 "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use". 2026-10-09 S2 closeout: "yes merge S2-02 to main and adopt V-01" (`.agent/owner-S2-closeout-2026-10-09.md`).

State: S2 is complete and merged to main at `82ba6cd` (S1, S2-01a/b/c, S2-02). Owner-confirmed `D-2026-10-09-owner-delivery-strategy` is in `.ai/DECISIONS.md`; V-01 is adopted as a W1 item. Branch `plan/pre-S3-startup` (from main) is for pre-S3 planning records.

One batched call:
1. **S2 leftovers:** rule on `.agent/S2-02-questions-7.md` (Q37-Q40) and `.agent/S2-02-fix-rereview.md` R3 (pre-transaction failure reported as ISSUE_OUTCOME_UNKNOWN). Say which, if any, need a follow-up task and where; otherwise record as carries.
2. **Mandatory pre-S3 shared-contract decisions** identified in `.agent/architect-batch-answers-4.md` "Delivery-planning contract answers" item 1: record `A-claim-work-routes` (tenant/Site-scoped Finding and Action routes, revision identity, unavailable/forbidden behaviour), `A-actor-identity` (human author vs authenticated/system actor, attestation provenance), and the bounded selected-window CapabilityReadiness/SourceHealth node (Unknown, freshness, coverage, lineage; separate contact freshness from reported-fact age per `.agent/S2-codex-review.md`). Review FindingIndex stable keys and state the money-comparability guard as that item says, leaving those nodes open. Design them for all three domains (mini-grid, cold chain, EV) per the delivery strategy; implementation stays in its wave. Also resolve `A-S1-bindings` and `A-S2-evidence` with citations as item 2 says.
3. Say what S3-01 refinement must now take from these, and confirm S3-01's technical `requires`.

Record decisions in `.ai/DECISIONS.md` (and the dependency-registry architecture nodes only if that is your file to edit; otherwise list the exact edits for the Planner). Write `.agent/architect-pre-S3-answers.md`. Say whether you want the owner to weigh in. No product code; leave edits uncommitted (the coordinator commits).
