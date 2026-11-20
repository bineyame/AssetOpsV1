# Review packet: mock-up vNEXT, the four headings and the snapshot "as of"

Status: in_review. Branch `task/l4-mock-categories-snapshot`, cut from `task/pack-recreate-integrate` at 28dc247c0, which now includes eb1e526d9 (design rev 16.10). Commits: 4399d289e (built to rev 16.9), then the rev 16.10 deltas commit, then this packet.
Open: `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/index.html`.
Sources: design rev 16.10 §2.0 (the four headings, Figure 1b), §2.1, §2.8 (Overview cards, the daily snapshot), OD-21, OD-23; `worked-portfolios.md` §1.0, the Home categories row; the owner's words, Q3, Q5 and Q10 (`.agent/owner-summary-confirmations-2026-11-19.md`); the coordinator's rev 16.10 deltas.

## Screens
| Screen | Change |
|---|---|
| Portfolio Overview | The four cards read the structure nodes whose home category they are. **Grow**: revenue against target, the factor effects (for example Kobo +$38), then "Potential, not realised" (the Mto letter of intent, idle crate-days, Ruiru's spare charger capacity), its Findings, the plan items with their Grow effect, and its verdicts. **Optimize**: cost, the litre, energy and service-to-charge effects (unmapped meters and adjustments included), operations measures, then "Cash collected, outside the contribution gap" (Kobo $3,180 collected of $3,458; $278 outstanding; across Lakeside $8,870 of $9,688), its Findings, plan items and verdicts. **Protect**: the Protect measures, at stake listed and never summed, a "possible fuel loss" line that links to the Kobo Finding and is not counted, its Findings (limits and deadlines), protective plan items, and the upkeep item. **Assure**: no money of its own, in five parts: actual against target with sources and coverage (contribution's bridge by heading opens here: Kobo +$38 Grow, −$600 Optimize, −$562); options against doing nothing with their limits; Actions and the three verdicts; the evidence the product keeps; contract notices and remedies (the Mto notice deadline 27 Nov; the Kisiwa contract credit, evidence assembled). |
| Decision pages | A new column, "Effect under each heading". Mto huller: Grow +$495 a month, Optimize −$100 a month. Protective options show their Protect measure (not money). No action reads "The reference". |
| The plan (Act first) | Each item card has an "Effect under each heading" row. The declared upkeep item reads Protect, upkeep, no value claimed. |
| Outcomes by site, factor tables | Re-placed by the home categories: unexplained litres are Optimize, unmapped meters, adjustments and cash are Optimize, compensation is Optimize, and penalties are Optimize. |
| Every screen (top bar) | "October 2026 · Figures as of 6 Nov, when the October books closed". A "Recalculation pending" badge appears only when the data says so (it never does yet). |
| Scope & coverage | "Where the data comes from, in order": first an upload of the energy management system's exports, then a direct link to that system, and last an edge gateway at the site. |
| Earlier Kobo outcome board | "Site earnings" is removed from Grow, and "Cash collected" moves from Grow to the cost row (hooks in `tools/rebase_v70.py`). |

Code: `loop-core.js`: the typed `lens:` values (47) and FAC's heading column are removed. `HOME` registry plus `placeHomes()`: a node gets its heading by name (Home categories row), by its bridge factor, or by inheritance from its parent. The root sits above. Anything else is listed in `HOME_GAPS`. `SNAP`, `snapText()` and `periodChip()` are also here. `loop-portfolio.js`: `effectsOf`, `contribGap`, `siteSplit`, `decHeading` (+`DEC_HOME`), `findingHeading`, `optHeadings`/`byHeading`, `cashLines`, `bridgeTable`, `assureGroups`, `categoryCard`, and CARDS reduced to position and context lines. `loop-site.js`: the options column. `economics.css`: the new rules.

## Checks (final source)
- Rebuild per the README. The rebase, evaluator and gen_fixtures runs showed 0 differences, and fixtures.js and derived-values.json are unchanged. The build ran.
- `node tools/render_text.cjs`: see the final report numbers below.
- `node tools/vocab_check.cjs`: an outcome category code rule was added (GROW_REVENUE, OPTIMIZE_COST…, PROTECT_ASSET…, ASSURE_PERFORMANCE…, and the bare upper-case words).
- `python3 tools/hand_typed_scan.py`.
- `python3 ../check_manifest.py`: 4034 passed, 0 failed. `python3 ../check_alignment.py`: 96 passed, 0 failed (at eb1e526d9).
- `node tools/plan_switch_check.cjs`: 223 passed, 0 failed, 0 script errors (was 164). The new checks are independent of the mock's HOME table:
  - each money card lists exactly its heading's bridge effects per Site;
  - Grow + Optimize = the evaluated contribution gap per Site (DERIVED actual − target, or the stated total at Ruiru);
  - no money effect sits under Protect or Assure;
  - Assure shows no money outside the bridge it presents;
  - the bridge opens from Assure only;
  - each Site's outstanding, Kobo's $278 included, sits under Optimize as cash, never under Grow;
  - the "as of" date is shown, and the pending notice appears only where the data says so;
  - the huller's Grow and Optimize effects appear on its decision page and plan item.
- Plants (each reverted with `git checkout`): see the final report.

## Not run
Playwright audit, screenshots and layout evidence: there is no browser. `CHANGE-REGISTER.md`, `browser-audit.md` and `rendered-manifest-strings.json` were not regenerated.

## Gaps (no value invented)
1. **Snapshot time.** No snapshot record exists in the data (`MANIFEST.snapshot` / `DERIVED.snapshot`), so the screens show the books-closed date (`as_of`, 6 Nov). No recalculation-pending flag exists either, so the notice never shows.
2. **Nodes with no stated home category** (shown with no heading and listed under Assure, "Not yet under a heading"): Kasarani "Charging energy deliverable per night" and Ruiru "Charger 7, connector 2". The likely homes are Protect (the import limit; charger life and cover), but the row does not name them.
3. **Placed by inheritance, not named in the row** (please confirm): technical losses, losses beyond expected, energy delivered, the fuel balance, tariff-like rates, idle capacity (potential), Thika's customer compensation (Optimize, as part of cost to serve) and EV maintenance.
4. **Decision headings named where the anchor factor differs from the lever** (`DEC_HOME`): Kisiwa genset → Protect, Thika backup → Protect, Ruiru expansion → Grow, Mto billing → Optimize.
5. **Operations measures** (availability, field visits, kWh per visit, and others) have no stated home. They stay under Optimize, as before.
6. **Option effects by heading** are split only where the data states revenue and cost lines that add up to the net (the huller, welding, the aggregator). Other options carry one money line, under their decision's heading.
7. Protect still shows two data measures in dollars, "Customer liability" and "Service penalties" (labelled "same factor as the cost line"). These come from the data, unchanged.
8. No `specs/INDEX.md` and no `.ai/state/` exist in this worktree, so no index row or built-state entry was written.
