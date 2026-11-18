# Whole-diff review: client-demo POLISH round (§5 PC)

Reviewer: fresh Claude reviewer (did not author any slice). Diff: `git diff 83918ac00...84a2914ab` in
`AssetOpsV1-polC` (branch `task/POLISH-PC-final-gate`, head `84a2914ab` on merged main `06543e540`). The per-slice
reviews were not redone. This review looks only for problems that show across slices.

## Verdict: REVISE (small fix round)

The guards, the wire changes, the no-tuning rule and the packet's numbers all hold up. Three Medium findings block:

- ids still show outside Technical details one click from the captured screens;
- the register's DEMO-B rows describe text the product no longer shows;
- the captured Verification page uses three different words for the data source.

Each fix is a copy, markup or register edit. None needs a rebuild of `assetops_polish_full_test`. A recapture of
`kobo-verification` is enough to show M3 fixed.

## Findings

### M1: ids, enum codes and raw timestamps remain outside Technical details on the Finding, Action and Recommendation pages
- **Where:**
  - `frontend/src/ui/ProductStatus.tsx:190-213`: `ExactReferences` is a "How this was worked out" `<details>` with no
    `data-technical-details`.
  - It is still used with ids in `SiteFinding.tsx:513-521` (Finding reference, version references, lifecycle,
    currentness and transition codes).
  - Also in `SiteFindingHistory.tsx:477-483`, `SiteAction.tsx:648-654` (stored `ACT-000001`, the Action uuid and a raw
    `accepted_at`), `SiteAction.tsx:896-902` and `:1093-1099`, `SiteRecommendation.tsx:890-896`, and
    `FindingConsequence.tsx:931`.
  - 18 Site files still use it in all.
- **What:** item 3 and R656 say that every id sits in a closed "Technical details" region. The rule was applied to the
  captured screens (Kobo board, verification, cold, EV, estate, WR, preventive). The pages those screens link to were
  left out:
  - "Open the finding" (Kobo Next step) and "Review Finding" (every Portfolio row) go to `SiteFinding`;
  - ACT-001's Overview, Application and History tabs go to `SiteAction`.
- **Why it matters:** these are the next clicks in a walkthrough. Opening "How this was worked out" there shows uuids,
  UPPER_SNAKE codes and the zero-padded `ACT-000001`. The strict gate never sees them, because none of those pages is
  a capture key and a closed `<details>` is not in `innerText`. R656's "Every id" claim overstates what was built.
- **Fix:** move the id rows of those uses into `WorkedOut`/`TechnicalReferences`, keeping any plain lines. Or, more
  simply, have `ExactReferences` render as the Technical details region: summary "Technical details" plus
  `data-technical-details`. Then narrow R656's wording to match. This is an acceptance gap, not a preference.

### M2: register rows R625, R628, R631 and R634 are "standing" but describe text the product no longer shows
- **Where:** `.agent/mock-departure-register.md` lines 624, 627, 630 and 633.
  - **R625:** headlines "Not comparable for this selection" and "Not established". The capture now reads "Can't be
    compared across these sites yet" and "Not known yet".
  - **R628:** Next step "Publish an EV gross tariff". It is now "Publish a charging tariff" (R655).
  - **R631:** "told apart only by an 8-character id". The Portfolio capture now tells the two GreenHarvest rows apart
    by date ("From 30 Oct 2026, 16:00" / "From 27 Oct 2026, 16:00"), and the id is gone (R640/R656).
  - **R634:** "ACT-000001 verified on test data". It is now "ACT-001 verified on example data" (R640, Addendum 14).
- **What:** the PC packet (section 5) checked R625-R662 only for unique ids and status. It did not check that the
  product text in each row is still accurate, which item 6 asks for.
- **Why it matters:** the owner walkthrough reads these rows as the record of what the client will see.
- **Fix:**
  - Update the product cells, or append "superseded by R6xx".
  - Decide whether R631 can now close.
  - Also, low priority: R08's status cell (line 27) still starts "standing (owner)…" and only says "closed by POLISH"
    at the end. Put the closed state first.

