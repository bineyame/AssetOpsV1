# A-S4-financial review (fresh Claude reviewer)

Target: `plan/A-S4-financial`, diff `9fde68f..d72bfff` (`2157ef7` activation, `7faa206` Architect output, `d72bfff` next-work report). This reviews a planning record only. No implementation was reviewed. I did not author the decision.

## Verdict: ACCEPT (no blocking findings; 2 medium and 7 low carries for the S4-02 Planner; 3 owner-facing notes)

The decision answers every item in the request. It is consistent with the technical design's intent, `A-actor-identity`, the shared-contract scope, the finding-episode decision and the S3-01 `dispatch-3.1` boundary (no fuel or money claim). Nothing moves toward Real. The registry edit is minimal and its anchors resolve. Three things are left for the Planner to settle: how validity closure works, what triggers the SYSTEM publication, and where the model's upper bound comes from. The decision gives the Planner enough to settle all three, and none of them contradicts it.

## Checks run (by me)
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0 ("Registry valid: 212 nodes, 11 linked pilot panels").
- `--next-work --json --out <scratch>/nw.json`: exit 0. Decision `stop_owner`: I-financial-store 2.229 vs A-S5-overview 2.148, gap 3.63%, tie-break recommends A-S5-overview.
- `--verify-report .agent/next-work-2026-10-13j.json`: exit 0.
- The fresh scratch report is byte-identical in content to the committed `-13j` report.
- `-13i` vs `-13j`: only the `registry` fingerprint changed. Queue, packet, panel, manifest and owner_input fingerprints are equal. Changed keys are `decision`, `eligible` and `candidates`. Candidates went from 58 to 57: A-S4-financial dropped out, and I-financial-store replaced it as eligible. Every score delta is a downstream B/P rise from one fewer open gate on the S4-02/S4-04/S5 paths, for example D-financial-basis 2.415 -> 2.429 and A-S5-overview 2.144 -> 2.148. The `missing_kind` change does not affect scoring, because the `gap_catalogue` section is unchanged. All of this is explained by A-S4-financial resolving.
- I did not rerun check-all, vitest or pytest, as the dispatch allowed. The coordinator reported them passing on `7faa206`.

## Item 1: request coverage and consistency
- Coverage: the decision covers assumption identity, versioning and validity, plus `author_id` (answers L7, L9). It covers basis kinds and fuel/maintenance (L8), "bounded" and rounding (L15, L17), consequence lineage and repricing (L16), honest states (L17), persistence and reads (L21), panels (L23), money-comparability and scenario boundaries and cold-chain/EV reuse (L25), the split (L29), the missing-kind rule (L33) and the owner weigh-in (L35). Nothing is missing.
- `A-actor-identity`: the server derives the author and refuses one the client supplies. A human edit is disabled without an authenticated human. A SYSTEM publication carries service/job/fixture provenance and impersonates no one. This matches DECISIONS L3989. Today no human principal exists (`backend/assetops_backend/finding_api.py:38`), so the S4-02 demo must use a SYSTEM publication.
- Shared-contract scope: there is no cross-Site or unlike-currency sum, and scenario is never observed money. `A-money-comparability` stays open. Consistent.
- Finding episode: lineage uses the primary plus supporting assessment revisions, which matches the S4-01 phase-1 clarification (DECISIONS L4065).
- S3-01 boundary: `dispatch-3.1` withholds fuel and money (`analytics/dispatch_v3.py:478`, `finding_read.py:47`). The decision requires a separately reviewed `fuel-cost-1` and forbids importing legacy `dispatch-2` fuel outputs. The input it names exists: the Foundation property `specific-fuel-consumption` is fixed to L/kWh (`sites/models.py:113`).
- Zero lower bound plus "upper only under a defensible model bound": this is coherent. It is deliberately more conservative than legacy dispatch-2, whose lower bound was nonzero (`dispatch.py:730`). Candidate time cannot prove a counterfactual, so 0 is the honest lower limit. It can be tested as two fixtures, bounded and unavailable, and the decision requires both. See M2 for where the upper bound comes from.
- "Whole-window price" and the backdated-correction demo: these can be fixtured. Publish v1 valid over `[t0,∞)`. Assess a Finding whose window falls inside it. Publish a correction v2 whose validity covers the old window. That gives a new consequence revision for the same FindingRevision, and the v1 consequence is still reproducible by pinned ID. A future-dated v3 leaves the old consequence unchanged. M1 is the one ambiguity this exposes.

