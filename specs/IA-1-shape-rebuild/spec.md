# IA-1 and IA-2: rebuild the mock-up by shape (implementer spec)

Status: in_review (IA-1a built on task/IA-1a-frame; IA-1b and IA-1c not started)

Architect (Claude), 2026-11-20, rev 2 (handshake round 1 folded in: D-IA.15 to D-IA.20). This is the handshake format (`.ai/RULES.md` §4): this spec, `reviewer-guide.md`,
`rulings.md` (D-IA.1 to D-IA.20, and "Handshake answers (round 1)"), `handshake.md` and
`mid-build-questions.md`.

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
  - **Base:** `a090e1220` (task/uiux-design-model, review r5 ACCEPT 20 Nov; merged to main as `25b3ae88b`). Branch from main at or after `25b3ae88b`. `786e1f905` is
    the handshake's pre-flight read, not the base. No IA-1a code starts before this line is filled.
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

Functions are cited by name, never by line: the UI branch is still moving.

### 2.1 Files

**New** (add to the bundle list in `build.mjs` after `loop-ux.js` and before `loop-init.js`):
- `vNEXT/ia-routes.js`: the route, alias and rail registry, `iaParse`, `iaLive`, `iaStart`, `iaDev` (§2.2);
- `vNEXT/ia-shapes.js`: the shape functions (§3 to §4), `iaFrame`, `iaFinish`, `iaUnlink`, `iaRender`, `iaBind`
  (§2.3, §2.4);
- `vNEXT/ia.css`, loaded between `ux.css` and `brand.css` (`brand.css` stays last);
- `vNEXT/tools/ia_crawl.cjs`: the shared jsdom boot, crawl and href classifier (§2.5);
- `vNEXT/tools/shape_check.cjs`, `vNEXT/tools/click_depth_check.cjs`, `vNEXT/tools/after_render_check.cjs`;
- `vNEXT/tools/ia_gates.cjs`: runs the three checks and every plant of every landed unit (§2.5).

**Changed:**
- `screens.js` `render()`: it resolves the hash with `iaParse`. If the path is a live `IA_ROUTES` entry (after
  alias resolution, §2.2), it writes the review bar and `<div id="ia-root"></div>` into `#app`, calls
  `iaRender(route, ctx)` and returns. Every other route renders as today and is reachable only from the review bar's
  screen select. The review bar is built with `uxReviewExtrasHtml(hash)` for every route (§2.3).
- `screens.js` `currentScreen()`: passes `iaParse(location.hash).path`, never the query.
- `loop-core.js` `resolveScreen`: resolves `IA_ALIASES` first, only when live; otherwise `ALIAS`; never both in
  a chain. With `iaDev()` off, a screen whose `root` is "Simulator Lab" resolves to `not-found`.
- `loop-core.js` `afterRender`: for an IA route it runs `brandAndListenersOnly()` only (§2.4).
- `loop-core.js` `uxScopeLine` becomes `uxScopeLine(root, screen)`: the legacy call passes the canvas and
  `currentScreen()`; the pending chip is read from `root`'s own top bar.
- `loop-ux.js`: `uxChrome`'s scope switch and period menu become the string builders `uxScopeSwitchHtml(entries,
  label)` and `uxPeriodMenuHtml(op)`, which `uxChrome` (legacy) and `iaFrame` both call. `uxBrandSwitch` becomes
  `uxReviewExtrasHtml(hash)` (the brand select, the D2 and D5 marks, `uxDecReviewMarks`' markup, the "Developer
  access" switch and the "Still to be rebuilt" line); its D5 route test also matches `#/plan`. `uxCommands()` is
  filtered by `iaLive` when an IA route is active.
- `loop-portfolio.js`: `planScreen` is split into `planParts(op)` (§2.6). `planScreen()` joins the parts into
  exactly today's string.
