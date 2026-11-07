# Review MB-1a: the mill in the Kobo Assure row and the verified count

- Reviewer: fresh Claude (Opus), independent of the builder. Branch `task/FUEL-MB1-mill-on-board`, head `f7fa95a06`;
  `main` = merge-base = `a2d48104a`, so `git diff main...HEAD` is the whole slice.
- Judged against: build sheet FUEL-1 MB-1-R §1 (Q1-Q6), §2 (MB-1a card), MB-1a-R2 §1-§4; packet `.agent/review-packet-MB-1a.md`.

## Verdict: ACCEPT

No High or Medium finding. The four Low items below are either ruled behaviour (recorded as residual risk for the
Architect) or test-depth notes; none needs a fix round.

## What I checked, and what I saw

1. **Verdict read.**
   - `postgres_chain_read.py:87-96`: the LEFT JOIN LATERAL is the ruled SQL verbatim (DOMAIN_INTENT only, `ORDER BY
     o.recorded_at, o.id LIMIT 1`, no `k` in the SQL). MINI_TRIAL rows get NULLs (L2 asserts it).
   - `site_chain.opportunity_actions` (`site_chain.py:155-180`): `accepted_at < hi`, `accepted_at <= cutoff`,
     opportunity occurrence meeting `[lo, hi)`, and the outcome masked to None unless `outcome_recorded_at <= cutoff`
     (D1: `outcome_recorded_at` masked too). All keys are read with `.get`.
   - One rule: `claims.verified_actions` (`claims.py:91-97`) and `mini.compose` (`mini.py:428-433`) both call
     `opportunity_actions`; the claim with the estate `[lo, hi)` at `lifecycle_cutoff(k)`, the board with
     `[work_lo, end)` at `k`, as Q5 rules.
   - `chain_threads` reads `ChainRequest.threads(sid)`, which is `read_scope.memo("chain.threads", ..., k)`
     (`chain/read.py:371-373`), so it is shared with the claim's read whenever the request `k` is equal. The policy is
     injected (`composition.py:83-84`, the function not its value); `read.py` no longer imports `chain.composition`
     (OUT-B4 guard passes).
2. **Assure row.**
   - Headline `verified` adds the VERIFIED opportunity Actions (`mini.py:492-493`); `_verified_results` uses the same
     expression on `comp.facts` (`read.py:512-513`), and the D6 board-service test proves equality through the real
     `SiteOutcomeBoardService.board` path.
   - The mill entry's `link_ref` is the DOMAIN_VERDICT Ref (`refs.py:119` gives `/domain-actions/{id}/verification`;
     the frontend already routes DOMAIN_VERDICT, `operatorSiteRoutes.ts:593`).
   - Before the verdict: `VERIFICATION_TEXT["PENDING"]` ("ACT-… not yet verified") with `PENDING_CHIP`, and the
     headline excludes it.
   - Q4 window: `hi=end` (the board day's end) and `cutoff=ct.k`, so an Action accepted on or after the end of the
     board day is not listed.
3. **COH.**
   - L3 (`chain_coherence.py:1341-1349`) = distinct Verified Finding threads + Σ `threads.verified_actions` (absent = 0).
     Pass, must-fail (`verified_actions` 0) and legacy cases present.
   - A1 (`chain_coherence.py:1238-1255`) is board-internal: headline number vs verified `verified_results` entries,
     mini only, cold board skipped.
   - D4 (no Assure row → `tally["skipped"]`) is counted, not silent.
   - D5: the exclusion is exact equality with `NO_VERIFIED`. The builder's must-fail ("2 verified results" + one verified
     entry + `NO_VERIFIED`) fails only *because* the entry is excluded; if someone dropped the exclusion, listed would be
     2 and the test would go green → the test would catch it. The ruled shape ("1 verified result" + one entry +
     `NO_VERIFIED`) passes with the exclusion and could not have been a must-fail; the builder asserts it passes. The
     builder's version matches the ruling's intent (prove the exclusion is load-bearing and cannot pad the count).
4. **S-d and the cap.** `composition.py` import + one keyword; `test_composition_injects_the_thread_policy` pins it;
   `test_ch9b1_origin_readers.py:42` is the one ruled line (cap 8, "both").
5. **Cold / EV / golden.** `cold.py` and `ev.py` untouched; `test_out_b3_cold_ev.py` and the `test_ch5a1_board_contract`
   goldens pass unchanged. `git diff main HEAD -- backend/tests/fixtures` touches only `estate_week_2026-10-25.json`:
   three `"verified_actions": 0` additions inside `sites[].threads`, nothing else.
6. **Mock deviation and wording.** `MOCK DEVIATION MD-FUEL-MB1-1` is at `mini.py:996-998` with a packet row. No new
   client literal: the mill line reuses `VERIFICATION_TEXT` ("ACT-000002 verified"), which is plain.
