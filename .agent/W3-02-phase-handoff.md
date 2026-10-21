# W3-02 phase handoff

## Commit 3 (Lane B c2d + c3 finish) - c2d and c3-q2 done; c3-q1 fixture HELD at c3-q3 (N3 still bars commit 3)

Merge of main (`.agent` W3-02 handoff/rulings kept ours). Commits `f9ef4034` (c2d), `181f62c6` (c3-q2), `fefa5ab4` (c3-q1). Branch released.

- c2d: `frontend/src/estate/estateEvidenceWords.ts` `ROLE_WORDS` gains the 9 EV missing roles + 8 EV binding roles (literal);
  `CLAIM_WORDS` six distinct cold labels. Tests `estateEvidence.test.tsx` "W3-02 c2d Evidence words" (2) + updated record-details
  line (`Power transfer position — Limited...`). c2d names no backend mapping; none changed.
- c3-q2: (5) W1 fingerprint unit `PRICE_UNIT` (`currency/L`) in `estate/financials.py:mini_grid_lines`; Lane B already joins
  `sel["limitations"]` with `; ` - **Lane A still owes `limitations` on `ConsequenceReadService.select_consequence_on`** (until then
  the persisted W1 `limit` is null). (6) `windowed_lines` returns the pinned EV windows' session revision IDs (adapter
  `ev_money` adds them from `pin["selected"]["result"]`), merged into Financials `selected_assessment_revision_ids`.
  (3) overlap test asserts group BASIS_NOT_PROVEN vs OVERLAPPING_BASIS and a withheld line never CONFLICT. (1,2,4,7) confirmed as built.
  New pure tests `test_w302_money_w1_price_unit_limit_and_citation_union`, `test_w302_money_ev_session_only_change_moves_token_and_fences`
  (head and no-head windows); both fail when their rule is reverted (reverted).
- c3-q1: `backend/tests/fixtures/w3/ev-lab-002.yaml`, `backend/conversions/ev-lab-002-bindings.json`, `install_second_ev_site` +
  `two_ev_sites` + the two ruled tests in `test_w302_money_comparability_postgres.py`; W2-05b harness parameterized
  (`ev_request(..., site_code, seed)`, `Chain.open(*, fresh, install)`, `site_code`/`seed` fields; one-Site defaults unchanged).
  STOP: EV-LAB-002 imports and publishes bindings in the same DB, then `create_draft_run` is refused (every shipped
  `config/scenarios/ev-*.yaml` names EV-LAB-001). Both two-Site tests are skipped under `blocked_c3q3`. Question c3-q3.
- Checks: backend pure money+evidence 27 passed; Postgres comparability + evidence ev/links/scope + W2-05b replay 26 passed, 2 skipped (c3-q3) in 12m25s on private `w302p_test` (dropped); estateEvidence.test.tsx 14 passed; tsc 0; check-all 11/11.
- Lane A (commit-3 confirmation): mount + no-DB 503 as before; the `select_consequence_on` `limitations` field (c3-q2(5)).
  Commit-3 review waits for c3-q3 and the persisted two-Site proof.

## Commit 3 (Lane B) - Financials read/API built; HELD at closure 2 N3 (c3-q1)

Merge of main (`.agent` W3-02 handoff/rulings kept ours); build commit `54625bdc`. Branch released.

- `backend/assetops_backend/estate/financials.py` (pure): `financials_body` (scope/fence/cursor/envelope reuse),
  `mini_grid_lines` (W1 `select_consequence_on` + `MoneyEligibility` + consequence provenance), `windowed_lines` (cold
  `money_on` both kinds, EV `money_on`; transient `STALE_BASIS` guard never a line), `decide` (Q6-Q7 order), `compare`
  (partitions, Q19 precedence, C1 coverage, NO_LINES sentinel, CONFLICT, exclusions, diagnostics), `assumption_fingerprint`.
  Estate basis alone gives HISTORICAL (c1-q1); EV `historical_label` ignored.
- `evidence_money.py`: `group_key_for_partition` (six-field amendment) and `EstateEvidenceService.financials`.
- `postgres_evidence_money_read.py`: `cold_money` (W3-01 `_cold_window` Findings -> `money_on`), `ev_money`.
- `estate_evidence_money_api.py`: `/api/estate/financials`, refusal extras `groups/exclusions/diagnostics:null`.
- Tests: `test_w302_money_api.py` (7 pure), `test_w302_money_comparability_postgres.py` (group key, unknown coverage
  over NO_LINES - pure; `test_w302_money_persisted_ev_single_site_line` - real replay/tariff/worker). 3 passed on
  private `w302o_test` (dropped); adjacent evidence/cursor/W3-01 API/EV Postgres 63 passed; check-all 11/11.
  Non-vacuous: disabling the overlap rule fails `test_w302_money_overlap_by_group_ids_and_citations` (reverted).
- STOP (N3): no second EV Site via reviewed producers (EV-LAB-001 only; fresh DB per chain). The two-Site COMPARABLE
  and different-currency persisted tests are not built. Architect question c3-q1; interpretations c3-q2.
- Lane A: `main.py` needs no change (route rides the mounted router); verify mount + no-DB 503 test
  (`.agent/W3-02-lane-a-requests.md` "Commit 3"). Review commit 3 only after c3-q1 is ruled and its fixture lands.

## Commit 2 (Lane B c2c finish) - COMMIT 2 READY FOR REVIEW

Merge of main `13392743` (`.agent/W3-02-pending-rulings.md` kept ours); build commit `93b065e8`. Branch released.

