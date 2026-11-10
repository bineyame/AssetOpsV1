# Architect proposal: Portfolio layout, coverage once and section tabs (2026-11-10)

- Architect: Claude (fresh `assetops-architect` instance). Binding checked: `.ai/ROLE_CONFIG.md`, Architect = Claude since 2026-10-27.
- Owner feedback, verbatim: `.agent/owner-walkthrough-2026-11-10.md` (item 1 money, item 2 coverage and layout).
- **Status: proposal for discussion. Nothing is built, and no spec, register or product code changes, until the owner approves the mockup draft.**
- **Approved by the owner (2026-11-10, items 5 and 12):**
  - the tab set, the top three findings kept on the Overview, and the term family (item 5);
  - the item 9 scalable outcomes design ("for now"), the region attribute (+0.25 units, so PF is 4.25 units), and "By outcome group" as the default view (§9.8).
- **Added on 2026-11-10:** one shared date range for every page (SR, 1.75 units, its own slice; §"Item 12.5"). The mockup shows it as Change 0b.
- Mockup draft: `frontend/mockups/v71/portfolio-tabs.html` (open it in a browser; the top bar switches between Proposed, Current v7.0 and Side by side, and "Show change notes" explains each change in place). v70 is unchanged.

## 1. In plain words, for the owner

- **Coverage once.** Today the Portfolio repeats "how many days were checked" up to seven times: once per partly checked Site in the header row, again under every one of the four cards, again in the findings count, again on every finding row of a partly checked Site, and again in the scope drawer. The proposal shows it **once**, in one line under the date range and above everything else: "Some days are not fully checked yet · Kobo … · GreenHarvest … · Depot … · Every figure on this page uses only the checked days · Which days, and why →". The link opens the detail tab.
- **Two things stay on purpose.** (1) A card keeps its own days line **only when its figures come from different days** than the shared line (for example, Grow potential from a separate study). (2) The short words "on the days checked" next to a zero stay, because "None found" alone would read as "none in the whole period". That is a few words, not a repeated list.
- **One thing I found that needs fixing first.** The header row and the cards count "checked days" by **two different rules** today (the header uses "an assessment exists for the day"; the cards use "the day's readings are fully checked"). While they are shown in different places, nobody notices. Shown once, the line must use one rule. I propose the cards' rule (fully checked), with "not assessed yet" days named in the same line. This is a small server change.
- **Section tabs: yes, with one change.** A row of tabs under the coverage line: **Overview · Act first · Outcomes by site · Opportunity · What changed · Scope & coverage**. The cards stay on Overview. Each tab has its own address, and the date range travels with it.
- **My pushback: keep the top three "act first" findings on the Overview.** The page's job is "where should management act first". If that only lives on a second tab, an executive who lands on the page sees four cards and no instruction. So the Overview shows the top three with "See all 6 findings →", and the full ranked list, lenses and warnings sit on Act first. The counts strip on the Overview becomes links to the tabs, so the Overview doubles as the table of contents.
- **Words for "checked" (item 3).** "Checked" goes wherever it describes data. The new words say what arrived: **complete readings, partial readings, too few readings, no readings received, still processing, not analysed yet**, each defined in one line on the page (section 10). "7 of 8 hours checked" exists only in the v7.0 mock, not in the app; by the app's own rule 7 of 8 hours is a complete day, so the mock now reads "complete readings · 1 of 8 operating hours missing".
- **Frame unchanged (item 4).** The draft uses the v7.0 left menu exactly, copied from its shell, and the date range sits at the top of the screen in the top bar on every tab, where v7.0 has it (section 11).
- **Size and timing.** About **2.25 build units** (coverage once 0.5, tabs 1.0, wording 0.75). **Not before Thursday**: the technical demo build is frozen Wednesday, and this changes the page the demo opens on. It **should land before the client session**, in a lane beside ANY-1, before ANY-2 starts on the same Portfolio code.

## 2. Item 1, money: recorded

- `.agent/backlog-post-demo.md` now marks D-MONEY.1-5 **owner-approved for the backlog, 2026-11-10**, in two parts:
  - **BL-66 row:** MN-1/2/3 folded into ANY-2 / AR-4 (AR-4 1.5 → 2.5, ANY-2 3.75 → 4.75, BL-66 6.75 → 7.75). ANY-1 unchanged; its contract takes D-MONEY.1-4 before AR-1's migration.
  - **BL-67 row:** FX store, structured tariffs, restatement note, settlement ledger only if billing; post-demo.
  - A short owner decision log at the end of the file.
- **Still open (owner):** Q1 reporting currency and rate; Q2 restatement style (restated figure with a note, recommended; or original plus an adjustment line); Q3 will AssetOps ever invoice.

## 3. Item 2a: where coverage shows today (verified in code)

| # | Place on the Portfolio | Text (shape) | Source |
|---|---|---|---|
| C1 | Header row badge and sentence | "Some days not checked yet" / "Portfolio: Partly checked" | `portfolioWords.ts:97` `contextWords` |
| C2 | Header row, one note per partly checked Site | "{Site}: {c} of {n} days checked · {g} days not available yet · not assessed: {days}" (R620) | `EstatePortfolio.tsx:785-796`, text from `estate/coverage.py:216-232` `_days_block` (rule: an assessed selection exists for the day) |
| C3 | Under each of the four cards (`oc-pfdays`) | "{Site}: {k} of {m} days checked · {p} partly checked" per Site, " · "-joined | `site_outcomes/read.py:746-754` `_site_days` (rule: day graded COMPLETE, CH6b3-R3 M1). **Protect and Assure carry the identical all-Site line**; Grow and Optimize carry only the Sites that have an income or cost claim, with that claim's days |
| C4 | Card values and the counts strip | "None found on the days checked", "{n} found on the days checked" (R670) | `chain/vocabulary.py:96-106`, `EstatePortfolio.tsx:103-118` |
| C5 | Grow parts | "Estimated income from checked days", "{amount} over {k} of {m} days checked" | `vocabulary.py:287-311` |
| C6 | Findings panel heading and count | "{n} findings · some days not checked" (twice: eyebrow and lens row) | `EstatePortfolio.tsx:284`, `:300` |
| C7 | Every finding row of a partly checked Site | "Partly checked · value shown once every day is checked" | `EstatePortfolio.tsx:121-128` `partialConsequence` |
| C8 | Scope drawer, per-Site table | coverage state and "Days not checked yet: {days}" | `EstatePortfolio.tsx:636-643` |
| C9 | Footer | "Other Sites may lack comparable full-window coverage." | `portfolioWords.ts:122` |
| C10 | "Why?" dialog | "Days used" per claim | `chain/why.py:141`, `chain_api.py:388` |