- `loop-init.js`: keeps registering the old screens for the review-bar select. It no longer sets `PR` renderers for
  routes that `IA_ROUTES` owns. The select omits Lab screens while `iaDev()` is off.
- Existing checks that boot `portfolio/act-first/plan` (`plan_switch_check.cjs`, `ux_interaction_check.cjs`,
  `design_lint.cjs`, `audit.mjs`, `rendered_strings.cjs`) boot `plan`. Retargeting is not a change to the check; an
  assertion on legacy chrome replaced by the frame's equivalent is, and is shown failing on a plant first (§6).
- `tools/run-audit.sh` calls `node tools/ia_gates.cjs` before its `CHROME` guard.

### 2.2 The registry (`ia-routes.js`)

**The landed units.** `const IA_LANDED = new Set(['IA-1a'])`. Each unit adds its own ID in its last commit.

**The address.** `iaParse(hash)` returns `{ path, params, query }`. The scope and the drawer live in the hash:
`#/route?scope=…&drawer=…`. `?state=` stays in `location.search` (mock tooling).

**The route table.** `const IA_ROUTES = [ … ]`, one entry per route pattern:

```js
{ id: 'portfolio/outcomes',          // the hash path; a parameter is written :site, :dec
  shape: 'hub',                      // one of IA_SHAPES (below)
  object: 'portfolio',               // portfolio | site | decision | plan | finding | action | asset | incident |
                                     // maintenance | right | record | results | evidence | financials | settings | lab
  home: 'Portfolio',                 // the rail item it lights (D-IA.9), or null
  unit: 'IA-1b',                     // the unit that builds it; the route is live only if IA_LANDED has it
  tab: 'Outcomes',                   // a hub or page tab label, or null
  noFigures: false,                  // optional; true hides the scope line (uxScopeLine)
  title: ctx => 'Outcomes',          // the H1; the document title is `${title} · ${operator name}`
  crumbs: ctx => [['Portfolio', 'portfolio'], ['Outcomes']],
  render: ctx => '…' }               // returns markup, built only by calling the shape function
```

`const IA_SHAPES = ['frame','hub','list','decision','plan','record','asset','drawer','statement']`.

IA-1a registers two routes:
- `plan`: shape `plan`, object `plan`, home Plan, unit IA-1a, crumbs `[['Plan']]`, render §2.6;
- `not-found`: shape `frame`, home `null`, unit IA-1a, `noFigures: true`, crumbs `[['Page not found']]`, body
  `<section data-shape="frame">` around `uxNotFound()`'s content. An unknown hash renders it inside the frame.

**The context.** `ctx = { op, scope, site, params, query }`:
- `op` is `LS.op` (`lakeside`, `harvest`, `metro`);
- `scope` is `{ kind: 'all' | 'group' | 'site', id }`, from `?scope=all|group:<vertical>|site:<key>`; the default is
  `all`; the group id is the vertical key (`mini`, `cold`, `ev`);
- `site` is the Site key, for routes that carry `:site`;
- `params` holds the route parameters; `query` holds the query parameters.

**The aliases.** `const IA_ALIASES = { old: new | (params => new) }`. An alias is live only once its target's unit
has landed. `resolveScreen` tries `IA_ALIASES` first (live entries only), then `ALIAS`, and never chains them. The
table:

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

**Liveness (D-IA.16).** `iaLive(href)` is true when the href's path is a landed `IA_ROUTES` entry, or a live alias,
or `lab` while `iaDev()` is on. Nothing else is live: not a legacy route, not a stub, not `not-found`.

**The start.** `iaStart()` is `plan` until `IA_LANDED` has IA-1b, then `portfolio` (D-IA.15).

**The developer switch.** `iaDev()` is `sessionStorage['l4-dev'] === '1'`; off by default (D-IA.7).

