# IA-1 handshake (one combined round, RULES §4 items 6 and 7)

The Reviewer writes questions after reading `spec.md`, `reviewer-guide.md` and `rulings.md`. The Implementer writes
questions after a pre-flight of `spec.md` against the accepted head of `task/uiux-design-model`. Both write them here
in one batch:
- Number them R1, R2 … for the Reviewer and I1, I2 … for the Implementer.
- Each question cites its spec section, says what is unclear and what answer the writer expects.
- Mark a question **(done)** when its answer changes what counts as done.

The Architect answers every question once, in `rulings.md` under "Handshake answers (round 1)", and folds the
answers into `spec.md`. The handshake ends when neither section has an open question. Coding starts only then.

## Reviewer questions

Unit IA-1a, round 1 (one agent in both roles, 2026-11-20). Code read: `task/uiux-design-model` at `786e1f905`
(`vNEXT/` below). Severity: **High** blocks coding; Medium and Low need an answer, not a redesign.

**R1 (High, done). What IA-1a's own gates assert, given what has landed in IA-1a** (spec §2.2, §2.5, §2.6; D-IA.12).
- In IA-1a only `plan` is a live IA route. `portfolio` belongs to IA-1b (§3.2), yet the rail lists Portfolio as
  unit IA-1a, and the crawl and the G1 walk both start at `#/portfolio`.
- So every IA-1a crawl starts on a legacy screen. It also reaches unlanded routes from the plan itself:
  - the rail's Portfolio link;
  - the breadcrumb;
  - the scope menu's Sites (`site/<key>`, IA-1b);
  - the plan's own links to `decision/*` and `site/*` (`loop-portfolio.js` planScreen's item rows and its "Left
    out" table).
- Under §2.5 item 2, `shape_check` fails by construction in IA-1a. The plan's depth-1 path would run through the
  legacy Overview's plan tile (`portfolio/act-first/plan`, via the alias).
- Expected answer, per unit:
  - the crawl's start route (for example `#/plan` in IA-1a, `#/portfolio` from IA-1b);
  - what the Portfolio rail item is in IA-1a (an unavailable root, or a link to the legacy Overview);
  - which assertions IA-1a must pass, and which are built but vacuous until IA-1b.

**R2 (High, done). How a reused function's link to an unlanded or legacy route is suppressed** (spec §1, §2.4,
§7; reviewer guide, Risks).
- Reused markup links through `link()` (`screens.js:29`) to routes that have not landed: `decision/*` and
  `site/*` from the plan; `portfolio` from `uxNotFound`; `portfolio/act-first/plan` from the Overview and the decision
  page.
- Today `uxShell` unlinks review-only targets after render (`loop-ux.js`, the `uxIsClassic` replace at the end of
  `uxShell`). `uxShell` is not called for IA routes (§2.4), and `iaFinish` lists five passes, none of which does this.
- The reviewer guide says "fixed at the link, never by an alias", but a link to an IA-1c decision cannot be fixed at
  the link in IA-1a.
- Expected answer: one named mechanism. Two candidates:
  1. a sixth pass in `iaFinish` that renders an `a[href]` as plain text unless its target is live, run before
     insertion;
  2. an `iaLink` that every reused function calls instead of `link()`.
- Also: whether a link to an alias whose target is live passes the crawl, or must be rewritten to the new route.

**R3 (High, done). The after-render check and its plant cannot fail as written** (spec §2.5; D-IA.13).
- `AR_PLANT=1` calls `plainWords(canvas)` after insertion. `iaFinish` has already applied `plainWords`, and
  `plainWords` writes a node only when its value changes (`loop-core.js:401-402`). The second pass is a no-op and
  produces no mutation. D-IA.13's wording, "re-enables PLAIN_WORDS after render", has the same flaw.
- The observer must be attached before the first post-insert mutation. `render()` calls `afterRender`
  synchronously, so an observer attached after `render()` returns misses everything the plant does. The spec needs a
  hook inside `iaRender`, for example `window.__iaInserted(canvas)`.
- §2.4 keeps `uxBrandSwitch` in `brandAndListenersOnly`. It inserts the brand select and the MOCK DEVIATION marks
  into `.reviewbar`, which sits inside `#app`. Observing `#app` therefore fails on legitimate code.
- Expected answer:
  - under the plant, `iaFinish` skips `plainWords` and the plant runs it after insertion, on a route that
    provably contains a word `PLAIN_WORDS` rewrites (the plant asserts at least one mutation);
  - the hook's name;
  - the observed root: the frame, not `#app`, or the review bar built in `render()` as a string.

**R4 (High, done). The G1 check is satisfied by the rail, so its plant cannot fail** (spec §2.5; D-IA.10).
- The walk follows every `a[href^="#/"]`, which includes the rail. From IA-1b onwards the rail's Plan item gives the
  plan depth 1 from any framed page. `G1_PLANT=1`, which removes the plan tile's link, then changes nothing, so the
  plant passes.
- D-IA.10's limits are path-specific: "1 from the Overview queue or plan tile", "2 through the inbox". A
  shortest-path BFS over all links cannot verify a path-specific limit.
- Expected answer, either:
  - limits measured with rail links excluded, or measured per named entry (queue, tile, inbox), with the inbox
    limit computed only over inbox edges; or
  - a plant that removes a link the rail cannot replace.

  Also, the IA-1a value of the G1 table (see R1).

**R5 (High, done). The stub plant passes, because stubs already resolve to not-found** (spec §2.5 item 2 and
item 4).
- `resolveScreen` turns any `stub: true` screen into `not-found` (`loop-core.js:340`), and the crawl accepts
  `not-found`. A crawl that classifies the route it lands on therefore sees not-found for `site/kisiwa/health`, and
  `SHAPE_PLANT=1` passes.
- The plant also targets the Portfolio Overview, which is not live in IA-1a (R1).
- Expected answer:
  - the crawl classifies each link by its href target (through `IA_ROUTES` and the aliases), never by the screen
    rendered;
  - a link whose target is not-found is a failure (not-found is reached only by a typed hash);
  - the plant's host page per unit (`plan` in IA-1a).

**R6 (High, done). The developer-only Lab gate** (spec §2.3; D-IA.7, D-IA.12; reviewer guide P8).
- §2.1 says "every other route renders as today". `lab` is a registered legacy screen, so `#/lab` renders the Lab
  with Developer access off. The review-bar select also lists it.
- P8 expects not-found, or "the review select only". D-IA.7 says the Lab is "reachable only by a person who holds
  the developer grant". D-IA.12 schedules "the Lab gate" in IA-2e, while §2.3 builds the footer in IA-1a.
- The footer's target in IA-1a is the legacy `lab` route, outside `IA_ROUTES`. A crawl with the switch on
  therefore fails, and a crawl with it off never sees the footer.
- None of the three checks asserts the gate, so P8 is untested.
- Expected answer:
  - in IA-1a, whether `#/lab` with the switch off resolves to not-found, and whether the review-bar select omits
    the Lab;
  - the footer's target, and whether the crawl skips it;
  - one automated assertion in `shape_check`: switch off, no Lab link and `#/lab` not-found; switch on, the
    footer item "Simulator Lab" present.

**R7 (Medium). Where the query lives** (spec §2.2 ctx, §4.3; D-IA.6, D-IA.9).
- `currentScreen()` takes the whole hash as the route id (`screens.js:943`), so `#/portfolio?scope=all` is not
  found today.
