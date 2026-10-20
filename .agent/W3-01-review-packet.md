# W3-01 review packet (estate Finding and Action roots)

Task `tasks/W3-01-estate-claim-action-roots.md`; spec `.agent/W3-01-build-spec.md` (commits 1-4, Runs 1-13, c1r1, c2r1,
c3r1). Branch `task/W3-01-estate-claim-action-roots`. Commit 4 = captures + this packet. Main merged at `a4dafe30` (after the checks: `.agent` files only).

## Commits
- Commit 1 (shared provenance DTO): Lane B `public_provenance.py` + Lane A compatibility; fix round r1.
- Prerequisites (q5/q6): `*_on` snapshot helpers, money helpers `0a`/`0b`, estate cold/EV selection mode.
- Commit 2 (estate core/API): `0b56f150`, `58b00bb6`, `c951dd8b`, `187a7020`, `9b2c09cd`, `4a311ae5`, Lane A
  `d9039997`, q10 `5d8c5794`, c2r1 `dc573bd9` (+ `7ff49e0c`), q12 `8c7be299`.
- Commit 3 (five roots): `5a72feea`, Lane A `013cdb38`, `483973f9`; fix round `97a68db0` (re-review ACCEPT, `76f2890f`).
- Commit 4: `89c53b0e` (CSS: state chips one scrolling row at 390), `3284909f` (captures), this packet.

## Files materially changed
- Backend: `estate/{scope,coverage,index,composition}.py`, `estate/adapters/postgres_estate_read.py`, `estate_api.py`,
  `evidence/public_provenance.py`, `financials/{consequence_read,money_eligibility}.py` (0a/0b), the two analytics
  adapters, `main.py` mount; guard `tools/checks/configuration-persistence.ps1` (`estate` domain).
- Frontend: `frontend/src/estate/{estateClient.ts,estateShared.tsx,findingIndex.tsx,actionIndex.tsx,estate.css}`,
  `shell/EstateRootFrames.tsx`, `App.tsx`, `operatorSiteRoutes.ts`, rail + `navigation-truthfulness.ps1`, registry.
- Tests: `backend/tests/test_w301_*` (10 files), golden `backend/tests/fixtures/w3/w301-estate-golden.json`,
  `frontend/src/estate/__tests__/estateRoots.test.tsx`, `shell/__tests__/w301EstateShellRoutes.test.tsx`.

## Acceptance
| Criterion | Status |
| --- | --- |
| Read-only, one REPEATABLE READ snapshot; no migration/Alembic head | Met (c2 review; `test_estate_injected_reads_share_one_connection`) |
| Scope auth, foreign excluded, missing Site kept | Met: tests + capture (FOREIGN-001 absent from scope; Site read 404) |
| Full-set summary/token before paging; cursor fence; page-one mode | Met: index/API tests; capture page one/two below |
| Five roots per v6.9 panels/copy; Site lens chips stay unavailable | Met, except q14-1 (1440 cards 150 px vs cap 146) |
| Positive/empty/partial/pending/late captures at 1440/390 | Met: 52 measured captures, no page overflow |
| Global Actions rail live; `/findings` replaced, `/api/findings` kept | Met (commit 3, nav guard) |
| Owner W3 checkpoint | Pending: independent review first |

## Captures (`.agent/W3-01-evidence/`)
Harness: `serve.py` seeds private `w301cap_test` (dropped after) through the replay paths into one `demo` tenant, then
serves the real `create_app()` (9741) behind vite (6141). `capture.mjs` captures app PNGs + rectangles per state;
`reads.py` records full public bodies (`reads-<state>.json`); `summarize.py` compares every piece with the spec caps
(`measure-summary.json`); mock: `node tools/measure-mock-panels.mjs .agent/W3-01-evidence/mock <5 screens>`.
- Sites (public `/api/estate/scope`, tenant `00000005-...0001`, `access_basis sha256:607f52e2...2b927`):
  COLD-LAB-001 `...0002` (W2-02 `late-reading`, settled), EV-LAB-001 `...0176` (W2-05b `interrupted`, settled,
  W2-07 tariff + money worker), KOBO-001 `...03d7` (S4 F01+F02, S6 Action bound), W301-EMPTY-001 `...0611` (added
  for partial). FOREIGN-001 `...060c` under tenant `...060b`: never in scope; `/api/sites/FOREIGN-001/finding-index`
  404 `No imported Site 'FOREIGN-001' in this tenant.`