**The rail.** `const IA_RAIL = [{ group, label, route, unit }]`, in the order of D-IA.1, with the same labels:
- Operations: Portfolio `portfolio` IA-1b · Sites `sites` IA-2b · Assets & cover `assets` IA-2c.
- Intelligence: Findings `findings` IA-2b.
- Work: Decisions `decisions` IA-2b · Plan `plan` IA-1a · Actions `actions` IA-2b · Incidents `incidents` IA-2c ·
  Maintenance `maintenance` IA-2c.
- Assurance: Results `results` IA-2d · Evidence & records `evidence` IA-2d.
- Business: Financials `financials` IA-2e.
- Admin: Settings `settings` IA-2e.

So in IA-1a only Plan is a link. An item whose unit has not landed renders as an **unavailable root**: its label,
muted, with the status "Not available yet", `data-rail-unavailable`, no link and no tab stop. This is the live
product's rule (`frontend/src/ui/NavRail.tsx`, W1-UX-07), and the frame copies its markup and wording. The group
header still renders.

### 2.3 The frame's markup (shape `frame`)

`iaFrame(route, ctx, body)` returns the frame root `<div class="shell ia-frame" id="ia-root">`, holding today's
structure: `nav.rail` and `main.workspace > header.topbar + .canvas`. The header inside `.canvas` uses today's
`.page-heading` markup, so `uxScopeLine` finds it. The review bar is outside the frame root.

**The rail.**
- The rail is built from `IA_RAIL`. The active item is `route.home`; with `home: null` no item lights.
- The Lab is not in the rail. A workspace footer `<div data-ia-footer>` with group "Workspace" and item "Simulator
  Lab" (`href="#/lab"`) renders only while `iaDev()` is on. The review bar's "Developer access" switch sets
  `l4-dev` and re-renders.

**The top bar.** Left to right, each on one line down to 1280 px (audit C15):
1. **Scope** (D-IA.6), from `uxScopeSwitchHtml`: the button reads `<operator name> · All sites ▾`, or `· <group
   name>`, or `· <Site name>`. The menu lists "All sites"; the groups (one per vertical the operator has:
   "Mini-grids", "Cold rooms", "EV depots"); the Sites. A Site entry links to `site/<key>`; a group or all links to
   the current path with `?scope=`. On a page that is not a hub, the choice is kept in the address and changes
   nothing on the page. Links elsewhere do not carry the scope; only "View all" does (D-IA.8). In IA-1a the Site
   entries are unlinked by `iaUnlink`.
2. **Search**: the button text "Search Sites, decisions and Findings" is in the frame markup, with Ctrl K and
   today's palette. `uxSearchLabel` is not called for IA routes. On an IA route the palette lists only entries that
   `iaLive` accepts. IA-2b extends its index.
3. **The period chip**, from `uxPeriodMenuHtml(op)`.
4. **Waiting for you**, with a red count badge, from IA-1c. In IA-1a the control is not drawn.
5. **The theme toggle** (`themeToggle()`), then **the avatar**, as today.

**The header.** The H1 is `route.title(ctx)`. The breadcrumb comes from `route.crumbs`. Tabs render only for routes
that have a `tab`, from the route's tab group (§3.1), and only for landed tabs.

**The phone.** At 390 px the rail collapses as it does today, and the phone Section menu is kept.

### 2.4 Render, finish, insert (D-IA.13, D-IA.16, D-IA.17)

`iaRender(route, ctx)`:
1. Builds the full markup string: `iaFrame(route, ctx, route.render(ctx))`.
2. Parses it into a detached `<template>`.
3. Runs `iaFinish(fragment, route)` on the **detached** fragment, in this order (today's order, plus the two passes
   that `uxShell` ran first):
   1. `iaUnlink`: every `a[href^="#/"]` whose target `iaLive` rejects becomes `<span class="ia-unlinked">` with
      its inner markup and any trailing arrow dropped; a tab link to such a target is removed; a link to a live
      alias gets its target's canonical href;
   2. `uxCapLists` (with "Show all");
   3. `tagReplay`;
   4. `uxScopeLine(fragment, route)`;
   5. `plainWords`;
   6. `uxDedupeUnits`;
   7. `uxFixSigns`.
