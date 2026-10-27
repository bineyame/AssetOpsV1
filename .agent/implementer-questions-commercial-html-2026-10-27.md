# Implementer review of commercial-capability-readiness.html (2026-10-27)

Read-only, worktree AssetOpsV1-demo-plan at c975d618. Re-ran test_w403_scenario_rules, test_s6_verification_rules, test_s4_fuel_cost, test_w303_portfolio_reduction: 152 passed. All referenced files exist; D1–D4 worked-example arithmetic checks. Main problems: D2 comparison keys, D3 Foundation read, D5 lens/recurrence/paging assumptions. Paths are under `backend/assetops_backend/` unless noted.

## 1. Answers to Q1–Q12
- **Q1 (settled):** no frontend schema bump needed — `frontend/src/sites/miniDecisionsClient.ts:isScenarioList` (l.295) / `isOpportunityDetail` (l.309) check a few keys then cast. Backend tests assert exact key sets and must change: `tests/test_w403_scenarios_postgres.py` l.199 `set(row) == ROW_KEYS` (l.45-47); `tests/test_w403_opportunity_read_postgres.py` l.497, 534, 542.
- **Q2 (settled, not persisted but recomputable):** `actions/verification_rules.py:window_evidence` builds per-slot `generator_power.kwh` (l.439-441) but never totals it (only `known` updated, l.442-444). `actions/verification.py:_assess` (l.614-637) persists only per-window evidence-ID unions plus a `details` subset (feeder, PV, unserved, below-reserve, SoC) — no slot payload, no generator kWh. `VerificationService._windows(..., known_at)` (l.502-529) filters `decided_at <= known_at`; `accepted_evidence` is append-only (0005 trigger, l.314), so re-running at the outcome's `recorded_at` reproduces slots. No load-by-ID helper exists. Simplest: add `generator_kwh` to `details` at evaluate time going forward.
- **Q3 (settled):** `actions/service.py:apply` → `sites/foundation_service.py:publish_battery_reserve` writes a whole new Foundation revision. SFC lives in Foundation content; `SfcValue.property_revision_id` is the Foundation revision ID (`mini_depth/inputs.py` l.226, 270). So `SFC_DIFFERS` must compare value + validity coverage, not IDs. SFC selection is `mini_depth/rules.py:_sfc_for` (l.636), not `fuel_cost.py`.
- **Q4 (mechanics settled; policy is a ruling):** `financials/fuel_cost.py:select_window_price` (l.440-463) needs exactly one assignment in `[valid_from, valid_to)` wholly containing the window. One open-ended assignment covers both days with the same `revision_id`. Compare `revision_id`; assignment IDs are re-issued on republish (l.428-430).
- **Q5 (settled: no):** `analytics/ev_availability.py:selected_foundation` (l.56-69) returns the raw revision dict; ratings are in `content.components[].properties` (`ev-site-import-limit`, `ev-charger-max-power`, `ev-connector-max-power`, `connector_enable_schedules`). No base-load field: `host/ev_publication.py:ev_parameters` (l.277-341) forces `base_load_kw=0` and refuses a base-load property. Nothing reads an arbitrary pinned Foundation revision; `analytics/adapters/postgres_assessment_store.py:foundation_revision_on` (l.3035-3053) is snapshot/cutoff-driven. A new read is needed.
- **Q6 (settled):** sessions carry `connector_asset_id` (0025 l.82-105; returned by `postgres_assessment_store.py:_sessions`), not asset_code. Session bounds are START and END/ABORT, not plug-in/unplug. Faults are point FAULT/CLEAR events; per-connector UNAVAILABLE spans exist only at read time (`ev_availability.py:_observations/_classify`, l.105-157).
- **Q7 (settled: rebuildable with work):** `cold_episode_evidence` stores `(evidence_id, use, reason)` sorted by ID text. Policy (low, high, hysteresis, min) is in `assessment_revision.result`. `analytics/adapters/postgres_finding_store.py:revision_evidence` (l.340-403) returns SUPPORT points with `source_time`, quality, value, time-ordered. Rebuild must re-apply the >10-min skip (`analytics/cold.py` l.446-452). No route exposes the curve.
- **Q8 (settled: none):** `postgres_finding_store.py:_insert_cold_finding` and `ev_apply` (l.732-737) always write `recurs_after_finding_id = NULL`; cold/EV returns transition SUPPORT_CHANGED or BASIS_REFRESHED, never REOPENED. Only `analytics/finding_episode.py` has REOPENED (l.785) and `_recurrence` (l.622-662).
- **Q9:** chain is Alembic `down_revision` (`0029_w4_mini_depth.py:41` documents the 0028 skip); 0036 is next; no numbering guard in `tools/checks/`. Whether one combined migration slice is acceptable is a reviewer/Architect call.
- **Q10 (partly):** no producer does a combined estate. Each producer creates its own DBs (w403, s602b one-per-case, w502, w504, w601). `tools/w601_seed.py` seeds KOBO-001/KOBO-002 in tenant `demo` and KOBO-001 in `w601-other` — mini only. Schema allows mixed site types per tenant; a new orchestrator is needed. Install-clock conflicts unchecked.
- **Q11 (settled, against the proposal):** paging is in memory (`estate/portfolio.py:_portfolio`, l.500-505); the cursor is a signed 5-part per-row marker (`estate/index.py:_cursor` l.228; `estate/scope.py:resume_after` l.367, `_MARKER_KINDS` l.61). Cross-page grouping changes order, so the marker needs the group (new arity) or grouping must be within-page; a changed marker/order invalidates cursors (422). The selection token need not include placement.
- **Q12 (settled: migration):** closed key set `financials/assumptions.py` `ASSUMPTION_KEYS` (l.30), `UNITS`, `validate`; DB CHECKs follow `0026_w2_ev_money.py:38-46` drop/re-add. Also `financials/assumption_read.py:121`, `frontend/src/sites/financialsClient.ts`, `frontend/src/estate/estateEvidenceWords.ts`. Assumptions are site-scoped time-ranged price assignments; "per rule" has no representation.

