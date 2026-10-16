# S4-05a review packet - immutable source binding and exact-revision resolver

## Task

`tasks/S4-05a-provenance-binding-resolver.md` (umbrella `tasks/S4-05-stored-demo-provenance.md`; authority
`D-2026-10-15-s405-stored-demo-provenance`, `.agent/architect-S4-05-answers.md` Q1-Q3, rule 8, Follow-up M1;
coordinator note N-L1..N-L3). Branch `task/S4-05a-provenance-binding-resolver` from main `fd7afd2c`.
USER_REVIEW_REQUIRED: false (no UI). This phase-2 review is the slice review.

## Outcome delivered

- Phase 1 (`2dd7b92e`, reviewed: accept once M1 fixed): migration 0014 insert-only publication + exact-commitment
  link, shared slot lock in registration and `open_batch`, SYSTEM authority, server CLI, rule 8 INSERT-only. See
  `.agent/S4-05a-phase-1-handoff.md`.
- Phase 2 (`a5f448b3`, `1d271c6a`): `SourceProvenanceResolver` - tenant/Site-scoped per-ID provenance and set
  state for a selected FindingRevision (its own cited set) and a consequence revision (union with its own
  power-interval IDs, reported separately), with exact IDs, all publication/run IDs, problematic IDs and typed
  reasons. Field contract for S4-05b: `.agent/S4-05a-phase-2-handoff.md`.
- Phase-1 review folded in (`a3640cce`): M1 every source class needs a SIMULATED gateway (LIVE authored refused,
  nothing written); L1 split `UPDATE`/`DELETE FROM`/`TRUNCATE` on provenance refused in any module; L2/L4 in the
  phase-2 handoff; L3 committed downgrade-refusal test.
- No read DTO, route or the old date/spec heuristic changed (S4-05b cuts over).

## Files materially changed (phase 2 + fixes)

- `backend/assetops_backend/evidence/source_provenance.py` (new, pure): `LinkRow`, `link_of`, `classify`,
  `SourceProvenanceResolver`, constants (class constants now defined here; `publication.py` imports them).
- `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py`: read-only `link_rows`,
  `finding_revision_evidence`, `consequence_inputs`; M1 gateway-mode refusal for every class.
- `backend/assetops_backend/evidence/composition.py`: `build_source_provenance`.
- `tools/checks/configuration-persistence.ps1`: L1 split-statement rule.
- Tests: `backend/tests/test_s405_resolver.py` (12, pure), `backend/tests/test_s405_resolver_postgres.py`
  (8, real Postgres), `backend/tests/test_s405_publication_postgres.py` (M1 flip, L3 downgrade test; 21).

## Acceptance criteria (phase 2)

| Criterion | Status |
| --- | --- |
| One tenant/Site-scoped resolver, exact per-ID provenance, all publication/run IDs, problematic IDs, typed reasons | Met: `classify` fields; real-PG `test_two_publications_of_one_fixture_version_resolve_authored` checks per-ID publication/batch |
| FindingRevision cited set (`finding_read.py:350,446` source table) and consequence power IDs (`consequence_read.py:87,149` source table) | Met: reads `finding_revision_evidence` and `financial_consequence_power_interval` for the named revision only; DTOs untouched |
| Two publications same fixture/version -> AUTHORED, list both | Met (pure + PG) |
| Differing version / fixture -> MIXED | Met (pure: version and ID; PG: P01 vs P02) |
| One run -> REGISTERED_SIMULATION; compatible/incompatible several runs -> MIXED (N-L2) | Met: no compatible-run-basis record exists, so any two run IDs are `MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS` (PG, two real runs); same run ID with two digests -> `RUN_IDENTITY_CONFLICT` (pure) |
| Class crossing; bound/unbound mix | Met: both reasons reported together (PG + pure) |
| Empty set; no positive binding | Met: `EMPTY_CITATION_SET`, `NO_POSITIVE_BINDING` |
| Foreign/missing/broken link with UNKNOWN precedence | Met: PG missing over a MIXED set; same-tenant other Site -> `FOREIGN_SITE_EVIDENCE`; other tenant -> not found (no disclosure); broken links built in a rolled-back transaction with FKs dropped (`LINK_COMMITMENT_MISMATCH`, `PUBLICATION_NOT_FOUND`) over a MIXED set; all six broken details in pure tests |
| Consequence-only mixed power | Met: real pipeline with power batches published P02 and the rest P01: Finding AUTHORED, consequence MIXED with `CONSEQUENCE_POWER_INPUT_CONFLICT` naming power-only IDs |
| Selected historical revision, not head | Met: after a new head revision (empty cited set, UNKNOWN), the old revision still resolves AUTHORED with the same publication IDs |
| Resolver usable without changing public DTOs | Met: no DTO/route diff |
| Rule 8 guard | Met: `tools/check-architecture.ps1` passes; L1 probes below |

## Checks run

