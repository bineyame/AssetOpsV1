# IA-1 and IA-2: rebuild the mock-up by shape (implementer spec)

Architect (Claude), 2026-11-20, rev 1. This is the handshake format (`.ai/RULES.md` §4): this spec, `reviewer-guide.md`,
`rulings.md` (D-IA.1 to D-IA.14) and `handshake.md`.

**Read first:**
- the proposal page `Docs/design-system/ia-proposal/index.html`, §2 to §6 (the screenshots beside it will do);
- `rulings.md`;
- `Docs/design-system/uiux-guide.md` §2 and §8;
- `layer4-transformation-design.md` §2.10.

The IA-1 units are fully specified here. IA-2 is specified to the level its order and gates need; its unit cards
are folded in after the owner's G2 input (D-IA.11). No IA-2 unit starts before that.

## 0. Before you start

- **Where.**
  - The mock-up is `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/`, shortened below to `vNEXT/`.
  - Branch from `task/uiux-design-model` at the head where its review is accepted (D-IA.13), then merge `main`.
  - If a fix round on that branch is still open when you start, branch from its latest head and merge each later
    fix round in before review.
  - Branches and worktrees, one per unit:
    - `task/ia-1a-frame` in `/opt/assetecon/AssetOpsV1-ia1a`;
    - `task/ia-1b-hub` in `/opt/assetecon/AssetOpsV1-ia1b`;
    - `task/ia-1c-decision` in `/opt/assetecon/AssetOpsV1-ia1c`.

    Each unit branches from the previous unit's merged head.
