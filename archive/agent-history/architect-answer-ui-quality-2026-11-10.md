# Architect answer: how AssetOps' UI becomes modern and international-grade (2026-11-10)

- Architect: Claude (`assetops-architect`). Binding checked in `.ai/ROLE_CONFIG.md`: Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-walkthrough-2026-11-10.md`, item 12, answer 1): "i want the architect to give honest take on how assetops UI can be turned into a modern, international grade high quality for a later focussed work(not a priority before the demo but it does affect some users first impression)".
- **Status:** an assessment and a staged plan, recorded as backlog item **BL-69**. Nothing is built, and no mockup changes, until the owner picks it up.
- **Evidence used:**
  - The E5 captures (`AssetOpsV1-ds1a/Docs/demo-sprint/demo-script-img/e5/`, at 1440 and 390 px): Portfolio, Kobo Finding, Cold board, Kisiwa fuel night and others.
  - The running app at `http://localhost:5490`, viewed only.
  - The v6.9, v7.0 and v7.1 mockups.
  - `frontend/src`: tokens, CSS, formatting helpers and the shell.
  - `.agent/owner-ui-ux-guidance-2026-10-25.md`.
- **Counts (measured):**
  - CSS: 35 files and 11,809 lines, with 228 distinct hex colours, 55 distinct font sizes, 143 custom properties and 20 distinct media queries.
  - Zero `prefers-color-scheme` and zero `prefers-reduced-motion` rules.
  - 118 physical left/right properties and 0 logical ones.
  - One `Intl.NumberFormat` in 105k lines of TypeScript, and 26 `.toFixed`.
  - No chart library: about 19 inline SVGs plus CSS bars.

## 1. In plain words, for the owner

**The verdict.**
- AssetOps is **honest, careful and more accessible than most B2B tools at this stage**.
- But it does **not yet look or read like an international-grade product**.
- A first-time viewer sees a dense, small-type, text-heavy evidence tool, not a confident decision product.

**Where the gap is.**
- The gap is mostly **presentation, not substance**.
- The things that are hard to copy are already there: every number is traceable ("Why?"), there is a strict "never guess" rule, and the vocabulary is plain.
- That makes the fix cheaper than it looks. The pages need less on them, larger type, one headline per page, real charts, and a proper design system.

**The five biggest problems.**
1. **The type is too small and the pages too dense.** Table text is 11 px, table headers 9 px and secondary text 10 px (`ui/tokens.css`), and there are 55 different font sizes. Mature products keep body text at 13-14 px and nothing below 12 px.
2. **No page has one clear headline.** Every block has the same weight. Each Portfolio card carries 6-10 lines of qualifiers. A Finding opens with "Priority: not assessed · Confidence: not assessed · Earlier version 1 of 3" before it says what happened.
3. **The honesty wording crowds out the content.** "Not available yet", "Unknown" and "No cold assessment for this window" repeat across whole screens. On the GreenHarvest board, the lower half is four cards that each say only that.
4. **Charts are few and ad hoc.** There is no chart standard, the Portfolio has no trend line, and some visuals carry little meaning (a strip of 40 identical orange blocks on the Finding page).
5. **The product is English, US-date and UTC-only, and inconsistent from page to page.**
   - The date inputs show "11/02/2026" next to "2–8 Nov 2026".
   - Money shows as "139.16 USD" with no thousands separators.
   - The month names are hard-coded in English.
   - Most on-screen words are composed in English on the server.
   - The layout cannot mirror for right-to-left languages.
   - There are about 20 different date bars.

**The plan, in four stages.**

| Stage | What | Size | When |
|---|---|---|---|
| 0 | Already planned fixes, plus quick wins | 0.75 | Before the client session: only what is already planned (PF, SR). The quick wins are optional |
| 1 | Design-system foundation: tokens, components, a chart standard | 3.5 | After the client session |
| 2 | Page-by-page uplift, mockup first | 4.5 | After stage 1 |
| 3 | Internationalisation: formats, translations, right-to-left | 4.0, plus translation | Alongside or after stage 2, once the first non-English client is known |

- **Total:** about 12-13 units after the client session.
- **Rules that stay in force:**
  - Each stage starts with a mockup that you approve (v7.2).
  - Two shrink-only checks protect it: the hard-wiring ratchet, and a new style ratchet.

