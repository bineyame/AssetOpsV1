# Review: Site page redesign, round 1 (discovery)

Branch `task/uiux-design-model`. Reviewed a snapshot of a77defa0b, covering 6b742bffa (the Site page), b6066fa43 (merge of main) and a77defa0b (regenerated fixtures and a one-line copy fix). Reviewer: a fresh Claude reviewer who did not author the work. Date: 2026-11-20.

## Summary (round 1)

- **Verdict: REVISE.** There is 1 High, 5 Medium and 7 Low findings.
- **High.** On the three Metro Sites, the first KPI tile shows *cost per required departure met* ($36.69, $23.71, $30.14), but the trend under it is the change in *monthly total cost* ("+$1,246 against Sep"). The tile mixes two measures. At Kasarani it reads "$23.71, Target $23.71, +$180 against Sep" while the gap is $0 in both months.
- **The arithmetic is right.** It holds on all 9 Sites against `derived-values.json` and history:
  - driver values sum exactly to the Site gap;
  - the trend deltas match DERIVED.history to the dollar;
  - Kasarani shows "No driver moved the result";
  - Ruiru shows "+$20 not attributed yet";
  - the Actions in hand match `demo_workflow.actions` (Kobo 3, Kisiwa 1, Mto 2, Mwea 1, Thika 1, Kirinyaga 1, Embakasi 1, Kasarani 1, Ruiru 0).
- **Where the copy goes wrong.** In 6 of 9 Sites, L1 and L2 call decisions "open" or say they "need a decision" when they are already chosen or released. The third tile shows "value if chosen" for a decision that is already released (Kobo). At Kobo the displayed driver effects add to −$561 against a −$562 gap, a rounding error.
- **Gates.** All 10 pass on a77defa0b. check_manifest needs the full `Docs/` tree; on the dispatch's partial snapshot it fails H9, which is an artefact of that snapshot (see the table).
- **Plants.** 5 of the 7 planted violations fail cleanly. The "no sideways scroll" plant passes, because `.workspace{overflow-x:clip}` makes that check impossible to fail. The "driver navigates" plant crashes the gate instead of reporting a FAIL.
- **Interaction grammar holds.** Driver rows open their drawers in place with no hash change, Esc returns focus to the opener, and only named links navigate. Tabbing 160 times on 3 Sites at 1280×720 and 390 never put focus fully under the sticky bar.

## Findings

### H1 (High, content truth): the Metro cost tile's trend uses a different measure from the tile
- **Route and shots:** `#/site/embakasi`, `#/site/kasarani` and `#/site/ruiru` (op metro), at every width. Shots: `review-site/embakasi-1440-neutral-dark-top.png`, `kasarani-1440-ea-light-top.png`, `embakasi-390-ea-light-top.png`.
- **Code:** `loop-ux.js` `uxSiteTiles` (line ~356) calls `uxTrendNA(op, cost ? 'cost' : 'contribution', sk)` under a tile whose value is `fmtU(t.actual, t.unit)` (cost per required departure met). `DERIVED.history['metro-bus'].sites[*].cost` is the monthly **total** cost (Embakasi Oct 22,744.80, Sep 21,499.20).
- **What is wrong:**
  - The tile reads "$36.69 · Target $31.52 · +$1,246 against Sep". A reader takes +$1,246 as the change in cost per departure.
  - At Kasarani the tile reads "$23.71 · Target $23.71 · +$180 against Sep" beside "Gap $0 · $0 against Sep", which contradicts itself.
  - The sparkline's aria-label reads "Jul +$20,286 … Oct +$22,745": a cost shown as a signed gain.
- **Why it matters:** this is a wrong figure on the L1 tile of 3 Sites. The standing brief puts "every number honest with its basis" above layout.
- **This slice made it visible:** the history lookup by Site name (R742) is what turns the tile trend on for Sites.
- **Sweep:** the Portfolio cost tile (line ~331) uses the same `uxTrendNA(op,'cost')` under the metro portfolio figure. Check it too.
- **Fix, either of:**
  - (a) Add a per-departure series to history and use it. The "How it has moved" section can keep total cost.
  - (b) Label the line as what it is ("Monthly cost +$1,246 against Sep"). Unsigned cost wording would also avoid "+" reading as good.
