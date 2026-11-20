# AssetOps UI/UX guide

**A working standard for designers, implementers and reviewers · AssetOps Architect (Claude) · 19 Nov 2026 · applies to the vNEXT mock-up and every product screen built from it**

Owner, 19 Nov (verbatim, `owner/owner-uiux-guide-request-2026-11-19.md`): the Portfolio page is "the most unattractive, confusing and devoid of best ui/ux practices such as progressive disclosure, intentional and scalable UI realstate use ..etc . it also does not feel like a state of the art commercial applciation". The owner asked for "a ui/ux guide to ensure state of the art professional UI/UX".

**The objective every rule serves.** An operator executive at a mini-grid, cold-chain or EV-charging company opens a screen and, **within five seconds, knows what needs a decision and how much money is at stake**. Within thirty seconds they know why. Evidence is one click away. That is the value beyond monitoring tools: monitoring shows that the generator ran; AssetOps shows what that cost, what to do about it, who decides, and whether it paid off.

**What this guide changes and what it does not.** It changes presentation: hierarchy, disclosure, layout, visual system, charts and interaction. It does not change the product's content or rules: the constructs, the figures, the six honesty rules, the roles and the frame (rail, six Portfolio tabs, range bar, drill-down pages) stay as the frozen design (`layer4-transformation-design.md` rev 16.12) defines them. Where good UX needs a design change, §11 lists it as a proposal with a default.

---

## 0. What exists today, and stays

The vNEXT mock-up already has real strengths, and this guide builds on them:
- **Honest figures.** Every figure says how it is known, kinds are never added, and "Not available yet" is stated, never invented (design Rules 1 to 6). This is the credibility executives need before they trust money. It is the product's best differentiator, and the guide keeps it.
- **A token layer with light and dark themes.** `theme.css` defines surfaces, text, lines, accent and status tones on `:root`, with dark values for the system preference and for a forced choice. It also has a 4 px spacing scale, tabular numbers and a theme toggle. The guide keeps these token names (§4).
- **Plain-language checks.** `vocab_check`, `plan_switch_check` and `render_text` scan the rendered text. They stay exactly as they are (§10).
- **The builder decision guide.** `frontend/docs/architecture/ui-ux-decision-guide.md` covers long values, height caps, phone tables, states and words. It stays in force for those local choices. **This guide sits above it**: it governs composition, disclosure and the visual system. Where the two conflict on a vNEXT screen, this guide wins and the conflict is reported to the Architect.

What is missing is **composition**: the content is right, but it is laid out at a single level of detail, with no visual system holding it together. The diagnosis follows.

### 0.1 Why the current Portfolio fails the bar

Evidence comes from real-browser captures of the current mock, taken 19 Nov after the last theme pass. The capture used `/opt/assetecon/tools/pw/shot.cjs` with the measurement script `Docs/design-system/tools/measure_screen.cjs`. Lakeside Power, `#/portfolio`:

| Measure | 1440 × 900 | 1280 × 720 | 390 × 844 |
|---|---|---|---|
| Page height | 4,221 px (4.7 screens) | 4,508 px (6.3 screens) | 8,284 px (9.8 screens) |
| Where "Factors needing attention", the list to act on, starts | 3,677 px | 3,964 px | 6,946 px |
| Text elements under 12 px | 165 of 345 (48%) | same | 167 of 345 |
| Visible evidence chips | 41 | 41 | 41 |

1. **No primary task and no hierarchy.** The Overview runs eight blocks of equal weight:
   - the headline banner;
   - four hero cards;
   - a 13-row table of the gap split by heading;
   - the three-moves strip;
   - the value-chain strip;
   - four outcome cards, the Optimize card alone about 1,900 px tall;
   - a note;
   - the attention list.

   What to act on comes last, four screens down on a laptop and ten on a phone. No region has a primary action.
2. **No progressive disclosure.** Every level is shown at once:
   - Glance figures sit beside a cents-level reconciliation table.
   - Each outcome card repeats Findings, plan items, verdicts and potential that appear elsewhere on the page.
   - The page spells out its own rules ("The four headings sit over one structure…", "A residual appears only where a leaf is not observed; here it is zero").
   - The caveat "Design estimate: not yet tested on your recorded data" repeats. On the Kobo decision page it appears 17 times.
3. **The use of space is neither intentional nor scalable.**
   - The four cards are equal-width columns of prose, from about 700 to about 1,900 px tall.
   - Site names are written inside sentences ("Kobo · Customer consumption…").
   - The gap table has one column per Site.
   - The value chain is boxes and arrows that wrap. At 30 Sites the table and cards break; at 300 they are unusable.