- **What you may touch:**
  - `vNEXT/` only, plus its `tools/`;
  - the new files named in this spec;
  - `walkthroughs.md` (the owner's guide), where a route or menu item it names changes;
  - no backend, no `frontend/src` and no database.
- **Machine.**
  - Browser checks run through `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh -- …`, with
    `source /opt/assetecon/tools/pw/env.sh; export LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH`.
  - jsdom checks need no browser.
  - Never touch ports 5490 or 8990, or Docker.
- **Build.**
  - `node build.mjs` writes `index.html`.
  - Run `python3 tools/gen_fixtures.py` only if the manifest changed; IA-1 does not change it.
- **Evidence** goes to `/opt/assetecon/evidence/IA-1/<unit>/`, never into the tree. The packet cites it by path
  (RULES §9).

## 1. Outcome

**Who sees what.** An operator executive opens the mock-up and sees:
- the approved menu;
- the Portfolio hub with three tabs;
- every Site's Overview from one hub shape;
- every decision from one decision shape;
- a "Waiting for you" inbox.

**What is reachable.** Every screen reachable from the Portfolio is rendered from a shape, with nothing rewritten
after it renders. No stub, and no v7.0 re-based screen, is reachable from it.

**G1.** The three executive journeys reach their answers within the limits of D-IA.10.

**G2.** After IA-1c, the owner sees these screens before anything else is built.

## 2. The frame (IA-1a)

### 2.1 Files

**New** (add to the bundle list in `build.mjs`, after `loop-ux.js`):
- `vNEXT/ia-routes.js`: the route, alias and rail registry (§2.2);
- `vNEXT/ia-shapes.js`: the shape functions (§3 to §4) and `iaRender` (§2.4);
- `vNEXT/ia.css`, loaded after `ux.css`;
- `vNEXT/tools/click_depth_check.cjs` (G1);
- `vNEXT/tools/shape_check.cjs`;
- `vNEXT/tools/after_render_check.cjs`.

**Changed:**
- `screens.js` `render()`, at `:998`: a route found in `IA_ROUTES` (after alias resolution) renders through
  `iaRender(route, ctx)` and returns. Every other route renders as today and is reachable only from the review bar's
  screen select.
- `loop-core.js` `resolveScreen` (`:340`) and `afterRender` (`:408`): see §2.4.
- `loop-init.js`: keeps registering the old screens for the review-bar select. It no longer sets `PR` renderers for
  routes that `IA_ROUTES` owns.

### 2.2 The registry (`ia-routes.js`)

**The landed units.** `const IA_LANDED = new Set(['IA-1a'])`. Each unit adds its own ID to this set in its last
commit.

**The route table.** `const IA_ROUTES = [ … ]`, one entry per route pattern:

```js
{ id: 'portfolio/outcomes',          // the hash route; a parameter is written :site, :dec
  shape: 'hub',                      // one of IA_SHAPES (below)
  object: 'portfolio',               // portfolio | site | decision | plan | finding | action | asset | incident |
                                     // maintenance | right | record | results | evidence | financials | settings | lab
  home: 'Portfolio',                 // the rail item it lights (D-IA.9)
  unit: 'IA-1b',                     // the unit that builds it; the route is live only if IA_LANDED has it
  tab: 'Outcomes',                   // a hub or page tab label, or null
  title: ctx => 'Outcomes',          // the H1; the document title is `${title} · ${operator name}`
  crumbs: ctx => [['Portfolio', 'portfolio'], ['Outcomes']],
  render: ctx => '…' }               // returns markup, built only by calling the shape function
```

`const IA_SHAPES = ['frame','hub','list','decision','plan','record','asset','drawer','statement']`.

**The context.** `ctx = { op, scope, site, params, query }`:
- `op` is `LS.op`;
- `scope` is `{ kind: 'all' | 'group' | 'site', id }`, read from `?scope=`; the default is `all`;
- `site` is the Site key, for routes that carry `:site`;
- `params` holds the route parameters;
- `query` holds the query parameters.

**The aliases.** `const IA_ALIASES = { old: new }`. An alias is live only once its target route's unit has landed;
until then the old route behaves as it does today. The table:

| Old route | New route | Target unit |
|---|---|---|
| `portfolio/outcomes-by-site` | `portfolio/outcomes` | IA-1b |
| `portfolio/act-first` | `portfolio` until IA-2b, then `decisions` | IA-1b, then IA-2b |
| `portfolio/act-first/plan` | `plan` | IA-1a (interim, §2.6), then IA-2a |
| `portfolio/what-changed` | `results` | IA-2d |
| `portfolio/scope`, `globalevidence` | `evidence` | IA-2d |
| `oprecords` | `evidence/records` | IA-2d |
| `mini`, `cold`, `ev` | `site/kobo`, `site/thika`, `site/ruiru` | IA-1b |
| `site/:site/economics`, `financials`, `cold-financials`, `ev-financials` | `site/:site/financials` | IA-2e |
| `recommendation`, `alternatives`, `cold-recommendation`, `ev-recommendation` | the decision on that Finding (from `DEC[].finding`) | IA-1c |
| `globalfinancials` | `financials` | IA-2e |
| `settings-policies`, `settings-tenant` | `settings`, `settings/organisation` | IA-2e |

IA-2 units add the remaining aliases. Their full list comes from the proposal's §6 table.

**The rail.** `const IA_RAIL = [{ group, label, route, unit }]`, in the order of D-IA.1, with the same labels:
- Operations: Portfolio `portfolio` IA-1a · Sites `sites` IA-2b · Assets & cover `assets` IA-2c.
- Intelligence: Findings `findings` IA-2b.
- Work: Decisions `decisions` IA-2b · Plan `plan` IA-1a · Actions `actions` IA-2b · Incidents `incidents` IA-2c ·
  Maintenance `maintenance` IA-2c.
- Assurance: Results `results` IA-2d · Evidence & records `evidence` IA-2d.
- Business: Financials `financials` IA-2e.
- Admin: Settings `settings` IA-2e.

An item whose unit has not landed renders as an **unavailable root**: its label, muted, with the status "Not
available yet". It has no link and no tab stop. This is the live product's rule (`frontend/src/ui/NavRail.tsx`,
W1-UX-07), and the frame copies its markup and wording. The group header still renders.

### 2.3 The frame's markup (shape `frame`)

`iaFrame(route, ctx, body)` returns the whole canvas: the rail, the top bar, the header, the tabs and the body. The
review bar is outside it and stays as it is.

**The rail.**
- The rail is built from `IA_RAIL`.
- The active item is `route.home`.
- The Lab is not in the rail. A workspace footer item "Simulator Lab" renders only when the review bar's "Developer
  access" switch is on (D-IA.7). The switch is stored in `sessionStorage` as `l4-dev` and is off by default.

**The top bar.** Left to right, each on one line down to 1280 px (audit C15):
1. **Scope** (D-IA.6): the button reads `<operator name> · All sites ▾`, or `· <group name>`, or `· <Site name>`. The
   menu lists:
   - "All sites";
   - the groups (one per vertical in the demo: "Mini-grids", "Cold rooms", "EV depots", only those the operator
     has);
   - the Sites.

   Choosing a Site goes to `site/<key>`. On a hub, choosing a group or all reloads the hub with `?scope=`. This
   replaces both of today's Site switchers.
2. **Search**, labelled "Search Sites, decisions and Findings", with Ctrl K. Keep today's palette. IA-2b extends its
   index.
3. **The period chip**, as today, from `uxChrome`'s period menu.
4. **Waiting for you**, with a red count badge, from IA-1c. In IA-1a the control is not drawn.
5. **The avatar**, as today.

