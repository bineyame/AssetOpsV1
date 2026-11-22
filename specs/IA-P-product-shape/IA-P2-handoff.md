# IA-P2 handoff (PARTIAL: P3a and P4a built; P3b not started)

Branch `task/IA-P2-portfolio-figures`, worktree `/opt/assetecon/AssetOpsV1-iap2b` (the brief's
`/opt/assetecon/AssetOpsV1-iap2` already held another clean worktree, `task/IA-P-spec-rev2`; left untouched).
Head after this file: see `git log -3`. No DB used, no process left running, no preview server.

## Done
- **P3a** (`c558fd4e2`): `deep_dive/period.py` (`Period`, `MonthServed`, `month_days`, `closed`, `resolve`, `header`,
  `Sums`, `period_view`, `driver`, `contribution`, `span`, `refused_text`, `RangeRefused`), `deep_dive/read.py`
  (`period`, `_period_reads`, `_suggest`, `BadRange = P.RangeRefused`), `deep_dive_api.py` (shared `answer()` refusal
  order; `GET /api/portfolio/period`), `deep_dive/tables.py` (code constants: modes, routes, `DAY_PATTERN`, ...),
  statements `i18n/statements/en/portfolio_period.py` and `portfolio_sites.py`, cases
  `backend/tests/statement_cases/portfolio_period.py|portfolio_sites.py`, T8 key list in `test_sc1_statements.py`,
  `period.py` and `sites.py` added to `ADOPTED` in `tools/checks/statement_catalogue.py`.
  Tests `backend/tests/test_iap_portfolio_period.py` (P.7 tests 1 to 12 plus every statement case rendered).
  Fixtures `frontend/src/estate/__tests__/fixtures/iap/period-{period-2026-09-10,month-2026-10,none-2026-11}.json`
  (test 10; rewrite with `IAP_WRITE_FIXTURES=1`).
- **P4a** (`dc03a546c`): E0 `waiting_count` / `waiting_by_site` in `estate/portfolio.py` (summary, after
  `category_counts`; `MONITOR` and matched Actions not waiting); E1 `deep_dive/sites.py` (`SiteRef`, `sites_view`,
  sum check `AssertionError("SITES_SUM")`, logged 503 in the route), `DeepDiveRead.sites`, `GET /api/portfolio/sites`.
  Tests `test_iap_waiting_counts.py` (4), `test_iap_portfolio_sites.py` (P.8 tests 1 to 9 with 4b).
  Fixtures `sites-2026-10.json`, `sites-2026-09-10.json`, `sites-none-2026-11.json`; `portfolio.json` gains
  `waiting_count` 6 and `waiting_by_site` {KOBO-001: 3, COLD-001: 2, EV-001: 1} (indent 1 kept).
