# T027 phase 1 - implementer plan

Written by the phase 1 coordinating implementer. Each sub-phase is built by a
fresh agent from this file plus the task file
(`tasks/T027-commit-ingestion-and-site-overview.md`). Phase 1 ACs: 1-9, 12,
16-18, 20, 21, 23 in full; 10, 13, 14, 15, 19 for evidence and Site > Evidence.
Phase 2 (Overview, AC11, AC22) is NOT built here.

## Settled design (do not re-decide)

### D1. The committed artifact is a contract: `contracts/assetops_contracts/committed_artifact.py`

- Built from envelopes + the frozen `SourceMappingSet` + a manifest. It must
  NOT import `source_stage` (contracts may import `source_envelope`).
- `CommittedArtifact` (frozen dataclass, validates in `__post_init__`):
  `schema` (`assetops.committed-artifact` v1), `artifact_id`, `run_id`,
  `site_id`, `source_id`, `gateway_id`, `source_mode` (`SIMULATED` | `LIVE`;
  the run's Site source mode, provenance only), `configuration`
  (`ConfigurationReference`: `site_id`, `foundation_version`,
  `foundation_valid_from` - the run's `FrozenSiteBinding`), `mapping`
  (`SourceMappingSet`), `stage_integrity_digest` (the stage digest it was
  sealed from), `envelopes` (tuple of `SourceEnvelope`, stage order),
  `manifest` (tuple of `(message_id, content_digest)` per envelope, same order),
  `sealed_at` (instant text).
- `artifact_id` is derived, not allocated: `commit-` + first 32 hex of
  BLAKE2b-256 over (`run_id`, `stage_integrity_digest`) under its own domain.
  So re-sealing the same stage yields the same id (AC2 "same identities").
- `content_digest` per envelope = BLAKE2b-256 of its canonical text.
  `artifact_integrity_digest` = BLAKE2b-256 over the canonical document minus
  the digest field. `artifact_text(a)` -> canonical JSON with the digest;
  `parse_artifact_text(text)` is strict (exact keys, canonical bytes, every
  envelope through `parse_canonical_envelope_json` and
  `check_against_mapping`, manifest digests recomputed, integrity verified)
  and raises `ArtifactUnreadable(detail)`.
- `ingestion_batch(artifact) -> IngestionBatch` (see D2): the artifact as an
  ordinary ingestion batch. This is the ONLY thing release hands ingestion.

### D2. One ingestion interface for every source (AC3, AC4, AC16)

`contracts/assetops_contracts/ingestion_batch.py` (or in the same module if
small): `IngestionBatch` = `batch_id`, `site_id`, `source_id`, `gateway_id`,
`source_mode`, `configuration` (`ConfigurationReference`), `mapping` (mapping
document, parsed by `parse_mapping_set`), `envelopes` (tuple of canonical
envelope TEXTS, not objects). `parse_ingestion_batch_document(doc)` exact keys;
an unknown key anywhere (e.g. `truth`, `lab_projection`, `observation`) is a
whole-batch rejection `UNKNOWN_FIELD`. Envelope texts are parsed one by one
in ingestion, so a bad envelope is a per-record rejection, not a batch failure.

The backend exposes the same interface twice: `POST /api/ingestion/batches`
(ungated, any source) and the in-process `IngestionService.ingest(batch)`
which the Lab Commit route calls. The HTTP route is a thin wrapper over that
same method. No other path writes evidence.

### D3. Backend evidence package `backend/assetops_backend/evidence/` (ungated)

Layout like `sites/`: `models.py`, `ports.py`, `service.py`, `read_model.py`,
`composition.py`, `adapters/json_evidence_store.py`; router
`backend/assetops_backend/evidence_api.py`, mounted in `create_app` in both
gate states (new injectable `evidence_store=` and `clock=` params).

Must not import: `assetops_simulator`, `host`, `assetops_contracts.source_stage`,
`assetops_contracts.lab_history`, `assetops_contracts.lab_projection`,
`assetops_contracts.observation`, `assetops_backend.runs`,
`assetops_backend.simulator_lab_api`. Add this as a NEW rule in
`tools/checks/dependency-direction.ps1` (with anti-vacuity: at least one
evidence module scanned) and prove it non-vacuous.

Records (`models.py`):
- `AcceptedRecord`: `message_id`, `envelope_text` (canonical, original),
  `content_digest`, `site_id`, `source_id`, `gateway_id`, `device_id`,
  `signal_id`, `family`, `source_time`, `published_at`, `received_at`
  (ingestion clock, UTC instant text), `batch_id`, `source_mode`,
  `mapping_set_id`, `mapping_version`, `configuration`
  (`ConfigurationReference`), `original` (value text + unit as published),
  `normalized` (value text + unit after normalization; normalization is the
  identity in this build because the mapping refuses unit conversion - say so
  in the inspector, do not invent a conversion), `quality`,
  `unavailable_reason`, interval fields, record-family fields.
- `Rejection`: `batch_id`, `index`, `message_id | None`, `kind` (envelope
  rejection kinds + `SITE_MISMATCH`, `CONFIGURATION_UNRESOLVED`,
  `SIGNAL_NOT_IN_CONFIGURATION`, `BEFORE_CONFIGURATION_EFFECTIVE`), `field`,
  `detail`, `received_at`, `content_digest` of the text.
- `Conflict`: `message_id`, `batch_id`, `original_digest`,
  `conflicting_digest`, `received_at`. The original accepted record is never
  touched (AC6).
- `BatchProgress` (release status, AC7/AC18): `batch_id`, `site_id`,
  `source_id`, `total`, `processed` (index watermark), `accepted`,
  `duplicates`, `rejected`, `conflicts`, `status` (`IN_PROGRESS` |
  `COMPLETED` | `REFUSED`), `refusal` (whole-batch kind/detail), `started_at`,
  `completed_at`, `window_start`/`window_end` (min/max source_time accepted).
- `ConfigurationBasis`: immutable registry entry keyed by
  (`site_id`, `foundation_version`): `foundation_valid_from`, `site_type`,
  `signals` ((device_id, signal_id, unit, component_id)...), `registered_at`.
- `MappingRegistration`: immutable by (`mapping_set_id`, `mapping_version`),
  canonical mapping document text.

Ingestion algorithm (`IngestionService.ingest(batch)`):
1. Resolve the Site via `SiteRepository.get_site`. Unknown Site, or
   `batch.source_mode != site.source.mode` -> REFUSED batch (no records).
2. Mapping: register or match the immutable registration; same id/version
   with different content -> REFUSED (`MAPPING_CONFLICT`).
3. Configuration: resolve (`site_id`, `foundation_version`) from the basis
   registry; if absent and it equals the Site's CURRENT Foundation version,
   register a basis snapshot from the current Foundation (devices/signals/
   units); if absent and not current -> REFUSED `CONFIGURATION_UNRESOLVED`.
   Once registered it is never rewritten, so a later Foundation edit cannot
   change historic interpretation (AC17).
4. Resume: if progress for `batch_id` exists and is `COMPLETED`, return it
   unchanged (idempotent). If `IN_PROGRESS`, continue from `processed`.
5. Per envelope text from `processed`: `parse_canonical_envelope_json` ->
   rejection on `EnvelopeRejected`; site/source/gateway must equal the batch
   (`SITE_MISMATCH`); `check_against_mapping` against the registered mapping;
   MEASUREMENT device/signal/unit must be in the basis
   (`SIGNAL_NOT_IN_CONFIGURATION` / `UNIT_INCOMPATIBLE`); `source_time >=
   foundation_valid_from` (`BEFORE_CONFIGURATION_EFFECTIVE`). Then identity:
   existing accepted with same digest -> duplicate (idempotent, counted, not
   re-stored); existing with different digest -> `Conflict`; else accept with
   `received_at = clock()`.
6. Persist in chunks (default 64 records): records + progress written in ONE
   atomic store write per chunk, so a crash leaves a consistent prefix and the
   watermark says exactly what was processed (AC7). A test fault hook
   (`fail_after` injected into the service, test-only) proves interruption.
7. Mark `COMPLETED`.

Overlap (AC9): identity is the envelope `message_id` (Site, gateway, source,
device, signal, source_time). Distinct ids at the same (device, signal,
source_time) - e.g. two gateways - are BOTH accepted and the read model reports
them as `overlapping` in coverage and lists both in the inspector; nothing
sums or replaces them. Document this in the module docstring.

Store (`adapters/json_evidence_store.py`): `var/evidence/` (gitignored, add to
`.gitignore` if `var/` is not already ignored): one canonical JSON document per
Site `sites/{site_id}.json` (accepted records keyed by message id, rejections,
conflicts, batch progress), plus `registry/mappings/*.json` and
`registry/configuration/*.json` written exclusively once. Atomic write =
`.partial` + `os.replace` (copy the pattern in `host/source_stages.py`). Port
signatures speak domain records only (Configuration Persistence rule).
`clear_derived()` empties the derived per-Site documents but keeps the
registries (used by rebuild, AC14).

Read model (`read_model.py`), accepted content only (AC8):
- `site_evidence(site_id, window_start?, window_end?)`:
  - `sources`: per (source_id, gateway_id): `source_mode`, accepted /
    rejected / conflict / duplicate counts, last `source_time`, last
    `published_at`, last `received_at`, batches (id, status, processed/total).
    Wording: source/connector health is data quality, never asset health.
  - `coverage`: per (device_id, signal_id) in the window: unit, records,
    `good`, `unavailable`, `overlapping`, first/last source_time, longest
    silence between consecutive source times (seconds), and `needed_by`
    (the Overview metric(s) that need it). Signals the Overview needs that
    have NO accepted record in the window are listed with status
    `NOT_REPORTED` ("coverage gap", no value). The needed-signal list is
    static substrate data keyed by `site_type` (`mini-grid`), in the backend
    read model, from the task's phase 2 card list: pv-inverter-controller/
    ac-power (Renewable), battery-pcs-controller/state-of-charge (Battery),
    generator-controller/status and ac-power (Dispatch), fuel-level-sensor/
    fuel-level (Fuel), residential-meter|clinic-meter|mill-meter/active-power
    (Service). It names signals only; it holds no card state.
  - `basis`: the mapping registrations and configuration bases the window's
    records were accepted under (ids, versions, valid_from), and the CURRENT
    Foundation version for contrast (AC17).
  - Default window: the latest completed batch's window, else all.
  - Nothing about capability readiness or claim ceilings (AC20).
- `records(site_id, device_id?, signal_id?, source_id?, window?)` - the
  inspector list (bounded, newest first, limit param).
- `record(site_id, message_id)` - the inspector detail: source/device/signal,
  mapping id/version, configuration basis, quality, original value/unit,
  normalized value/unit, source_time, published_at, received_at, batch id,
  source_mode (AC12). Plus any conflicts recorded against it.
- `batch(batch_id)` - progress for the Lab and the Open in AssetOps context.

Routes (`evidence_api.py`, ungated):
- `POST /api/ingestion/batches`
- `GET /api/sites/{site_id}/evidence?from=&to=`
- `GET /api/sites/{site_id}/evidence/records?device=&signal=&source=&from=&to=`
- `GET /api/sites/{site_id}/evidence/records/{message_id}`
- `GET /api/ingestion/batches/{batch_id}`
- `GET /api/sites/{site_id}/evidence/rejections` (inspectable rejections)

### D4. Commit lives on the Lab surface (gated), release goes through D2

- Contract-free seal in `simulator_lab_api.py` (allowed to import
  `source_stage`): `seal(view, run)` builds the `CommittedArtifact` from a
  `SourceStageView` only when `view.release_eligible` (AC1: failed/corrupt/
  incomplete/conflicting stage -> 409 `COMMIT_REFUSED` with the blockers).
- `CommittedArtifactStore` port in `backend/assetops_backend/runs/` (gated,
  built in `create_app` only when the gate is open, injectable
  `commit_store=`): `var/commits/{run_id}.json`, written exclusively once
  (`open(..., "x")` then `os.replace` pattern). If one exists, it is read,
  verified and REUSED - never rewritten (AC2). If its stage digest differs
  from the current stage, refuse `COMMIT_STAGE_CHANGED`.
- `POST /api/simulator-lab/runs/{run_id}/commit`: seal-or-reuse, then
  `ingestion.ingest(ingestion_batch(artifact))`, return
  `{commit, release}`; an exception mid-release leaves progress
  `IN_PROGRESS` and the response (or the next GET) says so. Retrying the POST
  resumes the same batch id (AC2, AC6, AC7).
- `GET /api/simulator-lab/runs/{run_id}/commit`: `NOT_COMMITTED` or the
  artifact summary (id, digest, envelope count, sealed_at) plus the release
  progress read from ingestion, kept SEPARATE in the payload (AC18), plus
  `open_in_assetops`: `{site_id, window_start, window_end, batch_id}` built
  from the accepted window, never from the stage.
- Commit writes no evidence itself: only `ingest` does.

### D5. Frontend

- Tab rule + AC23 per the task's anchors (sub-phase 1a).
- Lab run screen: a Commit panel beside the stage inspector: Commit button
  (disabled with the stage's release blockers named when ineligible - a
  built capability not currently eligible), then commit and release shown as
  two separate facts (accepted / duplicates / rejected / conflicts,
  processed of total, status), a Retry release when `IN_PROGRESS`, and an
  "Open in AssetOps" link to
  `/sites/{siteId}/evidence?from=..&to=..&batch=..`.
- Site > Evidence route `/sites/:siteId/evidence` (operator, ungated):
  window line; Source health table; Signal coverage table (with coverage-gap
  rows named); Configuration and mapping basis; Rejections (count + list);
  the record inspector as a drill-down opened from a source or signal row
  (an in-page panel/drawer under the same root: the URL may gain
  `?record=` / `?signal=` but the Site root and tab do not change). Inspector
  shows AC12 fields and the three timestamps labelled Source time /
  Published / Received.
- Settle store reads with `settledScreen`; add the new loading sentences to
  `frontend/src/test/settled.ts`.

## Sub-phases (sequential, one agent at a time, each commits)

- **1a** tab rule + AC23 (frontend + `navigation-truthfulness.ps1` + layout
  script `/` visit). Mechanical.
- **1b** contracts (D1, D2) + backend evidence package (D3) + commit route
  and store (D4) + dependency guard + backend tests. Tests: commit once;
  ineligible refused; artifact immutable + reuse; resume after injected
  interruption; duplicate idempotent across a fresh service/store instance
  (restart); conflict preserves original; bad unit / bad mapping / private
  field rejected and inspectable while valid records accepted; three
  timestamps distinct; gate off -> evidence routes 200, lab routes 404;
  rebuild into empty derived store equals original excluding received_at;
  Foundation edit does not change accepted basis.
- **1c** host integration tests (real Kobo profile-5 degraded run -> stage ->
  commit -> evidence; delayed publication shows three distinct timestamps;
  rebuild from `var/commits` text alone with no executions/stages dirs) +
  frontend Commit panel + Site > Evidence + inspector + tests.
- **1d** full checks serially, layout evidence (`/` redirect, Evidence
  populated and empty), phase 1 packet, handoff, CODE_STATE/ACTIVE_CONTEXT.

## Frontend anchors (survey, 2026-10-02; paths under `frontend/src/`)

- Tabs: `shell/operatorSiteTabs.tsx` types :56-69, `OPERATOR_SITE_TABS` :80-89
  (Evidence entry exists at :88 as `labelled_in_place`), `labelledAspectsSentence`
  :126-148, `COUNT_WORDS` :157, `firstLabelledIndex` :176, render :193-233, doc
  comment :23-44. Consumers `shell/SiteDetailFrame.tsx:84`,
  `shell/SiteFoundationFrame.tsx:83`. Routes `shell/operatorSiteRoutes.ts:35,45,50,58`;
  `App.tsx:121-177` (`/` at :124, catch-all :176, Lab routes :162-175).
- Foundation subtabs: `sites/FoundationSubtabs.tsx` :55-58 kind, :73-78 list
  (Readiness :77), :98 absent span, :104-107 note, doc :1-44; consumer
  `sites/SiteConfiguration.tsx:262`.
- Rail: `shell/OperatorShellLayout.tsx:33-36` (`Operator home` :34), NavRail
  `ui/NavRail.tsx:16-38`; placeholder `shell/OperatorShellFrame.tsx:21-38`.
- Pinned tests: "Operator home" in `shell/__tests__/operatorRouteFrames.test.tsx:189`,
  `simulatorLabWorkspaceEntryPoint.test.tsx:46`, `siteDetailRoute.test.tsx:98`,
  `siteFoundationRoute.test.tsx:111,118`, `sitesIndexRoute.test.tsx:51`;
  labelled tabs `shell/__tests__/operatorSiteTabs.test.tsx` (many), 
  `sites/__tests__/foundationScreen.test.tsx` :35,253,274,382,391-411,728-737;
  `ui/__tests__/overflowContainment.test.tsx:239`.
- Comments: `shell/simulatorLabRoutes.tsx`, `ui/DataTable.tsx:24-27`.
- Layout script `tools/layout-evidence.mjs`: `/` visit :1270-1278; Site tabs
  `tabLabels.length === 8` at :1250 (becomes 3); tabs query :450-457.
- Check `tools/checks/navigation-truthfulness.ps1`: messages :220, :316, :333.
  No Pester tests exist for it; "its tests" = the frontend tests above plus a
  non-vacuity proof recorded in the packet.
- Lab run screen `shell/RunFrame.tsx` (1639 lines): stage state :205,
  `rereadStage` :231-236, `getStage` :366/:422, stage Disclosure :1115,
  "Release eligibility" Fact :1169-1180 ("Commit and ingestion do not exist
  yet" - must change), blockers :1219, "not committed" copy :705-709, comment
  :1120-1124. Client `shell/runSetupClient.ts`: interface :709-751 (`getStage`
  :737), `RunStageResult` :698-701, impl :1548-1575, POST helper
  `executionRequest` :1594-1654, factory :1370.
- Operator client pattern: `sites/siteDirectoryClient.ts` (`SITES_API_PATH`
  :24, factory :340); clients injected via `AppProps` `App.tsx:88-100`.
  Feature flags `config/featureFlags.ts:21-30`, `featureFlagsWith()` for tests.
  `test/settled.ts` LOADING regex :17-18.
