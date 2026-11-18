# S4-05 plan re-review (after fix round 1)

Reviewer: fresh Claude, independent of the Planner (Codex) and of the first reviewer. Date: 2026-10-15.
Branch `plan/stored-demo-provenance`, HEAD `157e3ab8` (merge-base with main `092657c5`).
Inputs: `tasks/S4-05-stored-demo-provenance.md` (umbrella), `tasks/S4-05a-provenance-binding-resolver.md`, `tasks/S4-05b-producers-reads-walkthrough.md`, `tasks/README.md`, registry diff, first review `.agent/S4-05-plan-review.md`, fix brief, `.agent/architect-S4-05-answers.md` (Q1-Q3, rule 8, Follow-up M1), `D-2026-10-15-s405-stored-demo-provenance` (`.ai/DECISIONS.md:4145`).
Scope: targeted. No test suites were run (plan review).

## Verdict: RETURN

One Medium (N-M1). It is a one-line packet fix. Everything else the dispatch asked about is resolved. The Lows do not block.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs` exits 0 and reports "Registry valid: 228 nodes, 11 linked pilot panels". The node count is confirmed at 228.
- `--next-work --json` exits 0 with `status: ranked`, `global_stops: []`, no refusals, and decision `stop_owner` on the LR-01 / I-action-store contest (gap 0.79%). That contest predates this plan and was not introduced by it. The three new README rows parse correctly. The S4-05a, S4-05b and S4-05 umbrella links are discovered by `parseGateQueue`, and all three Status lines map to `not_started`, so they cause no `queue_mismatch` and no false global stop. `parseQueue` does not match the "Stored source provenance" rows. That is consistent with the S4-02c/LR-01 rows and with the fact that no `layer: task` node is involved.
- Every cited path:line was checked against `main` (`092657c5`). The following resolve as described: `MILESTONE_REVIEW_BACKLOG.md:2195,2226`; `postgres_evidence_ledger.py:202` (`open_batch`), `285-296` (`UPDATE ingestion_batch`); `configuration-persistence.ps1:621-625` (ledger tables), `678` (`$pgWriters`), `828` (driver non-vacuity); `finding_read.py:350` (`finding`), `:446` (`evidence`); `consequence_read.py:87` (`dto`), `:149` (`read`); `finding_api.py:247,284,275,306`; `gateway/assetops_gateway/service.py:130` (`seal_batch_v2`); `s402b_fuel_cost_walkthrough.py:201-240` (prepare, P01 priced pick); `FindingConsequence.tsx:115,443`; `financialsClient.ts:108,122,207`; `demonstration_label.py:36-77`; `test_s4_assumption_read_api.py:268-307`; `tools/schedule-install-gate.py:24-35` (`decide`, which already reads `real_pilot_requires`); `tasks/S5-01-site-overview.md:39`. These files exist: `tools/s402b_power_cases.py`, `tools/s402c_late_power_walkthrough.py`, `backend/conversions/s4-power-late-demo-cases-v1.json`, `backend/tests/test_s4_power_demo_case_postgres.py`. The two files absent on main are correctly marked. `tools/s405_provenance_walkthrough.py` is marked "Create". `financials/money_eligibility.py` is marked as LR-01's: it exists on the LR-01 branch, and `finding_api.py:347-367` there is the LR-01 money-gate reasons and `bridge_consequence`. The LR-01 branch adds migrations 0014 and 0015, so the "renumber to 0016" note is correct. The exception is `simulator_lab_api.py:3403`, which exists but anchors the wrong function (N-L1).
- Ports 8935 and 5435 are not used by any other tool or packet on main or LR-01. `vite.config.ts:44` honours `ASSETOPS_API_PORT`.

## Prior findings

| Item | Status | Where |
| --- | --- | --- |
| M1 undesignated = UNKNOWN consequence | Resolved | Umbrella Outcome: unbound historical, unbound ordinary simulation and real rows are `UNKNOWN`, with no current amount on all three money reads even under `CURRENT PRICED`/`ELIGIBLE`. Ordinary Finding pages gain cautious copy, and P01/P02 need a fresh publication. Positive ordinary-simulation class added. Real-pilot gate added as a separate node. S5-01 amendment stated (contract 5). |
| M2 producers, P02, owner walkthrough | Resolved | S4-05b phase 1 names all three producers ("register before upload", "registration failure stops upload"), P02 from the late fixture, and `test_s4_power_demo_case_postgres.py`. S4-05b phase 2 specifies `tools/s405_provenance_walkthrough.py prepare\|serve\|links\|drop`, the `assetops_s405*` / `var/s405*` guards, DB `assetops_s405_owner`, ports 8935/5435, the exact command order, the old-host case without backfill, and what the owner should see. |
| M3 read surfaces / frontend | Resolved | S4-05b phase 1 names the Finding detail `:350`, Evidence `:446`, consequence `:87,149` and both money routes, with exact response fields. It states that the shape changes, names `FindingConsequence.tsx` and `financialsClient.ts`, and requires `tsc`, `npm.cmd test` and desktop/narrow layout evidence. |
| L1 backlog citation | Resolved | `:2195,2226` |
| L2 Architect packet changes | Resolved | Shared lock key and transaction, refusal after partial admission, mismatch failure (contract 2). Truth table and fields (contract 3). Gate composition (contract 4). Insert-only rule 8 and DB immutability, with a column-specific trigger if `ingestion_batch.publication_id` is used (S4-05a phase 1). |
| L3 LR-01 composition / re-chain | Resolved | Contract 5 and S4-05b phase 2 |
| L4 exact P01 membership | Resolved | S4-05b phase 1 checks every cited ID and every consequence power ID. A contextual ordinary ID makes the result `MIXED`. |
| Residual: lock cost | Resolved | S4-05a phase 1 measures sample size, median/p95 and contention against an unbound baseline. |

## Architect follow-up fidelity

- Two positive classes: correct. Contract 1 covers `AUTHORED_DEMONSTRATION` (fixture/spec ID and version) and `REGISTERED_SIMULATION` (server-recorded run ID, run identity/digest, registered `SIMULATED` gateway, proof the exact batch came from the run). It also states that mode, credential, client text, Site/day or manifest alone confers nothing, that there is no public route, and that private truth stays out.
- Truth table and precedence: correct. Several authored publications sharing one fixture/version count as authored. One run, or several runs with a recorded compatible basis, counts as simulation. Crossed classes, mixed bound and unbound IDs, and conflicting fixture/version/run are `MIXED`. Empty, no positive binding, or a missing/foreign/broken link is `UNKNOWN`, and a broken link takes precedence over `MIXED`. Consequence sets are evaluated separately from the union of each revision's own power IDs. Historical revisions keep their own state.
- `I-attested-real-source-provenance`: correct. It is open, has a contract in `acceptance_target` that matches the follow-up (authority, peer/device, capture channel, credential binding, lineage, revocation/correction), and requires `I-stored-demo-provenance`. It is in `real_pilot_requires`, and the `physical_peer_gate` text is updated. S4-05b phase 2 also hard-wires it into `schedule-install-gate.py`, with tests for the open, missing and resolved cases.
- S5-01 amendment: correct. It applies whichever of S4-05b or S5-01 merges second, replaces the line-39 trigger, keeps `MIXED_OR_UNKNOWN_SOURCE` independent of spec readability (including consequence-only power), carries IDs and simultaneous reasons, updates walkthrough expectations, and leaves Finding choice unaffected. One wording point is in N-L3.
- Rule 8 and DB immutability: correct. The packet extends the existing ledger writer, adds no ninth writer, allows only ledger INSERT to publication/link rows, rejects UPDATE, DELETE, TRUNCATE, upsert, DDL and other-writer INSERT, enforces immutability with DB triggers, uniqueness and scoped FKs, keeps existing allowlists and non-vacuity, and accounts for the Action writer.
- Split: coherent. S4-05a is a non-UI binding and resolver that leaves the public DTOs and the heuristic unchanged until S4-05b, so merging it changes nothing visible. S4-05b depends on merged S4-05a and has `USER_REVIEW_REQUIRED: true` with a merge hold. Each is M with two phases.

## Findings

### N-M1 (Medium): S4-05a is non-UI but declares `USER_REVIEW_REQUIRED: true`, which holds its merge and therefore all of S4-05b

`tasks/S4-05a-provenance-binding-resolver.md:3` reads "USER_REVIEW_REQUIRED: true — review the new source-state contract and owner-visible copy proposal at W1; this slice has no UI merge hold." `tasks/README.md:32` repeats "USER_REVIEW_REQUIRED for contract/copy checkpoint".

The project convention is that a `USER_REVIEW_REQUIRED` slice is never merged without the owner's walkthrough (owner-absent rule). The precedent is S6-01a (`README:41`: "non-UI ... USER_REVIEW_REQUIRED: false; mergeable after review"). `packetMeta` reads any value other than `false` as `true`, so a next-work selection of S4-05a reports `user_review_required: true`. The "no UI merge hold" clause contradicts the field. A coordinator following the rule will hold S4-05a, and S4-05b ("after S4-05a is independently reviewed and merged") then cannot start while the owner is away. S4-05a has no owner-visible surface. The copy proposal it mentions is owned and checkpointed by S4-05b.

Fix: set S4-05a to `USER_REVIEW_REQUIRED: false — non-UI; public DTOs and heuristic unchanged until S4-05b; mergeable after independent review; source copy proposal goes to the S4-05b owner checkpoint`. Mirror that in README row 32. Acceptance gap, not preference: it was a dispatch criterion.

### N-L1 (Low): the simulator registration anchor points at the wrong path, and the batch-to-run hop is implicit

`S4-05b` phase 1 cites `simulator_lab_api.py:3403` as the "server-recorded run path". That line is `port.run_to_end(record)` in the run-to-end route, not a release step.

Registered runs reach admission differently. The gateway seals them as STAGED batches. Lab Commit then calls `release_registered`, which moves them to READY and lets the gateway upload them itself. The relevant code is `backend/assetops_backend/simulator_lab_api.py:~3278-3283` and `backend/assetops_backend/runs/execution_ports.py:178`. Because `gateway/assetops_gateway/service.py:_fit` (~140-170) splits by size, one run can produce several batches.

Fix: anchor `REGISTERED_SIMULATION` registration at the registered-commit/release step. Each sealed STAGED batch digest is verified against the run's committed stage (for example the envelope set or `stage_integrity_digest`) and registered before STAGED moves to READY. A release whose registration fails must not move to READY. Without that ordering, a registration that loses the race uploads unbound, and the batch can no longer be registered after admission. That is detectable by the planned "ordinary positively registered run" test but costly to discover late.

### N-L2 (Low): "explicitly recorded compatible run basis" is undefined

Contract 3 lets several runs be `REGISTERED_SIMULATION` with a recorded compatible basis, but no packet says what records that basis. The Architect left it open too. S4-05a should either define the record (who writes it and what it pins) or state that v1 treats several run IDs as `MIXED`, and test whichever it chooses.

### N-L3 (Low): S5-01 ordering wording

`S4-05b` phase 2 says "If S5-01 merges second, its implementer amends its packet before coding". S5-01 may be built, stacked on LR-01, before S4-05b merges and still merge second. Replace "before coding" with "before its merge (re-review the amended source gate)". The Architect's rule is keyed to merge order, not to build order.

## Residual risk (not already named)

- S4-05a phase 1 carries a lot: migration, shared lock, two registration classes with simulator proof, rule 8 and DB triggers, the latency study, and the full probe matrix. It is at the top of M. The phase reviewer should be prepared to split off the simulator-class registration if phase 1 runs long.
- If the implementer picks the `ingestion_batch.publication_id` alternative, `open_batch` already INSERTs with `ON CONFLICT DO NOTHING`. Rule 8's "reject upsert" probe must then distinguish that existing batch INSERT from an upsert on the binding. The preferred separate-table design avoids the problem.
- Owner-visible degradation (ordinary Findings lose any current amount) lands only with S4-05b. The W1 checkpoint is the place the owner sees it. That is unchanged from the first review and already handed off.
