### 9m.4 K6b card: `fuel-residual-within-band-1`, the verdict page and the board entry, 1.4 (range 1.25–1.6)

**What K6b delivers.**
- The pure family (`B/actions/fuel_verification.py`): night choice, verdict, outcome rows and client text.
- The plan freeze and the evaluation (service methods, a separate store context, ports, composition).
- The verdict read API and the page `F/sites/SiteFuelResidualVerification.tsx` at its own route, with the Ref kind `FUEL_VERDICT`.
- The chain Action Ref fix (§9m.1 item 6) and the Kisiwa board's Assure "Verified results" entry. **No value line, anywhere (H2).**
- Finish rows **KIS-5** (moved here from K9) and **KIS-10** (new).
- **Not in K6b:** a tick stage (the evaluation is explicit, as K3's assess and K4a's raise are; the after-the-demo list gains "fuel verdict tick stage"), the Portfolio Assure count (K8), the Protect thread line (K4b), and any edit to the mill's methods, columns, wire or page.

**The family (pure; no I/O; `B/actions/fuel_verification.py`).** It imports `reserve_trial`, `verification_rules as rules`, `actions.ports.ActionRefused`, `actions.lifecycle.SYSTEM_DEMO`, `fuel_balance.model` (types only) and `fuel_balance.finding_text` (`litres1`, `short_day`). It never imports `verification_families` (that avoids a cycle), `financials`, `fuel_cost*` or any price module.
```python
FUEL = "fuel-residual-within-band-1"
FUEL_PLAN_VERSION = "fuel-residual-verification-1"
FUEL_LEVER = "fuel-seal-dip-sensor-power@1"          # verification_plan.triggering_fixture (0057 pins it)
FREEZE_COMMAND = "FREEZE_FUEL_VERIFICATION_PLAN"
MIN_NIGHTS, LOOK_NIGHTS = 3, 14
METRIC_KEY = "fuel_residual_night"
EVALUATOR_JOB = "fuel-verification-evaluator"
#: §8.5, verbatim; frozen in the plan; never fitted.
TARGET = {"rule": "every later night: residual_low <= 0 <= residual_high and reporting_gap_minutes == 0",
          "over": "first 3 COMPLETE nights after the change",
          "basis": "owner-reviewed design, fuel-loss-feasibility Part A §3 Verify, chosen 2026-11-07"}
NIGHT_RULE = ("A night counts only when its stored fuel check is assessed (state is not NOT_ASSESSED) and every "
              "generator slot of the night is known (terms.unknown_slots == 0); nights are chosen by data quality "
              "only, never by value.")
BASIS_TEXT = ("SYSTEM_DEMONSTRATION: story-time freeze of a fuel Action's verification plan after its work case is "
              "COMPLETE and linked; no verified human principal exists, so no operator approval is recorded")
TARGET_MET, TARGET_MISS, LATER_SHORT = "TARGET_MET", rules.TARGET_MISS, "LATER_SHORT"
```
- **Later candidates** `later_nights(effective_from, tz) -> list[date]` (14 dates). `d0` = the Site-local date of `effective_from`. If the window start of `d0` (18:00 local on `d0`, as UTC) is earlier than `effective_from`, use `d0 + 1` instead. The candidates are `d0 … d0 + 13`. A window that starts exactly at `effective_from` counts (`>=`).
- **COMPLETE night** `complete(w) -> bool`: `w is not None and w.state != "NOT_ASSESSED" and int(w.terms["unknown_slots"]) == 0`. Gap minutes do **not** affect COMPLETE: a gap is part of the target and fails it.
- **Night passes** `passes(w) -> (bool, reason|None)`: `w.residual_low <= 0 <= w.residual_high` (exact `Fraction`; no tolerance) **and** `w.gap_minutes == 0`. The failure reason is `"BAND"` when the band test fails (checked first), else `"GAP"`.
- **Verdict** `assess(plan, windows_by_date, now) -> dict`. `windows_by_date` = the latest revision per candidate night as known at `now` (`FuelBalanceReadPort.windows(…, d0, d0 + 14, known_at=now)`):
  1. `chosen` = the first 3 candidates, in date order, that are COMPLETE (chosen by grade, never by value).
  2. `closed` = the window end of the 14th candidate (12:00 local on `d0 + 14`) is `<= now`.
  3. If 3 are chosen, or `closed`: if any chosen night fails → `INEFFECTIVE`, `[TARGET_MISS]`, with the sentence naming the **first** failing night; else if 3 are chosen → `VERIFIED`, `[TARGET_MET]`; else → `INCONCLUSIVE`, `[LATER_SHORT]`.
  4. Otherwise: not decided (`NOT_JUDGED`; nothing is stored).
- **Outcome rows** `outcome_rows(plan, result, now, source_class)`, the mill's shape (`verification_families.outcome_rows`):
  - Metrics, PK `(outcome_id, metric_key, window_name)`, all with `METRIC_KEY`:
    - BASELINE: `PASS`, `value` = the baseline range text, `reason` = "night {date}: UNEXPLAINED".
    - LATER: `PASS` if 3 were chosen, else `UNKNOWN`; `value` = `"{n} of 3"`; `reason` = the chosen night dates joined by ", ".
    - COMPARISON: `PASS`/`FAIL`/`UNKNOWN` by outcome; `reason` = `TARGET["rule"]`.
    - `unit` = "L".
  - `basis` = `{plan_id, plan_sha256, rule_id: FUEL, plan_version, target: TARGET, windows_known_at}`.
  - `details` = `{"baseline": {window pin}, "later": [{night_date, window_id, revision, input_sha256, state, residual_low, residual_high, gap_minutes, passes, fail_reason}], "first_fail": date|None, "sentence", "source": {"source_class"}, "look_ahead_closed"}`.
  - `idempotency_key` = `f"fuel-outcome-{plan_id}"`; `actor_id` "service:verification-evaluator"; `triggering_job` = `EVALUATOR_JOB`.
