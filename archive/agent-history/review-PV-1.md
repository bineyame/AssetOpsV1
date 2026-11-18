# Review: PV-1 Portfolio verified-value lines (FUEL-1, lane 1)

- Reviewer: fresh Claude (Opus) first reviewer, independent of the builder.
- Branch / worktree: `task/FUEL-PV1-portfolio-values`, `C:\Users\assef\Bineyame\AssetOpsV1-pv1`.
- Revision reviewed: `5789fdf47` (code at `5b0b06c96`), base main `3b09aea6c` (PV-1-R ruling).
- Judged against: build sheet §3.3 (line literals, MD-FUEL-PV1-1, no-total rule) as replaced by PV-1-R, plus the owner decision `.agent/owner-fuel-scope-2026-11-07.md` (no combined total, fuel and mill money never added, nothing annualised).

## Verdict: ACCEPT

No High or Medium findings. The four Low findings below are not acceptance gaps against PV-1-R. They can be fixed on the branch at the Implementer's discretion, or carried forward.

## What I verified

1. **Mill line (focus 1).**
   - `read.py:304-305` binds `verdict_value` to `_need(s.verification, "verification").domain_summary(t, sid, UUID(id))["value"]`, as ruled.
   - `mini._verified_values` (`mini.py:1002-1030`) calls the port only for `o.outcome == "VERIFIED"`. `opportunity_actions` already nulls an outcome recorded after the cutoff, and `test_a_mill_verdict_after_the_cutoff_is_not_read` proves the port is not called in that case.
   - `domain_summary` (`verification.py:381-401`) returns a stored outcome, never recomputed. Its price is read as known at the verdict's `recorded_at` (`_mill_price`, `:403-419`), which is at or before the cutoff. Nothing reads past the cutoff.
   - A `None` or non-PRICED value gives no line. A raising port gives PARTIAL with `verdict_value` in `failed` (`Reads.call`, `mini.py:260-272`).
   - The amount is `v["per_day"]`, the verdict page's own field. Parity holds by construction: one source, no recomputation.
   - The memo key is `(site, action_id)`. That is safe, because a VERIFIED mill's value does not depend on the cutoff.
2. **Trial-fuel line (focus 2).**
   - It is gated on `a.verification_state == "VERIFIED"`, `credited(a.cost_check, "VERIFIED")` and `fuel_change_l`.
   - Amounts are rounded half-even with `round(Fraction)`: money to 2 dp, litres to 1 dp. The tests cover 1/3, 0.125, 0.135 and 0.25.
   - Every uncredited case gives no entry. The tests cover no total, negative, zero, not an improvement and INEFFECTIVE.
3. **Card (focus 3).**
   - `portfolio_cards` (`read.py:820-836`) lists lines in Site order (summary order), then each row's stored entry order, each as `card_text("assure.value_line", site=..., text=...)`.
   - `value_note` is `values_separate` exactly when lines exist; otherwise it is `MONEY_NOT_CREDITED`.
   - `card_notes` (`portfolio.py:658-665`) now gives the evidence-gap clause alone. `recovered()` and `cost_checks` are not in the diff.
4. **No sum (focus 4).**
   - No arithmetic across entries exists in `mini.py`, `read.py`, `board.py` or the frontend. The frontend renders server strings only, with no join.
   - The pairwise and full-total Decimal sums are absent from the card in `test_pv1_value_lines`, and from the composed rows in `test_mill_plus_trial_...`.
   - COH PV1 (ii) and PV-A each have a failing case for "21.12".
   - I did not re-run the packet's two mutation proofs. The tests they mutate exist and assert the right thing.
5. **Byte-equality (focus 5).**
   - Grow, Optimize and Protect are equal on both the row and the card (tests).
   - Cold and EV never set the field. `test_out_b3_cold_ev.py` passes unchanged.
   - The golden diff (`estate_week_2026-10-25.json`) is exactly `value_lines: []` plus the not-credited `value_note`.
   - No `ch5a1_board_contract` golden moved: they hold no VERIFIED mill, so the key is absent.
