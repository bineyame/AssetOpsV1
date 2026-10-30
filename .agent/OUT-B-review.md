# OUT-B slice review: Site outcome board (final, B3/B5/B6 + integration)

Reviewer: fresh Claude Reviewer, 2026-10-30. Branch `task/OUT-B-site-outcome-board` at e5a95e18, against main 32adae2f (the merge base; 43 commits).
Contract: build spec rev 3 §1 and Slice B, with Pre-flight rulings B and addenda 1-8. Per-unit reviews B1, B2 and B4 were accepted earlier, and their fixes are intact: the B1 M1 suffixes and `_resolve_finding`, B2 M1 `findings_settled`, and the B4 M1 main-binding test, which passes.

## Verdict: REVISE

There is one High finding, a mock departure that is not registered, and it is cheap to fix. There are three Medium findings. One of them, M1, needs an Architect copy ruling because the code follows the spec's letter. The board, the matrix, the dots, the register and the test rewrites are otherwise sound.

## Findings

### H1 (High, unregistered mock departure): the explainer is a centred modal, not the mock's right-hand drawer
- **Where:** `frontend/src/sites/OutcomeBoard.tsx:257-300` and `frontend/src/sites/outcomes.css:107-108`.
- **What the mock does:** `explainBoard` calls `drawer(...)` (`frontend/mockups/v70/screens.js:1007-1010`). That opens a right-aligned panel, full height, `width:min(550px,95vw)` (`mockups.css` `.modal-backdrop{justify-content:flex-end}` and `.drawer{height:100vh}`).
- **What the app does:** the native `<dialog>` uses default centring, at most 640 px wide.
- **Why it is High:** §B.5 asks for a `<dialog>`, but it does not ask for a centred layout. No R-row registers the change. Under the owner rule, an unregistered mismatch is High.
- **Fix, either of:**
  - (a) style `.ob-dialog` as the mock drawer: `margin:0 0 0 auto`, `height:100vh`, `max-height:none`, `width:min(550px,95vw)`, padding 28px. The `<dialog>`, the focus trap and Escape all stay. This is preferred.
  - (b) register it, for example "R553: explainer as a centred dialog".

### M1 (Medium, honest copy, needs an Architect ruling): the EV Grow row says "15 kWh in 0 complete sessions"
- **Where:**
  - `backend/assetops_backend/site_outcomes/ev.py:131` (`kwh` = `energy.complete_kwh`);
  - `ev.py:216` (contributor "{kwh} kWh in {completed} complete sessions");
  - `ev.py:181` (subline "{kwh} kWh delivered in complete sessions").
- **Seen in the capture:** `.agent/OUT-B-captures/shots/overview-ev-depot-open-390-app.png` shows "15 kWh in 0 complete sessions" beside the Protect headline "1 interrupted · 0 unknown of 1 session".
- **Cause:** `complete_kwh` sums the sessions whose *energy record* is complete (`ev_site_reads.py:681,687` `energy_complete`). It does not count sessions that *completed*. `denominator.completed` counts session outcomes. A fault-aborted session with complete metering therefore gives 15 kWh against 0 completed sessions.
- **Why it matters:**
  - The two texts contradict each other on the client screen.
  - The subline is false: the energy was not delivered in complete sessions.
- **Fault:** the builder followed ruling B-Q26 to the letter, so the fault is in the spec.
- **Fix:** the Architect rules the wording or the source. One option is "{kwh} kWh with complete metering in {started} sessions". Another is to use `supported_kwh` with `started`. The implementer then applies it and adds a unit test with completed=0 and complete_kwh>0.

### M2 (Medium, stale client copy): the mini objective line still says "Check each card…"
- **Where:** `frontend/src/sites/SiteWindowOverview.tsx:420`, `MINIGRID_OBJECTIVE`. The full text is "Objective: serve residential, clinic and productive loads while protecting the battery reserve. Check each card for the supported result and its limits."
- **Seen in the capture:** the Kobo capture shows this sentence right above the board, and no cards exist any more.
- **Why it matters:** addendum 8 replaced the strip's second sentence for exactly this reason: it named the retired cards. The mock's line ends after "battery reserve.", so this sentence is the app's own and points the client at UI that is gone.
- **Fix:** drop the second sentence, or reword it to name the outcome rows. Update the s5 test that pins `MINIGRID_OBJECTIVE`. If the copy needs a ruling, the Architect gives one, as for addendum 8.

