# W3-03 review packet (Portfolio composition)

Task: W3-03 `tasks/W3-03-*`; contract `.agent/W3-03-build-spec.md` (closures 4-5, r0a..r3b). Branch
`task/W3-03-portfolio-composition`; reviewed baseline `04474b3c` (run 2); packet head = the commit after `13624ab2`.
USER_REVIEW: UI slice; hold the merge for the owner walkthrough (W1 rule).
Independent-review command: `git diff 6cdb8c4b..HEAD -- ':!.agent'` (6cdb8c4b = merge base with main; 49 files, +5419/-130).

## Commits
0a Lane A `87f8ffed` `9f24f4e5`; 0b `45592a22` `7ab8019a` `e21a9355`; 1a `450f5f9f` `565335aa`; 1b Lane A `06acf1cf`
`f5407e95`, Lane B `f3f04ef6` `3a0d96bc` `6c4e0449` `0f29d4cb` `271577c6` `1a5c0c2f`; run 2 `2845897c` `a0631e80` `d3fb632b`
`4a1fd7f9` `5cef129c` `c501d089` `04474b3c`; P-2-1 `63e83d83`; run 3 `8af47c17` (registry), `e055b841` (captures), r3b `13624ab2`.
Handoff-only commits and main merges omitted. No migration file is in the range (no path under any `versions/` dir
changed; no `0031` file exists).

## Files materially changed
- Lane A (existing estate files): `estate/coverage.py`, `financials.py`, `index.py`, `scope.py`, `evidence_money.py`,
  `adapters/postgres_estate_read.py`, `evidence/adapters/postgres_evidence_ledger.py`, `main.py` (mount), `estateClient.ts`,
  shell `App.tsx`, `EstateRootFrames.tsx`, `OperatorShellLayout.tsx`, `operatorSiteRoutes.ts`, registry/ledger JSON,
  `ui/gapCatalogue.ts`, `test/panelStructure.ts`, `test/settled.ts`, two navigation guard fixtures.
- Lane B: `estate/portfolio.py`, `estate_portfolio_api.py`, `estate/composition.py`, `EstatePortfolio.tsx`,
  `portfolioWords.ts`, `estatePortfolio.css`; tests `test_w303_*`, `estatePortfolio*.test.tsx`, `portfolioFixtures.ts`.
- Evidence: `.agent/W3-03-evidence/` (`test_serve_portfolio.py`, `capture-portfolio.mjs`, eight `app-portfolio-<state>.json`,
  `portfolio-<state>-{1440,390}-app.png`).

## Acceptance
| Criterion | Status / proof |
| --- | --- |
| One-snapshot four-selector scope, auth, signed cursor, selection token | Met: `test_w303_portfolio_scope_snapshot_postgres.py` (12 selector calls + 1 action, 1 snapshot), `test_w303_portfolio_api.py` cursor/refusal tests; reviews 1a, 1b |
| Full-scope cards, matrix, prompt, opportunity, progress, footer; never paged; no client sum | Met: `test_full_scope_projections_ignore_page_size_and_empty_scope`, comparison/fixture Postgres tests, page tests |
| B3 one-day three-domain persisted proof; W1/cold/EV money boundaries | Met in `test_w303_portfolio_fixture_postgres.py` (cold excursion + W2-04 drain, r0b) |
| Q9 variants | Pure vs persisted per r1b3 (P-1b-1..6), see limitations |
| Page: v69 panel order/titles, 1440/390 caps, empty/pending/historical/refusal states | Met; eight captures below, `expectV69Panels` and planted-panel rejection |
| Refusal clearing (409 on load-more), 401/503 show no privileged block | Met: captures refusal-409/401/503 |
| Registry: four `panels` rows (`gap`), nodes `I-estate-portfolio-read`/`-ui`, `G-portfolio-opportunity` gap + mirror + two `MissingClaim` | Met (r2, r3): registry checker exit 0, missing-claim scan, check-all 11/11 |
| Empty-state copy r3b | Met: `No supported value` (API `DISPLAYED_VALUE` + `CARD_VALUE` fallback), exact tests in both stacks |

## Independent reviews
| Unit | Verdict |
| --- | --- |
| spec review / closure checks 1-5 | closed before build (`W3-03-spec-review.md`, `closure-check*.md`, `closure4-check.md`, `seam-recheck.md`) |
| 0a | REVISE (M1 `_windows_covered`) then ACCEPT (`0a-review`, `0a-rereview`) |
| 0b | REVISE (H1 re-pin clock, M1/M2, Lows) then ACCEPT (`0b-review`, `0b-rereview`) |
| 1a | REVISE (M1 `finding_count` on partial coverage), fixed in `565335aa` (`1a-review`) |
| 1b (with r1a fix) | ACCEPT (`1b-review`); Lows closed in r1b3/`1a5c0c2f` |
| final review | pending (next step) |

