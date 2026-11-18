> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 5 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## T027 phase 1 - Commit, ingestion and Site > Evidence

Packet `.agent/T027-phase-1-review-packet.md`; handoff `.agent/T027-phase-1-handoff.md`.
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
`.agent/T028-review-packet.md`; handoffs `.agent/T028-phase-{1,2,3a}-handoff.md`,
`.agent/T028-presentation-cp{1,2a}-handoff.md`; final layout evidence
`.agent/T028-layout-evidence-final.txt` (presentation cp2b).

- Analytic `analytics/dispatch.py` (model `dispatch-2`, `assess()`); rules and
  thresholds in `backend/tests/dispatch_decision_table.md`. Classification uses
  accepted evidence only; never observed PV as capability, never simulator truth.
  Fix round 1 (Codex R1-R5, `.agent/T028-review-packet.md` "Fix round 1"):
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

Packet `.agent/S2-02-review-packet.md`; walkthrough `.agent/S2-02-owner-walkthrough.md`; handoffs `.agent/S2-02-phase-{1,2,3a,3a2,3b}-handoff.md`, `.agent/S2-02-corrections-handoff.md`.

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

- Questions-7 (Q37-Q40) await the Architect (fail-closed defaults shipped); questions-5/6 answered in `.agent/architect-batch-answers-4.md`.
- C3/N2 full seeded layout run still unverified.
- Crash/resume 202 and closing-boundary rejection are Postgres test evidence only; the rejected sibling is live via the labelled fault fixture.
- Generator-status run and capability channels unconfigured; no S3 projection; physical devices remain a pilot gate.

## S3-01 phase 1 - Role vocabulary and `s3-dispatch-cases-v1` fixture (reviewed, accepted with carries)

Built on `task/S3-01-dispatch-assessment` (1a `e68da1c`, 1b `7e9da8c`..`f508bae`); packet `.agent/S3-01-phase-1-review-packet.md`, questions `.agent/S3-01-questions-1.md`.

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

Built on `task/S3-01-dispatch-assessment` (`75886d1`..HEAD); packet `.agent/S3-01-phase-2-review-packet.md`, questions `.agent/S3-01-questions-2.md`, table `backend/tests/dispatch_3_decision_table.md`.

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
- Questions Q1-Q8 in `.agent/S3-01-questions-2.md` (controls at cutoff vs as-accepted, minimum runtime mapping, day windows, fixture-epoch default read, in-flight cutoff, interval key anchoring).
- Same-epoch overlap (10-04) yields a window `INDETERMINATE` with no intervals (generator series ambiguous).

## S3-01 phase 3a - Durable dispatch read, comparison and cutover gate (active, phase review pending)

Built on `task/S3-01-dispatch-assessment` (`aaa47ae`..HEAD); packet `.agent/S3-01-phase-3a-review-packet.md`, questions `.agent/S3-01-questions-3.md` (Q9-Q13), handoff `.agent/S3-01-phase-3a-handoff.md`.

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

Built on `task/S3-01-dispatch-assessment` (`05f9b4d`..HEAD) under `D-2026-10-11-s3-phase-3a-version-and-cutover`. Packet: the "dispatch-3.1" section of `.agent/S3-01-phase-3a-review-packet.md`. Handoff to 3b: `.agent/S3-01-dispatch-3-1-handoff.md`. Questions: `.agent/S3-01-questions-4.md` (Q14-Q16).

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

Built on `task/S3-01-dispatch-assessment` (`b04b904`..closeout). Packet: `.agent/S3-01-review-packet.md`; questions Q17-Q22 in `.agent/S3-01-questions-5.md`.

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

Branch `task/S4-05a-provenance-binding-resolver` from main `fd7afd2c`. Handoffs `.agent/S4-05a-phase-1-handoff.md`, `.agent/S4-05a-phase-2-handoff.md` (resolver field contract for S4-05b); packet `.agent/S4-05a-review-packet.md`. Authority `D-2026-10-15-s405-stored-demo-provenance`, `.agent/architect-S4-05-answers.md`.

