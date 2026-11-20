# Build sheet OUT-C · early warnings, first set (self-contained)

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-30. Code read at main `e8cf8a36` in worktree
`C:\Users\assef\Bineyame\AssetOpsV1-outC`, branch `task/OUT-C-early-warnings`. All file:line anchors are at that commit.
Backend paths are relative to `backend/assetops_backend/` unless they start with `backend/`, `tools/` or `frontend/`.
**This sheet replaces Slice C of `build-spec-outcome-sprint-2026-10-29.md` for building.** Where they differ, this
sheet wins (rulings are in the spec section "Pre-flight rulings C"). Read nothing else unless a step names it.

## 0. Rules that bind every unit

- Do not touch `main.py`, any `*/composition.py`, `field/ gateway/ contracts/ simulator/ host/ contract-fixtures/`,
  `backend/migrations/`, `tools/checks/*`, `estate/financials.py`, `financials/**`, `estate/money_invariants.py`.
  B already wires every port C reads (`site_outcomes/read.py:142-306`): work, plans, dispatch, EV overview, health,
  availability, cold and EV Findings. C adds no port and no new read service.
- `outcomes/*.py` stays pure: imports only `__future__`, `dataclasses`, `typing`, `collections.abc` and `outcomes.*`
  (AST test `backend/tests/test_out_a1_outcome_map.py`). So no `datetime`/`Decimal` import there: the composer passes
  instants (compared only), pre-computed bounds, Site-local `date` objects (`.day`, `.month` only) and pre-formatted
  number texts.
- **No warning ever carries money**: no amount, currency, price or rate key or text.
- No outcome code, enum value or policy version on screen, in `title` or `aria-label`. No visible MOCK DEVIATION
  label; deviations go only to `.agent/mock-departure-register.md`, IDs **R560-R571** (§8).
- The frontend authors no "Not available yet" string (that would trip `tools/checks/missing-claim-scan.mjs`). All
  such text below is backend text.
- Every string in §3 was scanned against `terms` + `w1.terms` + `w1.codes` + the w1 patterns of
  `frontend/src/test/productVocabulary.json`: 0 hits. A new string you invent must be scanned the same way.

## 1. Code reality (what C may rely on)

| Rule / element | Source (existing read, already ported in B) | Verdict |
|---|---|---|
| REPEATED_MAINTENANCE_NO_RESULT | `work/site_index.py:309` maintenance rows: `case_id, code, state, asset_id, asset_label, occurred_at, finding_links`; filtered by root **`created_at`** in `[from,to)`, max 31 d (`:42`, `:114`), `to` may be in the future | **EXTEND** (3 windows, §2 U2) |
| ...linked Finding open | cold/EV/mini Findings already in `SiteFacts.findings` (`FindingFact.open`) | OK |
| PLAN_OVERDUE / PLAN_DUE_SOON | `work/global_index.py:388` `select_preventive`: DRAFT heads only (no ACTIVE/PAUSED/CANCELLED exist), root `occurred_at` in `[from,to)`; `next_due_at`, `trigger_kind`, `asset_id`, `asset_label` | OK (+ `PlanFact.due_at`, U2) |
| BATTERY_NEAR_RESERVE | dispatch `window()` body `intervals[].result.binding_constraints` (`analytics/dispatch_v3.py:471`, served `analytics/dispatch_read.py:161`), values `BATTERY_AT_RESERVE`/`BATTERY_NEAR_RESERVE` (`dispatch_v3.py:291`). Reserve **%** is only inside reason prose: not read | **EXTEND** (count periods; no %). Overrules B-Q11's "not read" |
| CHARGER_FAULT_OVERDUE_INSPECTION | EV `health.rows[]` `kind CONNECTOR`, `condition_state NEEDS_INVESTIGATION`, `asset_id`, `label` (`analytics/ev_depth.py:180-195`); **no fault date** on the row | **EXTEND** (no date in text) |
| CONNECTOR_OUT_OF_SERVICE | `availability.connectors[]` `asset_id, label, known_unavailable_seconds, unknown_seconds` (`analytics/ev_availability.py:184-212`) | OK |
| PEAK_NEAR_IMPORT_LIMIT | EV overview `site_power.observed_peak_kw`, `configured_limit_kw` (`ev_site_reads.py:693-700`) | OK |
| CHARGERS_MOSTLY_IDLE | needs connector rated kW: on no read (only `scheduled_seconds`) | **NOT AVAILABLE → dropped** (R565) |
| Generator service due soon | no hours-since-service value | **NOT AVAILABLE → not a rule**; B text stays (R561) |
| Fault date, 30-day reserve dwell, lowest % | none | **NOT AVAILABLE** (R562, R566) |
| Site-local dates | mini: depth zone; cold/EV: route Site `timezone` (B addendum 3 b); UTC + `UTC_SUFFIX` fallback (`site_outcomes/mini.py:34`) | OK |
| `source_label` on a warning | needs per-rule provenance parsing; not rendered anywhere | **dropped from wire** |
| Maintenance "Repeat findings" card | `frontend/src/work/GlobalMaintenance.tsx:253-259` exists | OK (retire, U6) |
| WR page Site code | `GlobalWorkDetailBody.site_code` (`frontend/src/work/globalWorkClient.ts:443`) | OK |
| Estate summary / board wire | `read.py:332` `"warnings": []`, `:362` `warning_count: 0`, `:365` `"warnings": []`; status rule 4b/5b already reads `WARNING` signals (`outcomes/status.py:63-71`) | OK (fill in) |

**Demo data facts.** w502 cold is shifted to yesterday `D` (`tools/w502_cold_work_cases.py:72-76`), so it is
durable. Its existing WR is created at build time, after the board window's `to`, which is why B could not show it
(B packet: "cold B.7 #4 absent"). w504 EV evidence window is fixed at `2026-10-06T08:00-09:00Z`
(`tools/w504_ev_work_cases.py:39-40`), and the Kobo fixtures (s602b, s5) use fixed October dates. Work occurrences
are refused older than 30 days (`work/model.py:37`, `:239`, code `WORK_OCCURRED_AT_TOO_OLD`). So EV and mini plans
inside their board windows would be time bombs: **C authors data only in w502 `positive`.** There are no repeated
visits and no cold plans in the data today.

