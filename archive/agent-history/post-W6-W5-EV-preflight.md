# W5-EV-Work pre-flight (post-W6)

Pre-flight only: nothing was built, tested, captured or written to a DB. Code anchors are from main `14696fda` (`AssetOpsV1-plan2`), which includes shell, W3, W1-a, W1-b, W2-EV and W6-global. W2-cold (`task/post-W6-W2-cold`) and W4-mini (`task/post-W6-W4-mini`) are still on branches. Both touch `SiteAnalyticsFrames.tsx` and `primitives.css`. W4 also touches `operatorSiteTabs.tsx` (R333 wrap, R453 label) and `siteWorkCases.tsx` (R322). **Build on main after both have merged**, then re-anchor the hunks below.

Authority: the W5-EV card (`post-W6-audit/fix-slices.md:173-195`); classification rows B16-06/07/16 and B17-04/06/08; batch-16/17 ledgers; and these rulings:
- W2-EV cross-card rulings 3, 4 and 5, plus Q11, Q14, Q23, Q28-Q30 and Q31.
- W2-cold rulings 4 and Q13: EV depth/work duplicates belong to W5-EV; the cold and `domainActionClient` B14 copies belong to W5-cold.
- W6 rulings Q13 (unknown-address pattern) and Q20 (the R373 EV case-detail 503 belongs to this card).
- W4 rulings Q1 (R322 shared case refusals), Q10 (cold Action refusal taxonomy) and Q17 (R333/R453 tab wrap).
- UI guide `frontend/docs/architecture/ui-ux-decision-guide.md`.

All paths below are relative to `frontend/src` unless stated otherwise. SAF = `shell/SiteAnalyticsFrames.tsx`.

## (a) Build plan per D3 item

### R345 (B16-06) availability: schedule count and units
- **Change:**
  - `connectorHoursText` hard-codes plurals: `EvAvailability.tsx:102` ("N connectors × X scheduled hours") and `:104` ("across N connectors"). Replace them with the existing `plural(n, one, many)` (`EvAssessmentViews.tsx:189`, already imported by `EvSiteViews.tsx:28`). Cover connector and connector, hour and hours, and verb agreement.
  - Cards `:301-304` currently show `dur()` → `durationText` ("X h Y min", `evDepthClient.ts:418`). Render them as the mock's `{hoursText(seconds)} connector-h` instead (mock `index.html:589`), using `hoursText` (`:58`). This is the true unit: seconds summed across connectors.
  - Keep the exact "X h Y min" value in the card's `title` and in the existing detail. `knownTimeNote` (`:107-116`) keeps "hours".
- **Tests (`sites/__tests__/evDepth.test.tsx`):** 0, 1 and 2 connectors; 1 h vs 1.5 h vs 8 h; a "connector-h" card unit; the exact value in the title.
- **Recapture:** all availability cases (part of the 124).

### R346 (B16-07) energy: bridge row, refreshed copy, chart
- **Bridge row 1.** `bridgeRows` (`EvEnergy.tsx:63-80`) reads `c.quantity_kwh` whenever a consequence exists (`:71`). A read-guard consequence (`state === "WITHHELD"`, built in `backend/.../ev_site_reads.py:366-370` with `quantity_kwh: None`) therefore shows "Unknown" next to a card showing 15 kWh. Change: when `c.state === "WITHHELD"` and `c.quantity_kwh === null`, fall back to `e.metered_complete_kwh` with the same "kWh complete-record delivery" wording as the `c === null` branch (`:69`).
  - A stored consequence with a null quantity stays "Unknown".
  - Same read, same measurement as the card (mock row 1, `index.html:598`).
- **"The gross tariff scenario is being refreshed."** This is backend copy: `MONEY_COPY["STALE_BASIS"]` (`ev_site_reads.py:36`). It is emitted on a CURRENT read when a tariff basis derives but no stored consequence matches it (`:323-329`). It reaches the bridge "Limit" cell (`EvEnergy.tsx:75`) and also EV Overview and EV Financials. Changing it alters a claim and a backend string, so it is **Question 3**. Until that is answered, build nothing for this sentence.
- **Point-only chart.** This is an accepted D1, **R06** (register line 24). The pins are `evDepthGraphics.tsx:4-8` and `EvEnergy.tsx:9`, but the page shows no visible label. Add one 12 px `MOCK DEVIATION D1 (R06)` line, with `data-mock-deviation`, directly under `EvDepthPowerChart` (mounted `EvEnergy.tsx:175`). This needs no new register row.
- **Tests (`evEnergy.test.tsx`):**
  - WITHHELD consequence with metered 15 → "15 kWh complete-record delivery".
  - Stored consequence with a null quantity → "Unknown".
  - `c === null` path unchanged.
  - R06 label present.
  - Q3 copy test once ruled.
