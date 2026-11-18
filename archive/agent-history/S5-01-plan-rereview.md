# S5-01 plan re-review after fix round 1 (fresh independent Claude reviewer, 2026-10-15)

Subject: `tasks/S5-01-site-overview.md` at `d5984d3a` on `plan/autonomy-2026-10-15`. Prior review: `.agent/S5-01-plan-review.md` (RETURN M1, M2). LR-01 citations were checked at `task/LR-01-late-reading-series-and-money-limit` head `bede75ec`, which has moved on from `17dc2f99`, the head used in the first review.

## Verdict: ACCEPT (0 High, 0 Medium, 5 Low carried to build)

## Blocking items

**M1 (resolved).** Packet line 18 now states how the route is composed:
- The existing `evidence_api.py:385-393` handler delegates imported Sites, and no second router is registered on that path.
- `Access` is applied before discovery and returns 401/403. `access_basis` is exposed in the response.
- `ledger_scope` (`sites/cutover.py:107-111`) supplies the tenant and Site IDs.
- If the S2-02 `imported_scope` comparison (`evidence_api.py:229-245`) is absent or failed, the whole imported Overview returns 409 `AWAITING_EVIDENCE_MIGRATION`.
- `performance_gate` (`main.py:329-340`) drives `source_open`, the S3 objective and the Finding and money claims. When the gate is closed, the response carries pinned audit material only.
- A closed Performance gate does not bypass S2.
- Tests are listed for comparison absent, Performance gate closed with the comparison passed, both open, and tenant and access denials.

All cited lines exist on main.

**M2 (resolved).** Packet lines 50-52 now make the walkthrough reproducible:
- **Fixtures** are named, and all of them exist:
  - F01-gateway on 2026-10-02 (`tools/s4_finding_cases.py:18`)
  - the unassessed day 2026-11-10
  - the failed day 2026-10-07 (`tools/s3_dispatch_walkthrough.py:49,68-88`)
  - P01 on 2026-10-23 (`s4-power-demo-cases-v1.json:11`)
  - P02 on 2026-10-24 (`s4-power-late-demo-cases-v1.json:13`)
- **Step commands:** `prepare|serve|attest|tick|stop-schedule|start-schedule|gate --close|gate --open|drop`. Gate handling follows `s402b_fuel_cost_walkthrough.py:282-293`.
- **Owner order:** the exact sequence is given, with the expected state after each step: withheld, then pending (before the tick), then eligible, then the stopped worker, then source closed, then reopened. Throughout, the selected P02 Finding and its history IDs stay the same.
- **Unnamed risk from the first review:** `prepare` must settle P01's full +/-6 h neighbourhood, or the tool stops.

**Architect ruling (reflected exactly).** Packet line 37 matches `D-2026-10-15-s501-finding-choice` (`.ai/DECISIONS.md:4141`) and `.agent/architect-S5-01-answers.md` point by point:
- half-open intersection, with an episode ending at 00:00Z excluded
- latest revision of each canonical Finding, excluding merge-superseded IDs
- no filtering by lifecycle, consequence state, price, amount or eligibility
- the greatest `episode_start` wins, with the smallest UUID as tie-break
- the response returns the rule, the Finding ID and the revision ID
- one Finding only, never a sum
- the pinned Finding is retained through stale and withheld states
- a consistent new basis may change the choice; an incomplete basis keeps the prior pinned choice with no amount
- `ABSENT` only after complete, current discovery

## L1-L8 from the first review