4. **No visual system.** The stylesheets declare 52 font sizes, and 186 declarations are 8 to 11 px. On screen, 48% of text is under 12 px, and about 190 colours are hard-coded outside the tokens. Hue carries status, category (each card's coloured top rule) and certainty (violet "Design estimate", green "Emulated") at once. Headline money is shown in cents ("+$6,088.50").
5. **Quantities written as text, and system words in the copy.** Target against actual, the bridge and the value chain are text and tables, never drawn. The copy still reads as the system's language:
   - "composed from the sites' factors";
   - "Factor effects on contribution";
   - "valued options";
   - "a leaf is not observed".

The Decision page repeats the pattern (`#/decision/kobo-generator`, 3,648 px):
- nine stacked sections at one level;
- 64 of 252 text elements under 12 px;
- 28 chips;
- the recommended option in a green-filled row;
- no control to choose an option.

Dark mode renders legibly. Its problems are the same composition problems.

---

## 1. Principles, ranked

When two principles conflict, the higher one wins. Each one serves the objective above.

| # | Principle | The rule it sets | Why it serves the objective |
|---|---|---|---|
| P1 | **Decision first** | Every screen leads with what needs a decision, the money or unit at stake, and who decides. Each region has at most one primary action. | The executive's first question is "what do I need to do?". Monitoring tools never answer it; this is the differentiation. |
| P2 | **Money in context** | A figure is shown against its comparison: target for actuals, no action for options, budget for spend. A figure without one is an exception, and its label says why. | Executives judge gaps, not levels. |
| P3 | **Disclose by level** | Glance → queue and decide → explain → evidence (§2). Each level shows only its own content and links to the next. | Five seconds to the answer; detail stays available without burying the answer. |
| P4 | **Honest without noise** | Certainty is one quiet marker per figure; its words, source and rule are one click away (§6). Caveats are said once per scope. | Trust comes from rigour you can inspect, not from chips on every line. |
| P5 | **Scale by design** | Every layout is specified at 3, 30 and 300 Sites, and for one or many verticals (§3.3). Text never carries a list. | The buyers run portfolios, and a pilot must look like the product they will grow into. |
| P6 | **One system** | Only tokens, a single type scale, one icon set and the defined components. No one-off sizes or colours. | A consistent system is what makes software read as professional, commercial product. |
| P7 | **Plain words, people named** | Write in operator language with no system terms. Roles appear where decisions happen, as "Site manager, Kobo · Peter", never as a role switch. | Executives buy what they understand. Accountability they can see is half the value. |
| P8 | **Accessible and fast** | WCAG 2.2 AA, keyboard-complete, readable at 390 px, legible in dark mode. Skeletons, not spinners. | A demo that fails on a laptop, a phone or a projector loses the room. |

---

## 2. Information architecture and progressive disclosure

### 2.1 The four levels

| Level | Question | Time | What it holds | Form |
|---|---|---|---|---|
| **L1 Glance** | Am I on target, and what is at stake? | ≤ 5 s | One headline sentence (at most 2 lines); at most 4 KPI tiles, each a number, its comparison and one certainty marker; one primary action | Header band, above the fold at 1280 × 720 |
| **L2 Queue and decide** | What needs my decision, and by when? | ≤ 30 s | The decision queue: each item with its Site, a one-line issue, what is at stake, the due date and who decides; the plan's status and meters | A table on desktop, a list of cards on phone; starts above the fold at 1440 × 900 |
| **L3 Explain** | Why, and what are the choices? | minutes | The bridge, the value chain, factor tables against target, options compared against no action, the reasoning, and what would change the recommendation | Charts and tables in sections below the fold, or on the drill-down page |
| **L4 Evidence** | How do we know? | on demand | Records, provenance, the certainty word and its rule, the calculation, coverage, revision history, verification windows | A side drawer (§8) or a collapsed "How this is worked out" section; never inline at L1 or L2 |

**Rules for moving between levels.**
- Each level links to the next with a named affordance: a row opens its decision; a figure opens its evidence drawer.
- Nothing a level needs to be understood hides at a deeper level. The certainty marker is at L1; its explanation is at L4.
- A level-3 or level-4 element shown at L1 is a finding (§10).

### 2.2 Never on the first screen

- Explanations of the product's rules, such as "never summed" or "the four outcomes are read over…". These go in an "About these figures" popover or at L4.
- The same caveat more than once. A caveat is said once per scope: page, section or figure.
- More than one certainty marker per figure, or a marker on a figure of the scope's baseline class (§6, proposal U1).
- Factor-level prose, rows of lists longer than 7 without "Show all", or any table wider than its region.
- Footnotes, methodology, record identifiers, or internal codes.
- More than one primary button, or more than 4 KPI tiles.
- Mock review tooling taller than one 32 px strip (it is exempt from content rules, but it does not take the fold).

### 2.2a The overview budget (wave 2c)

An overview page holds the answer and the next step, nothing more: **the headline, at most four KPI tiles, the decision queue, one chart, and a slim strip of the four outcome headings**. Everything else lives in its tab and is linked from a single "More in the tabs" line. At 1440 the page stays under about two and a half screens; `ux_interaction_check` asserts at most six blocks and 2,500 px. On the Portfolio, "Where value leaks" lives on Demand and capacity, the insight on Outcomes by site, and the plan behind the Plan tile's "Review the plan". The four headings stay on the Overview (OD-21), as a strip whose tiles open their drawers.

### 2.3 What each screen holds at each level

| Screen | L1 Glance | L2 Queue and decide | L3 Explain | L4 Evidence |
|---|---|---|---|---|
| **Portfolio** (Overview tab) | The headline; tiles for contribution against target, the gap by heading, plan spend against budget with the plan's state, and the options' modelled value | The decision queue across Sites (top 6, "View all in Act first"); the plan card with state, meters, first three moves and "Review plan" | The bridge waterfall by heading; the value-chain chart; the four category tiles, each opening its factor table; the "Sites that look alike" insight | A drawer per figure; the category drawer with factors, certainty words and listed, never-summed values |
| **Portfolio** (other tabs) | The tab's one answer, such as "2 of 3 Sites below target" | Outcomes by site: a Site × heading table sorted by gap. Act first: the full queue and the plan summary | Demand and capacity: headroom against evidenced demand. What changed: Actions, verdicts, plan review. Scope: coverage by source | Source and coverage drawers |
| **Site** | The Site's contribution against target, its gap, and its open decisions as a count with money | The Site's queue; Actions in hand with owner and due date | The outcome board (factor rows with Issues, What can be done, Already in hand); value chain; trends | Asset and record drawers |
| **Decision** | The recommendation in one line: the option, its 12-month result against no action, its one-off cost, who decides and the deadline; the primary action **Choose this option** | The options table against no action (§7.2) | How each option changes what drives it; limits; cover; cost lines and who pays; the reasoning; what would change it; the verification plan, as collapsible sections | Records behind it; the calculation; the design-value status |
| **Findings** | Count by heading and by state, with money at stake | The Findings table, filterable by Site, heading and state, each with its decision or Action | The Finding page: what was seen, against what, since when, and its thread | Revisions and evidence |
| **Plan** | State (Draft, Proposed, Approved, Revised, Closed), version, who proposed and who approves; **Approve** / **Send back** for the approver | Items with their option, owner, due date, cost and crew; budget and crew meters; switches | Items left out and why; the cases; changes since the last version | The plan's history; each item's decision |
| **Financials** | Contribution, revenue, cost to serve and cash against target for the period | The lines most off target, each opening its factor | The bridge; the value chain; price and tariff versions | Records and versions |
| **Actions** | Overdue and due-this-week counts | The Actions table: what, Site, owner, due, state, origin | The Action page: steps, thread, verification verdicts | Events |

---

## 3. Layout and screen real estate

### 3.1 Grid and breakpoints

| Width | Rail | Content | Columns | Gutter |
|---|---|---|---|---|
| ≥ 1440 | 208 px, labelled | max 1280 px, centred | 12 | 24 px |
| 1280–1439 | 208 px | fluid | 12 | 24 px |
| 1024–1279 | 64 px icons, labels as tooltips, expands on demand | fluid | 12 | 20 px |
| 600–1023 | hidden; a menu button in the top bar | fluid | 6 | 16 px |
| < 600 (design target 390) | hidden | fluid | 4 | 16 px side gutter |

**Region patterns** (they compose every screen):
- **8 + 4**, a main column and an aside: the queue beside the plan; a table beside a summary.
- **12**: full-width tables and charts.
- **6 + 6**: two related charts.
- **3 × 4**: the KPI band.

Below 1024 px, the aside drops under the main column. The page never scrolls horizontally. Only a table or diagram scrolls, inside its own frame, with a visible cue (builder guide §1, §2).

### 3.2 Density

- **Comfortable** is the default for L1 and L2: table rows 48 px, card padding 16 px, a 24 px gap between sections.
- **Compact** is for L3 tables with more than 10 rows: rows 36 px.
- Text is never smaller than 12 px. Body text is 14 px and table text 13 px.
- The line length of prose is at most 75 characters.
- Whitespace separates groups. A border or a card separates only objects the user can act on.

### 3.3 Scaling: Sites and verticals

| Element | 3 Sites | 30 Sites | 300 Sites |
|---|---|---|---|
| Decision queue | All items | Top 6 by the design's order, then "View all (n)" | The same, plus filters for Site, vertical, heading and status, with the counts |
| Category tiles | Headline + counts | Same | Same: tiles hold counts and totals, never per-Site text |
| Bridge | Effects by heading and factor | Top 8 factors + "Other factors" | Same; a Site breakdown in the drawer |
| Site comparison | A table, or small multiples | A sortable table, sticky header | A paginated or virtualised table, search, saved filters; a Site × heading heat table |
| Map or list of Sites | List | List with filters | List with filters; a map only if location data exists |

**Several verticals.** A vertical filter (All · Mini-grid · Cold chain · EV charging) sits in the page header and shows only the verticals present. Figures in different units are never added across verticals. A portfolio tile that cannot sum shows one line per vertical, or a count, and says so. Where a captive EV depot has no revenue, Grow says "Not applicable: captive fleet", not "$0".

### 3.4 Tables, cards, charts or lists

| Use | When | Never |
|---|---|---|
| **Table** | Comparing more than 6 items on 3 or more attributes; anything a user sorts, filters or scans | For 1 to 3 items with one attribute |
| **Card** | Up to 6 different objects, each with its own action: KPI tiles, the plan card, category tiles | To hold sentences of data, or lists that grow with Sites |
| **Chart** | When the question is size, shape, gap or change (§5) | As decoration; when a table of 3 numbers would do |
| **List of cards** | A table's rows at phone width, each showing its first 3 columns, then "More" | Hiding columns without a way to see them |

### 3.5 Viewports

- **1280 × 720** (small laptop, projector): L1 is fully visible, and the first row of L2 is visible.
- **1440 × 900**: L1 and at least 3 rows of L2 are visible.
- **390 × 844** (phone):
  - one column in level order;
  - KPI tiles 2 × 2;
  - the queue as cards;
  - charts simplified to horizontal bars;
  - L1 plus the first queue card visible without scrolling, below a compact header of at most 120 px.
- Portfolio tabs at phone width follow proposal U4.

---

## 4. Visual system

Tokens extend `theme.css`, keeping the existing names. New tokens are marked **new**. Every colour and size on a screen comes from a token; a literal value is a finding.

### 4.1 Colour roles

| Role | Tokens | Use | Never |
|---|---|---|---|
| Surfaces | `--bg`, `--surface`, `--surface-2`, `--surface-3` | Page, card, raised and sunken areas | — |
| Text | `--text` (primary), `--text-2` (secondary), **new** `--text-3` (placeholder and disabled, light `#7a8699`, dark `#7d8899`) | — | `--text-3` for content a user must read |
| Lines | `--line`, `--line-strong` | Dividers, borders | Heavy borders around every block |
| Accent | `--accent`, `--accent-solid`, `--accent-soft` | **Interactive only**: links, primary buttons, selection, focus | Status, categories or decoration |
| Status | `--good`, `--warn`, `--bad` (+ `-soft`, `-line`); **new** `--info` (light `#0e6a8a`, dark `#6cc4e0`) | State of a figure against its comparison (§4.6) | Categories or certainty |
| Certainty | Neutral only: `--text-2`, plus a pattern for modelled marks in charts | The marker (§6) | Hue. Violet is retired from certainty |
| Charts | **new** `--series-actual` (= `--text`), `--series-target` (= `--text-2`, dashed), `--series-1…4`, a muted categorical set for Sites or verticals | §5 | Status hues as series colours |

Both themes are designed, not inverted. Every pair is checked in both: text 4.5:1, large text and non-text 3:1 (WCAG 1.4.3, 1.4.11). Dark mode raises surfaces by lightness, not by shadow.

### 4.2 Type scale

The font is Inter, or the system UI font; numbers use tabular figures. There are seven sizes, replacing today's 52.

| Token | Size / line | Weight | Use |
|---|---|---|---|
| `--fs-xs` | 12 / 16 | 500 | Labels, captions, chips, table headers (sentence case, not spaced capitals) |
| `--fs-sm` | 13 / 18 | 400 | Table cells, secondary text |
| `--fs-md` | 14 / 20 | 400 | Body |
| `--fs-lg` | 16 / 24 | 600 | Section titles (h2) |
| `--fs-xl` | 20 / 28 | 600 | Page sub-headline; decision headline |
| `--fs-2xl` | 24 / 32 | 600 | Page title (h1) |
| **new** `--fs-kpi` | 32 / 40 | 600 | KPI numbers only |

The weights are 400, 500 and 600. Spaced all-capitals are used only for the rail's group labels.

### 4.3 Spacing, radius and elevation

- **Spacing**: 4, 8, 12, 16, 24, 32, plus **new** 48 and 64 (`--s7`, `--s8`) for page-level rhythm. Inside a component the step is 8; between components 16; between sections 24 or 32.
- **Radius**: `--r1` 6 px for controls and chips; `--r2` 8 px for cards; **new** `--r3` 12 px for drawers and dialogs.
- **Elevation**:
  - 0: flat, with a border; cards and tables.
  - 1: `--shadow-sm`; sticky headers, a hovered card that is a link.
  - 2: `--shadow-md`; drawers, popovers and menus.
  - 3: a dialog, with `--overlay`.
- A card that is not a link does not lift on hover. Today's `.value-card:hover` translate is removed.

### 4.4 Iconography

- One outline set at 1.5 px stroke (the current inline set, Lucide style), 16 px in text and 20 px in navigation.
- Icons sit beside a label. Only search, close, more, expand, external link and the theme toggle stand alone, and each has an accessible name.
- Category headings: Grow (trending up), Optimize (gauge), Protect (shield), Assure (badge check). Each is an icon plus its name, with no colour of its own (§4.6).

### 4.5 Components

The set is closed: build screens only from these.
- Page header: title, context line, filters, one primary action.
- KPI tile.
- Section, with a title, an optional "About" popover and an optional action.
- Data table.
- Queue row or card.
- Status chip.
- Certainty marker.
- Meter.
- Chart frame: title, the answer in one line, the chart, and a "Show as table" toggle.
- Side drawer.
- Dialog.
- Toast.
- Inline notice.
- Empty, loading and error states.
- Tabs.
- Filter bar with applied-filter chips.
- Person chip.

A new component needs an Architect ruling.

### 4.6 Status semantics

Status is one of five states. Each always carries a word, and an icon where space allows, never colour alone (WCAG 1.4.1).

| State | Token | Icon | Words (examples) |
|---|---|---|---|
| Adverse against target | `--bad` | arrow down-right | "Below target", "Over budget", "Off target" |
| At or near a limit; deadline | `--warn` | triangle | "At its limit", "Due 27 Nov" |
| On or better than target; met; verified | `--good` | check | "On target", "Met", "Verified" |
| New; opportunity | `--info` | sparkle | "New", "Opportunity" |
| Unknown; not explained yet | neutral | circle with a question mark | "Not explained yet" |

- Colour follows meaning, not sign: a cost rising is `--bad`.
- Categories and certainty never use status hues. Today the Grow card's green top rule reads as "good", and the Protect card's orange as a warning.

---

### 4.7 Brand packs (wave 2; owner, 19 Nov: "some african design identity … configurable")

A brand pack is a named set of tokens, applied as `data-brand="<name>"` on the page root (`brand.css`). The product ships **Neutral** (the default, no attribute) and **East Africa** (`data-brand="east-africa"`). Regional packs share one structure, so **West Africa**, **Southern Africa** or others are new token blocks, not new code.

| A pack may change | A pack may never change |
|---|---|
| Surface warmth (`--bg`, `--surface*`, `--line*`), text tints within AA, the interactive accent, the rail colour | Status colours and their meanings (§4.6) |
| The brand mark, a textile band under the top bar (up to 12 px), the rail footer rule and a pattern in the rail's empty lower part, the active-item and active-tab colours, the heading typeface and colour with a short accent rule under the page title (wave 2c: clearly distinguishable, still professional) | Chart series meaning, type sizes, spacing, radius, layout, components |
| The empty-state mark and the loading shimmer | Anything behind data: no motif in a chart, table, tile or card body |

- **East Africa**: a sunlit palette (sand surfaces; terracotta, ochre, deep indigo and earth accents) and accents from the region: kikoi and kanga stripe bands, a Maasai beadwork row, and the stud-and-link chain of Swahili-coast carved doors. The active rail item takes the pack's indigo. The accents are contemporary and sparing, never pictorial or a stereotype.
- **To add a pack:** copy the three `east-africa` token blocks in `brand.css` under a new name (light, dark by preference, dark by choice), and register it in `UX_BRANDS` (`loop-ux.js`). No component or layout changes. Then run the contrast measure for the pack in light and dark: 0 text below AA.
- **Resolution:** the tenant's setting (`UX_BRAND_BY_TENANT`; the three demo operators start in East Africa, U10), else Neutral, the product default. In the mock-up, a review-bar switch overrides it for comparison.
- **Heading typeface:** a pack may set `--font-heading`. East Africa uses an editorial serif stack (Iowan Old Style, Palatino or Georgia, with DejaVu Serif as the offline fallback), for headings only. Body text and figures stay in the system sans.
- **Layout height:** a pack may add at most 32 px of decorative height (the band and the title rule); the brand-switch check asserts it.

## 5. Data visualisation

Each chart answers one question. Its title states the answer, for example "Cost to serve explains $755 of the $852 gap". Every chart has a "Show as table" toggle and a text alternative.

| Question | Chart | Rules |
|---|---|---|
| How far from target? | **Bullet**: the actual bar, a target tick, the gap labelled | In KPI tiles and factor rows. No gauges or dials |
| Why is it off target? | **Bridge waterfall**: target → effects grouped by heading (Grow, Optimize) → actual | Effects sorted by size within a heading; at most 8 bars plus "Other factors"; the part not explained yet is a neutral hatched bar; totals to the cent in its table view (Rule: effects equal the gap) |
| Where does value leak? | **Value chain**: horizontal bars on one baseline (delivered → metered → billed → collected), each leak a labelled segment between stages | A stage with no source is an outlined empty bar labelled "Not available yet", never zero (Rule 3). Units stay in kWh until billed, then money; the axis change is labelled |
| How is it moving? | **Line** with a target line; at most 3 series | Only with real history; otherwise the tile says "Trend not available yet". Sparklines only in tiles, with no axis |
| Which factors or Sites contribute most? | **Diverging horizontal bars**, sorted | Up to 12 Sites as small multiples; more Sites as a sortable heat table (Site × heading) |
| Which option is best? | **The options table**, with a dot-and-range column for the 12-month result against no action | No action is the zero line, always shown (Rule 5); a modelled result is a hollow dot; ranges come from the stated sensitivities |
| How much budget or crew is used? | **Meter** | Label "$3,750 of $5,000"; `--warn` at 90% or more, `--bad` over |

**Never use:**
- pie or donut charts for gaps;
- 3-D effects or dual axes;
- stacked or added marks of different certainty (Rule 2). A modelled bar never stacks on a recorded one: it sits beside it, outlined or hatched;
- red and green as the only difference between marks;
- legends where direct labels fit.

**Wave 2 additions.**
- **The bridge is the page's hero**, full width under the decision queue (the queue stays above the fold). It has two parts:
  - the totals on an honest zero axis, as one bullet;
  - below it, **the gap itself as the scale**: target at the left edge, October at the right, each driver a step across it, grouped under its heading with the heading's subtotal. The heading is printed once, never on every row. There is no axis break and no empty area, and each step shows its share of the gap.
  - Tooltip figures never break across lines.
- **Bars take the guide's thresholds:** on or better than target is green; within 5% is amber; further off is red.
- **Where value leaks** draws the losses, not the stages. Each stage is a labelled value. Under it, each loss is a bar drawn against the largest loss, with its share of the stage before it ("1,350 kWh · 5.9% of delivered"). The title names the biggest leak. With no measurable leak, the title says "no leak measured".
- **The bridge is the page's interactive chart.** Each step links to the decision on its driver, and shows its detail (amount, share of the gap, the decision) on hover and on keyboard focus. A step with no decision says so in its detail.
- **Trend slot.** Each money tile reserves a trend line. Until earlier months are loaded it shows a dashed placeholder and "Trend not available yet", never an invented line.

- **Displayed figures reconcile** (wave 2c ruling). Parts are rounded with the largest-remainder method, so the shown parts add up to the shown total: steps to their heading's subtotal, subtotals to the gap. Shares add to 100%. A check asserts it for every operator.
- **Shares are of what widens the gap.** A step that works the other way is an **offset**: it shows "offsets" and its amount, never a share. Example: Harvest's +$155 electricity effect.
- **One sign rule per page:** every figure is its effect on the headline result. For a cost centre, a cost overrun is negative (worse), as the tile, the drawer and the Site rows show. The bridge follows the same rule (Metro: −$2,604, −$600, +$20).
- **Scales hold their marks.** When offsetting steps run past the target or October, the track widens to the lowest and highest running total, and Target and October sit at their scaled places. A check asserts every bar ends inside its track.
- **Modelled never carries the weight of an actual.** A modelled tile is lighter (smaller value, secondary colour, dashed outline) and keeps its marker.
- **A number that opens its working** looks like text at rest and shows an underline on hover and focus. It is a button, so it stays reachable by keyboard.
- **Prose is 14 px.** 12 to 13 px is for labels, units, notes and table cells only.
- **Trend (when history is loaded, U9):** a 64 × 16 px sparkline of the months loaded, followed by the change against last month in words ("−$120 against September"). The accessible name lists each month and value. With fewer than two months it shows the "Trend not available yet" state, never an invented line.

### 5.1 Numbers

| Context | Format | Example |
|---|---|---|
| L1 and L2 money | Whole currency; compact from 10,000 | $1,443 · $12.4k · $1.2M |
| L3 money | Whole currency | $8,245 |
| Bridge reconciliation and L4 | To the cent | $8,244.60 |
| Deltas | Always signed, with a true minus (−); a direction word in the label | −$852 below target |
| Percent | At most 1 decimal; whole numbers at L1 | 59% of target · 98.6% |
| Units | Always beside the number, with a thin space | 21,445 kWh · 330 L · 3 crew visits |
| Dates | Day and month, with the year only when it differs; Site-local time (builder guide §4) | 27 Nov · as of 06:00, 6 Nov |

- Numbers are right-aligned in table columns, and a column header carries its unit.
- Rounding never changes a sign or a comparison's outcome.
- Every figure has the exact value in its drawer (proposal U3).

---

## 6. Certainty and provenance

**One indicator, detail on demand.** Each figure carries at most one quiet certainty marker after its number. The marker's accessible name and tooltip give the design's exact word (Rule 1). Clicking the figure opens the evidence drawer (L4) with:
- the word;
- what it is computed from;
- the records behind it and its coverage;
- the rule that applies ("never added to recorded figures");
- whether a recalculation is pending.

| Class (design Rule 1) | Marker at L1 to L3 | Notes |
|---|---|---|
| **The scope's baseline class** (usually Recorded, Measured or Calculated; in today's demo, Emulated) | **None**: stated once for the page or section ("Figures are simulated demo data unless marked"), and in every figure's accessible name and drawer | Proposal U1. A figure differing from the baseline is marked |
| Verified | Check icon + "Verified" | The only class shown as a positive claim; money is credited only here |
| Estimated, Quoted | "est." / "quote" as small text after the number | — |
| Modelled | Hollow circle + "Modelled" at L1 and L2; hollow circle only in L3 tables, with a column legend | In charts: hollow or hatched marks |
| Emulated | "Simulated" in words, as the page baseline notice or as the figure's marker | Never Verified, never realised money (D14) |
| At stake, not money | Shown in its own "Listed, never added" group, with "at stake" after the value | Never inside a total |
| Not available yet | The words replace the value; one line on what would fill it, at L3 | Never "0", never "—" alone (Rule 3) |

