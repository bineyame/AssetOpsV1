# Build sheet: WALK1 (owner walkthrough fix round, 2026-11-01 notes)

Architect: Claude (assetops-architect; ROLE_CONFIG "Architect Is Claude By Default", 2026-10-27). Date 2026-11-02.
Main at writing: `2058a6567`. Owner words (authoritative): `.agent/owner-walkthrough-notes-2026-11-01.md`.
Diagnosis evidence: code at `2058a6567` and read-only SELECTs on `assetops_polish_full_test` (container
`assetopsv1-postgres-1`, user `assetops`). `assetops_demo3_full_test` was not touched.

Standing rules (unchanged from POLISH):
- Plain client copy. No codes, ids, enum names or developer words on screen. The product vocabulary guard
  (`frontend/src/test/productVocabulary.json`) bans, among others, **load, run/ran/running, scenario, PV, SOC,
  simulated, candidate, tick, draft**. Every string below was checked against it.
- Missing data reads "Not available yet". **Never tune numbers or story data.** A declared input is shown as
  declared ("Declared at …", chip "Declared"), never as measured.
- POLISH Addendum 3 capture rule, Addenda 4/5/11/13/14 vocabulary and exemption rules apply unchanged.
- v70 mock is the layout spec. Each visible departure gets a register row (§7) and a review-mode label.
- Every change sits in the outcome mechanism: outcome → drivers → evidence → lever → action → verify. Each item
  below names its place.

A **unit** is about 0.25 builder-day, one reviewable commit including the tests that pin changed strings.

---

## 1. Verdicts

| # | Owner point | Verdict | Reason (plain language) |
|---|---|---|---|
| WN-2 | Missing days lower confidence, they do not blank the assessment | **ACCEPT-MODIFIED** | Right principle. The product already assesses partly checked weeks (COV-PARTIAL: rows, gap days, "N of 7 days checked" text). The bug is narrower: Portfolio counts are gated on *complete* coverage (`estate/portfolio.py:598` `finding_known`), so a partly checked week shows "Not assessed" even though findings on checked days are listed. Fix: counts are published over the checked days with a `count_basis`, every "none" is qualified "on the days checked", coverage is stated, and nothing is extrapolated. Modification: **money totals are not summed over a partly checked period** (unchanged: COV-PARTIAL withholds Kobo money there); the cost card only gets the "on the days checked" qualifier. Site boards already state their day gaps (`finding_gaps`); only the empty "None open" text is qualified. |
| WN-5 | A new day should trigger re-assessment | **ACCEPT, already built (no slice)** | It already works end to end. Accepted readings enqueue the day's assessment in the same transaction (`evidence/adapters/postgres_evidence_ledger.py:478-487`, migration 0029 `enqueue_mini_depth`), and the scheduled cycle (`scheduling/tick.py`: assessment → mini → opportunity → matching → money) recomputes. A declared price change also enqueues money work (0026 trigger). Every screen reads on request (no cache), so a reload shows the change. The demo serve runs that cycle every 120 s and `demo_combined.py add-day` adds a day live. Action: a demo step plus one check in each rebuild gate (§5 G1/G2). No new design. |
| WN-6 | Productive-use revenue should not need sales records; use a declared per-kWh price | **ACCEPT-MODIFIED** | Agreed. Kobo's grain mill is separately metered (`load-mill`, 168.3 kWh measured on S), so productive-use **sales can be estimated as measured kWh used by productive users × a declared price per kWh**, shown as an estimate, never as billed or collected income. Modifications: (1) which users are "productive" must be declared in the Site configuration (a new Foundation property), not guessed from names; (2) the monthly MG-1 target is not compared from one day (that would extrapolate); (3) the *opportunity* side (spare midday solar for more productive use) cannot be priced until Kobo reports the solar-check readings (see WN-4). |
| WN-7 | Declared price/tariff (Depot charging tariff) | **ACCEPT** | The EV declared tariff path is fully built (key `ev_gross_tariff_per_kwh`, model `ev-gross-tariff/1`, Grow headline, Optimize sentence, next-step gap). The demo simply never declared one (DB: 0 EV assumption rows). Declare one in the demo dataset; fix copy. |
| — | Idle-generator fuel rate (parked alongside) | **PUSHBACK: stays parked** | It changes a reviewed money model (`fuel-cost-1` prices delivered kWh only) and the priced amount on the story's lead Finding, which needs its own spec, recompute and review. The current screen is honest ("No fuel cost estimated: the generator was on but delivered no measured power"). Recommended as its own slice after the walkthrough if the owner wants Kobo's Cost row to carry an amount (about 4 units, new model version `fuel-cost-2` with a declared idle rate in L/h). Owner may overrule. |
| WN-1 | Portfolio Assure card says "No verified result yet" while Kobo says "1 verified result" | **ACCEPT** | Real contradiction: `assureDetailText` (`PortfolioOutcomes.tsx:184-191`) hard-codes the phrase. Fix: the outcome summary sends a verified-result count from the same Site boards; the card uses it. |
| WN-3 | Grow cannot fill | **ACCEPT, fixed by WN-6/7** | With declared prices, EV shows estimated charging income and Kobo estimated productive-use sales; the Portfolio Grow card shows them. GreenHarvest Grow stays "Not available yet" (no income input exists; honest). |
| WN-4 | Productive-use headroom invisible | **PUSHBACK on the proposed cause, ACCEPT the fix** | WN-2's rule does **not** fix it. Root cause from the DB: Kobo has **zero** spare-solar assessments for any day. Kobo is configured with `minigrid-roles-3`; the midday solar check only runs on a `minigrid-roles-4` binding (0029 `mini_enqueue_hour` gate) and needs a storage-charge request reading and two declared margins that Kobo does not report. The story data does contain real spare solar: at local noon on 10-16, 10-23, 10-30 and 10-31 about 48 kW was available against about 15 kW used, battery not charging. Fix (WALK1-4/5): Kobo reports the charge-request reading from its own model, declares the two margins, and the board reads the last 5 days, as the mock shows ("Spare solar on 3 of 5 well-observed days"). Expected honest result: no spare solar on day S (cloudy), spare solar visible from S+1. Not tuned. |

---

## 2. WALK1-1: Portfolio checked-days counts, Assure verified count, Grow card (WN-2, WN-1, WN-3 display)

Mechanism: outcome cards (Protect, Assure, Optimize, Grow) → evidence coverage stated → verify by counts on
checked days. Lane 1. **5 units.** Backend + frontend. Scoped regression tier.

### 2.1 Backend `estate/portfolio.py` (`_portfolio`, near `:596-612`)

