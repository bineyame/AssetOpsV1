# Review: post-W6 W3-estate (`task/post-W6-W3-estate` @ 76f66f25)

Reviewer: fresh Claude reviewer, independent of the implementer. Base: merge-base with main `dcf5b086`. Main has since moved to `aa0ff22f`, but only with docs (`post-W6-W1-rulings.md`, `post-W6-W3-closeout-rulings.md`), so no code conflicts.

Authority: `.agent/post-W6-W3-estate-rulings.md` (cross-card items 1-8, Q1-Q23), `.agent/post-W6-W3-estate-build-rulings.md` (1-6), and the W3 card in `.agent/post-W6-audit/fix-slices.md`.

## Verdict: ACCEPT-with-findings

One Medium finding must be fixed on the branch: the ruled Q8 152 px column has no effect in the browser, so R295 is only half closed.

The Architect closeout rulings that landed on main (`post-W6-W3-closeout-rulings.md`, items 1-3) are not yet implemented at 76f66f25. I did not rule on them. They are listed under "Architect points" below.

Everything else matches the rulings, and the tests prove the behaviour. I confirmed this by reverting single files, listed below.

## Findings

### M1 (Medium, D3 left open): the Q8 152 px Finding column has no effect at 390 px, so R295 is half fixed

- **Where:** `frontend/src/estate/estate.css:137-147`, and the CSS-source assertion in `estateRoots.test.tsx` (the Q8 block that expects `width: 152px; max-width: 152px`).
- **What is wrong:** B10-09/R295 (batch-10 ledger line 70) has two parts: "KOBO title clamped … **the wide sticky Finding column leaves only Finding and Site visible**". The clamp is fixed. The column is not.
  - The Findings index table has no `<colgroup>`, so `.estate-page .data-table col:first-child` matches nothing.
  - Chrome ignores `max-width` on auto-layout table cells.
  - The table keeps `min-width: 900px`.
- **What the captures show:** in `part-b10-positive/findings-positive-390-app.png` and `part-b10-partial/findings-partial-390-app.png`, the Finding column is about 205 px wide (the FINDING header is at x≈47 and the SITE header at x≈254). Only Finding and Site are visible, with no Priority column.
  - The recorded `hscroll` gives the app table as sw 900 / cw 318, against the mock's 672 / 320.
  - The mock 390 capture shows Finding, Site, Priority and part of Confidence. That is the exact target named in the pre-flight Q8 default, and the ruling says to verify it "in CSS assertion and both-width captures".
- **Why the test does not catch it:** the CSS test reads the stylesheet text, so it passes while the rendered layout does not change. No capture measures the first column's width.
- **Failure scenario:** an operator on a phone opens `/findings` and still sees only the title and Site. Priority and confidence need a horizontal scroll, which is the D3 the card set out to close.
- **Fix:** make the width take effect on the Findings table. For example:
  - add a `<colgroup>` to the Findings index, as `actionIndex.tsx:144` already has, or set `width`/`min-width` on the first column together with a narrower 390 `min-width` for the table;
  - then re-measure at 390 with a recorded first-column width and the columns that are visible.
  The lens pages (`findings-cost/risks/opportunities`) share the table and would change too.

### L1 (Low, copy note for the Architect, not blocking): the "no selected result" sentence does not agree with several Sites

`findingIndex.tsx:229,239` produce "{A}, {B} has no selected result; totals are unknown." and "{A}, {B} is not yet assessed; …".

Build ruling 5 made only the pending sentence plural ("their rows"). The implementation follows the ruled literal exactly, so this is not a defect against the rulings. It is worth one line in the next copy batch.

## What I verified

### Rulings, item by item

- **Cross-card item 7 / Q1 / Q2 / Q9 (`site_home_href`):**
  - `evidence_money.py:139` returns `/sites/{code}/ev` for EV (both the domain constant and the stored Site type), and leaves cold and mini-grid unchanged.
  - It is reused for the Evidence `window_links` fallbacks and the placeholder `_row`, Financials `_money_links`, the Findings index `_finding_links` and the Portfolio rows.
  - A grep finds no remaining bare `/sites/{code}` site link for EV.
  - Only the four authorised backend files were changed, with no schema change. The nullable `links.finding` follows build ruling 1.