**The header.** The H1 is `route.title(ctx)`. The breadcrumb comes from `route.crumbs`. Tabs render only for routes
that have a `tab`, from the route's tab group (§3.1).

**The phone.** At 390 px the rail collapses as it does today, and the phone Section menu is kept.

### 2.4 Render, finish, insert (D-IA.13)

`iaRender(route, ctx)`:
1. Builds the full markup string: `iaFrame(route, ctx, route.render(ctx))`.
2. Parses it into a detached `<template>`.
3. Runs `iaFinish(fragment, route)`, which applies today's global passes in this order, on the **detached**
   fragment:
   1. `tagReplay`
   2. `plainWords`
   3. `uxDedupeUnits`
   4. `uxFixSigns`
   5. `uxScopeLine`
4. Replaces `#app .canvas` once with the fragment.
5. Calls `iaBind(route)`, which only adds event listeners and sets focus.

**Rules.**
- `afterRender` must not run its DOM passes for IA routes. Guard it with `if (IA_ROUTE_ACTIVE) return
  brandAndListenersOnly()`.
- Brand-pack attributes on `<html>` are allowed: they are outside `#app`.
- `uxChrome` and `uxShell` are not called for IA routes. The frame renders what they injected.

The passes may later move into components. That is allowed but not required.

### 2.5 The three checks (IA-1a builds them; every later unit runs them)

**`tools/shape_check.cjs`** (jsdom), for each operator (`lakeside-power`, `harvest-cold`, `metro-bus`):
1. **Every live route renders from its shape.** Its canvas has `[data-shape="<shape>"]` once, and its level regions
   `[data-level]` appear in the order L1, L2, L3, with any of them allowed to be absent. It has exactly one `h1`, at
   most 4 `.ux-kpi` in L1, and at most one `button.primary` per region.
2. **Crawl.** Start at `#/portfolio`. Follow every `a[href^="#/"]`, `[data-go]` and tab link breadcrumb-first, for
   up to 6 hops. Every route reached must be a live IA route or `not-found`:
   - a route whose screen has `stub: true` fails;
   - a route outside `IA_ROUTES` fails;
   - a link to an unlanded route fails.
3. **The rail.** Every rail item whose unit has not landed has no `href`.
4. **The plant.** `SHAPE_PLANT=1` adds a link from the Portfolio Overview to `site/kisiwa/health`, which is a stub.
   The check must fail.

**`tools/click_depth_check.cjs`** (jsdom, G1, D-IA.10):
- For each operator, it walks breadth-first from `#/portfolio` over the same links, plus the "Waiting for you"
  control and its items.
- It reports the shortest depth to each answer surface in D-IA.10's table that has landed:
  - IA-1a: the Plan page;
  - IA-1b: every Site Overview, and the driver drawer of the largest adverse driver;
  - IA-1c: every decision waiting for a choice, and the inbox items.
- It fails past each limit.
- **Interim rule (until IA-2d).** The "Finding at depth 3" surface is the driver drawer that names the Finding,
  opened from the Site Overview's driver row. The Finding page replaces it in IA-2d.
- It prints one line per surface: `op · surface · depth · path`.
- **The plant.** `G1_PLANT=1` removes the Overview's plan tile link. The check must fail.

**`tools/after_render_check.cjs`** (jsdom):
- For every live IA route and operator, it attaches a `MutationObserver` to `#app` the moment `iaRender` inserts
  the fragment, and waits for idle (2 animation frames plus 300 ms).
- It fails on any `childList` or `characterData` mutation, or any attribute mutation other than `aria-expanded`,
  `open` or `class` on a `details` or `button`, that no dispatched user event caused.
- **The plant.** `AR_PLANT=1` calls `plainWords(canvas)` after insertion. The check must fail.

All three are added to `tools/run-audit.sh` and to the packet's check list.

### 2.6 The plan, in the interim

`plan` is registered as a live route in IA-1a: shape `plan`, unit `IA-1a`, home Plan. Its `render` calls the
reviewed `planScreen()` (`loop-portfolio.js:465`), wrapped in `<section data-shape="plan">` with its sections marked
L1, L2 and L3. That marking covers:
- the state band and the approve bar as L1;
- the items as L2;
- left out and the review as L3.

This is the one interim. It goes through `iaRender`, so it passes the after-render check. IA-2a rebuilds it as the
plan shape proper. G1 needs the plan at depth 1 from the start.

### 2.7 Copy (exact)

- **Group labels:** OPERATIONS, INTELLIGENCE, WORK, ASSURANCE, BUSINESS, ADMIN. They are uppercase by CSS; the text
  is title case.
