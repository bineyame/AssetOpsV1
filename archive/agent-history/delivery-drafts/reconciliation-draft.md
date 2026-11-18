# Startup 1 reconciliation draft — 2026-10-09

Planning only. Source baseline: `main` at `b4006d1` for merged S1-01/02/03 and S2-01a/b/c; current S2-02 task branch is excluded. Apply only after S2-02 independent review, S2 owner Evidence closeout, and the S2-wide Codex review required by the queue. Status means reviewed task closeout, not merely merged code. Preserve carries in the task packets and `.ai/MILESTONE_REVIEW_BACKLOG.md`.

## Exact registry and checker edits proposed

Target: `frontend/docs/architecture/v69-dependency-registry-pilot.json` and its checker. Evidence cells below are pointers to be checked against the accepted review record at application; they are not new approvals.

| Node(s) | Current | Proposed after evidence check | Evidence / limitation |
| --- | --- | --- | --- |
| `I-S1-01` | open | resolved | S1 packet and main merge `26d013b`; owner UI acceptance |
| `I-S1-02` | open | resolved | S1 packet and main merge `26d013b`; owner UI acceptance |
| `I-S1-03` | missing | add `implementation`, `layer: task`, `area: configuration`, `task: S1-03`, `requires: [A-S1-organization, I-S1-02]`, `sequenced_after: [I-S1-02]`, resolved | S1-03 review/merge and `D-2026-10-08-s1-foundation-organization`; add resolved architecture node `A-S1-organization` with that decision as evidence. S1-03 is a view organization cut, not another data store. |
| `I-lab-registered-basis`, `I-S2-01a` | open | resolved together | S2-01a reviewed merge at `7c10283`; carries stay visible |
| `I-edge-outbox`, `I-edge-simulated-adapter`, `I-S2-01b` | open | resolved together | S2-01b reviewed merge at `7c10283`; carries stay visible |
| `I-edge-diagnostics-publish`, `I-edge-fault-scenarios`, `I-S2-01c` | open | resolved together | S2-01c fresh review after fix rounds and merge `b4006d1`; verify final review packet |
| `A-S1-bindings`, `A-S2-evidence` | open | resolve only when their *full registry decision wording* matches recorded decisions; otherwise narrow/split the nodes | Their current open state blocks transitive readiness of already reviewed S1/S2 nodes. An implementation merge cannot silently approve a broader architecture contract. Architect verifies exact scope and cites decision IDs. |
| `I-accepted-evidence-store`, `I-edge-diagnostics-store`, `I-S2-02` | open | leave open in this draft | S2-02 remains active. Reconcile only after its required reviews and owner checkpoint. |

Add `I-S1-03` to `queue_baseline_nodes` adjacent to S1-02, and add it to the checker task list between S1-02 and S2-01a. Change `I-S2-01a.sequenced_after` from `[I-S1-02]` to `[I-S1-03]`. The checker currently hard-codes 13 tasks against the queue's 14 and fails at `Task queue rows, packets and registry task sequence differ`; update task discovery from `tasks/README.md` as the owner strategy requires. Validate task packet existence, unique IDs, task-node identity, same-status layered nodes, graph acyclicity, evidence for resolved nodes, and owner decisions separately. `A-S1-organization`/`I-S1-03` must be inserted before resolving S1-03. Do not infer panel-real status from these changes.

When S2-02 closes, change its three nodes together, attach accepted review/merge evidence, and retain any carries; do not mark them resolved from phase commits. Recheck `queue_baseline_nodes` for each refined S3-S7 packet and remove nodes no longer actually owned by that queue before estimates are used.

## Queue prose and predecessor edits proposed

`tasks/README.md` currently has mutually stale lines: the opening paragraph says S2-01c has R1 open and S2-02 is waiting, although the row says S2-01c merged at `b4006d1`; a later paragraph again calls R1 open. Replace both with the merged S2-01c reviewed state and current S2-02 implementation/review status at application time. Replace the paragraph that calls S1/S2-01a/b merged and S2-01c open with a factual S1/S2-01a/b/c merged summary. Replace the statement that the checker has a 13-task mismatch once the 14-task reconciliation passes. Do not rewrite S2-02 as done until its actual closeout. The pre-S3 paragraph should distinguish mandatory architecture decisions from implementation/dispatch prerequisites and reflect the Architect's recorded scope ruling.

Current explicit `Depends on`/`Direct dependency` edges for S3-S7, classified for a future queue/packet/checker diff:

| Edge | Classification | Reason and proposed edit |
| --- | --- | --- |
| S2-02 → S3-01 | technical `requires` | Dispatch consumes centrally accepted evidence, typed source identity and normal ingestion; retain `I-S2-02` and fixture gate. |
| S3-01 → S4-01 | technical `requires` | Finding episode and exact lineage derive from dispatch assessment revisions; retain through `I-finding-store`/`A-finding-episode`. |
| S4-01 → S4-02 | technical `requires` | Financial consequence is bounded to the Finding/episode; retain plus actor and assumption gates. |
| S4-02 → S5-01 | technical `requires` for **bounded money panel**, ordering-only for a partial Overview | Current S5 promise includes bounded cost and exact drill-down, so retain for this packet. If owner approves a smaller core panel, split the packet and keep the money panel gated; never pretend full S5 is independent. |
| S5-01 → S6-01 | ordering-only `sequenced_after` | Action uses accepted Finding, S1 Foundation publish, actor/route contracts and action records; it does not consume Site Overview. Remove from S6-01 `Depends on` and sequence after queue reconciliation. Its actual technical graph still requires `I-finding-read` (hence S4-01) and S1. |
| S6-01 → S6-02 | technical `requires` | Verification requires persisted Action, applied policy change, baseline and later window; retain with `D-verification-window` and producer. |
| S6-02 → S7-01 | ordering-only `sequenced_after` | SourceHealth consumes S2 diagnostics, bindings and health fixtures; battery stress needs its own accepted observation or stays Unknown. No S6 verification output is required. Remove from S7-01 `Depends on` and sequence after queue reconciliation. |

The linear checker `sequenced_after` chain contains additional ordering-only links S5-01→S6-01 and S6-02→S7-01. For the other edges, keep the row order as scheduling history if desired, but readiness must be calculated from `requires` and panel AND gates only. Do not release S3-S7 selection around a currently binding queue/packet edge before the tracked files and checker agree. Owner review checkpoints S4/S6/S7 still block acceptance even when tasks reorder.

## Startup guard at application

Run the updated registry checker, ledger and navigation guards, compare the 14 queue rows with task nodes, confirm resolved evidence citations and carries, then compare `git diff` against the S2-02 review baseline. Record the final S2-02 state and owner input only from their actual records. This document does not alter executable status.
