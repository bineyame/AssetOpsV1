# IA-1 rulings: the app-wide menu, page organization and the shape rebuild

Architect (Claude), 2026-11-20. Each ruling gives its reason. Index lines are in
`.ai/decisions/index-rulings-8.md`. Owner sources, verbatim:
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
| IA-1a | Frame and gates | The menu, the top bar, the route and shape registry, aliases for old routes, and the G1, shape and after-render checks; the reviewed plan page as one named interim, so that G1 holds from the start (spec §2.6) |
| IA-1b | Hub | Portfolio's three tabs; the Overview of all 9 Sites |
| IA-1c | Decision | All 14 decisions; the inbox drawer |
| G2 stop | | The owner's input |
| IA-2a | Plan | The plan page per operator |
| IA-2b | List | Decisions, Findings, Actions and Sites |
| IA-2c | Asset | The Asset page; the lists for Assets & cover, Incidents and Maintenance; Site Operations, Performance and Setup |
| IA-2d | Drawers and record page | The Incident, Maintenance, Right, Record and figure-evidence drawers; the Finding and Action pages; the Results and Evidence & records lists; Site Evidence |
| IA-2e | Statement | Financials and Site Financials; Settings; the Lab gate; the final route sweep |

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
    no user event caused. Plant: `AR_PLANT=1` re-enables `PLAIN_WORDS` after render, and the check must fail.
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

## Handshake answers (round 1)

(None yet.)