## 2. Units (6). Effort 5.5 builder days plus one full suite

### U1 · Warning producer (pure) · 1.0 d · per-unit review
Files: new `outcomes/warnings.py`; `outcomes/catalogue.py:7,49-50,62-63,75`.
- `catalogue.py`: `CATALOGUE_VERSION = "outcome-catalogue/2"`. MG-4 and CC-3 lose their `missing_records`
  (so they are measured). Delete the `(COLD, "OPTIMIZE_COST")` entry of `ROW_NOT_MEASURED` (`:75`).
- `warnings.py`, `POLICY = "early-warnings/1"`:
```python
@dataclass(frozen=True) class Visit:  case_id; code; asset_id; asset_name; state; occurred_at; occurred_on; finding_ids; href
@dataclass(frozen=True) class PlanCue: plan_id; code; title; due_at; due_on; asset_id; href
@dataclass(frozen=True) class WarningFacts:
    domain: str; site_code: str; to: Any; visits_from: Any; soon_until: Any   # to-60d, to+14d (composer computes)
    window_days: tuple[Any, Any]; date_suffix: str = ""                        # Site-local first/last day of the window
    visits: tuple[Visit, ...] = (); plans: tuple[PlanCue, ...] = ()
    open_findings: Mapping[str, tuple[tuple[str, ...], str | None]] = {}      # id -> (moves+checked keys, href)
    reserve: tuple[int, int] | None = None                                      # mini (n at/near, m assessed)
    faults: tuple[tuple[str, str], ...] = ()                                    # EV (asset_id, label)
    connectors_out: tuple[tuple[str, str, str, str], ...] = ()                  # EV (asset_id, label, out text, unknown text)
    peak: tuple[float, float, str, str] | None = None                           # EV (peak, limit, peak text, limit text)
@dataclass(frozen=True) class Warning: kind; subject; badge; lens; title; seen; persistence; price_needs;
    status_effect; categories; href; evidence_refs; count; subject_label; visit_ids   # visit_ids, subject: not on the wire
    def wire(self, site_code, site_name) -> dict
def evaluate(f: WarningFacts) -> tuple[Warning, ...]   # sorted (badge order RISK, EARLY_WARNING, OPPORTUNITY; kind; key)
```
- Rules (all bounds half-open; nothing fires when its input is absent):

| Kind | Fires when | `subject` | badge / lens / effect | `href` |
|---|---|---|---|---|
| `REPEATED_MAINTENANCE_NO_RESULT` | per non-null `asset_id`: ≥ 2 visits `state == "COMPLETED"` with `visits_from ≤ occurred_at < to`, **and** some visit on that asset in the window (any state) links a Finding id in `open_findings` | asset_id | RISK / COST / NEEDS_ATTENTION | latest completed visit (max `occurred_at`, then `case_id`) |
| `PLAN_OVERDUE` | `due_at is not None and due_at < to` | plan_id | EARLY_WARNING / RISK / WATCH | `/maintenance/preventive` |
| `PLAN_DUE_SOON` | `to ≤ due_at < soon_until` | plan_id | EARLY_WARNING / RISK / WATCH | `/maintenance/preventive` |
| `BATTERY_NEAR_RESERVE` (mini) | `reserve` and `reserve[0] ≥ 1` | `site` | EARLY_WARNING / RISK / WATCH | `/sites/{c}/performance/dispatch` |
| `CHARGER_FAULT_OVERDUE_INSPECTION` (EV) | a `faults` asset_id equals the `asset_id` of a plan that fires PLAN_OVERDUE | asset_id | EARLY_WARNING / RISK / WATCH | `/sites/{c}/health` |
| `CONNECTOR_OUT_OF_SERVICE` (EV) | one per `connectors_out` entry (composer passes only `known_unavailable_seconds > 0`) | asset_id | RISK / RISK / WATCH | `/sites/{c}/performance/availability` |
| `PEAK_NEAR_IMPORT_LIMIT` (EV) | `peak[0] ≥ (1 - PEAK_MARGIN) * peak[1]`, `PEAK_MARGIN = 0.10` | `site` | RISK / RISK / WATCH | `/sites/{c}/performance/energy` |

  Persistence: `RECURRING` ("Recurring") for the repeat rule, `OBSERVED` ("Observed") for every other rule.
  Badge labels: RISK "Risk", EARLY_WARNING "Early warning". The builder confirms the three EV/mini hrefs open real
  routes (`frontend/src/shell/evSiteRoutes.tsx:26-28`, `sitePerformanceHref`/`siteHealthHref`), else uses those helpers' output.
- `categories` = `outcome_map.categories_for("WARNING:" + kind, domain, linked)`. For the repeat rule `linked` =
  the union, in order, of the open linked Findings' moves+checked keys, minus the warning's own moved key (CC-3 etc.).
- `key` on the wire = `f"{kind}:{site_code}:{subject}"`. `count` = n visits (repeat only, else null). `subject_label`
  = the visit `asset_name` (repeat), connector or fault `label` (EV), else null.
- `evidence_refs`: repeat → each completed visit `{kind: "WORK_CASE", id, label: code, href}` ascending, then each
  open linked Finding `{kind: "FINDING", id, label: null, href}`; PLAN_* → `{kind: "PLAN", id, label: code, href}`;
  fault → the plan ref plus `{kind: "ASSET", id: asset_id, label, href: null}`; connector → the ASSET ref; others `[]`.
- Tests: `backend/tests/test_out_c_rules.py` (positive + negative per rule): 1 vs 2 completed; Finding open vs
  closed vs unresolved; visit at `to − 60 d` (in) vs `to − 60 d − 1 s` (out) and at `to` (out); 4 OPEN + 3
  COMPLETED on one asset gives exactly **one** warning (this replaces the Postgres worstcase check); due exactly at
  `to` → DUE_SOON, at `soon_until` → none, at `to − 1 s` → OVERDUE; RUN_HOURS plan (no `due_at`) → none; fault with
  no overdue plan → none; fault + overdue plan on another asset → none; peak 72/80 none, 76/80 fires; `reserve` None,
  (0, 3), (2, 3); key, sort order and `categories` for each kind; `@LINKED` excludes the warning's own key.
