# Build sheet FUEL-1: mill dollars, the mill on the board, Portfolio value lines, money wording, idle fuel (Option A), and the diesel-heavy story

- Architect: Claude (fresh Architect, FUEL-1), 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `da40bf5e7`. Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `T/` = `tools/`.
- Owner decisions, verbatim (`.agent/owner-fuel-scope-2026-11-07.md`):
  - scope: "Both (~5.4 units) (Recommended)" (shortlist items 1–4 and Option A idle fuel, before the demo script);
  - idle rate: "Generic 3.3 L/h, labelled (Recommended)";
  - example tank: "Leave it, explain in 'Why?' (Recommended)";
  - diesel-heavy story: "inject days, i don't see why it should be mutually exclusive". Read as: build it as well, not instead. Timing and form go back to the owner with sizes (section 5 and section 7).
  - The mill goes on the main board. `.agent/owner-mill-route-2026-11-07.md` ("Fix link, use route") is superseded; BL-45 comes out of the backlog.
- Design basis: `.agent/feature-shortlist-2026-11-07.md` (items 1–4, B5, B6, B8) and `.agent/fuel-story-design-2026-11-07.md` (Option A, B2 probe, B3 options (i) and (ii), B5 literals, B6 fit). This sheet supersedes both where they differ.
- Rules that apply to every unit:
  - SCOPE-1: only what we can present defensibly.
  - Money comes only from evidence and declared prices. Never tune a number. Expected values are computed from the inputs, never typed from a run.
  - Never add money with different bases (v69 `:131`, `:482`). Never annualise.
  - The mock is the layout spec. Label every deviation MOCK DEVIATION, with an id, in a code comment and a packet row.
  - Localised tests only. No full suite, no prepare (except A3's one Kobo-only scratch prepare, below), no baseline build. Every test runs on its own `*_test` DB. Never `assetops_demo3_full_test`. No `-ExecutionPolicy`.
  - Each unit: own Opus first build and first review, Sonnet fix rounds and re-reviews. Pre-flight questions are batched into one message before any code.

---

## 1. Units, lanes, order and conflicts

### 1.1 Units

| Unit | What the client gets | Size | Lane | Depends on | Files (main ones) |
|---|---|---|---|---|---|
| **MV-1** mill dollars on the verdict page (item 1) | "About 17.00 USD a day more in estimated sales…" under "Target met", and "No cost is recorded for this change" | 0.5 | 1 | none (starts now, beside CH-5d1) | `B/actions/verification_families.py`, `B/actions/verification.py`, `B/actions/composition.py`, `B/financials/composition.py`, `B/financials/fuel_cost.py` (two keyword arguments only), `F/sites/SiteMillVerification.tsx`, `F/sites/millVerificationClient.ts`, `T/demo_combined_finish.py` (one row) |
| **MB-1** mill on the main board (item 2, BL-45) | The Kobo board shows the mill change with its thread line and verdict link; the Assure row and the Portfolio count include it | 1.25 (1.0–1.5) | 1 | CH-5d1 merged | `B/site_outcomes/board.py`, `B/site_outcomes/mini.py`, `B/chain/claims.py`, `T/checks/chain_coherence.py`, the board, Portfolio and COH tests |
| **WD-1** money wording (item 4, BL-48) | Kobo month sales line and the Depot fault-day income line say plainly why there is no figure | 0.15 | 1 | CH-5d1 merged (`chain/vocabulary.py`) | `B/chain/vocabulary.py:268`, `B/site_outcomes/mini.py` (`MG1_ACTUAL`), `B/site_outcomes/ev.py:229` |
| **PV-1** Portfolio verified-value lines (item 3) | The Assure card lists one value line per verified result, each with its own basis, and never a total | 0.75 | 1 | MV-1, MB-1, A2, CH-5d1 merged | `B/site_outcomes/read.py` (`portfolio_cards` Assure), `B/site_outcomes/mini.py` (Assure node values), `B/estate/portfolio.py` (`card_notes`), `B/chain/vocabulary.py` `CARD_TEXT`, `F/estate/PortfolioOutcomes.tsx`, COH-17 |
| **A1** fuel-cost-2 and the declared no-load fact | Nothing visible yet; the reviewed model that counts idle running | 0.85 | 2 | none (starts now, beside CH-5d1) | `B/sites/models.py` (vocabulary and carriers), `B/financials/fuel_cost_v2.py` (new), the consequence store and recompute, migration `0053`, model-id readers |
| **A2** trial-fuel-comparison/2, priced total, no-sum credit | Nothing visible yet; the trial's fuel change stored in litres and USD; the Portfolio rule never adds results | 0.55 | 2 | A1 merged | `B/actions/verification_rules.py` (window idle seconds), `B/financials/trial_fuel_comparison.py`, `B/actions/verification.py` (`_cost_check`, `_cost_check_read`), `B/outcomes/credit.py`, `B/estate/portfolio.py` (`recovered`) |
| **A3** idle fuel on Kobo's screens and story | Three "0 USD" mornings become idle-fuel lines; the trial's verdict shows litres and USD saved, labelled modelled and generic | 0.7 | 2 | A2 and MB-1 merged | `T/demo_combined_kobo.py` (declare the fact), `B/site_outcomes/mini.py` and `board.py` copy, the trial verification page, finish rows, COH; one Kobo-only scratch prepare |
| **E3 allowance** | finish-row runs and recaptures of the changed screens inside E3 | 0.35 | end-game | all of the above | none |
| *(done)* idle-fuel probe | | 0.25 | | | `.agent/fuel-story-design-2026-11-07.md` B2 |

**Remaining build: 5.1 units** (2.65 lane 1, 2.1 lane 2, 0.35 E3). With the probe already spent: 5.35, which is the owner's "about 5.4".

### 1.2 Order and parallel work

```
now:            CH-5d1 (in build, lane 2 worktree)   |  MV-1 (lane 1)   |  A1 (lane 2b)
after CH-5d1:   MB-1 (lane 1)                         |  A2 (after A1)
after MB-1:     WD-1 (lane 1, 0.15)                   |  A3 (after A2 and MB-1)
after A2+MB-1+MV-1:  PV-1 (lane 1)
then:           E3 allowance rows written (inside A3 / PV-1), DS-1, E1–E6
```

- Lane 1 = MV-1 → MB-1 → WD-1 → PV-1 (2.65). Lane 2 = A1 → A2 → A3 (2.1).
- A3 must not start its copy edits before MB-1 merges (shared `board.py` and `mini.py`). Lane 2 reaches A3 at about 1.4 units, while MB-1 finishes at about 1.75 on lane 1. The A3 builder starts with the parts that touch neither file (the Kobo declaration, the finish rows, the scratch-prepare plan) and rebases before the copy edits.
- MB-1's pre-flight (reading and measurement, no code) may run while CH-5d1 builds. MB-1 code starts only after CH-5d1 merges.
- Three builders run at once only during the "now" row (CH-5d1, MV-1, A1). Their files are disjoint.

### 1.3 File-overlap conflicts

| Pair | Shared file | Resolution |
|---|---|---|
| CH-5d1 ↔ MB-1 | `T/checks/chain_coherence.py`, `backend/tests/test_ch6b2_portfolio_cards.py` | MB-1 code starts after CH-5d1 merges |
| CH-5d1 ↔ WD-1, PV-1 | `B/chain/vocabulary.py` (CH-5d1 adds `CARD_TEXT` cost keys and `COST_SMALL`) | both after CH-5d1 |
| CH-5d1 ↔ PV-1 | `B/site_outcomes/read.py` `portfolio_cards`, `F/estate/PortfolioOutcomes.tsx` | PV-1 after CH-5d1; PV-1 edits the Assure card only, and the CH-5d1 Optimize card stays byte-equal |
| **CH-5d1 ↔ A3 (data, not files)** | none | After A3, Kobo's Optimize row `nodes.earnings` (`money.possible_extra_fuel_cost`) is **priced above zero** on the three idle mornings. So the CH-5d1 Optimize card will show a money value at E3, not the "Not known yet" that CH5d1-R §4 forecast. That is the intended effect of Option A, and CH-5d1's code does not change. CH5d1-R §4 "Owed at E3" is superseded by A3's finish rows (section 4.3). Tell the CH-5d1 lane; it needs no edit |
| MV-1 ↔ A1 | `B/financials/fuel_cost.py` | MV-1 adds two keyword arguments to `select_window_price`. A1 puts fuel-cost-2 in a **new module**, `fuel_cost_v2.py`, and does not edit `fuel_cost.py`, so there is no conflict |
| MB-1 ↔ A3 | `B/site_outcomes/board.py` (`cost_line`), `B/site_outcomes/mini.py` (`COST_ZERO`, `VERIFIED_WITH_COST`) | A3 copy after MB-1 merges |
| MB-1 ↔ PV-1 | `B/site_outcomes/mini.py` Assure row | PV-1 after MB-1 |
| A2 ↔ PV-1 | `B/estate/portfolio.py` (`recovered`, `card_notes`) | PV-1 after A2. **Between A2's merge and PV-1's merge, main may show no recovered-value clause on the Assure note** (A2 makes the credit list per result, and the clause text is None while CREDITED). No demo build runs in that gap. PV-1 restores the clause |
| A1 ↔ A2 | migration | **One migration, `0053`, in A1**, carries both units' CHECK changes (section 4.1). A2 adds no migration, so there is no alembic-head race |

---

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

## 4. Lane 2 unit cards (Option A, idle fuel)

### 4.1 A1: fuel-cost-2 and the declared no-load fact, 0.85

**Foundation vocabulary (`B/sites/models.py`):**
- `"generator-no-load-fuel-rate": PropertyDefinition(unit="L/h", kind="PHYSICAL", display_name="Generator no-load fuel rate")`.
  - Comment: a no-load rate is defined at one operating point, zero load, which is exactly what it states. The `:75` argument against L/h applies to SFC and is unchanged. The parser still refuses SFC in L/h.
- `"generator-no-load-fuel-rate-basis"`: a state property, `STATE_PROPERTY_VALUES["generator-no-load-fuel-rate-basis"] = frozenset({"GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST"})`, unit `"state"`.
- Both are carried by `GENERATOR`, added to `MINIGRID_PROPERTY_CARRIERS` (`:312`).
- The basis travels with every later Foundation revision, because additive publishes keep the other properties. So the "generic" label is data the Site declared, never product copy.

**fuel-cost-2 (`B/financials/fuel_cost_v2.py`, new; `fuel_cost.py` untouched):**
- `MODEL_ID = "fuel-cost-2"`. A new immutable `PARAMETER_VERSION`:
  - `parameter_version = "fuel-cost-2/sfc-upper-multiplier-and-no-load/v1"`, value 1.10, applied to both terms;
  - formula: `quantity_low = 0 L; quantity_high = 1.10 × [Σ_loaded P_j·h_j·SFC_j + Σ_idle h_j·r_j]`. An idle interval is a selected reading whose accepted GOOD mean is exactly 0 kW, wholly inside observed Candidate time; Candidate time is generator-running time by the dispatch classification. `r_j` is the single positive `generator-no-load-fuel-rate` of the generator in the reading's as-accepted Foundation revision, valid over the whole interval;
  - author "Claude Architect (FUEL-1)"; reviewer = the A1 review file;
  - source: this sheet and `.agent/owner-fuel-scope-2026-11-07.md`.
- **Selection:** fuel-cost-2 applies to a Finding revision **iff** at least one counted reading's as-accepted Foundation revision declares `generator-no-load-fuel-rate` on the generator. Otherwise `fuel_cost.quantify` runs exactly as today, so every existing fixture and test stays fuel-cost-1 and byte-equal.
- **Inside v2:** the v1 checks run in v1's order, then the new checks:
  - an idle reading whose revision has no rate → `QUANTITY_UNAVAILABLE` `NO_LOAD_RATE_MISSING`;
  - more than one distinct rate → `NO_LOAD_RATE_CONFLICT`;
  - a rate ≤ 0 or a unit other than L/h → `NO_LOAD_RATE_INVALID`;
  - no basis property → `NO_LOAD_RATE_BASIS_MISSING`.
- **Loaded intervals compute exactly as v1.** `CountedInterval` gains, in a v2 subclass, `idle: bool`, `no_load_l_per_h: Decimal | None` and `no_load_basis: str | None`. The v2 `litres` = `h × r` when idle, else v1's.
- `LIMITATIONS_V2` = v1's four lines, with line 3 reading "…specific fuel consumption, and the declared no-load fuel rate for running at 0 kW (fuel-cost-2 reviewed modelling allowance)", plus a fifth line: "Running at 0 kW inside Candidate time is counted at the declared no-load fuel rate; a generic rate is not this generator's own figure."
- The technical digest adds the model id, r, the basis and the idle flags.

**Migration `0053_fuel_cost_2.py`** (one migration for A1 and A2):
- `financial_consequence` (0011): `model_id IN ('fuel-cost-1','fuel-cost-2')`; nullable `no_load_fuel_rate_l_per_h numeric`, `no_load_fuel_rate_basis text CHECK IN (the three)`, `idle_seconds integer CHECK >= 0`; CHECK `model_id = 'fuel-cost-1'` ⇒ all three NULL.
- The trial cost table (0037 `TABLE`): `formula IN ('trial-fuel-comparison/1','trial-fuel-comparison/2')`; the REASONS CHECK widened by `NO_LOAD_RATE_DIFFERS` and `IDLE_SECONDS_UNKNOWN` (A2).
- Downgrade restores both. Run the single-alembic-head test.

**Store, recompute, readers:**
- The consequence store reads the two properties from each Foundation revision it already reads for SFC, and writes the new columns.
- Recompute calls the selection.
- PRE-FLIGHT lists every reader of the literal `fuel-cost-1` with a disposition: `B/finding_api.py:328`, `:352`; `B/site_overview/read.py:39`; `B/outcomes/outcome_map.py:164`; `B/mini_depth/rules.py:636`; `B/financials/recompute.py`. **Stop if any reader filters rows on `model_id = 'fuel-cost-1'`**, because it would silently drop v2 rows. Copy that names the model shows the stored row's model id.

**Tests:**
- new L0 `backend/tests/test_fuel_cost_v2.py`:
  - no rate → v1 selected and bytes equal;
  - idle-only, 200 min at 0 kW with r = 3.3: `high_exact == Fraction(11,10) * Fraction(200,60) * Fraction(33,10)` (= 12.1 L);
  - loaded-only with r declared: litres equal v1's;
  - mixed;
  - each of the four new refusals;
- parser tests (L/h accepted for the no-load rate and still refused for SFC; the basis states; carrier GENERATOR);
- L2 store round trip and migration up/down on own `assetops_a1_test`;
- `test_s4_fuel_cost.py` and `test_s4_consequence_*` unchanged and green.

**Stops:**
- adding the vocabulary changes any scenario, run-contract or handover digest in the contract tests (`test_scenario_execution_contract.py`, `test_execution_contract_alignment.py`);
- a reader filters on model id;
- more than 1.1 units.

### 4.2 A2: trial-fuel-comparison/2, priced total, no-sum credit, 0.55

- **Window idle seconds** (`B/actions/verification_rules.py` `window_evidence`, `:378-536`):
  - `generator_idle_seconds` = Σ `SLOT` seconds over slots whose sampled `generator_state` value is `"RUNNING"` (`analytics/dispatch.py:97`) and whose slot generator kWh is exactly 0. It is None if any such slot is unknown.
  - It gets the **same exclusion from `plan_sha256` and stored details as `gen_total`** (`:432` comment).
  - Stop if any existing plan digest or stored detail byte changes.
- **`trial_fuel_comparison.py`:**
  - `FORMULA_V2 = "trial-fuel-comparison/2"`;
  - `WindowFacts.idle_seconds: int | None = None` (the default keeps v1);
  - `compare(..., no_load_in_force=())`: v2 iff a no-load rate is in force over both windows;
  - window fuel = SFC × gen_kWh + r × idle_seconds/3600, the upper = × MULTIPLIER as v1;
  - new reasons, appended after `SFC_DIFFERS`: `IDLE_SECONDS_UNKNOWN`, `NO_LOAD_RATE_DIFFERS`;
  - on `MODELLED_IMPROVEMENT`, the result gains `priced_total = {"amount": fmt(cost_b_nominal - cost_l_nominal), "currency", "basis": "TRIAL_HOUR_MODELLED_FUEL", "window": [later_start, later_end], "fuel_change_l": fmt(fuel_b_nominal - fuel_l_nominal)}`;
  - `LABEL` unchanged ("Modelled change after the trial · not realised savings"). No annualising.
- **`verification._cost_check`:** pass the idle seconds and the no-load history (a `store.no_load_history` beside `sfc_history`).
- **`_cost_check_read`:** additive `priced_total`.
- PRE-FLIGHT checks where `COST_CHECK_SOURCE` ("Generator stop setting changed; no direct cost declared", `:49`) is shown. ACT-001 changed the battery reserve, not the stop setting. If a client screen shows the text, report it as a finding; do not rewrite stored data.
- **`B/outcomes/credit.py:74-96`, the owner-requested fix:**
  - `recovered_value` never sums. It returns `{"state": "CREDITED", "text": None, "items": [{"key": <outcome id>, "currency", "amount": _wire(amount), "basis": <priced_total basis>} per credited item]}`;
  - `"amounts"` is removed. PRE-FLIGHT greps its readers (`frontend/src/estate/estateClient.ts`, `portfolioFixtures.ts`, `test_w303_*`, `test_ch3_rows.py`) and updates them by the same rename;
  - fail loud on two items with the same key.
  - Tests: two credited items in the same currency → two items, and no field equals their sum.
- **Expected demo figures (computed in tests from the inputs, never typed from a run):** trial hour baseline 12 slots RUNNING at 0 kWh, later 0 slots, r = 3.3:
  - `fuel_change_l` 3.3;
  - `priced_total.amount` 3.3 × 1.25 = 4.125, shown by `money2` as 4.12 USD;
  - per kWh of demand 0.275 USD/kWh (15 kWh).
- **Tests:** `test_out_e*` cost-check tests green; a new `test_tfc2.py` (v1 byte-equal without a rate; idle only; loaded only; mixed; both new reasons; priced_total); the credit no-sum tests.

### 4.3 A3: idle fuel on Kobo's screens and story, 0.7

**Declaration** (`T/demo_combined_kobo.py`): `declare_no_load_rate(foundation, result, install_at)`, called in `configure_at` after `declare_supply_uses`.
- One `publish_component_properties` on the generator asset (PRE-FLIGHT: its asset code), `effective_from = install_at + CONFIG_OFFSETS["uses"]`.
- Properties `[{"property_key": "generator-no-load-fuel-rate", "value": 3.3, "unit": "L/h", "source": "SITE", "source_version": 1}, {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state", "source": "SITE", "source_version": 1}]`.
- Note: "Generic no-load fuel rate for a 40 kW diesel set (common design-software default, about 0.08 L/h per kW of rating); not this generator's datasheet. Owner decision 2026-11-07."
- The value 3.3 is the owner's; the source is the HOMER-style generic intercept, about 0.0815 L/h per kW × 40 kW. Never change it to reach a figure.

**Copy (all server-side; guard V; literals):**
- **Finding / board day line**, replacing `COST_ZERO` (`B/site_outcomes/mini.py:64-65`) only for a fuel-cost-2 PRICED row with idle seconds above 0. Fuel-cost-1 rows keep `COST_ZERO`.
  - `COST_IDLE = "Generator ran {h} with no load: up to about {l} L, {amount} of possible extra fuel · counted at {basis} of {r} L/h, not measured"`;
  - `{basis}` from `NO_LOAD_BASIS_WORDS = {"GENERIC_DEFAULT": "a generic no-load rate", "MANUFACTURER_DATASHEET": "the datasheet no-load rate", "SITE_TEST": "the site-tested no-load rate"}`;
  - `{h}` is the duration text helper the board already uses (PRE-FLIGHT names it), `{l}` is one decimal, and `{amount}` is `money_text`.
- **Board Optimize cost line** (`board.py:497-509` `cost_line`): when the cost check carries `priced_total`, `COST_PRICED = COST_PREFIX + "about {l} L less diesel in the trial hour, {amount} at {p} {cur} per litre."`. Without it, today's lines are unchanged.
- **Assure** `VERIFIED_WITH_COST` (`mini.py:96`, `:986-988`): with `priced_total`, the same litres-and-amount clause replaces the per-kWh clause.
- **Trial verification page** (the ACT-001 page): one line under the verdict, "About {l} L less diesel in the trial hour, about {amount} at {p} {cur} per litre · modelled from a generic no-load rate, not measured by a fuel meter" (basis words as above).
  - **MOCK DEVIATION MD-FUEL-A3-1:** v69 `:498-505` shows no money on Verification.
- **"Why?" line** (owner decision 3), on the Optimize row's "Why?" where the idle line shows: "The example data does not count fuel while the generator idles; this estimate does, at the declared no-load rate, so the two differ."
- **Readiness "Generator fuel curve"** (v69 `:426`), only if that row exists on main (PRE-FLIGHT greps). If it does not, nothing is added; that is not a mock gap this unit owns.

**Finish rows (written now; run at E3):**
- **MONEY-B / O16:** S-14, S-7 and S are PRICED fuel-cost-2. `quantity_high` = 1.10 × (stored Candidate idle seconds / 3600) × 3.3, computed from the stored segments and readings. The amount equals that × the stored price.
- **PROBE_CHOSEN** (`T/demo_combined_finish.py:39-40`): the cost state becomes `MODELLED_IMPROVEMENT`, and `fuel_change_l` = 3.3 × (stored baseline idle seconds − later idle seconds) / 3600.
- **CH-5d1:** the Optimize card on S equals the one priced Site's claim text (replacing CH5d1-R §4's "Not known yet" forecast).
- **COH-17:** unchanged rules, new data.