- c2-q7 (c2c): `backend/assetops_backend/estate/evidence_money.py` `COLD_OBSERVATION_WORDS` (the eight literal sentences) and `plain_limitation()`; applied to cold `current_ceiling`, `prior_selection` and disclosure `constituents[].limitation`; EV passes an empty mapping (fail closed to `Some required observations have no readable description.`). Stored limitation unchanged.
- Tests: `test_w302_evidence_scope_snapshot_postgres.py::test_w302_cold_observation_codes_map_to_plain_sentences` (8 codes, two-code, kept following sentence, unexpected/malformed/EV fallback) and `assert_plain_observations` over every wire row of the cold scope test, plus a non-empty proof (`No record of` present). Non-vacuous: disabling the mapping fails both (reverted). `estateEvidence.test.tsx::rendersTheSelectedColdBackupCeilingInPlainWords` (cell text; Record details has no `TRANSFER`/`Not observed:`).
- c2-q6: the three link-following tests in `test_w302_evidence_links_postgres.py` were already built; they pass.
- c2-q8: `frontend/src/test/settled.ts` `LOADING` gains `evidence across the estate`.
- Checks: touched backend files (snapshot, links, ev, api) 28 passed on private `w302m_test` (dropped); frontend full suite twice 96 files / 2384 tests green both runs; tsc 0; build 0; check-all 11/11.
- Capture: positive 2026-10-06 window re-taken (harness copy on `w302m_test`, vite 5299 -> 9751); 1440 backup row ceiling reads `No record of power transferring to the generator.` (viewed); 1440 cards 115/coverage 279/gaps 183/notice 43, 390 280/421/350/80, over=[]; doc scroll = client.

## Commit 2 (Lane A c2b eyebrow) - READY FOR COMMIT-2 REVIEW

Merge of main `44743fb5`; build commit `39afe950`. Branch released.

- Eyebrow (c2b): `frontend/src/ui/PageHeader.tsx` optional `eyebrow?: ReactNode`, rendered as `p.page-header__eyebrow` inside the left text column above `.page-header__title`, omitted when empty; `primitives.css` `.page-header__eyebrow` (10 px, 600, uppercase, `--text-muted`). `EstateEvidence.tsx` passes `eyebrow={EVIDENCE_EYEBROW}` (comment updated); no breadcrumb.
- Tests: `estateEvidence.test.tsx::test_evidence_eyebrow_above_title_on_estate_root` (eyebrow, then h1, then subtitle in one header; no breadcrumb); `estateRoots.test.tsx::test_five_mock_panels_and_supported_links` asserts no `.page-header__eyebrow` on Findings. Non-vacuous: dropping the prop fails the first; always rendering the node fails the second (both reverted).
- c2-q5: registry already matches c2b (`I-estate-evidence-root` area `estate-aggregation`, requires `A-estate-index-scope`,`I-capability-read`; in brief `implementation_nodes`; `P-estate-area` governs `estate-aggregation`; `globalevidence:1/:2` requires as ruled, `gap`). No change.
- Captures (private `w302l_test`, dropped; `capture.mjs` now also records the eyebrow): eyebrow `EVIDENCE` 10 px rgb(107,118,144), same header, above h1 (1440: eyebrow 24/h1 43/subtitle 84; 390: 108/127/162). positive 1440 115/279/183/43, 390 280/421/350/80; partial 1440 108/302/183/43, 390 277/445/350/80 - unchanged from Lane B, all within maxima; doc scroll = client at both widths; table scroll widths 520/330 at 390.
- Checks at `39afe950`: tsc clean; build ok; `check-all.ps1` 11/11; estate files pass alone (evidence 4/4 reruns). Full frontend 96 files / 2383 tests: 1 failure per run, different each time (`estateEvidence` line 323; then `siteFinancials` S4-08 typed 409, which passes alone 83/83) - load flakes; the Evidence one is c2-q8 (`settled.ts` misses the Evidence loading copy).
- Open: c2-q6 (Lane B link-follow proof), c2-q7, c2-q8.

## Commit 2 (Lane B fixes) - c2-q1..q4 and page defects; READY FOR COMMIT-2 REVIEW

Commits `cd98969a`, `ce75d9c4` (after merging main, `d321c76d`). Branch released.

- c2-q1: `evidence_money.py:_groups` emits `gaps[].site_names` (stored name, parallel, full group before paging); page `gapSiteNames` (empty name -> stored code), codes stay in `Record details`. Tests: `test_w302_evidence_api.py::test_w302_evidence_gap_site_names_cover_rows_on_other_pages`, `namesGapSitesFromTheWireNotThePage`.
- c2-q2: `EVIDENCE_REFUSAL_COPY` pinned to the exhaustive table (`toEqual`); unknown code -> 503 sentence (asserted with copy).
- c2-q3: new `backend/tests/test_w302_evidence_links_postgres.py` (3 ruled tests): cold/EV row links followed through `/api/sites/{code}/cold/evidence` and `/ev/evidence` with the row's exact window + cutoff (200); no-cutoff Site keeps base route + `Opens current Site view`. 3 passed on private `w302k_test`; non-vacuous (swapping from/to in `window_links` fails both follow tests with 422, reverted).
- c2-q4: `Conflicting records`; context `Not assessed`; test `showsPlainReadinessAndContextWords` (no raw state words visible).
- Defects: W3-01 `.estate-page:not(actions) .data-table {min-width:900px}` was overriding; evidence selectors now carry `[data-estate-root="evidence"]`. Capability cell is two lines (label + `Record details`, then window); compact cells; coverage list 176 px; notes on one 12 px line; headers/window wrap at <=640.
- Defect 4 (`Not observed: TRANSFER.`) is unruled: stored cold limitation text; filed as c2-q7 in pending rulings, unchanged.

