# Plan review - S6-02a / S6-02b (verification core and UI)

Reviewer: fresh Claude, independent of the Planner and the Architect. Branch `plan/S6-02-refine`. Packets reviewed at `166fcd14`, which is unchanged at `e0543173`; the later commits add only the Architect request/answers and `D-2026-10-16-s602-questions`. No code, no test suites.

## Verdict: RETURN (one Medium)

The packets cover the ruling and every re-review carry. Cited code is accurate, and outcomes fail closed. One registry Medium contradicts the core promise of the split, that S6-02a is a non-UI slice mergeable after S6-01a. The Lows are precision items for the same fix round. Separately, the Architect's `D-2026-10-16-s602-questions` packet changes (S6-02a Q1-Q3, S6-02b Q1-Q2) still have to be folded into both packets. That is expected work, not a finding.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 230 nodes, 11 linked pilot panels".
- `... --next-work --json`: exit 0. It parses and ranks (`stop_owner`, I-action-execution-ui vs I-action-history-ui tie). S6-02a/S6-02b appear as candidate `task` values. Of the S6-02a nodes, only `I-verification-plan-read` is eligible (see M1).
- Registry diff vs main: 2 nodes added (`I-S6-02a`, `I-S6-02b`), 228 -> 230. `task` fields were re-pointed: the read/data/producer nodes go to S6-02a and the three UI nodes to S6-02b. Both new IDs were added to `queue_baseline_nodes`, consistent with how S6-01a/S6-01b are listed. That part is sound.
- Code reality on main (S6-01b via `git show task/S6-01b-action-ui`), all confirmed:
  - `0018_finding_match_deferral.py:22-23` is the head (the last migration file is 0018).
  - `postgres_action_store.py:203-232`: accept, a Finding-scoped `action-trial` lock at :217, the Finding-scoped guard at :228-231.
  - `0016_action_store.py:123-162`: the action_event kind, command, channel and server-time CHECKs.
  - `lifecycle.py:64` `reduce`, `service.py:57` `is_unresolved`.
  - `configuration-persistence.ps1:702-709` (ninth writer, table list), `:770-812` (Action forbidden/statement loop), `:1011` (writer-proves-itself).
  - `assessment_worker.py:62-69` `day_windows`, `dispatch_read.py:66-67,123-149`.
  - `dispatch_v3.py:343` `_segments`, with the OPEN_BOUND interval limitation at `:452-456`.
  - `binding_roles.py:18-25,49-82` (roles-2, `pv_available_power` exists at :65), `profiles.py:1856`, `source_provenance.py:245-260`.
  - `action_api.py:121-131,201-215`, `finding_api.py:112-160`.
  - `DECISIONS.md:4123,4145,4152,4155`.
  - Tech design `:57-58,207`, execution plan `:32,55,72`, manifest `:306-330,1395-1452`, `TESTING.md:7-31,91-153` (`-n 2 --dist loadfile`, 20-minute cap, keep-awake).
  - Test files named exist (`test_s6_action_apply_postgres.py`, `test_s3_dispatch_assessment_postgres.py`, `test_s1_bindings_postgres.py`).
  - New items are marked new: migration, verification tables, routes, role set/profile, fixture, walkthrough tool, UI views.

## Coverage of ruling and carries

All present in S6-02a:

- **N1:** one `(tenant,Site,asset,field,rule)` lock replacing the Finding-scoped one, shared by accept and the evaluator. The guard reads all prior Actions at that scope, with a different-Finding test for both guardrail failure and overlap.
- **N2:** the parent-interval OPEN_BOUND makes any segment time in the window INCONCLUSIVE.
- **Residual:** the previous-UTC-day revision is included, with a cross-midnight test.
- **M2:** the guardrail block uses `PRIOR_TRIAL_GUARDRAIL_FAILED` with the Action/outcome link.
- **Roles:** both critical-load roles are time-valid power under a new versioned role set after roles-2, with the Lab profile and readiness messages.
- **Single append path:** the evaluator job alone; the SYSTEM demo command can freeze or request but cannot write a verdict, metric or event.
- **Migration and rule 8:** the migration comes after 0018, with the CHECK migration and `reduce`/`is_unresolved` changes, and statement-level rule-8 entries.
- **Ruling items:** per-window provenance, REASSESSMENT_PENDING as a read state, append-only supersession, `RESOLUTION_WITHDRAWN`, `PRIOR_TRIAL_REASSESSMENT_OVERLAP`, the backdated Foundation pending-then-INCONCLUSIVE rule, closed-window zero-Finding basis, and labelled simulated/no-savings examples.

Fail-closed behaviour is consistent: an unknown fact gives INCONCLUSIVE with the known failure retained, `GUARDRAIL_FAIL` is a reason only, and there are no causal or savings claims.

S6-02b:

- It is held for the owner, stacked on S6-02a and S6-01b with an explicit unmerged-stack rule.
- It uses canonical child routes under the S6-01b root, a typed selector conflict, and a historical outcome that is never shown as current.
- The walkthrough is reproducible: prepare/serve/capture/drop, private DB, 1440/390, six labelled cases, app-vs-v69, owner records acceptance.

Each slice has at most two phases, focused tests per phase, and one final-revision full suite.

## Findings

### M1 (Medium) - the registry gates S6-02a behind the S6-01b owner walkthrough