- Migration `0017_evidence_publication`: insert-only `evidence_publication` (SYSTEM actor, class CHECK: authored fixture ID+version or run ID+64-hex run digest) and `batch_publication_link` (composite FKs to the exact batch and publication commitment); UPDATE/DELETE triggers; downgrade refuses while publications exist (tested).
- Ledger writer (`postgres_evidence_ledger.py`) is the only provenance writer: `register_publication` and `open_batch` share `pg_advisory_xact_lock` on (tenant, Site, external batch ID); registration refuses after any admission, needs a registered gateway/source and (phase-1 review M1) a `SIMULATED` gateway for every class; `open_batch` binds the exact commitment or refuses 409 `PUBLICATION_MISMATCH`. Unpublished uploads stay accepted and unbound.
- Domain `evidence/publication.py` (authored records, run attestation), `runs/source_publication.py`, server CLI `publish_source.py`; no HTTP route.
- Resolver `evidence/source_provenance.py` (pure, route-safe) + read-only ledger methods `link_rows`, `finding_revision_evidence`, `consequence_inputs`; `composition.build_source_provenance`. FindingRevision cited set; consequence = union of its FindingRevision set and its own power-interval IDs, with `finding_revision_state` and `CONSEQUENCE_POWER_INPUT_CONFLICT`. Several run IDs -> MIXED (N-L2). Missing/foreign-Site/broken precede MIXED. Cross-tenant IDs read as not found (no disclosure).
- Rule 8 (`configuration-persistence.ps1`): ledger INSERT-only provenance; split `UPDATE|DELETE FROM|TRUNCATE <provenance table>` refused in any module (review L1); HTTP modules may not reference designation.
- Not changed: every read DTO and the date/spec source heuristic (S4-05b cuts over).
- Open: N-L1 producer registration in a non-route module (S4-05b); migration re-chain vs LR-01/S6-01a; run identity digest is not re-verified after registration (file-backed run store); lock key is the admission slot, stricter than the packet wording; no TRUNCATE trigger (rule 8 only); S5-01 amendment (N-L3).
## S4-07 - evidence decided_at on DB time (built, review pending)

Branch `task/S4-07-evidence-decided-at` from main `5bfff665`; packet `.agent/S4-07-review-packet.md`.

- `PostgresEvidenceLedger.decide_chunk` takes one DB `clock_timestamp()` per chunk after the batch row lock (`_decision_instant`), inside the write transaction; it stamps every newly decided ordinal's `decided_at` and a newly inserted `recompute_job`'s `available_at`/`created_at`. A widened PENDING job keeps `created_at` and has `available_at` lifted to `GREATEST(available_at, decision)` (Known Deviation 1; closes the cutoff-sampled-before-commit race, proved failing without it).
- `EvidenceLedger.decide_chunk(..., completed_at=)` replaces `decided_at=`: `BatchIngestionService` passes its app clock only for the receipt `completed_at`; `received_at` unchanged.
- `test_decision_clock_override` (constructor kwarg/attribute) is test-only; `main.py`/`evidence/composition.py` never set it. Deterministic fixtures (S2 ledger/site evidence, S3 dispatch, S4 CaseRunner, S4 consequence work) use it.
- Proofs: `tests/test_s4_evidence_decided_at_postgres.py` (production path, fast/slow app clocks: ingestion-first, worker-first with L-b lock wait, cutoff-sampled race, uncommitted-job tick; crash/replay across two windows, duplicate-only chunk, another Site). F-A test re-driven as override-path, skew 120 s (R-2).
- Open: manual app-clock `process-jobs` beside the tick (README-db); configuration `recorded_at` vs `reconcile`; `clock_timestamp()` vs `now()` (an instant predating a batch-lock wait) is reasoned, not mutation-proved (no batch-lock contention test).
## LR-01 - late-reading series and money limit (phases 1-2 built, slice review pending)

Branch `task/LR-01-late-reading-series-and-money-limit`; handoffs `.agent/LR-01-phase-1-handoff.md`, `.agent/LR-01-phase-2-handoff.md`; packet `.agent/LR-01-review-packet.md`; decision `D-2026-10-15-lr01-source-time-cohort`.

- Clock attestation: append-only `source_clock_attestation` (migration 0014), SYSTEM-only CLI `assetops_backend.record_clock_attestation`, `SIMULATED` proof class only; attestation change requeues old+new validity (`postgres_assessment_store.record_clock_attestation`).
- cohort-4 / `dispatch-3.2`: source-time order only under one covering attestation (`analytics/cohort.py`); a reading's clock reason depends only on attestations touching it (phase-1 review F1); overlap checks span attestation boundaries (L1).
- Matcher `finding-episode-3` (`analytics/finding_episode.py`): `claim.end_reason` (`OFF_OBSERVED|CANDIDATE_ENDED|OPEN_BOUND|SERIES_LIMIT`) and `claim.series_limits` with exact lineage; a cut tail drops its dependent `OPEN_BOUND`.
- Shared money gate `financials/money_eligibility.py` (`money-eligibility-1`): PENDING_REASSESSMENT > WITHHELD_GENERATOR_SERIES > ELIGIBLE, read-derived on every read, fails closed. Consumed by `ConsequenceReadService(eligibility=...)` (gates `presented_as_current`/`current_amount_shown`), `finding_api.bridge_consequence` (states + `recorded_consequence_revision_id`), and `scheduling/upstream.py` `findings[].money_eligibility` for S5-01. ELIGIBLE is not an amount authorization.
- Migration 0015 `0015_finding_returning_basis`: FindingRevision basis may return (A -> B -> A); replay guard compares with the latest revision only.
- UI: Financials bridge shows withheld/pending with the refused span and an exact link to the recorded consequence; Finding page states a SERIES_LIMIT end.
- Walkthrough: `tools/s402c_late_power_walkthrough.py run|attest|tick|serve|drop --db assetops_lr01*`; browser claims `tools/lr01-money-evidence.mjs`.
- Open: real-source clock proof has no write path (by design); S5-01 owns its own UI over the seam; the schedule install gate stays closed until this slice is reviewed and merged; broader per-analytic input/clock coverage remains the owner analysis-input backlog.

