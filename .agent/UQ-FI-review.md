# UQ-FI review (UQ-FI-1 + partial UQ-FI-2 + UQ-FI-3), branch task/UQ-FI-3

Reviewer: fresh Claude reviewer, 2026-11-13. Reviewed at `fbc5373e3`. Diff: `git diff c9e40d56e HEAD` (merge-base with main). Spec: rev 6, rev 7 UQ-FI-3 row, D-UQFI.1-12. Packets: `UQ-FI-packet.md`, `UQ-FI-3-packet.md`.

## Verdict: ACCEPT WITH FINDINGS FIXED ON THE BRANCH (one High, small)

One High must be fixed before merge: H1, the On track pill's check symbol has no size. The rest is sound.

## Findings

### H1 (High, acceptance gap: D-UQFI.11 look) `frontend/src/ui/status-pill.css:18-19`, the On track glyph is unsized
- Round 2 (`fbc5373e3`) deleted `.status-pill__icon { width: 12px; height: 12px; flex: none; }` and left the dangling `.status-pill__glyph,` selector. That selector is now grouped into the `.s-complete` colour rule. Nothing sizes the `<svg viewBox="0 0 12 12">` (`StatusPill.tsx:37`). The sheet has `.chip svg{width:12px;height:12px;flex:none}` (`foundation-sheet.html:445`).
- An inline SVG with a viewBox and no width or height uses the default replaced-element size in a shrink-to-fit inline-flex, which is about 300 px. Every ON_TRACK pill (board rows, matrix cells, matrix key, per-Site states behind "Why?") would draw a large filled green disc spilling out of a 24 px pill. jsdom cannot show this, and no layout evidence was run, so the tests pass.
- Fix: restore `.status-pill__glyph { width: 12px; height: 12px; flex: none; }` as its own rule, and drop the glyph from the `.s-complete` selector list. The glyph inherits `--status-pill-bg` from the pill. Add a CSS assertion in `statusPill.test.tsx` that `.status-pill__glyph` has `width: 12px` and `height: 12px`. (No browser on this VPS, so the size is inferred from CSS rules rather than observed. The missing rule is certain.)

### L1 (Low, consistency) `frontend/src/estate/PortfolioOutcomes.tsx:291`, the R740 label has no class
- `<p data-mock-deviation="R740">` has no `className="mock-deviation-line"`, unlike the other labels (`SiteAnalyticsFrames.tsx:1061`, `operatorSiteTabs.tsx:153`). Client mode hides it correctly through `[data-mock-deviation]`. In review mode it takes `.value-card p` styling instead of the label style. Fix: add the class. This is a preference and does not block.

### L2 (Low, residual risk) the "Why?" popover now carries the card qualifiers
- `.conf-pop.why-pop` (`blocks.css:22`) has `max-height: none` above 600 px. With per-Site pills, Grow parts and fuel and value lines added, a Portfolio "Why?" can grow tall. It is absolutely positioned, so the page scrolls rather than clipping, but the size is unmeasured. It goes on the capture list together with the card fit of the 30 px figure at 1280 and 390, which the packet honestly records as "not run (no serve/DB)".

## Verified (what I checked and saw)
- **Inter licensing.** `public/fonts/InterVariable.woff2` SHA-256 `693b77d4…a8e3` and `OFL.txt` `262481e8…935a` match the packet. OFL 1.1 text with the Inter copyright line. `fonts.css` uses a same-origin URL only (no CDN). It is imported before `tokens.css` in `main.tsx`.
- **Type scale and 12 px floor.** `--font-size-100..800` = 12/13/14/16/18/20/24/30. Every role token is re-pointed onto the scale, and the phone page title is 20 px. The ratchet wall resolves var chains and found no size under 12 px.
- **Codemod scope.** I re-applied `rewriteType` (all CSS files) plus `rewriteSpacing` (the 14 DEMO_PATH_CSS only) to each merge-base file and compared the result with HEAD. 27 of 31 changed CSS files are byte-identical to the codemod output. The 4 that differ are hand edits, each documented:
  - `primitives.css`: `--leading-body`, the tabular-figure selectors, figures 700 to 600 per D-UQFI.4/7, and the GapGroup CSS.
  - `blocks.css`: `.why-more`, and the dead `.oc-pfval` removed.
  - `estatePortfolio.css`: figures 700 to 600, and the UQ-FI-3 card rules.
  - `outcomes.css`: the `.oc-info` Georgia shorthand moved to tokens, neutral cells, and dead tone rules removed.
  - `node tools/uqfi-type-codemod.mjs --check`: 0 files would change.