**Caveats once per scope.** A caveat such as "Design estimate: not yet tested on your recorded data" is one notice at the top of the page or section. The affected figures carry a small dagger (†) that points to it (proposal U2). Today the same sentence appears 17 times on the Kobo decision page.

**Freshness.** The top bar shows "Figures as of 06:00, 6 Nov". Figures are recalculated at the daily run, or at once when someone asks (owner, Q7; OD-23). The pending notice carries a secondary **Recalculate now** button. Pressing it turns the notice to "Recalculated · figures as of <time>", recorded under the person who asked. Until the recalculated values exist, it says the numbers are unchanged; it never invents them. This is a mock-up addition, labelled MOCK DEVIATION. While a recalculation is pending, an inline notice under the page header says "Thika is being recalculated after a new invoice; its figures are from 06:00" (design §2.8). There is one notice, not a badge per figure.

---

**Wave 2: one provenance control.** Under the page title, a single quiet "ⓘ About these figures" popover replaces the scope lines, the section-level "About" notes and the footer's demo-data line. Certainty markers stay only where §6 requires them (a figure that is not the page's baseline). It holds the baseline evidence word, the † meaning (its summary shows "· † design estimates" when the page has any), "Names are illustrative" and how to open a figure's working. Esc closes it.

## 7. Workflow surfaces

