# CH-6a3 handoff (PARTIAL, stopped at the context limit)

Branch `task/CH-6a3-composers`, head `6cdfdc4aa` (on `c41dc104b`). Binding: `.agent/CH-6a3-preflight.md` + CH6a3-R
(end of `AssetOpsV1-plan2/.agent/build-sheet-CH-6.md`). `git merge main` not yet done.

## Landed (commit 6cdfdc4aa; L0 `test_ch6_evaluator.py` + `test_ch6_claims.py` 59 passed)
- `B/chain/outcomes.py`: `POTENTIAL_EXCLUDED`, `POTENTIAL_STATES` derived from `lifecycle.TRANSITIONS` minus the
  exclusion, `potential_shown(item)` (use it for Q5 too). Tests: ACTION_IN_HAND shown + no signal; 3 excluded states.
- Earnings claim `value` gains `kwh` + `price {amount,currency}` (one revision, `inp.price`) or `price_count` (n>1):
  `energy_basis(rows, price)`. MG-2 earnings gains `litres_low/high` + `price` from `money_head.body["consequence"]`
  `quantity`/`price` (`financials/consequence_read.py:110-118`): `fuel_basis(head)`, None when no price.
- `site_nodes(inp, keys)` -> `{key: {kpi, earnings, potential} JSON}` for keys with an objective or a node record.
- `B/chain/read.py` `DayFacts.rows` = the raw `SnapshotRow`s of the same memo read (no new statement).
- `B/outcomes/status.py` R7 swap, `outcome-status/4`. `vocabulary.NODE_TEXT["row.target_note"]`.
- `B/site_outcomes/board.py`: `SiteFacts.nodes`; `row_nodes(...)` (Q1) spread into the `_row` dict (`nodes`,
  `days_line`, `target_note`). `B/chain/site_chain.py` `outcomes_of` copies them.

## Next (in order)
1. Mini composer `B/site_outcomes/mini.py` `compose` (:373-527): build `NodeInputs(site_code=c, domain=MINI,
   tz=zone_name, window=(day, day), rows=day_facts.rows, objectives, readings=mini_readings(...),
   opportunity=<CH-4 item, change `_study` (:549) to return the item; study = item["study"]>, warnings,
   money_heads={lead id: money_head}, lead_findings={"GENERATOR_SUPPORT_CANDIDATE": lead id},
   price=_measured_sales' price)`; `readings = OutcomeEvaluator().readings(inp)`; `nodes = site_nodes(inp, keys)`
   into `SiteFacts(nodes=...)`. R13: signal `headroom_signal_on(item)`; Q5: Grow headline/"kW unused" chip only when
   `potential_shown(item)`. Grow `headline_money` = earnings claim amount (`{amount_low, amount_high, currency}`),
   None when NOT_KNOWN (Q4). Delete `_productive_month`, `mg1_reading`, the MG-1 branch of `mini_readings`
   (callers: `tests/test_ch6_claims.py:86`, `test_walk1_3b_target_progress.py:202`, `test_out_d5_objectives_postgres.py:94`);
   remove both `_productive_month` entries from `tools/checks/fixtures/chain_structure_baseline.json:15,43`.
   `_measured_sales` (:799) must return `"price": {"amount": str(value), "currency": cur}` when priced.
2. Cold/EV (`cold.py:179`, `ev.py:228,251`): new port `chain_rows(lo, hi)` in `B/site_outcomes/read.py:194-200`
   (`req.day(...).rows`, same memo); `readings = evaluator.readings(inp)` (R6); EV Grow `headline_money` from the
   EV-3 earnings claim; EV price `consequence_summary.tariff_value` (`ev.py:186`) when PRICED with one tariff.
3. "Why?" `B/chain/why.py`: `used_measures` (:85-89) UNION the category outcomes' `MEASURE:` records (domain-
   filtered, Site-type order); after the earnings measure line add `why.from.price` "{kwh} kWh × {price} {cur}/kWh",
   `why.from.price_several` "{kwh} kWh at {n} declared prices over these days", `why.from.fuel_price`
   "{lo}–{hi} L × {price} {cur}/L" (one value when lo==hi), all inside `MAX_FROM`.
4. Frontend: `F/sites/outcomeBoardClient.ts:155-173` + `F/sites/chainClient.ts` parse `nodes`/`days_line`/
   `target_note` (absent -> null); `F/blocks/OutcomeRow.tsx` Grow `ob-grow` three `ob-part`s (Target, Potential,
   Estimated income), each with its days line, potential split on "\n"; `target_note` under the subline.
5. Regenerate the 10 goldens (`backend/tests/fixtures/ch5a1_board_contract/*`, `ch5a2_chain_contract/*`), add
   `test_ch6_contract.py`; L2m `test_ch6_nodes_postgres.py`; scoped existing list (§A8 item 4); vitest.
6. Clone L3 table, MD-0 L3m if stale, graph check, ratchet, guards one at a time, packet, merge main.

## Risks
- Until step 1-2, every board row's `nodes` is all null and R7 changes states: goldens/board tests fail at this head.
- `row_nodes` treats kpi "No target set yet" by text match on `target.none`; fine but brittle.
