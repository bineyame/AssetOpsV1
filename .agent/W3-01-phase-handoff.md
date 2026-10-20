# W3-01 phase handoff (commit 1 partial, 2026-10-20)

Branch `task/W3-01-estate-claim-action-roots` (worktree `AssetOpsV1-review2`, from `d30fdc90`). Build commit `1c409a3d`. **Stopped on rulings**: `.agent/W3-01-pending-rulings.md` (7 items). No migration, no Alembic head, no shared (Lane A) file touched.

## Landed
- `backend/assetops_backend/evidence/public_provenance.py`: `basis_sha256(...)` (selection digest), `canonical_reasons`, `source_ids_of(LinkRow)`, `public_dto(result, tenant_id, site_id, selected_revision_ids, source_ids, detail=True)`, `w1_compatible(resolver_result, dto)`, `PublicProvenance(reads).{cited_set, finding_revision, consequence_revision}` (each takes caller-supplied `selected_revision_ids`). Pure; `reads` is the `ProvenanceReads` port (pass connection-bound reads for one transaction).
- `backend/tests/test_w301_provenance_dto_postgres.py::test_empty_foreign_broken_and_mixed_precedence` (1 of the 3 named provenance tests).

## Checks (on `w301a_test`, dropped after)
- Focused: `pytest backend/tests/test_w301_provenance_dto_postgres.py` 1 passed (8.6 s).
- Mutations after commit, each reverted with `git checkout`: reversed reason sort -> FAIL; digest version string -> FAIL; dropping the `in_scope` filter in `source_ids_of` -> still PASS (redundant: the adapter's `evidence_gateway_source` is already None for out-of-scope rows; no behavioural gap, recorded honestly).
- `tools/check-architecture.ps1`: passed. Workflow guard, full suites: not run (out of scope for this run).

## Readings made (all to be confirmed by the Architect)
1. Lane B commit-1 scope is `public_provenance.py` + tests; every existing read call site and `sourceProvenance.tsx` is Lane A (ruling 1).
2. "Classification uses `SourceProvenanceResolver.resolve`" is met by calling the resolver itself through a recording proxy over the caller's reads; `source_ids` come from that same single `link_rows` call.
3. `source_ids` = `accepted_evidence.source_id` (via `LinkRow.evidence_gateway_source[1]`) of in-scope rows, lowercased; missing/foreign contribute none.
4. All resolver reason extras are preserved, including `finding_revision_state` on `CONSEQUENCE_POWER_INPUT_CONFLICT` (spec "reasons and detail preserve typed resolver evidence"); closure-2 sorts apply to the named list extras.
5. `detail` = the resolver's nine keys verbatim, with `reasons` replaced by the canonical list.
6. W1-compatible shape = resolver top-level fields kept, public keys overlaid; top-level `reasons` become the canonical order.
7. Empty `selected_revision_ids` gives `basis_sha256: null`.
8. Test vectors use a synthetic `uuid4` selected ID as digest input (domain mapping awaits ruling 2); the empty vector uses the W20 factory IDs and reproduces the spec's literal digest `ed86298a...`.

## Resume (after rulings)
1. Per rulings 2/4/5: add the EV persisted-class adapter and pending dual DTO to `public_provenance.py`; add `test_persisted_ev_class_disagreement_unknown` and `test_w1_cold_ev_exact_cited_id_mapping` (fixtures: `contract-fixtures/w2/cold/normal.json`, `contract-fixtures/w2/ev/*.json`; replay helpers `test_w202_cold_replay_postgres.py:383-445`, `test_w205b_ev_replay_postgres.py:531-893`; W1 Finding/consequence via `test_s405_resolver_postgres.py::power_site`).
2. Send Lane A the call-site patch request (ruling 1 list) and verify W1 consumers per `test_source_state_compatibility_all_w1_consumers`.
3. Then commit 2 (estate read/API) per spec.
