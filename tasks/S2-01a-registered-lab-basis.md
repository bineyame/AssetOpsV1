# S2-01a — Registered Kobo Lab basis

Status: implementation-ready on `task/S2-01a-registered-lab-basis`; independent review before S2-01b
USER_REVIEW_REQUIRED: false
Milestone: S2 Evidence
Depends on: merged S1 Foundation (`main` at `26d013b`)
Architect cuts: `D-2026-10-07-s2-edge-split-and-demo-source`, `D-2026-10-08-s1-bindings-roles-and-snapshot`
Visible reference: v6.9 manifest `lab`, especially Gateway & Ingestion; only the registered Draft/run basis becomes real here.

## Result and boundary

An imported KOBO-001 Draft can be created and run from one selected effective, registered Postgres Foundation plus SignalBinding snapshot. The Lab shows the exact frozen Foundation revision, binding revision, snapshot schema/hash and selected source time after reload. A later configuration publication affects a new Draft, never an existing one. Existing unimported YAML Sites retain their current Lab path. Imported Commit remains unavailable until S2-02; this slice creates no accepted Evidence, receipt, durable gateway queue or V3 identity.

S1-02 stores canonical combined snapshot bytes and SHA-256 in each binding revision. The S1 download (`GET /api/sites/{id}/foundation/snapshot?at=&knowledge_at=`) is development-tenant scoped, not gateway authenticated. S2-01a uses the same immutable contract through a server-side read; do not claim a credential boundary that S2-02 has not built. The selected time is the run's declared source interval start; one immutable basis must cover the whole run interval, or setup refuses before allocating a run. A selected revision that is absent, not effective, not registered, incomplete, or hash-invalid is unavailable, with the actual reason shown. Do not fall back to the YAML Site or current Foundation.

## Acceptance criteria

1. **Registered selection.** Imported KOBO-001 appears in Lab setup with its available effective Foundation/binding basis. Setup reads the S1 Postgres registry and pinned combined snapshot, verifies its stored SHA-256 and schema, and validates the declared run interval against the selected valid period. It refuses a mismatched requested version or period with a specific reason and no Draft. S1 configuration Readiness remains about declared mappings, not live telemetry.
2. **Kernel input.** Map the selected public Site topology, reserve control, registered device/source and signal roles to the existing Lab run input. Preserve scenario and model-profile resolution and private Lab causes/oracle inside Lab storage. The public device report boundary may contain only observations available to a device and public registered identifiers; it cannot read or serialize world causes, controller intent or oracle. The S2-01b adapter will consume that report boundary.
3. **Frozen run.** Persist the exact selected Foundation revision ID/version, binding-set ID/version, snapshot schema/hash, selected time and canonical snapshot bytes or a durable immutable reference on the Draft. Reopen Draft, execution and Stage reads after process restart and show the same basis. If a later Foundation or binding publication changes the current basis, the old run keeps its original basis and a new run selects the new one. An explicit earlier selected time still resolves its then-effective registered basis when available; it never silently selects today's version.
4. **Controls and history.** Imported registered Draft setup, start, step and run-to-end operate through the frozen basis. A missing or unavailable basis keeps those controls blocked with a useful reason. `GET /runs/{run_id}/stage` and run history for pre-import YAML Drafts remain read-only and visibly labelled `LEGACY_FILE`; a pre-import Stage cannot be stepped, reinterpreted or Committed under a new registration. New imported-run Stage inspection is labelled as registered but makes no accepted-evidence claim. Both the UI Commit control and server Commit route refuse every imported run until S2-02 delivery exists, including a newly completed one.
5. **Failure integrity.** A Postgres outage, unsupported snapshot schema, missing bytes or digest mismatch fails closed and leaves no partial Draft or run advancement. Current registration edits cannot rewrite the pinned bytes. Close S1-02 carry n5 under the Architect answer in `.agent/planner-S2-questions-2026-10-08.md`: historical download availability must be tested separately from byte immutability. Until that answer lands, a 409 from the S1 snapshot contract blocks new setup; no cached/YAML substitute is allowed.

## Built anchors and bounded implementation phases

Keep each phase reviewable within roughly 120k implementer context; commit each phase on this task branch, then review the complete slice.

1. **Selection and freeze:** `backend/assetops_backend/foundation_api.py` snapshot route, `sites/binding_service.py::acquisition_snapshot`, `sites/binding_alignment.py` canonical bytes, `sites/cutover.py` imported guard, `runs/service.py::RunSetupService` and the run record/serializer. Add a read-only registered basis adapter at the Lab setup boundary; do not make the legacy YAML repository authoritative for imported codes. Pin and reload the basis with focused setup/period/hash tests.
2. **Execution and inspection:** `backend/assetops_backend/simulator_lab_api.py` Draft/start/step/run-to-end/Stage/Commit guards, `host/lab_execution.py` and the Lab frontend. Drive the existing kernel from the frozen basis, expose basis and configuration refusal, preserve legacy Stage reads, and guard Commit server-side. Use the existing `simulator/assetops_simulator/observation/` and `gateway/` public-report boundary as the S2-01b handoff, without building its outbox here.

The implementation may choose internal adapter and persistence factoring. Do not migrate old Lab artifacts, rewrite `var/sites`, introduce physical protocol parsing, gateway credentials, SQLite, Batch V2, central diagnostics, Evidence or analytics in this packet.

## Reviewer path and checks

- On a fresh Postgres test DB, apply migrations, import/convert KOBO-001 using the S1 documented commands, and verify its registered snapshot response/hash. Create a Kobo Draft at a period with complete bindings; start, step, finish and reopen it after restart. Inspect the visible basis and public report without exposing private cause/oracle.
- Publish a later reserve or binding revision using the S1 UI/API. Create a second Draft at its effective time; compare both frozen revision IDs and hashes after reload. Select an earlier time and verify the earlier registered basis. Try an interval that crosses a configuration boundary and verify a typed setup refusal with no Draft.
- Make a KOBO-GAP-001 or missing-binding case and a simulated store/hash failure. Confirm a specific blocked state and no YAML fallback. Open a pre-import Stage: it remains labelled legacy and read-only. Directly POST Commit for both old and new imported runs: both refuse, and Site Evidence is unchanged.
- Run focused backend/host/simulator and frontend tests for changed setup, execution, reload and guards; run the repository architecture/workflow checks and frontend build. Record commands and results in the review packet. A full gateway/ingestion suite belongs to S2-01b/S2-02.

Registry comparison: `queue_baseline_nodes` still owns `A-lab-registered-basis`, `I-lab-registered-basis` and `I-S2-01a` here; `I-edge-outbox` and later evidence nodes remain with S2-01b onward. No baseline node moves in this refinement.
