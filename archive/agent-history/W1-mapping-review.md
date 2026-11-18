# W1 37-panel mapping review (fresh Claude reviewer, 2026-10-11)

This review was produced by a fresh Claude reviewer that did not author the mapping. It covers branch `plan/pre-S3-startup`: the Planner mapping pass `e4cf13a` and the registry/checker carry edits inside `75dd4d8`. The PRE-S3-04 product files are out of scope.

The mapping was judged against `.agent/architect-batch-answers-5.md` ("One Planner mapping pass" plus Q1–Q6), the owner W1 confirmation, and `.agent/planner-mapping-questions.md`.

## Verdict

**Accept with findings fixed on the branch.**

- 33 of the 37 panels can be marked `reviewed_mapping:true` now. Some of them have carries.
- 4 panels must not be marked until B1–B3 below are fixed: `dispatch:3`, `finding:2`, `recommendation:3` and `changes:1`.

The mapping meets the rule's core conditions:

- Every `technical_requires` ID is a real registry node. The checker reported no `unknown_node` errors.
- No live `R-*`/`UI-*`/`D-*` proposal remains on a core portion. Proposed gates survive only on the non-core `analysis:3#b` and `asset:3#b`, as Q4 allows.
- No node was resolved by the mapping, and no panel became Real.
- Resolved S1/S2 seams are reused rather than cloned.
- Every new node carries `task`, `layer`, `effort` and `acceptance_target`, and the S3-02 and S4-03 queue rows and packets exist.
- `A-money-comparability` is not on any path, and its reason has been corrected (Q6).

## Checks run

- `tools/check-all.ps1`: all 6 guards PASS (architecture, navigation truthfulness, agent workflow, dependency registry, delivery checker fixtures, ledger with 110 screens and 258 panels).
- Live `check_v69_dependency_registry.cjs --next-work`: **refused**, with `[unmapped_approved_panel]` listing exactly these 37 panels. This is the expected fail-closed result.
- An in-memory simulation in the scratchpad (no repo edit) set the 37 panels to reviewed and ran `delivery_next_work.nextWork`. Results are in "Likely ranking" below.

## Block findings (fix before marking these panels reviewed)

**B1. `dispatch:3#a` requires `I-capability-read` (S3-02).**
- The Architect assigns `dispatch:1-3` to S3-01 and says the S3-02 follow-up must not be an S3-01 prerequisite.
- The S3-01 packet's new text says its nodes "are the real gates for `dispatch:1-3`".
- With this edge, the S3-01 closeout cannot complete its own panel. It also inflates S3-02's reach: `I-capability-read` reaches 4 panels and scores 2.555, against 1.917 without the edge.
- **Fix:** remove `I-capability-read` from `dispatch:3#a`. If a positive capability/coverage portion is intended, split it out as `dispatch:3#b` (variant positive, owned by S3-02) and say so in both packets.

**B2. `finding:2#a` and `recommendation:3#a` require `I-evidence-analysis-claim-limit-ui` and `I-capability-read`.**
- The first is a UI node on the Evidence Analysis screen. A UI on another screen is not a technical AND prerequisite of a Finding or Recommendation panel.
- The bounded "limits / missing inputs" claim comes from the S3 assessment's own claim limits. `analysis:3#a` ("limitation reasons") is mapped to S3-01 alone for that reason.
- The owner packets S4-01 and S6-02 do not mention any S3-02 dependency.
- **Fix:** remove the UI node.
  - If the bounded portion needs only S3 limits, drop the S3-02 nodes.
  - If a positive capability limit is genuinely part of the core claim, add a separate positive portion that requires `I-claim-limit-read`, and record that dependency in the S4-01 and S6-02 packets.

**B3. `changes:1` is a single portion that requires both `I-S6-01` and `I-S6-02`.**
- The Architect splits the panel: the applied-change portion belongs to S6-01 and the "changes:1-2 effect" to S6-02.
- The S6-01 packet now says it "closes … applied-change `changes:1`", but the registry cannot close it without S6-02.
- The S6-02 packet names only "effect `changes:2`".
- **Fix:**
  - Split `changes:1` into `#a`, the applied change (`I-configuration-change-read/ui`, `I-S6-01`).
  - Add `#b`, the effect (`I-verification-read/ui`, `I-S6-02`).
  - Name the `changes:1` effect in the S6-02 packet.

## Carry findings (can be marked reviewed; record and fix in a later pass)

