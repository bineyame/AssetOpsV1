# CH-6a3 R2a handoff (PARTIAL, stopped at the context limit)

Branch `task/CH-6a3-composers`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch6a3`. Main merged (`f3e76f5bb`, clean).
R2a code commit: `1fb51daff`. Binding: review `AssetOpsV1-plan2/.agent/review-CH-6a2-6a3.md`, ruling CH6a3-R2 at the end of
`AssetOpsV1-plan2/.agent/build-sheet-CH-6.md`.

## Landed (commit 1fb51daff)
- **H3 ONE-SOURCE.** `chain/outcomes.py` `earnings_parts(claim, day)`: known -> money, basis kWh, single-revision price,
  stored `measured_seconds`; NOT_KNOWN -> `"Not known yet · {days_line}"`. Mini `_sales_from_claim` (`mini.py` after
  `_measured_sales`) and EV `_charging_from_claim` (`ev.py` before `_charging`) apply it whenever the live read found use;
  NOT_KNOWN drops money and subline. Live read kept only for conflict / no users / no readings / not loaded, and the
  EV session counts (known case). `energy_basis` now adds `measured_seconds` when every counted row carries it.
- **M5.** `energy_basis` prints `price` only when `price["revision_id"]` (lower-cased) is the counted rows' one revision;
  mini passes the price selection's `revision_id`, EV the overview `tariff_revision_id`. `fuel_basis` litres via
  `_litres` (1 place, half up, as `analytics/dispatch.py` `_dec(..,1)`).
- **M4.** `SiteFacts.one_day` (board.py), set in `read.py` `board` (threads branch, where `day` is set) when the window
  is exactly one Site-local day; `row_nodes` passes `day` only then. EV `earnings_parts` gets the day only for a one-day window.
- **L4.** outcomes.py blank-line block removed; board.py long line split.
- **H1.** `test_walk1_productive_sales.py`: `snapshot()` builds the stored row from the same readings (producer rules);
  `run()` injects rows into `chain_day`; MG-1 asserts via `assert_mg1` -> `nodes["MG-1"]["kpi"]` + `judge_month` over the
  rows. 25.25 / 42.08 USD still come out. New LOW-day case. No test deleted. Failed-price-port case now asserts the
  ruled behaviour (money 24.00 from the stored priced row, no subline).
- **M2/M3.** New `tests/test_ch6_r2a_rows.py` (R7 Cold lab 24 Oct note, row_nodes selection, no-target days line,
  M4 one-day, `_lead_findings` negative). `test_out_b3_cold_ev.py`: `ev_snapshot()` fake rows, EV LOW-day ONE-SOURCE,
  `ev_priced` flag test. `test_walk1_productive_sales.py::test_mg1_snapshot_verdict_sets_the_row_state_and_chip`
  (MET->ON_TRACK "Met", BEHIND_PACE->WATCH "Behind pace", no objective->OPPORTUNITY + potential node). Evaluator/contract
  tests for M5 (kWh x price == amount; other/no revision -> no line; litres rounding).
- EV golden `ch5a1_board_contract/ev_2026-10-27.json` regenerated: LOW fake rows now give "Not known yet · 0 of 1 days
  checked · 1 with too little data, not counted" and subline null (the review's H3 example, now consistent).

## Checks run
- Scoped pure set (25 files: ch6 x5, ch5a1 contract, ch5a2*, ch5b*, out_b1/b2/b3/c2/c4/d4, walk1_3b, walk1_4*,
  walk1_productive_sales, out_a1, b4 imports, polish_pa1) via `tools\run-host-tests.ps1`: 522 passed, 2 failed before the
  golden regen + read.py fix; after: the 2 re-run green (26 passed). Re-run the whole scoped set once at the end.
- Non-vacuity: 10 mutations (script `%TEMP%\r2a\mut.py`), each new test failed under its mutation, tree clean after.

## M1 / H2 clone evidence (clone `r2a`, created+migrated+settled, then dropped)
- Polish source is at Alembic `0041`; `site_day_snapshot` arrives in `0043`, so the clone starts with **0 rows**.
- After `chain_clone settle` (S2 + one tick + performance, 115 s): **11 rows, all `critical_served`**; no
  `productive_kwh`, no `charging_kwh`. The tick's `chain_snapshots` stage only consumes outbox events; the polish
  readings predate the outbox, so nothing enqueues those days. **Rows were never produced (not unread).**
- Producer that does make them: `python -m assetops_backend.chain.backfill --site <code> --steps a` (CH-1a
  `build_range`, first evidence day to today). On the clone: KOBO-001 `productive_kwh` 35 rows = 8 PARTIAL
  (2026-10-03..11-01) + 27 NO_DATA (22 s); EV-LAB-001 `charging_kwh` 18 rows = 2 LOW (10-20, 10-27) + 15 NOT_EXPECTED +
  1 NO_DATA (3 s). So with step (a): Kobo story days are PARTIAL -> counted (earnings known if the rows are priced),
  MG-1 checked_days 0 -> NOT_JUDGED; EV story days are LOW -> earnings NOT_KNOWN legitimately (coverage), not a defect.
- Fix size: adding step (a) to `tools/chain_clone.py settle` is ~10 lines (<=0.25) but changes the shared L3 procedure
  (lane 2 uses it) and every L3 baseline. NOT done. Decide: do it in R2a-resume, or route to the Architect.

## Next (resume here)
1. Decide the settle step (a) question above; if done, add it after the tick in `chain_clone.py` `settle`.
2. **H2 §A8 item 3 on `mechanism_db()`** (`backend/tests/mechanism_dataset.py`; see `test_md0_mechanism_postgres.py`,
   `test_ch5a1_mechanism_postgres.py` for the fixture pattern). New `test_ch6_mechanism_postgres.py`: Kobo D13 MG-1
   checked_days == COMPLETE days and verdict == `judge_month` over stored rows; Kobo earnings D7-D13 6 of 7, amount ==
   Σ stored money; each "Why?" price line kWh x price == amount (`chain/why.py` `price_lines`); D13 potential SUPPORTED with
   value + money lines; MG-2 D11 MISSED / D12 MET; Cold D3 CC-1, CC-6 not MET; EV D9 earnings 1 of 1, EV-1 MISSED; rows read
   once; ONE-SOURCE assert on one Kobo day and one EV day (money/subline/sales line all from the claim). NOT_KNOWN on a
   COMPLETE day = defect.
3. Run L2m files (`test_ch6_nodes_postgres.py`, `test_out_d5_objectives_postgres.py`, the new file) via run-host-tests
   (DB 127.0.0.1), one heavy job at a time.
4. Polish clone (bodies changed): create --migrate, settle, W6, `fresh` store on, collect, COH 0 new (packet L3 commands).
5. Guards A, W, V (`ASSETOPS_GUARD_PYTHON` set). L2 (vitest copy) belongs to R2b with the H4 markup (ruling: "closed under H4").
6. Add "Fix round R2a" to `.agent/review-packet-CH-6a3.md` (this file has the evidence), commit.

## Open risks
- EV known case keeps the overview session counts beside the snapshot kWh (sessions are not money; noted).
- Mini unpriced day: the sales line now reads "Not known yet · 1 of 1 days checked" (ONE-SOURCE literal); the
  "no price per kWh declared" reason stays on the Price per kWh line.
- Mini known claim with no single-revision price (several prices or a price-port failure): money shown, subline None.