Captures (Lane A harness, DB name switched to private `w302k_test` for the run, dropped; serve.py left unchanged):
positive 1440 cards 115 / coverage 279 / gaps 183 / notice 43; 390 280/421/350/80. partial 1440 108/**302**/183/43; 390 277/445/350/80. All within maxima. 1440 coverage list shows 3 rows (thead + 3 x 48 px). 390 table scroll widths: coverage 520 (mock 531), gaps 330 (mock 337). Document scroll width = client width at both widths.

Checks at `ce75d9c4`: `tsc --noEmit` clean; focused estate 2 files pass; full frontend 96 files / 2382 tests passed; `tools/check-all.ps1` 11/11; backend `test_w302_evidence_api.py` 18 passed, links Postgres 3 passed.
Open: c2-q5/q6 and the Evidence eyebrow (Architect), c2-q7 (raw role code in Current ceiling).

## Commit 2 (Lane A shell) - READY FOR REVIEW

Commits `9e05d970`, `8817543b` on `task/W3-02-estate-evidence-money-basis` (Lane A items 1-3, 5, 6 of `.agent/W3-02-lane-a-requests.md` "Commit 2"; captures item 7). Branch released.

- `frontend/src/shell/EstateRootFrames.tsx:EstateEvidenceFrame` (`<main aria-label="Evidence">`); `App.tsx` optional `estateEvidenceMoney` prop defaulted to `createEstateEvidenceMoneyClient()`; route after Actions.
- Deviation (guard-forced, by W3-01 precedent): the route uses shell `EVIDENCE_PATH="/evidence"` (`shell/operatorSiteRoutes.ts`), not `ESTATE_EVIDENCE_PATH`, because `navigation-truthfulness.ps1` resolves only `frontend/src/shell` constants; `w302EstateEvidenceShellRoute.test.tsx` pins `EVIDENCE_PATH === ESTATE_EVIDENCE_PATH`. No existing `/evidence` route shadows it; `/sites/{code}/evidence` keeps its handler (test).
- Rail `Evidence` live (`OperatorShellLayout.tsx`); `navigation-truthfulness.ps1` tuple `live|Evidence|ASSURANCE|/evidence`; four new `navigation-rail-fixtures.ps1` cases (missing route target, route removed, demoted, Financials promoted), all failing as expected inside the fixture check. Pinned rail inventories in 9 shell/ui tests updated.
- Eyebrow (item 4): estate roots render no shell breadcrumb, so no crumb was added; mock eyebrow `Evidence` remains absent (no `PageHeader` slot).
- Registry: `I-estate-evidence-root` (open, W3-02), `globalevidence:1` `Capability coverage across sites`, `:2` `Recurring evidence gaps`, status `gap`, awaiting independent review, no owner-acceptance claim; ledger row `bounded`/W3-02 with `registry_dependencies`; brief lists the node. Prerequisite choice is c2-q5 in pending rulings.
- Worksheet `.agent/W3-02-mock-measurements.md` corrected to closure-4 ceiling maxima (Aggregation 390 = 187).

Captures `.agent/W3-02-evidence/` (harness `serve.py` copied from W3-01 with the `EvidenceMoneySnapshot` read clock pinned TEST-SCOPED; private `w302j_test`, dropped; `capture.mjs`; mock `node tools/measure-mock-panels.mjs .agent/W3-02-evidence/mock globalevidence` reproduces the worksheet: 113/285/287/42 and 264/425/639/78).
- `positive` = `/evidence?from=2026-10-06T00:00:00Z&to=2026-10-07T00:00:00Z`, three Sites COMPLETE, 9 rows, 1 gap. 1440: cards 115, coverage 303, gaps 204, notice 43 (max 137/314/316/66); 390: 280/421/282/80 (max 291/468/703/102); all within. Cards 2+1 at 390. Document scroll width = client width (1440/1440, 390/390).
- `partial` = 2026-10-05..12 (KOBO UNKNOWN, 15 rows): 1440 coverage **334 > 314**; others within.

For Lane B (page defects/observations, not edited - `frontend/src/estate/` untouched):
1. Partial state at 1440: Capability panel 334 px exceeds the 314 maximum (likely the partial note plus the 200 px scroll region).
2. At 390 both table scroll widths are 900 (coverage client 318, gaps 318) against mock 531/337; min-widths are 520/330, so a cell is forcing ~900 px. It scrolls inside the panel (no page overflow), but is far wider than the mock.
3. At 1440 the 200 px coverage scroll region shows about two of nine rows; mock panel shows three rows.
4. Ceiling cell shows a raw code: `Not observed: TRANSFER.` (cold Backup response row).

Checks on `8817543b`: focused shell + estate 57 files pass; `tsc --noEmit` clean; `npm run build` ok; registry checker valid (242 nodes, 18 pilot panels); `tools/check-architecture.ps1` passed; `tools/check-all.ps1` 11/11. Full frontend 96 files / 2380 tests passed (an earlier run at `9e05d970` had the 2 `sharedVisualVocabulary` rail pins, fixed in `8817543b`, and one load-flaky `siteFinancials` 409-reload test that passes alone).

