# W1 mapping fix round re-review (fresh Claude reviewer, 2026-10-11)

A fresh Claude reviewer produced this re-review. It did not author the mapping, the original review, or the fix. Scope: commit `9ae48ef` on `plan/pre-S3-startup` (base `69d6c12`), judged against `.agent/W1-mapping-review.md` (B1-B3, "Residual risk") and `.agent/architect-batch-answers-5.md`. No branch switch, no repo edit, no commit.

## Verdict

**Accept.** B1-B3 are closed. The PRE-S3 global stop and the V-01a requirement are correct. The 33 panels cite the review correctly, and nothing else moved.

**These 4 may be marked `reviewed_mapping:true` citing this re-review: `dispatch:3`, `finding:2`, `changes:1`, `recommendation:3`.**

Two carries are recorded below. Neither blocks the panel marks or the first selection. C9 must be fixed before any visual-gate packet (V-01a/V-01b) or carry-lane packet (S2-02r) is activated.

## What was verified

I compared the old and new registry JSON structurally, by node id and by panel key.

- **Only three registry areas changed:** the new node `I-PRE-S3-04`, `V-01a.requires`, and `w1_panel_mapping`.
- **Mapping content changed on exactly 4 panels:**
  - `dispatch:3`, `finding:2` and `recommendation:3` had requires removed.
  - `changes:1` was split.
  - Every other panel changed only its `reviewed_mapping` and `mapping_review` fields.
- **B1 is closed.** `dispatch:3#a` no longer requires `I-capability-read`. It is gated only by S2 and S3-01 nodes, which matches Architect row S3-01 ("not an S3-01 technical prerequisite"). `I-capability-read` now reaches only `evidence-analysis:2#b`, with a score of 1.917, as predicted.
- **B2 is closed, and the implementer's choice is sound.** `finding:2#a` and `recommendation:3#a` drop both `I-evidence-analysis-claim-limit-ui` and `I-capability-read`.
  - Panel contract `finding:2` ("What limits this conclusion") reads `FindingRevision` from `finding_revision + assessment_revision`, owned by S4-01+S4-02. The limits come from the S3 assessment, and `I-dispatch-read` remains in the path.
  - `recommendation:3` ("Evidence needed to verify") is satisfied by the frozen plan's required evidence. `I-verification-plan-read` and `I-S6-02` remain in the path, and the S6-02 packet names "predeclared target/guardrails and required evidence".
  - Architect row S3-02 limits S3-02 to positive capability/coverage portions, and neither bounded portion is positive. See carry C8 for the stale "CAP" boundary labels.
- **B3 is closed.**
  - `changes:1#a` is the applied change: S6-01 nodes plus `I-configuration-change-read/ui`. It has no verification or dispatch nodes.
  - `changes:1#b` is the later-window effect: it adds `A-S6-verification`, `I-S6-02`, `I-sim-verification-cases`, `D-verification-window`, `I-verification-read/ui` and `I-dispatch-read/ui`.
  - The S6-01 packet now names `changes:1#a`, and the S6-02 packet names `changes:1#b`. This matches the contract claim limit, "No later evidence means outcome pending", and Architect row S6-02 ("changes:1-2 effect").
- **The global stop is correct for PRE-S3 packets.**
  - `parseGateQueue` reads every `[PRE-S3-NN](x.md)` link and deduplicates them. It finds PRE-S3-03 and PRE-S3-04 in `tasks/README.md` line 34.
  - `packetPhase` maps `done (accepted …)` to `done` through `/^done\b/`. An unknown or missing Status refuses.
  - The CLI fingerprints gate packet status.
  - Live check: with PRE-S3-04's Status changed in memory to `in_review`, the decision is `stop: PRE-S3-04 is in_review`.
- **V-01a is correct.**
  - It requires `["I-S1-03","I-PRE-S3-04"]`, which matches its packet ("PRE-S3-04 correction incorporated before acceptance").
  - `I-PRE-S3-04` is resolved, and its evidence is the packet, whose Status is `done (accepted 2026-10-11 …)`.
  - V-01a stays eligible with 7 panels ready now.