**What is fine for the client session.**
- The walkthrough fixes already planned make the biggest first-impression difference: coverage shown once, tabs, a shared date range, and scalable outcomes.
- The presenter can rely on depth and honesty, which is a real strength.

## 2. What is already good (keep it)

- **Explainability as a feature.** "Why?" on every number, "What limits this conclusion", and "Where to look next" (numbered, on the Finding page). Few asset-management products do this, and it is the strongest trust signal AssetOps has.
- **Plain, defensible copy rules.**
  - No raw codes in prose.
  - Server-owned words (the CH-6b2 rule).
  - The term family the owner approved.
  - "Not billed or collected" and "not a saving" qualifiers.
- **Accessibility thinking.**
  - Colour is never the only signal (`tokens.css` header).
  - Tabs are links with `aria-current`.
  - Focus outlines, a labelled rail landmark, and contrast-checked badge tones.
- **One formatting helper each for times and money** (`ui/time.ts`, `ui/money.ts`): one time-zone note per page and exact decimal rounding. They are the right seams to extend.
- **Phone layouts mostly work.** Cards stack, the rail collapses behind Menu, and most pages have no page-level sideways scroll (Kisiwa fuel at 390 px reads well).
- **A consistent frame:** a stable rail, breadcrumbs, the Site tab row, and status pills.

## 3. The assessment, area by area

The grade is how far each area is from international B2B practice.

### 3.1 Visual design system (grade: weak)

**Type scale.**
- `tokens.css` copies the v6.9 mock's sizes: page title 27 px, panel title 15 px, table 11 px, table head 9 px, rail eyebrow 9 px and secondary cell 10 px.
- The CSS then uses **55 distinct font-size values** around those tokens.
- Carbon, Atlassian, Material 3 and GOV.UK all keep 6-9 steps, with body text at 14-16 px and a floor of 12 px.
- 9-11 px text is the most "dated / internal tool" signal on every screen. It also fails users at 125-150% OS scaling on Windows laptops (common at clients) once zoom is applied.

**Colour.**
- **228 distinct hex values,** many outside the tokens (for example the v7.1 drafts use `#fffaf0`, `#f0dcb4` and `#5b4413` inline).
- The palette (navy rail, single blue accent, amber and red tones) is sound but not systematised.
- There is no semantic tier (`--color-status-attention-bg`, and so on) and no dark-mode readiness (0 `prefers-color-scheme`).

**Spacing and density.**
- There is no spacing scale in use: paddings are hand-set per component.
- Density is "maximum everywhere". No comfortable mode exists, and nothing is hidden by default.
- Example: the Cold board's five-column "What drives it / Issues / What can be done / Already in hand / Earlier interventions" grid puts about 40 links in one band at 11-12 px.

**Icons.** A small custom line set (`RailIcon.tsx`) is consistent in the rail. Beyond the rail, icons are used rarely and inconsistently: some panels have them, most do not.

**Typeface.** The system font stack (`system-ui, Segoe UI, Roboto…`) renders differently on Windows, Mac and Android. It also has no tabular figures by default, so numbers in tables do not align.
- International products either self-host one variable font with full Latin, Cyrillic, Greek and Arabic coverage, such as Inter or IBM Plex with Noto fallbacks, or set `font-variant-numeric: tabular-nums` on the system stack.

**Data visualisation.**
- There is no chart library or chart standard.
- Visuals are hand-built:
  - CSS bars (fuel balance, good);
  - the block strip (Finding page);
  - the coloured matrix (Portfolio outcomes);
  - occasional inline SVG.
- What is missing:
  - trend lines with uncertainty bands (estimated money ranges are shown as text, "0.00 to 15.13 USD");
  - sparklines in the cards;
  - a timeline for incidents, actions and verification;
  - one series palette;
  - accessible table alternatives for charts.
- The Finding's 40 identical orange blocks tell the reader "3 h 20 min", which the tile below says better. A timeline that shows needed versus avoidable blocks against solar and battery state would carry the argument.

### 3.2 Information hierarchy and copy (grade: mixed)