- **Recapture:** all energy cases.

### R347 (B16-16, plus B17-15) apply W2-EV's tab override to the depth and work mounts
The mechanism is `OperatorSiteTabs` `hrefs`/`search` (`shell/operatorSiteTabs.tsx:106-127`), `EV_SITE_TAB_HREFS` (`shell/evSiteRoutes.tsx:39-43`), and `renderEvTabs`/`selectedWindowSearch` (`sites/evSelectedWindow.ts:9/19`). Per W2-EV Q14 and Q23, tabs carry the loaded read's own `from`/`to`/`known_at`; a refused or no-window read carries none.

| Mount | Current gap | Change |
| --- | --- | --- |
| availability, energy | SAF:270 passes the overrides, but depth mode calls `renderEvTabs(props.tabs, "")` (`EvAssessmentViews.tsx:703`), so the search is always empty | Depth pages report the loaded `read.window` to the frame (one `onWindow` callback, or pass `selectedWindowSearch(read.window)`). The empty string remains for refused or loading reads |
| ev-health | `shell/SiteHealthFrames.tsx:71` passes neither prop | For EV, pass `EV_SITE_TAB_HREFS` and the search from `EvHealthDepth`'s loaded `read.window` (already used by `sessionsHref`, `EvHealthDepth.tsx:58-60`) |
| ev-scenarios | `EvSiteViews.tsx:442-449` reads the search from `ReportSelected`, but `EvScenarios` never reports | `EvScenarios` reports its loaded `read.window` (`evScenariosClient.ts:60`) |
| ev-work (Actions) | SAF:2054 `<OperatorSiteTabs siteId current="Work" />` passes neither prop | For EV only: overrides, plus the search from the explicit URL `from`/`to`/`known_at` when the list read loaded (planned choice C7). Cold is left to W5-cold (R339) |
| ev-work-incidents / maintenance | SAF:~2254 (B17-15 is merged into B16-16) | Same as ev-work, for EV |
| ev-action | Mock root is **Actions** (`screen-manifest.json:1310-1313`), with no Site tab row | No `OperatorSiteTabs`. The Action tab and crumb use the validated window (see R348) |

- **Tests:**
  - EV/mini/cold tab hrefs on each mount: loaded carries the window, refused carries none, and a historical `known_at` is kept.
  - Update existing tab tests in `evDepth`, `evHealthDepth`, `evScenarios` and `evWorkActions`.
- **Recapture:** all depth and work cases. After rebasing on W4, check that the R453 wrapped tab row and its label hold on EV rows at 390.

### R348 (B17-04) ev-action: invalid window ignored and carried onto its own links
- **Change:**
  - SiteActionFrame (SAF:1711-1712) passes raw `from`/`to`. `domainVerificationHref` (SAF:1435-1444) copies them onto the Verification tab (SAF:1481/1524) and the redirect (SAF:1648), and the detail key (SAF:1622) ignores them.
  - Validate EV `from`/`to` with the existing `invalidScope`/`isUtcInstant` (`domainActionClient.ts:376-402`), imported only, with no edit to the client.
  - If the window is one-sided, reversed, longer than 31 days or not UTC: render the R348 invalid-window refusal in the R110 state panel. It has `role="alert"`, the W2-EV ruling-5 sentence for the cause, and title "Window cannot be read". Make no detail read.
  - Offer one link, `Open this Action without a window` (keeps a valid `known_at`). No Retry.
  - Links on a valid window carry it unchanged.
  - Make `windowQuery` (`DomainActionVerification.tsx:63-64`; set at `evWorkPresentation.ts:111`, `coldWorkPresentation.ts:133`) the real switch for window parsing, replacing the `site_type` check at SAF:1712.
- **Tests (`domainActionVerification.test.tsx`; update `:526-529`):**
  - reversed, one-sided, 32-day and non-UTC windows → refusal, no fetch, no carried window;
  - valid window carried;
  - cold ignores the window.