- **Acceptance gap:** yes, under the guide's P2 "money in context" and the dispatch's "no invented or contradictory figures".

### M1 (Medium, content and copy): "open" and "needs a decision" count decisions already chosen or released; the tile says "value if chosen" of a released one
- **Routes:**
  - `#/site/kobo`: both decisions are released or awaiting approval. Even so, the headline says "2 decisions open" and the panel says "Needs a decision at this Site 2". Tile 3 shows "+$2,916 value if chosen · Stop the generator at 70%". That decision is *Released: Actions under way*, and two of its Actions show Released in the Actions in hand panel.
  - `#/site/thika` and `#/site/kasarani`: both are released, yet they still say "1 decision open" and "Needs a decision 1". Kasarani shows "+$150 value if chosen".
  - `#/site/mwea`, `#/site/kirinyaga` and `#/site/embakasi`: each is chosen and awaiting approval, yet shows "value if chosen".
- **Shots:** `kobo-1440-ea-light-full-closed.png`, `kasarani-1440-ea-light-top.png`.
- **What is wrong:**
  - L1 and L2 tell an executive something needs deciding when nothing does (no Decide button appears anywhere).
  - The tile labels as hypothetical a value that is already committed in the plan.
  - The sticky pill turns green while it says "2 open".
- **Fix:**
  - Split the count by state: "2 decisions: 1 under way, 1 awaiting approval". Keep "need a decision" for the `choose` state.
  - Title tile 3 by state: "Value in the plan", or "value if chosen" only for decisions still to choose.
  - Name the panel by what it holds: "Decisions at this Site".
- **Source:** the queue and `uxSiteTiles` predate this slice, but the Site L1 is this slice's deliverable (guide §2.3 Site row: "open decisions as a count with money").

### M2 (Medium, content): at Kobo the displayed driver effects do not add up to the displayed gap
- **Route and shot:** `#/site/kobo`, the board. Shot: `kobo-1440-ea-light-drawer.png`.
- **What is wrong:** the underlying drivers are −412.5, −150, +38 and −37.5, which sum to −562 exactly. `usdW` rounds the halves to −$412 and −$37, so the rows show −412, −150, +38 and −37, which add to −$561 against a gap of −$562.
- **Fix:** round with largest remainder so the shown rows sum to the shown gap, or show cents when a half occurs. Add a gate that sums the *displayed* board effects against the displayed gap.

### M3 (Medium, gate): the "no sideways scroll" check cannot fail
- **What is wrong:**
  - The gate tests `documentElement.scrollWidth > innerWidth`.
  - `theme.css:71 .workspace{overflow-x:clip}` swallows any wide child, so the page never scrolls; the content is clipped instead.
  - A planted 3,000 px element in `uxSitePage` passes all 27 Site checks (`rsite-r1/plant-overflow.log`: 28 PASS).
- **Current content is fine:** my own probe of all 9 Sites at 390 and 1280, with sections open, found 0 elements past the viewport outside a scrolling frame.
- **Fix:** assert that no element in `.canvas` extends past the viewport or its region unless it sits inside an `overflow-x:auto|scroll` frame. `ux_interaction_check.cjs:74` already does this for chips; generalise it.

### M4 (Medium, answer-titled standard): "Operations measures" has a topic line, not an answer, and the gate accepts it
- **Route and shot:** every Site. Shot: `embakasi-1280x720-neutral-light-sticky.png`.
- **What is wrong:**
  - The answer is the same fixed string on all 9 Sites: "Availability, field visits and output per visit, against target". The long-page standard says a closed section "should still be useful".
  - The gate only checks that the answer is longer than 4 characters.
- **Fix:** derive the answer from the measures, for example "Availability 46.7%; target not declared". Make the gate reject an answer that is identical across Sites when the section's data differs.

### M5 (Medium, content): the "Service and assets" answer disagrees with its own table at Embakasi
- **Route and shot:** `#/site/embakasi`. Shot: `embakasi-1440-ea-light-full-open.png`.
- **What is wrong:** the answer reads "1 issue open on service or assets (at its limit)", but every row of the table below reads "At its target". The answer counts the queue's protect-heading findings (here the 500 kW peak-import limit). The table is `protectSite()` and does not list that limit.
- **Fix:** derive the answer from the same rows the section shows, or add the limit that is in issue to the table.

