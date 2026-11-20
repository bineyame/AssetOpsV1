## CC-00 · Pre-flight (no code) · 0.25 d

Builder reads this file and Appendix C D1, D2, D5 and "No double-counting"; records in the C2 packet the two fixture facts this spec pins from code (the W3-03 fixture's cold row `episode_end` and EV row placement, CC-R2) and the w403 study's minimum ELIGIBLE lower headroom (CC-D1). **Gate:** "no open questions" (revision 2 answers all 51).

---

## CC-R1 · Links, claim labels, beneficiary key, no-double-count check · 1 d · no migration

**Files.**
- Backend: `estate/financials.py` (map, `_beneficiary`, `_partition`, `compare` unpack, `_line` field), `estate/evidence_money.py` (`group_key_for_partition` keyword), new `estate/money_invariants.py`.
- Frontend: `sites/actionPresentation.tsx` (types and maps), new `sites/ClaimLabel.tsx`, `sites/MiniScenarios.tsx` (label under the gross scenario), `sites/SiteActionVerification.tsx` (label under the verdict), `estate/EstateFinancials.tsx` (beneficiary line), `sites/FindingConsequence.tsx` (`BridgeLinks.recommendation` and the forward link), `shell/SiteAnalyticsFrames.tsx` (wire `recommendation` into the mini `FinancialsLinks` at ~`:1377`).
- Tests: extend `backend/tests/test_w303_portfolio_reduction.py`, new `backend/tests/test_cc_money_invariants.py`, frontend tests beside each touched view.

**Approach and interfaces.**
- `_line(...)` sets `"beneficiary": BENEFICIARY_OF_CATEGORY[category]` (public field, after `"category"`). Partition per §0.4.
- `estate/money_invariants.py`:
  ```python
  def double_count_violations(portfolio: Mapping[str, Any], financials: Mapping[str, Any] | None = None) -> list[str]: ...
  ```
  Pure, over parsed HTTP JSON bodies (the service dicts have the same public shape). Checks, one text per violation:
  1. `portfolio["money"]["estate_total"]`, `portfolio["summary"]["combined_value"]` and, when given, `financials["summary"]["estate_total"]` are null.
  2. Member set = `portfolio["selected_lines"]` (the full, unpaged set), keyed by `line_key`. For every group in `portfolio["money"]["groups"]` and `financials["groups"]` with a non-null `amount`: every `line_keys` entry is in the member set (else `MEMBER_NOT_FOUND`); the members agree on `category`, currency (`(line["amount"] or line["disclosure"]["pinned_amount"] or {}).get("currency")`), `window_start`, `window_end`, `period_kind`, `assumption_fingerprint` and `beneficiary`; and no two members intersect on `technical_interval_ids` or `basis_evidence_ids`.
  The paged `financials["rows"]` are never used as the member set. Called by tests and by the s602b `estate` case (CC-R2). **Rejected:** calling it in the API at runtime.
- Forward link: `BridgeLinks` gains optional `recommendation?: (findingId: string, revisionId: string) => string`. `SiteAnalyticsFrames.tsx` wires it for the mini-grid Financials frame as `(findingId, rev) => siteFindingViewHref(site.site_id, findingId, "recommendation", rev)`. `FindingConsequence.tsx` renders "Open the recommendation →" only when the prop is present, with the same `revision_id` the view was opened with. Cold and EV frames do not pass it (their recommendation routes stay in their domain frames), so no link shows there. `SiteRecommendation.tsx` is not changed (it already links the accepted Action, `:174`).
- Labels: gross scenario → `MODELLED_OPPORTUNITY` + `MINI_OPERATOR`; verdict → `VERIFIED_SIMULATED_TECHNICAL` + `MINI_OPERATOR`, shown when the displayed outcome's `outcome` is `VERIFIED` or `INEFFECTIVE` (an INEFFECTIVE verdict is still a verified technical result; Appendix B copy is final). Not shown for INCONCLUSIVE, pending or no outcome.
- Estate beneficiary: in `EstateFinancials.tsx`, a second line inside the existing category cell, `<span className="line-beneficiary" data-beneficiary={b}>Benefits: {BENEFICIARY_WORDS[b]}</span>`. No new column.

**Acceptance gates.**
- Pure: two otherwise identical eligible lines that differ only by beneficiary form two groups, never `COMPARABLE`, with different `group_key`s; every category is mapped; an existing group key is unchanged (assert one pinned value from a current fixture).
- `double_count_violations` returns `[]` on every existing `test_w303_portfolio_*` body and one violation per crafted defect.
- Frontend: the three labels render with `data-claim-level`; the forward link carries `revision_id`; the text of every `ClaimLabel`, the beneficiary line and the forward link contains neither "saving" nor "saved". Existing negations ("not a measured saving", "Realised savings" headings, etc.) are out of scope and stay.
- Tier 2: `test_w303_portfolio_comparison_postgres.py`, `test_w303_portfolio_fixture_postgres.py`.

**Stop.** Adding `beneficiary` to the line object breaks an exact-key test outside `test_w303_*` (report the test; do not loosen it).

---

## CC-R2 · Portfolio placement (D5) and the estate producer case · 1.5 d · no migration

**Files.**
- Backend: new `estate/placement.py`; `estate/coverage.py` (carry `mechanism`, and for mini `recurs_after_finding_id`, `revision_no`, `transition`, all read with `.get` so fake snapshots need no new keys); `analytics/adapters/postgres_finding_store.py` (`_index_snapshot` head SELECT gains `f.mechanism`; no new query); `estate/adapters/postgres_estate_read.py` (`_cold_window`, `_ev_window`: one batched `SELECT id, mechanism FROM finding WHERE tenant_id = :t AND site_id = :s AND id = ANY(:ids)` per window read, adding `"mechanism"` to each findings dict); `estate/index.py` (carry the new private facts `_recurs_after`, `_transition`, `_revision_no`; RISK lens flag); `estate/portfolio.py` (call `place`, order, marker, row fields, `placement_counts`); `estate/scope.py` (six-part marker).
- Producer: `tools/s602b_test_scoped_cases.py` gains case `estate`; `tools/s602b_verification_walkthrough.py` `CASES` gains it. **No `tools/cc_estate_seed.py`** (see Producer).
- Frontend: `estate/EstatePortfolio.tsx` (group heading rows, Placement column, confidence, policy disclosure).
- Tests: new `backend/tests/test_cc_placement.py` (pure), new `backend/tests/test_cc_placement_postgres.py` (over `build_portfolio_fixture`), extend `test_w303_estate_cursor.py` (five-part fixtures rewritten to six-part by design), `test_w303_portfolio_api.py`; update `test_w301_estate_index_postgres.py:204` and `:548-563`, which assert an empty risks lens for cold rows (the specified R5.5 change; list them in the packet).

**Interfaces.**
```python
POLICY_VERSION = "estate-placement/1"
GROUPS = ("NEEDS_INVESTIGATION", "ACT_NOW", "COMPARE_VALUE", "UNPRICED_RISK", "MONITOR")   # group_rank = index + 1
GROUP_LABEL = {"NEEDS_INVESTIGATION": "Needs investigation first", "ACT_NOW": "Act now",
               "COMPARE_VALUE": "Compare value", "UNPRICED_RISK": "Unpriced risk", "MONITOR": "Monitor"}
@dataclass(frozen=True)
class Reason: code: str; text: str
@dataclass(frozen=True)
class Placement:
    group: str; group_rank: int; reasons: tuple[Reason, ...]
    confidence: str            # SUPPORTED_SOURCE_COHERENT | LIMITED | UNKNOWN
    confidence_reasons: tuple[str, ...]
def place(row: Mapping[str, Any], action: Mapping[str, Any] | None, site_cov: Mapping[str, Any],
          line_group: str | None) -> Placement: ...
```
`row` is the internal portfolio row (with its private facts); `action` is `_action_for(row, actions)`; `line_group` is the `state` of the money group (from the same call's `compare()` result) whose `line_keys` contain the line with this row's `finding_revision_id`, or `None` when the row has no line. It is already computed in the same request, so no query is added.

**Rules (first match wins; row facts only).** `label = portfolio.workflow_label(action)`; `src = (row["source_provenance"] or {}).get("state", "UNKNOWN")`; `cons = (row["consequence"] or {}).get("state")`.
1. NEEDS_INVESTIGATION when any of: `src == "MIXED"` → `EVIDENCE_SOURCE_MIXED`; `src` is `UNKNOWN`/null → `EVIDENCE_SOURCE_UNKNOWN`; `lifecycle == "UNCONFIRMED"` → `LIFECYCLE_UNCONFIRMED`; `cons == "WITHHELD"` → `CONSEQUENCE_WITHHELD`. All that apply, in that order.
2. ACT_NOW when a signal holds (`recurs_after_finding_id` not null → `RECURRED`; `transition == "REOPENED"` → `REOPENED`; `episode_end` null → `EPISODE_OPEN`; in that order, all that apply) **and** `label` is one of: "Recommendation not accepted" → `NO_ACTION_RECORDED`; "No action yet" or "Pending" → `ACTION_PENDING`; "Outcome pending" → `OUTCOME_PENDING`; "Resolution withdrawn" → `RESOLUTION_WITHDRAWN`. Reasons = signals + the one action reason. Cold and EV rows never recur (C13), so only `EPISODE_OPEN` applies to them.
3. MONITOR when `label == "Verified"` → `VERIFIED_WATCH_RETURN`, or `label == "Applied"` → `APPLIED_AWAITING_PLAN`. **Change to Appendix C:** this check runs before COMPARE_VALUE, so a verified or applied row with a priced exposure is monitored, not re-offered for value comparison (the KOBO-001 acceptance needs it). A return after verification arrives as a new Finding or a new revision with no Action of its own, which lands in ACT_NOW by rule 2.
4. COMPARE_VALUE when `cons == "PRICED"`: `PRICED_COMPARABLE` if `line_group == "COMPARABLE"`, else `PRICED_SINGLE` (single, ineligible or conflicting line).
5. UNPRICED_RISK when `cons` is present and not PRICED: mechanism `COLD_EXCURSION` → `UNPRICED_PRODUCT_EXPOSURE`; `COLD_START_FAILURE` → `UNPRICED_START_FAILURE`; `EV_INTERRUPTION` → `UNPRICED_SERVICE_INTERRUPTION`; anything else (mini `GENERATOR_SUPPORT_CANDIDATE`, `finding_episode.py:79`, or null) → `UNPRICED_OTHER`.
6. Otherwise (no consequence) MONITOR / `NO_OPEN_SIGNAL`.

**Reason texts (one dict `REASON_TEXT` in the module; `{other}` = `"Finding " + recurs_after_finding_id[:8]`, the existing `finding_label` format):**

| Code | Text |
|---|---|
| EVIDENCE_SOURCE_MIXED | Evidence comes from mixed sources; check the source before acting |
| EVIDENCE_SOURCE_UNKNOWN | Evidence source is not resolved; check the source before acting |
| LIFECYCLE_UNCONFIRMED | The latest assessment no longer confirms this Finding; check its basis |
| CONSEQUENCE_WITHHELD | Cost is withheld because its basis is not current |
| EPISODE_OPEN | No end is recorded for this episode (CC-R2-F4; was "The episode is still open") |
| RECURRED | Returned after an earlier episode ({other}) |
| REOPENED | Reopened after it had closed |
| NO_ACTION_RECORDED | No accepted Action; open the recommendation |
| ACTION_PENDING | Action accepted, not yet applied |
| OUTCOME_PENDING | Change applied; verification result pending |
| RESOLUTION_WITHDRAWN | Earlier resolution withdrawn after new evidence |
| PRICED_COMPARABLE | Priced cost exposure; compares with like lines in Financials |
| PRICED_SINGLE | Priced cost exposure; no like line to compare with |
| UNPRICED_PRODUCT_EXPOSURE | Product temperature risk; no price basis |
| UNPRICED_START_FAILURE | Backup start failure; no price basis |
| UNPRICED_SERVICE_INTERRUPTION | Charging service interruption; no price basis |
| UNPRICED_OTHER | No price basis for this Finding |
| VERIFIED_WATCH_RETURN | Change verified on simulated data; watch for a return |
| APPLIED_AWAITING_PLAN | Change applied; no verified result yet |
| NO_OPEN_SIGNAL | No open signal |

**Confidence (row facts; `site_cov` adds text only, R5.6).** `UNKNOWN` when `src` is MIXED, UNKNOWN or null; else `LIMITED` when `lifecycle == "UNCONFIRMED"` or `cons == "WITHHELD"`; else `SUPPORTED_SOURCE_COHERENT`. `confidence_reasons`, in order: lifecycle ("Supported claim" / "Unconfirmed claim"); source ("Registered simulation source" / "Authored demonstration source" / "Mixed sources" / "Source not resolved"); "Cost basis withheld" when WITHHELD; "Site coverage incomplete; other Findings may be missing" when `site_cov["state"]` is not CURRENT or HISTORICAL. Portfolio rows always carry `confidence` (never null); Findings-index rows keep null.

**Portfolio wiring.** `portfolio_row` gains `placement` (`{"policy_version", "group", "group_rank", "reasons": [{"code","text"}]}`), `confidence`, `confidence_reasons`; `priority` stays null. `_marker = (group_rank, _at, site_code_key, site_id, finding_id, finding_revision_id)`; `order_key = (group_rank, at is None, -ts, *marker[2:])`. `PORTFOLIO_ORDER = "group_rank asc, episode_start desc nulls last, site_code_key asc, site_id asc, finding_id asc, finding_revision_id asc"` verbatim. `summary.placement_counts`: over `members` (all lenses, like `finding_count`), all five keys always present, null values unless `states["F"] in (COMPLETE, EMPTY)` (EMPTY gives zeros).

**Cursor (R5.4).** `_MARKER_KINDS["portfolio"] = 6`; `_marker_ok("portfolio", after)`: `type(after[0]) is int and 1 <= after[0] <= 5` (bool refused), `after[1]` null or canonical instant, `after[2]` nonempty, `after[3:]` UUIDs. `resume_after` unchanged (exact tuple equality). Payload version `v` and `_PORTFOLIO_CURSOR_KEYS` unchanged; a five-part cursor fails through the existing invalid-cursor path.

**Lens (R5.5).** In `estate/index.py`, `flags = (["COST"] if PRICED else []) + (["RISK"] if mechanism in ("COLD_EXCURSION", "COLD_START_FAILURE", "EV_INTERRUPTION") else [])`; a row may carry both. The Findings root `lens=risks` changes the same way (intended).

**Frontend.** `TABLE_HEADS` "Priority" becomes "Placement"; Confidence column stays and shows the confidence words ("Supported, coherent source" / "Limited" / "Unknown") with `confidence_reasons` joined by " · ". Before the first loaded row of each group, a heading row `<tr className="placement-group"><th colSpan={TABLE_HEADS.length} scope="colgroup">{GROUP_LABEL} · {count}</th></tr>` (" · {count}" omitted when `placement_counts` is null); a group split across pages shows its heading once. The Placement cell: group label (bold), then the reason texts joined by " · ". Under the table, a `<details>` "How placement works" (R5.3) listing in order: "Needs investigation first: the evidence source is mixed or unresolved, the Finding is unconfirmed, or its cost is withheld." / "Act now: the episode is open, returned or reopened, and no Action is underway or its resolution was withdrawn." / "Monitor (checked next): a change was applied or verified." / "Compare value: the Finding has a priced cost exposure." / "Unpriced risk: the Finding has no price basis." and the footer "Groups say where to look first; they are not a value ranking. Within a group, most recent first. Policy estate-placement/1."

**Battery-stress stand-in (owner Q11).** The UNCONFIRMED generator-support Finding stays the stand-in, placed `NEEDS_INVESTIGATION` / `LIFECYCLE_UNCONFIRMED`, never labelled "battery stress".

**Producer (Change to Appendix C).** The combined cross-vertical producer is replaced, because no existing builder takes a site code or shares a database (`tools/s4_finding_cases.py` is KOBO-001 only and has no MG-B/MG-C cases; each walkthrough drops and recreates its own DB). Two pieces, both on existing seams, no builder parameterised:
1. **Mini thread, s602b case `estate`** (DB `assetops_s602b_audit_cc_estate`). Build order in `build()`: `run_case` F01 and F02 (as today); `run_case(runner, S4["F03"])` (its second anchor, 09:30, `recurs_after` 08:00: the **MG-B stand-in**, recurrence with no Action); F05's steps through and including the first `match` step whose expectation has `"lifecycle": "UNCONFIRMED"` via `runner.step` (the **MG-C stand-in**); diesel price v1 (see CC-D2 "Price"); then the `withdrawn` case's verification steps up to and including the first VERIFIED evaluation (`complete_windows` defaults; after CC-D2 lands, the `verified` case's window parameters). End assertions through a `TestClient(lab_app.app)` with the Action clock pinned as `serve` does, on `GET /api/estate/portfolio?from=2026-10-03T00:00:00Z&to=2026-11-03T00:00:00Z` (CC-R2-F1): the F01 row (with `action_id`) is MONITOR / `VERIFIED_WATCH_RETURN`; the F03 09:30 row is ACT_NOW with `RECURRED` and `NO_ACTION_RECORDED`; the F05 row is NEEDS_INVESTIGATION with `LIFECYCLE_UNCONFIRMED`; `double_count_violations(portfolio) == []`; no row has a numeric priority. Any failure exits non-zero before capture. **Superseded by CC-R2-Q6:** no Action or evaluation in this case; the end assertions are the F05 row on 2026-10-21 and the two 10-11 rows, as ruled there.
2. **Cold and EV**, in `test_cc_placement_postgres.py` over the existing W3-03 `build_portfolio_fixture` (cold `excursion` + EV + KOBO-001, one `demo` tenant, a `*_test` DB): `lens=risks` returns exactly the cold and EV rows; the cold row's group and reason are pinned to the single value its fixed `episode_end` implies (recorded in CC-00; ACT_NOW/`EPISODE_OPEN`+`NO_ACTION_RECORDED` if null, else UNPRICED_RISK/`UNPRICED_PRODUCT_EXPOSURE`; a conditional assertion is not allowed); the EV row is UNPRICED_RISK/`UNPRICED_SERVICE_INTERRUPTION` unless CC-00 records rank 1 or 2 for it; `limit=2` paging returns every row once in group order; `double_count_violations == []`.

The productive-use (MG-W402-001) D1 line is asserted on the D1 DB (CC-D1), not here. `INSTALL_CLOCK_CONFLICT` and its fallback are withdrawn.

**Rejected.** A numeric priority score. Placing in the frontend. Keeping five-part cursors valid. Parameterising the five shared builders for site codes (edits to tools other walkthroughs depend on, for a demo arrangement placement does not need).

**Acceptance gates.** One pure case per rule and reason code; MIXED + PRICED lands in NEEDS_INVESTIGATION; Verified + PRICED lands in MONITOR; six-part marker passes and five-part fails; the two producer assertion sets above; browser group headings and reason lines (`settledScreen` from `frontend/src/test/settled` in `estatePortfolio.test.tsx`).

**Stop.** Placement needs a fact not on the row or in the same call; the selection token would have to include placement; KOBO-001 rows in case `estate` resolve to source UNKNOWN or MIXED (report; do not fake provenance); the F03/F05 steps stop the F01 verdict from being VERIFIED (report the case).

---

## CC-M · Combined schema slice (owner Q14) · 0.5 d + one full suite · lands before CC-D2

**Files.** `backend/migrations/versions/0036_cc_mini_contribution.py` (down `0035_w5_ev_work`), `0037_cc_trial_cost_comparison.py` (down `0036_cc_mini_contribution`), `backend/tests/test_cc_schema_postgres.py`, and the head literal `"0035_w5_ev_work"` changed to `"0037_cc_trial_cost_comparison"` (slip: `"0036_cc_trial_cost_comparison"`) where it means "the current head" in: `tests/mini_depth_probe.py:22`, `test_s1_bindings_postgres.py:118`, `test_s2_evidence_ledger_postgres.py:458`, `test_s405_publication_postgres.py:499`, `test_s4_consequence_store_postgres.py:469`, `test_s4_evidence_consequence_work_postgres.py:537,568`, `test_w200_source_events_postgres.py:587,638,693`, `test_w201_cold_foundation_postgres.py:456,464`, `test_w203_cold_migration_postgres.py:30`, `test_w204_cold_migration.py:38`, `test_w205a_ev_migration.py:28`, `test_w206_ev_migration_postgres.py:29`, `test_w207_ev_money_postgres.py:38`, `test_w401_migration_postgres.py:28`, `test_w402_migration_postgres.py:40`, `test_w403_migration_postgres.py:34`, `test_w501_cold_scenarios_postgres.py:28`, `test_w502_domain_intent_postgres.py:37`, `test_w503_ev_scenarios_postgres.py:50`, `test_w504_ev_intent_postgres.py:45` (re-grep at build time; the W5 slices did the same edit). Where a test asserts `0035` as a downgrade *target* (e.g. the refusal text at `test_w504_ev_intent_postgres.py:48`), it stays. Lane T adds no migration.

**Content.**
- `0036`: drop and recreate `mini_scenario_revision_kind_check` with `'PRODUCTIVE_USE_CONTRIBUTION'` added. Downgrade raises if any row uses the new kind, else restores the old check.
- `0037`: append-only `trial_cost_comparison_revision`, using 0019's `SHA`, `KEY` and `DEMO_ACTOR` column pattern:

  | Column | Type, null | Constraint |
  |---|---|---|
  | id | uuid PK | |
  | tenant_id, site_id | uuid not null | FK `(tenant_id, site_id)` → `site` as `verification_outcome` |
  | action_id | uuid not null | FK `(tenant_id, site_id, action_id)` → `action(tenant_id, site_id, id)` |
  | verification_outcome_id | uuid not null | FK `(action_id, verification_outcome_id)` → `verification_outcome(action_id, id)` (the outcome belongs to the Action) |
  | revision_no | integer not null | `> 0`; UNIQUE `(verification_outcome_id, revision_no)` |
  | supersedes_revision_id | uuid null | FK `(verification_outcome_id, supersedes_revision_id)` → self `(verification_outcome_id, id)` (UNIQUE on that pair); CHECK `(revision_no = 1) = (supersedes_revision_id IS NULL)` |
  | formula | text not null | `= 'trial-fuel-comparison/1'` |
  | state | text not null | in the three states |
  | reason | text null | in the eleven reasons; CHECK `(state = 'UNAVAILABLE') = (reason IS NOT NULL)` |
  | result | jsonb not null | the `compare()` body |
  | intervention_cost | jsonb not null | `{amount, currency, source}` |
  | price_revision_id | uuid null | no FK (null unless both windows share one revision) |
  | basis_sha256 | text not null | `SHA`; UNIQUE `(verification_outcome_id, basis_sha256)` |
  | DEMO_ACTOR six columns | | as 0019 (`actor_kind = 'SYSTEM'`, `source_channel = 'SYSTEM_DEMONSTRATION_API'`, …) |
  | idempotency_key | text not null | `KEY`; UNIQUE `(action_id, idempotency_key)` |
  | payload_sha256 | text not null | `SHA` |
  | recorded_at | timestamptz not null | index `(tenant_id, site_id, action_id, recorded_at)` |

  Trigger `trial_cost_comparison_revision_immutable BEFORE UPDATE OR DELETE ... EXECUTE FUNCTION w4_append_only()` (defined in 0027). Downgrade drops the table.
- Two revisions, not one: each decision's schema stays separately reversible. **Rejected:** a single revision.

**Gates.** `alembic upgrade head`, `downgrade 0035_w5_ev_work`, `upgrade head` on a fresh `assetops_cc_schema_test`; the trigger refuses UPDATE and DELETE; the kind insert passes after 0036 and fails before; the chain CHECK refuses revision 2 without `supersedes_revision_id`; `pg_harness.assert_at_head`; full backend and frontend suites green on an idle machine (tier 4).

**Slip rule.** If CC-D1 is already out of the sprint at CC-M start, CC-M carries only the trial table, numbered `0036_cc_trial_cost_comparison` (down `0035_w5_ev_work`).

**Stop.** Any existing migration needs editing.

---

## Next sprint (not briefed for build): battery-stress approximation (owner Q11)

**Recommendation.** One SoC-only cue, `battery-soc-stress/1`, next sprint, first item. It is not cheap enough for this sprint: Lane C is full after the owner chose both D2 and D1, and the cue needs a declared analytic, a read path into placement, seed data and a reason line (about 1 day plus tier 2-3 validation).

- Inputs: accepted `battery_soc` evidence and the Foundation `battery_reserve` control only.
- Per Site-local day: depth of discharge = max SoC − min SoC (points); hours at or below reserve + 10 points (`dispatch_v3.py` `SOC_HEADROOM_POINTS`).
- Cue when, over the last 7 complete days with full SoC coverage, depth ≥ 70 points on at least 3 days, or near-reserve time ≥ 2 h on at least 3 days. Thresholds are declared assumptions shown with the cue.
- Label: "Battery stress cue (approximation from state of charge) · not a health, degradation or cycle-life estimate". Placement reason `BATTERY_STRESS_CUE` in NEEDS_INVESTIGATION; it replaces the stand-in only when the stand-in site's seeded SoC raises it.
- **Rejected:** equivalent full cycles from `battery_power`; any degradation model (horizon 3).

---