4. Replaces `#ia-root` once with the fragment.
5. Calls `window.__iaInserted?.(root)` with the new `#ia-root`, synchronously.
6. Calls `iaBind(route)`, which only adds event listeners, sets focus and schedules `uxStickyTick`.

**Rules.**
- `afterRender` does not run its DOM passes for IA routes: `if (IA_ROUTE_ACTIVE) return brandAndListenersOnly()`.
  `brandAndListenersOnly` applies the brand attribute on `<html>` and the `.scroll-region` `scrolls` mark.
- `uxChrome`, `uxShell`, `uxSearchLabel` and `uxBrandSwitch` are not called for IA routes. The frame calls the
  string builders of §2.1 instead; no markup is copied.
- The two layout-caused class changes after insertion are allowed and named: `is-on` on `[data-ux-sticky]`
  (`uxStickyTick`) and `scrolls` on `.scroll-region`.

The passes may later move into components. That is allowed but not required.

### 2.5 The checks (IA-1a builds them; every later unit runs them)

**Shared: `tools/ia_crawl.cjs`.** The jsdom boot (as `shell_check.cjs` boots today), `go(hash)`, the crawl and the
href classifier. The classifier reads `IA_ROUTES`, `IA_LANDED` and `IA_ALIASES` from the window and matches hrefs
with its own code; it never calls `iaLive`. A target is **good** only if its path is a landed `IA_ROUTES` entry.
It is **bad** if it is an alias (live or not), a stub, a legacy screen, an unlanded route or `not-found`. Operators
are `lakeside`, `harvest`, `metro`; output prints `OPS[op].name`. `:site` is enumerated over `OPS[op].sites` and
`:dec` over the `DEC` entries of those Sites. A route's identity is its path plus its query keys, sorted.

**`tools/shape_check.cjs`**, for each operator:
1. **Every live route renders from its shape.** For each live route (and the typed `#/x-unknown`, which must show
   `not-found`): the frame root once; `[data-shape="<shape>"]` once; the `data-level` values in document order never
   decrease (L1, L2, L3; any may be absent); exactly one `h1`; at most 4 `.ux-kpi` in L1; at most one
   `button.primary` per `[data-level]` region; a `button.primary` outside every region fails unless it is inside
   `[data-ux-sticky]` and has the same `data-act` as the L1 primary.
2. **Crawl.** Start at `iaStart()`. Follow every `a[href^="#/"]`, the tab links and, once per operator, the
   palette's `[data-go]` targets (open with `uxPalette(true)`, read, close), for up to 6 hops. Skip the review bar
   and `[data-ia-footer]`. Every href met must classify good.
3. **The rail.** Every rail item whose unit has not landed has `data-rail-unavailable`, the status "Not available
   yet" and no `href`; every landed item has an `href` to its route.
4. **Text.** Every live route's document title is `${title} · ${operator name}`.
5. **The Lab gate** (D-IA.19). Switch off: no `[data-ia-footer]`, no `a[href^="#/lab"]` in `#app`, no review-select
   option for a screen whose `root` is "Simulator Lab", and `#/lab` resolves to `not-found`. Switch on: the footer
   reads "Workspace" and "Simulator Lab" with `href="#/lab"`, and `#/lab` resolves to `lab`.

