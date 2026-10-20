# W3-01 phase handoff (commit 1, Lane B part complete, 2026-10-20)

Branch `task/W3-01-estate-claim-action-roots` (worktree `AssetOpsV1-review2`). Lane B commits: `1c409a3d` (core),
`990f2113` + `2951b66c` (completion, Run 1 rulings 2/4/5/6). **Branch released to Lane A** (ruling 1). No Lane A
call site, migration or Alembic head touched.

## Landed (`backend/assetops_backend/evidence/public_provenance.py`)
- Ruling 2 `*_selection` helpers; `finding_revision`/`consequence_revision` default to the W1 row sets.
- Ruling 4 `PublicProvenance.ev_selected(..., persisted_class)` with `SOURCE_CLASS_MISMATCH`.
- Ruling 5 `dual_blocks(selected, pending)`; ruling 6 `estate_projection`; `LinkRowsReads` for one-connection
  set reads.
- Tests (`backend/tests/test_w301_provenance_dto_postgres.py`): `test_empty_foreign_broken_and_mixed_precedence`,
  `test_persisted_ev_class_disagreement_unknown`, `test_w1_revision_selection_sets_and_estate_projection`,
  `test_pending_dual_blocks`.

## Checks (private `w301b_test`, dropped after)
- Focused file: 4 passed (22.6 s). Mutations after commit, each reverted with `git checkout`: UNKNOWN override
  removed -> FAIL; consequence default selection minus Finding revision -> FAIL; `dual_blocks` alias -> FAIL.
- `tools/check-architecture.ps1` passed. Full suites, workflow guard: not run (out of scope).

## Next
1. **Lane A** (exclusive checkout): compatibility commit per `.agent/W3-01-lane-a-adapter-contract.md`.
   Open q2 items in `.agent/W3-01-pending-rulings.md` (empty-envelope shape; cold pending set) block parts of
   its cold/EV envelope work.
2. **Lane B** after Lane A releases: `test_w1_cold_ev_exact_cited_id_mapping` (ruling 7) against the integrated
   public reads; then review of `1c409a3d..<that commit>`; then W4 cherry-pick per ruling 1.
3. Then W3 commit 2 (estate read/API) per spec.

