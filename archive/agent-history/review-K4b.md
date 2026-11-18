# Review: DIESEL-K4b (Protect MG-8 "Fuel accounted for", fuel Finding on the board, Portfolio Protect fuel lines)

- Reviewer: fresh Claude (Opus), independent first review, 2026-11-08.
- Branch `task/DIESEL-K4b-protect-fuel`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k4b`, head `08a446410` (code at `7b77886f0`). Diff `git diff main...HEAD`.
- Spec: `.agent/build-sheet-DIESEL-1.md` §9j.10–§9j.13, §9j2 (R3j2), §9l.4; PV-1 pattern; owner notes "unexplained fuel, never theft" and "never a combined total".

## Verdict: FIX

The slice matches the K4b card and R3j2 closely. The tests are non-vacuous: I ran 8 mutations myself and all 8 were caught. The goldens differ exactly as the card says. One High finding blocks the merge. The board and the estate summary are stored routes, and they now read two tables that carry no watermark (W2) change triggers. That breaks the CH-5c stored-route contract. It needs an Architect ruling, because the fix is a migration outside the approved file list.

## Findings

### H1 (High): stored routes now read two untracked tables, `fuel_balance_window` and `fuel_residual_consequence_revision`

- **Where:**
  - `backend/assetops_backend/site_outcomes/read.py:408-423` binds `fuel_has_windows`, `fuel_windows` and `fuel_findings` into `mini_ports`.
  - These call `PostgresFuelBalanceStore.has_windows`, `windows` and `_fuel_findings` (`fuel_balance/adapters/postgres_fuel_balance_store.py:229-234`, `:217-227`, `:289-312`). The SQL reads `FROM fuel_balance_window` and `FROM fuel_residual_consequence_revision`.
  - `mini.compose` runs `has_windows` on **every** mini board, Kobo included (`mini.py:500`).
- **What is wrong:**
  - The board (`outcome_api.py:220`) and the outcome summary and Portfolio (`outcome_api.py:252`, `estate_portfolio_api.py:75`) are served through `ChainResponseStore.serve`. A stored body is reused while the watermark `W` is unchanged.
  - The CH-5c contract (`tools/chain_watermark_guard.py` docstring) says: "Every base table read must carry the four W2 change triggers ... one that does not fails it (`untracked`)."
  - Neither table is in 0047's `INPUT_TABLES` (`backend/migrations/versions/0047_chain_response.py:29-50`) or in `config/chain/watermark-inputs-v1.json`.
  - Neither 0055 nor 0056 creates `chain_input_change` triggers. 0055 creates only an immutability trigger, and 0056 only one on the consequence table.
  - Before K4b, no stored composer read the fuel-balance store: K4b had to add the store module to `stored-composer-modules-v1.json` (KD-5).
- **Concrete failure:**
  - A K3 assessment writes a `fuel_balance_window` row for Kisiwa's night D−1. Examples: a WITHIN_MARGIN, BELOW_MATERIALITY, EXCESS or NOT_ASSESSED night, or the Site's first window ever. None of these raises a Finding, so `finding` and `finding_revision` stay untouched.
  - `W` does not move. A board for that day stored before the write keeps serving the old body: "Not available yet · no fuel check for the night of …", MG-8 UNKNOWN, or MG-8 NOT_APPLICABLE when it was the first window.
  - A live body is refreshed only at the next local midnight (`valid_until`).
  - A historical (`known_at`) body with no live boundary never expires (`response_store.py:216-217`). This matters with backdated prepare writes such as K7's clock override.
  - The W6 listener guard CLI (`tools/chain_watermark_guard.py --database-url …`) would report `untracked: [fuel_balance_window, …]` on every stored board route, Kobo included, because `has_windows` always runs.
  - No pytest catches this. The F4 test (`test_ch5c2_real_composers_postgres.py`) checks modules, not tables, and `test_ch5c_w6_guard_postgres.py` uses planted tables only.
- **Why it matters:**
  - The stored-route cache is the demo's serving path. Stale Protect fuel state on Kisiwa would contradict the Fuel page (K5), which is not stored.
  - The prebuild-after-prepare order may hide this in the scripted demo. It is still a broken guarantee and a guard failure waiting for E2.
- **Fix (needs an Architect ruling, since a migration is outside §9j.13/§9j2.6):**
  1. A migration that adds the 0047-style `chain_input_change` triggers (INSERT, UPDATE, DELETE, TRUNCATE) to `fuel_balance_window` and `fuel_residual_consequence_revision`.
  2. Add both tables to `watermark-inputs-v1.json`, in step with the frozen list that `test_ch5c_watermark_postgres.py:40` compares.
  3. Run the W6 guard CLI once on a Kobo and a Kisiwa-shaped clone and record the result in the packet.
  - The alternative is to rule explicitly that these reads are exempt, with a reason. I see no sound reason.
  - Note for the Architect: R3j2 §9j2.5 item 1 approved the store injection without naming watermark coverage. This is a spec gap as much as a build gap.

### L1 (Low): two cutoffs on a live board

- **Where:** `read.py:410-423`.
- **What is wrong:** `fuel_has_windows` and `fuel_windows` read as of `k` (the store's `night_context` instant when `known_at` is None). `fuel_findings` passes `known_at` itself (None, meaning no cutoff).
- **Scenario:** a K4a raise commits between the `night_context` capture and the `fuel_findings` read. The node and issue then show a Finding whose window is newer than the `k` used for MG-8 settlement.
- **Impact:** tiny on a demo host, but it is not "as known at the board cutoff" (§9j.11).
- **Fix:** pass `fuel_context()[1]` to `fuel_findings` as well. Stored composes already pass `known_at`, so this is unchanged there.

### L2 (Low): the no-countdown marker depends on `ct.policy`

- **Where:** `mini.py:818` (`no_close = policy is not None and …`).
- **What is wrong:** when `chain_threads` fails or `thread_policy` is not injected, the fuel `FindingFact` gets no `close_measured` marker. `with_threads` can still attach a view, so the §9j2.4 guard is bypassed.
- **Impact:** none today. `_thread_action` sees only W1 `ActionFact`s, and the fuel Action is a domain Action. It is spec-compliant (§9j2.4 conditions on `measures_for`), so this is recorded as residual risk only. A fixed `FUEL_MECHANISM` check would close it.

### L3 (Low, cosmetic): whitespace regression

- **Where:** `mini.py:504`, `plan_facts =tuple(...)`.
- **What is wrong:** main has `plan_facts = tuple(...)`. The edit lost a space.
- **Fix:** restore the space.

## What I checked, item by item

1. **Lifecycle and graph:**
   - `lifecycle.py:101-104` drops only `or not names` and adds the verbatim comment. The top-level non-empty check is unchanged.
   - Mutations "empty list rejected again" and "list-type check dropped" both fail `test_parse_accepts_an_empty_list_and_still_refuses_bad_lists`.
   - The config change adds `"UNEXPLAINED_FUEL": []` as the last key and nothing else.
   - `test_the_app_start_graph_check_passes` and `test_ch5b_graph.py` (7 / 6 / 16) are green.
   - I re-ran `tools/chain_graph_render.py`. It rewrote both chain-graph files, and `git status` was clean afterwards, so the committed `.dot`/`.svg` are the exact regeneration. (I ran it to view its options and it writes in place; nothing changed.)
   - No other mechanism or lifecycle byte changed.
2. **MG-8:**
   - With no stored window, the outcome is NOT_APPLICABLE (`has_fuel is False`, `mini.py:624`).
   - A failed `has_windows` read gives MG-8 UNKNOWN and a PARTIAL board. The mutation "`has_fuel is not True` → N/A" is caught.
   - The settled rule matches §9j.11: the window for night D−1 exists, is not NOT_ASSESSED, and the Finding read succeeded. The existing `findings_ok` loop also applies. The mutation that drops the NOT_ASSESSED term is caught.
   - Kobo: the goldens and the 3 Kobo Postgres tests show MG-8 NOT_APPLICABLE, with the Protect state, tone, lead and headline unchanged.
3. **Fuel Finding on the board:**
   - Placement goes only through `ENTRIES["FINDING:UNEXPLAINED_FUEL"] = (("MG-8",), ())`, so it lands on Protect only.
   - The lead is filtered to `GENERATOR_SUPPORT_CANDIDATE` (`mini.py:535-536`). `heads`, `lead_findings` and `money_head` stay on dispatch `heads`. The mutation "lead from all findings" is caught.
   - `thread_line_item` has the `close_measured is False` guard. Removing it is caught.
   - The node keeps SUPPORTED Findings only (`_unexplained_fuel`). The mutation "node on every row" is caught.
   - Wording matches §9j.11 verbatim. A scan of the added lines found no theft, steal, stolen, pilfer or siphon words. Guard V passed per the packet's check-all 17/17 (I did not rerun check-all).
4. **Portfolio Protect card:**
   - It adds only `fuel_lines` and `fuel_note` (`read.py:849-864`). Each line is a `card_text` of the server node text. There is no arithmetic.
   - UF1 (`chain_coherence.py coh17_fuel`) checks that no card string holds a two-place sum of fuel+fuel or fuel+other in the same currency.
5. **`claims.disrupting`:** it excludes `UNEXPLAINED_FUEL`, and the predicate mutation is caught. `threads.classify` is untouched, so the open, in-hand and verified counts still include the fuel thread.
6. **Goldens:**
   - The diff is exactly: 2 × Kobo Protect MG-8 N/A entries, plus `"fuel_lines": []` and `"fuel_note": null` in `estate_week_2026-10-25`.
   - No Cold or EV golden appears in the diff.
   - **KD-3** (the `NoFuelBalance` fake) is correct. It reproduces the real Kobo answer (no tank, `has_windows` False), and the real-store path is covered by `test_out_b4_board_postgres` Kobo, which I ran green. The fake cannot hide a missing-store failure, because the L0 `test_failed_applicability_read_is_partial_and_mg8_unknown_never_na` covers that path.
7. **KD-5:**
   - The module-list entry is correct (F4).
   - The clock-allowlist entries are sound. The board binds only `night_context`, `has_windows`, `windows` and `fuel_findings` (`read.py:408-423`). `night_context.work` wraps its `clock_timestamp()` in `read_scope.read_instant` (store `:244`). `transaction` (K3 assess) and `night_window_on` (K4a raise) have no board caller.
   - The entries are keyed by (module, function), the established pattern. The guard is not weakened: the planted-clock non-vacuity tests are unchanged and green.
   - The `test_out_b4_board_postgres.py` edits only pop MG-8 and assert NOT_APPLICABLE before the unchanged set checks.
8. **Mutations (scratch copy of `backend/assetops_backend` and `config`, imports verified to resolve into the scratch copy; repo untouched):** 8 of 8 caught.
   - claims predicate
   - lead from all Findings
   - failed `has_windows` → N/A
   - countdown guard removed
   - empty list rejected again
   - list-type check dropped
   - node on every row
   - MG-8 settled ignoring NOT_ASSESSED
9. **Not-run items:** `test_ch6b_estate_postgres` (TEMPLATE_STALE) and `test_w301` (pre-existing on main per the packet) were not run by me. In what I ran, K4b adds no failure.

## Checks I ran

- **Focused and adjacent L0 tests:** 487 passed in 51.6 s. Python was the plan2 venv. PYTHONPATH was absolute into the worktree, and I verified that `assetops_backend` resolves there. Files:
  - `test_k4b_protect_fuel.py`, `test_ch5b_graph.py`, `test_ch6_contributions.py`, `test_ch5c2_clock_guard.py`
  - `test_ch5a1_board_contract.py`, `test_ch5a2_contract.py`, `test_ch3_lifecycle.py`, `test_ch2_threads.py`
  - `test_out_b2_vocabulary.py`, `test_out_b3_cold_ev.py`, `test_out_b4_imports.py`
  - `test_pv1_value_lines.py`, `test_ch6b2_portfolio_cards.py`, `test_demo_combined_finish_rows.py`
  - `tools/checks/test_chain_coherence.py`
- **Postgres:** `test_out_b4_board_postgres.py -k kobo` on `assetops_k4b_test` through `tools/run-host-tests.ps1`: 3 passed, 2 deselected, 109 s. Free RAM was 3.97 GB beforehand.
- **Frontend:** `npx.cmd tsc --noEmit` exited 0. `npx.cmd vitest run src/estate/__tests__/estatePortfolio.test.tsx`: 65 passed. It ran here, despite the standing note that it usually does not.
- **Mutations:** 8 of 8 caught (above).

## Not verified by me

- The full suites; `check-all.ps1` (the packet reports 17/17 on `7b77886f0`).
- The W6 listener guard CLI. H1 is established from the migrations and the SQL, not from a run.
- `test_ch5c2_real_composers_postgres.py`, `test_k5`/`test_k4a` Postgres, and `test_ch6b_estate_postgres` (TEMPLATE_STALE).
- Kisiwa real data, which comes with K7.

## Residual risk not in the packet

- H1 above, until it is ruled on.
- Every mini board, Kobo included, now runs `night_context` plus `has_windows`: two read-only snapshots per Site per compose. Estate summaries multiply this by the number of Sites. This is a latency cost, not a correctness one.