The system proposes; people choose, approve and act (design §2.6). Every surface below shows **who** decides and records it under their name.

### 7.1 Decision queue

- **Row anatomy**: status chip · Site · the issue in one line (at most 90 characters) · at stake (money or unit, with its marker) · due date · who decides (person chip) · **Decide**, a button-styled link to the decision page.
- **Order**: the design's placement (must do, deadline, value, evidence; design §2.8, "never a value ranking"), shown as groups with headers. The UI never re-ranks.
- **Header**: a count and urgency, such as "6 need a decision · 2 due this week".
- **Phone**: each row becomes a card with the chip and Site on the first line, the issue, then the at-stake value and due date, then the person chip and **Decide**.

**Wave 2c row rules.** The status chips sit on their own line and the title starts on the next, so every row has the same left edge. A title never repeats a column: in the Kobo row, "Kobo generator stop setting" reads "Generator stop setting". An empty cell stays blank, and "No deadline" is said only to screen readers. Exactly one Decide is primary: the first row's, which is the first decision to take. The checks assert all four.

**Wave 2 row anatomy (replaces the sentence row).**
- **One row per decision.** Every issue behind it is a status chip on the row, and "Why (2 issues)" lists each issue. Counts on every screen are decisions, not issues.
- A short **title**: the decision's name, for example "Kobo generator stop setting".
- Columns: Site · At stake · Due · Who decides · **Decide**. The person chip never wraps.
- **Why ▾** expands the explanation and the certainty ("How sure: Modelled · † design estimate"). Certainty markers stay out of the row itself.
- **Controls** above the list: a type-ahead Site filter, Status, Sort (priority, due date, at stake), Group (by urgency: due this week, this month, later, no deadline; or by Site) and a Compact toggle, with a live "n of m" count. A control appears only when it can change something.
- **The row lays itself out by the room it has** (a container query): with less than 880 px it stacks, as in a side column or on a phone. No cell may run into its neighbour; `ux_interaction_check` asserts it at 1280 and 1440.
- **At 50 to 300 Sites:** filters and sort run on the server and are kept in the URL; 25 rows a page; grouping by Site shows collapsed groups with counts; saved views per person. A worked count: 300 Sites with about four open decisions each is about 1,200 rows. That is 48 pages at 25 a page, or 1 page of the 25 due this week when grouped by urgency. The scope switcher and the Site filter are type-ahead for the same reason. The Metro operator, with 3 Sites, 4 statuses and 7 issues, demonstrates the controls in the mock-up.

