# UQ-FI-1 / UQ-FI-2 packet (lane D, branch task/UQ-FI-1-2) - PARTIAL

Spec: `architect-sequence-client-scope-2026-11-11.md` Revision 6 (6.1-6.4, D-UQFI.1-5). Owner go: `owner-proceed-waiting-items-2026-11-13.md` (provisional).
Commits: `a42dee64b` UQ-FI-1 (complete), `8b2d1e61a` UQ-FI-2 (partial). main merged at `53de574b9`.

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

## Not built (resume here)
1. Headline moves P1-P8 (one h1 = 6.1 headline text; P3 h1 = Finding title then first sentence, statusbar under them). P3's h1 today is the lifecycle title set via `onTitle` (`SiteFinding.tsx:134`, frame `SiteAnalyticsFrames.tsx:771`, a file SR-5/SR-8 are changing).
2. Portfolio card / board outcome-row collapses ("Not available yet"/"Unknown"/"not worked out yet").
3. Per-page tests P1-P7 (one h1; gap id/fact set unchanged).
4. `tools/uqfi-captures.mjs`, before/after captures, `measure.json` (needs a serve + DB: not run, lane rules say no DB). Layout evidence: not run; the 13px table text / 12px heads fit at 1280 is unverified (risk 1).

## Tests and checks (revision 8b2d1e61a)
- `npx tsc --noEmit`: exit 0.
- vitest, 91 files (every `/sites/[A-Z]|from=20` test file + Portfolio, Finding, cold, findings index, verification, mini decisions/performance, tokens, gapGroup, postW6ShellCss): 91 passed, 2463 tests passed. 7 more CSS-reading files: 36 passed.
- Guards run alone: style ratchet pass; style-ratchet fixtures 7/7; frontend hard-wiring pass; missing-claim pass; mock-deviation labels OK (172 files); node fixtures mock-deviation 14/14, hard-wiring 9/9, evidence 12/12. check-all: for coordinator. Architecture check: not run (coordinator).
- Tests changed (CSS-literal only): `postW6ShellCss.test.ts` x2 (`font-size: 12px` -> `var(--font-size-100)`); `miniDecisions.test.tsx` x3 (spacing snap: 20px -> `--space-5`, 10px 12px -> 8px 12px, 5px 0 4px -> 4px 0 4px). Behavioural: `siteFinding.test.tsx` chip assertions -> one gap line (the collapse itself).

## Known deviations
- GapGroup line is a `div` (inline form: `span`), not `<p>`: `<ul>` cannot sit in `<p>`; the Finding status strip allows inline elements only.
- MOCK DEVIATION for the collapse is a code comment citing D-UQFI.4, not a rendered `MockDeviation` (no register row added).
- Page title below 760px: 23px -> 20px (`--font-size-600`); rev 6 names no phone size.
- Spacing snap excludes `ui/primitives.css` (shared by every page; rev 6 says "other files keep their values").

## Questions for the Architect
1. Cold board: rev 6 says "a section is one panel" and "grouping never crosses sections", but the named target (the "No cold assessment for this window" blocks) is six separate Panels (`coldSiteViews.tsx:722,746,762,975,1031,1150`). Merging them removes panels (a layout change). Which rule wins?
2. Figures: rev 6 ("nothing else at page-title size or larger") vs the v7.2 hi-fi `--text-figure` 30px. Built per rev 6 (20px). Confirm, or leave figures to UQ-FI-3.
3. P3 headline needs a change in `SiteAnalyticsFrames.tsx` (SR-5/SR-8 are editing it): build after they merge?
4. Should `primitives.css` spacing be snapped too (affects non-demo pages)?
- For lanes merging after this: rerun `node tools/uqfi-type-codemod.mjs` (add `--spacing` only for the 14 listed files) and the style ratchet. SR-8-10 touches `w4-mini-performance.css` and `primitives.css`: expect conflicts there.
