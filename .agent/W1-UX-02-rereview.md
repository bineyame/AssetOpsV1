# W1-UX-02 re-review - fix round 1

Reviewer: fresh independent Claude reviewer (did not author the slice or the fix). Revision: `77ceba1d` (detached, worktree `AssetOpsV1-review5`). Diff: `git diff 68b61dae..77ceba1d` (8 files, +78/-13; frontend, evidence script, packet). Inputs: `.agent/W1-UX-02-review.md` (RETURN: M1, L1-L6), packet "Fix round 1".

## Verdict: ACCEPT

M1 is closed and proven by a test that fails when either half of the fix is reverted. L1, L2 and L3 are fixed. L5 is cleaned up. No new fail-open path and no weakened assertion. Two new Lows below; neither blocks.

## Checks run (from `frontend/`, PowerShell)

- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run src/sites/__tests__/siteFinancials.test.tsx src/shell/__tests__/s5SiteWindowOverview.test.tsx`: 2 files, 115/115 passed.
- Vocabulary tests `t028Vocabulary`, `findingLinkWordsParity`, `productStatus`, `sharedVisualVocabulary`, `w1Vocabulary`: 5 files, 63/63 passed.
- Planted reverts (each restored with `git checkout`, tree clean afterwards):
  - M1 headline back to `"Diesel price in use: "` unconditionally: "an earlier recorded moment" test fails (`expected 'Diesel price in use: 1.25 USD per lit...' not to match /in use/i`).
  - M1 strip `stateOf` back to `"in-use"` unconditionally: the same test fails.
  - L2 `consequencesLoading={false}`: the new loading test fails.
  - L3 `const w = overviewMoneyWords(m.state)`: both new `it.each` cases (`amount_low`, `amount_high`) fail on the "Current amount" check.
- Not run: full `npm.cmd test`, `npm.cmd run build`, `tools/w1-ux-02-evidence.mjs`. I cite the implementer's full run (74/74 files, 1843/1843, 128 s) as stated in the packet; I did not verify it. The Financials/Assumptions 1440/390 re-capture is recorded `not run` (no Postgres); accepted per dispatch because W1-UX-06 reruns every capture.

## Findings checked

- **M1 closed.** `SiteFinancials.tsx:413`: historical headline is "Diesel price covering today, as recorded then: <price>"; `:179` the strip's selected entry becomes `recorded-then` ("Covered today, as recorded then"). Default view unchanged: `:413` keeps "Diesel price in use: ", `PriceInUse` passes `historical={false}` (`:692`), and existing assertions at `siteFinancials.test.tsx:1325` ("In use today") and `:1337` ("Diesel price in use: 1.25 USD per litre") still pass. The remaining "in use" in the historical state sentence (`:372`, "may not be the price in use now") is a hedge, not a claim; scoping the new assertion to headline and strip is correct.
- **L2 fixed.** `FindingConsequence.tsx:589-591`: a shown (PRICED, CURRENT) bridge returns a loading line while `consequences === null`; no amount, no untimed bound. Non-shown states are unaffected (they draw no amount). If the consequences read is refused, `consequences` is non-null, so the amount draws with an untimed bound; that is the pre-existing refused-read path, not new.
- **L3 fixed.** `SiteWindowOverview.tsx:621`: PRICED without both bounds uses `moneyWords("PRICED")`, which is not in `MONEY` and so falls to `unrecognised` ("We cannot judge this yet", tone `limited`). The test asserts no amount, no "Current amount", no positive tone.
- **L1 fixed.** `tools/w1-ux-02-evidence.mjs:193-197` waits for the loading line to go (its own claim) plus 800 ms; `:207` accepts "As of: time not recorded" only when `amountShown` is false. This is stricter than before; packet `:96` corrected.
- **L5.** `STATUS_WORDS` is still used locally; export and stale comment removed. Fine.
- **No weakened assertions.** The diff only adds test lines.

## New findings (Low, non-blocking)

### N1 (Low): a likely one-commit window where a stale "no consequences" read draws the amount untimed
`SiteFinancials.tsx:127-141` (`useRead`) with `:628-658`. `useRead` clears its state in an effect, after render. Before the bridge lands, the consequences read resolves immediately to `{loaded, null}`. When the bridge lands, `pinnedRevision` changes, but in that render `consequences` is still the stale `{loaded, null}`. So `consequencesLoading` is false and `consequenceRead` is null for one commit. That commit draws the amount with "As of: time not recorded" until the effect's `setRead(null)` switches to the loading line. With real network timing this is probably a single frame, so it is cosmetic. I reasoned this from the code and did not observe it. Fix if wanted: key the read state on its deps, for example by storing the deps with the result and treating a mismatch as `null`.

### N2 (Low, evidence script): `amountShown` is page-wide, so it can fail a correct capture
`tools/w1-ux-02-evidence.mjs:158`. `[data-price-selection="PRICED"]` also matches the Overview's "Price in use" panel (`SiteFinancials.tsx:683`). A legitimately untimed non-positive Financials bridge state, shown beside a priced site price, would fail the as-of claim. This fails closed, so it cannot hide a defect, but it may produce a false failure when W1-UX-06 reruns the captures. Fix: scope the query to the measured card (`c.querySelector(...)`).

## Still for the owner's list (unchanged, carried by the packet)

L4 (Overview and Financials word money codes differently; "Upstream" jargon) and L6 (untimed non-positive Financials states). Both are correctly deferred.
