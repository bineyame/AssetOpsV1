# Build sheet CH-6: outcome nodes, strategies, the proven-verdict rule and the Portfolio from EstateChain — split into CH-6a and CH-6b

- Architect: Claude, 2026-11-04 (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). Rulings are logged in the plan as **CH6-R**. Rulings marked **(away)** are Architect calls while the owner is away; owner to review (`.agent/decisions-while-owner-away-2026-11-04.md` D-AW-4 to D-AW-6).
- Plan: `Docs/demo-sprint/client-demo-plan.html` §2.1 CH-6 row, §2.4 OL-1, §2.5.3 PC-1, §2.5.2 MD-0, §4 ladder; CH4-R R7, CH5a-R, CH5b-R R1/R2/R7, CH3-R build question 1 (money unit) and phase-3 item 1 (Portfolio cutoff); the MA-1 ruling on the Grow card total.
- Design (`Docs/demo-sprint/implementation-logic-design-proposal.html`): A3 (proven verdicts, precedence fix), A4 (money over graded days), A6 (Portfolio composition), §4.3b (evidence-class authority, AG-9), §5b.1 `contributions:`, §5b.4 strategies (AG-15), §7 EstateChain, §8 Portfolio contract, §8b item 4 and 7, §13 backend guard (AG-31), §14 D6.
- Register: I-04, I-05, I-07, I-16, I-19, I-22 (part, R9), I-24 (the Portfolio side).
- Mock: MA-1 in v70. **M3** Grow in three parts: `frontend/mockups/v70/outcomes.js:116-121` (`GROW`, `growParts`, `pfGrowParts`), placed in `outcomeRow` `:158-163` and `pfCard` `:186-194`. **M1** day lines `:111-115` (`DAYS`, `PFDAYS`). Measurements: `.agent/MA-1-mock-measurements.md`.
- Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `T/` = `backend/tests/`. Lines are to main **`a07452c63`** (CH-1b merged). CH-5a1/5a2/5b names are as their sheets specify (`.agent/build-sheet-CH-5a.md`, `.agent/build-sheet-CH-5b.md`); pre-flight P1 re-anchors every line to the merged code.

## Why it is split (sizing ruling, CH6-R S1)

The plan's 6 units predate two additions: the OL-1 reshape with its ratchet guard (about 1 unit, plan §2.4) and the PC-1 money and verdict claims (about 1 unit, BASE-1). Counted per unit (§A10, §B9) the slice is **11 units**. It splits along the backend/estate seam:

| Slice | Lane | Units | Depends on | Delivers |
|---|---|---|---|---|
| **CH-6a** contributions, strategies, OutcomeEvaluator and the Site nodes | 1 | 6 | CH-5b (lane order), CH-5a2 (claim type, SiteChain) | `OutcomeContribution` records and the ratchet guard (OL-1). The strategy registry (AG-15). `OutcomeEvaluator`: A3 verdict over graded days, A4 earnings, the potential node, the evidence-class authority, the I-19 precedence fix. PC-1 money and verdict claims. Every board row and SiteChain outcome carries `nodes: {kpi, earnings, potential}`. MG-1 reads day snapshots, not a recount of readings. |
| **CH-6b** Portfolio from EstateChain and the Grow three parts on screen | 1 | 5 | CH-6a | EstateChain rows and earnings over the same graded window for every Site (A6, I-04). The Portfolio cards render server claims; the browser card rules are deleted (I-05, I-16, I-24). The Grow row in three parts on the board and the Portfolio card (M3, I-07). COH-17 over money and verdicts. |

- Lane 1 grows by 5 units (6 → 11). The plan's §2.1, §3 and §8 rows are updated with this sheet (**(away)**, D-AW-4).
- Order: CH-5b → CH-6a → CH-6b on lane 1. CH-6b's L3m step needs MD-0 (merged before CH-5a1). CH-9 (lane 2) may merge before or after CH-6b; §B6 says what each order means.

## CH6-R rulings (none needs the owner, except as marked)