### L1 (Low): "$0.00 under target" at Kasarani
- **Route:** `#/site/kasarani`, the headline.
- **Fix:** say "on target in October" when the variance is 0. Ruiru's "$0.04 under target" is fine.

### L2 (Low, guide §3.5): at 390 the first queue card is not visible without scrolling
- **Shots:** `kobo-390-ea-light-top.png`, `embakasi-390-ea-light-top.png`.
- **What is wrong:** only the queue panel's heading is visible. Tile 3 runs to 5 or 6 lines of option text on a phone.
- **Fix:** clamp the option text in tile 3 to 2 lines on a phone.

### L3 (Low, claim): no slot for the Operations tab is rendered
- **What is wrong:** `SITE_TABS_PENDING = ['Operations']` (`loop-ux.js:856`) is never read. The tabs are Overview and Financials only, so the "reserved slot" exists only as a constant.

### L4 (Low, gate): the "drivers open in place" plant crashes the gate instead of reporting
- **What happens:** with a driver that navigates, the gate throws `Cannot read properties of null (reading 'click')` on the next driver. The run exits 1, but with no FAIL line, and the rest of the checks are lost (`plant-navigate.log`).
- **Fix:** guard the lookup and report `nav++`.

### L5 (Low): the trend table formats cost inconsistently
- **What is wrong:** the Metro "How it has moved" table shows cents ("$20,285.76") while the gap row is whole dollars, and the cost row is signed against the contribution convention.

### L6 (Low): "Where value leaks" repeats itself when open
- **What is wrong:** the open section repeats its own heading and its answer line inside the panel (`embakasi-1440-ea-light-full-open.png`). The guide (§2.2) says a caveat is said once per scope.

### L7 (Low, UX polish)
- **Driver drawer:** "Evidence" lists only the same figure again ("−$412"), with no record or source line (`kobo-1440-ea-light-drawer.png`, `mwea-390-neutral-dark-drawer.png`).
- **Actions in hand rows:** they wrap awkwardly at 1440: the owner role is in bold, then "· Joseph", then "· due" on separate lines.
- **Queue controls:** the full queue control bar (Status, Sort, Group, Compact) is shown for 1 or 2 items.

Leading SaaS products would tidy these before shipping, but they do not block.

## Checks the dispatch asked for

### 1. Content truth on all 9 Sites, by hand against DERIVED

**Headline gap and history.** The October values in history equal the page's actual and gap on every Site.

| Site | Gap shown | Drivers on screen (sum) | Trend in the tile (history) | Actions in hand (manifest) |
|---|---|---|---|---|
| Kobo | −$562 | −412 −150 +38 −37 = **−561** (raw −562.0) **M2** | −$8 (883−891.45) / gap −$90 ✓ | 3 = 2 KOB-STOPSOC + BAT-EVIDENCE ✓ |
| Kisiwa | −$185 | −185 ✓ | −$113 / −$150 ✓ | 1 KIS-REPAIR ✓ |
| Mto | −$105 | −105 ✓ | −$30 / −$90 ✓ | 2 MTO-INV-CLAIM ✓ |
| Mwea | −$468 | −620 +155 −3 = −468 ✓ | −$91 / −$117 ✓ | 1 ✓ |
| Thika | −$108 | −108 ✓ | −$54 / −$86 ✓ | 1 ✓ |
| Kirinyaga | −$194 | −194 ✓ | −$12 / −$50 ✓ | 1 ✓ |
| Embakasi | −$3,204 | −2,604 −600 ✓ | **+$1,246 is total cost (H1)** / −$809 ✓ | 1 ✓ |
| Kasarani | $0 | none: "No driver moved the result in October" ✓ | **+$180 is total cost (H1)** / $0 ✓ | 1 ✓ |
| Ruiru | +$20 | +19.68: "+$20 not attributed yet" ✓ | **+$259 is total cost (H1)** / +$148 ✓ | 0 ✓ |