- **D-UQFI.9.** `primitives.css` spacing is not snapped (the residual diff shows no padding, margin or gap change).
- **Ratchet is non-vacuous.** On a scratch copy of `frontend/src`, a planted `.x{font-size:11px;color:#abcdef}` gave 2 rises (rawFontSize 0 to 1, rawHex 9 to 10) and a wall hit "11px < 12px".
- **Card (D-UQFI.7).** `--text-figure` is used only by `.estate-portfolio .oc-pfcard .value-number.oc-pffig` (0,4,0, which beats the `.neutral` and media overrides). Every other figure is 20 px. The card shows the label link, "Why?", one figure (server `value`), one sentence (server `detail`) and the basis (server `basis_text`). `CardQualifiers` keeps the old card order (definition, days, Grow parts, fuel lines/note, value lines/note, note, per-Site states) with the same hooks and server strings. No new words.
- **StatusPill (D-UQFI.11).** NEEDS_ATTENTION partial, OPPORTUNITY accent, WATCH neutral and NOT_MEASURED notanalysed (dashed) carry no symbol. ON_TRACK takes the complete look with the filled-circle check. UNKNOWN, NO_OBJECTIVE, NOT_APPLICABLE and unrecognised codes are neutral with no symbol. The word is the caller's (server `state_label`), and there is no `site_type` branch. The token hexes match the sheet primitives (green/amber/blue/neutral). Text-on-background contrast is about 5.4:1 or better for every look.
- **R740.** The register row has all 9 cells (ID, unit, screen, mock element, shown instead, D1, reason, owner, status). It is labelled in code at `PortfolioOutcomes.tsx:288-291`.
- **D-UQFI.6.** No `coldSiteViews.tsx` change in the diff, so the six Cold panels are unchanged.
- **Accessibility.** "Why?" is a `<button>` with `:focus-visible` (`blocks.css:6`) and z-index above the stretched card link, which has its own focus ring. The dialog is a native `showModal()` `<dialog>` (Escape, focus inside). Glyphs are `aria-hidden`.
- **No stray files.** `frontend/mockups/v72/*` and `.agent/UQ-0-packet.md` come in through the UQ-0 / UQ-hifi-mockups lineage the branch is stacked on, and they are the named visual targets. Font files are in the repo. The worktree is clean apart from this file.

## Checks run (this review, revision fbc5373e3)
- vitest, 18 files, 618 tests, all passed:
  - statusPill, estatePortfolio, outcomeBoard, postW6ShellCss, miniDecisions, tokens, gapGroup, siteFinding;
  - Site-href/range files: estateRoots, w301EstateShellRoutes, s5SiteWindowOverview, siteDetailScreen, operatorSiteTabs, coldScenarios, siteFindingEvidence, estateEvidence, estateFinancials, sitesIndexRoute.
- `npx tsc --noEmit`: exit 0.
- `node tools/checks/style-ratchet.mjs`: passed (rawHex 458). `test_style_ratchet.mjs`: 7/7.
- `node tools/checks/mock-deviation-labels.mjs`: OK, 174 files. `test_mock_deviation_labels.mjs`: 14/14.
- Not run, per lane rules: check-all (coordinator), the full vitest suite, production build, layout evidence and captures (no serve, DB or browser on this VPS).

## Not verified / residual risk
- Rendered appearance of every pill and of the 30 px card figure at 1280 and 390. There is no browser on this VPS, which is how H1 got through.
- Order inside "Why?" is checked by review only. The test pins the hook sets and line text, not the sibling order.
