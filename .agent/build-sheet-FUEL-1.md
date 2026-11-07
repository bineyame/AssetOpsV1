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

## MB-1a-R2: ruling on the MB-1a build's stops and deviations (Architect, Claude, 2026-11-07)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `099b57c96`. Build `845ece111`, packet `fa186fa3c` (`.agent/review-packet-MB-1a.md` in the mb1 worktree).
- This section **amends MB-1-R §1 Q1(c) and §2.1** for MB-1a. Every other part of MB-1-R stands. `B/` = `backend/assetops_backend/`, `T/` = `tools/`. READ = I read the code; nothing here was measured.

### 0. Order of the fix round (builder, mb1 worktree, Sonnet)

1. Merge main (`099b57c96` or later) into `task/FUEL-MB1-mill-on-board`. Reconcile the golden as in §3.
2. Apply §1 (S-d) and §2 (cap).
3. Run the checks in §6 and amend the packet as in §7. Commit. Do not push.

### 1. S-d: the policy is injected by `site_outcomes/composition.py` (builder's option, approved)

- **Decision.** `read.py` must not import `chain.composition`. OUT-B4 §B.3 (`backend/tests/test_out_b4_imports.py`) is the rule, and MB-1-R's "import locally" was wrong for `site_outcomes/`; the `postgres_estate_read.py` precedent is an adapter, not a `site_outcomes` module. Deferring to MB-1b is rejected: `ChainThreads` already carries the field, and leaving it unbound would hand MB-1b a half-wired port.
- **READ facts.** `site_outcomes/composition.py:18` already imports from `assetops_backend.chain.composition`. `thread_lifecycle_policy` is `chain/composition.py:113`. `BoardServices` is `B/site_outcomes/read.py:85-113`.
- **Code.**
  - `B/site_outcomes/read.py` `BoardServices`, directly after `chain_reader` (`:108`), verbatim:
    ```python
    thread_policy: Callable[[], Any] | None = None  # MB-1a-R2: chain.composition.thread_lifecycle_policy (composition.py injects it; OUT-B4)
    ```
  - `B/site_outcomes/read.py` `chain_threads` binding (`:295-300`): delete the local import. The body becomes:
    ```python
    if s.chain_reader is None:
        return None
    req = chain()
    return mini.ChainThreads(req.threads(sid), req.k, None if s.thread_policy is None else s.thread_policy())
    ```
    Update the comment above it: "... and the lifecycle policy (`BoardServices.thread_policy`, None when not injected)".
  - `B/site_outcomes/composition.py:18`: `from assetops_backend.chain.composition import build_chain_reader, build_thread_sources, thread_lifecycle_policy`. In the `BoardServices(...)` call, add `thread_policy=thread_lifecycle_policy` after `chain_reader=chain_reader`. Pass the function, not its value (the policy is read per board read, as MB-1-R ruled).
  - `B/site_outcomes/mini.py:210-212` comment: replace "(`chain.composition.thread_lifecycle_policy()`)" with "(`BoardServices.thread_policy`; None when not injected)". `ChainThreads.policy` stays typed `Any`; None is allowed.
- **Test**, in `backend/tests/test_mb1_opportunity_board.py` (L0, no DB):
  - `test_composition_injects_the_thread_policy(monkeypatch)`: monkeypatch `composition.build_chain_reader` to `lambda url, **kw: (None, lambda: None)` and `composition.build_thread_sources` to `lambda url: None`, as `test_out_b4_imports.py:76-77` does. Call `composition.build_outcome_board_service(None)` and assert `service.s.thread_policy is chain_composition.thread_lifecycle_policy`.
  - In the existing board-service test (the `test_ch5a1_board_contract.Port` subclass, D6), assert the `ChainThreads` built there has `policy is None` when `thread_policy` is not set. That pins the None branch.
- **MB-1b consequence (amends MB-1-R §3.3 step 4).** If `ct.policy is None`, the view is None, so there is no thread line, never a guessed `close_after`. Add one L0 case for it to `test_mb1_thread_line.py`. Production always injects the policy.
- **Files approved:** `B/site_outcomes/composition.py` (the import line and one keyword argument only).

### 2. Origin-reader cap: approved, `chain/site_chain.py` cap 8, class "both"

