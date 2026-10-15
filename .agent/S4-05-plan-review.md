# S4-05 plan review - stored demonstration provenance

Reviewer: fresh Claude (independent; did not author the packet). Date: 2026-10-15.
Branch `plan/stored-demo-provenance` at `f9c75089` (packet `98bf4d93`). Packet: `tasks/S4-05-stored-demo-provenance.md`.
Architect answers `.agent/architect-S4-05-answers.md` were present in the worktree (uncommitted `DECISIONS.md` edit) and were read; Q1-Q3 accepted with packet changes, which the packet does not yet carry.

## Verdict: RETURN

Three Medium findings (M1-M3). The core design (pre-admission SYSTEM publication, ledger-writer extension, set-state rule, heuristic retirement) is sound and the code reality is accurate. The gaps are in stating the product-wide consequence of "undesignated = UNKNOWN", the authored-fixture producers and the owner walkthrough, and the read surface that "traced into Finding reads" names.

## Checks run

- Code reality, spot-verified on main (`092657c5` base): `demonstration_label.py:36-45,60-77` (heuristic: Site code + UTC day, unreadable spec -> "Source not confirmed"); callers `finding_api.py:34,275,306` (only runtime callers; grep); `FindingConsequence.tsx:115,443`; `test_s4_assumption_read_api.py:268-307`; `0005_evidence_ledger.py:116,161-210` (`source_mode LIVE|SIMULATED`, composite batch FK); `postgres_evidence_ledger.py:202-240` (`open_batch` ON CONFLICT DO NOTHING), `242-307` (`decide_chunk` FOR UPDATE, chunked, UPDATEs `ingestion_batch`), `309+` (`_persist`, duplicate via `accepted_evidence_message_unique`); `evidence_api.py:264-275,287`; `postgres_finding_store.py:161,308`; `finding_read.py:350,446`; `consequence_read.py:87,149`; `finding_api.py:247,284`; `publish_assumption.py:1-4,104`; `configuration-persistence.ps1:621-625` (ledger tables, target-only check), `678-704`, `828-840` (non-vacuity); `check-all.ps1:64`; `DECISIONS.md:3987-3989`; `TESTING.md:7-29,104,152`. All accurate except L1.
- Migration head on main is `0013_schedule_state`; LR-01 branch adds `0014_source_clock_attestation` and `0015_finding_returning_basis` (re-chain stated).
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0. Registry diff only sets `I-stored-demo-provenance.task` to `S4-05`; node stays `open`; README row valid.
- Not run: any test suite (plan review, no node_modules, per dispatch).

## Acceptance-target coverage (`I-stored-demo-provenance`)

| Clause | Covered |
| --- | --- |
| Server-authorized immutable tenant/Site-scoped publication, fixture/spec version, publication ID | Yes (contract 1-2; Architect Q1 adds lock/mismatch detail to apply) |
| Binds accepted evidence IDs | Yes (contract 3; duplicate/rejected/restart covered) |
| Traced into Finding and consequence reads | Partial - money routes only are named (M3) |
| Mixed/unknown cautious | Yes for money routes; product-wide consequence unstated (M1) |
| Date heuristic retired | Yes, exact lines |
| Wrong-Site and client-only/gateway authorship refused | Yes (phase 1 tests, guard probe) |
| Writer/rule 8 | Correct: existing ledger writer extended, INSERT-only, DB immutability (Architect adds) |
| Lock/race, no retroactive authorship | Yes (contract 2-3, cutover) |

## Findings

### M1 (Medium, acceptance/consequence gap) - "undesignated = UNKNOWN" silently withdraws every non-demonstration amount and labels every ordinary Finding

Packet contract 4 and Architect Q2/Q3 make an accepted ID with no designation `UNKNOWN`, and `UNKNOWN` blocks a current amount on Financials, consequence and S5. There is only one designation (`AUTHORED_DEMONSTRATION`). Consequence: after merge, every ordinary or real Finding (F01-gateway, P02, all future real KOBO-001 data) reads "Source not confirmed" with no current amount, and nothing in the contract can ever change that for real data. The Architect ruling is fail-closed and I do not dispute it, but the packet does not say so. Today's ordinary Findings carry no source label (`finding_api.py:275,306` return `None`), so this is a visible change on every Finding page, not just P01. It also leaves `tasks/S5-01-site-overview.md:39` stale: S5-01 produces `MIXED_OR_UNKNOWN_SOURCE` only when the spec file is unreadable, and it reuses `demonstration_case`, which this packet removes. Closing this node also satisfies a `real_pilot_requires` gate (`registry:6`, `tools/schedule-install-gate.py:32`) while pilot money stays impossible until an undefined "pilot data designation" exists.
Fix: in Outcome/Cutover, state that all undesignated evidence becomes cautious with no current amount, and list the affected surfaces and fixtures. Name the positive pilot/real-source designation as an explicit follow-on (a new open registry node, or a W1/pilot checkpoint item next to the owner wording question) so the pilot gate is not read as money-ready. Record the S5-01 packet amendment (trigger `MIXED_OR_UNKNOWN_SOURCE` from the stored-provenance resolver, not `demonstration_case`) for whichever of S4-05 or S5-01 merges second.

