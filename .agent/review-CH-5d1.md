# Review CH-5d1: the Portfolio Optimize card (first review, Opus)

- Branch `task/CH-5d1-optimize-card`, reviewed at `b156c4740` (build `151580feb`), diff `1428e3a8c...HEAD`.
- Spec: CH5d1-R (`.agent/build-sheet-CH-5d.md` §51-161). Packet: `.agent/review-packet-CH-5d1.md`.
- Reviewer: fresh Claude (Opus), not the author. No code edited.

## Verdict: ACCEPT

There are no High or Medium findings. The two Low findings and the residual notes below can be fixed later or left; none of them blocks the merge.

## What I checked against the ruling

1. **One builder, 0/1/2+ paths, no sum** (`backend/assetops_backend/site_outcomes/read.py:746-776`).
   - `_cost_claim` reads only `rows[OPTIMIZE_COST].nodes.earnings`. A failed board (`_unknown_row`, nodes None) gives None, so it is never priced. Nothing reads `value_cards`, financials or coverage.
   - 0 priced: "Not known yet", neutral, claim None.
   - 1 priced: `value.text` is `claim["text"]` (the same object, so byte-equal), and `claim` is the node claim unchanged.
   - 2+ priced: "Costs at N sites", with one `"{site}: {text} {small}"` line per Site, joined by " · ", and claim None.
   - There is no Decimal arithmetic anywhere. Every field matches the 2.1 table and the 2.2 texts verbatim.
   - The days line goes through `_site_days` over priced Sites only, so it is None for a stored consequence.
   - An unknown label raises KeyError (`:759`).
   - `portfolio_cards` order is Grow, Optimize, Protect, Assure. The signature is unchanged. The Grow, Protect and Assure branches are untouched.
2. **Card and "Why?" share one source.** The card reads the same summary Site row (`nodes.earnings`) that V4 ties to the board. The estate "Why?" explains each Site's board Optimize row, and `_estate_why` is unchanged. Packet M2 records both on the L3m DB.
3. **COH-17 O1** (`tools/checks/chain_coherence.py:1206-1238`).
   - It is correct for the ruled cases: absent card, 0, 1 and 2+.
   - It is non-vacuous. It has 9 direct parametrised cases (pass and fail) and two planted bundle breaks. The `_optimize_other` break changes the card on both the summary and the chain, so C3 still agrees and only O1 can catch it, which is the right design.
   - The packet also reports a forced `return []` mutation that turned 8 self-tests red. I did not repeat that mutation.
4. **Client wording and MD-CH5d-1.** The words are plain. The MOCK DEVIATION label is on `COST_SMALL` and on the new `CARD_TEXT` keys (`vocabulary.py:296-298`, `:521-524`), and in the packet.
   - **KD-2 is justified and strengthens the guard.** Every `CARD_TEXT` template is `.format(**card)`-ed in `test_out_b2_vocabulary.py`, so the new `cost.site` key needs a `small` sample or the guard itself raises. Adding `COST_SMALL.values()` puts more copy under the banned-word scan, not less.
   - The frontend edit is also a strengthening. The w1 scan in `estatePortfolio.test.tsx` no longer removes the Optimize detail before scanning.
5. **Frontend** (`frontend/src/estate/PortfolioOutcomes.tsx:86-104`).
   - Optimize takes the generic server-card path, with `note` held at null. It renders `{text} <small>{small}</small>`. If the summary is missing it shows "Not known yet", the same as the other cards.
   - `cardValue`, `OPTIMIZE_COST_MISSING` and `CARD_VALUE` have no remaining importers (grep over `frontend/src`). KD-3 is fine.
   - `amountOf` is kept. The `/financials` destination is unchanged.
6. **The A3 / Kisiwa lanes (KD-5).**
   - After A3, Kobo's claim is a stored consequence with a value and no days. Its text is the amount alone, so the card reads "<amount> USD possible extra fuel cost", amber, "At Kobo · not added across sites", with no days line. That is correct.
   - Kisiwa is a mini-grid Site (DIESEL-1), so its Optimize row maps through MG-2 to the same `money.possible_extra_fuel_cost` label. `COST_SMALL` covers it and the KeyError path is not hit.
   - The 2+ path gives "Costs at 2 sites" plus the two per-Site lines, with no total. The L0 test pins all of this, including that no form of the Decimal sum appears anywhere.

## Findings

**L1 (Low, a gap in the guard, not in acceptance): O1 does not catch a summed value on the 2+ path.**
- Where: `tools/checks/chain_coherence.py:1229-1234`.
- The problem: for two or more priced Sites, O1 checks only that each Site name prefixes a detail line and that `claim is None`. It never looks at `value.text`.
- Failure scenario: a later edit makes the ≥2 card show a total, e.g. `value.text = "4.51 USD"`, while the per-Site detail lines and `claim: None` stay. O1 then passes on a real bundle, and the never-summed rule (design A6, D-AW-5) is guarded only by the L0 test. The ruling's own O1 text does not ask for this check, so it is not an acceptance gap.
- Fix: in the ≥2 branch, also require `value.text == card_text("cost.sites", sites=sites_text(n))`, or at least that `value` carries no amount. Add one self-test fail case.

