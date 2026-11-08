# Review packet: DIESEL-K4b, Protect row MG-8 "Fuel accounted for", the fuel Finding on the board, Portfolio Protect lines

- **Task:** K4b card, `.agent/build-sheet-DIESEL-1.md` §9j.10–§9j.13 (R3j), amended by §9k (domain filters, K4a), §9l.4 (link with `fuel_finding_ref`, reason words imported from K5), §9m/§9m2 (Protect thread line stays K4b), §9j2 (R3j2: the S-a stop ruling). PV-1-R (`build-sheet-FUEL-1.md`) for the one-line-each, never-summed pattern.
- **Branch:** `task/DIESEL-K4b-protect-fuel`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k4b`. Base main `a6c28932b`; main (K5, `f29b1a421`) merged at `7ab4dd910`.
- **Commits:** `f7e219a46` part 1 (K5-independent), `7ab4dd910` merge main (K5), `745b0462e` part 2 (contributor), `5588b7e35` goldens, `7b77886f0` module list / clock allowlist / Kobo Postgres expectations, plus this packet's commit.
- **USER_REVIEW_REQUIRED:** no separate walkthrough (W1 rule: merge on review ACCEPT); the change is visible on Kisiwa only once K7's data exists.

## Outcome delivered

- **MG-8 "Fuel accounted for"** (MINI, Protect, after MG-4), moved by `FINDING:UNEXPLAINED_FUEL`. Not applicable on a Site with no stored fuel-balance window (Kobo). Settled when night D−1's window exists and is assessed and the fuel Finding read succeeded (and the dispatch Finding source is settled, the existing rule). A failed applicability read is PARTIAL and MG-8 UNKNOWN, never N/A.
- **The unexplained-fuel Finding on Kisiwa's board**: a Protect issue "Unexplained fuel overnight" (link `FUEL_FINDING`, K5's page), its thread line on Protect, in-hand/earlier placement through the outcome map only. COST lead, money head and Trial option stay on dispatch Findings.
- **No close countdown** for the fuel thread (R3j2 §9j2.4): `close_measured: False` marker set by the composer, kept by `with_threads`, honoured by `thread_line_item`.
- **"Fuel in the tank"** Protect contributor after "Backup readiness", only on a Site with a stored window; six cases verbatim from §9j.11, reason words imported from K5's `night_text.FUEL_REASON_WORDS` (unknown reason -> K5's `UNKNOWN_VALUE`); a failed window read reads "Not available yet · this record could not be loaded".
- **Protect node `unexplained_fuel`** and **Portfolio Protect `fuel_lines` / `fuel_note`** (PV-1 pattern: one line each, own basis `UNEXPLAINED_FUEL_AT_DECLARED_PRICE`, no total, no arithmetic). Frontend renders lines and note after the card detail; server text only, no new CSS.
- **S-a route (b)** (R3j2 §9j2.3): `parse_thread_lifecycle` accepts an empty list; `"UNEXPLAINED_FUEL": []`; `ENTRIES` line; chain graph regenerated; counts updated.
- **`SITES_DISRUPTED`** excludes `UNEXPLAINED_FUEL` (`NOT_DISRUPTION_MECHANISMS`). Kisiwa's Protect `open_findings` +1 while the thread is open is intended (R3j2 §9j2.5 item 3).
- **COH-17 row UF1** and **finish row KIS-8a** (runs at E3).

## Files materially changed

Backend: `outcomes/catalogue.py`, `outcomes/outcome_map.py`, `chain/lifecycle.py` (one predicate + comment), `chain/claims.py`, `chain/vocabulary.py` (two `CARD_TEXT`), `site_outcomes/board.py` (two `SiteFacts` fields, `applicable=`, node, countdown guard, `with_threads` marker), `site_outcomes/mini.py` (ports, fuel Findings, lead restriction, MG-8 settled/applicability, contributor, node, literals), `site_outcomes/read.py` (`BoardServices.fuel_balance`, port bindings, Protect card keys), `site_outcomes/composition.py` (store, field, dispose). Config: `config/chain/thread-lifecycle-v1.json`. Docs: `Docs/demo-sprint/chain-graph.{dot,svg}` (regenerated). Frontend: `estate/estateClient.ts`, `estate/PortfolioOutcomes.tsx`. Tools: `checks/chain_coherence.py`, `demo_combined_rows.py`, `demo_combined_finish.py`. Tests: `test_k4b_protect_fuel.py` (new), `test_ch5b_graph.py`, `test_ch6_contributions.py`, `test_demo_combined_finish_rows.py`, `test_ch5a1_board_contract.py` (fixture fuel store), `tools/checks/test_chain_coherence.py`, `estate/__tests__/estatePortfolio.test.tsx`, `portfolioFixtures.ts`; goldens `ch5a1_board_contract/kobo_2026-10-31`, `kobo_2026-11-01`, `ch5a2_chain_contract/estate_week_2026-10-25`. Also (KD-5): `config/chain/stored-composer-modules-v1.json`, `test_ch5c2_clock_guard.py`, `test_out_b4_board_postgres.py`.

## Rendered (L0 fake ports, Kisiwa-shaped: night D−1 UNEXPLAINED, one open SUPPORTED Finding, priced)

- Protect row: state `NEEDS_ATTENTION`, lead `MG-8 Fuel accounted for`, headline unchanged (the composer's Protect headline); outcomes MG-5, MG-4, MG-8 `NEEDS_ATTENTION / PRIMARY_FINDING_OPEN`; issue (MOVES, primary) "Unexplained fuel overnight" -> `/sites/{site}/fuel-findings/{id}`; contributors Battery, Generator, Service delivery, Backup readiness, **Fuel in the tank** "About 61.2–98.4 L unexplained on the night of 19 Oct" (Limited, amber) -> `/sites/{site}/performance/fuel`; node `unexplained_fuel[0].text` "Unexplained fuel on the night of 19 Oct: about 61.2–98.4 L, 76.55–122.95 USD at your declared price (a modelled range, shown on its own)".
- Portfolio Protect card: `fuel_lines` ["Kisiwa · Unexplained fuel on the night of 19 Oct: about 61.2–98.4 L, 76.55–122.95 USD at your declared price (a modelled range, shown on its own)"], `fuel_note` "Unexplained fuel is shown on its own and never added to any other money"; detail, value, claim, tone unchanged.

## Acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| MG-8 N/A with no windows; UNKNOWN when night D−1 NOT_ASSESSED/absent; NEEDS_ATTENTION with open SUPPORTED Finding; WATCH when applied | Met | `test_k4b_protect_fuel.py` (applicability, unknown x3, attention, watch) |
| Six contributor cases and chips, after Backup readiness | Met | `test_fuel_stock_contributor_cases_follow_backup_readiness` (7 params incl. the guard-V-safe idle wording) |
| Issue on Protect and no other row | Met | `test_open_supported_fuel_finding_needs_attention_on_protect_only` |
| COST lead and Trial option unchanged; must fail if lead from all Findings | Met | `test_cost_lead_and_trial_option_ignore_the_fuel_finding`; mutation proof below |
| Thread line on Protect only; no countdown (R3j2) | Met | `test_fuel_thread_line_shows_on_protect_only`, `test_no_close_countdown_without_a_clean_day_measure`, `test_composer_marks_the_fuel_view_and_with_threads_keeps_it` |
| Node present only when non-empty | Met | `test_no_window_site_...`, node tests |
| Kobo Protect row equals main's except the MG-8 entry | Met | `test_kobo_protect_row_equals_the_pre_k4b_row_except_the_mg8_entry` + goldens below |
| Protect card gains only `fuel_lines`/`fuel_note`; Grow/Optimize/Assure byte-equal; no fuel sum | Met | `test_protect_card_lists_each_line_...`; `test_pv1_value_lines.py`, `test_ch6b2_portfolio_cards.py` green unchanged |
| Golden diff only MG-8 N/A entry + Protect `fuel_lines: []`, `fuel_note: null` | Met | see Golden diffs |
| Cold/EV unchanged | Met | Cold/EV goldens: no content diff on regeneration; `test_out_b3_cold_ev.py` green unchanged |
| S-a route (b) tests + app-start graph check | Met | parse/declaration/graph tests; `test_ch5b_graph.py` |
| `SITES_DISRUPTED` exclusion L0 | Met | `test_fuel_thread_is_not_a_service_disruption` |
| UF1 + 6 self-tests; KIS-8a L0 | Met | `tools/checks/test_chain_coherence.py` (UF1 x6), `test_kis8_protect_passes_on_the_node_line_and_fails_otherwise` |
| Vocabulary scan gains every K4b literal | Met | `mini.COPY` (titles, label, all contributor texts incl. every reason word, node lines) and `CARD_TEXT` are swept by `test_out_b2_vocabulary.py` |
| Frontend: Protect renders lines and note; absent keys render nothing; `tsc` | Met | two new `estatePortfolio` tests; `tsc --noEmit` clean |
| Board outcome list renders "Fuel accounted for" | Deviation | KD-2 |

## Golden diffs (DRIFT-R1 §2.2: regenerate, diff, accept only the named change)

- `ch5a1_board_contract/kobo_2026-10-31.json`, `kobo_2026-11-01.json`: +1 Protect `outcomes` entry `{"key": "MG-8", "label": "Fuel accounted for", "reason": "CONFIGURATION_NOT_APPLICABLE", "state": "NOT_APPLICABLE"}`. Nothing else.
- `ch5a2_chain_contract/estate_week_2026-10-25.json`: `cards.PROTECT_ASSET` gains `"fuel_lines": []`, `"fuel_note": null`. Nothing else.
- `cold_2026-10-31.json`, `ev_2026-10-27.json`: regenerated, zero content diff (`git diff --numstat` empty).
- The first regeneration (before the fixture fix) gave MG-8 **UNKNOWN/PRODUCER_NOT_SETTLED** on Kobo, because the contract fixture's `BoardServices` had no fuel store (the port raises, R3j2 rule). It was reverted, not accepted; the fixture now supplies a no-window store (KD-3).

## Checks run

All on the branch head (`7b77886f0` code; the packet commit adds only this file). Python: `AssetOpsV1-plan2\.venv`, PYTHONPATH absolute into the k4b worktree.

- **L0 K4b:** `test_k4b_protect_fuel.py` 29 passed.
- **Non-vacuity (committed first, mutated, reverted with `git checkout`):** lead filter removed -> lead/Trial test fails; `close_measured` guard removed -> countdown test fails; `NOT_DISRUPTION_MECHANISMS` predicate removed -> exclusion test fails; config `UNEXPLAINED_FUEL` line removed -> declaration test and app-start graph-check test fail (5 failed, 16 passed); tree clean after revert.
- **Adjacent L0:** graph, contributions, outcome map, vocabulary, imports, PV-1, portfolio cards 136; mini, MB-1, out_d4, walk1-3b, cold/EV, claims, optimize card 244; finish rows, lifecycle, threads, md0b 166; board read/contract suites (ch5a1/ch5a2 contract, out_b4 read/window, out_c2, out_w2, qw2, walk1 sales, ch6b1_r5, ch5a1 ledger, ch6b estate chain, fetch seam, ch5b why, k6b rules, k5 text) 267; `test_ch5c2_clock_guard.py` 7.
- **Coherence self-tests:** `tools/checks/test_chain_coherence.py` 164 passed (UF1 x6 included).
- **Frontend:** `estatePortfolio.test.tsx` 65 passed; `tsc --noEmit` clean.
- **Postgres (`assetops_k4b_test`, created for this slice; template routing):**
  - `test_out_b4_board_postgres.py`, `test_k5_fuel_night_api_postgres.py`, `test_k4a_fuel_finding_postgres.py`: all pass (30 passed in one run with the F4 test below, 397 s).
  - `test_ch5c2_real_composers_postgres.py`: 6 passed (155 s) after KD-5; it first failed F4 (`['assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store']` unlisted), then the clock guard named the store's three SQL clock sites.
  - `test_w301_estate_golden_postgres.py`: 6 failed, `$.summary.claims` holds an extra `count.opportunities` the golden lacks. **Pre-existing on main** (recorded by the K4a builder, `.agent/followups-fuel-kisiwa-2026-11-07.md:26`); K4b adds no claim key.
  - `test_ch6b_estate_postgres.py`: not run, `MechanismRefused: TEMPLATE_STALE` (the mechanism dataset template belongs to another checkout; the rebuild, `tools/mechanism_dataset.py build --variant states --budget 540`, is a heavy step not taken during the Kisiwa prepare). Unverified here.
- **Guards:** `check-all.ps1 -Python` on part 1: 17/17 passed. Final run: CHECKALL_FINAL.
- **Not run:** full suites, prepare, layout evidence (not layout-sensitive: two server-text `<p>` lines with existing classes on an existing card).

## Known deviations

- **KD-1 (R3j2 §9j2.4 placement):** the ruling sets `close_measured: False` in `mini.py`, but the lifecycle view is attached after compose (`read.py` -> `board.with_threads`). The composer marks the fuel `FindingFact` and `with_threads` keeps the key on the looked-up view; dispatch/Cold/EV views never carry it. Same behaviour, one extra function in `board.py` (on the approved list).
- **KD-2 (frontend outcome list):** the card asks for a board-outcome-list test rendering "Fuel accounted for". The Site board has no outcome-list render path (`OutcomeBoard.tsx` renders only `lead_outcome`), so no client test can attach; MG-8 reaches the client only as the server's `lead_outcome.label` when it leads. Recorded as directed by the coordinator.
- **KD-3 (contract fixture):** `test_ch5a1_board_contract.py` gains a `NoFuelBalance` fake (no tank, `has_windows` False), like its other fake services. Without it the fixture board would be PARTIAL with MG-8 UNKNOWN, which is not Kobo's real state.
- **KD-4 (contributor on a failed window read):** the card names no text for it; the board's standing rule (`not_available`, "Not available yet · this record could not be loaded") is used.
- **KD-5 (files beyond the approved list, mechanical consequences of R3j2's store injection):** `config/chain/stored-composer-modules-v1.json` gains the fuel-balance store module (F4/Q5: every module a stored compose runs is listed); `backend/tests/test_ch5c2_clock_guard.py` allowlists its three SQL clock sites by (module, function): `night_context.work` as a read-instant capture (K5 wraps it in `read_scope.read_instant`), `transaction` (K3 assess) and `night_window_on` (K4a raise) as writers a stored compose never calls; `backend/tests/test_out_b4_board_postgres.py` three Kobo state-set assertions now pop MG-8 and assert it NOT_APPLICABLE before the unchanged set check.
- MOCK DEVIATIONs: MD-FUEL-K4-1 (board issue title, `mini.py` literal comment), MD-FUEL-K4-2 (MG-8 in `catalogue.py`, contributor literals in `mini.py`), MD-FUEL-K4-3 (node lines in `mini.py`, Portfolio lines in `read.py` and `PortfolioOutcomes.tsx`).

## K5 overlap

K4b copies no K5 code. It imports `night_text.FUEL_REASON_WORDS`/`UNKNOWN_VALUE` and calls the store's `night_context`/`has_windows` as merged on main (`f29b1a421`), and links with main's `refs.fuel_finding_ref`. No K5 file was edited (no S-f).

## Residual risk

- Kisiwa's real board (issue, contributor, node, Portfolio line, Protect row NEEDS_ATTENTION) is proven on fake ports only; the first real-data run is K7's prepare and KIS-8a at E3.
- Every board build now constructs a fuel-balance store (an action store and fuel-records reader inside it): more engines per process; disposed with the board service.
- The Portfolio Protect `open_findings` count rises on Kisiwa while the thread is open (intended, R3j2); K8 re-expects it.

## User-review focus

- The Protect wording: "Fuel accounted for", "Fuel in the tank" texts, "Unexplained fuel overnight", the Portfolio line and clause ("Unexplained fuel is shown on its own and never added to any other money").
- Kobo shows MG-8 as N/A only in the outcome list (not rendered on the board today); its Protect state, tone, lead and headline are unchanged.