### M2 (Medium) - authored-fixture producers, P02 and the owner walkthrough are missing

- `backend/conversions/s4-power-late-demo-cases-v1.json` (P02, "authored ... same evidentiary class ... as s4-power-demo-cases-v1", KOBO-001 2026-10-24) is also authored demonstration content. The heuristic never labelled it, and the packet does not mention it. Under the new rule it becomes `UNKNOWN`, with no amount, unless it gets a publication. That conflicts with the LR-01 and S5-01 walkthroughs, which expect P02 `ELIGIBLE` with a current amount.
- The producers post through the gateway with no pre-admission step: `tools/s402b_power_cases.py` (P01), `tools/s402b_fuel_cost_walkthrough.py:230` ("P01-power (demonstration data, priced)") and `tools/s402c_late_power_walkthrough.py` (P02). The packet does not say these must register a publication before upload, so the existing P01 walkthrough loses its label and amount. Adjacent `backend/tests/test_s4_power_demo_case_postgres.py` is not named.
- USER_REVIEW_REQUIRED is true, but the only owner step is "record an exact P01 plus same-day ordinary source walkthrough". There is no tool, private DB or work directory, ports, URL list or command order, unlike LR-01/S5-01. That is not reproducibly reachable by the owner.
Fix: name the producer changes (publish via the SYSTEM command, then upload the exact batch) and decide whether P02 is designated. Add the adjacent P01/P02 tests to phase 2. Specify a repeatable owner walkthrough: tool, private `assetops_s405*` DB, ports, P01 authored, same-day ordinary or undesignated, mixed case, and an old-host-without-publication case. Give the commands in order and the API IDs to record.

### M3 (Medium, acceptance ambiguity) - read surface for "traced into Finding reads" and the frontend scope are unnamed

Phase 2 names only the two `finding_api.py` money routes. The Outcome says the selected FindingRevision shows provenance, and the Architect Q2 requires per-evidence provenance, all publication IDs, problematic IDs and separate Finding/consequence states. The packet does not name which DTOs carry these: Finding detail (`finding_read.py:350`), the Evidence page (`finding_read.py:446`), consequences (`consequence_read.py:87`) and Financials. Today the frontend renders one `{label, statement, case_id}` object (`FindingConsequence.tsx:115,443`), and "with exact IDs" plus "backend-only, no new screen" may be incompatible. Fix: name the routes and response fields. Either keep the `demonstration` object backward-compatible and state that the frontend is unchanged, or name the frontend files plus `npx.cmd tsc --noEmit`, `npm.cmd test` and the layout-evidence obligation (or `not run` with its precondition).

### Low

- L1: The backlog citation `.ai/MILESTONE_REVIEW_BACKLOG.md:2157` is unrelated (S4-02 L1 technical design rows). The relevant lines are 2195 (L2 real-pilot checker) and 2226 (pilot install gate on this node).
- L2: Apply the Architect packet changes: Q1 lock key and transaction, refusal after partial admission, mismatch failure; Q2 truth table and response fields; Q3 gate composition with `CURRENT PRICED` and LR `ELIGIBLE` plus tests; rule-8 INSERT-only and DB immutability. If the binding is `ingestion_batch.publication_id`, note that the ledger UPDATEs `ingestion_batch` (`postgres_evidence_ledger.py:285-296`), so a DB trigger and column-level guard are needed. A table-level guard is not enough.
- L3: LR-01 is in walkthrough and likely merges first. Name the composition point `financials/money_eligibility.py` and `finding_api.py:342-367` on LR-01, and the renumber to `0016`.
- L4: P01's positive proof requires every cited ID of its selected FindingRevision, and the consequence's power intervals, to come from published batches. Any ordinary context row from another batch makes it `MIXED`. Have phase 2 assert the P01 cited set's batch membership explicitly.

## Residual risk

The fail-closed default (M1) will make ordinary-Finding pages look degraded at the W1 checkpoint. The owner should see that before approving the wording. The race proof depends on both transactions holding the same advisory lock. Every gateway `open_batch` now takes that lock, which adds a small cost to ingestion. Measure it in the phase-1 tests.