**Finding (defensibility, must be settled before the one line is built):** C2 counts days by the estate selection rule, C3 by the chain day grade. The same Site can read "31 of 31" in C2 and "28 of 31 · 3 partly checked" in C3. One shared line needs one rule.

## 4. Item 2a: proposal (coverage once)

- **PF-C1, one estate coverage line (server).** The estate summary carries one `coverage_line`: per Site, the chain day grade (fully checked / partly checked / too little data), plus the estate "not assessed yet" days named in the same clause. It is built once, from the same `counted.days` the cards use, so the line and the card figures cannot disagree. Words are server text (CH-6b2 rule: the browser renders, never composes).
- **PF-C2, cards show an exception only.** A card's `days_line` is sent only when its day set differs from the shared line (Grow: income or study days; Optimize: cost-claim days). Protect and Assure lose theirs (today they repeat the shared line byte for byte). The card label reads "Different days: …".
- **Removed:** C2 per-Site notes (absorbed into the line), C6's second copy (keep one, on the tab label count only), C9 (moved to the Scope & coverage tab).
- **Kept:** C1 badge (the state, not the days); C4 and C5 qualifiers (removing them makes zeros read as whole-period claims; R670 and D-W1-4 stay); C7 shortened to "Value shown once every day is checked" (the row's value cell is empty otherwise, so the reason must sit there); C10 "Why?" days (the deep explanation of one claim).
- **Per-Site exceptions in the line itself:** a Site whose coverage differs is named inside the one line ("Depot: 6 Oct, 7 of 8 hours"); a Site that is fully checked reads "{n} of {n} days checked"; when every Site is fully checked the line collapses to "All days checked" (green, no list).
- **Deep view:** the line's link opens the Scope & coverage tab: per-Site days, the named days not checked, assessment periods, what is left out and why, and the reference ids (today's scope drawer, unchanged in content).
- **Registers touched at build:** R620 and R622 replaced; R670 kept; MD-CH5b-4 and the `oc-pfdays` rows (BL-13) revisited.

## 5. Item 2b: sections on the Portfolio today

From `EstatePortfolio.tsx:751-842` and v70 `portfolio.js:43-60`:

| Section | Component | v70 place |
|---|---|---|
| Date range and evidence cutoff | `EstateDateBar` | top bar |
| Context row: badge, Site counts, per-Site partial notes, "Assessment scope & periods" drawer | `Loaded` header, `ScopeDisclosure` | `portfolio-context` |
| Four outcome cards with "Why?" and Site dots | `CategoryCards` | `oc-pfgrid` |
| Counts strip (priority Sites, opportunity, evidence gaps, accepted actions, warnings) | `portfolio-pulse` | `portfolio-pulse` |
| Where management should act first: lenses, ranked table, load more, early warnings | `PriorityPanel` | `portfolio-main` left |
| Outcomes across the estate (matrix and key) | `ObjectivesPanel` / `OutcomeMatrix` | side column |
| Evidence that would change a decision | `EvidenceAside` | side column |
| An opportunity beyond reducing cost | `OpportunityPanel` | bottom left |
| What changed in this review (with basis drawer) | `ProgressPanel` | bottom right |
| Business context footer | `ContextFooter` | footer |

## 6. Item 2b: the proposed tabs

| Tab (label) | Contents | Address |
|---|---|---|
| **Overview** (default) | four cards; counts strip as links to the tabs; top 3 "Where management should act first" with "See all {n} findings →" | `/portfolio` |
| **Act first** {n} | full ranked table, lenses, load more, early warnings; "Evidence that would change a decision" beside it (as in v70) | `/portfolio/act-first` (+ `lens`) |
| **Outcomes by site** | the matrix at full width, its key | `/portfolio/outcomes` |
| **Opportunity** {n} | the opportunity panel | `/portfolio/opportunity` |
| **What changed** {n} | the progress panel; its basis drawer content | `/portfolio/changes` |
| **Scope & coverage** (the deep tab, right-aligned) | per-Site days and gaps, assessment periods, exclusions, reference ids, business-context footer | `/portfolio/scope` |

- **Above the tabs, shared by all:** page title, date bar, context badge, the one coverage line. They apply to every tab, so they never move.
- **Addresses:** every tab link carries `from`, `to`, `known_at` (as `operatorSiteTabHref` does for Site tabs). `lens` belongs to Act first only. An old `/portfolio?lens=X` link redirects to `/portfolio/act-first?lens=X`; an unknown tab redirects to Overview. Card links, "Why?" and Site links are unchanged.
- **Loading:** one route `/portfolio/:tab?` keeps the page mounted, so switching tabs uses the reads already loaded (no refetch, instant). The reads stay as today (portfolio + outcome summary). Splitting reads per tab is a later speed option for ANY-2, not part of this.
- **Counts on tab labels** come from fields the page already has (`total_count`, `opportunity_count`, accepted actions). A count that is unknown shows no badge, never "0".
- **Phones (≤760 px):** the same rule as the Site tab row (R453): the row wraps so every label stays visible, current tab underlined; the coverage line wraps Site by Site; the top-3 list stacks.
- **Accessibility (WCAG 2.2 AA):** a `<nav aria-label="Portfolio sections">` of links with `aria-current="page"`, not an ARIA tablist, because each tab is an address (the same reasoning as `operatorSiteTabs.tsx`). On a tab change, focus moves to the panel heading; the browser back button returns to the previous tab; the coverage line is a `role="note"` read before the tabs.
- **Consistency with the Site pages:** same component family (`site-tabs` styles), same link-not-tablist rule, same window-query carry, same wrap rule. The Site row is a top-level section row; the Portfolio row is the same pattern one level down, as W1-F5b's in-page rows are.
- **Pattern basis:** progressive disclosure and "recognition over recall" (Nielsen Norman Group); GOV.UK / Carbon tabs guidance (tabs for peer sections a user switches between, not for steps; keep the most important content on the first tab).

## 7. Pushback

1. **Do not move "Where management should act first" off the landing view completely.** It is the page's question (v69 §8.1: "Where should management act first, what is at stake, and what would prove improvement?"). Keep the top 3 on Overview.
2. **Do not hide the coverage line inside a tab.** It qualifies every number on every tab, so it stays above the tabs. Only its detail moves to the deep tab.
3. **Do not remove the "on the days checked" words beside zeros**, for defensibility (R670). They are not the repetition the owner saw.
4. **Do not split the page into separate data reads per tab now.** It would turn a frontend change into a backend one, and it collides with ANY-2.
5. **Six tabs, not more.** Evidence prompt and footer join existing tabs instead of getting their own.

## 8. Size and sequencing

