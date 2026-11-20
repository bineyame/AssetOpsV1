# Review IA-1c r1: the decision shape and the "Waiting for you" inbox

Reviewer: fresh Claude (did not author IA-1c). Depth: discovery (W5). Branch `task/IA-1c-decision`, head `c139ac40b`,
worktree `/opt/assetecon/AssetOpsV1-ia1c`, diff `b817f9370...c139ac40b`. Evidence: `/opt/assetecon/evidence/IA-1/IA-1c/review-r1/`.

## Summary (r1)

- **Verdict: ACCEPT WITH FINDINGS FIXED ON THE BRANCH** (M1 must be fixed before G2; M2 and M3 are owner-facing and should be
  fixed or ruled before G2; Lows may ride along).
- The core holds: 15 decisions live through one shape, parts byte-identical (70/70, rerun), one decision set and predicate,
  badge 1/1/2, Choose keeps the row and moves every count, Undo restores, the act log works, G1 within limits.
- **M1** "See the options" goes to "Page not found" on 5 live decisions under the no-recommendation preview the review bar
  offers on every decision page. IA-1c is what makes these pages reachable: fix it here, as a class (router + gate).
- **M2** The top bar from 761 to ~1330 changes shape four times (two rows, one row without search, two rows with full search,
  one row with search cut to "Search Sites, de…"). It reads patched. One collapse rule would read deliberate.
- **M3 (Q2)** At 1280×720 (a common laptop) and 390 a decision has no visible way to its Site. Recommend Q2 option (a).
- **L1** No in-tree gate sees the act log or the decision's Site crumb (my plants B and C pass every check).
- **L2** A decision's scope switch reads "All sites" while its Site page reads its Site.
- Gates rerun: ia_gates 47/47 as expected; parts_identity 70/70; ia_shots (decision set) 108/0; guards pass.

## Checks I ran (head `c139ac40b`, all browser runs through `tools/heavy-slot.sh`)

| Check | Result |
|---|---|
| `node tools/ia_gates.cjs` (worktree, read only) | **47 runs, landed IA-1a, IA-1b, IA-1c, all as expected (703.8 s)**; IA-1c plants fail on the packet's first lines (decprimary, stickyact, inbox `depth ∞ > 2`, foryou `badge reads 0, expected 1`) |
| `parts_identity.cjs` against main's `index.html` at `b817f9370` | **70 cases, 70 byte-identical, 0 sticky only, 0 differ** |
| `ia_shots.cjs`, `SHOTS_ONLY=decision` (scratch copy) | **108 measured, 0 bad** (15 decisions + inbox × 3 operators × 1440/1280×720/390 × light/dark) |
| My plant A: `iaExecChooses = () => true` (badge becomes a portfolio count) | count_check **fails** ("Lakeside · the badge reads 4, expected 1"): the gate bites |
| My plant B: `uxActDo` no longer writes `next.log` | count_check, shape_check, after_render_check **all pass**: no gate sees the act log (L1) |
| My plant C: the decision's Site crumb loses its link | shape_check, click_depth_check **pass**: no gate sees the decision's way to its Site (L1) |
| P7 probe (Metro Ruiru expansion, browser) | before: badge 2, For you `plan, ruiru-expansion`; after Choose: H1 question → subject, pill "Chosen in this demonstration · awaiting approval", badge 1, row in Since "… chosen Daniel · 19:06"; Undo restores all; no page errors |
| Queue after Choose (1440 and 390) | the Ruiru row stays, "2 waiting … 1 awaiting approval" → "1 waiting … 2 awaiting approval", badge 2 → 1; 1 click from the queue to the decision |
| Inbox at 390 (Lakeside) | opens, focus inside, 0 of 30 Tab presses leave it, Esc closes and returns focus to the control; a row opens its decision and the drawer is closed there |
| `node build.mjs` in the worktree | `index.html` unchanged (the committed build is reproducible) |
| `check-agent-workflow.ps1` | passed |
| `check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` = main's `.venv`) | passed |

