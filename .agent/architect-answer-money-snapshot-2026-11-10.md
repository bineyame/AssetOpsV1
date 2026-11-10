# Architect answer: storing money in the snapshot (2026-11-10)

- Architect: Claude (fresh `assetops-architect` instance). Binding checked: `.ai/ROLE_CONFIG.md`, Architect = Claude since 2026-10-27.
- Owner question, verbatim: `.agent/owner-money-snapshot-2026-11-10.md`.
- Decisions logged as **D-MONEY.1 to D-MONEY.5** in `build-sheet-OWN-GAPS-2026-11-08.md`; the later work is **BL-67** in `backlog-post-demo.md`. Read-only investigation; no jobs were run.

## 1. In plain words, for the owner

- **You are right to want the result stored. But store it with its receipt, not on its own.** Every stored amount should carry what it was made from: the quantity (for example 41.2 kWh), the price used and which version of the price it was, the currency, the rule that multiplied them, and (later) the exchange rate with its source and date. This is how utility bills, PPA invoices and fund reports work: the bill shows the amount, and every line on it shows the meter reading and the tariff that produced it.
- **Storing only the amount fails twice.** An auditor asking "why is this 52.40?" gets no answer. And when a price is corrected, you cannot show what changed, or why. The amount alone cannot be checked.
- **Storing only the inputs and recomputing on every read is the reason pages are slow today.** It also makes an old answer depend on keeping every past formula working for ever. We use the inputs and the formula to **rebuild** a stored amount when something changes. We never recompute on every read.
- **Most of this is already in place.** Daily sales income (`productive_kwh`) is already stored as amount + currency + price version. Fuel savings and trial results are stored. The one money line still computed on every read is the **potential income** from spare solar (spare kW × 1 h × the declared price). That line moves into stored rows, with its receipt, in the second speed slice (ANY-2). It needs no separate project.
- **Data size is not a real concern.** Money with full receipts comes to about **1.5 MB per Site per year**, under 1% of what the raw meter readings take. At 1,000 Sites that is about 1.5 GB a year. What costs money is recomputing, not storing.
- **Currencies: store each amount only in the currency it was earned in.** Converting to a reporting currency is a reporting choice: which currency, and which day's rate. Converting is one multiplication per line when a page is shown, with the rate and its date written next to the result. If we stored converted amounts, we would freeze one policy into the history. Turning amounts into one currency is your decision (questions below). Until a second currency exists, amounts in different currencies are never added together, as today.
- **Tariff corrections:** a corrected price becomes a new version of that price, valid from a past date. The affected days are rebuilt as new versions. The old versions are kept, so "as known at k" still shows what was known then. How a correction is shown to the client is your call (question 2).

## 2. What exists today (verified in code)

| Money line | Where the amount lives | Receipt today |
|---|---|---|
| Sales income per day (`productive_kwh`) | `site_day_snapshot.money` = `{amount, currency, assumption_revision_id}` (`chain/measure_impls.py:145-155`); amount = unrounded kWh × rate, rounded to cent (`ROUND_HALF_UP`) | Partial: the price revision is in `money` and in `input_fp` (`price:<revision_id>`), kWh in `value`. The **rate value and the formula reference are not stored** |
| Earnings over a window | Read-time sum of stored day amounts, one currency or `CURRENCY_MIXED` (`strategies/priced_energy.py`, `_earnings`) | Composed from stored rows: fine |
| Potential income | **Read-time**: opportunity thread `study.headroom_kw` (low, high) × 1 h × the declared price at the window's last day (`chain/outcomes.py:209-237`, `priced_energy._potential`) | None stored; only in `chain_response` (a cache) |
| Avoided cost / fuel | Stored consequence range read through `money_head` (`strategies/avoided_cost.py`) | Stored by the producer |
| Trial / verified results | Stored by `financials/trial_fuel_comparison.py` (litres and priced total; intervention cost must match price currency, `:211-215`) | Stored; never totalled (FUEL-1 A2, PV-1) |
| `daylight_headroom_kw` snapshot | `value` = `{low_kw, high_kw, decision, window_hours}`, `money` NULL | n/a |
| Prices | `AssumptionReadService.series(valid_at, recorded_at)`: already bitemporal (`postgres_chain_inputs.py:221-225`) | This is the minimal tariff catalogue |
| FX | **None anywhere** (no rate table, no conversion code) | n/a |

The schema (`0043_chain_snapshots.py`) already has `money jsonb` with the CHECK "money only with a value", `input_fp`, `computed_at` and revisioning by input fingerprint. So nothing new is needed at the table level.

