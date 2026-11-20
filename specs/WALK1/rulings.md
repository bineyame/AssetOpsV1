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