## Commit 2 (Lane B) - Evidence page landed; READY FOR LANE A SHELL

Commit `d9f898e7` (after merging main into `33b9711e`). Branch released to Lane A.

What landed (build spec: mock ledger 72-104, states 105-119, closure 1 "Mock copy..." 183-194, closure 2 Q27, closure 4 wire/links 398-407, closure 5 S13):
- `frontend/src/estate/estateEvidenceMoneyClient.ts`: typed `estate-evidence-1` envelope/rows/gaps, `EMPTY_SCOPE`/`EMPTY` unions, `EVIDENCE_REFUSAL_COPY` (W3-02 state-table copy), `createEstateEvidenceMoneyClient` (`GET /api/estate/evidence`); the W3-01 `EstateClient` is unchanged. Commit 4 adds Financials here.
- `frontend/src/estate/EstateEvidence.tsx`: `EstateEvidencePage`, `ESTATE_EVIDENCE_PATH="/evidence"`. Header `Portfolio evidence` + subtitle; shared `EstateDateBar`; three neutral (`muted`) cards with the ruled values/notes; panel `Capability coverage across sites` (mock subtitle, 5 columns, server `links.site_readiness` + `Opens current Site view`, readiness chips with page-local `estate-tone--*`, context chip, `No current ceiling`/`Not recorded`, closed `Record details` disclosure); panel `Recurring evidence gaps` (4 columns, Unlocks dictionary, `{next_step} · Not available yet` via `UnavailableInline`, `Next step not recorded`, inert `Example destinations` via `UnavailableLinkEntry`); blue mock notice. Empty-scope, no-selection, partial and historical notes sit outside the tables with headers kept. Refusals clear rows.
- `frontend/src/estate/estateEvidence.css`: tones, bounded internal table scroll (coverage 200/300 px, gaps 180/420 px at 1440/<=640), table min-widths 520/330 px.
- `frontend/src/estate/__tests__/estateEvidence.test.tsx`: `rendersMockEvidencePanelsAndHonestCards` (with `expectV69Panels` + planted-panel rejection), `rendersGroupedCapabilitiesAndTypedGaps`, `keepsInertMockActions`, `rendersEvidenceEmptyPendingAndRefusals`, `preservesSupportedSiteLinksAndCurrentViewLabel`, `readsTheEvidenceWireAndMapsRefusals`.

Checks at `d9f898e7`: focused 6/6; `tsc --noEmit` clean; full frontend 95 files / 2379 tests passed; `tools/check-all.ps1` 11/11.
Not run: 1440/390 captures (blocked: no shell route until Lane A mounts `/evidence`); layout claims unverified.

Next (Lane A, `.agent/W3-02-lane-a-requests.md` "Commit 2"): frame, App prop/route, live rail entry, registry `I-estate-evidence-root` paths, worksheet correction, captures; then independent commit-2 review. Open: `.agent/W3-02-pending-rulings.md` c2-q1..q4 (gap Site names, refusal copy for unnamed codes, B5 route-read follow tests, row context words).

## Commit 1 - READY FOR COMBINED REVIEW (Lane B c1 follow-ups landed)

`9efa3914` applies the c1 rulings (build spec "Commit-1 rulings (c1)") on top of Lane A's `cb39fdc9`. Lane B files only.
- c1-q2: `EvidenceMoneySnapshot.ev_capabilities` uses the public `capabilities_on` `unknown_meter`; the private `_sessions(_pinned_ctx(...))` call is gone.
- c1-q7: the adapter's `claim_limit_on` passes the estate `page_one_mode` (`snap.basis_historical`) as `basis_mode`.
- c1-q1: the W1 day is labelled `Historical as of {estate known_at}` from the estate basis (cold/EV already were).
- c1-q3(5): EV token `selected_assessment_revision_ids` adds the pinned selected session revision IDs.
- Tests: pure `test_w302_evidence_meter_gap_and_frozen_basis_mode`, W1 historical-label and session-only 409 asserts; Postgres `test_w302_evidence_ev_meter_gap_from_unknown_meter_seconds` (`missing-meter` replay).
- Checks: `test_w301_estate_*` + `test_w302_*` on private `w302h_test` (dropped): 119 passed, 0 skipped, 16m38s. `check-all` 11/11. No full suite.
- No new pending rulings. Branch released.

### Earlier: commit 1 (Lane B) - Evidence read/API, before the c1 rulings

Commits `8d1e6325` (code + pure tests) and `c9e19695` (Postgres proofs) on `task/W3-02-estate-evidence-money-basis`, after `git merge main`. Lane A files were not touched. The branch is released to Lane A for the mount (exact diff in `.agent/W3-02-lane-a-requests.md`).

What landed:
- `estate/evidence_money.py`: `EstateEvidenceService(EstateIndexService)` reuses the shared `_scope/_fence/_cursor/_envelope/_read`, `site_coverage`, `selection_token` and `resume_after`.
  - W1: one `GENERATOR_SUPPORT@day` row per intersecting day from `claim_limit_on` + `reduce_day`.
  - Cold/EV: four grouped rows per pinned window from `capabilities_on`. A Site with no selected window gets four unsuffixed placeholders.
  - Also: typed gap groups, B5 row-local links, `EMPTY_SCOPE`/`EMPTY`, and the 3-part cursor.
