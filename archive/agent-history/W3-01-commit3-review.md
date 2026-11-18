# W3-01 commit 3 review and main-merge check (independent)

Branch `task/W3-01-estate-claim-action-roots` at `8d289359`, worktree `AssetOpsV1-review2`. Reviewer: a fresh Claude
reviewer, not an author of this work. The review is read-only apart from this file.

**Verdict: REVISE (test-only).** The merge is safe: no W4-01 change was lost. Commit 3 matches the spec, rulings q6 and
q8–q12, and the v69 panel set, order and titles. It has no High finding. One Medium finding, a test-coverage gap, blocks
under the High/Medium rule. Fix it on the branch in the same round that applies q13. The q13 rulings are open work, not
findings against this revision.

## Part A: merge `96a2df01` (main `32a936b7` into W3 `75f4e4c8`)

The merge base is `654f4c8f`. For each file, `git diff 96a2df01^2 96a2df01` lists every line that main had and the merge
lacks. Each one was traced with `git log -S`.

| File | Lines main had that the merge lacks | Classification |
| --- | --- | --- |
| `analytics/adapters/postgres_assessment_store.py` | 1. `_bound_link_rows` try/except `Exception` → `unavailable(...)`. | (a) This is older W3 code. It was added by W3 `503c0245`/`c4631e1a` and removed by W3 c2 r1 L1 (`ee5900f2`). Dropping it is correct. |
| | 2. Six raises of plain `ColdReadUnavailable` / `EvReadUnavailable`, where the merge raises `ColdPinnedLineageUnavailable` / `EvPinnedLineageUnavailable`. | (a) These are the older W3 copy. The subclasses come from W3 `ee5900f2` (c2 r1 L1). |
| | 3. The selection dict without `model_version` / `cohort`. | (a) The merge keeps the W3 `0b` addition (`da15d71f`). Main reverted it in `7876b79c`. |
| `analytics/adapters/postgres_finding_store.py` | None. The merge only adds `money_revision_on`, which is the W3 `0b` code that main reverted in `7876b79c`. | (a) |
| `main.py` | `from ...sites.ports import SiteRepository, SiteTemplateCatalog`. The merge's line adds `SiteStoreUnavailable`, so this is a superset. | No loss. The W4 work router and every W4 line (`5973ca09`, `3353e858`, `998d3330`) are present. |
| `tools/checks/configuration-persistence.ps1` | None. The merge only adds the `estate` domain entry. The W4 `work` domain, `$pgWriters`, and `$pgReaders` are main's lines. | No loss. |

I also checked every other file where the merge drops lines that main has (`git diff --numstat` with deletions > 0):

- `postgres_evidence_ledger.py`, `postgres_assumption_store.py` and `money_eligibility.py` are byte-identical to the merge
  base on main. The merge equals the W3 side.
- In `postgres_consequence_store.py`, main's only change since the base is W3 `503c0245`'s `r.finding_revision_id` line,
  and the merge contains it at line 1116. The dropped block is the base-era inline `load_input` body, which W3 `0a`
  refactored into `load_input_on`.

No file that exists on main is missing from the merge. **No genuine W4-01 change was lost (zero class-(b) hunks).** The
handoff's reading ("main = W3 pre-c2r1 minus 0b, take HEAD") is confirmed.

These symbols survive at HEAD:

- `ConsequenceReadService.select_consequence_on` (`financials/consequence_read.py:274`)
- `MoneyEligibility.for_finding_on` (`financials/money_eligibility.py:192`)
- `PostgresFindingStore.money_revision_on` (`postgres_finding_store.py:518`)

`backend/tests/test_w301_w1_money_snapshot_helpers_postgres.py` is unchanged by the merge. It ran in the focused set below.

## Part B: commit 3 (`8c7be299`, `5a72feea`, `013cdb38`, `483973f9`)

### Conformance (checked, no finding)

- **Panels, order and titles.**
  - The Findings lens roots render: header, lens tabs, date bar, four cards, state chips, the panel (`Findings across the
    estate` / `Cost lens` / `Risks lens` / `Opportunities lens` with the mock subcopy), the limitation notice, and the
    static notice.
  - The Actions root renders: header, date bar, four cards, `Managed actions`, the limitation notice, and the notice.
  - This order matches `screens.js:506-510,806-810,931`.
  - Columns and widths match the dry-read (23/13/10/11/11/22/10 and 24/13/17/11/13/22).
  - `expectV69Panels` runs for all five screens.
  - The rewrites are all ruled:
    - `Supported findings` (B3)
    - the Actions lifecycle line (B9, q13-8)
    - the Actions notice (dry-read)
    - the date bar (S17)
    - no fake seven-cell empty row (dry-read)
