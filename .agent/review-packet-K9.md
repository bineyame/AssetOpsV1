# Review packet K9 — Kisiwa checks, then rehearsal

Branch `task/DIESEL-K9-checks-rehearsal` (worktree `AssetOpsV1-k9`). Binding rulings: DIESEL-1-R3q (§9q, main d257bdc68,
merged as 1b1b05e0c), §8.7 rows. Rehearsal DB `assetops_demo3_k9rehearsal_test`, work folder `var/demo3_k9rehearsal`
(replaces the build sheet's name). USER_REVIEW_REQUIRED: no (the rehearsal waits for K8's merge and coordinator clearance).

## Pre-rehearsal (R3q Q1-Q5)

### Commits
| Commit | What |
|---|---|
| 2f084897a, 853fc207d, 319236613, 399e7127d, f03573d93, fec760855 | earlier K9 builder (wording guard, COH-10 thread, KIS-8, KIS-8a carry, K6b L4 / K7-F L1, K7-F L2) |
| 1b1b05e0c | merge main (ruling R3q) |
| f004bea98 | Q1 Kisiwa boards; Q5 COH-17 V2/V4 Kisiwa self-tests |
| 70639ecac | Q2-Q4 KIS-1, KIS-2, KIS-6, KIS-7 rows + L0 bodies; carry raise count 7 -> 11 |

### Rows and evidence
- **Q1 (`tools/checks/chain_coherence.py`)**: `SITE_CODE` and `LOCAL_DAY_TZ` gain `kisiwa` (`KISIWA-001`,
  `Africa/Dar_es_Salaam`); `KISIWA_BOARD_DAYS = ((-5, "fuel-morning"), (0, "S"))`; `kisiwa_day_windows(story)` gated on
  `"kisiwa" in story["sites"]` and `story["kisiwa"]`, rows `date=`, Site-local `[D-1 21:00Z, D 21:00Z)`, estate the
  enclosing UTC midnights; `day_windows` skips `kisiwa` explicitly (otherwise byte-equal; the old Kobo/Cold/EV tests
  pass unchanged); `collect` uses `day_windows(days) + kisiwa_day_windows(story)`. L0 tests 1-4 of §9q.1 in
  `tools/checks/test_chain_coherence.py` (story_links' KISIWA-001 `date=` values, S-5d = night 4 + 1 day via the real
  `demo_combined_kisiwa.resolve`, no-Kisiwa gate and `day_windows` skip, zone equals `demo_combined_kisiwa.ZONE`).
- **Exception E1 (recorded)**: COH-3 Kisiwa pairs: 0 (R3q E1). The fuel Action is a FUEL_BALANCE domain Action,
  absent from `/api/estate/actions`, and Kisiwa is not in `DOMAIN_SITES`; not extended. After-the-demo list: "COH-3 for
  mini-Site domain Actions (Kisiwa fuel)".
- **Expected merge conflict with K8**: K8 adds `SUMMARY_SITE_TZ` beside `LOCAL_DAY_TZ` (line ~39) and edits the
  `_coh7a_window` lookup. Whoever merges second keeps the union: K9's `kisiwa` entries in `SITE_CODE`/`LOCAL_DAY_TZ` plus
  K8's `SUMMARY_SITE_TZ` line and lookup unchanged. `KIS-6`'s objectives check assumes K8's CO-6 four-Site objectives list.
- **Q2 KIS-6 (`demo_rows.kis6`)**: week `[S-6d, S+1d)`: summary, `/api/estate/chain` and Portfolio objectives Site codes
  each the four codes; Kisiwa's summary `{category: state}` equals `/api/sites/KISIWA-001/outcome-board?date=S`;
  `window_basis == "DAY"`, `window.from` = Dar es Salaam midnight of S; `want = 1 if kisiwa.json verdict == VERIFIED
  else 0` (read, never forced) equals the chain Kisiwa `threads.verified`; Assure card claim value equals chain
  `count.verified_results`; no Kisiwa Assure value line (H2).
- **Q2 KIS-7 (`demo_rows.kis7`)**: S summary priced codes (read from each cost claim) exactly `[KOBO-001, KISIWA-001]`;
  card `claim is None`, value `card_text("cost.sites", sites=sites_text(2))`; `never_summed(amount_high of each claim,
  [S summary, week summary, Portfolio week]) > 0` with no hit. Kisiwa unpriced on S fails (a stop).