| Card | Scope | Size |
|---|---|---|
| **PF-C** Coverage once | server `coverage_line` from `counted.days` + exception-only card `days_line`; frontend line, removals, C7 wording; tests; R620/R622 replaced | 0.5 |
| **PF-T** Section tabs | route `/portfolio/:tab?`, tab row, Overview top 3, pulse links, panels regrouped, redirects, focus, 760 px wrap; tests; captures re-baselined against v71 | 1.0 |
| **PF-W** Wording ("checked" to the readings family) | backend vocabulary and frontend words files (section 10 inventory), tests' expected strings, register rows | 0.75 |
| Mock (this draft) | done; once approved, folded into `frontend/mockups/v71/` as the Portfolio spec | 0 |

- **Total 2.25 units, one slice** (well under the 6-unit split rule). PF-W can also run on its own.
- **Before Thursday: no.** The demo build must be ready a day early (Wednesday); this changes the opening page and the technical script DS-1b's Portfolio steps, and would need build, review and recapture in under a day. For Thursday the presenter can say "coverage is the line at the top; the repeats go in the next build".
- **Before the client session: yes.** Run it as a lane beside ANY-1 (no shared files: ANY-1 is the Site boards). PF-C touches `site_outcomes/read.py` portfolio cards, which ANY-2 / AR-4 also touch, so PF lands **before ANY-2 starts**, or PF-C folds into ANY-2 if ANY-2 is already running. DS-1b's client version takes the new tab steps.

## 9. Questions for the owner

1. Approve the tab set and names (Overview · Act first · Outcomes by site · Opportunity · What changed · Scope & coverage)?
2. Agree to keep the top 3 findings on the Overview (pushback 1)?
3. Agree the one coverage line uses the cards' rule (complete readings) for every Site?
4. Agree the reading words (complete / partial / too few / no readings received / still processing / not analysed yet), and that "complete" means at least 80% of the hours the day needed, stated on the page?

## 10. Item 3: the word "checked" (owner, verbatim, item 3)

### 10.1 What "checked" means today (verified in code)

The day grade is set per measure by `chain/grading.py:76-97` `classify_day`, with the bands in `config/chain/coverage-policy-v1.json` (complete 0.80, partial 0.25). It compares the seconds covered by readings with the hours the measure needs that day (its declared operating or daylight hours):
- COMPLETE: at least 80%.
- PARTIAL: 25-80%.
- LOW: above 0 and under 25%.
- NO_DATA: no readings.
- PENDING: readings arrived but are not analysed yet.
- NOT_EXPECTED: no readings are due.

A measure may set its own threshold: spare solar (`measure_impls.py:164-171`) needs every daylight hour. A day takes the weakest grade of its measures (`chain/read.py:87-97`).

B = backend wording, F = frontend wording.

| Source | Strings (shape) | Technical meaning |
|---|---|---|
| B `chain/vocabulary.py:96-106` | "{n} found / None found / None open / None confirmed on the days checked" | count over COMPLETE days (CH6b3-R3 M1) |
| B `vocabulary.py:287-311` | "{amount} over {k} of {m} days checked · {p} partly checked", "Estimated income from checked days", "At least {total} … from checked days" | money over COMPLETE days; PARTIAL days named |
| B `vocabulary.py:299-302` `days_line.*` | "{k} of {m} days checked · {p} partly checked · {n} with too little data, not counted" | COMPLETE / PARTIAL / LOW counts of the claim's days |
| B `vocabulary.py:194, 210-222` `why.*` | "{label} on {k} checked days", "{c} of {e} days checked", "{d} partly checked", "Checking {n} more days" | the same grades in "Why?"; "Checking more days" means more COMPLETE days would change the answer |
| B `vocabulary.py:278-284` MG-1 | "… on {c} of {e} days checked", "all {m} days checked", "no fully checked day counted yet this month" | month to date over COMPLETE days |
| B `vocabulary.py:538, 547, 553-554` | "on the days checked", ", {sites} not checked", "findings next to unchecked days not shown yet" | COMPLETE days; objectives not judged; Findings held back next to days that are not assessed |
| B `site_outcomes/mini.py:94, 96, 133-134, 186` | "spare solar not checked on the last 5 days", "{g} of the last {n} days have no checked readings yet", "… only partly checked", "the night of {date} could not be checked" | gap line: NO_DATA, versus a day with some COMPLETE or PARTIAL measure; a fuel night that cannot be assessed |
| B `site_outcomes/board.py:73-80` | "no fully checked day since", "{k} more fully checked days to close" | COMPLETE days counted by the close rule (`lifecycle.py:309`) |
| B `site_outcomes/ev.py:52` | "No income figure for this day: it is not fully checked" | the day is not COMPLETE |
| B `actions/verification_families.py`, `actions/fuel_verification.py` | "fully checked days/nights before/after the change", "Nights checked after the change", "Not checked yet" | COMPLETE days or nights used by the verdict; NOT_JUDGED |
| B `outcomes/objectives.py:17-20`, `site_outcomes/objective_facts.py:26` | "Not checked yet", " · {u} not checked yet" | objective verdict NOT_JUDGED |
| B `fuel_balance/night_text.py:28, 42` | "Fuel balance: not checked", "Not checked: {why}" | the night is not assessed |
| F `estate/portfolioWords.ts:97, 148`, `estateShared.tsx:168, 196`, `EstateEvidence.tsx:85` | "Some days not checked yet", "Portfolio: Partly checked", "Partly checked" | estate coverage PARTIAL: some requested days have **no assessment selection**. This is a different rule, from `estate/coverage.py`, whose own text already says "assessed" |
| F `estate/EstatePortfolio.tsx:122, 284, 300, 396`, `estate/findingIndex.tsx:125, 265` | "Partly checked · value shown once every day is checked", "some days not checked", "Nothing seen on the days checked", "{sites} are partly checked; totals are unknown" | the same estate PARTIAL rule; the value is withheld until every day is assessed |
| F `sites/OutcomeBoard.tsx:53, 93` | "None found on the days checked", "No open issues on the days checked" | COMPLETE days |
| Mock only: v70 `outcomes.js:114-119` | "6 Oct, 7 of 8 hours checked · 1 hour partly checked" | no app source (10.3) |

These stay, because they are not about data:
- "checked as a safeguard" (`board.py:33, 958, 995`) means an outcome is watched so that a change does not harm it.
- "Checked and working, monitoring" means a verified fix.

Both say that a person checked a change, which is true.

### 10.2 The new words: say what arrived, not whether we looked

| Term on screen | One-line definition shown on the page | Grade |
|---|---|---|
| **Complete readings** | Readings arrived for at least 80% of the hours the day needed (spare solar: every daylight hour). The day is counted. | COMPLETE |
| **Partial readings** | Readings arrived for 25-80% of those hours. The day is shown, and named wherever it is used. | PARTIAL |
| **Too few readings** | Readings arrived for under 25% of those hours. The day is not counted. | LOW |
| **No readings received** | Nothing arrived from the site for that day. | NO_DATA |
| **Still processing** | Readings arrived and are being analysed. | PENDING |
| **Not analysed yet** | The day has not been through the site analysis yet. | estate PARTIAL / UNASSESSED |