**Hierarchy.**
- Pages answer many questions at equal volume. The Portfolio (E5 capture 01) shows, above the fold, all of the following:
  - a date form;
  - an earlier-point control;
  - two coverage badges;
  - a per-Site coverage note;
  - four cards with 8-15 lines each;
  - a counts strip.
- Products such as executive finance and fleet dashboards lead with **one sentence or number per card, plus a delta and a sparkline**, and put qualifiers behind "Why?" or a hover.
- The v7.1 coverage-once and tabs work starts this. Each card should go further: one figure, one sentence, a basis chip.

**Repetition of qualifiers.** "On the days checked", "estimated", "not billed or collected" and "counted separately · loss not priced" all appear several times per card. Defensibility needs the qualifier once, next to the figure, and the detail in "Why?".

**Copy quality.**
- Plain language is good at sentence level.
- Some system nouns still leak through: "Placement", "Unpriced risk", "Distinct consequence categories · no combined savings total", "Earlier version, kept for the record", "Selected sources: Example data, not field readings", "Open 2026-11-08 →" (an ISO date as link text on the Finding page).

**Codes on screen.** WR-007, ACT-002, INC-005, PM-009 and REC-000015 are fine as references. They are styled as primary link text, though, so they compete with the description. Products show the human title first and the code as a muted suffix.

### 3.3 Consistency across pages (grade: weak to medium)

- About **20 date forms with 5 defaults** (SR fixes this).
- **Three tab rows stacked** on the Finding and Site depth pages: Site tabs, then sub-tabs, then a third row on Performance. At 390 px this is 4-5 lines of tabs before any content (E5 capture 13).
- Status shows in several styles: pills, outlined chips, dashed "not assessed" chips and amber bars. "Unknown", "Not assessed", "Not available yet" and "Not measured yet" are near-synonyms that look different.
- Empty panels look different on every page: italic grey line, dashed card, or a notice.

### 3.4 Responsiveness and perceived speed (grade: medium; speed weak)

- Layouts adapt (760 and 1100 px breakpoints), but there are 20 distinct media queries with no shared breakpoint tokens.
- Wide tables at 390 px clip their last column without a scroll cue. The Kisiwa "Balance bridge" "Treatment" text is cut.
- **Perceived speed is the weakest point.**
  - Off-list pages take 10-36 s (BL-66).
  - Lens changes blanked the whole page until PL-1 fixed it.
  - There are 58 different "Loading…" strings, and skeletons are used only in places.
  - Products keep the page frame and show skeletons per panel, with content arriving progressively.
  - ANY-1 and ANY-2 fix the root cause. The UI side is a standard loading pattern.
- No `prefers-reduced-motion` rule exists. There is little motion today, but the rule must come with any micro-interaction.

### 3.5 Accessibility, WCAG 2.2 AA (grade: medium-good intent, gaps in practice)

**Good:** colour is never the only signal, tab and nav semantics are right, focus is visible, and labels are present on most controls.

**Gaps:**
- **Text size.** 9-10 px text is legal under WCAG but fails the readability intent and low-vision users.
- **Reflow at 400% zoom (1.4.10)** is likely to fail on wide tables and the five-column board grid.
- **Target size (2.5.8).** Many 20-22 px chips and links sit in dense rows.
- **Live regions are rare** (3 `aria-live`), so filter and lens results are not announced.
- **Charts have no data-table alternative.**
- **No skip link** to the main content was seen in the shell.

No audit with axe or NVDA has been run. Stage 1 adds one.

### 3.6 Internationalisation (grade: not started)

**Locale.**
- `<html lang="en">` is hard-coded.
- Month names are an English array (`ui/time.ts`).
- Dates use a fixed "2 Nov 2026" pattern.
- Native date inputs follow the browser locale, which gives the "11/02/2026 vs 2–8 Nov" mismatch on one bar (E5 capture 01).

**Numbers and currency.**
- `money2` gives "139.16" with no grouping, and the currency is shown as an ISO suffix ("139.16 USD").
- Products use `Intl.NumberFormat(locale, {style: "currency"})`. That gives "US$139.16", "139,16 $US" (French) or "TSh 139" (Tanzania; 0 decimals for TZS, KES or UGX where customary), with grouping.
- Estimated ranges should round to sensible significant figures ("about US$3–4", not "3.31–3.97") when the basis is modelled.

