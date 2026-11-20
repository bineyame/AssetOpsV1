# IA-1 rulings: the app-wide menu, page organization and the shape rebuild

Architect (Claude), 2026-11-20. Each ruling gives its reason. D-IA.15 to D-IA.20 come from the handshake (round 1), D-IA.21 to
D-IA.30 from the IA-1b/IA-1c handshake. Index lines are in `.ai/decisions/index-rulings-8.md` (D-IA.1 to D-IA.14),
`index-rulings-9.md` (D-IA.15 to D-IA.20) and `index-rulings-10.md` (D-IA.21 to D-IA.30). Owner sources, verbatim:
- `owner/owner-app-wide-ia-proposal-2026-11-20.md` (the request);
- `owner/owner-ia-proposal-answers-2026-11-20.md` (the answers to Q1 to Q9);
- `owner/owner-ia-direction-approved-2026-11-20.md` (the approval and the two guardrails).

The proposal is `Docs/design-system/ia-proposal/index.html`. Handshake answers go at the end of this file, under
"Handshake answers (round 1)" and "IA-1b/IA-1c handshake answers".

**Scope (O1 boundary).** These rulings govern the Layer 4 destination: the vNEXT mock-up and the product screens
built from it. The live product on `main` (`frontend/src`) keeps its rail and Site tabs until a product slice
builds this structure.

## D-IA.1 The menu: six groups, thirteen items, in this order

- **Ruling.** The rail, top to bottom:

| Group | Items |
|---|---|
| Operations | Portfolio · Sites · Assets & cover |
| Intelligence | Findings |
| Work | Decisions · Plan · Actions · Incidents · Maintenance |
| Assurance | Results · Evidence & records |
| Business | Financials |
| Admin | Settings |

  The Simulator Lab is not a rail item (D-IA.7).
- **Why.**
  - The six groups and their order follow the operating loop the current menu was designed around, and the owner
    kept them (U8).
  - The owner put Decisions and Plan under Work, with the order Decisions, Plan, Actions, Incidents, Maintenance.
    The Architect agrees and does not push back. A decision is where a person commits; the system's own output, the
    Finding, stays in Intelligence. Work then reads decide, commit, do, fix, maintain.
  - Intelligence keeps one item. That is acceptable: Business and Admin also hold one item each, and the group label
    still says what kind of thing the item is.
- **Supersedes:**
  - the design's frame rule, "the rail with no new menu items" (`layer4-transformation-design.md` §2.8);
  - the guide's "the rail keeps every item (the frame rule)" and proposal U8's note (`uiux-guide.md` §8, §11).

  Both texts now point here.

## D-IA.2 Portfolio tabs: Overview, Outcomes, Demand & capacity

- **Ruling.** The Portfolio hub has three tabs. The other three are moved, not removed:

| Today | Moves to |
|---|---|
| Act first | Work › Decisions (the queue) and Work › Plan |
| What changed | Assurance › Results (verdicts), the "Waiting for you" inbox ("since you last looked") and Plan › Review |
| Scope & coverage | Assurance › Evidence & records › Coverage |

  "Outcomes by site" is renamed Outcomes: one row per Site, sorted by gap, capped at 10 with "Show all N".
- **Why.**
  - Act first repeated the Overview's queue.
  - What changed did not list changes.
  - Scope repeated the Evidence list.

  Each duplicate was a second rendering that could disagree with the first (UX audit C1, C2, C9).
- **Supersedes:**
  - the guide's "six Portfolio tabs" frame (`uiux-guide.md` header and §2.3);
  - the design's "the six Portfolio tabs" (§2.8).

## D-IA.3 Site tabs: six, the same on every vertical

- **Ruling.** Every Site has these six tabs: Overview · Operations · Performance · Financials · Evidence · Setup.
  - Health and Performance merge into Performance. Its panels follow the vertical, and its slots do not.
  - Foundation, readiness, changes and the single-line diagram become Setup.
  - The Findings and Work tabs become the Overview queue and the Operations tab.
- **Why.**
  - The same structure on every Site, as the owner asked on 20 Nov and in the range rule of 12 Nov.
  - Each tab is one aspect, never a second home for an object (D-IA.8).
- **Consistent with** design §2.10's Operations tab "between Overview and Financials". Nothing there is superseded.

## D-IA.4 Incidents and Maintenance stay two Work items, rebuilt on the operations data

- **Ruling.** Incidents and Maintenance stay separate items under Work, as they are today, and their content is
  rebuilt. Each item:
  - lists one row per Site at portfolio scope (counts, repeats, overdue), opening to its items;
  - shows the items themselves at Site scope;
  - opens each item in a drawer.

  Assets & cover holds the asset registry and its cover. Operational records move to Evidence & records.
- **Why.** This is the owner's option B (eight answers, item 1) and the owner's answer to Q4. Incidents and
  Maintenance answer different questions, and both read one store (work cases), so they cannot contradict each
  other.
- **Supersedes:** design §2.10, "The Portfolio's five earlier lists become one rail entry, Operations, with four
  views". The rest of §2.10's model stands: the asset as anchor, rights, repeats, cost basis and the Site Operations
  tab.

## D-IA.5 Assurance: Results, and Evidence & records

