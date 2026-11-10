# DATA-1 review packet: one Kisiwa recording session (D-E5.30)

Branch `task/DATA-1-kisiwa-one-session` from `main` ec6ee2643. Card: `.agent/architect-answer-non-kobo-sites-2026-11-10.md`
"DATA-1", ruling D-E5.30 in `.agent/build-sheet-OWN-GAPS-2026-11-08.md`. Tools only; no product code changed.

## Outcome
- `tools/demo_combined_kisiwa.py`: `KISIWA_EPOCH = "kisiwa-gw-1"`, `kisiwa_gateway(work)` = `work / "kisiwa-gateway"`,
  `publish_night(rp, tmp, work, run, received_at)` calls `_publish_and_accept(..., KISIWA_EPOCH, ...,
  gateway_dir=kisiwa_gateway(work))` (DD1a1-R5, the Kobo pattern). Both call sites use it: `build` (was `f"epoch-{item}"`)
  and `_publish_night` for add-day (was `f"epoch-add-{ymd}"`). Each night still keeps its own `tmp` folder
  (`kisiwa-replay/rNN`, `kisiwa-replay/add-YYYYMMDD`), so the PARTIAL_NIGHT and resume logic are unchanged.
- The gateway's `provision` is a no-op on an identical identity (`gateway/assetops_gateway/service.py:331-355`), so
  the sequence continues across nights and across processes.
- New finish row `KISIWA-COHORT` (`tools/demo_combined_finish.py`, placed after KIS-OV; its logic is in
  `demo_combined_rows.kisiwa_cohort`). It reads the latest `dispatch` selection per window and requires
  `SELECTED_UNIQUE` on every window whose day has `accepted_evidence`. It fails when no window has readings, and on a
  dataset without Kisiwa (`KisiwaMissing`). Its id does not start with `KIS-`, so `demo_combined_kisiwa.py check`
  does not run it; the prepare's finish `check` does.
- Night figures and `run_guards` are unchanged.

## Files
- `tools/demo_combined_kisiwa.py`, `tools/demo_combined_finish.py`, `tools/demo_combined_rows.py`.
- Tests: `backend/tests/test_own_g1_add_dates.py` (+3), `backend/tests/test_k1_kisiwa_fixtures.py` (+1),
  `backend/tests/test_demo_combined_finish_rows.py` (+3), and `backend/tests/test_k7_kisiwa_story.py`.
  In `test_k7_kisiwa_story.py`, the KisiwaMissing count guard goes from 13 to 14 for the new row; it is extended,
  not loosened.

## Acceptance (card)
| Item | Status |
|---|---|
| `:789` one epoch, persistent `work/kisiwa-gateway` | done (`build`, via `publish_night`) |
| `:1189` add-dates, same epoch and dir | done (`_publish_night`) |
| Docstrings cite D-E5.30 | done |
| KISIWA-COHORT finish check, pass and fail rows | done |
| Unit test: one epoch and one gateway dir every night | done (test_k1) |
| Night figures and fuel-balance guards unchanged | not touched; the K3/K4a/K7 files pass |

The coordinator's extra tests (all in `test_own_g1_add_dates.py`) drive the real `add_night` and `_publish_night`
with the DB, simulator and gateway faked:
- one session across 3 added nights;
- the Site-local day 8 Nov, which spans nights 7 and 8 Nov, gives `select_cohort` → `SELECTED_UNIQUE`;
- a night interrupted after publish resumes without republishing, and the next night stays on the same session.

## Fail on main
With main's three `tools/` files checked out and these tests run, all 7 new tests fail: 3 in add-dates, 1 in k1, and
3 in the finish rows. Examples: `assert 3 == 1` (epochs), `'AMBIGUOUS' == 'SELECTED_UNIQUE'`,
`'epoch-add-20261107' == 'epoch-add-20261108'`. The files were then restored from HEAD.

## Checks (Postgres `assetops_test` on 127.0.0.1:55432, run-owned DBs, one file at a time)
| File | Result |
|---|---|
| test_demo_combined_finish_rows | 72 passed |
| test_demo_combined_mill | 15 passed |
| test_k0_operational_actions | 35 passed |
| test_k10_declared_none_adapter_postgres | 11 passed |
| test_k10_declared_none_board | 10 passed |
| test_k10_declared_none_rule | 26 passed |
| test_k1_kisiwa_fixtures | 19 passed |
| test_k1_kisiwa_site_postgres | 3 passed |
| test_k2_fuel_records | 15 passed |
| test_k2_fuel_records_postgres | 8 passed |
| test_k3_fuel_balance_postgres | 10 passed (see note) |
| test_k3_fuel_balance_rules | 18 passed |
| test_k4a_fuel_finding_postgres | 14 passed |
| test_k4a_fuel_finding_rules | 25 passed |
| test_k4b_protect_fuel | 31 passed |
| test_k5_fuel_night_api_postgres | 6 passed |
| test_k5_fuel_night_text | 24 passed |
| test_k6a_fuel_action_origin | 9 passed |
| test_k6a_fuel_action_origin_postgres | 7 passed |
| test_k6b_fuel_verification_postgres | 6 passed |
| test_k6b_fuel_verification_rules | 38 passed |
| test_k6c_assure_fuel_count | 8 passed |
| test_k7_kisiwa_story | 101 passed (after the count fix) |
| test_k7f_kis10_window | 3 passed |
| test_k8_estate_fuel | 21 passed |
| test_k8_estate_fuel_postgres | 1 passed |
| test_k9_finish_callsites | 4 passed |
| test_own_g1_add_dates | 48 passed |
| test_own_g2_fuel_night_due / stage / tick | 14 / 7 / 7 passed |
| test_own_g2_fuel_night_tick_postgres | 6 passed |
| test_own_g3_operational_entry / _postgres | 55 / 8 passed |
| host: test_k0_kisiwa_actions | 32 passed |
| host: test_k1_registered_kisiwa | 1 passed |
| host: test_k3_fuel_balance_parity | 6 passed |
| host: test_k4a_kisiwa_night4 | 4 passed |
| host: test_own_g3_entry_env | 7 passed |
| host: test_probe_kisiwa_fuel_band / metric | 7 / 3 passed |

