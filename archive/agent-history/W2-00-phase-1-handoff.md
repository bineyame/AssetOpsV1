# W2-00 phase 1 handoff — PARTIAL (survey and plan only; no code yet)

Branch `task/W2-00-source-events` at `9c21aabf`; worktree clean apart from this file. The context budget ran out during the survey (about 140k tokens), so the slice stops here, as the brief requires. Resume from "Build order". Settle the open questions first: the brief says to stop rather than choose.

## Open questions (unspecified in the packet or design; need the Architect or coordinator)

1. **What the event-identity SHA covers.** The rule "changed event identity SHA → `EVENT_ID_CONFLICT`" and "identical event under a new message ID → `DUPLICATE`" needs a digest that leaves out transport fields. Envelope SHA cannot serve, because `message_id`, `sequence` and `published_at` change on retransmission. No column is specified for it, so it would be computed from the stored `envelope_text` at reread time. The design does not say which fields it covers.
   - Candidate: SHA-256 of canonical JSON `{source, timing minus published_at, payload}`, without message or mapping.
2. **Possible typo in migration `0020`.** It says "`conversion_kind='INTERVAL_DELTA'` requires kWh…", but `conversion_kind` holds binding conversions (`IDENTITY`/`ENUM`). It probably means `measurement='INTERVAL_DELTA'`.
   - Candidate: a CHECK on `(measurement='INTERVAL_DELTA' OR conversion_kind='INTERVAL_DELTA')`, which satisfies both readings.
3. **Batch V2 refuses invalid envelopes before S2 can record a disposition.** `contracts/assetops_contracts/ingestion_batch_v2.py:203` parses every envelope with the strict v3 parser and refuses the whole batch with `INVALID_ENVELOPE`. Parser-level v4 refusals therefore never reach per-ordinal `evidence_rejection`/disposition. Acceptance 1 demands "persisted ordinal disposition", and the design says "every refusal writes `evidence_rejection` and one ordinal disposition".
   - Candidate: leave v3 texts strict and unchanged. For texts stating schema 4, or schema 3 carrying a v4-only kind (`EVENT`, `INTERVAL_DELTA`), the batch reads only the header fields (message/source/mapping) for its homogeneity and order checks. The S2 dispatcher then decides `SCHEMA_UNSUPPORTED` or the v4 parse codes per ordinal.
4. **Where parser-level delta and session faults land.**
   - The `EV_DELTA_*` codes are listed only as S2 `REJECTED` codes. Candidate: the v4 parser raises them for a non-kWh delta, a non-positive interval or a negative value.
   - A delta missing its session or connector ID has no named code. Candidate: `CORRELATION_INVALID`.
   - Interval-delta alignment is unspecified. Candidate: mirror `INTERVAL_MEAN`, with `interval_end == source_time`.
5. **Where the mapping entry and the "pinned new publication profile" live.**
   - The v3 allowlist is the acquisition-snapshot `bindings` rows, not `SourceMappingEntry`:
     - backend builder `backend/assetops_backend/sites/binding_alignment.py:65-141`;
     - gateway strict key set `gateway/assetops_gateway/snapshot.py:162-172`;
     - backend reader `backend/assetops_backend/evidence/ledger.py:200-212`.
   - `SourceMappingEntry` reads schemas {1,2} only.
   - Publication profiles live in `backend/assetops_backend/runs/profiles.py:2031`. A cold profile needs the W2-02 model pack.
   - Candidate:
     - Snapshot binding rows gain five optional keys (`allowed_record_kinds, allowed_outcomes, requires_correlation, requires_session, allowed_units`). Absent keys parse as None in both the backend reader and the gateway verifier.
     - A closed contract table `V4_CHANNEL_MAPPINGS` in `source_envelope_v4.py` holds the §4 cold tuples plus the two reserved EV tuples, as `simulator-lab-gateway-cold` v1 pinned to schema 4. S2 refuses `MAPPING_INCOMPATIBLE` when a binding row's entry is absent or differs from the closed entry.
     - Registering the runtime publication profile and producing v4 at the gateway are deferred to W2-02, recorded as a Known Deviation.