- `backend/tests/test_out_c1_never_money.py`: for every rule's positive output, `json.dumps(w.wire("X", "Y"))` has
  no key in `{"amount","amount_low","amount_high","currency","value","price","rate"}` (walk nested) and no match of
  `r"[$€£]|\b(USD|EUR|GBP|KES|ETB)\b|\d+(\.\d+)?\s*(per litre|/kWh|per kWh)"`; `price_needs` ∈ `PRICE_NEEDS.values()`.
  **Anti-vacuity:** the same check on a wire with an injected `"amount": 1` (and one with seen text "$5") must fail.
- Update `test_out_a1_outcome_map.py:109` (MG-4/CC-3 now measured) and `test_out_b1_status.py` golden grid to
  the C values: mini Protect WATCH, cold Cost NEEDS_ATTENTION.

### U2 · Board and read plumbing · 1.0 d · per-unit review (shared seam)
Files: `site_outcomes/board.py`, new `site_outcomes/visits.py`, `site_outcomes/read.py`, `mini.py`, `cold.py`, `ev.py`.
- **Visits read (EXTEND, rules B-Q22 carried, widened).** New `visits.py`
  `maintenance_cases(reads, work_port, site_code, to) -> list[CaseFact] | None`: three `work("maintenance", ...)`
  reads by `created_at`: `[to−62 d, to−31 d)`, `[to−31 d, to)`, `[to, to+31 d)` (the third catches visits recorded
  after `to`; a work record can be recorded up to 30 days after it occurred). Dedupe by `case_id`; keep
  `to − 60 d ≤ occurred_at < to`. Any refused read → None (name `work_index` failed, PARTIAL, as now).
  Replace the `maintenance` half of the case loop in all three composers (`mini.py:254-257`, `cold.py:93-96`,
  `ev.py:95-98`) with it. Incidents keep B's `[to−31 d, to)` (the index already filters them by `occurred_at`).
- `PlanFact` (`board.py:133`) gains `due_at: Any = None` (UTC instant); `plan_fact` (`mini.py:425`) fills it.
- `visits.py` also holds `warning_facts(facts, *, to, tz, suffix, lo, **extras) -> WarningFacts`, deriving visits
  (asset_name = text before " · " in `asset_label`, else the label), plans (CALENDAR with `due_at`), and
  `open_findings` (open `FindingFact`s, keys via `outcome_roles`) from `SiteFacts`. Each composer then does
  `facts = replace(facts, warnings=evaluate(warning_facts(...)))`.
- `board.py`:
  - `SiteFacts.warnings: tuple[Warning, ...]` (`:193`).
  - Status signals (in `assemble`, after `:334`): per warning, per moved outcome `i`:
    `Signal(WARNING, key, i == 0, True, False, w.status_effect, w.key)`. Checked outcomes give no signal.
  - Issues (`_row`, after `:384`): warnings MOVES then CHECKED, in `evaluate` order:
    `{"kind": w.badge, "role": role, "text": w.title, "href": w.href, "ref": w.key}`. MOVES categories plus
    CHECKED categories not already MOVES (the `_Roles` rule).
  - Case placement: a case whose id is in a repeat warning's `visit_ids` is also placed in that warning's MOVES
    categories (Earlier and in hand), in addition to B's placement.
  - Plans (`:423-427`): `state_label` "Overdue" / "Due soon" when that plan fires PLAN_OVERDUE / PLAN_DUE_SOON,
    else B's `_plan_label`. Add a note on register rows **R08** and **R10**: the due cue is now evaluated; the plan
    state stays DRAFT.
  - Must not harm (after `:438`): if still None and a repeat warning MOVES in this row with checked outcomes
    outside the row: `{"text": join_names(labels) + ": a repair counts only when the fault it answers stops",
    "href": <first open linked Finding href>}`.
- `read.py`: `POLICY_VERSIONS["warnings"] = "early-warnings/1"` (`:32-33`). `board()` `:332` →
  `[w.wire(site.site_code, site.site_name) for w in comp.facts.warnings]`. `summary()`: collect each Site's
  `body["warnings"]` in Site order (already sorted per Site); `warning_count` (`:362`) = warnings with the category
  in any `categories.items[].category`; `"warnings"` (`:365`) = that list. A failed Site contributes none.
- Settled (U2 sets; U3/U4 rely on it): `CC-3 = base and findings_ok and visits is not None` (`cold.py:106-109`);
  `MG-4 = base and dispatch is not None` (`mini.py:268`).
- Tests `backend/tests/test_out_c2_board.py`: three-window visit read with a fake work port (calls, dedupe,
  occurred filter, refusal → PARTIAL); warning → status (NEEDS_ATTENTION beats WATCH; a CHECKED role sets nothing);
  issue order (Findings, signals, CHECKED Findings, then warnings); case double placement; plan state labels; Must
  not harm text; wire keys; summary order and `warning_count`. Update the B fakes that model the maintenance work
  port (`test_out_b2_mini.py`, `test_out_b3_cold_ev.py`, `test_out_b4_read.py`) and list each in the packet.

### U3 · GreenHarvest cost row and authored data · 1.0 d · slice review
Files: `site_outcomes/cold.py`, `tools/w502_cold_work_walkthrough.py`, new `backend/tests/test_out_c3_repeat_visits_postgres.py`,
`backend/tests/test_out_b4_board_postgres.py`.
- Cold Cost contributors (`cold.py:123`, replace `COST: ()`), headline and subline (`:141-145`):