| # | Gap (code reality) | Ruling |
|---|---|---|
| R1 | OL-1 record shape vs today's table. `ENTRIES` (`B/outcomes/outcome_map.py:16-35`) holds **15** keys (4 Findings, 3 signals, **8** warnings; the plan's "7 warnings" is a miscount). It has 14 importers (P2 lists them), not nine. | `CONTRIBUTIONS: tuple[OutcomeContribution, ...]` with exactly the plan §2.4 fields. **`ENTRIES` is derived**: for each record with `source` kind in {FINDING, SIGNAL, WARNING} and `node == "status"`, grouped by source, `moves` = MOVES records by `rank`, `checked` = CHECKED records by `rank`. A test asserts the derived dict equals today's literal, kept verbatim in the test. `DOMAIN_ALIAS`, `@LINKED`, `outcome_roles`, `categories_for`, `lens_flags`, `thread_signal_key` are unchanged. No importer changes. |
| R2 | The node records have no today equivalent. | The new records (§A2.2) are `node` in {kpi, earnings, potential}. They never appear in `ENTRIES`. For a `kpi` record, `driver` is the **objective measure key** (`B/outcomes/objectives.py:57-73` `MEASURES`), so the evaluator finds the snapshot measure behind an objective without a second table. |
| R3 | The ratchet (plan §2.4, AG-31 pre-demo part). Today's literal sites: `objectives.py:58-71` (6), `site_outcomes/mini.py:417-419,480,502,559-562`, `cold.py:128-130,266`, `ev.py:100,156-157`, `objective_facts.py:20`, `read.py:65`; key constructions `board.py:211,305,930`, `mini.py:428-430`, `warnings.py:162,168`. | **`tools/checks/check_outcome_ids.py`** (AST, run from `tools/check-architecture.ps1`, guard A). Outside `outcomes/outcome_map.py` and `outcomes/catalogue.py`, and outside `backend/tests/`, it counts per file: (a) a `str` constant that fully matches `(MG\|CC\|EV)-\d+`; (b) a `str` constant, or the first constant part of a `JoinedStr`/`BinOp` concatenation, that starts with `FINDING:`, `SIGNAL:`, `WARNING:` or `MEASURE:`. The baseline `tools/checks/fixtures/outcome_id_baseline.json` is `{file: {"count", "owner"}}`, generated on the CH-6a head after the §A6 removals. A file's count rising, or a new file with a count, fails. `--shrink` rewrites downward only. Owners: CH-10a for `objectives.py` and the `settled` dicts; CH-7 for the cold/EV composers. Self-test `tools/checks/test_check_outcome_ids.py`. |
| R4 | Strategies (AG-15) and what each may compute. | Registry `B/chain/strategies/` with six keys. **No strategy computes new money.** `priced_energy@1` multiplies stored snapshot money only (the snapshot's `money` is already measured × declared price, `B/chain/measure_impls.py:152,358`), or headroom kW × 1 h × the declared price for a potential. `avoided_cost@1` reads the stored consequence through `ChainReader.money_head` (CH-5a1). `recorded_amount@1` returns `NOT_AVAILABLE` (no billing source, AG-11). Load-time check: every `CONTRIBUTIONS.strategy` resolves, or the app refuses to start (beside CH-5b's graph check). |
| R5 | A3 inputs. Today MG-1's month counts a "checked day" as any local day with GOOD coverage, and sums every day (`B/site_outcomes/mini.py:588-618`). | **MG-1 reads day snapshots.** `value` = Σ `productive_kwh.value.kwh` over the month's COMPLETE and PARTIAL days (every subject); `checked` = COMPLETE days only; LOW days are shown and not totalled; only MEASURED/RECORDED rows count (`AUTHORITY`, design §4.3b). `judge_month` (`objectives.py:127`) is reused unchanged on that `Reading`. `_productive_month` is deleted. The value change on the polish clone is listed old → new (expected: Kobo checked days fall, because 8-of-24 h days are PARTIAL). |
| R6 | Completeness of the other KPIs. MG-2 is per day; CC-1, CC-6 and EV-1 are window counts from the composer's Readings (`cold.py:252-266`, `ev.py:100`). Design A3 Cold 28 Oct: CC-1 must not read "Met" when the chamber was not read. | A KPI `Reading.complete` is **AND-ed** with "every expected day of its `kpi` record's measure in the window is COMPLETE". The value is unchanged. `judge` (`objectives.py:112`) is unchanged, so an AT_MOST miss is still proven on incomplete days and a MET needs complete days. CC-1 on 28 Oct then reads NOT_JUDGED (design A3 data check). |
| R7 | I-19 precedence. `PRECEDENCE` (`B/outcomes/status.py:34`) ranks NO_OBJECTIVE above ON_TRACK. | Swap them: `(NEEDS_ATTENTION, WATCH, UNKNOWN, OPPORTUNITY, ON_TRACK, NO_OBJECTIVE, NOT_MEASURED, NOT_APPLICABLE)`. `STATUS_POLICY = "outcome-status/4"`. The row gains `target_note` = "{k} of {m} outcomes have a target" when the winning state is ON_TRACK and any outcome of the row is NO_OBJECTIVE (vocabulary, §A4). The Portfolio dot word `DOT_NO_OBJECTIVE` (`F/estate/PortfolioOutcomes.tsx:247-250`) stays for an all-NO_OBJECTIVE row. |
| R8 | PC-1 money and verdict claims. CH-5a2 builds the `Claim` type and the count claims (plan §2.5.3), but its sheet gives no type. | The type is fixed **here** for both slices (§A3). CH-5a2 builds it as written; CH-6a adds `money_claim` and `verdict_claim`. If CH-5a2 has merged with a different shape, P3 reports it and CH-6a adapts to the merged type without changing a count claim. The browser renders `text` only. Money text is server-rendered by one function that must equal `boardMoneyText` (`F/sites/OutcomeBoard.tsx:73`) on a shared fixture. |
| R9 **(away)** | I-22: "EV-2 never judged; MG-5 read from one noon hour". EV-2 is NOT_MEASURED by the catalogue (no odometer, `catalogue.py:53-54`). MG-5 has no day-snapshot measure; a full-day unserved-critical measure is a new adapter (CH-8 catalogue work). | **CH-6 resolves I-22 in part.** The MG-5 verdict claim names its basis in words ("checked over 12:00–13:00"), so no wider claim is made. EV-2 keeps its ruled not-measured sentence. A full-day MG-5 measure is a **labelled keep → CH-8**. D-AW-6. |
| R10 **(away)** | MA-1 ruling: "CH-6 decides whether same-currency Grow figures may be added." | **Never added, even in one currency.** Design A6 and rev 6 §2.1 forbid sums across Sites; the Sites' checked days differ (Kobo 24 h days, EV Tuesdays). The Portfolio Grow card names each Site's figure; `money_total` stays null. The note reads the mock's "Different days at each site, so not added together" when the Sites' checked-day sets differ, else "Shown per site, never added together" (vocabulary). D-AW-5. |
| R11 | Mock M3 Kobo "Estimated income" ("$7.50 over the 3 checked study days (3 × $2.50)") prices headroom, not measured use. The plan §2.5.1 and the MA-1 brief M3 give "the week … at 0.25 USD per kWh" (measured × declared). | **Estimated income = measured productive kWh × declared price** (A4, `priced_energy@1` over `productive_kwh`). The headroom money is the **Potential** part's second line, only when the study is SUPPORTED ("{lo}–{hi} {cur} per hour of use", design §5b.4). The mock's own illustrative figures stay; the difference is **MD-CH6-1**. |
| R12 | EV Potential. The mock gives "Chargers used under a fifth of capacity", the title of the `CHARGERS_MOSTLY_IDLE` warning (moves EV-3, `outcome_map.py:34`). | A `potential` record `WARNING:CHARGERS_MOSTLY_IDLE → EV-3`, `direction_only@1`, no money. The part shows the warning's own title when the warning is present, else "No potential found yet". No new detector. |
| R13 | CH4-R R7 keep: the board's opportunity signal comes from the renewable cards (`mini.py:428`), not the thread. | **Fixed in CH-6a.** The Kobo `potential` node reads the headroom opportunity **thread** (CH-4 items: state, `headroom_kw`, `window_hours`, evidence status) through ChainReader. The `SIGNAL:PRODUCTIVE_USE_HEADROOM` status signal is open exactly when that thread is OPEN or RECURRED at `k`. The renewable cards stay a contributor line only. |
| R14 | Portfolio window (I-04). Cold and EV rows use the latest selected event window (`B/site_outcomes/read.py:168` `latest_window`, `:449` `_event_window`); mini uses the UTC day of `to`. | **One graded window for every Site** (A6). Each Site's nodes are evaluated over the Site-local days of `[from, to)`. Row **state** keeps CH3-R's rule: the board composition on the Site-local day of `to − 1 µs` for mini, and over the whole window for cold and EV (their composers take any `lo/hi`, `cold.compose`/`ev.compose`, `read.py:390-391`). `latest_window` and `_event_window` are deleted from the summary and EstateChain paths. |
| R15 | Recurrence while CHANGE_APPLIED (D-AW-3) is pending MD-0's measurement. | Not in CH-6 unless D-AW-3 assigns it. CH-6 reads thread states as stored. |

## Shared definitions (both slices)

### S.1 The OL-1 record (`B/outcomes/outcome_map.py`)

```python
@dataclass(frozen=True)
class OutcomeContribution:
    source: str        # "FINDING:<mechanism>" | "SIGNAL:<key>" | "WARNING:<kind>" | "MEASURE:<measure key>"
    outcome: str       # "MG-2" or a domain alias "@COST" | "@ASSET_LIFE" | "@EVIDENCE" | "@LINKED"
    role: str          # "MOVES" | "CHECKED"
    rank: int          # 0 = primary, within (source, role)
    driver: str        # snake_case driver; for node "kpi": the objectives.MEASURES key
    direction: str     # "ADVERSE" | "FAVOURABLE" | "CHECK"
    node: str          # "status" | "kpi" | "potential" | "earnings"
    strategy: str      # "<key>@<version>", registered in B/chain/strategies
    money: Mapping[str, str] | None   # None | {"measure": …, "price": …, "label": …, "basis"?: …}
```

- Records are data only; no function, no lambda.
- Field order and names are the CH-8 export's (plan §2.4 conversion recipe).

### S.2 The claim (PC-1, `B/chain/vocabulary.py`)

```python
@dataclass(frozen=True)
class Claim:
    key: str              # e.g. "count.open_threads", "money.estimated_income", "verdict.MG-1"
    value: Any            # int | Decimal string | verdict code | None
    basis: str            # "COMPLETE" | "CHECKED_DAYS" | "NOT_KNOWN"
    days: Mapping[str, int] | None   # {"complete", "partial", "low", "no_data", "pending", "expected"}
    text: str             # rendered once, here
    def to_json(self) -> dict: ...
def count_basis(days: GradeCounts | None) -> str   # the one basis rule (Portfolio count_basis today)
```

- **`count_basis`**: NOT_KNOWN when `days` is None or `expected == 0` or every expected day is PENDING/NO_DATA; COMPLETE when `complete == expected`; else CHECKED_DAYS. It is the only basis function (plan §2.5.3).
- Wire: `{"key", "value", "basis", "days", "text"}`. Decimal values travel as strings.

## Part A — CH-6a: contributions, strategies, OutcomeEvaluator and the Site nodes (lane 1, 6 units)

- Branch: `task/CH-6a-outcome-nodes`, cut from main after CH-5b merges.

### A0. Result and boundary

**Observable result.**
- `outcome_map.CONTRIBUTIONS` is the one declaration of what moves, checks, earns and judges each outcome. `ENTRIES` is derived from it, unchanged.
- `tools/check-architecture.ps1` fails on any new outcome-id literal or map-key construction outside the two allowed files.
- Every board row (`/api/sites/{code}/outcome-board`) and every SiteChain outcome (`/api/sites/{code}/chain`) carries `nodes`: `kpi`, `earnings` and `potential`, each a PC-1 claim or null, plus `days_line`. The browser renders them through CH-5b's `OutcomeRow` slots (which showed the headline until now, MD-CH5b-2).
- MG-1's month-to-date verdict counts fully checked days from day snapshots.
- A row with a met target and an undeclared outcome reads "On track" with "{k} of {m} outcomes have a target" (I-19).