## Ruling rounds applied
Closures 4-5 (B1-B4, S1-S19, N1-N10; S4 reductions, S7 workflow labels); r0a (0a), r0b (P-0b-1 cold excursion + drain);
r1a (Q-1a-1 private `_selected_recorded_at`, eleven readings); r1a2 (review items); r1b (Q-1b-1 cursor key, Q-1b-2
workflow-label precedence, Q-1b-3 line-less guard); r1b2 (readings R1-R13); r1b3 (P-1b-1..6); r1b4 (1b review Lows);
r2 (P-2-1 + eleven readings, all Confirm); r3 (P-3-1 registry nodes); r3b (P-3-2 literal + scroll gate).
All pending items in `W3-03-pending-rulings.md` are marked RESOLVED.

## Builder readings
Run-0a readings 1-6 (`W3-03-phase-handoff.md` "Readings"): first of six runs; private `_domain/_episode_end/_mechanism`
and `_plans/_outcomes/_outcome_id` keys keep root bytes; nonnull `state_filter` or bad lens = 422; cursor tests in
`test_w303_estate_cursor.py`; client status union deferred. Runs 1a/1b readings (eleven + R4-R13) and run-2 readings
1-11 are in the handoff and build spec "Eleven handoff readings", "Five 1b readings", "Eleven run-2 readings"; all ruled
(Confirm or replaced) by r1a/r1b2/r2.

## Accepted limitations
- Q9 (a)-(d) variants and the persisted overlap/false-guard/two-Action-tie cases are proven pure or on a fake snapshot,
  not persisted (r1b3).
- Opportunity CTAs and unlinked Finding/Site targets are inert "Not available yet" (G-portfolio-opportunity).
- Registry rows stay `gap` until independent whole-slice review; `A-estate-comparability` is not closed here.
- Second Action row on one Finding origin is not persisted in any fixture.

## Checks run (head `13624ab2` code; packet commit adds only `.agent` files)
- Focused: `estatePortfolio.test.tsx` 15/15; `test_w303_portfolio_api.py` 4 passed, 1 skipped (Postgres-only).
- Full frontend suite, run 1: 104 files, 2450/2450 passed. Run 2: 104 files, 2450/2450 passed.
  Earlier run (before r3b) failed once: `s404SiteFindingIndex.test.tsx` "changing the dates writes a new window"
  (`toHaveValue 2026-10-20`); it passed alone (37/37) and in both reruns above, so it is a flake under full-suite load.
- `tsc --noEmit` exit 0; `npm run build` ok; `tools/check-all.ps1` 11/11 guards passed.
- Full real-Postgres backend suite (coordinator, in-container OPS-03 run 20261022-015213-39681c on 782c3044 code; later commits are .agent-only): 3703 passed, 0 failed, 56:44. An earlier run on 85efbea7 reached 95% with 0 failures before the 100-minute cap under load.

## Captures (Vite via localhost -> API :9781, private `w303p_test`, dropped; `.agent/W3-03-evidence/`)
| State | Status | Matrix Sites | Doc height 1440/390 | over / failed |
| --- | --- | --- | --- | --- |
| positive | CURRENT | 4 | 1362 / 2947 | [] / [] |
| partial | UNKNOWN | 5 | 1319 / 2966 | [] / [] |
| historical | HISTORICAL | 5 | 1319 / 2732 | [] / [] |
| pending | PENDING | 4 | 1362 / 2947 | [] / [] |
| empty | EMPTY_SCOPE | 0 | 1232 / 2614 | [] / [] (390 card0 = card1 = 194 <= 207) |
| refusal-401 / 503 / 409 | UNAUTHENTICATED / ESTATE_STORE_UNAVAILABLE / ESTATE_BASIS_CHANGED | 0 | refusal | [] / [] |
Matrix-scroll gate: 390 and >= 4 Sites needs `scrollWidth > clientWidth` (positive, partial, historical, pending pass);
fewer Sites assert the exact column count and the container. Empty 390 image viewed: "No supported value" fits two-line
in the first-row cards, no overflow.

## Known deviations
None new. P-3-2 resolved by r3b.

## Final-review fix round (rF; M1, M2, L1-L5)
- M1: `ContextFooter` `Energy basis ↗` disclosure (selected window + six source fields, `No selected source basis` fallback; none when footer null); test opens it.
- M2 (docs only): `backend/README-db.md` "Portfolio cursor key" block before `# serve`; the 503 missing/malformed-key assertion already exists in `test_w303_portfolio_api.py` (kept).
- L1 suffix only for PARTIAL/UNKNOWN; L2 `Finding {site_code} · {finding_id}` (twin-prefix test); L4 footnote literal + absence assertions (stocked and partial); L3/L5 left as ruled.
- Recaptured positive, pending, partial, historical, empty (refusals unchanged): all `over=[]`, `failed=[]`; positive 1440 image viewed. Docs: positive 1381/2985, partial 1338/3024, historical 1335/2732, empty 1248/2577.
- Checks: tsc 0; frontend 104 files all pass; build ok; check-all run.

## Owner walkthrough preconditions
Set ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX in the backend server environment before starting the API; follow backend/README-db.md. Confirm an authenticated GET /api/estate/portfolio returns 200 before opening /portfolio.

## Residual risk / user-review focus
Owner walkthrough of the Portfolio page at 390 (stacked cards, matrix horizontal scroll) and the empty state wording;
registry `gap` statuses after final review.
