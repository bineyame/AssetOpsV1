# post-W6 shell: capture and fix-round review

- Reviewer: fresh Claude reviewer (did not author the slice).
- Worktree `AssetOpsV1-review3`, branch `task/post-W6-shell`, head `3f686150`.
- Scope: what is new since the code review. That is `7605b824` (L3/L4/L5/L7), `e9b1b8d9` (Q23 cap fallbacks, Q13 SLD key) and the recapture in `.agent/post-W6-shell-recapture/`.
- Inputs: packet `.agent/post-W6-shell-packet.md` and rulings Q13 and Q23-Q26.

## Verdict: ACCEPT-WITH-FINDINGS

The fixes do what the rulings say. No row is hidden and no guard is loosened. The recapture covers the Q24 plan completely. The cap proofs are within their caps and honestly labelled. Two Low findings, F1 and F2, should be fixed on the branch. Neither blocks the capture evidence, because neither changes a captured screen.

## Findings

### F1 (Low; test gap; the packet's non-vacuity claim is overstated): the Identity `wide` wiring has no test that fails when it is reverted

- **Where:** `frontend/src/sites/StoredFoundationViews.tsx:505-507` and `:547-579`. The test is `frontend/src/shell/__tests__/siteFoundationRevision.test.tsx:2346-2359`.
- **What I saw:** I reverted only `StoredFoundationViews.tsx` to `7605b824`. The Q23 test still **passes** (1 passed).
  - The route half of the test only asserts that the short rows (archetype, timezone) are *not* wide. That is true with or without the change.
  - The long-value half renders `KeyValues` directly, so it tests `V69Layout.tsx` and not the Identity panel.
- **Packet claim:** "all five new tests fail" with the five files reverted. That holds only for a joint revert. File by file, the Identity wiring is uncovered.
- **Failure scenario:** someone drops or mis-keys the `wide(...)` flags on Location, Timezone, Site identity, critical order or supplied users. No test fails. The Foundation worst case then returns to the measured 982/1064 px, past the Q23 850/1050 caps.
- **Fix:** add a route test with one long stored value, for example a 41+ character `location` in the fixture. Assert that `[data-key-value="location"]` carries `data-key-value-wide` and that its `dd` text is complete.

### F2 (Low; correctness, latent): the floored plan target understates whole-number targets because of float error

- **Where:** `frontend/src/sites/SiteFoundationChange.tsx:209`, `Math.floor((1 - num / den) * 100)`.
- **What I saw:** a node sweep of every `num < den <= 1000` whose exact reduction is a whole number found 570 that show one point low. Examples:
  - `[4,5]` (a 20% target) renders "≥19% lower";
  - `[9,10]` renders "≥9% lower";
  - `[11,20]` renders "≥44% lower".
- **Before L4,** `Math.round` gave 20 for `[4,5]`.
- **Current exposure:** the backend stores only `[3,4]` (`backend/assetops_backend/actions/verification.py:234`), which still renders 25. No current screen is wrong.
- **Failure scenario:** the first plan with a 0.8 or 0.9 ratio shows the wrong stored target on the Change page. "At least 19%" is weaker than the stored figure, so it is not an overstatement, but it does not match the stored target.
- **Fix:** use integer arithmetic, `Math.floor(((den - num) * 100) / den)`. Add `[4,5]` → "≥20% lower" to the unit test.

### Notes (not findings)

- **N1 (test precision).** The Q13 route test (`siteFoundationRevision.test.tsx:2361-2378`) checks two things after a key click: the entry is `aria-pressed`, and exactly one drawn part is `data-selected`. It does not check that the drawn part is the *same* component.
  - I read the code: the key calls the same `selection.onSelect(pressed ? null : node.componentId)` as `choiceProps` (`SiteSingleLineDiagram.tsx:340-357` vs `:774-785`), for the bus as well as the parts. So the behaviour is right.
  - Asserting the drawn node's component would make the test stronger.
- **N2 (CSS reach not named in the packet).** `[data-evidence-inspector] tbody th[scope="row"] { min-width: 15rem }` at ≤640 px (`primitives.css`, the Q23 block) also matches the non-ledger `SiteEvidence` inspector table (`SiteEvidence.tsx:760`, `:798`, "Source time"). The packet does not list that reach.
  - The only non-ledger `evidence` case in the selection is `no-readings`, which draws no inspector table, so no capture shows this reach.
  - The page cannot overflow, because the table sits in its own scroll wrapper. Still, a populated legacy Evidence inspector at 390 has not been seen.
- **N3 (index honesty, pre-existing).** `build_index.py:41` treats `[] == None` as a title match. So `portfolio / w302-partial-week` (the B11-16 503: no titles, no heights) shows as `ok`/`titles = frozen`.
  - The packet does name it as a pre-existing claim failure.
  - The index also records `clipped` per pair but never evaluates it. I checked the clipped entries on the changed screens: `changes` "Changed value" is a visually-hidden caption, and the `sites` filter labels were already clipped in the frozen `fddf5cad` evidence. Both are pre-existing.

## Checklist results