- **Q3 KIS-1 (`demo_rows.kis1`)**: `PostgresFoundationStore.revisions`, current rows only. Stop setting
  `{(90, "%")}` across every current revision; no-load `4.9 L/h GENERIC_DEFAULT` equal to `demo_combined_kisiwa.NO_LOAD`
  in every revision from `no_load_effective_from`; sensor accuracy `10 L GENERIC_DEFAULT` equal to `ROLES4` from
  `roles4_effective_from`; `price_selection` per stored night window (latest revision per night): all PRICED, one
  revision id, value/currency = fixture step v1 (`1.25 USD`, read from the file). Content path confirmed
  `components[].properties[]` on the in-memory store from `register_in` (the L0 test uses those real revisions).
- **Q4 KIS-2 (`demo_rows.kis2`)**: dispatch Findings selected with `finding_episode.DOMAIN` and `dispatch.ANALYTIC_ID`
  (the R3k filter's constants, bound); latest revision SUPPORTED; head consequence (latest `recorded_at`,
  `revision_no`) cites it, `fuel-cost-2` PRICED, multiplier `fuel_cost_v2.MULTIPLIER`, no-load 4.9 GENERIC_DEFAULT;
  `exact = M x (loaded + idle)` over `financial_consequence_power_interval` with `Fraction`, equal to
  `quantity_high_exact`; `quantity_high == fuel_cost.to_decimal_ceiling(exact)`; `idle_seconds` equals the idle
  intervals. Per-Finding `idle_seconds` is reported, not asserted to 0.
- **Q5**: COH-17 V2/V4 Kisiwa self-tests on a four-Site bundle (clean_full + EV and Kisiwa, built in the test).
  Rehearsal evidence still owed: `board_summary.S.KISIWA-001` at status 200.
- Finish wiring: `KIS-8a, KIS-1, KIS-2, KIS-6, KIS-7`, then the existing rows; KIS-8 (wording) runs later and so reads
  their bodies. Each new row raises `KisiwaMissing` without Kisiwa (carry test count now 11).

### Non-vacuity (commit, mutate, run, `git checkout --`)
| Mutation | Failing test(s) |
|---|---|
| `KISIWA_BOARD_DAYS` -5 -> -6 | `test_kisiwa_day_windows_are_the_boards_story_links_opens`, `test_kisiwa_s5_board_is_the_morning_after_the_incident_night` |
| drop the `day_windows` kisiwa skip | `test_without_kisiwa_nothing_more_is_collected_and_day_windows_skips_it` |
| V4 check `True or ...` | `test_kisiwa_v4_fails_when_a_board_node_differs` |
| V2 check `True or ...` | `test_kisiwa_v2_fails_when_the_board_headline_differs` |
| Kisiwa zone -> Addis | `test_kisiwa_local_day_zone_is_the_story_zone` |
| KIS-1 price `len(revs) >= 1` | `test_kis1_...` (two price revisions) |
| KIS-1 stop `in` instead of `==` | `test_kis1_...` ("stop 60 in one revision") |
| KIS-2 idle term `Fraction(0)` | `test_kis2_...` (pass body fails) |
| KIS-2 ceiling `True or ...` | `test_kis2_...` ("half-up quantity_high") |
| KIS-6 `want = 1` | `test_kis6_...` (INEFFECTIVE pass case) |
| KIS-7 `never_summed(amounts, [])` | `test_kis7_...` ("a summed string") |
| `@row("KIS-6x")` | `test_kis_rows_are_wired_after_kis8a_in_order` |
`git status` clean after each restore.

### Checks
- `tools/checks/test_chain_coherence.py`: 172 passed. `backend/tests/test_demo_combined_finish_rows.py` +
  `test_k7_kisiwa_story.py`: 143 passed.
- `npm ci` in `frontend`, then `tools/check-all.ps1 -Python ...plan2\.venv\Scripts\python.exe` on 70639ecac: exit 0,
  "All 18 guards passed", wall 1502 s. The estate guard self-tests alone took 1148 s (15 passed), probably because of
  memory pressure: free RAM was 2.67 GB at the start, with K8 running in parallel.

### Deviations and notes
- Q5 four-Site bundle is built in the test from `clean_full` (adds EV and Kisiwa entries plus manifest requests) rather
  than a committed fixture directory; same coverage, no 40-file copy.
- KIS-6 "Portfolio Assure card" read as the week outcome-summary `cards.ASSURE_PERFORMANCE.claim.value` (the card the
  Portfolio page draws); the portfolio body itself carries `summary.claims`, not cards.
- KIS-1 prices: the latest stored revision per night (`DISTINCT ON (night_date)`), the 10 nights.
- No DB or rehearsal step was run (pre-rehearsal only).