| key / label | text | confidence | href |
|---|---|---|---|
| `maintenance_effectiveness` / "Maintenance effectiveness" | warning: "{n} visits ({d1}, {d2}, {d3}); the linked finding is still open"; none: "No repeated visit without a result in 60 days"; visits None: `NOT_LOADED` | readiness chip (none when NOT_LOADED) | warning `href` |
| `repair_cost` / "Repair and call-out" | "No cost on work record {latest completed code}", else "No repair or call-out cost recorded" | `UNKNOWN_CHIP` | `/sites/{c}/financials` |
| `cooling_energy` / "Cooling energy" | "Not available yet · no cooling energy meter" | null | null |

  Headline when the repeat warning exists: "{n} repair visits in 60 days without a result"; subline "None of the
  visits resolved the linked finding; repair cost is not recorded". Otherwise both None. Dates "d MMM" ascending
  plus `date_suffix`. Cold Protect `_plan` (`cold.py:229-246`): an overdue plan reads "{title} overdue since {date}".
- **w502 authored data**, `positive` mode only, appended at the **end** of the `BUILD` string (after the case reads,
  ~`:455`), so no existing manifest count or K-cutoff assertion changes. Through the same `work` service and
  `PRINCIPAL` as `:196-220`. `d16 = sh.start`, `wr_at = d16 + 20 min`:
  - Visit 1: `request(f"w502b-{mode}-wr-e1-{tag}", title="Starter battery replaced", occurred_at=iso(wr_at − 24 d),
    asset_id=gen.id, finding_links=[])`; `record(... activity="Starter battery replaced", occurred_at=+20 min,
    outcome_note="Battery replaced; automatic start not tested")`; ASSIGN (+21 min), COMPLETE (+22 min) citing the record.
  - Visit 2: same at `wr_at − 11 d`, "Control relay reset", note "Relay reset; automatic start not tested".
  - Plans via `work.post_plan(tenant, site, body, PRINCIPAL)` (`work/service.py:424`, keys `:32`): "Witnessed backup
    start test", CALENDAR, `next_due_at = floor_day(wr_at) − 4 d`, `next_due_hours None`, `asset_id = gen.id`,
    `occurred_at = wr_at − 1 d`; "Compressor coil cleaning", `next_due_at = floor_day(wr_at) + 9 d`, asset = the
    single registration with `asset_type == "COMPRESSOR"` (stop and ask if not exactly one), same `occurred_at`.
  - Idempotency keys `w502b-{mode}-{wr-e1|wr-e2|rec-e1|...|plan-start|plan-coil}-{tag}`. `doc["out_c"]` records
    the ids; `attest` fails a `positive` manifest without `out_c` (2 cases, 2 records, 2 plans).
  - If any write returns `WORK_OCCURRED_AT_TOO_OLD`, use −20 d and −8 d and record it.
- Postgres test (pattern of `test_out_b4_board_postgres.py:447-475`, DB `assetops_out_c_cold_test`): BUILD
  `positive`; board on `doc["w501"]["window"]`, no `known_at`. Assert: exactly one REPEATED warning, `count == 3`;
  Cost row `NEEDS_ATTENTION`, lead CC-3, headline "3 repair visits in 60 days without a result"; Cost Earlier =
  2 × "Did not fix it" then "Not yet verified"; Protect issues include "Witnessed backup start test overdue"
  (`EARLY_WARNING`) and in hand has the coil plan with state "Due soon"; no money key anywhere in the body
  (reuse the U1 walker). **P-C1** (record, then branch): GET the estate summary for `[D, D+1)`. If GreenHarvest's
  summary row Cost is NEEDS_ATTENTION with one warning, assert it (U5/U6 estate surfaces are then captured on this
  DB). Otherwise record the honest state, assert only the board, and carry estate acceptance to the combined dataset.
- Update `test_out_b4_board_postgres.py:466-470`: with the authored visits, `repeated` and `present` are both true.

### U4 · Mini battery and EV warnings · 0.75 d · slice review
Files: `site_outcomes/mini.py`, `site_outcomes/ev.py`, new `backend/tests/test_out_c4_mini_ev.py`,
new `backend/tests/test_out_c4_ev_warnings_postgres.py`.
- Mini: `reserve = (n, m)` from the dispatch body already read at `mini.py:243`: `m = len(intervals)`, `n` = intervals
  whose `result.binding_constraints` contains `BATTERY_AT_RESERVE` or `BATTERY_NEAR_RESERVE`; None if dispatch failed.
  Battery contributor (`mini.py:481`, replaces `FIXED["battery"]`): n ≥ 1 "At or near the reserve during {n} of {m}
  assessed generator {period|periods}"; n = 0 < m "No generator period at or near the reserve ({m} assessed)";
  m = 0 "Not available yet · no generator period assessed on this day"; dispatch None `NOT_LOADED`. Confidence:
  readiness chip when n or m is known, else null. Protect headline (`mini.py:307`): w = warnings moving MG-4;
  w ≥ 1 "{w} early {warning|warnings} on battery and generator", else `PROTECT_HEADLINE`.
- EV (`ev.py` before `:200`): `faults` from `fault_rows` (`ev.py:134-135`), `connectors_out` from `out_connectors`
  (`:133`) with `duration_text` (`:68`), `peak` from `site_power` (floats; texts via `num`). EV contributors unchanged.
- Seen texts: §3. EV window days: Site-local date of `lo` and of `hi − 1 µs`.
- Tests (fake ports): every mini/EV text above, plural forms, the reserve count from a dispatch body with mixed
  constraints, and that a failed dispatch leaves MG-4 UNKNOWN. Postgres (reuse `EV_BUILD` from the B4 test module,
  DB `assetops_out_c_ev_test`): board on the E window; assert no PEAK warning (60 of 80 kW, R563); assert
  CONNECTOR_OUT_OF_SERVICE is present exactly when an availability connector has `known_unavailable_seconds > 0`;
  record whether CHARGER_FAULT fires (it cannot: no plan, R569).

### U5 · Early-warning list and estate surfaces · 1.0 d · slice review
Files: new `frontend/src/sites/EarlyWarnings.tsx`; `frontend/src/sites/outcomes.css`; `sites/outcomeBoardClient.ts:42-49,105`;
`estate/estateClient.ts:488`; `estate/findingIndex.tsx:460`; `estate/EstatePortfolio.tsx:618-632` and `PriorityPanel` (`:208`);
`estate/PortfolioOutcomes.tsx:64`; `sites/SiteFindingIndex.tsx:918`; `sites/ColdAssessmentViews.tsx:1255`; `sites/EvFindingIndex.tsx:21`.
- Types: `OutcomeWarning` with exactly the wire keys of §4; `warnings: OutcomeWarning[]` on both bodies;
  `OutcomeIssue.ref: OutcomeRef | string | null`.