- **Item labels:** as in §2.2.
- **Unavailable status:** "Not available yet".
- **Workspace footer:** group "Workspace", item "Simulator Lab".
- **Review bar:**
  - the switch label is "Developer access";
  - the line "Still to be rebuilt: " followed by the unlanded rail items, joined by " · ".

## 3. The hub shape (IA-1b)

### 3.1 The shape

`shapeHub(ctx, { headline, tiles, primary, queue, explain })` returns:

```html
<section data-shape="hub">
  <div data-level="L1"> headline (≤2 lines) · up to 4 uxKpi tiles · at most one primary action </div>
  <div data-level="L2"> the queue: uxQueue rows, top 6 at portfolio scope and top 3 at Site scope, the count of the rest; "View all" only once its home list has landed </div>
  <div data-level="L3"> answer-titled sections, one level, in the order given </div>
</section>
```

- **Evidence (L4)** is reached only through drawers, from a figure (`uxOpen`).
- **Tab groups:**
  - Portfolio: Overview `portfolio`, Outcomes `portfolio/outcomes`, Demand & capacity `portfolio/demand-and-capacity`.
  - Site: Overview `site/:site`, Operations `/operations`, Performance `/performance`, Financials `/financials`,
    Evidence `/evidence`, Setup `/setup`. Only tabs whose unit has landed are drawn (D-IA.12), so IA-1b draws Overview
    alone and the review bar lists the rest.

### 3.2 The routes it renders

| Route | Content (reuse) | Rules |
|---|---|---|
| `portfolio` | `uxOverview(op)` (`loop-ux.js:323`), split into the shape's slots | The overview budget (guide §2.2a): at most 6 blocks, 2,500 px at 1440. The plan tile links to `plan`. The gap tile links to `portfolio/outcomes` |
| `portfolio/outcomes` | L1: "N of M Sites below target" and one tile per heading. L2: **one row per Site** (columns below). L3: `uxInsight(op)`, "Sites that look alike" | Sorted by gap, most adverse first. Capped at 10 with "Show all N". Grouped by vertical when the scope has more than 10 Sites. No factor tree inline (audit C5) |
| `portfolio/demand-and-capacity` | `uxChain(op)` and the content of `opportunityScreen()` | Red only for an adverse deviation against target (audit C11) |
| `site/:site` (all 9) | The reviewed Site page from `siteOverview(sk)` (`loop-site.js:7`) and its UI-branch sections | One template for all 9 Sites. Each driver row opens its driver drawer, which names its Finding and decision |

**The Outcomes columns:**
1. Site (link to `site/<key>`)
2. Vertical
3. Contribution against target
4. Gap
5. Largest adverse driver, with its heading
6. Open decisions (count)

Every figure reads `DERIVED`, as the Overview's tiles do. The Site's gap is the same term the Site Overview's gap
tile reads (D-IA.14, one source).

### 3.3 Copy

- **Tab labels:** as in §3.1.
- **Outcomes L1 headline:** "{n} of {m} Sites are below target this month". If none is below target: "Every Site is
  on or above target this month".
- **The cap link:** "Show all {n} Sites".

## 4. The decision shape (IA-1c)

### 4.1 The shape

`shapeDecision(ctx, { subject, state, steps, recommendation, tiles, options, sections, primary })` returns:
- `data-shape="decision"`, with L1, L2 and L3 as in §3.1.
- **L1:**
  - the H1 is the decision's subject (`d.q` without a question form), from the UI branch's rule (audit C17);
  - the state line is a stepper: Recommended › Chosen › Released › Verified, with the current step marked;
  - the recommendation, in one line, with who decides and by when;
  - up to 3 tiles: the 12-month value against no action, the one-off cost, and what is at stake;
  - the primary action, "Choose this".
- **L2:** the options compared against no action, from the UI branch's option cards.
- **L3:** answer-titled sections, one level deep. Each section is one of today's: how each option moves its drivers,
  limits, cover, what would change it, and the verification plan.

### 4.2 Routes and wayfinding

- `decision/:dec` covers all 14 `DEC` entries, through `decisionScreen` (`loop-site.js:52`), split into the shape's
  slots.
- `home: 'Decisions'`. Until IA-2b lands, the Decisions rail item is unavailable, so no rail item lights.
- The breadcrumb is `Decisions › <Site name> › <subject>`. Until IA-2b, "Decisions" is plain text, not a link.
- "Open site" links to `site/<key>`.
- **The acts.** Choose, and Undo, use the UI branch's single pattern (`uxChooseDialog`, `UX_ACTS`): a dialog, then
  a toast with Undo, then the state changes on the page, in the queue and in the inbox count.