- `estate/adapters/postgres_evidence_money_read.py`: `PostgresEvidenceMoneyRead` and `EvidenceMoneySnapshot`, subclasses that keep the one REPEATABLE READ transaction and add `claim_limit_on`, `pinned_windows`, `cold_capabilities` and `ev_capabilities`.
- `estate_evidence_money_api.py`: `build_estate_evidence_money_router`. Every refusal includes `gaps:null` inside `detail` (401 and 503 too).
- Tests:
  - `test_w302_evidence_api.py` (5, pure), including the literal empty-scope vector and `/2` token `5944cb...`.
  - `test_w302_evidence_scope_snapshot_postgres.py` (2: cold scope/windows/citations/cursor/409/foreign, and W1 two days plus historical, with the store's own transaction trapped).
  - `test_w302_evidence_ev_postgres.py` (1: EV rows, links, gaps).

Checks, on the private DB `w302f_test` (dropped afterwards):
- The 3 new files plus `test_w301_estate_api`, `test_w302_estate_cursor`, `test_w302_w1_day_reduction`, `test_w302_pinned_facades` and `test_w301_estate_coverage`: 73 passed, 0 skipped, 54s.
- Mutations, both reverted:
  - Rows cite all window evidence: the pure test failed.
  - The link `from` is shifted off the row window: the cold and EV Postgres tests failed (2 failed).
- `check-all`: 11/11. No full suite.

Pending rulings: `.agent/W3-02-pending-rulings.md`.
- c1-q1: the EV `historical_label` is set only when the snapshot state is HISTORICAL, which differs from "explicit earlier cutoff". This matters for commit 3.
- c1-q2: `unknown_meter` is not exposed by the EV facade; there is an interim private `_sessions` call.
- c1-q3: readings applied where the spec is silent.

Next: Lane A mounts the router in `main.py` (with the composition builder), then the combined phase-1 review. Then commit 2 (Lane B).

## 0c (Lane A) - READY FOR REVIEW

Commit `750ce929` on `task/W3-02-estate-evidence-money-basis` (`git merge main` was already up to date at `724c0832`).
0a/0b files untouched. Branch released. Spec: closure 4, "W1 day source, cold/EV windows and pinned facades",
third and fourth paragraphs, plus the `0c` row of the per-commit index.

What landed:
- `analytics/cold_site_reads.py`: `ColdSiteReadService.capabilities_on(c,pinned_snap)` and
  `money_on(c,pinned_snap,selected_findings)`, with the helpers `_pinned` (the proof check) and `_pinned_ids`.
  `_money` gains an optional `cutoff`, and the default `None` keeps W2 unchanged.
- `ev_site_reads.py`: `EvSiteReads.capabilities_on(c,pinned_snap)` and `money_on(c,pinned_snap)`, with the helpers
  `_pinned_ctx` (built without `_ctx`/`open_on`) and `_pinned_ids`. `_select` gains an optional `cutoff`, and the
  default `None` keeps W2 unchanged.
- `financials/consequence_read.py:select_consequence_on` adds `window_start/window_end` (ISO),
  `quantity_low/quantity_high` (Decimal text), `quantity_unit` and `overlap_group` from the selected head. They are
  null without a head. The old keys and the cutoff semantics are unchanged.
- `estate/adapters/postgres_estate_read.py`: `imported_sites` items add `site_code_key`.
  `PostgresEstateRead.__init__` takes optional `cold_site`, `ev_site` and `ev_money`.
- `estate/composition.py`: wires `ColdSiteReadService(cold, cold consequence store)`, `EvSiteReads(ev, ev_money)` and
  `ev_money` onto the same owner, sharing its cold/EV read services. `financials/composition.py` has a new
  `build_ev_money_reads(link_rows)`, because the architecture guard bans adapter imports outside the financials
  composition.
- Tests: `tests/test_w302_pinned_facades.py` (16, pure) covers unprovable pins (cold 7 cases, EV 7 cases) refused
  as typed errors, a head newer than the cutoff refused, later history/work dropped, `STALE_BASIS` kept as a guard
  with `revision_id:null`, and the default paths unchanged. `tests/test_w302_pinned_facades_postgres.py` (3) shows
  that cold and EV facades equal the W2 Site `_capabilities`/money for the same exact window. `_ctx`, `open_on`,
  `_selected`, `within` and the routes are monkeypatched to fail. The EV case uses a stored, priced head from the
  W2-07 golden tariff. It also checks that the W1 head fields equal the stored immutable row for revisions 1 and 2,
  and are null when PENDING.

Checks: on the private DB `w302c_test` I ran the touched tests plus `test_s4_consequence_read`,
`test_w204_cold_consequence`, `test_w204_cold_reads`, `test_w207_ev_money`, `test_w207_ev_money_postgres`,
`test_w207_ev_site_reads_postgres`, the `test_w301_{cold,ev}_selection_on_postgres` pair,
`test_w301_w1_money_snapshot_helpers_postgres` and every `test_w301_estate_*`/`test_w302_estate_cursor` file:
191 passed, 0 skipped, 30m51s (JUnit 191/0/0/0). That run's code was revision `5c241fa5`. The amend to `750ce929`
only moved the `EvMoneyReads` construction into `build_ev_money_reads`, and I re-ran
`test_w301_estate_index_postgres` + the pure facades on it: 36 passed, 0 skipped, 7m03s. The DB was dropped afterwards.
`check-all`: 11/11 guards passed. No full suite run.

Readings (I am recording these, not making rulings):
1. A pin counts as "provable" when the snapshot carries `selection_cutoff` and `selection_seqs`, the seqs name
   exactly the selected analytics (cold) or the one session analytic (EV), it has an exact `lo/hi`, and its
   row-local `known <= selection_cutoff` and `known <= watermark`. A failure raises `ColdPinnedLineageUnavailable`/
   `EvPinnedLineageUnavailable`, which composition already maps to `EstateSelectionInconsistent` (409). I did not
   return an in-band unavailable value.
2. "Never pick a newer head": a selected cold head (`cold_heads_on` latest per Finding revision/kind) or an EV
   current head (`select_on`) recorded after `selection_cutoff` (the estate `k`) is refused (409). It is not
   replaced by an older revision. This fails closed, and a historical estate read after a later recompute
   therefore refuses. If an older-head fallback is wanted, that needs a ruling.
3. Under the pin, cold work enqueued after the cutoff does not withhold, and EV history recorded after the cutoff
   is dropped.
4. Cold `money_on` returns every selected head of both kinds (`PRODUCT_EXPOSURE` and `RECORDED_REPAIR`), each with
   `counted` (the W2 latest-per-overlap-group exposure), `finding_revision_id` and its window. `selected_findings`
   items may carry `revision_id` or `finding_revision_id`.
5. EV `money_on` returns `consequence` (the W2 `_consequence` DTO), `history` (labelled), `guard` and `state`. The
   per-row `source_provenance` is not included. Lane B calls `money_row_provenance_on` if it needs it.
6. I did not rename `cited.power_evidence_ids` to `technical_interval_ids`. That is the commit 3 wire; the docstring
   records the mapping.

Next: commit 1 (Lane B), after 0a-0c review.

## 0b (Lane A) - READY FOR REVIEW

Commit `d208faef` on `task/W3-02-estate-evidence-money-basis` (after merging main into `2d36689a`). 0a files
untouched. Branch released. Spec: Review closure 4, "W1 day source, cold/EV windows and pinned facades", first
paragraph only.

What landed:
- `analytics/claim_limit_read.py`: `ClaimLimitReadService.claim_limit_on(c,tenant_id,site_id,day,revision_id,
  known_at)` (never `read()`/`claim_limit_snapshot()`); module `interval_state`, `reduce_day`, `GAP_CODES`,
  `HISTORICAL_SELECTION_UNAVAILABLE`, state constants. Protocol `ClaimLimitStore` gains `claim_limit_snapshot_on`.
- `analytics/adapters/postgres_assessment_store.py`: one new method `claim_limit_snapshot_on`, placed directly after
  `_revision_detail`; it composes `select_dispatch_days_on` (one day) and `_revision_detail`. No existing function
  changed (W4-02 merge surface untouched).
- Tests: `tests/test_w302_w1_day_reduction.py` (5, pure: precedence, zero intervals, single-ceiling agreement,
  role-tagged gaps vs role-less window reasons, unavailable). `tests/test_w302_w1_claim_limit_on_postgres.py` (3:
  F02 two days; F06 cutoff with disagreeing FULL/LIMITED intervals, gaps, later CONTRADICTORY selection, later
  revision/acceptance excluded, earlier selection as HISTORICAL; DONE-without-selection unavailable history). The
  store `_snapshot` is monkeypatched to raise, so any second transaction fails the test.

Checks: those 2 files + `test_w301_w1_snapshot_helpers_postgres`, `test_s3_claim_limit_postgres`,
`test_s3_claim_limit_vocabulary`, `test_s3_dispatch_read_postgres`, `test_s3_dispatch_assessment_postgres`,
`test_s3_dispatch_v3_analytic` on private DB `w302b_test`: 77 passed, 0 skipped, 1m43s; DB dropped. `check-all`:
11/11 guards passed. No full suite run. The `_snapshot` trap was not separately mutation-proven.

Readings (recorded, not rulings):
1. `revision_id` is the day's window revision (all INTERVAL revisions of its run are projected) or one INTERVAL
   revision (that one only). Lane B calls it with `window_assessment_revision_id`.
2. Interval state: a role-tagged `CONFLICTING` reason gives CONTRADICTORY (even when not CURRENT); otherwise any
   non-CURRENT currentness (PENDING/FAILED/STALE_PROJECTION/UNASSESSED/HISTORICAL) gives UNKNOWN; else support
   COMPLETE/NONE/LIMITED -> FULL/NONE/LIMITED.
3. A revision not in the day's selection at `known_at` is HISTORICAL (IDs, `historical_ceiling` kept, no current
   claim), not refused. Day unavailable, revision/interval/run recorded after the cutoff, or cited Evidence accepted
   after it -> `available=False` + `HISTORICAL_SELECTION_UNAVAILABLE`. Unknown revision 404, other window 422,
   unsupported model 422 and absent lineage 409 are raised as `read()` does; the estate caller maps them to UNKNOWN.