### M3: the captured Verification page uses three words for the data source
- **Where:** `frontend/src/sites/verificationWords.ts:213`, where REGISTERED_SIMULATION gives "Registered Lab trial
  data". It is rendered at `SiteActionVerification.tsx:960,1236,1621,1624,1702,1863`.
- **What:** `kobo-verification-1440.png` shows, on one screen:
  - "Source: Example data, not field readings";
  - "Verified on example data · benefits the mini-grid operator";
  - Outcome evidence: Source "Registered Lab trial data";
  - the footnote "Policy trial on demonstration data: …".
- **Why it matters:** item 1 asks for one term for this idea ("example data"), and Addendum 14 made that the strict
  rule. The strict scan does not catch "Lab trial data", because its lab-name regex matches only "replay lab" and
  "charging lab". So this screen passes the gate with a contradiction on it.
- **Fix:**
  - Change `sourceWords` REGISTERED_SIMULATION to "Example data".
  - Change AUTHORED_DEMONSTRATION to "Prepared example data", which also removes the `:215` residual.
  - Align the footnote to "example data".
  - Update the verification vitest pins, then recapture `kobo-verification`.

### L1: "Finding" capitalised in running text, including on the first demo screen
- **On the Portfolio** (`portfolio-week-1440.png`):
  - the panel subtitle "Selected Findings across accessible Sites";
  - the placement reasons from `backend/assetops_backend/estate/placement.py`:
    - `:25` "…no longer confirms this Finding…";
    - `:39` "No price basis for this Finding" (the Kobo row);
    - `:62` `_COVERAGE_TEXT` "…other Findings may be missing".
  - One confidence cell reads "Supported finding · example data · Site coverage incomplete; other Findings may be
    missing", with both casings in the same cell.
- **On the Kobo board:** "Open the Finding →" (Needs attention) sits beside the "Open the finding" button (Next step).
- **Elsewhere:** many strings in `findingWords.ts`, `SiteFinding.tsx`, `actionPresentation.tsx:128-161` and
  `OverviewFindingList.tsx:94,165,201`.
- The build sheet's "no Finding/Action capitals" pattern was builder latitude for strings the gate found, not a global
  sweep, so this is a preference-level gap. Fix with a single lower-casing pass over the strings above.

### L2: EV tariff wording is mixed on the captured EV board
- `site_outcomes/ev.py:45` "Gross tariff estimate not available yet" (the Grow headline) sits beside "Needed before
  charging income can be estimated." (the Next step) and "No tariff set for estimates" (Needs attention).
- R628 and R655 keep the "Gross tariff estimate" tile label as mock wording, so this is accepted. But the headline is
  server prose, not a tile label.
- Off the demo path (it shows only once a tariff exists), `ev_site_reads.py:42` ELIGIBLE "Gross tariff scenario; not
  cash collected." contradicts the PC copy pass ("Estimate · not cash collected"). So do `:31` and `:37` ("gross
  tariff estimate").
- **Fix:** an owner wording call; at minimum `:42`.

### L3: estate pages keep wording that the Site pages replaced
- `estateEvidenceWords.ts:16` and `estateFinancialsWords.ts:19` say "Potential product exposure", where cold now says
  "Stock may be at risk".
