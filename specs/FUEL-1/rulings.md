## 2. MV-1 ruling: mill dollars on the verdict page (ready to build)

### 2.1 Code reality (main `da40bf5e7`)

- The verdict read: `VerificationService.domain_summary` (`B/actions/verification.py:378-396`) → `summary_wire` (`B/actions/verification_families.py:384-419`). The head always carries `"cost_check": None, "trial_hours": None` (`:390`).
- Stored outcome details carry the exact sums and the shown means (`verification_families.py:363-366`): `details.baseline = {days, sum_kwh, mean_kwh_per_day}` and `details.later = {days, sum_kwh, mean_kwh_per_day}`. Means are cents, half-even (`mean_text`, `:260-261`). The R7 line shows those same means (`:232`, `:315`).
- The plan basis stores the Site timezone (`plan["basis"]["timezone"]`, `:163`). `local_midnight(day, tz)` exists (`:102-103`).
- The productive price is published at Kobo as `productive_use_price_per_kwh` v1, 0.25 USD, `valid_from 2026-01-01T00:00:00Z`, open-ended, basis AUTHORED_ESTIMATE (`backend/conversions/demo-productive-price-publications.json`). It is recorded at install + 1 h (`T/demo_combined_kobo.py:137-149`), before every story day.
- The verification service has no productive-price port. The only price port is the diesel `trial_comparison.price_selection` (`B/financials/composition.py:141-154`), through `fuel_cost.select_window_price`. That function refuses any key or unit other than the diesel ones (`fuel_cost.py`, the `PRICE_UNIT_MISMATCH` line in `select_window_price`).
- Money display: `chain/vocabulary.py:304` `money2` (two places, half even). `actions` already imports `chain`.
- The page: `F/sites/SiteMillVerification.tsx:69-113`. The client type: `F/sites/millVerificationClient.ts`.
- Finish row MILL-3 reads the page at `T/demo_combined_finish.py:771-795`.

### 2.2 Build: backend

**(a) `B/financials/fuel_cost.py`: two keyword arguments, nothing else.**
- `select_window_price(assignments, revisions, window_start, window_end, *, key: str = PRICE_KEY, unit: str = PRICE_UNIT)`.
- The unit check line becomes `if rev.get("assumption_key", key) != key or rev.get("unit") != unit:`. Every existing caller passes no keyword, so its behaviour is byte-equal.
- Do not touch `PARAMETER_VERSION`, `MODEL_ID` or anything else in this module.

**(b) `B/financials/composition.py`: one new builder.**
- Add `build_productive_price_selection(database_url) -> Callable[[UUID, UUID, datetime, datetime, datetime], PriceSelection]`.
- It mirrors `price_selection` at `:150-152`:
  - `snap = prices.snapshot(tenant, site, PRODUCTIVE_PRICE_KEY, known_at, 0, 1)`;
  - `return fuel_cost.select_window_price(snap["timeline"], snap["cited"], start, end, key=PRODUCTIVE_PRICE_KEY, unit="currency/kWh")`.
- Import `PRODUCTIVE_PRICE_KEY` and `unit_for` from `financials/assumptions.py`, and use `unit_for(PRODUCTIVE_PRICE_KEY)` rather than retyping the unit.

**(c) `B/actions/verification.py`.**
- `VerificationPorts` gains `productive_price: Callable[[UUID, UUID, datetime, datetime, datetime], Any] | None = None`, documented: "MV-1: the declared productive-use price over one span as known at a cutoff (`PriceSelection`); None: the mill value reads UNPRICED".
- `domain_summary`: when `outcomes` is non-empty and `outcomes[0]["outcome"] == "VERIFIED"`, compute the price selection:
  - `tz = plan["basis"]["timezone"]`;
  - `lo = local_midnight(min(baseline days), tz)`;
  - `hi = local_midnight(max(later days) + 1 day, tz)`. The days are `outcomes[0]["details"]["baseline"]["days"]` and `["later"]["days"]`, parsed with `date.fromisoformat`;
  - `known_at = outcomes[0]["recorded_at"]` (the price as known when the verdict was recorded, so a later price publication never changes a shown verdict);
  - `price = port(tenant_id, site_id, lo, hi, known_at)` when the port exists, else `None`.
- Pass `price=price` to `summary_wire`. For any other state, pass nothing.

**(d) `B/actions/composition.py:122`.** Wire `productive_price=build_productive_price_selection(database_url)` into the `VerificationPorts(...)` call. `evaluate_domain_plans` (`:127-141`) is unchanged: it never reads the page.

**(e) `B/actions/verification_families.py`: constants, one pure function, one wire key.**

Constants, verbatim:
```python
#: MV-1 (FUEL-1 §2): the mill value line of a VERIFIED outcome. The arithmetic uses the SHOWN means and the shown
#: price, so the line reproduces by hand.
VALUE_BASIS = "ESTIMATED_SALES_AT_DECLARED_PRICE"
VALUE_TEXT = ("About {d} {cur} a day more in estimated sales to productive users: ({a} − {b}) kWh a day × your "
              "declared {p} {cur} per kWh, on {n} fully checked days before and after the change")
VALUE_COST_TEXT = "No cost is recorded for this change"
VALUE_UNPRICED_TEXT = "No sales estimate: {why}"
VALUE_UNPRICED_WHY = {
    "NO_PRICE": "no price per kWh is declared for productive users",
    "PRICE_SPANS_WINDOW": "the declared price per kWh changed between the two periods",
}
VALUE_UNPRICED_OTHER = "the declared price per kWh could not be read"
```
- The `−` in `VALUE_TEXT` is U+2212, the same as the mock's minus. If guard V or N rejects any of these literals, stop (S3).

`mill_value(details: Mapping[str, Any], outcome: str, price: Any) -> dict[str, Any] | None`, pure:
1. Return None unless `outcome == VERIFIED`.
2. `b = details["baseline"]["mean_kwh_per_day"]` and `a = details["later"]["mean_kwh_per_day"]`, the stored cent strings. `nb = len(details["baseline"]["days"])` and `nl = len(details["later"]["days"])`.
3. Return None (and `LOG.warning`) when any of these holds: `a` or `b` is None, `Decimal(a) <= Decimal(b)`, or `nb != MIN_DAYS or nl != MIN_DAYS`. None of them is reachable for a VERIFIED outcome. They are guards, never a zero.
4. **Not priced.** When `price is None`, or `price.state != "PRICED"`, or `price.value is None`:
   - `reason = None if price is None else price.reason`;
   - `why = VALUE_UNPRICED_WHY.get(reason, VALUE_UNPRICED_OTHER)`;
   - return `{"state": "UNPRICED", "reason": reason or "PRICE_UNREADABLE", "basis": VALUE_BASIS, "per_day": None, "before_per_day": None, "after_per_day": None, "currency": None, "price": None, "text": VALUE_UNPRICED_TEXT.format(why=why), "cost_text": VALUE_COST_TEXT}`.
5. **Priced:**
   - `p = Decimal(str(price.value))` and `p_txt = _price_text(price.value)`;
   - `per_day = money2((Decimal(a) - Decimal(b)) * p)`, `before = money2(Decimal(b) * p)`, `after = money2(Decimal(a) * p)`;
   - return `{"state": "PRICED", "reason": None, "basis": VALUE_BASIS, "per_day": per_day, "before_per_day": before, "after_per_day": after, "currency": price.currency, "price": {"revision_id": price.revision_id, "value": p_txt, "currency": price.currency}, "text": VALUE_TEXT.format(d=per_day, cur=price.currency, a=a, b=b, p=p_txt, n=nl), "cost_text": VALUE_COST_TEXT}`.