## Item 2: panel claims
- `financials:1#a`, `financials:2#a`, `assumptions:1#a` and `assumptions:3#a` all exist in `delivery_plan.w1_panel_mapping` as core, open portions with `reviewed_mapping: true`.
- `financials:3#a/#b` and `assumptions:2#a` are non-core and unmapped. The decision leaves them as gaps, which is consistent.
- `mini:4#a` is an S5-01 mapping target. The decision correctly does not claim it for S4-02.
- No `panel_status`, portion state or ledger row changed. Nothing moves toward Real.
- The `financials` and `assumptions` screens are not gap-enrolled (`gap_enrolled_screens` lists only sites, foundation, readiness and sld). The decision's named gaps, such as the maintenance line, cash flow, FX, extrapolation and Scenarios, are not yet catalogue nodes. Those are G-05 territory (see L5).

## Item 3: registry edits
- Exactly two lines changed. Node `A-S4-financial` (registry L37) went from open to resolved, with evidence `../../../.ai/DECISIONS.md#D-2026-10-13-s4-bounded-financial-basis` (anchor present, DECISIONS L4101) and the answers file (present). Its `decision` text was updated and its `requires` and `effort` are unchanged. Node `G-readiness-commissioning` (L340) changed only `missing_kind` from `data_source` to `contract`. Its claim, boundary, status `open`, `source_status` `absent`, `target_wave` `unplanned`, allocation, five `ui_placements` and review trigger are byte-identical.
- `frontend/src/ui/gapCatalogue.ts:20` mirrors only status and placements. It carries no `missing_kind`, so no mirror edit is needed.
- `mock_gaps.cjs:133` forbids only `data_source` together with `existing`. The edit leaves `contract` with `absent`, which is valid.
- The change is justified by the stated rule. Commissioning has no record type, so the first authority that is absent is a contract.

## Item 4: split and owner
- The split is sound. S4-02a covers assumption publication and history plus an honest unpriced/quantity-unavailable bridge. S4-02b covers `fuel-cost-1`, the consequence and repricing. Each part is observable on its own. Promoting the panels only at the final closeout matches the registry: every claimed portion's `technical_requires` includes I-financial-read/ui and I-S4-02, so `assumptions:1#a` cannot be marked delivered after S4-02a alone.
- "No owner decision needed now" is correct under `.ai/ROLE_CONFIG.md` L26-37. Decisions go to the Architect, the owner already chose this node, and the S4-02 owner checkpoint is kept as a USER_REVIEW_REQUIRED acceptance. The decision also correctly reserves a tenant-wide price policy, true maintenance cost, FX and scenario comparison for later owner choices.

## Findings and Planner carries

Medium
- **M1 (carry; ambiguity).** Answers L7 and L10 together with technical design L53 ("Value immutable; recorded closure only", plus a GiST current-valid exclusion) do not say how an ordinary future price change ends an open-ended prior revision. One option is that setting `valid_to` is an allowed recorded closure. The other is that the prior row is superseded and re-appended with a closed window. If supersession is the mechanism, any consequence pinned to v1 for an earlier window would show as superseded or STALE even though its price is still valid for that window. Likewise, a correction covering only part of v1's validity requires re-issuing the uncovered remainder. Why it matters: the honest-state labelling (`STALE/PENDING` vs historical vs current) depends on this choice. Fix for the Planner: define validity closure separately from correction supersession, and base STALE on "the price selected for this window changed", not on "a row was superseded". Fixture both a future price that leaves the old consequence current and a partial-window correction.
- **M2 (carry; testability).** Answers L15 makes the upper bound depend on "the reviewed model's ... configured rate/uncertainty". The Foundation property `specific-fuel-consumption` has no uncertainty field. The only existing uncertainty is the legacy constant `SFC_UNCERTAINTY = 1/10` (`analytics/dispatch.py:49`). Fix: the S4-02b Planner must name the source of the bound before activation. It can be a reviewed `fuel-cost-1` model parameter or a new Foundation field. It also needs to say how the upper power and duration bounds are taken from accepted generator power, for example the maximum accepted mean over candidate segments times the candidate upper duration. Otherwise "defensible" cannot be tested.