Cited, not rerun (builder, same revision `cb7f8454a`; `b5739046d` is CSS only and was reshot): uxi 384/0, full ia_shots 342/0,
count_check, G3 36/36, plan_switch 785/0, check_manifest 7572/0, shell/design_lint/vocab/copy/hand_typed 0.

Screens I looked at: Lakeside Kisiwa late repair (1440 light), Metro Ruiru expansion (1280×720 dark), Harvest Thika backup (390
light), the inbox open (Lakeside 1440 light, Metro 390 dark), the top bar at 761, 1100, 1199 and 1280. The page bodies read as the
reviewed decision page; levels, one primary, the stepper, no tiles, no Verified step.

## Findings

### M1 (Medium, acceptance gap; fix on the branch) "See the options" opens "Page not found" on live decisions

- **Where.** `loop-ux.js:718` (`<a class="button" href="#uxcards-${id}">See the options</a>`; the same pattern at `:715` for
  "Choose another option"). Reviewed code, unchanged by IA-1c.
- **What.** The hash router treats `#uxcards-<id>` as a route. Swept every live route of the three operators in both states: in
  the default state no such link exists; under `?state=no-recommendation` five decisions carry one (kisiwa-om, mto-billing,
  mto-losses, ruiru-expansion, ruiru-connector). Clicking it on `#/decision/ruiru-connector` lands on `#uxcards-ruiru-connector`,
  H1 "Page not found".
- **Why it matters.** Before IA-1c these pages were not reachable from the Portfolio; IA-1c makes them reachable (spec §1 "what is
  reachable"), and the review bar shows "Preview: no option recommended" on every decision page, so the owner is invited to take
  exactly this path at G2. It is the recommendation card's own act in that state. No gate sees it: every crawl and check reads
  only `a[href^="#/"]`.
- **Fix (class, W6).** One rule in the router: a hash that does not start with `#/` and names an element on the current page scrolls
  to it (focus it) and keeps the route and its query; anything else falls through as today. Plus a shape_check item: on every live
  route, in the three states, every `a[href^="#"]` is either a landed `#/` path or names an element id present in the page; a
  plant (`SHAPE_PLANT=anchor`, e.g. a `#nowhere` link in L1) must fail. This touches the router, not the reviewed function, so it
  fits §7; the Architect should confirm in one line (rulings-2) because it is beyond D-IA.22/24/28's list.
- **Answer to the dispatch's question:** yes, IA-1c should fix it; leaving it puts a not-found on the owner's G2 path.

### M2 (Medium, owner-facing; not a spec gap: §4.3 is met at 1280 and silent between 761 and 1199) The top bar reads patched

- **Where.** `ia.css:51-57` (the IA-1c search and 761-1199 rules) together with the legacy `mockups.css:4` rule that hides `.searchbox` at
  ≤ 1100 px.
- **What I measured (Metro, `#/portfolio` and a decision).** 761: two rows, no search, inbox icon only. 900 to 1100: one row, no
  search. 1101 to 1199: two rows, full search (330 px). 1200: one row, search 275 px and cut. 1280: one row, search 223 px reading
  "Search Sites, de…" (see `tb-1280.png` and the 1280×720 shots). 1440: one row, full. Four layouts in 700 px, and the widest
  search appears exactly where the bar breaks into two rows.
- **Why it matters.** This is the first thing the owner sees on every screen at G2, and the standing brief asks for control
  choices that read chosen ("right control per content", "simplicity by design"). An ellipsised placeholder reads as overflow,
  not as a design.
- **Fix.** One collapse rule for the search control: where the full box does not fit beside the other items, it becomes the
  icon button with its existing aria-label and Ctrl K (a `.ia-search-t` visually hidden, as the inbox label is), so the bar is one
  row at every width from 761; drop the 761-1199 wrap. Keep the inbox label rule (hidden below 1024) as it is; it is consistent.
  Gate: ia_shots' existing width sweep asserts one row and no truncated `.ia-search-t` from 761 up (`oneLine` today is asserted
  only at ≥ 1200). No new copy. If the Architect prefers the current behaviour, record it as a ruling so the owner sees it was
  chosen.

### M3 (Medium, wayfinding; this is open Q2) A decision has no visible way to its Site at 1280×720 and 390

