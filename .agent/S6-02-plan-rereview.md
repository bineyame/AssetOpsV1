# Plan re-review: S6-02a / S6-02b (after fix round 1)

Reviewer: fresh Claude, independent of the Planner, the Architect and the coordinator who edited the checker. Branch `plan/S6-02-refine` at `df7b7105`. The fix is `26c34da8` (Planner) plus `df7b7105` (coordinator checker change). This is a targeted re-review. I ran no test suites.

## Verdict: ACCEPT

M1 is resolved, and the checker exception is minimal and fails closed. Every Architect ruling in `D-2026-10-16-s602-questions` is folded in exactly, and L1-L8 are addressed. Two precision Lows remain (R1, R2). Neither blocks.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 230 nodes, 11 linked pilot panels".
- `... --next-work --json`: exit 0, `status: ranked`, `decision: stop_owner` (I-action-execution-ui vs I-action-history-ui tie, unchanged), no global stops.
- `node frontend/docs/architecture/test_delivery_next_work.cjs`: 35/35 pass.

## M1: resolved

- **Registry diff (`26c34da8`):**
  - `I-S6-02a.sequenced_after` is now `["I-S6-01a"]`.
  - In `I-sim-verification-cases.requires` and `I-verification-read.requires`, `I-S6-01` is replaced by `I-S6-01a`.
  - `I-S6-02.requires` gains `I-S6-02b` (L5). The umbrella keeps `I-S6-01`.
  - `I-S6-02b` still requires `I-S6-01b`.
  - `D-verification-window` requires the resolved `I-action-store`, not the umbrella.
- **Transitive closure:** I computed the `requires` + `sequenced_after` closure of each S6-02a node, stopping at resolved nodes. Every open upstream node is an S6-02a-owned node: `D-verification-window`, `I-sim-verification-cases`, `I-verification-plan-read`, `I-verification-read`, `I-action-evidence-read`. None is `I-S6-01`, `I-S6-01b` or an S6-01b UI node. Every direct external input is resolved: `I-S6-01a`, `I-action-store`, `I-action-read`, `D-action-records`, `I-accepted-evidence-store`, `I-S2-02`, `I-S3-01`, `A-S6-verification`, `A-demo-scenarios`.
- **next-work:**
  - `eligible` now contains `I-sim-verification-cases` as well as `I-verification-plan-read`. The first review found only `I-verification-plan-read` eligible.
  - Each remaining S6-02a node's `blocked` reason lists only S6-02a-owned prerequisites. For example, `I-S6-02a` is blocked on "D-verification-window, I-action-evidence-read, I-sim-verification-cases, I-verification-plan-read, I-verification-read".
- **About the brief's wording:** the per-candidate `paths[].proof` arrays still list `I-S6-01`/`I-S6-01b`. Those arrays are screen-closure sets: everything needed to finish the action-plan, action-evidence and verification panels, which include the S6-01b UI. They are not the candidate's prerequisite gate. So the literal check "proof paths no longer carry S6-01b" is not the right test. Eligibility and `blocked` are, and both pass. The same distinction applies to the first review's M1 evidence wording. The finding itself was correct, because eligibility was gated.

## Coordinator checker change (`df7b7105`): minimal, correct, not weakening

- **The change:** one `predecessorOverride = {'S6-02a': ['I-S6-01a']}` entry. It is consulted before the existing default rule, and the check is still exact JSON equality on `sequenced_after`. Without the entry, S6-02a's default predecessor would be `I-S6-01`, the umbrella row before it in `tasks/README.md`.
- **What is untouched:**
  - The other 18 S1-S7 tasks still take the default predecessor rule, or the existing `S6-01`/`S7-01` empty exceptions.
  - The task-row/packet/registry equality checks and the direct architecture-gate check are unchanged.
  - The combined technical/queue cycle check is unchanged.
  - The layered-capability co-resolution check is unchanged.
- **Failure modes:**
  - If S6-02a is renamed, the override goes inert and the default rule applies. That fails closed.
  - If `I-S6-01a` is removed, `visitQueue` rejects an invalid dependency.
  - The override cannot be satisfied by an empty or missing `sequenced_after`.
- **Authority:** the comment cites `D-2026-10-16-s6-verification`, which orders non-UI proof before UI, and this review's M1. Both support the exception.
- **New fail-open paths:** none found.
- **Optional, non-blocking:** `test_delivery_next_work.cjs` has no case pinning the override, either that S6-02a equal to `I-S6-01` is refused or that S6-02a is not routed behind S6-01b. A one-line test would keep a later edit from reverting M1 unnoticed.

## Architect rulings: folded in exactly

- **S6-02a Q1 (bands): present.**
  - Feeder-demand and PV-available energy within 10%, inclusive, and initial SOC within 2 percentage points, inclusive.
  - kWh integration over the window, using PV *available* power.
  - A zero baseline requires a zero later total.
  - Missing, negative, ambiguous or non-finite inputs give INCONCLUSIVE, and exact decimal comparison is used.
  - The bands are frozen in the plan and API fixture, with no widening after freeze, and exact-match fields are kept.
  - Tests cover the inclusive edge, just outside the edge, and a zero baseline.