### R349 (B17-06) ev-action non-loaded states
- **Change:**
  - Every non-404 result shows "EV work unavailable" (`evWorkPresentation.ts:27/108`), the raw `state.message` (SAF:1574) and an unconditional Retry (SAF:1575-1579). The h1 reads "Action" (SAF:1512, :1642, :1695).
  - Map by **code and status**, following the W4 Q10 taxonomy (the cold B15-04 copy) with the EV noun:
    - 422 `INVALID_KNOWN_AT` → `Choose a valid evidence cutoff.`
    - 403 → `You do not have access to this site.`
    - 503 or network failure → `EV work is unavailable right now. Try again.`, with **Reload**.
    - 404 `ACTION_NOT_FOUND` keeps `Action was not found at this site.`
    - 409 → `The Action changed while it was being read.`, with Reload.
    - Any other code → `The Action could not be read.`
  - No Retry on 403, 404 or 422.
  - The raw code and message move to a labelled `Technical detail` disclosure (status, code).
  - The h1 becomes `Action not found` (404), `Action unavailable` (other refusals) or `Loading Action…`. The loaded title is unchanged.
  - Keep R110's single untitled panel.
- **Tests:** replace the `:549-568` it.each that pins raw message and Retry; network `:623`; h1 per state; no raw text in the main panel.
- **Recapture:** ev-action 403, 404, 503 and refused-bad-known-at.

### R350 (B17-08) Action section addresses
- **Current main:** W1-b R222 already aliases `/overview` to the bare route for every Site type (SAF:1678-1680). Bare probes then redirect to `/verification`, which is the domain canonical page, so R350's "check the existing `/overview` destination" is satisfied. Verify it by link-check recapture; no chrome rewrite.
- **Remaining gap:** `W1_ONLY_SECTIONS` (`plan`, `execution`, `evidence`, `history`; SAF:1416) are probed and silently redirected to Verification (SAF:1647-1648), or fall to W1 on a non-loaded read (SAF:1650).
- **Change (W6 Q13 pattern):**
  - Reuse the layout of `WorkRequestUnknownSectionFrame` (`work/workRequestShared.tsx:455-487`): header `Page not available`, panel `This address is not served`, link `Open this Action's verification`.
  - The link keeps a validated `known_at` and (for EV) a valid `from`/`to`.
  - Make no API read and no redirect.
  - Bare and `/verification` are unchanged; `/overview` stays the R222 alias.
  - The cold reach is **Question 2**.
- **Tests:** each of the four suffixes plus `/overview`; the link preserves valid params and drops invalid ones; no fetch.
- **Recapture:** the R350 link-check landings (bare, `/verification`, `/overview`, `/execution`, `/history`, `/plan`, `/evidence`) at both widths.

### Merged EV duplicates owned here (W2-cold rulings 4 and Q13)
- **B16-01 → R244: EV depth refusals.**
  - The current state:
    - `EvDepthRefusal` (`EvAvailability.tsx:139-158`; used by Availability `:343`, Energy `EvEnergy.tsx:280`, Health `EvHealthDepth.tsx:196`) and `ScenariosRefusal` (`EvScenarios.tsx:80-98`, `:311`) print the raw code and message (for example `EV_WINDOW_INVALID 'from' must be before 'to'.`).
    - Both show Retry unconditionally and drop all page furniture.
  - The change applies W2-EV ruling 5 and Q11 with the existing helpers `evRefusalText`, `isEvWindowRefusal`, `RefusedHead` and `RefusedGap` (`EvAssessmentViews.tsx:80-166`):
    - Keep the strip and each page's normal tile labels with `Not assessed`.
    - Add one in-panel sentence and a technical disclosure, with no page banner.
    - The title is "Window cannot be read" only for window codes.
    - 403, 404 and 503 keep their specific titles and the requested-window line.
    - Reload only on 503 or unreachable.
  - Adapt `ColdRead` to `EvRead` (both carry `httpStatus`) with a small local mapper. Do not change the helper signatures.
  - The correction is a link (planned choice C3).
  - **Tests:** reversed, one-sided and >31-day `EV_WINDOW_*` codes, 403, 404 and 503 on all four pages. Update `evDepth.test.tsx:310-316`, `evEnergy.test.tsx:269-274`, `evHealthDepth.test.tsx:198-205` and `evScenarios.test.tsx:182-188`, which pin the raw text.
