# 5c packet: units 1 to 3 (unit 3, the screen)

Implementer (Claude), 2026-11-21, spec rev 3 (main merged at 51b545159). Branch `task/5c-unit3-screen` (from `task/5c-deep-dive-screen` at 4b18a2c77; units 1
and 2 unchanged here). `USER_REVIEW_REQUIRED: true`: merge waits for the owner's walkthrough. Units 1 and 2: see
`handoff.md` (their review runs on `task/5c-deep-dive-screen`).

## Outcome

`/portfolio/month` shows "the month, explained" as the Portfolio tab "The month", in IA-1b's hub shape, rendering
`deep-dive-month-1` exactly as served (D-5C.2). Evidence: `/opt/assetecon/evidence/5c/unit3/`.

## Files (unit 3)

New: `frontend/src/estate/DeepDiveMonth.tsx`, `deepDiveMonth.css`, `deepDiveMonthClient.ts`, `PortfolioTabs.tsx`,
`__tests__/DeepDiveMonth.test.tsx`, `__tests__/fixtures/portfolioTabsOverview.before.html` (the tab row's markup
captured before the move, dates normalised), `tools/deep_dive_gates.cjs`. Edited: `App.tsx` (route, `deepDive` client
prop), `portfolioWords.ts` (tab), `EstatePortfolio.tsx` (tab row and `portfolioHref` moved out, re-exported; `month`
redirects), `estatePortfolio.test.tsx` (the seventh tab in five list assertions), `test/settled.ts` ("Preparing the
month…"), `test/rawSource.d.ts` (`*.json?raw`, `*.html?raw`), `tools/checks/fixtures/chain_coherence/screen_routes.json`
(`/portfolio/month`), register rows R757 to R767, state entry. Outside §0's list: `settled.ts`, `rawSource.d.ts`,
the routes fixture (test plumbing the guards require).

## Done list (spec §8)

- **Q9 hub gates and G3: yes.** `gates-worldA.jsonl`: 9 views pass (lint plus 1440/1280/390 light and dark, A with
  D's headline at 1440 and 1280). 6 blocks; headline 1 line (2 with D's) at 1440 and 1280; L1 ends 511 px (1440 × 900)
  and 547 px (1280 × 720); headline and status end 513 px at 390 × 844; hub 1,738 px at 1440; page width = viewport;
  0 page errors; 0 texts under 12 px; sizes 12/13/14/16/20/24 only. Drawers: dialog, aria-modal, labelled, focus to
  Close, Escape/scrim/Close close, focus returns (test 11; 390 shot: focus "Close", 0 errors).
- **Q10 nothing computed in the browser: yes.** Test 10 pins every tile and step value to the JSON string in place
  and scans the page source for `toFixed`, `toLocaleString`, `Intl.NumberFormat`, `parseFloat`, `toPrecision` and
  `Number(` outside `barWidths`. Month link labels ("September 2026") are made from `nav` codes (labels, not figures).
- Q1, Q2, Q3, Q5, Q6 (screen side): test 10 finds every fixture string on screen (drawers opened one by one), no
  "$1,693.00", the notice visible outside any drawer, the status line `role=status` naming Kisiwa, the Assure drawer
  lines `[standing.text, *standing.details]`; World B shows no "not yet reconciled".

## Tests and gates

- Tests first: `tests-first.txt` (module missing, 0 tests). Focused vitest: `DeepDiveMonth.test.tsx`,
  `estatePortfolio.test.tsx`, `estatePortfolioRoutes.test.tsx`: 3 files, 110 passed (15 in the new file). `tsc
  --noEmit` clean; `vite build` clean.
- Plants, each failing as named: gates `block`, `headline`, `levels`, `height`, `fold`, `status`, `scroll`, `lint`
  (`plant-*.jsonl`, `gates-summary.txt`: exit 1 each, world A exit 0). Frontend: P5 fails test 10, P8 fails test 10
  (two cases; it survived the first draft, so test 10 was strengthened), P12 fails test 11 (`plants-frontend.txt`).
- `check-architecture.ps1`: passed. `check-agent-workflow.ps1`: passed.
- check-all (fast), once: `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1`
  at b5db599d8, 146.8 s wall: 40 of 42 blocking guards passed; failed "Missing-claim orphan scan" and its fixtures:
  the literal heading "What is not available yet" (`DeepDiveMonth.tsx:39`). Fixed at 3c3183d84 by a named exemption
  (`DD_NOT_AVAILABLE_TITLE`, decision spec §5.2, D-5C.11, D-5C.14) in `missing-claim-scan.mjs`: scan passed, fixture
  tests 26/26; a planted "Not available yet" literal in the page still fails the scan. Review point: a guard
  exemption added by the builder. Log `/opt/assetecon/evidence/5c/unit3/check-all.log`.
- `chainScreenRoutes.test.ts` fails on this branch before and after 5c: App registers `/sites/:siteId/uploads`, which
  the routes fixture lacks (not a 5c route; left for its owner).

## Layout evidence and G3

Shots (`shots/`): `A-1440x900-{light,dark}.png`, `A-1280x720-…`, `A-390x844-…`, `A-with-D-headline-…`,
`A-390x844-{light,dark}-fuel-cost-drawer.png`. `measure_screen.jsonl`: six views, 0 errors, under12 0, width =
viewport, "Where the gap comes from" above the fold at 1440 and 1280; lowContrast 14 per view, all in shared parts
(the shell's demonstration bar 4.12:1 and the shared `DataTable` header cells 4.35:1), none in the page's own CSS.
`H-390x844-light-fuel-cost-drawer-nested.png`: World H's parts nested under Diesel used. Served from the World A fixture, not from a
`_test` database (MBQ6). Dark shots render the light theme: the live product has no dark theme (MBQ3).

## Known deviations

- MD1 to MD10 as spec §7 (R757 to R766). MD11 (R767, open): steps have no bars on the gap's scale; the JSON serves
  no plain step decimals (MBQ5).
- 401 shows the spec's sentence, not the served "Sign in to continue." (MBQ2). KPI figures 24 px, not 32 (MBQ4).
- Spec rev 3 (merged from main): D-5C.21 nested drivers from `children` (test 11: H's three parts inside Diesel
  used's `<li>`); D-5C.22 caps on screen (test 11: 12 rows show 10 then 12; 9 not-available rows show 8 then 9);
  D-5C.20 and D-5C.23 render as served (the fixture on this branch predates the backend fix round; test 10 reads the
  fixture, never a literal, so "Estimated, not yet reconciled" and "(at budget)" flow through when it lands).
- `.agent/owner-ui-ux-guidance-2026-10-25.md` is not in either tree; the standing brief and `uiux-guide.md` were used.

## Mid-build count

7 (MBQ1 from unit 2; MBQ2 to MBQ7 from unit 3, `mid-build-questions.md`), each on its default.

## Residual risk and review focus

- The backend fix round (H1, H2 on `task/5c-deep-dive-screen`) changes served strings; the screen renders whatever
  is served, but test 10 reads the fixture, so a fixture change flows through. Merge that branch in when it lands.
- Review: the drawer's focus trap, the 390 step rows, the not-available list's reading order, MD11.

## Round 3b: the screen on the merged backend (main 08f3bf86c merged at 70a654d29), 2026-11-21

Evidence: `/opt/assetecon/evidence/5c/unit3b/`.

- **Merge.** One conflict, `.ai/state/index-3.md`: main's rows 185 to 187 (0K4b, 0K4c, 0K4e) kept, 5c's row renumbered
  188. Under the 2k-token cap (209 words).
- **Payload.** `DeepDiveDriver.key` and `.children` are required (D-5C.21: every driver carries both; a leaf has
  `children` []). No other page change was needed: the page already rendered each served string as given, so "(at
  budget)" (D-5C.23), the headline's evidence chip (D-5C.20, now "Estimated, not yet reconciled"), the record words
  (D-5C.25), KES figures, the M3 out-line and the L7 headline all flow through.
- **Served worlds.** `backend/tests/fixtures/5c/make_screen_worlds.py` writes two screen fixtures from the backend's
  own view (never by hand): `frontend/src/estate/__tests__/fixtures/deep_dive_world_h.json` (World H) and
  `deep_dive_currency_mismatch.json` (World X: Kobo in KES with O&M and staff not compared; Kisiwa in USD with fuel
  cost not compared; Mto's actual in KES against a USD target). X serves the L7 headline "Contribution for October is
  not available yet: the Sites' figures are in different currencies." with `evidence` [], Mto's line "Mto: not
  compared: its actual and its target are in different currencies (KES and USD)." in every step drawer, fuel cost
  "−KES 600.00" beside O&M "$0.00", and the Optimize heading and card "Not available yet" for figure and word (L9).
- **Tests (test 11, new describe).** The hand-written World H (spec test 11 keeps it by hand) must equal the backend's
  World H in `tiles`, `bridge`, `fresh`, `outcomes`, `headline`, so it cannot drift. World X: every shown string, the
  headline exactly and with no chip, no tile bar, the Optimize card and heading, each step value character for
  character, Mto's line in each drawer, no "$" in the KES drivers. World A and X: every money figure on the page (read
  one text node at a time) is one the JSON serves. World B now strips the headline's evidence too (its word gained
  ", not yet reconciled"). `fresh.untracked_text` is left out of the page-wide string check: it is read in the Assure
  drawer, which test 11 already asserts.
- **Plant X1** (page puts "$" on a KES step: `step.value.replace("KES ", "$")`) fails the World X test:
  `plant-X1-dollar-on-kes.txt`.
- **Vitest** (`DeepDiveMonth.test.tsx`, `estatePortfolio.test.tsx`, `estatePortfolioRoutes.test.tsx`): 3 files, 115
  passed (20 in the new file). `tsc --noEmit`: exit 0. `vite build`: exit 0 (`vite-build.txt`).
- **Gates** (`tools/deep_dive_gates.cjs`, now with `--world` to name views and shots), served by `vite preview` of
  this build on 127.0.0.1:8797 (stopped after): World A exit 0 (8 views; 1280 × 720 headline now 2 lines, L1 ends 575
  px, because the chip is longer), World X exit 0 (8 views; L1 ends 455/459 px; 390 width 390), World H exit 0; the
  eight plants on A each exit 1 (`gates-summary.txt`, `plant-*.jsonl`). 0 page errors, 0 texts under 12 px.
- **Shots** (`shots/`): `{A,H,X}-{1440x900,1280x720,390x844}-{light,dark}.png` and the D-headline views; drawer shots
  `{X,H}-{390x844,1440x900}-light-fuel-cost-drawer.png` (`drawer-shots.jsonl`). Dark renders light (MBQ3).
- **Drawer shots** at 390 and 1440: World X's fuel-cost drawer shows drivers "−KES 600.00", "−KES 37.50", "−KES 412.50",
  "−KES 150.00", "KES 0.00" and the out-lines "Kisiwa: not split this far." and Mto's currency line; focus on Close,
  0 errors, width = viewport.
- **check-all (fast), once:** `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File
  tools/check-all.ps1` at 915d42288, 313 s wall: all 42 blocking guards passed (missing-claim scan passed with the
  exemption unchanged). `check-architecture.ps1` and `check-agent-workflow.ps1`: passed. Log `check-all.log`.
- **Guard (for the reviewer).** The missing-claim scan exemption `DD_NOT_AVAILABLE_TITLE`
  (`tools/checks/missing-claim-scan.mjs:86`) stays as it was: a builder-added named exemption for the section title
  "What is not available yet" (spec §5.2, D-5C.11, D-5C.14). Review point unchanged.
- **Register.** R766 now names the served word and the no-figure headline with no chip.
- **Review point.** In World X the Contribution and Gap tiles show "Not available yet" at full figure size beside a
  "Not available yet" chip (both served); the plan tiles mute theirs by key. The page does not read words to style
  them; whether the tile should mute a value with no figure is a served-shape question for the Architect.

## Screen fix (spec rev 4 §11 "Screen fix"; D-5C.26 to D-5C.28, L1 to L5), 2026-11-21

Evidence: `/opt/assetecon/evidence/5c/unit3c/`. Main (backend fix r5, 27b9fcd2a) merged at eb73d2c0a.

- **Merge.** Four conflicts, all docs: `.ai/state/index-3.md` (main's rows 188, 189 kept, 5c's row renumbered 190),
  `specs/INDEX.md` (5c row kept in_review, DDR row from main), `spec.md` status line (main's rev 4 with in_review),
  `review.md` (both sections kept: unit 3 round 1, then backend fix r5).
- **Generator (§11 1).** `make_screen_worlds.py` imports only `deep_dive_worlds.world_h` and `world_x` (no
  `test_5c_deep_dive_view` import, no private helper, no patch of its own; `self.word`, `NO_CURRENCY`, `t._in_kes`,
  `t._gone` gone). Both fixtures regenerated: H gains the bars and scale; X loses its chips beside no figure, its
  shares, and serves `bar`/`scale` null.
- **L4 (§11 2, test 17).** `backend/tests/test_5c_screen_worlds_fresh.py` (no database) builds both worlds through
  the generator's `worlds()` and compares bytes with the committed files; on a mismatch it fails with "<name> is
  stale: rerun make_screen_worlds.py". Plant: World X's "−KES 600.00" changed to "−KES 601.00" → `1 failed, 1 passed`
  with that message (`plant-L4-stale-world.txt`); file restored by `git checkout`.
- **D-5C.26 (§11 3).** `mute(word, className)` adds `dd-na` when `word` is null: tile values, step values, driver
  values, and an outcome card's value in its no-drawer branch (so a card with a drawer, Assure, is never muted). The
  `startsWith("plan")` test is gone; no key or text test remains. The not-available list's own classes moved from
  `dd-na`/`dd-na__*` to `dd-gaps`/`dd-gaps__*` so `dd-na` means one thing. `.dd-kpi__value.dd-na` keeps the old
  tile size.
- **D-5C.27 (§11 4).** Each step button ends in `.dd-wf__track` (aria-hidden, 20 px, 1 px left rule
  `--border-strong`, pinned to the last grid column `--dd-track: 30%`; at ≤600 px a full-width row). A served `bar`
  draws `.dd-wf__bar--{tone}` at `left: {bar.left}%`, `width: {bar.width}%` (12 px, top 4 px, radius 2 px; lowers
  `--status-red-text`, raises `--status-green-text`). A served `scale` draws `.dd-wf__scalerow` (aria-hidden) above
  the `<ol>`, same grid and padding as the step rows, with the target mark at `target_at` and the actual end mark at
  `actual_at` (`translateX(-100%)`), ux.css `:597-601` under `dd-` names. The served strings go straight into `style`;
  no `Number(`, `parseFloat` or arithmetic was added. Types: `DeepDiveStep.bar`, `DeepDiveStepBar`, `bridge.scale`.
  Register R767 set to resolved.
- **L1, L2 (§11 5).** The drawer's Escape and Tab cycle moved from the panel's `onKeyDown` to a `document` listener
  while open; Tab from outside the panel goes to its first (Shift: last) control. `Capped` owns its `<li>` and, after
  "Show all {n}", focuses the first newly shown row (`tabIndex={-1}`). `body.dd-locked` (`overflow: hidden`) is added
  on open and removed on close and unmount (effect cleanup).
- **L5 (§11 5).** `deep_dive_gates.cjs` adds the two D-headline views only for `--world A` (named `A-with-D-…`).
- **Tests (§6 rev 4, unit 3).** New describe in `DeepDiveMonth.test.tsx`, 5 cases: A's bars (revenue 0.00 / 11.38
  lowers, fuel cost 11.38 / 88.62, O&M and staff tracks empty, every track aria-hidden) and the two scale marks with
  their served texts; World X no bar, no scale, no chip "Not available yet", `dd-na` on contribution, gap, revenue
  step and Optimize card, not on Assure or fuel cost; the mute follows the shape (a contribution tile with word null
  mutes, a plan tile with a word does not, a driver with word null mutes); L1 (A's revenue drawer at 12 Sites: after
  "Show all 12" focus is on row 11, `tabIndex` −1; with focus on `body`, Tab returns into the dialog and Escape on
  `document` closes and returns focus to the opener); L2 (lock while open, not after Close, not after unmount). World
  X's card test now asserts no word chip (revises L9). jsdom writes a served "0.00%" as "0%"; the test asserts the
  served bar object and the style together.
- **Plants (vitest; each run of `DeepDiveMonth.test.tsx` exits 1, file restored after each; `plants.txt`):** mute by
  key restored (2 failed), card not muted (1), step not muted (2), driver not muted (1), bar width from `left` (1),
  no scale (1), no focus after Show all (1), keys on the panel (1), no body lock (1), lock kept after close (1).
- **Vitest** (`DeepDiveMonth.test.tsx`, `estatePortfolio.test.tsx`, `estatePortfolioRoutes.test.tsx`): 3 files, 120
  passed (25 in the 5c file). `tsc --noEmit`: exit 0. `vite build`: exit 0 (`vite-build.txt`). Backend
  `test_5c_screen_worlds_fresh.py` + `test_5c_deep_dive_view.py`: 187 passed.
- **Gates** (`vite preview` of this build on 127.0.0.1:5577, stopped after): World A exit 0 (9 lines: lint plus 8
  views), World X exit 0 and World H exit 0 (7 lines each: lint plus 6 views; L5). A: 6 blocks; headline 1 line at
  1440, 2 at 1280 (2 at both with D's); L1 ends 511 px (1440 × 900) and 575 px (1280 × 720); hub 1,758 px at 1440
  (+20 px for the scale row; was 1,738); page width 390 at 390; 0 errors; 0 texts under 12 px. X: L1 ends 441 / 459
  px; hub 1,602 px. The eight gate plants on A each exit 1 (`plant-*.jsonl`).
- **Known deviation KD4 (layout; for the reviewer).** Spec §5.3 places the track as the last grid column "at widths
  above 600 px". At a 768 px viewport the shell's navigation leaves the hub 488 px, and the six-column row (120 + 76
  + chip 188 + track 30% + gaps) widened the page to 852 px (measured: `.dd-wf__track` right edge 848 to 852 px). The
  step row now also takes the ≤600 px layout when its section is under 720 px wide (`@container`, `.dd-section`
  `container-type: inline-size`); the viewport rule at 600 px is unchanged. After the fix: no element past the
  viewport at 768 except the tab row and by-Site table, which scroll in their own boxes (as before); at 1280 the row
  has six columns (track 285 px); at 1024 it stacks (section 744 px).
- **D-5C.29 (coordinator heads-up).** The cash sentence rewrite is on `fix/5c-cash-r6`. The page prints the served
  text and table as given, so no screen change; once r6 merges, merge `main` here and rerun `make_screen_worlds.py`
  (test 17 fails until then on any drift).
- **Gates rerun after KD4** (same build served on 127.0.0.1:5577, stopped after): A, X, H exit 0 with the figures
  above unchanged; the eight plants exit 1 again (`gates-world*.jsonl`, `plant-*.jsonl`).
- **Bars and drawers in the browser** (`drawer-shots.jsonl`, scratch script; worlds A, X, H at 1440 × 900, 768 × 1024
  and 390 × 844): every step track has the same left edge and width, and the scale's box equals it (A at 1440: tracks
  and scale at x 1050, 333 px wide; at 768: 273, 438; at 390: 41, 308); A's bars at 1440: revenue 37.8 px from the
  track start, fuel cost from 1088.8 px, 294.2 px wide; X: no bar, no scale. Page width equals the viewport in all
  nine. Opening fuel cost: `body.dd-locked` true, focus on Close; Escape closes and the lock is gone; 0 page errors.