7. **Do the tests bite?** Yes for each rule I traced: the truth table has one row per exclusion (accepted == hi,
   accepted > cutoff, no opportunity occurrence, Finding-origin, MINI_TRIAL, no thread) and the outcome masking;
   the compose tests compute expected text from constants; the D6 test asserts `_verified_results == shown >= 1`, so
   dropping the mill from `read.py` fails it; the L2 test runs on real rows and checks the stored `recorded_at`, the
   cutoff mask and `verified_actions == 1`. MILL-5's self-test has one failing body per assertion.
8. **Regression.** Grow/Optimize/Protect byte-equality test passes; `test_ch6b2_portfolio_cards`, `test_ch5a2_contract`,
   `test_ch5a2b_claims`, `test_demo_combined_ex1` pass. EX-1 compares before/after on the same build, so the new
   Kobo headline does not trip it. No stored client-facing copy of "1 verified result" for Kobo outside the test files
   updated here.
9. **Empty heredoc.** The fix-round commit `f7fa95a06` has a subject-only message (no body describing the R2 changes).
   Noted, not blocking.

## Findings

### Low

- **L1. A failed trial read is hidden when a mill is listed** - `backend/assetops_backend/site_outcomes/mini.py:1003-1006`.
  `if actions_failed and not merged` drops the "Verified results: not available" entry as soon as a mill exists.
  Scenario: `action_rows`/`action_facts` fail on the S+0 Kobo board while `chain_threads` succeeds; the Assure row reads
  "1 verified result" with only the mill entry and no sign that the trial (ACT-001) could not be read. The board is
  PARTIAL, so it is not a silent wrong claim, but the row itself under-reports. This is the ruled code (MB-1-R §2.3
  verbatim), so it is a note for the Architect, not a fix-round item. A fix would keep the not-available entry whenever
  `actions_failed`, alongside any mill.
- **L2. Board and claim can diverge on a mill that shares a counted Finding thread** -
  `backend/assetops_backend/chain/claims.py:97` vs `mini.py:492-493`. The claim drops a verified mill whose thread is a
  counted Finding thread even when that thread is not itself Verified, while the board headline counts it. Scenario: a
  mill linked to a Finding thread that is OPEN/RECURRED → board "1 verified result", claim 0, COH L2 fires. It is not
  reachable in the demo (the mill thread is opportunity-only) and the "counted once" rule is ruled (R3). Residual risk
  only.
- **L3. A1's `" not yet verified"` exclusion is redundant** - `tools/checks/chain_coherence.py:1252` (same in
  `tools/demo_combined_rows.py:638`). `re.fullmatch(r"\S+ verified\b.*", "ACT-003 not yet verified")` cannot match, so
  the clause never acts and no test can show it is load-bearing. Harmless; preference only.
- **L4. Boundary cases not pinned** - `backend/tests/test_mb1_opportunity_board.py`. There is no case for
  `accepted_at == cutoff` (included) or `outcome_recorded_at == cutoff` at board level (the pure test covers the latter
  via `cutoff=VERDICT_AT`). A `>` → `>=` slip on the accepted cutoff would pass the suite. Low; add one parametrised row
  if MB-1b touches this file.

## Checks run (this review)

- Imports resolve into the worktree (`mini.py`, `tools/checks/chain_coherence.py`, `tools/demo_combined_rows.py`,
  `backend/tests/test_out_b2_mini.py` all under `AssetOpsV1-mb1`).
- L0: `test_mb1_opportunity_board`, `test_out_b2_mini`, `test_out_b3_cold_ev`, `test_ch5a2_contract`,
  `test_ch5a1_board_contract`, `test_ch5a2b_claims`, `test_ch6b2_portfolio_cards`, `test_demo_combined_ex1`,
  `test_demo_combined_finish_rows`, `test_ch9b1_origin_readers`, `test_out_b4_imports`, `test_out_d2_objectives`,
  `test_ch9b3_mill_verdict`, `test_dd1b2b_action_ref`, `tools/checks/test_chain_coherence.py`: **471 passed** (40 s).
  `test_ch5a1_summary_ledger`, `test_ch6_contract`, `test_ch4_opportunities`: **29 passed**.
- L2 `test_mb1_site_actions_postgres.py` on `assetops_mb1_test` (free RAM 3.7 GB): **1 passed** (26 s).
- `tools/check-agent-workflow.ps1`: passed.
- `tools/check-architecture.ps1`: first run failed only because the guard found no Python (`ASSETOPS_GUARD_PYTHON`
  unset; Rule 8 and chain-structure refuse to skip). Rerun with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv:
  **Architecture check passed**.
- Not run (as instructed): full suite, prepare, `test_demo_combined_postgres`, the TEMPLATE_STALE mechanism tests,
  frontend (untouched by this slice).

## Residual risk not in the packet

- L1 and L2 above.
- E3 is the first whole-story proof (MILL-5, COH L2/L3/A1); nothing in this review proves the live S+0 board, as the
  packet says.