- **B16-02 → R261: the `domainActionClient` "31 days" message for a reversed window.** The list-message fix is in the shared client, which W5-cold owns (W2-cold Q13). W5-EV does not edit it:
  - If W5-cold has merged first, recapture ev-work refused-reversed/32d as the EV-instance proof.
  - Otherwise record the dependency in the packet.
- **R373 packet: EV positive Site Work case-detail 503 (W6 Q20).**
  - Cause: `tools/w504_ev_work_walkthrough.py:501-502` prepends `build_work_router(None, ..., lists=...)` with no `details`. It is inserted at `:512` ahead of the product router (`backend/assetops_backend/main.py:574-577`). Its `GET /api/sites/{site_code}/work/cases/{case_id}` (`work_api.py:191`) then raises 503 at `:196-197`.
  - Fix (producer tool only, no product backend): pass `details=M.build_work_detail_service(url)` and the product service to that router, exactly mirroring `main.py:574-577`.
  - Rerun `backend/tests/test_w504_ev_intent_api.py`. Its producer route-shape test (`:205`) may need its expected route list updated.
  - Recapture the EV positive case-detail landing reached from ev-work-incidents and ev-work-maintenance rows at both widths.
- **Not here:**
  - B16-04/B17-14 default window is R338, owned by W5-cold for Site Work, in the shared `domainWorkScope` (SAF:1936-1942).
  - B13-04 case refusals are W4 R322 (`siteWorkCases.tsx`).
  - Plurals on the case strips belong to the merged shell.
  - The depth-page Window control ("extend R88/R112") is not among this card's IDs. It is recorded as a residual, not built.

### Tests and recapture totals
- **Focused tests:** `evDepth`, `evEnergy`, `evHealthDepth`, `evScenarios`, `evWorkActions` and `domainActionVerification` `.test.tsx`; shell tab/route tests for SiteHealthFrames and SAF; `backend/tests/test_w504_ev_intent_api.py`.
- **Full suites:** the frontend suite, typecheck, build, and architecture, navigation-truthfulness and missing-claim guards. No backend product change is planned unless Q3 chooses the backend option. In that case run the scoped `ev_site_reads` tests and the tiered backend run per test policy.
- **Recapture:** all 124 indexed pairs (B16 depth 64, ev-work 24, B17 ev-action 36) at 1440 and 390, plus:
  - one-sided and >31-day URL cases on the four depth pages and on ev-action (extra to the index, following W2-EV Q29);
  - the R350 landings;
  - the EV case-detail landing;
  - cold-action landings if Q2 takes the default.
- **Producer:** `tools/w504_ev_work_walkthrough.py` with its port knob and a fresh `ASSETOPS_WORK_CURSOR_KEY_HEX` (W6 Q20).
- **Gaps** (selected-DTO tests, no fabricated screenshots):
  - `unknown` mode (0 SUPPORTED);
  - pending and stale;
  - missing-meter, historical depth and status-gap;
  - authored EV scenario (B16-09);
  - any state beyond Open (B17-12).