- **Wire.** `estateClient.ts` types `estate-finding-index-2`, including `episode_start`, row `status`, `amount_low`,
  `amount_high` and the `amount` alias. Actions and scope stay `-1`. Any other `schema_version` is treated as 503.
  Refusal copy matches the refusal table exactly for all nine codes.
- **Cursor.** The cursor is opaque and passed back unchanged, so `page_one_mode` rides inside it. Lens tabs, state chips,
  the date bar and the First-page link all drop the cursor. Only the Next link carries it. A 409 `ESTATE_BASIS_CHANGED`
  or 422 `INVALID_CURSOR` shows `Reload the first page.` with a page-one link (tested).
- **Date/cutoff bar.**
  - The window is given in UTC days.
  - The cutoff is the response's `window.known_at`.
  - On a top-level `HISTORICAL` read the bar shows `This is an earlier evidence cutoff.`, while row Site chips keep the
    literal basis state (q12-3, tested with a PENDING chip on a HISTORICAL page two).
  - The default window is seven whole UTC days with `known_at` omitted (tested).
- **Consequence cell.** The five q6/q13-5 presentations are present. The priced cell shows the interval only, with no
  sum and no point estimate.
- **Honest empties.** Risks and Opportunities show `No findings match.` plus their ruled line (tested). The backend never
  sets the RISK/OPPORTUNITY flags. Partial coverage shows the totals-unknown line instead of a zero.
- **Actions rail.** `OperatorShellLayout` has Actions `live` → `/actions`. The navigation tuple is
  `live|Actions|WORK|/actions`. Four new rail fixtures cover: missing route, route removed, demoted, and Incidents
  promoted. Incidents and Maintenance stay unavailable. The three Site lens chips stay unavailable (tested).
- **Routes.** The four lens paths and `/actions` are registered before the legacy `/findings/:siteId/:assessmentId[/:tab]`
  routes. The legacy routes keep their handler: the test asserts the legacy client is called and the estate client is
  not. `/api/findings` is unchanged.
- **Registry and ledger.**
  - The four nodes are tagged `W3-01` and still `open`.
  - The five panels are `gap` with the reason "awaits independent review".
  - Ledger rows are `bounded`/`W3-01`, with `to_candidate:null`, tier `Deferred`, and `tier_approval: pending owner
    review`. This matches the W4-01 precedent (`sitework-incidents`).
  - Nothing claims owner acceptance.
- **`EstateRootFrames.tsx`** only adds the `<main>` landmark and a per-lens `key` remount. This is correct.
- **The nine updated existing test files, plus three in `483973f9`.** I found no weakening.
  - Each change appends `Actions`/`/actions` to an exact list, or raises the exact link count from 2 to 3. The lists
    stay exact.
  - `operatorRouteFrames` now also clicks through to the Actions root.
  - `t028Screens` drops the T028 global-index row assertions, because B1/B2 replace that element. It now asserts both
    legacy detail routes still render the Finding, with no estate root and no "Page not available".
  - The T028 row content is still covered by its Site-scoped tests.
- **q12 backend (`8c7be299`).** It removes the `_mini_grid` overwrite, sets `_windowed`/`_actions` Site state from
  `basis_historical`, puts `as_of` on every HISTORICAL response, and replaces the L2 assertion exactly, as ruled.

### Findings

**M1 (Medium, acceptance gap: test coverage). `frontend/src/estate/__tests__/estateRoots.test.tsx`.**

The commit-3 dry-read requires frontend tests to "cover every card, table column, chip, link,
empty/partial/historical/refusal string". These rendered strings have no assertion anywhere in the tests:

- `No actions match.`
- `Source unavailable`
- the Site chips `This result may miss newer readings.`, `Not yet assessed` and `Earlier evidence cutoff`
- the stale notice line `Some sites' results may miss newer readings.`
- the Actions null-card `Coverage incomplete` and `Due / overdue` partial branch
- `No action yet`
- the `No longer supported` and `Merged` chips and lifecycle chips
- the UI copy for `ESTATE_SELECTION_INCONSISTENT`, `INVALID_WINDOW`, `INVALID_KNOWN_AT`, `INVALID_LENS` and
  `INVALID_LIMIT`

The code paths exist and read correctly, but a regression in any of them would go undetected.

Fix: extend the named tests on the branch. The natural time is the q13 round, since q13-2's five stable chips make the
chip assertions direct.

**L4 (Low, test strength). `frontend/src/estate/__tests__/estateRoots.test.tsx:139`.**

`test_five_mock_panels_and_supported_links` renders the Actions root and asserts only `expectV69Panels("actions")`.
Its comment says "exact Action and pinned source links". The links are asserted only in the second test, through the
fixture's literal hrefs.

Fix (optional): the first test should assert the Action/source hrefs and the absence of any
Incident/Maintenance link in the Actions root. The third test asserts this only for a Findings fixture shape.

**L1 (Low, mock interaction). `frontend/src/estate/actionIndex.tsx:100-103`.**

