# Post-W6 W3-estate: verification packet

Branch `task/post-W6-W3-estate`, worktree `AssetOpsV1-review6`. The build is at `7f67154c` (main merged in). This verification batch adds `14441112`, `c9665a90`, `cc00730a`, `b81989b0` and `26e6c49c`, plus the packet commit. Authority: `.agent/post-W6-W3-estate-rulings.md` and `.agent/post-W6-W3-estate-build-rulings.md`.

## Changed files (branch vs main, product and tests)

- Backend production (rulings item 7, Q1): `backend/assetops_backend/estate/{evidence_money,portfolio,financials,index}.py`. No schema change. The nullable `links.finding` follows build ruling 1.
- Backend tests: `test_post_w6_w3_estate_links.py` (new), `test_w302_evidence_api.py`, `test_w302_evidence_ev_postgres.py`, `test_w302_money_api.py`, `test_w303_portfolio_api.py`, `test_w303_portfolio_comparison_postgres.py`, `test_w303_portfolio_scope_snapshot_postgres.py`.
- Frontend production: `frontend/src/estate/` files `EstateEvidence.tsx`, `EstateFinancials.tsx`, `EstatePortfolio.tsx`, `actionIndex.tsx`, `findingIndex.tsx`, `estateShared.tsx`, `estateClient.ts`, `estateEvidenceMoneyClient.ts`, `estateFinancialsWords.ts`, `portfolioWords.ts`, `estate.css`, `estateFinancials.css`, `estatePortfolio.css`.
- Frontend tests: `estateRoots`, `estateEvidence`, `estateFinancials`, `estatePortfolio`, `estateFixtures`, `portfolioFixtures`, and (this batch) `src/shell/__tests__/w301EstateShellRoutes.test.tsx`.
- Evidence: `.agent/W3-02-evidence/app-financials-{positive,partial}.json` and `financials-*-app.png` were regenerated (build ruling 3). New: `.agent/post-W6-W3-estate-recapture/`.

### Fixes made in this batch (within the rulings; all test-side)

1. `14441112`: in `test_w303_portfolio_scope_snapshot_postgres.py::test_evidence_prompt_null_steps_and_coverage_precedence`, the fake `_gap_row` had no `links`. The Q10 `objective_destinations` reads `row["links"]`, so the test raised `KeyError: 'links'` at `portfolio.py:326`. Real Evidence rows always carry `links`. The fake row now gets the unproven-window fallback (`site_readiness_label = CURRENT_VIEW`). There is no product change.
2. `c9665a90`: `w301EstateShellRoutes.test_estate_route_precedence_and_actions_rail` expected exactly one estate call per lens. Q7 adds the ruled `scope()` read at the same window, so the test now expects one `findings` call for the lens plus one `scope` call.
3. `26e6c49c`: build ruling 3. The Financials JSON is regenerated, and `meetsMeasuredNarrowLayoutWithoutDocumentOverflow` now asserts `maxHeight: none`, every row measured, and no vertical internal scroll. The document-overflow, piece-maxima, row-visibility, 448 px three-row, aggregation and opened-results checks are unchanged. **Non-vacuous proof:** I restored the old JSON (maxH `300px`) and the test failed with `positive register list has no vertical cap: expected '300px' to be 'none'`. Then I reverted it with `git checkout`.

## Test selection

**Backend.** I chose the backend files by grep:
- every test file that imports `assetops_backend.estate.{evidence_money,financials,index,portfolio}`, the estate API modules or `/api/estate`;
- plus all `test_w30[123]_*` and `test_post_w6_w3_estate_links.py` whose names match estate, evidence, financials, money, portfolio or selectors.

That gives 23 files, a superset of the 20 direct importers. It includes the three held Postgres files (`test_w303_portfolio_scope_snapshot_postgres.py`, `test_w303_portfolio_comparison_postgres.py`, `test_w302_evidence_ev_postgres.py`).

Excluded after inspection:
- `test_w601a/b/c/e`, `test_r373`, `test_s6_action_records_postgres`, `test_run_*` and `s7_health_cases` match "estate" only through `evidence/work/actions.composition`, or import only `estate_api.Authenticate`, which is unchanged.

I did not run a full backend suite, because there is no schema or shared plumbing change.

**Frontend.** Full vitest, `tsc --noEmit`, the production build, and `tools/check-all.ps1`.

## Results