- The existing `?state=no-recommendation` uses `location.search`, which reloads the page.
- Expected answer: the scope and drawer query sit in the hash (`#/route?scope=…&drawer=…`); `resolveScreen` splits
  them off; and the crawl and depth walk treat the query as part of the route identity, or not.

**R8 (Medium). What element `iaRender` replaces** (spec §2.3, §2.4 step 4).
- `iaFrame` returns the rail, the top bar, the header, the tabs and the body. In the DOM today the rail and the top
  bar sit outside `.canvas` (`screens.js:996`: `.shell > rail + main.workspace > header.topbar + .canvas`), so
  "replaces `#app .canvas`" would nest the rail inside the workspace.
- Expected answer: `iaRender` replaces `#app .shell` (or a named frame root). For IA routes, `render()` writes only
  the review bar and an empty root first, never a legacy shell that is then replaced.

**R9 (Medium). The search palette reaches legacy screens** (spec §2.3 item 2; §1 "no v7.0 screen reachable").
- "Keep today's palette": `uxCommands()` (`loop-ux.js`) indexes every old Portfolio tab (`PTABS`, including
  `portfolio/act-first`, `what-changed` and `scope`), `portfolio/act-first/plan`, `globalfinancials` and
  `globalevidence`.
- `[data-go]` exists only inside the palette's list, which is empty until the palette is opened, so the crawl
  never sees it.
- Expected answer:
  - in IA-1a, the palette lists only live IA routes, or it is exempt and stated so;
  - whether the crawl opens it.

**R10 (Medium, done). The checks inside `run-audit.sh`** (spec §2.5, last line).
- `run-audit.sh` refuses to run without `CHROME`, `PW` and a heavy slot, and runs `audit.mjs`. Adding three jsdom
  checks there makes them depend on a browser setup they do not need.
- A run where `CHROME` is unset would silently skip them.
- Expected answer: a jsdom runner (or the packet's command list) that runs them standalone with their plants, and
  `run-audit.sh` calls that runner.

**R11 (Low). Operator ids.**
- §2.5 names `lakeside-power`, `harvest-cold` and `metro-bus`, which are tenant ids.
- The code and every existing check key operators as `lakeside`, `harvest` and `metro` (`LS.op`, `sessionStorage`
  `l4-op`).
- Expected answer: confirm the check uses the `LS.op` keys and prints the operator name.

**R12 (Low). Route parameters for "every live route"** (spec §2.5 items 1 and 3).
- Expected answer: `:site` is enumerated over `OPS[op].sites` and `:dec` over the `DEC` entries of that operator's
  Sites; other operators' instances are never visited.

**R13 (Low). The scope switch on a non-hub page in IA-1a** (spec §2.3 item 1; D-IA.6).
- On `plan`, choosing "All sites" or a group has no defined effect. The group ids for `?scope=group:<id>` are not
  given.
- Expected answer:
  - the group id form (for example the vertical key);
  - on a non-hub page, the choice is kept in the address only.

**R14 (Low). "No dispatched user event caused"** (spec §2.5, after-render).
- The check as written only waits for idle; it dispatches no event, so the allowed-attribute clause is never
  exercised.
- Expected answer: either it also opens one `details` and one drawer per route and asserts only the allowed
  attributes change, or the clause is dropped.

**R15 (Low). The top bar's other controls** (spec §2.3).
- The list omits today's theme toggle (`themeToggle()`, `screens.js:996`).
- Today's search button reads "Find a screen", relabelled after render by `uxSearchLabel`.
- Expected answer: the theme toggle stays, in its place; the search text is baked into the frame markup and
  `uxSearchLabel` is not called for IA routes.

## Implementer pre-flight

Read against `task/uiux-design-model` at `786e1f905`. The worktree there also holds uncommitted fix-round edits
(`loop-portfolio.js`, `loop-ux.js`, `ux.css`, `index.html`), so cited lines are already moving (`uxPlanSticky`
`1019` → `1030`).

**Cited anchors at `786e1f905`.**
- Correct:
  - `screens.js:998` `render()`;
  - `loop-core.js:408` `afterRender`;
  - `loop-portfolio.js:465` `planScreen`;
  - `loop-ux.js:323` `uxOverview`;
  - `loop-site.js:7` `siteOverview`;
  - `loop-site.js:52` `decisionScreen`.
- Off by a little:
  - `resolveScreen` is at `loop-core.js:338`, not `:340`;
  - the injected top bar (`uxChrome`) is at `loop-ux.js:472`, not `:471`.
- `NavRail.tsx` has the "Not available yet" constant and `data-rail-unavailable`, as cited.

**What is reused, at a glance.**
- **As is:**
  - `planScreen` and the functions it calls;
  - `periodChip`, `themeToggle` and the avatar;
  - `tagReplay`, `plainWords`, `uxDedupeUnits` and `uxFixSigns`. Each takes a root and walks a detached
    `<template>` fragment as written.
  - the palette UI;
  - `uxDrawer` (IA-1c).
- **Only after a refactor:**
  - `uxScopeLine` (P2);
  - `uxChrome`'s scope switch and period menu (P3);
  - `uxSearchLabel` and `uxBrandSwitch` (P3, R3);
  - the `uxShell` behaviours the plan relies on (P5).
- **New:** the rail, the registry and the three checks.

**P1 (Medium). Pin the base.** Name the accepted head's SHA in the spec, and cite functions by name, not by line.
The UI branch is mid-fix-round, and its lines shift while IA-1a is being built.

**P2 (Medium, done). `uxScopeLine` cannot run on a detached fragment** (spec §2.4 step 3.5).
- `loop-core.js:411` takes no root. It reads `document.querySelector('.canvas')`, `currentScreen().noFigures` and
  `document.querySelector('.topbar .snap-pending')`, which it moves into the canvas.
- Expected answer: the implementer may change it to `uxScopeLine(root, screen)`, with the legacy call site passing
  the canvas, and with the pending chip read from the fragment's own top bar.
- The order also changes from today's (`tagReplay`, `uxScopeLine`, `plainWords` …) to §2.4's (`uxScopeLine`
  last). Expected answer: either the order is kept, or `render_text` differences are listed in the packet.

**P3 (Medium, done). "The frame renders what they injected" against "nothing re-typed"** (spec §2.4; reviewer
guide, First checks 2).
- These functions mutate the live DOM after render:
  - `uxChrome` (scope switch, period `<details>`);
  - `uxSearchLabel`;
  - `uxBrandSwitch` (the review bar, including D2 and D5 marks keyed on `#/portfolio/act-first/plan` and
    `#/portfolio`).
- The frame can get their markup only in one of two ways:
  1. refactor each into a string builder that both the legacy path and the frame call;
  2. copy the markup, which the reviewer guide forbids.
- Expected answer: option 1, with the D5 mark's route test extended to `#/plan`.

**P4 (High, done). The plan interim fails `shape_check` by construction** (spec §2.6; §2.5 item 1).
- "At most one `button.primary` per region": the approve action renders twice, once in `uxPlanBand`
  (`loop-ux.js:383`) and once in `uxPlanSticky` (`:1019`). Both are "Approve version N", and both fall in L1 (band
  and approve bar).
- `planScreen` returns one string in a two-column `layout-main-side`, with the approval panel and the "Try another
  case" switches in the `aside`. L1, L2 and L3 can therefore be marked only in one of two ways:
  1. `planScreen` returns slots (an edit to reviewed code);
  2. the string is wrapped, which breaks the two-column layout.
- Six sections have no level in §2.6:
  - "Two ways to restore Mto's inverter";
  - crew visits;
  - "All four cases";
  - "Actions that return to their creator";
  - the switches;
  - the side approval panel.
- Expected answer:
  - may `planScreen` return `{l1, l2, l3, aside}` (the legacy route joins them);
  - the level of each unassigned section;
  - whether the sticky duplicate (`[data-ux-sticky]`) is exempt from the one-primary rule, or dropped.

**P5 (Medium, done). What the plan loses when `uxShell` is skipped** (spec §2.4).
- `uxShell` does three things for `portfolio/act-first/plan` today:
  1. caps long lists (`uxCapLists`, with "Show all");
  2. unlinks review-only links;
  3. schedules `uxStickyTick`. Its `hashchange` listener still fires, 50 ms later, and toggles `is-on` on a `div`.
     In a browser that is a class mutation on an element that is neither a `details` nor a `button` (reviewer
     probe P3), though jsdom never shows it, because its rects are zero.
- Expected answer:
  - `uxCapLists` moves into `iaFinish` (before insertion);
  - the unlinking is R2's mechanism;
  - the sticky toggle is allowed, as a scroll-caused class change, in both the check and P3.

**P6 (Medium). Existing checks hard-code `portfolio/act-first/plan`** (spec §6 item 4; D-IA.14).
- The checks that do:
  - `plan_switch_check.cjs` (five boots);
  - `ux_interaction_check.cjs:447`, `:483`;
  - `design_lint.cjs:15`;
  - `audit.mjs`;
  - `rendered_strings.cjs`.
- Once the alias is live, these boot the framed plan, without `.ux-scope-sw` or the legacy top bar.
- Expected answer:
  - they may be retargeted to `plan`, and the retargeting does not count as "changing a check" (no plant-first
    needed);
  - any assertion on legacy chrome is replaced by the frame's equivalent, under the plant-first rule.

**P7 (Low). One crawler.** `shell_check.cjs` already crawls with the same jsdom boot: S5 (no stub) and S7 (no
review-only link). Expected answer: a shared `tools/ia_crawl.cjs` module, used by `shape_check`,
`click_depth_check` and `shell_check`, rather than a third copy.

**P8 (Medium). Two alias tables** (spec §2.2; `loop-core.js:337`).
- `ALIAS` already maps `financials`, `cold-financials` and `ev-financials` to `site/<k>/economics`. `IA_ALIASES`
  maps the same ids to `site/:site/financials` (IA-2e).
- Parameterised entries (`recommendation` → the decision on that Finding; `site/:site/economics`) are not
  `{old: new}` strings.
- Expected answer:
  - `IA_ALIASES` is resolved first, and only when live;
  - otherwise `ALIAS` applies, with no chaining;
  - values may be functions of the parameters.

**P9 (Medium). Not-found in the frame.** `not-found` is a legacy `addL` screen drawn in the legacy shell, with the
old rail. Expected answer: in IA-1a it is registered in `IA_ROUTES` (shape `frame`, unit IA-1a), so that an unknown
hash keeps the new menu.

**P10 (Low). Bundle order.**
- `ia-routes.js` and `ia-shapes.js` go after `loop-ux.js` and before `loop-init.js`, which calls `render()` last.
  That order works.
- Expected answer for `ia.css`: does it go between `ux.css` and `brand.css`? `brand.css` is last and overrides
  tokens.

**P11 (Low). `afterRender` also marks `.scroll-region` with `scrolls`.** That is a class change on a `div` inside the
frame. Expected answer: it is part of `brandAndListenersOnly`, and the check allows it as layout-caused. The
alternative is to move it to a CSS-only rule.

## IA-1b/IA-1c reviewer questions

**Answered** (Architect, 2026-11-20): `rulings.md`, "IA-1b/IA-1c handshake answers" (D-IA.21 to D-IA.30, OQ-IA.1 and
OQ-IA.2), folded into `spec.md` rev 3 and `reviewer-guide.md` rev 3.

Units IA-1b (hub) and IA-1c (decision, inbox), round 2 (one agent in both roles, 2026-11-20). Read on `main` at
`e100640bf` (IA-1a merged): spec rev 2 §3, §4, §6; rulings D-IA.1 to D-IA.20; reviewer guide rev 2; packet and review
of IA-1a; the two owner files of 20 Nov. Code: `vNEXT/` on the same head. Numbering continues from round 1. Severity as
in round 1: **High** blocks coding.

### Highs

**R16 (High, done). G1's driver-drawer surface cannot be measured, and hidden links count as edges** (spec §2.5
click_depth_check; D-IA.9, D-IA.18).
- Every drawer today opens from a button (`uxOpener`, `data-ux-drawer`), not from an addressed link. `contentEdges`
  in `click_depth_check.cjs` reads only `a[href^="#/"]`, so "each Site's largest adverse driver drawer (≤ 3)" has
  no edge into it and is unreached by construction.
