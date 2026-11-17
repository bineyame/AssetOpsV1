# Browser audit · Layer 4 rev 4 mock-up

Scripted with Playwright and Chromium (`tools/audit.mjs`, run via `tools/run-audit.sh`), against `index.html` opened with `file://`. Raw results: `tools/audit-results.json`. A static-server run (`python3 -m http.server` on 127.0.0.1) was also checked on five routes: all rendered, 0 console errors.

## Summary

| Check | Result |
|---|---|
| Screens in the mock-up | 184 (Changed 36, Preserved 65, Merged 9, Added 74) |
| Route renders checked (all screens for Lakeside; Portfolio tabs, Sites and Financials also for Harvest and Metro) | 202 |
| Routes rendering an h1 with 0 console errors | 202 / 202 |
| Routes with a console error | 0 |
| Routes with a link to a missing screen | 0 |
| Routes with horizontal page scroll at 390 px | 0 |
| Vocabulary hits (option codes, internal terms, ISO dates, ">=", "LOI", "O&M", undefined/NaN) on added and changed screens and sampled evidence drawers | 0 |
| Filter or lens controls on Portfolio tabs | 0 |
| Demo operator selector in the product top bar / in the review bar | 0 / 202 |
| Switch cases re-computing the plan correctly | 8/8 |
| Evidence drawer (keyboard open, focus inside and trapped, Escape closes, focus returns, definition, formula, source rows, clocks, coverage, provenance) | all pass |
| Visible focus on representative controls | 7/7 |
| Contrast spot checks at least 4.5:1 | 36/36 |
| Preserved v7.0 screens identical after the name map | 65/65 |
| Private oracle shipped in the bundle | no |

## Switch cases

| Case | Checks |
|---|---|
| lakeside 5000/yes | expectSpend: $3,880; expectValue: +$6,096; spendOk: pass; valueOk: pass; inverterOk: pass; competingShown: pass; hullerOk: pass; announced: pass; focusKept: pass |
| lakeside 5000/no | expectSpend: $2,680; expectValue: +$2,556; spendOk: pass; valueOk: pass; inverterOk: pass; competingShown: pass; hullerOk: pass; announced: pass; focusKept: pass |
| lakeside 6500/yes | expectSpend: $3,880; expectValue: +$6,096; spendOk: pass; valueOk: pass; inverterOk: pass; competingShown: pass; hullerOk: pass; announced: pass; focusKept: pass |
| lakeside 6500/no | expectSpend: $6,430; expectValue: +$3,546; spendOk: pass; valueOk: pass; inverterOk: pass; competingShown: pass; hullerOk: pass; announced: pass; focusKept: pass |
| harvest aggregator yes | spendOk: pass; visitsOk: pass |
| harvest aggregator no | spendOk: pass; visitsOk: pass |
| metro tariff yes | spendOk: pass; valueOk: pass |
| metro tariff no | spendOk: pass; valueOk: pass |

Lakeside expected values are the four precomputed cases in the scenario file (spend, modelled 12-month change, inverter path, huller kept). After each change the plan is announced in a polite live region and focus stays on the radio button.

## Operator switch

- harvest: top bar "Harvest Cold Network / Demo operator"; headline "October contribution, composed from the sites’ factors: $946 against a plan of $1,716, $77…"; selector in product top bar: false
- metro: top bar "Metro Bus Depots / Demo operator"; headline "October charging and depot cost, composed from the depots’ factors: $41,705.12 against a p…"; selector in product top bar: false
- lakeside: top bar "Lakeside Power / Demo operator"; headline "October contribution, composed from the sites’ factors: $1,443 against a plan of $2,295, $…"; selector in product top bar: false

## Focus

- `.rail a`: A, outline solid 3px → visible
- `.tabs a`: A, outline solid 3px → visible
- `.ev-num`: BUTTON, outline solid 3px → visible
- `#op-switch`: SELECT, outline solid 3px → visible
- `button.wfrow`: BUTTON, outline solid 3px → visible
- `input[name="sw-budget"]`: INPUT, outline solid 3px → visible
- `details.astable summary`: SUMMARY, outline auto 1px → visible

## Contrast

- portfolio `.ec-rec`: 5.19:1 (11px) pass
- portfolio `.ec-est`: 6.35:1 (10px) pass
- portfolio `.ec-der`: 5.23:1 (11px) pass
- portfolio `.ec-mod`: 5.17:1 (11px) pass
- portfolio `.ec-stake`: 6.96:1 (10px) pass
- portfolio `.ec-na`: 5.92:1 (10px) pass
- portfolio `.hero small`: 5.92:1 (11px) pass
- portfolio `.note`: 5.52:1 (11px) pass
- portfolio `.attn-k`: 6.96:1 (10px) pass
- portfolio `.attn-new .attn-k`: 7.01:1 (10px) pass
- portfolio `.attn-at .attn-k`: 6.35:1 (10px) pass
- portfolio `.attn-unobs .attn-k`: 7.15:1 (10px) pass
- portfolio `.chain .stage span`: 5.92:1 (10px) pass
- portfolio `.chain .leak`: 6.69:1 (10px) pass
- portfolio `.ocard h4`: 5.92:1 (10px) pass
- portfolio `.op-select`: 7.92:1 (11px) pass
- portfolio/outcomes-by-site `.fac small`: 5.66:1 (10.5px) pass
- portfolio/outcomes-by-site `.wfval small`: 5.92:1 (10px) pass
- portfolio/outcomes-by-site `.wflabel small`: 5.92:1 (10px) pass
- portfolio/outcomes-by-site `.lens`: 10.16:1 (10px) pass
- portfolio/outcomes-by-site `.ftab thead th`: 5.66:1 (10px) pass
- portfolio/outcomes-by-site `.lgrid tbody th small`: 5.92:1 (11px) pass
- portfolio/act-first `.cellnote`: 5.92:1 (10px) pass
- portfolio/act-first `.switch small`: 5.92:1 (11px) pass
- portfolio/act-first `.meterhead`: 9.47:1 (11px) pass
- decision/mto-inverter `.legal`: 8.18:1 (11px) pass
- decision/mto-inverter `.steps small`: 5.03:1 (10px) pass
- decision/mto-inverter `.deadline`: 14.83:1 (12px) pass
- decision/kobo-generator `.obl-pass`: 7.09:1 (11px) pass
- decision/kobo-generator `.obl-fail`: 8.03:1 (11px) pass
- decision/kobo-generator `.obl-cost`: 6.59:1 (11px) pass
- decision/kobo-generator `.obl-unknown`: 8.71:1 (11px) pass
- decision/kobo-generator `.badge.green`: 5.67:1 (10px) pass
- decision/kobo-generator `.badge.amber`: 5.3:1 (10px) pass
- decision/kobo-generator `.badge.red`: 5.8:1 (10px) pass
- findings `.slim-banner`: 6.9:1 (11px) pass

## Issues found during the build and fixed

- Absolutely positioned screen-reader text inside number buttons escaped scrolling table containers and caused 390 px page scroll on 47 routes: fixed by relative positioning; the workspace grid item now has `min-width:0`.
- Two class names (`.rank`, `.ob`) collided with v7.0 styles: renamed.
- A cold-room evidence drawer showed an EV invoice sample ("undefined kW"): fixed.
- Uppercase table headers produced false vocabulary hits; the scan now reads text content.

## Not covered

- Screen-reader output was not tested with an assistive technology; roles, labels, live region and focus order were checked by script only.
- Contrast is a spot check of 36 representative elements, not every pixel; charts use text labels and text equivalents, not colour alone.
