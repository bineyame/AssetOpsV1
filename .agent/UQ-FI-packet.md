# UQ-FI-1 / UQ-FI-2 packet (lane D, branch task/UQ-FI-1-2) - built except the P3 frame (held, D-UQFI.8) and captures (coordinator)

Spec: `architect-sequence-client-scope-2026-11-11.md` Revision 6 (6.1-6.4, D-UQFI.1-5). Owner go: `owner-proceed-waiting-items-2026-11-13.md` (provisional).
Commits: `a42dee64b` UQ-FI-1, `8b2d1e61a` UQ-FI-2 part 1; session 2 (2026-11-13): merge of main `e028515df` (SR-5/6/7/11/12; no conflicts), `c358a6f79` codemod rerun (D-UQFI.10: `sites/rangeOverview.css` 12px, `ui/primitives.css` 0.85em -> `--font-size-100`; `--spacing`: 0 files), `8acf207a5` P1-P2 + board-row collapse, `fc2d007a3` P3-P5 + Finding headline prep, `ec7b22d56` P6-P8, `82420ed3e` captures script.

## UQ-FI-1 delivered (D-UQFI.2, D-UQFI.3)
- Inter v4.1: `frontend/public/fonts/InterVariable.woff2`, `OFL.txt` from https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip (zip SHA-256 `9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e`; entries `web/InterVariable.woff2`, `LICENSE.txt`).
  - InterVariable.woff2 SHA-256 `693b77d4f32ee9b8bfc995589b5fad5e99adf2832738661f5402f9978429a8e3`
  - OFL.txt SHA-256 `262481e844521b326f5ecd053e59b98c8b2da78c8ee1bdbb6e8174305e54935a`
- `ui/fonts.css` (@font-face as specified), imported in `main.tsx` before `tokens.css`.
- `ui/tokens.css`: `--font-size-100..800`, `--space-1..16`, `--font-sans` (Inter first), `--font-mono`, `--leading-body`; all 17 role tokens re-pointed per the 6.3 table. Body uses `--leading-body`.
- Tabular figures (`primitives.css`): `table, .money, [data-figure], .v69-metric__value, .value-number, .fact-list__value, .key-values dd, .v69-key-values dd, .price-entry__amount, .global-work-value`.
- Codemod `tools/uqfi-type-codemod.mjs` (idempotent; `--spacing`, `--check`). Type pass: 34 files changed (largest: primitives 84 sizes/3 families, estatePortfolio 70, outcomes 37, w1ux02-money 18, globalWork 16, w1ux02-finding 16). Spacing pass on 14 demo-path files: 13 changed (estatePortfolio 139, outcomes 76, globalWork 37, w1ux02-finding 28, w1f4-verification 24, w4-mini-decisions 23, blocks 15, w2-cold-site 13, findings-index 9, w2-ev-site 8, w4-mini-performance 8, estate 7, w1ux02-site 4).
  - Builder-added mappings: `0.85em` -> 100; `var(--text-md, 1rem)` (undefined token) -> its fallback -> 400. Hand edit: `outcomes.css .oc-info` `font: italic 600 11px/1 Georgia, serif` -> longhands on `--font-size-100` + `--font-sans`.
- Distinct font-size strings: 46 before (`font-size:` values, normalised) -> after: the 7 used scale steps (100-700), 17 role tokens, `inherit`. No `1em`/`100%` remain.
- Style ratchet `tools/checks/style-ratchet.mjs` + `test_style_ratchet.mjs` (7 tests) + baseline (`rawHex` only, 458; rawFontSize/rawFontFamily 0); wired in `check-all.ps1` (guard + fixtures). Non-vacuous: a planted `font-size:11px;color:#abcdef` failed (wall + 2 rises); `--font-size-100: 0.6875rem` failed the wall (378 sizes); both reverted.
- `ui/__tests__/tokens.test.ts` (4 tests): scale exact, all 25 size tokens >= 0.75rem (incl. media overrides), role re-pointing, fonts.css import order, no URL in fonts.css.