- `identity()` in `ia_crawl.cjs` keeps query *keys* only. Two drawers on one page (`?drawer=a`, `?drawer=b`) are
  one node, so the crawl never visits the second.
- `contentEdges` takes every `[data-level] a`, including links inside closed drawers (jsdom has no visibility). The
  Overview's heading drawers (`uxCats` → `uxDriverBody` → `uxDecLine`) hold "Open decision →" links, and the Site
  page's driver drawers sit in its markup too. So decisions count as depth 1 from the Overview and the Site page
  through content nobody can see without opening a drawer. Depths come out too low.
- Expected answer:
  - the driver drawer gets an address in IA-1b (`site/<key>?drawer=driver:<stable id>`; today's id
    `uxsdrv-<sk>-<k>-<index>` is index-based) and an opener that is a link carrying it, or the check treats a
    `[data-ux-drawer]` opener as an edge to `<route>?drawer=<id>`;
  - a link inside a drawer is an edge of the drawer node, never of the host page;
  - `identity()` keeps the `drawer` value (scope may stay key-only);
  - a plant that removes the Site's driver opener must fail the driver surface.

**R17 (High, done). The overview budget is at its limit, its "block" changes meaning, and the `tile` plant cannot
bite** (spec §3.2 `portfolio`; guide §2.2a; spec §2.5 `G1_PLANT=tile`).
- IA-1a's own uxi run: Lakeside **6 blocks, 2,453 px** at 1440 (47 px of headroom); Harvest 6 / 2,067; Metro 6 / 2,064.
  There is no room for a seventh block or a new line.
- uxi counts the visible children of `.ux-overview`. Once `uxOverview` is split into `<div data-level>` slots, either
  `.ux-overview` goes (the assertion silently changes target) or the three level wrappers are the children (3 blocks:
  the rule passes by construction).
- The Overview links the plan twice: the plan tile's "Review the plan" and the "More in the tabs" line's "the plan".
  If that line sits in a level, `G1_PLANT=tile` (remove the tile link) still reaches the plan at depth 1, so the
  plant passes. The same line repeats the frame's three tabs and still says "outcomes by site" (the old label).
- Expected answer:
  - a block is a direct child of a `[data-level]` region inside `[data-shape="hub"]`; at most 6 in total, at most
    2,500 px at 1440 on all three operators; uxi is retargeted with a plant shown failing first (spec §6);
  - the "More in the tabs" line is dropped on the hub (the tabs are now in the frame), which frees one block and
    makes the `tile` plant bite. Or, if it stays, it sits outside every level and the plant also removes it;
  - the gap tile's link to `portfolio/outcomes`: its exact words (§3.3 has none, §7 forbids new copy).

