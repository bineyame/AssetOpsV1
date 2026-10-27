# Build spec, commercial lane (Lane C), 2026-10-27

Architect: Claude (`.ai/ROLE_CONFIG.md` line 9). Owner instruction on depth, verbatim: `.agent/owner-build-plan-depth-2026-10-27.md`. Owner answers: `.agent/owner-answers-open-questions-2-2026-10-27.md` (Q9 yes, Q10 both, Q11 stand-in, Q12 yes, Q13 yes, Q14 yes, Q15 yes, Q16 yes, Q17 yes). Index and calendar: `.agent/build-sequence-2026-10-27.md`.

**Authority order:** this file, then `Docs/demo-sprint/commercial-capability-readiness.html` Appendix C (D1, D2, D5 wire shapes, rulings R1.x, R2.x, R5.x, acceptance criteria, producer cases, mock-deviation texts, migration plan). This file does not repeat Appendix C's wire shapes; it fixes the build order, the module boundaries, the interfaces and the choices Appendix C left open. Where it changes Appendix C, it says **Change to Appendix C**.

---

## 0. Lane rules (every task)

### 0.1 Worktree, branch and environment

- Worktree `C:\Users\assef\Bineyame\AssetOpsV1-cc`, created from `main`. Branches: `task/CC-R1-links-labels`, `task/CC-R2-placement`, `task/CC-M-schema`, `task/CC-D2-reassessment`, `task/CC-D1-contribution`.
- Python: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`.
- **PYTHONPATH (top of the first task file and of every packet):**

  PowerShell:
  ```
  $env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-cc\backend;C:\Users\assef\Bineyame\AssetOpsV1-cc\contracts;C:\Users\assef\Bineyame\AssetOpsV1-cc\simulator;C:\Users\assef\Bineyame\AssetOpsV1-cc\gateway;C:\Users\assef\Bineyame\AssetOpsV1-cc\host;C:\Users\assef\Bineyame\AssetOpsV1-cc"
  ```
  No `field` entry: the backend suite must run without it (`backend/TESTING.md:107`). Verify once per terminal that `assetops_backend.__file__` names the `-cc` worktree.
- Frontend: `cd C:\Users\assef\Bineyame\AssetOpsV1-cc\frontend; npx vitest run <files>`.
- Databases: `assetops_cc_*_test` only, in `assetopsv1-postgres-1`.

### 0.2 What Lane C must not touch

`field/**`, `contract-fixtures/telemetry/**`, `gateway/**`, `contracts/**`, `simulator/**`, `host/**`, `tools/checks/module-roots.ps1`, `tools/checks/dependency-direction.ps1`, the Kobo registered basis and its fixtures, `MINIGRID_ROLES*`, and the source classes in `evidence/source_provenance.py`. No field-source special case in `financials/`, `analytics/` or `evidence/`.

### 0.3 Heavy-job queue

Until 30 Oct 23:59 Lane C runs heavy jobs only when Lane T is not (coordinator holds the queue). From 31 Oct Lane C has priority. Tiers per Appendix C "Validation on a 16 GB machine": tier 0-1 every commit, tier 2 once per slice, tier 3 once per slice after tier 2, tier 4 (full suites) only for CC-M and merges, machine idle.

### 0.4 Cross-cutting decisions (settled here)

**Beneficiary map (owner Q9 = constant per category).** One backend constant, `estate/financials.py:BENEFICIARY_OF_CATEGORY`:

| Category | Beneficiary |
|---|---|
| `CANDIDATE_OPERATING_COST_EXPOSURE` | `MINI_OPERATOR` |
| `PRODUCTIVE_USE_CONTRIBUTION_SCENARIO` (D1) | `MINI_OPERATOR` |
| `POTENTIAL_PRODUCT_EXPOSURE` | `GOODS_OWNER` |
| `RECORDED_REPAIR` | `COOLING_PROVIDER` |
| `GROSS_TARIFF_SCENARIO` | `CHARGING_SERVICE` |

**Change to Appendix C:** the beneficiary enum gains `COOLING_PROVIDER`, because a cold repair cost is borne by the cooling provider, not the goods owner; without it the repair line would be mislabelled. A category missing from the map raises at import time (a test asserts every category in `APPLICABLE` and `COLD_CATEGORY` is mapped).

**Claim labels.** Server-provided `claim_level` and `beneficiary` on every **new** wire shape (D1 `contribution`, D2 `commercial_reassessment`, estate lines). For the two **existing** figures (mini gross scenario, verification verdict) the frontend derives the level from the existing kind/state, so no existing exact-key test changes in R1. **Rejected:** adding `claim_level` to existing reads in R1 (exact-key churn across `test_w403_*` for no user-visible gain).

**Frontend vocabulary.** One map in `frontend/src/sites/actionPresentation.tsx`:
```ts
export const CLAIM_LABEL: Record<ClaimLevel, string> = {
  MODELLED_OPPORTUNITY: "Modelled opportunity · declared assumptions",
  INVENTORY_REQUIRING_REVIEW: "Inventory requiring review · declared value · not a loss",
  EXPECTED_VALUE: "Expected value · declared assumptions",
  VERIFIED_SIMULATED_TECHNICAL: "Technical result verified on simulated data",
  POST_INTERVENTION_MODELLED: "Modelled change after the trial · not realized savings",
};
export const BENEFICIARY_WORDS: Record<Beneficiary, string> = {
  MINI_OPERATOR: "mini-grid operator", GOODS_OWNER: "goods owner", FLEET_OPERATOR: "fleet operator",
  CHARGING_SERVICE: "charging service", COOLING_PROVIDER: "cooling provider",
};
```
and one component `frontend/src/sites/ClaimLabel.tsx`: `ClaimLabel({ level, beneficiary }: { level: ClaimLevel; beneficiary: Beneficiary })` rendering `<p data-claim-level={level} data-beneficiary={beneficiary}>{CLAIM_LABEL[level]} · benefits: {BENEFICIARY_WORDS[beneficiary]}</p>`. Unknown values render "Claim not stated" and never throw. The existing local `CLAIM_LABEL` in `EvSiteViews.tsx:96` is a different vocabulary (evidence claims) and is left alone; the new export is named `CLAIM_LABEL` in `actionPresentation.tsx` as Appendix B says, and EV code keeps its local name (no import collision because EV does not import it).

**Arithmetic.** Exact `Fraction`; divisions stored with `actions/verification_rules.py:fmt` (decimal when terminating, `p/q` otherwise); display rounds once to 4 significant decimals, outward for bounds (Appendix B R-X.2).

**Mock deviations.** Every new panel gets its Appendix C "Mock-deviation notes" entry in `.agent/mock-departure-register.md` in the same commit as the panel.

---

## CC-00 · Pre-flight (no code) · 0.25 d

Builder reads this file and Appendix C D1, D2, D5 and "No double-counting"; batches every question into one request; confirms the producer tools named below exist and how the estate is captured today (Appendix C "Producer risk"). **Gate:** "no open questions" or answers recorded at the end of this file.

---

## CC-R1 · Links, claim labels, beneficiary key, no-double-count check · 1 d · no migration

**Files.**
- Backend: `estate/financials.py` (map, `_partition`, line field `beneficiary`), new `estate/money_invariants.py`.
- Frontend: `sites/actionPresentation.tsx` (two maps), new `sites/ClaimLabel.tsx`, `sites/MiniScenarios.tsx` (label under the gross scenario), `sites/SiteActionVerification.tsx` (label under the verdict), `estate/EstateFinancials.tsx` (beneficiary on each line), `sites/FindingConsequence.tsx` (forward link).
- Tests: extend `backend/tests/test_w303_portfolio_reduction.py`, new `backend/tests/test_cc_money_invariants.py`, frontend tests beside each touched view.

**Approach and interfaces.**
- `_partition(line)` returns the existing six-tuple plus `line["beneficiary"]` as the seventh element. Lines are built with `beneficiary = BENEFICIARY_OF_CATEGORY[category]` at the single place lines are constructed (`estate/financials.py:118-134`), and the field is part of the public line object.
- `estate/money_invariants.py`:
  ```python
  def double_count_violations(portfolio: Mapping[str, Any], financials: Mapping[str, Any]) -> list[str]: ...
  ```
  Pure. Returns one text per violation: a non-null `estate_total` or `combined_value`; a non-null group amount whose members span more than one category, currency, window, period, fingerprint or beneficiary; any two members of one amount with intersecting `technical_interval_ids` or `basis_evidence_ids`. Called by tests and by `tools/cc_estate_seed.py` (CC-R2) before any capture. **Rejected:** calling it in the API at runtime (it duplicates `compare()`, which already enforces the rule at construction, and a failure would become an outage rather than a test failure).
- Forward link: `FindingConsequence.tsx` adds "Open the recommendation" linking to the Finding's recommendation route with the same `revision_id` it was opened with, using the route builder `SiteRecommendation.tsx` already receives (`links.action` at `:78`, and the recommendation route it is mounted on). `SiteRecommendation.tsx` already links the accepted Action (`:174`), so it is not changed. The Action screen already reaches the verification outcome. No backend change.
- Labels: gross scenario → `MODELLED_OPPORTUNITY` + `MINI_OPERATOR`; verdict `VERIFIED`/`INEFFECTIVE` → `VERIFIED_SIMULATED_TECHNICAL` + `MINI_OPERATOR` (shown only for a final verdict).

**Acceptance gates.**
- Pure: two otherwise identical eligible lines that differ only by beneficiary never form `COMPARABLE`; every category is mapped.
- `double_count_violations` returns `[]` on every existing `test_w303_portfolio_*` body and one violation per crafted defect.
- Frontend: the three labels render with `data-claim-level`; the forward link carries `revision_id`; no string under these views says "saving" or "saved".
- Tier 2: `test_w303_portfolio_comparison_postgres.py`, `test_w303_portfolio_fixture_postgres.py`.

**Stop.** Adding `beneficiary` to the line object breaks an exact-key test outside `test_w303_*` (report the test; do not loosen it).

---

## CC-R2 · Portfolio placement (D5) and the combined estate producer · 1.5 d · no migration

**Files.**
- Backend: new `estate/placement.py`; `estate/coverage.py` (carry `mechanism`; for mini also `recurs_after_finding_id`, `revision_no`, `transition` from the snapshot); `estate/portfolio.py` (call `place`, `PORTFOLIO_ORDER` gains `group_rank asc` first, row fields `placement`, `confidence`, `confidence_reasons`, summary `placement_counts`); `estate/scope.py` (`_MARKER_KINDS["portfolio"] = 6`, six-part marker).
- Producer: new `tools/cc_estate_seed.py`.
- Frontend: the estate priority panel (grouped sections, "Placement" column with reason line, confidence text).
- Tests: new `backend/tests/test_cc_placement.py` (pure), extend `test_w303_estate_cursor.py`, `test_w303_portfolio_api.py`, a new Postgres test over the seeded estate.

**Interfaces.**
```python
POLICY_VERSION = "estate-placement/1"
GROUPS = ("NEEDS_INVESTIGATION", "ACT_NOW", "COMPARE_VALUE", "UNPRICED_RISK", "MONITOR")   # rank = index + 1
@dataclass(frozen=True)
class Reason: code: str; text: str
@dataclass(frozen=True)
class Placement:
    group: str; group_rank: int; reasons: tuple[Reason, ...]
    confidence: str            # SUPPORTED_SOURCE_COHERENT | LIMITED | UNKNOWN
    confidence_reasons: tuple[str, ...]
def place(row: Mapping[str, Any], action: Mapping[str, Any] | None, site_cov: Mapping[str, Any]) -> Placement: ...
```
Rules are Appendix C's rank table, first match wins, row facts only (R5.1-R5.8). `site_cov` is used only for confidence text, never to move a row (R5.6). Reason texts are fixed literals per code, listed in the module next to the codes (one dict), so frontend and tests share them through the API.

**Battery-stress stand-in (owner Q11).** MG-C stays the UNCONFIRMED generator-support case, placed `NEEDS_INVESTIGATION` / `LIFECYCLE_UNCONFIRMED`, labelled as such and never as "battery stress". The approximation recommendation is in §"Next sprint".

**Producer `tools/cc_estate_seed.py`.** One tenant `demo`, database `assetops_cc_estate_test`; runs the existing builders in time order (Appendix C "Demo data and producers", D5 row): MG-W402-001, KOBO-001 (D2 verified case when CC-D2 lands; before that the existing s602b verified-trial state), MG-B and MG-C from `tools/s4_finding_cases.py`, COLD-LAB-001, EV-LAB-001, with distinct site codes. It asserts a monotone install clock and stops with `INSTALL_CLOCK_CONFLICT` naming both builders. It ends by calling `double_count_violations` and the D5 placement assertions; any failure exits non-zero before capture. **Fallback (pre-decided):** on `INSTALL_CLOCK_CONFLICT`, D5 acceptance runs on the per-vertical databases and the combined estate becomes a follow-up task; the builder records this and does not try to re-time builders.

**Rejected.** A numeric priority score (Appendix C: no combined score). Placing in the frontend (paging order must be server-side, so the cursor needs `group_rank`). Keeping five-part cursors valid (would need a second order path; cursors are short-lived, refusal uses the existing invalid-cursor path).

**Acceptance gates.** Appendix C D5 criteria: one pure case per rank and reason; MIXED + PRICED lands in NEEDS_INVESTIGATION; six-part marker passes and five-part fails; `limit=2` paging returns every row once in group order; API placements MG-C / MG-B / cold / KOBO-001 as listed; `lens=risks`; no numeric priority; browser group headings and reason lines (`settledScreen` from `frontend/src/test/settled`).

**Stop.** Placement needs a fact not on the row (report it; do not add a query beyond Appendix C's "Row facts"); the selection token would have to include placement.

---

## CC-M · Combined schema slice (owner Q14) · 0.5 d + one full suite · lands before CC-D2

**Files.** `backend/migrations/versions/0036_cc_mini_contribution.py` (down `0035_w5_ev_work`), `0037_cc_trial_cost_comparison.py` (down `0036`), `backend/tests/test_cc_schema_postgres.py`.

**Content (Appendix C "Migration slice plan", D1 and D2 tables).**
- `0036`: drop and recreate `mini_scenario_revision_kind_check` with `'PRODUCTIVE_USE_CONTRIBUTION'` added. Downgrade restores the old check and refuses (raises) if any row uses the new kind.
- `0037`: append-only `trial_cost_comparison_revision` with the columns listed in D2 "Migration 0037", unique `(verification_outcome_id, basis_sha256)`, `revision_no` unique per `verification_outcome_id`, `supersedes_revision_id` self-FK, the `w4_append_only()` trigger, tenant/site FKs as sibling W4 tables. Downgrade drops it.
- Two Alembic revisions in one slice, not one revision: each decision's schema stays separately reversible and traceable. **Rejected:** a single revision with both changes (a D1 slip would leave half a revision unused but unremovable).

**Gates.** `alembic upgrade head` then `downgrade 0035` then `upgrade head` on a fresh `assetops_cc_schema_test`; the trigger refuses UPDATE and DELETE; inserting kind `PRODUCTIVE_USE_CONTRIBUTION` passes after 0036 and fails before; `pg_harness.assert_at_head`; full backend and frontend suites green on an idle machine (tier 4, the only full run this slice pays).

**Slip rule.** If at CC-M start the coordinator has already moved CC-D1 out of the sprint, CC-M carries only the trial table, numbered `0036_cc_trial_cost_comparison`.

**Stop.** Any existing migration needs editing.

---

## CC-D2 · Post-trial commercial reassessment (D2, roadmap R3) · 1.5 d

**Files.**
- Backend: `actions/verification_rules.py` (`window_evidence` returns `generator_kwh`, outside `plan_sha256`), new `financials/trial_fuel_comparison.py`, new `financials/adapters/postgres_trial_comparison_store.py`, the verification service and routes (outcome and history reads; the POST command), action composition wiring.
- Producer: `tools/s602b_test_scoped_cases.py` gains cases `verified` and `price_split` (Appendix C D2 rows) in `assetops_cc_d2_verified_test` and `assetops_cc_d2_price_split_test`.
- Frontend: `sites/SiteActionVerification.tsx` "Commercial reassessment" panel with `ClaimLabel` (`POST_INTERVENTION_MODELLED`, `MINI_OPERATOR`).
- Tests: new `backend/tests/test_cc_trial_fuel_comparison.py` (pure), extend `test_s6_verification_rules.py`, `test_s6_verification_evaluator_postgres.py`, frontend panel test.

**Interfaces.**
```python
FORMULA = "trial-fuel-comparison/1"
REASSESSMENT_STATES = ("MODELLED_IMPROVEMENT", "MODELLED_NO_IMPROVEMENT", "UNAVAILABLE")
REASSESSMENT_REASONS = ("OUTCOME_INCONCLUSIVE", "NOT_COMPARABLE", "SOURCE_NOT_COHERENT", "WINDOW_INCOMPLETE",
    "EVIDENCE_REPLAY_MISMATCH", "GENERATOR_KWH_UNKNOWN", "SFC_MISSING", "SFC_DIFFERS",
    "PRICE_MISSING", "PRICE_BASIS_DIFFERS", "ZERO_DEMAND")
@dataclass(frozen=True)
class WindowFacts:
    evidence_ids: tuple[str, ...]; generator_kwh: Fraction | None; feeder_demand_kwh: Fraction | None
    start: datetime; end: datetime
@dataclass(frozen=True)
class InterventionCost: amount: Fraction; currency: str; source: str
def compare(baseline: WindowFacts, later: WindowFacts, outcome: Mapping[str, Any],
            sfc_in_force: Sequence[SfcValue], price_selections: tuple[Mapping[str, Any], Mapping[str, Any]],
            intervention_cost: InterventionCost) -> dict[str, Any]: ...   # returns the Appendix C wire body minus ids/recorded_at
class TrialComparisonStore(Protocol):
    def latest(self, tenant_id: UUID, site_id: UUID, outcome_id: UUID) -> dict[str, Any] | None: ...
    def history(self, tenant_id: UUID, site_id: UUID, outcome_id: UUID) -> list[dict[str, Any]]: ...
    def append(self, row: Mapping[str, Any]) -> dict[str, Any]: ...      # idempotent on (outcome, basis_sha256)
```
Gate order is Appendix C Figure C.2: outcome final → comparable and coherent → replay matches → SFC value and price revision equal → compute. `basis_sha256` = SHA-256 of canonical JSON over `{outcome_id, evidence_ids, generator_kwh, feeder_demand_kwh, sfc value, price revision_id, intervention_cost, formula}`.

**Approach.** Window replay re-runs `VerificationService._windows(plan, known_at=outcome.recorded_at)` and compares evidence-ID sets with the stored outcome basis (R2.6); no new loader. Hook (a) runs after `record_evaluation` commits, in its own transaction, catching every exception into `commercial_reassessment: null` + `REASSESSMENT_PENDING` on the response; hook (b) is the POST command under the existing VERIFY grant (R2.9). Price republish is detected on read (`current_price_basis: "CHANGED"`), resolved only by (b). No worker.

**Rejected.** Recomputing on every read (non-reproducible once prices change; the revision is the audit record). A worker (no queue exists for verification and none is needed for an explicit command). Comparing SFC by revision ID (APPLY re-issues IDs; R2.7). Annualizing (Appendix C: never).

**Acceptance gates.** Appendix C D2 criteria: `compare()` gives `change_per_demand_kwh.nominal == "16/375"`; each reason has one isolating test; the route walk on `verified`; `price_split` → `PRICE_BASIS_DIFFERS`; inconclusive → `OUTCOME_INCONCLUSIVE`; `target_miss` never UNAVAILABLE; a second command after a new price publication appends `revision_no == 2` with 1 still readable; the wording test ("saving", "saved", "realized" only inside "not realized savings"); label "per kWh of feeder demand" (owner Q12).

**Stop.** `plan_sha256` would change; replay cannot reproduce a stored outcome's evidence set on the existing s602b cases (report the case; do not relax the check).

---

## CC-D1 · Productive-use contribution (D1, roadmap R4) · 1.5 d · slips first

**Files.**
- Backend: `mini_decisions/scenario_rules.py` (`_physical_gate`, `contribution`), the scenario write/read and opportunity read modules, `estate/financials.py` (category, `APPLICABLE[MINI_GRID]`, `assumption_fingerprint_v2`, line fill).
- Producer: the w403 producer (`tools/w403_mini_decisions_walkthrough.py` case path) gains `cc-d1-contribution-r1` and the three negatives in `assetops_cc_d1_contribution_test`.
- Frontend: the opportunity view and `MiniScenarios.tsx` contribution panel (four stat tiles, inputs table, `ClaimLabel` `EXPECTED_VALUE` + `MINI_OPERATOR`), the Portfolio PRODUCTIVE_USE card state.
- Tests: extend `test_w403_scenario_rules.py` (unchanged cases must pass unedited), `test_w403_scenarios_postgres.py` (`ROW_KEYS`), `test_w403_opportunity_read_postgres.py` (`OBJECT_KEYS`), estate financials tests.

**Interfaces.**
```python
def _physical_gate(items: Sequence[Mapping[str, Any]], days: Sequence[DayRow]) -> dict[str, Any] | None: ...
def contribution(items: Sequence[Mapping[str, Any]], days: Iterable[DayRow]) -> dict[str, Any]: ...
PAYBACK_REASONS = ("NO_ENABLEMENT_COST", "NO_POSITIVE_CONTRIBUTION")
def assumption_fingerprint_v2(category: str, currency: str, rates: Mapping[str, str]) -> str: ...  # payload "estate-money-assumption/2"
```
Rules R1.1-R1.7 as Appendix C. `calculate()` keeps its kind gate and calls `_physical_gate`; its output for every existing case is byte-identical.

**Rejected.** Optional keys on `PRODUCTIVE_LOAD` (the Implementer's alternative; it changes the stored meaning of existing revisions, R1.5). A stored hurdle rate (R1.3). Summing contribution with operating cost (R1.4).

**Acceptance gates.** Appendix C D1 criteria (1.7, 3/25, 71; collection 0.1 gives −0.05 with `NO_POSITIVE_CONTRIBUTION`; Postgres eligible_days × 1.7 with `DECLARED`; headroom-below-load and MIXED give a null amount with reason; estate one SINGLE_LINE line, never OPERATING, `estate_total` null; browser copy), plus `double_count_violations == []` on the seeded estate.

**Stop.** Any existing `calculate()` case changes output.

---

## Next sprint (not briefed for build): battery-stress approximation (owner Q11)

**Recommendation.** One SoC-only cue, `battery-soc-stress/1`, next sprint, first item. It is not cheap enough for this sprint: Lane C is full after the owner chose both D2 and D1, and the cue needs a declared analytic, a read path into placement, seed data on MG-C and a reason line (about 1 day plus tier 2-3 validation).

- Inputs: accepted `battery_soc` evidence and the Foundation `battery_reserve` control only. Both exist for every mini Site.
- Per Site-local day: daily depth of discharge = max SoC − min SoC (points); hours at or below reserve + 10 points (the dispatch headroom, `dispatch_v3.py` `SOC_HEADROOM_POINTS`).
- Cue raised when, over the last 7 complete days with full SoC coverage, depth of discharge ≥ 70 points on at least 3 days, or near-reserve time ≥ 2 h on at least 3 days. Thresholds are declared assumptions in the policy version, shown with the cue.
- Label: "Battery stress cue (approximation from state of charge) · not a health, degradation or cycle-life estimate". Placement reason `BATTERY_STRESS_CUE` in NEEDS_INVESTIGATION; it replaces MG-C's stand-in only when MG-C's seeded SoC raises it.
- **Rejected:** equivalent full cycles from `battery_power` (needs a declared usable capacity no Site has, and `battery_power` is AC converter power, D5); any degradation model (horizon 3).

---

## Implementer questions and resolutions

_Empty. The Implementer review of this spec posts its questions here as `Q-C<n>`; the Architect answers each in place, with the date and the section it amends._