**One Kobo-only scratch prepare** (approved with Option A: "one Kobo-only trial build is needed first"):
- `--sites kobo` on own `assetops_fuel_a3_test`, with the keep-awake script running;
- confirm the stored figures equal the computed ones (B2 table at r = 3.3: 11.0 L nominal per morning, 12.1 L upper; trial hour 3.3 L);
- confirm no scenario, handover or run digest changed;
- then drop the DB and its var folder. Cap 1 h; it takes about 20–30 min.

**Stops:**
- a digest changes;
- the stored idle seconds differ from the probe's 200 min per morning or 12 slots in the trial hour (that is a data finding, never a retune);
- more than 1.0 unit.

---

## 5. The diesel-heavy story (owner: "inject days")

### 5.1 Form: a fourth Site, "Kisiwa", a diesel-hybrid island mini-grid (recommended over a Kobo extension)

**Why not extend Kobo (option (i)):**
- The new days would sit inside the mill's 3+3 checked-day windows (mill change S-9) and the recurrence span.
- Four earlier attempts at a Kobo trial that both shows a lever and passes its check failed (`.agent/DEMO-SPARSE-trial-probe.md:63-126`).
- Every Kobo count that passes today (SP-3 gap 24, MILL-3, the recurrence, COH) would move.
- Kobo is mostly solar, so the numbers stay small.

