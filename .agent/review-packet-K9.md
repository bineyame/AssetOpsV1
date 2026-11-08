# Review packet K9 — Kisiwa checks, then rehearsal

Branch `task/DIESEL-K9-checks-rehearsal` (worktree `AssetOpsV1-k9`). Binding rulings: DIESEL-1-R3q (§9q, main d257bdc68,
merged as 1b1b05e0c), §8.7 rows. Rehearsal DB `assetops_demo3_k9rehearsal_test`, work folder `var/demo3_k9rehearsal`
(replaces the build sheet's name). USER_REVIEW_REQUIRED: no (the rehearsal waits for K8's merge and coordinator clearance).

## Path fix (review-K9-r3u)

H1: `pv_values` and `kis4` in `tools/demo_combined_rows.py` now insert `tools/checks` on `sys.path` before importing
`chain_coherence` (as `kis8_protect` does). New L0 test `test_pv_values_and_kis4_import_chain_coherence_without_tools_checks_on_the_path`
runs both in a fresh subprocess with `tools/checks` stripped. L2: `kis_ov` wraps `second_read()` in try/except; an error
is recorded as `second_read_error` inside the R3u-s1 message (test added). `test_demo_combined_finish_rows.py` (56) and
`test_k9_finish_callsites.py` (4) each pass alone with PYTHONPATH excluding `tools` and `tools/checks`.

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

## R3r addendum (DIESEL-1-R3r §9r, main 9db00ce17)

### Delta (commit 39d4d2aa5)
- `tools/demo_combined_kisiwa.py` `register()`: after `register_in`, `store.record_no_legacy_evidence_basis(UUID(tenant_id), UUID(site_id), now=import_at)`
  (Postgres path only; `register_in` and the JSON outputs unchanged, so KIS-1 is byte-stable).
- `tools/demo_combined_rows.py` `kis_ov` (pure body) and `tools/demo_combined_finish.py` `KIS-OV` (wired right after KIS-7): Overview 200 for S-5d and S;
  exactly one `site_cutover_basis` row, `NO_LEGACY_EVIDENCE`, same import row and digest; board `read_state` reported, not asserted;
  `KisiwaMissing` when no Kisiwa Site (carry count in `test_k7_kisiwa_story.py` 11 -> 12).
- L0 tests (`test_demo_combined_finish_rows.py`): wiring, pass body, six fail bodies (409 AWAITING_EVIDENCE_MIGRATION, no basis, two basis, other basis, other import, other digest), and a `register` test that proves the call and its arguments after `register_in`.
- Tests: `test_demo_combined_finish_rows.py` + `test_k7_kisiwa_story.py`, 146 passed.
- Non-vacuity (committed first, then mutated, then `git checkout`): removing the one-row assertion and removing the register call each failed `test_kis_ov_pass_and_each_break_fails` and `test_register_records_the_no_legacy_basis_after_register_in` (2 failed, 1 passed).

### Clone probe (`assetops_k9_audit_r3r`, dropped after)
Free RAM 3.67 GB (>= 2.5); template had 0 open connections; `CREATE DATABASE ... TEMPLATE assetops_demo3_kisiwa_test`, upgraded to head; template touched only as the clone source.
Cutover recorded with the same store call at the stored import instant (2026-10-26T09:00:00Z). Read through K9 code with the K7 work folder (`keys.json`, `story.json`, `kisiwa.json`).

| Read (S = 2026-11-06) | Before | After |
|---|---|---|
| Overview S-5d / S | 409 AWAITING_EVIDENCE_MIGRATION / 409 | 200 / 200 |
| Kisiwa S board `read_state` | PARTIAL | PARTIAL |
| KIS-1, KIS-2, KIS-3, KIS-4, KIS-5, KIS-8a, KIS-9, KIS-10 | pass | pass |
| KIS-6, KIS-7, KIS-8 | fail | fail (same) |
| KIS-OV | fail | pass |

No row passes before and fails after (S-r2 clear); Overview 200 (S-r1 clear). KIS-6/7/8 fail on both sides because a Kisiwa-only clone has no Kobo/four-Site summary (they need the full prepare); not caused by the basis.