- **Shots** (`/opt/assetecon/evidence/5c/unit3c/shots/`): `{A,H,X}-{1440x900,1280x720,390x844}-{light,dark}.png`,
  `A-with-D-headline-{1440x900,1280x720}-light.png`, and `{A,H,X}-{1440x900,768x1024,390x844}-light-bridge.png` and
  `-fuel-cost-drawer.png`. Dark renders light (MBQ3).
- **Not verified:** a screen reader pass; the screen served from a real `_test` database (MBQ6).
- **check-all (fast), once:** `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File
  tools/check-all.ps1` at c4053336c, 144 s wall: "All 42 guards passed (blocking; 0 advisory, 0 warned)" (architecture
  seams, agent workflow, missing-claim scan included). Log `/opt/assetecon/evidence/5c/unit3c/check-all.log`.
- `USER_REVIEW_REQUIRED: true`: next is a fresh re-review at verification depth on these items, then the owner's
  walkthrough before merge.

## Screen fix, after D-5C.29 (cash fix r6 on main), 2026-11-21

Evidence: `/opt/assetecon/evidence/5c/unit3c/r6/`. Main (8bac2bed4) merged at ebb25e162. Two conflicts: index-3
(main's rows 190, 191 kept, 5c renumbered 192) and the spec status line (rev 5, in_review).
- **Worlds.** `make_screen_worlds.py` rerun: World H's cash text now reads the D-5C.29 sentence (one line changed);
  World X unchanged ("Cash collected in October is not available yet."). Test 17 passes again.
- **Cash on screen.** No page change: the sentence and table are printed as served. New vitest case (D-5C.29): A's
  cash `<p>` is "Of $9,688.00 billed for October, $8,870.00 has been collected, $150.00 is paid but in transit and
  $668.00 is still outstanding.", the head row equals `columns` (Billed second), rows and total equal the JSON, and
  the cash section holds no "expected". Plant (page drops " billed" from the sentence): exit 1, 2 failed (this case
  and test 10) (`plant-cash-text.txt`). Browser (`a-shots.jsonl`, 1440/768/390): the same sentence, head row
  Site, Billed, Collected, In transit, Outstanding, total "$9,688.00 · $8,870.00 · $150.00 · $668.00".
- **Tests.** `tools/run-host-tests.ps1 -- backend/tests/test_5c_screen_worlds_fresh.py
  backend/tests/test_5c_deep_dive_view.py`: 201 passed. Vitest (3 Portfolio files): 121 passed. `tsc` exit 0;
  `vite build` exit 0.
- **Gates** (`vite preview` 127.0.0.1:5577, stopped after): A exit 0 (9 lines), X exit 0 (7), H exit 0 (7); figures
  as in the previous section (A hub 1,758 px at 1440, L1 511/575 px, width = viewport, 0 under 12 px, 0 errors).
- **A shots** (`r6/shots/`): the gate views `A-{1440x900,1280x720,390x844}-{light,dark}.png`, the two D-headline
  views, and `A-{1440x900,768x1024,390x844}-light-full.png` (cash table open) and `-fuel-cost-drawer.png`. The full-page
  shot shows the shell's sticky header partway down where the page scrolled (a capture artefact).
- **check-all (fast), once** at bb6941806: 145.7 s, "All 42 guards passed (blocking; 0 advisory, 0 warned)"
  (`r6/check-all.log`). `USER_REVIEW_REQUIRED: true`: fresh re-review, then the owner's walkthrough before merge.
