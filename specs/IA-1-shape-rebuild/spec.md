# IA-1 and IA-2: rebuild the mock-up by shape (implementer spec)

Status: IA-1a, IA-1b, IA-1c merged (`bf9428ca3`); G2 seen by the owner ("UI looks ok for now", 21 Nov); IA-2a specified (§5.1), handshake next

Architect (Claude), 2026-11-21, rev 5: IA-2a handshake folded in (D-IA.49 to D-IA.53, `rulings-3.md`); rev 4: IA-2a's full design (§5.1; D-IA.43 to D-IA.48 in `rulings-2.md`). Rev 3, 2026-11-20
(the IA-1b/IA-1c handshake folded in: D-IA.21 to D-IA.30; rev 2 folded in round 1,
D-IA.15 to D-IA.20). This is the handshake format (`.ai/RULES.md` §4): this spec, `reviewer-guide.md`, `rulings.md`
(D-IA.1 to D-IA.30, "Handshake answers (round 1)" and "IA-1b/IA-1c handshake answers"), `handshake.md` and
`mid-build-questions.md`. Where rev 3 changed a rev 2 rule, the ruling names it.

**Read first:**
- the proposal page `Docs/design-system/ia-proposal/index.html`, §2 to §6 (the screenshots beside it will do);
- `rulings.md`;
- `Docs/design-system/uiux-guide.md` §2 and §8;
- `layer4-transformation-design.md` §2.10.

The IA-1 units are fully specified here. IA-2 is specified to the level its order and gates need; its unit cards
are folded in after the owner's G2 input (D-IA.11). The owner gave it on 21 Nov; IA-2a's card is §5.1 (rev 4). For
IA-2a the binding part is §5.1, §6, §7 and §8.

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

    Each unit branches from the previous unit's merged head: IA-1b from `main` at or after the merge of
    `task/IA-1bc-handshake-answers` (IA-1a is merged at `e100640bf`); IA-1c from IA-1b's merged head.
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
- every decision from one decision shape (every `DEC` entry: 15 today);
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
| `portfolio/act-first` | `decisions` (no interim alias, D-IA.25) | IA-2b |
| `portfolio/act-first/plan` | `plan` | IA-1a (interim, §2.6), then IA-2a |
| `portfolio/what-changed` | `results` | IA-2d |
| `portfolio/scope`, `globalevidence` | `evidence` | IA-2d |
| `oprecords` | `evidence/records` | IA-2d |
| `mini`, `cold`, `ev` | the operator's first Site of that group, else none (D-IA.28) | IA-1b |
| `site/:site/economics`, `cold-financials`, `ev-financials` | `site/:site/financials` (`financials` is a reserved route, never an alias key, D-IA.28) | IA-2e |
| `recommendation`, `alternatives` · `cold-recommendation` · `ev-recommendation` | `decision/kobo-generator` · `decision/thika-backup` · `decision/ruiru-connector` (fixed table, D-IA.28) | IA-1c |
| `globalfinancials` | `financials` | IA-2e |
| `settings-policies`, `settings-tenant` | `settings`, `settings/organisation` | IA-2e |

IA-2 units add the remaining aliases. Their full list comes from the proposal's §6 table.

**Liveness (D-IA.16).** `iaLive(href)` is true when the href's path is a landed `IA_ROUTES` entry, or a live alias,
or `lab` while `iaDev()` is on. Nothing else is live: not a legacy route, not a stub, not `not-found`.

**The start.** `iaStart()` is `plan` until `IA_LANDED` has IA-1b, then `portfolio` (D-IA.15). From IA-1b the empty hash
renders `iaStart()` (D-IA.29).

**Parameters stay in the operator** (D-IA.28): `:site` matches only `OPS[LS.op].sites`, `:dec` only those Sites'
`DEC` entries; a typed address outside them shows not-found.

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
4. **Waiting for you**, with a red count badge, from IA-1c (§4.3). In IA-1a and IA-1b the control is not drawn.
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

### 2.5 The checks (IA-1a builds them; every later unit runs them; §2.8 changes them from IA-1b)

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
- `primary`: the host's L1 gains a second `button.primary` (from IA-1b: two, with distinct acts, §2.8);
- `lab`: `iaDev()` returns true always.
- IA-1a's round-2 plants (`tabstop`, `notfound`, `noact`, `lablegacy`) stand; `noact` runs on `plan` from IA-1b (§2.8).

**`tools/click_depth_check.cjs`** (G1, D-IA.10 measured as D-IA.18):
- **Edges.** Content edges only: header tab links, links, rows and tiles inside `[data-level]` regions, the
  "Waiting for you" control and its drawer rows. The rail, the breadcrumb, the scope menu and search are not edges.
  A drawer is a node, reached by its opener (§2.8, D-IA.21).
- **Origin.** `#/portfolio`. Until IA-1b lands there is no origin, so no live surface: the check prints
  `G1: origin lands in IA-1b; 0 live surfaces` and runs only its self-test.
- **Self-test** (every unit). A fixed synthetic graph in the check (Overview, a tile, a queue row, the inbox, the
  plan, a decision, a Site, a driver drawer) with the expected depths; the BFS must reproduce them.
- **Surfaces, per landed unit:**
  - IA-1b: the Plan page (≤ 1); every Site Overview (≤ 2); the driver drawer of each Site's largest driver against
    target, `iaLargestAdverse` (≤ 3; the interim Finding surface until IA-2d; `n/a` for a Site without one);
  - IA-1c: every decision the Overview queue shows (≤ 1 over queue edges); every decision waiting for a choice
    (`iaWaiting`) and a plan in PROPOSED (≤ 2 over inbox edges only); each plan item's Decision (≤ 2).
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

### 2.8 Gate changes that land with IA-1b and IA-1c (D-IA.21 to D-IA.30)

These change §2.5's checks. Each changed assertion is shown failing on its plant first (§6).

**Where the new code lives.**
- `ia-shapes.js`: `iaLevels`, `shapeHub`, `shapeDecision`, `iaOutcomeTable`, the inbox control and drawer builders,
  and the predicates `iaDecIds(op, scope)`, `iaWaiting(id)`, `iaForYou(op)`, `iaLargestAdverse(sk)` (D-IA.24, D-IA.27).