4. Interval reasons exclude window limitations; role-less window reasons are returned separately as
   `window_reasons` and never become gaps. Gaps carry `domain="dispatch"` (the W1 DOMAIN constant).
5. The W1 `_reasons` maps NOT_EVALUATED spans to `GENERATOR_UNOBSERVED` with the span's role, so F06 yields
   `GENERATOR_UNOBSERVED` gaps for non-generator roles; kept as the reused W1 vocabulary.
6. The row key `GENERATOR_SUPPORT@YYYY-MM-DD` and placeholders are left to commit 1.

Next: `0c` (Lane A, pinned facades), after 0b review.

## 0a (Lane A) - READY FOR REVIEW

Commit `7a4d06ef` on `task/W3-02-estate-evidence-money-basis` (base main `c50ea24b`). Branch released.

What landed (the spec is Review closure 4, "Shared parser, 3- and 5-part cursor, refusals (B1, S7-S8)"):
- `backend/assetops_backend/estate/scope.py`: `KEYS` gains `evidence` and `financials`, both
  `from,to,known_at,limit,cursor`. `parse_request` and `decode_cursor` refuse an unsupported kind with
  `EstateRefusal("INVALID_CURSOR")` (422). New cursors use the Action key set, with `kind` equal to the root.
  `_marker_ok` validates the 3-part Evidence marker and the 5-part Financials marker (null-first). `cursor_after` is
  kind-aware. New helpers: `cursor_marker(kind, after)`, the wire inverse, and `resume_after(markers, after)`, which
  raises 422 for an absent marker and is called only after the fence.
