# Build spec, commercial lane (Lane C), 2026-10-27 (revision 2: Implementer questions resolved)

Architect: Claude (`.ai/ROLE_CONFIG.md` line 9). Owner instruction on depth, verbatim: `.agent/owner-build-plan-depth-2026-10-27.md`. Owner answers: `.agent/owner-answers-open-questions-2-2026-10-27.md` (Q9 yes, Q10 both, Q11 stand-in, Q12 yes, Q13 yes, Q14 yes, Q15 yes, Q16 yes, Q17 yes). Index and calendar: `.agent/build-sequence-2026-10-27.md`. Implementer questions: `.agent/implementer-questions-commercial-spec-2026-10-27.md`. Every answer is written into the body below; the last section is the numbered record.

**Authority order:** this file, then `Docs/demo-sprint/commercial-capability-readiness.html` Appendix C (D1, D2, D5 wire shapes, rulings R1.x, R2.x, R5.x, acceptance criteria, producer cases, mock-deviation texts, migration plan). This file does not repeat Appendix C's wire shapes; it fixes the build order, the module boundaries, the interfaces and the choices Appendix C left open. Where it changes Appendix C, it says **Change to Appendix C** (Appendix C has been updated to match in revision 2).

---

## 0. Lane rules (every task)

### 0.1 Worktree, branch and environment