### 7.2 Option comparison (Decision page L2)

- **Fixed columns**: Option · 12-month result against no action · one-off cost and who pays · limits (pass or fail, with words) · condition · recommendation.
- **No action** is always the last row: the baseline, pinned and labelled.
- **The recommended row** has a "Recommended" chip and an accent left rule, not a green fill. Its row holds the primary button **Choose this option**. Other rows hold a secondary "Choose instead".
- **Rejected or deferred options** show their reason in the row. Limit detail expands inline.

### 7.3 Choosing, creating and tracking Actions

1. **Choose.** A dialog confirms in plain words what happens:
   - which Actions are created, and who owns them, with due dates;
   - whether the change is released now (within the spend and crew-visit thresholds, and not capital) or waits for the plan's approval;
   - that the choice is recorded under the chooser's name.
2. **Create an Action** from a Finding or a plan item in a side drawer. The fields are: what, owner, due date, origin (prefilled and read-only) and plan item. Saving shows a toast, "Action created · View", and returns focus.
3. **Track** an Action on its page as a horizontal step indicator through the thread's states (in hand → applied → monitoring → verified, or recurred). The three verdicts (operational, economic, causal) show as three separate chips, never one score.
4. **Overdue** items show a `--warn` chip, "Overdue by 3 days", in every list.

### 7.4 Plan approval

- **The plan header** shows a state chip, the version, "Proposed by AssetOps", and "Approved by: Operator executive · <first name>", or "awaiting".
- **For the approver**, a sticky action bar holds **Approve plan** (primary) and **Send back** (secondary). Send back requires a reason and a trade-off, in a dialog.
- **For other roles**, the bar reads "The operator executive approves this plan". No disabled buttons without a reason.
- **"Changes since version 2"** is a compact diff list at the top of a revised plan.

### 7.5 Who decides

The person chip reads role, scope and first name: "Site manager, Kobo · Peter". It appears on:
- the queue row;
- the decision header;
- each plan item;
- each Action row;
- each history entry.

There is no role switcher, role view or role filter (design §2.6; memory "no bolt-on role filters").

### 7.6 Empty, loading and error states

| State | Treatment | Copy example |
|---|---|---|
| Loading | A skeleton in the layout's shape, after 300 ms; `role="status"` per region | — |
| Empty, nothing waiting | A calm line plus the next relevant date or action | "No decisions waiting. The next books close on 6 Dec." |
| Not available yet | The value replaced by the words; at L3, one line on the source that fills it | "Not available yet · needs the energy-management export" |
| Filtered to nothing | Name the filter and offer to clear it | "No Sites match Cold chain · At its limit. Clear filters" |
| Error | `role="alert"`, a plain reason, **Try again** only if recoverable (builder guide §3) | "Figures could not be loaded. Try again" |
| Stale | One inline notice (§6) | — |

### 7.7 Microcopy

- Sentence case. Verbs on buttons ("Choose this option", "Approve plan", not "Submit"). Units on every number.
- Lead with the answer: "Contribution is $852 below target", not "October contribution, composed from the sites' factors: …".
- No system vocabulary (`vocab_check` enforces its list). Write the user's words instead:

| Not this | This |
|---|---|
| factor structure | what drives it |
| valued options | the options |
| attributed to factors | explained |
| the replay | a re-run on your recorded days |
| deviation | gap to target |
| plan (for a target) | target |
| evidence class | how sure we are |

---

## 8. Interaction

| Pattern | Use for | Rules |
|---|---|---|
| **Page** | Objects with identity: Site, Decision, Finding, Plan, Action | The URL is shareable; breadcrumbs; Back restores scroll and filters |
| **Side drawer** (right, 480 px; full screen on phone) | L4 evidence, a row's detail, creating an Action | Keeps the context visible; Esc closes it; focus is trapped and returned; the URL reflects it, so it can be shared |
| **Dialog** | Confirming a consequential act: choose, approve, send back | Says what happens and who is recorded; never for reading |
| **Popover** | "About these figures", a term's meaning | Opens on click, not hover only; Esc closes it |
| **Inline expand** | Table row detail, long values (builder guide §1) | `aria-expanded` |

- **Filters**: a filter bar under the page header (vertical, Site, heading, status), with applied-filter chips and "Clear". Filters are kept in the URL. The period selector is global, in the top bar.
- **Drill-down**: a figure opens its evidence; a row opens its object. Each target is a single link or button; a whole-row link never contains other controls.
- **Motion**: 150 to 200 ms ease-out for drawers, expansion and toasts, and nothing else. `prefers-reduced-motion` removes it. There is no parallax, no count-up numbers and no hover lifts.
- **Keyboard and accessibility (WCAG 2.2 AA)**:
  - a skip link, landmarks, one `h1`, ordered headings and `th scope` on tables;
  - focus visible at 2 px and 3:1 contrast, and never hidden under a sticky bar (2.4.11);
  - targets at least 24 × 24 px (2.5.8), 44 px for touch where layout permits;
  - reflow at 320 px (1.4.10);
  - charts with a text alternative and a table view;
  - toasts announced politely, and never the only record of a result;
  - drag never required.

