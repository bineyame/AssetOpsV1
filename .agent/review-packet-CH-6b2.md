# Review packet: CH-6b2 (Portfolio cards and board Grow from server claims), lane 1

Branch `task/CH-6b2-portfolio-cards` (main with FIX-MAIN-4 merged), worktree `AssetOpsV1-ch6b2`. Rulings: CH6b2-R in `AssetOpsV1-plan2\.agent\build-sheet-CH-6.md`. USER_REVIEW: none required. Not merged.

## Outcome
The Portfolio cards (Grow, Protect, Assure) and the Site-board Grow row render server-written claims. The browser card rules are deleted.
- Backend: `summary.cards`, `summary.card_notes`, `count.sites_disrupted` (+ Protect Why? lines), `grow_headline`, `study.headroom_unit`, "1 of 1 day checked" (Q7a).
- Frontend: `PortfolioOutcomes.tsx` renders `summary.cards` (own `card_notes` line, `oc-pfdays`, Grow `dl.oc-pfgrow`); `OutcomeBoard.tsx` Grow value = `grow_headline`, `GrowParts` in `ob-body`; `EstatePortfolio.tsx` unit = `study.headroom_unit`.
- A summary or body without `cards` renders "Not known yet" and no browser-built text.

## Mock (v70) -> new
| mock element | now |
|---|---|
| Portfolio Grow card value + `pfGrowParts` (Target / Potential / Estimated income + note) | `summary.cards.GROW_REVENUE` value and `parts`, `dl.oc-pfgrow`; `missing` keeps gap `G-portfolio-grow-revenue` |
| Protect "N sites disrupted" `<small>` | `cards.PROTECT_ASSET.value {text, small}` from `count.sites_disrupted` |
| Assure detail / targets clause | `cards.ASSURE_PERFORMANCE.detail` verbatim |
| `oc-pfdays` days line | `card.days_line` (Optimize carries none, Q3) |
| Portfolio-body clause | `summary.card_notes[key]`, its own line |
| board Grow `ob-val` + three parts | `row.grow_headline`; `GrowParts` inside `ob-body` |
| board Grow "Opportunity" chip | removed (Q6). It had no `link_ref`, only a `title`. That hover text (`row.potential.text`) is now the `title` of the Potential part. |
| opportunity panel unit | `study.headroom_unit` (Q7c) |

## Checks
- Frontend: `estatePortfolio.test.tsx` 24 old-rule tests rewritten against `summary.cards` / `card_notes` / `headroom_unit` fixtures (`serverCard`, `serverCards` in `portfolioFixtures.ts`); intent kept (rendering, tone, small, days line, note on its own line, vocabulary scan, dots, missing gap, not-known). Added: NOT_KNOWN basis (Q8, plus the type), Grow parts and income note, body without cards. `estatePortfolio` + `outcomeBoard` 84 pass. `tsc --noEmit` clean. Hard-wiring ratchet passes at api 12 / href 24 / lit 70 / cmp 51 / code 3, not raised.
- Backend: `test_ch6b2_portfolio_cards.py` 15 pass; with `test_ch6_claims` and `test_out_b1_board` 53 pass after merging main.
- Non-vacuous proofs (mutate, fail, revert, committed first): one-day rule `m == 1` -> `m == 99`: `test_copy_preferences` fails (1 failed, 14 passed). `{parts.potential}` -> `{parts.target}`: `growOneSiteEstimate...` fails. Note render switched off: 2 fail (`serverTextsRender...`, `withheldFindings...`).
- Pre-existing on main (7): `test_ch6_claims` a4, `test_out_b1_board` imports, 5 x `test_walk1_productive_sales`. Fixed by FIX-MAIN-4 (merged here); no change in this slice.
- Guards one at a time: architecture, navigation, agent workflow, dependency registry, delivery fixtures, mock-gap fixtures, missing-claim scan + fixtures, evidence width, mock deviation labels, screen ledger, COH fixtures (108), event register (12), chain graph, perf budget (8/8), ratchet: all pass. (Run in `powershell` via the tool; `-File` under bash is blocked by execution policy, which was not overridden.)
- No full suite and no `prepare`, per the testing rule.

## Polish clone L3 (`ch6b2`, dropped)
create -> migrate -> backfill a-d (a 186, b 9, c 3, d 6) -> settle (tick 99 s) -> W6: 46 requests, 0 non-200, 0 unlisted modules, 0 violations -> `fresh` 43/43 stored bodies equal a fresh compose -> collect 85/85 200 -> COH `check` against `expected-today.json`: 0 new (COH-0..: 0 new; COH-2 2 expected).
Old (CH-6b1 browser rules, from the same bundle's `category_counts`) -> new (server `cards`):
- Week 25 Oct-1 Nov Protect: old "2 sites disrupted" (open_findings 5, 2 sites with a primary finding) -> new "None found on the days checked" (`count.sites_disrupted` = 0); detail "5 early warnings, counted separately"; days line names each Site ("GreenHarvest Cold Room: 0 of 7 days checked ... Depot Charging Hub: 0 of 1 day checked ... Kobo mini-grid: 0 of 7 days checked").
- Month Protect: old "2 sites disrupted" (7 findings) -> new "None found on the days checked" (7 early warnings).
- Grow: old short value -> new week "At least 84.16 USD estimated", month "At least 168.32 USD estimated", S window "At least 0.00 USD"; parts: Target "Kobo mini-grid: sales not recorded", Potential "Kobo mini-grid: Limited evidence ...", income per Site.
- Assure: old "Not known yet" lead -> new "None confirmed on the days checked" (week/S), "1 confirmed on the days checked" (month).
- Why? named Sites for Protect: none on this clone. Every graded day is low / no_data / pending (week `complete` 0 of 15), so no thread qualifies as disrupting and `count.sites_disrupted` is 0. The Why? route is not in the coherence bundle. Not tuned.
- Observation for the reviewer: old "2 sites disrupted" vs new "None found on the days checked" is a large visible change on this clone, because the count now follows graded days (CH6b2-R) rather than findings. Numbers were not adjusted.

## Known deviations / risks
- Layout evidence is owed at E5; none run in this slice (no layout claim made).
- Grow chip hover text now lives on the Potential part only; no link target existed to carry over.
- The `NOT_KNOWN` vitest asserts rendering; the type widening itself is enforced by `tsc`.