- Worktree `C:\Users\assef\Bineyame\AssetOpsV1-cc`, created by the **coordinator** from `main` before CC-R1. Branches: `task/CC-R1-links-labels`, `task/CC-R2-placement`, `task/CC-M-schema`, `task/CC-D2-reassessment`, `task/CC-D1-contribution`.
- Task files: the Implementer writes one per task at its start, `tasks/CC-R1-links-labels.md` etc. (status, a link to this spec's section, the gates), and sets the active-task pointer in its own section of `.ai/ACTIVE_CONTEXT.md`. Review packets are one per review group: `.agent/CC-C1-review-packet.md` (R1), `-C2-` (R2), `-C3-` (CC-M + D2), `-C4-` (D1).
- Python: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`.
- **PYTHONPATH (top of the first task file and of every packet):**

  PowerShell:
  ```
  $env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-cc\backend;C:\Users\assef\Bineyame\AssetOpsV1-cc\contracts;C:\Users\assef\Bineyame\AssetOpsV1-cc\simulator;C:\Users\assef\Bineyame\AssetOpsV1-cc\gateway;C:\Users\assef\Bineyame\AssetOpsV1-cc\host;C:\Users\assef\Bineyame\AssetOpsV1-cc"
  ```
  No `field` entry: the backend suite must run without it (`backend/TESTING.md:107`). Verify once per terminal that `assetops_backend.__file__` names the `-cc` worktree. Producers that import test builders also need `...\AssetOpsV1-cc\backend\tests` (as their headers say).
- Frontend: `cd C:\Users\assef\Bineyame\AssetOpsV1-cc\frontend; npx vitest run <files>`.
- **Databases (authorized names only, `assetopsv1-postgres-1`):**
  - pytest tier 2: `ASSETOPS_TEST_DATABASE_URL` → `assetops_cc_test`; schema slice `assetops_cc_schema_test`.
  - D2 and D5 producer cases (s602b, which refuses `*_test` by design): `tools/s602b_verification_walkthrough.py --db assetops_s602b_audit_cc --work var/s602b_cc`, giving per-case DBs `assetops_s602b_audit_cc_<case>` (the owner's 2026-10-24 `<tool prefix>_audit*` authorization). Dropped with the tool's own `drop`.
  - D1 producer (w403, which requires `*_test`): `--db assetops_cc_d1_contribution_test --work var/cc_d1`.
  - **Change to Appendix C:** the names `assetops_cc_d2_verified_test`, `assetops_cc_d2_price_split_test` and `assetops_cc_estate_test` are withdrawn.

### 0.2 What Lane C must not touch

`field/**`, `contract-fixtures/telemetry/**`, `gateway/**`, `contracts/**`, `simulator/**`, `host/**` (except reading `host/lab_app.py` through the s602b `serve` wrapper), `tools/checks/module-roots.ps1`, `tools/checks/dependency-direction.ps1`, the Kobo registered basis and its fixtures, `MINIGRID_ROLES*`, and the source classes in `evidence/source_provenance.py`. No field-source special case in `financials/`, `analytics/` or `evidence/`. Lane C **may** extend `tools/checks/configuration-persistence.ps1` (CC-D2 only, see there); Lane T's spec forbids it that file, `backend/migrations/**` and the mock register, so there is no shared-file conflict.

### 0.3 Heavy-job queue

Until 30 Oct 23:59 Lane C runs heavy jobs only when Lane T is not (coordinator holds the queue). From 31 Oct Lane C has priority. Tiers per Appendix C "Validation on a 16 GB machine": tier 0-1 every commit, tier 2 once per slice, tier 3 once per slice after tier 2, tier 4 (full suites) only for CC-M and merges, machine idle.

**Tier 3 evidence.** Use the producers' existing capture scripts: `tools/s602b-verification-evidence.mjs` (D2 panel, estate Portfolio for case `estate`) and `tools/w403-mini-decisions-evidence.mjs` (D1 panel). If Chrome is unavailable, record `layout evidence: not run` in the packet; the slice may merge on review ACCEPT, and the coordinator schedules the capture before the Lane C Codex batch review.

### 0.4 Cross-cutting decisions (settled here)

**Beneficiary map (owner Q9 = constant per category).** One backend constant, `estate/financials.py:BENEFICIARY_OF_CATEGORY`:

| Category | Beneficiary |
|---|---|
| `CANDIDATE_OPERATING_COST_EXPOSURE` | `MINI_OPERATOR` |
| `PRODUCTIVE_USE_CONTRIBUTION_SCENARIO` (D1) | `MINI_OPERATOR` |
| `POTENTIAL_PRODUCT_EXPOSURE` | `GOODS_OWNER` |
| `RECORDED_REPAIR` | `COOLING_PROVIDER` |
| `GROSS_TARIFF_SCENARIO` | `CHARGING_SERVICE` |

**Change to Appendix C (B and C):** the beneficiary enum gains `COOLING_PROVIDER`, because a cold repair cost is borne by the cooling provider, not the goods owner. A test asserts every category in `APPLICABLE` and `COLD_CATEGORY` is mapped.

**Partition and group key.** `_partition(line)` returns seven values: the existing six plus `_beneficiary(line)`, where
```python
def _beneficiary(line: Mapping[str, Any]) -> str | None:
    return line.get("beneficiary", BENEFICIARY_OF_CATEGORY.get(line["category"]))
```
(hand-built test lines without the key, e.g. `test_w302_money_api.py:_eligible`, keep working). `compare()` unpacks seven values. `evidence_money.group_key_for_partition` gains a keyword `beneficiary: str | None = None`: when `beneficiary is None` or equals `BENEFICIARY_OF_CATEGORY.get(category)` the payload is exactly today's six values (every existing group key is byte-identical); otherwise `"beneficiary"` is added to the hashed payload, so a crafted line with a foreign beneficiary gets its own group key. The group object gains no field.

**Claim labels.** Server-provided `claim_level` and `beneficiary` on the new D1 `contribution` and D2 `commercial_reassessment` bodies. Estate lines carry `beneficiary` only (no `claim_level`; their claim wording stays the existing category copy). For the two **existing** figures (mini gross scenario, verification verdict) the frontend derives the level, so no existing exact-key test changes in R1. **Rejected:** adding `claim_level` to existing reads in R1.

**Frontend vocabulary.** In `frontend/src/sites/actionPresentation.tsx` (the name `ClaimLevel` is taken by `siteAnalyticsClient.ts:25`):
```ts
export type CommercialClaimLevel = "MODELLED_OPPORTUNITY" | "INVENTORY_REQUIRING_REVIEW" | "EXPECTED_VALUE"
  | "VERIFIED_SIMULATED_TECHNICAL" | "POST_INTERVENTION_MODELLED";
export type Beneficiary = "MINI_OPERATOR" | "GOODS_OWNER" | "FLEET_OPERATOR" | "CHARGING_SERVICE" | "COOLING_PROVIDER";
export const CLAIM_LABEL: Record<CommercialClaimLevel, string> = {
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
All five levels are in the union now (two are unused this sprint). One component `frontend/src/sites/ClaimLabel.tsx`: `ClaimLabel({ level, beneficiary }: { level: string; beneficiary: string })` rendering `<p className="claim-label" data-claim-level={level} data-beneficiary={beneficiary}>{CLAIM_LABEL[level]} · benefits: {BENEFICIARY_WORDS[beneficiary]}</p>`; an unknown level or beneficiary renders "Claim not stated" and never throws. The local `CLAIM_LABEL` in `EvSiteViews.tsx:96` is a different vocabulary and is left alone.

**Arithmetic.** Exact `Fraction`; divisions stored with `actions/verification_rules.py:fmt` (decimal when the denominator is 2^a·5^b, `p/q` otherwise). The wire is always exact. **Display (frontend only):** currency amounts 2 decimal places; per-kWh rates 4 decimal places; litres 2 decimal places; kWh as the wire gives them. A nominal value rounds half up to the nearest; an **upper** value rounds up (toward +∞), so it never understates. **Change to Appendix B R-X.2:** "4 significant decimals" reads "4 decimal places for per-kWh rates, 2 for currency".

**Mock deviations.** Every new panel gets its register entry in `.agent/mock-departure-register.md` in the same commit. Lane C takes IDs **R500-R519** (Lane T does not edit the register). Category **D2 improvement**. Row format = the register's table columns: `| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |`, Status `standing (owner)`. "What is shown instead" uses the Appendix C deviation text verbatim. Planned rows: R500 claim labels (`scenarios`, `verification`), R501 beneficiary line (`financials`), R502 placement groups (`portfolio`), R503 commercial reassessment (`verification`), R504 expected contribution (`opportunity-finding`, `scenarios`), R505 Portfolio productive-use card SCENARIO state (`portfolio`). Texts for R500, R501, R505: "Claim level and beneficiary stated under the figure; v69 shows the figure only." / "Beneficiary stated on each money line; v69 has no beneficiary." / "Declared contribution scenario on the productive-use card; v69 shows a placeholder."

---

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
| EPISODE_OPEN | The episode is still open |
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
1. **Mini thread, s602b case `estate`** (DB `assetops_s602b_audit_cc_estate`). Build order in `build()`: `run_case` F01 and F02 (as today); `run_case(runner, S4["F03"])` (its second anchor, 09:30, `recurs_after` 08:00: the **MG-B stand-in**, recurrence with no Action); F05's steps through and including the first `match` step whose expectation has `"lifecycle": "UNCONFIRMED"` via `runner.step` (the **MG-C stand-in**); diesel price v1 (see CC-D2 "Price"); then the `withdrawn` case's verification steps up to and including the first VERIFIED evaluation (`complete_windows` defaults; after CC-D2 lands, the `verified` case's window parameters). End assertions through a `TestClient(lab_app.app)` with the Action clock pinned as `serve` does, on `GET /api/estate/portfolio?from=2026-10-01T00:00:00Z&to=2026-11-03T00:00:00Z`: the F01 row (with `action_id`) is MONITOR / `VERIFIED_WATCH_RETURN`; the F03 09:30 row is ACT_NOW with `RECURRED` and `NO_ACTION_RECORDED`; the F05 row is NEEDS_INVESTIGATION with `LIFECYCLE_UNCONFIRMED`; `double_count_violations(portfolio) == []`; no row has a numeric priority. Any failure exits non-zero before capture.
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

## CC-D2 · Post-trial commercial reassessment (D2, roadmap R3) · 1.75 d

**Files.**
- Backend: `actions/verification_rules.py` (`window_evidence` returns `generator_kwh` = sum of slot `generator_power` kWh, `fmt`, null if any slot unknown; outside `plan_sha256`; not added to the stored outcome `details`); new `financials/trial_fuel_comparison.py` (pure); new `financials/adapters/postgres_trial_comparison_store.py`; `financials/composition.py` (`build_trial_comparison_ports(url) -> TrialComparisonPorts` holding the store and `price_selection`); `actions/adapters/postgres_action_store.py` (`sfc_history`); `actions/verification.py` (replay helper, hook (a), command (b), reads); `actions/action_api.py` (route and body whitelist); `actions/composition.py` (calls `financials.composition.build_trial_comparison_ports`; only `financials/composition.py` imports the financials adapter).
- Guard: `tools/checks/configuration-persistence.ps1` gains `$trialComparisonWriter = "$backendRoot/financials/adapters/postgres_trial_comparison_store.py"` in `$pgWriters`, the table list `@('trial_cost_comparison_revision')` as INSERT-only (no UPDATE/DELETE/TRUNCATE/MERGE/COPY/DO UPDATE from any module) with an INSERT-seen anti-vacuity counter, and a probe test proving the check fails with the writer removed (pattern of `tools/checks/test_estate_guard.py`). No other rule changes.
- Producer: `tools/s602b_test_scoped_cases.py` gains cases `verified` and `price_split` (and `estate` adopts the `verified` window parameters); every case publishes prices (below); `window_fake` passes the four new window parameters.
- Test helpers: `backend/tests/test_s6_verification_rules.py:full_window` gains `gen_kw="20"`; `test_s6_verification_evaluator_postgres.py:complete_windows` gains `baseline_gen_kw="20", later_gen_kw="20", baseline_load_kw="10", later_load_kw="10"`, chosen by window date like `soc`. Defaults keep every existing caller byte-identical.
- Frontend: `sites/SiteActionVerification.tsx` "Commercial reassessment" panel with `ClaimLabel` (`POST_INTERVENTION_MODELLED`, `MINI_OPERATOR`).
- Tests: new `backend/tests/test_cc_trial_fuel_comparison.py` (pure), extend `test_s6_verification_rules.py`, `test_s6_verification_evaluator_postgres.py`, frontend panel test. If `fixtures/s6_verification_api_contract.json` pins the windows read's or the evaluations response's exact keys, add only the new keys and list them in the packet.

**Interfaces.**
```python
FORMULA = "trial-fuel-comparison/1"
REASSESSMENT_STATES = ("MODELLED_IMPROVEMENT", "MODELLED_NO_IMPROVEMENT", "UNAVAILABLE")
#: precedence order: the first that applies is the reason
REASSESSMENT_REASONS = ("OUTCOME_INCONCLUSIVE", "WINDOW_INCOMPLETE", "NOT_COMPARABLE", "SOURCE_NOT_COHERENT",
    "EVIDENCE_REPLAY_MISMATCH", "GENERATOR_KWH_UNKNOWN", "ZERO_DEMAND", "SFC_MISSING", "SFC_DIFFERS",
    "PRICE_MISSING", "PRICE_BASIS_DIFFERS")
@dataclass(frozen=True)
class WindowFacts:
    evidence_ids: tuple[str, ...]; complete: bool
    generator_kwh: Fraction | None; feeder_demand_kwh: Fraction | None
    start: datetime; end: datetime
@dataclass(frozen=True)
class OutcomeFacts:
    outcome_id: str; plan_id: str; origin_finding_revision_id: str
    outcome: str                                         # VERIFIED | INEFFECTIVE | INCONCLUSIVE
    stored_evidence_ids: Mapping[str, tuple[str, ...]]   # outcome.basis.evidence_ids["baseline"|"later"]
    comparability_state: str                             # rules.comparability(replayed windows)["state"]
    source_state: str                                    # rules.source_pair(replayed sources)["state"]
@dataclass(frozen=True)
class InterventionCost: amount: Fraction; currency: str | None; source: str   # None = the price currency
def compare(baseline: WindowFacts, later: WindowFacts, outcome: OutcomeFacts, sfc_in_force: Sequence[SfcValue],
            prices: tuple[PriceSelection, PriceSelection], intervention_cost: InterventionCost) -> dict[str, Any]: ...
class TrialComparisonStore(Protocol):
    def latest(self, tenant_id: UUID, site_id: UUID, outcome_id: UUID) -> dict[str, Any] | None: ...
    def history(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> list[dict[str, Any]]: ...
    def append(self, row: Mapping[str, Any]) -> tuple[dict[str, Any], bool]: ...   # (row, inserted); idempotent on (outcome, basis_sha256)
def price_selection(tenant_id: UUID, site_id: UUID, start: datetime, end: datetime, known_at: datetime) -> PriceSelection: ...
```
`SfcValue` is `mini_depth/rules.py:SfcValue`; `PriceSelection`, `select_window_price` and `MULTIPLIER` come from `financials/fuel_cost.py`; `fmt` from `actions/verification_rules.py` (no import cycle: `actions` does not import `financials`).

**Reason conditions, in precedence order.** `OUTCOME_INCONCLUSIVE`: `outcome.outcome` not VERIFIED/INEFFECTIVE. `WINDOW_INCOMPLETE`: either window `complete` false. `NOT_COMPARABLE`: `comparability_state != "PASS"`. `SOURCE_NOT_COHERENT`: `source_state != "PASS"`. `EVIDENCE_REPLAY_MISMATCH`: a window's `evidence_ids` set ≠ the stored set. `GENERATOR_KWH_UNKNOWN`: either `generator_kwh` null. `ZERO_DEMAND`: either `feeder_demand_kwh` is 0. `SFC_MISSING`: a window has no single positive SFC in force over it (`_sfc_for` semantics). `SFC_DIFFERS`: the two values differ. `PRICE_MISSING`: either selection not PRICED. `PRICE_BASIS_DIFFERS`: revision IDs differ. Rules 2-4 cannot arise from a real final outcome (the evaluator would have said INCONCLUSIVE); they are pure guards, each with one isolating pure test.

**Compute.** Per window: fuel nominal = SFC × generator kWh, upper = nominal × `MULTIPLIER`; cost = fuel × price; cost per kWh = cost / feeder kWh. Change = baseline − later, nominal and upper. `state = MODELLED_IMPROVEMENT` iff change nominal > 0, else `MODELLED_NO_IMPROVEMENT` (0 included). The intervention cost is stated beside the change and never subtracted (it is a total, the change is per kWh; **Change to Appendix C** D2 "Money": "…per kWh of feeder demand; intervention cost stated beside it"). Its currency must equal the price currency; null takes the price currency.

**Output split.** `compare()` returns: `formula, claim_level, beneficiary, state, reason, outcome_id, plan_id, origin_finding_revision_id, windows` (per window `generator_kwh, feeder_demand_kwh, fuel_l, cost, cost_per_demand_kwh`; fields that could not be computed are null), `change_per_demand_kwh` (null when UNAVAILABLE), `intervention_cost, price` (`{revision_id, value, currency}` only when both windows share one revision, else null), `sfc` (`{value_l_per_kwh}` or null), `evidence_ids, basis_sha256, label`. The read layer adds `id, revision_no, recorded_at, read_flags, current_price_basis`. `basis_sha256` = SHA-256 of sort-keyed compact JSON over `{formula, outcome_id, evidence_ids{baseline,later}, generator_kwh{b,l}, feeder_demand_kwh{b,l}, sfc_l_per_kwh{b,l}, price_revision_ids{b,l}, intervention_cost{amount,currency,source}, state, reason}` (unknowns as JSON null).

**Window replay (R2.6).** A `VerificationService._replay(tenant, site, plan, outcome)` helper runs the evaluator's own steps at `known_at = outcome.recorded_at`: `_windows`, `rules.comparability`, and the provenance port into `rules.source_pair`, exactly as the evaluation does (`verification.py` ~598-610). No new loader.

**SFC (R2.7).** `postgres_action_store.sfc_history(tenant, site, generator_asset_id, lo, hi, known_at) -> list[SfcValue]`, same SQL shape as `reserve_history`, reading the generator component's `specific-fuel-consumption` (L/kWh); generator = the plan basis' bound `generator_power` asset. Compared by value; IDs are not compared.

**Price (R2.8), Change to Appendix C.** Demo step v4 does **not** cover both windows: v4 ends 2026-11-01, so the 11-02 later window falls in v1's remainder, and v2 must precede v3/v4 by `expected_prior_step`. Publication is in-process through `assetops_backend.publish_assumption.main([...], store=PostgresAssumptionStore(url))` for site KOBO-001, after `run_case` F01/F02 and before any evaluation:
- `verified`, `estate`, `target_miss`, `guardrail`, `inconclusive`, `withdrawn`: `fixture --step v1` only (1.25 USD/L covers both windows with one revision).
- `price_split`: `fixture --step v1 v2 v3 v4`; baseline (10-06) selects v4 (1.28), later (11-02) selects v1's remainder [2026-11-01, 2030-01-01) (1.25): one PRICED selection each, different revisions, `PRICE_BASIS_DIFFERS`. No new step and no conversions-file change.
`price_selection` uses the assumption store's assignments and revisions known at the computation time (hook or command instant) and `select_window_price`. On read, `current_price_basis` re-runs it for both windows at read time: `CHANGED` when either selection's state or revision differs from the stored ones, else `SAME`; `read_flags` contains `PRICE_REPUBLISHED` exactly when `CHANGED`, and `SUPERSEDED_BY_WITHDRAWAL` when `lifecycle.latest_resolution` for that outcome is RESOLUTION_WITHDRAWN.

**Authored windows for `verified`.** `complete_windows(..., baseline_gen_kw="40", later_gen_kw="28", baseline_load_kw="60", later_load_kw="63")`: generator 40 → 28 kWh, feeder 120 → 126 kWh (two loads), PV 6/6, SOC 50/50. Feeder band |126 − 120| = 6 ≤ 12 (10%), PV and SOC bands pass, guardrails pass (unserved 0, SOC above reserve 30, terminal 50 ≥ 50); the target comes from real S3 with `later_generator_off` (0 later Candidate seconds), so the verdict is VERIFIED. Otherwise the case runs the `withdrawn` case's steps up to its first VERIFIED evaluation. Expected: `MODELLED_IMPROVEMENT`, and with SFC 0.3 nominal change `"1/24"`.

**Hooks (R2.9).** (a) In the evaluations command, after `record_evaluation` commits a **newly inserted** final outcome (VERIFIED, INEFFECTIVE **or INCONCLUSIVE**; **Change to Appendix C**, so inconclusive outcomes get their UNAVAILABLE revision without a command), in its own transaction: compute and append with `idempotency_key = f"auto:{outcome_id}"`, the SYSTEM_DEMO actor and grant basis of that evaluation, intervention cost `{amount: "0", currency: null, source: "reserve-trial-1 policy change; no direct cost declared"}`. An idempotent replay of an evaluation does not run the hook; it reads the latest revision. The POST evaluations response gains top-level `commercial_reassessment` (the revision or null) and `commercial_reassessment_status` ∈ `RECORDED | NOT_RECORDED | NOT_APPLICABLE` (no final outcome). Any exception in the hook gives `null` + `NOT_RECORDED`, never a rollback. **Change to Appendix C:** `REASSESSMENT_PENDING` is not used here (it already names a verification state).
(b) `POST /api/sites/{code}/actions/{id}/verification/commercial-reassessments`, existing VERIFY grant. Body (whitelist; an unknown field is refused as the evaluations route refuses one): `idempotency_key` (8-128), `outcome_id` (required, no default), `intervention_cost {amount: exact decimal ≥ 0, currency: ISO 4217, source: 1-500 chars}` (required). 201 when a revision is appended (`revision_no` = previous + 1, `supersedes_revision_id` = previous); 200 with the stored revision when `(outcome, basis_sha256)` already exists or the same key repeats with the same `payload_sha256`; 409 `IDEMPOTENCY_KEY_REUSED` for the same key with a different payload; 404 `OUTCOME_NOT_FOUND` for an unknown outcome or one of another Action; 422 `INTERVENTION_COST_INVALID` for a bad amount or a currency other than the PRICED price currency. `payload_sha256` = SHA-256 of the canonical body without `idempotency_key` (hook: of `{outcome_id, intervention_cost}`). Response `{"commercial_reassessment": ...}`.

**Reads (R2.11).** `GET .../verification/outcome` adds `commercial_reassessment` (latest revision for the selected outcome, or null). `GET .../verification/history` adds `commercial_reassessments`: all revisions of the Action, newest first, each `{id, revision_no, outcome_id, state, reason, price_revision_id, current_price_basis, recorded_at}`. No estate field (R2.5).

**Panel.** Two-column table (Baseline, Later): generator kWh, feeder kWh, modelled fuel (nominal / upper L), modelled cost (nominal / upper), cost per kWh of feeder demand; then "Modelled change per kWh of feeder demand" (nominal, upper); "Intervention cost" with its source; then `ClaimLabel`. UNAVAILABLE shows "Not calculated: {reason words}" with plain words per reason (e.g. `PRICE_BASIS_DIFFERS`: "the two hours were priced from different diesel price records"; `OUTCOME_INCONCLUSIVE`: "the trial result is inconclusive"). `CHANGED` shows "Diesel prices were republished since this was calculated."

**Rejected.** Recomputing on every read. A worker. Comparing SFC by revision ID. Annualizing. Subtracting intervention cost from a per-kWh change.

**Acceptance gates.** Pure: the worked example (generator 40/28, feeder 120/126, SFC 0.3, price 1.25, cost 0) gives `change_per_demand_kwh == {"nominal": "1/24", "upper": "11/240"}` and per-window cost per kWh `"0.125"` / `"1/12"`; each reason has one isolating test and the precedence order is tested. Route walk on `verified` (Appendix C steps). `price_split` → `PRICE_BASIS_DIFFERS`; `inconclusive` → `OUTCOME_INCONCLUSIVE` (from hook (a)); `target_miss` → `MODELLED_NO_IMPROVEMENT` with nominal change `"0"`; in a Postgres test, publishing a test-only CORRECTION over both windows (1.30 USD/L, 2026-10-01 to 2026-12-01, through `publish_assumption.main(["publish", ...])`) after a `verified`-style evaluation makes the read say `CHANGED`, and the command appends `revision_no == 2` with revision 1 still in history. The wording test ("saving", "saved", "realized" only inside "not realized savings"); label "per kWh of feeder demand" (owner Q12). Guard probe green.

**Stop.** `plan_sha256` would change; replay cannot reproduce a stored outcome's evidence set on the s602b cases (report the case; do not relax the check).

---

## CC-D1 · Productive-use contribution (D1, roadmap R4) · 1.75 d · slips first

**Files.**
- Backend: `mini_decisions/scenario_rules.py` (`KINDS`, `KEYS`, units, `_physical_gate`, `contribution`, state `CONTRIBUTION_SCENARIO`); `mini_decisions/scenarios.py:342` (dispatch); `mini_decisions/opportunities.py` (`_compatible` at `:427` accepts both kinds; `demand_state`; `contribution_scenario`); `estate/financials.py` (category, `APPLICABLE[MINI_GRID] = (OPERATING, PRODUCTIVE)`, `assumption_fingerprint_v2`, `mini_contribution_lines`, `_line` gains `line_key: str | None = None`); `estate/adapters/postgres_estate_read.py` (snapshot method `mini_contributions`); `estate/composition.py` (inject the opportunity read service, as cold/EV site reads are injected); `estate/portfolio.py` (PRODUCTIVE_USE card and `opportunity` object). Test fake snapshots in `test_w30*` gain `def mini_contributions(self, *a): return []` (explicit; no getattr default).
- Producer: `tools/w403_mini_decisions_walkthrough.py` gains phase `replay-contribution` (after `replay-late`, requires its marker, writes `contribution.json`); existing phases and captures unchanged. DB `assetops_cc_d1_contribution_test`.
- Frontend: new `sites/ContributionPanel.tsx`, used by `sites/MiniOpportunity.tsx` (under the gross card) and `sites/MiniScenarios.tsx` (row detail; `KIND_WORDS.PRODUCTIVE_USE_CONTRIBUTION = "Productive-use contribution"`); `sites/miniDecisionsClient.ts` types; `estate/EstatePortfolio.tsx` OpportunityPanel and card state SCENARIO.
- Tests: extend `test_w403_scenario_rules.py` (unchanged cases pass unedited), `test_w403_scenarios_postgres.py` (`ROW_KEYS` gains `contribution`), `test_w403_opportunity_read_postgres.py` (`OBJECT_KEYS` gains `contribution_scenario`), estate financials and portfolio tests.

**Interfaces.**
```python
KINDS = ("STOP_SOC", "PRODUCTIVE_LOAD", "TARIFF_ONLY", "OTHER", "PRODUCTIVE_USE_CONTRIBUTION")
KEYS["PRODUCTIVE_USE_CONTRIBUTION"] = (
    ("collection_fraction", "duration_hours", "marginal_cost_per_kwh", "proposed_kw", "tariff_per_kwh"),
    ("enablement_cost", "other_cost_per_window"))
CONTRIBUTION_SCENARIO = "CONTRIBUTION_SCENARIO"
def _physical_gate(items: Sequence[Mapping[str, Any]], days: Sequence[DayRow]) -> dict[str, Any] | None: ...
def contribution(items: Sequence[Mapping[str, Any]], days: Iterable[DayRow]) -> dict[str, Any]: ...
PAYBACK_REASONS = ("NO_ENABLEMENT_COST", "NO_POSITIVE_CONTRIBUTION")
def assumption_fingerprint_v2(category: str, currency: str, rates: Mapping[str, str]) -> str: ...
```
- **Units and bounds** (`_assumption`): `collection_fraction` unit `"ratio"`, 0 < x ≤ 1; `marginal_cost_per_kwh` unit `<CCY>/kWh` via `tariff_currency`, ≥ 0; `enablement_cost` and `other_cost_per_window` unit `<CCY>` (exactly an `ISO_4217` code), ≥ 0; `tariff_per_kwh` > 0 as today and required for this kind (R1.6); `proposed_kw`, `duration_hours` as today. Every currency must equal the tariff currency, else `invalid()` (422 `DECISION_INPUT_INVALID`).
- **Dispatch.** `scenarios.py:342` calls `rules.contribution(...)` when `cmd["kind"] == "PRODUCTIVE_USE_CONTRIBUTION"`, else `rules.calculate(...)`. `calculate()` keeps its kind gate (it still returns `NO_CALCULATION`/`NOT_PRODUCTIVE_LOAD` for the new kind and is never called for it) and calls `_physical_gate`; output byte-identical for every existing case.
- **Stored shape.** For the new kind, the `calculation` jsonb is `{state, energy_kwh: E per window, gross_sales: null, reason, contribution: {...} | null}`; other kinds' calculations are unchanged (no `contribution` key). Scenario rows expose `contribution` = `calculation.get("contribution")` (null for other kinds).
- **Arithmetic.** E = proposed_kw × duration_hours; revenue = E × tariff × collection; supply = E × marginal; other = `other_cost_per_window` or 0 (shown as `"0"`); unit = revenue − supply − other (products exact or `Inexact` 422). Study = eligible_windows × unit. c* = (marginal + other / E) / tariff as `Fraction`, stored with `fmt` (example: `"0.12"`). Payback: `NO_POSITIVE_CONTRIBUTION` when unit ≤ 0 (checked first); `NO_ENABLEMENT_COST` when `enablement_cost` is absent or 0; else `ceil(enablement / unit)`.
- **Fingerprint v2.** `"sha256:" + sha256(sort-keyed compact JSON {"payload": "estate-money-assumption/2", "category", "currency", "rates": {"tariff_per_kwh", "collection_fraction", "marginal_cost_per_kwh", "other_cost_per_window"}})`, values as `decimal_text`, absent other cost as `"0"`. `enablement_cost`, E and `eligible_windows` are excluded by design (they do not change the per-window economics; overlap is the technical-ID rule).
- **Opportunity read.** `_compatible` accepts `PRODUCTIVE_LOAD` and `PRODUCTIVE_USE_CONTRIBUTION`. `contribution_scenario` = the selected compatible link's scenario `calculation.contribution` under the existing gross read gate (CURRENT/HISTORICAL, class not MIXED/UNKNOWN), else null. `demand_state = "DECLARED"` when that link is the new kind; `collection_state = "UNVERIFIED"`.
- **Estate line (Appendix C "Estate line field fill", plus):** `mini_contributions(t, s, from_, to, k)` calls the injected opportunity service's list read (`from`/`to` = estate window, `known_at` = k) and its detail read per opportunity, returning per opportunity `{opportunity_id, scenario_revision_id, contribution, calculation_state, calculation_reason, gate (currentness.state), source_class, source_provenance (selected_source_provenance), pins: [{mini_revision_id, decision, evidence_ids}], first_day, last_day, tz}` for those with a selected compatible contribution link. `mini_contribution_lines` builds each line with `line_key = f"mini-contribution:{opp}:{scenario_rev}"`, `finding_id`/`finding_revision_id` null, `consequence_revision_id` = scenario revision ID, `quantity = {"low": E×n, "high": E×n, "unit": "kWh"}`, `assumption_revision_ids = []` (scenario assumptions are not financial-assumption revisions), `limit = "Expected value under declared demand, collection and cost; not collected revenue."`, `source_provenance` = the opportunity's selected block, `links` = `_money_links(code, MINI_GRID, None, None, k)`, `disclosure = {"opportunity_id", "scenario_revision_id", "currentness": gate, "contribution": contribution}`. `applicable[PRODUCTIVE]` equals the site's OPERATING flag, and False if the opportunity read raised.
- **Portfolio.** `CARD_SLOTS[("PRODUCTIVE_USE", "SCENARIO")] = (None, "Declared contribution scenario", "amber")`; the card is SCENARIO when at least one contribution line is ELIGIBLE (display: the amount when exactly one, else "Several studies · see Financials"); `CARD_DESTINATION` for SCENARIO is `"/financials"`. The `opportunity` object keeps its five keys: `{"state": "SCENARIO", "finding_id": None, "scenario_amount": amount when exactly one eligible line else None, "headroom": None, "destination": "/financials"}`. **Change to Appendix C:** "lists eligible lines in placement order" is replaced by "points to Financials, where lines follow the Financials order (never by amount)". OpportunityPanel shows the amount (or the several-studies text), `ClaimLabel` `EXPECTED_VALUE` + `MINI_OPERATOR`, and "See in Financials →".

**Panel copy (`ContributionPanel.tsx`).** Tiles: "Contribution per eligible noon hour" ("1.70 USD"; a negative value is shown with "Loses money at this collection rate"); "Study contribution" ("6.80 USD over 4 eligible noon hours"); "Collection break-even" (c* as a percent of billed energy collected, 1 decimal place when not whole: "12%"); "Payback" ("71 eligible noon hours", or "Not computed: no enablement cost declared" / "Not computed: contribution is not positive"). Inputs table (Input, Value, Unit, Source = the assumption's `source`): Proposed load, Hours per day, Tariff, Share of billed energy collected, Supply cost per kWh, One-off enablement cost, Other cost per hour. Then "Demand: declared, not observed" and "Collection: not verified", then `ClaimLabel`. Withheld copy: `HEADROOM_BELOW_LOAD` "Not calculated: the proposed load is larger than the smallest spare solar capacity in the study days."; `INCOMPLETE_STUDY` "Not calculated: not every study day has a complete assessment."; `NO_ELIGIBLE_DAY` "Not calculated: no study day had spare solar capacity at noon."; `NO_PINNED_SELECTION` "Not calculated: no study days are pinned." No authoring form: scenarios are written by the producer or the API only.

**Producer cases (`replay-contribution`).** On MG-W402-001's positive opportunity: the contribution scenario `cc-d1-contribution-r1` (10 kW, 1 h, tariff 0.25 USD/kWh, collection 0.8, marginal 0.03 USD/kWh, enablement 120 USD; sources "Declared demo assumption"), linked as the opportunity's selected scenario. Negatives, written as scenarios and not linked: (a) the same inputs with `proposed_kw` = the study's minimum ELIGIBLE lower headroom + 1 (read from the stored day rows; recorded in CC-00) → WITHHELD / `HEADROOM_BELOW_LOAD`; (b) collection 0.1 → `"-0.05"`, `NO_POSITIVE_CONTRIBUTION`; (c) pinned to the `missing_study_days` variant's study → WITHHELD / `INCOMPLETE_STUDY`. The tier-2 Postgres gates use the w403 test fixtures in `assetops_cc_test`.

**Rejected.** Optional keys on `PRODUCTIVE_LOAD` (R1.5). A stored hurdle rate (R1.3). Summing contribution with operating cost (R1.4). The estate adapter re-querying mini decision tables (it would duplicate the currentness gate).

**Acceptance gates.** Pure: `unit_contribution == "1.7"`, `collection_break_even == "0.12"`, `payback.windows == 71`; collection 0.1 gives `"-0.05"` with `NO_POSITIVE_CONTRIBUTION`; enablement absent gives `NO_ENABLEMENT_COST`; currency mismatch 422. Postgres: `contribution_scenario.study_contribution` equals eligible_days × 1.7 with `DECLARED`; (a) and the MIXED case give a null amount with the reason; estate one PRODUCTIVE_USE_CONTRIBUTION_SCENARIO line, group SINGLE_LINE, never OPERATING, `estate_total` null; `double_count_violations == []` on the D1 DB's Portfolio and Financials bodies. Browser: the panel copy above and "Expected value · declared assumptions".

**Stop.** Any existing `calculate()` case changes output.

---

## Next sprint (not briefed for build): battery-stress approximation (owner Q11)

**Recommendation.** One SoC-only cue, `battery-soc-stress/1`, next sprint, first item. It is not cheap enough for this sprint: Lane C is full after the owner chose both D2 and D1, and the cue needs a declared analytic, a read path into placement, seed data and a reason line (about 1 day plus tier 2-3 validation).

- Inputs: accepted `battery_soc` evidence and the Foundation `battery_reserve` control only.
- Per Site-local day: depth of discharge = max SoC − min SoC (points); hours at or below reserve + 10 points (`dispatch_v3.py` `SOC_HEADROOM_POINTS`).
- Cue when, over the last 7 complete days with full SoC coverage, depth ≥ 70 points on at least 3 days, or near-reserve time ≥ 2 h on at least 3 days. Thresholds are declared assumptions shown with the cue.
- Label: "Battery stress cue (approximation from state of charge) · not a health, degradation or cycle-life estimate". Placement reason `BATTERY_STRESS_CUE` in NEEDS_INVESTIGATION; it replaces the stand-in only when the stand-in site's seeded SoC raises it.
- **Rejected:** equivalent full cycles from `battery_power`; any degradation model (horizon 3).

---

## Implementer questions and resolutions

Answered 2026-10-27 by the Architect (Claude) against the code at `abb5ab56`. Numbering matches `.agent/implementer-questions-commercial-spec-2026-10-27.md`. "Body" names the section now carrying the decision.

**Q-C1 (c* format).** Defect confirmed: `fmt(Fraction(3,25)) == "0.12"`. The gate is `"0.12"`; no new formatter. Body: CC-D1 Arithmetic and gates; Appendix C D1 wire, acceptance and worked example amended.

**Q-C2 (v4 does not cover the later window).** Confirmed: v4 ends 2026-11-01, the later window is 11-02. `verified` publishes v1 only (one revision over both windows); no conversions-file edit and no window move. The worked example moves to 1.25 USD/L: nominal change `1/24`, upper `11/240` (replaces `16/375`, `88/1875`). Body: CC-D2 Price, gates; Appendix C D2 updated.

**Q-C3 (v2 in the chain; tool; assignments).** v2 is required before v3/v4. Tool: `publish_assumption.main(["fixture", "--site", "KOBO-001", "--file", ..., "--step", ...], store=PostgresAssumptionStore(url))` in-process. Assignments: v1-only cases, both windows → v1; `price_split` (v1-v4), baseline → v4, later → v1's remainder [2026-11-01, 2030-01-01); no conflict or span. Body: CC-D2 Price.

**Q-C3b (`price_split` step).** No new step: publishing v1-v4 already splits the windows across two revisions. Body: CC-D2 Price; Appendix C Demo-data row amended.

**Q-C4 (authored windows).** Defect confirmed: the helpers author 20 kWh generator and 20 kWh feeder. Allowed edit: default keyword parameters on `full_window` (`gen_kw`) and `complete_windows` (four kW parameters), so existing callers are byte-identical. `verified`: 40/28 kW generator, 60/63 kW per load (120/126 kWh). Bands are 10% feeder and PV and 2 SOC points (`BANDS_V1`); 6 ≤ 12 passes. The target comes from real S3 (`later_generator_off`, 0 s), not the authored windows. Body: CC-D2 Files, Authored windows.

**Q-C5 (MG-B/MG-C do not exist; builders are single-site).** Confirmed. The combined orchestrator is withdrawn. MG-B stand-in = S4 F03's recurring 09:30 Finding; MG-C stand-in = S4 F05 run through its UNCONFIRMED match; both on KOBO-001 in the new s602b case `estate` next to the verified F01 Action. Cold/EV placement and `lens=risks` are asserted on the existing W3-03 `build_portfolio_fixture`. No builder is parameterised. Body: CC-R2 Producer; Appendix C D5 rows amended.

**Q-C6 (rank 3 swallows MONITOR).** Confirmed. A Verified/Applied check (group MONITOR, rank 5) runs before COMPARE_VALUE. "Applied" = `workflow_label == "Applied"` → `APPLIED_AWAITING_PLAN`; "Verified" → `VERIFIED_WATCH_RETURN`; `NO_OPEN_SIGNAL` only when a row has no consequence. Body: CC-R2 Rules 3 and 6.

**Q-C7 (rank 3 needs the line group).** Signature is `place(row, action, site_cov, line_group)`, with `line_group` taken from the same call's `compare()` groups. No query. `PRICED_SINGLE` covers single, ineligible and conflicting lines. Body: CC-R2 Interfaces, Rule 4.

**Q-C8 (`mechanism` missing).** In scope. Mini: add `f.mechanism` to `_index_snapshot`'s head SELECT. Cold/EV: one batched `finding` mechanism SELECT per window read in `estate/adapters/postgres_estate_read.py`. Coverage reads with `.get`, so fakes are unchanged. Mini string `GENERATOR_SUPPORT_CANDIDATE`. Body: CC-R2 Files, Rule 5.

**Q-C9 (no recommendation builder in `BridgeLinks`).** Confirmed. Add optional `recommendation` to `BridgeLinks`, wired in `SiteAnalyticsFrames.tsx` for the mini Financials frame (the file is added to the CC-R1 list; the main checkout's uncommitted edit is not in the `-cc` worktree). Cold/EV pass nothing, so no link shows. Body: CC-R1 Files, Forward link.

**Q-C10 ("saving" test).** It applies only to the new text (the labels, the beneficiary line, the forward link). Existing negations stay unchanged. Body: CC-R1 gates.

**Q-C11 (seventh element breaks `compare()` and hand-built lines).** Confirmed. `compare()` unpacks seven values; beneficiary is read with a category default (`_beneficiary`); `group_key_for_partition` gains an optional `beneficiary` that changes the hash only for a non-default beneficiary, so every existing group key is unchanged. Body: §0.4 Partition and group key.

**Q-C12 (head literals).** Confirmed, and there are about 22 files, not 8 (all are listed in CC-M Files). They move to the new head; downgrade-target uses stay. Lane T has no migration. Body: CC-M Files.

**Q-C13 (guard, import direction).** Lane C may extend `configuration-persistence.ps1` with the new writer, an insert-only table rule, an anti-vacuity counter and a probe test. No new estate reader is added: D1 reuses `postgres_estate_read.py`, already in `$pgReaders`. Imports: `financials` → `actions.verification_rules.fmt` and `mini_depth.rules.SfcValue` have no cycle and no rule against them. `actions/composition.py` reaches the store only through `financials/composition.py`. Body: CC-D2 Files, Guard; §0.2.

**Q-C14 (`ClaimLevel` name).** The new names are `CommercialClaimLevel` and `Beneficiary` in `actionPresentation.tsx`. All five levels are in the union. Body: §0.4 Frontend vocabulary.

**Q-C15 (estate beneficiary display).** A second line in the existing category cell: "Benefits: {words}". No new column. Register row R501. Estate lines carry no `claim_level`. Body: §0.4, CC-R1.

**Q-C16 (verdict label gating).** The label shows when the displayed outcome's `outcome` is VERIFIED or INEFFECTIVE, with the same label for both (the technical result is verified either way; the Appendix B copy is final). Body: CC-R1 Labels.

**Q-C17 (invariant input).** Inputs are parsed HTTP bodies. The member set is `portfolio["selected_lines"]`; the paged financials rows are never used, and a missing member is `MEMBER_NOT_FOUND`. The three null paths are as you listed. Currency comes from `amount` or `disclosure.pinned_amount`. Body: CC-R1 Approach.

**Q-C18 (register).** Block R500-R519, category D2, the register's existing columns, Appendix C texts verbatim, plus three texts given for the extra rows. Body: §0.4 Mock deviations.

**Q-C19 (texts and labels).** All 20 reason texts, the group labels and the confidence texts are fixed. `{other}` is the first 8 characters of `recurs_after_finding_id`. Body: CC-R2 tables.

**Q-C20 (confidence rule).** UNKNOWN for a MIXED, UNKNOWN or null source; LIMITED for UNCONFIRMED or WITHHELD; otherwise SUPPORTED_SOURCE_COHERENT. Site coverage adds a reason only. Every Portfolio row carries it. Body: CC-R2 Confidence.

**Q-C21 (open, recurred, reopened, action mapping).** Open = `episode_end` null. RECURRED = `recurs_after_finding_id` not null. REOPENED = `transition == "REOPENED"`. Action reasons map from `workflow_label` as in Rule 2. Cold/EV can only be open. A resolved, verified row is not ACT_NOW; a return arrives as a new Finding or revision without its own Action, which is ACT_NOW. Body: CC-R2 Rules 2-3.

**Q-C22 (cold non-deterministic).** The value is pinned once from the fixture's fixed `episode_end`, recorded in CC-00; a conditional assertion is not allowed. EV: UNPRICED_SERVICE_INTERRUPTION unless CC-00 records rank 1 or 2. Source key `row["source_provenance"]["state"]`; consequence `row["consequence"]["state"]`. Body: CC-R2 Producer 2, Rules.

**Q-C23 (cursor).** Confirmed as you proposed: an int 1-5 that is not a bool, then the old rules shifted by one. The order string is given verbatim. MAC `v` is unchanged. Rewriting the five-part fixtures is expected. Body: CC-R2 Cursor.

**Q-C24 (`placement_counts`).** Counted over `members`, with all five keys. Null unless the F state is COMPLETE or EMPTY; EMPTY gives zeros. Body: CC-R2 Portfolio wiring.

**Q-C25 (lens in `index.py`).** In scope. The Findings-root change is intended. A row may carry both COST and RISK. `test_w301_estate_index_postgres.py:204,548-563` are updated and listed. Body: CC-R2 Files, Lens.

**Q-C26 (frontend layout).** Group heading rows (`colSpan`) appear before each group's first loaded row; the count comes from `placement_counts`; the Confidence column stays; a "How placement works" `<details>` holds the policy text. Body: CC-R2 Frontend.

**Q-C27 (`INSTALL_CLOCK_CONFLICT`).** Moot. The combined producer and its fallback are withdrawn (Q-C5). Body: CC-R2 Producer.

**Q-C28 (end assertions).** Case `estate` asserts three KOBO-001 rows plus the invariant on the Portfolio body. The W3-03 test asserts the cold, EV, `lens=risks` and paging criteria. The D1 line is asserted in CC-D1. Body: CC-R2 Producer.

**Q-C29 (opportunity lines in the estate).** The estate adapter gets a `mini_contributions` snapshot method that calls the opportunity service injected by `estate/composition.py`. This reuses `_study`'s gate and does not re-query tables. `_line` gains a `line_key` override. Every unspecified field is now given. Fakes gain an explicit method. Body: CC-D1 Estate line.

**Q-C30 (Portfolio card and opportunity object).** The change is in CC-D1 and `estate/portfolio.py` is in its file list. The card slot and the five-key object are given. The order is Financials order, never by amount. Appendix C wording amended. Body: CC-D1 Portfolio.

**Q-C31 (where contribution lives; dispatch; kind gates).** The contribution is stored inside the `calculation` jsonb and surfaced as the row's `contribution`. For the new kind, `energy_kwh` is E per window and `gross_sales` is null. The dispatch is in `scenarios.py:342`; `calculate()` is unchanged for the new kind. `KINDS`, `KEYS`, `_compatible` (`:427`) and `KIND_WORDS` all gain the kind. Body: CC-D1 Interfaces, Dispatch, Stored shape.

**Q-C32 (units and bounds).** Units: `"ratio"`, `<CCY>/kWh`, `<CCY>`. Values ≥ 0 except tariff > 0 and collection in (0, 1]. Absent other cost is shown as `"0"`. An enablement cost of 0 or absent gives `NO_ENABLEMENT_COST`, after the non-positive-contribution check. Body: CC-D1 Units, Arithmetic.

**Q-C33 (fingerprint v2 keys).** Four rate keys; absent other cost encoded `"0"`; values as `decimal_text`. Enablement, E and the window count are excluded by design. Body: CC-D1 Fingerprint v2.

**Q-C34 (panel copy).** All copy is given. c* shows as a percent; payback is in "eligible noon hours". There is no UI authoring form. Body: CC-D1 Panel copy.

**Q-C35 (producer location, DB, headroom).** A new w403 phase `replay-contribution` in `assetops_cc_d1_contribution_test`, the name the w403 tool's own `*_test` guard accepts. Negative (a) uses the stored minimum headroom + 1, not a fixed 30 kW, because the fixture states no headroom value. Tier 2 uses the w403 test fixtures. Body: CC-D1 Producer cases.

**Q-C36 (outcome facts; reason order).** `OutcomeFacts` is typed, and the replay recomputes comparability and source with the evaluator's own steps. Three reasons are pure guards, unreachable from real final outcomes. The full order of the 11 reasons is fixed in the `REASSESSMENT_REASONS` tuple. Body: CC-D2 Interfaces, Reason conditions.

**Q-C37 (improvement; intervention cost).** IMPROVEMENT iff nominal change > 0. Intervention cost is never subtracted and never affects the state. Its currency equals the price currency, and a null default takes it. Appendix C "Money" amended. Body: CC-D2 Compute.

**Q-C38 (display rounding).** 4 decimal places for per-kWh rates and 2 for currency, in the frontend only. Nominal rounds to nearest; upper rounds up (the example upper shows 0.0459). Body: §0.4 Arithmetic.

**Q-C39 (SFC, price loading, CHANGED).** SFC comes from a new `sfc_history` on the action store; price from `price_selection` via the financials composition. Both use the computation instant as cutoff. CHANGED = a read-time re-selection differs from the stored one. `PRICE_REPUBLISHED` is set iff CHANGED. Withdrawal comes from `latest_resolution`. Body: CC-D2 SFC, Price.

**Q-C40 (UNAVAILABLE persistence).** UNAVAILABLE results are persisted. Hook (a) also runs for INCONCLUSIVE outcomes (Appendix C amended), which covers the `inconclusive` case; `price_split` gets its revision from hook (a). Uncomputable fields are null, and `basis_sha256` hashes the nulls plus state and reason. Body: CC-D2 Hooks, Output split.

**Q-C41 (command contract).** Body fields, status codes, refusal codes, idempotency scope (`(action_id, idempotency_key)` unique), the `payload_sha256` definition and the slim history fields are all given. `outcome_id` has no default. Body: CC-D2 Hooks (b), Reads.

**Q-C42 (column list).** Full types, nullability, CHECKs, FKs, actor columns (0019's `DEMO_ACTOR`), uniques, index and trigger name are given. `supersedes_revision_id` is required iff `revision_no > 1`. Body: CC-M table.

**Q-C43 (`generator_kwh` and tests).** A new key in `window_evidence`'s return, not stored in `details`. A contract fixture that pins keys gains only that key. The s602b `serve` already re-applies the same fake, so replay equality is expected; a mismatch is the Stop. Body: CC-D2 Files.

**Q-C44 (hook transaction).** The hook runs only on a newly inserted outcome; a replayed evaluation reads instead. It uses key `auto:{outcome_id}` and the evaluation's SYSTEM_DEMO actor. The response gains top-level `commercial_reassessment` plus `commercial_reassessment_status` (not `REASSESSMENT_PENDING`, which already names a state). Exact-key tests gain these keys. Body: CC-D2 Hooks (a).

**Q-C45 (default cost; R2.5).** The default is as given, with `currency: null` (the price currency). There is no estate reassessment field. Body: CC-D2 Hooks, Reads.

**Q-C46 (worktree and task files).** The coordinator creates the worktree. The Implementer writes one task file per CC task and one packet per review group C1-C4. Body: §0.1.

**Q-C47 (DB names).** The s602b cases use `assetops_s602b_audit_cc_<case>`: the s602b tool refuses `*_test`, and the owner's `_audit*` authorization covers this name. D1 uses `assetops_cc_d1_contribution_test`; tier 2 uses `assetops_cc_test`. The old names are withdrawn. Body: §0.1.

**Q-C48 (browser evidence).** Use the existing s602b and w403 evidence scripts and the `serve` ports they use. Without Chrome, record "not run"; the merge is not blocked, and the capture happens before the Codex batch review. Body: §0.3.

**Q-C49 (merge conflicts with Lane T).** None. Lane T's spec forbids it migrations, the persistence guard and the register. The merge order in the build sequence stands. Body: §0.2.

**Q-C50 (`compare()` output vs read layer).** `compare()` emits everything except `id, revision_no, recorded_at, read_flags, current_price_basis`, which the read layer adds. The tests assert on `compare()` output. Body: CC-D2 Output split.

**Effort and sequence effect.** CC-R2 is unchanged at 1.5 d: no orchestrator, but one extra s602b case and a Postgres test. CC-D2 goes 1.5 → 1.75 d (helper parameters, the guard extension, INCONCLUSIVE hook, command contract). CC-D1 goes 1.5 → 1.75 d (the estate seam through the opportunity service, the Portfolio card). CC-M stays 0.5 d but edits about 22 test files. Order is unchanged: R1, R2, M, D2, D1. Slip rule 2 (combined estate) is withdrawn. No question needs the owner.

**CC-R1-Q1 (verdict label trips the vocabulary guard).** Answered 2026-10-27 by the Architect (Claude). `"simulated"` stays guarded (D-2026-10-04), so the guard is not loosened. `CLAIM_LABEL.VERIFIED_SIMULATED_TECHNICAL` = `"Technical result verified on test data"`. This matches the existing "Generated test data" and "Policy trial on Lab or authored test data", and it holds for both generated and authored sources. The enum key is unchanged. The CC-R2 `VERIFIED_WATCH_RETURN` text becomes `"Change verified on test data; watch for a return"`. Body: §0.4 Frontend vocabulary and the CC-R2 table read with these texts. Detail: `.agent/CC-R1-questions.md`.

**CC-R1-Q2 ("Claim not stated" fallback).** Answered 2026-10-27 by the Architect (Claude). `"claim"` is guarded. The `ClaimLabel` fallback = `"Evidence level and beneficiary not stated"`, shown alone with no beneficiary suffix. It never throws, and the data attributes carry the raw values. One unit test scans the fallback and expects no vocabulary hits. Body: §0.4 `ClaimLabel` reads with this text.

**CC-R2-Q1 (confidence texts trip the vocabulary guard).** Answered 2026-10-28 by the Architect (Claude). There is no exemption. The new `confidence_reasons` texts are "Supported Finding" / "Unconfirmed Finding" and "Generated test data source" / "Prepared example data source". "Mixed sources", "Source not resolved" and the withheld and coverage texts are unchanged. A frontend test runs `forbiddenPhrases` over the priority panel, and a pure backend test scans every placement text. Body: CC-R2 Confidence and the Appendix C D5 example read with these texts. Detail: `.agent/CC-R2-questions.md`.

**CC-R2-Q2 (W3-03 fixture has no EV row).** Answered 2026-10-28 by the Architect (Claude). The fixture keeps `ev == []` pinned as a CC-00 fact. A new test, `test_ev_interruption_placement`, uses the existing W2-05b `interrupted` chain (one SUPPORTED `EV_INTERRUPTION` Finding with an open episode), with no builder parameterised. It asserts ACT_NOW with `EPISODE_OPEN` + `NO_ACTION_RECORDED` (CC-00 rank 2, Q-C21), SUPPORTED_SOURCE_COHERENT, `lens=risks` and no double count. `UNPRICED_SERVICE_INTERRUPTION` stays pure-only. Body: CC-R2 Producer 2 reads with this test. Detail: `.agent/CC-R2-questions.md`.

**CC-R2-Q3 (panel copy contradicts Confidence).** Answered 2026-10-28 by the Architect (Claude). `PRIORITY_SUBTITLE` becomes "Selected Findings across accessible Sites, grouped by where to look first, with evidence confidence alongside." The panel-bottom line becomes "Placement and confidence answer different questions.", shown only when there are rows, and the `both` logic is removed. Both are labelled MOCK DEVIATIONS against v69 `index.html:133,135`. Body: CC-R2 Frontend. Detail: `.agent/CC-R2-questions.md`.

**CC-R2-Q4 (no Portfolio capture claim).** Answered 2026-10-28 by the Architect (Claude). CC-R2 adds a follow-up commit before capture. `estate_assertions` returns the three row keys. `tools/s602b-verification-evidence.mjs` gains `portfolioSuite` for case `estate`, which checks the group headings with counts, the three placements and reason lines, the confidence vocabulary, the bottom line, the policy disclosure, no overflow and a mock comparison, and takes six screenshots at 1440×1000 and 390×900. The evidence is produced by the walkthrough `prepare` and `capture` on `assetops_s602b_audit_cc` / `var/s602b_cc`. Body: CC-R2 Files and §0.3. Detail: `.agent/CC-R2-questions.md`.