## UQ-FI-2 delivered (D-UQFI.4) - partial
- `ui/gapGroup.ts` + `ui/GapGroup.tsx` + `ui/__tests__/gapGroup.test.tsx` (7 tests: by fact, reasons never merge, D-E5.46 order, subject order, single gap unchanged, gap ids kept, no composed text).
- P3 Finding statusbar: "Priority: not assessed" + "Confidence: not assessed" -> one inline line, fact "not assessed", subjects Priority, Confidence (`SiteFinding.tsx`).
- Headline size: no CSS outside tokens uses `--font-size-700/800` or `--text-2xl`; `--text-page-title` only on `.page-header__heading`. Figures that were 24-27px (`.v69-metric__value`, `.v69-money`, `.v69-panel-value`, `.window-money__amount`, Portfolio `.value-number`, `.opportunity-quantity`) now 20px.

## UQ-FI-2 session 2 (D-UQFI.4, .6, .8)
- Headlines: every P1-P8 page already renders exactly one `h1` through `PageHeader`/`SitePageHeader`, first in its header (only an eyebrow may precede it). No move was needed except P3 (below). Shared assertion `frontend/src/test/headline.ts` `expectOneHeadline` (count 1, text, nothing but an eyebrow above the title row); proven non-vacuous (a planted second `h1` in `PageHeader` failed `millVerification`; reverted).
- Collapse list:
  - P1 Portfolio: none built. The only repeated-gap card is the outcome card (`PortfolioOutcomes.tsx`), out of bounds for this lane (UQ-FI-3 owns it; D-UQFI.12). Pulse, opportunity panel, matrix: different facts or links/table cells (rev 6 exclusions).
  - P2 Site board rows (`sites/OutcomeBoard.tsx` `contributorLines`): in the drives column of one row, contributors whose whole server line is the same gap ("Not available yet ...", "Unknown", "... not worked out yet") become one `GapGroup` line naming each contributor (link kept), at the first one's place. Exact-string grouping only; a chip-carrying contributor keeps its own line. MOCK DEVIATION code comment cites D-UQFI.4. Not seen on live data (no DB): whether any row repeats a line today is for the captures to show.
  - Cold board: none (D-UQFI.6); test pins no `GapGroup` and the per-panel lines.
  - P3 Finding status strip: done in part 1.
- P3 (D-UQFI.8): SR-8 is not on main (checked `git log main` at 03:45 UTC), so `SiteAnalyticsFrames.tsx` is untouched. Prepared: `SiteFinding` `onHeadline` prop + exported `findingHeadline(body)` = lifecycle title + the first sentence of its lifecycle sentence, as written. To finish after SR-8: in the mini frame (`SiteAnalyticsFrames.tsx` Finding frame, `onTitle` at the `SiteFinding` call) pass `onHeadline`, render `PageHeader title={h.title} subtitle={h.sentence}`, and drop the duplicated `LifecycleSentence` only if the reviewer agrees it is the moved text; the fuel Finding frame (`SiteFuelFindingFrame`) h1 is today the Site name and needs the same move from `read.value.lines`.
- Per-page tests (one `h1` + text; gap ids pinned on P1): P1 `estatePortfolio` (all six tabs), P2 `siteDetailScreen` (mini), `coldSiteViews` (cold, no collapse), `evSiteMoneyRoutes` (EV), `outcomeBoard` (row collapse: one line, both subjects, links kept, other reason / chip / value untouched, every contributor still named), P3 `miniDecisions` (mini Finding frame), `siteFuelFinding` (count only, text held), `siteFinding` (headline prep x2), P4 `millVerification`, `fuelVerification` (5 states), P5 `miniDecisions` opportunity, P6 `estateRoots` (4 lenses), `s404SiteFindingIndex`, P7 `miniFuelRoutes`, `miniServiceRoutes`, `operationalRecords`, P8 `globalMaintenance`, `sitePrices`.
- `tools/uqfi-captures.mjs` written (CDP like `layout-evidence.mjs`; `capture <links.json> <out-dir> [web-base] --widths 1440,1280 --narrow 390`; links = array of `{case|page|id, url}`; `P1`-`P3` names also get the 390 px sideways check). Syntax and in-page expressions checked; not run: no Chrome on the VPS (`ASSETOPS_CHROME` to point at one) and no serve/DB in this lane. Before/after captures, `measure.json` and the index page: for the coordinator.

