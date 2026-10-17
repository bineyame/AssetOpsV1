# W2-00 — Ordinary source events and interval evidence

Status: implementation-ready (planned). Size S; one phase. Branch `task/W2-00-source-events` from merged main; independent review before merge. USER_REVIEW_REQUIRED: false. This shared non-UI source contract unlocks W2-02 and W2-05b; it creates no cold/EV assessment or claim.

## Binding design

- `.agent/W2-technical-design-cold.md:5-23` owns SourceEnvelope v4 exact shapes, version dispatch, mapping/refusals, S2 intake, deduplication, storage and read; `:25-31,36-38` owns migration `0020_w2_source_event`, downgrade and transactional collision order; `:91` owns closed cold/EV mapping entries; `:191-193` owns required cases. `.agent/architect-W2-design.md:59-64` sequences the slice. Decisions `D-2026-10-17-w2-design` and `D-2026-10-17-w2-techdesign-cold` apply. Existing v3, Stage v1/v2 and private-world boundaries remain as specified there.

## Phase 1 — v4 admission through ordinary evidence

Extend the v3 authenticated gateway/Batch V2/S2 path with a distinct v4 parser and pinned new publication profile. Support the exact v4 measurement, cold/EV EVENT and EV interval-delta forms, closed `(device_id,signal_id)` mappings, typed refusals, append-only accepted event columns and `/evidence/records` family/kind read. Keep v3 parser, accepted rows, receipt bytes and dedup semantics unchanged. Apply `0020` after `0019_verification_core`; preserve tenant/Site FKs, uniqueness, rejection ordinal, conflict reference, savepoint and reread precedence. No direct product write from Lab truth.

Acceptance tests:

1. Golden v3 vector and Receipt V2 bytes remain unchanged. v4 numeric/state/event and EV delta round-trip canonically; exact keys/nulls, UTC, value/unit, kind/outcome, event/session/connector scope and source-time validity hold. Reject v4 under v3, missing correlation/session, unknown kind, invalid outcome/unit/time, private field, incompatible mapping, cross-tenant binding and malformed delta with the design's exact code and persisted ordinal disposition.
2. Replay same message bytes and same event under a new message ID: duplicate with first accepted reference. Changed message SHA gives byte-stable `MESSAGE_CONFLICT`; changed event identity SHA gives `EVENT_ID_CONFLICT`; distinct EV START collision gives `SESSION_ID_CONFLICT`. Test message+event and event+session double collisions, concurrent race loser, unlisted unique violation propagation, distinct contradictory terminal events accepted, and all receipt counts/reference fields after reload.
3. Upgrade from `0019` to `0020` with preexisting v3 evidence and compare rows/reads. Downgrade refuses while v4 event/delta, new conflict or cold job exists, without deleting evidence; after removing only test-created blockers, downgrade restores old checks/nullability and v3 reads. Probe composite Site FKs, partial unique indexes and append-only trigger. Run statement-level rule-8 probes (`python tools/writer_guard_probes.py`) plus applicable architecture/workflow guards and registry checker. Run one full backend suite on the final slice revision, private `*_test` database, per `backend/TESTING.md`; retain JUnit evidence of zero failed/skipped tests.

## Registry and review

W2-00 is a prerequisite shared source-format packet. The current registry has no dedicated W2-00 node; leave existing resolved S2 nodes and all statuses unchanged until independent graph review. Fresh independent review verifies the exact `0020` migration and replay vectors before coordinator merge.

## Architect questions

None; the cited design specifies the contract.
