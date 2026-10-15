# S4-05a phase 1 - independent review

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review4`, branch
`review/S4-05a-phase-1` at `11fad416`; diff `fd7afd2c..11fad416` (build `2dd7b92e`, handoff `11fad416`).
Judged against `tasks/S4-05a-provenance-binding-resolver.md` phase 1, `tasks/S4-05-stored-demo-provenance.md`
shared contract 1-2, `.agent/architect-S4-05-answers.md` (Q1, rule 8, Follow-up M1) and the brief.

## Verdict

**Accept with M1 fixed on the branch.** One Medium (an authored designation is accepted on a `LIVE` gateway,
and a test asserts it). Four Lows; none blocks.

## Findings

### M1 (Medium, contract gap) - authored designation accepted on a `LIVE` gateway

- `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py:328` checks gateway mode only for
  `REGISTERED_SIMULATION`. `backend/tests/test_s405_publication_postgres.py:467-471` positively asserts that
  an `AUTHORED_DEMONSTRATION` publication on a freshly registered `LIVE` gateway/source is created.
- Follow-up M1: "A real gateway, even with `source_mode=LIVE`, has no positive source designation from S4-05
  and cannot show current money yet"; real-source designation is the separate open node
  `I-attested-real-source-provenance`. Authored verification checks only the spec's declared ID/version and
  canonical bytes, not that the bytes came from the fixture (disclosed in the handoff), so this path lets the
  operator CLI put a positive, immutable, un-revocable `AUTHORED_DEMONSTRATION` binding (later
  "Demonstration data" plus current-money eligibility in S4-05b) on any batch a `LIVE` gateway uploads.
  Ingestion enforces batch `source_mode` = gateway mode (`ledger_service.py:115,201`), so the gateway mode
  is the right check.
- Fix: refuse `AUTHORED_DEMONSTRATION` (both classes) unless the gateway is `SIMULATED`, under the lock
  (e.g. `GATEWAY_NOT_SIMULATED`), and flip the test to expect the refusal. If the Architect wants authored
  content over a `LIVE` gateway, that needs an explicit ruling first. P01/P02 and the test kit use the
  imported Site's `SIMULATED` gateway, so nothing legitimate should break.

### L1 (Low, guard teeth) - rule 8 misses a two-line UPDATE on provenance

- Mutation: adding `c.execute(text("UPDATE evidence_publication "` / `"SET fixture_version = '2' ..."))` to
  `register_publication` passes `tools/check-architecture.ps1`. The generic `$sqlWrite` needs
  `UPDATE <t> SET` on one line, and the new ledger-wide and other-writer provenance checks key off it
  (`tools/checks/configuration-persistence.ps1` added block near 718 and 812). The same split form in
  another module is also missed. `DELETE FROM` split across lines is caught (null target).
- The 0014 trigger still refuses it at run time, so this is not silent corruption, but the Architect asked
  rule 8 itself to reject UPDATE on these tables.
- Fix: on every line of every module, refuse
  `(?i)\b(?:UPDATE(?:\s+ONLY)?|DELETE\s+FROM|TRUNCATE(?:\s+TABLE)?)\s+(?:evidence_publication|batch_publication_link)\b`
  regardless of `SET`, and add this mutation to the proof set.

### L2 (Low, carry inconsistency) - rule 8 forbids the N-L1 anchor the handoff names

- The handoff's N-L1 carry says S4-05b should call `run_attestation(...)` + `register_run` in
  `simulator_lab_api.py` ~3270. Rule 8's route-module ban (`*_api.py`) refuses exactly that; verified by
  mutation (`A client route reaches source designation in .../simulator_lab_api.py:3276`).
- The guard is arguably right, since that commit endpoint is a client-triggered route. But the carry
  as written will fail the guard, and the Architect has not said whether a Lab commit route that triggers
  a server-side designation counts as a "public designation route".
- Fix: amend the carry to place the call in a non-route module that the commit route reaches through the
  port/service (e.g. beside `release_registered`). Or batch the question to the Architect before S4-05b
  starts and record any exception in rule 8 by name.

### L3 (Low, missing test) - downgrade refusal untested

- `0014` `downgrade()` refuses while publications exist, but no committed test exercises it. The existing
  downgrade tests only pass through the empty case. I verified it with a throwaway probe (not committed):
  after one publication, `command.downgrade(config, "0013_schedule_state")` raised
  `Downgrade of 0014_evidence_publication refused: source publications exist...`. Head stayed `0014`
  and the publication count stayed 1.
- Fix: add that test (0012 precedent).

### L4 (Low, disclosure precision) - the lock-cost baseline already pays the new index

- The "pre-S4-05a statement alone" baseline runs on the post-0014 schema, so the new 7-column
  `ingestion_batch_commitment_unique` index maintenance is inside the baseline, not the reported delta. The
  delta is the lock, the read and the link only. The cost is small, but the handoff should say so.

## Focus items judged

- **No retroactive authorship:** registration refuses any existing `ingestion_batch` row for the slot,
  including `IN_PROGRESS` (`postgres_evidence_ledger.py:306-315`). The test covers a partial (202) and a
  full admission. Link insert happens only when `open_batch` itself inserted the batch. A direct-SQL
  retroactive link is refused by the commitment FK and the `publication_id` unique constraint (tested).
- **Shared lock:** `open_batch` and `register_publication` both call `_lock_slot` with
  `admission_lock_key(tenant, Site, external batch ID)` as the first statement of their transactions. Tests
  include the held-key test and a 6-iteration race asserting `pubs == links == registered`.
- **Slot-key choice:** accepted. The key is coarser than the packet's (it omits gateway/source), but
  `ingestion_batch_external_unique` and `evidence_publication_slot_unique` are both Site + batch ID. Every
  contender for one admission slot must serialize, and gateway/source/digest are compared under the lock.
  Being stricter is safe. Distinct slots do not contend (measured).
- **Exact-commitment FKs / mismatch 409:** both composite FKs cover (tenant, Site, gateway, source, batch ID,
  digest, id). `PublicationMismatch` becomes a recorded 409 `PUBLICATION_MISMATCH`, with
  `ingestion_batch` and `accepted_evidence` both 0 (tested, including the other-source case).
- **Insert-only + triggers:** UPDATE/DELETE row triggers on both tables, and direct-SQL probes are refused
  (tested). **TRUNCATE:** acceptable as is. No append-only table since 0001 carries a TRUNCATE trigger, and
  the harness's TRUNCATE fallback relies on that. A plain TRUNCATE of `evidence_publication` is also blocked
  by the link FK. Residual: a privileged `TRUNCATE ... CASCADE` erases provenance. It is the same exposure
  as every other ledger table, and rule 8 covers it at the code level.
- **Downgrade refusal:** works (L3).
- **SYSTEM-only, no route:** `_authority` and DB CHECKs (`actor_kind='SYSTEM'`, channel set) both enforce it.
  A non-SYSTEM authority on a direct ledger call gets an IntegrityError (tested). The CLI takes no
  actor/basis/channel flags. No HTTP module references designation (rule 8, and verified by mutation).
- **Authored checks:** fixture must be the server spec's declared ID+version (`FIXTURE_UNKNOWN`,
  `FIXTURE_VERSION_MISMATCH`, `FIXTURE_UNREADABLE` tested). Digest is recomputed by the canonical parser
  (tampered digest -> `BATCH_UNREADABLE`). The bytes are not tied to fixture content (disclosed; S4-05b
  producer). See M1.
- **Registered-simulation attestation:** the digest covers run_id, created_at, the full
  deterministic_identity and registered_basis from `render_run_document`, as domain-tagged canonical JSON.
  It is deterministic, and private scenario fields are hashed, not stored (tested). Stage run/status, digest
  re-parse, Site, snapshot and message membership are checked, with refusals tested. `SIMULATED` gateway is
  required under the lock (`GATEWAY_NOT_SIMULATED` tested). Residual (disclosed): the run store is
  file-backed, so nothing re-verifies the digest later, and the real `registered_stage` port is untested
  until S4-05b.
- **Rule 8:** the ledger may only single-line INSERT provenance with VALUES and no ON CONFLICT. Ledger-wide
  `DO UPDATE` is refused, and ON CONFLICT is allowlisted to exactly the three arbiters already on main
  (`batch_refusal_identity`, `ingestion_batch_external_unique`, `accepted_evidence_message_unique`; I
  compared against `fd7afd2c`). The check also refuses ledger DDL/TRUNCATE and other-writer writes, has a
  non-vacuity check per table, and bans route modules. Existing writer lists are unchanged. Gap: L1.
- **Lock cost:** plausible. My rerun (n=60, same laptop, other pytest processes running elsewhere):
  baseline 12.59 / 18.08 ms (median / p95), unbound 17.03 / 21.50, bound 19.67 / 28.66, two threads on
  distinct slots (n=20) 20.61 / 27.73. These match the handoff's 12.10 / 16.61 / 19.15 medians.
- **Migration re-chain:** stated in the handoff (collides with LR-01 0014/0015 and S6-01a 0014; the later
  merge renumbers and updates the four head assertions).

## Checks run (this worktree, `assetops_backend.__file__` confirmed in `AssetOpsV1-review4`)

- `pytest test_s405_publication_postgres.py test_s2_evidence_ledger_postgres.py test_s1_bindings_postgres.py
  test_s4_evidence_consequence_work_postgres.py test_s2_gateway_access_postgres.py` on private base
  `assetops_s405arev_test`: JUnit tests=102, failures=0, errors=0, skipped=0, 120.6 s. (The first attempt
  errored only because the base DB did not exist yet. I created it and reran.)
- Lock-cost test alone at `ASSETOPS_S405_LOCK_SAMPLES=60`: passed (figures above).
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Mutations (applied, checked, restored by `git checkout`, tree clean afterwards): two-line ledger UPDATE on
  `evidence_publication` was **not caught** by the guard (L1); `register_run`/`run_attestation` in
  `simulator_lab_api.py` was caught (L2).
- Throwaway downgrade probe (created, run, deleted): refusal confirmed (L3).
- Not run: the full backend suite (out of scope for phase 1; owned by S4-05b) and frontend checks (no
  frontend change).