- `EarlyWarningList({ warnings, max, showSite }): JSX | null` (mock `outcomes.js:137-140`). Empty → `null`.
  `<div className="oc-warn"><div className="oc-warn-head"><h3>Early warnings · not priced yet</h3>` + an
  `oc-info` `<button type="button" aria-label="About early warnings">i</button>`, then `<ul>`; each `<li>`:
  `<span className="oc-kind {risk|stress|opp}">{badge label}</span>` (reuse `ISSUE_KIND`, `OutcomeBoard.tsx:46-52`,
  export it), `<div><a href><strong>{title}</strong></a><small>{…}</small></div>`. `small` =
  `[showSite ? site_name.split(" ")[0] : null, label of the first MOVES item, seen].filter(Boolean).join(" · ")`.
- Explainer: native `<dialog>` like the board's (same focus trap, Escape, focus return; `OutcomeBoard.tsx`), title
  "Early warnings", the paragraph of §3 verbatim, then a table "Warning | Outcome | What would put a value on it"
  with one row per listed warning: title, first MOVES category label, `price_needs`.
- Port `.oc-warn`, `.oc-warn-head`, list rules from `frontend/mockups/v70/outcomes.css` into `sites/outcomes.css`
  with tokens; 24 px targets; visible focus; 390 px reflow (`overflow-wrap: anywhere`, `min-width: 0`).
- Placement: estate Findings, under the table inside the panel (`findingIndex.tsx:460`), from the estate summary
  of the page's own window; filter All → all, Cost → `lens == "COST"`, Risks → `"RISK"`, Opportunities →
  `"OPPORTUNITY"` (none exist now, so that list renders nothing). Site Findings lists (three): under the list, from
  the Site board, `showSite={false}`; cold/EV pass the page's `from/to/known_at`; mini passes `date` = UTC day of
  `to` (previous day when `to` is midnight, as `read.py:132` `mini_summary_day`). Portfolio: under the ranked table
  in `PriorityPanel`, `max={4}`, `showSite`.
- Portfolio pulse (`EstatePortfolio.tsx:618-632`), new span before `pulse-note`:
  `<strong>{countText(n, "Unknown")}</strong> {n === 1 ? "warning" : "warnings"} not yet priced`, n = summary
  `warnings.length`, shown when 0; "Unknown" when the summary is not loaded. No icon (no new `<svg>`, R570).
- Protect card detail (`PortfolioOutcomes.tsx:64` `PROTECT_DETAIL`): "Service disruptions recorded in Findings ·
  {w} early {warning|warnings}, counted separately · loss not priced", w = summary
  `categories[PROTECT_ASSET].warning_count`; summary not loaded → keep the A text. The value stays the disruption
  count. No Grow card change (idle warning dropped).
- Tests: `frontend/src/sites/__tests__/earlyWarnings.test.tsx` (structure, classes, `max`, showSite, empty → nothing,
  dialog focus, `scanProductVocabulary(root, page, {set: "w1"})`, and a regex `/[$€£]|\b(USD|EUR|GBP|KES|ETB)\b/`
  over `textContent` = no match); extend `estatePortfolio.test.tsx` (pulse incl. 0 and Unknown, card detail, list
  ≤ 4) and the estate/Site Findings tests (lens filters; list absent when empty).

### U6 · Maintenance metric, WR notice, captures, register · 0.75 d · slice review
Files: `frontend/src/work/GlobalMaintenance.tsx:228-262`, `frontend/src/work/WorkRequestOverview.tsx:140-157`,
their tests, `.agent/mock-departure-register.md`, `.agent/OUT-C-captures/`.
- Card 4 (`GlobalMaintenance.tsx:253-259`) is retired and replaced: label "Repeat visits without a result",
  value = number of REPEATED warnings in the estate summary read over the covering UTC days of the page window
  (via `getOutcomeSummary`); note: the first one's "{subject_label} · {count} visits, linked finding still open"
  linked to its `href`, or "None in the last 60 days". Summary refused, still loading, or window over 31 days:
  value "Not assessed" (`word`), note "Repeat visits could not be checked for this window".
  `data-global-work-card="repeat_visits"`. Update the R358 comment and row to "cards 2-3".
- WR notice: in `OverviewPanels` read the Site board for `body.site_code` with **no window** (the board's own default,
  as the Overview page). If a REPEATED warning's `href` ends with this case id, render `<Notice tone="amber">` above
  the pair: "This is the {ordinal} visit to {subject_label} in 60 days, and the linked finding is still open.
  Repeated work without a result costs money; no amount is shown because a cost per visit is not set for this
  site." Ordinals 2 second, 3 third, 4 fourth, 5 fifth; n > 5: "This is visit {n} to …" (same rest). A refused board
  read shows nothing.
- Captures at 1440 and 390 vs v70: GreenHarvest Overview (Cost row open), its Findings list, the latest request
  page (notice), and, if P-C1 passed, Portfolio, estate Findings Cost and Risks lenses and Maintenance on the w502
  `positive` DB; Depot Overview on w504. Record each result in the packet.
- Register rows §8; resolve R541; notes on R08, R10, R358.

## 3. Copy (exact; all scanned, 0 hits)

