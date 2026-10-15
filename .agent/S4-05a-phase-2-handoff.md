# S4-05a phase 2 handoff - exact-revision resolver (slice complete, in_review)

Branch `task/S4-05a-provenance-binding-resolver` (worktree `AssetOpsV1-review3`). Phase-2 commits `a5f448b3`,
`1d271c6a` (resolver), `a3640cce` (phase-1 review fixes), then closeout. Phase-1 review
(`AssetOpsV1-review4/.agent/S4-05a-phase-1-review.md`, coordinator brings it onto the branch) folded in.

## Resolver contract for S4-05b

- Domain (pure, route-safe; no SQL, no designation import): `backend/assetops_backend/evidence/source_provenance.py`.
  Build with `evidence.composition.build_source_provenance(database_url)` -> `SourceProvenanceResolver`.
  - `resolve(tenant_id, site_id, ids)`; `finding_revision(tenant_id, site_id, finding_revision_id)`;
    `consequence_revision(tenant_id, site_id, consequence_revision_id)`. Revision calls return None when the
    revision is not in the tenant/Site (never a fallback to the head).
  - Fields: `state` (`AUTHORED_DEMONSTRATION|REGISTERED_SIMULATION|MIXED|UNKNOWN`), `reasons[]`
    (`{code, accepted_evidence_ids, ...detail}`), `accepted_evidence_ids` (the resolved set; for a consequence,
    the union), `problematic_accepted_evidence_ids`, `publication_ids`, `source_classes`, `fixtures[]`, `runs[]`,
    `evidence[]` (per ID: `accepted_evidence_id, status, batch_id, publication_id, source_class, fixture_id,
    fixture_version, run_id, run_identity_sha256, broken_detail`); revision calls add `tenant_id, site_id,
    finding_revision_id, consequence_revision_id, cited_accepted_evidence_ids, power_accepted_evidence_ids`, and
    a consequence adds `finding_revision_state`.
  - Reason codes: UNKNOWN `EMPTY_CITATION_SET, EVIDENCE_NOT_FOUND, FOREIGN_SITE_EVIDENCE, BROKEN_PUBLICATION_LINK`
    (details `BATCH_NOT_FOUND, EVIDENCE_BATCH_SCOPE_MISMATCH, LINK_COMMITMENT_MISMATCH, PUBLICATION_NOT_FOUND,
    PUBLICATION_COMMITMENT_MISMATCH, PUBLICATION_CLASS_INVALID`), `NO_POSITIVE_BINDING`; MIXED
    `BOUND_AND_UNBOUND, CROSSED_SOURCE_CLASSES, AUTHORED_FIXTURE_VERSION_CONFLICT,
    MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS, RUN_IDENTITY_CONFLICT, CONSEQUENCE_POWER_INPUT_CONFLICT`.
    Missing/foreign/broken precede MIXED; several MIXED reasons are all reported.
- SQL: read-only methods on `PostgresEvidenceLedger` (`link_rows`, `finding_revision_evidence`,
  `consequence_inputs`) because rule 8 allows the driver only in the eight writers.
- Fixtures for S4-05b tests: `backend/tests/test_s405_resolver_postgres.py` (`power_site(..., policy)` publishes
  each exact sealed batch per device before upload, so the real Finding/consequence pipeline cites bound evidence).
- S4-05a leaves every read DTO and the date/spec heuristic unchanged.

## Carries for S4-05b (amended per phase-1 review)

- N-L1 (amended, review L2): the `run_attestation(run, port.registered_stage(run))` + `register_run` call lives in
  a non-route module reached through the runs port/composition (e.g. beside `release_registered` in
  `runs/execution_ports.py`), never in `simulator_lab_api.py` or any `*_api.py`: rule 8 refuses designation names
  in HTTP modules. Refuse release on any `PublicationRefused`.
- Review M1 now applies: every publication (authored too) needs a SIMULATED gateway. P01/P02 authored producers
  must publish through a SIMULATED gateway.
- Lock-cost note (review L4): the phase-1 latency baseline was measured after migration 0014, so the "unbound"
  baseline already includes the new 7-column unique index `ingestion_batch_commitment_unique`; the added cost
  of that index on batch INSERT is not separated out.
- Migration re-chain (0014 vs LR-01/S6-01a) and the S5-01 amendment (N-L3) are unchanged from phase 1.

## Fix-round amendment (S4-05b contract)

`consequence_revision(...)["state"]` is UNKNOWN whenever `finding_revision_state` is UNKNOWN (including
`EMPTY_CITATION_SET`), regardless of power inputs; the Finding part's reasons are carried first. S4-05b must not
present a positive or MIXED consequence provenance beside an UNKNOWN Finding revision.
