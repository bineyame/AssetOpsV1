> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 5 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## T027 phase 1 - Commit, ingestion and Site > Evidence

Packet `archive/agent-history/T027-phase-1-review-packet.md`; handoff `archive/agent-history/T027-phase-1-handoff.md`.
In review (phase 1); phase 2 (Overview, AC11, AC22) not started.

- Commit: a release-eligible stage seals once into `var/commits` (contracts
  `committed_artifact.py`; `runs/adapters/json_commit_store.py`); a filed artifact
  is never rewritten, a changed stage is refused, a tampered one reads unreadable.
  `RUN_COMMIT_ROUTE` exists only when the Lab gate is open.
- Release goes through the one product ingest (`evidence/service.py`,
  `ingestion_batch.py`); `received_at` is ingestion's; duplicates idempotent,
  same id/other content a conflict keeping the original, reused batch id with
  other content `BATCH_ID_CONFLICT`; an unknown-Site batch is refused, not stored.
  Store: `var/evidence`, one JSON per Site rewritten per 64-record chunk,
  single-process lock.
- Read model `evidence/read_model.py`: accepted content only; coverage over
  `NEEDED_SIGNALS` keyed by `site_type` (MINIGRID); routes `evidence_api.py`,
  served gate open or closed. Rebuild from artifact text matches (in-process).
- UI: Site > Evidence (`sites/SiteEvidence.tsx`; inspector state in
  `?signal=`/`?source=` + `&record=`; `?batch=` only highlights). Lab
  `RunCommitPanel.tsx` keeps Commit and release apart; Open in AssetOps ->
  `/sites/{id}/evidence`.
- Tabs per `D-2026-10-02-rendered-tabs-per-capability`: Overview|Foundation|Evidence,
  Definition|Topology|Controls; `/` -> `/sites`; rail Sites only.
- Checks: evidence dependency rule (`dependency-direction.ps1`), evidence and
  commit domains (`configuration-persistence.ps1`), navigation-truthfulness
  messages "not rendered, never disabled, never labelled in place"; all proven
  by mutation (no Pester tests for navigation-truthfulness).
- Layout evidence needs T026's isolated method (packet); 3 "blocked table" and
  the T025e delta-budget claims fail for environment reasons.
- Open: AC15 rebuild not proven without host/simulator on `sys.path`; the
  profile-5 run stages no fuel-level envelopes (Fuel NOT_REPORTED).

## T028 - Dispatch Finding and Evidence capability table

In review (independent review and owner UI walk pending). Packet
`archive/agent-history/T028-review-packet.md`; handoffs `.agent/T028-phase-{1,2,3a}-handoff.md`,
`.agent/T028-presentation-cp{1,2a}-handoff.md`; final layout evidence
`.agent/T028-layout-evidence-final.txt` (presentation cp2b).

- Analytic `analytics/dispatch.py` (model `dispatch-2`, `assess()`); rules and
  thresholds in `backend/tests/dispatch_decision_table.md`. Classification uses
  accepted evidence only; never observed PV as capability, never simulator truth.
  Fix round 1 (Codex R1-R5, `archive/agent-history/T028-review-packet.md` "Fix round 1"):
  segments split at constraint-record effective times between reports; 5b
  enforces SOC headroom; equal-rank differing policy/override records are
  classified under each (agree or Indeterminate); evidence digest covers
  bounds, alternatives and fuel basis; reconcile also compares the payload.
- `AssessmentService` (`analytics/service.py`) reconciles assessments: same
  evidence gives no new revision; changed evidence appends a revision and keeps
  the prior; stored under `var/assessments` (`json_assessment_store.py`). Runs on
  ingestion completion (listener in `evidence/service.py`) and on read. Evidence
  never imports analytics (card assessments are injected into `overview.py`).
- Routes (`analytics_api.py`, ungated): `/api/sites/{id}/analytics` (declaration
  with per-analytic `readiness`), `/dispatch`, `/findings`,
  `/assessments/{aid}`, `/assessments/{aid}/revisions`, and global `GET /api/findings`.
- Declaration (`analytics/declaration.py`): id, site types, Finding type, required
  and optional evidence, claim levels, `readiness` basis (`readiness-3`; `-2` made None need neither generator status nor output, `-3` counts unobserved generator-state spans as a limiting gap).
  `score_readiness`: Full/Limited/None, ceiling, missing evidence. A coverage gap
  lowers Full only when it left a segment Indeterminate; absent optional evidence
  is listed and never lowers it. Site-wide, not the selected window.
- Guard `tools/checks/analytic-declaration.ps1` (declaration fields incl.
  `readiness`; no `EXECUTION_REQUIREMENTS` or simulator reads); dependency rule
  (evidence may not import analytics); persistence domain for analytics;
  `navigation-truthfulness.ps1` rail rule is two grouped items. Probes proven.
- Frontend: Performance > Dispatch (only subtab), Finding detail
  `Overview | Evidence | Alternatives` with `ClaimDrawer` reusing T027
  `RecordDetail` (`?record=&claim=`, root unchanged), Findings rail root,
  Site > Findings, `CapabilityReadiness.tsx` above source health. Rail groups via
  `ui/NavRail.tsx` `group`. Presentation profile (`presentationProfile.ts`,
  `presentationProfiles.json` `capabilities`, `performanceSubtabs`,
  `finding_types`) obeys the three rules; orphan lists `EXPECTED_ORPHANS`,
  `EXPECTED_ORPHAN_FINDING_TYPES` in `test_t028_presentation_profile.py`.
- Owner rulings 2026-10-03: Necessary intervals stay assessments without a
  Finding; stop-60 gets no policy record (T034).
- Presentation correction (`D-2026-10-04-practitioner-first-finding-presentation`,
  packet "Presentation correction"): `dispatch.reading()` (meaning, next steps
  with targets, framing) is served at read time on every lineage summary, never
  persisted (adds no revision); readiness carries `question`/`meaning`/`scope`.
  Frontend leads with plain six-part headings, readable UTC periods
  (`readablePeriod`), and puts IDs/revisions/digest, full coverage, fuel inputs,
  Performance method and readiness scoring behind closed `Disclosure`s.
- Totals at closeout: backend 1465, host 616, simulator 244, frontend 1097.
- Presentation revision cp1 (`D-2026-10-04-plain-language-analysis-views`,
  supersedes the disclosure layout above; packet "Presentation checkpoint 1"):
  `analytics/plain.py` generates every product sentence at read time from the
  stored structured assessment (`reading`, `card`, `readiness`, `role`); old
  `dispatch.reading`/`CLAIM_MEANINGS` removed. Finding tabs
  `Overview | Analysis | Evidence | Alternatives` (`/analysis`); Dispatch and
  Site Evidence local `Overview | Analysis` (`?view=analysis`, other params
  kept); shared `sites/assessmentAnalysis.tsx`; card and index "View analysis".
- Presentation cp2a (packet "Presentation checkpoint 2a"): four graphics in
  `sites/assessmentGraphics.tsx` (assessed-period timeline full/compact, fuel
  range, reported values for a selected part `?part=N`, coverage by input),
  region `.assessment-graphic` named in `shell-overflow.ps1`; card
  `lead_timeline`/`lead_revision` from `plain.card_timeline`; Site Evidence
  `?view=analysis&assessment=<id>` one-period coverage, apart from readiness.
- Presentation cp2b (packet "Presentation checkpoint 2b"): vocabulary guard -
  list `frontend/src/test/productVocabulary.json` (v1), scanner
  `productVocabulary.ts`, suite `shell/__tests__/t028Vocabulary.test.tsx`
  (29 Lab-off + 2 Lab-on states), exemptions only `data-vocabulary-exempt=
  source-reference|user-owned|lab` on single values; live scan `t028Journey`
  in `tools/layout-evidence.mjs` (`ASSETOPS_LAYOUT_T028_JOURNEY_ONLY=1` runs
  it alone, Lab-off); backend test scans served evidence statements and
  rejection reasons against the same list. Read-time rejection `reason`
  (`evidence/read_model.py` `REJECTION_READINGS`; stored detail unchanged);
  plain `NORMALIZATION_STATEMENT`, `INTERVAL_STATEMENT`; source mode label
  "Demonstration data". Layout evidence `.agent/T028-layout-evidence-final.txt`
  (615 PASS, 4 known FAIL) and `-lab-off.txt` (4 PASS).
  Exclusions also by value: `data-vocabulary-reference` (`sites/vocabularyReference.ts`).

### What this leaves open

- Owner decisions: any-gap vs limiting-gap readiness rule; site-wide vs selected
  window readiness.
- Overview shows whole-interval generator runtime beside a different-basis
  assessment (backlog item stays open for the metric).
- `GET /api/findings` and `/analytics` run `assess_site` per Site on read.
- Ingestion keeps the first record at a key, so same-key recipe re-runs do not
  revise intervals.
- Recommendation and History tabs, verification rules: T034.
- Legacy product copy outside the T028 journey (Foundation, Sites index
  filters, other pages) is not scanned by the vocabulary guard: post-T029
  inventory follow-up. `INPUT_WORDS` coverage labels are still a frontend map.
- Persisted `summary`/claim-limit wording unchanged by the presentation
  correction (Necessary "4.5-open", `(dispatch-2)` in the Candidate limit);
  rewording them appends a revision per lineage.

## S2-02 - Authenticated ingestion and Site Evidence (in review)

Packet `archive/agent-history/S2-02-review-packet.md`; walkthrough `archive/agent-history/S2-02-owner-walkthrough.md`; handoffs `.agent/S2-02-phase-{1,2,3a,3a2,3b}-handoff.md`, `archive/agent-history/S2-02-corrections-handoff.md`.