Titles: "Repeated maintenance without a result" · "{plan title} overdue" · "{plan title} due soon" · "Battery at or
near its reserve" · "Charger fault and overdue inspection" · "Connector {label} out of service" · "Peak close to the
import limit".
Seen: "{asset} visited {n} times in 60 days ({d1}, {d2}, …); the linked finding is still open" · "Planned for {date},
not done" · "Due {date}" · "During {n} of {m} assessed generator {period|periods} on {date}" · "{label} fault
recorded in this window · inspection overdue since {date}" · "{out} out and {unknown} unknown on {date}" (two days:
"between {d1} and {d2}") · "{peak} kW against {limit} kW". Dates "d MMM", then `date_suffix`.
`PRICE_NEEDS`: repeat "A cost per visit is not set for this site" · PLAN_* "Needs repair cost and wear history" ·
battery "Needs a tested battery wear model" · fault "Needs repair cost and fault history" · connector "Needs the
bus roster" · peak "Needs a demand forecast".
Explainer: "An early warning points at something that tends to cost money or shorten equipment life, before its
cost can be worked out. It shows what was seen and how often. It never shows a money figure."
Board, Maintenance, WR and Portfolio strings: as quoted in U2-U6.

## 4. Wire (additions only; schema versions unchanged)

Board `warnings[]` and summary `warnings[]`, each: `key, kind, badge, badge_label, lens, title, seen, persistence,
persistence_label, price_needs, status_effect, categories {policy_version, state, items[]}, site_code, site_name,
href, evidence_refs[{kind, id, label, href}], count, subject_label`. Board `policy_versions.warnings =
"early-warnings/1"`, `catalogue = "outcome-catalogue/2"`. Issues: `kind ∈ {RISK, EARLY_WARNING}`, `ref` = warning
key. Summary `categories[].warning_count`. Never on the wire: `subject`, `visit_ids`.

## 5. Validation tier

| Unit | Focused backend | Frontend |
|---|---|---|
| U1 | `test_out_c_rules.py test_out_c1_never_money.py test_out_a1_outcome_map.py test_out_b1_status.py` | — |
| U2 | `test_out_c2_board.py test_out_b1_board.py test_out_b2_mini.py test_out_b2_vocabulary.py test_out_b3_cold_ev.py test_out_b4_read.py test_out_b4_imports.py test_out_b4_route.py test_out_b4_window.py` | — |
| U3 | U2 set + `test_out_c3_repeat_visits_postgres.py` + `test_out_b4_board_postgres.py::test_cold_w502_positive` | — |
| U4 | U2 set + `test_out_c4_mini_ev.py test_out_c4_ev_warnings_postgres.py` | — |
| U5/U6 | `test_out_b4_route.py` | `npx vitest related --run <changed files>`, `npx tsc --noEmit` |

`tools/check-all.ps1` at every unit commit. Slice end: `python tools/select-tests.py --base main` (it selects the
whole suite because `tools/w502_cold_work_walkthrough.py` changes), so **one full backend run,
`tools\run-backend-suite-in-container.ps1 -Tier all`, idle machine (about 41 min)**, plus full `npx vitest run` once.

## 6. Pre-flight checklist (answer in one batch before code, then stop)

- [ ] Worktree on `e8cf8a36`; `git ls-files --eol | grep "eol=lf" | awk '$2=="w/crlf"'` empty; `.venv` junction.
- [ ] Python `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`; PYTHONPATH =
  `<wt>\backend;<wt>\contracts;<wt>\tools;<wt>\simulator;<wt>\gateway;<wt>\host;<wt>\field`;
  `assetops_backend.__file__` resolves to `-outC`. The host test script may be blocked by execution policy: run
  pytest directly, as B did. `check-all` with `ASSETOPS_GUARD_PYTHON` = that venv. No policy override.
- [ ] Each anchor opens to its symbol (±15 lines is noted, not asked).
- [ ] Vocabulary: `ran running run runs runtime load draft claim candidate necessary binding scenario simulated
  stage fixture cursor projection replay "dispatch interval" "measured intervals"`, case-sensitive `SOC PV PCS`,
  uppercase codes (`COMPLETED`, `OBSERVED`, `CURRENT`…) and any `UPPER_UNDERSCORE` are forbidden on screen. Plan and
  request titles you author must pass too.
- [ ] `<svg>` only in the allow-listed modules (`tools/checks/shell-overflow.ps1:83-92`); C adds none.
- [ ] No `variant` prop on new components.
- [ ] No golden or contract changes are expected (the map is unchanged). If one moves, stop and ask; any
  regeneration goes only through its write flag (e.g. `ASSETOPS_WRITE_W301_GOLDEN`).
- [ ] Register: `grep -c "| R5[6-7][0-9] " .agent/mock-departure-register.md` is 0.
- [ ] P-C1 (U3): estate summary on w502 `positive` over `[D, D+1)`; record the result before U5.
- [ ] B fakes that model the maintenance work port: list them with the change.
- [ ] DB names `assetops_out_c_<x>_test`, dropped by the producer's own `drop` or the test fixture.

**Known failures (merge gate ignores exactly these):** vitest `src/sites/__tests__/w1f4VerificationStructure.test.tsx`
(the 3 tests named in `AssetOpsV1-outA/.agent/OUT-A-packet.md:99-104`). The `coldWorkCases` "W5-02 K3b … Incident
What happened" test flakes under full-run load; it must pass alone. No backend failure is known (the w303 pair is
fixed). Any other failure blocks.

## 7. Acceptance

1. Never-money test passes for every rule; the injected-amount double fails it.
2. Every rule in U1 has its positive and negative test; the 4 OPEN + 3 COMPLETED case gives one warning.
3. w502 `positive`, board on `w501` window: Cost NEEDS_ATTENTION · Cost per cooling unit, headline "3 repair
   visits in 60 days without a result", Earlier 2 × "Did not fix it" + "Not yet verified", Must not harm present
   with the Finding link; Protect lists "Witnessed backup start test overdue" (Early warning) and the coil plan
   "Due soon"; the Portfolio matrix cell (when P-C1 passed) reads Needs attention.
4. w504 `positive`: no PEAK warning; CONNECTOR_OUT_OF_SERVICE iff unavailable time exists.
5. Estate Findings Cost lens lists the repeat warning; Risks lists plan, battery, fault, connector and peak warnings;
   All lists all; Opportunities shows no list (fake summary in vitest; real data only if P-C1 passed).
6. Portfolio pulse "{n} warnings not yet priced" (0 shown); Protect card shows disruptions and warnings as separate
   clauses; no currency or amount in any warning (w1 scan + regex).
