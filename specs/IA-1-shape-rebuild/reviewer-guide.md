# IA-1 reviewer guide (rev 1; review each unit separately)

You are the fresh Reviewer.
- **At the handshake:** read `spec.md`, `rulings.md` and this guide, plus the proposal page
  `Docs/design-system/ia-proposal/index.html` §2 to §6. Write your questions in `handshake.md`, together with the
  Implementer's pre-flight.
- **At the review:** the depth is discovery (W5). This is a new structure across every screen.

## What counts as done (per unit)

1. Every route the unit owns is live in `IA_ROUTES`, has the unit's shape, and renders through `iaRender`.
2. `shape_check`, `click_depth_check` and `after_render_check` pass, **and each one's plant fails**. Run the plants
   yourself; do not take the packet's word.
3. The gates already earned pass (spec §6, item 4).
4. The menu, the tab labels and the copy match spec §2.7, §3.3 and §4.4 word for word.
5. No unlanded destination is reachable: the rail item is unavailable, the tab is not drawn, and there is no
   "View all" link.

## First checks

1. **Scope.** The diff touches `vNEXT/` and the spec's evidence-free files only. No manifest, evaluator or
   `frontend/src` change.
2. **Starting point.** The branch contains the accepted head of `task/uiux-design-model`. Nothing that passed review
   there is re-typed: the reused functions are called, not copied.
3. **The render path.** Open `iaRender`. The markup is built, finished on a detached fragment and inserted once. For
   IA routes, `afterRender` adds only listeners, focus and the brand attribute on `<html>`.

## Probes

- **P1 Crawl** (the G1 and stub probe). For each operator, start at `#/portfolio` and click through every link to 6
  hops by hand on a sample: Overview, Outcomes, two Sites, and one decision.
  - Nothing reached is a v7.0 screen: no "earlier view", no "Event window", no `KOBO-001`.
  - Nothing reached is a stub, and nothing belongs to another operator.
- **P2 Depth.** Count the clicks yourself:
  - the plan: 1;
  - the Kisiwa Overview: 2;
  - the Kisiwa largest-driver drawer: 3;
  - a waiting decision: 1 from the queue, 2 through the inbox.

  Compare with the packet's table.
- **P3 After render.** In the browser, open devtools, add a `MutationObserver` on `#app` and reload a hub route. You
  should see no mutation after load until you click.
- **P4 One source.** The Kisiwa gap on Portfolio › Outcomes equals the gap tile on `site/kisiwa`. The count of
  decisions on Outcomes equals the Site's queue. The Overview's Grow and Optimize tiles still tie to the statement
  with the "of which unbilled energy" line.
- **P5 Wayfinding.**
  - The H1 differs on each Portfolio tab.
  - The document title is "<view> · <operator>".
  - A decision's breadcrumb starts at Decisions.
  - An unknown hash shows not-found.
  - Back restores the tab, the scope and an open drawer.
- **P6 Scope.**
  - There is one scope switch.
  - Choosing a group on Outcomes filters the rows, and the address shows `?scope=group:…`.
  - Choosing a Site opens its page.
- **P7 Acts** (IA-1c). Choose an option. You should see:
  - the dialog, then the toast with Undo;
  - the state step moving;
  - the queue and the badge dropping by one;
  - Undo restoring all three.
- **P8 Developer gate.** With "Developer access" off, the Lab is not in the rail, and `#/lab` shows not-found or the
  review-select only. With it on, the workspace footer shows "Simulator Lab".
- **P9 Phone and 1280.**
  - At 390: no sideways scroll, and the Section menu works.
  - At 1280: the top bar stays on one line.
  - Light and dark, both brand packs.

## Class sweeps (W6)

- **One route not through `iaRender`:** check every `IA_ROUTES` entry.
- **One link to an unlanded or legacy route:** grep every `link(` and `href="#/` in `ia-shapes.js` and in the reused
  functions they call.
- **One figure that differs between two screens:** list every figure the hub and the decision show twice, and
  compare each pair.
- **One after-render mutation:** run the check on all three operators at 1440 and 390, not one.

## Risks

- **Reused functions.** They may still link to v7.0 routes, such as `sitefindings` or `finding`. The crawl finds
  them. Each one is fixed at the link, never by an alias that points back to a v7.0 screen.
- **Global passes.** Moving them from `afterRender` into `iaFinish` can change the order they run in. Compare
  `render_text.cjs` output before and after; any difference is explained in the packet.
- **The plan interim (spec §2.6).** It must not grow. IA-2a replaces it.