- `backend/assetops_backend/estate/index.py`: `_fence` returns `cursor_after(cursor)`, so it handles any kind.
  `_cursor(tenant_id, req, scope, token, *after)` keeps the old `(at, row_id)` call sites. `kind` comes from
  `req.kind`. The Finding/Action bytes are unchanged, and a test pins them.
- `backend/tests/test_w302_estate_cursor.py`: 31 tests. They cover parser kinds and the typed unknown-kind refusal,
  both marker arities, null-first money, 20 malformed cases (missing `page_one_mode`, wrong kind, unknown or extra
  keys, arity, non-UUID, empty string, non-canonical instant), kinds not crossing, old bytes unchanged, changed
  grant/selection/window/cutoff and the old `/1` digest giving 409, and historical page two.

Checks: the 6 estate test files on the private DB `w302a_test` gave 66 passed, 0 skipped, in 9m31s. The DB was
dropped afterwards. `tools/check-all.ps1` passed all 11 guards. I ran no full suite, as instructed.

Readings (I am recording these, not making rulings):
1. Evidence/Financials cursors also need the canonical six-digit `from/to/known_at`, matching the "canonical time"
   wording. Finding/Action cursors keep the looser W3-01 check.
2. `site_id` is the marker element at index 1 (Evidence) and index 2 (Financials). It is validated as a UUID string,
   and its case is not normalized.
3. I added `resume_after` to `scope.py` as the shared absent-marker check. Phases 1 and 3 should call it on the full
   ordered marker list, after `_fence`.
4. A changed cutoff is refused 409 inside `_scope` (W3-01 behaviour), before `_fence`.

Next: `0b` (Lane A, W1 day projection), after 0a has its independent review.
- 0b fix r1: W3-02 0b fix r1 — trap now patches _snapshot/_run/_connect_engine (mutation via _run: 4 failed, reverted); window-only revision mode (non-window 422 REVISION_NOT_WINDOW); HISTORICAL day shape/copy, conflict precedence, gap key (mini_grid, code, role) per rulings; 63 passed on w302d_test.
- 0c fix r1 (`2c46c9fd`): H1 cold heads `created_at <= K` before DISTINCT ON (`cold_heads_on(known_at=)`), EV basis from tariff assignments recorded at K + head `recorded_at <= K` (also under HISTORICAL; as-of head labelled history, `historical_label`), pinned STALE_BASIS copy `STALE_AS_OF_COPY`; M1 W2-04 drain before the comparison, ≥1 PRODUCT_EXPOSURE, ids/kind/basis/counted/withheld/hold vs W2; L1 `cold_pending_as_of_on`; L2 K+ε absent at K in pure + Postgres; L3 `ev-session/1` key + positive seq. Mutation (drop as-of bounds): both historical Postgres tests failed, reverted. 0c + w204 cold reads/consequence/worker + w207 EV money/Site reads: 118 passed, 0 skipped, 20m26s on w302e_test (dropped). check-all 11/11.
- commit-1 Lane A integration (`71c00d59`, after merging main): c1-q2 `EvSiteReads.capabilities_on` now returns
  `unknown_meter: bool` (one `_pinned_ctx`, `any(unknown_meter_seconds > 0)` over `_sessions(ctx)`;
  `ev_site_reads.py:334`). c1-q7 `ClaimLimitReadService.claim_limit_on(..., *, basis_mode=None|"live"|"historical")`
  (`analytics/claim_limit_read.py:357`, applied at `historical_day`; other values raise `ValueError`; `None` keeps
  `known_at < transaction_time`). Evidence router mounted: `build_estate_evidence_service` in
  `estate/composition.py` (exactly the requested builder) and `main.py` mount after the W3-01 estate router. No guard
  change. c1-q1 assigns no Lane A file. Tests: `test_w302_pinned_facades_postgres.py::test_ev_capabilities_on_exposes_unknown_meter_of_the_selected_sessions`
  (complete / missing-meter) and `test_w302_w1_claim_limit_on_postgres.py::test_w1_frozen_basis_mode_overrides_the_transaction_time_comparison`.
  W3-01 estate (5 files) + all `test_w302_*` + `test_w207_ev_site_reads_postgres.py`: 136 passed, 0 skipped, 19m49s on
  `w302g_test` (dropped). check-all 11/11.
  Next for Lane B: in `PostgresEvidenceMoneyRead.ev_capabilities` consume `read["unknown_meter"]` and drop the private
  `_sessions(_pinned_ctx(...))` call; pass the cursor's `page_one_mode` as `basis_mode=` to `claim_limit_on`
  (c1-q7); add the estate METER_GAP test for a selected session with positive unknown meter seconds (c1-q2), the
  c1-q1 label change in `evidence_money.py`, and the c1-q3 token replacement (5). `evidence_read` in
  `test_w302_evidence_scope_snapshot_postgres.py` may now call `build_estate_evidence_service`.

