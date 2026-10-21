# W3-02 v69 mock measurements: `globalevidence`, `globalfinancials` (2026-10-20)

These are measured mock pixels, not caps. They feed the `.agent/W3-02-build-spec.md` "1440/390 panel budget" section and close its "pre-review browser measurement of the mock DOM" for the mock side. The app side is still measured at commits 2 and 4.

Method: headless Chrome via raw CDP, the same pattern as `tools/w1-ux-03-evidence.mjs` (the repo has no Playwright package; its evidence tools drive Chrome through CDP). The page was `file:///.../frontend/mockups/v69/index.html#/<screen>` on main `dc692c21`. Viewports were 1440x1000 and 390x900 (mobile emulation), DPR 1. The measured elements were each top-level `.cards`, `.statusbar`, `section.panel` and `.notice` under `main`, using `getBoundingClientRect` (top is document Y). A panel table's client and scroll width come from `.table-wrap`. The helper script and full JSON are in the session scratchpad (`measure.mjs`, `mock-measure.json`, four PNGs), not in the repo.

## globalevidence (h1 `Portfolio evidence`)

| Element (title) | 1440 top | 1440 h | 390 top | 390 h | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Cards row (`Sites with limited claims`, `Priority evidence actions`, `Unsupported claims`) | 244 | **113** | 414 | **264** | 1440: 3 x 378 px wide, each 113 high. 390: **2 + 1 grid**, not a single stack (cards 174 wide x 126 high, rows at y 414 and 553). |
| Panel `Capability coverage across sites` | 375 | **285** | 697 | **425** | thead 33. Rows 51/51/51 at 1440 and 80/97/97 at 390. Table client/scroll width is 1121/1121 at 1440 and **320/531** at 390, so it scrolls inside the panel. Column widths at 1440: Site / domain 200, Operational capability 200, Readiness 101, Current ceiling 320, Next evidence 300. Subtitle is under the title (`sub`), not a footnote. |
| Panel `Recurring evidence gaps` | 678 | **287** | 1139 | **639** | thead 33. Rows 45/45/45/44 at 1440 and 115/150/133/132 at 390. Table width 1121/1121 at 1440 and 320/337 at 390. Columns at 1440: Gap 459, Sites 161, Unlocks 324, Next step 177. |
| Notice (blue) `Source connectivity is not physical asset health…` | 983 | **42** | 1797 | **78** | |
| Whole document | | 1091 | | 1969 | Document scroll width = client width at both widths (1425 at 1440 because of the scrollbar; 390), so there is no page overflow. |

## globalfinancials (h1 `Portfolio financials`)

| Element (title) | 1440 top | 1440 h | 390 top | 390 h | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Status bar (`Site-owned consequences` blue chip + `Values grouped by basis and period; no financial assessment`) | 244 | **44** | 414 | **71** | |
| Panel `Consequence register` | 306 | **266** | 503 | **407** | thead 33. Rows 45/45/44 at 1440 and 97/97/79 at 390. Table width 1121/1121 at 1440 and **320/514** at 390. Columns at 1440: Site 124, Category 265, Window / quantity 227, Value 101, Basis / limit 268, Source 138. The subtitle `No independent repricing or technical re-derivation` is under the title, not a footnote. |
| Notice (default **amber**) `These values are not an additive profit…` | 589 | **42** | 928 | **78** | |
| Panel `Aggregation rule` (prose only) | 650 | **99** | 1024 | **163** | |
| Whole document | | 1001 | | 1282 | No page overflow at either width. |

Both screens have the same page header above the first element: eyebrow (`Evidence` / `Financials`), h1, and subtitle (`Cross-site claim readiness, recurring gaps and instrumentation priorities` / `Estate consequences with source-site ownership and bounded interpretation`). The top bar shows `Window: Event window · 6 Oct 2026 · each site's event window`.

## Against the spec caps (build spec "1440/390 panel budget")

| Region | Mock 1440 | Spec cap 1440 | Ceiling max: mock + max(24, 10%), rounded up | Mock 390 | Spec cap 390 | Ceiling max: mock + max(24, 10%), rounded up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Evidence cards row | 113 | 220 | 137 | 264 | 430 | 291 |
| Capability coverage panel | 285 | 500 | 314 | 425 | 560 | 468 |
| Recurring gaps panel | 287 | 390 | 316 | **639** | 460 (below mock) | 703 |
| Financial status bar | 44 | 96 | 68 | 71 | 120 | 95 |
| Consequence register panel | 266 | 500 | 293 | 407 | 560 | 448 |
| Aggregation rule panel | 99 | 250 | 123 | 163 | 330 | 187 |
| Evidence notice | 42 | none | 66 | 78 | none | 102 |
| Financial notice | 42 | none | 66 | 78 | none | 102 |

At 390 the measured Recurring gaps panel (639) is taller than its cap, so the spec's "measured mock plus tolerance governs" gives 703. Every other cap is well above mock + tolerance, so the two rules in the spec disagree; see `.agent/W3-02-spec-review.md` Q38.

Correction (W3-02 commit 2, Lane A): the maxima columns above now use build-spec Review closure 4's ceiling values (1440/390: cards 137/291, capability 314/468, gaps 316/703, notices 66/102, status 68/95, register 293/448, Aggregation 123/187). The earlier floor values (290, 313/467, 315/702, 292/447) are superseded. The unrounded mock-side measurements are unchanged; mock heights are integers, so the cards and panels whose 10% term was fractional (264, 285/425, 287/639, 266/407) round up.