**Translation.**
- Most words come **from the server** (`chain/vocabulary.py`, `site_outcomes/*`, `warnings.py`), composed in English sentences with values inside them.
- This is the right place for a catalogue (one owner, already centralised). It needs:
  - message keys with ICU plural and gender rules;
  - an `Accept-Language` or user locale;
  - no sentence fragments joined with " · " in code.
- The 12 frontend `*Words.ts` files are the same pattern on the frontend.

**Time zones.**
- Estate pages are UTC-only ("Times in UTC"). That is correct for an evidence product, but a user wants their own or the Site's local time, with UTC available.
- The Site-local day rule exists in the mini-grid code.

**Right-to-left.** 118 physical left/right properties and 0 logical ones. The rail, tables and arrows ("→") would not mirror.

**Units.** kWh, L, °C and kW are fine internationally, but there is no unit-preference layer (gallons, °F) for a US client.

### 3.7 Empty, loading and error states (grade: weak)

- **Empty states are statements, not guidance.**
  - Examples: "No cold assessment for this window" (four times on one board), "No recorded next step", "Not available yet".
  - Products say what would fill the space and offer the next action: "No assessment for 8 Nov yet. Readings arrive daily; the next assessment runs at 02:00 UTC. [See readings]".
  - Panels that would only say "nothing" collapse into one "Not shown yet, and why" line.
- **Loading.** A full-page text line or per-panel text. A standard skeleton block is needed.
- **Errors.** Refusals are honest and typed ("Window not valid", "Sign in to edit Site prices"). Recovery actions are rare: no "Try again", and no "Go to last valid range".

### 3.8 Onboarding and first impression (grade: weak)

- There is no first-run experience: no welcome, no "what this page answers", no guided tour, no sample-data explanation beyond the "Demonstration" banner.
- The Portfolio subtitle ("Operating decisions across the estate…") is good. But the first viewport is filters and badges, not an answer.
- The top bar has no product identity beyond the rail logo: no user, no organisation switcher, no help. The v7.0 mock has them; the app does not.
- Sign-in does not exist (BL-54), and an international buyer will ask for it in the first five minutes: SSO, roles and audit.

### 3.9 Trust signals (grade: strong core, weak surface)

**Strong:**
- "Why?";
- source records;
- version history ("Earlier version 1 of 3");
- "as known at";
- the "Example data" badges;
- never adding incomparable money.

**Weak:**
- Freshness is shown in several places and forms: "Latest information, as of 10 Nov 2026, 05:28", "information up to 10 Nov, 05:26:48" (with seconds), and "Times in UTC".
- There is no single, consistent data-freshness indicator per page.
- There is no "last updated by" on records, and no visible security or compliance signals (SSO, audit log, data residency, a status page) that enterprise buyers look for.

## 4. Benchmark by pattern (not copying one product)

| Pattern | Seen in well-regarded products (examples, not models to copy) | AssetOps today | Target |
|---|---|---|---|
| One global time range, relative presets, in the URL | observability and analytics tools (Grafana, Datadog, Google Analytics) | 20 local bars | SR (planned) |
| Executive card: one figure, a delta, a sparkline, a basis | finance and fleet dashboards (Stripe, Linear insights, fleet APM) | paragraphs per card | stage 2 Portfolio |
| Exceptions-first lists with status tiles that filter | energy-fleet monitoring, infrastructure asset management | partly (v7.1 outcomes) | approved design |
| Design tokens in tiers, a component catalogue, density modes | Carbon, Atlassian, Material 3, GOV.UK Frontend | one flat token file | stage 1 |
| One chart standard with an accessible table fallback | Carbon Charts, Highcharts accessibility module, GOV.UK guidance | ad hoc | stage 1 |
| Locale-aware formats through `Intl`, ICU messages, RTL by logical CSS | most international SaaS | not started | stage 3 |
| Empty state = cause + next step; skeleton loading | Atlassian, Material, Shopify Polaris guidance | statements | stages 1-2 |
| Trust surface: freshness chip, audit trail, SSO, roles | enterprise B2B in general | strong core, little surface | stage 2 + BL-54 |

## 5. The staged plan

### Stage 0: before the client session (only what is already planned, plus optional quick wins)