- Postgres ledger (migrations 0005/0006): `ingestion_batch`, `accepted_evidence`, `evidence_rejection`, `ingestion_disposition`, `batch_refusal`, `recompute_job` (`dispatch` domain); `gateway_credential` (selector + SHA-256 verifier), `gateway_access_event`, `gateway_diagnostic`(+refusal). Three confined writers (guard `tools/checks/configuration-persistence.ps1`).
- Ingestion: `evidence/ledger_service.py` `BatchIngestionService.submit` (413/422/403/409/202/200, per-chunk transactions, first-receipt `received_at`); Receipt V2 contract `contracts/assetops_contracts/ingestion_receipt_v2.py`.
- Credential: `provision_gateway issue` writes `<credential-out>.<selector>` owner-only (DACL/0600) and verifies it BEFORE one DB transaction (verifier, revocation, enablement); gateway `read_upload_credential` re-checks the DACL. Rotation = new file + gateway config switch + restart.
- Transport: `python -m assetops_backend.serve_tls` (426 on plaintext credentialed routes); gateway `uploader.py` bounded passes, exact bytes, receipt verification before ACK; IPC `deliver`, `release_run`, `run_delivery`.
- Reads: `evidence/ledger_reads.py` + four Site Evidence routes for imported Sites behind `permits_cutover` (schema v2 report bound to tenant/Site/environment/inventory digest, newest report decides, `var/evidence/migration/<site>/`); CLI `python -m assetops_backend.evidence_migration run|show`. `GET /api/sites/{id}/gateway-health` UNKNOWN/CURRENT(2x cadence)/STALE.
- Frontend: `sites/LedgerSiteEvidence.tsx` (overview/analysis/inspector/reading detail), `shell/RegisteredDeliveryView.tsx` (Commit release claim, batch table, blockers).
- Demo: `tools/s2_demo_walkthrough.py run|serve` (isolated `git archive` tree under `%LOCALAPPDATA%\AssetOps\s2-demo`, DB `assetops_s2demo`, API 8610, TLS 8643, new openssl cert). Layout: `ASSETOPS_LAYOUT_S2_02_RUN=<run> ASSETOPS_LAYOUT_S2_02_RECORD=<evidence id> node tools/layout-evidence.mjs <base>`.
- Dev DB KOBO-001 comparison regenerated 2026-10-09 (schema v3, empty set, PASSED).
- S2-01c carries closed here: N1, N3, C2.
- Fix round 1 (review F1, Architect batch 4 Q28/Q26/Q32/count): forwarded scheme headers -> 426 and `serve_tls` `proxy_headers=False`; `provision_gateway` reconciles an ambiguous issue COMMIT via `PostgresGatewayAccess.issue_outcome` (ISSUED / proven NOT_ISSUED / `ISSUE_OUTCOME_UNKNOWN` exit 3, file kept); comparison report schema v3 binds `store_root` (digest of adapters' `canonical_root()`), checked in `permits_cutover` and by the configuration-persistence guard; walkthrough step 8b posts a labelled fault-fixture sibling batch, step 5 prints the post-run batch (245/292 -> 246/293 = profile-v2 delayed 15:00 battery SOC report).

### Open

- Questions-7 (Q37-Q40) await the Architect (fail-closed defaults shipped); questions-5/6 answered in `archive/agent-history/architect-batch-answers-4.md`.
- C3/N2 full seeded layout run still unverified.
- Crash/resume 202 and closing-boundary rejection are Postgres test evidence only; the rejected sibling is live via the labelled fault fixture.
- Generator-status run and capability channels unconfigured; no S3 projection; physical devices remain a pilot gate.

## S3-01 phase 1 - Role vocabulary and `s3-dispatch-cases-v1` fixture (reviewed, accepted with carries)

Built on `task/S3-01-dispatch-assessment` (1a `e68da1c`, 1b `7e9da8c`..`f508bae`); packet `archive/agent-history/S3-01-phase-1-review-packet.md`, questions `archive/agent-history/S3-01-questions-1.md`.

### What it settled in code

- `sites/binding_roles.py`: `minigrid-roles-2` = roles-1 + optional `pv_available_power` (INVERTER) and `pcs_discharge_capability` (POWER_CONVERSION_SYSTEM), kW, ONE. MINIGRID publishes roles-2 and still serves roles-1; `BindingService.publish(role_set=)` refuses an unserved set; the replayed Kobo conversion records roles-1.
- `FoundationService.publish_component_properties` (no API route) and `sites/demo_configuration.py` (CLI `python -m assetops_backend.sites.demo_configuration --fixture backend/conversions/kobo-001-s3-dispatch-demo-config.json --tenant demo [--steps properties]`): labelled SIMULATED demo configuration - generator rated power/start 35/stop 90/start-delay 5 (TEMPLATE v2) from 2026-10-01, roles-2 bindings with both declared capability channels from 2026-10-02. Idempotent; earlier periods split, never rewritten.
- `runs/profiles.py` `registered-kobo-publication` v3: v2 + generator status (STATE_SIGNAL), generator power at 15 min, both capability signals at resolution 0.000001, discharge-capability reporting gap; `record_channels=()`. v1/v2 unchanged.
- The Lab publishes a declared signal only where the frozen basis maps it (`host/execution_adapter.py:690-705`), so on a roles-1 basis capability readings never exist on the public path (not a gateway hold).
- Scenario `config/scenarios/kobo-s3-dispatch-degraded-reporting.yaml` v1 (prolonged world, 1 h discharge-capability gap, 10-min SOC hold, no override/record); fingerprint pinned.
- `tools/s3_dispatch_cases.py run|verify` (reuses S2 `Demo`; DB `assetops_s3cases`, ports 8710/8743, own pipe): 8 cases, 2868 accepted readings; manifest with public IDs only, Lab run IDs under `private_oracle`; `verify` reloads accepted IDs from Postgres and fails on any mismatch or unmet precondition. Run output `.agent/S3-01-dispatch-cases-run.txt`, manifest copy `.agent/S3-01-dispatch-cases-v1.manifest.json`.
- Registry `I-sim-dispatch-cases` has an `acceptance_target`; status stays `open` (tied to `I-S3-01`).

### Open

- No analytic, `EvidenceQuery`, cohort selection or persistence yet (phase 2); no UI (phase 3).
- Q1-Q6 unanswered: contradiction is a labelled fault-fixture batch; poor quality = UNAVAILABLE readings + gap (no SUSPECT); same-epoch overlap is ambiguous by construction; the ordinary path produces late but not out-of-order-within-source readings; `fuel_level` is not published by `mini-grid` v3 registered runs.
- Any Foundation-UI binding edit on a MINIGRID Site now records roles-2 (risk noted in packet).
- The manifest's IDs are environment-specific (fresh import UUIDs per run); replay regenerates, `verify` compares within one environment.

## S3-01 phase 2 - Typed seam and durable dispatch assessment (active, phase review pending)

Built on `task/S3-01-dispatch-assessment` (`75886d1`..HEAD); packet `archive/agent-history/S3-01-phase-2-review-packet.md`, questions `archive/agent-history/S3-01-questions-2.md`, table `backend/tests/dispatch_3_decision_table.md`.

### What it settled in code

- `analytics/assessment_inputs.py`: `EvidenceQuery` (tenant/Site/domain, UTC half-open `Window`, `knowledge_at`, optional explicit cohort, roles, 6 h `BRACKET`), `AcceptedReading`, `RoleBinding`, `ControlValue`, `EvidenceQueryResult`, `CohortSelection`/`CohortLimit`, `AnalyticInputSet` with canonical `input_sha256` (evidence IDs + digests, cohort, as-accepted and selected revisions, controls, bindings, coverage, window, model; not `knowledge_at`).
- `analytics/cohort.py`: default cohort = streams `(gateway, source, epoch)` with a reading in the window; overlapping epochs of one source -> `AMBIGUOUS`; explicit selection; per-channel `SEQUENCE_ORDER_INVERTED` / `REPORTS_OVERLAP` limits. No epoch-name, manifest or receipt-order logic.
- `analytics/dispatch_v3.py` (`MODEL_VERSION = "dispatch-3"`, reuses `dispatch.ANALYTIC_ID`, no own declaration): pure; window + interval assessments; rows 3/4/5a/5b carried; row 1 unavailable; row 2 = Candidate-blocking minimum runtime only; window `COMPLETE|LIMITED|INDETERMINATE`. `dispatch.py` (`dispatch-2`) untouched.
- Migration `0007_dispatch_assessment`: `analytic_run` (idempotent basis key), `analytic_run_evidence`, `assessment_revision`, `analytic_run_assessment` (all append-only), `recompute_job.last_error`.
- `analytics/adapters/postgres_assessment_store.py`: the fourth product DB writer (guard rule 8 extended: own tables plus `recompute_job` lease/retry/scheduling only). Evidence read joins the ACCEPTED disposition; cutoff on `decided_at`; Foundation/binding selected bitemporally at the cutoff, tenant/Site scoped.
- `analytics/assessment_worker.py` + CLI `python -m assetops_backend.analytics.assess_dispatch process-jobs|reconcile|assess`: lease (SKIP LOCKED, expired leases reclaimed), UTC-day windows over job window +/- bracket, one commit for runs + revisions + DONE under a lease token; retry with back-off, FAILED after 3 with `last_error`; `reconcile` enqueues windows whose latest default run has another model version or configuration digest.
- `tools/s3_dispatch_cases.py`: case `late-out-of-order` renamed `late-publication`; new `out-of-order-fault-fixture` (10-07, labelled epoch) and `late-central-acceptance` (10-08, two batches held at the gateway; cutoff A/B); each case carries its persisted `dispatch-3` result and a check; `verify` reloads runs and the cutoff-A revision.

### Open

- No read API, projection table, UI or Performance cutover (phase 3); phase 3 derives `CURRENT/STALE_PROJECTION/...` from runs + overlapping jobs unless Q7 rules otherwise.
- Questions Q1-Q8 in `archive/agent-history/S3-01-questions-2.md` (controls at cutoff vs as-accepted, minimum runtime mapping, day windows, fixture-epoch default read, in-flight cutoff, interval key anchoring).
- Same-epoch overlap (10-04) yields a window `INDETERMINATE` with no intervals (generator series ambiguous).

## S3-01 phase 3a - Durable dispatch read, comparison and cutover gate (active, phase review pending)

Built on `task/S3-01-dispatch-assessment` (`aaa47ae`..HEAD); packet `archive/agent-history/S3-01-phase-3a-review-packet.md`, questions `archive/agent-history/S3-01-questions-3.md` (Q9-Q13), handoff `archive/agent-history/S3-01-phase-3a-handoff.md`.

### What it settled in code

- `analytics/cohort.py` `_multi_epoch`: two or more epochs of one source in a window make the default cohort `AMBIGUOUS`, overlapping or not (F3).
- `postgres_assessment_store.lease_job(max_attempts)`: an expired lease on its last attempt is `FAILED` with "lease expired on attempt N of M" (F6). Worker `run_pending(reconcile=True)` reconciles every assessed Site (F4).
- Migration `0008_assessment_selection`: append-only `analytic_run_selection` (commit order `seq`), written per DEFAULT run; `run_heads` reads it. Guard rule 8 lists it.
- `analytics/dispatch_v3.py`: a `LIMITED` window always names its limitation; interval limitations are lifted as `INTERVAL_LIMITED: interval from <first_on>: ...` (the necessary-interval open-bound anomaly; Q13).
- `analytics/dispatch_read.py`: `derive_status` (UNASSESSED/PENDING/CURRENT/STALE_PROJECTION/FAILED + reasons) over one REPEATABLE READ `window_snapshot`; `window`/`run`/`revision` with as-accepted revisions, `selection_note`, `CUTOFF_LABEL`, typed `UNAVAILABLE`, `superseded_keys`, demo annotations kept apart from provenance (`adapters/demo_manifest_file.py`, env `ASSETOPS_DEMO_FIXTURE_MANIFEST`).
- `performance_api.py` (mounted in `main.py`): `/api/sites/{code}/performance/dispatch/cutover` always; `windows/{day}`, `runs/{id}`, `revisions/{id}` 409 `PERFORMANCE_CUTOVER_CLOSED` until the gate opens, 404 unknown/foreign, 503 store unavailable.
- `analytics/performance_comparison.py` + CLI `python -m assetops_backend.performance_migration run|show`: MATCH / INTENTIONAL_DELTA / MISSING_SOURCE / UNPROVEN; gate opens only on PASSED, current legacy digest, same tenant/Site/environment, zero live lineage breaks. Reports under `<EVIDENCE_STORE_ROOT>/migration-performance/<site>/`.
- Fixture: case `necessary-interval` (scenario `kobo-s3-dispatch-necessary-run` v1, 10-09); fault-fixture SOC template chosen by minimum `(source_time, sequence)`.

### Open

- No UI yet (phase 3b): `SitePerformance.tsx` `DispatchView` still reads the file-backed `/dispatch`; anchors in the 3a handoff.
- Q9-Q13 resolved by `D-2026-10-11-s3-phase-3a-version-and-cutover`; built as `dispatch-3.1` (next entry).
- A window read evaluates the full input basis per request; `run_pending` reconciles every assessed Site per pass.

## S3-01 dispatch-3.1 - Model version bump, stored-window reassessment, stricter comparison (active, review pending)

Built on `task/S3-01-dispatch-assessment` (`05f9b4d`..HEAD) under `D-2026-10-11-s3-phase-3a-version-and-cutover`. Packet: the "dispatch-3.1" section of `archive/agent-history/S3-01-phase-3a-review-packet.md`. Handoff to 3b: `archive/agent-history/S3-01-dispatch-3-1-handoff.md`. Questions: `archive/agent-history/S3-01-questions-4.md` (Q14-Q16).

### What it settled in code

- `dispatch_v3.MODEL_VERSION = "dispatch-3.1"` covers Q9 and Q13. Stored `dispatch-3` runs and revisions are immutable history. The worker reconcile, already keyed on `model_version`, reassesses their windows; `assess_dispatch process-jobs` runs it. Explicit selections are not remapped.
- `dispatch_read`: `run` and `revision` carry `model_note` (`OLDER_RULE_RESULT ...` for a non-current model); a `dispatch-3` head reads `STALE_PROJECTION` with `MODEL_VERSION_CHANGED`.
- `postgres_assessment_store`:
  - `lineage_breaks(..., model_version)` counts `selected_heads_other_model`;
  - `accepted_evidence` maps a message ID to its evidence ID;
  - `selected_intervals(..., domain, bracket)` adds the overlapping `window_jobs`.
- `performance_comparison` (report schema v2, which records `model_version`):
  - `STALE_MODEL` and `STALE_PROJECTION` are `UNPROVEN`.
  - `MATCH` and `INTENTIONAL_DELTA` need the cited records in the interval's evidence.
  - `INTENTIONAL_DELTA` applies only through `DOCUMENTED_DELTAS` (`CAPABILITY_CHANNELS_REQUIRED`, rows 5a/5b), and only on the interval's own limitation.
  - `MISSING_SOURCE` gives `EXCEPTIONS`, which keeps the gate closed.
  - The gate refuses a report made under another model, and refuses while any head uses another model.
- The cutover route's read label is now `POSTGRES_DISPATCH_3_1`. The decision table has "Model versions" and "Comparison" sections.

### Open

- Phase 3b UI. Its required displays are listed in the handoff, and the cutover route does not yet expose the report summary.
- Q14-Q16 are open, with fail-closed defaults built.

## S3-01 phase 3b - Performance > Dispatch UI, cutover summary, walkthrough (in review)

Built on `task/S3-01-dispatch-assessment` (`b04b904`..closeout). Packet: `archive/agent-history/S3-01-review-packet.md`; questions Q17-Q22 in `archive/agent-history/S3-01-questions-5.md`.

### What it settled in code

- `performance_comparison.comparison_summary` and `classified_revision_ids`. `permits_performance_cutover(..., selected_revision_ids=)` refuses when a classified MATCH or INTENTIONAL_DELTA revision is no longer selected or the selection is unreadable (R2). An empty-set report needs no recheck.
- The cutover route returns `comparison`. File-store errors give a 503 with a closed body (`read: CLOSED`, `permitted: false`, `unavailable.code` COMPARISON_STORE_UNAVAILABLE or ASSESSMENT_STORE_UNAVAILABLE) (R3). `main.py` wires the live `selected_intervals`.
- Frontend: `sites/PerformanceDispatch.tsx` (Overview and Analysis views), `performanceDispatchClient.ts`, `dispatchWords.ts`; `SitePerformance.tsx` renders it when the legacy declaration is AWAITING_EVIDENCE_MIGRATION. Address state `?day=&revision=&block=&view=`. Without `?day=` the screen opens on today UTC.
- Fuel, money and Finding panels are gated and typed unavailable. Demo annotations are shown apart from provenance.
- `tools/s3_dispatch_walkthrough.py` (prepare/serve/recover; private DB `assetops_s3walk`, port 8820) and `tools/s3-dispatch-evidence.mjs` (32 claims at 1440 and 390).
- Comparison recovery test closes R1-C1.

### Open

- No list of assessed days; older-rule label and late-evidence history proven by tests only; demo notes absent from walkthrough data; staged FAILED/STALE days have no interval.
- Carries: R1-C2, 3a R4/R5. Committed fixture manifest is per run (evidence IDs change on a new producer run).
- Owner checkpoint pending.

## S4-05a - immutable source binding and exact-revision resolver (built, in_review)

Branch `task/S4-05a-provenance-binding-resolver` from main `fd7afd2c`. Handoffs `archive/agent-history/S4-05a-phase-1-handoff.md`, `archive/agent-history/S4-05a-phase-2-handoff.md` (resolver field contract for S4-05b); packet `archive/agent-history/S4-05a-review-packet.md`. Authority `D-2026-10-15-s405-stored-demo-provenance`, `archive/agent-history/architect-S4-05-answers.md`.

- Migration `0017_evidence_publication`: insert-only `evidence_publication` (SYSTEM actor, class CHECK: authored fixture ID+version or run ID+64-hex run digest) and `batch_publication_link` (composite FKs to the exact batch and publication commitment); UPDATE/DELETE triggers; downgrade refuses while publications exist (tested).
- Ledger writer (`postgres_evidence_ledger.py`) is the only provenance writer: `register_publication` and `open_batch` share `pg_advisory_xact_lock` on (tenant, Site, external batch ID); registration refuses after any admission, needs a registered gateway/source and (phase-1 review M1) a `SIMULATED` gateway for every class; `open_batch` binds the exact commitment or refuses 409 `PUBLICATION_MISMATCH`. Unpublished uploads stay accepted and unbound.
- Domain `evidence/publication.py` (authored records, run attestation), `runs/source_publication.py`, server CLI `publish_source.py`; no HTTP route.
- Resolver `evidence/source_provenance.py` (pure, route-safe) + read-only ledger methods `link_rows`, `finding_revision_evidence`, `consequence_inputs`; `composition.build_source_provenance`. FindingRevision cited set; consequence = union of its FindingRevision set and its own power-interval IDs, with `finding_revision_state` and `CONSEQUENCE_POWER_INPUT_CONFLICT`. Several run IDs -> MIXED (N-L2). Missing/foreign-Site/broken precede MIXED. Cross-tenant IDs read as not found (no disclosure).
- Rule 8 (`configuration-persistence.ps1`): ledger INSERT-only provenance; split `UPDATE|DELETE FROM|TRUNCATE <provenance table>` refused in any module (review L1); HTTP modules may not reference designation.
- Not changed: every read DTO and the date/spec source heuristic (S4-05b cuts over).
- Open: N-L1 producer registration in a non-route module (S4-05b); migration re-chain vs LR-01/S6-01a; run identity digest is not re-verified after registration (file-backed run store); lock key is the admission slot, stricter than the packet wording; no TRUNCATE trigger (rule 8 only); S5-01 amendment (N-L3).
## S4-07 - evidence decided_at on DB time (built, review pending)

Branch `task/S4-07-evidence-decided-at` from main `5bfff665`; packet `archive/agent-history/S4-07-review-packet.md`.

- `PostgresEvidenceLedger.decide_chunk` takes one DB `clock_timestamp()` per chunk after the batch row lock (`_decision_instant`), inside the write transaction; it stamps every newly decided ordinal's `decided_at` and a newly inserted `recompute_job`'s `available_at`/`created_at`. A widened PENDING job keeps `created_at` and has `available_at` lifted to `GREATEST(available_at, decision)` (Known Deviation 1; closes the cutoff-sampled-before-commit race, proved failing without it).
- `EvidenceLedger.decide_chunk(..., completed_at=)` replaces `decided_at=`: `BatchIngestionService` passes its app clock only for the receipt `completed_at`; `received_at` unchanged.
- `test_decision_clock_override` (constructor kwarg/attribute) is test-only; `main.py`/`evidence/composition.py` never set it. Deterministic fixtures (S2 ledger/site evidence, S3 dispatch, S4 CaseRunner, S4 consequence work) use it.
- Proofs: `tests/test_s4_evidence_decided_at_postgres.py` (production path, fast/slow app clocks: ingestion-first, worker-first with L-b lock wait, cutoff-sampled race, uncommitted-job tick; crash/replay across two windows, duplicate-only chunk, another Site). F-A test re-driven as override-path, skew 120 s (R-2).
- Open: manual app-clock `process-jobs` beside the tick (README-db); configuration `recorded_at` vs `reconcile`; `clock_timestamp()` vs `now()` (an instant predating a batch-lock wait) is reasoned, not mutation-proved (no batch-lock contention test).
## LR-01 - late-reading series and money limit (phases 1-2 built, slice review pending)

Branch `task/LR-01-late-reading-series-and-money-limit`; handoffs `archive/agent-history/LR-01-phase-1-handoff.md`, `archive/agent-history/LR-01-phase-2-handoff.md`; packet `archive/agent-history/LR-01-review-packet.md`; decision `D-2026-10-15-lr01-source-time-cohort`.

- Clock attestation: append-only `source_clock_attestation` (migration 0014), SYSTEM-only CLI `assetops_backend.record_clock_attestation`, `SIMULATED` proof class only; attestation change requeues old+new validity (`postgres_assessment_store.record_clock_attestation`).
- cohort-4 / `dispatch-3.2`: source-time order only under one covering attestation (`analytics/cohort.py`); a reading's clock reason depends only on attestations touching it (phase-1 review F1); overlap checks span attestation boundaries (L1).
- Matcher `finding-episode-3` (`analytics/finding_episode.py`): `claim.end_reason` (`OFF_OBSERVED|CANDIDATE_ENDED|OPEN_BOUND|SERIES_LIMIT`) and `claim.series_limits` with exact lineage; a cut tail drops its dependent `OPEN_BOUND`.
- Shared money gate `financials/money_eligibility.py` (`money-eligibility-1`): PENDING_REASSESSMENT > WITHHELD_GENERATOR_SERIES > ELIGIBLE, read-derived on every read, fails closed. Consumed by `ConsequenceReadService(eligibility=...)` (gates `presented_as_current`/`current_amount_shown`), `finding_api.bridge_consequence` (states + `recorded_consequence_revision_id`), and `scheduling/upstream.py` `findings[].money_eligibility` for S5-01. ELIGIBLE is not an amount authorization.
- Migration 0015 `0015_finding_returning_basis`: FindingRevision basis may return (A -> B -> A); replay guard compares with the latest revision only.
- UI: Financials bridge shows withheld/pending with the refused span and an exact link to the recorded consequence; Finding page states a SERIES_LIMIT end.
- Walkthrough: `tools/s402c_late_power_walkthrough.py run|attest|tick|serve|drop --db assetops_lr01*`; browser claims `archive/tools/lr01-money-evidence.mjs`.
- Open: real-source clock proof has no write path (by design); S5-01 owns its own UI over the seam; the schedule install gate stays closed until this slice is reviewed and merged; broader per-analytic input/clock coverage remains the owner analysis-input backlog.

## S4-05b - registered producers, stored-source reads and owner walkthrough (phases 1-2 built, in_review)

Branch `task/S4-05b-producers-reads-walkthrough` (unmerged; owner W1 copy checkpoint first). Packet
`archive/agent-history/S4-05b-review-packet.md`; owner steps `archive/agent-history/S4-05b-owner-walkthrough.md`; ruling D-2026-10-16-s405b-label
(`archive/agent-history/architect-S4-05b-answers.md`).

- Producers: `tools/s4_finding_cases.py` `publish_authored`/`post(fixture=)` publish each exact batch before upload
  (P01/P02); Lab Commit registers the whole sealed Stage first (`runs/registered_release.py` `publisher_for`, wired in
  `host/lab_app.py`); any Stage status outside STAGED/NOT_STAGED/HELD -> `SOURCE_PUBLICATION_REFUSED`
  (`STAGE_NOT_ATTESTABLE`), nothing released; Lab shows the refusal (`RunCommitPanel`).
- Reads: `evidence/provenance_read.py` (`source_gate`, `permits_current_money`, `MIXED_OR_UNKNOWN_SOURCE`) feeds
  `financials/consequence_read.py`, `finding_api.py` `bridge_consequence`, `site_overview/read.py`
  (`source_provenance`, `source_gate`, `withheld_reasons`) and `actions/service.py` (pinned origin revision; unwired
  or failing -> UNKNOWN). `demonstration_label.py` deleted.
- UI: `frontend/src/sites/sourceProvenance.tsx` (`SOURCE_WORDS` per ruling; unknown states -> UNKNOWN), used by
  Finding, Evidence, consequence/Financials, Overview, Action, Recommendation; marker `[data-source-provenance]`.
- Pilot install gate (`tools/schedule-install-gate.py`) always requires `I-attested-real-source-provenance`.
- Walkthrough `tools/s405_provenance_walkthrough.py` (DBs `assetops_s405_{owner,old,mixed}<suffix>`, work
  `var/s405_*`, API 8935/web 5435, `serve --case`); browser claims `archive/tools/s405-provenance-evidence.mjs`.
- S5-01 packet amended (shared contract item 5).
- Open: owner copy approval; `ATTESTED_REAL_SOURCE` class (separate task); `MoneyInputs.provenance_resolved`
  default True for unit tests; per-row provenance queries in consequence history; Action fixture size.
## S3-02a - selected-assessment capability and claim-limit read (built, slice review pending)

Branch `task/S3-02a-capability-read` (base main `71009bf6`, unmerged); packet `archive/agent-history/S3-02a-review-packet.md`; S3-02b handoff `archive/agent-history/S3-02a-handoff.md`. No migration.

- Read: `analytics/claim_limit_read.py` `ClaimLimitReadService.read(tenant, site, day, revision_id, rule)`, rule `s3-claim-limit-1` over `dispatch-3.2` only (`SUPPORTED_MODELS`). Capability = per required role (`generator_state`, `feeder_demand`, `pv_available_power`, `pcs_discharge_capability`, `battery_soc`) exact COVERED/MISSING/POOR_QUALITY/CONFLICTED/NOT_EVALUATED spans with minutes and pinned accepted Evidence IDs, derived from the revision's stored segments (unknown problem text fails closed to MISSING). Claim limit: interval ceiling CANDIDATE_AVOIDABLE/NECESSARY (COMPLETE or LIMITED, `supported_minutes` = that class's segment sum) or INDETERMINATE; withheld (INDETERMINATE) on unusable cohort or a non-covered required role inside a claim-carrying segment. Current ceiling only when the window projection is CURRENT and the revision is in the selected run; otherwise `currentness` PENDING/FAILED/STALE_PROJECTION/HISTORICAL and only `historical_ceiling`. No revision -> `UNASSESSED` + `NO_REVISION_SELECTED`. Window revisions list `interval_ceilings (top level only when CURRENT; otherwise under historical_ceiling)`, no single ceiling.
- Store: `PostgresAssessmentStore.claim_limit_snapshot` reads the window snapshot and the revision detail in one REPEATABLE READ snapshot (`_window`, `_revision_detail` extracted; existing methods unchanged in behaviour). Reads only; no new SQL writer.
- Route: `claim_limit_api.py` `GET /api/sites/{code}/performance/dispatch/windows/{day}/claim-limit?revision=&rule=`; order access 401/403 -> scope 404 -> 503 -> 422 (`INVALID_REVISION_ID`, `UNSUPPORTED_RULE_VERSION`) -> Performance gate 409 `PERFORMANCE_CUTOVER_CLOSED` -> read (404 `ASSESSMENT_REVISION_NOT_FOUND`, 422 `REVISION_OUTSIDE_WINDOW`/`UNSUPPORTED_RULE_VERSION`, 409 `ACCEPTED_LINEAGE_ABSENT`). Wired in `main.py` with `performance_gate`; composition `build_claim_limit_read_service`.
- Fixture: `backend/tests/s3_claim_limit_records.py::build(runner, url)` (S4 `CaseRunner`, Batch V2 + S3 worker) -> manifest `s3-claim-limit-records-v1` (days 10-06 full-candidate, 10-08 missing-pv, 10-11 poor-quality-conflict, 10-13 late-revision with `withdrawn`, 10-15 stale-selection). Normalised sample responses `backend/tests/fixtures/s3_claim_limit_api_samples.json`.
- Tests: `test_s3_capability_read_postgres.py`, `test_s3_claim_limit_postgres.py` (gate, fail-closed and currentness mutations proven).
- Open: registry `I-capability-read`/`I-claim-limit-read`/`I-S3-02a` stay open until review; Necessary/open-bound/cohort/configuration/absent-lineage are proven by mutating the real snapshot, not by separate ingested cases; S3-02b UI and walkthrough; S6-02a's `0019` does not interact (no migration here).

