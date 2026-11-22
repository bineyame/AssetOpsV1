# Browser audit · Layer 4 mock-up rev 8

Scripted with Playwright and Chromium (`tools/audit.mjs`, run via `tools/run-audit.sh`), against `index.html` opened with `file://`. Raw results: `tools/audit-results.json`. A static-server run (`python3 -m http.server` on 127.0.0.1) was also checked on five routes: all rendered, 0 console errors.

## Summary

| Check | Result |
|---|---|
| Screens in the mock-up | 187 (Changed 21, Preserved 80, Merged 9, Added 77) |
| Route renders checked (all screens for Lakeside; Portfolio tabs, Sites and Financials also for Harvest and Metro) | 207 |
| Routes rendering an h1 with 0 console errors | 207 / 207 |
| Routes with a console error | 0 |
| Routes with a link to a missing screen | 87 |
| Routes with horizontal page scroll at 390 px | 0 |
| Vocabulary hits (option codes, internal terms, ISO dates, ">=", "LOI", "O&M", undefined/NaN) on added and changed screens and sampled evidence drawers | 38 |
| Product record ids (F-, ACT-, WR-, INC-) bare, or asset/batch tags without a plain name, on added and changed screens and sampled drawers | 0 |
| Same check on preserved v7.0 screens (exempt; reported separately) | 133 occurrences on 16 preserved routes (16 distinct pages) |
| Role words (CEO, COO, CFO, CCO), executive-question stems or headings phrased as a question on added/changed screens, tab rows, evidence drawers and review-notes drawers | 0 |
| Rev 6: Portfolio tab order Overview, Outcomes by site, Demand and capacity, Act first, What changed, Scope & coverage | FAIL (old route lands on #/portfolio/demand-and-capacity) |
| Rev 6/7 (0K4m: the Simulated chip or the gap words): labels on the Kobo, Mto demand, Embakasi, Kirinyaga and Mto inverter decision pages; each operator's plan-value drawer (Harvest: assumption wording, no forward replay) and Overview note | FAIL |
| Rev 7/8 (0K4m: Simulated chips): source scan over every route and every evidence drawer, using the audit's own set derived from the YAML (tools/replay_values.py) | independent set of 3 replay figures (same as the tagger's: true); 4 occurrences scanned on all routes and 405 drawers; unlabelled 0; unrelated matches on preserved v7.0 pages (exempt, not replay figures): 0 |
| Rev 7: EV measure shown as "Deliverable energy used (import-limited)" with binding limits; Ruiru 34% labelled nameplate charger-hours beside 61% of deliverable energy | FAIL |
| Rev 6: no "not explained by the model" wording on Ruiru (site page, economics, factor structure, waterfall rows) | pass |
| Filter or lens controls on Portfolio tabs | 0 |
| Demo operator selector in the product top bar / in the review bar | 0 / 207 |
| Switch cases re-computing the plan correctly | 2/8 |
| Evidence drawer (keyboard open, focus inside and trapped, Escape closes, focus returns, definition, formula, source rows, clocks, coverage, provenance) | all pass |
| Visible focus on representative controls | 5/5 |
| Contrast spot checks at least 4.5:1 | 21/21 |
| Preserved v7.0 screens identical after the name map | 0/80 |
| Private oracle shipped in the bundle | no |
| Hand-typed figures restating an evaluated figure: total (in loop-*.js / in 285 rendered manifest strings / unused allow-list entries) | 0 (0 / 0 / 0); allow-list 48 entries, each keyed by file or manifest path, literal and context |
| Manifest placeholders filled on screen (fig / rec / strings) and unresolved | 97 / 52 / 81; unresolved 2 |

## Switch cases

| Case | Checks |
|---|---|
| lakeside 5000/yes | expectSpend: $3,660; expectValue: +$2,213.33; spendOk: pass; valueOk: FAIL; inverterOk: pass; competingShown: pass; hullerOk: FAIL; valuedCostsOk: pass; downsideOk: FAIL; announced: pass; focusKept: pass |
| lakeside 5000/no | expectSpend: $2,460; expectValue: +$0; spendOk: pass; valueOk: FAIL; inverterOk: pass; competingShown: pass; hullerOk: pass; valuedCostsOk: FAIL; downsideOk: FAIL; announced: pass; focusKept: pass |
| lakeside 6500/yes | expectSpend: $3,660; expectValue: +$2,213.33; spendOk: pass; valueOk: FAIL; inverterOk: pass; competingShown: pass; hullerOk: FAIL; valuedCostsOk: pass; downsideOk: FAIL; announced: pass; focusKept: pass |
| lakeside 6500/no | expectSpend: $6,340; expectValue: +$2,213.33; spendOk: pass; valueOk: FAIL; inverterOk: pass; competingShown: pass; hullerOk: FAIL; valuedCostsOk: pass; downsideOk: FAIL; announced: pass; focusKept: pass |
| harvest aggregator yes | spendOk: pass; visitsOk: pass; valueOk: FAIL; downsideOk: FAIL |
| harvest aggregator no | spendOk: pass; visitsOk: pass; valueOk: FAIL; downsideOk: FAIL |
| metro tariff yes | spendOk: pass; valueOk: pass; downsideOk: pass |
| metro tariff no | spendOk: pass; valueOk: pass; downsideOk: pass |