7. Maintenance card "Repeat visits without a result" = 1 on w502 positive when P-C1 passed (else vitest only); the
   latest cold request page shows the "third visit" notice.
8. Full backend run, full vitest and `check-all` pass, except the known failures.

## 8. Register rows (R560-R571; R554 stays free for B)

R541 resolved (MG-4, CC-3 measured). New: **R560** D2 title "at or near" (mock "below its reserve") · **R561** D1
generator service due soon not determinable (no hours since service) · **R562** D1 battery seen counts assessed
generator periods on the board day; no reserve %, no 30-day dwell, no lowest % · **R563** D4 peak 60 of 80 kW does
not fire in the capture (mock 76 kW) · **R564** D2 the latest request is under Earlier, not "Already in hand ·
Completed" · **R565** D1 Chargers mostly idle dropped: no rated connector power on any read · **R566** D1 no fault
date on the health read · **R567** D2 asset named by its code ("generator-1"; mock "Backup generator") · **R568** D2
cold Must not harm names every linked outcome (mock names Cooling continuity only) · **R569** D1 EV and mini plan
cues and the charger-fault warning have no demo data (fixed-date fixtures and the 30-day backdate limit); unit tests
only; carried to the combined dataset · **R570** D2 pulse warning count without an icon · **R571** D2 maintenance
visits are read by occurrence over 60 days (three recorded-time windows), not by recorded time over 31 days.

## 9. Review points per unit

- **U1:** purity (AST test green); every rule's bounds half-open as tabled; `@LINKED` minus own key; no money in
  any code path; PRICE_NEEDS closed; sorting deterministic; `source_label` absent.
- **U2:** no port, no `main.py`/composition edit (`test_out_b4_imports.py`); the three windows exactly
  `[to−62,to−31) [to−31,to) [to,to+31)` and the occurred filter; a failed visit read is PARTIAL and CC-3 UNKNOWN; a
  CHECKED warning sets no status; changed B tests listed with reasons, none weakened.
- **U3:** authored writes go through the service with idempotency keys, after the existing reads; no existing manifest
  assertion edited except the new `out_c` block; Postgres asserts the exact texts; P-C1 recorded honestly.
- **U4:** reserve count from `binding_constraints` only (no reason-text parsing); PEAK margin a named constant;
  EV texts never print "None".
- **U5:** list renders nothing when empty; mock structure and classes; dialog focus behaviour tested; 390 px
  reflow; w1 scan and money regex in tests; no new `<svg>`, no `variant`.
- **U6:** card 4 replaced, not a fifth card; fallback never says "Not available yet"; notice only on the warning's
  `href` case; captures and register complete.

## Rulings C, final review (Architect: Claude, `.ai/ROLE_CONFIG.md:9` in `-outC`, 2026-10-30)