Note on `test_k3_fuel_balance_postgres`: the first run had 2 failures, both
`ImportError: TWIN_TANK_TEMPLATE from 'fixtures'`, caused by path order (`backend/tests/fixtures` shadows
`host/tests/fixtures.py`). With `host\tests` first on PYTHONPATH it passes 10/10. This comes from the environment,
not this change. Not run: the full suites, `check-architecture`, and a prepare.

## Known deviations and residual risk
- No prepare or scratch build was run, so "days analysed" has not been seen in a database. KISIWA-COHORT is the
  build-time proof. A Kisiwa-only scratch build is not possible on its own: Kisiwa is a child of
  `demo_combined.py prepare`, budgeted at up to 3600 s (`EXPECTED_SECONDS["kisiwa"]`), plus the tree and finish steps.
  The card's estimate is +0–3 min over today's prepare.
- An add-dates run on a work folder built before DATA-1 would create a fresh `kisiwa-gateway` on `kisiwa-gw-1`.
  Its epoch differs from the old `epoch-N` series, so the IDs would not collide, but the days that join old and new
  nights would stay AMBIGUOUS. A fresh prepare avoids this.
- D-E5.30: Kisiwa may gain dispatch Findings it never had before. The coordinator should read the Kisiwa board for
  2–8 Nov in the fresh build before the demo.

## Fix round 1 (review REJECT: H1, M1, L1, L2), commit 2bcfb3b31

- H1: `publish_night(..., previous_end)` passes `keep=after_previous_night(previous_end)` (instants strictly after
  the previous night's end), Kobo's `keep` seam (`demo_combined_kisiwa.py` `after_previous_night`,
  `story_previous_end`). `build` passes run k-1's end (None for run 1), `_publish_night` passes
  `night_end(night - 1 day)`. The previous night keeps the boundary reading. KISIWA-COHORT now also reads
  `r.cohort -> 'limits'` and fails on any `REPORTS_OVERLAP` (`demo_rows.kisiwa_cohort`). The SQL was run read-only
  on `assetops_polish_client4_test`: 11 windows, `limits` = [] each (that build is pre-DATA-1: 9 AMBIGUOUS).
- Behavioural tests, each failing with the fix disabled (seen, then `git checkout`): the real `add_night` keeps,
  applied to 5-minute readings of two nights, give the boundary once and no overlap limit, with a control showing
  REPORTS_OVERLAP without them (`test_own_g1_add_dates`); the story nights' keeps send every instant once, none
  lost (`test_k1`, source inspection removed); a real `select_cohort` payload with the boundary twice fails the
  row (`test_demo_combined_finish_rows`).
- L1: the PARTIAL_NIGHT message says what to do (do not delete the gateway state or night folder; fresh prepare or
  Architect). L2 not done: checking every day with readings needs every window assessed when the row runs, and
  the drain does not count Kisiwa dispatch jobs; a false failure would abort the 2h45m build. Left open.

M1 (read-only on client4, scripts in the session scratchpad `data1fix/`): the real cohort, `dispatch_v3.assess`
and `finding_episode.plan_pass` over the stored evidence with the epochs merged and boundaries keep-filtered.
Check: the harness gives the stored 10-30 basis exactly (intervals, 433 reports) and gives the 2 stored Findings.
With DATA-1: all 11 windows SELECTED_UNIQUE, no limits; 20 SUPPORTED Findings (2 per night, 30 Oct to 8 Nov, each
17:40-19:05Z and 22:55-00:15Z); generator energy per episode is the same every night (646 / 432).
- KIS-2 holds: diesel v1 PRICED (one revision) for every day; current Foundation since 28 Oct 09:57 has no-load 4.9
  GENERIC_DEFAULT; 20 items are within `consequence_items_per_site` 50.
- KIS-4 holds: fuel Findings unchanged; dispatch amounts are the stored two values (26.2774, 17.5725); no
  k*A + m*B (k, m <= 10) equals a forbidden sum.
- KIS-6 holds: derived from data; Assure is unaffected.
- KIS-7: d1 is unchanged (30 Oct). New: Kisiwa is now priced on S (8 Nov local holds two heads), so items 1 and 4
  take the two-Site path for the first time on real data. The product `_optimize_card` matches what the row expects
  (code read). Residual risk: a coincidental "41.40/41.41" string (Kobo 15.125 + Kisiwa 26.2774) in a body.
  CH5D1-O1 also allows Kisiwa.

USER_REVIEW_REQUIRED: no (tools only; a fresh Claude review is required by the card).