**Other checks:**
- The headline count, the queue's "n of N" and the sticky bar's count agree on every Site, because they come from the same source as the queue.
- Section labels are identical on all 9 Sites.

### 2. Interaction grammar
- Clicking a driver opens its drawer with no hash change. Focus goes to the close button and Esc returns it to the row's button. This held on all 5 Sites I drove (shots.log).
- The board is inside a collapsed section. The gate clicks hidden buttons through JS, so it does not prove that the rows are reachable while the section is closed. They are, through the section toggle.
- Focus under the sticky bar: 0 cases of focus fully hidden over 160 tabs each on Kobo, Thika and Embakasi, at 1280×720 (bar at the top) and at 390 (bar at the bottom).

### 3. Plants (my own copy of the gate's Site block, `rsite-r1/site_gate.cjs`, against planted bundles)

| Gate | Plant | Result |
|---|---|---|
| Sections answered | blank the "How it has moved" answer | FAIL ×27 ✓ |
| One h1 | a second `<h1>` on the Site page | FAIL ×27 ✓ |
| No sideways scroll | a 3,000 px div in the Site page | **PASS ×27: the gate is inert (M3)** |
| Sticky bar | remove `data-ux-sticky` from the Site bar | FAIL ×27 ✓ |
| Drivers open in place | the driver button sets `location.hash` | exits 1 by crash, no FAIL line (L4) |
| Phone trend in words | remove the CSS that hides the sparkline at ≤600 px | FAIL ×9 (all phone runs) ✓ |
| Section-structure parity | drop "Where value leaks" at Ruiru only | FAIL ×1 (the parity check) ✓ |

### 4. Gate table (a77defa0b; heavy-slot; `source /opt/assetecon/tools/pw/env.sh; export LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH`)

| Gate | Result |
|---|---|
| render_text | 237 renders, 0 script errors |
| vocab_check | 0 hits |
| copy_check | 17,585 segments, 0 hits |
| hand_typed_scan | exit 0 |
| plan_switch_check | 778 passed, 0 failed |
| design_lint | exit 0 (only residual colour-literal notes) |
| shell_check | 0 fails |
| ux_interaction_check | 247 PASS, 0 FAIL (includes the 27 Site runs and the parity check) |
| check_manifest.py | on the full `Docs/` tree at a77defa0b: **7,571 passed (2,869 history), 0 failed**. On the dispatch's partial archive: 7,525 passed, 1 failed (H9 baseline 4,456 ≠ 4,501), because figure documents outside the archived folders are missing. That failure is a snapshot artefact, not a defect. |
| check_alignment.py | full tree: 114 passed, 0 failed (partial: 102 / 0) |

**Bundle:** `index.html` rebuilt with `node build.mjs` is byte-identical to the committed file.

### 5. Screenshots (looked at)

`/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/review-site/` holds 49 shots:
- **Kobo, Mwea and Embakasi:** 1440 (East Africa pack, light: top, drawer, full page open and closed), 1440 (Neutral pack, dark: top and drawer), 1280×720 (Neutral light: top and sticky; East Africa dark: sticky), 390 (East Africa light: top, sticky, full page open; Neutral dark: top and drawer).
- **Kasarani and Ruiru:** 1440 East Africa light only.

**What they show:**
- Layout is clean in both packs and both themes.
- No content overflows the page.
- The sticky bar at 1280×720 sits under the top bar's position. At 390 it moves to the bottom and drops the gap figure, keeping the Site and the count.

## Residual risk not in the packet
- `uxSiteActions` calls `actionState(op, a, true)`, so an item that a plan switch leaves out still shows Waiting or Released on the Site page, as it does on the Actions screen. Only the Plan page shows "returned to creator".
- With every section open, the page is 4,100 to 4,400 px at 1440, and there is no in-page section navigation (point 4 of the long-page standard). It works closed (about 1,800 to 2,460 px).
- The dispatch's snapshot recipe is insufficient for check_manifest. Future reviews should archive the whole `Docs/` folder.
- The shared scratchpad was cleaned by another reviewer mid-run. I re-ran my plants in `rsite-r1/`, and confirmed that the shared `snap/` was byte-identical to a77defa0b (`diff -rq` against a fresh archive: only generated outputs differ), so the gate results stand.