Expected values are the evaluator's switch cases in derived-values.json (spend, modelled 12-month change, visits, inverter path and huller from the case's items, downside); valuedCostsOk checks that the note names spend − the case's spend not valued in money as the valued options' costs. downsideOk checks the downside line beside the plan value ("Downside:" in the default case, "Downside shown for the default plan:" in switched cases). Lakeside's note now names must-do $1,800 and protective $430 spend. After each change the plan is announced in a polite live region and focus stays on the radio button.

## Rev 5 checks

| Operator | Protect table by site | November-to-date table | At-stake listed, never summed | "Avoidable" in an observed view | Overview Protect card shows targets |
|---|---|---|---|---|---|
| lakeside | false | false | false | false | true |
| harvest | false | false | false | false | true |
| metro | false | false | false | false | true |

Plan-figure notes as shown on the Overview:
- lakeside: ""
- harvest: ""
- metro: ""

## Operator switch

- harvest: top bar "undefined"; headline "undefined…"; selector in product top bar: false
- metro: top bar "undefined"; headline "undefined…"; selector in product top bar: false
- lakeside: top bar "undefined"; headline "undefined…"; selector in product top bar: false

## Focus

- `.rail a`: A, outline solid 2px → visible
- `.tabs a`: A, outline solid 2px → visible
- `.ev-num`: BUTTON, outline solid 2px → visible
- `#op-switch`: SELECT, outline solid 2px → visible
- `input[name="sw-budget"]`: INPUT, outline solid 2px → visible

## Contrast

- portfolio `.ec-rec`: 7.53:1 (12px) pass
- portfolio `.ec-est`: 7.53:1 (12px) pass
- portfolio `.ec-der`: 7.53:1 (12px) pass
- portfolio `.ec-mod`: 7.53:1 (12px) pass
- portfolio `.ec-stake`: 7.53:1 (12px) pass
- portfolio `.ec-na`: 7.53:1 (12px) pass
- portfolio `.note`: 7.53:1 (12px) pass
- portfolio `.attn-k`: 5.8:1 (12px) pass
- portfolio `.attn-new .attn-k`: 5.34:1 (12px) pass
- portfolio `.attn-at .attn-k`: 5.56:1 (12px) pass
- portfolio `.attn-unobs .attn-k`: 6.87:1 (12px) pass
- portfolio `.ocard h4`: 7.53:1 (12px) pass
- portfolio `.op-select`: 7.44:1 (12px) pass
- portfolio/act-first `.cellnote`: 7.53:1 (12px) pass
- portfolio/act-first `.meterhead`: 16.46:1 (12px) pass
- decision/mto-inverter `.legal`: 14.83:1 (12px) pass
- decision/mto-inverter `.steps small`: 7.53:1 (12px) pass
- decision/mto-inverter `.deadline`: 14.83:1 (12px) pass
- decision/kobo-generator `.obl-pass`: 6.35:1 (12px) pass
- decision/kobo-generator `.obl-unknown`: 8.57:1 (12px) pass
- decision/kobo-generator `.badge.amber`: 5.56:1 (12px) pass

## Issues found during the build and fixed

- Absolutely positioned screen-reader text inside number buttons escaped scrolling table containers and caused 390 px page scroll on 47 routes: fixed by relative positioning; the workspace grid item now has `min-width:0`.
- Two class names (`.rank`, `.ob`) collided with v7.0 styles: renamed.
- A cold-room evidence drawer showed an EV invoice sample ("undefined kW"): fixed.
- Uppercase table headers produced false vocabulary hits; the scan now reads text content.

## Not covered

- Screen-reader output was not tested with an assistive technology; roles, labels, live region and focus order were checked by script only.
- Contrast is a spot check of 36 representative elements, not every pixel; charts use text labels and text equivalents, not colour alone.