**R18 (High, done). The interim alias turns "View all" and "Act first ›" into live self-links** (spec §3.1 "View
all only once its home list has landed"; §2.2 alias `portfolio/act-first` → `portfolio`).
- `uxOverview` renders "Act first ›" and "View all {n} in Act first" as links to `portfolio/act-first`. Once IA-1b
  lands, that alias is live, so `iaUnlink` rewrites both to `#/portfolio`: the Overview links to itself under a
  label that names a tab that no longer exists. The crawl classes `#/portfolio` as good, so nothing fails.
- Expected answer:
  - a content link whose canonical target is the current route is unlinked (or removed) by `iaUnlink`, or the
    `portfolio/act-first` alias serves typed addresses only and is never applied to content links;
  - shape_check asserts no self-link inside `[data-level]` (fragment-only `#…` links aside), with a plant;
  - the hub shows the count of the rest ("{n} more") without a link until IA-2b. Its words are needed (§7).

**R19 (High, done). The counts do not come from one state source, and probe P7 cannot pass as written** (spec §3.2
Outcomes column 6; §4.2 "the acts"; §4.3; reviewer guide P4, P7).
- Today:
  - the Overview's "Decisions N" and the Site's "Decisions at this Site N" use `uxDecCount(ATTN[op])`, which counts
    every decision in any state;
  - the state split uses `uxDecState`; `uxStateCount` counts `choose` and `none` together as "waiting for a choice";
  - the inbox (§4.3) takes `choose` only, so a `none` decision (nothing recommended; also every decision under the
    `?state=no-recommendation` preview) is waiting on the Site page and absent from the inbox.
- `HC.decisions[].chooser`: 13 SITE_MANAGER, 1 FINANCE_AND_COMMERCIAL_LEAD, 1 OPERATOR_EXECUTIVE (`ruiru-expansion`).
  So "For you" on Lakeside and Harvest holds only the plan. Choosing any other decision does not move the badge, and a
  chosen decision stays in the queue with a new state, so "the queue and the badge dropping by one" (P7) is false for
  14 of 15 decisions.
- Expected answer:
  - one predicate, for example `iaWaiting(id)` over `uxDecState`, with `none` ruled in or out, used by: the Overview
    count, the Site count, Outcomes column 6 ("Open decisions": waiting only, or all?), both inbox sections, the badge
    and G1's "every decision waiting for a choice";
  - whether Choose removes the row from the queue or only changes its state (today: the state changes);
  - P7 restated per case (a For-you decision, a portfolio decision, the plan);
  - a jsdom assertion that the counts agree on every operator, before and after a planted act, with a plant that
    breaks one count.

**R20 (High, done). The decision page fails shape_check item 1 by construction** (spec §4.1; shape_check after
IA-1a review L5).
- "Choose this" (L1 and sticky) is a `uxOpener` button with `data-ux-drawer` only. shape_check fails every
  `button.primary` that names no act (`data-act` or `data-ux-act`), and needs the sticky primary's act to equal L1's.
- Each `uxChooseDialog` is a drawer in the page markup with its own `button.primary` "Confirm the choice"
  (`data-ux-act-go` only); a decision has up to three. Inside a level, that is several primaries in one region;
  outside every level, each is "a primary outside every level".
- The spec does not say where the page's drawers (choose dialogs, Evidence and records, How this works, The Actions)
  sit in the level structure.
- Expected answer: page drawers go in one container outside the levels (for example `<div data-ia-drawers>`) that the
  primary rule skips; the opener's act identity is its `data-ux-drawer` value (or the opener gains
  `data-ux-act="choose:<id>:<oid>"`), so L1 and sticky compare equal; a plant with two L1 openers still fails.

**R21 (High, done). Each decision's L1, L2 and L3 split is not decidable from §4.1** (spec §4.1, §4.4; guide §2.3,
§7.2; audit C17).
- **H1.** §4.1 says the subject "without a question form, from the UI branch's rule (C17)". C17 (`loop-init.js`
  `h1:`, guide §7.2) is the question while a choice waits, and the subject once chosen. They conflict.
- **Stepper.** §4.1 fixes Recommended › Chosen › Released › Verified. The reviewed `uxDecSteps` is path-specific:
  "No option recommended", "Awaiting approval", "Actions released", "Released at once", "Actions go ahead". The fixed
  list drops "Awaiting approval" (state `approval`) and has no step for `none`. Verified has no data, ever.
- **Tiles.** "Up to 3 tiles" against the guide's "one number" hero. Several decisions carry no money (rights,
  NOT_VALUED, cover at stake); several have a basis other than no action (`RESTORE_REFERENCE`), so "against no
  action" is wrong for them. Tile labels are not in §4.4.
- **L3.** §4.1 lists drivers, limits, cover, what would change it, verification. Today's six sections are: Why we
  recommend it (which holds "what would change it"), What it changes, Limits and cover, Cost and who pays, How we
  will check it worked, All options in detail. Two have no home and two are one.
- Elements without a level: the meta line, "Choose another option", the "Evidence and records" opener, the sticky
  bar, "How this works". "Open site" (§4.2) exists nowhere today, and its words are new copy.
- Expected answer: one table, element → level, with the H1 rule, the stepper mapping for each `uxDecState` key and
  `draft`, the tile rule per basis (which tiles appear, and their exact labels), and the six sections placed.

### Mediums

**R22 (Medium). Copy and wayfinding for the hub routes** (spec §3.2, §3.3, §7).
- No H1, crumbs or `home` is given for `portfolio`, `portfolio/demand-and-capacity` or `site/:site`; P5 asks that the
  H1 differs on each tab.
- Outcomes column headers are listed, not given as copy. For Metro (`kind: 'cost'`) "Contribution against target",
  "below target" and "most adverse first" are wrong in sign and word: the Site tile reads "Cost per required
  departure met", and adverse is over target.
- A Site with no target (`tree(sk).plan == null`, where `uxSiteTiles` returns nothing): its row, and whether it counts
  in "{m}".
- "this month" in the Outcomes headline, while every figure is October and the Overview says "in October".
- Demand & capacity has no L1 headline in the reused code, and no copy for one.

**R23 (Medium). Rules that no demo data can exercise** (spec §3.2 Outcomes; guide P6).
- Every operator has 3 Sites of one vertical. "Capped at 10 with Show all N", "grouped by vertical above 10" and "a
  group scope filters the rows" are identity on every operator, so their checks cannot fail.
- `uxCapLists` (in `iaFinish`) and §3.3's "Show all {n} Sites" are two cap mechanisms.
- Expected answer: a jsdom check of the row builder on a synthetic list (12 Sites, two verticals) with a plant, or an
  explicit deferral to IA-2b's list component; and one cap mechanism named.

**R24 (Medium). "Largest adverse driver" has no single definition** (spec §3.2 column 5; §2.5 G1 surface).
- `uxSiteDrivers` sorts by absolute effect; `uxSiteBoard`'s "the largest" is the largest non-residual, of either
  sign. The sign of "adverse" flips for a cost operator.
- Expected answer: one function (sign rule per `kind`; residual excluded) read by Outcomes column 5 and by
  `IA_G1_SURFACES`, plus the case of a Site with no adverse driver (its row and its G1 surface).