### M3 (Medium, gate evidence): the known-failure claim does not add up, and its lists are not kept
- **Where:** `.agent/OUT-B-packet.md:56-63`.
- **What the JUnit shows:** I read the full-run JUnit, `var/test-results/OPS-03/20261030-151209-b7030a/junit.xml`. It has 28 non-passing cases: 20 failures and 8 errors.
- **What the packet claims:**
  - "the other 24 reproduce on main";
  - the serial rerun on both checkouts gave 23 identical entries (15 failed + 8 errors);
  - "five further full-run failures passed on rerun".
- **Why that does not add up:** 23 + 5 = 28.
  - The 23 already include the 2 named w303 tests and the 2 w301 tests.
  - The 5 "flakes" were rerun on the branch only. Nothing shows they fail on main.
  - The 5 are not named anywhere.
  - Neither sorted list nor the diff is saved: the serial-rerun JUnit is not in either worktree's `var/`.
- **Why it matters:**
  - Several failing files exercise estate scope and portfolio code that OUT-B changed (`estate/scope.py`, `estate/portfolio.py`, `estate/evidence_money.py`): `test_w303_portfolio_scope_snapshot_postgres`, `test_w303_selectors_postgres`, `test_w301_estate_index_postgres` and `test_cc_placement_postgres`.
  - Ruling B-Q32 says any failure outside the ignore list blocks.
  - The coordinator's ignore list covers main-reproducible failures, not branch-only flakes.
- **Fix:** in the packet:
  - name the 5 rerun-passed tests;
  - give the paths of the saved branch and main serial-rerun results, so the "diff empty" claim can be checked;
  - correct the count to 23 reproduced + 5 flakes.
  - If any of the 5 sits in an estate file listed above, rerun it once on main to show it is not caused by OUT-B. No full suite is needed.

### Low
- **L1:** `backend/assetops_backend/site_outcomes/cold.py:116`, `:141-142` and `:271` count only `MISSING` steps as gaps. A causal strip with a `CONTRADICTORY` step therefore reads "Every step recorded" and "Event fully reconstructed · no verified result yet", which overstates the chain. Count CONTRADICTORY as not recorded, or rule that it is not.
- **L2:** `ev.py:171-173`, Assure subline. When `denominator.incomplete` is null but connector status is missing, it prints "0 session ends and … are missing", stating a count that is unknown. Omit the session part when `incomplete` is null.
- **L3:** `ev.py:280`. `stamp()` can return None, which would render "Missing None–None". Guard against null span bounds.
- **L4:** `frontend/src/estate/portfolioWords.ts:144`. The orphaned doc comment "Q10: … matrix cell without a destination" now sits on `NO_SELECTED_ASSESSMENT`. Delete it.
- **L5, captures:**
  - The "open" captures open the first row only. §B.6 asked for one all-open capture per Overview.
  - `shots/raw-evidence.json`, which holds the height and overflow numbers the packet cites, is git-ignored and was not force-added.
  - I checked it on disk. The closed board measures 359/716 (cold), 410/762 (EV) and 409/740 (Kobo) at 1440/390, all within the 450/800 caps. At 390, scrollWidth equals clientWidth (390).
  - Force-add the file or quote the figures.
- **L6:** `SiteWindowOverview.tsx:1055`. The Operating context subtitle, "context for the cards, not a status source", is the mock's own text, but the cards are gone. Note it for the W1 copy pass. It is not blocking because it matches v70.

## What I checked and found clean
- **B3, addendum 3:**
  - The cooling texts and chips match exactly: null for LIMITED and UNAVAILABLE, Unknown/gray for CONTRADICTORY, and R551 is registered.
  - Cold and EV dates use the route Site record's `timezone` (`read.py:287,308`), with the UTC suffix as fallback.
  - The EV counts map as specified: f=`fault_aborted`, u=`incomplete+contradictory`, n=`started`. Nulls give "Not available yet · no session assessment covers this window", and the Protect headline is null.
  - For closed EV Findings, the single `finding(...)` read is called for each linked id the list lacks. None gives the outside-view rule, and a refusal unsettles EV-1/EV-3 and sets PARTIAL.