## Not built
1. P3 headline in the frames (held, D-UQFI.8; resume steps above).
2. Captures and `measure.json` (coordinator: serve + DB + Chrome). Layout evidence: not run; the 13 px table text / 12 px heads fit at 1280 is unverified (risk 1).

## Tests and checks, session 2 (revision 82420ed3e)
- `npx tsc --noEmit`: exit 0.
- vitest, 96 files (every `grep -rlE "/sites/[A-Z]|from=20"` test file + all P1-P8 page files + outcomeBoard, gapGroup, tokens): 96 passed, 2510 tests passed.
- Guards run alone: style ratchet pass (rawHex 458); `uqfi-type-codemod --check` 0 files; mock-deviation labels OK (178 files); frontend hard-wiring pass; missing-claim scan pass. check-all: for coordinator.

## Tests and checks, part 1 (revision 8b2d1e61a)
- `npx tsc --noEmit`: exit 0.
- vitest, 91 files (every `/sites/[A-Z]|from=20` test file + Portfolio, Finding, cold, findings index, verification, mini decisions/performance, tokens, gapGroup, postW6ShellCss): 91 passed, 2463 tests passed. 7 more CSS-reading files: 36 passed.
- Guards run alone: style ratchet pass; style-ratchet fixtures 7/7; frontend hard-wiring pass; missing-claim pass; mock-deviation labels OK (172 files); node fixtures mock-deviation 14/14, hard-wiring 9/9, evidence 12/12. check-all: for coordinator. Architecture check: not run (coordinator).
- Tests changed (CSS-literal only): `postW6ShellCss.test.ts` x2 (`font-size: 12px` -> `var(--font-size-100)`); `miniDecisions.test.tsx` x3 (spacing snap: 20px -> `--space-5`, 10px 12px -> 8px 12px, 5px 0 4px -> 4px 0 4px). Behavioural: `siteFinding.test.tsx` chip assertions -> one gap line (the collapse itself).

## Known deviations
- GapGroup line is a `div` (inline form: `span`), not `<p>`: `<ul>` cannot sit in `<p>`; the Finding status strip allows inline elements only.
- MOCK DEVIATION for the collapse is a code comment citing D-UQFI.4, not a rendered `MockDeviation` (no register row added).
- Page title below 760px: 23px -> 20px (`--font-size-600`); rev 6 names no phone size.
- Spacing snap excludes `ui/primitives.css` (shared by every page; rev 6 says "other files keep their values").

## Questions for the Architect (session 2; part 1's Q1-4 answered by D-UQFI.6-9)
1. P5: rev 6 names "Daytime solar unused at Kobo mini-grid" as the headline, but that title is not in the opportunity page's read (it comes from the estate opportunities read). The h1 stays "Productive-use headroom at {site}". Add the read, or keep?
2. P2: "the board's day line" - no such element found on the Site boards; h1 = Site name, subtitle = screen description. Which line is meant?
3. P6: "Findings across the estate" is the All-lens panel title; the h1 is "Findings" on every lens. Move it (the panel loses its heading, and the h1 changes per lens) or keep?
4. P7: Fuel and Service h1 is the Site name (v69 Site heading), not a page title. Keep?
5. P1: the only Portfolio card with repeated gap lines is the outcome card, which this lane must not touch (UQ-FI-3). Collapse it in UQ-FI-3, or not for 17 Nov?
6. P3 (after SR-8): moving the first sentence into the header leaves `LifecycleSentence` repeating it in the body on non-SUPPORTED versions. Remove that copy (a move) or keep both?
- For lanes merging after this: rerun `node tools/uqfi-type-codemod.mjs` (add `--spacing` only for the 14 listed files) and the style ratchet.