- **The fixes implement the rulings; no rows hidden; no guards loosened.**
  - Q23 used the allowed sequence: wrapping (the `wide` stacking), then an inner scroll (`.evidence-record-view__body`, max-height 26rem/24rem), then a wider phone first column.
  - All ten Identity rows remain, and all five record rows in the worst case (`record 5 opened (all five rows shown)`).
  - Neither commit touches `tools/checks/*` or `shell-overflow.ps1`. `git diff --name-only e9b1b8d9 HEAD` outside `.agent/` is empty.
  - L3, L4, L5 and L7 match the review's asks. L4's independent figures fall back per card (`:348-361`).
- **New tests fail on single-file revert.** Each file was reverted alone, the focused file run, then restored; `git status` was clean afterwards. Results:

  | File reverted alone | Result |
  |---|---|
  | `V69Layout.tsx` | Q23 test fails |
  | `SiteSingleLineDiagram.tsx` | Q13 test fails |
  | `LedgerSiteEvidence.tsx` → `7605b824` | v01b record test fails |
  | `primitives.css` | both CSS tests fail |
  | `LedgerSiteEvidence.tsx` → `7605b824^` | L5 test fails |
  | `SiteFoundationChange.tsx` → `7605b824^` | both L4 tests fail |
  | `StoredFoundationViews.tsx` | **passes** (F1) |

- **The SLD key selects the same part and is keyboard-accessible.**
  - It shares the selection callback with the drawing (N1).
  - Its entries are native `<button aria-pressed>`, so Enter and Space work.
  - It is shown only at ≤640 px and is `display:none` at desktop.
  - `sld-legibility-r2.json` at 390 shows the key visible at 12 px, with 10 entries for 10 drawn parts, all focusable. `aria-pressed` follows `?component=battery`. At 1440 the key is hidden and the drawing is at scale 1.
  - The drawing still fits: scale 0.315, the scroll width equals the client width at 316, and overflowX is 0.
  - The `unknown-part` URL has no query because the app strips an undeclared component (`SiteFoundationFrame.tsx:117-124`). That is expected.
- **The inner scroll box is focusable.** It has `role="region"`, `aria-label="Reading detail"` and `tabIndex={0}` (`LedgerSiteEvidence.tsx:1660`). The test asserts this, and the DTO proof records `tabindex "0"` and a scrollTop that moves.
- **Recapture coverage (Q24).** I checked this independently against `post-W6-audit/audit-index.json`:
  - 370/370 pairs and all 88 frozen screen IDs, both widths each.
  - All 230 indexed cases of the 18 changed screens are present, none missing.
  - selection.json equals index.json.
  - Titles and order equal the frozen titles for every pair except the two portfolio pairs, where both are empty (N3).
  - overflowX is 0 everywhere. Heights are recorded per panel.
- **Cap proofs.**
  - App: Foundation 606/850 and 606/1050; mini records 452/1200 and 662/1800; record opened 919/1200 and 1097/1800.
  - DTO worst case: mini 1180/1200 and 1687/1800; Foundation 843/850 and 860/1050.
  - All-open runs (2617 and 3519) are exempt, with no clipping.
  - `dto-proof/README.md` and `results.json` are labelled "DTO RENDER PROOF - not an app screenshot" and an explicit capture gap. The harness imports the real `App` plus the same two CSS files as `src/main.tsx`.
  - The 7 px Foundation margin at 1440 is stated in the packet.
- **Batches 1-5 at `710b0de5` are not reached by `e9b1b8d9`.**
  - `e9b1b8d9` touches `LedgerSiteEvidence` (ledger inspector and record view), `SiteSingleLineDiagram` (`SldDrawing`), `StoredFoundationViews` (Identity), `V69Layout` (`KeyValues`, which changes only when `wide` is passed, and only Identity passes it) and new CSS selectors.
  - The 710b screens are the action-*, analysis, asset, assumptions, changes, dispatch, evidence/no-readings, financials, finding*, health, mini, readiness, recommendation, sitefindings, sites, sitework and verification screens. None renders `SldDrawing`, the Identity panel, the ledger inspector or the record view. Readiness has no SLD or Identity.
  - foundation, sld and evidence-analysis were recaptured at `321cfe56`.
  - No product file differs after `e9b1b8d9`.

## Checks run

- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-all.ps1`: all 11 guards passed.
- Targeted vitest: `postW6ShellCss`, `measuredTime`, `siteFoundationChange`, `siteFoundationRevision` and `v01bEvidenceVisual`, 161 tests, all passing at HEAD. Vitest ran on this machine despite the standing note.
- The seven single-file reverts above.
- Not run, per the dispatch: the full suites, the build and any capture or layout-evidence rerun. The packet's full-batch numbers at `e9b1b8d9` (3015 passed, 1 load flake) are cited, not verified.

## For the Architect (evidence only, no ruling)

- **L1:** `G-changes-plan-figures` is still `contract`/`absent`. I did not re-examine it.
- **L4 "No increase":** the backend never stores `[1,1]` today. F2 is separate from the wording question.
- **Register rows for the fallback layouts:** the SLD phone key, the Identity stacking and the inner scroll have no mock equivalent and no D-row. The packet flags the key.
- **Batches 10-12:** captured through `run_renamed_producer.py` into `assetops_shellrc_bNN_test` DBs, recorded in each `batch-1[0-2]/run.md`. Titles, overflow and heights for those pairs pass the same checks as the rest.