## (b) Planned guide-covered choices
- **C1 (§4): units and plurals.** Use "connector-h" with decimal hours, which matches the mock unit, and keep exact h/min in the title. Reuse the existing `plural` import instead of a new module. Check 0, 1 and 2.
- **C2 (§3): refusal mapping.** Map by code and status, not status alone. Reload only on 503 or unreachable with a recoverable view; never on 401, 403, 404 or 422. Raw codes go only in a labelled `Technical detail` disclosure. Use one `role="alert"` per refusal, loading uses `role="status"`, and there are no nested live regions.
- **C3 (§3): correction for an invalid depth window.** With no window control on depth pages, offer a real link, `Read without a selected window`: the same path minus `from`/`to`, keeping a valid `known_at`. The requested window stays visible in the strip line, so the user's selection is preserved.
- **C4 (§3, §4): ev-action non-loaded h1.** Use state-specific plain h1s (`Action not found`, `Action unavailable`, `Loading Action…`) and keep R110's untitled single panel.
- **C5 (§5): R06 label.** Add a visible adjacent `MOCK DEVIATION D1 (R06)` line for the accepted D1, with no new row.
- **C6 (§2, mock root): ev-action tabs.** Add no Site tab row on ev-action, because the mock places it under the Actions root. Window propagation goes through the Action tab and crumb.
- **C7 (§2, W2-EV Q14/Q23): which window the Work tabs carry.** Work tabs carry only explicit URL `from`/`to`/`known_at` that the loaded list read accepted. The implicit 7-day Work default is not pushed onto evidence pages as if it were a selected evidence window.
- **C8 (§1): caps.** Use the ruled caps from the docket: ev-health Condition and evidence 400/800 and ev-work Actions at this site 550/800. Unruled panels get a provisional `50 × ceil(peak × 1.15 / 50)` from the worst closed peak, including the new refused strip and tiles. Those panels are the three availability panels, the energy panels and bridge, ev-scenarios Financial scenarios, and ev-action Declared verification plan / state panel. Measure with five-row, 160-character probes where rows lengthen (ev-work, ev-action criteria). All-open is exempt and must not clip.
- **C9 (§2): phone layout.** Keep the energy tables' inner horizontal scroll with its cue at 390, keep zero document overflow, and keep 24 px minimum targets for the new links and Reload.
- **C10 (§5): tests.** Use pure selected-DTO tests for every unproducible state. Settle store reads with `settledScreen`.

## (c) Escalation-only Architect questions (4)

1. **Card file list (scope).** R347 and R350 cannot be built inside the listed files. Confirm these additions, with EV-only hunks:
   - SAF (`:270`, `:1416-1712`, `:2054`, `:~2254`);
   - `shell/SiteHealthFrames.tsx:71`;
   - `sites/EvAssessmentViews.tsx:703` (tab search in depth mode, plus reuse of its refusal helpers);
   - `sites/evWorkPresentation.ts` and `coldWorkPresentation.ts` (the `windowQuery` switch);
   - the producer tool `tools/w504_ev_work_walkthrough.py:501-512`, for the W6 Q20 503;
   - `backend/tests/test_w504_ev_intent_api.py` expectations only.

   **Default: authorize.** Shared SAF and tab hunks rebase after W2-cold and W4-mini.
2. **R350 cold reach (ownership).** `W1_ONLY_SECTIONS` dispatch (SAF:1416, :1701-1704) is one branch for COLDCHAIN and EV_CHARGING, and B17-08 is marked "shared with cold". W5-cold's card does not own it.

   **Default: apply the unknown-address panel to both domains in that one branch.** W5-EV adds cold-action link-check landing recaptures and a cold test. The alternative is to gate on EV only and leave cold's silent redirect for a later card.
3. **B16-07 "The gross tariff scenario is being refreshed." (claim and backend copy).** `ev_site_reads.py:36` uses it for `STALE_BASIS` on a CURRENT read (no stored consequence matches the derived basis, `:323-329`). It implies a recompute is in progress, which nothing proves, and it shows on energy, EV Overview and EV Financials.

   **Default: authorize a one-string backend change to `No stored gross tariff estimate matches the current evidence.`** This is not a wire, schema or field change. Update the scoped backend test and recapture representative ev and ev-financials pairs.

   Alternatives:
   - map `reason === "STALE_BASIS"` in `EvEnergy.tsx` only, which leaves the other two pages inconsistent;
   - leave the sentence unchanged and close R346 on the bridge quantity alone.
4. **Register block (numbering).** No new row is expected (see d), but W5-EV has no reserved range. **Default: reserve R460–R469 for W5-EV-Work** after W4's R450–R459. Suggest R470–R479 for W5-cold if it is unassigned.

## (d) Register numbering need
- **Existing rows used:**
  - R345, R346, R347, R348, R349 and R350 close in place after tests, review and paired recapture.
  - R06 gets its visible label.
  - R110 and R112 are unchanged (R112's stale "planned" status is already "built; audit verified" on main).
  - The R244/R261 EV instances are reported for their merged rows.
  - R453 is inherited from W4.
- **Expected new rows: zero.** The unknown-address state, refusal copy and unit wording follow existing rulings and the mock.
- **If a departure appears during the build** (for example a D2 for the depth-page correction link if the reviewer judges it a layout change), use the reserved block from Q4, never self-allocated.
- **Current register state:** main ends at R421 (R396 W6; R420/R421 W2-EV). R422–R449 are reserved for W2-EV/W2-cold and R450–R459 for W4.