6. **Checks (focus 6).**
   - COH PV1 (`chain_coherence.py:1250-1285`) is wired after `coh17_optimize`. It has pass, fail (i), fail (ii), fail (iii) and skip self-tests.
   - PV-A asserts the mill value is PRICED, that the mill line equals the page's `per_day` (built from backend constants), that the trial line is present exactly when the trial is credited, and that no sum appears.
   - PV-A will bite at E3 on the mill. Its no-sum assertion is only non-vacuous in the "credited" trial case; see L3.
7. **Wording (focus 7).**
   - Both lines are plain and honest. The trial line says "modelled, not metered" and "one-hour trial". The mill line says "estimated sales" and "your declared price".
   - The mill line is a per-day figure, not an annualised one.
   - The MD-FUEL-PV1-1 comment cites v69 `:129` ("Verified value recovered" / "Not established"), `:131` ("no combined savings total") and `:482` ("lines with different bases are not added together"). I checked all three against the mock.
8. **Merge interaction (focus 8).**
   - `task/FUEL-MB1b-mill-thread-line` currently points at main `da51c7a8a` and has no commits, so there is no conflict yet.
   - A trial merge of HEAD with current main (`git merge-tree`) is clean. Main's 18 new files (K2 fuel records, migration 0054) are disjoint from PV-1.
   - Whichever of PV-1 and MB-1b merges second will conflict textually on the `SiteFacts` last field and on `_row` just before the `NOT_MEASURED` return. The ruling's rule (merge main first, put your own field last) resolves this mechanically. The `_row` insertions are independent `if` blocks, so their order does not matter.