**C1. S4-03 bundling has knock-on gating.**
- Every panel requires the single `I-S4-03` closeout. As a result, `finding-evidence:1-2` and `finding-history:1` depend on `A-finding-index`, which is outside ranking and undecided, and on the Site index fixtures.
- `mini:1/2/4` also depend on the Finding Evidence/History UIs, through `I-S5-01 → I-S4-03`.
- The Architect allowed one "Site Finding/history follow-up" packet, so this is not a mapping error. It does mean the child views wait on the Q6 index decision.
- **Architect question:** accept this, or split the index work from the evidence/history work.

**C2. Variant labelling on `mini:3#a`.**
- It is labelled `variant:"bounded"` with the claim "supported bounded or Unknown portion", but it carries the empty fixture.
- Q3 asks for an explicit empty/Unknown variant, so this portion should be `unknown` with a precise claim.
- The empty variants of `sitefindings:1#a` and `mini:3#a` also include the positive rows fixture through `I-S4-03`. That has no ranking effect, because the checker unions all core portions and Q3 treats both variants as AND for completion.

**C3. Placeholder text.**
- 25 portions keep the placeholder claim "bounded or explicitly missing claim".
- `mapping_target` is identical boilerplate on all 37 and says "independent path review pending", which becomes stale once the panels are marked.
- The reused nodes have no `acceptance_target`: the task nodes `I-S4-01`, `I-S5-01`, `I-S6-01` and `I-S7-01`, plus `I-finding-*` and `I-action-*`.
- The Architect asked to retain the claim and to give an acceptance/evidence target.

**C4. Task-node effort semantics are inconsistent.**
- `I-S6-01` is M but requires 4 M-sized and 7 S-sized open subnodes. `I-S6-02` is M over 3 M-sized and 5 S-sized subnodes. `I-S3-01` is L.
- The registry should define whether a task node's effort means the closeout only or the whole packet. Scoring (E) and the tie-break both use it.

**C5. `A-action-index` gates all 14 Action panels** (a pre-existing edge on `I-action-read`).
- The Architect scoped it to "where the Site list consumes it", which is `sitework:1`.
- This over-gates the detail panels and inflates `A-action-index`'s reach to 14 panels.

**C6. The S6 panels are inconsistent about the S4 Finding gate.**
- `action-overview:1`, `sitework:1`, `recommendation:*` and the verification/changes panels list `I-S4-01`/`I-finding-ui`. The `I-S6-01` node requires only `I-finding-read`.
- So `action-execution:1` and `action-history:1` do not need the S4-01 closeout, while `action-overview:1` does.
- Pick one rule for "gate on S4 Finding" and apply it to all of them.

**C7. `evidence-analysis:2#b` reuses `I-sim-dispatch-cases` for coverage.**
- This is acceptable under the planner Q1 fail-closed default. The S3-02 packet records that a bounded fixture is added if review shows reuse does not prove the rule.
- The S3-02 reviewer must verify it.

## Residual risk (outside this mapping, but it affects the first ranked run)

- The report's global stop only considers S1–S7 queue rows (`parseQueue` matches `S[1-7]`). PRE-S3-03 and PRE-S3-04 are both `Status: in_review`, yet the simulation shows no global stop and selects work. Q7 requires a stop while any packet is active or in review. This should go to the PRE-S3-03 checker lane or the coordinator before any autonomous selection.
- The V-01a packet says the PRE-S3-04 correction must be incorporated before acceptance. In the registry, V-01a requires only `I-S1-03`.

## Likely ranking once the panels are marked (simulated, non-authoritative)

The simulation returned `ranked` with no global stop (see the residual risk above).

| Candidate | Score | Notes |
| --- | --- | --- |
| `I-sim-dispatch-cases` (M, S3-01 phase 1) | 3.011 | Reaches 35 panels. Selected. |
| `A-finding-episode` (Architect node) | 2.676 | Reaches 29 panels. Second; the gap is 11.1%, just above the 10% notice band. |
| V-01a | 2.655 | 7 panels ready now. |
| `I-capability-read` | 2.555 | Inflated by B1/B2. |
| V-01b | 2.463 | |

Other eligible candidates: `A-action-lifecycle` (1.969), and `A-S7-health` and `D-edge-health-cases` (1.542 each).

With B1/B2 fixed, the top two are 3.018 against 2.679, a gap of 11.2%. The decision is unchanged and `I-capability-read` falls to 1.917.

Because the margin over the second candidate is about 11%, small later effort or reach edits could move the result into the 5–10% notice band.