- `ia-routes.js`: the hub and decision routes, `IA_TAB_GROUPS`, `IA_G1_SURFACES()`, the alias changes (D-IA.28).
- `loop-ux.js` / `loop-site.js`: the parts splits only (D-IA.22) and the act log in `uxActDo` (D-IA.24).
- `ia.css`: `[data-shape="hub"] > [data-level], [data-shape="decision"] > [data-level], [data-ia-drawers] { display:
  contents }`, and the inbox control (`.ia-inbox`, `.ia-badge`, the 390 rule hiding `.ia-inbox-label`).
- `tools/count_check.cjs`, `tools/outcomes_table_check.cjs` (new); one byte-identity script, `tools/parts_identity.cjs`,
  covering `planParts` and the three new splits (§6 item 2).

**`tools/ia_crawl.cjs`.**
- `identity()` keeps the value of `drawer`; other query keys stay key-only (D-IA.21).
- The classifier accepts `:site` only from the booted operator's `OPS[op].sites` and `:dec` only from those Sites'
  `DEC` entries (D-IA.28).

**`tools/shape_check.cjs`.**
- Item 1, the primary rule (D-IA.23): a primary is `a.primary` or `button.primary` outside every `.ux-drawer`; its act
  is `data-act`, else `data-ux-act`, else `drawer:<data-ux-drawer>`, else `href:<href>`, and a primary without one
  fails; at most one per `[data-level]` region; the page primary is the first inside a region, in document order; a
  primary outside every region sits in `[data-ux-sticky]` with the page primary's act.
- Item 1 runs, unplanted, in three states per operator: default; `?state=no-recommendation` (in `location.search`);
  after one act (the operator's first waiting decision chosen with its recommendation through `uxMockSet`, where one
  exists).
- Item 6 (IA-1b), no self-link: no `a[href^="#/"]` inside a `[data-level]` region whose `iaCanon` href has the
  current route's path and query.
- Item 7 (IA-1b), reserved paths: no `IA_ALIASES` key matches an `IA_ROUTES` pattern, an `IA_RAIL` route or a route
  of an `IA_TAB_GROUPS` entry for the operator's Sites (static).
- Item 8 (IA-1b), the operator's own addresses: typed `#/site/<a Site of another operator>` and
  `#/decision/<a decision of another operator>` show not-found.
- Item 9 (IA-1b), the landing: the empty hash renders `iaStart()`.
- Plants: `primary` now adds two `button.primary` with distinct acts to the host's L1; `noact` runs on `plan` and
  removes the act of its page primary. New from IA-1b: `selflink`, `aliaskey`, `crossop`, `linkprimary` (two
  `a.button.primary` in the host's L2), `landing`. New from IA-1c (host: the operator's first waiting decision; Harvest,
  which has none, skips them): `decprimary`, `stickyact`. Each is defined in D-IA.23, D-IA.25, D-IA.28 or D-IA.29.

**`tools/click_depth_check.cjs`** (D-IA.21):
- Nodes are pages (the route) and drawers (`<route>#drawer=<element id>`). A page's edges: `a[href^="#/"]` and
  `[data-ux-drawer]` inside its header tabs, its `[data-level]` regions and `[data-ia-inbox]`, never inside a
  `.ux-drawer`. An opener is an edge to its drawer node. A drawer node's edges: the links and openers inside that
  drawer element.
- `IA_G1_SURFACES()` (in `ia-routes.js`) returns `{ op, surface, route, limit, via }`, `via` one of `any`, `queue`,
  `inbox`. For `queue`, the check walks only the links in `portfolio`'s L2 `.ux-queue`; for `inbox`, only the
  `[data-ia-inbox]` control and `#ia-inbox a[data-ia-row]`.
- Self-test: the synthetic graph gains a drawer node reached by an opener; and the edge reader is tested on a fixed
  DOM fixture (a level region with a link A and an opener to drawer D; inside the closed D, a link B), which must read
  page → A, page → D and D → B, never page → B.