9. **Postgres (focus 9).**
   - Deferring the three TEMPLATE_STALE `test_ch6b_estate_postgres` cases to E2 is acceptable. They test the estate Optimize card and summary, which PV-1 does not change except through `card_notes`.
   - `card_notes` is covered on Postgres by `test_w303_portfolio_api.py`, which I re-ran (below).
   - The real gap is narrower, and the packet does not name it. No Postgres test composes a board through the real `VerificationService.domain_summary` with a VERIFIED, priced mill. The binding test uses a fake `Verification` object. The real path (`site_outcomes/composition.py:59`, which uses the board's `actions.verification_ports.productive_price`) is first exercised end to end by PV-A at E3. That is acceptable under the demo-sprint test policy, because PV-A asserts PRICED and the line text and so fails loudly. It is listed under residual risk.

## Findings

### L1 (Low): the line order is by stored code string, which can read out of order next to the display codes
- Where: `backend/assetops_backend/site_outcomes/mini.py:1030`.
- What: entries are sorted by `(action_code or "", key)`. Mill codes are stored 6-digit (`ACT-000002`) and trial codes 3-digit (`ACT-001`), so the sort is lexicographic across mixed widths.
- Failure: in the demo, `"ACT-000002" < "ACT-001"`, so the card shows "Kobo · ACT-002: … estimated sales" above "Kobo · ACT-001: … less diesel". §3.3 says "Action display-code order".
- Context:
  - PV-1-R §3 explicitly chose this key ("the Assure contributors' order", `mini.py:1040-1042`), so the board's contributors and the card agree. This is not a ruling violation.
  - The frontend fixture (`portfolioFixtures.ts:479`) shows the opposite order (ACT-001 first) from what the backend would emit for the same data.
- Fix, if wanted: sort the value entries and the contributors by `(prefix, int(number))`. This is an Architect call because contributors share the key; it fits the W1 polish pass.

### L2 (Low): whitespace regression on an untouched line
- Where: `mini.py:554`. `suffix = "" if …` became `suffix ="" if …`.
- What: there is no behaviour change, but it is an unrelated diff hunk in a byte-sensitive file.
- Fix: restore the space.

### L3 (Low): PV-A's credited test hard-codes "VERIFIED", and its no-sum check is vacuous in the not-credited case
- Where: `tools/demo_combined_rows.py:330`, `got = credited(trial_cost_check, "VERIFIED")`.
- What: the board gates on the trial's real `verification_state == "VERIFIED"`, but PV-A assumes it.
- Failure: if ACT-001's outcome at E3 is not VERIFIED (for example INEFFECTIVE) while its stored cost check is MODELLED_IMPROVEMENT with a positive `priced_total`, PV-A expects a trial line the board correctly omits. That is a false fail, never a false pass.
- Second gap: in the not-credited case only one entry exists, so `sums_checked == 0`. The row reports it, but it is not flagged.
- Context: this follows PV-1-R §5 literally ("`credited(ACT-001's summary cost_check, \"VERIFIED\")`").
- Fix, if wanted: pass `(action.get("verification") or {}).get("outcome")` (or the state) in place of the literal, and surface `sums_checked == 0` as a note in the row output.

### L4 (Low, inherited): the trial line inherits a present-time verification read, not a cutoff read
- Where: `backend/assetops_backend/chain/read.py:405-417` (`action_facts`, which calls `VerificationService.summary`, which calls `current_state`). This file is not changed by PV-1.
- What: the trial's `verification_state` and `cost_check` are read as of now. Only the Action's existence is bounded by `k`.
- Failure: a Portfolio window that ends before ACT-001's verdict was recorded would still show the trial-fuel money line, along with the existing Assure verified count and the `VERIFIED_WITH_COST` text, which share the same source.
- Context: the mill line is correctly cutoff-bounded, so the two lines differ in how strictly they respect the cutoff. This is pre-existing behaviour and not PV-1's to fix.
- Action: name it in the packet's residual risk. If the demo only shows windows after the trial verdict, it is harmless for the demo.

Not findings, noted:
- `key={line}` (`PortfolioOutcomes.tsx:229`) would collide only for two identical server lines (same Site name and same code), which is not realistic.
- Board `nodes` can now hold a fourth key that is a list, `verified_values`. The `ch6` contract tests assert `set(nodes) == {kpi, earnings, potential}` only on goldens without a VERIFIED mill, and `test_ch6_nodes_postgres` checks only the Grow and Cold rows, so nothing breaks. A future reader that iterates `nodes.values()` as claims on an Assure row would trip on it. This shape was directed by the ruling.

## Checks I ran (revision `5789fdf47`)

- **Import resolution:** with the plan2 venv and an absolute worktree PYTHONPATH, `assetops_backend`, `tools/checks/chain_coherence.py` and `tools/demo_combined_rows.py` all resolve into `AssetOpsV1-pv1`.
- **Backend L0, no DB:** `test_pv1_value_lines`, `test_out_b2_vocabulary`, `test_ch6b2_portfolio_cards`, `test_out_b4_imports`, `test_out_b2_mini`, `test_out_b3_cold_ev`, `test_demo_combined_finish_rows`, `test_mb1_opportunity_board`, `test_w303_portfolio_api`, `test_ch5a2_contract`, `test_ch5a1_board_contract`, `test_ch6_contract`, `test_ch9b3_mill_verdict` and `tools/checks/test_chain_coherence.py`. Result: **436 passed, 1 skipped** (the w303 DB case without a URL), 28.7 s.
- **Postgres (`assetops_pv1_test` only; 4.33 GB and then 4.12 GB free before the runs):** `test_w303_portfolio_api.py` gave **7 passed**, 31.6 s. This covers the `card_notes` change on a real DB.
  - I did not re-run the packet's 7-file, 372 s DB batch. I cite it: 28 passed and 3 TEMPLATE_STALE setup errors, on `5b0b06c96`, the same code as the revision under review.
- **Frontend:**
  - `npx.cmd vitest run src/estate/__tests__/estatePortfolio.test.tsx` gave **63 passed**. It ran in this session.
  - `npx.cmd tsc --noEmit` exited 0.
- **Guards:**
  - `tools/check-agent-workflow.ps1` passed.
  - `tools/check-architecture.ps1` first failed on the environment ("chain structure guard cannot run: no Python interpreter"; the worktree has no `.venv`). With `ASSETOPS_GUARD_PYTHON` set to the plan2 venv it **passed**.
  - That first run also printed two "Rule 8 … EV consequence insert-only check is vacuous" notes about a file PV-1 does not touch. They are pre-existing.
- **Not run (per brief):** the full suite, prepare, baseline build, `test_demo_combined_postgres`, the PV-A row itself (E3), and layout evidence. The card adds text lines with an existing class.
  - Rendered layout is unverified. The packet records it as not run, not as a pass.

## Residual risk not named in the packet

- No Postgres test reads a board whose mill is VERIFIED and priced through the real `domain_summary`. The first end-to-end proof of the binding and the price port is PV-A at E3.
- The trial line, the verified count and the `VERIFIED_WITH_COST` text use present-time verification state (L4).
- At E3, the PV-A trial case depends on ACT-001's real outcome (L3).
