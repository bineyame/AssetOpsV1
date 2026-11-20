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