## 2. Open questions
**D1 mini productive-use**
- `calculate()` returns NO_CALCULATION unless kind is `PRODUCTIVE_LOAD`: new kind (refactor gate) or optional keys on `PRODUCTIVE_LOAD`?
- Division is inexact (payback ceil(120/2.55); break-even with tariffs like 0.07); the rule traps `Inexact` → 422. Rounding rule for break-even and payback? What does payback show when unit contribution ≤ 0?
- Estate line: what goes in `technical_interval_ids` / `basis_evidence_ids` (`_overlaps` marks lines without them BASIS_NOT_PROVEN)? Which `window_start/end`, given `_partition` keys on window so different study windows never compare?
- `PRODUCTIVE_LOAD` tariff is optional (ENERGY_ONLY): required for contribution?

**D2 generator trial reassessment**
- R2.1 denominator is feeder demand, not served kWh (no all-load served total, `window_evidence` l.523). Is "cost per kWh of demand" acceptable, or is a served total needed?
- Hook point: evaluation is a synchronous POST (`action_api.py:275` → `postgres_action_store.py:record_evaluation` l.759), no worker. Same transaction, or after `evaluate` returns SETTLED?
- How is "price republish appends a revision" triggered?
- Which route carries `commercial_reassessment`: `.../verification/outcome` or `.../history`?
- How is intervention cost published, given Q12 (new assumption key = migration; Action field = schema change)?
- Accept baseline readings citing the pre-split Foundation revision (`verification.py` l.173-176)?

**D3 EV bus decision**
- Base load: declared in decision assumptions, or fixed 0 to match the simulator?
- Foundation enable schedule is Tuesday-only 08:00-16:00 (`tests/fixtures/w2/ev-lab-001.yaml` l.153-166): must the allocator honour weekday?
- How does a declared vehicle `connector` map to `connector_asset_id` (asset_code not returned)?
- R3.2 gate: UNAVAILABLE spans or FAULT/CLEAR points?
- `ev_scenarios/service.py:_authorable` (l.76-84) refuses without a CURRENT energy-complete selection and refuses a currency different from the priced tariff: inherited by the new kind? A depot tariff (R3.3) may differ in currency.
- `preferred`: target's cost only, or total energy cost across vehicles?
- Option C: when/where does the external top-up happen relative to departure?

**D4 cold inventory review**
- `ColdPolicy` is one COLD_ROOM and one probe per site (`postgres_assessment_store.py` l.1213-1257): no "room R2". NOT_IN_ROOM = "declared room ≠ site room asset", or drop it?
- `handle_at` inside a step: truncate with the same min/max rectangle bound, or snap to the previous reading?
- Date lots `placed_at/removed_at` against `start_earliest` or `start_latest`?

**D5 Portfolio triage**
- Opportunity lens works over Finding rows only (`estate/index.py:select_finding_scope`); D1 opportunities are not Findings and have no Finding link. New row type, or panel-only?
- Cold/EV rows are always `_consequence("UNPRICED")` (`estate/coverage.py` l.264): precedence rule 4 puts every EV row in UNPRICED_RISK. Exclude EV from the risk group?
- Coverage is per site (copied into rows as `status`): should one PARTIAL site send all its rows to NEEDS_INVESTIGATION?
- Paging (Q11): within-page grouping or a new marker?