- Focused: `test_s405_resolver.py` + `test_s405_resolver_postgres.py` 20 passed (24 s);
  `test_s405_publication_postgres.py` + `test_s2_evidence_ledger_postgres.py` 44 passed before fixes;
  `test_s405_publication_postgres.py` 21 passed after fixes. Private DB `assetops_s405a_test`.
- Resolver mutations (applied to committed tree, restored by `git checkout`, tree clean): all 10 caught -
  precedence (broken only when nothing bound), several runs coherent, link commitment not compared, missing
  publication read as unbound, fixture version ignored, bound+unbound not mixed, crossed classes not mixed,
  consequence ignores its power IDs, SQL loses Site scope (PG test), cited set not pinned to the selected revision
  (PG test).
- Review fixes: M1 mutation (mode check limited to simulation) fails `test_a_live_gateway_cannot_carry_any_publication`.
  L1 probes: split `UPDATE evidence_publication`/`SET` in the ledger and split `TRUNCATE TABLE evidence_publication`
  in the finding store fail with the new insert-only message; split `DELETE FROM batch_publication_link` in a
  non-writer fails via the existing second-writer rule.
- `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1`: pass. `tools/check-all.ps1` (main venv python,
  `npm ci` in frontend): all 9 guards passed.
- Full backend suite on code revision `a3640cce` (closeout commit changes docs only): `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=<scratchpad>/full-junit.xml` from PowerShell, base `assetops_test`, keep-awake running, temporary `var/sites/*.yaml` copy (removed after). Wall 687 s (cap 20 min). JUnit: tests=2170 failures=0 errors=0 skipped=0; `2170 passed, 27 warnings in 685.34s`. (An earlier start was stopped because another worktree's full run was active; this run started after it ended.)

## Known deviations

- Resolver SQL lives in the ledger adapter, not a separate read adapter: rule 8 allows the database driver only in
  the eight writer modules. Reads only; no new writer.
- Cross-tenant IDs are reported `EVIDENCE_NOT_FOUND`, not foreign, so a tenant learns nothing about another
  tenant's rows; `FOREIGN_SITE_EVIDENCE` means another Site of the same tenant.
- On UNKNOWN by precedence, `reasons` name only the UNKNOWN causes (the MIXED causes of the rest are not listed);
  per-ID `evidence[]` still shows every binding.
- `CONSEQUENCE_POWER_INPUT_CONFLICT` is added whenever the union is MIXED and the FindingRevision set alone is not
  MIXED and not UNKNOWN; its IDs are the power-only IDs.
- Fix round L2 (supersedes the earlier "including UNKNOWN" wording): when the FindingRevision part resolves UNKNOWN
  (incl. `EMPTY_CITATION_SET`), the consequence state is UNKNOWN, never positive or MIXED, and carries the finding
  part's reasons first (then any further union reasons with other codes). Fail closed, consistent with
  `D-2026-10-15-s405-stored-demo-provenance`. Tests: `test_unknown_finding_part_makes_the_consequence_unknown_never_positive`
  (pure) and `test_unknown_finding_makes_its_consequence_unknown_even_with_bound_power_inputs` (Postgres).
- Fix round L1: rule 8 refuses UPDATE/DELETE FROM/TRUNCATE on a provenance table when schema-qualified, quoted, or
  split with the table name on the next line, in any module.
- The packet said S4-05b owns the final full suite; the phase-2 dispatch asked for one here, so it was run.

## Residual risk

- Broken links are impossible under the scoped FKs; the broken-link PG proof drops constraints inside a rolled-back
  transaction and reads on that connection, so it exercises the SQL but not a production failure path.
- Run identity digest is not re-verified after registration (file-backed run store); migration 0014 re-chain vs
  LR-01/S6-01a; lock key is the admission slot (stricter than packet wording); see phase-1 handoff.
- Phase-1 latency baseline already includes the new 7-column `ingestion_batch` unique index (review L4).

## User-review focus

None required (USER_REVIEW_REQUIRED false). Owner copy for MIXED/UNKNOWN and labels is S4-05b's checkpoint.

## Re-chain onto main (2026-10-16)
- Merged main `4fbb97f8` (LR-01 0014/0015, S6-01a 0016) into the branch; doc conflicts kept both sides.
- `0014_evidence_publication` -> `0017_evidence_publication.py`, `down_revision = "0016_action_store"`; downgrade message and test target updated (refuses to 0016). Pins updated in s1_bindings, s2_evidence_ledger, s4_evidence_consequence_work, s4_consequence_store, s405_publication tests. `alembic heads`: single head `0017_evidence_publication`.
- Rule 8 keeps LR-01 `source_clock_attestation`, S6-01a Action writer, and this branch's provenance rules plus split-statement refusals; `check-architecture.ps1` passes.
- Focused (5 files): 87 passed. Full backend, PowerShell, `-n 2 --dist loadfile --no-loadscope-reorder`, on merge commit 5f60f48f (docs-only edits after): 2368 cases, skipped=0, failed=0, wall 12:03. `tools/check-all.ps1`: all 9 guards passed.