**Not in this slice.** The Portfolio (CH-6b). Any new detector, money model or measure. Any copy change outside §A4. The Grow three-part markup on the Portfolio card (CH-6b); the board's Grow parts render here only through the CH-5b slots.

### A1. Module layout

| Module | Content |
|---|---|
| `B/outcomes/outcome_map.py` | `OutcomeContribution`, `CONTRIBUTIONS`, derived `ENTRIES`, `records_for(source, node)`, `kpi_record(outcome_key)`, `warning_signal_key(kind)` (replaces `"WARNING:" + kind`, `B/outcomes/warnings.py:162,168`). Pure. |
| `B/chain/strategies/base.py` | `ContributionStrategy` Protocol (`key`, `version`, `effect(ctx) -> Effect`), `ContributionContext`, `Effect`, `Registry` |
| `B/chain/strategies/{finding_presence,direction_only,graded_verdict,priced_energy,avoided_cost,recorded_amount}.py` | one class each (§A2.3) |
| `B/chain/outcomes.py` | `OutcomeEvaluator`, `AUTHORITY`, `verdict_inputs`, `earnings`, `potential` (A3, A4). Pure: inputs are frozen facts from ChainReader. |
| `B/chain/read.py` (CH-5a1) | one new port `days_rows(site, lo_day, hi_day, measures)` → `tuple[SnapshotRow]`, memoised in the read scope, if P4 finds none |
| `B/chain/vocabulary.py` | `Claim`, `count_basis` (if not merged by CH-5a2), `money_text`, `money_claim`, `verdict_claim`, the §A4 templates |
| `B/outcomes/status.py` | R7 |
| `B/site_outcomes/board.py` | `_row` (`:692-883`) adds `nodes`, `days_line`, `target_note` |
| `B/site_outcomes/mini.py` | MG-1 from snapshots (R5); `_productive_month` (`:588-618`) deleted; Grow earnings from the evaluator, replacing `_measured_sales`'s money (`:752-790`, the contributor lines stay); the potential from the thread (R13); the literal removals of §A6 |
| `B/site_outcomes/cold.py`, `ev.py` | KPI completeness AND-ed with the measure grade (R6); EV earnings from the evaluator (`ev.py:220-226` headline money becomes the earnings claim's value; the headline text stays) |
| `B/chain_api.py` (CH-5a2) | SiteChain `outcomes[].nodes` |
| `F/blocks/OutcomeRow.tsx` (CH-5b) | the three slots render `nodes.*.text` and `days_line`; Grow uses the `ob-grow` / `ob-part` markup (M3) |
| `F/shell/chainClient.ts`, `F/sites/outcomeBoardClient.ts` | parse `nodes` (absent → null) |

### A2. The records and strategies

**A2.1 Status records.** One record per today's `ENTRIES` item: MOVES items in order, rank 0…; CHECKED items in order. `node="status"`. Strategy `finding_presence@1` for FINDING sources, `direction_only@1` for SIGNAL and WARNING. Direction: FINDING and WARNING MOVES → ADVERSE, except `SIGNAL:PRODUCTIVE_USE_HEADROOM` and `WARNING:CHARGERS_MOSTLY_IDLE` → FAVOURABLE; every CHECKED → CHECK. `driver`: a snake_case name per source (the builder proposes them in P2; e.g. `avoidable_generator_runtime`). `money=None`.

**A2.2 Node records** (exactly these; any other needs an Architect ruling):

| source | outcome | node | strategy | driver | money |
|---|---|---|---|---|---|
| `MEASURE:productive_kwh` | MG-1 | kpi | `graded_verdict@1` | `productive_use_kwh` | None |
| `MEASURE:productive_kwh` | MG-1 | earnings | `priced_energy@1` | `productive_use_sales` | `{"measure": "productive_kwh", "price": "declared.productive_price", "label": "estimated_income"}` |
| `SIGNAL:PRODUCTIVE_USE_HEADROOM` | MG-1 | potential | `priced_energy@1` | `daytime_solar_headroom` | `{"measure": "headroom_kw", "price": "declared.productive_price", "label": "potential", "basis": "per_hour_of_use"}` |
| `MEASURE:avoidable_gen_min` | MG-2 | kpi | `graded_verdict@1` | `avoidable_generator_minutes` | None |
| `FINDING:GENERATOR_SUPPORT_CANDIDATE` | MG-2 | earnings | `avoided_cost@1` | `possible_extra_fuel_cost` | `{"measure": "consequence", "price": "model.fuel-cost-1", "label": "possible_extra_fuel_cost"}` |
| `MEASURE:chamber_temp_c` | CC-1 | kpi | `graded_verdict@1` | `excursions` | None |
| `MEASURE:backup_start_chain` | CC-6 | kpi | `graded_verdict@1` | `backup_start_failures` | None |
| `MEASURE:charging_kwh` | EV-1 | kpi | `graded_verdict@1` | `interrupted_sessions` | None |
| `MEASURE:charging_kwh` | EV-3 | earnings | `priced_energy@1` | `charging_income` | `{"measure": "charging_kwh", "price": "declared.ev_tariff", "label": "estimated_charging_income"}` |
| `WARNING:CHARGERS_MOSTLY_IDLE` | EV-3 | potential | `direction_only@1` | `idle_charger_capacity` | None |

All node records: role MOVES, rank 0, direction FAVOURABLE (earnings/potential) or CHECK (kpi), except MG-2 earnings ADVERSE. MG-5 has no node record (R9).

**A2.3 Strategies.** `Effect = {direction, magnitude: (Decimal|None, unit), money: {amount|range, currency}|None, basis: MEASURED|RECORDED|DECLARED|MODELLED|EXTERNAL, days: GradeCounts-like dict, explanation_ids: tuple}`.

| Key | Computes | Never |
|---|---|---|
| `finding_presence@1` | The status signal of a Finding source: open, primary, applied, from the thread state at `k` (today's `Signal` inputs, `board.py:575-581`) | a state rule; `outcome_state` stays in `status.py` |
| `direction_only@1` | direction + the source's title; no money | a number |
| `graded_verdict@1` | §A3.1 inputs for `judge` / `judge_month` | a new comparison |
| `priced_energy@1` | earnings: Σ stored day `money.amount` over COMPLETE + PARTIAL days of the measure (A4), single currency or REFUSE (`CURRENCY_MIXED`); potential: headroom kW low/high × 1 h × the declared price at the window's last day, only when the opportunity's evidence status is SUPPORTED | scaling a partial day, extrapolating, summing across Sites |
| `avoided_cost@1` | the stored consequence's amount range via `money_head` (CH-5a1), basis MODELLED | a fuel model run |
| `recorded_amount@1` | `None` with reason `NO_RECORDS` | anything |

### A3. OutcomeEvaluator (`B/chain/outcomes.py`)

```python
AUTHORITY = {"MEASURED": True, "RECORDED": True, "DECLARED": False, "MODELLED": False, "EXTERNAL": False}

@dataclass(frozen=True)
class NodeInputs:            # built by the composer from one ChainRequest; frozen
    site_code: str; domain: str; tz: str
    window: tuple[date, date]            # Site-local [lo, hi] inclusive
    rows: tuple[SnapshotRow, ...]        # every measure of the Site over the window (and the month for MG-1)
    objectives: tuple[ObjectiveFact, ...]
    readings: Mapping[str, Reading]      # the composer's KPI readings (MG-2, MG-5, CC-1, CC-6, EV-1)
    opportunity: Mapping | None          # the CH-4 opportunity item of the Site's headroom thread at k
    warnings: tuple[Warning, ...]
    money_heads: Mapping[str, MoneyHead]  # by Finding id (CH-5a1)
    price: Mapping | None                # the declared productive price at the window's last day

class OutcomeEvaluator:
    def __init__(self, contributions=CONTRIBUTIONS, strategies=STRATEGIES): ...
    def nodes(self, inp: NodeInputs, outcome_key: str) -> dict[str, Claim | None]   # {"kpi", "earnings", "potential"}
    def readings(self, inp: NodeInputs) -> dict[str, Reading]                     # R5/R6 adjusted readings
```

**A3.1 Verdict (A3, AG-6).**
- For each objective `o` with a `kpi_record(o.outcome_key)`: `days` = rows of the record's measure in the window with `AUTHORITY[row.evidence_class]`.
- Monthly (`MEASURES[o.measure_key].monthly`, MG-1): the window is the Site-local month from day 1 to the board day. `Reading(value=Σ kWh over COMPLETE+PARTIAL days or None, complete=(elapsed == month_days and checked == month_days), checked_days=#COMPLETE days, elapsed_days, month_days)`. A day is COMPLETE when every subject row of the measure that day is COMPLETE (the `_day_grade` weakest rule, `B/chain/reader.py:42`).
- Non-monthly: the composer's `Reading` with `complete = reading.complete and all(expected day rows of the measure are COMPLETE)` (R6).
- `judge` / `judge_month` are called unchanged. `min_checked_days` comes from the objective (AG-6 "configurable per objective revision" is already met).
- MG-5 (no record): its `Reading` is used as today (R9).

**A3.2 Earnings (A4).** `priced_energy@1` over the record's measure rows in the window. `days` counts per grade. LOW days are counted in `days.low` and never add money. No priced row → `basis NOT_KNOWN`, text per §A4.

**A3.3 Potential.** Kobo: the headroom opportunity at `k` (R13): SUPPORTED → value `{lo, hi, unit: "kW"}` and the money line; LIMITED/UNKNOWN → the CH-4 limit line (`vocabulary.limit_line`, `B/chain/vocabulary.py:47-54`) as the text; no thread → "No potential found yet". EV: R12. Cold: no potential record → null.

**A3.4 Status.** `outcome_state` (`status.py:55`) is called as today with `objective = verdict` from A3.1. Only R7 changes the roll-up.

### A4. Copy (vocabulary templates; V guard; each a MOCK DEVIATION candidate against MA-1 M3 unless equal)

| Key | Text |
|---|---|
| `money.days` | `{amount} over {k} of {m} days checked` (PC-1) |
| `money.days_partial` | `{amount} over {k} of {m} days checked · {p} partly checked` |
| `money.income_suffix` | ` · not billed or collected` (MA-1 M3) |
| `money.not_known` | `Not known yet` |
| `money.currency_mixed` | `Not shown · amounts in more than one currency` |
| `potential.value` | `{lo}–{hi} kW of daytime solar unused` (today's Grow headline words, `mini.py:452`) |
| `potential.money` | `{lo}–{hi} {cur} per hour of use, at the declared price` |
| `potential.none` | `No potential found yet` |
| `target.none` | `No target set yet` (MA-1 ruling) |
| `target.days_none` | `No target, so no days are judged yet` (mock `:118`) |
| `verdict.*` | the MG-1 month texts, **moved unchanged** from `mini.py:149-152` (`MG1_SO_FAR`, `MG1_PACE`, `MG1_TOO_EARLY`, `MG1_MISSED`), with `{c}` now the COMPLETE-day count; other KPIs keep their objective actual texts |
| `verdict.mg5_basis` | ` · checked over 12:00–13:00` (R9) |
| `row.target_note` | `{k} of {m} outcomes have a target` (design A3) |
| `days_line.*` | the M1 line of each node, from its `days`: `{k} of {m} days checked`, `· {p} partly checked`, `· {n} with too little data, not counted` (mock `:112`), `No readings on {day}` for a single NO_DATA day |

- `money_text(amount: str, currency: str) -> str` must produce exactly `boardMoneyText` (`F/sites/OutcomeBoard.tsx:73-90`). Shared fixture `frontend/src/shell/__fixtures__/money-text.json` (amount, currency → text), read by a pytest and a vitest.

### A5. Wire (additive; parsers accept absent fields)

Board row and SiteChain outcome:

```json
{"nodes": {"kpi": Claim|null, "earnings": Claim|null, "potential": Claim|null},
 "days_line": "<M1 line of the row's lead node>", "target_note": "…"|null}
```

`headline`, `headline_money`, `subline`, `potential` (the old chip) keep their values for one slice; CH-6b removes the old `potential` chip from the frontend once the parts render. `policy_versions.status` becomes `outcome-status/4`.

### A6. Deletions and literal removals (the ratchet baseline shrinks)

- `mini.py:588-618` `_productive_month` (B8 AST guard entry from CH-5a2 is removed from its baseline).
- `mini.py:480` `o.outcome_key == "MG-1"` → `kpi_record` lookup by `productive_use_kwh`.
- `mini.py:502` `o["key"] == "MG-4"` → `DOMAIN_ALIAS["@ASSET_LIFE"][MINI]`.
- `mini.py:559-562` reading keys → `objectives.MEASURES[<measure>].outcome`.
- `mini.py:428-430`, `board.py:211,930` `"SIGNAL:…"` → `outcome_map` constants `HEADROOM_SIGNAL`, `EVIDENCE_GAP_SIGNAL`.
- `warnings.py:162,168` → `warning_signal_key`.
- The `settled` dicts (`mini.py:417-419`, `cold.py:128-130`, `ev.py:156-157`) stay in the baseline (owner CH-10a).

### A7. DS-R1, OL-1 and mock deviations

| Item | Touched how | Resolution |
|---|---|---|
| MG-1 "checked day" = any GOOD coverage (`mini.py:588-618`) | Replaced | **Fixed:** COMPLETE day snapshots (R5) |
| KPI "complete" without the measure grade (`cold.py:257`, `ev.py:100`) | Edited | **Fixed** (R6) |
| Board opportunity signal from the renewable cards (`mini.py:428`; CH4-R R7) | Replaced | **Fixed** (R13) |
| Precedence NO_OBJECTIVE over ON_TRACK (`status.py:34`) | Edited | **Fixed** (R7) |
| MG-5 one noon hour (`mini.py:536-547` `_depth` service window) | Labelled in the claim | **Labelled keep → CH-8** (R9) |
| Outcome-id literals in edited functions | Edited | **Fixed** (§A6); the rest in the baseline with owners |
| `noon_headroom_kw` one-hour basis (`B/chain/measures.py:46-49`) | Read, not edited | **Labelled keep → CH-9** |

**OL-1.** Every outcome link added here is a `CONTRIBUTIONS` record. The evaluator, strategies and composers name measures and sources only. The ratchet baseline is generated after §A6 and may only shrink.

**MOCK DEVIATION candidates.** MD-CH6-1 (R11 Estimated income basis). MD-CH6-2 (the §A4 lines vs the mock's examples, listed old → new). MD-CH6-3 (`target_note` has no mock place; it sits in the row subline).

### A8. Test ladder

1. **L0** `tools\run-host-tests.ps1 -- backend/tests/test_ch6_contributions.py backend/tests/test_ch6_evaluator.py backend/tests/test_ch6_claims.py`
   - Derived `ENTRIES` equals today's literal (kept verbatim in the test); every record's `strategy` resolves; every `kpi` record's driver is a `MEASURES` key and its source a `B/chain/measures.py` key; no record repeats `(source, outcome, node, role)`.
   - A3 truth tables: MG-1 with COMPLETE/PARTIAL/LOW/NO_DATA mixes (LOW never added, PARTIAL added, `checked` = COMPLETE only), MET proven on 2 days, TOO_EARLY on 1 day, ON_PACE/BEHIND_PACE, MISSED only on a full month; CC-1 with chamber NO_DATA → NOT_JUDGED; MG-2 AT_MOST miss proven on a PARTIAL day; a DECLARED-class row ignored.
   - A4: `CURRENCY_MIXED`; a PARTIAL day adds its stored amount unscaled; zero kWh on a priced day gives 0.00 (CH1a-R).
   - Potential: SUPPORTED → value + money; LIMITED (mixed) → `LIMIT_MIXED`; no thread → none.
   - R7: the design A3 "Cold lab 24 Oct" case → ON_TRACK with "2 of 3 outcomes have a target".
   - `count_basis`, `money_claim`, `verdict_claim` texts; `money_text` over `money-text.json`.
   - The ratchet self-test (`tools/checks/test_check_outcome_ids.py`): each pattern counted; an allowed file ignored; a rise fails; `--shrink` never raises a count.
2. **L1** `backend/tests/test_ch6_contract.py`: SiteChain goldens (from CH-5a2) gain `nodes` for Kobo 31 Oct and 1 Nov, Cold 31 Oct, EV 27 Oct; the frontend renders them in vitest.
3. **L2m** `backend/tests/test_ch6_nodes_postgres.py` on `mechanism_db()` (`.agent/build-sheet-MD-0.md` §7):
   - Kobo board D13: MG-1 `kpi` claim's `checked_days` equals the number of COMPLETE `productive_kwh` days D1–D13 (GAP-K7 excluded), and the verdict equals pure `judge_month` over those stored rows (asserted by recomputation, never by a literal);
   - Kobo `earnings` over the D7–D13 week: 6 of 7 days, the amount = Σ stored day money of the 6 COMPLETE days;
   - Kobo `potential` on D13: W2 SUPPORTED → value line and money line;
   - MG-2 D11 (overrun) MISSED and D12 (after ACT-K1) MET;
   - Cold D3 (GAP-C3, PARTIAL): CC-1 and CC-6 not MET;
   - EV D9: EV-3 `earnings` 1 of 1 Tuesday; EV-1 MISSED;
   - ledger: the snapshot rows are read once per request.
4. **Existing, scoped:** `test_out_a1_outcome_map.py`, `test_out_b1_status.py`, `test_out_b1_board.py`, `test_out_d2_objectives.py`, `test_out_d4_board.py`, `test_walk1_objective_min_days_postgres.py`, `test_ch5a2_*`, `test_ch5b_why*.py`, and every importer of `outcome_map`, `status`, `chain.vocabulary` (P2 lists them).
5. **L3** (clone): settle, collect and check with `expected-today.json`: 0 new findings. The packet lists every changed board value old → new (R5, R6, R7), each with its rule. **L3m:** build, collect, `check --threads … --expect expected-mechanism.json`: 0 unexpected.
6. **Frontend:** `npx vitest related --run src/blocks/OutcomeRow.tsx src/sites/OutcomeBoard.tsx src/shell/chainClient.ts`, plus the `money-text.json` vitest.
7. **Guards:** A (with the new ratchet), W, N, V, M, L, D. The estate guard self-tests do not run unless P5 needs a `configuration-persistence.ps1` edit.

### A9. Pre-flight (answer from code, batch them, then stop)

- **P1.** Re-anchor every CH-5a1/5a2/5b name used here (`ChainRequest`, `money_head`, the claim type if merged, `OutcomeRow` slots, `chain_api` outcome builder) to merged `path:line`.
- **P2.** The importers of `outcome_map`, `status` and `chain.vocabulary`; the proposed `driver` name of each status record.
- **P3.** The merged PC-1 `Claim` shape and `count_basis` (if CH-5a2 built them); any difference from §S.2.
- **P4.** Whether ChainReader already has a window-rows port; the SQL plan for one Site × 31 days × all measures on the clone (≤ 50 ms or report).
- **P5.** Whether the ratchet or any new reader needs an estate-guard registration.
- **P6.** The `ChargingEnergy.money` fields (`B/chain/measure_impls.py:358-366`): do they carry the tariff-priced amount and currency the EV board shows today (`ev.py:225`)? If not, `priced_energy@1` for EV reads the stored EV consequence through `money_head` instead; state which.
- **P7.** The `boardMoneyText` rounding rules, so `money_text` can match them; list the fixture cases.

### A10. Size: 6 units

- u1 (1.5): S.1, A2.1, derived `ENTRIES` and its equality test, `warning_signal_key`, the ratchet guard with baseline and self-test.
- u2 (1): the strategy registry and six strategies, load-time check.
- u3 (1.5): OutcomeEvaluator A3/A4/potential, `AUTHORITY`, R7.
- u4 (0.75): S.2 money and verdict claims, §A4 copy, `money-text.json`.
- u5 (1.25): the composers (§A1 rows), §A6 removals, wire, L1/L2m, the packet tables.

### A11. Review focus

- No outcome link outside `CONTRIBUTIONS`. Derived `ENTRIES` equals today's table. The ratchet only shrinks.
- No strategy computes new money; every amount is a stored amount, summed over COMPLETE and PARTIAL days only.
- `judge` and `judge_month` are unchanged; only their inputs are graded.
- Every changed board value is listed old → new with its rule. Nothing is tuned.

---

## Part B — CH-6b: Portfolio from EstateChain and the Grow three parts (lane 1, 5 units)

- Branch: `task/CH-6b-portfolio-estatechain`, cut from main after CH-6a merges.

### B0. Result and boundary

**Observable result.**
- `/api/estate/chain?from&to` (CH-5a2) carries, per Site, its graded `days` over the window, its four `rows` (state, state label, `nodes`), and per-kind `earnings` claims. Every Site is judged over the **same window** in its own time zone (I-04).
- `/api/estate/outcome-summary` reads the same composition, so the summary, the Portfolio and the boards agree (COH-17).
- The Portfolio's four cards render server claims only. `protectValue`, `growShortValue`, `growEstimates` and the per-card rules in `content` (`F/estate/PortfolioOutcomes.tsx:117-235`) are deleted (design §8b item 4).
- The Grow card has the three parts (M3, `oc-pfgrow`). Each Site's estimated income is named over its own checked days and never added (R10). The board's Grow row shows its three parts (`ob-grow`). The old `Opportunity` chip (`F/sites/OutcomeBoard.tsx:160-163`) is removed; the potential lives in its part.
- "Priority sites" and "verified results" are count claims; "recovered value" reads "No money credited · modelled, not saved" (CH3-R) as a claim (I-24).

**Not in this slice.** The Portfolio evidence and money-line reads (`evidence_money.py`, the Optimize money card): CH-5c. The Portfolio priority table rows beyond the CH-4 opportunity row (MD-CH4-1 closes here only if P4 shows the table reads EstateChain rows). Detail pages.

### B1. EstateChain composition (A6)

```python
def estate_chain(request, sites, lo: datetime, hi: datetime) -> dict:
    for site in sites:                                   # authorized, in the Portfolio order
        lo_d, hi_d = site_local_days(site.tz, lo, hi)   # [lo, hi) as Site-local days
        rows = request.days_rows(site, lo_d, hi_d, measures_for(site.site_type))   # one query for all Sites (P2)
        comp = board_composition(site, last_local_day(hi) if mini else (lo, hi), k=request.site_cutoff(site))
        nodes = evaluator.nodes(NodeInputs(..., window=(lo_d, hi_d), rows=rows, ...), outcome) per outcome
        out[site] = {"days": GradeCounts.to_json(), "rows": {cat: {state, state_label, lead, nodes, days_line}},
                     "earnings": {kind: Claim}}
    counts = {"verified_results", "open_threads", "opportunities", "priority_sites"} as count claims (sums allowed)
    return {..., "money_total": None}
```

- **Row state:** the board composition as CH3-R ruled (Site-local day of `hi − 1 µs` for mini; the whole window for cold and EV, R14). **Nodes:** over the window's Site-local days.
- **Row nodes on the Portfolio:** for each category, the lead outcome's nodes (the `roll_up` lead, `status.py:105`).
- **Earnings kinds:** one per `earnings` record whose outcome the Site's domain holds (Kobo `estimated_income`, EV `estimated_charging_income`). The MG-2 `possible_extra_fuel_cost` is **not** an earnings kind on the Portfolio (the Optimize card stays on its money lines until CH-5c).
- **Cost:** O(Sites × (days + threads + actions)), one snapshot query for all Sites, read-scope memo (CH5a-R R1).
- `B/site_outcomes/read.py:168` `latest_window` and `:449-465` `_event_window` are deleted; the summary (`:467`) calls the same per-Site composition.

### B2. Portfolio cards (server claims → markup)

| Card | Value | Detail | Days line (M1) |
|---|---|---|---|
| Grow | each Site with an `estimated_income` claim: one Site → its claim text; several → "{n} sites with an estimate" (today's wording) | the three parts `dl.oc-pfgrow`: **Target** (each Site's MG-1/EV-3 target claim, or "No target set yet at any site"), **Potential** (each Site's potential text, `Site: text · Site: text`), **Estimated income** (each Site's claim text; then the R10 note) | `PFDAYS.grow` shape: `Kobo: {line} · Depot: {line}` |
| Optimize | unchanged (CH-5c) | unchanged | the Site lines from `rows.OPTIMIZE_COST.days_line` |
| Protect | count claim `count.sites_disrupted` (Sites with a primary Protect thread OPEN/RECURRED/ACTION_IN_HAND at `k`), text by basis: COMPLETE "{n} sites disrupted" / "No sites disrupted"; CHECKED_DAYS "{n} found on the days checked" / "None found on the days checked"; NOT_KNOWN "Not known yet" | today's detail text, from the server | per Site |
| Assure | `count.verified_results` claim; "recovered value" claim | today's `assureDetailText` words, built on the server | per Site |

- The texts above that exist today in `PortfolioOutcomes.tsx` move to `B/chain/vocabulary.py` **unchanged**; the browser keeps only the markup. The vocabulary guard runs.
- `SiteDots` (`PortfolioOutcomes.tsx:253-280`) reads `rows[cat].state_label` from EstateChain.
- `GROW_ESTIMATE_BASIS` and the card basis lines come from the server.

### B3. The Grow row on the board

- `OutcomeRow` (CH-5b) renders, for `category == "GROW_REVENUE"` and a measured row, `div.ob-grow` with three `div.ob-part` (`span.ob-plabel`, `b`, `small.ob-days`) in the order **Target, Potential, Estimated income** (mock `:120`), from `nodes.kpi`, `nodes.potential`, `nodes.earnings`. A null node renders the §A4 "none" text, never an empty part.
- The row headline (`ob-val`) is the earnings text when its basis is not NOT_KNOWN, else the potential text, else the target text (I-07: the three are labelled, never merged into one sentence).
- The Grow `Opportunity` chip is removed (its content is the Potential part).

### B4. DS-R1, OL-1 and mock deviations

| Item | Touched how | Resolution |
|---|---|---|
| Three time slices in one Portfolio window (`read.py:140,150,403-437`; I-04) | Replaced | **Fixed** (R14, B1) |
| Browser card rules (`PortfolioOutcomes.tsx:117-235`; CH-5b keep) | Deleted | **Fixed** |
| Grow card shows one hour of one Site (`growEstimates`, I-05) | Deleted | **Fixed**: every Site's claim over the window |
| No money in a partly checked period (`B/estate/coverage.py:255`, I-16) | Not used by the Grow card any more | **Fixed** for Grow; the Optimize money lines are **labelled keep → CH-5c** |
| Priority count / recovered value (I-24) | Rendered from claims | **Fixed** |
| `DOT_NO_OBJECTIVE` card word | Kept | **Labelled keep** (R7): it describes an all-undeclared row |
| Portfolio evidence cell (`evidence_cell_state`) | Not edited | **Labelled keep → CH-5c** (CH5a-R R5) |

**OL-1.** EstateChain reads outcome links only through `CONTRIBUTIONS` and the evaluator. `F/estate/` gains no outcome id (CH-5b's frontend ratchet).

**MOCK DEVIATION candidates.** MD-CH6-4: the Protect card's CHECKED_DAYS forms ("found on the days checked") have no mock example. MD-CH6-5: the R10 note's second form. MD-CH6-6: the Portfolio Grow Target lists per-Site targets when any Site declares one (the mock shows only "No target set yet at any site").

### B5. Test ladder

1. **L0** `backend/tests/test_ch6b_estate_chain.py`: composition over a fixture ChainRequest: the same Site-local window for three Sites in two time zones; cold/EV rows over the whole window, mini on the last local day; counts claims summed, money never; the R10 note's two forms; the Protect basis forms.
2. **L1:** the EstateChain week golden (CH-5a2) gains `days`, `rows[].nodes`, `earnings`; `estatePortfolio.test.tsx` renders it with no server; the Grow card parts and the board Grow parts render from goldens; a body without `nodes` renders the §A4 "none" texts.
3. **L2m** `backend/tests/test_ch6b_estate_postgres.py` on `mechanism_db()`, window D7–D13 (MD-0 §7):
   - Kobo `days` = 6 of 7 COMPLETE (GAP-K7 NO_DATA); Cold 7 of 7; EV 1 expected Tuesday (D9), 1 COMPLETE;
   - Kobo `earnings` = Σ the 6 COMPLETE days' stored money; EV = D9's stored money; no total;
   - MG-1 judged on ≥ 3 COMPLETE days (`judge_month` over the stored rows);
   - the Optimize row on D13 reads the ACT-K1 verdict (RESOLVED_MONITORING since D12, CH-3 line);
   - the summary and EstateChain give equal rows and claims (in-process, same request);
   - after `late_fill(KOBO-001, D7)` and its consume: Kobo `days` 7 of 7, earnings grow by D7's stored money, and a `known_at` before the fill still gives 6 of 7.
4. **Existing, scoped:** `test_w303_portfolio_api.py`, `test_w303_portfolio_reduction.py`, `test_w303_portfolio_fixture_postgres.py`, `test_w301_estate_coverage.py`, `test_cov_partial_portfolio.py`, `test_ch5a2_chain_api_postgres.py`, and every importer of `site_outcomes.read` and `estate.portfolio` (P1 lists them).
5. **L3** (clone): settle, collect, check with `expected-today.json`: 0 new; COH-17 over count, money and verdict claims (board, summary, Portfolio, why) = 0. The packet lists every Portfolio value old → new. **L3m:** build, collect, check with `expected-mechanism.json`: 0 unexpected; the PC-1 CHECKED_DAYS forms appear only in windows containing GAP-K7, GAP-C3 or GAP-E2.
6. **Frontend:** `npx vitest related --run src/estate/PortfolioOutcomes.tsx src/estate/EstatePortfolio.tsx src/blocks/OutcomeRow.tsx src/sites/OutcomeBoard.tsx`, including `estatePortfolio.test.tsx` and `outcomeBoard.test.tsx`.
7. **Guards:** A, W, N, V, M (retire the `G-portfolio-grow-revenue` missing claim if the card no longer renders it, P5), L, D; the CH-5b frontend ratchet (`F/estate/PortfolioOutcomes.tsx` counts shrink).

### B6. CH-9 order

- **CH-9 merged first:** the Kobo Potential part reads CH-9's daylight-window study; L2m asserts D12/D13 eligible.
- **CH-6b merged first:** the Potential part reads the one-hour study; CH-9 then lists the Potential part value old → new in its packet. Either order is accepted; neither slice waits for the other.

### B7. Pre-flight (answer from code, batch them, then stop)

- **P1.** Re-anchor CH-6a and CH-5a2 names (`estate_chain`, `site_cutoff`, the EstateChain builder, `days_rows`); list the importers of `site_outcomes.read` and `estate.portfolio`.
- **P2.** One snapshot query for every Site of the window: SQL and plan on the clone (≤ 50 ms or report).
- **P3.** Every reader of `latest_window` / `_event_window` and of the summary's `short_value`, `headline_money` (frontend and tools), so none is left reading a deleted field.
- **P4.** Whether the Portfolio priority table reads EstateChain rows after CH-5a2 (MD-CH4-1).
- **P5.** The missing-claim catalogue entries on the Grow card (`G-portfolio-grow-revenue`) and the Protect card.
- **P6.** `MA-1-mock-measurements.md` budgets for `oc-pfgrow` and `ob-grow` at 1440 / 390 px.

### B8. Review focus

- Every Site in the window is judged over the same Site-local days. No per-Site "latest window" remains.
- No money is summed across Sites, in any currency. Counts may be.
- The browser renders server text; no card rule is left in `F/estate/`.
- Every Portfolio value that changed is listed old → new with its rule.

### B9. Size: 5 units

- u1 (1.5): B1 composition and the summary on the same path; deletions.
- u2 (1.5): B2 cards, server texts moved to vocabulary, browser rules deleted.
- u3 (0.75): B3 board Grow parts.
- u4 (0.75): COH-17 over money and verdicts, L2m, L3/L3m.
- u5 (0.5): the packet's old → new tables and the mock-deviation list.

## Revision OWN-1104 (Architect 5, 2026-11-04; owner agreed "all as recommended")

**R10 replaced (D-AW-5 reversed): the Grow card adds estimated income across Sites, honestly worded.**
- `money_total` is a Claim (`money.estate_income`), built by one function in `B/chain/vocabulary.py`:
  - over the Sites whose `estimated_income` / `estimated_charging_income` claim has a value;
  - **only when every such claim has the same currency**; otherwise value null and text `money.currency_mixed`.
- **Text:**
  - every contributing Site COMPLETE: "Estimated income from checked days: {total}";
  - any contributing Site CHECKED_DAYS: "At least {total} estimated income, from checked days";
  - in both cases followed by `· not billed or collected` (MA-1 M3).
- **Under it, one line per Site:** "{Site}: {amount} over {k} of {m} days checked". A Site whose claim is NOT_KNOWN is named and excluded: "{Site}: not known yet".
- **Days rule.** An EV non-operating day is NOT_EXPECTED, so it is not counted in `m` and never makes the total partial.
- **No scaling.** Values are never scaled or extrapolated. Days are not aligned between Sites; each Site's own checked days are named.
- The D-AW-5 note "Different days at each site, so not added together" is deleted.
- COH-17 checks that the total equals the sum of the Site claims shown, in the one currency.
- Design A6 is amended for Grow income only (owner, OWN-1104). Optimize money is unchanged: per Site, CH-5c.
- **Size:** CH-6b +0.25 (5.25).

**R16 new (D-AW-3, OWN-1104): a recurrence while a change is under check is recorded.**
- `B/chain/lifecycle.py` `TRANSITIONS` (`:45-56`) gains `(CHANGE_APPLIED, OCCURRENCE) → CHANGE_APPLIED`, recorded as a thread event with `cause_kind = RECURRED_DURING_CHECK`. The cause is no longer skipped (`:280`, `lifecycle_run.py:117-143`).
- **Thread line:** `thread_lines` (CH-5a2 B4) gains kind `RECURRED_DURING_CHECK`, with text "Happened again on {day}, after the change on {day} · still being checked". This is a vocabulary template and a MOCK DEVIATION candidate.
- **Counting.** The occurrence counts against the change: the verification evaluators receive the thread's during-check occurrences as an input. `reserve-trial-1` already sees the event in its later window. For CH-9b see its R6. No rule threshold changes.
- **L2m (MD-0 Kobo):** the recurrence day after ACT-K1's apply (MD0-S2) produces exactly one RECURRED_DURING_CHECK event and the line.
- **Placement and size.** Placed in **CH-6b** (+0.5), not CH-6a: CH-6a is already at 6 units, and the owner's rule splits slices over 6. **CH-6b = 5.75.**

**R16 addendum (MD-0 phase 3, 2026-11-04).** On MD-0 `states`, the D14 recurrence joined the thread (steps b/c) but produced **no lifecycle cause at all**: `run_lifecycle` returned `written 2, skipped 0, skipped_causes []`. That is a silent drop, not a skip.
- **R16 must therefore cover the cause-generation path.** `lifecycle_run` derives an OCCURRENCE cause for every occurrence joined to a thread in CHANGE_APPLIED (or later) state whose episode starts on or after the change's effective day, and the new transition records it.
- **L2m assertion:** exactly one `RECURRED_DURING_CHECK` event and one line for the D14 recurrence. An L0 test asserts that `written` counts it, not merely that `skipped` is 0.

**R16 revision MD0b-R (2026-11-04).** MD-0b verifies ACT-K1 on D12, so the D14 recurrence is now a real RECURRED from RESOLVED_MONITORING. MD-0 no longer exercises an occurrence during CHANGE_APPLIED. The D14 assertions above are replaced:
- **L0:** a thread in CHANGE_APPLIED plus an OCCURRENCE cause whose episode starts on or after the change's effective day, before any outcome. This gives exactly one RECURRED_DURING_CHECK event, `written` counts it, and the state stays CHANGE_APPLIED.
- **L2 synthetic** (`pg_harness.fresh_database()`): the same case through `run_lifecycle` and the thread store, plus the thread line.
- **L2m (MD-0):** D14 still reads RECURRED from RESOLVED_MONITORING, with no RECURRED_DURING_CHECK event (the negative case).
- No MD-0 fixture change.

## Build units (split 2026-11-05)

- Architect: Claude (Architect 13), 2026-11-05, under the owner's efficiency rule (`.ai/ROLE_CONFIG.md` "Token Efficiency", demo-sprint additions). Plan row **SPLIT-1**. No ruling above changes; this section cuts CH-6a (6) and CH-6b (5.75) into builder units.
- **Totals unchanged:** CH-6a 6 (2.5 + 2 + 1.5); CH-6b 5.75 (0.5 + 1.75 + 2.25 + 1.25).
- **Common rules** are as in `build-sheet-CH-5b.md` "Build units": one branch per unit, a per-unit reading budget, per-unit pre-flight items answered by the unit's first builder (Opus), Sonnet continuation and fix rounds, 10-line builder replies.
- **Shared reading for every CH-6 unit:** only the R-table rows named in the unit, and §S.1/§S.2 only where named. Never the whole sheet.

### CH-6a (lane 1, after CH-5b3; CH-6a1 also needs CH-5b1)

| Unit | Size | Scope | Review |
|---|---|---|---|
| **CH-6a1** records, derived `ENTRIES`, ratchet, strategies | 2.5 | old u1 + u2: R1–R4; §S.1; §A1 rows `outcome_map.py`, `strategies/*`; §A2 | Own review |
| **CH-6a2** evaluator and claims (pure) | 2 | old u3 without R7, + u4: R5, R6, R8, R11, R12, R13 (logic only); §S.2; §A1 rows `chain/outcomes.py`, `vocabulary.py`; §A3; §A4 | **Batched with CH-6a3** (pure code with no consumer until CH-6a3) |
| **CH-6a3** composers, wire, R7, removals, proofs | 1.5 | old u5 + R7 (0.25, moved from u3 so every board-value change lands in one L3 table): §A0; §A1 composer and frontend rows, `read.py` `days_rows`, `status.py`; §A5; §A6; §A7 | Batched with CH-6a2 (one review of both, after CH-6a3) |

**CH-6a1 (2.5).**
- **Reading budget:** R1–R4; §S.1; §A1 rows 1–3; §A2 (`:113-144`); §A8 item 1 first bullet and the ratchet bullet, item 4 first line; §A9 P2, P5, P6; §A11 bullet 1. Code: `B/outcomes/outcome_map.py`, `B/outcomes/warnings.py:150-175`, `B/chain/measure_impls.py:140-160,350-370`, the `B/main.py` startup hook CH-5b1 added (grep `graph`), `tools/check-architecture.ps1`.
- **Acceptance:** L0 `test_ch6_contributions.py` (derived `ENTRIES` equals today's literal, kept verbatim; every `strategy` resolves; every `kpi` driver is a `MEASURES` key; no duplicate `(source, outcome, node, role)`); `tools/checks/test_check_outcome_ids.py` (each pattern counted, allowed files ignored, a rise fails, `--shrink` never raises); the app refuses to start on an unresolved strategy; `test_out_a1_outcome_map.py` and every `outcome_map` importer (P2 list) pass with no importer edit; the ratchet baseline generated on this unit's head and run by guard A; guards W, N, V, M, L, D.

**CH-6a2 (2).**
- **Reading budget:** R5, R6, R8, R11, R12, R13; §S.2; §A1 rows `chain/outcomes.py`, `vocabulary.py`; §A3; §A4; §A8 item 1 (truth tables, A4, potential, claims and `money_text` bullets), item 6 `money-text.json` line; §A9 P3, P7. Code: `B/outcomes/objectives.py:50-140` (`MEASURES`, `judge`, `judge_month`), the merged `Claim` / `count_basis` in `B/chain/vocabulary.py`, `F/sites/OutcomeBoard.tsx:70-95` (`boardMoneyText`), `B/site_outcomes/mini.py:145-155,445-455` (texts moved unchanged).
- **Acceptance:** L0 `test_ch6_evaluator.py` and `test_ch6_claims.py` (MG-1 COMPLETE/PARTIAL/LOW/NO_DATA mixes; MET on 2 days, TOO_EARLY on 1, ON_PACE/BEHIND_PACE, MISSED only on a full month; CC-1 chamber NO_DATA → NOT_JUDGED; MG-2 AT_MOST miss on a PARTIAL day; a DECLARED row ignored; `CURRENCY_MIXED`; a PARTIAL day unscaled; zero kWh priced → 0.00; potential SUPPORTED / LIMITED / none); `money_text` equals `boardMoneyText` on `money-text.json` in pytest and vitest; `judge` and `judge_month` unedited (the diff shows it). No composer, route or frontend edit in this unit.

**CH-6a3 (1.5).**
- **Reading budget:** R5, R6, R7, R13; §A0; §A1 rows `read.py`, `status.py`, `board.py`, `mini.py`, `cold.py`/`ev.py`, `chain_api.py`, `OutcomeRow.tsx`, the two clients; §A5; §A6; §A7; §A8 items 2–7; §A9 P1, P4. Code by line range only: `board.py:680-890`, `mini.py:410-620,750-790`, `cold.py:120-135,250-270`, `ev.py:95-105,150-160,215-230`, `status.py:25-45`, `F/blocks/OutcomeRow.tsx`. `.agent/build-sheet-MD-0.md` §7 (the D-days named in §A8 item 3).
- **Acceptance:** §A8 items 2–7 in full: L1 `test_ch6_contract.py` goldens with `nodes`; L2m `test_ch6_nodes_postgres.py` (every bullet of §A8 item 3, asserted by recomputation); the scoped existing list of §A8 item 4; L3 0 new, with every changed board value listed old → new with its rule (R5, R6, R7); L3m 0 unexpected; the vitest of §A8 item 6; ratchet `--shrink` after §A6 with no file rising; guards A, W, N, V, M, L, D.

### CH-6b (lane 1 after CH-6a3, except CH-6b0 on lane 2)

| Unit | Size | Scope | Lane | Review |
|---|---|---|---|---|
| **CH-6b0** recurrence during a check | 0.5 | Revision OWN-1104 **R16**, with its MD-0 phase 3 addendum and the MD0b-R revision | **Lane 2** (moved), after CH-9b2 | **Batched with CH-9b2** |
| **CH-6b1** EstateChain composition and the income total | 1.75 | old u1 + the OWN-1104 R10 replacement (0.25): R14; §B0 bullets 1–2; §B1; R10 as replaced | Lane 1 | Own review |
| **CH-6b2** Portfolio cards and the board Grow parts | 2.25 | old u2 + u3: §B0 bullets 3–5; §B2; §B3; the CH-9 §11 Q2 label moved to server copy | Lane 1 | **Batched with CH-6b3** |
| **CH-6b3** coherence, proofs and the packet | 1.25 | old u4 + u5: §B4; §B5 items 3 (rest), 5, 7; COH-17 over count, money (including `money_total`) and verdict claims | Lane 1 | Batched with CH-6b2 (one review of both) |

**CH-6b0 (0.5). Lane move, lane 1 → lane 2.** It edits only `B/chain/lifecycle.py`, `B/chain/lifecycle_run.py` and the `thread_lines` vocabulary (CH-3 and CH-5a2 code, both merged). No other CH-6b unit reads it. CH-9b3's R6 needs it, so landing it on lane 2 before CH-9b3 removes CH-9b's "still skipped" fallback.
- **Reading budget:** the Revision OWN-1104 paragraphs "R16 new", "R16 addendum" and "R16 revision MD0b-R" only. Code: `B/chain/lifecycle.py:40-60,270-290`, `B/chain/lifecycle_run.py:110-150`, `thread_lines` (grep). If `cause_kind` is a DB enum or CHECK, the pre-flight names the migration (next free head) and the unit stops for a ruling.
- **Acceptance:** the L0, L2 synthetic and L2m (D14 negative) cases of the MD0b-R revision; `written` counts the new event; the thread-line literal passes guard V; scoped `test_ch2_*` / `test_ch3_*` lifecycle tests; guards A, W, N, V, M.

**CH-6b1 (1.75).**
- **Reading budget:** R14; R10 **as replaced** in Revision OWN-1104 (not the original R10 row); §S.2; §B0 bullets 1–2; §B1; §B5 item 1, item 3 bullets 1, 2 and 5, item 4; §B7 P1, P2, P3. Code: `B/site_outcomes/read.py:130-180,385-470`, the EstateChain builder in `B/chain_api.py` (grep `estate`), `days_rows` (CH-6a3), `status.py` `roll_up`.
- **Acceptance:** L0 `test_ch6b_estate_chain.py` (the same Site-local window for three Sites in two time zones; cold/EV over the whole window, mini on the last local day; counts summed; `money_total` only in one currency, both text forms, the per-Site lines, a NOT_KNOWN Site named and excluded, EV non-operating days not in `m`); L2m `test_ch6b_estate_postgres.py` bullets for `days`, `earnings`, the income total and summary = EstateChain; one snapshot query for all Sites (P2 plan reported); `latest_window` / `_event_window` deleted with no reader left (P3); the scoped existing list of §B5 item 4; L3 clone 0 new; guards A, W, N, V, M, L, D. The Portfolio frontend still renders its old rules after this unit (CH-6b2 replaces them); summary changes are listed old → new.

**CH-6b2 (2.25).**
- **Reading budget:** §B0 bullets 3–5; §B2; §B3; §A4 (texts only); the §B4 MOCK DEVIATION candidates; §B5 items 2 and 6; §B7 P4, P5, P6. Mock: `frontend/mockups/v70/outcomes.js` Grow row (`:115-125`) and Portfolio cards (`:185-200`); `.agent/MA-1-mock-measurements.md` `oc-pfgrow` / `ob-grow`. Code: `F/estate/PortfolioOutcomes.tsx:100-290`, `F/blocks/OutcomeRow.tsx`, `F/sites/OutcomeBoard.tsx:150-170`, `F/estate/EstatePortfolio.tsx:415-430`, `B/chain/vocabulary.py`.
- **Acceptance:** §B5 item 2 (L1 goldens; `estatePortfolio.test.tsx` with no server; the Grow parts on card and board; a body without `nodes` renders the "none" texts) and item 6 (vitest); `protectValue`, `growShortValue`, `growEstimates` and the per-card rules deleted; texts moved to `vocabulary.py` unchanged (guard V); the CH-5b frontend ratchet shrinks for `F/estate/PortfolioOutcomes.tsx`; captures at 1440/390 against the mock; guards A, W, N, V, M.

**CH-6b3 (1.25).**
- **Reading budget:** §B4; §B5 item 3 (the remaining bullets: MG-1 on ≥ 3 COMPLETE days, the Optimize row on D13 with the ACT-K1 verdict, `late_fill` with `known_at`), items 5 and 7; §B6; §B8. CH-6b1/6b2 code by grep only.
- **Acceptance:** the remaining L2m bullets; L3 clone 0 new, and COH-17 = 0 over count, money (`money_total` = the sum of the shown Site claims) and verdict claims on board, summary, Portfolio and why; L3m 0 unexpected, with the CHECKED_DAYS forms only in windows containing GAP-K7, GAP-C3 or GAP-E2; guard M retires `G-portfolio-grow-revenue` if P5 says so; the packet's old → new Portfolio table and the MD-CH6-4/5/6 list; the §B6 CH-9 order line recorded.
