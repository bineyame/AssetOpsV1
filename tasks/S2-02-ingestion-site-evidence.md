# S2-02 - Shared ingestion and Site Evidence

Status: outline; refine after S2-01 review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S2 Evidence
Depends on: S2-01
Branch: task/S2-02-ingestion-site-evidence
Planner: Codex, 2026-10-07; contract audit 2026-10-07

## Visible outcome

Site evidence/evidence-analysis and Lab Commit show accepted, delayed, rejected, duplicate and conflicting records with source provenance, queue/ingestion lag and exact lineage after reload.

## Current code and required transition

The current `POST /api/ingestion/batches` and `IngestionService` already share parsing/deduplication for the demo, but use batch V1, no gateway credential boundary, process-local locking, identity normalization and `JsonEvidenceStore`. Lab Commit calls `ingestion.ingest` in process. Adapt the service and route; replace product evidence storage with Postgres and Commit's privileged in-process call with a registered simulated gateway posting the same authenticated HTTPS API as the captured physical fixture. Preserve legacy parsers for migration, not as the new write contract.

Carry the Foundation-only cutover: imported Site Evidence remains visibly awaiting migration until this task compares and switches its Postgres read. Authenticate tenant/site/gateway/source separately; S1 pending registration authorizes no upload. Resolve the originally registered Foundation/binding at each source time, preserving the accepted-as basis.

## Persisted object and read contract

Use registered gateway/site/source credentials over TLS, bounded Batch V2 upload, durable queryable Receipt V2 and Postgres IngestionBatch, AcceptedEvidence, EvidenceRejection/Conflict and per-ordinal Disposition. Check each envelope's original registered Foundation/binding validity at source time; normalize with its accepted-as conversion, retain raw bytes/digest and quality, and record `received_at` at the server. Identical ID/bytes are duplicates; same ID/different bytes conflicts without overwrite. Persist batch progress, per-record decisions and a recompute job in the same transaction. S3-01 supplies the analytic worker/consumer.

`GET /api/sites/{id}/evidence` and `/api/sites/{id}/evidence/records/{id}` read Postgres with window, coverage, provenance, rejection/conflict detail and projection watermark. A partial batch returns `202 IN_PROGRESS` until its terminal receipt; retries resume by ordinal. Authentication failures and whole-batch configuration refusal cannot be disguised as per-record acceptance.

## Demo acceptance and cutover

Commit a simulated run and upload a captured physical fixture; disconnect/retry, duplicate exact bytes, conflict same ID/different bytes, crash after server commit, partial sibling rejection, same-timestamp distinct sequences and late sample. Inspect receipt and Site Evidence after process reload. Register/import existing Site/Foundation/mapping data, replay sealed committed batch bytes via legacy parsers, compare acceptance counts and representative records with the file-backed baseline, and record the old dispatch claims as S3 comparison fixtures. Switch supported Evidence reads to Postgres only after the evidence comparison passes; S3-01 compares dispatch claims before switching Performance reads. Keep `var/sites`, Lab runs/stages/committed artifacts untouched; report unresolved configuration as migration exceptions. Lab-private truth never enters Postgres.

## Missing/conflicting evidence

Missing required role, bad unit, stale configuration or wrong credential has an explicit refusal/rejection/coverage state. Ingestion lag is pending, never healthy.

## Evidence lineage

Open each accepted record to original/normalized value and unit, source/published/received times, registered gateway/source, Foundation/binding revisions, canonical envelope digest and per-ordinal receipt. A duplicate resolves the first accepted ID; a conflict preserves the original.

## Review and refinement

Reviewer opens Site Evidence and Lab Commit, verifies Postgres reload, receipt retry, legacy comparison and the shared physical/simulated path. Before activation, refine exact credentials, migration fixture, wire fields and focused checks using S2-01 outcome and the current technical design. Apply shared queue gates.

## Defer

Analytics, full replay UI, broker transport and optional artifact-store offload.