- **Why.** The guard exists so that a new reader is classified before it lands. `opportunity_actions` is a chain reader that handles the opportunity origin on purpose. Class "both" is already correct, and its "names the opportunity origin" check still holds. The four new tokens are the verbatim docstring, the filter, and the item key and value. Nothing new is unclassified.
- **Code.** `backend/tests/test_ch9b1_origin_readers.py:42` becomes:
  ```python
      "chain/site_chain.py": ("both", 8),  # MB-1a-R2: + opportunity_actions (MB-1-R Q1(b))
  ```
  Change nothing else in that file. The non-vacuity cases (`higher_count` uses `chain/lookup.py`; `both_ignores` uses `site_chain.py`'s text) are unaffected.
- **Files approved:** `backend/tests/test_ch9b1_origin_readers.py` (that one line).

### 3. D2, the `estate_week_2026-10-25` golden: take main's file, then regenerate; the only diff must be `verified_actions`

- **Main already carries the card.** DRIFT-R1 (merge `7bba9e64f`, `.agent/build-sheet-TEST-drift.md` §2.2) added `cards.OPTIMIZE_COST` to this golden. The builder's "pre-existing drift" diagnosis is right, and main has settled it.
- **Procedure during the merge in §0.**
  1. On a conflict in `backend/tests/fixtures/ch5a2_chain_contract/estate_week_2026-10-25.json`, take main's version whole: `git checkout --theirs -- <that path>` (during `git merge main`, "theirs" is main). Never hand-merge the JSON.
  2. If there is no conflict, still restore main's file before regenerating: `git checkout main -- <that path>`.
  3. Regenerate with DRIFT-R1 §2.2's procedure, using the mb1 worktree paths in place of `AssetOpsV1-drift`. Then run `tests/test_ch5a2_contract.py` without the variable.
- **Acceptance (STOP if any fails):**
  - `git diff main -- backend/tests/fixtures/ch5a2_chain_contract/` touches only `estate_week_2026-10-25.json`.
  - That diff adds only `"verified_actions": 0` inside each `sites[].threads` object. It adds no other key, it does not move the `OPTIMIZE_COST` card, and it changes no value.
  - If another golden or key changes, stop and report the diff. Do not commit it.
- D2 is confirmed on those terms. In the packet, replace D2's "pre-existing drift ... please confirm" with "main's DRIFT-R1 golden plus `verified_actions: 0` per Site (MB-1a-R2 §3)".

### 4. Deviations D3-D6 and the wording check

- **D3, MILL-5 in `T/demo_combined_rows.py`: confirmed. The file is approved retroactively for `mill_assure` only.** The precedent is MILL-3b, whose pure logic lives in the same file with its L0 self-test beside it. The function is pure over the board and chain bodies. It imports only backend constants (`VERIFICATION_TEXT`, `NO_VERIFIED`, `display_code`, `provenance_suffix`) and never retypes them. No other edit to that file.
- **D4, A1 skips a mini board with no Assure row: confirmed. It does not weaken A1.**
  - A1's rule is "headline count == listed verified entries". With no Assure row there is no headline to judge, so judging would mean inventing a value.
  - The skip is counted (`tally["skipped"]`), never silent.
  - The live story board is held separately. MILL-5 asserts that the S+0 Kobo Assure row exists (`"no Assure row on the S+0 Kobo board"`). E3 also checks every live mini board's rows through the V-rows (summary nodes vs board nodes).
- **D5, A1 excludes the `NO_VERIFIED` entry: confirmed. It does not weaken A1.**
  - The exclusion is exact string equality with the backend constant, not a pattern.
  - "No verified result yet" is the empty-state entry, not a verified result. Counting it would make A1 fire on every board with nothing verified, which is a false finding, not a stricter rule.
  - Add one self-test to `T/checks/test_chain_coherence.py`: headline "1 verified result" with one verified entry plus a `NO_VERIFIED` entry must FAIL. That shape is impossible on a real board, and the test proves that the exclusion cannot hide a real mismatch the other way.
- **D1 and D6: confirmed.** D1 is the cutoff rule MB-1-R Q1(b) already states (outcome None when not known by the cutoff). D6 is a stronger form of §2.5 item 4.
- **"ACT-048 verified on example data": confirmed as the existing trial (ACT-001-class) entry, byte-equal to today.**
  - It is `VERIFICATION_TEXT["VERIFIED"]` with `provenance_suffix(a.source_class)` (`mini.py:1021`), and the fake carries an example-data source class (`EXAMPLE_SOURCES`, `chain/vocabulary.py:106-112`).
  - The mill entry is `provenance_suffix(None)`, which reads "ACT-… verified" with no suffix, as MB-1-R §2.3 ruled. A domain verdict row carries no source class on `_SITE_ACTIONS`.
  - **Note, not an MB-1a change.** If the live S+0 Kobo board shows the trial "on example data" while the mill, on the same Site's data, shows no suffix, that asymmetry is a wording question. It goes to **WD-1** (money and verdict wording) as an item. WD-1 decides whether the mill line gains the suffix from the Site's source mode. MB-1a adds no literal.

### 5. Main-branch drift (not MB-1a's)

- **`test_ch9b2_midday_plan_postgres.py::test_0052_round_trip_and_refusal`: test drift. Fix it in a small Sonnet round on main**, on its own branch `task/TEST-drift-0053` from main, in worktree `C:\Users\assef\Bineyame\AssetOpsV1-drift2`. It runs in parallel with MB-1a.
  - Cause (READ): the test pins the Alembic head literally (`:236`, `:240`, `:252`). `0053_fuel_cost_2` (A1, `4be7bbc44`) is now head. `test_ch9b1_opportunity_actions_postgres.py:218,222,239` already uses the head-agnostic form; follow it.
  - Code, in `test_0052_round_trip_and_refusal` only:
    - `:236` → `assert head(mill.engine) == pg_harness.alembic_head()`. Then add `command.downgrade(_alembic(), "0052_verification_plan_domain")` and `assert head(mill.engine) == "0052_verification_plan_domain"`. The fixture has no fuel-cost-2 or `/2` rows, so 0053's downgrade does not refuse (`0053_fuel_cost_2.py:62-73`). Lines 237-250 are then unchanged and test 0052 itself.
    - `:252` → `assert head(mill.engine) == pg_harness.alembic_head()`.
    - Docstring line 1: add "(head-agnostic since 0053, MB-1a-R2 §5)".
  - Check: that one test plus `test_0052_checks_exactly_one_action_and_family_coupling`, on pg_harness base `assetops_drift2_test`. Drop it after the merge. No other test, no suite.
  - Review: a fresh Sonnet reviewer checks the diff against this item. The coordinator merges on ACCEPT.
- **`test_out_d2_objectives.py::test_policy_is_v2`** (packet, fast tier): DRIFT-R1 §2.1 is on main, so this should pass once MB-1a merges main. If it still fails after the merge, record it in the packet as main drift. It is not an MB-1a stop.
- **`test_ch5a1_mechanism_postgres` and `test_ch6b_estate_postgres`, `TEMPLATE_STALE`: rebuild once, at the start of E2, not now.**
  - Why: the template fingerprint covers the input writers. Lane 2 (A3), MB-1b and the Kisiwa story will change writers again before E2. Each rebuild costs about 1300-1700 s of machine time, and every rebuild before the last writer change is wasted.
  - Who and when: the coordinator, once, on an idle machine (the quiet-suites rule), as E2's first step and before E2's full suites. Use the exact command that the `TEMPLATE_STALE` message prints (`backend/tests/mechanism_dataset.py:1205-1243`).
  - Until then: these two tests failing with `TEMPLATE_STALE` is expected. It does not block any unit's review or merge, MB-1a's included, because MB-1a's L2 proof builds its own DB (`test_mb1_site_actions_postgres.py`).
  - Exception: if a later unit's acceptance needs a mechanism-template test, that unit's ruling orders the rebuild then, and E2 does not repeat it unless the fingerprint has moved again.

### 6. Checks for the fix round

- **L0:** `test_mb1_opportunity_board.py`, `test_out_b4_imports.py`, `test_ch9b1_origin_readers.py`, `test_ch5a2_contract.py`, `test_ch5a1_board_contract.py`, `test_out_b2_mini.py`, `test_out_b3_cold_ev.py`, `test_out_d2_objectives.py`. Also `T/checks/test_chain_coherence.py`, which includes the new D5 case.
- **Fast tier:** the same scoped set as the packet (48 files, `-m "not slow"`). Expected: 0 failures.
- **Guards:** A, W, N, V, M, chain coherence, and `node tools/checks/frontend-hardwiring.mjs` (no rise). The orphan-scan `MODULE_NOT_FOUND` stays a known worktree condition (no `npm ci`). Say so in the packet.
- **L2:** do not rerun `test_mb1_site_actions_postgres.py` unless `read.py` / `composition.py` changes touch its path. They do not, because it calls the chain reader and claims directly.
- **Not run:** the full suite, prepare, the template rebuild.

### 7. Packet amendments

- Change the status to "built; S-d and the cap closed by MB-1a-R2".
- Stops: mark both closed and cite §1 and §2.
- D2 as in §3. D3, D4 and D5 marked "confirmed (MB-1a-R2 §4)".
- Add the two approved extra files (`composition.py`, `test_ch9b1_origin_readers.py`) and `T/demo_combined_rows.py` to the files table, with their MB-1a-R2 reason.
- Add the WD-1 note on the provenance suffix (§4) under residual risk.
- Main-drift lines: point to §5. MB-1a fixes none of them.

### 8. Size and review

- **Size:** +0.05 (S-d wiring and test 0.02, cap 0.01, merge and golden reconcile 0.02). **MB-1a = 0.85**, inside S-f (0.9). Lane 1 = 2.8. FUEL-1 total = 5.5.
- The drift-0053 round is ≈0.05 of main-maintenance work outside FUEL-1.
- **Review:** MB-1a has had no review yet. After this fix round it goes **straight to its first review**: a fresh Opus reviewer, per Model by role. There is no separate re-review of this round. The reviewer reads MB-1-R §2, this section, and the packet. Review focus: §1's injection and the OUT-B4 guard passing, §3's golden diff limited to `verified_actions`, D4 and D5 against §4, and R4 (Cold and EV byte-equal).
- MB-1b stays blocked on MB-1a's merge. Its card gains only §1's "policy None → no line" case.

**Owner question: none.** For information only: two main tests were stale against migration 0053 and the mechanism template, and are scheduled as above.

---

## PV-1-R: ruling on the PV-1 pre-flight (Architect, Claude, 2026-11-07)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `70a5e8699` (MB-1a merged).
- This section **replaces §3.3's build detail**. §3.3's two line literals, MOCK DEVIATION MD-FUEL-PV1-1 and the no-total rule stand. Every other part of §3.3 is superseded where this section differs.
- `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `T/` = `tools/`. READ = I read the code; nothing here was measured.
- **Order.** PV-1 and MB-1b both edit `board.py` `SiteFacts` (last field) and `_row`. Whichever merges second merges main first and puts its field after the other's. Neither waits for the other.

### 0. Code reality (READ)

- **Mill value.** `VerificationService.domain_summary` (`B/actions/verification.py:381-401`) returns the verdict page's `value`. That is `mill_value(details, outcome, _mill_price(...))`, with the price as known at the outcome's `recorded_at` (`:403-419`). For a VERIFIED outcome it reads the context, the outcomes and one price. It runs no live assessment.
- **The board already holds that service.** `BoardServices.verification` (`B/site_outcomes/read.py:98`) is built in `site_outcomes/composition.py:59` as `VerificationService(actions)`. Its ports come from `actions.verification_ports` (`verification.py:547`), and they include `productive_price` (`B/actions/composition.py:125`). It is the same port the verdict page uses.
- **Trial fuel.** The board's `ActionFact.cost_check` is the verification summary's `cost_check`, passed whole (`B/chain/read.py:416`). Since A2 it carries `priced_total` (`verification.py:1210`), which holds `amount`, `currency`, `basis`, `window` and `fuel_change_l` (`B/financials/trial_fuel_comparison.py:199-201`).
- **Summary path.** The Portfolio summary rows' `nodes` come from `_window_parts`, which is `assemble(replace(comp.facts, nodes=...))` (`read.py:496-522`). A new `SiteFacts` field set in `mini.compose` therefore reaches both the board and the summary rows unchanged.
- **Card note.** `card_notes` (`B/estate/portfolio.py:658-668`) joins the recovered-value text and the evidence-gap clause into one server line. The browser renders it whole (`F/estate/PortfolioOutcomes.tsx:89`). The estate read cannot see the board's value lines.

### 1. S1: the mill line reads the verdict page's own `value` through the board's existing verification service (option c)

- **Decision.** Add one `MiniPorts` port, bound in `read.py` to the already-injected `s.verification.domain_summary(...)["value"]`.
- **Rejected.**
  - **(b)**, widening `_SITE_ACTIONS` and adding a price read, re-derives MV-1. Two code paths would then decide the same figure, and PV-A could drift after a price revision.
  - **(a) as proposed**, a new composition injection, is unnecessary: the service is already injected, and calling a method on an injected instance imports nothing. OUT-B4 holds with no new import in `site_outcomes/`.
  - The board's day price (`read.py:286`) is never used for this line.
- **No leak past the cutoff.** The port is called only for an opportunity Action whose `outcome == "VERIFIED"` is known by the board cutoff (`opportunity_actions` already nulls a later outcome). Domain verdicts are single and decisive (MB-1-R §0), and the price is read as known at that verdict's `recorded_at`, which is at or before the cutoff.
- **Code, `B/site_outcomes/mini.py`.** `MiniPorts` gains, last and defaulted, verbatim:
  ```python
  #: PV-1-R §1: the verdict page's own `value` (`VerificationService.domain_summary`, MV-1 `mill_value` at the price as
  #: known when the verdict was recorded) of one VERIFIED opportunity-origin domain Action; None = no value.
  verdict_value: Callable[[str], Any] = lambda action_id: None
  ```
- **Code, `B/site_outcomes/read.py` `mini_ports`,** beside `chain_threads`:
  ```python
  def verdict_value(action_id: str) -> Any:
      return jsonable_encoder(_need(s.verification, "verification").domain_summary(t, sid, UUID(action_id))["value"])
  ```
  Pass `verdict_value=verdict_value` to `mini.MiniPorts(...)`.
- **Code, in `mini.compose` after `opp` and `actions` exist,** for `o` in `opp` with `o.outcome == "VERIFIED"`:
  - `v = reads.call("verdict_value", ports.verdict_value, o.action_id, memo=True)`.
  - A failure is recorded by `Reads` (board PARTIAL, `verdict_value` in `failed`) and gives no line.
  - `None`, or `v["state"] != "PRICED"`, gives no line. The verdict page already states why a value is unpriced.
  - The port is never called when there is no VERIFIED opportunity Action. The CH-5a1 contract fixture has none, so its goldens do not move on this account.

### 2. S2: the money clause moves from `card_notes` to the Assure card (option c)

- **Decision.**
  - The Assure card, built by `portfolio_cards` (the one source that sees the board rows), carries the value lines **and** the money clause.
  - `card_notes` keeps only the evidence-gap clause.
  - `recovered()` and the estate `cost_checks` port do **not** change in PV-1. The estate body's `summary.recovered_value` field stays as it is: it is still computed, and it is no longer rendered on the card.
- **Rejected.**
  - (a) as stated: `portfolio_cards` cannot rebuild the evidence-gap clause, because that comes from the estate body. The browser must not split or join server lines.
  - (b): the estate read would have to compose boards.
- **Code, `B/estate/portfolio.py` `card_notes`.**
  - The signature becomes `card_notes(summary, authorized)`.
  - Assure = `evidence_gap_text(...)` alone.
  - Docstring: "PV-1-R §2: the money clause is the Assure card's `value_note` (`portfolio_cards`)."
  - Update the one call at `:894` (drop the third argument).
- **Code, `B/chain/vocabulary.py` `CARD_TEXT`,** under the Assure block, verbatim:
  ```python
  # PV-1-R §2: the Assure card's verified-value lines (one per result, never added) and their clause.
  "assure.value_line": "{site} · {text}",
  "assure.values_separate": "Each result's money is shown on its own and never added together",
  ```
- **Code, `B/site_outcomes/read.py` `portfolio_cards`.** The `ASSURE` card dict gains two keys after `"claim"`:
  - `"value_lines"`: for each `s` in `sites` (summary order), for each `e` in that Site's `ASSURE_PERFORMANCE` row's `(nodes or {}).get("verified_values") or []` (already in code order), the string `card_text("assure.value_line", site=s.get("site_name") or s["site_code"], text=e["text"])`.
  - `"value_note"`: `card_text("assure.values_separate")` if `value_lines`, else `MONEY_NOT_CREDITED` (imported from `B/outcomes/credit.py`).
  - Grow, Optimize and Protect are untouched.
  - There is no total, no sum and no arithmetic across entries.

### 3. The builder's defaults

**Default 1, entry shape: amended.** Each `verified_values` entry is a dict with these keys, in this order:
`{"key": action_id, "action_code": code, "basis": <stored basis>, "amount": <shown money text>, "currency": cur, "text": <line without the Site>}`.
- **No `site` key.** The board does not know the Site's display name. The card adds the Site via `assure.value_line`, as every other card Site line does.
- `amount` and `currency` exist so that COH PV1 can prove nothing is summed.
- `basis` is the stored value: the mill's `v["basis"]` (`ESTIMATED_SALES_AT_DECLARED_PRICE`) or the cost check's `priced_total["basis"]` (`TRIAL_HOUR_MODELLED_FUEL`). It is never retyped.

**Default 2, carriage: confirmed, with one change. The key is emitted only when the list is non-empty.**
- `B/site_outcomes/board.py` `SiteFacts` gains `verified_values: tuple[Mapping[str, Any], ...] = ()`, last field.
- `mini.compose` passes it in the existing `SiteFacts(...)` call, after `opportunity_actions=opp`.
- In `_row` (`board.py:816`), directly after the `GROW_REVENUE` `grow_headline` block and **before** the `NOT_MEASURED` early return:
  ```python
  if cat == "ASSURE_PERFORMANCE" and facts.verified_values:   # PV-1-R §3: nodes only; the board shows no new line
      row["nodes"] = {**row["nodes"], "verified_values": [dict(v) for v in facts.verified_values]}
  ```
- Cold and EV never set the field, so they carry no key, and every board and golden without a value line is byte-equal. A reader takes an absent key as `[]`.

**Default 3, trial fuel: confirmed, with exact rounding.**
- For each trial `a` in `actions` (`not a.is_domain`) with `a.verification_state == "VERIFIED"`:
  - `got = credited(a.cost_check, "VERIFIED")` (from `B/outcomes/credit.py`);
  - `pt = (a.cost_check or {}).get("priced_total") or {}`.
  - A line is produced only when `got` is not None and `pt.get("fuel_change_l")` is set.
- `(n, d), cur = got`.
- `amount = f"{Decimal(round(Fraction(n, d) * 100)) / 100:.2f}"`. Python's `round` on a `Fraction` is exact half-even, the same rule as `money2`.
- `litres = f"{Decimal(round(Fraction(str(pt['fuel_change_l'])) * 10)) / 10:.1f}"`.
- No new read.

**Literals, `B/site_outcomes/mini.py`, beside `VERIFICATION_TEXT`, verbatim.** These are §3.3's lines without the Site prefix, which the card adds:
```python
#: PV-1-R §3: a verified result's money, one line each, never added together (the card prefixes the Site).
VALUE_LINE_MILL = "{code}: about {d} {cur} a day more in estimated sales to productive users (your declared price)"
VALUE_LINE_TRIAL_FUEL = "{code}: about {l} L, {amount} {cur} less diesel in the one-hour trial (modelled, not metered)"
```

**Building the entries.**
- Mill: `{"key": o.action_id, "action_code": o.code, "basis": v["basis"], "amount": v["per_day"], "currency": v["currency"], "text": VALUE_LINE_MILL.format(code=display_code(o.code), d=v["per_day"], cur=v["currency"])}`.
- Trial: `{"key": a.action_id, "action_code": a.code, "basis": pt["basis"], "amount": amount, "currency": cur, "text": VALUE_LINE_TRIAL_FUEL.format(code=display_code(a.code), l=litres, amount=amount, cur=cur)}`.
- Order: all entries sorted by `(action_code or "", key)`, the Assure contributors' order.
- Add both literals and both `CARD_TEXT` strings to `backend/tests/test_out_b2_vocabulary.py`'s list. If guard V or N rejects any of them, stop (S-a) with the message.

### 4. Frontend (`F/estate/estateClient.ts`, `F/estate/PortfolioOutcomes.tsx`)

- `EstatePortfolioCard` gains `value_lines?: string[]; value_note?: string | null;`.
- `CardContent` gains `values: { lines: string[]; note: string | null } | null`.
  - In `content()`, set `values` to `key === "ASSURE_PERFORMANCE" && card ? { lines: card.value_lines ?? [], note: card.value_note ?? null } : null`.
  - It is `null` on the not-loaded path. `grow` is unchanged.
- **Render**, after `c.detail` and before `c.note`, using existing classes only:
  - each line as `<p className="oc-pfnote" data-portfolio-card-value-line>{line}</p>`;
  - then, when set, `<p className="oc-pfnote" data-portfolio-card-value-note>{c.values.note}</p>`.
  - Server text only. No join, no new CSS.
- Header comment at the render: **MOCK DEVIATION MD-FUEL-PV1-1** (text as in §3.3). Add a packet row.

### 5. COH and finish row

- **COH-17 row PV1.** Name it PV1, not V1, because V1 already exists in COH-17 (CH6b3-R Q1). Put it in a new function `coh17_values(w, summary, files, tally)`, called in `_coh17_full` right after `coh17_optimize` (`T/checks/chain_coherence.py`, ~`:1290`).
  - (i) `cards.ASSURE_PERFORMANCE.value_lines` must equal the list rebuilt from `summary.sites[]`'s Assure `nodes.verified_values`, using the `assure.value_line` form imported from `CARD_TEXT`.
  - (ii) For every pair of entries with the same currency, the exact sum `f"{Decimal(a) + Decimal(b):.2f}"` must not appear as a substring of any string in the Assure card (walk the card JSON).
  - (iii) `value_note` is `values_separate` if and only if there are lines.
  - A summary without the keys (an older bundle) is skipped and counted.
- **Self-tests (`T/checks/test_chain_coherence.py`):**
  - pass: two Sites with one entry each;
  - fail (i): a card line differs;
  - fail (ii): a card `detail` holding the sum of two same-currency amounts;
  - fail (iii);
  - skipped: an older bundle.
- **Finish row PV-A (written now, runs at E3), `T/demo_combined_finish.py` after MILL-5,** with pure logic in `T/demo_combined_rows.py` `pv_values` (the D3 precedent):
  - On the week estate summary that contains the S+0 Kobo board, the Assure card's `value_lines` contains `card_text("assure.value_line", site=<Kobo name>, text=VALUE_LINE_MILL.format(code=display_code(code), d=page["value"]["per_day"], cur=page["value"]["currency"]))`. Here `page` is the mill's verdict page body (`GET` the domain verdict, as MILL-3b reads it).
  - The trial-fuel line is present **if and only if** `credited(ACT-001's summary cost_check, "VERIFIED")` is not None. Report which case holds.
  - No card string contains the sum of two same-currency amounts.
  - Add an L0 self-test with pass and fail bodies.

### 6. Tests

- **New `backend/tests/test_pv1_value_lines.py` (L0, fake ports, no DB):**
  - 0, 1 and 2 entries: no mill and no credited trial; mill only; mill plus trial, in code order.
  - The mill `UNPRICED` or None gives no entry.
  - `verdict_value` raising gives board PARTIAL with `verdict_value` in `failed`, and no entry.
  - The port is not called when there is no VERIFIED opportunity Action (a counting fake).
  - A trial whose `credited` is None (a `/1` result, `priced_total` absent, a negative or zero amount, or INEFFECTIVE) gives no entry.
  - Rounding: `amount` for `"1/3"` is `0.33`, `"0.125"` gives `0.12`, `"0.135"` gives `0.14`; litres for `"0.25"` is `0.2`.
  - The Assure row `nodes.verified_values` is present only when non-empty. Kobo Grow, Optimize and Protect rows are byte-equal with and without entries.
  - `portfolio_cards`: `value_lines` order (Site order, then code order); `value_note` in both forms; the Grow, Optimize and Protect cards byte-equal; no card string equal to or containing the Decimal sum of the two amounts.
  - `card_notes` gives the gap clause alone.
  - Parity: the mill entry's `amount` equals `mill_value(details, "VERIFIED", price)["per_day"]` for the same fake details and price.
- **Existing tests, updated by import, never retyped:**
  - `test_ch6b2_portfolio_cards.py:195-205` (`card_notes` without the money clause);
  - `test_w303_portfolio_api.py:422-423`;
  - `test_ch5a2_contract.py` goldens, regenerated by the DRIFT-R1 §2.2 procedure. **Acceptance:** the diff against main is only `cards.ASSURE_PERFORMANCE` gaining `"value_lines": []` and `"value_note": "No money credited · modelled, not saved"`. Anything else is a stop (S-b).
  - `test_out_b3_cold_ev.py` must pass unchanged;
  - `test_out_b2_mini.py`;
  - `test_out_b4_imports.py`;
  - `F/estate/__tests__/estatePortfolio.test.tsx` and `portfolioFixtures.ts`: the Assure card renders its lines and note; a card without the keys renders neither; the body note is the gap clause.
- **Guards:** A, W, N, V, M, chain coherence, and `node tools/checks/frontend-hardwiring.mjs` (no rise). Fast tier for `board.py`, `mini.py`, `read.py` and `portfolio.py`. Frontend: the two test files plus `tsc`. **Not run:** the full suite, prepare.

### 7. Files (complete list)

- Backend:
  - `B/site_outcomes/mini.py`;
  - `B/site_outcomes/board.py` (the field and the `_row` lines only);
  - `B/site_outcomes/read.py` (`verdict_value`, `portfolio_cards`);
  - `B/estate/portfolio.py` (`card_notes` and its call);
  - `B/chain/vocabulary.py` (two `CARD_TEXT` entries).
- Tools: `T/checks/chain_coherence.py`, `T/checks/test_chain_coherence.py`, `T/demo_combined_finish.py`, `T/demo_combined_rows.py`.
- Frontend: `F/estate/estateClient.ts`, `F/estate/PortfolioOutcomes.tsx`.
- Tests: as in §6.
- No other file. In particular, `recovered()` and `postgres_estate_read.py` `cost_checks` are not changed.

### 8. Stops

- **S-a.** A guard rejects a literal.
- **S-b.** A golden diff beyond §6, or any Grow, Optimize or Protect card or row byte change, or any Cold or EV change.
- **S-c.** `domain_summary`'s `value` for the mill differs from `mill_value` over the same details and price (the parity test).
- **S-d.** The work exceeds 1.0 unit.

### 9. Size and review

- **Size:** +0.1. The `verdict_value` port is 0.03; moving the clause out of `card_notes` and its two test updates is 0.04; COH PV1 is 0.03. **PV-1 = 0.85.** Lane 1 = 2.9 and FUEL-1 = 5.6.
- **Review:** PV-1 has had no review. After the build it goes to its first review with a fresh Opus reviewer. Focus:
  - S1 parity with the verdict page;
  - the no-sum proof;
  - the `card_notes` move and the card-render order;
  - the golden diff limited to the Assure card.
- PV-1 is a screen change (the Assure card). It joins the post-W6 owner walkthrough, with no separate walkthrough.

**Owner question: none.**

---

## WD-1-R: ruling on the WD-1 pre-flight (Architect, Claude, 2026-11-07)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `4235318d6`. This section amends §3.2 for WD-1. `B/` = `backend/assetops_backend/`. READ = I read the code; nothing here was measured.
- Sources: §3.2, A2-R1 L4 (the `GENERATOR_KWH_UNKNOWN` note), MB-1a-R2 §4 (the mill suffix note), BL-48.

### 1. EV fault-day Grow headline: the §3.2 literal, confirmed

- **READ.** `B/site_outcomes/ev.py:229` picks the headline from `priced` (the overview's money state). `_charging_from_claim` (`:293-309`) later sets `headline_money[GROW]` to None when the chain earnings claim is NOT_KNOWN, but leaves the headline. So a priced fault day shows "estimated charging income" with no amount.
- **Decision.** The builder's proposal is the §3.2 card's literal. New constant in `ev.py`, beside `NO_TARIFF` (`:51`), verbatim:
  ```python
  NO_INCOME_FIGURE = "No income figure for this day: it is not fully checked"  # WD-1 (BL-48); MOCK DEVIATION MD-WD1-1
  ```
- **Rule (three cases, exhaustive):**
  - shown Grow money has a value: `TARIFF_ESTIMATE` (unchanged);
  - `priced` is true and the shown Grow money is None (the claim is NOT_KNOWN): `NO_INCOME_FIGURE`;
  - `priced` is false: `NO_TARIFF` (unchanged; the reason there is a missing price, not a missing check).
- **Code.** `_charging_from_claim` returns `"headline": {**facts.headline, GROW: NO_INCOME_FIGURE}` when `priced and money is None`, else it leaves the headline unchanged. Add `NO_INCOME_FIGURE` to the export tuple at `:79-82`. No other module changes.
- **Test.** One new L0 case beside the existing EV Grow row tests: a priced day with a NOT_KNOWN claim gives `headline[GROW] == ev.NO_INCOME_FIGURE` and `headline_money[GROW] is None`. Non-vacuity: drop the override, and the case fails. Existing tests import the constants, never retype them.
- **MOCK DEVIATION MD-WD1-1.** v69 shows the Depot Grow headline only with a figure ("gross tariff estimate"). It has no no-figure state, so this literal has no mock example.

### 2. Kobo monthly sales line: the §3.2 literal, confirmed

- **Decision.** `MG1_NO_DAY` (`B/chain/vocabulary.py:268`) and `MG1_ACTUAL` (`B/site_outcomes/mini.py:135`; §3.2 cited `:127`) both become, verbatim:
  ```python
  "no fully checked day counted yet this month"
  ```
  They must stay equal. Make it one literal: `mini.py:135` becomes `MG1_ACTUAL = MG1_NO_DAY`, added to the existing `chain.vocabulary` import at `mini.py:27` (READ: that import already brings in the `MG1_*` forms, so there is no new edge). Update the CH6a2-R Q5 twin comment at `vocabulary.py:267` to say so.
- **Retyped strings: approved, by import.** These files change only to import the constant in place of the old text:
  - `backend/tests/test_ch6_claims.py:84`
  - `backend/tests/test_ch6_evaluator.py:90`
  - `backend/tests/test_out_d4_board.py:124`
  - `backend/tests/test_demo_combined_finish_rows.py:441`
  - `tools/demo_combined_rows.py:93,98` (finish rows WK-1 and WK-4)
- **Test.** One new L0 case: a month with no fully checked day renders the line equal to `MG1_NO_DAY`, and the text does not contain "sales not recorded".
- **MOCK DEVIATION MD-WD1-2.** v69 shows the sales line only with a value. The empty state has no mock example; this replaces the earlier unlabelled empty-state words.

### 3. `GENERATOR_KWH_UNKNOWN`: change it

- **READ.** The reason fires when **either** window's generator energy is None (`B/financials/trial_fuel_comparison.py:129-130`). "Not known for both hours" is false when only one hour is missing. Rows store the reason code; the words are applied at read time (`B/site_outcomes/board.py:90`), so no stored row or golden carries the text (grep: the literal appears only at `board.py:90`).
- **Decision** (`B/site_outcomes/board.py:90`), verbatim:
  ```python
  "GENERATOR_KWH_UNKNOWN": "generator energy is not known for one or both hours",
  ```
  It matches A2-R1's `IDLE_SECONDS_UNKNOWN` form. No mock deviation: the reason words have no v69 example, as for A2-R1 D1.
- **Guard.** Run `backend/tests/test_out_e4_readback.py` (the no-code-on-screen and reason-set tests). If any other test or golden fails on this text, STOP and report it.

### 4. Mill "verified" line suffix: the mill must be labelled; not in WD-1

- **Decision.** Leaving the mill plain is **rejected**. The owner rule is that example data is clearly labelled as example data on client screens. On the S+0 Kobo board the mill verdict is judged on the same Site's example readings as the trial. A plain "ACT-… verified" beside "ACT-048 verified on example data" reads as a field result, and that is a false impression.
- **The literal** is the existing one: the mill entry uses `VERIFICATION_TEXT[s]` with `provenance_suffix(<the verdict's source class>)`, giving "… verified on example data" (`B/chain/vocabulary.py:106-112`). No new words.
- **Not in WD-1.** `OpportunityActionFact` (`B/site_outcomes/board.py:190`) and `site_chain.opportunity_actions` (`B/chain/site_chain.py:155-180`) carry no source class, and the verdict row has none on `_SITE_ACTIONS` (MB-1a-R2 §4). Labelling needs new plumbing: a source class read for the mill verdict, a field on the fact, the `provenance_suffix` call at `mini.py:1084`, MILL-5 in `tools/demo_combined_rows.py` taking the suffix by import, and the `estate_week_2026-10-25` golden check.
- **New unit WD-1m, "mill example-data label", 0.35, lane 1, after WD-1 and before PV-1** (PV-1 reads the mill verdict line too). It is demo-critical, because the mill line is on the demo board. The WD-1m pre-flight names the source: the verdict's stored evidence source class if it exists; otherwise the Site's bound telemetry source class over the verdict window (`analytics/adapters/postgres_assessment_store.py:2760` pattern). It must never be a hard-coded "example" flag. If neither source is readable within 0.35, STOP and report to the Architect.
- **Until WD-1m merges,** WD-1 leaves the mill line unchanged. WD-1's packet lists the asymmetry under residual risk, as "closed by WD-1m". It is not "accepted".

### 5. Size and order

- **WD-1: 0.15 → 0.17** (+0.02 for item 3: one literal and one guard run). Items 1 and 2 are inside the card's 0.15.
- **WD-1m: +0.35, new.** Lane 1 becomes MV-1 → MB-1a → MB-1b → WD-1 (0.17) → **WD-1m (0.35)** → PV-1. That is 2.75 + 0.02 + 0.35 = **3.12**.
- WD-1 and WD-1m are screen-wording changes. They join the post-W6 owner walkthrough, with no separate walkthrough. Guards V and N run on both.
- Logged for the owner (Architect decision during delegated absence): the mill result will carry "on example data" like the trial, which costs +0.35.

**Owner question: none.**

---

## WD-1m-R: ruling on the WD-1m pre-flight (Architect, Claude, 2026-11-08)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `cbb89ed60`; worktree `C:\Users\assef\Bineyame\AssetOpsV1-wd1m`. This section replaces WD-1-R §4's "source" paragraph. Everything else in WD-1-R §4 stands. `B/` = `backend/assetops_backend/`, `T/` = `tools/`. READ = I read the code; nothing here was measured.
- The builder's first-choice finding is accepted. The mill outcome `details` has no `source` block (`B/actions/verification_families.py:382-390`), and `site_day_snapshot.evidence_class` is not a source class. The fallback applies.

### 0. Code reality the ruling rests on (READ)

- `B/evidence/source_provenance.py:40-41`: there are exactly two positive source classes, `AUTHORED_DEMONSTRATION` and `REGISTERED_SIMULATION`, and both are in `EXAMPLE_SOURCES` (`B/chain/vocabulary.py`). Field telemetry has no publication link; it is UNBOUND. So "any of the window's evidence is published under a positive class" means the same as "some of it is example data".
- `batch_publication_link` is keyed by `batch_id` (`0017_evidence_publication.py:83`), so a class lives per batch, not per reading.
- `accepted_evidence` has `source_time` and `received_at`, and the index `accepted_evidence_site_time (site_id, source_time DESC)` (`0005_evidence_ledger.py:214`). `site.timezone` is `text NOT NULL` (`0001`).

### 1. Decisions (one line each)

- **Q1 window: (ii).** The verdict's used days (`details.baseline.days` ∪ `details.later.days`), as Site-local dates, limited to evidence received by the outcome's `recorded_at`. Rejected: (i) labels on days the verdict never used; (iii) is exact but repeats the measure per day for a label.
- **Q2 classification: "any example data labels it", not `classify`.** Return the smallest positive publication class found among the window's batches, else NULL. A mixed window still gets the label. `classify` would give MIXED/UNKNOWN and drop the label for a window that does contain example data, which breaks the owner's labelling rule. The trial's `source_pair` is a comparability gate, not a label rule, and is not reused.
- **Q3 location: (a), as a guarded lateral on `_SITE_ACTIONS`.** (b) is rejected because it crosses OUT-B4 and the evidence boundary. (c) is rejected for now: the verdict code has no evidence ids, so (c) would need this same window query at verdict time *plus* a write path, golden churn and a rebuild. E3's rebuild does not remove the golden churn. (c) goes to the backlog as BL-"mill verdict stores its source", post-demo.
- **Q4 speed: measure first; stop at more than 50 ms added per board read, or any seq scan** (§4).

### 2. The SQL (`B/chain/adapters/postgres_chain_read.py`, `_SITE_ACTIONS`)

- The existing lateral `v` also selects `o.details`. Add one guarded lateral and one output column, `source_class`. The intended form is below. The builder may adjust the syntax, but it must not change the semantics:
  ```sql
  -- in the select list:
         v.outcome, v.recorded_at AS outcome_recorded_at, src.source_class
  -- the existing lateral v also selects o.details:
  LEFT JOIN LATERAL (SELECT o.outcome, o.recorded_at, o.details FROM verification_outcome o ...) v ON true
  -- WD-1m (WD-1m-R §2): the mill verdict's example-data class over its used days; NULL = none found.
  -- No S4-05 commitment checks on purpose: a broken link can only add "on example data", never remove it.
  LEFT JOIN LATERAL (
    SELECT min(p.source_class) AS source_class
      FROM site st,
           LATERAL (SELECT array_agg(CAST(d AS date)) AS days
                      FROM jsonb_array_elements_text(coalesce(v.details->'baseline'->'days', '[]'::jsonb)
                                                     || coalesce(v.details->'later'->'days', '[]'::jsonb)) d) u
      JOIN accepted_evidence e
        ON e.tenant_id = a.tenant_id AND e.site_id = a.site_id
       AND e.source_time >= (CAST((SELECT min(x) FROM unnest(u.days) x) AS timestamp) AT TIME ZONE st.timezone)
       AND e.source_time <  (CAST((SELECT max(x) FROM unnest(u.days) x) + 1 AS timestamp) AT TIME ZONE st.timezone)
       AND CAST(e.source_time AT TIME ZONE st.timezone AS date) = ANY(u.days)
       AND e.received_at <= v.recorded_at
      JOIN batch_publication_link l ON l.batch_id = e.batch_id
      JOIN evidence_publication p ON p.id = l.publication_id
     WHERE st.tenant_id = a.tenant_id AND st.id = a.site_id
       AND a.kind = 'DOMAIN_INTENT' AND a.origin_opportunity_id IS NOT NULL AND v.outcome IS NOT NULL
  ) src ON true
  ```
- **Guard.** The lateral runs only for an opportunity-origin domain Action that has an outcome. Trials and other Actions get NULL and no scan.
- **Commitment checks are deliberately not repeated.** The S4-05 select (`postgres_evidence_ledger.py:1171-1194`) checks commitments, and a broken link resolves to BROKEN_LINK. Here a broken link to an example publication still labels. That is the conservative direction: a broken link can add the words "on example data", and it can never remove them. Write this in the packet.
- **Approved cap.** If `test_ch9b1_origin_readers.py` counts the new `origin_opportunity_id` token, raise the `chain/adapters/postgres_chain_read.py` cap by exactly the counted tokens (expected +1, class "both") with a `# WD-1m-R` comment. Anything beyond +2: STOP.

### 3. Pass-through and render

- `B/chain/site_chain.py` `opportunity_actions` (`:175-178`): add `"source_class": a.get("source_class") if known else None`. The class follows the outcome's own cutoff visibility. If no outcome is known by the cutoff, there is no class.
- `B/chain/claims.py:95` also calls `opportunity_actions`. It must ignore the new key. If any claims wire or golden gains the key, STOP.
- `B/site_outcomes/board.py` `OpportunityActionFact`: add `source_class: str | None = None` with the comment `# WD-1m-R: example-data class over the verdict's used days (None = none found)`. Fill it where the fact is built from the `opportunity_actions` dict (`mini.py:444`).
- `B/site_outcomes/mini.py:1084`: `provenance_suffix(None)` becomes `provenance_suffix(a.source_class)`. Literal: the existing `VERIFICATION_TEXT[s]` with " on example data", so the entry reads "ACT-… verified on example data". No new words and no mock deviation, because this is the trial's existing form.
- `T/demo_combined_rows.py` MILL-5 (`:279-286`): the expected mill entry takes `provenance_suffix` by import, with the class read from the board body. The live S+0 Kobo mill entry must end with `provenance_suffix(<Kobo's publication class>)`; name the class in the packet. It must never be retyped.

### 4. Speed check (before writing the render; STOP gate)

- On the authorized test DB (`*_test` in `assetopsv1-postgres-1`) with the prepared Kobo story data, run `EXPLAIN (ANALYZE, BUFFERS)` on `_SITE_ACTIONS` for Kobo with and without the new lateral.
- **STOP** and report the plan if either holds:
  - the added time is more than **50 ms**;
  - the plan reads `accepted_evidence` by seq scan rather than `accepted_evidence_site_time`.
- Record both timings and the index line in the packet. Do not add an index or a migration to fix a slow plan; report it.

### 5. Parity test (Postgres, test DB; new file `backend/tests/test_wd1m_mill_source_postgres.py`)

- **Reference.** For the same window, select the ids of `accepted_evidence` on the used days that were received by `recorded_at`. Pass them to `link_rows_on`, apply `source_provenance.link_of` to each row, keep the links that are `BOUND` with a class in `EXAMPLE_SOURCES`, and take `min` of their classes, else None. The adapter column must equal the reference in every case below.
- **Seed:** one Site whose `timezone` is not UTC, two batches on different days, one published as `REGISTERED_SIMULATION` and one unpublished (UNBOUND), and an opportunity-origin domain Action with a recorded outcome whose `details` name the days.
- **Cases:**
  1. used days only on the published batch: `REGISTERED_SIMULATION`;
  2. used days only on the unpublished batch: None;
  3. used days on both: `REGISTERED_SIMULATION` (the mixed window keeps the label; `classify` would say UNKNOWN, and the test asserts the difference on purpose);
  4. the published batch's evidence lies on a day that is not used: None (proves the window);
  5. the published evidence has `received_at` after `recorded_at`: None (proves the knowledge limit);
  6. a reading at 23:30 Site-local on a used day, which is the next day in UTC: it counts (proves the Site-local mapping);
  7. a `MINI_TRIAL` Action on the same Site: `source_class` is NULL (proves the guard).
- **Non-vacuity:** remove `= ANY(u.days)` and case 4 fails; remove the `received_at` line and case 5 fails. Record both in the packet.
- **L0:**
  - In `test_mb1_opportunity_board.py`, a mill fact with `source_class="REGISTERED_SIMULATION"` renders the entry with `provenance_suffix(...)`, and one with None renders it plain.
  - MILL-5's self-test gains a mill entry that is missing its suffix on an example Site, and that entry must FAIL.

### 6. Goldens, files, size

- **Golden diffs allowed:** only the Kobo mill "Verified results" entry gains " on example data", in any board or Portfolio golden that carries it. Any other change: STOP and report.
- **Files:**
  - `B/chain/adapters/postgres_chain_read.py`
  - `B/chain/site_chain.py`
  - `B/site_outcomes/board.py`
  - `B/site_outcomes/mini.py`
  - `T/demo_combined_rows.py` (MILL-5 only)
  - `backend/tests/test_wd1m_mill_source_postgres.py` (new)
  - `backend/tests/test_mb1_opportunity_board.py`
  - MILL-5's self-test file
  - `backend/tests/test_ch9b1_origin_readers.py` (the cap line only, if needed)
  - the affected goldens
- **Out of scope, a stop-check only.** The builder records whether the mill **verdict page** already says the result is on example data. If it does not, report it; it is not fixed in WD-1m.
- **Size: WD-1m 0.35 → 0.45** (+0.1 for the Postgres parity test and the speed gate). Lane 1 total: 3.12 → **3.22**.
- WD-1m is a screen-wording change. It joins the post-W6 owner walkthrough, with no separate walkthrough. Guards V and N run.

**Owner question: none.**