- New local `count_basis`:
  - `"COMPLETE"` when `states["F"] in (COMPLETE, EMPTY)` (today's rule);
  - `"CHECKED_DAYS"` when `status == PARTIAL_STATUS` (every Site is settled or PARTIAL on all three roots;
    rows of a PARTIAL Site already exclude Findings touching an unchecked day, `coverage.py:156-159`);
  - `None` otherwise.
- `finding_known = count_basis is not None`. `finding_count`, `opportunity_count`, `placement_counts` and
  `category_counts` use it, unchanged otherwise.
- Evidence gap count: same rule **if** `select_evidence_scope` returns rows for a PARTIAL Site.
  **Pre-flight E1:** check this. If it returns none for PARTIAL Sites, keep `evidence_gap_site_count` null in
  the PARTIAL case and report it in the packet; the frontend then keeps "evidence gaps not assessed".
- `summary` gains `"count_basis": count_basis` and
  `"checked_days": [{"site_id", "site_name", "checked", "requested"}]` for each Site whose coverage state is
  PARTIAL and whose `days` block is not null (from `cov["days"]`), else `[]`.
- Money: unchanged. `accepted_action_count`, `verified_resolution_count`: unchanged.

### 2.2 Backend `site_outcomes/read.py` (`summary`, `_summary_row`)

- Board body gains a stripped private key `"_verified_results"`: `sum(1 for a in comp.facts.actions if a.verification_state == "VERIFIED")`
  (all three domains; `ActionFact` is shared). Strip it in the route exactly as `_short_values` is stripped.
- Summary top level gains `"verified_result_count"` (sum over Sites whose board loaded; `None` when none loaded)
  and `"verified_sites_unread"` (Sites whose board failed).
- `_summary_row` passes `"headline_money": row.get("headline_money")` through (null for an unknown row).
- Same window as each Site row, so the card can never disagree with a Site row.

### 2.3 Frontend `estate/estateClient.ts`, `estate/PortfolioOutcomes.tsx`

Types: `summary.count_basis: "COMPLETE" | "CHECKED_DAYS" | null`, `summary.checked_days[]`;
`EstateOutcomeSummaryBody.verified_result_count: number | null`, `verified_sites_unread: number`;
`EstateOutcomeSummaryRow.headline_money: OutcomeMoney | null`. Parsers accept absent fields as null/[]/0.

New helper `checkedDaysClause(body)`:
- one entry: `"{checked} of {requested} days checked at {site_name}"`;
- two or more: `"days not checked yet at {k} sites"`;
- none or `count_basis !== "CHECKED_DAYS"`: `null`.

Card rules (each detail appends ` · {clause}` when the clause is not null):

| Card | Change |
|---|---|
| Protect value | n ≥ 1 unchanged. n = 0 and CHECKED_DAYS: `None found <small>on the days checked</small>`. n = 0 and COMPLETE: "No sites disrupted" (unchanged). null: "Not assessed" (unchanged). |
| Protect detail | `PROTECT_DETAIL` and `protectDetailText` text "Service disruptions recorded in Findings" becomes **"Service disruptions recorded as findings"** (Low, capital-F). Clause appended. |
| Assure detail | `assureDetailText(summary, gap)` lead clause: `verified_result_count` null → "Verified results not available yet"; 0 → "No verified result yet"; v ≥ 1 → `"{v} verified result"`/`"{v} verified results"`; plus `", {sites(u)} not checked"` when `verified_sites_unread > 0`. Targets clause and gap clause unchanged. `evidenceGapText(0, …)` in CHECKED_DAYS reads "no evidence gaps on the days checked". Clause appended. |
| Optimize detail | Clause appended in CHECKED_DAYS (no number changes). |
| Grow | New order: (1) Sites whose Grow row has `headline_money` with amounts. One Site: value `boardMoneyText(money)` + `<small>estimated</small>`; two or more: value `{k} <small>sites with an estimate</small>`. Detail: Site entries `"{site_name} {money}"` joined with " · ", then " · latest day per site". Basis: **"Declared price × measured kWh · not billed or collected"**. Tone green. Destination unchanged. (2) else `growShortValue` path, unchanged. (3) else "Not available yet", unchanged. Never add amounts from different Sites. |

### 2.4 Frontend `estate/EstatePortfolio.tsx`, `sites/OutcomeBoard.tsx`, label Lows

- Portfolio summary strip: a zero count with CHECKED_DAYS reads `"None found on the days checked"` where it
  would read "0" or "None"; non-zero counts unchanged.
- `OutcomeBoard.tsx`: when `body.finding_gaps` is not null, `EMPTY.issues` renders **"None found on the days checked"**
  and `countsText(0, …)` head renders **"No open issues on the days checked"**.
- Capital-F Lows: "Review Finding" → **"Review finding"**, "Open Finding →" → **"Open finding →"**
  (`EstatePortfolio.tsx:182`, `coldSiteViews.tsx:662,703`, `EvAssessmentViews.tsx:347`, `EvSiteViews.tsx:237`).

### 2.5 Tests

- `backend/tests/test_cov_partial.py` (extend): PARTIAL estate → `count_basis == "CHECKED_DAYS"`,
  `category_counts.PROTECT_ASSET.sites_with_primary_finding` is an int; UNKNOWN estate stays null; COMPLETE stays COMPLETE.
- Outcome summary test (existing OUT-B summary test file): `verified_result_count` = 1 for a board with one
  VERIFIED Action; `headline_money` passthrough; failed Site → `verified_sites_unread` 1.
- Vitest `PortfolioOutcomes`: every row of the card table, including clause singular/plural and the Grow
  one-Site / two-Site / fallback cases; `assureDetailText` 0/1/2/null; capital-F strings.
- Vocabulary vitest over the new strings.

Captures (after the G1 rebuild): `portfolio-week`, `kobo-board-S`, `findings-*` (labels).

---

## 3. WALK1-2: Depot declared charging tariff, EV Grow copy, two Lows (WN-7, WN-3 for EV)

Mechanism: Grow outcome → driver "charging delivered" (measured kWh) × lever input "declared tariff" → estimate.
Lane 2. **3.5 units.** Scoped tier.

### 3.1 Data (demo producer)

- New fixture `backend/conversions/demo-ev-tariff-publications.json`, same shape as
  `demo-diesel-price-publications.json`: `assumption_key "ev_gross_tariff_per_kwh"`, one step `v1`,
  `change_kind INITIAL`, `currency "USD"`, `value "0.30"`, `basis "AUTHORED_ESTIMATE"`,
  `source_reference "Demonstration charging tariff set by the system (illustrative, not a contract rate)"`,
  `valid_from "2026-01-01T00:00:00Z"`, `valid_to null`, `idempotency_key "demo-ev-tariff-v1"`.
  **Value source:** the v70 mock's own EV Grow figure ($36.00 for 120 kWh = 0.30 per kWh). It is an input
  chosen before seeing any result, not tuned to one.
- `tools/demo_combined_ev.py`: publish it with `publish_assumption fixture --site EV-LAB-001 --file … --step v1`
  at `install_at + 30 min` (the configuration knowledge instant), as `demo_combined_kobo.publish_price` does.
- The EV money recompute is enqueued by the 0026 trigger and drained by the `ev_consequence` stage of the
  prepare ticks. **Pre-flight E2:** confirm after a local prepare that the fault-Tuesday window's consequence
  is ESTIMATED/PRICED; if `publish_assumption` refuses the EV key, report before coding.

### 3.2 Backend `site_outcomes/ev.py`

- `TARIFF_ESTIMATE` "gross tariff estimate" → **"estimated charging income"**.
- Grow subline when priced: **"{kwh} kWh with a complete meter record, at the declared tariff of {p} {cur} per kWh · not billed or collected"**;
  unpriced: unchanged.
- New Grow contributor `charging_tariff`, label **"Charging tariff"**: priced → **"Declared at {p} {cur} per kWh"**,
  chip `DECLARED`, href `/sites/{c}/ev/financials`; no tariff → **"Not available yet · no charging tariff declared"**.
- `{p}` uses `mini.price_text` rules (shared helper; move or import as the code allows).
- **Pre-flight E3:** if the overview `consequence_summary` lacks the tariff value and currency, add them as a
  read-time serialisation of the selected consequence's `tariff_value`/`currency` (Addendum 12 pattern). If that
  needs a new query path, use the assumption read instead and report.
- Optimize (P-11) and the TARIFF_GAP next step switch automatically on a priced tariff; pin both in tests.

### 3.3 Lows folded in

- **L-A** `frontend/src/sites/SiteFindingHistory.tsx:461-467`: "Related Findings: … Finding <id>" becomes
  **"Related findings: {plain title}"** with no id; `:576-641` "Times and references": model version and
  assessment ids move inside the existing Technical details region (`data-technical-details`).
- **L-B** `tools/demo_combined.py:197-199`: print "ready:" only on a 2xx status; otherwise "prewarm returned {status}".

### 3.4 Tests

- `test_w207_ev_site_reads_postgres.py` / EV board compose tests: priced headline, subline, contributor, chip;
  unpriced texts unchanged.
- Producer test (`test_demo_combined_postgres.py` or the EV producer unit test): the publication step runs once and is idempotent.
- Vitest for SiteFindingHistory: no 8-char id outside Technical details.

Captures (G1): `ev-board-fault`, `portfolio-week`.

---

## 4. WALK1-3: Declared productive-use price and estimated productive-use sales at Kobo (WN-6, WN-3 for Kobo)

Mechanism: Grow outcome MG-1 "Productive electricity sales" → driver "measured use by declared productive
users" → evidence (accepted metered readings) × declared price → estimate; lever: the productive-use what-if
(WALK1-5); verify: MG-1 reading. Lane 2 after WALK1-2. **6 units.** Migration → **full suite tier**.

### 4.1 Declared price key (migration `0040_walk1_productive_price`)

- `financial_assumption_revision` CHECKs widened exactly as 0026 widened them for the EV key (and any
  assignment-table key CHECK the same way): key `productive_use_price_per_kwh`, unit `currency/kWh`, value > 0.
  Downgrade refuses while any row with that key exists (0026 pattern).
- `financials/assumptions.py`: add the key to `ASSUMPTION_KEYS`, `UNITS` (`currency/kWh`), the strictly-positive
  check and the ISO 4217 currency check (same as EV).
- Frontend assumption words (wherever `ev_gross_tariff_per_kwh` gets its label): **"Price per kWh for productive users"**.
- Fixture `backend/conversions/demo-productive-price-publications.json`: `value "0.25"`, `currency "USD"`,
  `basis "AUTHORED_ESTIMATE"`, `source_reference "Demonstration price per kWh for productive users, set by the system (illustrative, not a contract rate)"`,
  `valid_from "2026-01-01T00:00:00Z"`, `idempotency_key "demo-productive-price-v1"`. **Value source:** the v70
  mock's grain-mill what-if ($2.50 per eligible window = 10 kW × 1 h × 0.25). Chosen before any result.
- `tools/demo_combined_kobo.py`: publish it next to the diesel price (same instant).

### 4.2 Declared productive users (Foundation property)

- `sites/models.py`: new state property `supply-use`, `PropertyDefinition(unit="state", kind="PHYSICAL", display_name="Supply use")`,
  `STATE_PROPERTY_VALUES["supply-use"] = {"PRODUCTIVE", "HOUSEHOLD", "ESSENTIAL_SERVICE"}`, carrier `LOAD`
  (add to `MINIGRID_PROPERTY_CARRIERS`). Optional; absence means "not declared".
- Foundation page words: PRODUCTIVE **"Productive use"**, HOUSEHOLD **"Household"**, ESSENTIAL_SERVICE **"Essential service"**
  (never the code).
- Kobo declares `load-mill` PRODUCTIVE, `load-res` HOUSEHOLD, `load-clinic` ESSENTIAL_SERVICE in an **additive**
  Foundation revision at commissioning (new `CONFIG_OFFSETS` entry, e.g. `"uses": 12 min`), so no existing
  pinned configuration file or digest changes. **Pre-flight E4:** confirm the additive revision does not change
  any S3 dispatch input digest the trial verification pins; if it does, report before coding.

### 4.3 Measured productive use (read-time, no new stored number)

- Pure module `site_outcomes/productive_use.py`: `productive_energy(readings, lo, hi)` →
  `{"kwh": Decimal | None, "measured_seconds": int, "evidence_count": int}`. kWh = Σ over GOOD
  `feeder_demand` interval readings of `value_kW × clipped_hours`, exact Decimal; `measured_seconds` = union of
  GOOD coverage inside `[lo, hi)`. No readings → `kwh None`. Non-GOOD readings are gaps, never zero.
- New `MiniPorts` ports, bound in B4 (`site_outcomes/read.py`):
  - `productive_users(at) -> list[{"asset_code", "name"}]` from the Foundation revision valid at `at` (LOAD components with `supply-use = PRODUCTIVE`; `name` = component `display_name`, e.g. "Grain mill");
  - `productive_readings(lo, hi) -> list[reading]` for those assets' accepted `feeder_demand` evidence.
  - SQL lives in an adapter only (`check-architecture` rule). **Pre-flight E5:** name the adapter file (the mini
    depth store already queries `accepted_evidence`).
  - `productive_price(at)` from the same assumption read the diesel `price` port uses, key `productive_use_price_per_kwh`.
- Window: the board's UTC day `[start, end)` (the overview day). Kobo's measured hours are those the gateway
  delivered (03:00–11:00 UTC on story days); the copy names the measured hours and never scales to 24 h.

### 4.4 Composer `site_outcomes/mini.py`

Let `names` = user names joined with ", " (Kobo: "Grain mill"); `h` = `num(measured_seconds / 3600)`;
`amount` = `kwh × price`, displayed at 2 decimals ROUND_HALF_UP (stored arithmetic exact).

| Case | Grow headline / `headline_money` | Contributor `productive_sales` "Productive-use sales" | Contributor `productive_price` "Price per kWh" |
|---|---|---|---|
| no productive user declared | unchanged (headroom or none) | **"Not available yet · no productive users identified for this site"** | omitted |
| users, no readings | unchanged | **"Not available yet · no measured use by {names} on this day"** | as below |
| users, kWh, no price | unchanged | **"{kwh} kWh used by {names} in {h} measured hours · no price per kWh declared"** | **"Not available yet · no price per kWh declared"** |
| users, kWh = 0, price | **"No productive-use sales on this day: {names} not used"** / null | **"0 kWh used by {names} in {h} measured hours"**, chip DECLARED | **"Declared at {p} {cur} per kWh"**, chip DECLARED, href `/sites/{c}/financials/assumptions` |
| users, kWh > 0, price | **"estimated productive-use sales"** / `{amount_low: amount, amount_high: amount, currency}` | **"{kwh} kWh used by {names} in {h} measured hours"**, chip DECLARED | as above |

- Grow subline when priced: **"{kwh} kWh used by {names} in {h} measured hours, at the declared price of {p} {cur} per kWh · not billed or collected"**.
  Otherwise `GROW_SUBLINE` stays only for "no productive user declared"; for the other unpriced cases the subline is null.
- Use "hour"/"hours" and "kWh" via `plural`. Order of Grow contributors: Productive use (spare solar),
  Productive-use sales, Price per kWh, Cash collected, Site earnings.
- Headline precedence: a sales estimate leads; spare solar stays in its contributor, the Issues column and
  `short_values` (Portfolio fallback).
- MG-1 reading (`mini_readings`): kWh known → `Reading(kwh, False, "{kwh} kWh used by productive users on this day; the monthly target is not compared from one day")`;
  else `MG1_ACTUAL` unchanged. The objective verdict therefore stays not assessed (no extrapolation).
- Row state logic is **not** changed. **Pre-flight E6:** report Kobo's Grow row state on S with the estimate; if
  it reads Unknown beside a money figure, register it (R678) rather than changing the state rule here.
- Add every new string to `COPY`.

S expected (not tuned): Grain mill 168.3 kWh measured → 42.08 USD at 0.25. Sunny days: 0 kWh → "No productive-use sales on this day: Grain mill not used".

### 4.5 Tests

- `test_productive_use.py` (pure): clipping, gaps, non-GOOD readings, exact sum.
- Migration test (0040 up/down/refusal, CHECK text), `test_w207_ev_money_postgres.py`-style CHECK assertions updated.
- Compose tests: each table row, subline, MG-1 reading, vocabulary scan.
- Foundation property validation (state set, carrier) and the words map.

Captures (G1): `kobo-board-S`, `kobo-board-S-open`, `kobo-board-S1`, `portfolio-week`.

---

## 5. Gate G1 (coordinator): rebuild, finish, strict captures. Walkthrough resumes after G1.

- **`assetops_polish_full_test` must be rebuilt** from merged main after WALK1-1..3 (migration 0040 and two
  data changes). Use the existing `tools/demo_combined.py prepare` on that DB name and its own work dir.
  **Never touch `assetops_demo3_full_test`.**
- Finish check 17/17, plus three new checks added in WALK1-3 to `tools/demo_combined_finish.py`:
  EV Grow headline "estimated charging income" with an amount; Kobo S Grow `headline_money` present;
  Portfolio summary `count_basis` not null for the story week.
- Strict 28-capture run: expect 0 counted vocabulary hits.
- **WN-5 check (no code):** with serve running, `add-day --site KOBO-001 --kind normal --day <next free>`, wait
  one cycle (≤120 s), reload: the Kobo board for that day is assessed and the Portfolio clause reads one more
  day checked. Record before/after in the G1 packet. This is also the demo step for the owner.

---

## 6. WALK1-4 and WALK1-5: Kobo spare midday solar (WN-4), declared price in the what-if

### WALK1-4: Kobo reports the midday solar-check readings. Lane 1 after WALK1-1; code after WALK1-3 merges (shared `tools/demo_combined_kobo.py`). **6 units.** Full suite tier.

Mechanism: Grow MG-1 opportunity → driver "spare solar" → evidence (charge request, available and used solar,
declared margins).

- **Pre-flight F1 (stop condition):** find the charge request the Kobo model already computes
  (`simulator/assetops_simulator/packs/mini_grid.py` ~`:686-735`, PCS `requested`/`charge_cap`). If the model has
  no requested-charge quantity of its own, **stop and report**: no series may be invented.
- Host Kobo publication **v5** (`host/lab_execution.py` and its publication module): v4 plus signal
  `battery-pcs-controller/charge-requested-power` (kW) = the model's requested charge, 0 when none. v4 stays
  byte-identical for its pinned tests.
- New config `backend/conversions/kobo-001-minigrid-roles-4-demo-config.json` (pattern:
  `mg-w402-001-minigrid-roles-4.json`): every roles-3 binding unchanged plus `storage_charge_requested_power` on
  the battery asset; component properties `pv-available-uncertainty` = **3 kW** on `pv-inverter` and
  `renewable-retained-margin` = **5 kW** on `ac-bus`, recorded as declared demonstration values (logged as
  Architect decision D-W1-3 for owner review).
- `tools/demo_combined_kobo.py`: apply roles-4 at commissioning (new `CONFIG_OFFSETS` entry after `roles3`);
  every Kobo day publishes with v5.
- **Pre-flight F2:** confirm S3 dispatch and the trial verification accept a roles-4 binding set
  (`SERVED_ROLE_SETS_BY_SITE_TYPE`) with unchanged results on S and S+1; confirm prepare drains the new mini jobs
  (add `mini_depth.worker run-pending` to prepare if the bounded cycle does not).
- Fuel, Service and Backup depth domains will start producing limited results where they produced none. The
  packet lists every Kobo contributor text before/after; each must stay honest (for example "No complete fuel
  balance yet" stays, since Kobo has no fuel level reading).
- Expected (not tuned): ELIGIBLE on 10-16, 10-23, 10-30, 10-31 (about 48 kW available vs 15 kW used, battery not
  charging); no positive headroom on 10-02, 10-09, 10-27, 10-29. The builder reports actual decisions.

### WALK1-5: 5-day solar read on the board, declared price in the productive-use what-if. Lane 1 after WALK1-4. **3 units.** Scoped tier.

- `mini.py` `_depth`: renewable window = the 5 Site-local days ending on the board day
  (`RENEWABLE_DAYS = 5`, the recurrence rule's day count, `mini_depth/rules.py:410`). Other domains unchanged.
  Contributor text stays the mock's "Spare solar on {e} of {a} well-observed days"; when `a < 5` append
  **" · {5−a} of the last 5 days not checked"**. Headline/short value unchanged in form. This is WN-2 applied
  to the Site row: assess the days read, state the rest.
- Productive-use what-if (PRODUCTIVE_LOAD authoring page): prefill `tariff_per_kwh` from the declared
  productive-use price (value, `USD/kWh` unit), labelled **"Declared price · {p} {cur} per kWh"**; an edited value
  is labelled **"Entered for this what-if"**. Stored calculation rules unchanged. **Pre-flight F3:** name the
  authoring file and confirm the prefill needs no new endpoint (reuse the assumptions read).
- Tests: compose test over 5 days (mixed eligible/excluded/missing), vitest prefill and label.
- Expected: S board "Spare solar on 0 of 2 well-observed days · 3 of the last 5 days not checked"; S+1 board shows
  a headroom headline and the Productive-use headroom issue.

### Gate G2 (coordinator)

Rebuild `assetops_polish_full_test` again from main, finish check (add: S+1 Kobo Grow contributor has
"Spare solar on"), strict captures; add capture key `kobo-whatif` (the productive-use what-if page, S+1).

---

## 7. Slices, lanes, order

| Slice | Units | Lane | Depends on | Tier | Register ids |
|---|---|---|---|---|---|
| WALK1-1 Portfolio checked days, Assure count, Grow card, labels | 5 | 1 | — | scoped | R670-R673 |
| WALK1-2 Depot declared tariff, EV copy, L-A, L-B | 3.5 | 2 | — | scoped | R674-R676 |
| WALK1-3 Productive-use price and sales estimate | 6 | 2 | WALK1-2 merged (lane order only) | full (migration) | R677-R680 |
| G1 rebuild + captures + WN-5 check | — | coordinator | 1, 2, 3 merged | — | — |
| WALK1-4 Kobo solar-check readings | 6 | 1 | WALK1-1 merged; code after WALK1-3 merged | full | R681-R684 |
| WALK1-5 5-day solar read, declared price in what-if | 3 | 1 | WALK1-4 | scoped | R685-R689 |
| G2 rebuild + captures | — | coordinator | 4, 5 merged | — | — |

- At most two lanes at once. WALK1-1 and WALK1-2 share no source file (WALK1-1 owns `PortfolioOutcomes.tsx`,
  `EstatePortfolio.tsx`, `OutcomeBoard.tsx`, the capital-F lines, `estate/portfolio.py`, `site_outcomes/read.py`
  summary; WALK1-2 owns `ev.py`, EV producer, `SiteFindingHistory.tsx`, `demo_combined.py`). WALK1-3 touches
  `read.py` port binding only (not the summary) and `mini.py`; it rebases onto WALK1-1.
- WALK1-4 pre-flight F1/F2 (read-only) may run while WALK1-3 builds.
- The walkthrough resumes after G1. Kobo's spare-solar opportunity is revisited after G2. If the owner prefers
  to wait for G2 before resuming, nothing else changes.
- Captures: backend slices defer captures to the gate rebuild (Addendum 3 option a) and pin every changed
  sentence in compose/read tests; frontend parts capture over the demo serve per Addendum 3.

## 8. Register rows (by slice)

- R670 (D2) Portfolio cards state checked days and qualify "none"; R671 (D2) Assure detail carries the verified
  count; R672 (D2) Grow card value from declared-price estimates; R673 (D2) "None found on the days checked" on boards.
- R674 (D2) EV Grow headline "estimated charging income" (mock "gross tariff estimate"); R675 (D4→data) the mock's
  EV tariff figure now comes from a declared tariff; R676 (D2) "Charging tariff" contributor (not in mock).
- R677 (D2) Kobo Grow headline is the sales estimate, not the mock's headroom headline; R678 (reserved, E6);
  R679 (D2) "Productive-use sales" and "Price per kWh" contributors; R680 (D2) Foundation "Supply use" words.
- R681-R684 (WALK1-4 as needed: new contributor texts from the depth domains); R685 (D2) the "· N of the last 5 days
  not checked" suffix; R686 (D2) what-if declared-price label.
- Add the new client strings to the R655 plain-language row.

## 9. Architect decisions logged for owner review (owner-away rule)

- D-W1-1: Depot tariff 0.30 USD per kWh, from the v70 mock's own figure; declared, illustrative.
- D-W1-2: Kobo productive-use price 0.25 USD per kWh, from the v70 mock's what-if figure; declared, illustrative.
- D-W1-3: Kobo solar uncertainty 3 kW and retained margin 5 kW, declared demonstration values.
- D-W1-4: money is not summed over partly checked periods or across Sites with different windows.
- D-W1-5: idle-generator fuel rate stays parked (own slice after the walkthrough if wanted).

## 10. Not in this round

PB-0 N1/N2 test hardening, test-pipeline items (shared `assetops_test`, rule 8 flake, `_case_db` collision),
`WarningFacts.soon_until`, GreenHarvest income inputs, Portfolio PRODUCTIVE_USE value card (stays
"Not established"; register if it shows on a capture), live page auto-refresh (reload shows new days; not needed
for WN-5).

---

## Addendum 1 (2026-11-02): WALK1-1 review M1, L1-L4 (`.agent/review-WALK1-1.md`)

**M1, accepted as the reviewer proposes. Spec gap in §2.1, not builder error.**
- Backend: each `summary.checked_days` entry gains `"withheld": bool` (from `cov["days"]["withheld"]`).
  `site_outcomes/mini.py` `finding_gap_line` also returns `"withheld": bool(body.get("withheld"))` beside `text`/`days`.
- A Finding-based zero count with **any** withheld entry never reads "None found…". Copy:
  - Protect card value: **"None shown yet"** (no `<small>` part).
  - Portfolio summary strip zero counts (finding, opportunity, placement): **"None shown yet"**.
  - Clause, replacing §2.3's: one Site **"{checked} of {requested} days checked at {site_name} · findings next to unchecked days not shown yet"**;
    two or more Sites **"days not checked yet at {k} sites · findings next to those days not shown yet"**.
    It is used on every card that carries the clause while any entry is withheld.
  - `OutcomeBoard.tsx`: with `finding_gaps.withheld` true, the empty Issues text is **"None shown yet"** and the zero
    counts head is **"No open issues shown yet"**. With withheld false, §2.4 is unchanged.
  - The evidence gap count is not affected: rows are per day and are never withheld (review E1). It keeps "no evidence gaps on the days checked".
- Guard check: no banned term ("unchecked", "shown", "findings" are allowed; lowercase "findings").
- Tests: one backend test (a PARTIAL Site with `withheld: true` → entry flag true, and the count is still an int)
  and vitest cases for the Protect value, the strip, both clause forms and the board's withheld text.
- Register: add to R670 and R673.

**L2. Grow detail suffix** "latest day per site" becomes **"each site's latest assessed period"**. Kobo is judged on a day,
cold and EV on their latest event. Full detail: `"{site} {money} · … · each site's latest assessed period"`.

**L1. Fold in, yes.** `EvAssessmentViews.tsx:345` `label="Open Finding"` → **"Open finding"** (update
`evAssessmentRoutes.test.tsx:506`); `SitePerformance.tsx:408` the same.

**L3. Yes.** Add `assert not any(k.startswith("_") for k in r.json())` to a board route test in `test_out_b4_route.py`,
with a fake body carrying both `_short_values` and `_verified_results`.

**L4. Check at G1, no change now.** The card counts verified Actions; "Fixes confirmed" counts verified resolutions in
a 30-day lookback. Those are different measures under different labels. At G1, record both on `portfolio-week`. If
they show different numbers for the same Kobo trial, it goes to a post-G1 copy Low (no blocking fix).

**L5.** Noted as pre-existing, no change.

The fix round stays within WALK1-1's 5 units (fix round, scoped tier).

---

## Addendum 2 (2026-11-02): separate performance, KPI progress and potential on the Grow row

Owner, verbatim (last entry of `.agent/owner-walkthrough-notes-2026-11-01.md`): "why are we conflating KPI with potential ?"

**Ruling: the owner is right, and the coordinator's three-way split is accepted.** Today one row state carries all
three. In `outcomes/status.py` `outcome_state`, an open opportunity signal (spare solar, *potential*) outranks
the declared-objective verdict (*KPI*), and a not-judged objective turns the row "Unknown" even when the
*performance* figure is shown. So whichever arrives first hides the others. Each of the three gets its own slot:

| Thing | Question it answers | Where it shows | Sets the row state? |
|---|---|---|---|
| (a) Performance now | What did productive use earn on this day? | Headline + `headline_money` (WALK1-3, unchanged) and the "Productive-use sales" line | No |
| (b) KPI progress | Are we on course for the declared target? | Row state chip and the "Declared objective" line | **Yes, when an objective is declared** |
| (c) Potential | What more could the site earn? | Issues column "Opportunity" item (exists), the "Productive use" spare-solar line, and a second header chip **"Opportunity"** | Only when no objective is declared for the row |

### A2.1 State rule (`outcomes/status.py` `outcome_state`, all domains)

- Move the `SIGNAL_OPPORTUNITY` step **below** the declared-objective steps:
  - an outcome **with** a declared objective takes its state from the objective verdict (A2.2);
  - an outcome **without** one keeps today's order (Opportunity, then No objective).
- Needs-attention Findings and warnings, applied Findings, limited evidence and MISSED keep their current
  precedence above both, unchanged.
- Row wire gains `"potential": {"label": "Opportunity", "text": <the opportunity issue title>} | null`. It is set
  when the row has an open opportunity signal and `state != OPPORTUNITY`.
- `OutcomeBoard.tsx` renders it as a second neutral-green chip **"Opportunity"** after the state chip, with
  the row header unchanged otherwise. Register **R690 (D2)**: the mock has one chip per row.

### A2.2 KPI judged from partial data (MG-1 only; it is the only per-month measure)

- **Reading:** month to date. Window = the Site-local calendar month containing the board day, from its first day
  through the end of the board day. `mtd` = Σ measured kWh of declared productive users over that window
  (`productive_energy`, WALK1-3, same rule; no new stored number).
  - `c` = days in the window with any measured productive-use coverage (checked days).
  - `e` = days elapsed in the month; `m` = days in the month; `need` = target ÷ `m` (kWh a day); `avg` = `mtd` ÷ `c`.
- **Verdict (`judge_month`, new, pure, beside `judge`).** First match wins:
  1. `mtd ≥ target` → **MET**. This is proven whatever the missing days, since missing days can only add.
  2. Month complete (board day is the last day) and every day checked → **MISSED**.
  3. `c < 3` → **TOO_EARLY**.
  4. `avg ≥ need` → **ON_PACE**.
  5. Otherwise → **BEHIND_PACE**. That covers a complete month with gaps that is still below target: the result is
     behind on the days checked, never MISSED.
- **Comparing rates, never projecting a total.** The pace step compares a daily average with the daily rate the
  target needs. No projected month total is ever shown.
- **State mapping:** MET and ON_PACE → On track; BEHIND_PACE → Watch; MISSED → Needs attention; TOO_EARLY →
  Unknown, reason `OBJECTIVE_TOO_EARLY`. Too early is the only case left that reads Unknown.
- **Verdict chips** (`VERDICT_CHIP`, added):
  - "On pace" green;
  - "Behind pace" amber;
  - "Too early to judge" gray.
  - MET and MISSED keep their chips.
  - The wire verdict codes are added to the objectives list; they are never rendered as codes.
- **Actual text** (`Reading.actual_text` for MG-1; `{d}` is "day"/"days" via `plural`):
  - MET: **"{mtd} kWh so far this month, on {c} of {e} days checked"**
  - ON_PACE / BEHIND_PACE: **"{mtd} kWh so far this month, on {c} of {e} days checked · averages {avg} kWh a day; the target needs {need} kWh a day"**
  - TOO_EARLY: **"{mtd} kWh so far this month, on {c} checked {d}; too early to judge"**
  - MISSED: **"{mtd} kWh this month, all {m} days checked"**
  - No productive user declared or no readings in the month: `MG1_ACTUAL`, unchanged; verdict NOT_JUDGED as today.
  - These replace WALK1-3's "…the monthly target is not compared from one day".
- **Threshold.** 3 checked days is an Architect decision (D-W1-6) for owner review. Below it, a single heavy or idle
  day decides the pace.
- **Expected on story day S (not tuned).** October checked mill days are 10-02, 10-09, 10-16, 10-23, 10-27 and
  10-29. `mtd` = 4 × 168.3 = 673.2 kWh, which is ≥ 300, so the result is **MET**: Grow reads "On track". The
  builder reports the actual figure.

### A2.3 Headline and contributor order (Kobo Grow)

- **Headline:** the performance figure (WALK1-3 table, unchanged). On a day without a priced estimate, the
  existing spare-solar headline may lead, and the spare-solar figure then also shows as the "Opportunity" chip text.
- **Contributors, in this order:**
  1. "Productive-use sales" (a);
  2. "Declared objective" (b), the existing `objective_contributor`, now carrying the month-to-date text and verdict chip;
  3. "Productive use" spare solar (c);
  4. "Price per kWh";
  5. "Cash collected";
  6. "Site earnings".
- R678 (Unknown beside a money figure) closes once A2 merges.

### A2.4 Slicing and scope

- **WALK1-3 is not reopened.** It reviews as specified; E6/R678 is the correct interim record.
- **New slice WALK1-3b, about 4 units, lane 2, after WALK1-3 merges, before G1** (the walkthrough would otherwise
  meet the same "Unknown"). Scoped tier plus the `outcomes/` and board test modules. Register ids R690-R693.
  1. `judge_month` and the MG-1 month-to-date reading, using a month window on the WALK1-3 port (1.5 units);
  2. the state precedence change and the `potential` wire field (1 unit);
  3. the frontend second chip and verdict chip words (0.75 units);
  4. tests and register rows (0.75 units).
- **Tests:**
  - `judge_month` truth table (each rule, boundaries at `c = 2/3` and `avg = need`);
  - an `outcome_state` test showing an opportunity no longer outranks a declared objective, while no-objective
    rows are unchanged;
  - the compose test for Kobo on S (MET, On track, Opportunity chip absent with no headroom);
  - a vitest for the second chip.
- **Other Sites:**
  - EV Grow: the precedence rule is generic, but EV declares no Grow objective, so its rows are unchanged.
    Pin this in a test.
  - GreenHarvest Grow: not measured, unchanged.
- **Portfolio Grow card:** value unchanged (money from (a)). Its Site dots follow the new row state (Kobo turns
  On track), which is intended.
- **WALK1-5 interaction:** once spare solar appears (S+1), Kobo's Grow state stays the KPI state and the spare
  solar shows as the "Opportunity" chip and issue. The mock's single "opp" state is replaced (R690).
- **G1 finish check adds:** Kobo S Grow state is not Unknown, and its objective line contains "so far this month".

### A2.5 (2026-11-02) Owner ruling on D-W1-6: the minimum is configurable

Owner, verbatim (last entry of the walkthrough notes): "\"the 3-checked-day minimum before the target is judged\" looks reasonabel but got to be configurable"

- **Where it is set: per declared objective.** The minimum is part of how a declared target is judged, and targets
  are already declared per Site and outcome as `outcome_objective_revision` rows. A per-Site or estate-wide setting
  would separate a judging rule from the target it judges. A changed minimum is a new objective revision, with the
  same chain, actor and idempotency rules as a changed target.
- **Storage: migration `0041_walk1_objective_min_days`** (after WALK1-3's 0040).
  - Adds a nullable `min_checked_days integer` column to `outcome_objective_revision`.
  - CHECK: `min_checked_days IS NULL OR (min_checked_days BETWEEN 1 AND 28)`.
  - CHECK: `min_checked_days IS NULL OR measure_key = 'productive_use_kwh'`, the only per-month measure. Widen this
    list when another monthly measure exists.
  - No backfill: NULL means the default.
  - Downgrade refuses while any row has a non-null value.
  - Because of the migration, WALK1-3b runs on the **full suite tier**.
- **Default and validation.**
  - Code constant `DEFAULT_MIN_CHECKED_DAYS = 3` in `outcomes/objectives.py`; `Measure` gains `monthly: bool`
    (true for `productive_use_kwh` only).
  - The objective declaration input gains optional `min_checked_days`. It is refused with the existing objective
    input refusal (same 422 code and copy path as an invalid target) when:
    - it is not an integer;
    - it is outside 1–28 (28 is the shortest month, so the minimum can always be reached);
    - it is given for a non-monthly measure.
  - It is part of the payload hash only when present, so existing declarations keep their idempotency hashes.
  - `ObjectiveFact` gains `min_checked_days: int` (resolved: stored value or 3). `judge_month` rule 3 uses
    `c < fact.min_checked_days`.
- **Client visibility.** Shown only where it explains a result, as plain text and never as a setting name:
  - TOO_EARLY actual text becomes **"{mtd} kWh so far this month, on {c} checked {d}; too early to judge (needs {k} checked days)"**.
    `{k}` is the resolved minimum, so the client can see why.
  - Other verdict texts are unchanged.
  - The objective's target sentence is unchanged.
  - Register R691 (D2).
- **Demo data:** unchanged. Kobo's MG-1 declares no minimum, so the default of 3 applies.
- **Tests:**
  - migration up/down/refusal and both CHECKs;
  - declaration validation:
    - 0, 29, 2.5 and "3" refused;
    - a non-monthly measure refused;
    - 1 and 28 accepted;
    - absent → NULL stored;
  - an idempotency hash test: an existing declaration without the field keeps its hash;
  - `judge_month` with minimum 1 (one checked day can judge pace) and minimum 5 (four days give TOO_EARLY);
  - the default path (NULL → 3);
  - a compose test pinning the TOO_EARLY text with `{k}`;
  - vocabulary scan.
- **Size:** WALK1-3b grows from about 4 to **about 5 units** (the migration and the declaration validation add
  1 unit). It stays one slice; the 6-unit cap holds.

---

## Addendum 3 (2026-11-02): WALK1-3 review M1, M2, L1-L4 (`.agent/review-WALK1-3.md`)

Fix round, scoped tier, within WALK1-3's units.

**M1, accepted.**
- `productive_energy` groups GOOD clipped spans by asset. If any declared productive user's spans overlap, the
  whole result is conflicting: `kwh None`, plus a new `conflict_assets: [name…]`. No partial sum. This follows the
  depth `series` CONFLICTING rule.
- Copy:
  - contributor "Productive-use sales": **"Not available yet · {names} has conflicting readings on this day, so use is not estimated"**,
    where `{names}` is the conflicting users, joined with ", ", and the verb is "have" for two or more;
  - headline and `headline_money`: unchanged from the no-estimate case (no money);
  - subline: null;
  - MG-1 reading: `MG1_ACTUAL`.
  - Under WALK1-3b, a conflicting day does not count as a checked day.
- Tests:
  - a one-asset overlap gives `kwh None` and names the asset;
  - two users overlapping each other still sum (existing test kept);
  - compose text pinned.
- Add to R679.

**M2: option (a).**
- The mini Assumptions page (`financialsClient.ts` `getAssumptions` and its page) reads a second series,
  `productive_use_price_per_kwh`, and shows it as its own row:
  - label **"Price per kWh for productive users"**;
  - value **"{p} {cur} per kWh"**;
  - basis word **"Declared"**;
  - its valid-from date, the same as the diesel row;
  - with no declaration: **"Not available yet · no price per kWh declared"**.
- The board link stays.
- R679 is corrected to: "Price per kWh contributor links to Assumptions, which shows the declared productive-use price as its own row".
- Tests:
  - client parser for both keys;
  - page vitest for declared and undeclared;
  - vocabulary scan.

**L1: fold in now.** It is client-visible on the walkthrough path and is a small rename.
- `EvEnergy.tsx:78`: "{amount} {cur} gross estimate" → **"{amount} {cur} estimated"**.
- `EvEnergy.tsx:164,297`: "Gross tariff estimate" → **"Estimated charging income"**.
- `estateEvidenceWords.ts:23` and `estateFinancialsWords.ts:20`: "Gross tariff estimate" → **"Estimated charging income"**.
- Update the tests that pin these strings, and add them to R655.

**L3: ruled now, built now** (the headroom headline path already exists in `mini.py`). On a priced day with zero
productive use, the spare-solar headline leads when one exists. The "No productive-use sales on this day: {names}
not used" headline is used only when there is no spare-solar headline. The zero-use fact stays in the
"Productive-use sales" contributor ("0 kWh used by {names} in {h} measured hours"). A compose test pins both
branches. This also holds after WALK1-3b: the headline is still never the row state.

**L4: confirmed.** On the NOT_LOADED `productive_users` branch, return `subline: None`. `GROW_SUBLINE` stays only
for "no productive users declared". Pin it in a test.

**L2: agreed, superseded.** WALK1-3b (Addendum 2) replaces the Unknown state with the month-to-date verdict.
"Unknown" remains only for "Too early to judge", which carries its own chip words. R678 closes at the WALK1-3b merge.

**L5:** update `.ai/CODE_STATE.md` head at merge (coordinator).

---

## Addendum 4 (2026-11-02): WALK1-4 pre-flight F1 (Kobo charge request). Owner away: the Architect decides; logged.

**Q1: accepted.** New model mini-grid **v6** = v5 + `resolve_v6`. `resolve_v6` is `resolve_v4` plus the measurement
`battery-charge-requested-power@{pcs}`. Flows, decisions and every existing measurement stay byte-identical. It is
registered in `runs/profiles.py` and `host/execution_adapter.py`. `REGISTERED_KOBO_PUBLICATION_PROFILE_V5` = v4 +
`battery-pcs-controller/charge-requested-power`, unit kW. This follows the v2–v4 precedent and
D-2026-09-22-contract-version-scope.
- **One correction:** the published value must be the **mean kW over the step**, because the role
  `storage_charge_requested_power` is in kW.
  - Encode it the way v4 encodes `pcs_discharge_capability`. If that convention is energy per step converted at
    publication, "× step hours" is right; if not, publish kW directly.
  - Pin it with a test: published kW equals `max(−requested, 0)` for a step with a known request.
- v5 and publication v4 are unchanged, and every test that pins them keeps passing untouched.

**(b): accepted. Use the controller's raw request**, `max(−requested, 0)`, not the converter-limited `charge_cap`.
The role means the storage's charge obligation, which is what the controller asks for. The converter limit is a
separate fact.

**(a): every Kobo day, both trial runs included, behind a hard identity gate.**
- **Why:** with the trial runs left on v5, the trial-after day 10-30 (a forecast spare-solar day) would read
  "limited". The S+1 board's 5-day view would then show no spare solar at all, and the opportunity would surface
  only on S+2.
- **Manifests:** the new manifest `d-verification-window-v3.json` (v6 + publication v5) is used by the demo
  producer for all Kobo days. `d-verification-window-v2.json` stays byte-unchanged, so the host and S6 tests that
  pin v2 digests are not touched.
- **Gate (the builder runs it on a local prepare before the slice is reviewed).** The trial verification on the
  v3 build must equal the current polish build exactly:
  - Action verification verdict;
  - the verification window figures (`feeder_demand_kwh`, `pv_available_kwh`, `unserved_critical_kwh`, `below_reserve_seconds`);
  - the trial cost check `change_per_demand_kwh` and intervention cost;
  - the S and S+1 dispatch results (avoidable and unclear minutes);
  - the S Finding's consequence;
  - finish check 17/17 plus WK checks.
  - Record a before/after table in the packet.
- **Fallback:** if any of those differ, the trial runs (trial-before, trial-after) stay on v5/publication v4, and
  only the other days move to v6/v5. Report the difference.
  - Then 10-30 reads "limited" for spare solar.
  - WALK1-5's no-assessed-day text applies: **"Not available yet · spare solar not checked on the last 5 days"**,
    replacing `SOLAR_NOT_READ` when the 5-day window has no assessed day. Add this to WALK1-5.
  - The G2 finish check then looks for spare solar on S+2 instead of S+1.
- **Forecast (the builder's, not tuned):** eligible 10-16, 10-23, 10-30, 10-31 (battery full at noon); 30%-charge
  days not eligible. The builder reports actuals.

Logged as D-W1-7 (v6 model and publication v5), D-W1-8 (raw request) and D-W1-9 (all days behind the identity gate, with fallback)
in `.agent/decisions-while-owner-away-2026-11-02.md`.

---

## Addendum 5 (2026-11-02): WALK1-4 phase 1, why every midday check reads "limited", and WK-2. Owner away; logged as D-W1-10..13.

Handoff: `AssetOpsV1-w1e/.agent/WALK1-4-phase-1-handoff.md`. The identity gate passed, so Addendum 4's fallback is not used.

**1. Readings bound under a superseded binding revision (a pre-existing defect in the mini depth read). Fix it in WALK1-4.**
- **Rule (D-W1-10):** each accepted reading is judged under **its own as-accepted binding revision**, as S3 dispatch
  and `assessment_inputs.py` already do. Today the read drops a reading whose binding is not in the current set.
- **`mini_depth/store.py` `read_hour_rows`** gains `row_bindings`. These are the `signal_binding_revision` rows whose
  id is any selected row's `binding_revision_id`, read by id whatever their set's `superseded_at`, the same way
  `row_foundations` is read.
- **`mini_depth/inputs.py`** (loop at `:249-251`) uses the row's own binding `b` = `by_id.get(r[13])` or
  `row_bindings.get(r[13])`. It is accepted only when all four hold:
  - `b.role == r.role`;
  - `b.asset_id == r.asset_id`;
  - `b` was in force at `r.source_time`;
  - the pinned roles-4 set covering the hour has a binding with the **same role and asset** in force at
    `r.source_time`. The meaning is unchanged; only the revision differs.
  - Otherwise it is skipped, as today.
- **Lineage:** the revision's `binding_set_revision_ids` lists the pinned set plus every as-accepted set used,
  sorted. The input digest therefore records the old revisions.
- **Tests:**
  - a split set (pre-split readings plus post-split pinned set, same role and asset) gives the readings selected;
  - a different asset under the old revision is still skipped;
  - the lineage lists both sets;
  - regression on `test_w402_*` and the mini depth projection tests, all unchanged.

**2. Accepted (D-W1-11): measure the charge request at `@{plant.battery}`.** The role is battery-typed and bound on
`battery`. Addendum 4's `@{pcs}` was my error. The value rule, `max(−requested, 0)` as mean kW, is unchanged.
Update `test_mini_grid_v6.py`.

**3. Accepted (D-W1-12): publication v5 sends `pv-inverter-controller/ac-power` (`pv_power`) at a 5-minute cadence.**
- The 15-minute publication leaves two thirds of each hour unreported, so the gap is real under v4. The check
  needs a complete hour.
- This is a reporting choice inside the new, unreviewed profile v5; v4 is untouched.
- S3 dispatch and the trial verification read `pv_available_power`, not `pv_power`. Even so, **rerun the identity
  gate** after 1–3 and record the table again. If any gated value moves, stop and report.

**4. WK-2: my expectation was wrong; the data and calendar are right (D-W1-13).**
- **Error source:** "42.08 USD on S" used the DEMO-A date S = 10-29.
  - The polish build has S = 10-30, so 10-29 is S−1. The walk1e build has S = 10-31 because the calendar is
    relative to the build date.
  - In both builds the mill measures 168.3 kWh on the cloudy, generator-needed days (S−28, S−21, S−3, S−1) and
    **0 kWh on the sunny days** (S−14, S−7, S, S+1), which are also the forecast spare-solar days.
- **The client lands on day S** (the `kobo-board-S` capture, the Portfolio week to S). S correctly shows no sales.
  - With the Addendum 3 L3 rule, once WALK1-5 adds spare solar, S leads with the spare-solar headline.
  - The "Productive-use sales" line reads "0 kWh used by Grain mill in {h} measured hours".
  - That is the story and needs no calendar change: on sunny days the mill sits idle while midday solar is spare,
    which is exactly the productive-use opportunity.
  - MG-1 month to date on S (polish) = 4 × 168.3 = 673.2 kWh ≥ 300 → MET, as Addendum 2 forecast.
- **WK-2 becomes two checks:**
  - **WK-2a:** on day **S−1**, the Kobo Grow `headline_money` = 42.08 USD (168.3 kWh × 0.25) and the headline is
    "estimated productive-use sales";
  - **WK-2b:** on day S, the Grow headline has no money and the "Productive-use sales" line starts "0 kWh used by Grain mill".
- **New capture key `kobo-board-S-minus-1`** (Kobo board, day S−1), so the walkthrough shows a priced sales day.
- **Calendar: not changed.** Flagged to the owner as information only. The demo day shows no mill sales because
  the mill is idle on sunny days, and the sales figure is shown on S−1.
- G2 forecast restated in build-relative days: spare solar on S−14, S−7, S and S+1.
  - S board 5-day view (S−4..S): S−3 and S−1 have no spare solar, S does → "Spare solar on 1 of 3 well-observed days"
    with the headroom headline.
  - S+1 board: "2 of 4".
  - The builder reports actuals; the G2 finish check asserts only that S shows a spare-solar contributor line.

---

## Addendum 6 (2026-11-02): WALK1-3b review M1, M2, Q1, Q2 (`.agent/review-WALK1-3b.md`). Owner away; logged as D-W1-14..16.

**M1: confirmed.** `read.py` `_summary_row` sends `short_value` when `row["state"] == OPPORTUNITY or row.get("potential")`.
Add the reviewer's summary test: a declared MG-1, an open headroom signal and no money give a non-null `short_value`.

**Q2 / L1: copy (D-W1-14).** `objective_facts.assure_text` becomes:
`"{met} of {n} declared objectives met"`, followed in this order, each part only when its count > 0, by:
- `" · {p} on pace"` (ON_PACE);
- `" · {b} behind pace"` (BEHIND_PACE);
- `" · {t} too early to judge"` (TOO_EARLY);
- `" · {u} not checked yet"` (NOT_JUDGED and None only).

MISSED is counted in `n` only, as today. Pin each part, and the order, in a test; add the strings to `COPY`.

**M2: honest "Too early" is accepted; G1 is prepared on a date that lands past it; demo-date rule (D-W1-15).**
- **Calendar arithmetic.** The Kobo story days relative to S are S−28, S−21, S−14, S−7, S−3, S−1, S, S+1. With S on
  day 1, 2 or 3 of a month, only 1–2 checked days fall in that month, so MG-1 is correctly "Too early to judge".
  From day 4 on there are at least 3.
- **WK-4 asserts the rule, not one outcome.** Let `c` be the checked days in S's month (from the reading):
  - if `c` ≥ the minimum, Grow state is On track or Watch and the MG-1 line contains "so far this month";
  - otherwise the line ends "too early to judge (needs {k} checked days)" and the state is Unknown.
  - Either way, the test fails if the text and state disagree.
- **G1 is prepared today, 11-02 (S = 10-31).** Any day when S is day 4 or later of its month also works, which means
  avoiding prepare days 3–5 of a month. The expected S figure is the reviewer's, "673.3 kWh so far this month, on 7
  of 30 days checked" (mill 0 kWh on S), Met. My earlier 673.2 was a rounding of 4 × 168.3.
- **Demo script rule** (for the client-demo sequence step): prepare the demo build on a date whose S (prepare day −2)
  is day 4 or later of its month. If that cannot be done, the board's "Too early to judge (needs 3 checked days)"
  is honest and the script says so. The story calendar is not changed.

**Q1 / L2: bump both (D-W1-16).** `outcome-status/2` → `outcome-status/3` (rule order changed);
`outcome-objectives/1` → `outcome-objectives/2` (verdict set and month reading). Update the tests that pin them.

**Q3, Q4:** residual risks as the reviewer states; no action.

---

## Addendum 7 (2026-11-02): WALK1-5 pre-flight F3 (no what-if authoring screen). Owner away; logged as D-W1-17.

**Ruling: (b) now; (a) is parked for the owner; (c) is refused.** The v70 marks the what-if authoring screen as
"to be designed with the owner" (screens.js:712), so building it without the owner would break the mock-is-layout-spec
rule. Showing the declared price read-only also fixes the false "No tariff declared" line on Kobo.

**WALK1-5 second half, about 1 unit, in `frontend/src/sites/MiniOpportunity.tsx` `ConsequenceBasis` and its route container:**
- **Data.** The container reads `getAssumptions` for `productive_use_price_per_kwh` (the WALK1-3 Addendum 3 M2
  series) and passes `declaredPrice: {value, currency} | null | "unavailable"` to the page. No new endpoint.
- **"Tariff" row.** The label stays "Tariff" (mock).
  - declared: **"Declared price · {p} {cur} per kWh"**;
  - not declared: **"No price per kWh declared"**;
  - read failed: **"Not available yet · the declared price could not be loaded"**.
  - When a what-if is linked, today's "Unavailable in this read" stays.
- **New row "Value at declared price"** (key `declared_value`), placed after "Tariff".
  - Shown only when `status == "SUPPORTED"`, the headroom bound is known and the price is declared:
    **"Up to {lo×p}–{hi×p} {cur} for each hour the spare solar is used · estimate, not sales"**.
  - The amounts use exact Decimal, 2 decimals ROUND_HALF_UP; one amount when lo = hi.
  - Otherwise the row is omitted.
  - This multiplies two shown figures; nothing is stored, projected over days or added up.
- **"Gross sales"** stays tied to a stored what-if, as today.
- **Tests (vitest):** the three Tariff states, the value row present or absent, rounding, and a vocabulary scan.
  - **Pre-flight F4:** the existing row label "Scenario energy" contains a guard-banned word. Check whether the
    strict capture gate counts it on this page. If it does, rename it **"What-if energy"** and register it under R686.

**G2:** the `kobo-whatif` capture key is replaced by **`kobo-opportunity`**, the Kobo productive-use opportunity page
from the S+1 board's Opportunity issue. Add a finish check: its Tariff row starts "Declared price".

**R686 is re-scoped** to: "Opportunity page Tariff line shows the declared productive-use price; added 'Value at
declared price' row (not in mock); what-if authoring not built (mock placeholder, to be designed with the owner)".
Use D2 for the added row and D1 for authoring not available.

**(a) is parked.** A productive-use what-if authoring slice is for the owner's design session. It prefills the
declared price, is labelled "Declared price" or "Entered for this what-if", and uses the existing create endpoint
(`mini_decisions/scenarios.py:119`). It is listed for the owner in the decisions log.

---

## Addendum 8 (2026-11-02): WALK1-5 re-review H1, which price instant the opportunity page asks for. Owner away; logged as D-W1-18.

**Ruling: price as of the study, at the Site-local noon of the study's last day.** This is the reviewer's proposal,
and it also settles KD3.
- **Instant:** `validAt` = the start of the **latest noon window the opportunity study used**, taken from the
  opportunity body's pinned renewable day rows (their window starts are already the Site-local 12:00 hour). It is
  sent as the ISO UTC instant. `recordedAt` stays the page's single `known_at`, as now.
  - Fallback when the body has no study day: the page window's last instant (`to` − 1 s).
  - Never omit `validAt`. Without it the server returns no selection, and the page then wrongly says "No price per kWh declared".
- **Consistency:**
  - The board prices at its own day (`ports.assumption(start)`, the UTC start of the board day,
    `site_outcomes/read.py:231,283`). The Assumptions page lists the whole timeline.
  - All three read the same declared series, each priced at the instant its figure describes. The board and the
    page can differ only if a price changes inside one day. In that case each is right for its own instant, so no
    change to the board.
  - The value row's text is unchanged; its price is the price in force for the hours studied.
- **WK-6** sends the same `valid_at` (from the S+1 opportunity body) and asserts selection PRICED and Tariff "Declared price · 0.25 USD per kWh".
- **Tests:**
  - The vitest asserts the outgoing `getAssumptions` query carries `validAt` = the latest study noon, plus the
    fallback case. The fixture must model the server: no `validAt` gives no selection, so a missing `validAt`
    fails the test.
  - One backend read test pins that selection is null without `valid_at` (existing behaviour, now documented).

---

## Addendum 9 (2026-11-02): G2 capture defects D1-D5 (`AssetOpsV1-polC/.agent/WALK1-G2-report.md`). Owner away; logged as D-W1-19..23.

**One fix slice, WALK1-6, about 3 units, frontend only. No prepare and no backend change**, so it captures over the
current G2 build with Vite from the slice worktree (Addendum 3 frontend rule). Scoped tier. Register ids R694-R699.
Re-capture strictly: `ev-board-fault` (1440 and 390), `kobo-opportunity` (both widths), `portfolio-week`, plus the
three Kobo board keys for the shared money format. 0 counted hits and no overflow required.

**D1. EV money panel: income under a cost title, and overflow at 390 (D-W1-19).**
- `EvSiteViews.tsx:733` panel heading: on the EV board it is always the charging-income slot (EV has no cost
  money), so it becomes **"Estimated income"**. Cold keeps "Possible cost". Register R694 (D2: the v69/v70 slot
  label is "Possible cost").
- ESTIMATED value: split the amount from its words.
  - `.ev-site-amount` (nowrap) holds only **"{cur} {money2(amount)}"**, for example "USD 4.50".
  - It is followed by a wrapping line **"estimated charging income"**, using the metric's existing label/caption class.
  - Remove the nowrap from that line. Other states are unchanged.
- The prose line stays.
- Tests: vitest pins the value and caption. The 390 capture must show no overflow.

**D2. "load" on the Kobo opportunity page (D-W1-20).** Every visible string in `MiniOpportunity.tsx` matching
`\bload\b` changes:

| Old | New |
|---|---|
| label "Proposed load" | "Proposed new use" |
| "No load proposed" | "No new use proposed" |
| "No load what-if" | "No what-if for a new use" |
| "…for a one-hour productive load in {n} adequately observed windows." | "…for one hour of added productive use in {n} adequately observed windows." |
| "…no added load has been validated." | "…no added use has been checked yet." |
| "…schedule any proposed load, and check…" | "…schedule any proposed new use, and check…" |
| "…before a load decision." | "…before deciding on a new use." |

- The builder sweeps the whole file for any other `load` in visible text (wire field names are not text), lists
  each change in the packet and adds the strings to R655.
- Vitest vocabulary scan over the page.

**D3. Money format (D-W1-21).** Every outcome-board money amount displays with **2 decimals**.
- `OutcomeBoard.tsx` `boardMoneyText` formats each bound with the existing `money2` rule. Move `money2` from
  `EvSiteViews.tsx` to a shared `frontend/src/ui/money.ts` and import it in both places.
- Shape unchanged: "4.50 USD"; ranges "{low} to {high} {cur}".
- This fixes the Portfolio Grow value ("4.50 USD estimated") and its detail at once, because both use `boardMoneyText`.
  The server keeps sending exact amounts.
- Tests: "4.50000" → "4.50", "42.075" per money2's rule, ranges, null.

**D4. Assure "No objective declared" for Kobo is correct per outcome; the wording misleads (D-W1-22).**
- **Why it is correct:** the dots show each Site's Assure row state. Kobo's declared target (MG-1) belongs to Grow,
  so its Assure row has none.
- **Copy:**
  - On Portfolio card dots (title and text), a row state `NO_OBJECTIVE` reads **"No target for this outcome"**.
    This is a frontend word override; the board chips stay as they are.
  - The Assure detail clause "targets declared at {n} sites" becomes **"targets declared at {n} sites, for any outcome"**.
  - Register R697 (D2).
- Tests: vitest for the dot word and the clause.

**D5. Strip "Opportunity: None found…" against the board's Opportunity chip (D-W1-23).**
- The strip counts reviewed opportunity *findings*. The board chip is an open opportunity *signal* (spare solar).
  Both are true but read as a contradiction.
- **Copy and logic (frontend only):**
  - The strip label becomes **"Opportunity findings"**.
  - When the outcome summary shows any Site whose Grow row has state OPPORTUNITY or a non-null `short_value` (sent
    when `potential` is set, Addendum 6 M1), append **" · {k} site with an open opportunity on its board"**
    ("sites" for k > 1).
  - The zero/withheld texts stay as Addendum 1 rules them.
- Expected on G2: "Opportunity findings: None found on the days checked · 1 site with an open opportunity on its board".
- Register R698 (D2). Tests: vitest with and without such a Site.

**Noted, as designed (no change):**
- The opportunity's "Value at declared price" row is absent because the study is "evidence limited" (five-day study incomplete).
- Kobo S+1 reads "too early to judge" (1 checked day in November).
- Both are honest. The walkthrough script names S as the demo day.