- Each new test file was run failing first (collection error: module absent), then green.
- Run at `dc03a546c`: `test_iap_portfolio_period.py`, `test_iap_portfolio_sites.py`, `test_iap_waiting_counts.py`,
  `test_sc1_statements.py`: 472 passed; with `test_5c_deep_dive_api.py` and `test_5c_deep_dive_view.py`: green
  (673 at P3a). `statement_catalogue.py`: only `HAND_BUILT_NEW decisions/adapters/structure_read.py:24`, which is
  pre-existing (seen with this slice's ADOPTED edit stashed). `git diff main -- backend/assetops_backend/deep_dive/view.py`
  is empty.

## Plants (one-line edits, each reverted; output in the packet to be written)
- `dayscut` (`resolve` counts a PARTIAL month: `if closed(...)`): test 1 fails (1 failed).
- `onefig` (row gap re-formatted from `R.effect.quantize(Decimal("1E1"))`): tests 2 and 3 fail. Note: a whole-dollar
  quantize is invisible on World P (all whole dollars); the tens rounding is the one shown.
- `handbuilt` (an f-string in `period.py`): `HAND_BUILT period.py:126`. E1's (f-string in `sites.py`):
  `HAND_BUILT sites.py:36`.
- `sum` (sum check returns): test 4 fails. `order` (reverse sort): tests 1, 7, 9 fail.

## Defaults and deviations to carry into the packet
1. Worktree path (above).
2. P.7 test 2 lists tiles[0] lines as only the target line; P.5 and R2 (D-IAP.25, later) keep 5c's `W.sites` line, so
   the test asserts `["Target $4,590.00 · 63% of target", "3 of 3 Sites"]`.
3. World P's recipe (`replace(served, snapshot=replace(snapshot, month=...))`) trips 5b's compose check, so
   `copy_to` also moves each Site snapshot's `month`, `inputs.month` and `targets.structure.month` (test support only).
4. P.8 test 8 "targets emptied": an empty values mapping breaks 5b's bridge (KeyError), so every target value is
   withdrawn (`value=None`); September `R.k` is then 2 (asserted).
5. `header(..., *, now)`: P.2's signature has no clock, but 5c's `_nav` rule needs one; added keyword-only.
6. Two statements not named in P.6 carry P.5/P.8's f-string forms without new English: `portfolio_sites.driver`
   ("{factor} {effect}") and `portfolio_period.assure_entry` ("{month}: {standing}"); plus `portfolio_period.month`
   (the year rule), `portfolio_period.text` and `portfolio_sites.text` (column words). BAD_RANGE's "two" and "the
   first not after the last" are example slots (SC-1 bans number words in literals).
7. A missing month row's `sites` is null, like its four figure keys.
8. E1 mode `none`: `without_target` is `{"count": 0, "text": null}` (no figure exists to be left out of).
9. E1 Site money is shown only in the months' own currency (`Sums.cur`); otherwise "Not available yet" (needed for
   test 4b: World X's Kobo would else read "−KES 562.00"). Compared rows with no effect sort after those with one.
10. E1 fixtures are built over the IA-P fixture estate's five Sites (World A's three plus `COLD-001` and `EV-001`
    from `portfolio.json`), so E0's keys are E1's codes (R8) and the frontend sees MD-IAP-12 rows.
11. Order P3a, P4a, then P3b (both backend units together; P3b reads E1 only from P4b on).

## Next (P3b, spec section 6 "P3b"; then the slice end)
- Build P3b exactly as its card: `portfolioWords.ts`, `PortfolioTabs.tsx`, new `portfolioPeriodClient.ts`,
  `PortfolioOverview.tsx`, `PortfolioPeriod.tsx`, `DeepDiveMonth.tsx` props (`month`, `nav`, `notes`; I1 deletes
  `MONTHS`, `monthWords`, `monthAfter`), `sharedRange.ts` (`entryRange(pathname?, now)` per I3, `monthDays`, `/results`
  in RANGE_PAGES and FILLED_PAGES), `EstatePortfolio.tsx`, new `Results.tsx` (I14), `EstateEvidence.tsx`, `App.tsx`
  aliases (§2.4 P3b rows), `tools/deep_dive_gates.cjs` (URL argument, period and IA-P portfolio fixtures),
  `tools/iap_gates.cjs` gates H1 to H6, the DDR runbook S7 line. Tests first: `portfolioHub.test.tsx` (the card's nine
  cases plus I3's `/` lands on last month), `DeepDiveMonth.test.tsx` updates (name them), `Results.test.tsx`, the
  `estateEvidence` scope section, and R2's vitest matrix (Overview names Thika on one- and two-month fixtures; the
  Outcomes/Sites part lands with P4b). Plants `fourtab`, `window`, `twofig`, `browsermonth`, `span`. Register
  MD-IAP-3, MD-IAP-7 (P3b part), MD-IAP-10, MD-IAP-11, MD-IAP-12 (P4a) in `.agent/mock-departure-register.md` from
  R784. Shots per the card to `/opt/assetecon/evidence/IA-P/IA-P2/` on `vite preview --port 5573`.
- Slice end: `IA_LANDED` gains `IA-P2`; test scope (every backend file importing a touched module, notably the
  `estate/portfolio.py` users `test_w303_portfolio_api.py`, `test_cov_partial_portfolio.py`,
  `test_cc_placement_postgres.py` via `--db`; whole `src/estate`, `src/shell`, `src/ui`) at head and on main; tsc;
  fast check-all; IA-P gates after a fresh build; packet `packet-IA-P2.md`, state entry (next number in
  `.ai/state/index-3.md`), spec status. The spec says IA-P2's merge stales the world ladder's L2 `code` part: the
  coordinator rebuilds the current rung once after the merge (spec section 8), to be stated in the packet.

## Risks
- `estate/portfolio.py` summary grew two keys: stored `chain_response` bodies grow (spec section 8, D-WK.16).
- Not yet run: the Postgres tests over `estate/portfolio.py`, and check-all.
