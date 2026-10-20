# W3-01 Lane A adapter contract (shared `source_provenance`)

From Lane B, branch `task/W3-01-estate-claim-action-roots` at `2951b66c` (commit-1 core `1c409a3d`, completion
`990f2113` + `2951b66c`). Authority: `.agent/W3-01-build-spec.md` "Run 1 rulings (q1)" 1-7 and review closure 2
D2/D6. Lane A edits only its own call sites (ruling 1) and calls the API below; it does not change
`evidence/public_provenance.py` (send a request to Lane B instead).

## API (`backend/assetops_backend/evidence/public_provenance.py`)

| Symbol | Use |
|---|---|
| `PublicProvenance(reads).finding_revision(t, s, finding_revision_id, selected_revision_ids=None)` | W1 Finding row/detail. Default selection `{finding_revision.id}`. Returns the **W1-compatible** dict: every existing resolver top-level field (`tenant_id, site_id, finding_revision_id, consequence_revision_id, cited_accepted_evidence_ids, power_accepted_evidence_ids`, the nine resolver keys) plus `classification, state, source_ids, evidence_ids, basis_sha256, reasons, detail`. `None` when the revision is not in the tenant/Site. |
| `.consequence_revision(t, s, consequence_revision_id, selected_revision_ids=None)` | W1 financial consequence row. Default selection `{consequence_revision.id, its finding_revision_id}`; keeps `finding_revision_state` and the fail-closed Finding conflict. W1-compatible; `None` out of scope. |
| `.cited_set(t, s, cited_ids, selected_revision_ids, *, detail=True)` | Any exact cited set (cold envelope, cold/EV rows, pending set). Six public keys (+ `detail`). |
| `.ev_selected(t, s, cited_ids, selected_revision_ids, persisted_class, *, detail=True)` | Selected EV read (ruling 4). `persisted_class` = selected `assessment_revision.result["source_provenance"]["class"]` (may be `None`). Mismatch gives UNKNOWN + `SOURCE_CLASS_MISMATCH{accepted_evidence_ids, persisted_class}` beside all resolver reasons. Empty `selected_revision_ids` skips the comparison. |
| `dual_blocks(selected_dto, pending_dto)` | Ruling 5: returns `{source_provenance, selected_source_provenance, pending_source_provenance}` to spread into the cold/EV envelope. Raises if `pending_dto["basis_sha256"]` is not null, or if both are `None` (unruled, see pending rulings). |
| `estate_projection(dto)` | Ruling 6: exactly `{classification,state,source_ids,evidence_ids,basis_sha256,reasons}` (estate rows; equivalently `detail=False`). |
| `LinkRowsReads(lambda t, s, ids: link_rows_on(c, t, s, ids))` | Reads bound to your snapshot connection `c` for `cited_set`/`ev_selected` (cold/EV services already hold a `link_rows(c, t, s, ids)` callable). Revision reads raise; use `PostgresEvidenceLedger` (or one bound to the transaction) for `finding_revision/consequence_revision`. |
| `*_selection(...)` helpers | Ruling 2 sets, sorted unique lowercase: `finding_row_selection`, `consequence_row_selection`, `cold_envelope_selection`, `cold_finding_row_selection(finding_rev, cold_episode_rev, assessment_rev)`, `cold_consequence_row_selection(cold_conseq_rev, finding_rev, cold_episode_rev, assessment_rev)`, `ev_envelope_selection(assessment_rev, session_revision_ids)`, `ev_session_row_selection`, `ev_finding_row_selection(assessment_rev, ev_session_rev, finding_rev)`. |

`basis_sha256` is only the selection digest; `null` only when no selected revision. Empty citations with a selection
give a digest (UNKNOWN / `EMPTY_CITATION_SET`).

## Call sites (Lane A, ruling 1) and what each passes

1. `analytics/finding_read.py:FindingReadService.source_provenance` (+ its 313/447/559 consumers): replace the
   resolver call with `PublicProvenance(reads).finding_revision(t, s, finding_revision_id)` (default selection).
2. `financials/consequence_read.py`, `financials/consequence_history.py`: `.consequence_revision(t, s, cid)`
   (default selection). Consequence DTO stays separate from its Finding's DTO.
3. `site_overview/read.py`, `actions/service.py`, `finding_api.py`: wherever they surface a Finding/consequence
   provenance, use the same W1-compatible results as 1/2 (no new shape). Where an Action row DTO is required by the
   spec, closure-2 D3's set goes through `cited_set(t, s, <D3 cited union>, <D3 selected set>)`; Lane B adds no
   Action-specific adapter.
4. Cold envelope `analytics/adapters/postgres_assessment_store.py:ColdReadService._envelope` and
   `analytics/cold_site_reads.py`: `selected = cited_set(t, s, union(x.evidence_ids for chosen),
   cold_envelope_selection(x.revision_id for chosen))` on `LinkRowsReads` over the snapshot connection; then
   `**dual_blocks(selected or None, pending)`, `pending = cited_set(t, s, <newer accepted set>, [])` only on a
   pending read. Cold Finding row: `finding_revision(t, s, finding_rev, cold_finding_row_selection(...))`. Cold
   consequence row (`financials/cold_consequence.py`): `cited_set(t, s, <consequence inputs ∪ pinned Finding
   citations>, cold_consequence_row_selection(...))`.
5. EV envelope `EvReadService._envelope`: `selected = ev_selected(t, s, sel["evidence_ids"],
   ev_envelope_selection(sel["revision_id"], sel["result"]["session_revision_ids"]),
   sel["result"].get("source_provenance", {}).get("class"))`; pending as in 4 with the window's full newer
   accepted EV set; spread `dual_blocks`. Session row: `ev_session_row_selection`; Finding row:
   `ev_finding_row_selection` with `finding_revision(...)`. Never overwrite the stored result.
6. Cursor fence (ruling 3): read the fence from the private selected basis (`ColdSelected.basis` / the existing
   two-analytic combination; EV `snap["selected"]["basis"]` + route prefix, or none) instead of
   `body["source_provenance"]["basis_sha256"]` at `cold_site_reads.py:505`,
   `postgres_assessment_store.py:1864,2327,2333,2366-2367`. Payload format and 409 behaviour unchanged. Add the
   same-selection and changed-basis cursor tests to the cold/EV selected-read suites.
7. `frontend/src/sites/sourceProvenance.tsx`: read `classification` (= `state`), `source_ids`, `evidence_ids`,
   `basis_sha256`, `reasons`; on cold/EV also `selected_source_provenance`/`pending_source_provenance`.

## Tests Lane A owns in its commit
Existing-reader tests at those call sites, the ruling-3 cursor tests, `test_pending_envelope_does_not_relabel_selected_row`
and `test_source_state_compatibility_all_w1_consumers`. Lane B then adds ruling 7's
`test_w1_cold_ev_exact_cited_id_mapping` against the integrated public reads.

## Lane B evidence at `2951b66c`
`pytest backend/tests/test_w301_provenance_dto_postgres.py` 4 passed on private `w301b_test` (dropped).
Mutations (reverted via `git checkout`): no UNKNOWN override in `ev_selected` -> FAIL; consequence default
selection without its Finding revision -> FAIL; `dual_blocks` alias to selected -> FAIL.
`tools/check-architecture.ps1` passed. Open: `.agent/W3-01-pending-rulings.md` (q2) items 1-2.