- **Backend batch on the build head plus fixes.** Run with `python -m pytest <23 files> -n 2 --dist loadfile`, using the venv at `../AssetOpsV1/.venv` with `PYTHONPATH` set to the worktree, and `ASSETOPS_TEST_DATABASE_URL=…/assetops_test` (harness-derived `assetops_pt*_test` DBs).
  - Result: 231 passed, 1 failed (above), in 1637.8 s. JUnit: tests 232, failures 1, errors 0, **skipped 0**.
  - After fix 1, `test_w303_portfolio_scope_snapshot_postgres.py` alone gave **10 passed** (1139.7 s). The other 231 are unchanged by fix 1, which touches only that file.
- **Frontend full vitest, first run.** 2981 passed, 2 failed:
  - `w301EstateShellRoutes` is fixed above.
  - `evEnergy.energy_states_table_loading` timed out at 10.8 s while the Postgres batch was running. It passes in isolation (10/10, 452 ms) and is not touched by this branch.
  - The final rerun at the batch head is recorded below.
- **`npm run build`** (tsc plus vite) passed, built in 20.3 s.
- **`tools/check-all.ps1`**: all 11 guards passed (architecture, estate guard self-tests 4 passed, navigation, workflow, missing-claim and others).
- **Final vitest and tsc rerun at the batch head:** see the addendum at the end.

## Recapture (`.agent/post-W6-W3-estate-recapture/`)

**Tools.**
- `tools/capture.mjs` is batch-11's `capture-b11.mjs` with three changes: CDP 9520, the profile prefix, and the worst-case probe hook. It was used for both the batch-10 and the batch-11 target sets.
- `mk_targets_b10.py` is copied from batch 10 unchanged. `mk_targets_b11.py` is copied from batch 11 with the port changed to 5180.
- `capture-portfolio.mjs` (W3-03 run-3, refusal-409) and `capture-financials.mjs` (W3-02 c4) are copied with CDP set to 9520.

**Producers, all unmodified and run one at a time:**
- W3-01 `serve.py`: 9741, `w301cap_test`.
- W3-03 `test_serve_portfolio.py`: 9781, `W303_DB=assetops_w3estate_portfolio_test`. Run three times: clean with `W303_ROUTER=capture`, then `W303_COLD_DRAIN=0`, then `W303_NO_CURSOR_KEY=1`.
- W3-02 `serve.py`: 9751, `w302j_test`.
- W3-02 `serve-financials.py`: 9751, `w302w_test`. Used only for the ruling-3 JSON.

**Environment.**
- Vite ran on 127.0.0.1:5180 with `--strictPort`, with `ASSETOPS_API_PORT` set per producer.
- I checked that ports 9741, 9781, 9751, 5180 and 9520 were free first.
- `var/sites` was moved to `var/sites.w3estate-aside` for the run and then restored.
- Every server was stopped by PID (6548, 30124, 30996, 19960, 2844, 9640, 30192, 6064, 21280). All my DBs were dropped `WITH (FORCE)`. I checked afterwards that none remain.

**Pairs: 128 at 1440/390.** The case sets match batch 10 (62) and batch 11 (66).

| Part | Claims passed |
| --- | --- |
| b10-positive | 164/168 |
| b10-historical (`known_at` 2026-11-02T11:04:08Z, before late-kobo) | 60/60 |
| b10-pending (+ page-two cursor) | 72/72 |
| b10-partial | 70/72 |
| w303-positive | 36/36 |
| w303-guards | 96/108 |
| w303-historical | 36/36 |
| w303-empty | 12/12 |
| w303-401 | 10/12 |
| w303-partial | 36/36 |
| w303-pending | 36/36 |
| w303-503 | 10/12 |
| w302-positive | 34/36 |
| w302-partial-week | 34/36 |
| w302-pending | 34/36 |

Every failed claim is a "same panel count" claim, on a refused, 401, 503 or W3-02-Portfolio-503 page that has 0 panels against the mock's panels. This is the same expected-by-design set as in batches 10 and 11.

Across all 128 pairs:
- 0 console errors;
- 0 pages with document horizontal overflow;
- 0 clipped text on estate screens.

**Spot checks.**
- The partial Findings page shows the Q7 cause copy for pending Kobo and the missing empty Site.
- The refused Portfolio at 390 shows "Window not valid", "Window cannot be read" and "The selected window is longer than 31 days." in one notice.
- EV Backup shows "Unknown · No configured objective" with no link.

