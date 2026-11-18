# S5-01 plan review (fresh independent Claude reviewer, 2026-10-15)

Subject: `tasks/S5-01-site-overview.md` at `ce0a3f0b` on `plan/autonomy-2026-10-15` (Planner packet, no code). LR-01 read at `task/LR-01-late-reading-series-and-money-limit` head `17dc2f99` (unmerged, still building). The Architect's Finding-choice ruling was assumed to follow the Planner's recommendation, which is sound: the choice ignores price and keeps the same Finding through stale and withheld states.

## Verdict: RETURN (2 Medium, 8 Low)

The core contract is right. A current amount requires all of these together: exact-head `CURRENT PRICED`, an open source, upstream `CURRENT` and LR-01 `ELIGIBLE`. The no-amount precedence starts with the source gate. The Finding list is unavailable rather than empty, the unsupported mock panels are excluded by name, the slice is M with two phases and one full suite, and the merge waits for the owner. Two gaps need a short Planner fix before build. Neither needs an Architect ruling.

## Medium

**M1 - The gate and scope seam at the reused route is unspecified.** In the packet, "Verified seam" and the read contract say only "tenant/Site-scoped S5 read at this route".
- What the code does: the route `GET /api/sites/{site_id}/overview` (`backend/assetops_backend/evidence_api.py:160,385-393`) lives in the evidence router. That router has only the S2-02 evidence-cutover scope `imported_scope` (`:229-245`, which returns 409 `AWAITING_EVIDENCE_MIGRATION` until `latest_comparison` passes). Its docstring says "Overview stays on the legacy gate" (`:197-199`).
- What the packet asks for: the S3 Performance source gate (`performance_gate`, `backend/assetops_backend/main.py:329-340`), the Finding access hook (`Access`/`access_basis`, `backend/assetops_backend/finding_api.py:36-40,63-77`) and `registry.ledger_scope`. None of these is wired into the evidence router.
- What is missing: the packet does not say whether the S5 read must also pass the S2-02 evidence cutover before it shows accepted-measurement context and evidence links. It also does not say which access hook and `access_basis` apply, or how the route is composed. Registering a second router on the same path is shadowed by the evidence router, which is included first.
- Why it matters: an implementation that uses `ledger_scope` plus `performance_gate` alone would serve ledger evidence on the Overview while the Evidence page for the same Site still says awaiting migration. That bypasses the S2-02 cutover rule. It is a fail-closed ambiguity in exactly the gate this slice must get right.
- Fix: state the gates for each section. Scope and access should reuse `finding_api`'s `Scope`/`Access`/`access_basis`. The evidence cutover gates context and evidence links: either 409 or a typed unavailable section. `performance_gate` drives `freshness.source_open` and the money/Finding claims. Say how the evidence router delegates imported Sites to the S5 service. Add focused tests for "evidence comparison absent", "performance gate closed" and "both open".

**M2 - Fixtures and walkthrough transitions are not named, so the owner walkthrough is not yet reproducible.**
- What is required: `.agent/architect-A-S5-overview-answers.md:11` requires the Planner to specify "fixtures for assessed/Unknown/late-power/failed/unpriced/priced cases". The work order requires a reproducible owner walkthrough.
- What the packet gives: phase 1 lists cases but names no fixture source. The walkthrough defines only `prepare|serve|drop` on one retained DB. It still expects the owner to see:
  - late withheld, then pending, then eligible. This needs the LR-01 SYSTEM attestation step and a tick between serves.
  - a stopped worker
  - a closed source, then an open one. This needs a gate toggle.
- Fix: name the seed sources:
  - P01 authored power: `backend/conversions/s4-power-demo-cases-v1.json`, `tools/s402b_power_cases.py`
  - late power: `backend/conversions/s4-power-late-demo-cases-v1.json`, the LR-01 extension of `tools/s402c_late_power_walkthrough.py`
  - the ordinary 0/11 day and the failed/unassessed day
- Also add explicit step subcommands such as `attest`, `tick`, `stop-schedule` and `gate --close/--open`. `tools/s402b_fuel_cost_walkthrough.py:282` `gate(work, close)` is the existing pattern. Alternatively, use separate Sites or days per state. In either case, give the exact command order the owner runs and the expected API IDs or states after each step.

## Low (carry to build; non-blocking)