Code read at `dd24988a` (`-outC`). Rulings on `OUT-C-review.md` H1, M2, L2 and P-C1. Every new string below was
scanned against `terms` + `w1.terms` + `w1.codes` + the uppercase-code pattern: 0 hits. Register IDs: **R572-R574**
(the rest of C's range) and **R575** (taken from the unallocated sprint reserve R575-R579).

### F1 · One fact carries the mock's wording honestly: `fault_name` (extend; no new read)
The data shows that the open Finding linked by the visits is a `COLD_START_FAILURE` Finding. It does not show a start
attempt after the visits: the authored notes say "automatic start not tested". So the copy may name the fault, but
must not say "still failed".
- `outcomes/warnings.py`: add `WarningFacts.fault_names: Mapping[str, str] = field(default_factory=dict)` (Finding id
  → noun phrase) and `Warning.fault_name: str | None = None`. In `_repeated`, take the warning's open linked ids. If
  every one has an entry and all the entries are equal, `fault_name` is that entry; otherwise it is `"linked finding"`.
  Only the repeat rule sets it.
- `site_outcomes/visits.py`: add `FAULT_NAMES = {"COLD_START_FAILURE": "automatic start failure"}`. `warning_facts`
  fills `fault_names[f.finding_id] = FAULT_NAMES[f.mechanism]` for each open Finding whose mechanism is listed.
- Wire §4 gains **`fault_name`** (string or null; non-null only on REPEATED). Add it to `OutcomeWarning` and to the
  never-money key walk (it is not a money key). Schema versions stay unchanged, because the change is additive.

### H1 · The six v70 mismatches
| # | Ruling | Exact copy / behaviour | Register |
|---|---|---|---|
| 1 | **Match the mock.** | Drop `showSite={false}` on the three Site Findings lists (`SiteAnalyticsFrames.tsx:525,541,555`), so `small` starts with the Site's first word, as `outcomes.js:139` does. Update the U5 test. | none |
| 2 | **Change the copy** (F1); register the remaining difference. | Seen: `"{asset} visited {n} times in 60 days ({d1}, {d2}, …); the {fault_name} is still open"`. Example: "generator-1 visited 3 times in 60 days (14 Aug, 18 Sep, 6 Oct); the automatic start failure is still open". | R572 |
| 3 | **Change the copy** (F1); register. | Cost contributor: `"{n} visits ({dates}); the {fault_name} is still open"`. Subline when `fault_name != "linked finding"`: `"None of the visits has fixed the {fault_name} yet; repair cost is not recorded"`. Otherwise keep `COST_SUBLINE`. The word "yet" keeps the claim true while the latest visit is "Not yet verified". | R572 |
| 4a | **Match the mock** (reuse the Protect option). | `cold.py` `options[COST]` is `(Option(OPTION_START_TEST, start_href),)` when the repeat warning exists **and** `start_failure` is one of its open linked Findings (its FINDING `evidence_refs`); otherwise `()`. It uses the same `start_href` as Protect. | none |
| 4b | **Keep RISK; register.** | The repeat issue badge stays "Risk" on the board and in every list. | R573 |
| 5 | **Change the copy** (F1); register. | `repeatVisitNotice(count, subject, faultName)`: `"{head} in 60 days, and the {faultName ?? "linked finding"} is still open. Repeated work without a result costs money; no amount is shown because a cost per visit is not set for this site."` | R572 |
| 6 | **Match the tone; change the note** (F1); register. | Use `tone="amber"` when the value is a number of 1 or more. Note link: `"{subject_label} · {count} visits, {fault_name ?? "linked finding"} still open"`. Example: "generator-1 · 3 visits, automatic start failure still open". | R572 |

### M2 · Maintenance card 4 (`RepeatVisitsCard`)
A Site counts as **checked** in the loaded summary when `read_state == "AVAILABLE"` **and** its `OPTIMIZE_COST` row
state is neither `UNKNOWN` nor `NOT_MEASURED`. `NOT_MEASURED` counts as unchecked: the EV Cost row cannot show whether
the repeat inputs loaded, and under P-C1 EV Findings are not visible on these windows either. Site names are
`site_name.split(" ")[0]`, joined as "A", "A and B" or "A, B and C". `found` is the number of REPEATED warnings.

| State | Value | Tone | Note |
|---|---|---|---|
| window null, loading or refused | "Not assessed" (word) | none | "Repeat visits could not be checked for this window" (unchanged) |
| loaded, no Site checked, found = 0 | "Not assessed" (word) | none | same as above |
| loaded, some Sites checked, found = 0 | "Partly checked" (word) | none | "None found at {checked}; not checked for {unchecked}" |
| loaded, all Sites checked, found = 0 | "0" | none | "None in the last 60 days" (used only here) |
| found ≥ 1, all Sites checked | n | amber | the H1-6 link |
| found ≥ 1, some Sites unchecked | n | amber | the H1-6 link, then the text " · not checked for {unchecked}" |

Vitest: a cold Site whose Cost row is UNKNOWN never shows "None…". Add one case for each row of the table.
Register **R574**.

### L2 · Mini Protect headline
When no warning moves MG-4 and `reserve` is known with `m ≥ 1`, the headline is
`"Battery stayed clear of its reserve in {m} assessed generator {period|periods}"` (use the `plural` helper). When
`reserve` is None or `m == 0`, keep `PROTECT_HEADLINE`. `PROTECT_SUBLINE` stays as it is; it still says that battery
and generator condition are not assessed. Add the new string to `COPY`. Unit tests: m = 24, m = 1, m = 0 and None.
No register row: this is a data state, and the mock shows only the warning state.

### Also in this round
- **L1:** fix it in this round. Apply the no-double-prefix rule from `warnings.py:246` at `ev.py:168,249`, with a
  unit assertion.
- **L3:** accepted as a reading.
- **L4:** correct the packet.
- **M1:** fix it as the review says.

### Register rows
- **R572** · OUT-C final review H1-2/3/5/6 · cold, wr-overview, maintenance · D3 copy honesty · standing.
  - Mock: "the automatic start still failed" · "fixed the backup generator's automatic start" · "start still failing".
  - Shown: "the automatic start failure is still open" · "has fixed the automatic start failure yet" · "automatic start
    failure still open".
  - Reason: no record shows a start attempt after the visits; the open start-failure Finding is the fact on record.
- **R573** · H1-4b · cold · D2 · standing.
  - Mock: the repeat issue shows as "Early warning" on the board (`outcomes.js:83`).
  - Shown: "Risk" on the board and in the lists.
  - Reason: one warning has one badge everywhere. This follows the mock's own warning entry (`outcomes.js:128`,
    `kind:'risk'`).
- **R574** · M2 · maintenance · D3 · standing.
  - Mock: card 4 always holds a count.
  - Shown: "Not assessed" or "Partly checked", with the unchecked Sites named.
  - Reason: a Site whose repeat check could not be made is never counted as "none".
- **R575** · P-C1 · portfolio, findings, maintenance · D5 build order · open.
  - Mock: the estate surfaces list GreenHarvest's repeat warning and its Cost cell.
  - Shown: on day and week windows, cold and EV Sites compose over a window that no assessed event covers. Their
    Findings, and the warnings that need them, are absent there.
  - Reason: the estate window choice for cold and EV Sites lands in the follow-up slice (P-C1 below).

### P-C1 · Recommendation (owner decision requested)
**Cause.** The cold read selects only a run whose window covers the request (`postgres_assessment_store.py:2036-2042`).
The EV read needs an exact window match (`:2725-2733`). So the Site board sees Findings only on an assessed event's own
window.

**Existing rule to reuse.** The estate already has a rule for this, `selected_windows_on` (`:1923`, W3-01 Run 6/7): every
exact selected window that intersects the period, at its greatest seq, pinned at the cutoff. Evidence and Financials
already use it through `snap.selected_windows` (`estate/coverage.py:210`).

**Options**
- **A (recommended).**
  - Add `site_selected_windows(tenant_id, site_code, from_, to, known_at)` on the estate service, modelled on
    `site_readiness` (`estate/evidence_money.py:495`). It returns `[(window_start, window_end)]` from that rule. The
    `estate` port is already wired, so composition needs no edit.
  - In `summary()`, compose each cold or EV Site on its **latest** intersecting window (max `window_end`, then
    `window_start`). When there is none, keep `[lo, hi)`, which honestly shows Unknown.
  - Add `sites[].window {from, to}` and carry it on `overview_href`, so a cell opens the same window.
  - Effort: about **1.5 builder days** (the method, the summary, the wire, a Postgres test on w502 `positive` and w504,
    and the Portfolio link vitest). The M2 approximation can then become an explicit per-Site repeat-check flag.
- **B.** Compose cold and EV with no window, which is the Site board's own default (the latest selection at the cutoff).
  About 0.25 d. It agrees with the Site default but ignores the period: a 29 Oct Portfolio could show a 6 Oct event.
  Not recommended.
- **C.** Widen the store rule to "intersects". This changes the W2 read under every cold and EV page and invents
  semantics. Rejected.
- **D.** Register only (R575) and leave the gap. 0 d, but the Portfolio still says Unknown where the Site says Needs
  attention.

**Placement:** a separate slice straight after C merges and before the client demo. C's REVISE round stays copy and
register work; option A changes estate read semantics and the summary wire, so it needs its own review.