- **Where:** `frontend/docs/architecture/v69-dependency-registry-pilot.json`
  - `I-S6-02a` has `sequenced_after: ["I-S6-01"]`.
  - It owns `I-sim-verification-cases` (`requires` `I-S6-01`) and `I-verification-read` (`requires` `I-S6-01`).
  - `D-verification-window`, `I-action-evidence-read` and `I-S6-02a` inherit that gate through them.
- **What is wrong:** `I-S6-01` is the umbrella that requires `I-S6-01b`, and S6-01b is held for the owner walkthrough. The packet and README say S6-02a depends only on merged S6-01a/S3/S4/S4-05a and is mergeable after review.
- **Evidence:** next-work confirms the gate. Every S6-02a node except `I-verification-plan-read` shows `I-S6-01`/`I-S6-01b` in its proof path, and none is eligible.
- **Why it matters:** under the owner-absent rule, next-work cannot route S6-02a until the owner accepts S6-01b. That defeats the reason for splitting the slice, and the registry disagrees with the packet's dependency line.
- **Fix:**
  - Re-point `I-S6-02a.sequenced_after` to `I-S6-01a`.
  - In `I-sim-verification-cases` and `I-verification-read`, replace `I-S6-01` with `I-S6-01a` (or `I-action-store`/`I-action-read`).
  - Keep `I-S6-01` on the `I-S6-02` umbrella and the UI side (S6-02b already requires `I-S6-01b`).
  - Rerun the checker and next-work, and confirm the S6-02a nodes become eligible once their architecture inputs are resolved.

### Lows (fix in the same round; non-blocking)

- **L1 - name the verification-table writer.** S6-02a :21 says "Action adapter remains sole Action SQL writer" and "add new verification tables to statement-level rule-8 writer entries". It does not say which module writes the plan/outcome/binding rows.
  - The evaluator writes the outcome and the `RESOLVED` event in one transaction, and the ninth writer was ratified for "Action-owned child rows" (`D-2026-10-15-s601-action-store-and-ui`).
  - State explicitly that `postgres_action_store.py` writes the verification tables: add them to `$actionTables`, INSERT-only. Without that, an implementer may add an unratified tenth writer.
- **L2 - evaluator trigger after late evidence.** The packet makes the read REASSESSMENT_PENDING immediately, and has the evaluator append the settled outcome or `RESOLUTION_WITHDRAWN`. It does not say what starts the re-evaluation: a demo SYSTEM request only, or a durable work marker/schedule tick.
  - It also does not say how an overlap is "detected": an Action accepted after window evidence was accepted, before withdrawal.
  - Fix: name the trigger (a demo request is acceptable for speed, if stated) and the overlap predicate, so the overlap case in the manifest is deterministic.
- **L3 - `action_event` columns beyond the named CHECKs.** `triggering_fixture` is NOT NULL, `authorization_basis` and `actor_id ~ '^service:...'` are required, and `triggering_job` is nullable (`0016:131-138`).
  - Fix: say what the evaluator job writes there (stable job ID in `triggering_job`; fixture or a fixed non-fixture value for a non-demo evaluation), so the CHECK migration is complete the first time.
- **L4 - adjacent tests for the lock change.** Phase 2 names `test_s6_action_apply_postgres.py`, but the accept lock/guard rework mainly touches `test_s6_action_store_postgres.py` and `test_s6_action_records_postgres.py` and the `s6_action_api_contract.json` fixture.
  - Fix: list those test files, and require the S6-01a contract fixture to be regenerated or kept stable explicitly. The recommendation read's `PRIOR_ACTION_UNRESOLVED` capability must also widen to asset scope.
- **L5 - registry umbrella.** `I-S6-02` is only `sequenced_after` `I-S6-02b`. Unlike the `I-S6-01` -> `I-S6-01b` precedent, it does not `require` the slice nodes. Add `I-S6-02b` to its `requires` (I-S6-02b already requires I-S6-02a).
- **L6 - layout evidence.** S6-02b is layout-sensitive (dense evidence slot tables, 390 px). Name `tools/layout-evidence.mjs`, or the walkthrough `capture` as its equivalent. Require a skipped run to be recorded as `not run` with its precondition.
- **L7 - Lab source and interval semantics.** The new five-minute profile has no code citation for where requested/delivered critical load come from. Per-load unserved power exists in the Lab (`simulator_lab_api.py:1055-1058,1433-1436`). Architect Q2 now requires declared interval semantics for power slots (point samples do not establish energy).
  - Cite the kernel source, and state that the new profile publishes interval-valued power.
- **L8 - minor citation.** `LR-01...md:29-32` is cited as a "selected-day/currentness precedent", but those lines are the consequence/schedule seam table. Point to the intended lines or drop the cite.
- **L9 - sizing (preference).** S6-02a carries 3 M + 2 S registry nodes plus a new role set, a two-run Lab producer and the Action guard rework, in two phases labelled M. That is comparable to S6-01a, which needed reopen rounds.
  - Acceptable under "demo speed". Consider putting the role set, Lab profile and manifest production clearly at the front of phase 1, so phase 2 is the evaluator and guard.

## Residual risk (not in the packets)

- Architect Q2 makes SOC/reserve a five-minute sampled guardrail, and requires interval-declared power. If the existing gateway/S2 path only carries point readings for these roles, the new profile and acceptance need interval semantics. That could grow phase 1.
- Feeder demand is `PER_ASSET`. The "total feeder-demand energy" band in Q1 must sum every bound load asset. A missing asset binding in either window should fail comparability, not shrink the total.
- A `RESOLVED` presentation can be withdrawn. Demo scripts must not present it as permanent (carried from the architecture review).

No owner acceptance is claimed or inferred.
