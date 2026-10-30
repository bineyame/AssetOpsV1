# OUT-A review: category labels and links

Reviewer: a fresh Claude reviewer (not the author). Branch `task/OUT-A-category-labels` at `7b826e97`, compared with main `cbc32703` (main is merged in at `8b4c52dc`). Diff: `git diff cbc32703...HEAD`.

## Verdict: REVISE

The one blocking item is a missing register row. The code, the wire, the tests and the captures all meet the spec. Adding that one row to `.agent/mock-departure-register.md` makes this an ACCEPT. No code change and no new run is needed.

## Findings

### H1 (High, by the owner rule "mockup is layout spec"): the per-Site status row on the four Portfolio cards is missing, and no deviation is registered
- **Where:** `frontend/src/estate/PortfolioOutcomes.tsx:173` renders an empty `<div className="oc-sitedots" />`. `frontend/src/estate/estatePortfolio.css:174` hides it with `:empty{display:none}`.
- **What is wrong:** the v70 mock `pfCard` (`frontend/mockups/v70/outcomes.js:144-151`) shows a row on every card with a status dot and the name of each Site (Kobo, GreenHarvest, Depot). The captures show the app's cards without that row (`portfolio-estate-1440-app.png` against `portfolio-estate-1440-mock-v70-portfolio.png`).
- **Why this is a finding:** build spec A6 does rule that the row stays "empty in A; B6 fills it". So the build is correct, but no deviation row records the departure. The spec's A.5 table and register rows R520-R528 both omit it. R521 covers only the matrix and R524 only the Grow value. Under the owner rule, a mock mismatch without a registered deviation is High.
- **Fix:** register only. Add a row such as "R529 | OUT-A A6 | portfolio | per-Site status row on the outcome cards (`.oc-sitedots`) | Not shown | D5 build order | needs the Site outcome board statuses | OUT-B B6 | open". R529 is still inside the A range R520-R534. Do not change any code.

### L1 (Low, does not block): the Optimize card detail shows a word the product vocabulary forbids, and the new scan leaves that text out
- **Where:** `frontend/src/estate/__tests__/estatePortfolio.test.tsx:843` removes the Optimize card detail before the w1 scan runs.
- **What it means:** the detail is the existing operating-cost card's text, "Kobo · Candidate operating-cost exposure · …", which spec A6 says to reuse verbatim. "candidate" is a word the guard forbids. The text was already on screen before this slice, so this is not a weakened test: the old five-card tests never scanned the cards.
- **Why it still matters:** the text now sits on a headline outcome card, where clients will see it. Record it for the W1-conclusion plain-language pass. It belongs with `estateFinancialsWords` `categoryLabel` and is not in this slice's scope.

