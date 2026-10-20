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