**Link-destination checks (not counted).**
- W3-01: 9 checks, 18/18.
- W3-03: 25 checks, 50/50, covering every Portfolio matrix destination per domain, Evidence, the register bridges, and the EV `/sites/{code}/ev` Site links. The API confirms each cell `destination`, and EV BACKUP is `null`.
- Cold and EV windowed Finding links (row-local `from`/`to`/`known_at`) land on the correct Finding.
- Every destination renders its mounted domain page.
- One clipped `CODE.action-ref` UUID appears on the Site Action page (a destination, outside W3 scope).

**KOBO-001 landing (Q18 step 1).** I moved `var/sites` aside. Then `/sites/KOBO-001`, `/sites/KOBO-001/findings/{id}?revision_id=…` (from the estate Findings and Portfolio) and `/sites/KOBO-001/actions/{id}?event_id=…` all rendered (part-b10-links l05–l08, part-w303-links). No 503 occurred, so I did not need the s404 step 2.

**Refusal-409 viewer state** (separate pair: `part-w303-refusal-409/`). The `capture-portfolio.mjs` refusal-409 flow ran: limit1, page one, `/__capture/empty-site`, then a capture-only "Load more Findings" click. At both widths it gave `ESTATE_BASIS_CHANGED`, with rows, cards and matrix all at 0, no leaked text, and no overflow.

## Cap proofs (`cap-proof.txt`)

**Probe method.** `tools/probe.js` runs after each app screenshot and before the mock navigation, in the capture browser only:
- It hides a panel's real rows and appends five clones of its first row.
- The **primary** variant (the ruled proof) sets each row's variable text to 160 characters: the Financials Limit when the row has one (first sentence plus the full Limits disclosure), otherwise the row title or label.
- The **stress** variant sets the first text and every visible text of 25 or more characters to 160 characters. It is informational only.
- It also measures the closed panel, clipping and inner scroll.
- `-worstcase-probe.png` shows the stress layout.
- Batch-10 parts ran an earlier one-variant probe that equals stress, so their numbers are upper bounds.

| Panel | Cap (1440/390) | Max real (1440/390) | Worst case (1440/390) | Within cap |
| --- | --- | --- | --- | --- |
| Findings across the estate | 1000/1500 | 454/491 | 774/976 (stress) | yes |
| Cost, Risks, Opportunities lenses | 1000/1500 | 165/203 | no rows producible (Q20); same table as Findings | yes (measured) |
| Managed actions | 750/1100 | 201/219 | 624/730 (stress) | yes |
| Consequence register | 800/1200 | 389/452 | 626/726 primary (stress 938/1575) | yes |
| Objectives across the estate | 600/800 | 352/321 | 342/311 | yes |
| Where management should act first (outer, Q17) | 900/1200 | 535/587 | 784/854; 604 inner scroll, 0 clipped | yes |

In every probe there were 0 clipped elements and no document overflow, and at 390 the tables keep their horizontal scrollers.

## Deviations

1. **Probe as the cap-proof mechanism.** The producers cannot make five 160-character rows (Q20). The cap proof is therefore an in-browser DOM probe on real pages. The probe is never presented as product data and runs only after the screenshot of record. **Reviewer to accept the method.**
2. **Consequence register stress exceeds the cap** (938/1575) when every cell, including Site name, Category and Window, is 160 characters. The ruled variant (160-character Limit) is 626/726. I made no layout change. If the Architect reads "160-character rows" as every cell, this needs a cap revision or a layout ruling.
3. **Ports and DB names are hard-coded by the producers.** They match the batch-10 and batch-11 records. `capture.mjs` was used for the batch-10 cases instead of `capture-b10.mjs`; it has the same measurements plus the link dump and probe.
4. **Build points 1–6, as implemented and verified:**
   - (1) Nullable index Finding link: unprovable cold/EV rows emit `null` and show "Finding detail unavailable". The recaptured cold/EV rows carry row-local window links.
   - (2) "Window cannot be read" appears in the existing estate refusal notice only for `INVALID_WINDOW`.
   - (3) The Financials JSON is regenerated and the test updated (above).
   - (4) The matrix opens mounted routes. Cold/EV Cost and Evidence carry the latest proven Evidence window; EV Backup is unavailable.
   - (5) Plural pending copy, "their rows are held until then.".
   - (6) "The selected window is invalid." is the generic 422 fallback.
5. **Flaky `evEnergy` timeout** happened under load. It is outside this branch.

## Residual risk / for the Architect