## S3-02b - Evidence Analysis selected claim limit UI (built, in_review; owner walkthrough before merge)

Branch `task/S3-02b-claim-limit-ui` (base main `8b5d8137`, S3-02a merged); packet `archive/agent-history/S3-02b-review-packet.md`; owner steps `archive/agent-history/S3-02b-owner-walkthrough.md`. Frontend and a walkthrough tool only; no backend change, no migration.

- Client `frontend/src/sites/claimLimitClient.ts`: `getClaimLimit(site, day, revision|null, signal)` over the S3-02a route; `getAssessedDay(site, day, signal)` maps the S3 dispatch window read to periods (whole-day revision + interval revisions, interval bounds from segments). Results are named: loaded / unauthenticated / forbidden / not_found(code) / closed / refused(code: 422 and 409 lineage) / unavailable / aborted.
- Section `frontend/src/sites/EvidenceClaimLimit.tsx` ("What the selected assessment can support"), rendered on every Evidence Analysis view beneath S2's `ClaimLimit` (`LedgerSiteEvidence.tsx`) and on the legacy analysis view (`SiteEvidence.tsx`). Selection is `day=<YYYY-MM-DD>&revision=<id>`; the legacy `assessment` parameter is not read. No day -> no read, "No assessment selected"; day without revision -> UNASSESSED read + period links. Positive sentence only when `currentness === CURRENT` with the rule's current claim (INDETERMINATE stated as such); others say no current conclusion and show the earlier ceiling as "At the time ...". Accepted IDs link in-page (`record=`, day/revision kept); pinned revision links to Performance > Dispatch through a shell-built `assessmentHref` (`SiteEvidenceFrame.tsx`). Rule, codes, IDs, run/cohort and watermarks sit in a closed "Technical details" disclosure. Stale answers are dropped (AbortController per selection).
- `SiteEvidenceClient.claimLimit` (optional) is wired in `createSiteEvidenceClient`; `settled.ts` LOADING knows the two new sentences; CSS `.claim-limit*` in `ui/primitives.css`.
- Tests `frontend/src/sites/__tests__/evidenceClaimLimit.test.tsx` (28) over S3-02a's samples.
- Walkthrough `tools/s302_claim_limit_walkthrough.py prepare|links|serve|late|attest|drop` (db `assetops_s302*`, work `var/s302*`, API 8932, web 5442): builds S3-02a's fixture, runs the Evidence then Performance comparisons (recorded in `gates.json`), verifies every case through the served route; `late` ingests a late SOC reading on 10-06 without a worker pass (STALE_PROJECTION); `attest` fails unless both gates passed and every served read matches.
- Open: registry `I-evidence-analysis-claim-limit-ui`, `I-S3-02b`, `I-S3-02` and `evidence-analysis:2#b` stay open until review and owner walkthrough; no ingested NECESSARY case (vocabulary only); a CURRENT whole-day revision's interval list is not covered by a sample or the walkthrough; copy polish goes to the W1-conclusion task.
## W2-00 - ordinary source events and interval evidence (built, in_review)