- **S6-02a Q2 (slots): present.**
  - Twelve UTC-aligned, half-open five-minute slots.
  - Whole-slot or exact-partition power values, integrated as `kW*s/3600`.
  - Point samples establish no energy, and gaps, conflicts and interpolation are refused.
  - SOC is sampled at each slot start and at the window end.
  - The reserve is read at slot start, and an intra-slot change makes the slot unassessable.
  - Each below-reserve slot counts 300 s, labelled as a "five-minute sampled guardrail".
  - No sample is carried across a missing boundary.
  - The convention is stated in coverage, the evaluator, the Lab profile and the evidence API, with boundary, partial-slot, conflict and missing-terminal tests.
- **S6-02a Q3 (replacement): present.** A new immutable ID with `supersedes_plan_id`. Bounds may be reused only while no later report has been accepted **and** no later run has begun. An idempotent retry returns the original ID, superseded plans stay addressable, and both sides of the cutoff are tested.
- **S6-02b Q1 (labels): present.** The three interim labels are exact, with metric, value, threshold, unit and evidence IDs. The typed INEFFECTIVE/INCONCLUSIVE outcomes are kept. The copy pass is deferred to the W1 conclusion.
- **S6-02b Q2 (default): present.** The default is the latest current read state, including PENDING and REASSESSMENT_PENDING, with an explicit link to the prior outcome. A historical selector persists in the URL across child links and reload, with a `Historical` label and a separate current state. An old VERIFIED is never shown as current, and conflicting selectors give a typed error. The owner walkthrough includes these cases.
- **Umbrella and README:** both summarise the rulings without contradicting the child packets.

## Lows L1-L9

- **L1: resolved.** `postgres_action_store.py`, the ninth writer, writes the verification plan, binding, metric and outcome tables INSERT-only and appends evaluator events in the same transaction. The packet says "no tenth SQL writer" and adds these tables to `$actionTables` (the declaration is at `configuration-persistence.ps1:707-708` on this branch; the packet cites `:708-709`, which is off by one and harmless).
- **L2: resolved, with a precision Low (R1 below).** The trigger is a SYSTEM demo evaluation request after S3/S4 settles. An overlap predicate is now stated.
- **L3: resolved.**
  - `triggering_fixture`: the fixture ID, or `non-demo-evaluation`.
  - `actor_id=service:verification-evaluator`.
  - `authorization_basis=SYSTEM_VERIFICATION_EVALUATOR`.
  - `triggering_job`: the stable job ID.
- **L4: resolved.** The store, records and apply Postgres tests are listed. `s6_action_api_contract.json` must be regenerated or explicitly proved stable. The Recommendation `PRIOR_ACTION_UNRESOLVED` check is widened to battery scope.
- **L5: resolved.** `I-S6-02` requires `I-S6-02b`.
- **L6: resolved.** `tools/layout-evidence.mjs` must run for the dense Evidence slots at 1440/390, or be recorded as `not run` with its precondition.
- **L7: resolved.**
  - The citation `simulator_lab_api.py:1052-1058,1429-1436` is verified: per-load `demand_power`, `served_power` and `unserved_power`.
  - The profile publishes interval-valued power.
  - The point-reading risk for the new roles is carried as a phase-1 risk.
- **L8: partly resolved (R2 below).**
- **L9: addressed.** Phase 1 now leads with migration, roles, the Lab profile and the manifest.

## Residuals stated

- A missing load binding fails comparability and never shrinks the total.
- Demo scripts must show RESOLVED as withdrawable, never permanent. This is in both S6-02a and S6-02b.
- Point-reading versus interval handling is a phase-1 risk.

All three first-review residuals are carried.

## Remaining findings (Low, non-blocking)

- **R1 (Low): overlap predicate wording.** At `tasks/S6-02a-verification-core.md`, in the "Late accepted evidence" paragraph, the packet says "when an Action was accepted after evidence for its verification window had been accepted but before the evaluator withdrew the invalidated resolution". The Architect's definition (`.agent/architect-A-S6-verification-answers.md`, overlap sentence) is narrower: the late evidence *that invalidates the closure* was accepted before the subsequent Action, and withdrawal came after it.
  - Read literally, "evidence for its verification window" includes the on-time evidence the closure was built on. An Action accepted after RESOLVED but before the late report arrived would then be permanently blocked.
  - The intent is recoverable. Fix in the build or a one-line touch-up: "accepted after the late SourceEnvelope that invalidated the prior Action's resolved basis, and before the matching RESOLUTION_WITHDRAWN". Pin both sides in the overlap test: an Action before the late evidence is not an overlap, and an Action after it is.
- **R2 (Low): LR-01 citation still imprecise.** `tasks/LR-01-late-reading-series-and-money-limit.md:29` is the consequence bridge/rendering table row, not currentness. `:32` (the money invariant) mentions currentness only in passing. Either drop the cite or point it at the read-state lines intended.

## Residual risk not in the packets

- The branch base is not current `main`: `git merge-base --is-ancestor main HEAD` fails. S6-02a already requires the implementer to recheck the migration head and code citations before coding. Line-level anchors such as `postgres_action_store.py:205-232` and `configuration-persistence.ps1:708-709` should be rechecked on the build base.

No owner acceptance is claimed or inferred.