- `_price_text(value)` is a private copy of the rule in `B/site_outcomes/mini.py:348-355` `price_text` (two places, more only when the stored value has them, ROUND_HALF_UP). Copy it rather than import it: `actions` must not import `site_outcomes`. A parity test pins the two functions together (2.4).

`summary_wire(ctx, outcomes, live, price=None)`:
- Add `"value": None` to `head`, so every state carries the key.
- In the stored-outcome branch, set `value = mill_value(o["details"], o["outcome"], price)`.
- Nothing else changes, including the key order of the existing keys.

**(f) Worked example, the demo figures (for the packet, not typed into any test).**
- Stored means 42.00 and 110.00, price 0.25 USD, 3 and 3 days:
  - per_day = (110.00 − 42.00) × 0.25 = 17.00;
  - before 10.50, after 27.50.
- Text: "About 17.00 USD a day more in estimated sales to productive users: (110.00 − 42.00) kWh a day × your declared 0.25 USD per kWh, on 3 fully checked days before and after the change".

### 2.3 Build: frontend

**`F/sites/millVerificationClient.ts`**
- Add:
  ```ts
  export interface MillValue {
    state: "PRICED" | "UNPRICED";
    reason: string | null;
    basis: string;
    per_day: string | null;
    before_per_day: string | null;
    after_per_day: string | null;
    currency: string | null;
    price: { revision_id: string; value: string; currency: string } | null;
    text: string;
    cost_text: string;
  }
  ```
- `MillVerification` gains `value: MillValue | null`. The parser accepts `value` absent or null as null. An object with a non-string `text` or `cost_text` is a parse error, the client's existing error state.

**`F/sites/SiteMillVerification.tsx`** (`MillVerificationPanel`)
- After the `lines` paragraphs and before the table, render, when `body.value !== null`:
  ```tsx
  <p data-mill-value={body.value.state}>{body.value.text}</p>
  <p data-mill-cost>{body.value.cost_text}</p>
  ```
- Use the same element and class as the lines: no new CSS and no layout change. The browser never formats a number; both strings are the server's.
- Header comment: add **MOCK DEVIATION MD-FUEL-MV1-1**:
  - v70 has no mill verdict page (D1, R700);
  - the value and cost lines are new;
  - the page shows a single basis (estimated sales at the declared price), so the mock rule "lines with different bases are not added together" (v69 `:482`) holds.
- The visible `mock-deviation-line` paragraph stays byte-equal.

### 2.4 Tests

- **L0, `backend/tests/test_ch9b3_mill_verdict.py`** (add tests; existing ones stay green):
  1. VERIFIED, means "42.00" and "110.00", price PRICED 0.25 USD: `value.state == "PRICED"`, `per_day == "17.00"`, `before_per_day == "10.50"`, `after_per_day == "27.50"`, and `text == VALUE_TEXT.format(...)` built from those inputs.
  2. Reproduce-by-hand property, over a small grid of means ("0.01", "41.99", "42.00", "109.995"-style cents) and prices ("0.25", "0.255", "1", "0.1"): `Decimal(per_day) == (Decimal(a) - Decimal(b)) * Decimal(price)` quantized half-even to cents.
  3. UNPRICED for each of NO_PRICE, PRICE_SPANS_WINDOW, PRICE_CONFLICT (falls back to `VALUE_UNPRICED_OTHER`) and `price=None` (reason `PRICE_UNREADABLE`). Each has `per_day` None and `cost_text == VALUE_COST_TEXT`.
  4. `value is None` for INEFFECTIVE, INCONCLUSIVE, NOT_JUDGED (live), NO_PLAN, and for VERIFIED with an equal-means guard.
  5. Every state's body has the key `value`, and every pre-existing key is unchanged. Extend `test_summary_wire_reads_the_stored_outcome_and_the_not_judged_state`, keeping its existing assertions.
  6. `_price_text` parity with `site_outcomes.mini.price_text` on "0.25", "0.255", "1", "0.1", "12.5".
- **L0, `backend/tests/test_s4_fuel_cost.py`:**
  - one test: `select_window_price(..., key=PRODUCTIVE_PRICE_KEY, unit="currency/kWh")` is PRICED on a productive revision;
  - the default call on the same revision is still `PRICE_UNIT_MISMATCH`.
- **L2, `backend/tests/test_ch9b3_mill_verdict_postgres.py`** (own DB):
  - one test: a VERIFIED outcome with a productive price v1 published (from `demo-productive-price-publications.json`), read through the composed service, has `value.state == "PRICED"` and the price revision id;
  - one test: a price `valid_from` after the first baseline day gives `UNPRICED` / `PRICE_SPANS_WINDOW`.
- **Frontend, `F/sites/__tests__/millVerification.test.tsx`** (vitest, list the file):
  - VERIFIED with a PRICED value renders both lines;
  - UNPRICED renders its text and the cost line;
  - `value: null` renders neither;
  - the parser accepts a body without `value` (as null).
- **Finish row, `T/demo_combined_finish.py`: new `@row("MILL-3b")`** after MILL-3:
  - read the same page;
  - expected `per_day = money2((Decimal(metrics[0].after) - Decimal(metrics[0].before)) * Decimal(v1.value))`, with v1 read from `backend/conversions/demo-productive-price-publications.json`;
  - assert `value.state == "PRICED"`, `value.per_day == expected`, `value.text == VALUE_TEXT.format(...)` (import the constant), and `value.cost_text == VALUE_COST_TEXT`;
  - return the line.
  - This row runs at E3, not now. Add an L0 self-test with a fixture page body, in the test file that already covers `demo_rows.mill_page` (grep), or a new `backend/tests/test_mv1_finish_row.py`.
- **Guards:** A, W, N, V, M, and `node tools/checks/frontend-hardwiring.mjs` (the count must not rise).
- **Not run:** the full suite, prepare, baseline build, `test_demo_combined_postgres`, check-all.

### 2.5 Stops (report to the Architect; never design around them)

- **S1.** Any byte change to an existing key of the verdict body, other than the added `value`.
- **S2.** The productive `snapshot` does not return v1 at the outcome's `recorded_at` on L2 (for example a recorded-time rule that differs from the diesel series).
- **S3.** A guard (V, N or the vocabulary guard) rejects a literal in 2.2(e). Report the guard's message and a proposed wording; do not reword silently.
- **S4.** Making `actions` read the price needs any import from `site_outcomes`, `estate` or `chain_api` (a layering guard).
- **S5.** The work exceeds 0.75 unit.

### 2.6 Branch, worktree, DB, reading budget

- Branch `task/FUEL-MV1-mill-dollars`, cut from main at or after `da40bf5e7`. Worktree `C:\Users\assef\Bineyame\AssetOpsV1-mv1` (the builder creates both).
- DB: pg_harness base `ASSETOPS_TEST_DATABASE_URL` → `assetops_mv1_test` on 127.0.0.1:55432 (run-owned clones `assetops_mv1_pt*_test`). Read credentials from the repo config; never guess them. Drop `assetops_mv1_*` after the merge.
- Reading budget: this section; `B/actions/verification_families.py:1-60`, `:220-443`; `B/actions/verification.py:40-72`, `:353-396`; `B/financials/composition.py:130-155`; `B/financials/fuel_cost.py` `select_window_price` only; `B/financials/assumptions.py:28-45`; `B/chain/vocabulary.py:300-322`; `B/site_outcomes/mini.py:348-355`; `F/sites/SiteMillVerification.tsx`; `F/sites/millVerificationClient.ts`; `T/demo_combined_finish.py:771-795`.
- **Size 0.5.** Owner: nothing to decide. The mill-cost question (section 7, Q4) changes only `VALUE_COST_TEXT`, and only if the owner gives a cost with a source.