- On the Portfolio, "Not known yet" (Assure card) sits beside "Not established" ("Completed activity · Not
  established", "Recovered value not established").
- These pages are not captured. Fold them into the same copy pass as L1.

### L4: the record-code check misses stored codes with exactly two leading zeros
- `tools/demo-combined-vocabulary.mjs:16` changed `0{2,}` to `0{3,}`, so that display codes (`ACT-001`) pass. That is
  narrow and justified by R640.
- The side effect: stored codes `ACT-001000`…`ACT-009999` (two zeros) are no longer flagged.
- This is harmless for this dataset, whose numbers are small. Fix by adding `\b(?:ACT|…)-\d{6,}\b`, since display
  codes never reach 6 digits under 100000.

### L5: stale test fixtures and tools keep the old server copy
- `frontend/src/estate/__tests__/estatePortfolio.test.tsx:853` and `portfolioFixtures.ts:144` still say "Supported
  Finding" / "Generated test data source".
- So does `tools/s405-provenance-evidence.mjs:36`.
- They do not pin the server, so nothing fails. They just no longer show what the server sends.

## Checks by item

1. **Copy.**
   - "example data" is consistent in the server constants (`board.py:49`, `mini.py:77,94-95`,
     `placement.py:42,56-58`) and the frontend (`sourceProvenance.tsx`, `productWords.ts:229-230`, `V69Layout.tsx`,
     `globalWorkParts.tsx:49,53`).
   - The exceptions are M3 and the two residuals in item 9.
   - "What-if" and "Possible cost" are consistent on Kobo, cold, EV and Portfolio. The Scenarios tabs keep the mock
     word "Scenario".
   - Display codes appear correctly on the captures (ACT-001, PM-013, WR-011/012).
   - "Times in UTC": `exempt_hits` gives exactly one note per capture. The two-part `due-dates` variant appears only on
     `maintenance-preventive`. `wr-overview` uses the plain note, per build sheet line 1059.
   - See L1-L3 for the rest.
2. **Guards.** All changes are narrow:
   - PB-1 adds one `REVIEWED_EXEMPTIONS` entry, keyed by file, constant and text (`missing-claim-scan.mjs:77-83`).
   - Guard 12 is new and strict: tagged labels, register ids, and the hide rule verbatim.
   - `AS_OF_PATTERN` now *rejects* the UTC suffix (R650); the pattern is mirrored in both places and tested.
   - The vocabulary scan moved to `demo-combined-vocabulary.mjs`. Its additions tighten the check: "finding id
     label", "lab name", "snake_case name", "test data wording", and PM/REC codes. MOCK DEVIATION is never exempt.
   - The only relaxations are the 2-to-3 zero change (L4) and the settle predicate, which now treats only whole
     loading lines as loading (PB-0, tested). `LOADING_LINE` needs ending punctuation. Every current loading line
     ends in "." or "…", so this is noted as residual only.
3. **Technical details.** `TechnicalDetails`/`WorkedOut` are used correctly on the captured pages. Gap: M1.
4. **Wire changes.** All the new fields are optional in the TS types:
   - `kind?` and `occurred_at?` (`outcomeBoardClient.ts`);
   - `due_state?`, `site_time_zone?` and `summary?` (`globalWorkClient.ts`);
   - `work_asset.asset_label?`.

   Consumers fall back as follows:
   - `GlobalPreventive.tsx:81` says the counts were not sent when they are missing, never zero;
   - `:95` falls back to UTC;
   - `WorkRequestOverview.tsx:99` falls back to `assetWords`;
   - `siteWorkCases.tsx:719,878` fall back to "No asset linked".

   No response key was removed. The value of the existing `asset_label` is now plain words. Its in-process reader,
   the cold board (`site_outcomes/cold.py`), moved to the new `asset_type`, so this is consistent. No JSON contract
   fixture pins these shapes.
5. **No tuning.**
   - `backend/conversions/` is untouched.
   - The golden `w301-estate-golden.json` diff is titles and `finding_label` only.
   - The story tools changed only the names, narratives and the `action_code`/`raised_at` record.
   - The analytics changes are copy: titles, the start-failure text, and `plain_limitation`, which fails closed.
   - The finish check's CO-1 got *stricter*: it now matches the href path instead of a text match.
6. **Register.**
   - Guard 12 passes: every `data-mock-deviation` id and `<MockDeviation id>` is a row, and the remaining "MOCK
     DEVIATION" strings are all code comments.
   - The hide rule in `mock-deviation.css` matches `reviewLabels.ts` and the P-04 rule: session-scoped
     `?review=labels`, `?review=off`, applied before render.
   - The R626, R630, R111 (demo) and R08 closures are justified by the captures.
   - Accuracy gaps: M2.
7. **Packet claims** (spot-checked against the artifacts):
   - **Finish check:** `var/polish_full/check.json` has 17 rows, all `pass`. CO-3 carries the new trial line.
   - **Strict capture:** `.agent/POLISH-PC-captures/captures.json` has `strict: true` and 28 captures, all settled,
     none overflowing, 0 counted. `exempt_hits` is 1 per capture, 283 on `kobo-board-S-open`.
   - **Unsettled first run:** `capture-run-first-unsettled.log` shows the two WAIT lines for `portfolio-week`, as the
     packet says.
   - **Backend `-Tier all`:** `var/test-results/OPS-03/20261101-172931-803fd5/junit.xml` has tests 4737, failures 0,
     errors 0, skipped 0, time 3380.9; `exit-code` 0.
   - **Revision gap:** that full run is at `c5277805b`, before the Addendum 14 backend copy change (`c6854cfab`). The
     packet says so, and it covered the change with scoped tests. I found no remaining backend test pinning "test
     data".
   - **Not spot-checked:** slow 19/19, vitest 3594/3594 and check-all 12/12 have no artifact in the requested set.
     I re-ran the guard parts myself (see below).
8. **Demo risk: cold-start Portfolio.** This is a real risk. The runbook's warm-up is necessary but should be made
   explicit and mandatory.
   - `GET /api/estate/outcome-summary` (`site_outcomes/read.py:400`) composes three full Site boards serially on
     every request.
   - Under Vite dev, StrictMode sends each Portfolio read twice.
   - In `api-8990.log`, the first portfolio and outcome-summary requests (lines 6-10) are followed by outcome-summary
     responses that finish only after the Kobo captures have started (lines 17, 18, 21).
   - The first run's 390 capture had a partial page (pageH 2990, against 3849 when settled), so the page was still
     loading more than about 2 minutes after the first request. The likely blocker is the outcome matrix ("Loading
     outcomes across the estate…") as much as the main read. The log has no timestamps, so this is an inference.
   - In a live demo, a Portfolio opened first on a fresh serve would sit on a loading line for minutes. That would
     embarrass the demo.
   - **Mitigation:**
     - after every serve start, open the Portfolio week URL and wait until the outcome matrix fills;
     - do not restart serve before the client joins;
     - consider pre-warming in `demo_combined.py serve`.
   - This is not a code finding for this round.
9. **Residual "test data" strings.**
   - `verificationWords.ts:215` (AUTHORED_DEMONSTRATION) cannot be reached on the demo. Every demo run is a
     registered Lab simulation, and the Portfolio shows "example data" for the source. But its sibling at `:213` is
     visible: that is M3.
   - `EvAssessmentViews.tsx:451` renders only through `SourceReasons` when the EV source is blocked (lines 506 and
     535), and then inside the tech disclosure. The demo EV source is coherent, so it cannot be reached. Its siblings
     at `:452-453` ("Registered test sources") are the same.

## Checks I ran (read-only)

- `node tools/checks/mock-deviation-labels.mjs`: OK, 153 files, labels tagged, ids registered, hide rule present.
- `node tools/checks/missing-claim-scan.mjs`: passed, with 43 tagged uses and 10 baselined (merge-base `06543e540`).
- `node --test` over `test_mock_deviation_labels.mjs`, `test_evidence_checks.mjs` and `test_missing_claim_scan.mjs`:
  50 passed, 0 failed.
- `pytest` over the pure tests `test_polish_pa2a_server_copy`, `pa1_board_truth`, `pa2b_plan_due_assets`,
  `pa3_ev_tariff_copy`, `test_demo_combined_links`, `test_demo_combined_finish_co1` and `test_cc_placement`: 83 passed
  in 2.07 s.
- Read the capture PNGs for `portfolio-week`, `kobo-board-S`, `ev-board-fault` and `kobo-verification` (1440).

## Not verified

- `npx tsc --noEmit`, vitest and the frontend build were not run, to respect the memory constraint. Frontend type and
  test results rest on the packet (3594/3594 at `c5277805b`, 282 scoped at Addendum 14).
- The slow demo test and check-all were not rerun; the guard parts were rerun as above.
- Cold and EV open-disclosure prose has no capture. The PB-3 residual stands, and M1 widens it to the Finding and
  Action pages.

## Re-review: whole-diff fix round (`84a2914ab...2d702a961`)

Reviewer: a fresh Claude reviewer. The review covers only the fix-round diff, which is these commits:

- `a08bf548b`
- `e547140a7`
- `9d96ffc04`
- `945002e04`
- `feb9ee4f7`
- `2d702a961`

The review was read-only. I confirmed the worktree head is `2d702a961`.

### Verdict: ACCEPT

- M1, M2 and M3 are closed.
- L1-L5 and item 8 are addressed.
- There are two new Low findings. Neither blocks the owner walkthrough, and neither do the residuals the packet lists.

### Closure checks

#### M1: closed

- `ExactReferences` now returns `WorkedOut` (`frontend/src/ui/ProductStatus.tsx:191-194`).
- With no `extra`, it renders one closed `<details data-technical-details>`. The `data-disclosure` and
  `data-exact-references` hooks are kept (`ui/TechnicalDetails.tsx:69-78`).
- With `extra`, the ids nest inside `TechnicalDetails` and the `extra` content stays plain (`:80-93`).
- Only three of the 18 Site files pass `extra`. None of them leaks an id:
  - `FindingConsequence.tsx:939`: the counted-readings table is now wrapped in `TechnicalDetails`
    (`FindingConsequence.tsx:456-492`). The method paragraphs stay plain.
  - `SiteFinancials.tsx:836`: plain links and prose, with no ids.
  - `FoundationRevisionPanel.tsx:228`: its `extraReferences` go into `references`, not `extra`.
- Nothing a client needs is newly hidden. The only content that moved deeper is the counted-readings table (From, To,
  kW, l/kWh), which now opens two folds down. That is a preference, not a gap.
- Coverage did not drop. The test pin changes are casing and summary text only, and `productStatus.test.tsx` gained one
  test for the nesting.

#### M2: closed

The rows the fix round changed now match the `.txt` captures:

- **R08** now leads with "closed by POLISH".
- **R625** (`portfolio-week`):
  - "Can't be compared across these sites yet";
  - "Not known yet";
  - the strip at lines 81-86: "Not assessed / priority sites / Unknown / opportunity / Unknown / site evidence gaps".
- **R628** (`ev-board-fault`):
  - "Charging income estimate not available yet";
  - "Publish a charging tariff";
  - "Needed before charging income can be estimated.";
  - "No published EV tariff covers the eligible delivery".
- **R631:** both "From 30/27 Oct 2026, 16:00" lines.
- **R632:** "60 min → 0 min", "0 kWh", "Critical demand not served" and "Verified".
- **R634** (`kobo-board-S`): "ACT-001 Verified on example data" and "no lower supply cost per kWh".
- **R656:** narrowed to the shared components and the 28 captures.

I spot-checked other rows against the same captures, and the text is present in each:

| Row | Text found |
|---|---|
| R626 | "No fuel cost estimated" |
| R627 | "No objective declared" / "1 verified result" |
| R630 | "Repeated maintenance without a result" |
| R635 | "Energy cost per km needs odometer readings and a published charging tariff" |
| R646 | the Site names |
| R652 | "View an earlier point in time" |
| R660 | "Incident INC-005" |
| R661 | "2 overdue" / "Overdue" / "Due soon" / "Not yet approved" |
| R662 | "What-if" / "Stock may be at risk" |

#### M3: closed

- The `kobo-verification` text uses only "Example data" and "example data" (lines 22, 24, 82 and 88).
- It has 0 hits for "Lab trial", "demonstration" or "test data".
- The copy changed in `verificationWords.ts:213-215` and `productWords.ts:260`.
- The new rule (`tools/demo-combined-vocabulary.mjs:31`) can fail. Its self-test expects `lab name:Lab trial data`,
  which the old regex cannot produce.
- The packet records a mutation proof: 13/14 with the rule removed.

#### L1-L5 and item 8

- L1-L5 are addressed as listed in the packet table. The L1 residuals are discussed below.
- **The L4 rule** (`demo-combined-vocabulary.mjs:19`) neither double-counts nor misses codes:
  - The `(?!000)` lookahead sits at a fixed position, right after `-`.
  - A code with three or more leading zeros is counted only by the zero-padded rule.
  - Every code of six or more digits with fewer leading zeros is caught by the new rule.
  - Display codes (3-5 digits, at most two leading zeros) pass both rules.
  - The self-test pins `ACT-001000` + `ACT-000001` = exactly 2 hits.
- **The item 8 pre-warm** (`tools/demo_combined.py:183-209` and `:563-570`):
  - It runs once, after the first tick.
  - It does not block serving: the API is a separate uvicorn child process. Only the tick loop waits, for at most
    `PREWARM_TIMEOUT_SECONDS=900`.
  - Timeouts and transport errors are caught by `except Exception`. They print "pre-warm did not finish" and no
    `ready:` line.
  - Ctrl+C still propagates.
  - One gap remains for non-2xx statuses; see L-B.

### New findings

#### L-A (Low, preference/residual): ids on the Finding History page

Finding History is one click from the Finding page, and it still shows ids outside Technical details. This code is not
covered by the shared components.

- `frontend/src/sites/SiteFindingHistory.tsx:461-467`: a visible line, "Related Findings: {label} Finding
  `<8-char id>` - its history". This is the exact pattern the `finding id label` rule targets.
- `:576-641`: the plain "Times and references" disclosure shows `model_version` and 8-character assessment ids.

**Why it matters:** R656's narrowed wording is now accurate, so the register does not overstate anything. The only
effect is a stray id if the presenter opens History on a Finding that has relations.

**Fix:** move these into `TechnicalDetails`, or show the related Finding's title or date. This can wait for a
post-walkthrough copy pass.

#### L-B (Low): `prewarm` prints `ready:` for any HTTP status

A 4xx or 5xx is returned as a status (`demo_combined.py:197-199`), so serve still prints "ready: … answered HTTP 500".
The runbook says to wait for `ready:`.

**Fix:** print `ready:` only for a 2xx status. For any other status, take the "did not finish" branch and include the
status.

This is not blocking: the line carries the status, and the recorded run answered 200 in 11 s.

### Residuals the packet lists: none blocks the walkthrough

- **"Review Finding" and "Open Finding →"**
  - Where: `EstatePortfolio.tsx:182`, `coldSiteViews.tsx:662,703`, `EvAssessmentViews.tsx:347` and
    `EvSiteViews.tsx:237`.
  - These are button and link labels, not prose, and v69 contains neither wording.
  - The capital is inconsistent beside "Open the finding", but this is cosmetic.
  - Fold it into the post-walkthrough copy pass. Include "Service disruptions recorded in Findings" in the same pass
    (the Portfolio Protect card, `portfolio-week-1440.txt:56`).
- **"Demonstration data" as the foundation Mode value**
  - It appears only on the `-open` stress capture, inside Technical details (`kobo-board-S-open-1440.txt:902-903`).
  - It is audit content, which a client reaches only by opening Technical details.
- **The "Gross tariff estimate" tile**
  - This is mock wording (v69 uses it 4 times), registered under R628 and R655.
  - It does not appear in the `ev-board-fault` capture text, so the demo board shows no conflict with the new
    headline.

### Evidence verified

- **`var/polish_full/check.json`:** 17 rows, all pass.
  - It was built at `e547140a7`.
  - The only later code change is the `performanceDispatch.test.tsx` pins, so the build matches the reviewed product
    code.
- **`captures.json`:**
  - `strict: true` and 28 captures.
  - All settled, none overflowing, 0 counted.
  - `capture-run.log` shows 28 OK lines and "0 counted hit(s) … (strict)" on the run that wrote the captures.
- **Not checked against an artifact:** the full vitest result (3593/3595) and check-all (12/12). I reran the affected
  files myself instead (see below), and they pass.

### Checks I ran

| Check | Result |
|---|---|
| `node --test tools/checks/test_mock_deviation_labels.mjs` | 14/14 pass |
| `node tools/checks/mock-deviation-labels.mjs` | OK, 153 files |
| `pytest test_demo_combined_links test_cc_placement test_out_b3_cold_ev test_cov_partial_portfolio` (pure tests; `test_w207` not rerun) | 78 passed in 1.7 s |
| `npx.cmd vitest run` over 11 files (listed below) | 453/453 pass, including `performanceDispatch` 44/44 |

The 11 vitest files:

- `productStatus`
- `performanceDispatch`
- `siteFinding`
- `siteActionVerification`
- `estatePortfolio`
- `siteFindingEvidence`
- `s404SiteFindingIndex`
- `siteFinancials`
- `evEnergy`
- `estateEvidence`
- `estateFinancials`

### Not verified

- `tsc --noEmit`, the full vitest suite, check-all and the build were not run, because of the memory constraint.
- There was no serve or browser run. The pre-warm timing and the captures rest on the recorded artifacts.