**Why a fourth Site:**
- Kobo's checks are isolated by construction.
- Diesel is the main source there, so the numbers are CFO-sized and honest.
- It reuses Option A's fuel-cost-2 unchanged.

**The cost of a fourth Site:**
- a four-Site Portfolio. **MOCK DEVIATION MD-FUEL-D-1:** v69 `:131` shows "3 priority sites";
- Site navigation;
- layout recaptures;
- new finish rows.

### 5.2 Stated physical assumptions (declared before any probe; never tuned)

| Item | Value | Basis |
|---|---|---|
| Template | new `config/site-templates/kisiwa-diesel-hybrid-60kw.yaml`, built from Kobo's component and topology pattern | |
| PV / inverter | 20 kWp / 20 kW AC | small array on an island site |
| Battery / PCS | 60 kWh, reserve 30 %, PCS ±20 kW at 95 % | |
| Generator | 60 kW (75 kVA prime). Start 35 %, stop 90 %, minimum runtime 30 min, start delay 5 min (Kobo's control values) | |
| SFC | **0.355 L/kWh**: the generic fuel curve F = 0.08145 L/h per kW rated + 0.246 L/kWh × P, evaluated at 75 % of rating (45 kW): (4.887 + 11.07) / 45 | One stated rule, at the common prime rating point. Partial-load running is then under-counted, which is conservative |
| No-load rate | **4.9 L/h**, basis `GENERIC_DEFAULT` (0.08145 × 60 = 4.887) | The same generic rule as Kobo's 3.3 L/h |
| Tank | 1000 L, not published (no tank signal; see 5.4) | |
| Diesel price | **1.25 USD/L**, Kobo's declared demo price, one publication | The same declared price; island transport premium not assumed |
| Load: households | 2 kW 06–18, 8 kW 18–23, 3 kW 23–06 (85 kWh/day) | |
| Load: cold store (ice / fish) | 4 kW constant (96 kWh/day). It is the critical load, so its unserved energy is a guardrail | |
| Load: water pump | 6 kW 19:00–23:00 (24 kWh/day), today's habit | |
| Solar | the same irradiance day-kinds as Kobo's calendar for the same dates (normal / overcast), scaled to 20 kWp | Weather is not chosen per outcome |

- Load ≈ 205 kWh/day; sunny PV ≈ 100 kWh/day. So about 100 kWh/day is diesel, roughly 35–40 L/day and about 1,100 L a month. This is an estimate to be measured by the probe, not a target.
- **Where the avoidable diesel comes from (stated physics):**
  - The evening load drains the battery to the 35 % start at about 21:00.
  - The generator then carries the load and charges at the PCS limit until 90 %.
  - Once SOC is above reserve + 10 points and the battery could carry the load, the dispatch classifier (`B/analytics/dispatch.py:44-63` thresholds) marks the running as Candidate avoidable. That is loaded diesel spent filling a battery the next morning's sun would partly refill.

### 5.3 Lever and before/after verification

- **Lever: owner question Q3**, both options declared before the probe:
  - (a) **stop the generator at 60 % instead of 90 %** and let the sun finish charging (v69 ACT-048 / CHG-019, `:335`, `:431-433`);
  - (b) **pump water at 10:00–14:00 instead of 19:00–23:00**.
  - If the probe shows that the chosen lever does not lower modelled diesel, we report it and do not swap levers silently.
- **Verification:** a new family, `generator-night-fuel-1`, built on the mill family's day choice (`choose_days`, 3 + 3 COMPLETE days, 14-day look limits; `B/actions/verification_families.py`). It is not the one-hour reserve trial, which is the path that failed four times.
  - Metric: modelled diesel litres per night (18:00–06:00 local), by fuel-cost-2's rule, from accepted readings: loaded SFC × kWh plus idle h × r.
  - Target: **owner-declared before the probe** (Q2), for example "at least 20 % less modelled diesel per night".
  - Guardrails: no unserved cold-store energy in either window, and sampled SOC never below the reserve.
  - Verdict page: a generic version of the mill verdict page, reusing its components.
- **Money on the verdict:** (mean baseline litres − mean later litres) × 1.25 USD, per night, "modelled from a generic fuel curve, not measured by a fuel meter". No annualising. The Portfolio line follows PV-1's per-basis rule (basis `NIGHT_MODELLED_FUEL`), never added to the mill or Kobo trial lines.
- **Measured tank or flow signal: not included.** The simulator's mini-grid law burns 0 L idle (BL-16), and no tank publication exists. A published tank would contradict the product's idle-inclusive estimate unless the simulator gets a Kisiwa-only law version and a tank publication (+1.0–1.5). That is post-demo, and it is the only path to the mock's "measured tank drop agrees with modelled" panel (v69 `:623-630`).

### 5.4 Screens (v69 as the layout spec)

- The Kisiwa Site board (the shared mini board; no new layout).
- The Finding fuel panel (v69 `:459`, `:468-472`).
- Financials assumptions (`:479-481`).
- The Change and Verification pages (`:431-433`, `:498-505`). MOCK DEVIATION MD-FUEL-D-2: money on Verification.
- Portfolio and estate pages with four Sites (MD-FUEL-D-1), and Site navigation.
- Layout evidence at 1440 and 390 for every changed page.

### 5.5 Finish rows, coherence, E3

- **New rows:**
  - KIS-1: Site, prices and declared facts;
  - KIS-2: Findings on the before nights, PRICED fuel-cost-2, `quantity_high` computed from the stored segments;
  - KIS-3: the verdict as computed. INEFFECTIVE is recorded truthfully and DS-1 tells it; it is never forced;
  - KIS-4: the money line reproduces from the shown means and price;
  - KIS-5: four-Site Portfolio counts;
  - KIS-6: CH-5d1's Optimize card on the "≥2 priced Sites" path (Kobo and Kisiwa), with no sum.
- **COH-17 and V4** extend to Kisiwa.
- **E3 prepare:** about 16 Kisiwa days (10 before nights including the baseline, the change day, 5 after). Estimate +15–25 min, giving about 1.3 h of the 3 h cap. One whole-list rehearsal prepare on its own `*_test` DB before E3 (about 1.3 h), as DD-1b2b did.

### 5.6 Units, size and risk

| Unit | Content | Size |
|---|---|---|
| D0 | In-memory probe (no DB), as `T/probe_kobo_nights.py` does: the 5.2 Site through the simulator for before and after nights under the owner's lever. Measure Candidate loaded hours, litres per night and the guardrails, and confirm the family's freeze rules accept the windows | 0.5 |
| D1 | Template, import, configure, prices, the no-load fact (reuses A1) | 0.75 |
| D2 | `generator-night-fuel-1` family: freeze, evaluate, read, verdict page | 1.5 |
| D3 | Authored calendar, scenarios, `demo_combined` child, story days, prepare list | 1.5 |
| D4 | Four-Site Portfolio, estate and navigation; mock deviations; recaptures | 1.0 |
| D5 | Finish rows, COH, rehearsal prepare, DS-1 beat | 0.75 |
| **Total** | | **6.0 planned, range 6.0–8.5 (plan figure 7.0)** |

**Risk:**
- **High on schedule and on the verification path.** The new family is new code, and the Kobo record shows trial windows can be refused at freeze. D0 de-risks this before any product code.
- **Medium-high on what passes today.** Every Portfolio and estate check, COH-17 and the all-26 layout audit gain a fourth Site.
- **Low for Kobo,** which is isolated.

**Honest assessment:** this cannot sensibly land before the demo **on the current date**.
- At about 7 units it is larger than everything else left combined (5.85 units).
- It changes the Portfolio checks and captures that pass now.
- Its verification path is unproven until D0.
- It can land before the demo only if the owner moves the demo by about 2–3 working days (two lanes at §15's rate, plus one extra rehearsal prepare) **and** D0 shows the lever lowers modelled diesel.
- Only the owner can trade those off. **Recommended:** run D0 (0.5, no product code, no risk to anything that passes) beside lanes 1 and 2 now, then decide with a measured size.

---

## 6. Plan delta (for the coordinator to carry into `Docs/demo-sprint/client-demo-plan.html`)

**New order:** CH-5d1 → {MV-1 ‖ A1} → {MB-1 ‖ A2} → {WD-1 ‖ A3} → PV-1 → DS-1 → E1–E6. With the diesel story before the demo: the D lane runs as lane 3 from now (D0 first) and merges before E1. Otherwise it runs after E6.

**Totals:**
- Before: ≈ 112.2 per the handoff, or ≈ 111.95 after CH5d1-R's −0.25 (CH-5d1 1.0 → 0.75).
- FUEL-1 adds +5.35: MV-1 0.5, MB-1 1.25, WD-1 0.15, PV-1 0.75, A1 0.85, A2 0.55, A3 0.7, E3 allowance 0.35, probe 0.25 (done).
- **New total ≈ 117.3.** Remaining before DS-1: CH-5d1 0.75 + 5.1 = **5.85**.
- With the diesel story before the demo: **+7.0 → ≈ 124.3**, remaining ≈ 12.85.

**Rows to change in the plan HTML:**
- Build-units table (around `:647-664`): add one FUEL-1 row before the DS-1 row (`:664`), "FUEL-1 mill dollars, mill on board, Portfolio value lines, wording, idle fuel (owner 2026-11-07)", 5.35. Add a "D-lane diesel-hybrid Site (owner timing question)" row, 7.0 est., marked conditional.
- Total row (`:665`): ≈ 117.3 (and lanes +5.0).
- G5 freeze (`:1172`) and G6 (`:1173`): +5.35, and the CH-5d −0.25 already owed.
- The lanes schedule table and figure (`:935`, `:968`): FUEL-1 lanes 1 and 2 between CH-5d1 and DS-1.
- Add a rulings-table row "FUEL-1" pointing to this sheet. Note BL-45 and BL-48 leave the backlog (`.agent/backlog-post-demo.md` rows 66 and 69 marked "scheduled FUEL-1"), and BL-16 is partly done (product side, Kobo).

---

## 7. Owner questions (plain language; for the coordinator to send)

1. **When do we build the diesel-heavy example?** It is a fourth example site, a diesel-hybrid island where the generator carries most nights. That gives large, honest fuel numbers without touching Kobo. It is about 7 units, more than all the other remaining work together, and it changes every Portfolio check that passes today. Options:
   - (a) after the demo;
   - (b) before the demo, moving the demo by about 2–3 working days;
   - (c) recommended: first a half-unit trial run of the new site in the simulator, beside the other work, which risks nothing that works now; then decide with a measured size.
2. *(Only if you choose (b) or (c).)* **What counts as success for the diesel change?** We need your pass mark before we run anything, so it cannot be chosen to fit the result. For example: "at least 20 % less diesel per night, averaged over 3 fully checked nights before and 3 after, with no power cut to the cold store".
3. *(Only if you choose (b) or (c).)* **Which change do we test at the diesel site?**
   - (a) stop the generator when the battery reaches 60 % instead of 90 %, and let the sun finish charging;
   - (b) pump water at midday instead of in the evening.
4. **Did the mill change have a real cost you can state, with where the figure comes from?** If not, the mill result page says "No cost is recorded for this change", which is true. If yes, we add a "pays back in N days" line (about a quarter unit).

Nothing else needs your decision. The idle-fuel work, the mill dollars, the mill on the board, the Portfolio lines and the wording fixes follow your answers from today.
