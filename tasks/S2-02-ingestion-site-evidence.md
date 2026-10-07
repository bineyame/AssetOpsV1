# S2-02 — Shared ingestion and Site Evidence

Status: outline; refine after preceding task review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S2 Evidence
Depends on: S2-01
Branch: task/S2-02-ingestion-site-evidence
Planner: Codex, 2026-10-07

## Visible outcome

Site evidence/evidence-analysis and Lab Commit show accepted, delayed, rejected and duplicate records with provenance.

## Persisted object and read contract

Authenticated HTTPS batch API; Postgres IngestionBatch, AcceptedEvidence, EvidenceRejection and per-ordinal Disposition; GET /sites/{id}/evidence and /evidence/records/{id}.

## Demo acceptance

Commit a simulated run and captured physical fixture; disconnect/retry, duplicate exact bytes, conflict same ID/different bytes, partial sibling rejection and late sample; inspect durable receipts and Site Evidence after reload.

## Missing/conflicting evidence

Missing required role or bad unit has explicit rejection/coverage, not a healthy claim.

## Evidence lineage

Open each accepted record to raw/normalized value, source times, gateway, Foundation and binding revisions and canonical envelope digest.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Analytics and full replay UI.
