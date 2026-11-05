# CH-6a1 pre-flight (records, strategies, CHARGERS_MOSTLY_IDLE) - branch `task/CH-6a1-records` from `628f77b36`

Binding scope: `build-sheet-CH-6.md` "Scope cut (SCOPE-1)" CH-6a1 (1.25): R2 node records + `records_for` /
`kpi_record` beside the unchanged `ENTRIES`; R4 registry (six keys, no new money); R12 record kept; graph known-gap
owner -> BL-06. Not built: BL-03 (R1 reshape, status records, derived `ENTRIES`, `warning_signal_key`), BL-04 (R3
ratchet `check_outcome_ids.py`), BL-05 (startup strategy refusal), BL-06 (detector).

## Code facts (path:line, worktree `628f77b36`)

- F1 `ENTRIES` literal: `backend/assetops_backend/outcomes/outcome_map.py:16-35`, 15 keys; stays byte-identical.
- F2 Objective measure keys `outcomes/objectives.py:57-73` `MEASURES`: avoidable_generator_minutes, productive_use_kwh,
  unserved_critical_kwh, backup_start_failures, interrupted_sessions, energy_cost_per_km. CC-1's driver `excursions` is
  NOT a `MEASURES` key; it is `CHAMBER_RANGE_MEASURE` (`objectives.py:75`). See Q2.
- F3 Chain measure keys `chain/measures.py:43-66`: productive_kwh, daylight_headroom_kw, critical_served,
  avoidable_gen_min, chamber_temp_c, backup_start_chain, charging_kwh. Every A2.2 `MEASURE:` source resolves. The
  potential money `"measure": "headroom_kw"` is not a chain measure (the chain key is `daylight_headroom_kw`; R13 reads
  `headroom_kw` from the opportunity thread items). See Q3.
- F4 Stored money is already measured x declared price (`chain/measure_impls.py:152-160`, `money()` returns
  `{"amount","currency",...}` or None); cold/backup `money()` returns None (`:362-363`). `priced_energy@1` sums only.
- F5 `avoided_cost@1` reads `ChainReader.money_head` (`chain/read.py:386`), returns `MoneyHead | None`.
- F6 `finding_presence@1` inputs: today's `Signal(kind, key, primary, open, applied, effect, signal_key)` built at
  `site_outcomes/board.py:570-578`; `outcome_state` stays in `outcomes/status.py`.
- F7 Graph known gap: `chain/graph.py:47` `(None, "CH-6a1")`, comment `:49`; pinned by `tests/test_ch5b_graph.py:32`
  (printed "owner CH-6a1") and `:100-103`. No `.dot`/`.svg` carries the owner text (grep), so no re-render.
- F8 Why measure rule (the CH5b2-R Q5 interim): `chain/why.py:85-89` `used_measures` (thread mechanisms'
  `clean_day_measures`), used at `why.py:154`; docstring `why.py:9-11` names CH-6a1 as its replacement. See Q1.
- F9 Catalogue categories (`outcomes/catalogue.py:44-63`): MG-1, EV-3 GROW_REVENUE; MG-2 OPTIMIZE_COST; CC-1, CC-6,
  EV-1 PROTECT_ASSET. So a `MEASURE:charging_kwh -> EV-3` record gives EV Grow its measure line (CH5b2-R Q5 KD).
- F10 Guards: no outcome-map or strategy seam in `tools/checks/`; `check_chain_structure.py` (`:31-37`) is untouched
  by these files. Frontend hard-wiring ratchet: no frontend edit planned, so it cannot rise.

## CHARGERS_MOSTLY_IDLE (CH5b1-R Q1) - confirmed against SCOPE-1

The dispatch default was "remove the key and the R12 record". SCOPE-1 (binding, later than CH5b1-R) says the
opposite: "R12 record kept, showing 'No potential found yet' while the warning has no producer; the graph check's
known-gap owner text ... becomes BL-06"; `backlog-post-demo.md` BL-06 agrees. I follow SCOPE-1 (Q4): keep the
`ENTRIES` key and the R12 record; `graph.py:47` owner `"CH-6a1"` -> `"BL-06"`; test pins updated; no detector.

## Planned files

- `outcomes/outcome_map.py`: `OutcomeContribution` (S.1 fields, frozen), `CONTRIBUTIONS` = the ten A2.2 rows exactly,
  `records_for(source, node)`, `kpi_record(outcome_key)`, `category_measures(domain, category)` (only if Q1 = wire).
- `chain/strategies/{__init__,base,finding_presence,direction_only,graded_verdict,priced_energy,avoided_cost,
  recorded_amount}.py`: Protocol, `ContributionContext`, `Effect`, `Registry`, `resolve(key@ver)`. Pure.
- `chain/graph.py` owner text; `chain/why.py` (Q1 only).
- Tests: `tests/test_ch6_contributions.py` (L0: records exact, no duplicate `(source,outcome,node,role)`, every
  strategy resolves, every kpi driver a measure key, every `MEASURE:` a chain measure, `ENTRIES` equals today's literal
  verbatim, strategy effects incl. CURRENCY_MIXED / partial unscaled / NOT_AVAILABLE); `test_ch5b_graph.py` pins;
  scoped: `test_out_a1_outcome_map.py`, `test_ch5b_graph.py`, `test_ch5b_why.py`.

## Lane-2 overlap (CH-9b2: 0052, `actions/*`, `verification_*`)

None by file. Only shared surface: if CH-9b2 adds an event-register row or lifecycle mechanism, the graph check
inputs change, not `graph.py:47`. Merge order free.

## Questions (all in one batch; each has a default)

- Q1 Wire the `MEASURE:` records into "Why?" in this unit? Default **yes**: `used_measures` = thread clean-day
  measures UNION the measures of the category's `MEASURE:` records (Site-type order kept). Closes CH5b2-R Q5's KD
  (EV Grow gets its `charging_kwh` line). It changes stored why bodies, so one polish clone run (W6 + fresh + COH)
  follows. Alternative: data only here, wiring in CH-6a3.
- Q2 CC-1's kpi driver `excursions` is not a `MEASURES` key (F2). Default: the L0 rule is "a `MEASURES` key or
  `CHAMBER_RANGE_MEASURE`"; the record keeps `excursions` as the sheet writes it.
- Q3 Potential money `"measure": "headroom_kw"` (F3). Default: keep the sheet's text (the thread item R13 reads);
  the L0 test requires an earnings `money.measure` to be a chain measure or `consequence`, and the potential one to be
  `headroom_kw`.
- Q4 CHARGERS_MOSTLY_IDLE: default as above (keep key + R12 record, owner BL-06), not removal.
- Q5 `ContributionContext` shape is unspecified. Default: a frozen dataclass of already-read facts (record, day rows
  as `SnapshotRow`, thread `Signal`s, `MoneyHead | None`, declared price/currency at the last day, opportunity
  evidence status, title); CH-6a2 may add fields additively. `Effect` as A2.3, `money=None` when not priced, with a
  `reason` (`CURRENCY_MIXED`, `NO_RECORDS`, `NOT_SUPPORTED`).