### 4.3 The inbox (the drawer, in its first use)

- **The control.** "Waiting for you", in the top bar. The count is the number of items in "For you".
- **The drawer.** It opens through `uxDrawer`, with the address `?drawer=inbox`. It has three sections:
  1. **For you:** the plan, if it is in PROPOSED, and every decision in `choose` state whose chooser role is the
     operator executive (`deciderOf`, design §2.6).
  2. **In your portfolio:** every other decision in `choose` state, with who decides.
  3. **Since you last looked:**
     - the acts recorded in this session (`uxMock()`), newest first, each with who, what and when;
     - the snapshot line, "Figures as of {asOf}", with "recalculation pending since {time}" when `snapOf(op).pending`.
- **Rows.** Each row opens its Decision or the Plan. The empty state is "Nothing is waiting for you".

### 4.4 Copy

- The drawer's title is "Waiting for you".
- Its section titles are "For you", "In your portfolio" and "Since you last looked".
- The stepper words are Recommended, Chosen, Released and Verified.

## 5. IA-2 (after the G2 stop; unit cards finalised after the owner's input)

| Unit | Shape | Routes | Shape's own gate, beyond §6 |
|---|---|---|---|
| IA-2a | Plan | `plan` | The state stepper (Draft › Proposed › Approved › Closed). The budget and crew meters. Items, Left out, Review and History as tabs. `plan_switch_check.cjs` passes |
| IA-2b | List | `decisions`, `findings`, `actions`, `sites`; "View all" goes live on the hubs; aliases `portfolio/act-first` → `decisions` and `findings-*` → `findings?heading=` | One list component. Filters, sort and scope in the address. Cap at 10 with "Show all". Count tiles equal the list length (audit C2.3). Search indexes every object |
| IA-2c | Asset | `asset/:asset`; `assets`, `incidents` and `maintenance` as list instances; `site/:site/operations`, `/performance`, `/setup` | One timeline per asset. Each row of the Site's Operations tab has the same columns on every vertical. Performance panels follow the vertical, with the slots fixed |
| IA-2d | Drawer and record page | The incident, maintenance, right and record drawers; `finding/:id`, `action/:id`; `results`, `evidence` (Coverage, Records, Imports); `site/:site/evidence` | Every drawer has an address and closes with Esc. G1's Finding surface moves to the Finding page |
| IA-2e | Statement | `financials` (Statement, Budget & targets, Prices); `site/:site/financials`; `settings` (four tabs); `lab` behind the developer switch | Reconciliation (the statement against the headings, all operators). Final sweep: every one of the 184 manifest routes plus `plan` resolves to a live route, an alias or not-found, and `rebase_v70.py` renders nothing routed |

## 6. Every unit's gate (D-IA.12, D-IA.14)

Before review, all of these pass, with their output in the packet:
1. `shape_check.cjs` (and its plant fails).
2. `click_depth_check.cjs` (and its plant fails).
3. `after_render_check.cjs` (and its plant fails).
4. `ux_interaction_check.cjs`, `shell_check.cjs`, `vocab_check.cjs`, `copy_check.cjs`, `render_text.cjs`,
   `design_lint.cjs` (and `LINT_PLANT=1` fails), `plan_switch_check.cjs`, `hand_typed_scan.py`.
5. `python3 ../check_manifest.py`.
6. Screenshots at 1440 × 900, 1280 × 720 and 390 × 844, for the three operators in light and dark, of every route the
   unit adds. They go to the evidence folder.

A unit that changes an existing check shows that check failing on a planted violation first.

## 7. Scope limits

- No figure, manifest or evaluator change. A figure that disagrees between two screens is reported to the Architect,
  never adjusted on screen.
- No new copy beyond §2.7, §3.3 and §4.4, plus the labels the reused functions already have. A missing string is
  raised as a question, not invented.
- No change to `frontend/src`. The live product keeps its rail (O1).
- The old screens stay registered for the review-bar select until IA-2e. None may be linked from a live IA route.
- `USER_REVIEW_REQUIRED: true` (UI/UX). After IA-1c, stop for the owner (D-IA.11).

## 8. Packet

Write the packet in `specs/IA-1-shape-rebuild/packet-<unit>.md`, at most 3k tokens. It holds:
- the module-path line;
- the checks with their real output and the plants failing;
- the G1 depth table (operator · surface · depth);
- the screenshots' folder;
- the count of mid-build questions (RULES §4, item 7);
- known `MOCK DEVIATION`s, each with its category.