How the patterns read:
- Days: "Complete readings on {k} of {m} days · {p} partial · {n} too few".
- Zeros: "None found on days with complete readings".
- Money: "{amount} over {k} days with complete readings".
- Verdicts: "Not judged yet: only {n} of 3 days with complete readings after the change".
- Objectives: "Not judged yet".

Where the mock explains them:
- The coverage line has a "What these words mean" disclosure with all six definitions.
- Each term in the line shows its definition on hover and focus (dotted underline).
- In the build, the same definitions sit in the "Days used" line of the "Why?" dialog.

Basis: Nielsen Norman Group heuristic 2 (use the user's words, not system states), and GOV.UK content style (say what happened).

### 10.3 "7 of 8 hours checked"

- **Source.** This string exists only in the v7.0 mock's example Depot data (`outcomes.js:114-119`, `PFDAYS`). Depot's operating window on 6 Oct was 08:00-16:00, which is 8 hours, and connector 2 was out for 1 hour. The app never shows it, because its day lines count days, not hours.
- **Logic.** Under the app's rule, 7 of 8 hours is 87.5%, which is **complete** (at least 80%). So the mock's "partly checked" contradicts the product. The app's logic is right and the mock is wrong. The v7.1 draft reads: "Depot: 6 Oct complete readings · 1 of 8 operating hours missing".
- **One owner choice: what "complete" covers.**
  - The draft lets "complete" cover a day with up to 20% of its hours missing, and says so in the definition.
  - "Enough readings" would avoid that, but reads less naturally.
  - Raising the band to 100% would turn many real days partial. That is a logic change, and I do not propose it.

### 10.4 This also settles the two-rules finding (section 3)

The two rules get two different names:
- **Reading completeness** ("complete / partial readings"): the day grades the cards and the one coverage line use.
- **Analysis status** ("not analysed yet"): the estate rule.

Neither is called "checked", so they can no longer look like one number that disagrees with itself. The coverage line uses the reading words, and adds "{n} days not analysed yet" only when that happens.

### 10.5 Before Thursday?

- **Frontend strings (F rows):** about 12 strings in 7 files. They could go in after tonight's build without a rebuild.
- **Backend strings (B rows):** about 45 strings. They need a rebuild, and tests pin many of them.
- **Recommendation: change neither before Thursday.** A frontend-only pass would put "complete readings" next to the backend's "days checked" on the same card, which is worse than one consistent old word.
  - Do PF-W in one pass with PF, before the client session.
  - For Thursday, the presenter can say: "checked means the readings for that day were complete".

## 11. Item 4: date at the top, left menu unchanged (owner, verbatim, item 4)

- **Left menu.** The mock now uses the v7.0 menu copied exactly from the rendered v7.0 shell:
  - six groups: Operations, Intelligence, Work, Assurance, Business, Admin;
  - eleven items: Portfolio, Sites, Assets, Findings, Actions, Incidents, Maintenance, Operational records, Evidence, Financials, Settings;
  - the Workspace footer.

  The items match the product rail (`shell/OperatorShellLayout.tsx:57-69`). The product's phone behaviour (the menu sits behind a Menu button at phone width) does not change.
- **Date range.** The mock uses v7.0's top-bar date picker. It sits at the top of the screen, stays there while scrolling, and is the same on every tab.
- **Current and Side by side** show v7.0 itself, which already has both.
- **Build note.** The app today shows the Portfolio date bar (`EstateDateBar`) below the page title, not in the top bar. PF-T moves it to the top, above the coverage line and the tabs. This is inside PF-T's 1.0 units.

## Item 9: scalable estate outcomes

- Architect: Claude (`assetops-architect`). Binding checked in `.ai/ROLE_CONFIG.md`: Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-walkthrough-2026-11-10.md` item 9): "on the main portoflio page, "Outcomes across the estate" page, it seems when the number of sites and the number of items under the four groups increase, the UI can't accommodate them well, is there a more scalabel UI design option? if so, update it on the mock-up and let me know once ready for me to review"
- **Status: draft for owner review. Nothing is built, and no spec, register or product code changes, until the owner approves.**
- **Mockup:** `frontend/mockups/v71/estate-outcomes-scale.html`. It is linked from the "Outcomes by site" tab of `portfolio-tabs.html`.
  - The switch at the top right moves between the demo estate (4 sites) and a synthetic estate of 120 sites. The synthetic estate is labelled as illustrative.
  - v69 and v70 are unchanged.

### 9.1 In plain words, for the owner

- **Yes, there is a more scalable design, and the draft is ready to review.**
  - Today's grid gives every site its own column.
  - Columns run out of room at about 25 sites.
  - For each site, the grid shows only one outcome per group.
- **The fix is to turn the grid round.**
  - Each site becomes a row, and the four outcome groups become four columns.
  - A page can grow downwards without limit, but not sideways.
  - There are always exactly four groups, so the columns always fit.
- **A summary for each group sits on top.**
  - Each of the four tiles counts sites by state, for example "16 need attention · 28 watch · 62 on track · 14 unknown".
  - Selecting a state lists only those sites.
  - The tiles count sites. They never add up money, energy or hours.
- **Finding a site.**
  - Search by name.
  - Filter by site type (mini-grid, cold room, EV charging, diesel), by readings, and by region.
  - Group by type or region.
  - Sort by "need for attention" (the default).
  - 25 sites load at a time.
  - With 8 sites or fewer, only the type chips and the view switch show, so the demo estate looks as simple as it does today.
- **Every outcome, when you want it.**
  - The "Every outcome" view shows one square per outcome for each site.
  - There is one table per site type, because each type has its own outcomes.
  - Each group can be opened to all of its outcomes (3 to 8) or folded to its lead outcome.
- **What stays from today:**
  - the state words and colours;
  - the lead outcome, named in each cell;
  - every cell opening that site's board for the same dates;
  - the four groups, in the same order.
- **Phones.** Each site becomes a card, with the four groups in a 2 × 2 grid.
- **Size and timing.**
  - This is about **1.75 build units**. It is added to the Portfolio tabs slice (2.25 units), so that slice becomes 4.0 units.
  - **It is not for Thursday.** It lands with the tabs before the client session.
  - At 100 or more sites, the server work needs ANY-2's stored rows (+0.75 units there). The page itself does not change again when that work lands.

### 9.2 How today's grid breaks (verified in code)

**The current grid.** It is built by `frontend/src/estate/PortfolioOutcomes.tsx` (`OutcomeMatrix`, lines 270-325) and styled in `frontend/src/sites/outcomes.css:146-162`.
- It has one row per outcome group and one column per Site.
- `.oc-mrow` is `repeat(var(--oc-sites), minmax(0, 1fr))`, with a 4 px gap.
- Each cell shows the state word and the group's **lead outcome only**.
- v70 hard-codes 3 columns (`outcomes.js:196`, `outcomes.css:40`).

**The usable width:**
- In the Portfolio side column today, about 285 px inside the panel at 1440 (`estatePortfolio.css:39`: `minmax(290px, 1fr)` beside `2.7fr`).
- In the v7.1 full-width tab, about 1,140 px.
- On a phone at 390, about 360 px.

| Sites | Side column (today) | Full-width tab (v7.1) | Phone (390) | What the user sees |
|---|---|---|---|---|
| 4 | ~68 px a cell | ~282 px | ~87 px | Readable. "Battery and generator life" wraps to 2-3 lines in the side column |
| 25 | ~8 px | ~42 px | ~11 px | Names and states no longer fit. The cell becomes a colour stripe, and its meaning is only in the tooltip. Phone and keyboard users do not get tooltips, so this fails WCAG 1.4.1 (colour alone) |
| 100 | the gaps alone are 396 px, wider than the column, so it overflows | ~7 px | overflows | Not readable. The page scrolls sideways |
| 500 | the gaps are 1,996 px, so it overflows | the gaps are 1,996 px, so it overflows | overflows | Not usable |

**Outcomes per group (3-8).**
- Today the catalogue (`outcomes/catalogue.py:44-67`) has 1-4 outcomes per group for each Site type. Mini-grid Protect, for example, has MG-5, MG-4 and MG-8.
- The board row already carries all of them (`OutcomeBoardRow.outcomes`, `outcomeBoardClient.ts:185`).
- The estate summary keeps only `lead_outcome` (`site_outcomes/read.py:892-899`, `_summary_row`).
- So the Portfolio cannot say "2 of 7 Protect outcomes need attention". The other outcomes stay hidden until you open each board.
- More outcomes per group make this gap bigger; they do not cause the layout break.

**Other parts that also do not scale:**
- **The Overview card dots.** `SiteDots` (`PortfolioOutcomes.tsx:146-170`) draws one named chip per Site on each of the four cards. At 120 Sites, that is 120 chips on every card.
- **The server.** `summary()` (`read.py:571-578`, with `_summary` from line 642) composes **one full board per Site, one after another**. Off-list boards measured 10-36 s each (`.agent/architect-answer-any-range-speed-2026-11-10.md` §2), so an estate of 100 Sites cannot be composed on read at all. ANY-2 fixes the same root cause.

### 9.3 Options weighed

**What mature products do.** Real-estate portfolio dashboards, energy-fleet and infrastructure monitoring dashboards all follow one pattern:
- status tiles that count assets by state;
- an exceptions-first asset list that can be sorted and filtered;
- a dense status grid behind a view switch, for analysts.

Data-table guidance points the same way (Carbon, the Atlassian dynamic table, GOV.UK "filter a list"):
- a sticky header and filters above the table;
- paging or "load more";
- on phones, the table becomes cards.

NN/g dashboard guidance adds three rules: lead with exceptions, reveal detail on demand, and never show meaning by colour alone.

| Option | Scales to 500 | Shows the "why" | Works across Site types | Phone | Verdict |
|---|---|---|---|---|---|
| (a) Group tiles, each opening a Site list | Yes | Only after a click | Yes | Good | Good for the summary, but four lists behind four tiles are four lists to learn |
| (b) Heat-map grid, with Sites as rows and outcomes as columns | Yes, as rows | Weakly (colour plus a symbol) | **No**: each type has its own outcomes, so one grid across types has uneven columns | Poor | Right for the analyst view, **within one Site type only** |
| (c) Exceptions-first list, with the full grid behind a switch | Yes | Yes | Yes | Good | Right for the default, but the healthy Sites stay hidden unless you sort |
| **(d) Hybrid: (a)'s tiles, one Site list with the four group columns sorted as in (c), and (b)'s grid per Site type as a second view** | **Yes** | **Yes** | **Yes** | **Good** | **Chosen** |

**Why (d):**
1. Sites are rows and the four groups never change, so the default table never runs out of width, whatever the estate size.
2. The tiles show at a glance how the estate is doing on each group, and they also work as filters.
3. The default sort, need for attention, gives the exceptions-first reading of (c). "Only sites that need attention" gives the pure exception list.
4. The analyst grid (b) appears only where it is honest: within one Site type, with groups that fold.

**Pushback: what stays.**
- Every cell keeps both the state word **and** the lead outcome. A colour-only heat map would lose the "why" and fail WCAG 1.4.1.
- The v7.0 state words and key stay.
- Every cell still opens that Site's board for the same dates.
- The full outcome grid is not the default view: it is for analysts.
- Sites do not go back to being columns for small estates. One layout at every size, with the controls hidden at 8 Sites or fewer, is simpler to build, test and learn than two layouts.

### 9.4 The design in detail (as in the mockup)

**Tiles (one per group).**
- The bar and the state buttons follow the key order: Needs attention, Watch, Opportunity, On track, Unknown, Not measured yet.
- Each tile counts a Site once, by its lead outcome in that group.
- The tiles follow the type, region, readings and search filters. They ignore their own state filter, so selecting a state never shrinks a tile to one colour (the usual faceted-search rule).
- The footer reads "Counts of sites. Values are never added across sites here."

**Coverage words.**
- At estate scale, the shared coverage line above the tabs counts Sites by reading word, for example: "Complete readings: 80 sites · Partial readings: 20 sites · Too few readings: 6 · No readings received: 8 · Still processing: 2 · Not analysed yet: 4".
- Each row's Readings column uses the approved words with the days: "Partial readings · 1 of 7 days partial · complete on 6".
- A Site whose readings are "no readings received", "still processing" or "not analysed yet" shows "Unknown" in every group. The cell names the reading word as the reason. It never shows a guessed state.

**List (the default view).**
- Columns: Site (with its type and region), Readings, and the four groups.
- Each group cell shows the state, the lead outcome, and either "{k} of {n} outcomes need attention" or "{n} outcomes · none need attention".
- Sort options:
  - need for attention (the default): most groups needing attention first, then most on Watch, then name;
  - name;
  - type;
  - readings, least complete first;
  - any group column (`aria-sort`).
- The header and the Site column stay in view while scrolling.
- 25 rows show at a time, with "Show 25 more".
- Grouped by type or region:
  - each group can be collapsed;
  - it shows 8 rows, with "Show all {n}";
  - its header counts the Sites with at least one group needing attention.

**Every outcome.**
- One table per Site type.
- Each group's header folds between all of the group's outcomes and its lead outcome alone.
- One square per outcome. Each square shows a symbol (! ~ + ✓ ? –) as well as a colour, and carries a hidden text label for screen readers.
- The Site column and both header rows stay in view while scrolling.
- The table scrolls sideways inside its frame, never the whole page.
- 15 rows show per type, with "Show all".
- Outcomes marked ◦ in the mockup are illustrative extras, added to show groups of up to 8.

**Phones (≤760 px).**
- The list becomes one card per Site: its name, its readings, and the four groups in a labelled 2 × 2 grid.
- The every-outcome view keeps its frame, which scrolls sideways.

**Accessibility (WCAG 2.2 AA).**
- A real `<table>`, with a caption, `scope` and `aria-sort`.
- The toolbar has `role="search"`, and every control has a label.
- The status line is `aria-live`, for example: "24 of 120 sites match · Protect asset and capital: Needs attention · Clear".
- Each cell link has a full accessible name, for example: "Kobo, Grow revenue: Opportunity, Productive electricity sales. 3 outcomes · none need attention. Open the site board".

**Reaching a Site's board.**
- The Site name and every cell link to `/sites/:code/overview` with `from`, `to` and `known_at`, as `overview_href` does today.
- A group cell also adds that group's anchor, so the board opens at the row.

**The Overview card dots (same slice).**
- At 8 Sites or fewer, the dots stay as they are.
- Above 8, each card shows its tile's distribution bar and "{n} sites need attention →", which opens this tab already filtered.

**Checked in headless Chrome.**
- Widths: 1440 and 320 px.
- Views: demo and large; list and grid; grouped; filtered from a tile.
- Results: no horizontal page overflow, and no script errors.

### 9.5 Backend implications

**What exists today.**
- `estate/portfolio.py` serves the **Finding** rows of "Act first". They are already paged on the server (`limit`, `next_cursor`, `PORTFOLIO_ORDER`, full-scope token) and need nothing new.
- The outcome grid reads `GET /api/estate/outcome-summary` (`outcome_api.py:45`). That read has no filter, sort or paging, keeps only the lead outcome, and composes one board per Site on read.

**New contract, built once in the PF slice.** A new route, `GET /api/estate/outcome-sites`, sits beside the summary. The summary body stays as it is, for the cards.

Parameters:
- `from`, `to` and `known_at`, under the W3-01 scope, cutoff and envelope;
- filters: `q`, `site_type[]`, `region[]`, `readings[]`, `pillar` with `state`, and `attention_only`;
- order: `sort` (`need` | `name` | `type` | `readings` | `pillar:<category>`) and `dir`;
- grouping: `group_by` (`type` | `region`);
- paging: `limit` (25 by default, at most 100) and `cursor`. The cursor is bound to the selection token, so page 2 reads the same snapshot;
- `detail=outcomes` with one `site_type`, for the every-outcome grid.

Body:
- `facets`:
  - Site counts per (pillar, state), over the filtered scope **before** the pillar and state filter;
  - Site counts per type, region and reading word.
- `total_count`, `match_count`, and `groups` (key, label, count, and how many need attention).
- `rows`, each with:
  - the Site's identity, type, region and `overview_href`;
  - `readings {word_key, label, text}`;
  - four `pillars`, each with `state`, `state_label`, `tone`, `lead {key, label}`, `outcomes_total` and `outcomes_needing_attention`, plus `outcomes[]` only with `detail=outcomes`.
- `columns`, with `detail=outcomes`: the type's catalogue outcomes for each group.
- `next_cursor`.

Two rules:
- Every word is server text (the CH-6b2 rule).
- The server computes the need-for-attention order, with a stable tie key (`site_code`, `site_id`), so the cursor is stable.

**Never-total.**
- Facets count Sites only. The route carries **no** summed amount field.
- A row's `short_value` or `headline_money` is that one Site's own value.
- MN-3's no-total guard (AR-4) extends to this route: a contract test asserts there is no amount field in the body or the facets.

**The readings word.**
- It comes from PF-C1's per-Site grade, built from the same `counted.days` as the cards and the coverage line. It is not a second rule.
- "Not analysed yet" is the estate's analysis status (§10.4).

**Region.**
- The Site has no region attribute today (`SiteRef`, `site_outcomes/read.py:73`).
- Ruling: region filtering and grouping appear only once the Site has a declared, optional `region`. Until then the control is hidden. The mockup shows it only on the illustrative estate.
- Adding the attribute costs 0.25 units, if the owner wants it (Q2).

**How it fits ANY-2 and the money receipts, so nothing is built twice.**
- **PF step (demo scale).**
  - The route works in memory over the existing `summary()` composition: it filters, sorts and pages those rows.
  - It adds `outcomes[]` from the board row the summary already reads (`_summary_row` stops dropping it).
  - This is correct and fast for 4-25 Sites.
  - The frontend uses the server parameters from day one.
- **ANY-2 (scale): new card AR-7, "Outcome rows on stored rows" (0.75 units).**
  - A new kind, `outcome.site_row`, in `site_period_read`.
  - Mini-grid rows are keyed per Site-local day (DAY basis). Cold and EV rows are keyed per selected event window (PERIOD basis), and the read takes the latest one inside the range.
  - Its body is exactly the `_summary_row` fragment, plus `outcomes[]`.
  - The existing event register marks it for rebuilding, like the other AR kinds.
  - Filter, sort, facets and the cursor become one indexed query over stored rows. The page reads one small row per Site and never composes a board.
  - Before the switch, AR-0's parity harness proves the stored rows equal today's compose. A Site type that cannot be proven equal stays on compose and is reported (the ANY risk rule).
- **Money receipts (MN-1/2/3).** These are untouched. The route shows no money beyond each Site's own value line, so AR-4 needs only MN-3's guard extended to it.
- **1,000+ Sites.** The estate roll-up rows in the ANY scale path (§4) also hold each tenant's facet counts, so the tiles read one row per scope.

### 9.6 Size and sequencing

| Card | Scope | Size |
|---|---|---|
| **PF-O1** Outcomes tab, frontend | tiles; toolbar, kept compact at 8 Sites or fewer; list with sticky header and Site column; need-for-attention sort; grouping; paging; every-outcome grid per type, with folding; phone cards; accessibility; empty and loading states; tests; captures re-baselined against this mockup | 1.0 |
| **PF-O2** `outcome-sites` route, in memory | the contract above, over `summary()`; `outcomes[]` kept; facets; need-for-attention order; cursor; never-total contract test; readings word from PF-C1 | 0.5 |
| **PF-O3** Overview card dots at scale | above 8 Sites, the distribution bar and "{n} sites need attention →" | 0.25 |
| **AR-7** (in ANY-2) | the `outcome.site_row` stored kind; its register entry; the route re-sourced from stored rows; AR-0 parity cases | 0.75 |
| Region attribute (only if the owner wants it, Q2) | a declared, optional `site.region`; its import field; filtering and grouping turned on | 0.25 |

- **The PF slice grows from 2.25 to 4.0 units.** That is under the 6-unit split rule.
  - PF-O depends on PF-T (the tab) and PF-C1 (the readings word), so it runs last in the slice.
- **ANY-2 grows from 4.75 to 5.5 units.** It stays one slice. If anything else joins ANY-2, AR-7 splits out as ANY-3.
- **Not for Thursday.**
  - It lands with the Portfolio tabs slice, **before the client session**.
  - It also lands before ANY-2 starts, as the tabs proposal already sequences (§8).
  - Later, ANY-2 changes only where the route reads its data from. The page and the contract stay the same.

### 9.7 Questions for the owner

1. Do you approve the hybrid design: the four tiles, one Site list with the four groups, and "Every outcome" for each Site type?
2. Should Sites get a declared region, or another grouping such as client or programme, to filter and group by? Until then, the region control is hidden.
3. Which view should open by default: "By outcome group" (recommended) or "Every outcome"?

### 9.8 Owner answers (item 12, 2026-11-10)

Verbatim in `.agent/owner-walkthrough-2026-11-10.md` item 12. Recorded by the Architect (Claude, `assetops-architect`; binding checked in `.ai/ROLE_CONFIG.md`).
- **Q1, the hybrid design (§9.4, `frontend/mockups/v71/estate-outcomes-scale.html`): approved "for now".** It is the layout spec for the "Outcomes by site" tab. The owner's wider ask (how the UI becomes international-grade) is answered separately in `.agent/architect-answer-ui-quality-2026-11-10.md` (BL-69). Nothing in that answer reopens this design before the client session.
- **Q2, a declared region on Sites: yes.** The optional `site.region` attribute, its import field, and region filtering and grouping are in scope: **+0.25 units**. The PF slice grows from 4.0 to **4.25 units**. Ruling: `region` is a value from a declared list per tenant (no region list in code), optional, and the region control stays hidden while no Site in scope has one. "Client" or "programme" can later use the same mechanism as a second attribute; it is not built now.
- **Q3, the default view: "By outcome group"**, as recommended. "Every outcome" is the second view. The choice is kept in the address (`view=outcomes`), never as a hidden preference.

## Item 12.5: one shared date range for every page (SR)

- Owner, verbatim (item 12, answer 5): "yes", to "Add one shared date range across all pages to the layout proposal and mockup".
- **Status: specified, and the mockup is updated.** `frontend/mockups/v71/portfolio-tabs.html` has Change 0b and a working picker. The `estate-outcomes-scale.html` top bar is marked "All pages". Nothing is built until the owner approves the mockup.

### SR.1 In plain words, for the owner

- **One range, at the top, for the whole app.** You pick the dates once. Portfolio, Findings, Actions, Evidence, Financials, every Site page, Incidents, Maintenance and Operational records all show the same dates. The pages lose their own date bars.
- **It stays when you move.** The left menu, the tabs and the links between pages keep the range. Today the left-menu links drop it, so every page falls back to its own default.
- **It stays in the address.** A copied link still opens exactly the same view, including "as known at" an earlier time.
- **Pages that need a finer view pick it inside the range.** A Site board can show one day, the fuel page one night, and the service page one hour. That finer choice stays on that page and is not carried to the others.
- **Size: 1.75 units.** It is its own slice in the Portfolio-tabs lane. It is built first, before the client session.

### SR.2 What exists today (verified in code)

The product has no shared top bar:
- `shell/OperatorShellLayout.tsx` renders only the rail, the demonstration banner and the page.
- The rail items are fixed paths with no query (`operatorRailItems`, lines 57-69). This is why the left menu resets the range.

There are about 20 date forms, with 5 different defaults:

| Pages | Form | Default when the address has none |
|---|---|---|
| Portfolio, Findings, Actions, Evidence, Financials | `EstateDateBar` (`estate/estateShared.tsx:98`) | `defaultWindow`: the 7 full UTC days **before** today (S17) |
| Incidents, Maintenance, Operational records | `work/globalWorkParts.tsx:197` | `defaultGlobalWorkWindow`: 7 UTC days **including** today (R338) |
| Site Actions and Work cases (all types) | `SiteWorkActions.tsx:177`, `siteWorkCases.tsx:304` | `defaultWorkWindow`: 7 days including today |
| Site Findings index | `SiteFindingIndex.tsx:333` | its own form |
| Mini-grid Renewable and Service | `miniDepthClient.ts:334, 358` | one **Site-local day** or one **local hour** (12:00-13:00), via `?date=` |
| Mini-grid Performance, Dispatch, Scenarios, Site overview, claim limit | `MiniPerformance.tsx:474, 1044`, `PerformanceDispatch.tsx:309`, `MiniScenarios.tsx:303`, `SiteWindowOverview.tsx:273`, `EvidenceClaimLimit.tsx:372` | their own forms, including a single-day picker |
| Cold and EV Site pages | `coldSiteViews.tsx:458-475` (`SelectedWindowBar`), `EvSiteViews.tsx:328` (`WindowBar`) | **no window**: the server picks the selected event window |

Some of the groundwork already exists:
- The parameter names are already shared: `from`, `to` and `known_at`.
- The Site tabs (`operatorSiteTabHref`) and the estate links (`estateHref`) already carry them.
- The v6.9/v7.0 mock already intended one range. Its picker says "One window for every page" (`v70/screens.js`, `rangePicker`). The product split it up page by page.

### SR.3 The design

**The state lives in the address, and only there.**
- **Shared parameters:** `from` and `to` (calendar days, `YYYY-MM-DD`, with `to` included), plus an optional `known_at` (an instant).
- **The two address forms:**
  - The top bar writes the short day form.
  - The current instant forms (`from=2026-11-02T00:00:00Z&to=2026-11-09T00:00:00Z`) stay accepted, so every existing link opens the same view as before.
- **What a day means:**
  - Estate pages read the days as UTC days. This is today's rule, with the "Times in UTC" note.
  - Site pages read them as the **Site's local days**. The mini-grid pages already do this; the Cold and EV pages start doing it.
  - Each page says which, in its time-zone note, so one link is exact on every page.
- **One hook, `useSharedRange()`:**
  - It reads both address forms from the address, and returns `{from, to, known_at, preset}`.
  - It checks the range. A bad range gives the existing `Window not valid` state, which never echoes the dates.
- **One helper, `withRange(path)`.** It adds the current shared parameters to any in-app path.
- **The left menu.** `NavRail` takes a `search` from the shell and adds it to every live item, the same way `OperatorSiteTabs` takes `search`.
- **Other links.** Tabs, breadcrumbs, row links and "Open site" links all use `withRange`.
- **Links with their own range.** A link that names its own range on purpose (for example a Finding's event window) keeps it. That range becomes the shared range on the page it opens.
- **An address with no range** (a typed URL or an old bookmark):
  - The shell replaces the address, without adding a history entry.
  - It uses the last range chosen in this browser tab, from `sessionStorage`, else the default. If the browser blocks storage, it uses the default.
  - The address on screen is therefore always complete and can be copied.
- **No hidden state.** The range is never kept in `localStorage` or on the server.

**Finer views inside the range (parameters for one page only).**
- **The parameters:**
  - `day=YYYY-MM-DD` for one day: the Site board day view, Dispatch, Renewable and a fuel night.
  - `hour=HH` for the Service hour.
  - `event=<id>` for the Cold or EV event in focus.
  - They replace today's `date=` parameter and the per-page forms. Old `date=` links redirect to `day=`.
- **They stay on their page:**
  - The left menu and links to other pages **never** carry them.
  - Tabs within the same Site carry them only to a tab that reads them.
- **The finer picker:**
  - It offers only days inside the shared range, and says so: "Day shown: 8 Nov (inside 2-8 Nov)".
  - By default it shows the last day of the range. On Cold and EV pages it shows the latest event inside the range, as the boards choose today.
- **A `day` outside the range** (for example, an edited link):
  - The page shows the last day of the range, with the line "8 Nov is outside the date range, so the last day of the range is shown".
  - A "Show 8 Nov" button widens the shared range to include that day.
  - The page never changes the range without saying so.

**`known_at` ("as known at" an earlier time).**
- **Where it is set:** in the same picker, under "View an earlier point in time" (the existing R652 words and closed disclosure).
- **While it is set,** the top bar on **every** page shows "As known at {time} · every page" and a "Return to latest" button.
- **Every link carries it,** like `from` and `to`.
- **A page that cannot use an earlier time** says so in place: "This page shows the latest information; earlier points in time do not apply here." It never shows live data under an "As known at" bar without saying so.
  - Build check: confirm, read by read, which reads accept `known_at`. The global Work reads already check it (`INVALID_KNOWN_AT`).
- **Page two of a list** keeps the cutoff of its first page, as today.

**One default for every page.**
- **The default: the last 7 days, ending yesterday,** with full days only. That means UTC days on estate pages and Site-local days on Site pages.
  - Why: a day still in progress always reads "partial readings", which makes the first view of every page look broken.
- **Work pages:**
  - This changes R338, Work's current "including today".
  - Work pages add a preset, "Last 7 days, including today".
  - They show the items open now in one line, for example "Open now: 3 requests, whatever the dates", so nothing current is hidden.
  - Register rows R338 and S17 are revised at build.
- **Cold and EV Site pages** lose "no window, so the server picks". With a range, the board picks the latest event inside it, and says "No event in 2-8 Nov" when there is none.
- **Presets:** Yesterday, Last 7 days, Last 30 days, This month, Last month and Custom.
  - "Today" is not a preset, because it is a partial day. Custom still allows it.
- **The demo** opens on explicit links (the DS-1b script), so the default never decides what the client sees first.

**Phones (760 px and below).**
- The button shows only the dates ("2-8 Nov") and is 44 px high. The preset name and the "All pages" label are hidden.
- The picker opens as a sheet from the bottom of the screen. It is full width, scrolls, and takes at most 85% of the screen height.
- The "As known at" label wraps onto its own line under the top bar.
- The native date inputs stay, so the phone shows its own date picker.

**Accessibility (WCAG 2.2 AA).**
- **The button** names the whole state, for example "Date range for every page: Last 7 days, 2 to 8 November 2026. Change". It has `aria-expanded` and `aria-controls`.
- **The picker:**
  - It is a non-modal dialog with a label.
  - Focus moves to the selected preset. Escape and Cancel close the picker and return focus to the button.
  - Nothing changes until "Apply", so the page does not reload on each keystroke (WCAG 3.2.2).
  - The presets are toggle buttons (`aria-pressed`) and the inputs have visible labels.
  - The earlier-time state is shown in words, not only in colour.
- **After Apply:**
  - A polite live region says "Every page now shows 2-8 Nov 2026", and focus stays on the button.
  - The content updates in place, under the PL-1 rule (the page never goes blank).
- **Target size:** at least 24 px (WCAG 2.5.8), and 44 px on phones.

**Consistency and guards.**
- **Two components:**
  - `SharedRangeBar`, in the shell top bar.
  - `FocusPicker`, for `day`, `hour` and `event`.
- **Checks:**
  - A new check in `tools/checks` fails when a page under `frontend/src` renders its own `type="date"` range form. The shell and `FocusPicker` are exempt.
  - The navigation-truthfulness guard also checks that the rail items take the shared `search`.
- **The frontend hard-wiring ratchet** is unaffected:
  - No branching on Site type is added.
  - The Site-local day rule reads the Site's declared time zone, not its type.

### SR.4 Size and sequencing

| Card | Scope | Size |
|---|---|---|
| **SR-1** Shell bar and state | `SharedRangeBar` in a new top-bar row of `OperatorShellLayout` (the demonstration banner stays); `useSharedRange`; `withRange`; the rail `search`; filling in the address on entry; the presets; the `known_at` label; the phone sheet; accessibility; tests | 0.5 |
| **SR-2** Pages move to the shared range | remove the ~20 page forms; each page reads the hook; `day`, `hour` and `event` through `FocusPicker`; old `date=` and instant links keep working; the one default; Cold and EV show the latest event inside the range; R338 and S17 rows revised; the addresses tests expect | 1.0 |
| **SR-3** Guard and captures | the check for page range forms, with its self-test; the rail check; captures re-baselined against v7.1 | 0.25 |

- **Total: 1.75 units, as a slice of its own.** It is not folded into PF: PF is 4.25 units after the region, so PF + SR would be 6.0, the split threshold.
- **Order:**
  1. SR-1 first. PF-T then builds its tabs under the shared bar, so PF-T drops its "move the date bar to the top" step and keeps its 1.0 units as margin.
  2. Then PF.
  3. SR-2 and SR-3 run alongside PF-O.
- **Lane:** the same lane as PF. SR-2 changes the Site page frontends, which ANY-1 (stored board rows, backend) does not touch.
- **Before the client session: yes. Not before Thursday,** because that build is frozen. With SR, a client who moves between the Portfolio and a Site sees the same dates. Different dates on different pages are the most visible inconsistency in this walkthrough.