- Positive, day `2026-10-06` (all IDs prefix `00000005-0000-4000-8000-`): Findings token `sha256:e58506f5...90bb4`,
  4 rows, all SUPPORTED/UNPRICED: COLD `...016d`/rev `...016e` (basis `sha256:e94d47d1...`), COLD `...0173`/`...0174`
  (`sha256:8dd768eb...`), EV `...03ce`/`...03cf` (`sha256:a97b912f...`), KOBO `...04bd`/`...058c` (UNKNOWN source,
  `sha256:9a140c3b...`). Selections: cold `...0170`, EV `...03c7`, KOBO `...0584`. Actions window 11-01..11-03:
  `ACT-000001` `...0561`, event `...057f`, source F01 rev `...04be` (origin != selected head `...058c`), APPLIED,
  token `sha256:6f3cb410...`.
- Complete empty: `state=merged`, Cost, Risks, Opportunities on the day; Actions on the day (`No actions match.`).
- Pending: `/__capture/late-kobo` delivered one KOBO SOC reading for 2026-10-06 decided 2026-11-02T11:08Z.
  KOBO `PENDING_RECOMPUTE` (job PENDING), its row withheld, totals null.
- Live page one/two (`limit=1`): page one live; cursor `page_one_mode: live`, `known_at 11:09:06.14Z`. Page two:
  top-level `HISTORICAL`, `as_of = window.known_at`, coverage (KOBO PENDING) and token equal, no KOBO row.
  UI capture `findings-page-two-pending-*` shows `This is an earlier evidence cutoff.` beside `New evidence is being
  assessed.`. The explicit-historical cursor (`known_at 11:07:15Z`) has `page_one_mode: historical`, same equalities.
- Late/historical: `known_at=2026-11-02T11:07:15Z` (before the late delivery). Findings 4 rows, every Site
  `HISTORICAL`, `as_of` set; Actions HISTORICAL with 1 row.
- Partial: after `W301-EMPTY-001`, Findings coverage `UNKNOWN/MISSING` for it; `Some sites have no selected result;
  totals are unknown.`. Actions stay complete (q14-3). Refusal: 33-day window -> 422 `INVALID_WINDOW`, UI `Choose a
  valid date range of at most 31 days.`; malformed cursor 422 `INVALID_CURSOR`.

## Panel heights (app max over all states / spec cap, px)
| Screen | W | cards | chips | panel | notice | page | overflowX |
| --- | ---: | --- | --- | --- | --- | --- | ---: |
| findings | 1440 | **150/146** | 33/40 | 454/575 | 43/54 | 1083/1431 | 0 |
| findings | 390 | 285/322 | 33/40 | 456/975 | 80/101 | 1457/2245 | 0 |
| findings-cost | 1440 | **150/146** | 33/40 | 165/240 | 43/54 | 1000/1431 | 0 |
| findings-cost | 390 | 285/322 | 33/40 | 165/341 | 43/101 | 1128/1579 | 0 |
| findings-risks | 1440 | **150/146** | 33/40 | 165/439 | 43/54 | 1000/1431 | 0 |
| findings-risks | 390 | 285/322 | 33/40 | 165/721 | 43/101 | 1128/1937 | 0 |
| findings-opportunities | 1440 | **150/146** | 33/40 | 165/240 | 43/54 | 1000/1431 | 0 |
| findings-opportunities | 390 | 285/322 | 33/40 | 165/341 | 43/101 | 1128/1579 | 0 |
| actions | 1440 | 115/146 | - | 201/436 | 43/54 | 1000/1431 | 0 |
| actions | 390 | 251/322 | - | 219/767 | 61/78 | 1059/1820 | 0 |
At 390 every table scrolls inside its panel (Findings scroll 900 > client 318, Actions 820 > 318), first column
`position: sticky`. The chip row scrolls in one row (scroll 460 > client 358); lens tabs are one row everywhere; no
text clipping. Before `89c53b0e` the 390 chip row measured 73 px (two wrapped rows, cap 40): the shared
`.v69-chips { flex-wrap: wrap }` rule won the cascade. The 1440 page is the 1000 px viewport floor.
The mock re-measured at 390 gives Findings panel 716, Cost/Opp 230, Risks 522, Actions 575/notice 60. The spec's caps
(750/263/555/590) are used unchanged.

## Checks (serial; private base `w301cap_test`, dropped)
- Focused backend at `3284909f`+main merge: 13 files (all `test_w301_*`, `test_lr01_money_eligibility_postgres.py`,
  `test_s4_consequence_read.py`, `tools/checks/test_estate_guard.py`): JUnit 75 tests, 0 failures/errors/skipped,
  1131.7 s. Includes `test_cold_revision_waits_for_its_selected_assessment` (the corrected q12 L2 assertion), golden
  `[mini_grid,cold,ev,mixed]` and `test_w301_golden_clock_plus_30_days[mini_grid,mixed]`.