Plants (`SHAPE_PLANT=<name>`, each must fail; host route `iaStart()`):
- `unlink`: `iaUnlink` is the identity on the host (in IA-1a the plan's `decision/*` and `site/*` links survive);
- `stub`: `iaLive` returns true for `site/kisiwa/health`, and the host's L2 gains a link to it;
- `rail`: the rail builder treats every item as landed;
- `palette`: the palette's `iaLive` filter is off;
- `primary`: the host's L1 gains a second `button.primary`;
- `lab`: `iaDev()` returns true always.

**`tools/click_depth_check.cjs`** (G1, D-IA.10 measured as D-IA.18):
- **Edges.** Content edges only: header tab links, links, rows and tiles inside `[data-level]` regions, the
  "Waiting for you" control and its drawer rows. The rail, the breadcrumb, the scope menu and search are not edges.
  A drawer opened by a link is a node (`?drawer=`).
- **Origin.** `#/portfolio`. Until IA-1b lands there is no origin, so no live surface: the check prints
  `G1: origin lands in IA-1b; 0 live surfaces` and runs only its self-test.
- **Self-test** (every unit). A fixed synthetic graph in the check (Overview, a tile, a queue row, the inbox, the
  plan, a decision, a Site, a driver drawer) with the expected depths; the BFS must reproduce them.
- **Surfaces, per landed unit:**
  - IA-1b: the Plan page (≤ 1); every Site Overview (≤ 2); the driver drawer of each Site's largest adverse driver
    (≤ 3; the interim Finding surface until IA-2d);
  - IA-1c: every decision the Overview queue shows (≤ 1 over queue edges); every decision waiting for a choice and
    a plan in PROPOSED (≤ 2 over inbox edges only); each plan item's Decision (≤ 2).
- It prints one line per surface: `op · surface · depth · path`, and fails past a limit.
- Plants (`G1_PLANT=<name>`): `engine` (every unit; one self-test edge removed); `tile` (from IA-1b; the Overview's
  plan tile link removed); `inbox` (from IA-1c; one waiting decision dropped from the inbox rows).

**`tools/after_render_check.cjs`** (D-IA.17):
- For every live route and operator, the check sets `window.__iaInserted` in `beforeParse`, attaches a
  `MutationObserver` (`childList`, `characterData`, `attributes`, `subtree`, old values) to the root it is handed,
  and waits for idle (2 animation frames plus 300 ms). It dispatches no event.
- It fails on any mutation, except a `class` change on `[data-ux-sticky]` whose only changed token is `is-on`, or on
  `.scroll-region` whose only changed token is `scrolls`.
- Plants (`AR_PLANT=<name>`; host: every live route):
  - `text`: the route's markup gains `<p data-ar-plant>the evaluator</p>`; `iaFinish` skips `plainWords`; `iaRender`
    runs `plainWords(root)` in a `setTimeout(0)`. The plant throws "plant did not bite" if that node's text is
    unchanged;
  - `attr`: a `setTimeout(0)` sets `data-ar-plant` on the first `div` inside `.canvas`;
  - `late`: a `setTimeout(250)` appends a text node to the H1.

**`tools/ia_gates.cjs`** runs the three checks, then each plant of each landed unit as its own process, and exits
non-zero if a check fails or a plant passes. It prints one line per run: `check · plant · expected · got`. No
browser is needed.

### 2.6 The plan, in the interim (D-IA.20)

`plan` is registered as a live route in IA-1a (§2.2). `planScreen` is split into `planParts(op)`, which returns:
- `sticky`: `uxPlanSticky(…)`;
- `band`: `uxPlanBand(…)`;
- `l2`: the items section with its total and "How the plan is chosen";
- `l3`: `uxPlanDiff`, "Two ways to restore Mto's inverter" (Lakeside), the crew visits and "Listed beside the
  plan" grid, "Left out of the plan, and why", "All four cases" (Lakeside), and "Actions that return to their
  creator" (when any);
- `aside`: `approvalPanel` and the "Try another case" switches.

`planScreen()` joins them into exactly today's string. **Proof:** for each operator and each switch case, a node
script compares `planScreen()` before and after the split; the packet cites its output (byte-identical).

The route's `render` returns:

```html
<section data-shape="plan">
  {sticky}
  <div data-level="L1">{band}</div>
  <div class="layout-main-side">
    <div><div data-level="L2">{l2}</div><div data-level="L3">{l3}</div></div>
    <aside class="side-panel" data-level="L3">{aside}</aside>
  </div>
</section>
```

The sticky bar repeats the L1 primary by design and sits outside every level (§2.5 item 1). This is the one
interim; it must not grow. IA-2a rebuilds it as the plan shape proper.

### 2.7 Copy (exact)

- **Group labels:** OPERATIONS, INTELLIGENCE, WORK, ASSURANCE, BUSINESS, ADMIN. They are uppercase by CSS; the text
  is title case.
- **Item labels:** as in §2.2.
- **Unavailable status:** "Not available yet".
- **Search button:** "Search Sites, decisions and Findings".
- **Scope groups:** "Mini-grids", "Cold rooms", "EV depots"; the first entry "All sites".
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
| `portfolio` | `uxOverview(op)`, split into the shape's slots | The overview budget (guide §2.2a): at most 6 blocks, 2,500 px at 1440. The plan tile links to `plan`. The gap tile links to `portfolio/outcomes` |
| `portfolio/outcomes` | L1: "N of M Sites below target" and one tile per heading. L2: **one row per Site** (columns below). L3: `uxInsight(op)`, "Sites that look alike" | Sorted by gap, most adverse first. Capped at 10 with "Show all N". Grouped by vertical when the scope has more than 10 Sites. No factor tree inline (audit C5) |
| `portfolio/demand-and-capacity` | `uxChain(op)` and the content of `opportunityScreen()` | Red only for an adverse deviation against target (audit C11) |
| `site/:site` (all 9) | The reviewed Site page from `siteOverview(sk)` and its UI-branch sections | One template for all 9 Sites. Each driver row opens its driver drawer, which names its Finding and decision |

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

- `decision/:dec` covers all 14 `DEC` entries, through `decisionScreen`, split into the shape's
  slots.
- `home: 'Decisions'`. Until IA-2b lands, the Decisions rail item is unavailable, so no rail item lights.
- The breadcrumb is `Decisions › <Site name> › <subject>`. Until IA-2b, "Decisions" is plain text, not a link.
- "Open site" links to `site/<key>`.
- **The acts.** Choose, and Undo, use the UI branch's single pattern (`uxChooseDialog`, `UX_ACTS`): a dialog, then
  a toast with Undo, then the state changes on the page, in the queue and in the inbox count.

### 4.3 The inbox (the drawer, in its first use)

- **The control.** "Waiting for you", in the top bar. The count is the number of items in "For you".
- **The drawer.** It opens through `uxDrawer`, with the address `#/<route>?drawer=inbox` (in the hash, §2.2). It has three sections:
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
| IA-2e | Statement | `financials` (Statement, Budget & targets, Prices); `site/:site/financials`; `settings` (four tabs); the Lab's own content only (its gate is built in IA-1a, D-IA.19) | Reconciliation (the statement against the headings, all operators). Final sweep: every one of the 184 manifest routes plus `plan` resolves to a live route, an alias or not-found, and `rebase_v70.py` renders nothing routed |

## 6. Every unit's gate (D-IA.12, D-IA.14)

Before review, all of these pass, with their output in the packet:
1. `node tools/ia_gates.cjs`: `shape_check.cjs`, `click_depth_check.cjs` and `after_render_check.cjs` pass, and
   every plant of every landed unit fails (§2.5).
2. (IA-1a) the `planParts` byte-identity script (§2.6).
3. (IA-1b onwards) `shell_check.cjs` on `tools/ia_crawl.cjs`, with `SHELL_PLANT=1` shown failing first.
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
- the checks with their real output, and `ia_gates.cjs`' table with every plant failing;
- the G1 depth table (operator · surface · depth · path); in IA-1a, the self-test table and the line "G1: origin
  lands in IA-1b; 0 live surfaces";
- the screenshots' folder;
- the count of mid-build questions (RULES §4, item 7);
- known `MOCK DEVIATION`s, each with its category.