- **B5, the board:**
  - Structure, classes, column headings, empty texts and the Earlier text from `earlier_empty_text` all match §B.5.
  - Only NEEDS_ATTENTION rows open, not-measured rows are one-liners, and the counts text is as specified.
  - Must not harm shows with its link, money is formatted only in the frontend (`boardMoneyText`), and the loading, refused and partial states are present.
  - The explainer text is verbatim from `outcomes.js:125`.
  - Focus moves to Close on open, Tab wraps, Escape and cancel close the dialog, and focus returns to the `i` button; this is tested.
  - The CSS ports the mock rules faithfully, with tokens.
  - No new `<svg>`, and no `variant` prop.
- **B6, the Portfolio:**
  - The matrix has `role=table` and the label, Site header links, four row headers with the definitions visually hidden, cells linking to `overview_href`, and the six-state key in mock order.
  - The dots carry the "{site}: {state}" name and match the matrix tones; this is tested.
  - The Grow `short_value` shows in green and falls back to MissingClaim.
  - The summary is fetched in parallel, and its failure gives the alert.
  - In the register, R521 and R529 are resolved, R437 is closed, and R535 and R540-R552 are added.
- **Changed tests:** I read every diff hunk of the cold, EV, s5 and estatePortfolio tests and the panel guard.
  - Card assertions became "board present + old cards absent" (`expectOutcomeBoardReplacesCards`), plus window and date forwarding to the board.
  - The non-card assertions are kept: Evidence strip chips, timeline, needs attention, money-free checks, "not Healthy", shared cutoff and never-zero.
  - The panel-guard extension is scoped to the mini, cold and EV screens and to before panel 1, with negative tests.
  - No test was weakened beyond losing its subject.
- **Addendum 8:** the strip reads exactly "Each outcome row shows only what these reads support for the selected period."; it is asserted in s5.
- **Process:** nothing under `var/` is tracked. No execution-policy override was added. The capture DB is outside `_test`, which the packet discloses and says was dropped.
- **Copy:** client-facing text, no outcome codes on screen, missing data shown as "Not available yet". The vocabulary guard passes inside check-all.

## Checks run (what I saw)
- `npx.cmd tsc --noEmit`: exit 0.
- Focused vitest on 6 files (outcomeBoard, estatePortfolio, panelStructure, s5SiteWindowOverview, coldSiteViews, evSiteMoneyRoutes): **207/207 passed**. Vitest ran in this session; the known sandbox esbuild failure did not occur.
- Backend non-Postgres b1-b4 (10 files): **134 passed**.
- `tools\check-all.ps1`, run directly with `ASSETOPS_GUARD_PYTHON` set: **All 11 guards passed**.
- Captures: I compared the cold, EV, Kobo and Portfolio 1440/390 pairs and the raw evidence on disk, as in L5.

## Not verified
- I did not rerun the full vitest, the full backend, the Postgres tests or a browser, as the dispatch instructed.
- For the full-suite numbers I relied on the packet and the JUnit file.
- I could not check the main-reproduction claim (M3).
- I did not see the explainer rendered in a browser.

## Residual risk
- R552 and the Kobo demo data: on the s602b and s5 producers, every Kobo measured outcome is Unknown. The board as captured shows no Kobo story. This is carried to the combined dataset.
- The Portfolio capture has only the Kobo column (R535), so the matrix and dots are untested in a browser on a three-domain estate.

## Coordinator verification of the final-review fix round (6959fca1, 484c4ea4) and the main merge (84cd47ba, 57fa9206), 2026-10-30: ACCEPT
- H1 closed: `.ob-dialog` is now the right-hand drawer, full height, min(550px,95vw), border-left only. It is still a native dialog.
- M1 closed: the addendum 9 EV strings are in ev.py, and R553 is registered.
- M2 closed: "Check each card" no longer appears in SiteWindowOverview.tsx.
- M3 closed by passing rather than by comparison. After merging main e07fd204 (the clock fix), every file that failed in OUT-B's full run passes on the branch, run one file per DB with the cache off: 89 Postgres tests across 13 files. test_out_b4_board_postgres passes 5. Non-Postgres b1-b4: 138. tsc is clean and check-all is 11/11.
- L1-L4 fixed. L5 (open captures show only the first row) and L6 (the subtitle, v70 copy) are deferred to the W1 copy and capture pass.
- Nothing is tracked under var/.