## S4-05b - registered producers, stored-source reads and owner walkthrough (phases 1-2 built, in_review)

Branch `task/S4-05b-producers-reads-walkthrough` (unmerged; owner W1 copy checkpoint first). Packet
`.agent/S4-05b-review-packet.md`; owner steps `.agent/S4-05b-owner-walkthrough.md`; ruling D-2026-10-16-s405b-label
(`.agent/architect-S4-05b-answers.md`).

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
  `var/s405_*`, API 8935/web 5435, `serve --case`); browser claims `tools/s405-provenance-evidence.mjs`.
- S5-01 packet amended (shared contract item 5).
- Open: owner copy approval; `ATTESTED_REAL_SOURCE` class (separate task); `MoneyInputs.provenance_resolved`
  default True for unit tests; per-row provenance queries in consequence history; Action fixture size.
## S3-02a - selected-assessment capability and claim-limit read (built, slice review pending)

Branch `task/S3-02a-capability-read` (base main `71009bf6`, unmerged); packet `.agent/S3-02a-review-packet.md`; S3-02b handoff `.agent/S3-02a-handoff.md`. No migration.

- Read: `analytics/claim_limit_read.py` `ClaimLimitReadService.read(tenant, site, day, revision_id, rule)`, rule `s3-claim-limit-1` over `dispatch-3.2` only (`SUPPORTED_MODELS`). Capability = per required role (`generator_state`, `feeder_demand`, `pv_available_power`, `pcs_discharge_capability`, `battery_soc`) exact COVERED/MISSING/POOR_QUALITY/CONFLICTED/NOT_EVALUATED spans with minutes and pinned accepted Evidence IDs, derived from the revision's stored segments (unknown problem text fails closed to MISSING). Claim limit: interval ceiling CANDIDATE_AVOIDABLE/NECESSARY (COMPLETE or LIMITED, `supported_minutes` = that class's segment sum) or INDETERMINATE; withheld (INDETERMINATE) on unusable cohort or a non-covered required role inside a claim-carrying segment. Current ceiling only when the window projection is CURRENT and the revision is in the selected run; otherwise `currentness` PENDING/FAILED/STALE_PROJECTION/HISTORICAL and only `historical_ceiling`. No revision -> `UNASSESSED` + `NO_REVISION_SELECTED`. Window revisions list `interval_ceilings (top level only when CURRENT; otherwise under historical_ceiling)`, no single ceiling.
- Store: `PostgresAssessmentStore.claim_limit_snapshot` reads the window snapshot and the revision detail in one REPEATABLE READ snapshot (`_window`, `_revision_detail` extracted; existing methods unchanged in behaviour). Reads only; no new SQL writer.
- Route: `claim_limit_api.py` `GET /api/sites/{code}/performance/dispatch/windows/{day}/claim-limit?revision=&rule=`; order access 401/403 -> scope 404 -> 503 -> 422 (`INVALID_REVISION_ID`, `UNSUPPORTED_RULE_VERSION`) -> Performance gate 409 `PERFORMANCE_CUTOVER_CLOSED` -> read (404 `ASSESSMENT_REVISION_NOT_FOUND`, 422 `REVISION_OUTSIDE_WINDOW`/`UNSUPPORTED_RULE_VERSION`, 409 `ACCEPTED_LINEAGE_ABSENT`). Wired in `main.py` with `performance_gate`; composition `build_claim_limit_read_service`.
- Fixture: `backend/tests/s3_claim_limit_records.py::build(runner, url)` (S4 `CaseRunner`, Batch V2 + S3 worker) -> manifest `s3-claim-limit-records-v1` (days 10-06 full-candidate, 10-08 missing-pv, 10-11 poor-quality-conflict, 10-13 late-revision with `withdrawn`, 10-15 stale-selection). Normalised sample responses `backend/tests/fixtures/s3_claim_limit_api_samples.json`.
- Tests: `test_s3_capability_read_postgres.py`, `test_s3_claim_limit_postgres.py` (gate, fail-closed and currentness mutations proven).
- Open: registry `I-capability-read`/`I-claim-limit-read`/`I-S3-02a` stay open until review; Necessary/open-bound/cohort/configuration/absent-lineage are proven by mutating the real snapshot, not by separate ingested cases; S3-02b UI and walkthrough; S6-02a's `0019` does not interact (no migration here).

## S3-02b - Evidence Analysis selected claim limit UI (built, in_review; owner walkthrough before merge)

Branch `task/S3-02b-claim-limit-ui` (base main `8b5d8137`, S3-02a merged); packet `.agent/S3-02b-review-packet.md`; owner steps `.agent/S3-02b-owner-walkthrough.md`. Frontend and a walkthrough tool only; no backend change, no migration.

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

