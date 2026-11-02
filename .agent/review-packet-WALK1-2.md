# Review packet: WALK1-2 (Depot declared charging tariff, EV Grow copy, L-A, L-B)

Branch `task/WALK1-2-depot-tariff` from main `2058a6567`. Spec: `AssetOpsV1-plan2/.agent/build-sheet-WALK1.md` §3,
§7 (R674-R676), §9 D-W1-1. Owner context: `owner-walkthrough-notes-2026-11-01.md` WN-7, WN-3.

## Outcome delivered

- Data (§3.1): `backend/conversions/demo-ev-tariff-publications.json` (key `ev_gross_tariff_per_kwh`, v1 INITIAL,
  USD 0.30, AUTHORED_ESTIMATE, idempotency `demo-ev-tariff-v1`). `tools/demo_combined_ev.py` `publish_tariff`
  publishes it once after the Depot's replays have installed the Site, recorded at `install_at + 30 min`
  (`demo_combined_kobo.publish_price` pattern); a repeat call is a replay. Recorded in `<work>/ev.json` `tariff`.
- Backend (§3.2): `ev_site_reads.py` overview `consequence_summary` gains `tariff_value`, a read-time
  serialisation of the selected consequence's own tariff (E3, no new query). `site_outcomes/ev.py`: headline
  "estimated charging income"; priced subline "{kwh} kWh with a complete meter record, at the declared tariff of
  {p} {cur} per kWh · not billed or collected" (unpriced unchanged); new Grow contributor `charging_tariff`
  "Charging tariff": "Declared at {p} {cur} per kWh", chip Declared, href `/sites/{c}/ev/financials`; tariff
  missing: "Not available yet · no charging tariff declared". `{p}` via `mini.price_text`.
- L-A: `SiteFindingHistory.tsx` related line "Related findings: {relation} generator support review", no id text;
  related ids added to the panel's Technical details references; "Times and references" keeps the plain times,
  the rules reference and assessment references moved into a nested `TechnicalDetails`
  (`finding-history-basis-technical-{n}`, `data-technical-details`).
- L-B: `tools/demo_combined.py` `prewarm` prints "ready:" only on 2xx; otherwise "prewarm returned {status}; …".
- Register: R674, R675, R676 added; WALK1-2 strings appended to R655; code comments carry the R-ids.

## Pre-flight findings

- E2 (defect found and fixed): the EV board tested `state == "PRICED"`, but the EV overview serialises the stored
  `ev_money` state, which is `ESTIMATED` for a priced window (never PRICED). The board could never show a priced
  Grow headline, even with a tariff. The composer now prices on `ESTIMATED` (`PRICED_STATE`); the B3 fixture used
  the non-existent PRICED state and is corrected; a test pins that PRICED does not price the board.
- E2 local prepare: see Checks.
- E3: `tariff_value` was already in the selected consequence (`_revision`), so only the summary dict changed.
- `publish_assumption` accepts the EV key (`financials/assumptions.py:30`).

## Acceptance (§3)

| Item | Status |
|---|---|
| 3.1 fixture, producer publication at install+30 min, idempotent | done; `test_walk1_ev_tariff_producer_postgres.py` |
| 3.2 headline, priced subline, unpriced unchanged | done; `test_out_b3_cold_ev.py` |
| 3.2 Charging tariff contributor, Declared chip, href, no-tariff text | done; same |
| 3.2 `{p}` via `price_text` | done (imported from `mini`) |
| 3.2 E3 tariff value in `consequence_summary` | done; `test_w207_ev_site_reads_postgres.py` (value, SUMMARY_KEYS) |
| 3.2 Optimize (P-11) and TARIFF_GAP switch on priced | pinned: B3 priced/unpriced Optimize sentence; w207 `TARIFF_GAP not in served` when priced |
| 3.3 L-A, L-B | done; vitest `siteFindingHistory.test.tsx` (new L-A case), `test_demo_combined_links.py` (non-2xx param) |
| 3.4 tests | as above |
| Captures `ev-board-fault`, `portfolio-week` | deferred to G1 rebuild (Addendum 3 option a) |

## Checks run

Revision `c41c98048` code (packet commit follows). Base DB `assetops_walk1b_test` (routed `_pt<run>_main_test`).

- `toolsun-host-tests.ps1 -- backend/tests/test_walk1_ev_tariff_producer_postgres.py test_out_b3_cold_ev.py
  test_demo_combined_links.py test_w207_ev_site_reads_postgres.py -q -x`: **53 passed**, 0 failed, 731 s.
- Unit, direct pytest: `test_out_b1_board.py test_out_b3_cold_ev.py test_out_b2_vocabulary.py
  test_polish_pa3_ev_tariff_copy.py test_demo_combined_links.py test_demo_combined_finish_co1.py`: 71 passed;
  `test_out_c4_mini_ev.py` with B2/B3: 39 passed.
- Vitest `siteFindingHistory.test.tsx evSiteMoneyRoutes.test.tsx`: 2 files, **69 passed**.
- `tsc --noEmit`: exit 0.
- Guards (the 12 `check-all.ps1` entries, run one by one in the foreground): Architecture seams PASS (197 s),
  estate guard self-tests, navigation truthfulness, agent workflow, dependency registry, delivery fixtures,
  mock-gap fixtures, missing-claim scan + fixtures, evidence width, mock deviation labels and client vocabulary,
  screen ledger: all exit 0.
- Not run: `test_out_c4_ev_warnings_postgres.py` (first background attempt was killed with the stalled session;
  not repeated). **E2 local prepare not run** (`demo_combined.py prepare --sites ev` needs a full private tree build;
  machine memory-constrained with lane 1 building). The fault-window ESTIMATED state after publication is
  therefore unverified on demo data; it is covered by the w207 read test (ESTIMATED with a published tariff) and
  must be confirmed at the G1 rebuild (`ev-board-fault` capture).

## Known deviations

- Tariff contributor, window unpriced for a reason other than TARIFF_MISSING (incomplete meter, withheld): text
  "Not available yet" without a cause, because the consequence names no tariff then and the spec gives no third
  text. Covered under R676.
- Related findings carry no stored title in the history read; the plain name is the Finding type name
  (`FINDING_NAME`, "generator support review": merge, split and recurrence relate Findings of one matcher cohort)
  with the relation label. No new read was added.
- The EV Overview/Financials pages (`EvSiteViews.tsx`) still say "gross tariff estimate"; §3.2 scopes the board
  only. Left unchanged.

## Residual risk

- The tariff is published after all EV story days; earlier consequence rows (if any) recompute through the 0026
  trigger on the next tick. Verified only by the E2 prepare result above.
- `recorded_at` is backdated by the test clock override, as Kobo's price is.

## User-review focus

The Depot Grow row at G1: amount = measured complete-meter kWh × declared 0.30 USD, worded as an estimate at a
declared tariff, never billed or collected. USER_REVIEW: at the G1 owner walkthrough (no separate review needed).