## Commit-1 fix r1

Implements "Commit-1 review r1 rulings" (build spec) against `.agent/W3-02-commit1-review.md`; no new pending rulings.
- M1: `_window_state` (`estate/evidence_money.py`): a live basis maps pin `HISTORICAL` to CURRENT; PENDING/STALE precedence kept; a missing pin stays UNKNOWN. Pure test in `test_w302_evidence_meter_gap_and_frozen_basis_mode`; Postgres `test_w302_evidence_live_cursor_later_disposition_preserves_rows_and_token` (ordinary late disposition after the cursor cutoff) plus control `..._changed_selected_id_is_409`.
- M2: `adapters/postgres_evidence_money_read.py` maps the five finite `ClaimLimitRefusal` codes to an unavailable day projection (HISTORICAL_SELECTION_UNAVAILABLE + original code); the row is UNKNOWN with no IDs. Other refusals still 409. Tests `..._w1_refusals_are_unknown_days` (5 codes), `..._w1_refusal_preserves_other_sites`.
- R1 role-specific `GENERATOR_UNOBSERVED` copy (generator_state unchanged); R2 confirmed (energy row only); L1 token cites full `read["evidence_ids"]`, claimless row cites nothing (`_token_cited`); L2 interval reasons in constituents and labelled `prior_selection` for non-current days; L3 canonical six-digit `Z` historical statements; L4 `complete` keyed on `snap.basis_historical`; L5 token session IDs asserted in the EV Postgres test, plus `test_w302_evidence_composition_mount_no_db_503`.
- Note: two live reads at different cutoffs have different tokens (k is in the token); the M1 test compares page two to page one only.

## Commit-2 fix r1 (rulings L1-L4) - READY FOR RE-REVIEW

Commit `e45f4219`. L1: `RowDetails` is a plain 6-10 field `<dl>` (`estateEvidenceWords.ts` dictionaries from the reviewed W1/cold/EV words; fallbacks `Description not available` / `Reason details are not available`; no JSON). L4: `.page-header__eyebrow` `text-transform: none` (captured `Evidence`). L2: `meetsMeasuredNarrowLayoutWithoutDocumentOverflow` reads the 390 captures (doc scroll<=client, both table scroll containers). L3: ledger `data_owner` set. New test `rendersPlainRecordDetailsWithAndWithoutPriorSelection`.
Mapping gaps for Architect: no reviewed words for EV roles/missing roles (fall back to `Description not available`); cold claims map to their row label (two claims share one label).
All four Evidence captures re-taken at head (private `w302n_test`, dropped; serve/vite stopped by port only). positive 1440 115/279/183/43, 390 280/421/350/80; partial 1440 108/302/183/43, 390 277/445/350/80; over=[]; doc 1440/1440, 390/390; eyebrow `Evidence`, transform none. Partial 1440 image viewed: no raw code, no JSON; Backup row reads the plain transfer sentence.
Checks: tsc 0, build ok, full frontend 96 files / 2386 passed, check-all 11/11. Branch released.

## Commit 3 Lane A items

Commit `1ba3306a`. c3-q2 (5): `ConsequenceReadService.select_consequence_on` (`financials/consequence_read.py`) adds `limitations` = the selected head's stored list in stored order, read from the same `selected_on` row on the caller's connection (no new transaction); null without a head, like the other 0c head fields; old keys and cutoff semantics unchanged. Test `test_w302_pinned_facades_postgres.py::test_select_consequence_on_carries_the_selected_head_limitations` (nonempty stored list equal at live and earlier cutoff, each head's own; null when no head at K); `HEAD_FIELDS` gains `limitations`. Mount verified: `/api/estate/financials` is on the already-mounted `build_estate_evidence_money_router` (`main.py:473`, no change). New `test_w302_evidence_api.py::test_w302_financials_composition_mount_no_db_503` asserts strict 503 and the exact null body. Lane B next: join `limitations` with `; ` for the W1 `limit` cell.
Checks: all `test_w302_*` + `test_w301_w1_money_snapshot_helpers_postgres.py` on `w302q_test`: 117 passed, 2 skipped (the c3-q3 comparability skips, Lane B's held proof), 12m35s; DB dropped. check-all 11/11. No new pending rulings. Branch released.

## Commit 3 Lane B c3b items - READY FOR REVIEW (comparability proof still blocked, N3 holds)

Commit `6f065647` (after merging main). Fixture `backend/tests/fixtures/w3/scenarios/ev-complete-lab-002.yaml`; `Chain.open(..., scenarios=, scenario_id=)` and `ev_request(..., scenario_id=)` (`test_w205b_ev_replay_postgres.py`), defaults unchanged; `second_scenario_repository` + drift test `test_w302_second_ev_scenario_differs_from_shipped_only_in_three_fields` (mutation failed, reverted) in `test_w302_money_comparability_postgres.py`.
Checks: all `test_w302_*` on `w302r_test`: 112 passed, 2 skipped (the two-Site tests), 9m39s; DB dropped. check-all 11/11. Branch released.
Not done: both two-Site tests keep `blocked_c3q3` - Lane A's c3b `ev_parsing.py` change is not on the branch, so the fixture is refused at parse (`site_code must be 'EV-LAB-001'`). See pending ruling c3b-q1. Next: Lane A parser item, then Lane B removes the skip and runs the two tests.