Branch `task/W2-00-source-events` (base merged main `dc643215`, rulings `D-2026-10-17-w2-00-answers`). Packet `.agent/W2-00-review-packet.md`.

- Settled: `contracts/assetops_contracts/source_envelope_v4.py` is the V4 parser/canonical text (schema 4, V3 message identity), `V4_MEASUREMENTS`, the kind-to-outcome allowlist, `event_identity_sha256` (canonical `{source, timing minus published_at, payload}`), the dispatcher `parse_canonical_source_envelope_text`, the Batch V2 header reader `read_envelope_header`, and the closed `V4_CHANNEL_MAPPINGS` (`simulator-lab-gateway-cold/1`: 12 cold tuples + 2 reserved EV). V4-only refusal kinds are a subclass of `EnvelopeRejected`; the shared `ENVELOPE_REJECTION_KINDS` is unchanged. Vectors `contract-fixtures/source-envelope-v4-vectors.json`.
- `ingestion_batch_v2.seal_batch_v2`: schema-4 texts (or schema 3 with EVENT/INTERVAL_DELTA) are admitted by header only; V3 texts stay strict.
- Migration `0020_w2_source_event`: seven nullable event columns, four relaxed columns, family/shape/delta/ID/kind-outcome/actor/length CHECKs, partial unique `accepted_event_identity_unique` and `accepted_ev_start_unique`, conflict-kind CHECK for three kinds; downgrade refuses while events, deltas, event/session conflicts or `cold_chain` jobs exist.
- `ledger.decide` dispatches by stated schema; `_decide_v4` requires the closed tuple and the pinned row's five v4 keys to agree (`MAPPING_INCOMPATIBLE`), then unit, periods and EV connector (`asset.asset_code` of the bound asset, read with the binding set). `postgres_evidence_ledger._persist` wraps each INSERT in a savepoint, keeps the message DO NOTHING arbiter and rereads `_REREAD_ORDER` (message, event, session); unlisted integrity errors propagate. Only accepted V3 rows enqueue the `dispatch` job.
- Reads: Postgres `records_page` family/kind filters and the seven event fields (`record_payload`, null on old rows); the legacy file read refuses the filters with 422 `FILTER_UNSUPPORTED`; `ledger_reads.CONFLICT_KINDS` counts all three conflict kinds.
- Snapshot: `gateway/snapshot.py` admits the five optional v4 binding keys all-or-none; `BindingRow.v4_mapping` serializes them only when supplied; `BindingBasis` reads absent keys as None.
- Rule 8: `$ledgerOwnedTables`, the accepted-evidence message-arbiter check (with vacuity count) and the exact `_REREAD_ORDER` line; 11 `w200` negative probes and one control in `tools/writer_guard_probes.py` (two replace the order line).
- Open: no runtime cold/EV publication profile or producer (W2-02/W2-05b); no closed tuple carries `INTERVAL_DELTA` yet, so a delta cannot be accepted until W2-05b; v4 metadata is not persisted on `signal_binding_revision` (W2-01 publishes it); read-model plain readings for the new rejection kinds are absent.


## 2a - canonical format v1 and the leaf factor IDs (built, in_review)

Branch `task/2a-canonical-format` (base main `184dc509e`); spec `specs/2a-canonical-format/spec.md` rev 2, rulings D-2A.1-D-2A.10; packet `specs/2a-canonical-format/packet.md`. Contracts only, no migration, no database.

