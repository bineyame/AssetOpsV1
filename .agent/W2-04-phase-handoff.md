# W2-04 phase handoff - run 4 (spec commits 1-2 COMPLETE, rulings applied; commit 3 NOT STARTED)

Branch `task/W2-04-cold-site-evidence-money`. Nothing is merged. Private DB `assetops_w204_test`; environment in
the scratchpad file `w204env.sh` (PYTHONPATH, `ASSETOPS_TEST_DATABASE_URL`, `ASSETOPS_GUARD_PYTHON`, `PY`, cd
`backend`).

- Spec commit 1: `11abf439` (0023 schema), `07e51a0d` (Q1-Q10 alignment), `527d5342` (rule-8 policy and probes).
- Spec commit 2: `bf3dd9aa` (derivation, store, worker, Q10 guard, tests), `cc6f83bf` (Q10 inserts-unseen probes).

## Run 4 (this run): rulings applied, commit 3 surveyed but not built (stopped at context budget)

- `git merge main` brought in the Architect's amended spec. Q4 is corrected, and a new section, "Commit-2 Architect
  rulings: stored codes and screen copy", is in `.agent/W2-04-build-spec.md`.
- `4f859372` applies both rulings:
  - **Q4.** `ColdBasis.episode_open` is true when the store finds `lower_end IS NULL AND upper_end IS NULL`. An open
    episode keeps its proved low. The high is set to null even when W2-03's observed high is finite, and the row
    carries `OPEN_EPISODE_UPPER_UNKNOWN`.
  - **Fixed code set.** Only `CLAIM_LEVEL_POSSIBLE|CLAIM_LEVEL_UNKNOWN` and `SOURCE_CLASS_MIXED|SOURCE_CLASS_UNKNOWN`
    are emitted. They are module constants.
  - **Screen wording.** `cold_consequence.SCREEN_WORDING` (the spec's exact sentences for all 14 codes) and
    `screen_sentences(limitation)` translate the "; "-joined stored string. Use them in commit 3 (`/financials`,
    `overview.consequence_summary`) and in commit 4. Never show a raw code.
- Tests: the replay test now asserts that the episode has both end bounds null and a finite W2-03 high, and that
  the consequence row has the low, a null high and the limit. Pure tests were added for the Q4 open case, the two
  fixed claim-level codes, and wording coverage of all codes.
- Evidence: `test_w204_cold_consequence.py` 35 passed (4m40s) on `4f859372`.
- Not re-run after the change: the worker test, rule-8 probes and the architecture check. No guard file changed.
  Re-run them in commit 3.
- Implementer readings 1 and 2 below are now ruled; they are superseded by the spec section above.

### Commit 3 survey (anchors checked; build from these)

- **W2-03 read service.** `analytics/adapters/postgres_assessment_store.py:ColdReadService` (line ~1147).
  - `_connect` returns a REPEATABLE READ connection. `_read` maps `OperationalError/DBAPIError` to
    `ColdReadUnavailable`.
  - The caller-connection internals already exist:
    - `_snapshot(c,t,s,code,lo,hi,known_at)` returns a dict with keys `selected` ({analytic: `ColdSelected`}),
      `watermark`, `known`, `lo`, `hi`, `state`, `pending_since`, `latest_probe`, `evidence`, `limitations`.
    - `_envelope(snap, analytics)` builds the exact common envelope.
    - `_temperature(c,...)`, `_backup(c,...)`, `_finding_ids`, `_revisions` and `_item` complete it.
  - Plan:
    - Add public `snapshot()` (a context manager yielding one REPEATABLE READ connection, with errors mapped to
      `ColdReadUnavailable`).
    - Add thin public wrappers that take `c`: `temperature_on`, `backup_on`, `findings_on` (all current Findings of
      the window, unpaged), `selection_on` (returns snap plus envelope over both analytics) and `accepted_on`.
  - `accepted_on` needs a new query on `accepted_evidence` for Analysis rows: `id, record_kind, source_time,
    received_at, published_at (=sent_at), quality, role, source_id, envelope_sha256, normalized_value_text,
    normalized_unit, outcome`, scoped by tenant/Site and `id = ANY`, ordered `(source_time,id)`. The page goes after
    the cursor tuple.
  - The excursion `ColdSelected.result["links"]` gives `evidence_id/use/reason`; this is the source of `exclusion`.
- **Cursor and refusals.** `analytics/cold_reads.py` has `encode_cursor/decode_cursor` (the spec's
  `{basis,id,t}` grammar, with 422/409) and `currentness_state`. Reuse them with `(source_time, evidence_id)` and
  the selection basis.
  - `cold_assessment_api.py:build_cold_assessment_router.opened` is the exact refusal and parse seam to mirror:
    401, 403, unknown keys, window rules, 404, 503, then disclosure 403.
  - Spec additions not in W2-03 `_instant`:
    - Reject precision beyond microseconds (Q3).
    - Reject `known_at` > the captured watermark as 422 `COLD_TIME_INVALID`. This needs the watermark, so check it
      inside the snapshot.
- **Consequence store.** `financials/adapters/postgres_consequence_store.py`. Add read-only methods that take the
  caller's `c`:
  - `cold_heads_on(c,t,s,lo,hi,known)`: the highest `revision_no` per (finding_revision → finding_id, kind) whose
    `created_at <= known` and whose window overlaps, plus evidence links.
  - `cold_pending_on(c,t,s,lo,hi,room?)`: work with no SUCCEEDED attempt overlapping the half-open window.
  - Overlap-group grouping is in the pure service: one counted exposure per group.
- **Source gate.** Call `evidence/composition.py:build_link_rows_reader()`, which returns
  `postgres_evidence_ledger.link_rows_on(c,t,s,ids)` (caller connection), then
  `source_provenance.classify(ids,{r.requested_id: link_of(r)})`.
- **Source contact.** The `gateway_diagnostic` table (0006) has jsonb `last_device_contact_by_source`
  ({source_id: contact_at|null}).
  - Read the latest row per gateway with `received_at <= known` in the assessment adapter.
  - A listed source with a contact time gives `RECENT|STALE` via `evidence/gateway_access.py:freshness(contact_at,
    binding_roles.COLD_PERIODIC_CADENCE_SECONDS, to)`, mapping CURRENT to RECENT.
  - A listed source with null gives `NEVER`. A source that is not listed, or has no diagnostic, gives `UNKNOWN`
    with a limitation.
  - The RECENT/STALE threshold and the NEVER mapping are an implementer reading; confirm them with the Architect if
    the reviewer objects.
  - `fact_age` is `to` minus the latest accepted `source_time` in `[from,to)` at the cutoff.
- **Roles.** Use the constants in `analytics/cold.py`: `PROBE_ROLE`, `START_ROLE`, `GRID_EVENT_ROLE`,
  `GENERATOR_STATE_ROLE`, `TRANSFER_ROLE`, `BUS_ROLE`, `COMPRESSOR_ROLE`, `DOOR_ROLE`, `STEPS`, `COVERAGE_NEEDED`
  and `MAX_BRIDGE`. `sites/binding_roles.py:COLD_ROLES_1` gives the required roles per capability.
- **Mount.** In `main.py:create_app`, near lines 384-388, reuse `cold_reads`. Build the consequence store with
  `financials/composition.py:build_cold_consequence_store(database_url())` and dispose it on shutdown.
- **Test harness.** Copy `tests/test_w203_cold_reads_postgres.py:client/get/error`, which uses a SimpleNamespace
  registry and `opened(case, chain)` + `run(built)` from `test_w203_cold_replay_postgres`. Copy `drain(built)` from
  `test_w204_cold_consequence.py`. A cold replay costs about 40 s, so keep the replay count small: excursion,
  late-reading (pending, then historical), missing-probe, plus one valid empty window and the pure refusal and
  cursor cases.

## Landed in spec commit 2

- `backend/assetops_backend/financials/cold_consequence.py` (pure; no SQL): `derive`, `basis_sha256`,
  `basis_document`, `check_basis` (raises `ColdBasisMismatch`, code `COLD_BASIS_MISMATCH`), `warranted`,
  `merged_evidence`, `source_gate` (S4-05 `classify`/`link_of` over the cited IDs; gate digest is SHA-256 of the
  canonical classify result), `overlap_group`, `selected_instant` (Q3; `test_w204_cold_migration._z` now reuses it),
  `decimal_text`.
- `financials/adapters/postgres_consequence_store.py`: `__init__(..., link_rows=)`; `cold_unit` (REPEATABLE READ,
  first statement `pg_advisory_xact_lock(hashtextextended('cold_consequence:' || work_id, 0))`) yielding `ColdUnit`
  with `work`, `targets`, `basis`, `append`, `succeed`; `cold_record_failure` (fresh transaction; records nothing if
  the work already succeeded); `cold_pending_work`; `cold_claim_site`; `cold_rows`. Server times are column
  defaults (Q6). `append` takes an extra Finding/kind advisory lock and checks the predecessor's Finding and kind (Q5).
  Mini-grid methods unchanged.
- `financials/cold_recompute.py`: `ColdConsequenceWorker.process_one/run/run_pending` on store protocols;
  `retry_due_at` schedule; empty-ID success when no Finding warrants an exposure.
- `financials/composition.py`: `build_cold_consequence_store`, `build_cold_consequence_worker`.
- Rule 8: `$coldConsequenceInsertsSeen[...] -lt 1` fails with "...insert-only check is vacuous" (after the provenance
  loop). Probes `cold <table> owner insert unseen` (x3) prove it.

## Evidence (final revision `cc6f83bf`)

- Cold probe set with `--seam` on a clean tree: 29/29 CAUGHT (incl. the 3 new unseen probes), 4/4 controls ALLOWED,
  "tree restored", exit 0. `tools/check-architecture.ps1`: passed.
- `test_w204_cold_consequence.py`: 29 passed (6 replays + late-reading history + 22 pure). `test_w204_cold_worker.py`:
  4 passed (trigger work/drain/idempotence, race, failed attempt/rollback/retry/no starvation, unpaired basis and
  foreign scope). Adjacent run on `cc6f83bf` (w204 migration/consequence/worker, s4 consequence store/recompute/dispatch/history postgres, w203 cold migration): 84 passed, 0 failed, 0 skipped, 6m38s.
- Replay results: normal and missing-probe have no exposure row. Excursion, backup-failed, late-reading (20:05) and
  contradictory each have one `UNPRICED` `PRODUCT_EXPOSURE`, REGISTERED_SIMULATION, chamber room, amounts null.
  Bounds copied from the episode: excursion 19/23, backup-failed 19.5/24, late-reading 18.5/23 degC_min. Late reading
  at 20:10 appends revision 2 with `prior_revision_id` = revision 1 and a new basis; revision 1 is unchanged.

## Implementer readings to confirm (spec does not name these values; no design was intended)

1. **Q4 vs. data.** W2-03 stores both `degree_minutes_low` and `degree_minutes_high` for the open excursion
   (`claim.open = true`; duration upper is null). As the dry-read says to copy the bounds, the row has both, and
   `OPEN_EPISODE_UPPER_UNKNOWN` is set only when the upper bound is null. So none of the six replays carries that
   limit; it is covered by a pure test. Architect question: should an open episode carry
   `OPEN_EPISODE_UPPER_UNKNOWN` (or a null upper bound) even when W2-03 gives a degree-minute upper bound?
2. **Stored codes.** Reasons are `COLD_VALUATION_NOT_APPROVED` (UNPRICED), `SOURCE_GATE_WITHHELD` and
   `TECHNICAL_CLAIM_LIMITED`. Limitation codes are `OPEN_EPISODE_UPPER_UNKNOWN`, `CONTRADICTORY_EVIDENCE`,
   `CLAIM_LEVEL_<level>`, `COVERAGE_INCOMPLETE` (below 0.8, the floor in the spec's EXCURSION_BOUNDS rule),
   `EXPOSURE_LOWER_BOUND_UNKNOWN` and `SOURCE_CLASS_<class>`; several are joined with "; ".
3. **Withholding.**
   - A technical limit nulls the quantity.
   - Withholding for the source alone keeps the proved bounds.
   - Currentness (pending or historical) is applied at read time in commit 3, not stored.
4. **Worker error codes.** `COLD_BASIS_MISMATCH` (from the spec). The others are this run's choice:
   - `COLD_RECOMPUTE_FAILED` for any other fault;
   - `STORE_UNAVAILABLE`;
   - `WORK_SCOPE_MISMATCH` for foreign work, which records no attempt.
5. **Race.** The RR snapshot starts at the lock statement, so a racing loser hits a unique constraint. It then
   records nothing, because `cold_record_failure` sees the success, and reports `already_succeeded`. The test proves
   one attempt and one revision.

## Residual

- The `SOURCE_GATE_CHANGED` worker path (`ColdUnit.targets` SOURCE_GATE SQL) has no positive test. In the chain,
  every batch is linked before acceptance, so no source-gate work arises. The 0023 trigger itself is tested in
  commit 1.

## Next run: spec commit 3 (five selected API reads)

Read the spec sections "Five API reads", "Selection, projection and capability", the dry-read rows "How does the API
keep one snapshot?", "What is a valid explicit selection/cursor?" and "What do `as_of` and contact mean?", and the
W2-03 `cold_reads.py`/`cold_assessment_api.py` anchors.

- Add `analytics/cold_site_reads.py:ColdSiteReadService` (pure; no SQLAlchemy) and `cold_site_api.py:build_cold_site_router`.
- Add read-only caller-connection methods on `PostgresAssessmentStore` and `PostgresConsequenceStore`.
- Mount the router in `main.py:create_app` beside the W2-03 and cold-foundation routers.
- Write `test_w204_cold_reads.py`.
- Consequence reads take the head per Finding/kind (highest `revision_no`), grouped by `overlap_group`. A relevant
  cold work item with no SUCCEEDED attempt means `PENDING_RECOMPUTE`.

Then commit 4 (frontend plus the retro corrections below), then commit 5 (final guards, one full backend suite and
the review packet).

## Retro-ruling corrections (carried forward, unchanged)

The exact text is in `.agent/W2-retro-rulings.md`, rows "Deviation 14" and "Deviation 17". List both in the review
packet.

- **Dev 14.** A cold Analysis link may render only after an integration test proves that the exact
  `record`/`assessment` target shows the selected cold ID in the existing Evidence Analysis route. The proof must
  show that Site, window and cutoff are preserved.
  - Until that proof exists, show the reference as labelled text with "Analysis view not available for this cold
    record".
  - Never render a dead link.
- **Dev 17.** Restore the mock's exact "Loading / batch" row label, and keep "Not established" when there is no
  loading record.
  - Make the capture/settling detector match the real loading-state element, or the exact loading sentences, rather
    than any text containing "Loading".
  - Recapture the affected cold screens.

## Open risks

- `cold_consequence_room` relies on W2-03 `record_cold_assessment` writing the Foundation ID into
  `analytic_run.foundation_revision_ids`. If W2-03 stops doing that, every cold append is refused (fail closed).
- W2-05a is building in parallel, and this run edited the shared files `configuration-persistence.ps1` and
  `writer_guard_probes.py`. Merge carefully. Before any full backend suite, confirm no other pytest is running.