- **Q4 / Q10 Finding links:**
  - Cold and EV take the one selected Site window that holds the Finding (recorded from `site_coverage`'s own `selected_windows` call, with no extra query) and the Site evidence cutoff.
  - The link is null if the window or cutoff is missing, the window is reversed or longer than 31 days, the cutoff is after the estate cutoff, or several windows hold the Finding.
  - Episode bounds are never used. Mini-grid keeps `revision_id`.
  - Portfolio reuses the index link, and the Postgres test asserts that the two are equal.
  - The frontend `findingLinkLive` stays as a defence, and a null link shows "Finding detail unavailable".
  - I checked that the delegating `_WindowRecorder` is safe: the estate code never assigns attributes on the snapshot and never checks its type.
- **Q10 matrix:** `OBJECTIVE_ROUTE` matches the ruled table.
  - I confirmed that each route is mounted: cold `temperature`/`backup` in `SiteAnalyticsFrames.tsx:193`, EV `sessions` at `:200`, and EV and cold Health through `SiteHealthFrames.tsx:43-45`.
  - Cold and EV Cost and Evidence use the latest proven Evidence-row window, else the Site home (build ruling 4).
  - EV Backup is `None` and reads "No configured objective".
- **Q5:** `actionRowTitle` shows the stored title, or the code alone. No "Battery reserve trial" remains.
- **Q7:** a second `scope()` read at the identical from/to/known_at, joined on `site_id`. It uses the four ruled sentences plus build ruling 5's plural, and falls back to the generic copy when the scope read fails or a Site is not named. Actions keeps `limitationSentences` unchanged, and a test checks that.
- **Q8:** the clamp is removed and `overflow-wrap: anywhere` is in place. The column width is not effective (see M1).
- **Q11:** "Related records" with the two live links. ACT-049/061 and "Map transfer switch" are gone.
- **Q12:** the limits join with a space; the cell shows the first sentence; a full "Limits" line is in Basis details; the 176/300 px caps are removed and horizontal scrolling is kept.
- **Q13:** `{n} selected assessment(s)`; a nested "Assessment IDs" disclosure with a 160 px scroll; plain coverage words; "Excluded from comparison" for an unknown code, with the raw code in "Record details"; the 320 px drawer is kept.
- **Q14 / cross-card item 5 / build rulings 2 and 6:**
  - One classifier, `invalidWindowCopy`, is shared by both clients and `EstateRefusal`.
  - The title "Window cannot be read" appears only for `INVALID_WINDOW`, and the bar reads "Window not valid".
  - A 403 keeps the window line (tested in Financials).
  - The copy matches the rulings verbatim.
- **Financials JSON regeneration and the `meetsMeasuredNarrowLayoutWithoutDocumentOverflow` change: sound.**
  - The only assertion removed is `threeRows <= cap`, and that cap no longer exists.
  - The new assertions (`maxH === "none"`, every row measured, `scrollH <= clientH`) are stricter.
  - The document overflow, 448 px three-row, piece-maxima, aggregation and opened-results checks are kept.
  - In the JSON, rows 62→46 px and the register 256→240 px, which is consistent with showing the first sentence only.
- **Fixture fix in `test_w303_portfolio_scope_snapshot_postgres.py::_gap_row`:** it matches the real row shape. Real `_row`/`window_links` emit exactly `{site, site_readiness, site_readiness_label}`, and a cold or mini-grid home is `/sites/{code}`. An unproven row carries `CURRENT_VIEW`, so `objective_destinations` correctly ignores it. It is a test-only change.
- **Guards not loosened:** no file under `tools/`, the guard self-tests or `frontend/src/ui` changed. The only shell test change (`w301EstateShellRoutes`) adds the ruled Q7 `scope` call expectation.
- **Recapture:** I compared the indexed batch-10/11 pairs in `audit-index.json` (62+66, keyed by screen, case and width) with the `*-{1440,390}-app.png` files in the recapture parts. **Missing: none. Extra: none.** All 128 pairs are present at both widths. I opened two 390 captures (refused-reversed Evidence and the partial Findings) and both show the ruled copy.

### Checks I ran (worktree at 76f66f25)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `tools/check-all.ps1` | All 11 guards passed (estate guard self-tests 4 passed) |
| `npx.cmd tsc --noEmit` | exit 0 |
| vitest, targeted: estateRoots, estatePortfolio, estateFinancials, estateEvidence, w301EstateShellRoutes | 5 files, 59/59 passed (vitest ran in this worktree) |
| pytest, pure: `test_post_w6_w3_estate_links`, `test_w302_money_api`, `test_w302_evidence_api`, `test_w303_portfolio_api` | 42 passed, 1 skipped (a DB-gated case with no URL set) |
| pytest, Postgres (`assetops_test`): `test_evidence_prompt_null_steps_and_coverage_precedence` and `test_three_domains_same_window_cutoff_and_full_selection_ids` | 2 passed in 93.8 s |

I did not run the full backend suite, full vitest, builds or captures, as instructed. For those I am relying on the packet: the backend batch of 232 cases (231 passed, plus the fixed one rerun in its file, 10 passed), and the frontend full run of 2983/2983 at `26e6c49c`. Backend product and test code is unchanged between `14441112` and HEAD; only two frontend test files changed after the backend batch.

### Revert proofs (one file at a time, restored with `git checkout HEAD`, tree clean afterwards)

| Reverted file | Tests that failed |
| --- | --- |
| `estateShared.tsx` | 3 (Financials refused window, estateRoots refused window, `test_every_state_and_empty_string`) |
| `estate.css` | 1 (`test_390_scroll_and_static_missing_destinations`) |
| `findingIndex.tsx` | 3 (windowed-link gating on every lens, cause copy plus fallback, refused window) |
| `actionIndex.tsx` | 2 (Action title, refused window) |
| `EstateEvidence.tsx` | 2 (Related records, refused window) |
| `EstatePortfolio.tsx` | 3 (matrix links and EV Backup, scope disclosure, refused window) |
| `EstateFinancials.tsx` | 2 (full Limits and no cap, refused window) |
| `estatePortfolio.css` | 1 (scope disclosure 160 px) |
| `financials.py` | 2 in `test_w302_money_api` |
| `index.py` | Postgres `test_three_domains…` fails: the cold link carries `revision_id=…`, which proves the non-vacuous cold windowed-link assertion. The pure suite fails at collection. |
| `portfolio.py` | `test_w303_portfolio_api` still passes. The matrix behaviour is pinned by `test_post_w6_w3_estate_links` (import) and the Postgres scope test. **Note:** no DB-free API-level test pins the Portfolio row links. |

## Architect points (evidence only, no ruling)

Closeout rulings for all three points are now on main (`post-W6-W3-closeout-rulings.md`, commit `7f73aed0`). The branch at 76f66f25 implements none of them yet.

1. **Cap-probe method.** `tools/probe.js` "primary" changes only the first visible text leaf, or the Limit, of each clone. It does not check that every intended field reached 160 characters.
   - Objectives across the estate measured a worst case (342/311) below its own maximum real height (352/321), so that probe did not stress the panel.
   - The lens panels had no rows to clone (0 rows).
   - Closeout ruling 1 asks for a probe assertion that every intended field changed.
2. **Consequence register.** `cap-proof.txt` records primary 626/726 and stress 938/1575. Closeout ruling 2 takes the all-cell reading and revises the cap to 1050/1800. It requires an amended probe (including the short Category and Source cells) and a recapture at both widths. The stress variant already measured 938 < 1050 and 1575 < 1800, but those numbers were not produced by an all-intended-fields-verified probe.
3. **`portfolioWords.ts:26`.** Confirmed stale: Q10 links every cell except EV Backup.
   - The mock footnote reads "N/A means no configured objective. Select any cell for context."
   - Related: the EV Backup cell's label is "Unknown", with "No configured objective" beneath it, while the footnote defines N/A as "not configured".
   - Closeout ruling 3 sets the footnote text and keeps the EV Backup wording.

## Residual risk not named in the packet

- The Q8 CSS test only checks the stylesheet text, so it cannot catch a layout that does not change (M1). Any similar "CSS source" assertion for a table column needs a measured capture behind it.
- A cold or EV Finding held by more than one selected window (for example an episode that crosses a day boundary) gets a null link by design. With a multi-day estate window, such rows read "Finding detail unavailable" even though a provable window exists. This follows the "stay unavailable if unproved" ruling, but it may surprise users once multi-day episodes are populated.
- No DB-free API test pins the Portfolio row `links.finding`/`links.site`. The proof sits in the 90 s+ Postgres scope test.
