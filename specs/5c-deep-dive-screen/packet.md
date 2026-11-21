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