- Settled: `contracts/assetops_contracts/canonical/` (standard library only), a protected seam (D-2A.2: a change is version 2 beside v1). `units.py`: six dimensions, `Unit`, canonical unit text and strict `parse_unit`, `QUANTITY_UNITS`, `BAND_UNITS` (the only record-to-catalogue unit bridge). `factors.py`: the 73 leaf IDs of `factor_map` (MINI_GRID 31, COLD_CHAIN 23, EV_DEPOT_CAPTIVE 23; 4 shared), one unit each, `leaves_of`, `FACTOR_ID_PATTERN`. `records_v1.py`: the fourteen kinds as data (`KIND_SPECS`), `loads_canonical` (the only bytes entry; duplicate keys, NaN, bad UTF-8 refused), `parse_record`, `parse_batch` (per-row outcomes; source-type, then duplicate check), `to_canonical_json` (sorted keys, decimals `format(d, "f")`), `record_digest`, `batch_digest` (valid records only). `sources_v1.py`: 17 source types, `EXISTING_FORMATS` (readings and fuel records unchanged).
- Tests (D-2A.10): `backend/tests/test_2a_canonical_v1.py`, `backend/tests/test_2a_canonical_manifest_parity.py`, fixture `backend/tests/fixtures/canonical_v1_examples.json` (byte copy of the spec folder's examples).
- Open: `simulator/.../world/leaves.py` still has its own list until DS1b (D-2A.8); node IDs, `filled_by`/`absent` are 3B1/3B6; the store and intake are 3A1/3A2; literal-unit cases inside `min`/`max` are 3B1's (D-2A.4); `select-tests` answers "full" for any fixture change (tools item, not 2a).

## DS1b - the generator's canonical record writers (built, in_review)

Branch `task/DS1b-canonical-writers` (base main `b28326e48`); spec `specs/DS1b-canonical-writers/spec.md` rev 2, rulings D-DS1B.1-D-DS1B.8; packet `specs/DS1b-canonical-writers/packet.md`. Simulator and tools only, no database.

- Settled: `simulator/assetops_simulator/world/records.py` writes month EXPENSE lines (O&M, staff, maintenance), customer-compensation ADJUSTMENTs and own-field BUDGET_LINEs for Jul-Oct at the nine Sites as `source-emulated` canonical v1 batches (one per tenant and source type, `parse_batch`-validated, golden `simulator/tests/world/golden/records_v1.json`). ESTIMATED October lines, fallback plan fields, zero actual liabilities and unread fields are listed unwritten with a reason. CLI `tools/world_history.py records --manifest M --out DIR` (exit 3 on `DS1B_*`). `history.json` byte-identical.
- Open: mid-build Q1/Q2 (edge reasons, no output depends on them); the coordinator's output run to `/opt/assetecon/generated/ds1b-<rev>/`; DS3 loads, 3A3 native files, 3A3/DS2 finer records reconcile to these month lines (D-DS1B.8).

## 3A1 - the commercial record store (built, in_review)

Branch `task/3A1-commercial-record-store` (base main `8c9af447b`); spec `specs/3A1-commercial-record-store/spec.md` rev 2, rulings D-3A1.1-D-3A1.12; packet `specs/3A1-commercial-record-store/packet.md`. Non-screen; no route.

- Settled: migration `0063_commercial_records` (four append-only tables: intake, record, revision, rejection; composite FKs, R11). `backend/assetops_backend/commercial/`: `CommercialRecords.ingest(tenant_id, bytes)` runs 2a's `parse_batch`, refuses envelope and tenant mismatch as REFUSED intakes (SHA of the bytes only, R1), decides records in input order under the per-tenant advisory lock at READ COMMITTED with a re-read under it (R4, R9), and reports NEW/REVISED/UNCHANGED/REFUSED per record; `latest_revisions` picks latest before any filter (R7). Sole writer registered in `configuration-persistence.ps1`.
- Open: 3A2 mounts the HTTP intake, caps declared provenance by path (D-3A1.9) and words STORED (R17); version order is arrival order (R10 residual for 3A3); erasure is a pilot residual (D-3A1.10); chain change-log registration waits for the first stored reader (D-3A1.6); migration renumbered at merge if 3C1a lands first (D-3A1.12).
## 3A2 - file intake of an operator's exports (built, in_review)

Branch `task/3A2-commercial-file-intake` (base main `6014ddedc`); spec `specs/3A2-commercial-file-intake/spec.md` rev 2, rulings D-3A2.1-D-3A2.16; packet `specs/3A2-commercial-file-intake/packet.md`. Non-screen; routes only.

- Settled: migration `0065_commercial_upload` (append-only `commercial_upload`, `commercial_upload_decision`). `commercial/uploads.py` checks, submits, accepts and declines an export on a Site path and an organisation path: only records 2a accepts are kept, pseudonymised (HMAC per tenant, key file outside the database) before anything is stored; refusals keep code and cut path only; the store sees records only on acceptance, in one transaction with the decision, and only if the checked basis still holds (`UPLOAD_STALE`). Roles: analyst/finance submit, finance/executive decide, a person always required. `create_app` refuses any mismatch of `ASSETOPS_REAL_OPERATOR_DATA` and an `assetops_op_` database (RC4). Every adapter method is scrubbed (D-3A2.16).
- Open: mid-build Q1 (key-file adapter placement, guard domain entry) and Q2 (two word placements); owner queue Q1, Q2, Q6 on defaults; native CSV/XLSX readers (3A6), emulators (3A3), amounts by month (3A4), the screen; a mislabelled real export and writers other than this route are residuals (R4); erasure by key deletion (pilot runbook).
## 3B1 - the structure registry, mini-grid (built, in_review)

Branch `task/3B1-structure-registry` (base main `8c9af447b`); spec `specs/3B1-structure-registry/spec.md` rev 2, rulings D-3B1.1-D-3B1.9; packet `specs/3B1-structure-registry/packet.md`. No migration, no route, no store.

- Settled: `backend/assetops_backend/structure/`: `registry.py` (records without validation, `HOMES`, `ABSENT`, `FAMILIES`, `REGISTRIES` = MINI_GRID v1), `rows_mini_grid.py` (47 literal rows: 31 leaves, 16 nodes; tolerance only on `unexplained_l`, 2.0 % of `diesel_l`), `expressions.py` (`Expr` = `Num`/`Ref`/`Bin`/`Neg`/`Call`, the contract for 3B3; `parse` with Decimal literals; `unit_of` with the literal rule), `check.py` (twelve `STRUCTURE_*` codes run code-major; `check_all`, `check_at_start`). `create_app` calls `check_at_start()` right after `install_handle_error_hook()`; a bad structure raises `ConfigurationError` naming the row. Test `backend/tests/test_3b1_structure_registry.py` (T1-T5).
- Open: evaluation and `missing` (3B3), Findings pins (3B2), observer and tolerance use (3B4), cold rooms and EV depots (3B6), snapshot (3B7a), rights and operations rows (9a0, OPS1), levers (step 6).

## 3B3 - the structure read and evaluator, mini-grid (built, in_review)

Branch `task/3B3-structure-read` (base main `bf72c735d`); spec `specs/3B3-structure-read/spec.md` rev 2, rulings D-3B3.1-D-3B3.16 and handshake round 1; packet `specs/3B3-structure-read/packet.md`. No migration, no route, no store.

- Settled: `structure/evaluate.py` (pure: `evaluate` folds a registry bottom-up in one prec-34 context; evidence weakest-part with `NEUTRAL` skipped; a `NEUTRAL` 0 operand is the only `*` short cut; `/0` and mixed currencies give no value with a node-level `Missing`; leaf-value checks `STRUCTURE_MISSING`/`_EVIDENCE`/`_CURRENCY`/`_LEAF_INPUT`; `blocks_of`; `compose` sums `SUM` rows per factor with `included`/`excluded`, None when no Site has it). `sources.py` (`SOURCE_STATE` literal: 2 PROVIDED, 2 ASSUMED prices, 9 HELD_NOT_CALCULATED, 15 NOT_CONNECTED, 3 OPTION_ONLY; `ProductLeafSource`), `read.py` (`StructureRead.site/portfolio`, `SITE_TYPE_TO_STRUCTURE`), `composition.py` (`build_structure_read`). Registry v2: `FactorRow.neutral`, `.composes`, `Registry.parsed/.parents` (parse once); check codes `STRUCTURE_NEUTRAL`, `STRUCTURE_COMPOSES`; L1 finite tolerance. `chain/outcomes.py` `month_sum` extracted. Pack parity: 47 nodes x 3 Sites x 2 sides to the cent.
- Round 1 settled: Q1-Q4 answered (rulings.md): `month_sum` returns the counted days with no value (D-3B3.17) so a month with one is NOT_RECEIVED `VALUE_NOT_STATED:n`, never summed as 0; `read.site_count` (k of n over every Site asked for); prices through `financials.composition.build_window_price_selection` (one store, disposed).
- Open: board's unstated days (`_month_reading`, `energy_basis`, decision queue); route and snapshot `3B7a`; display "k of n Sites" `3B5`; providers `3A4`/`4b`; cold/EV `3B6`; `wear_rate` step 6; template rebuild (coordinator).

## 3A4 - amounts by month (built, in_review)

Branch `task/3A4-amounts-by-month` (base main `38e2b3fe1`); spec `specs/3A4-amounts-by-month/spec.md` rev 2, rulings D-3A4.1-D-3A4.11 and handshake round 1; packet `specs/3A4-amounts-by-month/packet.md`. No migration, no route, nothing under `structure/`.

- Settled: `commercial/months.py` `CommercialMonths.site_month/portfolio_month` read latest revisions (as of `known_at`, cutoff before "latest") as money by month: six money kinds, recognition month or Site-local settlement month (`month_bounds`, parity with 3B3's `month_window`), lines keyed `(kind, dims, measure, currency, unit, provenance, basis)`, exact 200-digit sums, budget lines never summed (`DUPLICATE_DECLARATION`), no line without a record; `MonthStamp` digest, `stale`, `months_touched`; `closed` at the read's cutoff. Store port and Postgres adapter: `latest_revisions(known_at=)`, `intake_revisions`, `site_zones`. `build_commercial_months`.
- Open: `_scrubbed` (D-3A2.16) on the three reads at 3A2's merge if 3A2 merges second; `4b` turns lines into leaves, `5a` reads budget lines, `3B7a` keeps stamps; Site re-zoning moves settlements (residual).

## 5a - targets per factor, unit 1: budget lines (merged 20 Nov; r2 ACCEPT)

Branch `task/5a-targets` (base main `880ba4dbf`); spec `specs/5a-targets/spec.md` rev 2 §2, rulings D-5A.1-D-5A.15; packet `specs/5a-targets/packet-5a-u1.md`. New package `structure/targets/`; no existing module edited, no migration, no route.

- Settled: `structure/targets/lines.py` `BudgetLineReader.site/portfolio` turn 3A4's `BUDGET_LINE` lines into `TargetLine`s in rule order (two versions block every registry factor, `NOT_A_FACTOR`, `DUPLICATE_DECLARATION` never summed, `CURRENCY_MISSING`/`CURRENCY_ON_QUANTITY`), `LEAF`/`NODE` place, and the declarer from the intake of each line's latest revision (`person_id` from `person:<uuid>`; an unchanged re-upload does not re-declare). Fixture `targets_lakeside.json`.
- Open: units 2 (target rules, `TargetRead.site`) and 3 (portfolio, composition, Postgres) wait for `4b1`; owner Q7 default (cost with no line at actual, D-5A.15) applies in unit 2.

## 5a - targets per factor, units 2-3: target rules, Site and portfolio read (built 20 Nov; in_review)

Branch `task/5a-targets-u23` (base main `e88641e97`); spec `specs/5a-targets/spec.md` rev 2 §3-§6, rulings D-5A.4-D-5A.15, D-4B.16, D-4B.18; packet `specs/5a-targets/packet-5a-u23.md`. New modules only (`structure/targets/{rules,read,composition}.py`); no migration, no route, nothing stored.

- Settled: `TARGET_RULE`/`MAIN_OF` literals for the 31 MINI_GRID leaves; `solve_main` through `evaluate` (linear, non-zero slope). `TargetRead.site`: leaf line DECLARED, stated heading line DECLARED (D-5A.7), other node lines are `TargetCheck`s only; no line gives a labelled ESTIMATED assumption (`LEAK_ZERO`, `AT_ACTUAL` incl. costs per D-5A.15, `MAIN`) or an absent target naming `BUDGET_LINE` (blocked `NOT_CALCULATED_YET`, D-5A.13). `portfolio` composes per factor with "k of n"; operator lines only in `portfolio_lines`. `build_target_read`. Lakeside Oct 2,295.00, 3 of 3; Kisiwa −60.00 vs −65.00 check False.
- Answered: Q2 (fixture declarer is `service:ds3-loader` everywhere) and Q3 (D-5A.16, origins of assumptions); merged 20 Nov (r1 ACCEPT, F1 test added). `5b` splits the gap from this read.

## 4b1 - the stated-node seam (merged 20 Nov; r2 ACCEPT + R2-1)

Branch `task/4b1-money-leaves` (base main `880ba4dbf`); spec `specs/4b-money-leaves/spec.md` rev 2 §2, rulings D-4B.1, .2, .10, .11, .16, .17, .18; packet `specs/4b-money-leaves/packet-4b1.md`; reviews `review-4b1.md` (r1, r2). No migration, no route, no store.

- Settled: MINI_GRID v3: `FactorRow.stated_by` on `revenue` (CHARGE) and `fuel_cost` (EXPENSE (FUEL)); check `STRUCTURE_STATED` after `STRUCTURE_COMPOSES`. `evaluate(registry, leaves, stated=)`: a stated value governs and the expression stays as `computed`/`detail_missing`; `NOT_CONNECTED`/`NOT_RECEIVED` let the expression through, `NOT_CALCULATED_YET` blocks (D-4B.16). `LeafValue.origins`, `FactorValue.origins/stated/computed/detail_missing`, `ORIGIN_ORDER`, `weakest_origin`, runtime `STRUCTURE_ORIGIN`; compose carries origins and `Site:leaf` detail. `StatedSource`, `StructureRead(sources, stated=None)`; `commercial.composition.build_commercial_reads`. With `stated` empty the old fields equal 3B3's.
- Fix round (D-4B.18): a valued part names its origin; only a NEUTRAL value or a CALENDAR row may carry `()`, else `STRUCTURE_ORIGIN`; `unknown` ranks last in `ORIGIN_ORDER`. S11(a) is parametrized from the registry over every valued non-CALENDAR leaf row (money and non-money, every registry) and every stated node (r2 R2-1), so the exemption cannot widen unnoticed; plants P1 (refuse `()` only with a currency) and P2 (exempt OPERATIONAL_RECORD too) now fail.
- Open: every production leaf still has `origins == ()` until 4b2 (`weakest_origin` is `None`, not "no weak part"); 4b2 providers (`structure/money.py`, states, T6 edits); `5a` builds on the new fields.

## RC4-F1 - the database a URL really reaches (merged 20 Nov; r1 ACCEPT)

Branch `task/RC4-F1-database-name` (base main `e88641e97`); spec `specs/RC4-F1-database-name/spec.md` rev 2, rulings D-RC4F1.1-5; packet `specs/RC4-F1-database-name/packet.md`. No migration, no route.

- Settled: `assetops_backend/database_target.py` `database_target(url, environ)` returns host, port and name as psycopg is handed them, or `DatabaseTargetUnclear(reason)` (query allowlist, one plain host, plain non-empty name, none of six `PG*` target variables; reasons hold no URL value). `commercial_upload_settings` decides RC4 on it (unclear: `ConfigurationError` "DATABASE_URL must name one database plainly (<reason>)."); `postgres_commercial_store.database_name` deleted; the backfill's protected check uses it; `tools/demo_combined.py` `Demo.env()` strips the six variables. Plants F1-F8 fail.
- Settled: Q1-Q3 answered (D-RC4F1.3-5); `$pgReaders` admits `database_target.py` (owner-approved line); plants F1-F9; test 8 pins the admission.
- Open: backlog `RC4-F1-tools` (`tools/sweep-setup-cache.py` and one other tool still read the name); 3A3 `refuse_operator_database` and ON1 onboarding must call `database_target`; review residuals (test 7 misses `engine.url.database`, test 8 misses `importlib`).

## 4b2 - the money leaves, providers (merged 20 Nov; r1 ACCEPT)

Branch `task/4b2-money-providers` (base main `e88641e97`); spec `specs/4b-money-leaves/spec.md` rev 3 §3 to §5, rulings D-4B.3 to .9, .12 to .15, .18; packet `specs/4b-money-leaves/packet-4b2.md`. No migration, no route, no store.

- Settled: `structure/money.py` `CommercialLeafSource(months, store, fallback)` serves `revenue` and `fuel_cost` (stated), `om`, `staff`, `productive_kwh`, `in_transit`, `outstanding` and `diesel_price` from 3A4's month; one `site_month` and one `latest_revisions` per context object. Connected = any record of the kind for the Site; open month = no value (`MONTH_OPEN`); QUOTE never cost; recorded 0 only for a held ZERO_WHEN_HELD kind; mixed currency `NOT_CALCULATED_YET`; the diesel price from INVOICED/PAID fuel invoices, the declared price only with no such invoice, none on zero litres. Absent values name `READ_AS`; valued ones carry record origins. `SOURCE_STATE` gains `PROVIDED_ELSE_ASSUMED`, `STATED_STATE` added; `build_structure_read` wires the commercial reads third.
- Open: mid-build Q2 (Postgres `entered_by` literal; default applied); test 5 lives under `simulator/tests/world/` (dependency guard). Carrying a missing actual at target is `5b`; litres burned `4d`; settlement matching queue Q3.

## 3A3 - emulated native exports and the source contract test (merged 20 Nov; r2 ACCEPT)

Branch `task/3A3-emulators` (base main `3b3916d4f`); spec `specs/3A3-emulators-contract-test/spec.md` rev 2, rulings D-3A3.1-12; packet `packet.md`. No migration, no route, no screen.

- Settled: `assetops_contracts.native` (`Layout`, `Column`, `read_layout`, `render_layout`, four `*-illustrative-1` layouts: billing, collections, expenses, budget). `commercial/readers.py` `ReadContext(tenant_code, received_at, real_data)`, `ReadResult.refused`, `LayoutReader` (provenance follows the database, D-3A3.10); `READERS` = canonical plus the four, each admitted by a case in `backend/tests/source_contracts.py` (C1-C10, S2). `_check` lets a reader's row refusal win; out-of-range is 500. Native refusal words (`NATIVE_ENCODING/HEADER/ROW/VALUE/CHARACTER`).
- Settled: one writer of commercial records (S1 AST scan); `build_commercial_records` deleted; `refuse_operator_database` on `database_target`; `AccountService.onboard_person`; `CommercialUploads.held` / `held_uploads`. `python -m assetops_backend.load_emulated_exports` (exit 2 before any submission, 3 on a refused submission; `ALREADY_WAITING`, `NOTHING_NEW`, `decided_by_script`). `simulator/.../world/exports.py` + `tools/world_history.py exports`: October, mini-grid, totals equal the manifest (pinned SHA-256s).
- Open: owner Q1 (`--accept-as` in rehearsal); `uploads_waiting` with the upload screen (D-3A3.8); `3A6` profiles append contract cases; S1 does not see `importlib`/string-built access.

## ON1 - an operator's tenant from one onboarding file (in review, 20 Nov)

Branch `task/ON1-operator-tenant` (base main `8fddb2bba`); spec `specs/ON1-operator-tenant/spec.md` rev 3, rulings D-ON1.1-16; packet `packet.md`. No migration, no route, no screen.

- Settled: `onboarding/operator_file.py` (`assetops.operator-onboarding/1`, strict; `roles_digest`; submitter never accepter) and `onboarding/service.py` `OperatorOnboarding.check`/`apply` (tenant, Sites through `import_site`, accounts, roles by `service:onboarding`, key); `python -m assetops_backend.onboard_operator digest|check|apply`. A real file is refused before any write (`ONBOARD_REAL_AWAITS_APPROVAL`, until `ON1b`). `AccountService.onboard_grant`/`onboarding_may_grant`/`executive_of`; store `add_onboarding_grant` under the role lock (ONBOARDING_CLOSED, ROLES_SEPARATE, ROLE_ALREADY_HELD). `FoundationStore.tenant_slugs`. `config.served_tenant_slug()` (`ASSETOPS_TENANT_SLUG`) in `create_app`; `app.state.site_registry.served_tenant_slug`. Key tombstone (`_tombstoned` by lstat), `erase_key_file`, `key_state`, `directory_ok`, `pseudonym_key erase`, 409 `PSEUDONYM_KEY_ERASED`. `Demo.env()` pins `demo`. Runbook `Docs/engineering/operator-deep-dive-runbook.md` tested line by line.
- Open: mid-build Q1 (structural refusal code, default `ONBOARD_FORMAT`) and Q2 (`onboarding_may_grant` trips the persistence guard's `open\(` pattern); `ON1b` (executive approval, real operators); Q5 grant-API separation (carried to `3C0b`).

## 5b - attribution, unit 1: the split rules (in review, 20 Nov)

Branch `task/5b-attribution` (base main `8a2900bc4`); spec `specs/5b-attribution/spec.md` rev 2 §2, rulings D-5B.1-14; packet `packet-u1.md`. Pure; no migration, no route, no screen; no diff in `structure/read.py`.

- Settled: `structure/attribution/rules.py` (`BRIDGE_ROOTS`, kinds, splits, reasons, `SOLVE_TOLERANCE` 1E-12, `agree`) and `bridge.py` (`BridgeRow`, `bridge`, `by_home`, `lowest`): AR1 signed sums, AR2 volume at target price then price at actual volume (price chosen by unit), money pushed down by `scale`, neutral terms give no row, a RESIDUAL only beside a stated heading's unobserved terms, record-vs-factors and children-vs-parent judged within 1E-12. Kobo §5.1: −562.00 = +38.00 − 600.00; AT-1 to AT-3 to the cent.
- Closed since: Q1 ruled D-5B.15 (`NOT_SPLIT`/`DETAIL_NOT_AVAILABLE`, now asserted); the seam is on `main`; units 2-3 below.

## 5b - attribution, units 2-3: carrying, Site and portfolio bridges, the read (in review, 20 Nov)

Branch `task/5b-attribution-u23` (base main `fb6d248d3`); spec rev 2 §3, §4, §5.2; rulings D-5B.1-15; packet `packet-u23.md`. Pure plus one wiring module; no migration, no route, no screen; no diff in `structure/read.py`.

- Settled: `carry.py` (`om`/`staff` at their own budget line, ESTIMATED, `carried_as` TARGET, never for an open month, an unconnected source, an assumed target or a heading); `site.py` (`SiteBridge`: contribution and cash trees from the carried inputs); `portfolio.py` (k of n over one Site set per row, values added only for `SUM` factors, effects always, currencies never, `carried` Sites named, repeated key refused, disagreements kept); `read.py` (`BridgeRead`, one UTC instant per call); `composition.py` (`build_bridge_read`, the only `commercial` import). Lakeside October: 1,443.00 against 2,295.00, −852.00, 3 of 3, ESTIMATED; without Mto's billing −747.00, 2 of 3.
- Open: owner Q1 (carry a heading) and Q5 (also show the 3-of-3 target) on their defaults; `5c` words every stop and disagreement (D-5B.10, D-5B.12); pack fix for summed prices queued (handshake R1).

## 4d - the monthly litre split (in review, 20 Nov)

Branch `task/4d-litre-split` (base main `b8b812f23`); spec `specs/4d-litre-split/spec.md` rev 2, rulings D-4D.1-15; packet `packet.md`. No migration, no intake, no route, no screen; 5b unchanged.

- Settled: `structure/litres/rules.py` (`month_litres`: `necessary_l = T(month) − candidate`, `candidate_l` = CANDIDATE spans' litres, `unexplained_l` = dips and deliveries in the dip window less `T(window)`; every litre MODELLED, origin `unknown`; one rounding to 0.001 L; twelve notes in precedence, never 0); `source.py` (`LitreLeafSource`, pinned reads memoised, at most 16); `inputs.py` (`day_state`: only a CURRENT selection is ASSESSED; `StoreLitreInputs` over K3's curve choice, K2's dips and A2's slot rule); `PostgresFuelBalanceStore.read_at`, `PostgresAssessmentStore.dispatch_spans` and `dispose`; the structure read's fourth builder. `SOURCE_STATE` makes the three leaves PROVIDED (`LITRE_LEAVES`). Kobo KOBO-OCT: 730.000 / 330.000 / 120.000 L; its −600.00 fuel gap splits −37.50 / −412.50 / −150.00 through 5b.
- Open: mid-build Q1 (5b's litre-row effects carry five places, `−600.00000`; 5c to format money); 3B7a lists valued litre leaves `untracked` (R13); `5c` words the notes (spec §2.4) and the label "Diesel not shown to be avoidable".

## 3B7a units 1-3 - the frozen monthly structure snapshot (merged 21 Nov; r1 accept-with-fixes, fix round 2)

Branch `task/3B7a-snapshot` (base main `264d7d6a7`, unit 0's seam merged); spec `specs/3B7a-structure-snapshot/spec.md` rev 2, rulings D-3B7A.1-12; packet `packet.md`. Migration 0066; no route, no screen.

- Settled: `structure_snapshot/` (model, canonical codec with digest, `untracked`, `rules_digest` import closure, `StoreHeldKinds`, memory and Postgres stores, `SnapshotBuilder.build`/`verify` at one instant, `SnapshotRead` serving frozen values with `RECORDS`/`MONTH_CLOSED`/`RULES` or `REBUILD_NEEDED`, composition); `python -m assetops_backend.build_structure_snapshot build|verify`; table `structure_snapshot` (append-only trigger, per-scope instant uniqueness).
- Open: the persistence-guard block awaits owner approval (Q6/R2; text in the packet); mid-build Q1 (`rules_digest.py` trips rule 2's `pathlib` pattern once the domain is registered), Q2 (3A2's migration test asserts 0065 is head), Q3 (verify's unknown-id code, default `UNKNOWN_SNAPSHOT`); `3B7b` triggers and daily run; `5b`/`5c` consumers.
## SC-1a - the statement composer, units 1-3 (built, in_review, 21 Nov)

Branch `task/SC-1a-composer` (base main `8805ee169`); spec `specs/SC-1-statement-composer/spec.md` rev 2, rulings D-SC1.1-D-SC1.31; packet `specs/SC-1-statement-composer/packet.md`. Non-screen; no migration, no route.

- Settled: `backend/assetops_backend/i18n/` gains typed facts, one format per slot type, one condition evaluator, the load check, `render`/`served` over structured statements (legacy entries unchanged), the wire form, the English vocabulary and `common.*`; worked statements for 3A7 and 5c live in the test catalogue (`backend/tests/statement_cases/`). Guard `tools/checks/statement_catalogue.py` (+ `--self-test`, 40 plants): load, a case per variant, legacy hash ratchet (123 keys), three-scope hand-built scan (mechanism positive, `ADOPTED` positive and empty, ratchet baseline 320 paths / 5,900 fingerprints from main), `KEY_INSTANCE`, `I18N_PRIVATE`/`I18N_BYPASS`, `MECH_UNSCOPED`.
- Fix round r1 (D-SC1.32-39): number words are roots joined to suffixes (`schema.number_words`), `TOKENS` no longer holds them; the ratchet reads prose by word pairs with SQL lead, encoded joins, display conditionals and any logger exempt; `messages.CATALOGUE` templates left to the legacy ratchet; word maps one fingerprint per entry; classed allow file `statement-handbuilt-allow.json` (empty); `UNSERVED_SERVED`; every `i18n/**` file classified; the five public modules declare `__all__` (`I18N_SURFACE`, bypass through them); `from_wire` L4. Baselines regenerated from main: 300 paths / 5,185 fingerprints, 123 legacy keys; self-test 68 plants.
- Fix round r2 (review round 2): the guard binds the `i18n` package object to surface `""` and chains attributes into the public modules (M4; a literal `import_module`/`__import__` counts as an import); `NUMBER_WORDS` adds the `-ing` forms, `cent` and the zero forms `zeroes`/`nought` (L6, D-SC1.32's class; extends spec §3.12's literal); each live allow entry prints `ALLOWED path:line class fingerprint | source` (L7).
- Owner approved both check-all lines, 2026-11-21 (`owner/owner-approve-sc1a-3c2-guards-2026-11-21.md`).
- Open: review round 3 ACCEPT; merge; 3A7 and 5c adopt (`ADOPTED`), SC-1b converts the legacy templates and the 229 served-exception handlers.

## SC-1f - "Declared", stated-figure basis, two guard fixes (built, in_review, 21 Nov)

Branch `task/SC-1f-declared-word` (base main `fa13f254f`); spec `specs/SC-1f-declared-word/spec.md` rev 1, rulings D-SC1F.1-6; packet `packet.md`. Non-screen.

- Settled: `DECLARED` reads "Declared" for every origin (step 1 of `evidence_word`); 3A7's accounts are `RECORDED`, its tolerance `DECLARED`; a `with` basis names only the figures its variant prints or reads (two-pass fill in `render._statement`), so 3A7's statement and standing read "within 1% (Declared)" and its matched/not-matched headings "(Recorded[, Emulated] and Declared)". The statement guard's logger rule is a stem (`LOG_STEMS`) or a `getLogger` binding; P55 plants merge into the real allow file, which now holds the two `profiles.py` `CODE` lines; baseline lost exactly four fingerprints.
- Open: review; KD1 (a variant that states no figure, `money_word`, keeps wording all its `of` figures) for Architect confirmation; owner sees "Declared" at the 5c walkthrough.

## 3B2 - Findings pinned to their factors (in review, 21 Nov)

Branch `task/3B2-findings-pinned` (base main `c69e72f61`); spec `specs/3B2-findings-pinned/spec.md` rev 2, rulings D-3B2.1-15; packet `packet.md`. No migration, no route, no screen, no served text.

- Settled: `structure/pins.py` (`PINS`: GENERATOR_SUPPORT_CANDIDATE -> MINI_GRID/`candidate_l`, UNEXPLAINED_FUEL -> MINI_GRID/`unexplained_l`; `PENDING_PINS` for the two cold and one EV mechanism; `pinned_category` from the row's home at call time; `parity()` in the pin's own domain); `check.check_pins` and `PIN_CODES` (STRUCTURE_PIN, _TOTAL, _DUPLICATE, _UNKNOWN, _MISSING), run by `check_all()` on the start-up path only. The outcome map's wire is unchanged; the one ruled difference is UNEXPLAINED_FUEL (Protect in the literal, Optimize in the registry, D-3B2.4).
- Open: `3B5` switches the wire to the pins applying D-3B2.4; `3B6` moves the pending pins onto their registries; the `-` structure key in `STRUCTURE_PIN_MISSING`'s text is for review.

## DS3 - the bulk loader (in review, 21 Nov)

Branch `task/DS3-bulk-loader` (base main `8eff70625`); spec `specs/DS3-bulk-loader/spec.md` rev 3, rulings D-DS3.1-23; packet `packet.md`; mid-build Q1-Q3 answered, 0 open. No migration, no route, no screen, no guard change.

- Settled: `PostgresEvidenceLedger.bulk_admit` (one transaction per batch, `_BULK_BATCH_SQL`/`_BULK_EVIDENCE_SQL`/`_BULK_DISPOSITION_SQL` set-based `INSERT ... SELECT FROM unnest`, only the existing DO NOTHING arbiters; refusals BULK_PUBLISHED_BATCH, BATCH_ID_CONFLICT, BULK_BATCH_IN_PROGRESS, BULK_SITE_TYPE_UNPROVEN (MINIGRID only), BULK_MESSAGE_COLLISION; other integrity errors propagate); `gateway_principal`; `BatchIngestionService.admit` and `_enqueue_admitted` extracted unchanged; `evidence/bulk_load.py` (`BulkEvidenceLoad`, SIMULATED only, `permitted_database`: audit names and harness clones only, host and port); `python -m assetops_backend.load_world_inputs` (commercial through `load_emulated_exports`, telemetry in bulk; exits 0/2/3/4); `pg_harness.clone_database`/`drop_database`. Parity on two Kobo days: equal evidence, batch and disposition rows, recompute-job rules, census.
- Open: nothing from the mid-build questions (answered). DS4 lifts BULK_SITE_TYPE_UNPROVEN per Site type with that type's parity slice, and checks the event cover for gap days (D-DS3.21).
## 0K2 - the Kobo replay study on a simulated season (in review, 21 Nov)

Branch `task/0K2-kobo-replay` (base main `15c5b07b6`); spec `specs/0K2-kobo-replay-study/spec.md` rev 2, rulings D-0K2.1-29; packet `packet.md`. No database, no migration, no served text.

- Settled: `runs/replay_study.py` (`replay_study` and the §2.5 helpers `0M` reuses; whole-window replays only, refusals before any port call, calibration on admissible days, dawn readings with new/cleared dates against no action, local-month splits, SIMULATED/MODELLED labels on every record); `host/tests/kobo_season.py` (the declared 61-day season, published at stated quanta); `tools/kobo_replay_study.py`. 61-day run: CALIBRATED (adapter fidelity); every case, the baseline included, has 16 of 61 dawns below 35% (day 0 and the 15 after-overcast dawns), no case adds or clears a dawn date.
- Open: owner-away rows 37 (design values unchanged) and 42 (dawn admissibility for `6c`); the reader from accepted readings (`0K3`); money and option choice (`6c`).

## 0K1 - the forward replay port and its host adapter (in review, 21 Nov)

Branch `task/0K1-forward-replay` (base main `3bdf3c81d`); spec `specs/0K1-forward-replay-port/spec.md` rev 2, rulings D-0K1.1-18; packet `packet.md`. No database, no route, no served text.

- Settled: `assetops_contracts/forward_replay.py` (request, projection, `FORWARD_REPLAY_REFUSALS`, Fraction-only fields); `runs/replay_port.py` `ForwardReplayPort` (one method; `LabExecutionPort` unchanged); `host/forward_replay.py` `HostForwardReplay`, `replay_inputs` (spec §2.4 order), `project`, `REPLAY_MODELS` mini-grid v5-v7. Replays of K-BASE (v5, v6, v7), K-START, K-STOP, K-RES and K-CLIP equal the kernel's own trajectories exactly.
- Open: mid-build Q1 (P2 is caught by T10, not T1: the projection depends on loads only through their sum) and Q2 (P4 is caught by T10, not T4); defaults applied. Calibration, the 61-day window, gap fill and composing the port are `0K2`/`6c`.

## 4a - Energy to cash, where the kWh went (in review, 21 Nov)

Branch `task/4a-energy-to-cash` (base main `aa3ebefe8`); spec `specs/4a-energy-to-cash/spec.md` rev 2, rulings D-4A.1-26; packet `packet.md`; mid-build Q1-Q2 (defaults applied). No migration, no guard edit, no route, no screen, no served text.

- Settled: MINI_GRID registry v4 (`metered_kwh` stated by customer meter reads, `billed_kwh` by the billing export); `structure/energy/` (pure `rules.month_energy` for the eight energy factors, `StoreEnergyInputs`, `EnergyLeafSource` as the fifth builder in `build_structure_read`); `MiniDepthRead.feeder_month` (roles-4 `feeder_demand`, SELECT only); the `technical-loss-band` LOAD property (below 100); 5a `MAIN_OF` tuples (`delivered_kwh` under `billed_kwh`, then `revenue`). Every absence is "Not available yet" with a cause and note, never 0.
- Open: 5c's record keys wait on 5c and SC-1a (D-4A.12, D-4A.20); `R-ABSENT-META` (`unexplained_loss_kwh` keeps `ZERO_WHEN_HELD`, unread; manifest change queued with D-4A.10); stored v3 snapshots read `REBUILD_NEEDED` until 3B7a rebuilds them (D-4A.25).

## 3B6 - Cold-room and captive-EV structures (in review, 21 Nov)

Branch `task/3B6-cold-ev` (base main `22dc0bbf3`); spec `specs/3B6-cold-ev/spec.md` rev 2, rulings D-3B6.1-24; packet `packet.md`; mid-build 0. No migration, no guard edit, no served text.

- Settled: `COLD_CHAIN` v1 (36 rows) and `EV_DEPOT_CAPTIVE` v1 (42 rows, `not_applicable=("revenue",)`) in `REGISTRIES`; `registry.applicability()` (APPLIES / NOT_APPLICABLE / NOT_IN_STRUCTURE; no caller outside tests); `STRUCTURE_NOT_APPLICABLE` (last per-registry code, plus a cross-registry pass) and the L2 key check in `check_all`; three cold and EV pins, `PENDING_PINS` empty; `SITE_TYPE_TO_STRUCTURE` maps COLDCHAIN and EV_CHARGING; `read.sites_excluded` (NOT_DECLARED / `STRUCTURE_OTHER_KEY`) used by every portfolio reader; `StructureRead.portfolio(structure_key=)`; `KEY_NOT_READ` refusals in `TargetRead.site` and `SnapshotRead.site`; `BridgeRead.site` reads targets first; `SOURCE_STATE` for both keys (calendar PROVIDED, HELD only with a stored record); `sources.COMMERCIAL_KEYS` gate in `CommercialLeafSource.leaf`.
- Open: cold and EV intake (9d, 9e), target sides and snapshots for cold and EV, a cross-structure total and the portfolio `cost_per_departure_met` (R-CROSS-KEY), a public-charging structure (R-EV-PUBLIC); stored snapshots read rebuild-needed after merge.

## 3A6 - source profiles as data (in review, 21 Nov)

Branch `task/3A6-source-profiles` (main `26dd65e60` merged in); spec `specs/3A6-source-profiles/spec.md` rev 2, rulings D-3A6.1-17; packet `packet.md`. Migration 0067 (revises 0066); no route change beyond the reader lookup, no screen.

- Settled: the profile engine (`native/profiles_v1.py`, `xlsx.py`, transforms, invisible rule, coded rule, `run_probes`); `commercial/profiles.py` (`SourceProfiles.check`/`admit`, steps 1-7 with coverage 4a-4c; `reader` with only the latest version reading new uploads); table `commercial_source_profile` (three hashes and a row count, never a cell); the intake's one-source-system-per-Site rule on check/submit and re-checked under the lock at acceptance; `python -m assetops_backend.source_profile check|admit|list`; the loader takes `<SLUG>.profile.<id>.csv|xlsx`; S1 tagged clauses (dynamic imports, `sys.modules`, `runpy`, names as strings, eval); the suite derives coded probes from the canonical side and runs the kobo profile case.
- Fix round r3 (XLSX work class): `xlsx.py` parses every member by event under one workbook budget of 500,000 elements (`NATIVE_WORKBOOK` past it), row numbers rise strictly, the header is never padded past the layout, numbers past a double are unreadable cells; adversarial set "N3 r3" in `contracts/tests/test_3a6_profiles.py`.
- Fix round r4 (bounds by resource): members are inflated a chunk at a time and counted (member 16 MiB, total 64 MiB, deflate or stored only), cell values charge one 16 Mi-character budget on every reference, CSV and XLSX reads stop one kept row past `MAX_RECORDS` and keep at most width+1 cells a row, the invisible scan is one regex class; set "N3 r4".
- Fix round r5 (the class, D-3A6.23-26): every upload parse (both readers, canonical JSON, admission's split) runs in a fresh forkserver child (`commercial/envelope.py`) under RLIMIT_AS 512 MiB, CPU 6 s, wall 12 s, a 32 MiB result, 2 at once per process; any breach is `NATIVE_TOO_LARGE` (its own words), logged with no content; the resource bounds switched to that code; N8-N10 bounds (attribute runs and names, 1 Mi characters a CSV row, a 256-entry/256 KiB zip directory). E0-E9, B1-B3.
- Open: the reading-upload intake (`reading_upload_api.py`) still parses in process (queued `ENV-1`); mid-build Q1 (A9 a's many-to-one map vs `check_layout`'s one-to-one rule); queue Q1 (moving a Site's source type to another system) and Q6 (Sites named, not coded) on their defaults; a v2 that changes `personal` turns that profile's corrections into version conflicts (packet risk); 3A7 next on the same files.

## 3A7 - one closed month reconciled (in review, commits 1 and 2, 21 Nov)

Branch `task/3A7-month-reconciled` (main `e5a283228` and the mid-build answers merged in); spec `specs/3A7-month-reconciled/spec.md` rev 2, rulings D-3A7.1-15, D-SC1.28 split; packet `packet.md`. Migration `0069_commercial_reconciliation` on 3B4's 0068.

- Settled: tables `commercial_accounts_statement` and `commercial_reconciliation_tolerance` (append-only); `structure/reconciliation.py` (`record`, `check`, `statements`, `standing` at `known_at`, `set_tolerance` citing an owner file by slug and figure) in the statement guard's `ADOPTED`; its sentences are SC-1 statements (`i18n/statements/en/reconciliation.py`: heading, gap, share, scope, statement, standing, money_word, refused); `structure/reconciliation_composition.py`; command `reconcile_month record|show|set-tolerance`; money reconciles only through a current opener with no covering mismatch; missing is never 0.
- Open: D1 (the standing's failing headings are a `details` list, not joined into `text`: SC-1 joins no sentences), D4 (tolerance evidence wording); the screen is 5c's.

## 3B4 - the structure observer (in review, 21 Nov)

Branch `task/3B4-observer` (main `2ef8e9769` merged in: 4a, 3B6, DS3); spec `specs/3B4-observer/spec.md` rev 2, rulings D-3B4.1-26; packet `packet.md`. Migration `0068_structure_finding` on 0066 (renumber at merge, gate B); no route, no screen, no served text.

- Settled: `structure/observe/` (`rules.py` OBSERVED/NOT_OBSERVED, signs, kinds, key, lifecycle table; `observe.py` the rule, band, basis, 25-key claim; `service.py` `StructureObserver.run` per Site under the Site-month lock; `composition.py`); today's Finding store gains domain `structure` and `structure_tolerance` (append-only, in `$findingTables`); four readers leave the domain out (`_fence`, `finding_detail`, `rows()` x5, thread sources); commands `observe_structure run` and `declare_tolerance set|clear|show`; `COMMAND_ROLES` `structure.tolerance.money`/`.operational`.
- Settled (unit 4): `check.check_observed` (`OBSERVE_CODES` KEY, COVER, LEAF, SOURCE, DIRECTION, KIND) runs in `check_all()` after `check_pins`, over `OBSERVED`'s keys only (COLD/EV registries not a fault); registry v4's 31 MINI_GRID leaves covered once (19 observed, 12 not).
- Open: owner Q1/Q2 (rows 27-28); residual R-FENCE-FUEL, R-NO-OPPORTUNITY, R-ASSUMED-TARGET; words and a screen come with 3B5/5c.

## DS4 - the template ladder, world check and re-benchmark, units 1-3 (in review, 21 Nov)

Branch `task/DS4-template-ladder` (unit 3 `58bb50809`, fix round `68449e49d`); spec `specs/DS4-template-ladder/spec.md` rev 3, rulings D-DS4.1-27; packet `packet.md`.

- Settled: `tools/world.py` builds the L0/L1/L2 ladder by key (migrations; definition, inputs, onboarding, code; L2 steps), frozen rungs, manifests, `clone`/`reset`/`list`/`drop` (keys erased before an L1 drops), and `check` C1-C7 with the total C4 oracle (`C4_CONTRACT` = §2.1, Kisiwa's O&M overrides, `C4_KNOWN_FINDINGS`), `harness_run` under its own base, and `check_passed` only while the check inputs are unchanged.
- Settled: the bulk load refuses a batch whose envelopes resolve other days than its cover (Site-local and UTC grains, step 7a; `BULK_BATCH_GAP_DAYS`, `BULK_BATCH_TIME_UNREADABLE`); `PostgresEvidenceLedger.site_timezone`.
- Settled (unit 3): `world bench` (B1-B6, `ds7`, five strategy targets; every bench database dropped). Run 1 at `58bb50809` (superseded, its ladder dropped): L0 4.4 s, L1 7.4 s, L2 8.9 s; clone 0.24-0.28 s at 19.7 MB; late billing row +10.00 end to end 9.8 s. Fix round at `68449e49d` (D-DS4.28-33): ladder L0 4.268 s, L1 7.665 s, L2 9.322 s; pipeline 13.497 s per Kobo Site-day (bulk load, mini-depth step and ticks); DS7 not triggered (read literally, owner row 35; L2 9.322 s); projection 7,419 s, information only. Kept and checked (`ALL` PASS, C4 `fails: []`): `assetops_world_audit_l0_53988be3439c` (18,559,459 bytes, 18.6 MB), `_l1_6e55fb8dc4b3` (19.6 MB), `_l2_1906a5d074a0` (19.9 MB); keys under `/opt/assetecon/keys/world/<database>`; manifests in `/opt/assetecon/worlds`.
- Open: DS7 is decided at the first world telemetry (owner row 35); serving a world is row 36 (held).

## 0M - Mto's demand-on-headroom replay (in review, 21 Nov)

Branch `task/0M-mto-headroom` (base main `6c33395ef`, after the 0K2 merge `3b4f06052`); spec `specs/0M-mto-headroom-replay/spec.md` rev 2, rulings D-0M.1-22; packet `packet.md`. No database, no migration, no served text, no money.

- Settled: `runs/headroom_replay.py` `headroom_study` adds a customer's kW to one Site load at its local weekday steps and replays the whole window beside the no-customer replay (full, and a second base run frozen at a reduced inverter limit fed `min(PV, limit)`); headroom days and kWh from the series; extra litres, generator, unserved, starts, month splits, dawn new/cleared dates; every customer id and the reduced run's frozen limit and other needs refused before any port call. Reuses 0K2's helpers only. `host/tests/mto.py`: the Kobo template edited to Mto's manifest facts, loads halved.
- 61-day SIMULATED/MODELLED figures beside the design values in the packet (huller Oct 6 days, 384 kWh, 156.7 L vs 3, 225, 68; reduced 0.24 L a day vs 5); design values unchanged (row 37).
- Open: replacing design values is the owner's (row 37); dawn admissibility and money are `6g`.

## ENV1 - every upload parse under hard limits (in review after fix round 1, 21 Nov)

Branch `task/ENV1-parse-limits` (base main `e9d6cdfb1`); spec `specs/ENV1-parse-limits/spec.md` rev 3, rulings D-ENV1.1-24; packet `packet.md`. No migration, no database, no served text, no guard change.

- Settled: `parse_slots.py` (abstract Unix socket names, `commercial` 2, `reading` 2 (checks) and `reading-send` 1 (sends, one at a time; D-ENV1.18) per network namespace, `ASSETOPS_PARSE_SLOT_NAMESPACE`; tests set their own per process); the envelope holds a host slot at each read; the field process sets its limits before it reads (`CHECK_LIMITS` 512 MiB/30/60, `SEND_LIMITS` 896 MiB/120/270, the send wall 2x the 129.2 s production-shape send, D-ENV1.19); breaches are `ParseLimitBreach` (slot, wall, cpu, memory, killed, crashed) answered with the existing 503 words and logged once; a 5,000-digit cell is `INVALID_VALUE`; the loader reads at most 8 MiB + 1 per file, sizes first, JSON only in the envelope.
- Open: words for `cpu`/`memory`/`crashed` after SC-1a (row 49); waiting-request cap (D-ENV1.12); JSON API body bounds (`financial_api.py`, backlog); limits are per host class (re-measure on a slower one); the gateway ledger's growth slows a send (+1.73 s per 2 MiB send, about 4.5 s per GB; retune on the production ledger's size class); another writer into the same gateway is not bounded by the send pool.

## 0K3 - the replay series reader from stored readings (in review, 21 Nov)

Branch `task/0K3-replay-reader` (base main `e9d6cdfb1`); spec `specs/0K3-replay-series-reader/spec.md` rev 2, rulings D-0K3.1-20; packet `packet.md`. No migration, no served text, no consumer change.

- Settled: `runs/replay_series.py` `SeriesReader.read` (built by `runs/composition.build_series_reader`) turns a Site's accepted readings over whole local days into 0K2's `ObservedSeries` or refuses with a code and subject: configuration before readings, 15-minute means refused never split, `pv_power` never read as available PV, instants only at step starts (off-grid counted), nothing carried, clock-change days refused before the query, `MAX_DAYS` 92, input class from source mode. Proven on R0 (no database), MG-W402-001 and DS3 Kobo in Postgres, and 0K2's 8-day season read back field by field with the same calibration.
- Open: no study on stored readings until a 61-day 5-minute series, Kobo's `pv_available_power` binding (row 48) and `6c`; mid-build Q1 (Kobo's zone is Addis Ababa, not Nairobi).

## 0K4b - the generator's fuel curve and the battery's charge taper (in review, 21 Nov)

Branch `task/0K4b-fuel-curve` (base main `b96d5e978`); spec `specs/0K4b-fuel-curve-taper/spec.md` rev 2, rulings D-0K4.5-7, D-0K4.19-21; packet `packet.md`. No migration, no database, no screen, no guard or template change.

- Settled: pure `packs/generator_curve.py` (fuel line through the no-load rate and SFC x rating, ordered refusals, fuel cap, taper to a 1/20 floor, three handlers; v8's physics, pinned by F12), imported by nothing until 0K4a; Foundation keys `generator-minimum-load`, `battery-charge-taper-start` and their bases on GENERATOR and BATTERY; `GENERATOR_CURVE_NEEDS` on no profile; `host/tests/kobo_assumed.py` (GENERIC_DEFAULT); the first `str | Message` legacy-family seam, `served_text.py`, with the `foundation_property` vocabulary and the `foundation.property_name` and `model_profile.need` statements.
- Open: 0K4a wires the module and the needs into v8 and adds the lab seam (`run_profile_summary`); the rest of each family's migration (Q9); Kobo's real curve and taper values (operator request).

## 0K4c - Kobo's declared season v2 (in review, 21 Nov)

Branch `task/0K4c-declared-season` (base main `ec8e64d3f`); spec `specs/0K4c-declared-season/spec.md` rev 2, rulings D-0K4.8, D-0K4.26; packet `packet.md`. Host test fixture only: no migration, database, screen or guard change.

- Settled: season v2 beside an unchanged v1 in `host/tests/kobo_season.py` (`OVERCAST_V2` 21 days in spells of 1-4, `load_multiplier_v2` 17/20-23/20 on res and clinic, `mill_on_v2` off on Sundays, `season_site_v2` with 0K4b's assumed rows); `season_inputs(..., overcast=None, season=)`; the canonical `inputs_digest` and `windows_digest`; v1 pinned (59d6456b, f2f0088e) and v2 pinned (465ab6e0). Declared and SIMULATED, never a Kobo record.
- Open: 0K4a was not on main, so S7's frozen half and the S8 v8 smoke are 0K4d's V0; 0K4d's `study.json` records the v2 digest.

## 0K4e - dispatch-3.3: a battery-support Candidate needs the energy to reach solar cover (in review, 21 Nov)

Branch `task/0K4e-candidate-energy` (base main `b96d5e978`); spec `specs/0K4e-candidate-energy/spec.md` rev 2, rulings D-0K4.10, D-0K4.11, D-0K4.19, D-0K4.23-25; packet `packet.md`. No migration (a model version is data).

- Settled: `dispatch_v3.MODEL_VERSION = "dispatch-3.3"`; row 5b keeps a Candidate only when (SOC - reserve) x capacity x PCS efficiency covers, with 10 % headroom, the load PV does not cover until PV alone covers it (memoised 5-minute walk on `_Index.energy_to_cover(t)`, means held over their own interval only, read range = window +/- 6 h); else Indeterminate `SHORT`/`GAP`/`NOT_REACHED`/`NOT_CONFIGURED`, stored as the segment's `energy_cover` codes and figures (never `reasons`/`missing` text). Foundation `battery-energy-capacity` and `pcs-conversion-efficiency` are controls (`_configuration`). `plain._segment` and `finding_read.portion_cause` render `dispatch.energy_cover` / `dispatch.energy_cover_cause` (SC-1). `claim_limit_read.SUPPORTED_MODELS` holds 3.2 and 3.3; role coverage stays per instant. One baseline swap (`rows_mini_grid` `unexplained_l` source). S4 fixture F05 continues load and PV to 09:45 so its battery-support Candidate holds (mid-build Q1, default applied).
- Open: Q1's ruling on F05; the md0 mechanism template rebuild (`TEMPLATE_STALE`); the reconcile pass on any demo or telemetry database (coordinator; verifications mixing model versions refuse until it ends); readiness naming an energy-cover Indeterminate (Q10); the dispatch texts' move to SC-1 (Q9); 5c's `test_4_h_kobo_litres` literals follow whichever merges second.

## 0K4a - `mini-grid` v8, the generator takes the load (in review, 21 Nov)

Branch `task/0K4a-dispatch-v8` (base main `b96d5e978`, 0K4b merged in); spec `specs/0K4a-dispatch-v8/spec.md` rev 2, rulings D-0K4.2-4, D-0K4.19, D-0K4.20, D-0K4.22; packet `packet.md`. No migration, no database, no screen, no guard change.

- Settled: simulator `mini-grid` v8 (`decide_v8` ranks a running generator ahead of the battery; `_resolve_cycle` is v7's resolve with the RUNNING allocation by `cycle_charge_split`, 0K4b's fuel curve with a `generator-fuel` balance and tank account at 10 kWh/L, and the charge taper; `_checked_curve` and `_fuel_cap_kw` guard the curve's divisions); v1-v7 byte-identical (N9), v8 pinned by N12 `d6add2a3...5371f11`; backend `MINI_GRID_V8_MODEL` with SC-1 `model_profile.description`/`model_profile.state` served through `served_text` in `run_profile_summary`; `EXECUTABLE_MODELS` and `REPLAY_MODELS` take v8 (N11).
- Open: no world runs v8 yet (0K4f); calibration is 0K4d's; five mid-build readings for the Architect (packet: N7 37 % run, N13 window, N13b, two test-pin edits).

## 5c-fix-r5 - the deep-dive's rev 4 backend fix: no word beside no figure, step bars, no share without a gap (in review, 21 Nov)

Branch `fix/5c-backend-r5` (base main `4b13c0afe`); spec `specs/5c-deep-dive-screen/spec.md` rev 4 §11 "Backend fix", rulings D-5C.26 to D-5C.28; packet `packet-backend-fix-r5.md`. No migration, no screen, no guard change; schema stays `deep-dive-month-1`.

- Settled: `_View.figure_word` builds every figure slot's word and the headline's evidence, None exactly when the figure's value or currency is absent (L9's card word and `words.NO_CURRENCY` gone; `W.word` takes `currency: str`); a heading's word is the weakest of the steps its sum adds; `shares()` returns nothing when R's effect is None or 0; module-level `bridge_bars(effects, gap)` serves each step's `bar` (`left`, `width`, `tone`) and `bridge.scale` as two-place track percentages (A: revenue 0.00/11.38, fuel cost 11.38/88.62). `backend/tests/deep_dive_worlds.py` holds `world_h`, `world_x`, `in_kes`, `gone`.
- Open: the screen fix (§11, `task/5c-unit3-screen`: generator on `deep_dive_worlds`, `dd-na`, track and scale, L1-L5); a gap of exactly 0 with a non-zero rest raises in `tile_rest` (pre-existing, not in this scope).

## 0K4d - the admission rule, the rerun on v8 and season v2, MG-T restated (in review, 21 Nov)

Branch `task/0K4d-rerun-restate`; spec `specs/0K4d-rerun-restate/spec.md` rev 2, rulings D-0K4.9, D-0K4.16, D-0K4.26-30; packet `packet.md`. No migration, database, screen or guard change.

- Settled: `runs/admission.py` (four parts, absolute-then-relative fallback, dawn as `DawnInformation` only) and `admission_measures` on `CaseOutcome`; both study tools take `--model-version {7,8}` and `--season {v1,v2}` (mixed pair `STUDY_FLAGS_INVALID`, exit 2; defaults reproduce 0K2 and 0M), headers carry commit, model, season, S9's inputs digest, site trajectory digest and D-0K4.27's assumption strings (`ASSUMED_DERIVATION`, `MTO_ASSUMED_DERIVATION`, `mto_site_v2`); the 61-day v8/v2 figures: Kobo stop 70 212.75 L a month, reserve 25 59.73, both admitted (all 14 cases admitted); Mto huller 153.88 L a month, reduced inverter 0 L a day; §4.2's Kobo option text restated to one figure per quantity.
- Open: `6c` values the options; the manifest and derived values (0K4m; `check_manifest` H9 counts 6 fewer anchors); the pack's line 5 and §4.3 still name design values; the reduced-inverter 0 is for review.

## WK - the walkthrough database tool (in review, 21 Nov)

Branch `task/WK-walk-world` (base main `3e77a8575`); spec `specs/WK-walkthrough-database/spec.md` rev 2, rulings D-WK.1-14; packet `packet.md`. No migration, no product code, no guard change; no database created or opened.

- Settled: `tools/walk_world.py` (copy, prepare, check, serve, smoke, stop, status, drop) over `world.World` through `WalkDeps(world, http, procs, world_factory, deep_dive, foundation)`; every walk connection through `walk_url` (label rule, `PROTECTED_DATABASES`, `walk_name_ok`, `database_target` name/host/port); copy gated on `current_l2` + `check_state` (one `CREATE DATABASE ... TEMPLATE ... STRATEGY FILE_COPY`); prepare = two `reconcile_month record` + one `build_structure_snapshot build` per tenant-month from `backend/conversions/walk-layer4-v1.json`; check W1-W7 (no stop at first FAIL); serve on 8991/5491 with built envs, refusing 8990/5490 and the 13 Nov tree; smoke S1-S4 (S4 the after-serve census, D-WK.13) with `tools/walk_world_smoke.cjs`.
- Open: the coordinator's run (spec §5, after 3C2 unit 2 and a world build and check); the npm cmdline form `stop` matches is unverified on a live serve; the smoke script carries no `assertHeavySlot` (packet, deviation 8); the one-figure read of the PNGs (D-WK.12) after the run.

## DDR - the deep-dive rehearsal checker (in review, 21 Nov)

Branch `task/DDR-rehearsal` (main with 3C2 unit 2 merged in); spec `specs/DDR-rehearsal/spec.md` rev 3, rulings D-DDR.1-15; packet `packet.md`. No migration, no screen, no statement.

- Settled: `python -m assetops_backend.rehearsal_check` (ten gates G1-G10, one JSON line each, codes and facts only, `DDR_GATE_FAILED G<n> <CODE>`); `StructureSnapshotStore.portfolio_history`; the board-budget profile fixtures and `lakeside-2026-10.expect.json`; runbook sections 6-12 (admit before load, `_test` names); test 1 runs S1-S12 through the commands with the first failing gate G2 -> ... -> none.
- Open: the rehearsal itself and its serve (spec §5, coordinator); MB2 and MB3 defaults (stored profile status `ILLUSTRATIVE`; tariff received drops four screen literals); PF1 (the emulated budget's driver lines make the 5c screen answer 500, `VOCABULARY_UNKNOWN actual_quantity`).

## 0K4m unit 3 - the mock restated to the evaluated figures (in review, held for the owner, 22 Nov)

Branch `task/0K4m-u3-mock` (on `task/0K4m-pack-restate` at 2b); spec `specs/0K4m-pack-restate/spec.md` rev 5 §4, rulings D-0K4.50-.56; packet `specs/0K4m-pack-restate/packet-unit3.md`. Mock only, plus five manifest prose strings (D-0K4.52).

- Settled: the Simulated chip (`srcTag`, title per study's days) replaces the design-value tag; the tagger and the audit read the source set from the fixtures (`SOURCE_PATTERNS`/`SOURCE_LABELS`) and independently (`tools/replay_values.py`); Kobo's settings, KIS-BATT60 and Embakasi per-bus timing read "Not available yet: needs a simulation ..."; admission and dawn lines from `information`; every reader of a removed field reads the evaluator or states its gap; `hand_typed_scan.py` exits 1 on a hit.
- Open: H10 re-base (manifest prose edit), H9 and K10 in commit 6; the browser audit is stale against the IA-1 mock (audit docs left at 18 Nov; browser-audit.md K11 clears on regeneration); P15 as worded cannot fail (P15b does).

## DD1: three operators (in_review; `specs/DD-demo-data/packet-DD1.md`)

- Settled: `lakeside-power`, `harvest-cold` and `metro-bus` onboard from `/2` files (`backend/tests/fixtures/on1/`) with
  devices, topology and EV schedules; nine conversions in `backend/conversions/world/`; `onboard_operator apply --bindings DIR`
  publishes each conversion and enables the gateway and sources in process, idempotently (emulated only). `provision_gateway`
  follows the served tenant (D-DD.35). `tools/dd_check.py` has C-DD1 and C-DD13 live, 18 stubs.
- Left open: Kisiwa and Mto bindings are refused by the product's ONE-per-Site roles (Q-DD1.7); Site document bounds were
  raised (Q-DD1.8); `tools/world.py` L1 does not pass `--bindings` yet.

## DD2b: cold and EV decided books (in_review; `specs/DD-demo-data/packet-DD2b.md`)
- Settled: `world_history.py exports` writes `harvest-cold` and `metro-bus` books for Jul-Oct in their source profiles'
  formats (`world/exports_cold.py`, `world/exports_ev.py`, rendered by `world/profile_csv.py` from
  `backend/conversions/profiles/`, 9 profiles with samples). Expenses use `expenses-illustrative-1` (no ENERGY or PENALTY
  row). Cold revenue and received are `COLD_CHAIN` nodes (D-DD.50). The ledger matches each month's crate-days exactly,
  and its peak is at most the room capacity. The EV roster comes from one function, `roster_rows` (D-DD.52). Every DS1b
  record lands in one place (D-DD.54, `world/books.py`). `ev-departures` bool is admitted and stored as a JSON boolean on
  PostgreSQL.
- Left open: the source-system switch at load for cold invoices/receipts/ADJUSTMENT (Q1, DD5). Receipts/tickets use the
  `row_digest` version and the EV invoice Line column is split (contract rules). TARIFF_SCHEDULE staging is DD2a's.
  NODES unify with DD2a at merge.