---

**Wave 2 navigation.**
- **Command search:** Ctrl K, ⌘K or "/" anywhere, or the top bar's search. It finds Portfolio views, the plan, Sites, decisions and the main screens. Use ↑ ↓ to move, Enter to open and Esc to close.
- **Scope switcher:** "All sites ▾" in the top bar opens the portfolio or one Site. It is a switch of scope, never of role.
- **Period menu:** the period chip is a menu. It shows the current period; earlier periods and custom ranges say "not available yet" until history is loaded.
- **The rail** keeps every item (the frame rule) and is visually compacted. Merging its legacy groups is proposal U8.

## 9. Worked example: the Portfolio redesigned

Lakeside Power, October 2026, Overview tab. The figures are the frozen mock's.

### 9.1 1440 × 900 (recommended)

```
┌───────────┬────────────────────────────────────────────────────────────────────────────────────────────────┐
│AssetOps   │ Lakeside Power ▾                October 2026 ▾   As of 06:00, 6 Nov   ⌕ Search   (BY)          │
│           │ ────────────────────────────────────────────────────────────────────────────────────────────── │
│Portfolio  │ Portfolio                                                [All verticals ▾]  [Export]           │
│Sites      │ 3 village mini-grids · books closed 6 Nov · simulated demo data unless marked                  │
│Assets     │ Overview  Outcomes by site  Demand and capacity  Act first  What changed  Scope                │
│           │ ────────                                                                                       │
│Findings   │ L1  Contribution is $852 below target in October; cost and efficiency explain $827.            │
│           │ ┌ Contribution ──────┐ ┌ Gap to target ─────┐ ┌ Plan, Nov–Dec ─────┐ ┌ Options' value ────┐    │
│Actions    │ │ $1,443             │ │ −$852              │ │ $3,750 of $5,000   │ │ +$6,089 ○ Modelled │    │
│Incidents  │ │ ▓▓▓▓▓▓▓▓░░│ $2,295 │ │ Optimize −$827     │ │ ▓▓▓▓▓▓▓▓▓▓░░ 75%   │ │ over 12 months     │    │
│Maintenance│ │ 63% of target      │ │ Grow −$25          │ │ Awaiting approval  │ │ before trials †    │    │
│Records    │ │                    │ │ fully explained    │ │                    │ │                    │    │
│           │ └────────────────────┘ └────────────────────┘ └────────────────────┘ └────────────────────┘    │
│Evidence   │ L2                                                                                             │
│           │ ┌ Needs a decision · 6 · 2 due this week ──────────────────┐ ┌ The plan ─────────────────────┐ │
│Financials │ │ MUST DO                                                  │ │ Proposed · v1                 │ │
│           │ │ ▲ At its limit  Kisiwa  Evening supply on one            │ │ Executive approves            │ │
│Settings   │ │    generator at 95% load · 30 h no backup Site mgr ›     │ │ Budget ▓▓▓▓▓▓▓░ $3,750        │ │
│           │ │ DEADLINE                                                 │ │ Crew   ▓▓▓▓▓▓▓▓ 3 of 3        │ │
│           │ │ ▲ Deadline  Mto  Inverter 2 failed; warranty             │ │ 1 Repair generator 1          │ │
│           │ │    notice due 27 Nov · $2,600 at stake       ›           │ │ 2 Battery evidence            │ │
│           │ │ VALUE                                                    │ │ 3 Stop at 70% battery         │ │
│           │ │ ↘ Off target  Kobo  Generator runs while solar           │ │ [ Review plan ]               │ │
│           │ │    could carry the load · −$413        Peter ›           │ └───────────────────────────────┘ │
│           │ │ … 3 more · View all in Act first                         │ ┌ Insight ──────────────────────┐ │
│           │ └──────────────────────────────────────────────────────────┘ │ Kisiwa burns the most         │ │
│           │                                                              │ diesel and has nothing        │ │
│           │                                                              │ to save.  Open Kobo ›         │ │
│           │                                                              └───────────────────────────────┘ │
│           │                                   ─ ─ ─ fold at 900 px ─ ─ ─                                   │
│           │ L3                                                                                             │
│           │ ┌ Where the gap comes from ──────────────────┐ ┌ Where value leaks ──────────────────────────┐ │
│           │ │ Target              2,295 ▇▇▇▇▇▇▇▇▇▇       │ │ Delivered 23,050 kWh ▇▇▇▇▇▇▇▇▇▇▇            │ │
│           │ │ Grow: kWh sold        −25 ▏                │ │   losses 1,350 ░                            │ │
│           │ │ Candidate running    −413 ▇▇               │ │ Metered   21,700     ▇▇▇▇▇▇▇▇▇▇             │ │
│           │ │ Fuel not explained   −176 ▇                │ │   unmapped, adjusted 255 ░                  │ │
│           │ │ Necessary running    −167 ▇                │ │ Billed    21,445     ▇▇▇▇▇▇▇▇▇▇             │ │
│           │ │ Other factors         −72 ▏                │ │ Revenue $9,688 → Cash $8,870                │ │
│           │ │ Actual              1,443 ▇▇▇▇▇▇           │ │ Capacity: Not available yet                 │ │
│           │ │ [Show as table · by Site]                  │ │ [Show as table]                             │ │
│           │ └────────────────────────────────────────────┘ └─────────────────────────────────────────────┘ │
│           │ By outcome                                             [About these figures ⓘ]                 │
│           │ ┌ ↗ Grow ────────────┐ ┌ ◔ Optimize ────────┐ ┌ ⛉ Protect ─────────┐ ┌ ✓ Assure ──────────┐    │
│           │ │ $9,688 vs 9,785    │ │ $8,245 vs 7,490    │ │ 2 of 4 off target  │ │ 91.5% cost recorde │    │
│           │ │ 1 opportunity      │ │ 3 Findings         │ │ 3 values at stake  │ │ 0 verified         │    │
│           │ │ View factors ›     │ │ View factors ›     │ │ View measures ›    │ │ View evidence ›    │    │
│           │ └────────────────────┘ └────────────────────┘ └────────────────────┘ └────────────────────┘    │
│           │ † Design estimate: not yet tested on your recorded data.                                       │
└───────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

At 1280 × 720 the same layout fits L1 and the queue header above the fold. The rail collapses to icons only below 1280.

### 9.2 390 × 844

```
┌────────────────────────────────────┐
│ ☰ Lakeside Power ▾     Oct ▾  (BY) │
│ Portfolio                          │
│ Section: Overview ▾          (U4)  │
│                                    │
│ Contribution is $852 below target  │
│ in October; cost and efficiency    │
│ explain $827 of it.                │
│ ┌ Contribution ┐ ┌ Gap ──────────┐ │
│ │ $1,443       │ │ −$852         │ │
│ │ of $2,295    │ │ Optimize −827 │ │
│ └──────────────┘ └───────────────┘ │
│ ┌ Plan ────────┐ ┌ Options ──────┐ │
│ │ $3,750/5,000 │ │ +$6,089 ○ †   │ │
│ │ Awaiting     │ │ 12 months     │ │
│ └──────────────┘ └───────────────┘ │
│ Needs a decision · 6               │
│ ┌────────────────────────────────┐ │
│ │ ▲ At its limit · Kisiwa        │ │
│ │ Evening supply on one          │ │
│ │ generator at 95% load          │ │
│ │ 30 h without backup            │ │
│ │ Site manager, Kisiwa  [Decide] │ │
│ └────────────────────────────────┘ │
│   … next cards · View all (6)      │
│       ─ ─ fold at 844 px ─ ─       │
│ The plan (card) · Where the gap    │
│ comes from (bars) · Where value    │
│ leaks (bars) · By outcome (4 rows) │
│ · Insight · † notice               │
└────────────────────────────────────┘
```

The figures are the current mock's. Who decides and the at-stake values come from the mock's decision data. A queue cell whose value is not in that data reads "Not available yet", never a typed number. The wireframes show proportions only; the slice spec fixes each row.

### 9.3 Nothing lost: where today's content goes

| Today (Overview, `loop-portfolio.js` `overviewScreen`) | Redesign | Level |
|---|---|---|
| Headline banner (contribution against target, gap, Grow −$25, Optimize −$827) | Headline sentence + the Gap tile | L1 |
| Contribution card (target $2,295; 91.5% of cost on simulated records) | Contribution tile with a bullet against target; the share of cost on records moves to the Assure tile and the drawer | L1 / L3 |
| Gap card (by heading, residual $0.00) | Gap tile; "all of it explained" replaces the residual line | L1 |
| Plan-spend card ($3,750 of $5,000, crew 3 of 3, Quoted) | Plan tile + the plan card's meters; Quoted as a "quote" marker | L1 / L2 |
| Modelled 12-month change + design-estimate chip | Options' value tile, ○ Modelled + the † page notice | L1 |
| "The gap, split by heading" table (13 rows × Kobo, Kisiwa, Mto, total) | "Where the gap comes from" bridge chart; the full table by Site in its "Show as table" view | L3 |
| The plan's first three moves + Open the plan | The plan card list + **Review plan** | L2 |
| Value chain strip (capacity n/a, delivered, losses, metered, adjustments, billed, revenue, in transit, outstanding, cash) | "Where value leaks" chart; in transit and outstanding in its table view | L3 |
| Four outcome cards: factor effects, potential, Findings, plan items, verdicts, service-failure cost, cash collected, measures, listed-never-summed values, the A1–A5 groups | Four category tiles (headline + counts) → a category drawer holding every one of those groups unchanged, with certainty words | L3 / L4 |
| Note on how the four headings relate | "About these figures" popover | L4 |
| Factors needing attention (6 rows: state, Site, text, Decision link) | Decision queue, the same rows plus at stake, due date and who decides | L2 |
| Sites that look alike need different levers | Insight card in the aside | L2 |
| Tabs, breadcrumbs, context line, figures as of | Page header and top bar | L1 |
| Footer | Unchanged | — |

### 9.4 Alternatives rejected

- **A tile dashboard**: a Grafana-style grid of many KPI and chart widgets. Rejected because it is what monitoring tools look like. It shows levels, not decisions, and it scales by adding widgets, not by answering the question (P1).
- **An inbox as the home page**: the queue only, with money behind a click. Rejected because executives need the money context before the list. The inbox stays as Act first, reached from "View all".
- **A long narrative report**: a refined version of today's scroll. Rejected because it has no hierarchy at 300 Sites and buries the action.

---

## 10. Acceptance checklist and gates

A reviewer applies these to any screen. Each item is a question; "no" on a **must** item is High.

### 10.1 Questions

**Must:**
1. At 1280 × 720, can you say within 5 seconds what needs a decision and the money at stake, from L1 alone?
2. Does every figure show its comparison (target, no action or budget), or say why not?
3. Is there at most one primary action per region, and one per screen at L1?
4. Is each piece of content at its level (§2.3), with nothing from §2.2 on the first screen?
5. Does each figure carry at most one certainty marker, with the design's word in its accessible name and its drawer?
6. Is each caveat said once per scope?
7. Does the layout hold at 3, 30 and 300 Sites, with no list carried in prose and every list past 7 rows capped with "Show all"?
8. Are all sizes and colours tokens: no text under 12 px, no literal colour?
9. Do status colours mean only status, each with a word?
10. Does each chart match §5, state its answer in its title, never stack certainty classes, and offer a table view?
11. Is the person who decides shown where the decision happens, with no role switch?
12. Is there no page-level horizontal scroll at 390, and are the targets at least 24 px?
13. Is it complete by keyboard, with visible, unobscured focus and a correct heading order?
14. Are light and dark both legible: 4.5:1 for text, 3:1 for non-text?
15. Are the loading, empty, not-available and error states designed (§7.6)?

**Should:**

16. Do numbers follow §5.1?
17. Is the copy free of system words (§7.7)?
18. Does motion respect reduced motion?

### 10.2 Gates, in order

| Gate | What | Who | Pass |
|---|---|---|---|
| G1 Content | `vocab_check`, `plan_switch_check`, `render_text` and the existing mock checks, **unchanged** | Implementer runs, reviewer re-runs | 0 hits |
| G2 Design lint (new, static) | A script over the CSS and JS templates: font sizes only from the scale; none under 12 px; colours only via tokens outside the token blocks; no inline style colours; a planted violation proves it | Implementer | 0 hits, planted proof recorded |
| G3 Screenshots | Real headless Chromium (§10.3) at **1280 × 720, 1440 × 900 and 390 × 844**, each in **light and dark**: six full-page shots per changed screen, per operator; `measure_screen.cjs` metrics recorded for each; 0 page errors; page width equal to the viewport | Implementer captures, reviewer opens every shot | All six views captured and inspected; L1 at or above the fold; page errors 0; text under 12 px 0; caveat count at most 1 per scope |
| G4 Design-quality review | A **separate** fresh reviewer, who did not build the screen and did not do the content review, answers §10.1 from the G3 shots and the code, and names the three weakest points on each screen | Design reviewer | Every must item is yes; the verdict is recorded apart from the content review |
| G5 Owner look | The combined walkthrough (memory: walkthroughs at W1 end) | Owner | Owner acceptance |

### 10.3 The screenshot gate, concretely

A headless Chromium is installed with the owner's approval (`/opt/assetecon/tools/pw/`). Use it for every screen-affecting slice:

```
source /opt/assetecon/tools/pw/env.sh && export LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH
M=file://<worktree>/Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/index.html
for v in "1280 720" "1440 900" "390 844"; do
  node /opt/assetecon/tools/pw/shot.cjs "$M#/portfolio" out/portfolio-${v% *}.png $v
  node /opt/assetecon/tools/pw/shot.cjs "$M#/portfolio" out/portfolio-${v% *}-dark.png $v dark
  node Docs/design-system/tools/measure_screen.cjs "$M#/portfolio" $v          # light metrics
  node Docs/design-system/tools/measure_screen.cjs "$M#/portfolio" $v dark     # dark metrics
