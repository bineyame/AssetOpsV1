# CH-6a3 pre-flight: composers, wire, R7, the `_productive_month` removal, "Why?" measures and price

- Branch `task/CH-6a3-composers` from `task/CH-6a2-evaluator` at `e373109bc`. Sheet: `build-sheet-CH-6.md` CH-6a3 unit,
  SCOPE-1, CH6a1-R Q1, CH6a2-R; CH5b2-R / CH5b2-R2 for "Why?". No code written yet.

## 1. Scope against code (path:line at `e373109bc`; `B` = `backend/assetops_backend`, `F` = `frontend/src`)

| Item | Code fact | Plan |
|---|---|---|
| Evaluator API | `B/chain/outcomes.py:41` `NodeInputs(site_code, domain, tz, window, rows, objectives, readings, opportunity, warnings, money_heads, price, lead_findings)`; `:132` `readings(inp)`, `:230` `nodes(inp, key)` | each composer builds one `NodeInputs` |
| P4 rows port | `B/chain/read.py:309-326` `ChainRequest.day` reads `ports.snapshots` under memo `"chain.day"` and keeps grades/values only (no `evidence_class`, no `money`); `SnapshotRow` `B/chain/ports.py` has both | new `ChainRequest.rows(site_id, site_type, days)` with the **same memo key**, returning the raw rows. Mini's `chain_day` (`B/site_outcomes/read.py:225`, 31-day work window, covers the MG-1 month) and cold/EV `readiness` (`read.py:194-197`, `local_days(lo, hi)`) already make that exact call, so no new statement |
| Mini composer | `B/site_outcomes/mini.py:373-527`; month `:407`; readings `:495`; signal `:442` (`study is not None`); Grow money `:483-485` from `_measured_sales` (`:799-838`, kWh × `productive_price` series, `:806`) | R5: readings from `evaluator.readings`; `_productive_month` (`:636-668`) and `mg1_reading` / `mini_readings`' MG-1 branch deleted; R13: signal = `headroom_signal_on(item)`, `opportunity` = the CH-4 item from `ports.opportunity` (`mini.py:549-558` already reads it, keeps only `study`) |
| Cold / EV composers | `cold.py:179` `cold_readings`, `:181` `SiteFacts`; `ev.py:251` `ev_readings`, `:228` Grow `headline_money` from `consequence_summary` | R6 via `evaluator.readings`; EV earnings claim from `charging_kwh` snapshots; headline text stays |
| Board row | `B/site_outcomes/board.py:695-895` `_row`; row dict `:716-726`, update `:883-894`; `SiteFacts` `:248-281` | `SiteFacts.nodes` (per outcome key) added by the composers; `_row` emits `nodes`, `days_line`, `target_note` |
| R7 | `B/outcomes/status.py:16` `STATUS_POLICY = "outcome-status/3"`, `:35` `PRECEDENCE` | swap ON_TRACK/NO_OBJECTIVE, `/4`; 10 contract fixtures carry `outcome-status/3` (`backend/tests/fixtures/ch5a1_board_contract/*`, `ch5a2_chain_contract/*`) and are regenerated |
| SiteChain | `B/chain/site_chain.py:179-183` `outcomes_of(board_rows)` | copies `nodes`, `days_line`, `target_note` from the row |
| "Why?" measures | `B/chain/why.py:85-89` `used_measures` = thread clean-day measures only; `:161-171` measure lines; `MAX_FROM = 4` (`:36`) | CH6a1-R Q1: UNION the `MEASURE:` records' measures of the category's outcomes (domain-filtered), Site-type order |
| "Why?" price | snapshot money carries no price value: `B/chain/measure_impls.py:160` (`amount`, `currency`, `assumption_revision_id`), `:453-456` (EV: `tariff_revision_ids`) | price from the composer's declared-price read (mini `productive_price` series, `mini.py:806`; EV `consequence_summary.tariff_value`, `ev.py:186`), see Q3 |
| `_productive_month` guard | `tools/checks/check_chain_structure.py:35,37` `REPLACED_CALLS/DEFS`; baseline `tools/checks/fixtures/chain_structure_baseline.json:15,43` | baseline entries removed (shrink only) |
| Frontend | `F/blocks/OutcomeRow.tsx` (62 lines; slots replace the headline when filled, `:23-49`); caller `F/sites/OutcomeBoard.tsx:177`; row type `F/sites/outcomeBoardClient.ts:155-173`; chain client is `F/sites/chainClient.ts` (the sheet's `F/shell/chainClient.ts` does not exist) | parsers accept absent `nodes`; Grow renders the parts (Q2) |

## 2. Architect confirmation: the CH-6a2 Known Deviations (`review-packet-CH-6a2.md:91-109`)

1. **MG-5 " · checked over 12:00–13:00" not built.** CH-9 R9 made MG-5 read the whole day (`mini.py` `MG5_UNSERVED`), so the suffix would be untrue. Recommend: confirm.
2. **ACTION_IN_HAND reads `potential.none`.** `POTENTIAL_STATES` (`outcomes.py:31`). In ACTION_IN_HAND, the action is agreed but no change is applied. Q4's own reason ("a change applied but not verified leaves the study as the latest evidence") applies even more strongly before the change, so "No potential found yet" there is untrue. **Default: add ACTION_IN_HAND in CH-6a3, with a test.** The R13 signal stays OPEN/RECURRED.
3. **R6 needs `expected > 0`** (`outcomes.py:124`): with no expected day of the measure, no MET is possible. Recommend: confirm.
4. **`NodeInputs.lead_findings`** (`outcomes.py:55`) is additive. Mini fills it from its `lead_money` (`mini.py:425`). Recommend: confirm.
5. **Earnings `value` = `{"amount","currency"}`** or `{"low","high","currency"}`, as strings. Recommend: confirm (Q3 adds two optional keys).
6. **MG-2 earnings text is the amount alone**, because there are no days (Q2). Recommend: confirm.
7. **`vocabulary.mg1_text` restates `mini.num`.** In CH-6a3, the MG-1 board text comes from `evaluator.readings` (`_month_text`), so `mini.mg1_reading` is deleted, not re-pointed. Recommend: confirm.
8. **`row.target_note` (R7)** is built here. Recommend: confirm.

## 3. Questions (each with the default I build if not overridden)

- **Q1. Which outcome's nodes does a row carry, and what is `days_line`?** A row holds several outcomes. Default:
  - `earnings` and `potential` are the row's outcome that has that record. Today there is at most one per row: Kobo Grow MG-1, Kobo Cost MG-2, EV Grow EV-3.
  - `kpi` is the lead outcome's claim when it has an objective, else the first row outcome (catalogue order) with an objective, else the claim of the outcome with the `kpi` record (giving "No target set yet").
  - A row with no node record and no objective (Protect/Assure today) has `nodes` = all null and `days_line` = null.
  - `days_line` = the first non-null `days_line(claim.days)` in the order kpi, earnings, potential. If that is null and the kpi is `target.none`, it is `target.days_none`.
- **Q2. What renders where?**
  - A row with an `earnings` or `potential` record (Grow today) renders `ob-grow` with three `ob-part`s, as in mock M3 (`v70/index.html:420-421`): Target = kpi, Potential, Estimated income. Each part has its own days line, because M3 puts it inside the part. BL-13 covers only the row-level M1 line under the value, which stays in "Why?".
  - Other rows keep the CH-5a2 headline, and no slot is passed. Their kpi text is often a raw actual ("12 minutes"), not a headline, so showing it would be a regression.
  - The potential's `"\n"` is split into lines (CH6a2-R Q1).
  - The old `potential` chip stays (§A5; CH-6b removes it).
- **Q3. The price line (SCOPE-1).** Snapshot money holds no price (§1). Default:
  - The earnings claim `value` gains optional `kwh` (Σ counted-day kWh) and `price` `{"amount","currency"}`. They are filled by the composer's declared-price read: the mini `productive_price` series at the board day; for EV, `consequence_summary.tariff_value` only when the summary is PRICED with one tariff.
  - "Why?" adds `why.from.price` = "{kwh} kWh × {price} {cur}/kWh" right after the earnings measure's line, inside `MAX_FROM`. It is a MOCK DEVIATION against "× assumed price $0.30 per kWh".
  - If the counted days carry more than one `assumption_revision_id` / tariff revision, there is no single price, so the line is omitted and the packet counts the case.
  - The MG-2 `avoided_cost@1` money is a stored model consequence priced per litre, not per kWh, so it gets no price line here. This becomes a Known Deviation, unless you rule that "every money claim" includes it. If you do, the line would be the consequence's own litres × price, if its body carries them.
- **Q4. The board money moves to the evaluator.** Kobo Grow and EV Grow `headline_money` become the earnings claim's amount, from stored snapshot money over COMPLETE/PARTIAL days.
  - The headline text stays.
  - On a LOW/NO_DATA board day, the money disappears (NOT_KNOWN). Today it shows kWh × price.
  - Each case is listed in the L3 old → new table. Default: accept.
- **Q5. R13 changes the state.** The Kobo Grow OPPORTUNITY signal turns off whenever the headroom thread is not OPEN/RECURRED, including ACTION_IN_HAND and CHANGE_APPLIED. The Grow headline "18–20 kW…" and the renewable contributor stay from the study. Default: accept, listed in L3.
- **Q6. L1 golden fixtures.** The 10 `ch5a1_board_contract` / `ch5a2_chain_contract` goldens change: `status` becomes `/4`, and `nodes`, `days_line` and `target_note` are added. Default: regenerate them, with the diff in the packet limited to those keys plus the R5/R6/R7/R13 value changes. `test_ch6_contract.py` asserts the node keys on the four named goldens.

## 4. Size

1.75 as briefed. If Q2 must also render the row-level M1 days line, that is +0.25, with BL-13 pulled in.