- **The 33 panels are exactly the 37 minus the 4.**
  - Each newly true panel has `mapping_review.evidence = ../../../.agent/W1-mapping-review.md`, with `by` set to a fresh Claude reviewer under Architect Q9.
  - The 14 earlier PRE-S3-03 citations are unchanged.
  - The panels that are still false are the 4 under review here plus 13 non-core or out-of-scope rows (`sites:2`, `readiness:2-4`, etc.). None of those 13 is in the 37.
- **Packet text.** Only the S6-01 and S6-02 sentences changed. The S3-02 packet still claims only `evidence-analysis:2#b`.

## Checks run (my own runs)

- `tools/check-all.ps1`: all 6 guards PASS. The ledger reported 110 screens, 88 models and 258 panels.
- `node test_delivery_next_work.cjs`: 21/21 pass.
  - I copied the pre-fix `delivery_next_work.cjs` from `HEAD~1` and the new test file into the scratchpad and ran them there. Result: 19 pass, 2 fail. The new tests fail without the change.
- Live `check_v69_dependency_registry.cjs --next-work`: **refused**, `[unmapped_approved_panel]`, for exactly `dispatch:3, finding:2, changes:1, recommendation:3`. The fingerprints match the fix notes.
- The backend and frontend suites were not run. This is a planning/registry-only change and no product files changed.

## Likely ranking with the 4 marked (in-memory simulation, non-authoritative, no repo edit)

A `fs.readFileSync` preload marked the 4 panels as reviewed, and the real CLI then ran `--next-work`. The status was `ranked` with no global stop.

| Candidate | Effort | Panels (tech/visual) | Score |
| --- | --- | --- | --- |
| `I-sim-dispatch-cases` | M | 35/0 | **3.018 (selected)** |
| `A-finding-episode` | M | 29/0 | 2.679 |
| V-01a | L | 0/7 (7 ready now) | 2.655 |
| V-01b | L | 0/8 | 2.463 |
| `A-action-lifecycle` | M | 14/0 | 1.969 |
| `A-S7-health`, `D-edge-health-cases` | M | 2/0 | 1.542 |

Decision: `select I-sim-dispatch-cases` (S3-01 phase 1), `user_review_required: true`, with an 11.2% gap over the runner-up and no notice. This matches the original review's post-fix prediction. The margin is still about 1 point above the 10% notice band.

## Findings

**C8 (carry, Architect/Planner wording): stale "CAP" boundary labels.**
- Where: `finding:2#a` boundary "FIND + CAP; …" and `recommendation:3#a` "WORK + CAP + …" in `frontend/docs/architecture/v69-dependency-registry-pilot.json`.
- Problem: both labels still say CAP, but the portions no longer carry a capability node. Panel contract `recommendation:3` also names `CapabilityReadiness` as its read model.
- Why it matters: the paths are correct, but the labels suggest an S3-02 dependency that does not exist.
- Fix: in the C3 placeholder pass, reword the labels to "S3 assessment limits" and "plan required evidence". If the Architect wants a positive capability limit in either panel, add it as a separate positive portion, as the fix notes already say.

**C9 (carry, with a deadline): the Q7 global stop covers only `PRE-S\d-\d{2}` links.**
- Where: `frontend/docs/architecture/delivery_next_work.cjs:23-27`, `:308-310`.
- Problem: the stop does not read the visual-gate packets (V-01a/V-01b), the S2-02r carry-lane packet, or any other non-S, non-PRE packet.
- Evidence (in memory, 4 panels marked): V-01a's Status set to `active` gave `select I-sim-dispatch-cases`, and S2-02r's Status set to `active` gave the same. Q7 says any active or in-review packet stops selection.
- Why it matters: V-01a ranks third. Once V-01a is selected and set active, the loop would select new work in parallel, and could even select V-01a again.
- Not a block now: no such packet is active, and this round's scope was the PRE-S3 packets.
- Fix before activating V-01a, V-01b or S2-02r: feed the `visual_gates` packet phases, and every packet linked from `tasks/README.md`, into `activeTasks`. Add a fixture for an active visual-gate packet.

Carries C1-C7 from the original review remain untouched and open.

## Residual risk

- The ranking margin is about 11%, so the C3/C4 effort or reach edits could move it into the notice band.
- `I-PRE-S3-04` uses `layer: projection` for what was a UI copy correction. It is harmless because the node is resolved, and it is not a finding.
