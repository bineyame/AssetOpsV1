# CH-6a3 handoff 2 (PARTIAL, builder 2 stopped at the context limit)

Branch `task/CH-6a3-composers`. Binding: `.agent/CH-6a3-preflight.md` + CH6a3-R. `git merge main` NOT done.
Env: venv python `AssetOpsV1-plan2/.venv/Scripts/python.exe`, absolute PYTHONPATH of this worktree.

## Landed since handoff 1 (all committed)
- Mini composer (`site_outcomes/mini.py`): `_opportunity_item`, NodeInputs, evaluator readings, `site_nodes`, R13 signal
  `headroom_signal_on`, Q5 `potential_shown`, Grow `headline_money` = `earnings_money(earnings claim)` (new helper in
  `chain/outcomes.py`), `_measured_sales` returns `price`. `_productive_month`, `mg1_reading`, MG-1 branch deleted;
  baseline entries removed. Cold/EV: `chain_rows` port (`read.py`, `ColdPorts`/`EvPorts`), `board.domain_nodes(...)`.
  EV Grow money from the earnings claim (null when the claim is NOT_KNOWN).
- "Why?": `chain/why.py` `outcome_measures`, `price_lines`; texts `why.from.price|price_several|fuel_price|fuel_price_one`.
  `tests/test_ch5b_why.py:150` slice changed `[1:]` -> `[-2:]` (a second measure line from the union).
- Goldens regenerated (10). Test fake changes: `Row` gained evidence_class/value/money defaults; the Kobo opportunity
  fake item gained `"state": "OPEN"` and `study.status "SUPPORTED"` (else the R13 signal/Potential vanish in the fake).
  Golden diffs: status /3 -> /4; nodes/days_line/target_note added; EV `headline_money` 54.75 -> null (Q4: fake snapshot
  rows carry no money, so the earnings claim is NOT_KNOWN); cold CC-1 kpi MISSED claim.
- Tests: `tests/test_ch6_contract.py` (9+1; non-vacuity proven by flipping `len(revs) > 1`). Removed as superseded by
  R5: `test_ch6_claims.py::test_mg1_text_equals_the_board_rule`, five `test_walk1_3b_target_progress.py` board tests
  (list in packet). `test_out_d5_objectives_postgres.py` spy now `spy(dispatch, **kw)` (unserved from `served`).
- Frontend: `outcomeBoardClient.ts` NodeClaim/RowNodes + row fields; `OutcomeBoard.tsx` `GrowParts` (ob-grow/ob-part),
  target_note under subline; css in `outcomes.css`. Committed. `tsc` + `vitest run src/sites src/estate src/blocks`
  were started and NOT confirmed (output unread): rerun in background, filter to failures.

## Next
1. Frontend: confirm tsc + vitest clean; fix any board/fixture test (add `nodes` to `test/outcomeBoardFixture.ts` if
   needed); add a vitest for GrowParts ("Not known yet" + days line, potential split on "\n"). `chainClient.ts` parse of
   `nodes` not checked (grep showed no `nodes`/`days_line` there).
2. L2m `tests/test_ch6_nodes_postgres.py` (+ run scoped existing list §A8 item 4): real-DB mini/cold/EV node values,
   price lines; prove non-vacuous. Not started.
3. `git merge main`; polish clone (create, migrate, settle, W6, fresh, store on, collect, COH 0 new, L3 table of
   board-value changes, drop); L3m if template stale (states only, `--budget 540`, parts). Check lane 2 not cloning.
4. Graph check, ratchet, guards one at a time (unused imports in mini.py: `calendar`, `judge_month`, `productive_energy`,
   MG1_* may now be unused; ruff/guard may flag). Known Deviation to record: MG-2 fuel line omitted when the stored
   consequence has no price; Mini lead-Finding mapping uses the board's lead money head for GENERATOR_SUPPORT_CANDIDATE
   regardless of its mechanism.
5. Packet `.agent/review-packet-CH-6a3.md` incl. mock->new table and golden-diff list.