- **Already planned, and they carry most of the first-impression gain:**
  - PF: coverage once, tabs, term family and scalable outcomes, 4.25 units;
  - SR: one date range, 1.75 units;
  - FC: Findings cards;
  - PL-1: the lens keeps the page.
- **Optional quick wins (QW, 0.75 units).** Each one is local and keeps the layout:
  1. a type floor of 12 px for table, head and secondary text, with tabular figures on numbers (tokens only);
  2. money through `Intl.NumberFormat` with grouping (`ui/money.ts`), keeping exact decimals;
  3. one shared `EmptyState` line style, with panels that hold only "nothing" collapsed into one "Not shown yet, and why" line on the Site boards;
  4. link text that never shows an ISO date ("Open 8 Nov dispatch day");
  5. a word-break fix for the matrix headers ("GreenHarves t").
- **Mockup rule.** Items 1 and 3 change what the v6.9/v7.0 mock specifies (its type scale and empty panels). They need a one-page **v7.2 "type and empty states" mockup sheet** that the owner approves before the build. That sheet takes about 0.25 units, inside the 0.75.
- **Recommendation:** do QW only if the lane has room after PF and SR. If not, nothing else before the client session.

### Stage 1: design-system foundation (3.5 units, after the client session)

1. **Tokens in three tiers (1.0).**
   - Primitive tier: colours, an 8-step type scale with a 12 px floor and 14 px body, a 4 px spacing scale, radii, shadows and breakpoints.
   - Semantic tier: surface, text, border, status (attention, watch, opportunity, on track, unknown, not measured), focus and data series.
   - Component tier.
   - Dark-mode values defined, but not shipped.
   - Density: comfortable as the default, compact for analyst tables.
   - The v7.2 mockup sheet shows every token. The owner approves it, and then it replaces the v6.9 type scale as the spec.
2. **Component library (1.5).**
   - Components: `PageHeader` (with one headline slot), `MetricCard`, `StatusPill` (one style for the six states), `DataTable` (sticky header, sort, density, scroll cue, card mode on phones), `Tabs` (one level, plus a "More" overflow at most), `SharedRangeBar`, `EmptyState`, `Skeleton`, `ErrorState` (with recovery), `Disclosure`, `Dialog`, `Toast`, `FreshnessChip`.
   - A catalogue page in the Lab workspace (not an operator route) renders every component in every state. It is the visual test bed. Storybook is not needed.
3. **Chart standard (0.75).**
   - One small library. Candidates: a thin layer over Observable Plot or visx, or hand-written SVG primitives if dependencies must stay minimal. The Architect picks at stage start, by bundle size and accessibility.
   - Six chart types:
     - sparkline;
     - line with an uncertainty band;
     - bar or stacked bar;
     - timeline (events, actions, verification);
     - status strip with a reason track;
     - bullet against a target.
   - One validated series palette, with colour-blind checks.
   - Every chart has a title, the unit, the source and "as known at", plus a "Show as table" alternative.
4. **Guards (0.25).**
   - A **style ratchet** in `tools/checks`, shrink-only like the hard-wiring ratchet. It counts raw hex colours, raw `font-size` values and physical left/right properties per file outside `ui/tokens.css`. It can only go down.
   - An axe-core pass over the capture set, failing on any new serious violation.

### Stage 2: page-by-page uplift (about 4.5 units, after stage 1)

**For each page family:**
1. A v7.2 mockup, approved by the owner.
2. The build, on stage-1 components.
3. Captures re-baselined.

**Order, by first-impression weight:**