| Item | Status |
| --- | --- |
| L1 | Resolved. All LR-01 citations are rechecked at `bede75ec`. `money_eligibility.py:12-23,39-44,170-186` is exact. `consequence_read.py:214-239` is exact. `upstream.py:140` `source_open=True` and `:155-161` (`head_consequence_revision_id` at `:160`) are exact. See N1 for the one remaining drift. |
| L2 | Resolved. The packet reuses `scheduling/composition.py:45-56` `build_upstream_currentness` (verified on both main and LR-01), and the instance is disposed at shutdown. |
| L3 | Resolved. Line 17 now describes today's 409 and the `AwaitingEvidenceMigration` page (`SiteOverview.tsx:93-95`). |
| L4 | Resolved. The half-open re-filter over `findings_over` (`postgres_finding_store.py:418-431`, closed `lo <= episode_end` at `:425`) is specified, with an exact-midnight test. |
| L5 | Resolved. `UPSTREAM_UNASSESSED` is added to the states and the precedence. Display amounts use the `display` values, and the raw amount is kept for drill-down. `MINOR_UNIT_UNKNOWN` gives no amount. `MIXED_OR_UNKNOWN_SOURCE` is sourced to `demonstration_label.py:60-69`. See N2 for a residual hedge. |
| L6 | Resolved. Line 41 fences the amount to the seam's `head_consequence_revision_id`, and a moved head fails closed. |
| L7 | Resolved. With no date, the default is the DB-clock UTC day, returned in `window.utc_date`. Legacy `date=` is translated to `from`/`to`, and with no selection the legacy `LATEST_RELEASE` default is kept (`evidence/overview.py:589`). |
| L8 | Resolved. All named files exist: the LR-01 tests (on the LR head), the four legacy frontend tests, `npx.cmd tsc --noEmit`, `npm.cmd test`, the new `tools/s5-overview-evidence.mjs`, and `layout-evidence.mjs`, which must be recorded `not run` if it cannot run. |

## Fail-open check

No new path leads to a current amount. An amount still needs all of the following:
- exact-head `CURRENT PRICED` on the same FindingRevision, window and basis
- an open source
- the S2 comparison passed
- upstream `CURRENT`
- the shared `ELIGIBLE` result
- the head-ID fence
- a known minor unit and a resolved demonstration provenance

Every moving or incomplete basis fails to stale or pending.

## Low (non-blocking, carry to build)

- **N1** `upstream.py:149-161,189-200` (line 20) has drifted at `bede75ec`. The ELIGIBLE-to-PENDING downgrade is now at `:186-193`, and the return block is at `:194-202`. The cited content is otherwise correct. Recheck when LR-01 settles.
- **N2** Line 39 says "if no other trusted provenance resolves that case, show no amount". No such provenance exists until Q3 stored authorship lands. Build should treat the unverified label as always giving no amount in S5, and not invent a resolver.
- **N3** "Retain the previous pinned choice" (line 37) needs the server to know which choice was previously pinned. The read contract takes only `date`. Have the UI send the URL-pinned `finding_id`/`finding_revision_id` as optional, scope-validated query parameters, or state that a stateless read with a moving basis returns the Finding pending with no current choice. Either way no amount can appear, so this is identity-only.
- **N4** The `attest` step relies on LR-01's walkthrough extension, which is not built at `bede75ec`. `tools/s402c_late_power_walkthrough.py` there still has only `run|drop` and is identical to main. The SYSTEM path does exist (`backend/assetops_backend/record_clock_attestation.py`). If LR-01's extension ships as a single `run`, the S5 tool should call that SYSTEM CLI directly for `attest`.
- **N5** This residual risk is not named in the packet. P01 (2026-10-23) and P02 (2026-10-24) are adjacent, so P01's upstream bracket reaches 2026-10-24T06:00:
  - The bracket includes the day 10-24 match state (`upstream.py:126-131`).
  - It also includes any consequence work whose affected interval overlaps the bracket (`:162-165`), such as P02's 06:00 reading.
  - Between `attest` and `tick`, P01 can therefore lose its amount as well. This is fail-closed and correct, but the owner might read it as a regression.
  - Either revisit P01 only when P02 is settled, which the current order already does, or say this in the walkthrough notes.

## Checks run

- Every new path and line cited in this round was inspected on main or at the LR-01 head where the packet marks it. The tables above give the results.
- `tools/s5_overview_walkthrough.py` and `tools/s5-overview-evidence.mjs` are absent, as expected for new files.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs` exited 0 with "Registry valid: 224 nodes, 11 linked pilot panels". The fix round did not edit the registry JSON.
- Not run, by instruction: the backend and frontend test suites, `check-architecture.ps1` and `check-agent-workflow.ps1`.
