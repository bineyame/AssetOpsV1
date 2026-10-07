# S1-01 — Persisted Site Foundation

Status: ready for implementation
USER_REVIEW_REQUIRED: true
Milestone: S1 Foundation
Depends on: accepted Site-first plan; no S task
Branch: task/S1-01-persisted-foundation
Planner: Codex, 2026-10-07

## Outcome and reason

Open Kobo's `foundation` mock surface and see a real persisted Site definition at a selected time. This is the first public configuration basis for gateway and claims. Reuse the existing shell and form where useful; the new product write/read authority is Postgres.

## Contract and migration seam

- Migrate the minimum tenant, site, asset, gateway, source and immutable FoundationRevision tables from the accepted technical design. Enforce tenant/site identity, stable asset and source IDs, valid-time selection and recorded-time revision history. Register one mini-grid role set, one gateway and its sources with the fixture Site; S1-02 binds channels to roles.
- Create/import a Kobo mini-grid Site through the supported Foundation path. Publish a changed reserve or control setting with a new effective version, preserving the earlier basis. `GET /sites/{id}/foundation?at=` returns selected Foundation ID/version, valid period, topology, objectives, controls, registered gateway/sources and explicit configuration gaps; a requested historical instant resolves the earlier version.
- Keep existing JSON/YAML Site data intact for migration comparison. Import one explicit Kobo fixture with stable external codes and record a comparison of identity/topology/control values. New writes go to Postgres. Do not silently rewrite `var/sites` or claim old file-backed evidence is migrated.
- A gateway snapshot read/download may expose the currently registered Foundation basis and gateway identity now; S1-02 adds versioned binding content and an atomic combined snapshot. Credentials are never returned as Site configuration.

## Demo and acceptance fixture

1. With a fresh Postgres database, create/import Kobo with generator, PV, battery, loads and controller as registered assets. Open Foundation and inspect version, effective period, topology and reserve/control value; reload and get the same IDs and values from the API.
2. Publish a future-effective reserve/control change, reopen before and after the cutover, and show both versions remain addressable. Invalid overlaps and a cross-tenant asset/source reference are refused without partial writes.
3. Open a Site lacking a required configuration value: Foundation names the gap; it does not present operational health or simulated runtime as observed fact. The configured SLD portion shows only persisted topology.
4. Reviewer follows the Foundation revision ID through API to Postgres and the imported fixture comparison. Record that operational evidence lineage begins at S2; S1 has no accepted SourceEnvelope yet. The API must never fabricate one.

## Protected seams and checks

Use the accepted architecture and technical design sections 1, 3 and 4; Site identity and time-valid configuration are public, Lab truth remains private. Run migrations from empty DB, API/reload and historical-time checks, tenant isolation and invalid revision transaction check, plus workflow/architecture guards and frontend checks for changed code. Reviewer opens the actual screen and API response.

## Defer

S1-02 owns role bindings and Readiness. S2 owns evidence delivery and operational status. No full bitemporal editing UI, estate seed, global index or speculative schema layer.