done
```

- `shot.cjs` takes the full-page shot and reports page errors.
- `measure_screen.cjs` prints, as one line of JSON:
  - page height and width;
  - the vertical position of each named section;
  - the rendered font sizes and the count under 12 px;
  - the visible chips;
  - the repeats of the design-estimate caveat;
  - an above-the-fold check for the first queue row.
- `tools/run-audit.sh --shots` works with `env.sh` sourced.
- Shots go to the slice's evidence folder, not to a commit, unless they illustrate a guide or spec.
- Mock review tooling is exempt from content rules. It is included in the shot, but it is not counted as page content.
- Baseline on 19 Nov (Lakeside Portfolio): 4,221 / 4,508 / 8,284 px tall; the queue at 3,677 / 3,964 / 6,946 px; 165 text elements under 12 px. The redesign's targets are the queue starting above the fold at 1440 × 900, and 0 text under 12 px.

**The design-quality review (G4)** is run by a fresh reviewer. It is a separate verdict from the content review. Its input is:
- the six shots;
- the metrics;
- this guide;
- the slice spec.

Its output is:
- a yes or no for each §10.1 item, with the shot that shows it;
- the three weakest points on each screen;
- a verdict, ACCEPT or REVISE.

Content checks (G1) stay as they are and are reported separately.

---

## 11. Proposals that need the owner

Each proposal changes how a design rule is presented, not the rule itself. The Architect's default applies unless the owner says otherwise.

| ID | Proposal | Why (objective) | Default |
|---|---|---|---|
| **U1** | **The scope's baseline class is stated once** ("Figures are simulated demo data unless marked"; with live data, "recorded unless marked"). Only figures that differ from it carry a marker, and every figure keeps its exact word in its accessible name and drawer. Rule 1 ("every figure states how it is known, in words") is met by the notice, the drawer and the legend, not by a chip on each line. | Today 41 chips on one screen, mostly "Emulated", bury the exceptions that matter (Modelled, Estimated, Not available yet). Marking the exceptions makes them visible. | **Adopt.** |
| **U2** | The caveat "Design estimate: not yet tested on your recorded data" is **one notice per page**, with a † on the affected figures. | It appears 17 times on the Kobo decision page. | **Adopt.** |
| **U3** | **Whole-currency and compact money at L1 and L2**; cents only in the bridge's table view and at L4. The rendered-text alignment checks compare at each figure's displayed precision. | Cents at a glance read as false precision and slow reading. | **Adopt**, with the check tolerance updated in the same slice. |
| **U4** | At phone width, a row of **more than 4 tabs becomes a "Section" menu button** (Carbon's tabs-to-dropdown pattern). Rows of 4 or fewer still wrap, as ruled. This replaces the post-W6 "wrap with complete labels" ruling only for rows of more than 4 tabs. | Six Portfolio tabs wrap to three rows at 390 and push L1 below the fold. | **Adopt** for vNEXT screens. |
| **U5** | The Overview's "Factors needing attention" becomes the **decision queue** (the same rows, plus at stake, due date and who decides). The four category cards become **tiles with counts**; their factor lists move into a category drawer. (MOCK DEVIATION D2) | P1 and P3: the queue is the decision; prose lists do not scale. | **Adopt.** |
| **U6** | Category headings carry **no colour of their own** (icon and name only), and violet leaves certainty. | Hue is reserved for status, so green, amber and red mean one thing. | **Adopt.** |
| **U7** (adopted 20 Nov; RULES §6 now cites this guide) | RULES §6 cites this guide beside the builder decision guide, and the G2 to G4 gates join the screen-slice review. | Makes the bar enforceable on every screen. | **Adopt** after the owner reads this guide (memory: align before doc revision). |

---

**Wave 2 proposals** (defaults apply unless the owner says otherwise):

| ID | Proposal | Why | Default |
|---|---|---|---|
| **U8** (settled 20 Nov: keep the six groups) | Merge the rail's six legacy groups into four (Portfolio, Sites; Work: Findings, Actions, Incidents, Maintenance, Records; Evidence; Financials, Settings) and drop the group labels. Every destination stays. | The rail is the most dated element left. The frame rule forbids new menus, not fewer labels. | **Keep the items and labels for now**; visual compaction only, until the owner agrees. |
| **U9** (adopted 20 Nov) | Load the July to September ledger history the scenario already declares, so the trend slot and "against September" become real. | Time context is standard in executive products. Today it is honestly "not available yet". | **Adopt**, in the data lane, not in this screen step. |
| **U10** (adopted 20 Nov) | East Africa as the starting pack for the three demo operators, which are East African. Neutral stays the product default. | It shows the configurability and suits the demo audience. | **Adopt** after the owner compares the two packs in the shots. |

## Appendix A. Applying the guide to the mock-up

1. **Slice UX-0, the foundation.**
   - Consolidate the type scale and colours into tokens across `mockups.css`, `portfolio.css`, `outcomes.css`, `economics.css` and `theme.css`. Today there are 52 sizes and about 190 literal colours.
   - Add `tools/design_lint.cjs` (G2).
   - Add the person chip, certainty marker, KPI tile, chart frame and drawer components.
   - This touches no content.
2. **Slice UX-1: Portfolio Overview and Act first**, as in §9, under U1 to U6.
3. **Slice UX-2: the Decision page**: the recommendation header, the options table (§7.2), and the L3 sections collapsed.
4. **Then Plan, Site, Findings and Financials**, one screen per slice. Each passes G1 to G4.

**Wave 2 queue** (from the wave-1 design reviews, 19 Nov; not done in wave 1):
- The Decision page is long: the options table starts below the fold. Move the comparison up, directly under the recommendation, and fold the explanation sections further.
- Content repeats across pages: the same issues appear on the Overview, Act first and the Site page, and the plan facts appear on the Overview, Act first and the plan. Give each page one job, and link instead of repeating.
- Act first lists the same issues as the Overview. Give it a reason to exist, for example grouping by urgency next to the plan.
- About 620 hard-coded colours remain in the earlier stylesheets, which theme.css re-points at tokens. Move them onto the tokens.
- The remaining screens (Outcomes by site, Demand and capacity, What changed, Scope, Financials, the other Site and Decision pages) still need the wave-1 treatment.
- The older v7.0 pages kept from the earlier mock-up still use system words ("Candidate avoidable", "Candidate runtime", "Factor"). The copy checks report them separately and do not fail on them; rewrite them in operator words.

Each slice is specified by the Architect before code, under the handshake rule (RULES §4). G3 runs on the installed headless Chromium (§10.3).

## Appendix A2. The history the trend slots read (U9, adopted)

The history comes from the data lane's deterministic generator, never typed by hand, and is evaluated by the same structure evaluator as October, so a trend figure is computed the way the October figure is.
- **Months:** 2026-07, 2026-08 and 2026-09 (October already exists). Monthly grain, with the right period days (31, 31, 30).
- **Operators and Sites:** all three demo operators and all nine Sites: Lakeside Power (Kobo, Kisiwa, Mto), Harvest Cold Network (Rooms A to C: Mwea, Thika, Kirinyaga) and Metro Bus Depots (Kasarani, Embakasi, Ruiru).
- **Input shape:** for each Site and month, a `period` block shaped exactly like October's in the demo scenario: `actual` and `plan` with the same leaf keys per vertical, plus `coverage` and `bridge`.
  - Mini-grid leaf keys: delivered, metered, loss, adjustment and billed kWh; revenue, collected, in transit, outstanding; diesel litres split into necessary, candidate and unexplained; diesel cost, O&M, staff.
  - Cold room leaf keys: crate-days, occupancy, revenue, collected, outstanding, model and metered kWh, energy, staff, maintenance.
  - EV depot leaf keys: the same leaves its October block has.
  - Proposed file: `history.json` beside the scenario, `{ "tenant": { "site": { "2026-07": { "plan": {…}, "actual": {…}, "coverage": {…}, "bridge": […] }, … } } }`.
- **Output the mock-up reads:** `DERIVED.history[tenant].portfolio[key] = [{ "m": "Jul", "v": … }, …]`, with keys `contribution` (or `cost` for the depot operator) and `gap`, written by the evaluator next to `derived-values.json`. Site series take the same shape under `sites[site]`.
- **Today's derivation cannot supply it.** `evaluate_structure.py` and `plan_model.py` evaluate October's records only. The scenario declares a four-month ledger span but carries no July to September values, so computing them now would mean inventing inputs. Until the file exists, every slot reads "Trend not available yet".

## Appendix B. Sources relied on

- WCAG 2.2: 1.4.1, 1.4.3, 1.4.10, 1.4.11, 2.4.11, 2.5.8 (w3.org/TR/WCAG22).
- NN/g, progressive disclosure, and the ten usability heuristics.
- IBM Carbon: data-table density, tabs on small screens, data-visualisation chart selection.
- Atlassian Design System: elevation and spacing tokens.
- Material 3: type scale roles, motion durations.
- Shopify Polaris: index-table and empty-state patterns.
- GOV.UK Design System: plain-language error and empty states.
- Stephen Few: bullet graphs.