- Frontend `npx vitest run`: 94 files, 2373 passed (3 min 8 s). `npm run build` (tsc + vite): ok, with the existing
  chunk-size warning.
- `tools/check-all.ps1`: all 11 guards passed (architecture, workflow, navigation, registry, ledger, estate guard).
- Full real-Postgres backend suite: **not run here**, by instruction (it runs in parallel with the final review).

## Merge hazard: the money helpers survived
`git diff 75f4e4c8 HEAD` is empty for `consequence_read.py`, `money_eligibility.py`,
`test_w301_w1_money_snapshot_helpers_postgres.py`, both analytics adapters and `postgres_evidence_ledger.py`.
At HEAD: `select_consequence_on` 1, `for_finding_on` 1, helper tests 6. Main `a4dafe30` has 0/0/0 (the W4 revert of
the 0b cherry-pick). Main is an ancestor of HEAD. **Merge W3-01 into main keeping HEAD's side for these six files.**

## Builder readings (not rulings; confirm at review)
- q8 1-11 and q9-2, q10 2-4, q11-1: in `.agent/W3-01-pending-rulings.md`. Ruled by Runs 9-12 and c2r1, except the
  readings those runs confirmed as built.
- c2r1 readings 1-7 (`.agent/W3-01-phase-handoff.md` "Commit-2 fix round r1"):
  - (1) page-two Site label: superseded by Run 12.
  - (2) STALE through a `dispatch_days` wrapper.
  - (3) the L2 test re-dates one revision by 1 s.
  - (4) the forged selection digest plus a grant change.
  - (5) forced-clock unshift rules.
  - (6) the EV inline catch-all is left as is.
  - (7) the golden test disposes the engine pool.
- q13 readings 1-12: ruled by Run 13.
- Commit-3 fix reading: mini-grid = `coverage.sites[].match_state !== "NOT_APPLICABLE"`. The re-review found it
  sound, with an optional Low (no wire `domain` field).
- Commit 4 (q14): 2 pending chip shown as the limitation sentence, because the rows are withheld; 3 Actions not
  partial for a no-selection Site; 4 capture clock pinned TEST-SCOPED.
- Observation, unverified: the 390 refusal capture shows a tall dark band under the shell header. The shell header was
  not touched by W3-01.

## Accepted limitations / known deviations
- **L2 widened job** (prerequisite r1 L2, Run 6 reading 4): a PENDING job's window can widen in place after `k` with no
  stored window history. A historical mini-grid day it did not cover at `k` reads pending, not unavailable.
- **Clock-drift residual**: the S4/S6 fixture clock (2026-10-29..11-02) is ahead of the DB clock. Golden and these
  captures pin the read clock to `max(fixture now + 1 min, DB now)`. The c2r1 forced-clock proof (+30 days) passes.
  Literals that depend on the watermark may move once the real date passes the fixture dates.
- **Zero awaiting-verification** (q9-2, ruled): the S6 settle re-revises F01, so the Action origin (`...04be`) is
  never the selected head (`...058c`). The card is an honest 0, with the ruled zero copy.
- **q14-1 open**: Findings cards at 1440 are 150 px against the 146 cap on all four lenses in complete states. This
  is caused by the ruled zero copy. Not changed; awaiting a ruling.
- Golden is a digest canonicalizer plus whole-response comparison, not an independent selection oracle (c2r1 L4).
  STALE/LEASED/FAILED are unit proof only (q10-2).
- Every Finding consequence in the persisted replays is UNPRICED. No PRICED Cost row is captured; PRICED Cost is
  test proof only (`test_cost_lens_only_exact_eligible_current_rows`).

## User review
`USER_REVIEW_REQUIRED`: owner W3 checkpoint after independent review. Focus:
- the q14-1 card height;
- the five roots side by side with `mock/mock-*.png`;
- pending vs historical copy on `findings-page-two-pending-*`.

## Final review fix (q14)
- `frontend/src/estate/estate.css`: `.estate-page .data-table thead th:first-child { background: var(--surface-sunken); z-index: 2; }` (sticky first header cell now matches the header band).
- New captures (positive state, private DB `w301cap2_test`, dropped after), viewed: header row is one uniform grey band at both widths. `findings-positive-1440-app.png`, `findings-positive-390-app.png`, `actions-positive-1440-app.png`, `actions-positive-390-app.png`; entries in `app-positive.json` replaced and re-measured, `measure-summary.json` regenerated: 52 rows, 0 over cap, overflowX 0.
- q14-1 waiver recorded: Findings card-row cap is 150 at 1440 for the four lenses (`summarize.py` `F[1440].cards`); measured 150/150.
- Checks: frontend 2373 passed (94 files), tsc clean, `npm run build` ok, check-all 11/11.