- **Client literals** (all server-composed; the browser formats no number; litres via K4a's `finding_text.litres1`, dates via `finding_text.short_day`):
```python
HEADLINE = {"VERIFIED": "Fuel stayed accounted for", "INEFFECTIVE": "Target not met",
            "INCONCLUSIVE": "Could not conclude", "NOT_JUDGED": "Not judged yet",
            "NO_PLAN": "No verification plan yet"}
VERIFIED_TEXT = ("On {n} fully checked nights after the change, the fuel in the tank matched the generator's "
                 "modelled use and the recorded deliveries within the stated margin, and the tank sensor sent "
                 "readings all night.")
FIXED_LINE = ("This check shows the fuel stayed accounted for after the change; it does not measure how much the "
              "change itself prevented.")                     # H1, §8.2 verbatim; shown in every state
MISS_BAND_TEXT = ("On the night of {date}, after the change, the fuel in the tank did not match the generator's "
                  "modelled use and the recorded deliveries within the stated margin.")
MISS_GAP_TEXT = "On the night of {date}, after the change, the tank sensor did not send readings all night."
LATER_TEXT = "Not judged yet: only {n} of 3 fully checked nights after the change"
LATER_SHORT_TEXT = ("Only {n} of 3 fully checked nights after the change in the 14 nights allowed, so no verdict "
                    "is given")
CRITERION_TEXT = ("3 fully checked nights after the change within the stated margin, with the tank sensor sending "
                  "readings all night")
RULE_TEXT = ("Rule fixed before the check: the first 3 fully checked nights after the change must each stay within "
             "the stated margin, with the tank sensor sending readings all night.")
ACTIVITY_NOTE = "Completed work is evidence of activity, not resolution."     # v69 :502, verbatim
NIGHT_TEXT = "{date} (6 pm to noon)"
RANGE_TEXT = "{lo} to {hi} L"
SENSOR_ALL = "Readings all night"
SENSOR_GAP = "No readings for {m} min"
RESULT_PASS, RESULT_BAND, RESULT_GAP = "Within the margin", "Outside the margin", "Sensor gap"
BASELINE_ROW = "The night of the finding"
BASELINE_RESULT = "Unexplained fuel found"
NOT_CHECKED = "Not checked yet"
CARDS = (("Nights checked after the change", "{n} of 3", "Chosen by data quality, never by result"),
         ("Fuel accounted for", "{k} of {n} nights", "Within the stated margin"),
         ("Tank sensor", "Readings all night on {g} of {n} nights", "A gap is more than 60 minutes without a reading"),
         ("Final outcome", "{headline}", "Decided by the rule fixed before the check"))
LITERALS = (...every string above...)        # scanned by the local guard test and test_out_b2_vocabulary.py
```
  - When `n == 0`, cards 2 and 3 show `NOT_CHECKED` as the value.
  - `{m}` is the stored `gap_minutes`.
  - `{date}` is `short_day(night_date)` ("4 Oct" form).

**Freeze** `VerificationService.freeze_fuel_plan(tenant_id, site_id, domain_action_id) -> (int, dict)`. A service method, with no HTTP route, as the mill's is. In order:
1. `ctx = store.fuel_plan_context(t, s, a)`, a new read in `postgres_action_store.py`. It returns the Action (`id, action_code, title, owner_label, domain, origin_finding_id, origin_finding_revision_id`, Site `timezone`), `applied` (the first COMPLETE `work_event` of a linked case: `id, case_id, occurred_at`, plus the case's `public_code`; the mill's statement) and the existing plan (`FUEL_PLAN_COLUMNS` = `DOMAIN_PLAN_COLUMNS + ", origin_finding_revision_id"`). None → 404 `ACTION_NOT_FOUND` "No such Action for this Site.".
2. If a plan exists → 200 `{"replayed": True, "plan": plan_wire(plan)}`.
3. `domain != "FUEL_BALANCE"` → 409 `VERIFICATION_FAMILY_UNSUPPORTED` "Only an Action raised from an unexplained-fuel Finding has a fuel verification plan."
4. `applied is None` → 409 `VERIFICATION_ACTION_NOT_APPLIED` "A verification plan needs the Action's linked work case to be COMPLETE."
5. Either fuel port is None → 503 `VERIFICATION_FUEL_READ_UNAVAILABLE` "The fuel checks cannot be read."
6. `ff = ports.fuel_findings.fuel_finding(t, s, origin_finding_id, known_at=now)`. If it is None, or the window its origin revision cites cannot be read (the plan cites **the Action's** `origin_finding_revision_id`: read that revision's claim `fuel_balance_window_id`, then `ports.fuel_windows.window(t, s, id)`) → 409 `VERIFICATION_ORIGIN_UNAVAILABLE` "The Action's unexplained-fuel Finding or its night check cannot be read."
7. `effective_from = applied["occurred_at"]` (UTC). **This is the effective-time field: `verification_plan.effective_from`, the linked case's first COMPLETE `occurred_at`** (the mill's anchor, `applied_work_event_id`).
   - `effective_from < baseline.window_end` → 409 `VERIFICATION_EFFECTIVE_BEFORE_BASELINE` "The change is recorded before the end of the night it answers."
8. Compute `later = later_nights(effective_from, tz)`. If `later_start` (the window start of `later[0]`) is `<= now` → 409 `VERIFICATION_LATER_WINDOW_STARTED` "The first night after the change has already begun; the plan must be frozen before it." (pre-registration).
9. Plan row:
   - `rule_id` FUEL; `plan_version`; `domain_action_id`; `origin_finding_revision_id`; `applied_work_event_id`; `effective_from`;
   - `baseline_start`/`baseline_end` = the baseline window's; `later_start` = `later[0]`'s window start; `later_end` = `later_start + 14 days`;
   - `baseline_selection` = `{"state": "COMPLETE", "night_date", "window_id", "window_revision", "input_sha256", "state_found": "UNEXPLAINED", "residual_low", "residual_high", "gap_minutes"}` (exact text); `baseline_evidence_ids []`;
   - `basis` = `{"timezone", "night_rule": NIGHT_RULE, "applied": {work_event_id, case_id, occurred_at}, "origin": {finding_id, revision_id}, "tank_asset_id", "windows_known_at": now}`;
   - `target` = `TARGET`; `guardrails {}`; `bands {}`;
   - `coverage {"min_nights": 3, "look_ahead_nights": 14}`;
   - `later_selection_rule {"rule": "the first 3 COMPLETE nights whose window starts at or after effective_from, at most 14 nights ahead, chosen by grade only at evaluation", "min_nights": 3, "candidates": {"from", "to"}}`;
   - `plan_sha256` = `reserve_trial.sha(content)`; the `SYSTEM_DEMO` actor columns; `authorization_basis` = `BASIS_TEXT`; `triggering_fixture` = `FUEL_LEVER`;
   - `idempotency_key` = `f"fuel-plan-{domain_action_id}"`; `payload` = `{"command": FREEZE_COMMAND, "domain_action_id"}`; `recorded_at` = now.