6. **Cross-tenant binding.** S2 has no existing cross-tenant refusal test; only the DB composite FKs exist (`0005:202-208`). Should the expected outcome be the whole-batch `CONFIGURATION_UNREGISTERED` (the binding set is looked up under the principal's tenant), or something else?
7. **Recompute for v4 acceptances.** `_coalesce_job` enqueues `RECOMPUTE_DOMAIN='dispatch'` for every acceptance. Should v4 events enqueue nothing in W2-00, or keep the current behaviour? Candidate: keep the current behaviour, since W2-03 adds `cold_chain`.
8. **Read routes.** `/evidence/records` has a Postgres path (`ledger_reads.records` → adapter `records_page` at `postgres_evidence_ledger.py:735`) and a file-backed `read_model.records`. Candidate: add the family/kind filters and the new fields to the Postgres path only.

## Survey anchors

- **v3 parser:** `contracts/assetops_contracts/source_envelope_v3.py`.
  - Exact key sets are at :336-344 and `_exact` at :347.
  - Message id is `v3_message_id` at :113; it is reused by v4, which retains v3 identity.
  - The v3 parser returns `INVALID_PAYLOAD`/`UNKNOWN_FIELD` for v4 kinds, never `SCHEMA_UNSUPPORTED`. The dispatcher must therefore pre-screen schema 3 for v4-only kinds.
  - `ENVELOPE_MEASUREMENTS` is in `source_envelope.py:110`; leave it unchanged.
- **S2 pure decision:** `backend/assetops_backend/evidence/ledger.py:268` `decide`. It parses with v3 at :272. `Accepted` is at :235 and `BindingBasis` at :100.
- **Postgres ledger:** `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py`.
  - `decide_chunk` :389 → `_persist` :464, then the accepted_evidence INSERT at :472-497. It uses only `ON CONFLICT ON CONSTRAINT accepted_evidence_message_unique DO NOTHING`; keep it.
  - The message reread is at :500-513 and `_reject` at :515.
  - Add: a per-ordinal savepoint (`c.begin_nested()`) around the INSERT; catch a unique violation whose constraint is `accepted_event_identity_unique` or `accepted_ev_start_unique`, re-raise anything else; then reread in the order message → event → START (design §2, `.agent/W2-technical-design-cold.md` line "Every accepted-evidence INSERT…").
- **Receipt and read counts:** `backend/assetops_backend/evidence/ledger_reads.py:232-233,376`. Change these to `kind IN (MESSAGE_CONFLICT, EVENT_ID_CONFLICT, SESSION_ID_CONFLICT)`. `record_payload` is at :145 (add the 7 fields, null for old rows); `records` is at :310.
- **API:** `backend/assetops_backend/evidence_api.py:411-440`. Pass the `family`/`kind` query params to `imported_reads.records`.
- **Batch V2:** `contracts/assetops_contracts/ingestion_batch_v2.py:149-176` (homogeneity) and :203 (parse).
- **Migration:**
  - Head is `0019_verification_core` (`down_revision` pattern at `0019:28-29`; refuse-downgrade pattern at `0019:251-260`).
  - `accepted_evidence` DDL is at `0005:161-217`. `family` has no CHECK today. `evidence_rejection_conflict_kind` is at `0005:239-241`.
  - `ledger_append_only()` triggers at `0005:310-321` already cover the new columns.
  - `recompute_job.domain` has no CHECK.
- **Rule 8:** `tools/checks/configuration-persistence.ps1`.
  - `$ledgerTables` is at :634.
  - `$ledgerConflictAllowed` is at :700. Its content already equals the design regex; the design asks for the double-quoted form.
  - The per-statement ledger checks are at :818-834 and :922-932.
  - Today only the Foundation store is barred from ledger tables (:918). Add "only the ledger writes accepted_evidence/evidence_rejection/ingestion_disposition" (`recompute_job` is shared with the assessment store).
  - Add "every `INSERT INTO accepted_evidence` carries the message DO NOTHING target", with a vacuity count, and a collision-order check (for example, an exact single `_REREAD_ORDER = (_REREAD_MESSAGE_SQL, _REREAD_EVENT_SQL, _REREAD_SESSION_SQL)` in the ledger).
- **Probes:** `tools/writer_guard_probes.py`.
  - The `NEGATIVE` list is at :58; the ledger entries are near :193-210 and `WRITER_CONTROLS` is at :234.
  - Add:
    - pass probes for the event-column insert and the message target;
    - fail probes for the event partial-index target, `DO UPDATE` and a foreign writer;
    - two collision-order fail probes: event before message, and session before event.
- **Tests to extend:**
  - `backend/tests/test_s2_evidence_ledger_postgres.py`. The `Kit` at :62 builds v3 envelopes from the pinned Kobo snapshot.
    - No cold or EV binding can be published before W2-01/W2-02. Candidate: Postgres v4 tests patch `ledger_service.basis_from_snapshot` to add v4 channel `BindingBasis` entries that reuse real binding_revision/asset IDs.
  - Snapshot optional-key parsing is tested purely through `basis_from_snapshot`.
  - Golden v3 tests are at `gateway/tests/test_wire_contracts.py:36,67,74,122`.
  - Receipt tests are at `backend/tests/test_s2_receipt_v2.py`. There is no pinned receipt-bytes fixture, so add one for `MESSAGE_CONFLICT` before changing reads.

## Build order (once the questions are answered)

1. `contracts/assetops_contracts/source_envelope_v4.py`:
   - parser and canonical text;
   - `V4_MEASUREMENTS`;
   - kind→outcome allowlist;
   - closed channel table;
   - dispatcher `parse_canonical_source_envelope_text` (v3|v4);
   - golden vectors `contract-fixtures/source-envelope-v4-vectors.json`.
2. Batch V2 v4 header path (Q3).
3. Migration `0020_w2_source_event` (upgrade and refusing downgrade).
4. `decide` v4 branch, then `_persist` savepoint and ordered reread.
5. Reads, API filters and receipt counts.
6. Rule 8 and the probes, each proven to fail.
7. Tests, `tools/check-all.ps1`, one full backend suite, review packet.