- **Ruling.**
  - **Results** lists, by period, the operational, economic and causal verdicts and the plan's review against what
    was observed. Each row opens the Action's Verification tab or the Plan's Review tab.
  - **Evidence & records** has three tabs: Coverage (from the Portfolio's Scope tab and the old Evidence list),
    Records (from Operational records) and Imports (imported records waiting for acceptance, §2.3). Each record opens
    in a drawer.
- **Why.** Owner Q5 and Q6. Assure (A1, A3, A4) gets a home.
- **Supersedes:** design §2.10's "Evidence's coverage view is the Portfolio's Scope tab".

## D-IA.6 One scope switch: all Sites, a group of Sites, or one Site

- **Ruling.**
  - The top bar holds one scope switch. It replaces the second Site select the mock-up has today (audit C9.4).
  - Every home list obeys the scope, and the address keeps it as `?scope=all|group:<id>|site:<key>`.
  - Choosing one Site from a hub opens that Site's page.
  - Groups are defined in Settings. The demo defines one group per vertical in each operator.
- **Why.** Owner Q7. At 300 Sites even a capped list is too long. Scope is never a role switch (owner, 17 Nov).

## D-IA.7 The Simulator Lab: developer role only

- **Ruling.**
  - The Lab is reachable only by a person who holds the **developer** grant. It is not a rail item for any other
    person.
  - With the grant, it appears in a workspace footer under the rail and opens its own shell, as the live product's
    `WorkspaceShellLayout` already keeps it.
  - The developer grant is a technical access grant beside the five business roles (design §2.6). It is not a role
    view, so "every role sees the same screens" still holds for the business roles.
  - In the mock-up, a review-bar switch "Developer access" stands in for the grant. The switch is off by default and
    is mock-only chrome.
- **Why.**
  - Owner Q8: "accessible only for advanced user (dev)".
  - The gate is by person, not by build, so a pilot build can still give an engineer the Lab.

## D-IA.8 One object, one home, many scopes

- **Ruling.**
  - Each object has exactly one home list and one page or drawer, drawn by one component that reads one store.
  - A hub queue, a Site tab or another page shows that component scoped: its top 3 rows and "View all", which opens
    the home list with the scope kept.
  - The Site's Financials tab is the Financials page at Site scope. The Site's Evidence tab is Evidence & records at
    Site scope. The Site's Operations tab composes the Incidents, Maintenance and Assets & cover lists at Site scope.
- **Why.** Cause A in the proposal. One store and one renderer remove the class behind audit C1, C2 and C3: two
  screens cannot disagree when there is only one.

## D-IA.9 Page or drawer, and one drill-down grammar

- **Ruling.**
  - **Page or drawer.**
    - A page: Portfolio, Site, Decision, Plan, Finding, Action and Asset.
    - A drawer: Incident, Maintenance, Right, Record, a figure's evidence and the inbox.
    - The rule: a page when people work through it over days, with a state, an owner and a history. A drawer when it
      is read beside its parent and acted on in one step.
    - Every drawer has an address (`?drawer=<kind>:<id>`), and Esc closes it.
  - **Drill-down.**
    - A row opens its object.
    - A figure opens its evidence drawer.
    - "View all" opens the home list.
    - A row has one target and holds no other control.
  - **Wayfinding.**
    - The breadcrumb is home list › Site › object.
    - The rail highlights the owning item, so a Decision lights Decisions.
    - The H1 and the document title name the view.
    - Tabs, filters and drawers live in the address.
  - **Acts.** The one feedback pattern built on `task/uiux-design-model`, `37507a194`: a dialog, then a toast with
    Undo, then the state changes on the page and in History. A state is never shown as a button.
- **Why.** The owner's standing brief asks why one thing is a panel, one a page and one brought up. One rule answers
  that for every object.

## D-IA.10 Guardrail G1: every executive journey within 3 clicks of the Portfolio

- **Ruling.**
  - **Click depth** is the number of navigations from `#/portfolio`, the Overview, for the active operator. A
    navigation is a link, a tab, a row or a tile that changes the route or opens a drawer. Pressing an action button
    and confirming its dialog are the act itself, so they are not counted.
  - **The answer surfaces and their limits,** for every demo operator:

| Journey | Answer surface | Max depth |
|---|---|---|
| What needs me | Every decision waiting for a choice and every plan waiting for approval (its Decision page or Plan page) | 1 from the Overview queue or plan tile; 2 through the inbox |
| Why is this Site off target | Every Site's Overview (its drivers against target) | 2 |
| | The Finding on that Site's largest adverse driver | 3 |
| Approve the plan | The Plan page | 1 |
| | Each item's Decision | 2 |
| | The released Actions, filtered to the plan version | 2 |

  - Evidence past the answer (drawers, the Asset page, records) may sit deeper.
  - The check `tools/click_depth_check.cjs` computes the shortest depth by walking the rendered links breadth-first.
    It fails past these limits, and it must fail when the plan tile's link is removed (plant `G1_PLANT=1`).
    How depth is measured (content edges, per entry) and the plants: D-IA.18.
- **Why.** Owner guardrail G1, approved on 20 Nov.

## D-IA.11 Guardrail G2: stop after the hub and decision shapes

- **Ruling.**
  - After units IA-1a, IA-1b and IA-1c merge to the mock-up branch, building stops.
  - The coordinator gives the owner screens of the hub and the decision, at 1440 and 390 and for all three operators,
    and asks for input.
  - IA-2 starts only after the owner's reply is saved verbatim in `owner/`. New input from the owner goes into IA-2's
    spec before it starts.
- **Why.** Owner guardrail G2.

## D-IA.12 Build by shape, in the order of the journeys

- **Ruling.**
  - Each unit builds one shape once and renders every object of its type in that unit's scope.
  - Its gate:
    1. every route of that type renders from the shape;
    2. no stub is reachable;
    3. the G1 check passes;
    4. the gates already earned pass (D-IA.14).
  - The order:

| Unit | Shape | Scope |
|---|---|---|
| IA-1a | Frame and gates | The menu, the top bar, the route and shape registry, aliases for old routes, the Lab gate (D-IA.19), and the G1, shape and after-render checks; the reviewed plan page as one named interim, so that IA-1b's plan tile has a live target (spec §2.6, D-IA.15) |
| IA-1b | Hub | Portfolio's three tabs; the Overview of all 9 Sites |
| IA-1c | Decision | Every decision (15 today; P12, D-IA.26); the inbox drawer |
| G2 stop | | The owner's input |
| IA-2a | Plan | The plan page per operator |
| IA-2b | List | Decisions, Findings, Actions and Sites |
| IA-2c | Asset | The Asset page; the lists for Assets & cover, Incidents and Maintenance; Site Operations, Performance and Setup |
| IA-2d | Drawers and record page | The Incident, Maintenance, Right, Record and figure-evidence drawers; the Finding and Action pages; the Results and Evidence & records lists; Site Evidence |
| IA-2e | Statement | Financials and Site Financials; Settings; the final route sweep (the Lab gate moved to IA-1a, D-IA.19) |

  - **A menu item or Site tab appears only when its unit has landed.** This is the current rail's own rule: a
    destination appears only when a real page stands behind it. Until then the review bar lists what is still to
    come, and no route renders a placeholder.
- **Why.**
  - The owner's Q9, and the order the coordinator relayed.
  - The journeys need the hub, the decision and the plan first.
  - IA-1 has 3 units and IA-2 has 5, so neither slice passes the 6-unit cap.

## D-IA.13 The rebuild starts from the reviewed UI branch; no patching after render

- **Ruling.**
  - **Starting point.** IA-1a branches from `task/uiux-design-model` at the head where its review is accepted. Code
    that passed review is reused as a function inside a shape: `uxKpi`, `uxQueue`, `uxBridge`, `uxDrawer`, the
    answer-titled section, the feedback pattern, and the Site and decision page sections.
  - **No patching after render.** A shape builds its markup in a detached fragment. One finishing step runs today's
    global passes on that fragment before it is inserted: plain words, the design-value tag, unit and sign tidying,
    and the scope line. The canvas is then replaced once.
    - After insertion, nothing rewrites the canvas's text or structure: no word-replacement pass, no injected top
      bar or chrome, and no re-based v7.0 screen under a new label.
    - The global passes are rules that apply to every screen alike, not fixes for one instance. Moving them into
      components later is allowed but not required.
  - **What stays out.** The v7.0 re-base (`tools/rebase_v70.py` and the `screens.js` renderers) no longer renders
    any routed screen. Retired and merged routes resolve through an alias, or to the not-found page.
  - **The check.** `tools/after_render_check.cjs` (jsdom) watches every shape route with a MutationObserver from
    the moment the shape's renderer returns until idle. It fails on any text or child-list change inside `#app` that
    no user event caused. Plant: `AR_PLANT=1` re-enables `PLAIN_WORDS` after render, and the check must fail. Corrected by D-IA.17: that plant was a no-op, and
    the observed root is the frame, not `#app`.
- **Why.**
  - Owner, 20 Nov: patching after render is the fundamental issue.
  - `loop-core.js` today rewrites words after render (`PLAIN_WORDS`), tags figures after render (`tagReplay`) and
    injects the top bar after render (`loop-ux.js:471`).

## D-IA.14 The gates already earned stay

- **Ruling.** Every IA unit keeps these passing, unchanged or tightened:
  - **Answer-titled sections, one level** (`ux_interaction_check.cjs`).
  - **One source per figure:** `hand_typed_scan.py` finds no hand-typed figure, and every figure reads `DERIVED` or
    the manifest.
  - **Reconciliation:** the statement and the headings tie, with the labelled "of which unbilled energy" line.
    `check_manifest.py` `reconciliation()` and the cross-page figure check pass.
  - **Honesty:**
    - every figure carries its evidence type;
    - "Not available yet" is shown only where a source is missing;
    - there is one design-value tag per container;
    - `vocab_check.cjs`, `copy_check.cjs` and `render_text.cjs` pass.
  - **One shell:** `shell_check.cjs` passes, with no other operator's Site on any route.
  - **No patching after render** (D-IA.13).
  - **G1** (D-IA.10).
  - **The design lint:** `design_lint.cjs`, gate G2 of the guide.

  A gate that a unit replaces is shown to fail on a planted violation before the old one is removed.
- **Why.** The coordinator's instruction, and W6: fix classes, and keep the checks that can fail.

## D-IA.15 IA-1a's gates start at the plan; the Portfolio item lands with the hub

- **Ruling.** `iaStart()` is `plan` until IA-1b lands, then `portfolio`. The Portfolio rail item's unit is IA-1b.
  In IA-1a the live surfaces are `plan` and the typed `not-found`; G1 has no live surface, and its engine self-test
  stands in until IA-1b.
- **Why.** R1. A gate that starts on a legacy screen fails by construction, and a rail link to the legacy Overview
  breaks §7. D-IA.12's "G1 holds from the start" was wrong: G1's origin is the Overview.

## D-IA.16 One liveness rule, applied before insertion; the crawl judges hrefs on its own

- **Ruling.** `iaLive(href)` decides whether a target is live (a landed `IA_ROUTES` entry, a live alias, or `lab`
  under the developer switch). `iaUnlink` applies it to the whole frame before insertion, and rewrites live aliases
  to canonical hrefs. The palette uses the same predicate. The crawl classifies hrefs with its own code and fails on
  any non-live, alias, stub, legacy or not-found target.
- **Why.** R2, R5, R9. One mechanism for one class (W6); a second, independent judge so the mechanism's own fault
  cannot pass its gate.

## D-IA.17 The after-render check watches the frame from the insertion hook

- **Ruling.** The observer attaches through `window.__iaInserted(root)`, called straight after the one insertion,
  on `#ia-root`. No event is dispatched; any mutation before idle fails except `is-on` on `[data-ux-sticky]` and
  `scrolls` on `.scroll-region`. Plants: `text`, `attr`, `late`.
- **Why.** R3, R14. D-IA.13's plant (running plain words again) was a no-op, and an observer on `#app` fails on the
  review bar. This corrects D-IA.13's check paragraph; the rest of D-IA.13 stands.

## D-IA.18 G1 is measured over content edges, per entry

- **Ruling.** Click depth counts content edges only (header tabs, `[data-level]` regions, the inbox control and
  rows). "What needs me" is measured per entry: depth 1 over queue edges for what the queue shows, depth 2 or less
  over inbox edges for every waiting decision and a proposed plan.
- **Why.** R4. The rail gives every page depth 1, so a whole-graph walk can never fail. This clarifies D-IA.10's
  measurement; its table and limits stand.

## D-IA.19 The Lab gate lands in IA-1a

- **Ruling.** The developer switch, the footer item, the not-found resolution of Lab screens with the switch off,
  and the review select's omission are built in IA-1a and asserted by shape_check. IA-2e keeps only the Lab's own
  content, if any changes.
- **Why.** R6. IA-1a builds the footer, so it must build the gate the footer stands behind; a gate built later
  leaves P8 untested for four units.

## D-IA.20 The plan interim is split into slots without changing its output

- **Ruling.** `planParts(op)` returns `{sticky, band, l2, l3, aside}` and `planScreen()` joins them byte for byte as
  today. The interim marks L1, L2 and L3 as listed under P4 above. The sticky bar may repeat the L1 primary.
- **Why.** P4. Wrapping the whole string breaks the two-column layout, and a split proven byte-identical is the
  smallest edit to reviewed code that lets the shape gate pass honestly.

## Handshake answers (round 1)

Answered once, 2026-11-20, against `task/uiux-design-model` as read at `786e1f905` (the pre-flight read, not the
base: the base is that branch's accepted head, named in spec §0 when its review is accepted). Folded into `spec.md`
rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the writer's expected answer is the ruling. Six new rulings
(D-IA.15 to D-IA.20) carry the answers that correct or clarify D-IA.10, D-IA.12 and D-IA.13.

**The test every answer was held to.** Each gate fails on a named plant that reaches the code the gate guards.
A plant that the code under test already neutralises (R3, R4, R5) is not a plant. Every plant is run by one runner,
`tools/ia_gates.cjs`, which fails if any plant passes.

### The Highs

- **R1: adopted, with the Portfolio item moved to IA-1b** (D-IA.15).
  - The crawl starts at `iaStart()`: `plan` while IA-1b has not landed, `portfolio` from IA-1b.
  - The Portfolio rail item's unit becomes IA-1b. In IA-1a it is an unavailable root, never a link to the legacy
    Overview: §7 forbids any live IA route linking a legacy screen.
  - The plan's breadcrumb is `Plan` alone. Every other unlanded target on the plan (the scope menu's Sites, the
    plan's `decision/*` and `site/*` links) is unlinked before insertion by the one liveness pass (R2).
  - What IA-1a must pass, live: shape_check items 1 to 5 (on `plan` and the typed `not-found`); the after-render
    check on `plan` and `not-found`; the click-depth engine self-test. What is built but has no live surface until
    IA-1b: the G1 table (its origin, the Portfolio Overview, lands in IA-1b). The packet says so in one line.
  - Pushback recorded: D-IA.12 said the plan interim makes "G1 hold from the start". It cannot be measured before
    the Portfolio exists. The interim is still right: IA-1b's plan tile needs a live target.
- **R2: adopted, candidate 1** (D-IA.16).
  - One predicate, `iaLive(href)` in `ia-routes.js`, and one pass, `iaUnlink(fragment)`, run first in `iaFinish`,
    before insertion. It applies to the whole frame (rail, top bar, breadcrumb, body).
  - A link to a non-live target becomes `<span class="ia-unlinked">` with its inner markup and a trailing arrow
    dropped (today's `uxShell` rule, moved before insertion). A tab link to a non-live target is removed.
  - A link to a live alias is rewritten to its target's canonical href by the same pass. The crawl then fails on
    any alias href it meets: one object, one address.
  - Why not `iaLink`: every reused function (`planScreen`, `decisionScreen`, `uxOverview`) would have to change its
    calls, which edits reviewed code, and a missed call is invisible. One pass is the class fix (W6). It runs before
    insertion, so it is a finishing pass, not patching after render (D-IA.13).
  - The reviewer guide's "fixed at the link, never by an alias" now reads: never by an alias pointing back to a
    legacy screen; a link to an unlanded IA route is unlinked by `iaUnlink` until its unit lands.
- **R3: adopted** (D-IA.17, which corrects D-IA.13's plant wording).
  - Hook: `iaRender` calls `window.__iaInserted?.(root)` synchronously, straight after the one insertion and
    before `iaBind`. The check sets the hook in `beforeParse`.
  - Observed root: the frame root `#ia-root` (R8), not `#app`. The review bar is mock tooling outside the frame.
  - Plants (each must fail):
    - `AR_PLANT=text`: the host route's markup gains `<p data-ar-plant>the evaluator</p>`; `iaFinish` skips
      `plainWords`; `iaRender` runs `plainWords(root)` in a `setTimeout(0)` after insertion. The plant itself throws
      "plant did not bite" if the planted node's text did not change.
    - `AR_PLANT=attr`: after insertion, a `setTimeout(0)` sets `data-ar-plant` on the first `div` in the body.
    - `AR_PLANT=late`: after insertion, a `setTimeout(250)` appends a text node to the H1 (inside the idle window).
  - Host route: `plan` in IA-1a; every live route from IA-1b (the plant hooks `iaRender`, not one route).
- **R4: adopted, both halves** (D-IA.18, which clarifies D-IA.10).
  - Depth is measured over **content edges** only: links, rows, tiles and tabs inside the frame's header tabs and
    `[data-level]` regions, plus the "Waiting for you" control and its drawer rows. The rail, the breadcrumb, the
    scope menu and search are excluded: they reach every page at depth 1 and would satisfy G1 by construction.
  - Path-specific limits are measured per entry. "What needs me": every decision the Overview queue shows is at
    depth 1 over queue edges; every decision waiting for a choice and a plan in PROPOSED is at depth 2 or less over
    inbox edges only (Overview → control → row). The other limits use the whole content graph.
  - Plants: `G1_PLANT=engine` (every unit) corrupts the self-test graph (one edge removed) and must fail;
    `G1_PLANT=tile` (from IA-1b) removes the Overview's plan tile link, and with the rail excluded the plan falls
    past depth 1, so it must fail; `G1_PLANT=inbox` (from IA-1c) drops one waiting decision from the inbox rows and
    must fail.
  - IA-1a's G1 table: no live surface (R1). The engine self-test runs and prints its expected table.
- **R5: adopted** (D-IA.16).
  - The crawl classifies each link by its href, never by the screen rendered. The classifier lives in
    `tools/ia_crawl.cjs` and reads `IA_ROUTES`, `IA_LANDED` and `IA_ALIASES` from the window, with its own matching
    code; it never calls `iaLive`, so a fault in `iaLive` cannot hide itself.
  - A link to `not-found`, a stub, a legacy route, an unlanded route or an alias fails. Not-found is reached only by
    a typed hash, which the check visits separately.
  - Plants: `SHAPE_PLANT=unlink` makes `iaUnlink` the identity on the host route (the plan's `decision/*` links
    survive; must fail); `SHAPE_PLANT=stub` makes `iaLive` return true for `site/kisiwa/health` and adds that link
    to the host's L2 (survives the pass; the classifier must still fail it). Host: `plan` in IA-1a, `portfolio`
    from IA-1b.
- **R6: adopted; the gate lands in IA-1a** (D-IA.19, which amends D-IA.12's IA-2e row).
  - `iaDev()` reads `sessionStorage['l4-dev'] === '1'`. With it off, `resolveScreen` turns every screen whose
    `root` is "Simulator Lab" into `not-found`, and the review-bar select omits them.
  - The footer item targets `lab`. `lab` is the one shell exit: `iaLive('lab')` is `iaDev()`. The crawl skips
    `[data-ia-footer]` (the Lab is its own shell, D-IA.7, and is not a product journey).
  - shape_check item 5 asserts: off, no `[data-ia-footer]`, no `a[href^="#/lab"]` in `#app`, no select option for a
    Lab screen, and `#/lab` resolves to `not-found`; on, the footer reads "Workspace" › "Simulator Lab" with
    `href="#/lab"`, and `#/lab` resolves to `lab`. Plant `SHAPE_PLANT=lab`: `iaDev()` returns true always; must fail.
- **P4: adopted, with a behaviour-preserving split** (D-IA.20).
  - `planScreen` is split into `planParts(op)` returning `{sticky, band, l2, l3, aside}`; `planScreen()` joins them
    into exactly today's string. Proof in the packet: for each operator and each switch case,
    `planScreen()` before and after are byte-identical (a node script, output cited).
  - The interim's markup: sticky, then `<div data-level="L1">` band, then `.layout-main-side` holding
    `<div><div data-level="L2">…</div><div data-level="L3">…</div></div>` and `<aside class="side-panel"
    data-level="L3">`. The two-column layout keeps its two children.
  - Levels: L1 the band (state, KPIs, approve). L2 the items, their total and "How the plan is chosen". L3:
    `uxPlanDiff`, "Two ways to restore Mto's inverter", the crew visits and "Listed beside the plan", "Left out",
    "All four cases", "Actions that return to their creator", and the aside (approval panel, "Try another case").
  - The sticky bar is kept (reviewed UX) and sits outside every level. The primary rule becomes: at most one
    `button.primary` per `[data-level]` region; a `button.primary` outside every region fails unless it is inside
    `[data-ux-sticky]` and has the same `data-act` as the L1 primary. Plant `SHAPE_PLANT=primary` adds a second
    primary to the host's L1; must fail.
  - The level sequence rule becomes: the `data-level` values in document order never decrease.

### Mediums and Lows

- **R7: adopted.** Scope and drawer sit in the hash: `#/route?scope=…&drawer=…`. `iaParse(hash)` returns
  `{path, params, query}`; `resolveScreen` and `currentScreen` see the path only. A route's identity in the crawl is
  the path plus its query keys, sorted. `?state=` stays in `location.search` (mock tooling, unchanged).
- **R8: adopted.** For an IA route, `render()` writes the review bar and `<div id="ia-root"></div>` only. `iaRender`
  builds the frame with root `<div class="shell ia-frame" id="ia-root">` (keeping today's
  `.shell > rail + main.workspace > header.topbar + .canvas` structure, so existing selectors hold) and replaces the
  placeholder once.
- **R9: adopted.** On an IA route the palette lists only `uxCommands()` entries whose target `iaLive` accepts (in
  IA-1a: Plan). shape_check opens it once per operator (`uxPalette(true)`), adds its `[data-go]` targets to the
  crawl as start-route edges, and closes it. G1 excludes search. Plant `SHAPE_PLANT=palette` turns the filter off;
  must fail.
- **R10: adopted.** `tools/ia_gates.cjs` (jsdom, no browser) runs the three checks, then each plant of each landed
  unit as its own process, and exits non-zero if a check fails or a plant passes. `run-audit.sh` calls it before its
  `CHROME` guard, so an unset `CHROME` cannot skip it. The packet cites the runner's output.
- **R11: adopted.** Keys are `lakeside`, `harvest`, `metro` (`LS.op`); the output prints `OPS[op].name`.
- **R12: adopted.** `:site` over `OPS[op].sites`; `:dec` over the `DEC` entries of those Sites only.
- **R13: adopted.** Group id is the vertical key (`mini`, `cold`, `ev`), as `?scope=group:mini`. On a non-hub page
  the choice is kept in the address only and changes nothing on the page. Rail and content links do not carry the
  scope; only "View all" carries it (D-IA.8).
- **R14: the clause is dropped.** The check dispatches no event. Any mutation in the frame between insertion and
  idle fails, except the two named layout-caused class changes (P5, P11): the token `is-on` on `[data-ux-sticky]`
  and the token `scrolls` on `.scroll-region`. The check diffs `classList` old against new, so any other class
  change on those elements still fails.
- **R15: adopted.** Top bar, left to right: scope, search, period chip, (Waiting for you from IA-1c), theme toggle,
  avatar (today's order for the last two). The search button's text, "Search Sites, decisions and Findings", is in
  the frame markup; `uxSearchLabel` is not called for IA routes.
- **P1: adopted.** The spec cites functions by name. Spec §0 holds the base line, which the coordinator fills with
  the accepted head's SHA when `task/uiux-design-model`'s review is accepted; no IA-1a code starts before.
- **P2: adopted, and today's order kept.** `uxScopeLine(root, screen)`; the legacy call passes the canvas and
  `currentScreen()`; the pending chip is read from `root`'s own top bar. `iaFinish` runs, in order: `iaUnlink`,
  `uxCapLists`, `tagReplay`, `uxScopeLine`, `plainWords`, `uxDedupeUnits`, `uxFixSigns` (today's order, because the
  scope line reads record keys before plain words replaces them). `render_text` differences, if any, are listed in
  the packet.
- **P3: adopted, option 1.** String builders shared by the legacy path and the frame: `uxScopeSwitchHtml(entries,
  label)` (the `details.ux-pop.ux-scope-sw` markup), `uxPeriodMenuHtml(op)` (the period `details` around
  `periodChip`), and `uxReviewExtrasHtml(hash)` (brand select, D2 and D5 marks, decision marks, the "Developer
  access" switch and "Still to be rebuilt"). `render()` writes the review bar with `uxReviewExtrasHtml` for every
  route, and `uxBrandSwitch` is removed. The D5 test also matches `#/plan`.
- **P5: adopted.** `uxCapLists` moves into `iaFinish`; the unlinking is `iaUnlink`; `iaBind` schedules
  `uxStickyTick`, and its `is-on` toggle is the allowed layout change (R14).
- **P6: adopted.** Retargeting a check's boot route from `portfolio/act-first/plan` to `plan` is not a change to the
  check. Replacing an assertion on legacy chrome with the frame's equivalent is, and is shown failing on a plant
  first.
- **P7: adopted for the new checks.** `tools/ia_crawl.cjs` holds the jsdom boot, the crawl and the href classifier,
  used by shape_check, click_depth_check and after_render_check. `shell_check.cjs` moves onto it in IA-1b, when its
  start route is live, with `SHELL_PLANT=1` shown failing first.
- **P8: adopted.** `IA_ALIASES` is resolved first and only when its target is live; otherwise `ALIAS` applies; no
  chaining. A value may be a function of the parameters (`recommendation` → `p => 'decision/' + …`).
- **P9: adopted.** `not-found` is in `IA_ROUTES`: shape `frame`, unit IA-1a, `home: null`, `noFigures: true`, crumbs
  `[['Page not found']]`, body from `uxNotFound`. Its Portfolio link is unlinked by `iaUnlink` until IA-1b.
- **P10: adopted.** `ia.css` goes between `ux.css` and `brand.css`.
- **P11: adopted.** The `scrolls` mark stays in `brandAndListenersOnly` and is the second allowed layout change.

## IA-1b/IA-1c handshake answers

This file is now at the 15k-token cap: later answers go to `rulings-2.md` (RULES §9).

Answered once, 2026-11-20, against `main` at `e100640bf` (IA-1a merged) and `vNEXT/` as read there. Folded into `spec.md`
rev 3 and `reviewer-guide.md` rev 3. Ten new rulings, D-IA.21 to D-IA.30, carry the answers; each names the question
class it closes and the sweep. The governing reference for every screen below is the reviewed vNEXT page the unit
reuses (`uxOverview`, `uxSitePage`, `uxDecisionPage`, `opportunityScreen`, `uxChain`, `uxInsight`); its content carries
over, and only its placement in levels is the shape's (dispatch, 20 Nov). Where this departs from spec rev 2, the
spec described a page that does not exist and the reviewed page wins.

**The test every answer was held to** (unchanged from round 1): each gate fails on a named plant that reaches the code
it guards, and `tools/ia_gates.cjs` (or, for a browser check, its own runner) fails if any plant passes.

### D-IA.21 Drawers in IA-1 open in place; G1 counts the opener; every drawer address lands in IA-2d

- **Ruling.**
  - In IA-1 every drawer keeps the reviewed pattern: a `[data-ux-drawer]` button opens it in place (`uxOpen`), Esc
    and the close button shut it. No drawer has an address in IA-1, the inbox included.
  - **G1's graph** (click_depth_check) has two kinds of node: a page (its route) and a drawer (`<route>#drawer=<element
    id>`). A page's edges are the `a[href^="#/"]` and `[data-ux-drawer]` openers inside its header tabs, its
    `[data-level]` regions and the inbox control, **never inside any `.ux-drawer`**. An opener is an edge to the drawer
    node it names. A drawer node's edges are the links and openers inside that drawer element only.
  - `identity()` in `ia_crawl.cjs` keeps the value of `drawer` (other query keys stay key-only), so two drawers on one
    page are two nodes when addresses arrive.
  - **IA-2d** gives every drawer its address (`?drawer=<kind>:<id>`, stable ids), Back restoring it, and moves G1's
    drawer nodes onto those hrefs. P5's "Back restores an open drawer" moves there.
- **Why.** R16, R28. Addressing the inbox alone in IA-1c would build a second drawer mechanism beside the one IA-2d
  builds for all drawers (W6: one mechanism per class). Counting an opener as an edge measures exactly the click
  D-IA.10 counts ("opens a drawer"); excluding links inside drawers stops hidden content from lowering depths.
- **Amends** spec rev 2 §4.3 (the inbox address) and the timing of D-IA.9's drawer address (its rule stands).
- **Plants.** `G1_PLANT=driver` strips `data-ux-drawer` from the Site board's driver openers (the driver surfaces
  become unreached; must fail). The edge reader gets its own self-test: a fixed DOM fixture (a level region with a
  link A and an opener to drawer D; inside the closed D, a link B) must read as page → A, page → D and D → B, never
  page → B. `G1_PLANT=hidden` removes the reader's `.ux-drawer` exclusion, and the fixture test must fail. (A plant on
  the live Overview cannot do this job: the plan and the Sites stay reachable through other live links.)

### D-IA.22 A reused page is split into parts proven byte-identical; the shape places the parts

- **Ruling.**
  - `uxOverview`, `uxSitePage` and `uxDecisionPage` each get a parts function, like `planParts` (D-IA.20):
    `uxOverviewParts(op)`, `uxSiteParts(sk, P, qMax)`, `uxDecisionSlots(id, parts)`. The legacy function joins its
    parts into exactly today's string. `siteOverview(sk)` and `decisionScreen(id)` keep their output; their part
    builders are extracted as `siteOverviewP(sk)` (the `P` object) and `decisionParts(id)`.
  - **Proof:** a node script compares the legacy function before and after the split, byte for byte, for every
    operator, every Site and every decision, in the default state and under `?state=no-recommendation`, with
    `UX_QN` reset to 0 before each call. The packet cites the counts.
  - **Levels and drawers.** `iaLevels(shape, { cls, sticky, l1, l2, l3, drawers })` (used by `shapeHub` and
    `shapeDecision`) returns `<section data-shape="<shape>" class="<cls>">{sticky}<div data-level="L1">…</div>
    <div data-level="L2">…</div><div data-level="L3">…</div><div data-ia-drawers>…</div></section>`, omitting an
    empty region. Drawers the reused function emits at the page's top level go in `[data-ia-drawers]`; a drawer
    nested inside a section stays where the section puts it. In `ia.css`, `[data-shape="hub"] > [data-level],
    [data-shape="decision"] > [data-level], [data-ia-drawers] { display: contents }`, so the reviewed layout is
    unchanged to the pixel and the levels are structure only.
  - **Top 3 at Site scope** (P17): `uxSiteParts(sk, P, qMax)` passes the queue the rows of its first `qMax` merged
    decisions, as `uxOverview` does for 6; `uxSitePage` calls it with `Infinity`, the hub with 3.
  - **One named fix in the split** (R20 class, below): the Site sticky's "Decide" targets the queue's own primary
    (the first `choose` decision among the rows shown), not `waiting[0]`; with none, the sticky has no "Decide". The
    byte-identity proof runs before this edit; the packet shows the one diff (it appears only when a `none` decision
    or a hidden row leads, never in the default data).
- **Why.** P14, P17, R20, R26. A wrapper around one string cannot place parts in levels; editing reviewed functions
  without proof re-opens their review. `display: contents` keeps the screens the owner reviewed identical while the
  gates read the structure.

### D-IA.23 One primary rule: any `.primary`, one act identity, drawers excluded

- **Ruling.** shape_check item 1's primary rule becomes:
  - a primary is any `a.primary` or `button.primary`; one inside a `.ux-drawer` belongs to its dialog and is skipped;
  - its **act** is `data-act`, else `data-ux-act`, else `drawer:<data-ux-drawer>`, else `href:<href>`; a primary
    with none of these fails;
  - at most one primary per `[data-level]` region;
  - the **page primary** is the first primary inside a level region, in document order;
  - a primary outside every region must sit in `[data-ux-sticky]` and have the page primary's act.
- **Plants** (each must fail): `primary` now adds **two** `button.primary` with distinct acts to the host's L1 (the hub
  has no L1 primary, so one would not bite); `noact` removes the act of the host's page primary (for a link, its
  `href`); `linkprimary` adds two `a.button.primary` with distinct hrefs to the host's L2;
  `decprimary` (IA-1c, host: the operator's first waiting decision; an operator without one, Harvest, skips the
  plant) adds a second "Choose this" opener to its L1; `stickyact` (IA-1c, same host) points the sticky's opener at
  another option's dialog.
- **Hosts.** `primary`, `unlink`, `stub`, `selflink` and `linkprimary` run on `iaStart()`; `noact` on `plan` (in
  IA-1b the Overview's "Decide" links are unlinked until decisions land, so its page has no primary to strip).
- **Why.** R20, R27. The reviewed pages' primaries are link-styled (`Decide`) or openers (`Choose this`); a rule that
  reads `button[data-act]` only fails them by construction or misses them. The confirm buttons belong to their
  dialogs, as the one feedback pattern defines.

### D-IA.24 One decision set, one waiting predicate; Choose changes the state, the row stays; the badge is "For you"

- **Ruling.**
  - **The set.** `iaDecIds(op, scope)`: the decision ids of `ATTN[op]` (`r[4]`), first appearance first, filtered
    by scope (Site: `r[2]`; group: `iaVertical(r[2])`). It is the set every "Decisions" count already counts
    (`uxDecCount`).
  - **The predicate.** `iaWaiting(id)` is `['choose', 'none'].includes(uxDecState(id).key)`: a decision with
    nothing recommended still waits for a choice ("can still choose one, or none"), and `uxStateCount` already counts
    the two together. Every "waiting" figure is `iaDecIds` filtered by `iaWaiting`: the Overview and Site splits
    (through `uxStateCount`, unchanged), Outcomes column 6, the Site sticky's pill, both inbox sections, the badge
    and G1's "every decision waiting for a choice".
  - **Choose** changes the decision's state on the page, in its queue row and in every count; the row stays in the
    queue (the queue lists every open decision with its state, as reviewed). Undo restores all.
  - **The inbox's sections:** "For you" holds the plan when `uxPlanState(op).state === 'PROPOSED'`, then every
    waiting decision whose chooser (`HC.decisions[].chooser`) is `OPERATOR_EXECUTIVE`; "In your portfolio" holds
    every other waiting decision. **The badge** is the count of "For you" (0: no badge). On the demo data: Lakeside
    and Harvest 1 (the plan), Metro 2 (the plan and the Ruiru expansion).
  - **Since you last looked** reads a new act log: `uxActDo` appends `{ key, op, by, at, toast }` to
    `uxMock().log` (newest first; `by` is who the act is recorded under: the decider for a choice, the executive for
    the plan; `at` the wall-clock ISO time). Undo restores the state before, so the entry goes with it. `chosen`
    keeps its shape, so no reader changes. The snapshot line is `snapText(op)`, then `pendingText(op)` when
    pending (existing strings).
  - **Counts check** (`tools/count_check.cjs`, from IA-1b; the inbox and badge from IA-1c). Per operator, in three
    states (default, `?state=no-recommendation`, and after one act: the first waiting decision chosen with its
    recommendation, where one exists), it computes its own expected values from `ATTN[op]`, `uxDecState(id).key` and
    `HC.decisions[].chooser` (never through `iaDecIds`, `iaWaiting` or the inbox builders) and asserts: the Overview
    "Decisions" count and its waiting split; each Site page's count, split and sticky pill; Outcomes column 6 per
    Site; (IA-1c) the badge, and the row sets of "For you" and "In your portfolio". Plants: `COUNT_PLANT=choose`
    (`iaWaiting` drops `none`; bites under the no-recommendation state); `COUNT_PLANT=foryou` (IA-1c; "For you" drops
    the plan).
- **Why.** R19, R29, P20. The counts disagreed because three predicates existed; one predicate, and a check that
  recomputes rather than reuses it, closes the class. Removing a chosen row would make the queue disagree with the
  Site page's state split and lose the "Chosen · awaiting approval" step the reviewed pages show.
- **P7 restated** (reviewer guide): a For-you decision (Metro, Ruiru expansion): the waiting counts and the badge drop
  by one, the row stays with its new state, the inbox row moves to "Since you last looked"; a portfolio decision
  (Lakeside, Kisiwa late repair): the same, the badge unchanged; the plan (approve on `#/plan`): the badge drops by
  one. Undo restores each.
- **P20 (who may choose).** Kept as reviewed: the viewer can choose on every decision in the demonstration, and the
  dialog records the choice under the decider. Owner question OQ-IA.1 below.

### D-IA.25 The hub: content per tab, the Overview budget, no self-links, no interim Act-first alias

- **Ruling.**
  - **Per tab (R25):**

| Route | H1 · crumbs | L1 | L2 | L3 | Primary |
|---|---|---|---|---|---|
| `portfolio` | "Portfolio" · `[['Portfolio']]` | headline; the 4 tiles | the queue panel (top 6), without "Act first ›" and without the "View all" lines | the bridge; "By outcome" | the queue's (first `choose` row's "Decide"), as reviewed; none in IA-1b, where `iaUnlink` turns decision links into text until IA-1c |
| `portfolio/outcomes` | "Outcomes" · `[['Portfolio','portfolio'],['Outcomes']]` | the headline (§3.3) | the Site table (D-IA.27) | `uxInsight(op)` | none |
| `portfolio/demand-and-capacity` | "Demand & capacity" · `[['Portfolio','portfolio'],['Demand & capacity']]` | `uxChain(op)` (its heading and answer are the headline) | none | `opportunityScreen()`'s sections | none |
| `site/:site` | the Site name, the legacy subtitle · `[['Sites'],[name]]` | the lead headline; `uxSiteTiles` | the queue (top 3) and "Actions in hand" (one block, as reviewed) | the seven sections; the help line | the queue's, repeated by the sticky |

    `home` is "Portfolio" for the three tabs and "Sites" for a Site (unlanded: nothing lights). `tabGroup` is
    "Portfolio" or "Site" (P18). A tab group with one landed tab draws no tab row, so IA-1b draws no Site tabs.
    The hub root carries the reused page's class (`ux-overview` on `portfolio`), so its CSS and the uxi selectors hold.
  - **Outcomes drops the per-heading tiles** of spec rev 2: the four headings already live once, as the Overview's
    "By outcome" tiles; a second rendering is the C1 class. Column 5 names each Site's heading.
  - **The overview budget (R17):** a block is a visible direct child of a `[data-level]` region of
    `[data-shape="hub"]`, outside `.ux-drawer` and `[data-ia-drawers]`; on `portfolio` at most 6 blocks and the
    hub section at most 2,500 px tall at 1440, on all three operators. The "More in the tabs" line is dropped (the
    frame's tabs replace it, and it names the old "outcomes by site"): 5 blocks. uxi's assertion is retargeted, shown
    failing first on `UXI_PLANT=block7` (a seventh block) and `UXI_PLANT=tall` (a 200 px block).
  - **No gap-tile link.** Spec rev 2's "the gap tile links to `portfolio/outcomes`" is withdrawn: the Outcomes tab
    sits one click away in the frame, and the link needed copy the spec forbade. The plan tile's "Review the plan"
    is then the Overview's only content edge to the plan, so `G1_PLANT=tile` bites (the plan falls to depth 2).
  - **No "View all" until IA-2b (R18).** The hub omits the "Act first ›" link and both "View all {n} in Act first"
    lines; the panel heading's "Decisions {n}" and its split state the total. `MOCK DEVIATION D5` (resolving unit
    IA-2b, which adds "View all {n}" to `decisions?scope=…`).
  - **The interim alias `portfolio/act-first` → `portfolio` is withdrawn.** `portfolio/act-first` gets its alias
    with IA-2b (→ `decisions`). An alias to the page that links it makes a self-link under a dead label.
  - **Self-link gate.** shape_check asserts that no link inside a `[data-level]` region has, after `iaCanon`, the
    current route's path and query (fragment-only `#…` links are not `#/` links). Plant `SHAPE_PLANT=selflink` adds
    a link to the host route in its L2.
- **Why.** R17, R18, R22, R25. The standing brief: each element is placed once, on purpose; a duplicate entry to the
  same view (the more-tabs line, the gap-tile link) is the clutter the owner named.

### D-IA.26 The decision page: the reviewed page placed in levels

- **Ruling.** Element by element (`uxDecisionPage`):

| Element | Place |
|---|---|
| The sticky bar | first, outside every level (`data-ux-sticky`) |
| `head`: the meta line, the stepper (`uxDecStatus`), "How this works" | L1 |
| `rec`: the recommendation card, its hero number(s), "Choose this" / "Choose another option" / "Review the plan" / "See the Actions" / "See the options", "Evidence and records" | L1 |
| `cards`: the option cards | L2 |
| `secs`: the six answer-titled sections, today's order (Why we recommend it, which holds "What would change the recommendation"; What it changes; Limits and cover; Cost and who pays; How we will check it worked; All options in detail) | L3 |
| the choose dialogs, Evidence and records, The Actions, How this works | `[data-ia-drawers]` |

  - **H1** (C17, as reviewed): the question (`uxDecQuestion(d)`) while `iaWaiting(id)`, the subject (`d.q`) once
    chosen. The document title follows the H1. Spec rev 2's "subject without a question form" is withdrawn.
  - **Stepper:** `uxDecSteps` as reviewed, path by path (a "none" first step; "Awaiting approval" for state
    `approval` and its `draft` variant; "Released at once" or "Actions go ahead" on the short paths). "Verified" is
    not shown: no verdict data exists before IA-2d's Results. Spec rev 2's fixed four words are withdrawn.
  - **No tiles.** The hero (`ux-drec-n`) is the guide's one number, with its basis (cover at stake, the value against
    its stated basis, or the cost and who pays) as reviewed. Spec rev 2's "up to 3 tiles" is withdrawn.
  - **Breadcrumb** `[['Decisions'], [Site name, 'site/<key>'], [d.q]]`; "Decisions" is text until IA-2b. The Site
    crumb is the way to the Site; spec rev 2's "Open site" is withdrawn (no new copy). `home: 'Decisions'`.
  - Routes: `decision/:dec` for every `DEC` entry of the operator's Sites (15 today; P12).
- **Why.** R21. The reviewed page already answers each question the spec tried to fix; the shape adds levels, not
  new content.

### D-IA.27 One adverse rule, the Outcomes table and its synthetic check

- **Ruling.**
  - **Adverse** is the bridge's own tone rule: a shown effect below zero (`vr < 0` in `uxSiteDriversShown`) works
    against the result on every operator, cost included (the model already signs effects as their effect on the
    headline result). `iaLargestAdverse(sk)`: the non-residual driver with the lowest `vr`, ties in board order; none
    → `null`. Read by Outcomes column 5 and by `IA_G1_SURFACES`. On the demo data Kasarani and Ruiru have none; their
    driver surface prints `n/a · no driver against target` and is not a surface.
  - **A Site's gap** is `siteM(sk).period.variance` (negative = adverse on every operator), through the same
    `figS('gap', sk, …)` call as the Site's gap tile. **Sort:** ascending gap, ties in `OPS[op].sites` order; Sites
    without a target (`tree(sk).plan == null`) last, with "Not available yet" in columns 3 to 5, and not counted in
    the headline's `m`.
  - **One cap mechanism:** the table caps at 10 rows the way the Site board does (`data-ux-over hidden`, then
    `uxCapNote(n, 10, id)`, "Show all {n}"). `uxCapLists` caps `ul.list` only, so the two never meet. The table is
    grouped (one `tbody` per group, headed by the group word and its count) only when the scope holds more than 10
    Sites in more than one group; the cap then applies per group.
  - **The builder is pure:** `iaOutcomeTable(rows, { scope })`, rows `{ key, name, group, hasTarget, resultHtml,
    gapHtml, gap, driverHtml, waiting }`. `tools/outcomes_table_check.cjs` (jsdom, from IA-1b) feeds it synthetic
    rows: A, 12 Sites in one group (10 shown and "Show all 12"); B, 12 Sites in two groups of 7 and 5 (two groups, no
    cap); C, B at `group:<the 7>` (7 rows); D, a Site without a target (last, outside `m`); and checks the sort.
    Plants `OUT_PLANT=cap|group|scope|sort|notarget`, each disabling its rule.
  - IA-2b's list component absorbs this table; its card names it.
- **Why.** R23, R24. Every demo operator has 3 Sites of one vertical, so these rules are identity on the data and
  only a synthetic list can fail them. One sign rule, the one the bridge draws, keeps the table and the bridge from
  disagreeing.

### D-IA.28 Addresses stay within the operator; an alias key never shadows a route

- **Ruling.**
  - `iaPattern` accepts `:site` only from `OPS[LS.op].sites` and `:dec` only from those Sites' `DEC` entries; the
    crawl classifier applies the same restriction with its own code. A typed `#/site/<another operator's Site>` or
    `#/decision/<another operator's decision>` shows not-found. Plant `SHAPE_PLANT=crossop` (`iaPattern` accepts any
    Site).
  - **Reserved paths:** every `IA_ROUTES` pattern, every `IA_RAIL` route and every route of every `IA_TAB_GROUPS`
    entry for the operator's Sites. No `IA_ALIASES` key may match one (shape_check, static, from IA-1b). Plant
    `SHAPE_PLANT=aliaskey` adds `IA_ALIASES['portfolio/outcomes'] = 'portfolio'`. The `financials` alias key is
    removed (the legacy screen keeps its legacy `ALIAS` only); `globalfinancials` → `financials` stays.
  - `mini`, `cold`, `ev` resolve to the operator's first Site of that group, or to no IA alias when it has none.
  - **The `recommendation` aliases** (P13) are a fixed table, mapped from the v7.0 Findings they named (`OBJ`):
    `recommendation`, `alternatives` (F-104, Kobo generator support) → `decision/kobo-generator`;
    `cold-recommendation` (F-118, Thika backup response) → `decision/thika-backup`; `ev-recommendation` (F-130,
    Ruiru charging session interrupted, the `ruiru-connector-fault` Finding) → `decision/ruiru-connector`. Under
    another operator the target is not live, so the typed address falls back as any non-live alias does.
    `iaRecDecision` is removed.
- **Why.** R30, R31, P13. One shell (D-IA.14) and one object, one address (D-IA.8); the static assertion catches the
  `financials` class before IA-2e lands it.

### D-IA.29 Gate economy and the browser gates the hub needs

- **Ruling.**
  - **Hosts (R38).** A planted run visits only its plant's host: shape plants run items 1, 3 and 4 on the host and
    the crawl to depth 0 (the host's own hrefs and the palette), the Lab plants item 5 only, `notfound` the typed
    probe only; AR plants run on one route per shape per operator (`plan`, `portfolio`, `portfolio/outcomes`,
    `portfolio/demand-and-capacity`, the first Site, from IA-1c the first decision); G1 and count plants run their
    whole check. Unplanted runs cover every live route. shape_check item 1 runs, unplanted, in the three states of
    D-IA.24.
  - **G3 (R33):** `g3_trends.cjs`'s root is `#app [data-shape="hub"] [data-level="L1"]`, failing when absent (no
    body fallback); it adds `t.scrollWidth <= t.clientWidth` on each `.ux-trend` at 390, 1280 and 1440. Plants
    `G3_PLANT=clip` (CSS clips `.ux-trend` at 390) and `G3_PLANT=root` (the L1 region renamed). It joins spec §6 from
    IA-1b (heavy slot).
  - **Headline (R35):** at most 2 lines at 1440 and 1280, measured by `ia_shots.cjs`; `SHOTS_PLANT=headline` narrows
    it to force a third line.
  - **Landing (R34):** from IA-1b the empty hash renders `iaStart()`; shape_check asserts it. Plant
    `SHAPE_PLANT=landing`.
  - **Kept, not gated (R36):** Demand & capacity's welding hour bar (`bad`, evening diesel) and `capBars`' `over`
    mark are reviewed content, not a deviation against target; spec rev 2's C11 clause is narrowed to "no new red".
    Listed in the packet; revisited after G2.
  - **Unmeasured at G2 (R37):** D-IA.10's "released Actions, filtered to the plan version" has no surface before
    IA-2b; the packet says so.
- **Why.** Each plant must still bite at its host; a whole-route rerun of every plant proves nothing more and costs
  minutes per unit.

### D-IA.30 The review bar's rebuild list is a popover, by design

- **Ruling.** The review bar is mock tooling, not product copy, so spec §7 does not bind it. The popover is the
  design: summary "Still to be rebuilt ({n})"; body "Still to be rebuilt: " and the unlanded rail items joined by
  " · ", then, from IA-1b, a line "Site tabs: Operations · Performance · Financials · Evidence · Setup". `{n}` counts
  both. IA-1a deviation 3 closes.
- **Why.** R32. One line pushed the 1280 queue row below the fold; the popover keeps the list one click away.

### Each question, once

- **R16** D-IA.21. **R17** D-IA.25. **R18** D-IA.25. **R19** D-IA.24. **R20** D-IA.22, D-IA.23. **R21** D-IA.26.
- **R22** D-IA.25 (H1, crumbs, home) and spec §3.3 (copy, per operator kind; the month is "October", from
  `MANIFEST.accounting_period`, as the Overview reads; a Site without a target per D-IA.27; Demand & capacity's
  headline is its chain's own).
- **R23** D-IA.27. **R24** D-IA.27. **R25** D-IA.25. **R26** D-IA.22 (levels) and D-IA.25; the row grammar ("a row
  has one target") is IA-2b's list component and its gate; until then the reviewed queue rows keep "Why" and the
  action link: `MOCK DEVIATION D5` (resolving unit IA-2b).
- **R27** D-IA.23. **R28** D-IA.21; the control is `button.ia-inbox[data-ia-inbox][data-ux-drawer="ia-inbox"]` in
  the top bar between the period chip and the theme toggle; queue edges are the links in the Overview's L2
  `.ux-queue`, inbox edges the control and `#ia-inbox a[data-ia-row]`; at 390 the label is visually hidden and the
  icon and badge stay; the drawer is in the frame, closed, so the after-render check covers it on every route.
- **R29** D-IA.24. **R30** D-IA.28. **R31** D-IA.28. **R32** D-IA.30. **R33** D-IA.29.
- **R34** D-IA.29 (a done criterion for IA-1b). **R35** D-IA.29. **R36** D-IA.29. **R37** D-IA.29. **R38** D-IA.29.
- **P12** every `DEC` entry (15 today); D-IA.12's "All 14 decisions" now reads "every decision". **P13** D-IA.28.
- **P14** D-IA.22. **P15** `uxCapLists` stays in `iaFinish` on every IA route (one rule for every screen, D-IA.13);
  the packet lists the `render_text` differences, and the overview budget is measured after it. **P16** adopted:
  each retarget whose assertion changes is shown failing on a plant first (uxi budget, uxi block 8's "link / no
  link", G3's root). **P17** D-IA.22. **P18** adopted (D-IA.25). **P19** no change: `uxFocusState` finds
  `.ux-dmeta .status-pill` (kept in L1) or the H1; acts are user-caused. **P20** D-IA.24, OQ-IA.1.

### Owner questions (W3; defaults applied)

- **OQ-IA.1 Who may press "Choose this".** The demonstration lets the viewer (the executive) choose on every
  decision and records the choice under the person who decides it (13 of 15 are the Site manager's). **Default:**
  keep it, so the walkthrough can show the act on any decision. The alternative is that only the decider sees the
  button and everyone else sees who decides.
- **OQ-IA.2 What the "Waiting for you" badge counts.** **Default:** only what the executive decides: the plan
  awaiting approval and decisions whose chooser is the executive (1 on Lakeside and Harvest, 2 on Metro). Other
  waiting decisions are listed under "In your portfolio" without adding to the badge. The alternative counts every
  waiting decision and the plan (4 on Lakeside), which makes the badge a portfolio count, not a personal one.