---

## 3. Lane 1 unit cards (pre-flight completes the literals marked PRE-FLIGHT)

### 3.1 MB-1: the mill on the main board (BL-45), 1.25

**Cause.** Board thread lines and the Assure row read Finding threads only: `B/site_outcomes/mini.py:416`, `:475`; `B/site_outcomes/board.py:691-765` (`thread_line_item`, `thread_line_findings`). The estate count `count.verified_results` counts only threads with a **Finding** occurrence (`B/chain/claims.py:9-12`, `:59-85`). The mill thread is an opportunity thread whose Action is a `domain_action` with `origin_opportunity_id`. The DD-1b2b record shows the mill thread **RECURRED** on 10-31 ("Seen again" true; coordinator handoff).

**Rules (binding):**
- **R1, board thread line.** An opportunity thread with a linked opportunity-origin Action shows its thread line on the **Grow** row by the same `thread_line_item` kinds (BEFORE_CHANGE, MONITORING, CLOSED, RECURRED), on the same days, with the Action `ref` = the DOMAIN_VERDICT page. That ref is the one MILL-3 and F-THREADS already read (`T/demo_combined_finish.py:799-813`). The Finding-thread path stays byte-equal for Kobo ACT-001, Cold and EV.
- **R2, Assure row.** The Assure row's "Verified results" contributor lists the mill Action when its decisive domain outcome is VERIFIED and known at the board cutoff. It uses the existing `VERIFICATION_TEXT["VERIFIED"]` with the mill's display code, linking to the verdict page. INEFFECTIVE and INCONCLUSIVE use their existing texts, and NOT_JUDGED uses the pending text.
- **R3, the count.** `count.verified_results` = the Finding-thread verified count (**unchanged**) **plus** the opportunity-origin domain Actions of the Site whose decisive outcome is VERIFIED, recorded at or before `k`, and whose opportunity thread has an occurrence meeting `[lo, hi)`. They are counted per Action, and only once.
  - A later recurrence does **not** remove a verified result. The check passed; the board's "Seen again" line says the problem can still appear. This is two true, separately scoped claims.
  - `count.open_threads` keeps its thread rule. On S+0 the mill may be both "seen again" (open) and a verified result. DS-1 narrates it.
- **R4.** No Cold or EV byte changes. Kobo's Optimize and Protect rows are byte-equal.

**Expected client view (DD1b2-R5 M1 table, option (ii)):**
- S-8: Grow thread line "Checked and working"-class wording (the existing MONITORING literal; PRE-FLIGHT confirms which kind applies as known at S-8).
- S-5: Assure "No verified result yet" (the verdict was recorded 10-31 23:00Z, after that local day).
- S+0: Assure "2 verified results", the mill among them.

**Measurements owed, M1 before code:** on a DB with the mill story. PRE-FLIGHT names it: `assetops_mechanism_test` if it carries an opportunity-origin Action, else a fixture-built L2. Record per story day S-11, S-8, S-5, S+0:
- the mill thread state as known;
- the domain outcome and its `recorded_at`;
- today's Assure count and Grow thread lines.
- If no DB carries the mill story, MB-1 proves R1–R3 on L0/L2 fixtures, and E3 confirms (finish rows below).

**Tests:**
- `test_out_b2_mini.py`, `test_out_b3_cold_ev.py` (Cold/EV byte-equal), `test_ch6b2_portfolio_cards.py`, `test_demo_combined_ex1.py` (3 verified-count references; computed, not typed);
- a new `backend/tests/test_mb1_opportunity_board.py` (R1–R3 truth table, including "recurred after verified");
- the COH re-expectation in `T/checks/chain_coherence.py` (Assure count == board), with a self-test case.
- Fast tier for shared board code.

**Finish rows (written, run at E3):**
- MILL-4: the S+0 Kobo board Grow row carries the mill thread line with the DOMAIN_VERDICT ref;
- MILL-5: the Assure count equals the Finding-thread verified count + 1, computed from the stored rows;
- update F-THREADS.

**Stops:**
- any Cold or EV byte change;
- the opportunity thread has no reachable Action link (the R0 link port missing at read time);
- R3 needs a schema change;
- more than 1.5 units.

### 3.2 WD-1: money wording (BL-48), 0.15

- Kobo: `MG1_NO_DAY` (`B/chain/vocabulary.py:268`) and its board twin `MG1_ACTUAL` (`B/site_outcomes/mini.py:127`, which must stay equal) change from "sales not recorded" to **"no fully checked day counted yet this month"**.
- Depot (EV): the Grow headline must never read `TARIFF_ESTIMATE` ("estimated charging income") without an amount on the same row.
  - PRE-FLIGHT M1: read the fault day's Grow row (`B/site_outcomes/ev.py:191`, `:229`) and record whether `priced` is true while the chain claim is NOT_KNOWN.
  - Fix: the headline uses `TARIFF_ESTIMATE` only when the row's shown money (the chain earnings claim the row renders) has a value. Otherwise it reads **"No income figure for this day: it is not fully checked"**.
- Tests: the existing MG-1 and EV row tests updated by import (never retyped); one new case each.
- Guards V and N. Finish rows WK-1 and WK-4 import the constants.

### 3.3 PV-1: Portfolio verified-value lines (item 3), 0.75

- **ONE-SOURCE.** The Assure card's value lines come from the per-Site board Assure rows, the way CH-5d1's Optimize card reads `nodes.earnings`.
- PV-1 adds `verified_values` to the Assure row nodes (`B/site_outcomes/mini.py`): one entry per verified result that has a money value, `{key, site, action_code, basis, text}`.
  - **Mill** (basis `ESTIMATED_SALES_AT_DECLARED_PRICE`): `mill_value(...)` from MV-1, over the same price port.
    - Line: **"{site} · {code}: about {d} {cur} a day more in estimated sales to productive users (your declared price)"**.
  - **Trial fuel** (basis `TRIAL_HOUR_MODELLED_FUEL`): the cost check's stored `priced_total` (A2), credited only by `outcomes/credit.py` `credited`.
    - Line: **"{site} · {code}: about {l} L, {amount} {cur} less diesel in the one-hour trial (modelled, not metered)"**.
- **Card.** In `portfolio_cards`, the Assure card gains `parts.value_lines`: a list of those texts in Site order, then Action display-code order. **There is no total, no sum, and no Decimal arithmetic across lines.**
- **Card note.** `card_notes` (`B/estate/portfolio.py:658-668`): when at least one value line exists, the recovered clause reads **"Each result's money is shown on its own and never added together"**. Otherwise it keeps `MONEY_NOT_CREDITED`.
- **Frontend.** `F/estate/PortfolioOutcomes.tsx` renders `parts.value_lines` as lines on the Assure card, the same way Grow renders its parts. No new CSS.
- **MOCK DEVIATION MD-FUEL-PV1-1:**
  - v69 `:129` is a "Verified value recovered" tile reading "Not established", and v70 `:492` puts the slot on the Assure card;
  - we show per-basis lines in that slot instead of one value, because v69 `:131` and `:482` forbid a combined total.
- **COH-17 row V1:** each Site's board `verified_values` texts equal the card's lines for that Site, and no card field holds a sum of two amounts. Add a self-test pass and fail case.
- **Tests:**
  - `test_ch6b2_portfolio_cards.py` (Grow, Protect and Optimize byte-equal);
  - a new `test_pv1_value_lines.py`: 0, 1 and 2 lines; mill plus fuel never summed (assert that no field contains the Decimal sum); order; the note text;
  - `estatePortfolio.test.tsx` and `portfolioFixtures.ts`.