### Screenshot
`.agent/k9-r3r-kisiwa-overview-1440.png` (1440 wide, `/sites/KISIWA-001?date=2026-11-06`, served read-only from the clone by uvicorn + vite on ports 18431/18432, both killed by PID).
The Overview renders. Its objective line reads "Objective: serve residential, clinic and productive loads while protecting the battery reserve." (K9's `SiteWindowOverview.tsx:484`), not the R3p "Households, Cold store (ice and fish) and Water pump" wording: that wording is in K8's unmerged branch, so it is not on K9 yet. Not a stop; it should appear after K8 merges into K9.

## Fix round (review `.agent/review-K9-pre.md`: H1, L1-L5)

Commit `afdbc9c81`. Focused tests after the change: finish rows + K7 story + K9 call sites + wording guard + chain coherence, 342 passed.

| Finding | Change |
|---|---|
| H1 | `kis7` asserts `sorted(codes) == sorted([KOBO, KISIWA])` and `codes ==` the priced Sites in the order `summary_s["sites"]` serves. L0 fixture now sorted by lower-case code (the server's `site_code_key` order, Kisiwa before Kobo); the pass test expects `["KISIWA-001", "KOBO-001"]` and fails if the row hard-codes Kobo first. A third priced Site also fails. |
| L1 | KIS-2 fail body `_kis2_body(finding_revision_id="r0")`. |
| L2 | `kis1(..., nights)`: `len(prices) == nights`; `kis_1` passes `len(kisiwa.json["runs"])` (no literal 10). L0: 3 of 10 fails, 0 fails, 3 of 3 passes; a source test pins that `kis_1` reads `kisiwa.json` `["runs"]`. |
| L3 | No current revision is `assert current, ...`, not `KisiwaMissing`; L0 asserts the failure is not a `KisiwaMissing`. The wrapper still raises `KisiwaMissing` with no Site (carry count unchanged). |
| L4 | `fuel_wording.py` also scans `frontend/src/**/*.json` (not `__tests__/`, `__fixtures__/`, `src/test/`) and `frontend/index.html` (HTML comments stripped), and adds `steal`, `steals`, `stealing`, `thief`, `thieves`, `thievery` (`stealth` stays clean). Self-tests: 9 new fail rows, fixtures and comment exclusions in the clean tree. Repo scan: clean, 693 files (was 691). |
| L5 | No change. |

**Coordinator note (H1):** R3q §9q.2's literal `[KOBO, KISIWA]` was a slip about order only; the intent is the set of two priced Sites. The row now matches the set and the served order.

**Mutations** (committed first, mutated, tests failed, then `git checkout`):
- `kis7` back to `codes == ["KOBO-001", KIS_SITE]`: `test_kis7_...` fails.
- KIS-2 head-cites-revision becomes `assert True or ...`: `test_kis2_...` fails (it passed before this round, review M3).
- `kis1` count check reduced to `assert prices`: `test_kis1_...` fails.
- `kis1` no-current-revision restored to `raise KisiwaMissing()`: `test_kis1_...` fails.
- Wording: new words removed from `WORDS`: 7 failed; JSON and `index.html` scans disabled: 4 failed.

### Read-only data check, `assetops_demo3_kisiwa_test` (SELECT only; no work folder, so no served read)
1. **KIS-2: ready.** Kisiwa has 2 dispatch Findings, both latest revision SUPPORTED; each head consequence is `fuel-cost-2` PRICED and cites that latest revision (episodes 2026-10-28 17:40-19:05Z and 2026-10-28 22:55Z-10-29 00:15Z; `amount_high` 26.277 and 17.573 USD). A third Finding is `fuel_balance` (not in KIS-2's filter).
2. **KIS-7: not ready on this clone.** The 10 nights run 2026-10-28 to 2026-11-06, but both priced dispatch consequences lie on night 1 (2026-10-28/29 local). Nothing is priced in Kisiwa's S local day (2026-11-05 21:00Z to 11-06 21:00Z). If the S board prices only consequences in its day, Kisiwa is unpriced on S and KIS-7 fails as a stop. Not confirmed by a served read; needs a live S summary on the four-Site prepare. The clone has only Kisiwa and no cutover basis row (pre-R3r).
3. **Board PARTIAL: cause found by code reading, not by a served read.** The cutover basis does not change it. Kisiwa has no Performance comparison report, so `performance_gate` (`main.py:404`) returns closed. In `site_outcomes/read.py` the mini ports `dispatch` (`:257`, `_open(s.performance_gate)`) and `chain_findings` (`:240`, `_open(s.finding_index_gate)`) then raise `PortUnavailable("... closed: ...")`, which `Reads` records, so `read_state` is PARTIAL. `basis_aware_gate` (`performance_comparison.py:199`) only changes the reason text, never the permit. R3r's basis fixed the `source` port (`OverviewClosed`), not these two. A four-Site prepare would not change it, since only Kobo has a Performance report. Consequence for KIS-7: if `chain_findings` is what feeds Kisiwa's Optimize earnings, a closed finding-index gate leaves Kisiwa unpriced on S regardless of the day. For the Architect.

## R3s (DIESEL-1-R3s): Kisiwa Performance comparison, KIS-7 from data, KIS-OV extension, clone probe

Commits: merge `85af3d702` (main into K9; its conflict markers were committed by mistake and fixed in) and `f994e3cf9` (the R3s change). Merge conflict: only `tools/checks/chain_coherence.py` (`LOCAL_DAY_TZ`/`SUMMARY_SITE_TZ`); both sides kept, plus `KISIWA_BOARD_DAYS`. Auto-merged: `test_demo_combined_finish_rows.py`, `test_chain_coherence.py`, `demo_combined_finish.py`, `demo_combined_rows.py`.

**Changes.** (1) `demo_combined.py` `performance_and_prebuild`: KISIWA-001 joins the loop when `"kisiwa"` is in `story["sites"]`. (2) `demo_rows.kis7(summary_s, bodies, heads, s_day, board_at)` rewritten per §9s.3, with expectations from stored heads (`finding_revision` episode + latest `financial_consequence_revision`); `kis_7` row reads them. (3) `demo_rows.kis_ov(reads, basis, board_states, report)`: newest Kisiwa report (`build_performance_comparison_reports().latest`) must be PASSED and empty-set, S-5d and S boards AVAILABLE.

**L0 and mutations** (`test_demo_combined_finish_rows.py`, 52 pass): each mutation committed-then-reverted by `git checkout`, tree clean after.
| Mutation | Result |
|---|---|
| remove the `Kisiwa priced on S == expected_s` assert | 2 tests fail |
| remove the d1 amount equality | 1 fails |
| remove the PASSED/empty-set assert | 1 fails |
| remove the AVAILABLE board assert | 1 fails |
| loop line back to `("KOBO-001",)` | 1 fails |

Focused: `test_demo_combined_finish_rows`, `test_k7_kisiwa_story`, `test_k9_finish_callsites`, `test_chain_coherence`, `test_fuel_wording` = 349 passed before the final test edits; finish_rows re-run 52 passed after.

**Clone probe** (`assetops_k9_audit_r3s` from `assetops_demo3_kisiwa_test`, 0 open connections, free RAM 2.7 GB, coordinator check-all finished first; upgraded to head; work folder copied from `AssetOpsV1-k7f` to scratch, tree = `git archive HEAD` of K9; R3r cutover `NO_LEGACY_EVIDENCE` recorded at the stored import 2026-10-26T09:00Z before the "before" read; read in-process through `TestClient`, so no server PID; dropped after). The clone holds only Kisiwa, so KIS-6 and KIS-7 fail before and after on the missing Sites (not a regression).

| Read | Before (basis, no report) | After (`performance_migration run`) |
|---|---|---|
| Report | none | PASSED, `empty_set` true, "Performance cutover: permitted"; lineage 11 runs, all break counts 0 |
| S-5d board `read_state` | PARTIAL (2 "could not be loaded") | AVAILABLE (0) |
| S board `read_state` | PARTIAL (2) | AVAILABLE (0) |
| d1 (2026-10-28) board | PARTIAL (2) | AVAILABLE (0); a dispatch FINDING issue now shows ("Generator may have been on longer than needed") |
| MG-8 (S-5d / S / d1) | UNKNOWN PRODUCER_NOT_SETTLED on all three | node found with state null / NO_OBJECTIVE / UNKNOWN PRODUCER_NOT_SETTLED |
| d1 Optimize earnings | "Not known yet"; MG-2 UNKNOWN PRODUCER_NOT_SETTLED | **"Not known yet"; MG-2 UNKNOWN PRODUCER_NOT_SETTLED** |
| Night-1 day earnings (S-5d, S) | Not known yet | Not known yet |
| Estate Findings (week) Kisiwa fuel rows | 3 | 3 |
| Kisiwa rows KIS-4, 8a, 1, 2, 5, 10, 3, 9, 8 | pass | pass |
| KIS-OV | FAIL (no report) | pass |
| KIS-6, KIS-7 | FAIL (clone has one Site) | FAIL (same) |

**Stop S-s4 fired: d1 is unpriced after the report.** S-s1 (report PASSED, gate open), S-s2 (no row passes-then-fails) and S-s3 (boards AVAILABLE, no failed port) did not fire. Both S boards also show `finding_gaps` "Not available yet · 31 of 31 days are not assessed yet" before and after. Reading, not a patch: the dispatch Finding is visible on d1 but MG-2 stays PRODUCER_NOT_SETTLED, so the Optimize earnings is not priced from the board's own snapshots. The clone was never ticked (the schedule/prebuild steps of `finish` did not run on it), which may be why the producer is unsettled; unconfirmed, for the Architect. No patch, no prepare.

**Screenshot:** not taken (stop S-s4; no frontend/API server started). Board JSON per day: scratchpad `k9r3s\out\board-{before,after}-{S-5d,S,d1}.json`.

**Process deviations:** the merge commit includes unresolved conflict markers (a failed Edit followed by a chained commit); fixed forward in `f994e3cf9`, no amend. Scratch `clone.py` was written with `Set-Content`. Free RAM was 2.6-2.75 GB while waiting for the coordinator's check-all, which was above the 2.5 GB floor.

## R3s2 (ruling DIESEL-1-R3s2, build sheet §9s2)

**Change** (`tools/demo_combined_rows.py` `kis7`, commit 8f0370c25; no product code):
- KIS-7 item 3 (d1 priced and equal to the stored lead head) is report-only. The row output carries `d1_priced`, e.g. "REPORT-ONLY (R3s2): d1 is unsettled: no `productive_kwh` subject (R3s2); board earnings unpriced; 2026-10-28". A code comment quotes the reason. Stop S-s4 is not a code assertion (it was a probe stop), so it is report-only by construction here.
- Items 1 (Optimize card follows the priced Sites), 2 (Kisiwa priced on S iff a PRICED head overlaps S) and 4 (`never_summed`) stay asserted. The "no PRICED head at all" precondition also stays asserted (it is data, present in the story).
- L0 (`test_demo_combined_finish_rows.py`): an unpriced d1 and a differing d1 amount now pass and report; new break cases for item 1 (tampered card) and item 4 (summed total on a two-priced S).
- Mutation (committed first, then `git checkout`): neutering item 2's assert fails 2 tests; replacing `never_summed` with `0 *` fails the item-4 test; `card = None` (item 1 dropped) fails the break-loop test. Tree clean after each revert.

**Packet notes**
- The Protect-row claim quotes the row state (NEEDS_ATTENTION, `unexplained_fuel` night 10-31) and MG-8's own entry in the board's outcome list, not the `lead_outcome` field, which carries only `{key, label}`. The earlier "MG-8 state null" line in the S-5d row above is that field read, not a defect (§9s2.3).
- Presenter note: open the S-5d Kisiwa board once before the client joins (Kisiwa is not in the prebuilt routes; the first open is a cold build).
- Process note: review `tools/checks/chain_coherence.py` at f994e3cf9, not at 85af3d702 (which holds conflict markers). At this HEAD the file has no `<<<<<<<|>>>>>>>|=======` line starts (Grep).

**Checks (focused, no DB, no check-all):** `test_demo_combined_finish_rows.py` 52 passed; `test_k7_kisiwa_story.py` 99 passed; `test_k9_finish_callsites.py` 2 passed; `tools/checks/test_chain_coherence.py` 177 passed; `tools/checks/test_fuel_wording.py` 21 passed.

## Rehearsal (four-Site prepare on `assetops_demo3_k9rehearsal_test`, `var/demo3_k9rehearsal`)

Read-only checks; no code or expectation edited. `check.json` copied to `check-rehearsal.json`.

**Run.** Started 14:38:07, last log write 16:59:36: wall 2 h 21 m 29 s (8489 s). Exit code 1. Kisiwa 3180 s, Kobo 1811 s, prebuild OK (23 requests, 0 non-200), drain-2 one tick (79 s), self-check 1183 s: 46 pass, 4 fail, 0 skipped. Peak working set: known only to 0.37 GB at 56 min (watchers reaped by low memory).

### Failing rows (4)

**KIS-8a** `AssertionError: ('COH-17 UF1', [{'rule': 'COH-17', 'site_code': None, 'window': 'week', 'subject': 'UF1', 'detail': "a Portfolio card holds the sum of an unexplained-fuel amount and another amount: ['119.57', '180.43']", 'bodies': []}], {'compared': 3, 'skipped': 0})`. Class (i), wrong expectation in the shared UF1 rule. Asserts before it passed (`demo_combined_rows.py:476-483`: night-4 node entry and `protect.fuel_line` in `fuel_lines`); it fails at `:485-486`, which calls `coh17_fuel`. Data (week `summary.week.json`): Kisiwa Protect `unexplained_fuel` amount_low 119.57, amount_high 180.43 USD; Kobo Optimize earnings value low `0.00` USD (`value.low`, schema pins amount_low to 0). `tools/checks/chain_coherence.py:1339,1342,1347-1350` pairs every fuel amount with every other same-currency amount and flags a two-place sum found in any card string: 119.57 + 0.00 = 119.57 and 180.43 + 0.00 = 180.43, each of which is printed in the Protect fuel line itself. Nothing is added in the product; the rule has no exclusion for a zero addend, and it never met a fuel amount alongside Kobo's 0.00 low before the four-Site estate.

**F-COH** `AssertionError` with 8 COH-17 faults, all COH-17, none other rules:
- UF1 on week and on S (the same zero-addend cause as KIS-8a, class (i)).
- A1 on KISIWA-001, week/S/month: "Assure headline 'No verified result yet', 1 verified entries" (`chain_coherence.py:1358-1375`, row at `:1443-1445`). Class (ii), a real product defect: `site_outcomes/mini.py:572-573` counts `verified` from `actions` and `opp` only, not the `fuel` verdicts that `_assure` lists (`mini.py:1210-1222`, "ACT-004 verified on example data", `link_ref.kind` FUEL_VERDICT); the headline at `:580-581` falls to `NO_VERIFIED`.
- L2 summary `verified_result_count` against `count.verified_results` (`chain_coherence.py:1413-1415`): week 2 vs 3, month 2 vs 3, S 2 vs 1. Week and month: class (ii), same cause (`site_outcomes/read.py:521` `_verified_results` counts `comp.facts.actions` only; chain counts Kisiwa's verified thread: `threads.verified` 1). S is 2 vs 1 and Kisiwa is 0 on both sides on S, so Kisiwa does not explain it. Chain S Kobo shows `verified` 1, `verified_actions` 0 while the S summary counts two Kobo entries; not diagnosed (possible older Kobo S-window row, class (i) or (ii) unknown).
V1, V2, V3, V4 and the other COH-17 rows raised no finding. Bundle dirs: `dd1b2-coh-4cpxq610`, `dd1b2-coh-havc4t61`.

**MILL-5** `NameError: name 'psycopg' is not defined`. Class (i), a defect in the row code, not the WD-1m watch item: `tools/demo_combined_finish.py:966` uses `psycopg` in `mill5` (`:955-970`) with no local `import psycopg` (every other row imports it inside the function). `demo_rows.mill_assure` at `:965` ran first and did not raise, so the WD-1m check (an example source class at E3) was not what failed; the stored-outcome SQL at `:966-969` never ran, so `stored == ["VERIFIED"]` is unverified.

**KIS-6** `AssertionError: ('Kisiwa verified threads', 1, 'verdict', {'evaluated_at': '2026-11-05T13:00:00Z', 'outcome_id': '0a2b66c6-5af9-4d4a-8bc9-f09100975c10', 'replayed': False, 'state': 'VERIFIED', 'stored': True})`. Class (i), wrong expectation: `demo_combined_rows.py:1140` compares `kisiwa_doc.get("verdict") == "VERIFIED"`, but `kisiwa.json` `verdict` is a dict (`demo_combined_kisiwa.py:688`; state "VERIFIED"), so `want` is 0 against the chain's `threads.verified` 1 (correct; the verdict is VERIFIED). The asserts before it passed (four Sites in summary, chain and objectives; summary cells equal the S board; window basis DAY and start). The Assure card claim and H2 asserts at `:1144-1153` did not run. K10 (measure applicability, read side) settles Grow, Optimize and Assure cells on both the board and the summary, so `cells == board` stays equal; K10 does not touch `:1140`, so KIS-6 would still fail until the row reads `verdict["state"]`.

### Passing rows (quotes)

- KIS-1 `current_revisions 3, stop_soc 90 %, no_load 4.9 L/h GENERIC_DEFAULT, sensor 10 L GENERIC_DEFAULT, price 1.25 USD (v1), windows_priced 10`. KIS-2 `findings 2` (17 and 16 intervals). KIS-3 `nights 10`, states 4=UNEXPLAINED else WITHIN_MARGIN, `max_diff_l` all 0. KIS-4 `supported 1, priced 1, sums_checked 5, served_strings 652`. KIS-5 `VERIFIED, TARGET_MET, pins_checked 4`, later nights 11-02..11-04. KIS-8 `bodies 90, naming_site 17, hits 0, repository_files 443`. KIS-9 `records 13, dips 11, placed 15`. KIS-10 `ACT-004 verified on example data`, thread 561002f3-68d6-521c-9035-0777be9a09ba.
- KIS-7 item 3 (report-only): `d1_priced: "REPORT-ONLY (R3s2): d1 is unsettled: no productive_kwh subject (R3s2); board earnings unpriced; 2026-10-28"`; `kisiwa_priced_on_s false, priced_on_s ["KOBO-001"], sums_checked 0, optimize_card "0.00 to 15.13 USD"`.
- KIS-OV: `overview_status {S-5d: 200, S: 200}, basis NO_LEGACY_EVIDENCE, performance_report {outcome: PASSED, empty_set: true}, board_read_state {S-5d: AVAILABLE, S: AVAILABLE}`.
- CO-6: `status UNKNOWN, kisiwa_present true`, `window_basis` COLD PERIOD, EV PERIOD, KISIWA DAY, KOBO DAY; Kobo days "5 of 7 days assessed · 2 days not available yet". CH5D1-O1: `0.00 to 15.13 USD`.
- COH-17 V1-V4: no finding on any of them in the F-COH report (V4 compares summary nodes to board nodes on S for the mini Sites, Kisiwa included).
- `board_summary.S.KISIWA-001`: request status 200 (path `/api/sites/KISIWA-001/outcome-board`, from 2026-11-05T21:00Z to 11-06T21:00Z).

### Kisiwa S-5d board (2026-11-01, in process, `ctx.get`)

- Protect row: state `UNKNOWN`, label "Unknown", lead `{key: MG-5, label: Reliable service}`, headline "Battery and generator condition are not assessed", `nodes.unexplained_fuel` one entry: night 2026-10-31, 95.7-144.3 L, 119.57-180.43 USD, "Unexplained fuel on the night of 31 Oct: about 95.7–144.3 L, 119.57–180.43 USD at your declared price (a modelled range, shown on its own)". This differs from the R3s2 note above ("row state NEEDS_ATTENTION"): on S-5d the row reads UNKNOWN.
- MG-8's own outcome entry (`rows[2].outcomes[2]`): `{"key": "MG-8", "label": "Fuel accounted for", "state": "UNKNOWN", "reason": "PRODUCER_NOT_SETTLED"}`.

### Watermark guard CLI (`tools/chain_watermark_guard.py`, R3j3, 256 s)

`requests 46 non-200 0 tables read 80 unresolved [] untracked [] event_consumption_read True clock_predicates 0 file_violations 0 modules 143 unlisted_modules ['assetops_backend.actions.fuel_verification', 'assetops_backend.actions.verification_families', 'assetops_backend.financials.assumptions', 'assetops_backend.financials.composition', 'assetops_backend.financials.fuel_cost_v2']`, exit 1. `fuel_balance_window`, `fuel_residual_consequence_revision` and `financial_consequence_revision` are in `all.read`. Result: **S-h** (`unlisted_modules` is not `[]`, exit not 0).

### Notes

- No server started; all reads were in process (TestClient), so no PIDs to kill. The DB and work folder are kept. The served reads write read-through board cache rows as in the prepare; no other DB write.
- Summary of causes: UF1 (KIS-8a, F-COH) i; KIS-6 i; MILL-5 i (row-code import); Kisiwa Assure headline and legacy verified count (F-COH A1, L2) ii; S-window L2 undiagnosed. None is an environment artefact (iii).

## Fix round (R3u) (ruling DIESEL-1-R3u, build sheet §9u; main 886341aff merged)

Commit `0be93c2ce` (code and tests). Tools-only plus tests: no backend or config diff, so `code_version` is unchanged. No DB, no check-all, kept DB and `var/demo3_k9rehearsal` untouched. The K6c (U2, U3, U6) items are not in this round.

| Item | Change |
|---|---|
| UF1 / U1 | `nonzero_pair_sums(pairs)` in `tools/checks/chain_coherence.py` (same-currency, non-None currency, neither addend zero). Used at all four sites: UF1 (`coh17_fuel`), PV1 (`coh17_values`), `pv_values`, and `kis4` (fuel x dispatch `amount_high` and fuel x fuel; the dispatch zero now reaches the helper instead of a pre-filter; the `stored` set still drops zero). |
| MILL-5 / U4 | `import psycopg` first statement of `mill5` (after its docstring). L0 AST test `_psycopg_import_gaps`: every function naming `psycopg` imports it in its own body, and the module has no top-level import. |
| KIS-6 / U5 | `(kisiwa_doc.get("verdict") or {}).get("state") == "VERIFIED"`; the assert message and the return `verdict` report the state. |
| KIS-OV / U7 | `kis_ov(..., s5d_board=None, second_read=None)`: S-5d Protect row state `NEEDS_ATTENTION` and MG-8 outcome `{NEEDS_ATTENTION, PRIMARY_FINDING_OPEN}`; the lead is not asserted. A failure raises with "R3u-s1" plus the board `read_state`, `warnings` and a second read by the Site-local `from`/`to` pair (lazy callable from the row). The row reads the S-5d body once and derives `read_state` from it. |
| KIS-7 item 3 / U8 | Asserted again ("KIS-7 item 3 (R3u)": unpriced d1, differing amount, non-PRICED lead head all fail). The R3s2 report-only form stays reachable: `kis7(..., item3_report_only=True)` or module `KIS7_ITEM3_REPORT_ONLY = True` (K10 held), with its quoted reasons. Default is asserting. |

**Tests (pure; PYTHONPATH absolute under the k9 worktree):** `test_demo_combined_finish_rows.py`, `test_k7_kisiwa_story.py`, `test_k9_finish_callsites.py`, `test_k4a_fuel_finding_rules.py`, `tools/checks/test_chain_coherence.py`, `tools/checks/test_fuel_wording.py`: 383 passed in 46 s. New: helper unit test; UF1, PV1, `pv_values`, KIS-4 each with a zero case (no finding) and a planted non-zero case (134.70 for UF1: 119.57 + 15.13; 21.12 for PV1) still found; KIS-6 dict VERIFIED reaches the card and H2 returns, INEFFECTIVE with `threads.verified` 1 fails, a null verdict fails; KIS-OV pass, the packet's UNKNOWN / PRODUCER_NOT_SETTLED shape fails, Protect UNKNOWN fails, MG-8 other reason or absent fails, and the failure text carries `read_state` and the second read; KIS-7 item 3 break cases plus the report-only form.

**Mutations (committed first, all five applied together, 10 tests failed as listed, then `git checkout --`; tree clean):**
- helper zero check removed: the UF1, PV1 and helper tests in `test_chain_coherence.py`, `test_pva_zero_addend_...`, and `test_kis4_zero_dispatch_...`.
- `mill5` local import removed: both psycopg AST tests.
- KIS-6 back to whole-verdict compare: `test_kis6_counts_cells_...`.
- KIS-OV pin disabled (`if False and`): `test_kis_ov_pins_the_s5d_protect_row_and_mg8_entry_r3u`.
- KIS-7 item 3 raise disabled: `test_kis7_expectations_from_data_pass_and_each_break_fails`.

**Process deviations:** the first `mill5` mutation Edit matched two places and was rejected; retried with more context (no change made by the failed call). The `test_k4a_fuel_finding_rules.py` file (not in the named list) was edited for the KIS-4 zero case and run. The `second_read` pair format (`from`/`to` ISO UTC of the Site-local day) is my reading of "the local `from`/`to` pair"; it has not been served-tested (R3u-s1 applies at the clone run).
