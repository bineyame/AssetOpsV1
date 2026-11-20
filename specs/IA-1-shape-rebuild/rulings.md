# IA-1 rulings: the app-wide menu, page organization and the shape rebuild

Architect (Claude), 2026-11-20. Each ruling gives its reason. D-IA.15 to D-IA.20 come from the handshake (round 1). Index lines are in
`.ai/decisions/index-rulings-8.md` (D-IA.1 to D-IA.14) and `index-rulings-9.md` (D-IA.15 to D-IA.20). Owner sources, verbatim:
- `owner/owner-app-wide-ia-proposal-2026-11-20.md` (the request);
- `owner/owner-ia-proposal-answers-2026-11-20.md` (the answers to Q1 to Q9);
- `owner/owner-ia-direction-approved-2026-11-20.md` (the approval and the two guardrails).

The proposal is `Docs/design-system/ia-proposal/index.html`. Handshake answers go at the end of this file, under
"Handshake answers (round 1)".

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
| IA-1c | Decision | All 14 decisions; the inbox drawer |
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
