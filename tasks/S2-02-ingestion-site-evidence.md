# S2-02 - Shared ingestion and Site Evidence

Status: outline; refine after S2-01c review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S2 Evidence
Depends on: S2-01c
Branch: task/S2-02-ingestion-site-evidence
Planner: Codex, 2026-10-07; contract audit 2026-10-07

## Visible outcome

Site evidence/evidence-analysis and Lab Commit show accepted, delayed, rejected, duplicate and conflicting records with source provenance, queue/ingestion lag and exact lineage after reload.

## Current code and required transition

The current `POST /api/ingestion/batches` and `IngestionService` already share parsing/deduplication for the demo, but use batch V1, no gateway credential boundary, process-local locking, identity normalization and `JsonEvidenceStore`. Lab Commit calls `ingestion.ingest` in process. Adapt the service and route; replace product evidence storage with Postgres and Commit's privileged in-process call with the registered simulated gateway posting the authenticated HTTPS API. The S2 demo source is simulated only; the physical protocol peer waits for the first real pilot. Preserve legacy parsers for migration, not as the new write contract.

Carry the Foundation-only cutover: imported Site Evidence remains visibly awaiting migration until this task compares and switches its Postgres read. Keep product index/detail routing one imported Postgres KOBO-001 plus unimported legacy YAML Sites; do not reintroduce a stale product read or write. Authenticate tenant/site/gateway/source separately; S1 pending registration authorizes no upload. S2-01a supplies the registered Lab run basis; this task supplies authenticated Commit delivery for new registered runs. Pre-import Stages remain read-only and cannot be Committed through the new path; separately replay only already sealed historical batches through the explicit migration procedure. Resolve the originally registered Foundation/binding at each source time, preserving the accepted-as basis. A pair whose original valid periods cover the source time remains eligible even if later superseded or current registration identity has changed; flag an outdated configuration without substituting the accepted basis.

## Persisted object and read contract

Use the recorded `A-edge-batch-signature` decision: the pilot verifies registered TLS gateway credentials and canonical Batch V2 SHA-256, with exact-byte retries; per-batch signatures and key rotation are deferred. Ingest authenticated `GatewayDiagnosticsV1` reports into `gateway_diagnostic` with server receive time. Expose last contact, queue depth/oldest age, clock offset and disk pressure with an explicit stale/unknown state for later SourceHealth. Diagnostics are operational reports, not AcceptedEvidence or a healthy-device claim. A gateway outage remains visible centrally after reload.

Use registered gateway/site/source credentials over TLS, bounded Batch V2 upload, durable queryable Receipt V2 and Postgres IngestionBatch, AcceptedEvidence, EvidenceRejection/Conflict and per-ordinal Disposition. Check each envelope's original registered Foundation/binding validity at source time; normalize with its accepted-as conversion, retain raw bytes/digest and quality, and record `received_at` at the server. Identical ID/bytes are duplicates; same ID/different bytes conflicts without overwrite. Persist batch progress, per-record decisions and a recompute job in the same transaction. S3-01 supplies the analytic worker/consumer.

`GET /api/sites/{id}/evidence` and `/api/sites/{id}/evidence/records/{id}` read Postgres with window, coverage, provenance, rejection/conflict detail and projection watermark. A partial batch returns `202 IN_PROGRESS` until its terminal receipt; retries resume by ordinal. Authentication failures and whole-batch configuration refusal cannot be disguised as per-record acceptance.

## Demo acceptance and cutover

Registered Kobo demo setup follows `D-2026-10-08-s2-registered-kobo-demo-configuration`. A `mini-grid` v3 generator-evidence run requires a separate, later-effective Foundation publication of the four missing static generator properties with explicit template/demo provenance and a scenario that supplies initial fuel-tank volume and generator state. Do not silently alter the S1 import, old snapshots or original YAML. For a profile-5 or capability demonstration, declare and bind PV inverter available-power and battery PCS discharge-capability as typed optional kW roles in a new role-vocabulary version before running; until then show them as unconfigured and withhold capability conclusions. The basic S2-02 accepted-evidence path may use already bound channels without these optional additions. Refine the publication fixture, selected effective interval, source-time coverage and focused proof before activating this outline; S2-01b does not own this setup.

Commit a simulated run; disconnect/retry, duplicate exact bytes, conflict same ID/different bytes, crash after server commit, partial sibling rejection, same-timestamp distinct sequences and late sample. Inspect receipt, central gateway diagnostics and Site Evidence after process reload. Register/import existing Site/Foundation/mapping data, replay sealed committed batch bytes via legacy parsers, compare acceptance counts and representative records with the file-backed baseline, and record the old dispatch claims as S3 comparison fixtures. Switch supported Evidence reads to Postgres only after the evidence comparison passes; S3-01 compares dispatch claims before switching Performance reads. Keep `var/sites`, Lab runs/stages/committed artifacts untouched; report unresolved configuration as migration exceptions. Lab-private truth never enters Postgres.

## Missing/conflicting evidence

Missing required role, bad unit, an unregistered pair or source time outside its original valid period, and wrong credential have explicit refusal/rejection/coverage states. A once-registered, time-valid pair later superseded is accepted under its original basis with an outdated-configuration flag, as the technical design requires. Ingestion lag is pending, never healthy.

## Evidence lineage

Open each accepted record to original/normalized value and unit, source/published/received times, registered gateway/source, Foundation/binding revisions, canonical envelope digest and per-ordinal receipt. A duplicate resolves the first accepted ID; a conflict preserves the original.

## Review and refinement

Reviewer opens Site Evidence and Lab Commit, verifies Postgres reload, receipt retry, central diagnostics and legacy comparison using simulated input. Before activation, refine exact credentials, migration fixture, wire fields and focused checks using S2-01c outcome and the current technical design. Apply shared queue gates. Physical-adapter input proof is a first-real-pilot gate, not S2 acceptance.

S1 carry to consume at refinement: registration identity fields remain mutable. `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` makes pinned historical snapshot reads independent of current registration gaps; S2-02 must validate originally registered identity and validity from immutable version/snapshot references rather than current mutable names. Define gateway credential scope separately; S1's development-tenant snapshot download is not an authenticated gateway endpoint. Reconcile the actual S2-01a frozen basis and S2-01b/c wire, outbox and diagnostics before activating this outline. `queue_baseline_nodes` still assigns `I-accepted-evidence-store`, `I-edge-diagnostics-store`, `I-S2-02` here; no baseline move from S1.

S2-01b seals V3/Batch V2 bytes under a separate local gateway and leaves every registered batch pending. At refinement, take its actual canonical vectors, batch IDs, receipt slots and transfer scope as inputs; make Commit release those existing staged bytes through authenticated HTTPS and persist a server decision before any local ACK. Do not re-envelope S2-01a's legacy file Stage or create a second batch identity in the backend.

Before this slice accepts evidence, close the S2-01a phase-1 identity carry: make `asset.asset_code` stable at the database boundary so a binding's immutable asset UUID cannot silently resolve to a different Foundation component after publication. Include an explicit reconciliation path for any existing changed row and prove that a direct update is refused. Apply the same original-versus-current identity review to Site type and gateway/source external IDs when refining registered credential and evidence checks; a current name is never evidence that an older snapshot used it. This is an acquisition-lineage gate, not an S2-01a snapshot-schema-v2 requirement.

## Defer

Analytics, full replay UI, broker transport and optional artifact-store offload.