### Notes (not findings)
- **Reviewer-focus item, the outlined "Also check · Protect asset and capital" pills on the cold and EV Finding pages: these follow the spec and the mock. They are not a defect.**
  - Ruling A-Q2 says the page line shows every CHECKED item on the wire, even when the same category also MOVES. Only the list form filters those out.
  - Spec A5 gives the exact F-118 text: "Affects Protect asset and capital cooling continuity, stock kept saleable Also check Protect asset and capital compressor life Optimize cost and efficiency cost per cooling unit".
  - The mock's `affectsLine` (`outcomes.js:33-34`) calls `catPills(a[1], true)` on the whole checked list without filtering.
  - EV F-130 follows the same rule ("Also check Protect asset and capital / charger life").
  - The list pills (A.7 #3 and #4) correctly drop the outlined Protect pill.
- The verified-recovery card's separate "Inspect financial basis" link is gone. The Assure card is now one link to `/evidence`. Spec A6 sets that destination, so this is as directed.
- The Optimize card falls back to "Not assessed" / "Operating cost is not assessed for this selection" / "No value line" / `neutral` / `/financials`, as addendum 2 requires. The test `optimizeCardStaysInUnknownWordingWhenOperatingCostIsMissing` covers it.
- The Grow value renders through `<MissingClaim gapId="G-portfolio-grow-revenue" placement="portfolio.outcomes.grow-value">`. The registry row and the `gapCatalogue.ts` mirror are both present, and the missing-claim scan passes.
- Money formatting is unchanged. `cardValue` moved to `PortfolioOutcomes.tsx` without edits, and no amount is summed across kinds. No category or count carries an amount.

## Correctness review
- **A1 outcome map** (`backend/assetops_backend/outcomes/outcome_map.py`, `catalogue.py`):
  - It is pure: it imports only `__future__`, `dataclasses`, `typing`, `collections.abc` and its own package, and an AST test enforces this.
  - It is versioned as `outcome-map/1`.
  - The entries match spec §1.3 exactly.
  - Item order follows A-Q3: MOVES categories in first-appearance order, then CHECKED categories.
  - An unknown mechanism, `None`, a cross-domain request, an unknown domain and a `@LINKED` key from another domain each give NOT_MAPPED.
  - `COLD_KIND_MECHANISM` and the domain literals are asserted equal to their sources.
- **A2 and A3 categories on every named read:** estate Findings rows, Portfolio rows (Site type mapped through `DOMAIN_OF_SITE_TYPE`), `summary.category_counts`, mini index rows, mini detail, cold items and detail, EV items and detail, and the mini Action read (from the `reserve_trial.MECHANISM` default).
  - `category_counts` has all four keys.
  - Its counts are null unless F is known.
  - `open_findings` counts members with the category in any role.
  - `sites_with_primary_finding` counts distinct Sites by the primary moved outcome.
  - NOT_MAPPED members are skipped.
- **The UI shows no codes.** Pills and lines render labels only. The accessible names come from visually hidden text, with `title` used only as an addition.

## Checks I ran (on `7b826e97`)
| Check | Result |
|---|---|
| `.agent/OUT-A-golden-equality.py` (plan2 venv, PYTHONPATH=backend; `main` = `cbc32703`) | exit 0. `w301-estate-golden` equal (raw), main=0 / new=12 categories keys. `s6_action_api_contract` equal after the test's own normaliser, new=5. `s6_verification_api_contract` equal except 2 `selection_seq` leaves (19→27, 22→30), new=1. The script strips only `categories` and tolerates only `selection_seq` leaves. Any differing key set fails. |
| Focused backend, `tools\run-host-tests.ps1` on 11 files (out_a1, w301_estate_api, w303_portfolio_api, s4_finding_api, s4_finding_index_postgres, w203_cold_reads_postgres, w206_ev_reads_postgres, s6_action_records_postgres, w301_estate_golden_postgres, w303_selectors_postgres, w303_portfolio_scope_snapshot_postgres) | 98 passed, 2 failed, 2170 s. The 2 failures are exactly the known CC-R2 tests: `test_w303_selectors_postgres::test_portfolio_row_facts_and_verification_ids_match_stored_rows` and `test_w303_portfolio_scope_snapshot_postgres::test_three_domains_same_window_cutoff_and_full_selection_ids` (`'COLD_EXCURSION' is None`). |
| Focused vitest on 11 files (estatePortfolio, estateRoots, s404SiteFindingIndex, coldFindingIndex, coldRoutes, evAssessmentRoutes, evFindingIndex, siteAction, siteActionVerification, siteFinding, w1f4VerificationStructure) | 433 passed, 3 failed. The 3 failures are exactly the known w1f4 tests ("elements before panel 1 of v69 screen verification"). |
| The same w1f4 file on a temporary detached checkout of main `cbc32703` (worktree since removed) | the same 3 failures with the same message, so they are pre-existing and not caused by the Affects line |
| `outcomeCategories.test.tsx` | 14/14 |
| `npx.cmd tsc --noEmit` | clean |
| `tools\check-all.ps1` (run directly; `ASSETOPS_GUARD_PYTHON` = plan2 venv) | All 11 guards passed |
| Process | `git ls-files var` gives 0. Nothing under `tools/checks` changed. No `-ExecutionPolicy` in the diff. Test runs used harness-owned `_test` databases only. |

**Not rerun:**
- The full backend suite. I cite the implementer's run `20261030-083106-83d548` at `a1733184`: `-Tier fast`, 4143 cases, 0 skipped, 2 failed, 2658 s. `a1733184` is the product revision. The commits after it are captures, docs and the main merge (tools and docs only), which I confirmed from the diff file list.
- The full vitest suite.
- The captures. I inspected them but did not recapture.

## Tests and planted failures
- The purity test is non-vacuous by construction: it fails on any import outside the allowlist.
- The vocabulary test asserts that the mock label "Buses ready to run" is caught.
- The pill contrast test computes ratios of at least 4.5 from the tokens.
- The w301 golden writer checks that each kept marker still resolves to the actual value.
- The five-card tests were rewritten to the four cards, and every money and href assertion was kept, now on Optimize. No assertion was dropped without a replacement. The new Protect, Assure and Optimize-missing tests cover the case tables in spec A6.
- **`frontend/src/test/panelStructure.ts`:** this is a test helper, not a guard. It adds `[data-affects-line]` as an allowed leading row. That is legitimate, because the mock places the line before the body (`screens.js:990-991`).

## Captures
- I compared the Portfolio at 1440 and 390, the GreenHarvest start-failure Finding page at 1440 and ACT-048 verification at 1440 with their v70 pairs.
  - The pills, the line and the card layout match the mock: 4 columns at 1440, 2 at ≤1200 and at 390.
  - The only unregistered visual departure is H1.
- At 390, `raw-evidence.json` records `scrollWidth == clientWidth` on every capture. The Portfolio 390 capture shows no page-level overflow; the ranked table scrolls inside its own container, as it did before this slice.
- The run 1 Kobo replay Site Findings capture rendered no rows (a 409). The Kobo Site Findings evidence comes from the estate-case capture instead, as the packet says.

## Residual risk
- These are as the packet states: no combined three-domain estate exists, and the full vitest suite has load-sensitive EV and cold tests.
- A further risk the packet does not name: the Portfolio Protect count comes from the estate case, which has mini-grid Sites only. So "No sites disrupted" is the only Protect value seen in a capture. The 1, 2 and null forms are proven only in unit tests.

## Coordinator verification, 2026-10-30: ACCEPT
- H1 closed: register row R529 added (Portfolio card site dots, D5 build order, resolved by OUT-B B6). No code changed.
- check-all.ps1 run directly with no override: 11/11 passed.
- L1 ("Candidate" in the Optimize card detail) is logged for the plain-language pass.
