# Re-review: MA-1 fix round 1 (v70 mock addendum)

- Reviewer: independent Claude reviewer, 2026-11-03. I did not author the work and made no edits to the branch.
- Branch `task/MA-1-mock-addendum`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ma1`. Fix commit `bf54ab5f9`, previous reviewed head `29d552bf3`.
- Prior review: `review-MA-1.md` (REVISE: M1, L1–L7). This round was asked to fix M1, L1, L2, L3, L4 and L6. L5 and L7 were left by decision.

## Verdict: ACCEPT

M1 and each of the requested Low findings are closed, and I found no regressions. One new Low finding (N1) is optional polish and does not block the merge.

## Checks run (by me, at bf54ab5f9)

| Check | Result |
|---|---|
| `git diff 29d552bf3..bf54ab5f9 -- ':!.agent'` | `outcomes.css` (+1, `.why-close`), `outcomes.js` (open rule, Kobo income, Close button, clientWidth clamp, focus target), `screens.js` (Close handler, focus return, Depot row), `index.html` (rebuilt). Nothing else changed. |
| `git diff --name-only main...bf54ab5f9` outside `.agent` | Only `frontend/mockups/v70/{index.html,outcomes.css,outcomes.js,portfolio.js,screens.js}` |
| Fresh `node build.mjs` from the bf54ab5f9 sources (in scratch), then `cmp` against the committed `index.html` | **Identical** |
| `node --test tools/checks/test_mock_deviation_labels.mjs` | 14/14 pass |
| `node --test frontend/docs/architecture/test_mock_gaps.cjs` | 13/13 pass |
| Headless Chrome over CDP, my own script, branch build compared with a main build, 7 screens at 1440×1000 and 390×900 | `bad: []`. Details below. |
| Regression: `<main>` innerText of all 110 SCREENS, branch compared with main | Only the 7 named screens differ: portfolio, mini, cold, ev, finding-history, findings-opportunities, verification |
| Vocabulary scan of the lines added in the fix | No thread, snapshot, revision, COMPLETE/PARTIAL, state code, lab or load wording. The only matches are the lower-case "complete sessions" and "Limited evidence", which was already there. |

## Each fix, checked

- **M1: closed.**
  - On a fresh load, the set of open and closed rows on mini, cold and ev is identical to main at both widths.
  - Only "Needs attention" rows are open:
    - mini: Optimize;
    - cold: Optimize and Protect;
    - ev: Protect.
  - The Grow row is closed by default. Its three parts are still in the row body (`outcomes.js:161–162`).
- **L1: closed.**
  - The Kobo part reads "$7.50 over the 3 checked study days (3 × $2.50) at the assumed $0.25 per kWh · not billed or collected", with the subline "$2.50 per eligible one-hour window · 3 eligible windows on the 3 checked days".
  - The Portfolio card reads "Kobo: $7.50 over 3 checked study days ($2.50 per window)".
  - **$7.50 is consistent with v70.** v70 gives $2.50 per eligible window (10 kWh × $0.25/kWh), and F-109 has 3 eligible days out of a 5-day study. 3 × $2.50 = $7.50.
  - $7.50 is the only new number in the diff, and the packet lists it as a derived illustrative value.
- **L2: closed.**
  - I tested all 14 "Why?" buttons at both widths (28 cases). In every case, focus returns to the "Why?" button that opened the dialog after each of these: Escape, a second click on the button, and the sheet's Close button at 390.
  - Enter and Space still open the dialog, and focus moves into it when it opens.
- **L3: closed.**
  - In all 28 cases there is no horizontal scroll, either at rest or with a dialog open.
  - The rightmost dialog edge at 1440 is the Portfolio Assure card's, at 1413 px, against a `clientWidth` of 1425. Before the fix it was 1428.
- **L4: closed.**
  - At 390, the Close button is visible inside the viewport on every sheet, and it receives focus when the sheet opens.
  - At 1440 it is hidden (`display:none` unless the dialog has `.sheet`). Desktop focus still goes to the evidence link.
- **L6: closed.**
  - "Chargers mostly idle at Depot" now appears in the list.
  - Its wording comes from v70 `outcomes.js` lines 94–96 and 136: "Under a fifth of daily capacity", "120 kWh in 10 complete sessions", "$36.00 gross tariff estimate".
  - It also carries the line "Early signal: no target set yet, and billed income is not recorded".
- **L5 and L7** are unchanged, as decided. L5 should still be carried into the CH-5b brief.

## Findings

### N1 (Low, preference-level clarity): the Depot opportunity row shows $36.00 but drops v70's "not priced" basis

- **Where:** `frontend/mockups/v70/screens.js:812`, `oppListPanel()`, the second `<li>`.
- **What is wrong:**
  - In v70, $36.00 is what Depot's delivered energy was worth on 6 Oct: it is the head of the Depot Grow row.
  - v70's own record for the "Chargers mostly idle" opportunity is unpriced: `price:'Needs other fleets’ demand and a rate'` (`outcomes.js:136`).
  - In a list titled "Opportunities to grow", directly under Kobo's row (whose numbers are the size of the opportunity), a reader can take $36.00 as the size of the Depot opportunity.
- **Why it is only Low:**
  - Every figure is v70's, and the row says "Early signal".
  - The prior review's L6 fix also suggested stating in words that the row is not priced.
- **Fix (optional):** use v70's basis as the limit line, for example "Early signal: not priced yet, needs other fleets’ demand and a rate". Or keep $36.00 but label it "earned on 6 Oct", so it does not read as the opportunity's size.

No High or Medium findings.

## Not verified

- Behaviour with a screen reader, and touch on a real device: I checked only DOM focus and visibility.
- I did not open the r1 PNG captures. The default-open state and the Grow content were checked in the DOM instead.

## Residual risk not named in the packet

- `window.whyTrigger` is a single global. If something re-renders the board while a dialog is open, focus would go back to a detached node. That does not happen in the mock today, but CH-5b should give the dialog its own reference to the button that opened it rather than copy the global.
- $7.50 assumes the 10 kWh trial runs in each of the 3 eligible windows. v70 states $2.50 for a single window. The mock now says "3 × $2.50", which makes the assumption visible. CH-6 should keep that multiplier explicit.
