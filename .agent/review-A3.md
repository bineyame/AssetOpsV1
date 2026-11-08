# Review: FUEL-1 A3, idle fuel on Kobo's screens and story

- Reviewer: fresh Claude (Opus), independent first review. I did not write or edit any of this slice.
- Branch `task/FUEL-A3-kobo-idle-fuel`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-a3`, HEAD `c728eb8a1`. Diff `git diff main...HEAD`: 21 files.
- Judged against `.agent/build-sheet-FUEL-1.md` A3-R and A3-R2, the packet `.agent/review-packet-A3.md`, and the owner's decision `owner-fuel-scope-2026-11-07.md` (on plan2 main).

## Verdict: FIX (one Medium, fixed on the branch; the rest are Low)

The build is faithful to A3-R. Every literal matches the card verbatim. All four gates are exact, and the tests for them fail when the gate is removed. I re-ran four of those mutations myself. G4(b) leaves `basis_sha256` unchanged, no golden file changed, and O16 matches A3-R2 D3.

One finish row, `never_summed`, cannot catch the failure it was written to catch, so a sum of idle mornings could appear on screen and the row would still pass. The fix is about five lines plus one self-test.

## Findings

### M1 (Medium): `never_summed` sums the rounded-up shown amounts, not the exact stored amounts, and its inputs never hold two mornings

- **Where:** `tools/demo_combined_finish.py:563-572` (`money_b`, which passes `m["shown_high"]`), and `tools/demo_combined_rows.py:705-728` (`never_summed`).
- **What is wrong:**
  - A3-R §3.9 asks for "the exact Decimal sum of two mornings' amounts". The row instead sums the displayed `headline_money.amount_high`, which is 15.13 after outward rounding (`ROUND_CEILING`, `financials/consequence_read.py:76`). So it searches for "30.26" and "45.39".
  - Code that summed the mornings would sum the stored amounts. 2 × 15.125 = 30.25, and 3 × 15.125 = 45.375, which shows as "45.38" under both ceiling and half-even rounding. The row searches for neither of those strings.
  - The inputs are also vacuous. The S week summary (S-6 to S+1) contains only the S morning, because S-7 (30 Oct) falls outside it. Each of the three day boards D6 added contains one morning. No body the row reads can contain a sum of two mornings.
- **Failure scenario:** a later change (for example a period Optimize card, or a Portfolio line that adds Kobo's daily `amount_high`) shows "30.25 USD" or "45.38 USD" as a combined idle-fuel cost. MONEY-B still passes. The "no combined total" rule for the idle mornings is then enforced by nothing.
- **Fix:**
  - Pass the stored `amount_high` values (`m["amount_high"]`) as well as the shown ones.
  - Format each sum both as half-even and as ceiling to two places, and search for every resulting string.
  - Add a body that spans the mornings, such as `/api/estate/outcome-summary` from S-14 to S+1, or say in the packet why no such body exists.
  - Extend `test_a3_never_summed_and_steady_day` with a FAIL case whose body holds "30.25".
- **Kind:** acceptance gap against A3-R §3.9 (the word "exact"), and test strength. It is not a preference.

### L1 (Low): mixed rounding on the S board at E3. It is defensible, but put it in front of the owner

- **Where:** `consequence_read.display` (outward rounding, so 15.125 shows as 15.13) and `chain/vocabulary.money_text` (half-even, so 4.125 shows as 4.12; `test_helpers` pins this).
- **My judgement:**
  - Each rule is right for its own line. 15.13 is the upper end of a range ("0.00 to 15.13"), and rounding an upper bound outward is the project-wide honest convention: it never understates the "up to". 4.12 is a point estimate ("about"), shown with PV-1's half-even rule as A3-R Q5 directs.
  - They sit in the same Optimize row on S. At E3 the S board carries both the idle headline and the trial's earlier-item line (the scratch read the trial line on the 6, 7 and 8 Nov boards).
  - A CFO checking 3.3 × 1.25 = 4.125 and seeing 4.12 may read it as truncation, since finance users expect half-up (4.13). Checking 12.1 × 1.25 = 15.125 and seeing 15.13 looks consistent.
- **Recommendation:** not a merge blocker, because both rules are existing, approved helpers. Add it to the post-W6 walkthrough list, with the option to show trial point money half-up (this would also change PV-1's value line; that is an Architect decision). Do not change it inside A3.

### L2 (Low, spec-level): the idle line's litres do not reproduce from the rate shown beside them

- `COST_IDLE` reads "generator on for 200 minutes … up to about 12.1 L · counted at a generic idle fuel rate of 3.3 L/h". But 200 min × 3.3 L/h = 11.0 L; 12.1 is the upper bound after the stored 1.10 multiplier, which the line never mentions.
- The trial line uses the nominal figure: 1 h × 3.3 = "about 3.3 L".
- So the same rate gives 3.3 L per hour on one line and 3.63 L per hour on the other. "Up to" hints at a bound, and "Why?" says "0–12.1 L × 1.25 USD/L" without explaining it either.
- The literal is A3-R's own, verbatim, so this is not the builder's error. Note it for the walkthrough.

### L3 (Low, cross-lane): CH5D1-O1 asserts exactly one priced Site

- **Where:** `tools/demo_combined_rows.py:768-782`, `assert [code for code, _ in priced] == [site]`.
- **Risk:** if the Kisiwa diesel lane (FUEL-1 §5.5, KIS-6, "≥2 priced Sites") merges before E3 and Kisiwa is priced on S's summary, this row fails at E3.
- This matches A3-R's wording ("the one priced Site"). Whichever lane merges second should reconcile CH5D1-O1 with KIS-6.

### L4 (Low, evidence): the §6 peak working set was not sampled, and parts of the packet are stale

- A3-R §6 asks for the prepare's peak working set to be recorded. The packet says it was not sampled, so the estimate of 1.5–2.5 GB is still unmeasured going into E3.
- Several packet passages are out of date:
  - "§7 stops: none hit so far. S-c and S-f can only be judged at §6";
  - the residual-risk line "unproven until §6";
  - the original D3 and D4 texts, which remain beside their closed versions.
- Packet hygiene only.

## The nine focus points

1. **Literals.**
   - I compared each literal by script against the A3-R text: `NO_LOAD_BASIS_WORDS`, `FUEL_VALUE_PAGE`, `why.from.fuel_idle_example`, `COST_IDLE`, `VERIFIED_WITH_FUEL` and `COST_PRICED` are all byte-equal.
   - Guard V (`test_out_b2_vocabulary.py`) scans all four new lines with every basis word, and it passes.
   - The labels MD-FUEL-A3-1 to -4 are present: `vocabulary.py:113` and `:199`, `mini.py:70` and `:108`, `board.py:62`, `SiteActionVerification.tsx:392`. `mock-deviation-labels.mjs` returns OK.
   - The rendered scratch lines match the brief: "0.00 to 15.13 USD" with the `COST_IDLE` text, and "about 3.3 L less diesel in the trial hour, 4.12 USD at 1.25 USD per litre".
2. **Gates.**
   - `COST_IDLE` uses an exact `Fraction(high_exact) == Fraction(mult) × Fraction(idle, 3600) × Fraction(rate)`, with the multiplier read from the stored model (`chain/outcomes.py:300-305`). It applies only when `priced and not zero` (`mini.py:517-519`). Mixed, fuel-cost-1 and zero rows keep their existing lines.
   - The "Why?" line is gated on `idle_seconds` and on `source_class in EXAMPLE_SOURCES` (`why.py:126`). `fuel_basis` sets `source_class` to None outside the example sources.
   - `fuel_value` is gated on `outcome == "VERIFIED"`, a stored `priced_total` and a shown price (`verification.py:1170-1184`). `priced_total` is stored only when the amount is above 0 (`trial_fuel_comparison.py:201`), so no negative line can appear.
   - `price_per_litre` is added only with `priced_total` (`verification.py:1232`), and the test pins the `/1` key set.
3. **G4(b).** `no_load` gains `basis` (`trial_fuel_comparison.py:245-246`). The digest input `basis` (`:221-231`) is unchanged, and the `test_tfc2` digest-equality test proves it. The L2 tests `TestNoLoadBasisRead` pass on `assetops_a3_test`.
4. **No golden changed.** The diff touches no golden file and does not touch `k0_byte_equal_pins.py`. The K0 pins and both contract tests pass on HEAD. I did not rerun the "before" side; the packet records it at `0c4aa7310`, and no file that could move a pin is in the diff.
5. **O16.**
   - `fuel_rows_ok` matches A3-R2 D3: it keeps the story-day and steady-day rules, requires at least one row for S-14 and S-7, and requires every such row to be PRICED with low 0 and high above 0. It holds no exact figures, and its docstring is verbatim.
   - The self-tests include the old priced-at-0 shape as a FAIL case.
   - D4's `steady_day` is right: every stored head row has no idle seconds, the headline is not the idle form, and the absence of rows is left to O16.
6. **Rounding.** See L1. It is acceptable for the merge and belongs on the walkthrough list.
7. **Scratch prepare.**
   - The stored rows (12000 s, 121/10, 15.125, 1.25), the trial figures (`/2`, 3.3, 4.125, 1.25, GENERIC_DEFAULT) and O16 (11 rows, pass) all match the expected values.
   - **MONEY-B at S, WK-2a and CH5D1-O1: I judge this a scratch artifact, with high but not certain confidence.**
     - A Kobo-only prepare skips `after_children` (backfill, mill and `drain-1`) and `drain-2`, and runs only two ticks (`tools/demo_combined.py:487-552`). So late-window producer work can stay unsettled.
     - `ChainRequest.money_head` sets `priced` only when `settled` is true (`chain/read.py:436-437`), and the outcome reason seen was `PRODUCER_NOT_SETTLED`. That explains "No fuel cost estimated" on S while the stored S row is correct, and why S-1 also reads "No readings".
     - S-10 (27 Oct) is a ruled "missing" day, so that gap is by design.
   - **E3 must explicitly re-read these, and record the values rather than just "pass":**
     - MONEY-B at S, which also runs `never_summed` for the first time on real data; it never executed in the scratch;
     - WK-2a's 42.08;
     - CH5D1-O1;
     - A3-PAGE.
     A full prepare's self-check fails hard on these rows, but the packet should record their values from `check.json`. If S still reads unsettled after both drains, that is a real data finding, not a scratch artifact, and it must not be waived.
8. **Test strength.** I ran these mutations myself, each on a scratch copy of the package, with imports confirmed to resolve to the scratch copy:
   - `idle_only` changed from `==` to `>=`: 2 tests FAIL.
   - The `EXAMPLE_SOURCES` gate dropped: 1 test FAILs.
   - The VERIFIED check in `_fuel_value` dropped: 1 test FAILs.
   - O16's `hi > 0` changed to `== 0`: FAIL. Changed to `>= 0`: FAIL.
   - The weak spot is `never_summed` (M1).
9. **Regression.**
   - Cold and EV: `test_out_b3_cold_ev.py` passes unchanged. A cost check is never present there, so `_assure` and `cost_line` keep their existing branches.
   - PV-1: the line is byte-equal through `trial_litres`, and `test_pv1_value_lines.py` passes.
   - Portfolio: `headline_money` is unchanged. CH5D1-O1 now expects a priced Kobo card (see L3).
   - Other Kobo rows: O16 holds that fuel rows exist only on story days, and steady days stay "No fuel cost estimated".
   - Redundancy: the trial's 4.12 USD appears on Assure twice (the `VERIFIED_WITH_FUEL` contributor and the PV-1 value line), on the Optimize earlier item and on the verification page, worded slightly differently each time. It is never summed and is approved by the card. Mention it at the walkthrough.

## Checks I ran (HEAD `c728eb8a1`)

- Imports resolve into the a3 worktree (`assetops_backend`, `demo_combined_rows`, `demo_combined_after`).
- **No-DB focused and adjacent tests: 549 passed, 2 skipped, 40.8 s.** Files: `test_a3_idle_fuel`, `test_tfc2`, `test_demo_combined_finish_rows`, `test_out_b2_vocabulary`, `test_out_b2_mini`, `test_out_b3_cold_ev`, `test_ch3_rows`, `test_pv1_value_lines`, `test_out_e4_readback`, `test_ch5a2_contract`, `test_out_e2_trial_comparison`, `tools/checks/test_chain_coherence`, `host/tests/test_k0_kisiwa_actions`, `test_scenario_execution_contract` and `test_execution_contract_alignment`. The 2 skips are the K0 DB cases (no URL set).
- **Postgres:** with 2.85 GB RAM free, `test_fuel_cost_v2_postgres.py` on base `assetops_a3_test`: **10 passed, 73.5 s**.
- **Frontend:** `npx.cmd tsc --noEmit` exit 0. `npx.cmd vitest run src/sites/__tests__/siteActionVerification.test.tsx`: **34 passed**. Vitest did run here; it was not blocked by the sandbox.
- **Guards:** `node tools/checks/mock-deviation-labels.mjs` OK. `node tools/checks/frontend-hardwiring.mjs` passed with totals unchanged (`api 12, href 24, lit 70, cmp 51, code 3`).
- **Not run:** the PowerShell guard suite (`check-all.ps1`, architecture and agent workflow), because the dispatch forbids passing `-ExecutionPolicy`; I cite the packet's 17/17 on `58b09582c`. Also not run: the full suites, any prepare, the full frontend suite and the build. Layout evidence is not applicable: one server-text paragraph, no CSS.
