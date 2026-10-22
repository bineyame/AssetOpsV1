# W6-01a (unit A1) phase handoff - BLOCKED before code

Branch `task/W6-01a-global-incidents` from main 3a14f5aa. No code written; no DB created; no process started.
Stopped per dispatch rule (unspecified/contradicting code => report, do not choose).

## Blocking (A1 file list vs guards)
- Q1. `tools/checks/configuration-persistence.ps1:833` rule 8 `$pgReaders` admits a sqlalchemy import only in
  listed reader files (`:900-904`). New `work/adapters/postgres_global_read.py` needs that import, but the guard
  file is not in A1's list. Amend A1 to own a one-line `$pgReaders` addition?
- Q2. Only `work/composition.py` may import work adapters (`configuration-persistence.ps1:8`, domain at `:168-176`;
  pattern `work/composition.py:51-64`). `main.py` cannot build the global read itself. Amend A1 to own
  `backend/assetops_backend/work/composition.py` (e.g. `build_global_work_index_service`)?

## Non-blocking readings needing a ruling (batched)
- Q3. Apply `missing_lineage` to a case row whose link lacks lineage, as the Site list does (`work/site_index.py:220-221`)?
  Spec says only "`provenance_dto`" + `case_basis`.
- Q4. HISTORICAL on a cursor page that omits `known_at`: W4 labels explicit only (`site_index.py:300`), estate labels
  `k < read_at` (`estate/index.py:160`). And a page-two explicit `known_at`: W4 exact-equal rule (`site_index.py:291`)
  or estate wire-second rule (`estate/index.py:155-157`)?
- Q5. Authorized-Site candidates: reuse estate `imported_at < to` (`estate/adapters/postgres_estate_read.py:116`)?
- Q6. Read time: W4 `clock_timestamp()` + `test_read_clock_override` (`postgres_work_read.py:283-288`) needed for the
  pinned `12:00:02Z` reads, vs estate `now()` (`postgres_estate_read.py:90`). Confirm W4 form.
- Q7. Link labels for `finding_links`/`action_links` (`Link={label,href}`): reuse W4 `Finding {id[:8]}` /
  `Action {id[:8]}` (`site_index.py:177-191`)? Order of `linked_request_codes`?
- Q8. `links.site_incidents` `known_at` when the page omitted it: always the response `known_at` (example shows it)?
- Q9. Example `actor_id` `service:w601-fixture` vs §4 "inject `W401_FIXTURE_SERVICE_PRINCIPAL_ID`" = `service:w401-fixture`
  (`work_api.py:39`). Which principal does the seeder use?

## Tests
None run (no code).

Next: Architect amendment of A1 card (Q1-Q2 required; Q3-Q9 rulings), then rebuild A1; then A1 per-unit review.