10. `store.freeze_fuel_plan(t, s, plan)` (the mill's `freeze_domain_plan` body with `FUEL_PLAN_COLUMNS`, the same advisory lock key form `verification-plan:{id}`) → 201, or 200 replayed.

**Evaluate** `VerificationService.evaluate_fuel_plan(tenant_id, site_id, domain_action_id) -> dict`. Mirrors `MiddayShift.evaluate`:
- 404 if there is no context.
- `{"state": "NO_PLAN", "stored": False}` if the plan is missing or not FUEL.
- If an outcome exists → `{"state", "stored": False, "replayed": True, "outcome_id"}`.
- 503 if a port is missing.
- `assess`. If not decided → `{"state": "NOT_JUDGED", "stored": False, "not_judged_text": LATER_TEXT…}`.
- Otherwise `source_class = store.example_source_class(t, s, used_dates, tz, now)`, where `used_dates` = for the baseline night and each chosen night, its `night_date` and `night_date + 1`, sorted and distinct (WD-1m-R2). Then `outcome_rows`, then `store.record_domain_outcome` (shared, unchanged) → `{"state", "stored", "replayed", "outcome_id"}`.

**Summary** `VerificationService.fuel_summary(tenant_id, site_id, domain_action_id) -> dict`. Read-only, the page's only read. A stored outcome is read back, never recomputed; with no outcome, the live `assess` gives the not-judged text. 404 if there is no context; 409 `VERIFICATION_FAMILY_UNSUPPORTED` for a non-fuel Action. Wire, `fuel_summary_wire(ctx, plan, outcomes, live, origin, baseline, site_code)`:
```
{"action_id", "action_code", "title", "owner_label", "rule_id": FUEL,
 "state": VERIFIED|INEFFECTIVE|INCONCLUSIVE|NOT_JUDGED|NO_PLAN, "headline": HEADLINE[state],
 "sentence": VERIFIED_TEXT|MISS_*_TEXT|LATER_SHORT_TEXT|None, "not_judged_text": LATER_TEXT|None,
 "fixed_line": FIXED_LINE, "criterion_text": CRITERION_TEXT, "rule_text": RULE_TEXT,
 "cards": [{"label", "value", "note"}] (4),
 "origin": {"finding_id", "revision_id", "title": finding_text.TITLE, "night_text", "ref": fuel_finding_ref(...), "href"},
 "nights": [{"role": "BASELINE"|"LATER", "label": BASELINE_ROW|NIGHT_TEXT, "range_text", "sensor_text",
             "result_text", "passes": bool|None, "window_id", "revision"}],   # baseline first, then chosen later nights
 "activity": {"case_code", "case_ref": case_ref(...), "case_href", "completed_text": "{d} {Mon} {HH:MM}" Site-local,
              "site_visit_text": the SITE_VISIT body citing the case, or None, "note": ACTIVITY_NOTE} | None,
 "effective_from": ISO, "plan": {"plan_id", "later_candidates": {"from","to"}} | None,
 "outcome": {"outcome_id", "outcome", "reasons", "recorded_at", "source_class"} | None,
 "value": None, "cost_check": None}
```
- `value` and `cost_check` are **always** null (H2).
- No key anywhere in the wire contains `amount`, `price`, `currency` or `money`.
- The SITE_VISIT text is read through the existing Work read port (PRE-FLIGHT (d) names it). It is the first `SITE_VISIT` operational record whose `case_id` is the linked case, as known. If it is absent, the field is None and the row is omitted.

**Ports and composition.**
- `VerificationPorts` (`actions/verification.py:54-72`) gains `fuel_windows: Any = None` (a `FuelBalanceReadPort`) and `fuel_findings: Any = None` (K4a's `FuelFindingReadPort`). Both are implemented by `PostgresFuelBalanceStore`.
- `B/actions/composition.py` gains `build_fuel_verification_service(database_url, *, test_clock=None) -> VerificationService`. It wires the existing verification store builder (PRE-FLIGHT (a) names it), `VerificationPorts(fuel_windows=s, fuel_findings=s)` with `s = build_fuel_balance_store(database_url)`, and `clock = test_clock or <the production clock the API uses>`. The test-only clock is constructor-only (§9d.4 precedent); production never passes it.
- `verification_families.py` gains only, at the bottom: `from assetops_backend.actions.fuel_verification import FUEL, FuelResidual` and `FAMILIES[FUEL] = FuelResidual()`, where `FuelResidual` is a frozen dataclass (`rule_id`, `plan_version`, `owner="domain_action"`). `family_of` then knows the family.

**API** (`B/action_api.py`, beside the mill's `:315`): `GET /api/sites/{site_code}/domain-work/actions/{action_id}/fuel-verification` → `{"access_basis", **verification.fuel_summary(...)}`, through the same `run(...)` error mapping. The router's verification service is built with `build_fuel_verification_service` (or the existing one gains the two ports; PRE-FLIGHT (b)).

**Ref kind and route.**
- `B/chain/refs.py`: `KINDS` gains `"FUEL_VERDICT"`. `href_for` gains `if kind == "FUEL_VERDICT": return f"{_site(ref)}/domain-actions/{_seg(ref['id'])}/fuel-verification"`. New constructor `fuel_verdict_ref(site, action_id) -> _ref("FUEL_VERDICT", site=site, id=str(action_id))`. It joins every validator the kinds list feeds (PRE-FLIGHT (c)).
- `F/sites/chainRef.ts` gains `| { kind: "FUEL_VERDICT"; site: string; id: string }`. `F/shell/operatorSiteRoutes.ts` gains ``SITE_FUEL_VERIFICATION_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/domain-actions/:actionId/fuel-verification` ``, `siteFuelVerificationHref(siteId, actionId)`, and `case "FUEL_VERDICT": return siteFuelVerificationHref(r.site, r.id);`. `F/App.tsx` registers the route beside `SITE_MILL_VERIFICATION_ROUTE_PATH` (`:501`), with a `SiteFuelVerificationFrame` in `F/shell/SiteAnalyticsFrames.tsx` (the mill frame's pattern, `:2600-2620`).
- **`fuel_finding_ref` (the origin link, §9l.4).** If K5 phase B has merged, import it. If not, K6b adds `FUEL_FINDING`, `fuel_finding_ref`, `siteFuelFindingHref` and `SITE_FUEL_FINDING_ROUTE_PATH` **exactly as §9l.2 specifies** (`refs.py` per `:3139`; frontend per `:3168-3177`), and whichever of K5 and K6b merges second takes main's copy. Until K5's page merges, the origin link has no page (Kisiwa is opt-in until K7-F, so no default prepare shows it).

**Chain Ref fix.**
- `postgres_chain_read.py` `_SITE_ACTIONS` gains `CASE WHEN a.kind = 'DOMAIN_INTENT' THEN (SELECT d.domain FROM domain_action d WHERE d.tenant_id = a.tenant_id AND d.id = a.id) END AS action_domain`. Nothing else in the statement changes.
- `site_chain.action_wire_ref` gains, after the mill branch: `if a["kind"] == "DOMAIN_INTENT" and a.get("action_domain") == "FUEL_BALANCE": return refs.fuel_verdict_ref(site, a["action_id"])`. Docstring: "DIESEL-1-R3m: a fuel Action has no Action page; its Ref is the fuel verdict page."

**The board entry (Kisiwa Assure "Verified results").**
- `site_chain.fuel_verdict_actions(rows, *, site, cutoff, lo, hi)` is `opportunity_actions` with three differences:
  - the filter is `kind == "DOMAIN_INTENT" and action_domain == "FUEL_BALANCE"`;
  - the thread occurrence tested against `[lo, hi)` is one with a `finding_id`;
  - it returns `{action_id, code, thread_id, outcome (known by cutoff, else None), outcome_recorded_at, source_class, ref}`.
- `B/site_outcomes/board.py` gains `@dataclass(frozen=True) class FuelVerdictFact: action_id, code, thread_id, outcome, verdict_ref, source_class=None`, and the facts dataclass that holds `opportunity_actions` gains `fuel_verdicts: tuple[FuelVerdictFact, ...] = ()`.
- `B/site_outcomes/mini.py`:
  - builds `fuel = tuple(FuelVerdictFact(...) for a in site_chain.fuel_verdict_actions(ct.rows, site=c, cutoff=ct.k, lo=work_lo, hi=end))` beside `opp` (`:440-445`; an empty tuple when `ct is None`);
  - passes `fuel=fuel` to `_assure`, which merges it into the same code-ordered list and renders it as the `OpportunityActionFact` branch does: `VERIFICATION_TEXT[s].format(code=…, suffix=provenance_suffix(source_class))`, `PENDING_CHIP` when not judged, link `verdict_ref`;
  - **`_verified_values` is not given `fuel` and its signature does not change** (H2, structural).
  - The comment at the merge reads: `# MOCK DEVIATION MD-FUEL-K6-5 (DIESEL-1-R3m): as MD-FUEL-MB1-1, a fuel Action has no Action page; its Verified results entry opens its verdict page (FUEL_VERDICT). It carries no value line (H2).`
- On Kobo, Cold and EV no `FUEL_BALANCE` Action exists, so their boards and goldens are byte-equal (test B6).
- **Lane note:** K4b also edits `mini.py` and `board.py` (Protect). The edits are disjoint; whichever merges second merges main.

**The verdict page `F/sites/SiteFuelResidualVerification.tsx` (new) and `F/sites/fuelVerificationClient.ts` (new; the mill client's shape, `GET …/fuel-verification`, 404 → `not_found`).**
- Layout follows v69 `verification` (`frontend/mockups/v69/index.html:498-503`), top to bottom, with the existing `ui` components (`Panel`, `DataTable`, `Badge`) and the W1 verification card classes (`verificationCards.tsx` / `w1f4-verification.css`). No new CSS unless a class is missing; then add it in the page's own CSS file.
  1. **Status line:** `Badge` "{action_code} · {headline}", and the subtitle "{action_code} · source: {origin.title}, {origin.night_text} · owner: {owner_label}" (v69 `:503` `subtitle` form).
  2. **Header** (v69 `mheader`): Owner = `owner_label`; State = `headline`; Source = `origin.title` linked by `routeFor(origin.ref)`; Success criterion = `criterion_text`.
  3. **Four cards** from `cards` (v69's four `metric` cards).
  4. **Panel "Target evaluated night by night"** (v69 "Target and guardrails evaluated together"): a `DataTable` with columns "Night", "Role", "Unexplained fuel range", "Tank sensor", "Result". Rows come from `nights`. Role is "Before the change" for the baseline row and "Target" for the others. The panel note is `rule_text`.
  5. **Pair:** "Activity evidence" (v69 `:502`): Maintenance request = `case_code` linked by `routeFor(case_ref)`; Completed = `completed_text`; Site visit = `site_visit_text`; then the note `ACTIVITY_NOTE`. "Outcome evidence": `sentence` or `not_judged_text`, then **`fixed_line` in every state**.
  6. The `mock-deviation-line` paragraph listing MD-FUEL-K6-1 to -4.
- **States:**
  - loading: "Loading the fuel check." (`FUEL_LOADING`);
  - not found: "No such Action for this site." (the mill's `MILL_NOT_FOUND` literal, imported);
  - error: the server's message.
- **Header comment, MOCK DEVIATIONs** (each also in the packet's "Mock to new"):
  - `MD-FUEL-K6-1`: v69 `:501` evaluates one target **with guardrails**. The fuel check has one target and no guardrails (`guardrails = {}`, the BL-09/SCOPE-1 mill precedent), and its table lists nights, not metrics.
  - `MD-FUEL-K6-2`: v69's four cards (`:500`: target change, reserve breaches, critical service, final outcome) become nights checked, fuel accounted for, tank sensor and final outcome. **There is no money card and no "Realized savings"** (H2).
  - `MD-FUEL-K6-3`: v69's "Provisional target pass" badge is not shown. A night is either checked or "Not checked yet", and an undecided check reads `LATER_TEXT`.
  - `MD-FUEL-K6-4`: v69's "Outcome evidence" prose and its "Review a complete evidence example" button are replaced by the server's sentence and the fixed H1 line.
  - `MD-FUEL-K6-5` is on the board (above).
- **Layout evidence:** captures at 1440 and 390 of the VERIFIED state (the K6b L2 data, read-only `serve` on `assetops_k6_test`), plus NOT_JUDGED from a fixture. Height cap: the page fits 1440×1800 with three later nights. The K8 all-26 recapture adds this page.

**Finish rows** (pure logic in `T/demo_combined_rows.py`, wired in `T/demo_combined_finish.py` after KIS-4; each has an L0 self-test with pass and fail bodies; they run at E3):
- **KIS-5 (moved from K9 to K6b):** for the Kisiwa `FUEL_BALANCE` Action:
  - each pinned window in the outcome's `details` (baseline and later) is read back by `window(id)` and equals its pin (revision, `input_sha256`);
  - the later pins are exactly the first 3 COMPLETE candidates as known at the outcome's `recorded_at` (re-run `later_nights` + `complete`);
  - `fuel_verification.assess` over those windows gives the stored outcome and reasons. **The verdict is recorded as computed**; INEFFECTIVE or INCONCLUSIVE pass the row if they reproduce;
  - the served summary has `value is None`, `cost_check is None`, no money key, and `fixed_line == FIXED_LINE`.
- **KIS-10 (new): fuel verification coherence.**
  - `plan.recorded_at < later_start` (frozen before the first later night);
  - `effective_from` equals the linked case's first COMPLETE `occurred_at`;
  - `plan.origin_finding_revision_id` equals the Action's;
  - the baseline window id equals the origin revision's claim `fuel_balance_window_id`;
  - the Action's chain thread equals the Finding's `UNEXPLAINED_FUEL` thread;
  - the Kisiwa board on the outcome's Site-local day + 1 lists a Verified results entry whose text starts with the Action's display code and whose Ref is `FUEL_VERDICT`;
  - no Kisiwa board `verified_values` entry or Portfolio value line names this Action.

**Tests (localised; no full suite).** Each "must fail" names the mutation the reviewer applies to a scratch copy.
- **L0 `backend/tests/test_k6b_fuel_verification_rules.py` (no DB):**
  1. **`later_nights`:** effective 12:05 UTC (15:05 in Dar es Salaam) gives the same local date first; 18:30 local gives the next date; exactly 18:00 local gives the same date. Must fail if `>=` becomes `>`.
  2. **Choice:** NOT_ASSESSED and `unknown_slots > 0` nights are skipped; a COMPLETE failing night before two passing ones is chosen, which gives INEFFECTIVE. Must fail if the choice filters on `passes`.
  3. **Verdict table:**
     - 3 passes → VERIFIED with `VERIFIED_TEXT` ("On 3 fully checked nights …").
     - A band failure → INEFFECTIVE, `MISS_BAND_TEXT` naming the first failing night; a gap failure → `MISS_GAP_TEXT`; band and gap together → band.
     - `residual_low == 0` passes; `residual_high == 0` passes; `residual_low == Fraction(1, 10**6)` fails (must fail if any tolerance is added); EXCESS (`residual_high < 0`) fails.
     - 2 nights and open → NOT_JUDGED; 2 nights and closed → INCONCLUSIVE `LATER_SHORT_TEXT`; closed with a failing night → INEFFECTIVE.
  4. **Literals:**
     - `FIXED_LINE` equals §8.2 H1's text byte for byte;
     - every literal passes guard V's terms, the upper-case code pattern and the H4 words;
     - no literal contains a currency code, `$` or "price".
  5. **H2 static:** an AST check of `fuel_verification.py` shows no import of `financials`, `fuel_cost`, `fuel_cost_v2` or any `price` module. A fully populated `fuel_summary_wire` has `value is None`, `cost_check is None` and no key matching `amount|price|currency|money` at any depth. Must fail if a value line is added.
  6. **Outcome rows:** the three metric windows, reasons, pins, the idempotency key, and `source.source_class` in `details` (never in `basis`).
  7. **Board:**
     - `_assure` with a VERIFIED `FuelVerdictFact` gives "{code} verified on example data" (`source_class` example) with the `FUEL_VERDICT` Ref;
     - with no outcome it gives "{code} not yet verified" and `PENDING_CHIP`;
     - `inspect.signature(mini._verified_values)` is unchanged.
     - Must fail if `fuel` is passed into `_verified_values`.
  8. **Refs:** `href_for(fuel_verdict_ref("KISIWA-001", id))` = `/sites/KISIWA-001/domain-actions/{id}/fuel-verification`; `action_wire_ref` gives `FUEL_VERDICT` for a `FUEL_BALANCE` row, `DOMAIN_VERDICT` for the mill and `ACTION` for a Cold row.
  9. **KIS-5 and KIS-10 self-tests:** one pass body, and one fail body per item.
- **L2 `backend/tests/test_k6b_fuel_verification_postgres.py`, own `assetops_k6_test`.** The test builds:
  - synthetic K3 windows (test clock) for night N (UNEXPLAINED) and nights N+2, N+3, N+4 (WITHIN_MARGIN, gap 0);
  - the Finding through K4a's `raise_night`;
  - the Action through K6a's `create_action`;
  - the case with its record, COMPLETE and link.

  Then:
  1. **Freeze:** at an instant before N+2's window start → 201. The row's columns match the spec, `effective_from` equals the COMPLETE `occurred_at`, and a retry → 200 replayed. A second Action frozen after N+2's start → 409 `VERIFICATION_LATER_WINDOW_STARTED`. A mill Action → 409 `VERIFICATION_FAMILY_UNSUPPORTED`. Before COMPLETE → 409 `VERIFICATION_ACTION_NOT_APPLIED`.
  2. **Evaluate:** before night N+4 is known → NOT_JUDGED, with no outcome row. After → VERIFIED stored with three metrics; a retry → replayed. A WITHIN_MARGIN → UNEXPLAINED revision of N+3 appended after the outcome does not change the read-back. A separate DB state with N+3 set to a gap of 90 min → INEFFECTIVE, `MISS_GAP_TEXT`.
  3. **API** (TestClient): GET `…/fuel-verification` → 200 with the wire. An unknown id → 404. A mill Action → 409. The mill route on the fuel Action → 409 (its existing literal).
  4. **Chain:** after `run_threads`, `_SITE_ACTIONS` gives `action_domain = 'FUEL_BALANCE'`, and the thread detail's Action entry carries the `FUEL_VERDICT` Ref.
  5. **The mill path stays byte-equal:** `freeze_domain_plan`/`evaluate_domain_plan`/`domain_summary` outputs for the CH-9b fixture equal their pins taken **as the branch's first commit**.
  6. **Board goldens:** Kobo, Cold and EV board goldens are byte-equal. Must fail if `_SITE_ACTIONS` drops a row or reorders.
- **Frontend `F/sites/__tests__/fuelVerification.test.tsx`:**
  - each state renders from a fixture wire;
  - `fixed_line` is present in all five states;
  - no "$", currency code or "price" text appears;
  - the origin link resolves `routeFor({kind: "FUEL_FINDING", …})` and the case link `routeFor({kind: "CASE", …})`;
  - `routeFor({kind: "FUEL_VERDICT", …})` and the `linkRefs` round-trip work;
  - the MOCK DEVIATION line is present;
  - the page text passes the existing product-vocabulary scan helper.
- **Must stay green unchanged:** `test_ch9b2_*`, `test_ch9b3_*`, `test_mv1_*`, `test_mb1*`, `test_pv1*`, `test_wd1m*`, `millVerification.test.tsx`, K4a's and K6a's tests, and both probe `--check`s. Any behaviour edit is stop S-b5.
- **Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1`, `tools\check-agent-workflow.ps1` and `tools\check-navigation-truthfulness.ps1` (new route), run directly, with no `-ExecutionPolicy`.

**Files (approved list; anything else is stop S-b4).**
1. `B/actions/fuel_verification.py` (new); `B/actions/verification_families.py` (the bottom registration only); `B/actions/verification.py` (the ports and the three fuel methods only); `B/actions/adapters/postgres_action_store.py` (`FUEL_PLAN_COLUMNS`, `fuel_plan_context`, `freeze_fuel_plan`); `B/actions/composition.py`; `B/action_api.py` (one route).
2. `B/chain/refs.py`; `B/chain/adapters/postgres_chain_read.py` (`_SITE_ACTIONS`); `B/chain/site_chain.py`; `B/site_outcomes/board.py`; `B/site_outcomes/mini.py`.
3. `F/sites/SiteFuelResidualVerification.tsx`, `F/sites/fuelVerificationClient.ts` (new); `F/sites/chainRef.ts`; `F/shell/operatorSiteRoutes.ts`; `F/shell/SiteAnalyticsFrames.tsx` (the frame only); `F/App.tsx` (one route); the K5 `FUEL_FINDING` items only if K5 has not merged.
4. `T/demo_combined_rows.py`, `T/demo_combined_finish.py` (KIS-5, KIS-10).
5. Tests: the L0, L2 and frontend files above, their pins module, and `backend/tests/test_out_b2_vocabulary.py`.

**PRE-FLIGHT (no code first; batch every question in one message).**
- (a) The builder of the verification store and the production clock the action API uses (file:line).
- (b) How `action_api.py` obtains its `VerificationService`, and whether adding the two ports there changes any existing route's wire.
- (c) Every validator fed by `refs.KINDS` (backend and frontend), and any JSON schema of Refs.
- (d) The Work read that gives a case's `SITE_VISIT` operational records with `case_id` (K2's store), and whether `actions` may import it (architecture guard).
- (e) Whether the architecture guard allows `actions` → `fuel_balance` imports (`model`, `finding_text`, `composition`). If not, that is stop S-b3.
- (f) The chain lifecycle's handling of a `verification.outcome` event on an `UNEXPLAINED_FUEL` thread (`chain/lifecycle_run.py`, `config/chain/thread-lifecycle-v1.json`): does it raise for a mechanism with no `clean_day_measures`? If it raises, that is stop S-b6.
- (g) Whether any board or chain golden compares `_SITE_ACTIONS` row dicts exactly (the new key).

**Stops (report to the Architect; never design around them).**
- **S-b1** any mill method, column list, wire, page or golden would change.
- **S-b2** a money field, value line or price read is needed anywhere on the fuel path (H2).
- **S-b3** PRE-FLIGHT (e) forbids the import.
- **S-b4** a file outside the list, or a Kobo, Cold or EV served byte or golden changes.
- **S-b5** an existing test needs a behaviour change.
- **S-b6** PRE-FLIGHT (f) shows the lifecycle raises.
- **S-a6b** guard V, the H4 scan or the navigation-truthfulness guard flags a K6b literal or route.
- **S-b7** more than 1.6 units.

**Dependencies, start, branch, DB, size.**
- **Needs K4a and K6a merged** (0057 and the fuel Action). Not K4b, K5 or K7.
- **What can start earlier:** `fuel_verification.py` with its L0 tests, and the page with its fixture tests. They need only K3's types (on main) and K4a's `finding_text` (on main once K4a merges). A builder may begin them on the K6b branch from main as soon as K4a merges, while K6a is in review.
- Branch `task/DIESEL-K6b-fuel-verification`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k6b`, from main after K4a merges. `git merge main` after K6a merges, before L2. Opus does the first build and the first review. `git add -f` of explicit paths; never rebase.
- **DB: only `assetops_k6_test`** (and its harness clones). Never `assetops_demo3_full_test` or any other DB. No prepare, tick or suite. `serve` only read-only on `assetops_k6_test`, for the layout captures.
- **Size 1.4** (range 1.25–1.6):

  | Item | Units |
  |---|---|
  | Pure family and literals | 0.3 |
  | Service, store context and freeze, ports, composition, API | 0.25 |
  | Ref kind, chain Ref fix, board entry | 0.15 |
  | Page, client, route, frame | 0.3 |
  | KIS-5, KIS-10 | 0.1 |
  | Tests (L0, L2, frontend) and captures | 0.25 |
  | Pre-flight and packet | 0.05 |
- **Reading budget:**
  - this §9m.1 and §9m.4; §8.2 (H1–H5); §9d.5; §9j.4–§9j.7;
  - `actions/verification_families.py`; `actions/verification.py:40-80`, `:350-420`;
  - `actions/adapters/postgres_action_store.py:60-90`, `:740-850`;
  - `0052_verification_plan_domain.py`; `0019_verification_core.py:40-240`;
  - `chain/refs.py`; `chain/site_chain.py:120-185`; `chain/adapters/postgres_chain_read.py:80-101`;
  - `site_outcomes/board.py:180-210`; `site_outcomes/mini.py:430-460`, `:1030-1100`;
  - `F/sites/SiteMillVerification.tsx`, `F/sites/millVerificationClient.ts`; `F/shell/operatorSiteRoutes.ts:360-380`, `:580-600`;
  - `frontend/mockups/v69/index.html:498-503`;
  - K4a's `fuel_balance/finding_text.py` and `model.py`.

### 9m.5 Effects on K7 (K7-D step 5 and K7-F's freeze step)

- **K7-D, §9l.3 step 5, "The Action":** the body's `"domain": "MINI"` becomes **`"domain": "FUEL_BALANCE"`**. Nothing else changes: the keys `origin_finding_id`/`origin_finding_revision_id` (PRE-FLIGHT (b) is answered: `domain_action.py:283-294`; the domain is checked at `domain_intent.py:104`), the title, `owner_label` "Site lead", `raised_at` `S−5d 13:00`, `idempotency_key` "kisiwa-fuel-action", and the domain store's clock at `raised_at`. Full call:
  ```python
  domain._store.test_db_clock_override = lambda: at(action["raised_at"])          # S-5d 13:00
  status, act = domain.create_action(tenant_id, site_id, "KISIWA-001", {
      "domain": "FUEL_BALANCE", "origin_finding_id": <night-4 Finding id>,
      "origin_finding_revision_id": <its SUPPORTED revision id>, "title": action["title"], "owner_label": "Site lead",
      "due_at": None, "raised_at": wire(at(action["raised_at"])), "actor": dict(ACTOR),
      "idempotency_key": "kisiwa-fuel-action"}, PRINCIPAL)                        # expect 201
  ```
- **The remaining step-5 calls stand as K7-D chose them,** following `T/demo_combined_mill.py:126-184`:
  - `work.create_case` `MAINTENANCE_REQUEST` (`asset_id` None, `finding_links []`, `action_links []`, the request title and narrative, key `kisiwa-fuel-request`), with a `StepClock` from `S−5d 13:10`;
  - `post_event` `ASSIGN` to "Site lead", occurred `S−5d 13:20` (key `kisiwa-fuel-assign`);
  - with a second `StepClock` from `S−4d 12:10`: `post_record` (`activity`, occurred `S−4d 12:00`, key `kisiwa-fuel-record`), then `post_event` `COMPLETE` occurred `S−4d 12:05` (`maintenance_record_id`, key `kisiwa-fuel-complete`);
  - the `SITE_VISIT` operational record (occurred `S−4d 12:00`, recorded `S−4d 12:15`, `case_id` = the request, key `kisiwa-kis-sealed-1`);
  - then `post_case_link` with the case's head revision and its latest event by `recorded_at`, with the domain clock at `S−4d 12:20` (key `kisiwa-fuel-link`).
  - **Stop S-7 is cleared once K6a merges.** K7-D merges main after K6a, then builds the Action step. If `create_action` still refuses, that is a K6a defect: report it, never work around it.
- **K7-F, "The freeze step" (§9l.3), now exact:**
  ```python
  from assetops_backend.actions.composition import build_fuel_verification_service
  svc = build_fuel_verification_service(url, test_clock=lambda: at(story["kisiwa"]["plan"]["freeze_at"]))  # S-4d 12:30
  status, frozen = svc.freeze_fuel_plan(tenant_id, site_id, UUID(action_id))      # expect 201
  svc = build_fuel_verification_service(url, test_clock=lambda: at(story["kisiwa"]["evaluate_at"]))       # S-1d 13:00
  judged = svc.evaluate_fuel_plan(tenant_id, site_id, UUID(action_id))            # {"state", "stored", "replayed", "outcome_id"}
  summary = svc.fuel_summary(tenant_id, site_id, UUID(action_id))
  ```
  - **The effective-time field is `verification_plan.effective_from`** (`frozen["plan"]["effective_from"]`): the linked case's first COMPLETE `occurred_at`, which on K7's calendar is **`S−4d 12:05`** (15:05 local), the resolved `action.complete_at`. K7's `action.effective_at` (`S−4d 12:00`) stays the physical change instant: the record, the site visit and run 6's start. The two differ by 5 minutes, and both precede night 6's window start (`S−4d 15:00` UTC, 18:00 local). The night partition is unchanged.
  - K7-F asserts, as stop S-6 on failure: `status == 201`; `effective_from == iso(resolve(complete_at))`; `effective_from < night 6 window_start`; `later_selection_rule.candidates.from == night 6's local date`; `baseline_selection.window_id` = night 4's window id. It records `judged["state"]` **as computed** (VERIFIED, INEFFECTIVE or INCONCLUSIVE; a NOT_JUDGED there is stop S-6) and `summary` in `kisiwa.json`. It never asserts a verdict.
  - **Story link and form** (K7-F): "KISIWA-001 fuel verification": `/sites/KISIWA-001/domain-actions/{id}/fuel-verification`. `LINK_FORMS` gains `"/sites/KISIWA-001/domain-actions/"`.
  - KIS-9 (e)'s K7-F half reads `plan.recorded_at == freeze_at` and an outcome `recorded_at == evaluate_at`.
  - K7-F's size is unchanged (0.5): these calls were its "K6 wiring" item.
- **K9:** KIS-5 has moved to K6b, so K9's size is unchanged. KIS-10 runs at E3 with the other rows.
- **K8:** the Portfolio Assure **count** includes the Kisiwa fuel verdict (as §8.4 said), read from the board's Verified results entry. **There is no Portfolio value line for it (H2).** K8's all-26 recapture adds the fuel verdict page.
- **After-the-demo list (coordinator):** "fuel verdict tick stage (the evaluation is explicit in v1)"; "list fuel Actions on a Site Actions surface".

### 9m.6 Sizes, critical path, tripwire, date

- **K6 = K6a 0.6 + K6b 1.4 = 2.0** (§9.5 had 1.5). The +0.5 covers:
  - the S-7 origin work (a new Action domain and its selection check, §9m.1 items 1–4), about 0.4 of K6a, which §8.4 did not foresee;
  - the chain Ref fix (item 6);
  - the v69-shaped page in place of a single panel.

  It is reported, not absorbed (the contingency is spent, §9h.8). **Kisiwa total: 18.3 → 18.8.**
- **Critical path:** spent 3.65 (F0r, K1, K3) → K4a 1.5 → K6a 0.6 → K6b 1.4 → K7-F 0.5 → K8 captures 0.25 → K9 1.0 ≈ **8.9 lane-units**. That is up from R3l's 8.4 and **below the 9.75 tripwire, with about 0.85 of headroom. No cut, and no owner question.**
  - If K6b's pure module and page start while K6a is in review (§9m.4), about 0.3 overlaps and the path is about 8.6.
  - **Watch item:** the headroom is now the smallest it has been. If K6a ends above its 0.8 stop, or K6b above its 1.6 stop, together adding more than 0.85, the Architect re-rules before K7-F and puts the cut question to the owner. The first candidate stays as named before: drop the verdict **page and board entry** (K6b's 0.45 of UI), keeping the stored verdict and KIS-5; the second is dropping K6 entirely.
- **Lanes:**
  - lane 3 runs K4a (finishing) → K6a → K6b → K7-F;
  - K7-D (lane 2 / the fourth builder) builds its Action step after K6a merges, at about t≈K4a+0.6. It keeps its float, because it must merge before K7-F starts, about 2.0 later;
  - lane 1 (K5 → K4b → K8) is unchanged and shares `mini.py`/`board.py` with K6b (disjoint edits).
- **Demo date:** about **+3.4 working days** (range 2.9–5.4) against the plan without Kisiwa, up about 0.15 day from R3l's +3.25 (0.5 lane-unit on the critical path at about 3 lane-units a day).
- **Machine time:** unchanged (K6 adds no prepare; two L2 files on `assetops_k6_test` when the machine is idle).
- **Plan HTML rows (coordinator):**
  - **Build-units table:** the DIESEL-1-R3 row becomes **18.8**, with "K6 2.0 (K6a 0.6, K6b 1.4)".
  - **Lanes figure:** lane 3 strip K4a → K6a → K6b → K7-F.
  - **Rulings table:** add "DIESEL-1-R3m: K7-D stop S-7 ruled: fuel Finding raises a `FUEL_BALANCE` domain Action (0057 widens the domain CHECK; MINI unchanged); fuel selection = latest SUPPORTED revision; K6 split K6a/K6b; family `fuel-residual-within-band-1` in 0057; effective time = linked case COMPLETE `occurred_at`; fuel verdict page at its own route (FUEL_VERDICT); Assure entry without value line (H2); KIS-5 to K6b, KIS-10 new; Kisiwa 18.8; path about 8.9".
  - **After-the-demo list:** the two items in §9m.5.

### 9m.7 Owner questions

None.

For the owner's information, in plain words:
- **Why the fix needed a small change first.** The system only let a finding about the generator, the cold room or the chargers start an action. The new "unexplained fuel" finding could not, so the builder correctly stopped. We now add a fuel-specific kind of action ("seal the tank cap, sign the dip log, protect the sensor's power"). Kobo's mill action and the cold-room and charger actions stay exactly as they are.
- **What the check says.** After the fix, the system looks at the first 3 fully checked nights. If on each of them the fuel stayed inside the stated margin and the tank sensor sent readings all night, it says the fuel stayed accounted for. It always adds: "This check shows the fuel stayed accounted for after the change; it does not measure how much the change itself prevented." It shows no money, and it never says the fix stopped a loss.
- **The result is whatever the data says.** The nights are chosen by data quality before anyone looks at the result. If a night fails, the page says so.
- **Cost.** About half a unit more than planned, all on the longest chain of steps. The demo moves by about 0.15 of a working day. We are still inside the limit we set for that chain, with less room to spare than before.

## 9n. Ruling DIESEL-1-R3k2: K4a review FIX, M1 (a window that returns to an earlier digest) and L1/L2

- Architect: Claude, 2026-11-08. Binding: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Review: `.agent/review-K4a.md` on `task/DIESEL-K4a-unexplained-fuel-finding` at `979c9da3e` (FIX, M1 reproduced on `assetops_k4_test`).
- **M1 is accepted as a gap the spec caused.** §9j.4 relied on two unique constraints. One of them, `finding_revision_basis_unique`, was dropped in `0015_finding_returning_basis.py`. The other, `analytic_run_basis_unique` (`0007:64`), makes the run unique per digest, not per window revision. **This ruling replaces §9j.4's two "Idempotent" sentences** (the persist bullet and "Re-running with the same window writes nothing").

### 9n.1 Fix (K4a fix round; same files, no new file)

1. **`PostgresAssessmentStore.fuel_balance_persist`** (`B/analytics/adapters/postgres_assessment_store.py:1508-1530`):
   - Keep the first check unchanged: if an `assessment_revision` already exists for `(site, 'fuel-balance-1', "{tank}:{night}", window.revision)`, return it.
   - **Then reuse the run:** `SELECT id FROM analytic_run WHERE site_id = :s AND analytic_id = 'fuel-balance-1' AND model_version = 'fuel-balance-1/v1' AND window_start = :ws AND window_end = :we AND input_sha256 = :b` (the exact `analytic_run_basis_unique` key).
     - If a run is found, use its id. Do not insert into `analytic_run` or `analytic_run_evidence`.
     - Otherwise insert both, as now.
   - **Always** insert the new `assessment_revision` (`revision_no = window.revision`, `result` naming *this* window's id) and its `analytic_run_assessment` row, citing that run. `analytic_run_assessment`'s PK `(run_id, assessment_revision_id)` (`0007:112`) allows one run for several revisions.
   - Docstring: "Idempotent per window revision. A window revision whose digest an earlier revision of the same night already had cites that earlier run (`analytic_run_basis_unique`, 0007:64): same digest, same inputs (DIESEL-1-R3k2)."
   - **Run evidence must match.** When a run is reused, its `analytic_run_evidence` set must equal `window.evidence_ids`. If it differs, raise `RuntimeError("fuel-balance-1 run reused with a different evidence set")`. Never insert into the run to make them agree. If this ever fires in a test, that is stop **S10**.
2. **`PostgresFindingStore._insert_fuel_revision`** (`B/analytics/adapters/postgres_finding_store.py:789-791`):
   - The replay guard compares with the Finding's **latest** revision only, which has been the house rule since 0015 (`_insert_revision`):
     ```sql
     SELECT basis_sha256, transition FROM finding_revision WHERE finding_id = :f ORDER BY revision_no DESC LIMIT 1
     ```
   - It returns None only when both values equal `(window.input_sha256, transition)`.
   - Comment: `# DIESEL-1-R3k2: latest revision only (0015 LR-01 rule); a basis that returns after another revision is a new revision.`
3. Nothing else changes: the lifecycle table in §9j.4, `fuel_transition`, the service, the consequence writer, and the R3k filters all stay as they are.

### 9n.2 Tests (added to `backend/tests/test_k4a_fuel_finding_postgres.py`, `assetops_k4_test` only)

- **B10. A → B → A → B on one night.**
  - Append four window revisions through `PostgresFuelBalanceStore.append`, each with a **fixed** `input_sha256`: A, B, A, B. Their states are UNEXPLAINED, WITHIN_MARGIN, UNEXPLAINED, WITHIN_MARGIN. They need distinct `recorded_at`, but the digests are set explicitly and do not include the clock.
  - Call `raise_night` after each append.
  - **Expected statuses:** OPENED, WITHDRAWN, REVISED, WITHDRAWN.
  - **Expected Finding revisions (four):** `OPENED/SUPPORTED`, `NO_LONGER_SUPPORTED`, `SUPPORT_CHANGED/SUPPORTED`, `NO_LONGER_SUPPORTED`. Each claim's `fuel_balance_window_id` is the window revision it was raised from.
  - **Expected rows:**
    - exactly **2** `analytic_run` rows for the night (digests A and B);
    - **4** `assessment_revision` rows (`revision_no` 1–4), where revisions 1 and 3 cite run A and revisions 2 and 4 cite run B;
    - **2** `fuel_residual_consequence_revision` rows (for Finding revisions 1 and 3);
    - `fuel_finding(...)` reads NO_LONGER_SUPPORTED with `consequence None`.
  - Calling `raise_night` a fifth time with no new window gives UNCHANGED and writes nothing.
  - **Must fail** if the run reuse is removed (IntegrityError at the third raise), or if the guard goes back to "any revision" (the fourth raise returns UNCHANGED and the Finding stays SUPPORTED).
- **B11 (review L1, in this round). The price is the one known at the window end.**
  - Set up a stored UNEXPLAINED window for night N with no diesel price. Then publish a price whose validity covers night N, but **recorded after** `window_end` and before the raise (test clock).
  - `raise_night` gives OPENED with an **UNPRICED** consequence: `price_reason = 'NO_PRICE'`, and every price and amount field NULL.
  - **Must fail** if `findings_service.py:90` passes `known_at = now` instead of `w.window_end` (the reviewer's m3 mutation).
- Re-run: §9j.8 A and B, B7–B9, the K3 L2 file, and the must-stay-green list of §9j.8 and §9k.5 that touches these two store files: the cold and EV Finding store tests and `test_s4_finding_domain_filter_postgres.py`. **Part C is not re-run**, because night 4 has one window revision and the fix does not affect it. No suite.

### 9n.3 L2: carry for K7's card (the coordinator passes it to K7 verbatim)

> **K7 carry (DIESEL-1-R3k2, from K4a review L2):** once K7 merges, a combined dataset without Kisiwa is a failure, not a skip. In `tools/demo_combined_finish.py:957-959`, KIS-4 (and every other KIS row that has the same "not in this dataset (K7 adds it)" branch) returns a failing body `{"kisiwa": "missing: no KISIWA-001 Site in this dataset", "checked": 0}` with the row marked failed, in place of the skip. K7 adds an L0 self-test fail body for a summary with no `KISIWA-001`, and changes any existing self-test that expected the skip. K7's packet lists these lines as "carry R3k2 L2". If any KIS row would then fail on a dataset that legitimately lacks Kisiwa, K7 stops and reports it.

- No K4a code change for L2. K7's size grows by about 0.03, which is absorbed inside K7's range.

### 9n.4 Size, critical path, tripwire

- **K4a fix round: about 0.1** (two store edits 0.03, B10 0.04, B11 0.03). That takes K4a from **1.5 to 1.6**, inside S7's ceiling of 1.7. Reported, not absorbed.
- **Kisiwa total: +0.1** on whatever the coordinator's current figure is after R3m.
- **Critical path:** R3m's 8.9 plus 0.1, so **about 9.0 lane-units**. That is below the 9.75 tripwire, with about 0.75 of headroom. No cut and no owner question. The demo date moves by about 0.03 day, which is within the current range.
- Fix round on Sonnet, from this card, in worktree `AssetOpsV1-k4a`. The re-review goes to a fresh Claude reviewer and checks M1 and L1 by name, including the two B10 mutations and the B11 mutation.

### 9n.5 Owner note (plain words)

The reviewer found that if a fuel delivery is recorded on the wrong night and then corrected, the unexplained-fuel check would crash, or would leave an old warning showing. The fix makes each correction add a fresh, correct entry, as the generator findings already do. It also adds a test that the fuel price used is the one known at the end of the night. The work grows by a tenth of a unit, and the demo date does not move in any way you would notice.

---

## 9m2. Ruling DIESEL-1-R3m2: K6a stop S-a3 (the maintenance request's Action link)

- Architect: Claude, 2026-11-08. Binding: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. READ on main at `1e0020df8` and on K4a's branch. Nothing was run.
- **The stop is confirmed.** `work/site_index.py:229-241` `_action_link` gives every domain link that has lineage and a `finding_revision_id` the address `/sites/{site}/actions/{aid}/verification`. On a MINIGRID Site that address is the W1 Action frame, and a fuel Action has no W1 row.
- **Owner: K6a.** K6a is the unit that creates the fuel Action, so it must not ship a link that leads to a "not found" page. K6b fills in the real address.
- **Exact change (K6a):**
  1. `work/adapters/postgres_work_read.py:169-172` (the `domain` list in the case links read): add a conditional key, exactly as the opportunity key is added: `**({"action_domain": r["action_domain"]} if r["action_domain"] == FUEL_DOMAIN else {})`.
     - `_domain_links` already selects `a.domain AS action_domain` (`:60`).
     - Cold, EV and mill link dicts stay byte-equal.
  2. `work/site_index.py` `_action_link`, at the start of the `DOMAIN_ACTION` branch:
     ```python
     if link.get("action_domain") == FUEL_DOMAIN:  # DIESEL-1-R3m2: a fuel Action has no W1 page; K6b sets its verdict address
         href = None
     elif lineage and link["finding_revision_id"] is not None:
         ...
     ```
     The `elif`s that follow are unchanged. `FUEL_DOMAIN` is imported from `work.domain_action`.
  3. K6a's approved file list gains these two edits only.
- **What the link reads between the two merges:** the plain label "Action" (`ACTION_LABEL`) with `href` None. That is the existing no-link rendering (the label is shown, but it is not clickable). It is honest and needs no new literal.
- **K6b (added to §9m.4):** the fuel branch becomes `href = f"/sites/{site_code}/domain-actions/{aid}/fuel-verification" if lineage else None`. K6b adds `work/site_index.py` to its file list. Its L0 test flips the K6a assertion below to that address.
- **Tests (K6a):**
  - **L0**, in `test_k6a_fuel_action_origin.py`: `_action_link` on a fuel link with lineage true gives `href is None` and label "Action". The same link without `action_domain` (a Cold link) still gives `/actions/{aid}/verification`. A mill link still gives `/domain-actions/{aid}/verification`. Must fail if the fuel branch is removed (the fuel link then yields `/actions/…/verification`).
  - **L2**, item 5 of K6a's L2: the request detail and index for the fuel Action's case serve no `href` that contains `/actions/` for that Action id. Must fail on the same mutation.
- **Confirmed:**
  - 0057's `down_revision` = `"0056_unexplained_fuel_finding"`. That is K4a's `revision` (and K4a's own `down_revision` is `0055_fuel_balance_window`), read on `task/DIESEL-K4a-unexplained-fuel-finding`.
  - `test_w502_domain_intent_api.py` failing to collect without a DB URL (`NameError: COLD`) is **not K6a's to fix**. The file imports `COLD` from `test_w502_domain_intent_postgres` inside its DB-gated block (`:23`), and K6a does not touch that file. It is a pre-existing collection quirk, so the coordinator adds it to the follow-up list. K6a runs it with `ASSETOPS_TEST_DATABASE_URL` set to `assetops_k6_test`.
- **Size:** K6a +0.03 (within its 0.8 stop). The critical path is unchanged at about 8.9. Owner questions: none.