| # | Page family | What changes | Size |
|---|---|---|---|
| 1 | Portfolio (all tabs) | one figure + sentence + sparkline per card; qualifiers into "Why?"; freshness chip; top 3 as cards | 0.75 |
| 2 | Site board (all types) | one-line headline per outcome; the five-column grid becomes "Drivers" + "In hand" with the rest behind a disclosure; empty panels collapse; event timeline chart | 1.0 |
| 3 | Finding detail | "What happened" first; status chips after it; timeline chart instead of the block strip; one tab row plus "More" | 0.5 |
| 4 | Findings and Actions lists | `DataTable` with density, card mode on phones, human title first, codes muted | 0.5 |
| 5 | Financials and Evidence | money charts with bands; receipts as a readable table | 0.5 |
| 6 | Work pages (Incidents, Maintenance, Records) | `DataTable`, status pills, empty states with a next step | 0.5 |
| 7 | Foundation, Health and depth pages | type and table pass; three tab rows reduced to two | 0.5 |
| — | First-run welcome and in-page "What this page answers" | one dismissible panel per root page, server text | 0.25 (in #1) |

### Stage 3: internationalisation (about 4.0 units, plus translation cost)

1. **Locale model (0.5).** Three separate settings, never mixed:
   - user locale: language and formats;
   - display time zone: the user's or the Site's, with UTC available on demand;
   - reporting currency (BL-67 Q1).
   They are stored per user once BL-54 exists, and are a tenant default until then.
2. **Formats through `Intl` (0.75).**
   - `ui/time.ts` and `ui/money.ts` become locale-aware (month names, ordering, grouping, decimals per currency).
   - Native date inputs are replaced by the `SharedRangeBar` and `FocusPicker` own fields, so one page has one date format.
   - Units go through one formatter.
3. **Message catalogue (1.75).**
   - Server words move from composed f-strings to keys with ICU MessageFormat parameters (plurals, lists). The server returns text for the request's locale.
   - The CH-6b2 rule stays: the server owns words, and the browser renders.
   - Frontend `*Words.ts` files move to the same catalogue.
   - A pseudo-locale (accented, 30% longer, mirrored) runs in captures, to find clipped text and hard-coded strings.
   - The first translation language is chosen by the first non-English client. Likely French or Kiswahili for the current markets: an owner question.
   - Professional translation and review is a cost outside the build units.
4. **Right-to-left (0.75).**
   - Physical left/right properties become logical ones (the style ratchet drives the 118 down to 0).
   - `dir` follows the locale, and arrows and icons mirror.
   - An RTL pseudo-locale capture pass is added.
   - Do this only if an Arabic, Hebrew or Persian-speaking market is planned. Otherwise the logical-property change alone (0.25) keeps the door open cheaply.
5. **`lang` attribute and font coverage (0.25).** `<html lang>` follows the locale, and the self-hosted font subset covers the chosen scripts.

## 6. How the existing rules stay intact

- **Mockup first.**
  - Every stage starts with v7.2 mockup sheets: tokens and components first, then each page family. The owner approves them before any build.
  - The approved v7.2 sheet replaces v6.9/v7.0 as the spec **only for what it covers**, and each page keeps its MOCK DEVIATION labels until its v7.2 page lands.
  - Nothing in stages 1-3 changes layout or content silently. A reviewer finding a mismatch with the mock is still High.
- **Frontend hard-wiring ratchet** (`tools/checks/frontend-hardwiring.mjs`).
  - The component library is Site-type agnostic. Components take server words and server states, never `site_type` branches or outcome ids. So every migrated page can only lower its counts.
  - Stage 2 pages run `--shrink` as they land.
  - The new style ratchet sits beside it with the same rules: shrink-only, no new baseline rows, reviewed diffs.
- **Defensibility rules unchanged.**
  - Shorter cards move qualifiers into "Why?" and basis chips. They never drop them.
  - R670 ("on the days checked" next to zeros) and the never-total rule stay.
  - Charts show measured and modelled values in different styles, and never add across Sites.
- **Demo speed until the client session:** only PF, SR and FC, with QW optional.

## 7. Backlog entry

BL-69 in `.agent/backlog-post-demo.md`. Its size: about 12.0 units across stages 1-3 (3.5 + 4.5 + 4.0), plus the optional QW (0.75), with translation as an outside cost.

Dependencies:
- **BL-54 (sign-in),** for per-user locale and the trust surface.
- **BL-66,** for perceived speed.
- **BL-67 Q1,** for the reporting currency.

## 8. Questions for the owner (when BL-69 is picked)

1. Which languages and markets come first (for example French, Kiswahili, Arabic)? This decides whether right-to-left is built or only prepared.
2. May the app self-host one brand font (for example Inter or IBM Plex, both open licence), or stay on system fonts with tabular figures?
3. Is a dark theme wanted for control-room use? Stage 1 prepares it either way, and shipping it costs about 0.5 units.
4. Should QW (0.75 units) go before the client session, if the lane has room after PF and SR?