- **Where.** `ux.css:242` (≤ 600 px) and `ux.css:372` (≥ 1024 px and ≤ 820 px tall) hide `.canvas .breadcrumbs`; D-IA.26 makes the
  Site crumb the decision's only way to its Site.
- **What.** Probe on Lakeside `#/decision/kisiwa-om`: crumbs visible at 1440×900, 1280×900 and 900×800; hidden at 1280×720 and
  390×844. The meta line's Site name is text; the scope switch reads "All sites" (L2). The only routes back are the browser Back,
  or the scope switch (two clicks, not obvious) or search.
- **Why it matters.** 1280×720 is the common small-laptop viewport the owner may well use; a decision is a drill-down page with
  no rail item lit and no tabs, unlike the hub routes for which the hiding rule was written.
- **Fix.** Q2 option (a): an `ia.css` rule that keeps the crumbs on the decision shape at every size (e.g.
  `.canvas:has(>[data-shape="decision"]) .breadcrumbs{display:block}` with the existing phone spacing). No reviewed function
  changes and no copy. Option (b) changes reviewed `uxDecisionSlots` and adds a second link to the same place. The packet's
  default (as built) leaves the gap at G2; I recommend the Architect answers Q2 with (a) before the owner sees it.

### L1 (Low, missing test) The act log and the decision's Site crumb are unguarded

- Plant B (no `next.log`) and plant C (the Site crumb as text) pass every gate. P7's 25 assertions live in the builder's scratch,
  not in the tree.
- **Fix.** count_check's after-act state: "Since you last looked" holds exactly one `log:0` row whose href is the chosen decision,
  and the For-you/In-your-portfolio sets lose that id (already asserted); shape_check: on every `decision/*` route the crumbs are
  `Decisions` (text), a link to `site/<d.site>`, then the subject. One plant each.

### L2 (Low, consistency; Architect) A decision's scope label reads "All sites"

- Packet item 5. On `site/<k>` the scope switch reads the Site; on that Site's decision it reads "Metro Bus Depots · All sites".
  The page is about one Site. Recommend the decision route's scope follow its Site as the Site page does (no new copy). Spec is
  silent; a one-line ruling either way.

## Answers to the dispatch's hunt list

- **Decisions and counts:** 15 live; parts byte-identical (70/70 rerun); `iaForYou`/`iaInPortfolio` use `iaDecIds` + `iaWaiting`;
  count_check recomputes independently from `ATTN`, `uxDecState` and `HC.decisions` (read); badge 1/1/2 (count_check, and plant A
  bites); Choose keeps the row (probe); act log as D-IA.24 (probe; unguarded, L1); counts agree at 1440 and 390 (probe, count_check
  M4 part).
- **Navigation:** G1 table matches the packet (gates rerun); queue → decision 1 click and inbox → decision 2 clicks measured in a
  real browser. No live link to an unlanded route (crawl, shape_check). Not-found reachable via M1. Way back to the Site: M3.
- **Top bar:** M2.
- **Regressions:** none found on hub, plan or Site pages; parts identical; ia_shots hub set cited (342/0); the inbox opened over the
  hub reads cleanly.
- **No-recommendation bug:** M1; fix in IA-1c.

## What I could not verify

- `tools/layout-evidence.mjs` (needs a served URL; 5490/8990 off limits). ia_shots measures layout instead; my 108 shots agree.
- I did not rerun uxi, G3, plan_switch, check_manifest or the full ia_shots; cited at `cb7f8454a` (`b5739046d` is CSS only, its
  shots rerun by the builder and by me for the decision set).
- The second brand pack was not shot by me.

## Residual risk the packet does not name

- The in-page anchor class (M1) has no gate today; any later reused section with a `#id` link will fail the same way.
- The inbox control's accessible name reads the count twice ("Waiting for you 2, 2 waiting"), as the spec's markup prescribes;
  worth a look in IA-2d's drawer pass.
- The act log persists in `uxMock()` for the tab; a long walkthrough grows "Since you last looked" without a cap (the 7-row cap is
  skipped inside drawers).