- Plants: `tile` (IA-1b; the plan tile's link removed), `driver` (IA-1b; the Site board's driver openers lose
  `data-ux-drawer`), `hidden` (IA-1b; the reader's `.ux-drawer` exclusion removed, failing the fixture test), `inbox`
  (IA-1c; one waiting decision dropped from the inbox rows).

**New checks, run by `ia_gates.cjs` from IA-1b:** `tools/count_check.cjs` (D-IA.24; plants `COUNT_PLANT=choose`, and
from IA-1c `foryou`) and `tools/outcomes_table_check.cjs` (D-IA.27; plants `OUT_PLANT=cap|group|scope|sort|notarget`).
The runner clears every `*_PLANT` variable before each run.

**Hosts** (D-IA.29): a planted run visits only its plant's host; AR plants run on one route per shape per operator.

## 3. The hub shape (IA-1b)

### 3.1 The shape

`shapeHub(ctx, { cls, sticky, l1, l2, l3, drawers })` returns `iaLevels('hub', …)` (D-IA.22):

```html
<section data-shape="hub" class="{cls}">
  {sticky}
  <div data-level="L1"> headline (≤ 2 lines at 1440 and 1280) · up to 4 uxKpi tiles · at most one primary </div>
  <div data-level="L2"> the queue or the home list's rows, capped </div>
  <div data-level="L3"> answer-titled sections, one level, in the order given </div>
  <div data-ia-drawers> the page's top-level drawers </div>
</section>
```

- An empty slot omits its region. `[data-shape="hub"] > [data-level]` and `[data-ia-drawers]` are
  `display: contents` (`ia.css`), so the reviewed layout does not move.
- **Evidence (L4)** is reached only through drawers, from a figure (`uxOpen`).
- **Parts, proven byte-identical** (D-IA.22). The hub never calls the joined legacy function.
  - `uxOverviewParts(op)` returns `{ headline, tiles, queue, actFirst, more, bridge, cats, moreTabs }`, cut from
    today's template at its element boundaries; `queue` is a function `(actFirst, more) => html` that returns the
    `.ux-main-aside` block with those two fragments in their places. `uxOverview(op)` returns `<div
    class="ux-overview">` + the parts in today's order, with `queue(actFirst, more)` + `</div>`, byte for byte.
  - `siteOverviewP(sk)` returns the `P` object `siteOverview` builds today; `siteOverview(sk)` is
    `uxSitePage(sk, siteOverviewP(sk))`.
  - `uxSiteParts(sk, P, qMax)` returns `{ sticky, lead, tiles, queue, secs, help, drawers }` (`queue` is the
    `.ux-main-aside` block with the queue and "Actions in hand"; `drawers` is `B.drawers` and the "How …" drawer);
    `uxSitePage(sk, P)` joins `uxSiteParts(sk, P, Infinity)` in today's order.
- **Tab groups** (`IA_TAB_GROUPS`, keyed by `route.tabGroup`):
  - `Portfolio`: Overview `portfolio`, Outcomes `portfolio/outcomes`, Demand & capacity `portfolio/demand-and-capacity`.
  - `Site`: Overview `site/:site`, Operations `/operations`, Performance `/performance`, Financials `/financials`,
    Evidence `/evidence`, Setup `/setup`.
  - Only landed tabs are drawn, and a group with one landed tab draws no tab row: IA-1b draws the three Portfolio tabs
    and no Site tab row. The review bar lists the five Site tabs (D-IA.30).

### 3.2 The routes it renders (D-IA.25)

| Route | H1 · crumbs | `cls` | L1 | L2 | L3 | Drawers |
|---|---|---|---|---|---|---|
| `portfolio` | "Portfolio" · `[['Portfolio']]` | `ux-overview` | headline; the 4 tiles | `queue('', '')`: the queue panel, top 6, without "Act first ›" and the "View all" lines | the bridge; "By outcome" | none at top level (the bridge's and headings' drawers stay inside their sections) |
| `portfolio/outcomes` | "Outcomes" · `[['Portfolio','portfolio'],['Outcomes']]` | none | the headline (§3.3) | `iaOutcomeTable(rows, { scope })` | `uxInsight(op)` | none |
| `portfolio/demand-and-capacity` | "Demand & capacity" · `[['Portfolio','portfolio'],['Demand & capacity']]` | none | `uxChain(op)` | none | `opportunityScreen()` | none |
| `site/:site` (the operator's 3) | the Site name; subtitle as the legacy Site screen's · `[['Sites'],[name]]` | the legacy wrapper's, if any | the lead headline; `uxSiteTiles(sk)` | the queue (top 3) and "Actions in hand", one block | the seven sections; the help line | the driver drawers; "How …" |

- `home`: "Portfolio" (three tabs), "Sites" (a Site; unlanded, so nothing lights). `tabGroup`: "Portfolio" or "Site".
- The Site sticky comes first, outside the levels. Its "Decide" targets the queue's own primary (D-IA.22's one named
  fix).
- The only content link from the Overview to the plan is the plan tile's "Review the plan" (`G1_PLANT=tile`).
- **The overview budget:** on `portfolio`, at most 6 blocks (a visible direct child of a level region, outside
  drawers) and the hub section at most 2,500 px tall at 1440, for all three operators (5 blocks once "More in the
  tabs" is dropped).
- **Outcomes** (D-IA.27). One row per Site in scope, sorted by gap ascending (most adverse first), ties in
  `OPS[op].sites` order, Sites without a target last. Capped at 10 with `uxCapNote` ("Show all {n}"). Grouped by
  group only above 10 Sites in more than one group. Every figure reads `DERIVED`, as the Site tiles do.

**The Outcomes columns** (headers exact; cells by operator kind, `OPS[op].kind`):

| # | Header | Cell |
|---|---|---|
| 1 | Site | `link('site/<key>', name)` |
| 2 | Group | the group word (`IA_GROUP_WORD[iaVertical(sk)]`) |
| 3 | Contribution (cost kind: Cost per required departure met) | "{actual} against a target of {target}", formatted as the Site's first tile (`usdW` or `fmtU(…, t.unit)`) |
| 4 | Gap to target | the Site gap tile's own call, `figS('gap', sk, s.period.variance, usdW(…, true))` |
| 5 | Largest driver against target | `iaLargestAdverse(sk)`: its label and `usdW(vr, true)`, then `<small>` its heading (`LENS[k][0]`); none: "No driver widens the gap" (cost kind: "No driver raises the cost") |
| 6 | Waiting for a choice | the count of `iaDecIds(op, site)` with `iaWaiting` (0 shown as 0) |

A Site without a target reads "Not available yet" in columns 3 to 5.

### 3.3 Copy

- **Tab labels:** as in §3.1. **H1s:** "Portfolio", "Outcomes", "Demand & capacity", the Site name.
- **Outcomes headline** (`{month}` is the accounting period's month, "October", as the Overview's headline reads):
  - contribution kind: "{n} of {m} Sites are below target in {month}"; none: "Every Site is on or above target in
    {month}";
  - cost kind: "{n} of {m} Sites are over target in {month}"; none: "Every Site is on or under target in {month}";
  - `n` counts Sites with a negative gap; `m` counts Sites with a target.
- **The cap link:** `uxCapNote`'s "Show all {n}".
- **Column headers and the two "no driver" cells:** as in §3.2.
- **Group header row** (grouped tables only): the group word and `<span class="ux-count">{k}</span>`.

## 4. The decision shape (IA-1c)

### 4.1 The shape (D-IA.26)

`shapeDecision(ctx, { sticky, l1, l2, l3, drawers })` returns `iaLevels('decision', …)`. The parts come from
`uxDecisionSlots(id, decisionParts(id))`, proven byte-identical (D-IA.22): `{ sticky, head, rec, cards, secs, drawers }`,
where `drawers` is today's `dialogs + evidence + actsDrawer + howDrawer`. `decisionParts(id)` returns the `parts` object
`decisionScreen` builds today; `decisionScreen(id)` is `uxDecisionPage(id, decisionParts(id))`, and `uxDecisionPage`
joins the slots in today's order.

| Element | Place |
|---|---|
| `sticky` | first, outside every level |
| `head` (meta line, stepper, "How this works") and `rec` (the recommendation card with its acts and "Evidence and records") | L1 |
| `cards` (the option cards) | L2 |
| `secs` (the six answer-titled sections, today's order) | L3 |
| the choose dialogs, Evidence and records, The Actions, How this works | `[data-ia-drawers]` |

- **H1:** `iaWaiting(id) ? uxDecQuestion(d) : d.q` (C17, as reviewed). The document title follows.
- **Stepper:** `uxDecStatus` / `uxDecSteps` as reviewed; no "Verified" step.
- **The hero number:** the recommendation card's `ux-drec-n`, as reviewed; no `.ux-kpi` tiles.
- **Primary:** "Choose this" (an opener) in L1 while state `choose`; the sticky repeats it with the same act.

### 4.2 Routes and wayfinding

- `decision/:dec` covers every `DEC` entry of the operator's Sites (15 across the three operators).
- `home: 'Decisions'`, `tabGroup: null`. Until IA-2b the Decisions rail item is unavailable, so no rail item lights.
- The breadcrumb is `[['Decisions'], [Site name, 'site/<key>'], [d.q]]`; "Decisions" is text until IA-2b. The Site
  crumb is the way to the Site (no "Open site" link).
- **The acts.** Choose and Undo use the reviewed pattern (`uxChooseDialog`, `uxActDo`): a dialog, a toast with Undo,
  then the state changes on the page, in the queue row, in every waiting count and, for a For-you item, in the badge
  (D-IA.24). The row stays in the queue with its new state.
- **The act log:** `uxActDo` appends `{ key, op, by, at, toast }` to `uxMock().log`, newest first (D-IA.24).

### 4.3 The inbox (D-IA.21, D-IA.24)

- **The control,** in the top bar between the period chip and the theme toggle:
  `<button type="button" class="ia-inbox" data-ia-inbox data-ux-drawer="ia-inbox" aria-haspopup="dialog"
  aria-controls="ia-inbox">{icon('check')}<span class="ia-inbox-label">Waiting for you</span>{badge}</button>`.
  `{badge}` is `<span class="ia-badge" data-ia-badge>{n}</span>` with `<span class="vh">, {n} waiting</span>`, and is
  absent when `n` is 0. At 390 the label is visually hidden (`.vh` rules); the icon and badge stay. At 1280 the top
  bar stays on one line.
- **The drawer** is `uxDrawer('ia-inbox', 'Waiting for you', body, true)`, rendered closed inside the frame root, after
  `.canvas`. It opens in place (no address until IA-2d). Esc and close shut it.
- **Sections:**
  1. **For you:** the plan row when `uxPlanState(op).state === 'PROPOSED'`; then each waiting decision whose chooser is
     `OPERATOR_EXECUTIVE`.
  2. **In your portfolio:** every other waiting decision (`iaDecIds(op, all)` with `iaWaiting`), in that order.
  3. **Since you last looked:** the operator's entries of `uxMock().log`, newest first; then the snapshot line,
     `snapText(op)`, and `pendingText(op)` when `snapOf(op).pending`.
- **Rows** (`<ul class="list ia-inbox-rows">`):
  - plan: `<a href="#/plan" data-ia-row="plan">The plan for {periodWords()} <small>{STATE_WORD[state]}: awaiting
    approval</small></a>`;
  - decision: `<a href="#/decision/{id}" data-ia-row="decision:{id}">{d.q} <small>{Site name} · Decides: {who(op,
    D.p)}</small></a>`;
  - log entry: `<a href="#/{decision/<id> or plan}" data-ia-row="log:{i}">{toast} <small>{by} · {hh:mm}</small></a>`
    (`hhmm(at)`).
- **Empty states:** For you: "Nothing is waiting for you"; In your portfolio: "Nothing else is waiting for a
  choice"; Since you last looked (no entry): "No change recorded in this session", then the snapshot line.

### 4.4 Copy

- The control's label and the drawer's title: "Waiting for you"; the badge's hidden text ", {n} waiting".
- Section titles: "For you", "In your portfolio", "Since you last looked".
- Row texts and empty states: as in §4.3. The plan row reuses "The plan for {periodWords()}" (the plan sticky's) and
  "{state}: awaiting approval" (the plan tile's); the decision row reuses "Decides: " (the meta line's).
- The stepper words are `uxDecSteps`'s, unchanged.

## 5. IA-2 (after the G2 stop; unit cards finalised after the owner's input)

| Unit | Shape | Routes | Shape's own gate, beyond §6 |
|---|---|---|---|
| IA-2a | Plan | `plan`, `plan/left-out`, `plan/review`, `plan/history` (§5.1) | The state stepper (Draft › Proposed › Approved › Closed). The budget and crew meters. Items, Left out, Review and History as tabs. `plan_switch_check.cjs` passes |
| IA-2b | List (card: `spec-IA-2b.md`, D-IA.61 to D-IA.66 in `rulings-5.md`; two parts, IA-2b1 and IA-2b2) | `decisions`, `findings`, `actions`, `sites`; "View all {n}" goes live on the hubs (the D5 deviation of D-IA.25 closes); aliases `portfolio/act-first` → `decisions` and `findings-*` → `findings?heading=`; the Outcomes table (D-IA.27) folds into the list component | One list component. Filters, sort and scope in the address. Cap at 10 with "Show all". Count tiles equal the list length (audit C2.3). A row has one target (D-IA.9; the queue rows' D5 deviation closes). Search indexes every object. G1's "released Actions, filtered to the plan version" gets its surface |
| IA-2c | Asset | `asset/:asset`; `assets`, `incidents` and `maintenance` as list instances; `site/:site/operations`, `/performance`, `/setup` | One timeline per asset. Each row of the Site's Operations tab has the same columns on every vertical. Performance panels follow the vertical, with the slots fixed |
| IA-2d | Drawer and record page | Every drawer's address `?drawer=<kind>:<id>` (stable ids; the inbox and the driver drawers included; Back restores it); the incident, maintenance, right and record drawers; `finding/:id`, `action/:id`; `results`, `evidence` (Coverage, Records, Imports); `site/:site/evidence` | Every drawer has an address and closes with Esc. G1's drawer nodes move onto the addressed hrefs, and its Finding surface moves to the Finding page. The stepper gains "Verified" once Results holds verdicts |
| IA-2e | Statement | `financials` (Statement, Budget & targets, Prices); `site/:site/financials`; `settings` (four tabs); the Lab's own content only (its gate is built in IA-1a, D-IA.19) | Reconciliation (the statement against the headings, all operators). Final sweep: every one of the 184 manifest routes plus `plan` resolves to a live route, an alias or not-found, and `rebase_v70.py` renders nothing routed |

### 5.1 IA-2a: the plan shape (rev 5; D-IA.43 to D-IA.48 in `rulings-2.md`, D-IA.49 to D-IA.53 in `rulings-3.md`)

**Rev 5 overrides rev 4 where they differ; read `rulings-3.md` "IA-2a handshake answers" with this section.** In short: checks run forced (`IA_FORCE_LANDED=IA-2a`, D-IA.49); the recommended stop is the end of 3(a); `crew` and `listed` are full width; L1 gains the case line (D-IA.51); `parts_identity` sets plan states (D-IA.50); the plan item's decision depth is 3 and reported only (D-IA.53); `ia_gates` runs `plan_switch_check` and uxi plants.

The owner reviewed G2 ("UI looks ok for now", `owner/owner-snapshot-guard-and-g2-2026-11-21.md`) and asked to start
IA-2a while the UI lane waits for 5c (`owner/owner-start-ia2a-2026-11-21.md`). 5c takes the lane the moment 3A7
merges, so IA-2a is cut into units that each end at a clean stop (§5.1.9). Brief: `owner/owner-ui-standing-brief-2026-11-20.md`
(right control per content, one interaction grammar, simplicity by design, honest numbers); G1 (D-IA.10).

**Where.** Branch `task/IA-2a-plan` in `/opt/assetecon/AssetOpsV1-ia2a`, from `main` at or after the merge of
`task/IA-2a-spec`. Touch `vNEXT/` only (plus its `tools/`, `walkthroughs.md` and this folder). No manifest, evaluator,
backend or `frontend/src` change. Evidence: `/opt/assetecon/evidence/IA-2a/<unit>/`. Browser checks run through
`tools/heavy-slot.sh` as §0 says. Never touch ports 5490 or 8990, or Docker.

**Mock.** The proposal page's plan shape (`Docs/design-system/ia-proposal/index.html`, §4 "4 · Plan": a title row
with Approve and Send back; the stepper "Draft › Proposed › Approved › Closed"; Budget meter, Crew-visit meter, Value;
L2 "Items: option · Site · owner · dates · spend"; L3 "Left out, and why · review against observed"; L4 versions;
tabs Items, Left out, Review, History; "Approve or Send back: dialog, toast with Undo"), and its journey "Approve the
plan" (§5: the plan at click 1, approve there). The content is the reviewed plan page (`planParts`, D-IA.20) and the
reviewed "The plan's review" section of `whatChangedScreen` (proposal §6: What changed → Plan › Review).

#### 5.1.1 Routes and tabs (D-IA.43)

| Route | Tab | `unit` | H1 · document title | Crumbs | Body |
|---|---|---|---|---|---|
| `plan` | Items | IA-1a (kept) | the reviewed title · `{title} · {operator}` | `[['Plan']]` | `shapePlan(ctx, 'items')` |
| `plan/left-out` | Left out | IA-2a | the same H1 · `Left out · {title} · {operator}` | `[['Plan','plan'],['Left out']]` | `shapePlan(ctx, 'left-out')` |
| `plan/review` | Review | IA-2a | the same H1 · `Review · {title} · {operator}` | `[['Plan','plan'],['Review']]` | `shapePlan(ctx, 'review')` |
| `plan/history` | History | IA-2a | the same H1 · `History · {title} · {operator}` | `[['Plan','plan'],['History']]` | `shapePlan(ctx, 'history')` |

- `title` and `subtitle` are the reviewed screen's (`iaLegacy('portfolio/act-first/plan')`), on every tab: the H1 names
  the object, the tab names the view (the object-page grammar, D-IA.43).
- All four: `shape: 'plan'`, `object: 'plan'`, `home: 'Plan'`, `tabGroup: 'Plan'`.
- `IA_TAB_GROUPS.Plan = ctx => [['Items','plan'],['Left out','plan/left-out'],['Review','plan/review'],['History','plan/history']]`.
- **Document title.** A route may carry `docTitle: ctx => string`. `iaScreen` adds `docTitle: route.docTitle ?
  route.docTitle(ctx) : route.title(ctx)`, and `screens.js` `render()` writes `${s.docTitle || s.title} · ${operator}`.
  The three new routes set `docTitle: ctx => \`${tab} · ${title}\``. No other route changes.
- No alias is added or changed. `portfolio/act-first/plan` → `plan` stays.

#### 5.1.2 The shape (`ia-shapes.js`, D-IA.43)

`shapePlan(ctx, tab)` returns, for Items and Left out:

```html
<section data-shape="plan">
  {p.sticky}
  <div data-level="L1">{iaPlanHead(op, p)}</div>
  <div class="layout-main-side">
    <div><div data-level="L2">{L2 of the tab}</div><div data-level="L3">{L3 of the tab}</div></div>
    <aside class="side-panel" data-level="L3">{p.switches}</aside>
  </div>
  <div data-ia-drawers>{uxDrawer('ia-plan-thresholds', 'Release thresholds', p.ap.thrBody)}</div>
</section>
```

and for Review and History (no side panel; their content does not depend on the case):

```html
<section data-shape="plan">{p.sticky}<div data-level="L1">{iaPlanHead(op, p)}</div><div data-level="L2">{L2 of the tab}</div><div data-ia-drawers>{the same drawer}</div></section>
```

`p = planParts(op)`. An empty L3 omits its region. `shapePlanInterim` is deleted in the flip commit (§5.1.9).

**The placement** (every reviewed fragment of the plan page, and where it goes):

| Fragment (part) | Tab · level |
|---|---|
| `p.sticky` (`uxPlanSticky`, unchanged) | every tab, first, outside the levels; repeats the L1 primary |
| stepper, band, release line, version notice, thresholds opener (`iaPlanHead`, §5.1.3) | every tab · L1, identical on the four |
| `p.l2` (items and their Actions, the total, "How the plan is chosen") | Items · L2 |
| `p.diff`, `p.paths` (Lakeside), `p.crew`, `p.cases` (Lakeside) | Items · L3, in that order |
| "Left out of the plan, and why": `uxSecA('Left out of the plan, and why', p.leftAns, p.leftBody, true)` (open) | Left out · L2 |
| `p.listed`, `p.returned` (when any) | Left out · L3, in that order |
| `whatChangedParts(op).review` ("The plan's review") | Review · L2 |
| `iaPlanHistory(op)` (§5.1.4) | History · L2 |
| `p.switches` ("Try another case") | Items and Left out · the side panel |
| `p.ap.thrBody` (release thresholds) | the drawer `ia-plan-thresholds`, every tab |
| `p.ap.status`, `p.ap.meters`, `p.ap.note` (the approval panel's state block, legacy meters, recording note) | not on the IA page (the band carries state and meters; the Approve dialog says "Recorded under"); `MOCK DEVIATION` D2, R757 |
| `p.ap.kv` (Opened, Proposed) | its facts are History's rows |

#### 5.1.3 L1: the plan's header (D-IA.44, D-IA.45)

`iaPlanHead(op, p)` returns
`${iaPlanStepper(op)}${iaPlanBand(op, p.P, p.budget)}${p.ap.releases}${p.ap.notice}{case line, D-IA.51}<p class="ia-plan-rules">${uxOpener('ia-plan-thresholds', 'Release thresholds', 'ux-link')}</p>`.

- **The stepper.** `const IA_PLAN_STEPS = ['DRAFT', 'PROPOSED', 'APPROVED', 'CLOSED']`. `iaPlanSteps(state)` (pure)
  returns `{ steps: IA_PLAN_STEPS.map(s => STATE_WORD[s]), cur }`, `cur` = 1 for `REVISED`, else
  `IA_PLAN_STEPS.indexOf(state)`, and throws `plan state <state> has no step` when that is −1. `iaPlanStepper(op)` reads
  `uxPlanState(op).state` and returns `<ol class="ux-dsteps ia-plan-steps" aria-label="Where this plan is">` with one
  `<li>` per step, `is-done` before `cur`, `is-current` and `aria-current="step"` at `cur` (the markup of `uxDecStatus`).
- **The band.** `iaPlanBand(op, P, budget)` returns
  `<section class="ux-planband" aria-label="The plan at a glance"><div class="heroes ux-kpis">${B.spend}${iaCrewTiles(op, P) || B.crew}${B.value}</div>${B.act}</section>`,
  `B = uxPlanBandParts(op, P, budget)` (§5.1.5). The budget meter is the spend tile's reviewed `uxMeterBar`.
- **The crew meters.** `iaCrewTiles(op, P)`: one tile per month of `crewByMonth(op, P)` (each month with a stated
  limit), `''` when there is none:
  `uxKpi(\`${cap(o.crewWord)} used${ms.length > 1 ? \`, ${m.month}\` : ''}\`, \`${num(m.used)} <small>of ${num(m.limit)}</small>\`, [], uxMeterBar(m.used, m.limit, \`${num(m.used)} of ${num(m.limit)} ${o.crewWord}${ms.length > 1 ? \` in ${m.month}\` : ''}\`))`.
  Lakeside has two months, so its L1 holds 4 tiles (spend, November, December, value): the L1 cap of 4 holds for every
  operator (period of at most two months).
- **State.** Every builder reads the plan's state through `uxPlanState(op)` and the one-source helpers
  (`planApprovedIds`, `planReleasedItem`, `releaseShown`, `itemStateOf`, `waitingSummary`; review r4 M1, D-IA.24).
  `PSTATE()` is read only for fields no act changes: `period`, `opened`, `proposed` and the proposed `version`.
- **The primary.** "Approve version {n}" in the band's act row while `PROPOSED`; the sticky repeats it with the same
  act (D-IA.23). Neither moves into the title row (R758).

#### 5.1.4 History (D-IA.47)

`iaPlanHistory(op)` returns `sec('Versions and approvals', body, \`Version ${num(S.version)}, ${STATE_WORD[S.state].toLowerCase()}\`)`,
`S = uxPlanState(op)`. `body` is `<ul class="list ia-plan-history">` + rows, newest first, + `<p class="note">Changes made
here are shown in this demonstration only.</p>`:
1. each entry of `uxMock().log` with `op === op` and `key` `approve-plan` or `send-back`, newest first:
   `<li data-ia-hist="log:{i}">{toast} <small>{by} · {hhmm(at)}</small></li>` (the inbox row's form; `i` counts within
   these entries);
2. `<li data-ia-hist="proposed">Version {num(PSTATE().version)} proposed <small>The system · {fdate(PSTATE().proposed)}</small></li>`;
3. `<li data-ia-hist="opened">Opened within the executive’s limits <small>The system · {fdate(PSTATE().opened)}</small></li>`.

#### 5.1.5 The parts splits, byte-identical (D-IA.46)

Each reviewed function below returns exactly today's string, proven by `tools/parts_identity.cjs` (§5.1.8):
- `planParts(op)` keeps `sticky`, `band`, `l2`, `l3`, `aside` and adds `P`, `budget`, `diff`, `paths`, `crew`,
  `listed`, `leftBody`, `leftAns`, `left`, `cases`, `returned`, `switches`, `ap`. `left` is
  `uxSecAx('Left out of the plan, and why', leftBody, leftAns)`; `l3` is today's template over `diff`, `paths`,
  `crew`, `listed`, `left`, `cases`, `returned`; `aside` is `${approvalPanel(op, P, budget)}${switches}`.
- `approvalParts(op, P, budget)` (new, beside `approvalPanel`) returns `{ status, kv, meters, releases, notice, note,
  thrBody, thresholds }` (`thresholds` = `<h3 class="h3s">Release thresholds</h3>${thrBody}`, `thrBody` =
  `thresholdsKv(op) + ILLUS`); `approvalPanel` joins them in today's template.
- `uxPlanBandParts(op, P, budget)` (new, beside `uxPlanBand`) returns `{ spend, crew, value, act }`; `uxPlanBand`
  joins them in today's template.
- `whatChangedParts(op)` (new) returns `{ kpis, actions, review, chosen, rightsM, rights }`; `whatChangedScreen()`
  joins them in today's template.

Untouched (no line of the diff): `uxPlanSticky`, `uxPlanStateChip`, `uxPlanActions`, `uxPlanState`, `UX_ACTS`,
`uxActOpen`, `uxActDo`, `uxFocusState`, `uxPlanDiff`, `uxItemRow`, `planStatusBlock`, `thresholdsKv`, `crewByMonth`,
`crewMeters`, `releaseOf`, `waitingSummary`, the inbox builders, every hub and decision part.

#### 5.1.6 Copy (exact; nothing else is new)

- Tabs: "Items", "Left out", "Review", "History". Document titles: §5.1.1.
- Stepper: the steps are `STATE_WORD`'s "Draft", "Proposed", "Approved", "Closed"; `aria-label` "Where this plan is".
- Crew tiles: label "{Crew word} used" or "{Crew word} used, {Month}" (`crewMeters`' own label); value "{used} of
  {limit}"; meter name "{used} of {limit} {crew word}" or "… in {Month}".
- Opener and drawer title: "Release thresholds".
- Case line (only when the case is not the proposal): "Showing the case you chose: {label}. Change the case" (D-IA.51).
- History: title "Versions and approvals"; sub "Version {n}, {state word in lower case}"; rows "Version {n} proposed",
  "Opened within the executive’s limits", "The system · {date}"; note "Changes made here are shown in this demonstration
  only."

#### 5.1.7 What stays byte-identical, and what changes (D-IA.46)

**Byte-identical** (`parts_identity.cjs`, every case below, `UX_QN` reset): `planScreen()` for every operator × switch
case × plan state {as proposed, approved, sent back to draft} × {default, `?state=no-recommendation`};
`whatChangedScreen()` for every operator × the three plan states × both previews; every existing job (hub, Site,
decision). The legacy plan page, Act first and What changed stay registered for the review select, unchanged.
Also unchanged: the Approve and Send back dialogs, the toast with Undo, focus after an act, the act log, the inbox's
plan row (`#/plan`), the badge rule, the Overview's plan tile and its "Review the plan" link.

**Changes:** the IA `plan` page (the interim, §2.6) becomes the plan shape; three tab routes; the L1 gains the stepper
and one crew meter per month; the approval panel leaves the page (R757); Left out, Listed beside and the returned
Actions move to the Left out tab; "The plan's review" appears on Review; History is new; tabbed routes may set
`docTitle`; `ia.css` gains `.ia-plan-steps{margin:0 0 var(--s3,12px)}` and `.ia-plan-rules{margin:var(--s2,8px) 0 0}` only.

#### 5.1.8 Gates and plants that must fail (D-IA.48)

§6 applies whole. Beyond it:

| Check | Asserts | Plants (each must fail) |
|---|---|---|
| `tools/plan_shape_check.cjs` (new, jsdom, run by `ia_gates.cjs`) | the four tabs, in order, on each plan route; one stepper in L1 with the four steps, `is-done` before the current only, the current from the manifest's own state; L1 identical on the four tabs, also after a non-default case is picked on Items; the placement table (§5.1.2); no `.approval`, no `.meter` on any IA plan route; side panel on Items and Left out only; the thresholds opener and its closed drawer; nothing hidden by a cap (`[data-ux-over]`) on Items, Left out, Review; L1's `.approval-releases` equals the one in `planScreen()` in the same state | `PLAN_PLANT=tabs` (History dropped from the group), `place` (the left-out section also on Items), `l1` (History's L1 without the release line), `approval` (the panel back in the Items aside), `thr` (no drawer), `stepdone` (no `is-done`), `cap` (`uxCapLists` caps at 1) |
| `count_check.cjs` (plan block, D-IA.24) | per operator, on the four plan routes: as proposed, then after Approve, after its Undo, after Send back (reason and trade-off filled): the stepper's current step, the band and sticky chips, the inbox plan row, the badge and History's first row agree with the state the check derives from `sessionStorage['l4-mock']` and the manifest | `COUNT_PLANT=planstep` (`iaPlanStepper` reads `PSTATE()`), `planhist` (History ignores the log) |
| `shape_check.cjs` | item 4 reads `docTitle` where set; new item 10: the routes of one tab group have distinct document titles | `SHAPE_PLANT=doctitle` (`docTitle` ignored) |
| `click_depth_check.cjs` | new surfaces `plan tab: Left out`, `Review`, `History`, each ≤ 2 via `any` | `G1_PLANT=plantabs` (the Plan group returns Items only) |
| `plan_switch_check.cjs` (retargeted, §2.1) | the budget figure from L1's spend tile; one crew tile with one meter per month with a stated limit, used of limit as the evaluator's; the release line from L1; Actions from `plan` and `plan/left-out` under the same switches | `PSW_PLANT=crewtile` (the last month's tile dropped; host Lakeside), `release` (the line of the default case), `leftout` (no `p.returned`); hosts of the last two: Lakeside 6500/No, Harvest No, Metro No |
| `ux_interaction_check.cjs` | the plan block's `r.n >= 4` becomes `>= 2` on `plan`, plus `plan/left-out` with at least 2 answer-titled sections, each answered; the M1 "every page agrees after Approve" routes gain the three tabs; on a tab too short to scroll the band away, the band's Approve stays in view (D-IA.48) | `UXI_PLANT=planans` (Left out's answers emptied), `planwait` (History's sub says "awaiting approval" after Approve) |
| `ia_shots.cjs` (heavy slot) | the four routes join its route list (fit, truncate and crumbs clauses, D-IA.37 to D-IA.41); at 1440 × 900 and 1280 × 720 the band's Approve is inside the first viewport | `SHOTS_PLANT=approvefold` (a 900 px block before the band) |

`after_render_check` and `shape_check` items 1 to 9 cover the new routes by construction (every live route).

**Screenshots** (`ia_shots.cjs`, to the evidence folder): the four routes × three operators × light and dark × 1440 ×
900, 1280 × 720, 390 × 844; on `plan` at 1440 and 390 (light): the Approve dialog open, after Approve (stepper on
Approved, the toast), after Send back (Draft); the thresholds drawer open at 1440 and 390; Lakeside 6500/No on Left out
at 1440 (the returned Actions).

#### 5.1.9 Units, size and the clean stop (D-IA.48)

**Size: 3 units** (5 commits), one branch, one review at the end (discovery depth, W5). Within the 6-unit cap.

| Unit | Commits | Content | Visible change |
|---|---|---|---|
| 1 | 1 | The four parts splits (§5.1.5); `parts_identity.cjs` gains the plan states and `whatChangedScreen` | none |
| 2 | 1 to 2 | The checks first (W2): `plan_shape_check.cjs`, the `count_check` plan block, `shape_check` item 10, the G1 surfaces, the `ia_shots` clause, the runner's rows; each new assertion is dormant by default (prints `IA-2a not landed; dormant`), runs under `IA_FORCE_LANDED=IA-2a` against a stub (D-IA.49), and `ia_gates` fails any `dormant` output after the flip, and item 10 runs at once (the Portfolio group passes) | none |
| 3 | 2 | (a) The builders (§5.1.2 to §5.1.4), the three routes with `unit: 'IA-2a'`, `docTitle`, `IA_TAB_GROUPS.Plan`, `ia.css`: not live, so nothing shows. (b) The flip: `plan` renders `shapePlan(ctx, 'items')`, `shapePlanInterim` deleted, `'IA-2a'` added to `IA_LANDED`; `plan_switch_check` and uxi retargeted with their plants shown failing first; `walkthroughs.md` (the plan's tabs); register rows R757 to R760; screenshots; packet | the plan shape |

**The clean stop.** Every commit boundary before 3(b) leaves `main`'s screens as they are and every gate green, so the
branch can pause there. If 3A7 merges during IA-2a: finish the commit in hand (never stop inside one), run the fast
check-all, push, and write `Stopped after <unit/commit> at <sha>; resume at <next>` at the top of `packet-IA-2a.md`.
The lane then goes to 5c. The recommended stop is the end of 3(a) (rev 5, D-IA.49: plants can only fail once the builders exist; unit 2 is "written and mutation-tested"). Unit 2 never merges alone; unit 1 alone may, after a verification review. The stop line names the next-resume sha and says `IA_LANDED` has no IA-2a. 3(b) never merges without unit 3(a) and the
discovery review. 5c touches no `vNEXT/` file, so neither lane waits on the other's merge.

#### 5.1.10 Done, deviations, packet

**IA-2a is done when**, beyond §6: the four plan routes are live from one shape; `plan_switch_check` passes with its
three plants failing; `parts_identity.cjs` reports every `planScreen` and `whatChangedScreen` case byte-identical; G1
prints the plan (≤ 1), each plan tab (≤ 2), the plan item's decision (3, reported, D-IA.53) and the proposed plan via the inbox (≤ 2);
the Approve journey reads dialog, toast with Undo, stepper on Approved, badge down by one, History's new first row, on
every tab; every new plant fails in `ia_gates.cjs`' table.

**`MOCK DEVIATION`s** (rows in `.agent/mock-departure-register.md`, a line each in the packet):
- **R757** D2: the approval panel is not on the plan page; its parts are placed once (§5.1.2).
- **R758** D2: Approve and Send back sit in the band's act row under the meters, not in the title row of the proposal's
  figure (inside the first viewport at 1440 and 1280; the sticky repeats them).
- **R759** D1: Review's "Observed change" and "Review" read "Not yet" while the period is open (reviewed copy).
- **R760** D5, resolving IA-2d: History has no per-version drawer (the figure's "L4 versions") and no address per entry.

**Packet** `specs/IA-1-shape-rebuild/packet-IA-2a.md` (§8's list), plus the stop line if any, the `parts_identity`
counts per function and state, and the L1 tile count per operator.

## 6. Every unit's gate (D-IA.12, D-IA.14)

Before review, all of these pass, with their output in the packet:
1. `node tools/ia_gates.cjs`: `shape_check.cjs`, `click_depth_check.cjs`, `after_render_check.cjs` and (from IA-1b)
   `count_check.cjs` and `outcomes_table_check.cjs` pass, and every plant of every landed unit fails (§2.5, §2.8).
2. The byte-identity scripts: `planParts` (IA-1a); `uxOverviewParts` and `uxSiteParts` for every operator and Site
   (IA-1b); `uxDecisionSlots` for every decision (IA-1c); each in the default state and under
   `?state=no-recommendation`, with `UX_QN` reset.
3. (IA-1b onwards) `shell_check.cjs` on `tools/ia_crawl.cjs`, with `SHELL_PLANT=1` shown failing first.
4. `ux_interaction_check.cjs` (its overview budget retargeted per D-IA.25, `UXI_PLANT=block7` and `UXI_PLANT=tall`
   shown failing first), `shell_check.cjs`, `vocab_check.cjs`, `copy_check.cjs`, `render_text.cjs` (differences
   listed), `design_lint.cjs` (and `LINT_PLANT=1` fails), `plan_switch_check.cjs`, `hand_typed_scan.py`.
5. (IA-1b onwards, heavy slot) `g3_trends.cjs` on the hub root, with `G3_PLANT=clip` and `G3_PLANT=root` failing;
   `ia_shots.cjs` with the headline rule and `SHOTS_PLANT=headline` failing.
6. `python3 ../check_manifest.py`.
7. Screenshots at 1440 × 900, 1280 × 720 and 390 × 844, for the three operators in light and dark, of every route the
   unit adds (IA-1c: also the inbox open, and one decision before and after Choose). They go to the evidence folder.

A unit that changes an existing check shows that check failing on a planted violation first.

**IA-1b is done when**, beyond the above: the empty hash opens `#/portfolio` (R34); the "Still to be rebuilt" popover
reads as D-IA.30; the `portfolio/outcomes-by-site`, `mini`, `cold` and `ev` aliases resolve per D-IA.28; G1 prints the
Plan (≤ 1), every Site Overview (≤ 2) and every Site's largest-driver drawer (≤ 3, or `n/a`).
**IA-1c is done when**, beyond the above: G1 prints every queue decision (≤ 1 via queue), every waiting decision and the
proposed plan (≤ 2 via inbox) and every plan item's decision (≤ 2); the recommendation aliases resolve per D-IA.28;
P7 holds in its three cases.

## 7. Scope limits

- No figure, manifest or evaluator change. A figure that disagrees between two screens is reported to the Architect,
  never adjusted on screen.
- No new copy beyond §2.7, §3.3, §4.4 and §5.1.6, plus the labels the reused functions already have. A missing string is
  raised as a question, not invented. The review bar is mock tooling (D-IA.30).
- Reviewed functions change only as D-IA.22 (the parts splits and the one named sticky fix), D-IA.24 (the act log in
  `uxActDo`), D-IA.28 (`iaPattern`, the aliases) and, for IA-2a, D-IA.46 (the four plan splits, the `docTitle`
  line in `screens.js`) say.
- No change to `frontend/src`. The live product keeps its rail (O1).
- The old screens stay registered for the review-bar select until IA-2e. None may be linked from a live IA route.
- `USER_REVIEW_REQUIRED: true` (UI/UX). After IA-1c, stop for the owner (D-IA.11).

**Known `MOCK DEVIATION`s, decided here** (each gets its row in `.agent/mock-departure-register.md` and a line in the
packet):
- D2, IA-1b: the Overview drops "More in the tabs" (the frame's tabs replace it; D-IA.25).
- D5, IA-1b, resolving IA-2b: no "Act first ›" and no "View all {n}" on the Overview queue (D-IA.25).
- D5, IA-1b and IA-1c, resolving IA-2b: queue rows keep "Why" and the action link beside the row (D-IA.9's one-target
  row; R26).
- D5, IA-1c, resolving IA-2d: the inbox and every other drawer have no address (D-IA.21).

## 8. Packet

Write the packet in `specs/IA-1-shape-rebuild/packet-<unit>.md`, at most 3k tokens. It holds:
- the module-path line;
- the checks with their real output, and `ia_gates.cjs`' table with every plant failing;
- the byte-identity counts (§6 item 2), and the one sticky diff (D-IA.22);
- the G1 depth table (operator · surface · depth · path), with `n/a` rows for Sites without a driver against target
  and the line that the plan-version Actions surface is unmeasured until IA-2b (D-IA.29);
- the overview budget per operator (blocks, px at 1440);
- the `render_text` differences, if any (P15), and the two kept red marks on Demand & capacity (D-IA.29);
- the screenshots' folder;
- the count of mid-build questions (RULES §4, item 7);
- known `MOCK DEVIATION`s, each with its category.
