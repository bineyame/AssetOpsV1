# Architect proposal: Portfolio layout, coverage once and section tabs (2026-11-10)

- Architect: Claude (fresh `assetops-architect` instance). Binding checked: `.ai/ROLE_CONFIG.md`, Architect = Claude since 2026-10-27.
- Owner feedback, verbatim: `.agent/owner-walkthrough-2026-11-10.md` (item 1 money, item 2 coverage and layout).
- **Status: proposal for discussion. Nothing is built, and no spec, register or product code changes, until the owner approves the mockup draft.**
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