- **L1** LR-01 citations have drifted. In `money_eligibility.py`, the states are at `:39-44` (docstring precedence `:12-23`) and `MoneyEligibility.for_finding` at `:170-186`, not `:22-35,113-179`. The `consequence_read.py:214-239` and LR `upstream.py:149-161,189-200` citations are correct. Recheck all of them at the reviewed LR-01 head.
- **L2** The seam factory already exists: `backend/assetops_backend/scheduling/composition.py:45-56` `build_upstream_currentness`, docstring "The S5-01 selected-window upstream seam". Reuse it for the one-per-process instance rather than writing a new composition, and dispose it in app shutdown.
- **L3** The packet does not describe the current Overview honestly for imported Sites. `site_or_404` raises `SiteAwaitingMigration` (`sites/cutover.py:114-119`), so imported Sites receive 409 today and the UI shows `AwaitingEvidenceMigration` (`SiteOverview.tsx:93-95`). The file-backed model serves only legacy Sites.
- **L4** Selecting the Finding by day has a boundary gap. `findings_over` (`analytics/adapters/postgres_finding_store.py:418-431`) returns latest revisions overlapping the +/-6 h bracket, with a closed `lo <= episode_end` test. Specify a half-open day intersection, `episode_start < day_end and day_start < episode_end`, so that an episode ending exactly at 00:00Z is not selected.
- **L5** The money-state vocabulary has three gaps:
  - An upstream `UNASSESSED` status has no money state in the precedence.
  - `MIXED_OR_UNKNOWN_SOURCE` has no producer in the code. Define its trigger, for example `demonstration_case` returning the unverified label, or mark it reserved until `I-stored-demo-provenance` lands.
  - The packet does not say whether `amount_low/high` take the unrounded `amount` or the minor-unit `display`. `MINOR_UNIT_UNKNOWN` must give no amount.
- **L6** The fence should require that the consequence revision the amount is read from equals the seam's `head_consequence_revision_id` for the selected FindingRevision. A second consequence read must not pick up a newer head.
- **L7** Two date behaviours are unspecified. With no `date` parameter, the default could be 422, the latest assessed day or the DB-today day. The `date=` handling for legacy Sites is also undefined.
- **L8** The test list is incomplete:
  - Name the LR-01 tests: `backend/tests/test_lr01_cohort_v4.py` and `test_lr01_money_eligibility_postgres.py`.
  - Name the existing Overview UI tests to keep green on the legacy branch: `frontend/src/shell/__tests__/siteOverviewScreen.test.tsx`, `overviewDispatchAssessment.test.tsx`, `t028Screens.test.tsx` and `t028Vocabulary.test.tsx`.
  - Name the frontend commands: `npx.cmd tsc --noEmit` and `npm.cmd test`.
  - Name the new browser-evidence script and the `tools/layout-evidence.mjs` run. This is a layout-sensitive slice, so a run that cannot happen is recorded as `not run` with its unmet precondition.

## Checks

| Check | Result |
| --- | --- |
| Code reality on main | Verified: `evidence_api.py:385-393`; `overview.py:575-640`; `siteOverviewClient.ts:138-164,197-263`; `SiteOverview.tsx:66-198`; `upstream.py:75-82,87-202` and `source_open=True` at `:136` (packet: `:140`; it is `:140` on LR-01); `finding_api.py:79-85,112-128,246-277,275,284,306`; `performance_api.py:88`; `financial_read_api.py:88`; `evidence_api.py:158`; `demonstration_label.py:60-76`; the three S4 test files; `TESTING.md` sections and the 20-minute `-n 2` cap; registry `:308-311` = `mini:1..4`; manifest `:105-124` = `mini`. `SiteWindowSummary` / `site_window_projection` have no runtime code, which matches the packet. `tools/s5_overview_walkthrough.py` is absent, as expected for a new file. |
| Decisions and carries | Covered: `D-2026-10-14-s5-selected-window-overview`, `-s402c-late-sequence-and-s5-money`, `D-2026-10-15-lr01-source-time-cohort`; P1-P9; S4-02c F1/R1; S4-02d seam carries (`S3_UNASSESSED` gap, `source_open`, F1 rule, one instance per process, stopped worker). The A-S5 L3 registry carry is already satisfied: `mini:1-4` include `I-evidence-acceptance-consequence-work`. Q2 and S4-02d nodes are resolved; LR-01 is open. |
| `node frontend/docs/architecture/check_v69_dependency_registry.cjs` | exit 0, "Registry valid: 224 nodes" |
| `--next-work` | `ranked`, no refusals. `I-S5-01` 2.22 is blocked on LR-01 and the S5 read/UI nodes. |
| Packet Status `implementation-ready (...)` | `packetPhase` = `not_started` (accepted). `USER_REVIEW_REQUIRED: true` parses true. |

Not run, by instruction: backend and frontend test suites, `check-architecture.ps1`, `check-agent-workflow.ps1`.

Residual risk not named in the packet: upstream `CURRENT` covers every Finding, consequence and piece of work in the +/-6 h bracket, so a stale neighbour withholds the selected Finding's amount. That is fail-closed and acceptable. The walkthrough must still show the P01 day with a settled bracket, or the owner will see no amount.