- **Stale Objectives footnote.** `portfolioWords.ts:26` still ends "Site detail is unavailable for these cells." Q10 now links every cell except EV Backup. The copy is outside the Q15 literal set, so I left it unchanged. It needs a copy ruling (likely D3 Low).
- Populated lenses, cold/EV Actions, an EV Portfolio priority row and multi-Site pending remain Q20 capture gaps, covered by pure DTO tests.

## Register rows

I added none, because the register is read-only for this batch. No R-IDs were assigned, so there is no collision with R375+.

## User review

The owner walkthrough comes after W6, per the standing rule. Merge waits on the Reviewer's ACCEPT.

## Addendum: final frontend rerun at `26e6c49c`

- `tsc --noEmit`: exit 0.
- Full vitest: **126/126 files, 2983/2983 tests passed**.

## Fix round (review M1, closeout rulings 1-3)

Evidence: `.agent/post-W6-W3-estate-recapture/fix-round/` (parts `part-b10-positive`, `part-b10-partial`, `part-w302-fin`, `part-w303-positive`, `part-w303-partial`; `cap-table.txt`; logs). Producers unmodified (W3-01 `serve.py`, W3-02 `serve.py`, W3-03 `test_serve_portfolio.py` with `W303_ROUTER=capture`), one at a time; the `*_test` DBs I created were dropped and every server stopped by PID.

**M1.** Root cause: the other columns' percent widths sum to 77% of a 900 px table, so the first column received the remainder (about 205 px); `col:first-child` and `max-width` had no effect. Fix: the Findings `<col>` elements carry `estate-findings-col`, and at 640 px and below the table is `table-layout: fixed` at 672 px with pixel widths 152/80/64/90/84/126/76 (`estate.css`, `findingIndex.tsx`). Measured at 390 (partial and positive, `tableCols` in evidence.json): Finding 152 px, Site 80, Priority 64, Confidence 22 of 90 visible (scroller 318 px), table 672 px, document overflow 0. The lens pages share the table but have no rows to render (Q20), so only the structural test covers them. Test `M1: the Findings index table renders a colgroup...` (estateRoots.test.tsx) renders the Findings and cost-lens routes, asserts 7 `col.estate-findings-col` equal to the th count, and the CSS pixel set (152 first, sum 672). Proof: removing `className` from `findingIndex.tsx` (single file, reverted by checkout) fails that test; with it, estateRoots 12/12.

**Ruling 3.** `OBJECTIVES_FOOTNOTE` set verbatim; the Portfolio test asserts it exactly and that "Site detail is unavailable for these cells." is absent. Captured footnote text at 1440 and 390 (`objectivesFootnote` in evidence.json) is the ruled sentence.

**Ruling 1 and 2 probe.** `tools/probe.js` now sets every intended variable field of all five clones to exactly 160 characters and asserts it (`verified`, `fields160/intendedFields`). Typed columns (Value, Priority, Confidence, State, Lens) keep real text. Register: Site, Category, Window/quantity, Basis/limit (cell, with the Limits disclosure text) and Source, all five changed (`changedColumns`). Objectives (five fixed rows) is padded to five Sites, with every Site name and cell label/note set to 160 characters. Outputs are labelled `synthetic: true`.

| Panel | Cap 1440/390 | Synthetic 1440/390 | Result |
| --- | --- | --- | --- |
| Consequence register | 1050/1800 | 974/1575 (w303), 974/1407 (w302) | within; doc overflow 0, clipped 0, table scroller 800/318 at 390 |
| Objectives across the estate | 600/800 | 336/321 | within; five fixed rows stay one line in the matrix's own scroller (3872/275-328), 0 clipped |
| Where management should act first | 900/1200 | 784/854 | within; 0 clipped |
| Findings across the estate | 1000/1500 | 1686/3549 (rows 304/671 px) | EXCEEDS under the all-field reading |
| Managed actions | 750/1100 | 1655/2225 (rows 304/414 px) | EXCEEDS |
| Evidence panels (no cap ruled) | none | Recurring gaps 287/549; Capability coverage unchanged | informational |

The old probe changed only the first text, or only the Limit; its Findings 774/976 and Actions 624/730 figures were not all-field. Findings and Actions are over their caps under the strict reading, and ruling 2's improve-widths fallback was ruled for the register only. They are returned for an Architect ruling (cap, or whether ruling 1 means all fields for these tables). At 390 the M1 fixed 672 px layout makes the Findings case taller than the old 205 px layout would (3549 vs 2575). Document overflow and clipped text are 0 everywhere.

Targeted checks: estate vitest folder, `tsc --noEmit` (clean), `check-all.ps1` (see report). No full suites, no build.