Low
- **L1.** Technical design L54 and L165 define the consequence with a single `assessment_revision_id`, an optional single `assumption_revision_id` and a scalar `quantity`. The decision requires link rows for several assessments and assumptions, plus `quantity_low/high` and a basis digest. The decision governs, but the technical design rows have not been amended. The S4-02b Planner should state the migration shape explicitly and note the divergence.
- **L2.** All seven S4-02 registry nodes point to `task: S4-02`, and `I-S4-02.effort` is still `S` (registry L73), which no longer matches two M slices. `I-financial-store` (L219) and `I-assumption-history-read` (L214, "prior assumption **and consequence** revisions") span both slices. The Planner must map nodes to S4-02a and S4-02b, splitting nodes where needed, and update the effort and queue row in `tasks/README.md` L28.
- **L3.** The SYSTEM demo trigger is not specified. Without an authenticated human, a UI button that records SYSTEM for an anonymous user's choice would get around `A-actor-identity`. The Planner should use a server-side CLI, job or fixture trigger with a stable service principal. Any UI edit control shows "unavailable: no authenticated operator".
- **L4.** `G-foundation-financial-assumptions` (registry L337) has the review trigger "A reviewed Site financial-assumptions read and route exist". S4-02a creates exactly that, but the decision does not name it. The Planner should include replacing or re-reviewing that Foundation line and the gap's status change.
- **L5.** The owner rule "missing data stated in UI" applies to the S4-02 surfaces. The second consequence line, the Scenarios subtab, cash flow, FX, extrapolation and the `assumptions:2` impact preview must be named visibly, not silently dropped. Because these screens are not gap-enrolled, the Planner must decide whether S4-02 enrols them (catalogue IDs and placements) or records them for G-05, consistent with the orphan guard.
- **L6.** Answers L15 offers "an expressly conditional point-rate scenario" as an alternative to "unavailable". That wording collides with the `SCENARIO` assumption basis (L8) and with `financial_scenario` (L25), which "cannot overwrite this operational consequence". The S4-02b Planner should either choose "unavailable" or define a label that is distinct from Scenario.
- **L7.** The missing-kind rule (answers L33) is applied only to commissioning. Applied as written, it would also reclassify other current `data_source` entries whose source text says no record type or rule exists. Examples: `G-foundation-obligation-policy` (L336, "no obligation or policy-document record"), `G-readiness-gateway-completeness` (L344, "no reviewed rule"), and arguably uptime, firmware and signal strength, whose "owner_or_role" already names an Architect report contract. The owner-confirmed `D-2026-10-12-mock-gap-closure-mechanism` cites several of these as data-source examples. This changes no scoring, because all are unrankable. G-03..G-05 or the W1-exit allocation should audit the six remaining `data_source` gaps against the rule, so the classification stays consistent.

## Planner carries (S4-02 refinement, consolidated)
1. Validity closure vs correction supersession, and how STALE is defined (M1).
2. The source and formula of the `fuel-cost-1` upper bound, and the accepted-power selection (M2).
3. Migration shape: link tables, `quantity_low/high`, basis digest; note the divergence from the technical design (L1).
4. Node-to-slice mapping, I-S4-02 effort and queue row (L2).
5. The SYSTEM publication trigger and principal; the disabled human edit state (L3).
6. Closing `G-foundation-financial-assumptions` in S4-02a (L4).
7. Visible missing states for omitted mock content, and the enrolment or G-05 hand-off (L5).
8. No "Scenario" wording for the point-rate alternative (L6).
9. Everything the decision already lists at answers L29: valid and recorded time selection, actor failure paths, half-open boundary, Decimal outward rounding, idempotent retries, old/new drill-downs.

## Owner-facing notes (informational; no decision requested)
- The S4-02 Financials amount will read as a range from 0 up to a modelled upper value, or as unpriced or unavailable. It will not match the mock's "KES 198–238", because the lower bound of potentially avoidable fuel is zero by design.
- Until an authenticated operator exists, the mock's interactive price edit will appear unavailable. The repricing demo will be a labelled system publication, not a person editing the price.
- The next-work report again stops for the owner: I-financial-store vs A-S5-overview, gap 3.63%, tie-break recommends A-S5-overview. S4-02 still needs Planner refinement and the split before I-financial-store can be built.

## Not verified
- The frontend suites, backend pytest and check-all were not rerun by me (the coordinator ran them on `7faa206`).
- No implementation exists to verify.