**Cross-cutting**
- `claim_level` has no value for D4's declared inventory; the ladder maps it to "Modelled opportunity", conflicting with "not a loss". Add `INVENTORY_REQUIRING_REVIEW`?
- Adding a category to `APPLICABLE` also creates a `NO_LINES` sentinel per site, and categories are documented as the mock enum (`estate/financials.py` l.43-46). Intended?
- One combined estate seed, or one per decision?

## 3. Corrections
- **D3 Foundation/base load:** limits do not come from `ev_availability.selected_foundation` as usable fields and base load does not exist (Q5). Build a pinned-revision read; declare or drop base load.
- **D2 window total:** "compute from frozen evidence IDs" needs a load-by-ID helper that does not exist; alternatively re-run `_windows` at `known_at = outcome recorded_at`.
- **D2 SFC:** ID equality would always fire (apply creates a new Foundation revision, Q3). Compare values.
- **D2 producer:** SFC already exists (`config/site-templates/kobo-mini-grid-60kw.yaml:136-139`, 0.3 L/kWh). s602b publishes no diesel price; one exists in `backend/conversions/demo-diesel-price-publications.json` (used by `tools/s402a_assumptions_walkthrough.py`).
- **D2 API:** no `GET /api/sites/{code}/actions/{id}/verification`; routes are `.../verification/plan|outcome|history|evidence` (`action_api.py` l.245-305).
- **D2 persistence:** there is no evaluator job; SETTLED is an `_assess`/`evaluate` response state (`verification.py:42`), not an outcome.
- **D1 "reuses calculate() gates unchanged":** impossible for a new kind (kind gate `scenario_rules.py:199`); payback/break-even break the exact-or-422 rule (l.217-225).
- **D1/D5 lenses:** "OPPORTUNITY for rows linked to D1 opportunities" cannot work — Portfolio rows are Findings and there is no opportunity→Finding link; OpportunityPanel and the lens need a new data path.
- **D5 "rows carry the mechanism":** false — `mechanism` is always None (`estate/coverage.py` l.153, 263).
- **D5 MG-C battery stress:** no battery-stress Finding exists in the backend; precedence row 4 example and the MG-C producer have no source.
- **D5 cold/EV recurrence:** no stored facts (Q8); cold/EV can never reach ACT_NOW by recurrence.
- **D5 mini recurrence:** no coverage change beyond the row builder — `postgres_finding_store.py:_index_snapshot` already selects `recurs_after_finding_id`, `revision_no`, `transition`; `coverage.py` l.150-155 drops them.
- **D5 R5.3 paging:** "order within each group stays existing" is insufficient; cross-page grouping breaks the cursor (Q11).
- **D4 "room R2":** unrepresentable (one room per site).
- **D4 curve:** episode evidence links are ID-sorted without time/quality; rebuild via `revision_evidence` plus stored policy.
- **D3 "plugs in at 10:00":** no plug-in time in the backend; session bounds are START and END/ABORT.
- **Fixtures:** `w601_seed.py` seeds mini sites only.
- **Minor:** `_sfc_for` is in `mini_depth/rules.py`; the "predicts no saving" text is `actions/service.py:344`; the same-clock-hour rule is enforced at freeze (`verification.py` l.148-150), not in comparability.

## 4. Usability gaps
- No exact JSON wire shapes for `contribution`, `commercial_reassessment`, D3 `calculation.options[]`, D4 calculation, D5 `placement`/`confidence`; no reason-code enums per object.
- Estate line field fill for D1 and D4 (`line_key`, `overlap_group`, `technical_interval_ids`, `basis_evidence_ids`, window, `period_kind`, fingerprint inputs, eligibility mapping) — otherwise every line falls to BASIS_NOT_PROVEN or never compares.
- Producer specifics: fixed IDs, dates, numbers, expected outputs per negative control; which DB/tenant per case; the D5 one-estate orchestrator is unscoped; installer clock conflicts unchecked.
- Name the test seams: by-ID evidence loader (D2), pinned-Foundation read (D3), cold SUPPORT-curve read (D4), backend exact-key constants (Q1), Portfolio cursor marker tests (`scope.py:_marker_ok`), frontend `settledScreen`.
- Migration slice: 0036-0039 plus a likely assumption-key migration (Q12) = five schema changes; say whether one slice and its full-suite cost.
- Acceptance criteria not executable as written: D2 "no step needs URL editing" needs a named route sequence; D4 "every lot state appears" must fit the one-room model; D5 "Opportunity and Risk lenses return rows" has no defined data source.
- Copy: no final screen strings beyond labels; no mock-deviation layout sketch for the new panels (owner's mockup rule requires labelled deviations).