- **Finish rows (written, run at E3):** PV-A, the Assure card on S+0 lists the mill line and the trial-fuel line, each equal to its source row, with no total.
- **Stops:**
  - any change to Grow, Protect or Optimize cards;
  - a value line needs a price read the board does not already make (then the Architect rules where it lives);
  - more than 1.0 unit.

---

## MB-1-R: ruling on the MB-1 pre-flight (Architect, Claude, 2026-11-07)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `826d91572` (CH-5d1 merged, so MB-1 code may start).
- This section **replaces §3.1's build detail**. §3.1's cause, R1–R4 and stops stand except where amended here.
- Paths: `B/` = `backend/assetops_backend/`, `T/` = `tools/`. READ = I read the code; nothing below was measured on a DB.

### 0. Code reality the ruling rests on (READ)

- **The lifecycle already runs the mill thread end to end.**
  - `_OUTCOMES` (`B/chain/adapters/postgres_thread_sources.py:67-72`) reads domain outcomes and dates a VERIFIED from the plan's `effective_from` (CH9b3-R Q10). The known time is the outcome's `recorded_at`.
  - `run_lifecycle` (`B/chain/lifecycle_run.py:109-143`) plans every thread of the Site, opportunity threads included.
  - `thread_clean_days` (`:102-106`) uses `clean_day_measures[mechanism]`. For `PRODUCTIVE_USE_HEADROOM` that is `["daylight_headroom_kw"]` (`config/chain/thread-lifecycle-v1.json`), a SITE measure (`B/chain/measures.py:49-50`).
  - `maybe_close` writes CLOSED after `close_after` such days.
  - So the mill thread has real RESOLVED_MONITORING / CLOSED / RECURRED events and real fully checked days. **The MONITORING count is computed, never set to `close_after`.**
- **Domain verdicts are single.** `evaluate` stores one decisive outcome and replays it after that (`B/actions/verification_families.py:207-209`). `domain_summary` reads `outcomes[0]`, ordered by `(recorded_at, id)`.
- **The mini board reads "as known now".** It is read with `date` only (`T/demo_combined_finish.py:82-85`), so `known_at` is None (`board_cutoff` mini, `B/site_outcomes/read.py:839-843`).
  - ACT-001's Assure state is the current verification summary (`ChainRequest.action_facts`, `B/chain/read.py:404-416`).
  - The Grow thread line reads every visible event: S-8 shows the VERIFIED state, back-dated to the change day.
  - Assure lists the Actions **created in the 31-day work window** `[work_lo, end)` (`site_window`, `B/actions/adapters/postgres_action_store.py:1046-1062`; `mini.py:402`).
- **Thread lines are attached in `read.py` `board()`** (`with_threads`, `:455`), after `mini.compose`. The Assure headline and contributors are built **inside** `compose` (`mini.py:430-481`, `_assure` `:974-1000`).
- **`board.py` does not list the mill.**
  - In hand / Earlier skip any Action with no `origin_finding_id` (`board.py:842-843`).
  - The mini `facts.actions` come from the trial Action index only.
  - So carrying the mill in a **new** `SiteFacts` field leaves those lists byte-equal (R4), as the builder found.
- `/estate/chain` `sites[].threads` is `EstateCounts.threads[code]` (`B/chain_api.py:346`). No frontend reads it (grep).
- The summary's `verified_result_count` is not rendered anywhere in the frontend (grep). It feeds COH L2 only.
- **An L2 fixture already makes a real VERIFIED mill outcome.**
  - `backend/tests/test_ch9b3_mill_verdict_postgres.py` provides `_frozen`, `_later` and `_after`.
  - `test_ch9b1_opportunity_actions_postgres.py` provides `mill`, `_threads` and `_lifecycle`, which link the Action to the opportunity thread and write the lifecycle events.

### 1. Decisions

**Q1, the verdict read: approved, as the builder recommends, with one shared pure function.**
- **(a) `B/chain/adapters/postgres_chain_read.py` `_SITE_ACTIONS`.**
  - Add one `LEFT JOIN LATERAL` and two output columns. No schema change, no new statement, no `k` in the SQL:
  ```sql
  SELECT ..., accepted_at, v.outcome, v.recorded_at AS outcome_recorded_at
    FROM chain_action a
    LEFT JOIN LATERAL (SELECT o.outcome, o.recorded_at FROM verification_outcome o
                        WHERE a.kind = 'DOMAIN_INTENT' AND o.tenant_id = a.tenant_id AND o.domain_action_id = a.id
                        ORDER BY o.recorded_at, o.id LIMIT 1) v ON true
   WHERE ... (unchanged) ORDER BY a.action_code, a.id
  ```
  - MINI_TRIAL rows carry NULL in both columns.
  - Update the comment above `_ACTION_PLANS` / `_ACTION_OUTCOMES`: "domain verdicts are read on `_SITE_ACTIONS` (MB-1-R Q1)".
- **(b) New pure function in `B/chain/site_chain.py`**, beside `actions_of`. Its signature and contract are verbatim:
  ```python
  def opportunity_actions(rows: Mapping[str, Any], *, site: str, tz: str | None, cutoff: datetime | None,
                          lo: datetime, hi: datetime) -> list[dict[str, Any]]:
      """MB-1 (FUEL-1 MB-1-R Q1/Q4): the Site's opportunity-origin domain Actions shown in `[lo, hi)` as of `cutoff`:
      kind DOMAIN_INTENT with `origin_opportunity_id` set and a thread; `accepted_at < hi` and (cutoff None or
      `accepted_at <= cutoff`); and the thread has an occurrence with an `opportunity_id` whose episode meets
      `[lo, hi)` (the `_finding_threads` predicate, claims.py:59-66). `outcome` is the stored decisive outcome when
      its `outcome_recorded_at` is known by `cutoff` (None = every one), else None (not judged as known)."""
  ```
  - Each item is `{"action_id", "code", "thread_id", "origin_opportunity_id", "accepted_at", "outcome", "outcome_recorded_at", "ref"}`.
  - `ref = action_wire_ref(site, a)`, which is DOMAIN_VERDICT for these rows.
  - Order: `(code or "", action_id)`.
  - Read every new key with `.get`, so a row without the columns gives `outcome` None.
- **(c) `B/site_outcomes/mini.py` `MiniPorts` gains, last and defaulted:**
  ```python
  #: MB-1 (FUEL-1 MB-1-R Q1): `ChainRequest.threads(site_id)` at the request cutoff, that cutoff, and the thread
  #: lifecycle policy (`chain.composition.thread_lifecycle_policy()`); None = no chain reader (no opportunity Actions).
  chain_threads: Callable[[], Any] = lambda: None
  ```
  - The port returns a frozen dataclass declared in `mini.py`: `ChainThreads(rows: Mapping[str, Any], k: datetime | None, policy: Any)`.
  - `B/site_outcomes/read.py` `mini_ports` binds it as `chain_threads=lambda: mini.ChainThreads(chain().threads(sid), chain().k, thread_lifecycle_policy())`.
  - Import `thread_lifecycle_policy` locally inside the binding, the way `B/estate/adapters/postgres_estate_read.py` reads it.
  - `ChainRequest.threads` is memoised on `(tenant, site, k)`, so the board and `claims.py` read the same rows in one request. That is the builder's "one read" goal.
  - Cold and EV ports are untouched.