**R25 (Medium). What the hub slots hold on Outcomes and Demand & capacity** (spec §3.1, §3.2).
- `shapeHub`'s L2 is "uxQueue rows". Outcomes' L2 is a Site table and Demand & capacity has no queue.
- The Site table is a new list renderer one unit before IA-2b's "one list component".
- `primary` per tab is not named (the Overview has none today; its queue's "Decide" is a link).
- Expected answer: each tab's L1, L2 and L3 contents, and whether the Outcomes table is the seed of IA-2b's
  component.

**R26 (Medium). The Site page's split and the row grammar** (spec §3.1, §3.2; D-IA.9).
- `uxSitePage` holds a sticky bar (`a.button.primary` "Decide"), the headline, tiles, the full queue, "Actions in
  hand", seven sections, the driver drawers and the help line. The levels for "Actions in hand" and the drawers are
  not given, and the queue shows every decision, not the top 3.
- D-IA.9: "a row has one target and holds no other control". Queue rows hold a "Why" toggle and a "Decide" link;
  board rows hold a drawer opener and decision links. Is the grammar enforced in IA-1b, or by IA-2b's list?

**R27 (Medium). The primary rule cannot see link-styled primaries** (shape_check item 1).
- shape_check counts `button.primary` only. The hub's and the Site's primaries are `a.button.primary` (the queue's
  "Decide", the Site sticky). On the hub the rule cannot fail.
- Expected answer: the rule reads `.primary` on `a` and `button`, with a plant on a hub route.

**R28 (Medium). The inbox's address and its checks** (spec §4.3; D-IA.9, D-IA.17, D-IA.18).
- The control's markup (expected: `a[data-ia-inbox]` with `href="#/<route>?drawer=inbox"`). The drawer is open in
  the inserted markup; it is not opened by `uxOpen` after insertion, because the `data-open` change would fail the
  after-render check.
- Whether `after_render_check` covers `?drawer=inbox` on every live route.
- What Esc and close do to the address (replace or back), so that Back restores the drawer (P5).
- The selectors that tag "queue edges" and "inbox edges" for the per-entry G1 rule.
- At 1280 the top bar gains a control; at 390 its place is not given.

**R29 (Medium). "Since you last looked" has no data** (spec §4.3 item 3).
- `uxMock().chosen` is `{ id: oid }`, with no who, when or order. `uxDecState` and `uxDecSteps` read it as a
  string. "Newest first, with who, what and when" needs a new act record. Rule its shape and whether the readers
  change.
- `{time}` in "recalculation pending since {time}": expected `snapOf(op).detail.received`.

**R30 (Medium). Addresses that cross operators** (spec §2.2; D-IA.14 "one shell").
- `iaPattern` accepts any `SK` Site for `:site` and any `DEC` entry for `:dec`. Under Lakeside, `#/site/thika`
  renders Harvest's Site inside Lakeside's frame and scope menu. The aliases `mini`, `cold`, `ev` and `financials`
  are fixed to one operator's Site.
- Expected answer: a parameter outside `OPS[op]` resolves to `not-found`; a typed probe in shape_check, with a plant.

**R31 (Medium, Architect, carried from the IA-1a review). `IA_ALIASES.financials` against IA-2e's `financials`
route.**
- `financials` is an alias key (→ `site/kobo/financials`) and the IA-2e rail route. Alias-first resolution
  (`resolveScreen`, `iaLiveAlias`, `iaCanon` in `iaUnlink`) will send the Financials rail item to Kobo, under every
  operator; the crawl classes the rewritten rail href as an alias and fails. `globalfinancials: 'financials'` points
  at the same key.
- Expected answer: a landed `IA_ROUTES` path is never an alias key (the legacy `financials` screen keeps only its
  legacy `ALIAS`), and shape_check asserts statically, from IA-1b, that no `IA_ALIASES` key matches an `IA_ROUTES`
  pattern (plant: add one). This catches the class before IA-2e.

**R32 (Medium, Architect). The "Still to be rebuilt" popover (IA-1a deviation 3; review L3, still open).**
- The review bar shows "Still to be rebuilt (12)", a summary string the spec does not give. It is labelled a
  workaround, and the label needs a ruling. From IA-1b the count changes, and §3.1 adds the five unlanded Site tabs
  to it.
- Expected answer: the review bar is mock tooling, not product copy, so §7 does not bind it; the popover is ruled as
  the design, with the summary "Still to be rebuilt ({n})" and the list "Still to be rebuilt: …" (rail items,
  then "Site tabs: …"). Otherwise, name the layout that keeps the one-line text without pushing the 1280 queue row
  below the fold.

**R33 (Medium). DS1m review L1: fold the `.ux-trend` clip into IA-1b's gate** (spec §6; `tools/g3_trends.cjs`).
- G3 measures clipping on the sub-line (`.ux-kpi-s`) and the figure's range rect. Neither sees a clip on `.ux-trend`
  itself at 390, the case DS1m's reviewer named.
- G3 finds its tiles under `#app .ux-overview` or `#app .ux-kpis`, falling back to `document.body`. Once the hub split
  moves or removes `.ux-overview`, it measures the whole body without failing.
- Expected answer: §6 for IA-1b adds `g3_trends.cjs` (heavy slot) with `t.scrollWidth <= t.clientWidth` on each
  `.ux-trend` at 390 and 1440 (and 1280, where IA-1a deviation 4 lets it wrap); the root selector names the hub's
  L1 and fails if absent; a plant clipping `.ux-trend` at 390 fails.

### Lows

**R34 (Low).** The empty hash opens `iaStart()` from IA-1b (IA-1a deviation 7 flips); the legacy rail's Lab footer
leaves with it (review L2). A done criterion for IA-1b?

**R35 (Low).** "Headline (≤ 2 lines)": at which widths? The Overview headline is one long sentence, so at 390 it
wraps past two lines. Expected: measured at 1440 and 1280 only.

**R36 (Low).** Demand & capacity "red only for an adverse deviation against target" (C11). `opportunityScreen`
draws the welding bar `bad` (evening diesel) and `capBars` marks `over`, neither against a target. Name the selectors
the check reads, with a plant, or list these as kept.

**R37 (Low).** D-IA.10's "released Actions, filtered to the plan version (≤ 2)" has no surface before IA-2b. The
packet should say that it is unmeasured at the G2 stop.

**R38 (Low).** A gate's runtime: IA-1a's 18 runs took 206 s. From IA-1c every plant reruns its whole check over all
live routes (decisions and `?drawer=` variants included). Expected: the plants run on their host route only, except
AR plants, which spec §2.5 runs on every live route.

## IA-1b/IA-1c implementer pre-flight

Read against `main` at `e100640bf`, `vNEXT/`. Functions are cited by file and name.

**Cited anchors.**
- Present and as described:
  - `loop-ux.js`: `uxOverview`, `uxQueue`, `uxKpi`, `uxInsight`, `uxChain`, `uxBridge`, `uxCats`, `uxDrawer`,
    `uxOpen`, `uxTabs`, `uxSitePage`, `uxSiteTiles`, `uxSiteBoard`, `uxSiteDrivers`, `uxDecisionPage`, `uxDecSteps`,
    `uxDecStatus`, `uxDecState`, `uxChooseDialog`, `uxChooseAct`, `UX_ACTS`, `uxActDo`, `uxMock`, `uxToast`;
  - `loop-site.js`: `siteOverview`, `decisionScreen` (which returns `uxDecisionPage(id, parts)`);
  - `loop-portfolio.js`: `deciderOf`, `opportunityScreen`;
  - `loop-core.js`: `snapOf`, `snapText`, `pendingText`, `periodChip`;
  - `loop-decisions.js`: `DEC`;
  - `ia-shapes.js`: `iaFrame`, `iaTabsHtml`, an empty `IA_TAB_GROUPS`;
  - `tools/click_depth_check.cjs`: it reads `IA_G1_SURFACES()` if defined.
- Absent: `shapeHub`, `shapeDecision`, `IA_G1_SURFACES`, any "Waiting for you" code, a gap-tile link, an "Open site"
  link, and `DEC[].finding` (P13).

**P12 (Medium, done). `DEC` has 15 entries, not 14.** `mto-losses` was added by D-RECON.7. Spec §4.2 and D-IA.12
say 14. G1, the shape check and the screenshots enumerate `DEC`, so only the text is wrong. Expected: the text
reads 15, or "every `DEC` entry".

**P13 (Medium). The `recommendation` aliases can never be live.** `iaRecDecision` looks up
`DEC.find(x => x.finding === OBJ[route])`, but `DEC` entries have no `finding`. `OBJ` holds v7.0 ids (`F-104`,
`F-118`, `F-130`), and `HC.decisions[].finding` is a sentence. The four aliases resolve to `null`, so the typed old
addresses stay legacy screens after IA-1c. Expected: a fixed table (old route → decision id) ruled by the Architect,
or these aliases go to `not-found`.

**P14 (Medium). Splitting the reused pages, and proving the split.** `uxOverview`, `uxSitePage` and `uxDecisionPage`
each return one string. Placing their parts in levels needs a `…Parts` split like `planParts` (D-IA.20). Expected:
the same rule (the legacy function joins the parts byte for byte, with a node script per operator and per decision
cited in the packet), or the Architect accepts wrapping without proof.

**P15 (Medium). `iaFinish` caps lists on every IA route.** The legacy `uxShell` ran `uxCapLists` only on
`decision/*`, `site/*` and the plan. The Overview, Outcomes and Demand & capacity gain "Show all" caps they never
had (rendered text and height change; Lakeside has 47 px of budget, R17). Expected: the `render_text` difference is
listed in the packet, or the cap is limited to the routes that had it.

**P16 (Medium). Checks tied to legacy markup.**
- uxi's overview budget reads `.ux-overview`.
- `g3_trends.cjs` reads `#app .ux-overview` and `#app .ux-kpis`, with a silent fallback to the body.
- uxi block 8 and `plan_switch_check` boot `#/portfolio` and `site/*`, which become IA routes.

Expected: each retarget whose assertion changes is shown failing on a plant first (spec §6, P6 of round 1).

**P17 (Medium). Top 3 at Site scope.** `uxQueue` renders every row it is given; the Overview's caller slices to 6
merged rows, and `uxSitePage` passes all of the Site's rows. Top 3 needs a caller change inside reviewed code, or
slicing in the shape. Which?

**P18 (Low). Tab groups.** `iaTabsHtml` keys `IA_TAB_GROUPS` by `route.tabGroup || route.home`. A Site route whose
`home` is "Sites" would share the key with IA-2b's Sites list. Expected: Site routes set `tabGroup: 'Site'`.

**P19 (Low). Acts after render.** `uxActDo` calls `render()`, which reaches `iaRender` on an IA route. It then calls
`uxFocusState`, which sets `tabindex` on `.ux-dmeta .status-pill` and focuses it. A new stepper must keep a focus
target. These are user-caused, so outside the after-render check. `uxActOpen` puts `#uxact` in `body`, outside the
frame.

**P20 (Low). Who "For you" holds.** `deciderOf` → `HC.decisions[].chooser` (R19): the executive chooses only
`ruiru-expansion`. Plan state is `uxPlanState(op)` (`PSTATE()` plus `uxMock().plan[op]`). Choose is open to the
viewer on every decision, whoever the chooser is. Is that intended?

## IA-2a

Questions on `spec.md` §5.1 (rev 4), `rulings-2.md` D-IA.43 to D-IA.48 and the reviewer guide's "IA-2a" section, in
one batch: the Reviewer as R1, R2 …, the Implementer's pre-flight (against `main` and the proposal page) as I1, I2 ….
Each cites its section and the answer expected; mark **(done)** when the answer changes what counts as done. The
Architect answers once, in `rulings-2.md` (or `rulings-3.md` past its cap), and folds the answers into §5.1.

### Reviewer questions

### Implementer pre-flight

## IA-2a reviewer questions

Reviewer (Claude), 2026-11-21, against `spec.md` §5.1 rev 4, D-IA.43 to D-IA.48 and `main`'s vNEXT code. **(done)** = the answer changes what counts as done.

**R1 (done) The dormant checks cannot be shown able to fail at the unit 2 stop (§5.1.9, §5.1.8).** `ia_gates.cjs` runs a unit's plants only when `IA_LANDED` has it, and every unit-2 assertion prints "IA-2a not landed; dormant". At the end of unit 2 no builder exists, so no plant can run: "checks written" is untestable there, and the first time any of them can fail is 3(b), after the stop. A typo in the dormancy guard would make a check pass for ever. Expected: (a) every new check takes `IA_FORCE_LANDED=IA-2a`, which adds the unit in the booted window only, and a mutation run proves each assertion fails against a stub or `shapePlanInterim` output; (b) after the flip, `ia_gates` fails any new check whose output still contains "dormant" (the plant table is the proof it ran); (c) say plainly that unit 2 evidence is "written and mutation-tested against the interim", not "plants failing". Otherwise move the recommended stop to the end of 3(a).

**R2 (done) "Shown failing before the flip commit" for `plan_switch_check` (§5.1.8, reviewer guide done-4).** The retargeted assertions read L1's crew tiles, the release line and Left out; the interim page has none of them, so they fail on the real plants only after the builders are live. 3(a) leaves routes "not live", so there is no page to run them on. Expected: the same `IA_FORCE_LANDED` route to render `plan` through `shapePlan` in 3(a), and the three `PSW_PLANT`s run there before 3(b).

**R3 (done) Byte-identity is only as strong as its states (§5.1.7).** `parts_identity.cjs` today loops operator × switch case × two previews and calls `planScreen()` with `Object.assign(LS, c)`; it never sets a plan state. Three plan states need `uxMockSet` (`plan[op]` with `state`, `by`, `version`, `ids`) in both the main and the new window, and for "sent back" the `reason` and `giveWay` too. Questions: is the state set identically in both windows, by the same literal? Does "approved" use a non-default case (version + 1, `ids` of that case) as well as the default? The count to commit: operators (3) × cases × 3 states × 2 previews for `planScreen`; 3 × 3 × 2 for `whatChangedScreen`. The packet must print that arithmetic per function. A `parts_identity` plant is missing: one deliberately changed byte in each of the four splits (`PI_PLANT=…`) must report DIFFERS, or the script could be comparing a window with itself.

**R4 `whatChangedScreen()` reads `LS.op`, the new `whatChangedParts(op)` takes `op` (§5.1.5).** Their inner calls (`planItemsV1(op)`, `actionRows`, `rightsMeasures(op)`) must agree. Say that `whatChangedScreen` calls `whatChangedParts(LS.op)`, and that Review calls it with `ctx.op`. Is `ctx.op === LS.op` guaranteed on a hash route with an operator in the address? If not, the Review tab can show another operator's items. Also: Review calls `whatChangedParts`, which builds all six parts (the rights tables included) to use one. State that this is accepted for counters (`UX_QN` advances as before) and cost, or build lazily.

**R5 (done) A case the page cannot undo (§5.1.2, §5.1.3).** The case switches live only on Items and Left out, but the L1 release line and the "case not proposed" notice follow the case on all four tabs, and Approve and the sticky act on `planCase(op)` (the case in `LS`). On Review or History a person can therefore approve a non-default case (version + 1) with no switch in sight. Expected: either the L1 on Review and History states which case it shows ("Showing the case you chose on Items: …", with a link back), or Approve on a non-default case is only offered on Items and Left out. The Approve dialog already names the version. Add to the check: after Approve of a non-default case, History's first row and the stepper show the new version.

**R6 One state source, and what the grep can catch (§5.1.3, reviewer guide first checks).** `uxPlanBand` and `approvalPanel` already read `uxPlanState`; `crewByMonth` and `planStatusBlock` read `PSTATE()` only for `period`. The risk is the new code: `iaPlanHistory` reads `PSTATE().version` for "Version N proposed" (correct: the proposed version), but `S.version` for the sub (the approved version after a non-default case). Say which is which in the copy. The plant `planstep` swaps the stepper to `PSTATE()`: `PSTATE().state` never changes on an act, so it fails after Approve only if the check acts. The check must act (Approve, Undo, Send back) on each of the four routes and compare with the manifest and `sessionStorage['l4-mock']`, not run on the first state only. Say so in the packet's count table.

**R7 (done) The `cap` plant may not be able to fail (§5.1.8).** `PLAN_PLANT=cap` makes `uxCapLists` cap at 1, but it only touches `ul.list`. The reviewed plan page has no `ul.list` (items are `ux-items`, the rest tables and sections); only History's list is one, and History is excluded from the assertion. Plan the plant so it fails: either assert History too (rows ≥ 2 after one act) or add a plant that caps the Review table. If nothing on Items, Left out or Review can be capped, say so and drop `[data-ux-over]` there.

**R8 `.approval` and `.meter` absence (§5.1.8).** `.approval-releases` is kept in L1, so a selector `[class*=approval]` fails and `.approval` passes. State the selectors: `section.approval`, `.meter, .metertrack, .meterhead`, and that `.ux-meterbar` is the only bar. Also assert `data-ux-sticky` is present once per tab, and the sticky's Approve and the band's carry the same act (D-IA.23).

**R9 Placement uniqueness (§5.1.2, §5.1.8).** "Each fragment once" needs a fingerprint per fragment: name each one in the check (the `<h2>` or `aria-label` text of every placed fragment, as the check's own constants, not read from `planParts`). The `place` plant (Left out also on Items) then fails on a count of 2. Add the fragments that are not headed: the release line, the version notice, the "Try another case" panel. Also `Listed beside` and the returned Actions: these hold only a heading when non-empty; state which operator/case has them (the returned Actions: Lakeside 6500/No only), so the check is not vacuous on the other hosts.

**R10 The empty-region rule against the L1 cap (§5.1.3).** "L1 cap of 4 holds for every operator (period of at most two months)." This holds for the three fixtures. The check should compute tiles from the manifest's period, and fail if a period spans three months, instead of only counting 4 on Lakeside.

**R11 (done) G1 through the tabs (§5.1.8, D-IA.9, D-IA.10).** Items: (a) the three new tab routes are `unit: 'IA-2a'`, so until 3(b) the tab strip hides them (`iaTabsHtml` filters on `IA_LANDED`): G1's graph for "plan tab: Left out" has no edge in unit 2 or 3(a), so the new surfaces would fail from the start. Dormant surfaces too? (b) "≤ 2 via `any`": which origin? From `portfolio` the plan is 1; each tab then 2 only if the tabs are edges on the plan page itself. The plan's inbox row (`#/plan`) and the Overview tile both land on Items. State the origins. (c) "every plan item's decision (≤ 2)": the item row's "Decision →" link is on Items only, inside a closed `details`; G1's D-IA.32 counts a closed details as a node, so it is 3 from `portfolio`? Confirm the number. (d) `G1_PLANT=plantabs` returns Items only: the plant host must be a route where the group is shown.

**R12 Counts agree: inbox row, badge, stepper, History (§5.1.8).** The inbox's plan row reads `uxPlanState`; History's first row reads the act log. The pairs that can disagree: after Undo, the log entry goes with the state (D-IA.24), fine; after Approve of a non-default case, the log's toast says "Version 2 approved" while `PSTATE().version` is 1. Add that case to the check; and the badge after Approve must be down by one *only when the plan was PROPOSED* (it is not counted at DRAFT). Also fix the order: the count check currently derives "expected" in three states; the plan block adds four more (as proposed, Approve, Undo, Send back): state per operator the total number of page loads, so the runtime is bounded (4 routes × 4 states × 3 operators = 48 boots).

**R13 `docTitle` and shape_check item 10 (§5.1.1).** `screens.js` line 1004 writes `document.title=` `${s.title} · ${op}` directly on IA routes; the spec says `render()` writes `s.docTitle || s.title`. Confirm that is the one reviewed line, and that tabbed routes of other groups (Portfolio, Site) remain distinct without `docTitle` (item 10 "runs at once"). The Site group's titles with `ctx.site` must be compared per Site, not once.

**R14 (done) "Approve inside the first viewport" (§5.1.8, `ia_shots`).** At 1440 × 900 and 1280 × 720 the L1 now has the stepper, 3 or 4 tiles and the release line above or below the act row; the sticky bar already holds Approve in view. Which test: the band's own button `getBoundingClientRect().bottom <= innerHeight`, or the sticky's? State the metric and the clause for `plan/review` and `plan/history`, where a short page shows the band even without scrolling. `SHOTS_PLANT=approvefold` should fail on the band's button and pass on the sticky, which is why the sticky must not count.

**R15 Untested "no change" claims (§5.1.7).** "The Approve and Send back dialogs, the toast with Undo, focus after an act" are not byte-compared by `parts_identity`. `uxFocusState` looks for `.ux-planband [data-plan-state], .ux-dmeta .status-pill` and falls back to `h1`: on the IA page the chip is still in the band's act row (`uxPlanStateChip`), so focus lands on the chip; but on Review and History is it present? Add an assertion that focus after Approve is on the chip on all four tabs, and that Undo returns focus to the button (`uxFocusAction`).

**R16 Wording that cannot be tested.** "Nothing else is new" (§5.1.6, done-5): give the check, e.g. every string rendered on the four routes and not on the reviewed pages is in an allowed list (`rendered_strings.cjs`, `copy_check.cjs`). "Honest numbers" for the History rows: "The system · {date}" attributes the proposal to the system with the manifest's `proposed` date; fine, but the "Opened within the executive’s limits" row is a claim: its source is `PSTATE().opened`; say so in the packet.

**R17 Rework of the two stepper states.** `iaPlanSteps` returns `cur = 1` for `REVISED`, but no act or fixture produces `REVISED` (`STATE_WORD` only); `CLOSED` is never current. These branches cannot fail in a check. Either unit-test the pure function directly on all five states in `plan_shape_check`, and on the thrown error for an unknown state, or drop `REVISED`.

**R18 Rule on a unit-2 merge (§5.1.9).** "Units 1 and 2 may merge alone after a verification review." Say what the reviewer verifies for unit 2 given R1: I would accept only with the force-landed mutation runs in the packet. Also a stop line needs the next-resume sha and a statement that `IA_LANDED` has no IA-2a at that point.

## IA-2a implementer pre-flight

Implementer (Claude), 2026-11-21, read against `main` at `96f642a14` (`vNEXT/`). Nothing coded.

**P1 Functions found, as cited.** `planParts` (loop-portfolio.js:476), `planScreen` (:504), `approvalPanel` (:467), `whatChangedScreen` (:576), `uxPlanBand` (loop-ux.js:394), `uxPlanState` (:1021), `uxPlanSticky` (:1079), `uxSecA` (:774, with the `open` argument), `uxSecAx` (:1070), `uxOpener` (:267), `uxDrawer` (:264), `uxMeterBar` (:28), `crewByMonth`/`crewMeters` (:394/:398), `thresholdsKv` (:417), `hhmm` (loop-core.js:315), `iaForYou` (ia-shapes.js:168), `shapePlanInterim` (ia-shapes.js:73). `iaPlanHead`, `iaPlanStepper`, `iaPlanSteps`, `iaCrewTiles`, `iaPlanBand`, `iaPlanHistory`, `shapePlan`, `approvalParts`, `uxPlanBandParts` and `whatChangedParts` do not exist yet, as spec.

**P2 The `planParts` split is not a pure rename.** Today `l3` holds `<div class="grid2">{crew}{listed}</div>` with the "Left out" section after it. §5.1.5 says `l3` is "today's template over diff, paths, crew, listed, left, cases, returned". `crew` and `listed` are built inside the template literal as `uxSecAx(...)` calls with `region(...)`, so each becomes a `const` that must be the identical string; the grid2 wrapper and the blank-line whitespace stay in `l3`. `parts_identity` proves it. `l2` has a leading newline and `l3` too: trust only the byte compare.

**P3 `grid2` is lost on the IA page (layout, not identity).** On Items, `p.crew` is alone (its `listed` neighbour moved to Left out), so the two-column grid is a half-empty row, and on Left out `listed` is alone. The spec's placement table does not say whether to wrap each in `.grid2` or place it full width. I will place each full width (no wrapper) and ask the Architect to confirm (R9's "placed once" holds either way).

**P4 `approvalPanel` and `uxPlanBand` splits.** Both are single template literals; `approvalParts` returns `status` (`planStatusBlock(op)`), `kv`, `meters` (`meter(...)` + `crewMeters`), `releases` (the `<p class="approval-releases">` with its computed text), `notice` (the `def||!pre ? '' : <p class="notice">`), `note`, `thrBody`, `thresholds`. `uxPlanBandParts` returns the four pieces; `uxPlanBand` joins with the same literal newlines. The crew tile in the band today is `uxKpi(cap(o.crewWord), …)` (first month only, with other months as plain lines): `B.crew` stays the fallback when `crewByMonth` is empty (`ms.length ? … : '—'`); `iaCrewTiles` returning `''` then falls back to the `—` tile, as the spec's `|| B.crew`. Note `B.act` is the `.ux-planact` div; the band template places it after `.heroes`; kept.

**P5 `whatChangedScreen` split.** It declares `S`, `v1`, `acts`, `review` (with an inner `acts` shadow), `rows`, `rt`; `review` does not need the outer values. `whatChangedParts(op)` returns six strings; `whatChangedScreen` becomes `const p = whatChangedParts(LS.op); return \`${p.kpis}${p.actions}…\``, with the section order today: kpis, actions, review, chosen, rightsM, rights. Whitespace between the sections is a literal newline + one space in today's template: kept in the join.

**P6 State source today.** `PSTATE()` appears in `periodWords`, `periodEnd`, `crewByMonth`, `orgLimitsByMonth`, and in `approvalPanel` (`S0`: `opened`, `proposed`, `version` for the non-default notice), `UX_ACTS['approve-plan']` and `send-back`. All stay. New code reads `PSTATE()` only for `opened`, `proposed`, the proposed `version` and `period`. One real trap: `uxPlanState` returns `version: m.version ?? S.version`, so after Approve of a non-default case History's sub says "Version 2" and the proposed row "Version 1": both right; I will word the sub as the plan's current version.

**P7 `docTitle`.** `screens.js:1004` (`render`) sets `document.title = \`${s.title} · ${OPS[LS.op].name}\`` for IA routes; `iaScreen` builds `s`. The change is `s.docTitle || s.title`, one line. `iaScreen` is in ia-routes.js (not read in full); I will read it before coding and add `docTitle` there.

**P8 Tabs and `IA_LANDED`.** `iaTabsHtml` (ia-shapes.js:29) filters a group by `IA_LANDED.has(route.unit)`; the three new routes carry `unit: 'IA-2a'`, so they are hidden and unreachable until 3(b) adds the unit, as the spec says. `iaLanded(path)` (ia-routes.js:95) gives not-found for them. A check that visits them before the flip needs the force flag (R1, R2): I propose `IA_FORCE_LANDED` read in `ia_crawl.cjs`'s `boot`, which runs `IA_LANDED.add(...)` after the scripts load and before the first render. No product-file change.

**P9 Gates against code.** `ia_gates.cjs` reads `IA_LANDED` by regex from ia-routes.js and runs `PLANTS` for landed units only; it has no `IA-2a` row yet: the table gains `PLAN_PLANT`, `COUNT_PLANT=planstep/planhist`, `SHAPE_PLANT=doctitle`, `G1_PLANT=plantabs`, `PSW_PLANT`, `UXI_PLANT` and `SHOTS_PLANT` entries. `PSW_PLANT`, `UXI_PLANT` and `SHOTS_PLANT` belong to checks that are not in `ia_gates` today (`plan_switch_check`, `ux_interaction_check`, `ia_shots` are run separately; `ia_shots` needs the heavy slot): I will add `plan_switch_check` to the runner and run the other two plants by hand with output in the packet; say if the Architect wants them in the runner. `count_check.cjs` has the `COUNT_PLANT` plant map with `foryou` and `nolog`; the new `planstep`/`planhist` follow the same eval-in-window form.

**P10 `parts_identity.cjs`** takes the base file and the new file, boots each with `boot(file, op, search)`, resets `UX_QN`, and compares. It has no plan-state step (R3) and no `whatChangedScreen` job; both are added. `index.html` is built by `build.mjs` from the sources: the script must run after `node build.mjs` on the branch, and the base file is `main`'s built `index.html` (so main's must be a built, committed file; checked: `index.html` is tracked).

**P11 `plan_switch_check`** reads the budget meter, spend, value, the approval panel (version, state, thresholds) and `meter` bars from `planScreen()`-era markup: its header says "the summary and the approval panel show version, state and thresholds" and "each month … has its own meter". Retargeting to L1's tiles, the release line, and the thresholds drawer touches several assertions. I count them at 3(a) time; I do not expect more than the three the spec names (§2.1).

**P12 `ux_interaction_check`** has plan blocks tied to the old page (`r.n`, the sticky on a short page, the M1 routes). I will read the whole block before touching it and list every line changed in the packet; I will not widen D-IA.48's changes.

**P13 Questions I would put to the Architect before coding:** R1 (force flag; or move the stop), R5 (the case on Review and History), R7 (the `cap` plant), R11 (G1 origins and the closed-details count), P3 (the `grid2`), P9 (runner rows).

**P14 Plan of commits.** (1) the four splits + `parts_identity` states + plants; (2) the checks first, with `IA_FORCE_LANDED` and mutation runs; (3a) builders, routes, `docTitle`, `ia.css`; (3b) the flip, retargeting, walkthroughs, register rows R757 to R760, screenshots, packet. No file outside `vNEXT/` and this folder.