In the Actions table, the Site cell is plain text (`site_name` over `site_code`). The v69 `actions` mock links the Site
(`link('mini','Kobo')`), and the Findings table links `site_code`. The spec column reads only "`Site`=`site name`", and
the Action wire has no `links.site`. This is not a panel, order or prominence mismatch.

Ask the Architect at the q13 round whether to link `/sites/{site_code}`, which is a reviewed route, as the Findings rows
do.

**L2 (Low, copy). `frontend/src/estate/estateShared.tsx:106-107`.**

While loading, or on a refusal of a live read, the bar reads `Evidence cutoff latest (latest at read time)`.

Fix: render one of the two phrases only.

**L3 (Low, dead code). `frontend/src/shell/SiteAnalyticsFrames.tsx:371`.**

`FindingsFrame` is now unmounted (B1/B2) but still exported.

Fix: remove it, or record it for the W1 conclusion pass.

### q13 rulings (`8c34f557`, on main and not yet applied): known open items, not findings

1. Keep `summary.as_of` on every HISTORICAL response. This is already built, and the golden `as_of` is retained.
2. Replace the page-derived `StateChips` (`findingIndex.tsx:180-216`) with five stable chips on every lens, including
   empty, filtered and paged reads. The chips carry no counts and no presence wording.
3. Cold/EV Finding titles become inert text, keeping the Site link and the disclosure. Only mini-grid rows link
   `links.finding` (`findingIndex.tsx:224`). `FINDINGS_NOTICE` (`findingIndex.tsx:95-96`) must become conditional or
   truthful for the mixed list. The ledger `findings` `supported_claim`/`interaction` text ("a row opens its exact
   Finding revision") must follow.
4. The test boundaries for readings 2–3 are confirmed. No change is required.
5. The consequence cell is confirmed as built.
6. The Site chips and the stale line are confirmed as built.
7. Replace `No closed verification yet` (`actionIndex.tsx:84`) with `No verified outcome in the last 30 days` on a
   complete response where `verified_in_30_days == 0`, independent of page rows. A partial response gets no note.
8. Readings 8–12 are confirmed, subject to item 3.

### Handoff readings classified

| Reading (`.agent/W3-01-phase-handoff.md`) | Status |
| --- | --- |
| q13 questions 1–2 and readings 1–12 (Lane B q12 + commit 3) | Covered by Run 13 rulings 1–8. Applying them is open (above). |
| Merge: take HEAD for both adapters ("Coordinator: confirm") | Covered. Verified in Part A; no Architect needed. |
| `EstateRootFrames` `<main aria-label>` wrapper | Covered: Lane A request item 1 ("needs the shell's `<main>`"). |
| `FindingsFrame` unmounted; `t028` global-index test retargeted | Covered: Review closure B1/B2. |
| Registry/ledger tagging (open, gap, bounded, `to_candidate:null`, tier pending) | Covered: spec commit sequence ("node's presence alone is not panel approval"), Lane A request item 5, and the W4-01 precedent. |
| Rail fixtures (4) and navigation tuple | Covered: dry-read and Lane A request item 3. |
| Actions Site cell unlinked (L1, found in review) | **Needs the Architect.** It is minor and can be batched with q13 application. |

No reading needs the Architect beyond L1.

## Checks run by this reviewer (at `8d289359`)

- `tools/check-architecture.ps1`: passed.
- `tools/check-agent-workflow.ps1`: passed.
- `tools/check-all.ps1`: all 11 guards passed (5 min 24 s). This includes navigation truthfulness, the dependency
  registry, the screen ledger and the estate guard self-tests.
- Frontend:
  - `npx.cmd tsc --noEmit` is clean.
  - `npm.cmd test` ran in this worktree: 94 files, 2370 passed, 0 failed (191 s).
  - `npm run build`: not run by me. The implementer reports it ok.
- Backend focused set on the private DB `w301z_test`, run serially:
  - Files: `test_w301_cold_selection_on_postgres`, `estate_api`, `estate_coverage`, `estate_golden_postgres`,
    `estate_index_ev_postgres`, `estate_index_postgres`, `ev_selection_on_postgres`, `provenance_dto_postgres`,
    `w1_money_snapshot_helpers_postgres` and `w1_snapshot_helpers_postgres`.
  - Result: 64 passed, 0 failed, 0 skipped (22 min 47 s).
  - The DB was dropped afterwards.
- Full backend suite: not run, per the dispatch. I found no same-revision full-suite evidence for `8d289359` in the
  handoff. The spec's closeout gate still requires one before W3-01 closes.

## Residual risk

- The layout is unproven until commit 4. The 390 rules are asserted as CSS text only, and the 1440/390 rectangles and
  captures are commit 4's.
- The mixed-branch golden literals may move after 2026-10-30. The handoff names this risk; the forced-clock test covers
  it.