## 3. The options, from practice

| | (a) Amount only | (b) Inputs + versioned formula, recompute on read | **(c) Amount + receipt, rebuild on event** |
|---|---|---|---|
| Audit ("why this number?") | Fails: no trail | Passes only while every formula version still runs | **Passes: the row explains itself** |
| Restatement (price corrected) | Cannot show old vs new or why | Silent: the number just changes | **New revision; old one kept; the diff is readable** |
| "As known at k" | Only if revisioned | Needs bitemporal inputs **and** old code | **Read the latest revision with `computed_at <= k`** (today's rule) |
| Speed | Fast | Slow (today's problem, BL-66) | Fast |
| Reproducibility | None | Code-dependent | Receipt + pinned formula ref; a rebuild must reproduce it to the cent (parity test) |
| Size | Smallest | Smallest | ~1.5 MB / Site-year (below) |

Practice behind (c):
- **Utility and PPA billing** keeps the billing determinants (metered quantity per period or band, tariff schedule id and version, rate, adjustments) on every invoice line. A tariff correction is never an in-place edit of a past line. Either the period is re-billed and the original is kept (a cancel-and-rebill pair), or a true-up line is posted in the current period.
- **Energy asset finance** (lender and investor reports) restates a prior period only for material errors, and discloses that it did. Model assumptions (fuel price, tariff escalation) are versioned in a named "case", and every figure states which case produced it.
- **Multi-currency reporting** (IAS 21 / ASC 830) records a transaction in its original currency. It translates income at the transaction-date rate, or a period-average rate as a practical shortcut, and closing positions at the closing rate. The original currency amount stays the record. A translated amount is derived, and it always names its rate, source and date.

## 4. Pushback

1. **"Save the outcome" alone: no.** On its own, an amount gives no audit trail and no explainable restatement. It also cannot tell you which amounts a corrected tariff touches, unless the price version is stored next to it. In AssetOps the amount is evidence, and evidence without its basis is the thing the product exists to avoid.
2. **"Inputs + formula may not be data-efficient": the worry is real only for the read path, not for storage.** The inputs a money line needs are tiny (a quantity, a rate id, a rate, a currency). What costs a lot is recomputing on every read. So keep both: store the amount and its receipt, and use the formula only to rebuild.
3. **Do not store converted amounts or totals.** If converted amounts are stored, the choice of reporting currency and rate date is frozen into history, and the rows multiply by the number of reporting currencies. A stored cross-Site total, or a total of verified results, would be a ready-made way around A6, OWN-1104 R10 and FUEL-1 A2. Totals stay a read-time roll-up. They are refused across currencies, and they never include verified results.
4. **Store the receipt where the amount is made.** The potential line belongs with the opportunity's study revision and the price valid on that day. The board then reads it the way it reads earnings. Folding it into BL-66's `money.lines` kind does exactly this.

## 5. Size, per Site-year

- Money-bearing rows per Site-day: about 2-6. Examples are one sales line per productive asset, one potential line, and one or two avoided-cost or fuel lines. Cold and EV Sites have fewer.
- Receipt per line: about 250-400 bytes of jsonb (amount, currency, quantity, unit, rate, rate revision id, formula ref, basis, receipt version, and an `fx` slot that stays null for now).
- About 2,000 lines × about 0.35 KB × about 1.5 for revisions (late data, corrections) ≈ **1.0-1.5 MB per Site-year**, plus index overhead of roughly the same order.
- For comparison: one Kobo Site produces readings at roughly a minute's grain over several channels, which is about 10⁶ rows and hundreds of MB per year. Money is under 1% of storage.
- At 1,000 Sites: about 1.5-3 GB per year. That is ordinary for Postgres with BL-66's monthly partitions. **The size concern does not hold at this scale or the next.**

## 6. Where it lives

- **It fits inside the existing design. No separate money ledger now.**
  - Daily measured money stays in `site_day_snapshot.money`, and the receipt gets complete fields.
  - Window, potential and evidence money go into BL-66's `site_period_read` as the `money.lines` kind (AR-4). The kind also covers `money.potential`: per (Site, local day), the study's headroom × 1 h × the price valid that day. The window read takes the window's last day row, which is today's rule, so it decomposes exactly.
  - Rebuild triggers already exist: `by_assumption_key` with `from_valid_local_to_today` in `event-register-v1.yaml`.
- **The minimal tariff catalogue is the existing bitemporal assumption store.** A flat price per key, with valid-from and recorded-at, is enough for today's Sites.
- **The receipt shape is decided now, so the schema is not redone later.** Each money line in `money` or in a `money.lines` body is shaped as follows:

```json
{"amount": "52.40", "currency": "TZS",                 // or low/high for a range
 "basis": "MEASURED|DECLARED|MODELLED|RECORDED",
 "receipt": {"v": 1, "formula": "priced_energy@1",
             "qty": "41.234", "unit": "kWh",
             "rate": "1.2708", "rate_unit": "TZS/kWh", "rate_ref": "<assumption_revision_id>",
             "segments": null,                          // later: time-of-use / mid-day tariff split
             "fx": null}}                               // later: {from, to, rate, rate_date, source, revision_id}
```

- **The amount is computed from the unrounded quantity, then rounded to the cent**, as `measure_impls.py` does today. The receipt states the rounding. A rebuild must reproduce the amount exactly, and a receipt that does not reproduce is a defect.
- **Later (BL-67, post-demo):**
  - **FX rate store.** It is append-only and bitemporal: base, quote, rate, rate_date, source, valid and recorded times. Conversion happens at read time under the owner's reporting policy, and the converted line names its rate.
  - **Structured tariffs.** Time-of-use bands, tiers, demand charges, and PPA escalation or indexation, as a `tariff` assumption kind with a `tariff_energy@1` strategy that fills `segments`.
  - **Restatement display.** A "restated on <date>, was X" note, read from the previous revision.
  - **A true settlement ledger** (double-entry, invoice-grade) only if AssetOps ever becomes the billing system of record. It is not that now.

## 7. Units and sequencing

| Card | Scope | Size | Where |
|---|---|---|---|
| **MN-1** Receipts on stored day money | `productive_kwh.money` gains `basis` and `receipt{v, formula, qty, unit, rate, rate_unit, rate_ref}`. `measure_impls` builder version bump, so old rows read PENDING until the backfill (BL-66 rule). L0 checks the receipt reproduces the amount (must-fail: wrong rate). | 0.25 | Folded into AR-4 |
| **MN-2** Potential money stored | The `money.potential` row in AR-4. `priced_energy._potential` reads the stored line. AR-0 parity check against today's read-time value, byte for byte. | 0.5 | Folded into AR-4 |
| **MN-3** No-total guard | An AST/L0 guard: no row kind, migration or builder writes a cross-Site, cross-currency or verified-result total. Estate roll-up rows (BL-66 estate stage) hold per-Site money lines only. | 0.25 | AR-4 |
| BL-67a FX store + read-time conversion + label | | 1.0 | Post-demo, when a second currency or a reporting-currency demand exists |
| BL-67b Structured tariffs (`segments`) | | 1.5-2.0 | Post-demo, at the first time-of-use or PPA Site |
| BL-67c Restatement note | | 0.5 | Post-demo (or sooner, depending on the owner's answer to Q2) |

- **ANY-1 (boards, AR-0/1/2, 3.0 units) is unchanged and can start as planned.** Before AR-1's migration is written, the generic contract must take D-MONEY.1 to D-MONEY.4:
  - `site_period_read.body` for money kinds holds lines in the receipt shape above.
  - `input_fp` includes every `rate_ref` (and, later, every fx ref).
  - `builder_version` covers the receipt version.
  - The AR-0 harness compares money to the cent.
  - None of this adds a column.
- **ANY-2 grows from 3.75 to 4.75 units** (AR-4 goes from 1.5 to 2.5 with MN-1/2/3). That is still under the 6-unit split rule. The ANY-1 then ANY-2 order stays.

## 8. Questions that are genuinely the owner's

1. **Reporting currency policy.** When Sites earn in different currencies, should the Portfolio show one reporting currency? If yes, which one, and at which rate: transaction-date, period-average, or the rate on the report date? Until you decide, amounts in different currencies are shown per Site and never added (today's `CURRENCY_MIXED`).
2. **Restatement policy.** When a price or tariff is corrected backwards, should the client see:
   - (i) the restated figure, with a "restated on <date>, was X" note (the Architect's recommendation, since AssetOps is evidence, not a ledger, and "as known at k" keeps the original); or
   - (ii) the original figure, plus a separate adjustment line in the period of the correction (billing practice)?
3. **Billing system of record.** Will AssetOps ever issue or settle invoices? If yes, BL-67 needs an immutable settlement ledger later. If no, the receipt rows are enough.