**L2 (Low, an unrun test, owed): the L2m test is committed but never run (KD-1).**
- Where: `backend/tests/test_ch6b_estate_postgres.py:217-249`.
- I reproduced the refusal myself on `assetops_ch5d1_test`: `TEMPLATE_STALE: template inputs abc647639e60 != this checkout 6780e1498733`. The test imports and collects cleanly.
- I do not judge this as blocking. Its three assertions were measured on the fuller L3m DB:
  - card == `_optimize_card(summary.sites)` and the key order (M2);
  - chain `cards` == summary `cards` (M2);
  - the Kobo row nodes == the board's (M1/M2);
  - the S2 byte check showed 0 other differences.
- The logic paths are pinned by the L0 tests and the O1 self-tests. On this data the test would exercise only the none path anyway (KD-5).
- Failure scenario if it stays unrun: a harness-level mistake in the test, such as a wrong window or helper, surfaces only at the next states-template rebuild and turns that run red. That is a nuisance, not a product defect.
- What closes it, on this branch, and only when that rebuild is authorised:
  1. Build the states template: `python tools/mechanism_dataset.py build --variant states --budget 540`.
  2. Then run `pytest backend/tests/test_ch6b_estate_postgres.py -k optimize_card -q` with `ASSETOPS_TEST_DATABASE_URL` on `assetops_ch5d1_test`.
- An alternative is to run it on main's next template after the merge.

## Residual risks (not findings)

- **One cost label away from a full outage.** An Optimize cost label missing from `COST_SMALL` raises inside `portfolio_cards` (`read.py:759`). That fails the whole outcome summary and `/api/estate/chain`, not just the card. The ruling chose this on purpose (fail loud). A new cost-label lane must add its `COST_SMALL` entry in the same slice. Kisiwa does not need one, since it uses the MG-2 label.
- **The L2m test assumes the week claim equals the S-day claim.** It asserts `claim == d13_claim` (`test_ch6b_estate_postgres.py:246`). That holds only while the window's claim is a single stored consequence, or NOT_KNOWN. If the mechanism data ever gains priced consequences on several days, the week claim and the S-day claim may legitimately differ, and the assertion would go red without a product fault.
- **No wording exists for a claim that has days.** If a cost claim ever carries days, its text becomes "X USD over k of m days checked". The ≥2 line would then read "Kobo: X USD over k of m days checked possible extra fuel cost", and the 1-Site card would repeat the days in both the value and the days line. No current label reaches this (`avoided_cost@1` over a stored consequence has no days).
- **No 2+ frontend test.** No frontend test renders the 2+ card. The render path is the generic one, and the detail is plain text that wraps. The detail can grow long with two Site names; the E3 captures (KIS-6) should look at it.

## Checks I ran (worktree, `assetops_backend` resolved to `AssetOpsV1-ch5d1\backend`)

- Free RAM 3.90 GB before the Postgres run.
- `pytest backend/tests/test_ch5d1_optimize_card.py backend/tests/test_ch6b2_portfolio_cards.py backend/tests/test_out_b2_vocabulary.py tools/checks/test_chain_coherence.py -q`: **216 passed**, 19.2 s.
- `pytest backend/tests/test_ch6b_estate_postgres.py -k optimize_card` with the URL unset: collected, 1 skipped (imports clean). With the URL on `assetops_ch5d1_test`: **1 error, TEMPLATE_STALE** (KD-1 confirmed).
- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run` on `estatePortfolio.test.tsx` and `estateFinancials.test.tsx`: 72 passed.
  - On `blocks/__tests__/evidenceTrace.test.tsx`, `estateRoots.test.tsx` and `estateEvidence.test.tsx`: 53 passed.
  - Vitest did run in this environment.
- `node tools/checks/frontend-hardwiring.mjs`: passed, with totals unchanged (api 12, href 24, lit 70, cmp 51, code 3).
- `node tools/checks/missing-claim-scan.mjs`: passed (42 tagged uses, 10 baselined).
- `tools/check-architecture.ps1`: **passed**.
  - The first run failed only because no guard interpreter was set: the worktree has no `.venv`, so Rule 8 and the chain-structure guard could not run.
  - Rerun with `ASSETOPS_GUARD_PYTHON` pointing at the plan2 venv: `Architecture check passed`.
  - The worktree has no `.venv`, which is an environment fact, not a finding about this branch.

## Not verified by me

- I did not rerun the packet's stored == fresh probe, the S2 byte check, the M1/M2 reads on `assetops_mechanism_test`, or `test_ch5c_response_store_postgres.py`. That DB is outside my allowed set.
- I did not run the Postgres portfolio files (`test_w303_*_postgres`). The packet reports 24 passed.
- No full suite, production build or layout evidence was run. The change is copy on an existing card with no CSS change, so layout evidence is not owed by the ruling.