- **Extra files approved:** `postgres_chain_read.py` (a), `site_chain.py` (b), `site_outcomes/read.py` (the binding and Q5's `_verified_results`), and the two fakes in `backend/tests/test_ch5a2_contract.py:61,239`.
  - In each fake, add the two keys to its DOMAIN_INTENT rows, or confirm with a one-line comment that it has none.
  - **No other extra file.**

**Q2, the thread line: approved, with one change.** The mill's thread view is built in `mini.compose` and carried on a new `SiteFacts` field. It is not built in `read.py` or `with_threads`. The Finding path stays byte-equal. Details are in MB-1b (§3).

**Q3, the MONITORING line:**
- **The measures and subject are the lifecycle runner's own.**
  - The fully checked days are `lc.fully_checked_days(rows, subject_ref, policy.measures_for(mechanism), occurrence start days)`.
  - Its inputs:
    - `rows` = the board's own snapshot rows, `day_facts.rows` (the `chain_day` read over the work window at `k`, the same cutoff `lookup` uses);
    - `subject_ref` and `mechanism` from the thread's occurrence rows;
    - the start days of **every** visible occurrence of the thread (`thread_clean_days`'s rule).
- **Yes, the runner closes opportunity threads** (§0).
- **k is computed, never `close_after`.** One guard: if the view's verified day is earlier than the first day of the work window, the board cannot see every checked day. The MONITORING line is then **omitted** (no line), never a wrong count. This cannot happen in the demo, because the verified day S-9 lies inside every story board's window.
- **Wording: not "Fix verified" for an opportunity thread.** A mill change is not a fix of a fault, and the thread page already labels RESOLVED_MONITORING "Checked and working" (`THREAD_STATE_WORDS`). The opportunity thread gets three plain literals in `board.py` (§3.2).

**Q4, the Assure window: the builder's occurrence rule, plus `accepted_at < end`.**
- The board's Assure row uses `opportunity_actions(rows, lo=work_lo, hi=end, cutoff=k)`. That means: accepted before the board day ends and by `k`, and the thread's opportunity occurrence meets the board's 31-day work window.
- Without `accepted_at < end`, S-11 would list an Action raised on S-9. The board must never show an Action not yet raised on its day.
- **§3.1's expected S-5 Assure ("No verified result yet") is withdrawn.**
  - The mini board reads "as known now" (§0), so on S-8, S-5 and S+0 the mill is listed as verified.
  - This is the same reading as ACT-001's state, and as the Grow line's "checked and working" on S-8.
  - "No verified result yet" on S-5 beside "Change checked and working" on S-8 would contradict itself on screen.
  - With an explicit `known_at` before the verdict's `recorded_at` (10-31 23:00Z), the mill is listed as **not yet verified** (Pending chip). The `cutoff` filter does this.
  - DS-1 narrates S-8 the way DD-1's script line already does: "The day after the change, the mill is checked and working" (`build-sheet-DD-1.md:2611`).

**Q5, coherence checks:**
- **The claim (R3) and the board use the same function, `opportunity_actions`, with their own windows.** The claim uses the estate `[lo, hi)` at `lifecycle_cutoff(k)`; the board uses `[work_lo, end)` at `k`. This is the existing Finding pattern (board work window vs estate window).
- **L2 stays as it is.** `_verified_results` (`read.py:481`) becomes the board's Assure headline number, so the summary sum now includes the mill.
  - L2 remains a cross-window check, as it is today for ACT-001.
  - E3 expectation: L2 holds on week and month, because the recurrence occurrence (RECURRED 10-31) meets the week and the first occurrence (S-13) meets the month.
  - If, and only if, L2 fires at E3 on a window where the mill thread has **no** occurrence, the expectation file carries one entry for that window. Reason: "MB-1-R Q5: board 31-day window vs estate window, mill thread has no occurrence in the window". Any other L2 difference is a fault.
- **L3 is re-expected.**
  - The rule: distinct Verified Finding threads in the table **plus** the Σ over sites of `threads.verified_actions` equals the claim.
  - The bundle already carries `chain_estate.{w}` `sites[].threads`. MB-1a adds the key there (§2.2), so no new bundle body is needed.
  - An absent key reads as 0, so stored older bundles stay valid.
- **The card's "Assure count == board" check is a board-internal row: COH-17 A1.**
  - It runs on each mini Site's `board_summary.{w}.{code}`.
  - The Assure headline count must equal the number of Assure `verified_results` contributors that read as verified. Both sides come from one board on one day, so windows never differ.
  - The claim-vs-board comparison stays with L2.

**Q6, size: split.**
- With Q1–Q5 as ruled, the builder's 1.4–1.6 is at or over the 1.5 stop. The split also lets PV-1 depend on the Assure half only.
- **MB-1a** (read, claims, Assure, COH L2/L3/A1, MILL-5): **0.8**.
- **MB-1b** (Grow thread line, MILL-4, F-THREADS): **0.55**.
- Total 1.35 (+0.1 on §3.1's 1.25). Lane 1 becomes 2.75.

**M1, no DB carries the mill story: enough as ruled.** The proof stack is:
- L0 truth tables (pure);
- **one L2 on real rows** built from the CH-9b fixtures (VERIFIED domain outcome, linked thread, lifecycle run), for the SQL columns, `opportunity_actions` and the claim;
- E3: MILL-4, MILL-5, F-THREADS and COH L2/L3/A1 on the full prepare, before any demo build.
- No scratch prepare is added (owner budget). An E3 failure comes back to the Architect as a fix round, never a reworded expectation.

### 2. MB-1a card: the mill in the Assure row and the count, 0.8

**Branch and worktree.** Use the existing worktree `C:\Users\assef\Bineyame\AssetOpsV1-mb1` on its branch. Rebase it onto main `826d91572` or later first. DB: pg_harness base `assetops_mb1_test` (run-owned `assetops_mb1_pt*_test`). Drop them after the merge.

**2.1 Files (complete list)**
- `B/chain/adapters/postgres_chain_read.py`: Q1(a).
- `B/chain/site_chain.py`: Q1(b).
- `B/chain/claims.py`: 2.2.
- `B/site_outcomes/mini.py`: `ChainThreads`, the port, 2.3.
- `B/site_outcomes/board.py`: the `OpportunityActionFact` dataclass and the `SiteFacts` field only (2.3). **No line logic in MB-1a.**
- `B/site_outcomes/read.py`: the binding and `_verified_results`.
- `T/checks/chain_coherence.py` and `T/checks/test_chain_coherence.py`: L3, A1.
- `T/demo_combined_finish.py`: MILL-5.
- Tests per 2.5.

**2.2 `claims.py` (R3 as amended)**
- New function:
  ```python
  def verified_actions(req: Any, site: Any, lo: datetime, hi: datetime, counted: set[str]) -> list[dict[str, Any]]:
      """MB-1-R (R3): the Site's opportunity-origin domain Actions verified as known at `k` whose thread has an
      opportunity occurrence meeting `[lo, hi)`, counted per Action; an Action on a thread already counted (`counted`
      thread ids) is not counted again."""
      acts = site_chain.opportunity_actions(req.threads(site.site_id), site=site.site_code, tz=site.timezone,
                                            cutoff=lifecycle_cutoff(req.k), lo=lo, hi=hi)
      return [a for a in acts if a["outcome"] == "VERIFIED" and a["thread_id"] not in counted]
  ```
- `estate_count_claims`: inside the existing `try`, after `counted = counted_threads(...)`:
  - `threads[code] = {**classify(t["state"] for t in counted), "verified_actions": len(verified_actions(req, site, lo, hi, {t["id"] for t in counted}))}`;
  - `verified_n = sum(t["verified"] + t["verified_actions"] for t in per) if known else None`.
- `open_n`, `disrupted` and `priority_site_count` are unchanged.
- Update the module docstring's "Threads" bullet and the `EstateCounts.threads` comment: `{"open", "in_hand", "verified", "verified_actions"}`.
- R3 stands: a later RECURRED does not remove the verified Action, because the count reads the outcome, not the thread state.

**2.3 The board's Assure row (`mini.py`, `board.py`)**
- `board.py`:
  ```python
  @dataclass(frozen=True)
  class OpportunityActionFact:
      """MB-1-R: an opportunity-origin domain Action on a mini board (the mill); never in `actions`, so In hand and
      Earlier are unchanged (R4)."""
      action_id: str
      code: str | None
      thread_id: str
      outcome: str | None                 # VERIFIED | INEFFECTIVE | INCONCLUSIVE known by the cutoff; None = not judged
      verdict_ref: Mapping[str, Any]      # the DOMAIN_VERDICT Ref (`site_chain.action_wire_ref`)
  ```
  - `SiteFacts` gains `opportunity_actions: tuple[OpportunityActionFact, ...] = ()`, last field.
  - MB-1b adds defaulted fields to the dataclass. MB-1a adds nothing else to `board.py`.
- `mini.compose`, after `actions` is built:
  - `ct = reads.call("chain_threads", ports.chain_threads)`;
  - `opp = () if ct is None else tuple(OpportunityActionFact(a["action_id"], a["code"], a["thread_id"], a["outcome"], a["ref"]) for a in site_chain.opportunity_actions(ct.rows, site=c, tz=site_timezone, cutoff=ct.k, lo=work_lo, hi=end))`.
  - A failed read is recorded by `Reads` (board PARTIAL) and shows no mill. That is never a "0" claim.
  - Pass `opp` to `SiteFacts(opportunity_actions=opp)`.
- `verified` (`mini.py:475`) becomes `sum(1 for a in actions if a.verification_state == "VERIFIED") + sum(1 for o in opp if o.outcome == "VERIFIED")`.
- `_assure(..., opp)`. The Verified results entries are one merged list.
  - `mine` (trials, unchanged) plus `opp`, sorted together by `(code or "", id)`.
  - The empty and not-available branches test the merged list: `if actions_failed and not merged` / `elif not merged`.
  - Each trial entry is byte-equal to today.
  - Each opp entry is a `Contributor("verified_results", "Verified results", VERIFICATION_TEXT[s].format(code=display_code(o.code), suffix=provenance_suffix(None)), PENDING_CHIP if s == "PENDING" else None, o.verdict_ref)`, with `s = o.outcome if o.outcome in ("VERIFIED", "INEFFECTIVE", "INCONCLUSIVE") else "PENDING"`.
  - **No new literal.** VERIFIED_WITH_COST never applies (no cost check), so no money appears on this line before PV-1.
- `read.py:481`: `"_verified_results": sum(1 for a in comp.facts.actions if a.verification_state == "VERIFIED") + sum(1 for o in comp.facts.opportunity_actions if o.outcome == "VERIFIED")`.
- Header comment in `mini.py` beside `_assure`: **MOCK DEVIATION MD-FUEL-MB1-1**.
  - v69 lists verified Actions under Assure "Verified results", each opening its Action.
  - The mill has no Action page (v70 D1), so its entry opens the verdict page (DOMAIN_VERDICT), as the chain wire already does (DD1b2-R6 O1).
  - Add a packet row with the same id.

**Client wording (S+0 Kobo, as known now):**
- Assure headline: **"2 verified results"**.
- Contributors: **"ACT-000001 verified"** and **"ACT-000002 verified"**, each with its own link. The order is by code; the codes shown are whatever the DB holds.
- Kobo Grow, Optimize and Protect rows: byte-equal in MB-1a.

**2.4 COH (`T/checks/chain_coherence.py`)**
- **L3** (`:1317-1321`):
  - `mill = sum(int((x.get("threads") or {}).get("verified_actions") or 0) for x in chain.get("sites") or ())`;
  - `check("L3", len(verified) + mill == want, f"{len(verified)} distinct Verified threads in the table + {mill} verified opportunity Actions, claim {want!r}", where)`.
  - Update its comment to cite MB-1-R Q5.
- **A1**, inside the COH-17 per-Site board loop (after V2/V4), for `site.get("domain") == MINI_DOMAIN` only:
  - Take the Assure row of `board`.
  - `shown = 0 if headline == NO_VERIFIED else int(m.group(1))`, with `m = re.fullmatch(r"(\d+) verified results?", headline)`.
  - Import `NO_VERIFIED` locally from `assetops_backend.site_outcomes.mini`. Any other headline is a finding "unreadable Assure headline".
  - `listed` = the count of Assure contributors with `key == "verified_results"` whose text matches `r"\S+ verified\b.*"` and does **not** contain " not yet verified".
  - `check("A1", shown == listed, f"Assure headline {headline!r}, {listed} verified entries", where, code)`.
- **Self-tests, `T/checks/test_chain_coherence.py`:**
  - L3 pass: table has 1 Verified thread, Kobo `verified_actions` 1, claim 2.
  - L3 fail: the same with `verified_actions` 0.
  - L3 legacy: key absent, claim 1, table 1, passes. The existing L3 parametrised case stays.
  - A1 pass: "2 verified results" with two verified entries and one "not yet verified" entry.
  - A1 fail: "2 verified results" with one verified entry.
  - A1 zero: `NO_VERIFIED`, no verified entry, passes.
  - A1 cases run only on a mini Site, and a cold Site board is skipped.

**2.5 Tests**
- **New `backend/tests/test_mb1_opportunity_board.py` (L0):**
  1. `opportunity_actions` truth table, one row per rule:
     - MINI_TRIAL ignored;
     - a domain intent with `origin_finding_id` ignored;
     - `accepted_at == hi` excluded;
     - `accepted_at > cutoff` excluded;
     - no opportunity occurrence meeting `[lo, hi)` excluded;
     - outcome recorded after cutoff gives `outcome` None;
     - cutoff None sees the outcome;
     - a row without the new keys gives `outcome` None;
     - `ref.kind == "DOMAIN_VERDICT"`.
  2. Claims with a fake `req`:
     - 1 verified Finding thread + mill VERIFIED → `count.verified_results` 2 and `threads[code]["verified_actions"] == 1`;
     - mill INEFFECTIVE → 1;
     - mill thread also counted as a Finding thread → counted once;
     - **recurred after verified** (the thread's last event RECURRED) → still 2;
     - `count.open_threads` unchanged by the mill (opportunity-only thread);
     - a failed thread read → every claim NOT_KNOWN, as today.
  3. Compose with fake ports:
     - S+0 shape → headline `f"{2} verified results"`, built from the constants;
     - entries in code order; the mill entry's `link_ref` is DOMAIN_VERDICT;
     - outcome None → "… not yet verified" with the Pending chip;
     - `chain_threads` raising → board PARTIAL, `chain_threads` in `failed`, no mill entry, headline from the trials only;
     - `chain_threads` default (None) → body byte-equal to the same fake without the port.
  4. `_verified_results` equals the headline's number on the S+0 fake.
- **New `backend/tests/test_mb1_site_actions_postgres.py` (L2, own DB).** Sequence:
  1. `_threads(mill, ("b",))`;
  2. `_frozen(mill, "mb1")` (from `test_ch9b3_mill_verdict_postgres`);
  3. `_threads(mill, ("b", "c"))`;
  4. `_later(mill, eff, "11.5")`; `clock.at = _after(eff, tz, 5)`; `evaluate_domain_plan` → VERIFIED;
  5. `_lifecycle(mill)`.
  - Assert:
    - `PostgresChainRead(URL).site_threads(t, s, None)` has the mill row with `outcome == "VERIFIED"` and `outcome_recorded_at` equal to the stored row;
    - with `known_at` one second before that `recorded_at`, `opportunity_actions` gives `outcome` None;
    - the trial-shaped rows (none here) and the column count of a MINI_TRIAL row are covered by L0;
    - `opportunity_actions` over the real rows with the occurrence's window gives one item;
    - `estate_count_claims` through a `ChainReader` on this DB gives `threads[code]["verified_actions"] == 1`.
  - If the fixtures cannot be combined in this order within 0.1 unit, stop (S-a).
- **Existing tests, updated by import, never retyped:**
  - `test_ch5a2_contract.py` (fakes);
  - `test_out_b2_mini.py`;
  - `test_out_b3_cold_ev.py` (Cold and EV byte-equal; must pass unchanged);
  - `test_ch6b2_portfolio_cards.py` (`threads` dict gains `verified_actions`; Grow, Protect and Optimize cards byte-equal);
  - `test_demo_combined_ex1.py` (its 3 verified-count references stay computed);
  - `T/checks/test_chain_coherence.py`.
- **Finish row MILL-5 (written now, runs at E3), in `T/demo_combined_finish.py` after F-THREADS.** On the S+0 Kobo board and the week `/api/estate/chain`, assert:
  - the Assure row has a contributor whose `link_ref` is `{"kind": "DOMAIN_VERDICT", "id": <mill id>}`, with text `VERIFICATION_TEXT["VERIFIED"].format(code=display_code(code), suffix=provenance_suffix(None))`;
  - the headline count equals the count of verified entries;
  - the week claim `count.verified_results` equals `Σ threads.verified + Σ threads.verified_actions`, with Kobo's `verified_actions == 1`;
  - SQL: the mill's one `verification_outcome` is VERIFIED.
  - Add an L0 self-test with fixture bodies (pass and fail) beside the MILL-3b one.
- **Guards:** A, W, N, V, M, and `node tools/checks/frontend-hardwiring.mjs` (the count does not rise). Fast tier for the shared board code (`board.py`, `mini.py`, `read.py`).
- **Not run:** the full suite, prepare, baseline build.

**2.6 Stops (report; never design around)**
- **S-a.** The L2 fixture order fails.
- **S-b.** Any Cold or EV byte change, or any Kobo Grow, Optimize or Protect row change.
- **S-c.** The mill opportunity thread has no reachable link at read time (`_SITE_ACTIONS` gives no DOMAIN_INTENT row with `thread_id`).
- **S-d.** Guard A rejects the local `thread_lifecycle_policy` import in `read.py`. Report the message.
- **S-e.** Any change needs a schema change.
- **S-f.** The work exceeds 0.9 unit.

### 3. MB-1b card: the mill's thread line on Grow, 0.55

**Depends on MB-1a merged.** Branch `task/FUEL-MB1b-mill-thread-line` from main after MB-1a. Worktree `C:\Users\assef\Bineyame\AssetOpsV1-mb1b`. DB `assetops_mb1b_test`. A3's copy edits wait for MB-1b, not MB-1a (shared `board.py` and `mini.py`). PV-1 needs MB-1a only.

**3.1 Files.** `B/site_outcomes/mini.py` (the view), `B/site_outcomes/board.py` (fields, literals, line function, `_row`), `T/demo_combined_finish.py` (MILL-4, F-THREADS), and tests per 3.4. No other file.

**3.2 Literals, `board.py`, beside `THREAD_MONITORING`, verbatim:**
```python
#: MB-1-R Q3: the thread line of an opportunity thread (the mill): a change to use spare solar, not a fix of a fault;
#: "checked and working" is the thread page's own word for RESOLVED_MONITORING.
OPP_THREAD_MONITORING = "Change checked and working ({code}) · {k} more fully checked days to close"
OPP_THREAD_CLOSED = "Change checked and closed ({code}) · spare solar not seen again in {n} fully checked days"
OPP_THREAD_SEEN_AGAIN = "Spare solar seen again on {day} after the change ({code})"
```
- BEFORE_CHANGE reuses `THREAD_BEFORE` alone ("Before the change on {e}"), with no "after the change" suffix. The suffix judges the row's state on another day, and the Grow row has no such judge. A bare true line is better than "not judged yet", which can be false. This kind is unreachable on the story's built days.
- Add all three to `test_out_b2_vocabulary.py`'s list beside `THREAD_MONITORING` (`:78-79`).
- If guard V or N rejects any of them, stop (S-g) with the message and a proposed wording.

**3.3 Build**
- `OpportunityActionFact` gains these defaulted fields: `view: Mapping[str, Any] | None = None`, `action_segment: int | None = None`, `category: str | None = None`, `count_known: bool = True`.
- In `mini.compose`, for each opp item, with `ct`, `day` (the board day), `site_timezone` and `day_facts`:
  1. **Occurrences.** Take the thread's occurrence rows with `episode_start < end` (started by the board day; the rows are already visible at `k`). `latest` is the one with the highest `occurrence_no`.
     - None, `day_facts` None or `site_timezone` None → `view = None`.
  2. `evs = lc.visible(<the thread's events from ct.rows, as site_chain._events>, ct.k)`.
  3. `starts` = the local start day of **every** visible occurrence of the thread. `complete = lc.fully_checked_days(day_facts.rows, latest["subject_ref"], ct.policy.measures_for(latest["mechanism"]), starts)`.
  4. `view = lc.thread_view(evs, lc.Occurrence(latest["opportunity_id"] or latest["finding_id"], local start day), day, ct.k, complete, ct.policy.close_after(SITE_TYPE_OF_DOMAIN[MINI]))`.
  5. `count_known = verified_day is None or verified_day >= local_days(work_lo, end, tz)[0]`. Here `verified_day` is the last `RESOLVED_MONITORING` effective day ≤ `day` in `view["events"]`.
  6. `action_segment`: the `segment_no` of this Action in `site_chain.actions_of(ct.rows, [thread_id], site=c, tz=site_timezone, cutoff=ct.k, verification={})`. Reuse it, never re-derive.
  7. `category`: the first MOVES category of `categories_for(thread_signal_key(latest["mechanism"]), MINI)`. It is `GROW_REVENUE` for the mill; a test pins that.
- `board.py`:
  - Lift `thread_line_item`'s inner `item` into a module-level `_line_item(...)`. Its keys, key order and values are unchanged, and `thread_line_item` calls it. **Every existing thread-line output is byte-equal** (existing tests pin it).
  - Add `opportunity_line_item(o: OpportunityActionFact, facts: SiteFacts) -> dict | None`, with `d = facts.day`, `v = o.view`, `code = display_code(o.code)`. Return None when `v` or `d` is None. Otherwise the first matching case applies:
    1. `e = v["change_day"]`, and `e` is set with `d < e` → `BEFORE_CHANGE`, `THREAD_BEFORE.format(e=_short_day(e))`, effective `e`;
    2. `v["state"] == "RECURRED"`, `o.action_segment` is set and less than `v["segment_no"]`, and `v["recurred_day"]` is set → `RECURRED`, `OPP_THREAD_SEEN_AGAIN.format(day=_short_day(v["recurred_day"]), code=code)`;
    3. `v["state"] == "CLOSED"` and `o.action_segment == v["segment_no"]` → `CLOSED`, `OPP_THREAD_CLOSED.format(code=code, n=n)`, `clean=n`, with `n = int(v["close_after"])`;
    4. `v["state"] == "RESOLVED_MONITORING"`, `o.action_segment == v["segment_no"]` and `o.count_known` → `MONITORING`, `OPP_THREAD_MONITORING.format(code=code, k=r)`, `remaining=r`, with `r = max(0, n - int(v["checked_days"]))`;
    5. anything else → None.
  - In every case: `thread_id = o.thread_id`, `action_code = o.code`, `ref = refs.thread_ref(site, thread_id)` (the thread page, whose Action link is already the verdict page).
  - `_row` (`board.py:950-957`): after the Finding loop, for `o` in `sorted(facts.opportunity_actions, key=(code or "", id))` with `o.category == cat`, append `opportunity_line_item(o, facts)` when it is not None and its text is new. The subline joins as today.
  - Header comment: **MOCK DEVIATION MD-FUEL-MB1-2**.
    - v69's Grow row has no thread line.
    - The CH-3 thread line (already a deviation on the Optimize row) now also appears on Grow for an opportunity thread, in opportunity wording.
    - Add a packet row.

**Expected client view (computed at E3 by MILL-4, never typed):**

| Story day | Grow row, the mill's line |
|---|---|
| S-11 | none (the Action is not raised yet) |
| S-8 | "Change checked and working (ACT-000002) · {k} more fully checked days to close" |
| S-5, S-1, S+0 | "Spare solar seen again on 31 Oct after the change (ACT-000002)", if the 10-31 recurrence is a visible started occurrence; else the S-8 kind |

**3.4 Tests**
- **New `backend/tests/test_mb1_thread_line.py` (L0):**
  - one case per kind: MONITORING with `r` computed from given complete days, CLOSED, RECURRED, BEFORE_CHANGE, and None;
  - `count_known` False gives no MONITORING line;
  - S-8 selection: a later occurrence starting after the board day is excluded, so the line is MONITORING, not RECURRED;
  - a RECURRED view with the Action in the same segment gives None;
  - **parity:** `complete` equals `lifecycle_run.thread_clean_days` over the same snapshot and occurrence rows;
  - `category == "GROW_REVENUE"` for `PRODUCTIVE_USE_HEADROOM`;
  - the Grow subline equals the sales subline plus " · " plus the line;
  - Kobo Optimize and Protect rows byte-equal with and without the mill.
- **Existing tests:**
  - `test_ch3_rows.py` (Finding lines byte-equal);
  - `test_out_b2_mini.py`;
  - `test_out_b3_cold_ev.py` (must pass unchanged);
  - `test_out_b2_vocabulary.py`;
  - `T/checks/test_chain_coherence.py` (COH-14 reads `kind`, unchanged; run it).
- **Finish rows (written now, run at E3):**
  - **MILL-4.** The S+0 and S-8 Kobo boards' Grow `thread_lines` hold one item with `action_code` = the mill code and `kind` in (MONITORING, CLOSED, RECURRED). Its `text` equals the matching literal formatted from the item's own fields (`remaining_days`, `clean_days`, `effective_day`), and `ref.kind == "THREAD"`.
  - **F-THREADS** adds: the S-8 Grow row carries the mill's line; report its kind and text.
  - Add an L0 self-test with a fixture body (pass and fail).
- **Guards:** as in MB-1a. Fast tier.

**3.5 Stops**
- **S-g.** A guard rejects a literal.
- **S-h.** Any existing thread-line byte change, or any Cold or EV change.
- **S-i.** `day_facts.rows` lacks `daylight_headroom_kw` on a day the lifecycle counted. The parity test shows it; report, never patch the count.
- **S-j.** The work exceeds 0.65 unit.

### 4. Plan and order delta

- **Lane 1:** MV-1 → **MB-1a (0.8) → MB-1b (0.55)** → WD-1 → PV-1. That is 2.75, against §1.1's 2.65.
- PV-1 depends on MB-1a (the Assure row and `OpportunityActionFact`), not on MB-1b. A3's copy edits depend on MB-1b.
- FUEL-1 total: +0.1 → **5.45**. The new plan total is ≈ 117.4.
- §3.1's "Expected client view" S-5 line is superseded by Q4.
- **Owner question: none.**

---

## A2-R1: ruling on review-A2 L1 and L4 (Architect, Claude, 2026-11-07)

Source: `.agent/review-A2.md` (A2 worktree) L1 and L4. This amends §4.2. It lands in **A2's current fix round**, beside H1. No golden is affected: the H1 goldens are `/1` or rate-less, and they carry no `priced_total`.

### L1: a priced total is stored only when it is a positive amount

- **Decision.** Keep the classification as it is. The state stays per demand kWh, which is the v1 rule that `/1` byte-equality and the board's per-kWh line rest on. Add `priced_total` only when its amount is above 0. A `priced_total` names fuel the trial hour did not burn. A negative total is not that, and it must not exist as a stored fact for any reader (Portfolio, `_cost_check_read`, A3, PV-1).
- **Rejected options.**
  - Guarding in A3's copy leaves a negative "total" stored, append-only, and exposed by `_cost_check_read`. Every later reader would then have to repeat the guard.
  - Reclassifying on the absolute difference changes v1 semantics and the state of rows that are already stored.
- **Code** (`backend/assetops_backend/financials/trial_fuel_comparison.py`, `compare`, `:196-200`):
  - compute `amount = bw["_cost"][0] - lw["_cost"][0]` first;
  - set `priced_total` only when `v2 and state == "MODELLED_IMPROVEMENT" and amount > 0`. The dict is unchanged otherwise.
  - Because `PRICE_BASIS_DIFFERS` guarantees one price revision, a positive price makes `amount > 0` equivalent to `fuel_change_l > 0`. A zero price gives no total, which is correct.
  - Add one clause to the module docstring (`:12`): "stored only when the amount is above 0".
  - The §4.2 bullet now reads: "on `MODELLED_IMPROVEMENT` **with a cost difference above 0**, the result gains `priced_total`".
- **Test** (`backend/tests/test_tfc2.py`, next to `test_no_improvement_has_no_priced_total`):
  - `test_improvement_with_more_fuel_in_the_later_hour_has_no_priced_total`:
    - `out = run(window(B0, 10, 0, ("b1",), Fraction(100)), window(L0, 10, 300, ("l1",), Fraction(110)))`;
    - assert `(out["formula"], out["state"]) == ("trial-fuel-comparison/2", "MODELLED_IMPROVEMENT")`;
    - assert `out["change_per_demand_kwh"]["nominal"] == vr.fmt(Fraction(1, 3520))`;
    - assert `"priced_total" not in out`;
    - assert `credit.credited({**out, "outcome_id": "outcome-1"}, "VERIFIED") is None`.
  - Non-vacuity: revert the `amount > 0` condition, and the test fails on the `priced_total` assertion. Record this in the packet.
  - Run `test_tfc2.py` and `test_ch3_rows.py` only (L0, no DB).
- **A3 consequence.** A3 needs no copy guard of its own. `COST_PRICED`, the Assure litres clause and the verification-page line key on the **presence** of `priced_total`, as §4.3 already says. A3 must not add a second sign check. Without the key, today's per-kWh lines stay.

### L4: D1 wording for `IDLE_SECONDS_UNKNOWN`

- **Decision** (`backend/assetops_backend/site_outcomes/board.py:90`):
  `"IDLE_SECONDS_UNKNOWN": "the generator's idle time is not known for one or both hours",`
- **Why not "for one of the hours".** The reason fires when either window's idle seconds are None, which includes both. "One or both" is true in every case, and it does not read as "neither".
- Delete the "builder-proposed ... Architect to confirm" comment at `:89` and replace it with `# FUEL-1 A2 (A2-R1): words for the two /2 reasons`. `NO_LOAD_RATE_DIFFERS` keeps its text.
- `GENERATOR_KWH_UNKNOWN` (`:85`, "not known for both hours") predates A2 and is shown on Kobo's stored rows. It is **not** changed here, and it goes to WD-1's money-wording pass as a note.
- **Guard.** The words reuse the already-passing vocabulary ("the generator's idle time is not known for") and add only "one or both". Run `backend/tests/test_out_e4_readback.py` (`test_no_code_on_screen_and_saving_only_in_not_realised_savings` and the reason-set test) to confirm.

**Owner question: none.**

---