## Lane A compatibility run (2026-10-20): stopped on rulings, no code committed
Merged main into the branch (`1f731005`, clean, Run 2 rulings present). Dry-read all ruling-1 call sites, then
stopped per the no-decision rule: `.agent/W3-01-pending-rulings.md` (q3) items 1-3 block the cold/EV envelope
work (EV no-head unassessable read vs empty DTO; detail-read top-level DTO; row DTO key and EV session cited
set); items 4-6 are readings (composition wiring via new `build_public_provenance` and a `ColdReadService`
`link_rows` kwarg; fail-closed `unresolved` blocks keep their shape; `dual_blocks(None, None)` still raises,
so Lane B's q2-ruling-1 change is a precondition). No test, DB or check-all run (no code changed).
Anchors for the resumed run: cold `_envelope` `postgres_assessment_store.py:1655`, fence reads 1864/1892,
`cold_site_reads.py:505`; EV `_snapshot` 2102, `_envelope` 2184, `_page` 2320, `page_on` 2362; W1 resolver
injection `analytics/composition.py:build_finding_read_service`, `financials/composition.py:45-63`.
**Branch released** (Lane A holds nothing). Next: Architect answers q3 and Lane B lands the `dual_blocks`
empty case; then Lane A resumes the one compatibility commit.
- Lane B q2/q3: dual_blocks(None, None) now returns the literal six-key EMPTY_CITATION_SET alias plus two null siblings (no signature change); test_pending_dual_blocks updated; 4 passed on w301d_test.

## Lane A compatibility run 2 (2026-10-20): stopped on q4, no code committed
Resumed at `9239fb45` (Lane B both-null `dual_blocks` present). Built the q3 map except EV money, then stopped:
`.agent/W3-01-pending-rulings.md` q4 item 1 (EV money rows have `finding_revision_id` always NULL, so the
literal q3 refusal would 503 every stored EV money read); items 2-6 are readings built into the patch.
Partial diff (uncommitted code, reverted from the tree): `.agent/W3-01-lane-a-partial.patch`
(`git apply` on this branch). It covers: `evidence/composition.py:build_public_provenance`; W1 injection in
`analytics/composition.py` (+ `build_cold_read_service` `link_rows`) and `financials/composition.py`; cold
`ColdReadService` (`_public`, `selected_basis`, `_pending_ids`, `_provenance_blocks`, `_envelope(c, ...)`,
`envelope_on(c, ...)`, row DTO in `_item`, detail override, `consequence_provenance_on`); `cold_site_reads.py`
(`envelope_on(c, ...)`, private cursor basis, `consequences[].source_provenance`); EV (`job` flag in
`_snapshot`, `_provenance_blocks`, `_envelope`, session union row DTO, Finding row DTO, `_page(basis)`,
`page_on` route|basis). Imports verified; no test, DB or check-all run yet.
Not yet done: EV money row blocks (`ev_site_reads.py`, `EvMoneyReads._with_links`) pending q4; all q3 test
changes; `frontend/src/sites/sourceProvenance.tsx` + its tests. **Branch released** (Lane A holds nothing).

## Lane A compatibility commit (2026-10-20): landed, branch released to Lane B
Merged main (q4 rulings + selection token v2 present), applied `.agent/W3-01-lane-a-partial.patch`, finished the q3
map with the q4 corrections. One commit (`W3-01 Lane A: compatibility integration`). Lane B files untouched.
- EV money (q4 ruling 1): `EvReadService.money_row_provenance_on` (`postgres_assessment_store.py`, after
  `_provenance_blocks`) selects `{row id, stored assessment, every ev_consequence_session revision}`, cites only
  `ev_consequence_evidence`; NULL Finding pin expected; non-null pin, missing assessment or a linked session not in
  the tenant/Site naming that assessment -> `EvReadUnavailable`. `ev_site_reads.py:financials` adds it to the current
  stored row and every history row; guard rows get none. `_EV_REVISION_SQL` also selects `r.finding_revision_id`.
- Frontend: `sourceProvenance.tsx` (optional public keys, `classification ?? state`, `detail` first, safe empties,
  `SOURCE_CLASS_MISMATCH` copy); cold/EV client types gain the two siblings (`ColdSourceBlock`, `EvSourceBlock`).
- Tests: W1 compat `test_s4_power_demo_case_postgres.py::test_source_state_compatibility_all_w1_consumers`; q3/q4
  edits in w203, w204, w206 (incl. `test_session_row_cites_meter_interval_outside_session_evidence`), w207 site,
  w207 money (`test_ev_money_row_provenance_uses_stored_window_links_without_finding_pin`), S4 Finding read /
  evidence history / Finding API, S4 consequence history, S5 overview, S6 action records; frontend
  `sourceProvenance`, `coldRoutes`, `evAssessmentRoutes`.
Readings (none blocking; confirm at review):
1. q4 EV money set is inlined (sorted distinct) and passed to `cited_set`; no Lane B helper added.
2. EV money integrity failures tested by direct `money_row_provenance_on` calls on the real DB (FKs prevent
   storing an inconsistent row); the public path covers present/history/zero-link/page-size.
3. Cold overview's Finding projection (`cold_site_reads.overview.findings.items`) is unchanged; the rows it
   consumes (`current_findings_on` -> `_item`) carry `source_provenance`, as do `/cold/findings` items.
4. Public reasons keep resolver extras, so w206 `_reasons` now requires `{code, accepted_evidence_ids}` as a subset.
5. Test-only DB edits: w206 marks open EV jobs DONE then restores them (no-job vector), inserts one EXCLUDED
   `ev_meter_interval` row (meter vector); w203 inserts then retires (DONE) a cold job (rows are never deleted).
6. S6 harness keeps `build_source_provenance`; the S6 test checks the production `build_finding_read_service`
   block for the same origin revision instead (golden contract bodies unchanged).
7. Open copy item: EV Finding detail "Assessment basis (SHA-256)" (`EvAssessmentViews.tsx:673`, and :324 for the
   envelope) now shows the public row/envelope digest, not the stored assessment basis; label left unchanged.
Checks (private `w301e_test`, dropped): final w203+w204+w206 44 passed; w207 site+money 32 passed; S4 Finding read,
power demo, consequence history, S5 overview 20 passed; evidence history + consequence read 8 passed; S6 1 passed;
Finding API 17 passed. Frontend: typecheck clean; 9 files 344 passed. check-all: 9/10, the one FAIL is pre-existing
on main (`Evidence width check`: `tools/measure-mock-panels.mjs` from main `29dea85f`, untouched here).
**Next:** Lane B `test_w1_cold_ev_exact_cited_id_mapping` (use the q4 EV money set), then commit-1 review.

## Lane B ruling-7 test (2026-10-20): landed; commit-1 unit ready for review
Merged main (`96b86c83`, clean). `6823d7d0` adds `test_w301_provenance_dto_postgres.py::test_w1_cold_ev_exact_cited_id_mapping`
(params `w1`, `cold`, `ev`). Each digest is recomputed by the file's own `digest()` from scoped DB sets; page size 1
(all cursors) vs 200 gives identical row and envelope blocks. W1: `power_site` + P01, consequence read, Finding read,
history at limit 25 vs 1. Cold: findings envelope, Finding rows/detail, `financials.consequences[]`. EV: all six
replays, sessions/findings rows + detail, envelope, q4 money set on the UNPRICED and priced stored rows.
Readings (none blocking; confirm at review):
- L-B1: cold uses `normal` (named) plus `excursion`, which adds the Finding and consequence rows so the row
  mapping is proven on non-empty sets (the test asserts it saw at least one of each).
- L-B2: the contract fixtures are pinned replay manifests rather than input data. The test builds each case through the
  same W2 replay `Chain`, using an inline copy of the `chain` fixture body, because both modules name their
  fixture `chain`.
- L-B3: W1 is read through the public service layer, as `test_source_state_compatibility_all_w1_consumers` does.
  The test makes no HTTP call for W1. Cold/EV selected IDs come from the public read (watermark
  `assessment_revision_ids`, item `revision_id`s); pins and cited sets come from the DB.
Checks: whole file 7 passed (264 s) on private `w301f_test`, which was dropped afterwards. Mutation after commit: dropping the cold
episode revision and the EV money session links from the expected selection made cold and ev FAIL on
`basis_sha256`. Reverted with `git checkout`. check-all: 10/10 passed.
**Next:** review `1c409a3d..HEAD` as the W3 commit-1 unit, then the W4 cherry-pick per ruling 1.

## Fix round r1 (commit-1 review rulings M1, M2, M3.1, M3.2, L1-L5)
| Finding | Fix | Test |
| --- | --- | --- |
| M1 digest copy | Cold claim refs and EV sessions refs read `selected_source_provenance` (`Selected source basis (SHA-256)`, `Not recorded` when null); EV Finding detail `Finding source basis (SHA-256)` on the row block | `coldRoutes::selected_source_basis_survives_pending`; `evAssessmentRoutes::selected_and_finding_source_basis_survive_pending` |
| M2 source owner | `selectedSourceBlock`/`selectedClassification` (`sourceProvenance.tsx`) used by cold claim facts, cold Site record/claim-rule rows, EV strip badge, EV Site claim line, financials line, assumptions badge; pending class shown only as `Current accepted evidence source`; EV Evidence Analysis record line and sessions `SourceReasons`/`sourceDetail` labelled current-set; backend `claim_rules[].source_class` from the selected block (`ev_site_reads.py`) | `coldRoutes::pending_source_does_not_relabel_cold_claim_or_site_rows` (+ `coldSiteViews.test` row case); `evAssessmentRoutes::pending_source_does_not_relabel_ev_selected_badges_or_rows`; `evSiteMoneyRoutes::selected_claim_rules_and_money_lines_ignore_pending_class`, `::current_accepted_record_line_names_pending_class`; `test_w207_ev_site_reads_postgres::test_claim_rules_source_class_is_selected_not_pending` (fails with the old line) |
| M3.1 withdrawn, dropped session | `_findings` selects `fr.transition`; lifecycle and transition NO_LONGER_SUPPORTED with a stored session id and zero matches use `ev_withdrawn_finding_row_selection` (two IDs); every other missing/duplicate session still refuses | `test_w206_ev_reads_postgres::test_withdrawn_finding_dropped_session_detail_has_two_id_provenance` (real second loop via rebind START + `select_exact`; SUPPORTED-with-missing-session 503 inside) |
| M3.2 historical cutoff | cold `pending_since` and EV `job` queried only when `not historical and known is not None`, plus `created_at <= :k` | `test_w203::test_historical_cutoff_precedes_pending_job`; `test_w206::test_historical_cutoff_precedes_pending_job` (extended existing test) |
| L1 | test only | `test_w206::test_public_selected_ev_class_mismatch_unknown` |
| L2, L5 | accepted as backlog, no change | none |
| L3 | named test maps to `test_w203::test_pending_historical_reload` plus the M2 tests above | none |
| L4 | `.agent/W3-01-lane-a-partial.patch` removed | none |
Readings to confirm: (1) M3.2 `:k` is the explicit `known_at` only (NULL on default reads): a default read has `known` = watermark and a job's `created_at` is after it, so `:k = known` would hide every real pending job (`test_w203::test_typed_errors_and_unknown_200` fails). (2) EV historical test name already existed; extended, not duplicated. (3) `evSiteRoutes.test.tsx` does not exist; the two named tests are in `evSiteMoneyRoutes.test.tsx`. (4) Test updates to `assessment_revision` use `SET LOCAL session_replication_role = replica` (append-only trigger), restored in `finally`. (5) The Finding strip falls back to the row's own block when no `selected_source_provenance` sibling exists. (6) Open copy item 7 above is now closed.
Checks (private `w301g_test`, dropped): w203 6 passed (5 full-file run + new test alone); w206 reads + w207 site reads 42 passed (1702 s); frontend cold/ev/coldSite/sourceProvenance files passed; tsc clean; check-all 10/10.
