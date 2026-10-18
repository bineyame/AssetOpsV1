# W2-04 phase handoff - run 6 (spec commits 1-3 COMPLETE incl. Run-5 fixup; commit 4 NOT STARTED)

## Run 6 (this run): commit 3 fixup `f7421764`; commit 4 next (did not fit this run's context budget)

- Fixup applies spec "Final Run-5 Architect rulings" Q-R1..Q-R8 and verdicts 1/5 (code: `analytics/cold_site_reads.py`
  constants `ATTENTION`, `COOLING_TEXT`, `MAINTENANCE_*`, `OBJECTIVE_*`, `NOT_INCLUDED_TEXT`, `REQUIREMENTS`, `CONTACT_*`;
  `_needs_attention`, `_cooling`, `_exact_basis`; `source_contact` now returns `(contact, contact_at, limitation)`).
  Adapters: `source_facts_on` adds the GOOD count (`quality:{good_count,other_count}`); `cold_heads_on` adds
  `source_gate_sha256`, `assumption_revision_ids` and sorted distinct `evidence_ids` (SELECT only).
  `/evidence.links.foundation` = `/api/sites/{code}/cold/foundation?at={to}`. Q-R9: rows stay UNAVAILABLE (no proof built).
- Verdict 1: W2-03 `known_points` already counts only qualifying (bound, GOOD, clock-attested) points and a missing
  calibration refuses the run, so capability predicates were already on qualifying points; pure test
  `test_capability_needs_qualifying_points` pins it. Verdicts 2/3/4/6/7/8 matched the built code (no change).
- Evidence on `f7421764`: `test_w204_cold_reads.py` + `test_w204_cold_worker.py` 22 passed, 0 failed, 0 skipped,
  2m29s; `tools/check-architecture.ps1` passed. Rule-8 probes not re-run (no DML changed; run at commit 5).
- Applied without an explicit per-code ruling (confirm with Architect; one line each):
  - Q-R1 `link`: Finding URL for the item's analytic if a selected Finding exists, else `backup-chain` read
    (start failure, transfer unknown) or `evidence` read (pending, probe gap, policy missing).
  - Q-R1 `COLD_POLICY_MISSING.limitation`: `POLICY_REVISION_UNRESOLVED` when unresolved, else the EXC limitation.
  - Excursion replay yields `needs_attention` codes `COLD_START_FAILURE, COLD_TRANSFER_UNKNOWN` (pinned in test).

### Commit 4 anchors (Explore survey on this revision; build from these)

- Test helpers: `frontend/src/test/panelStructure.ts:187 expectV69Panels(screenId, values?, scope?)`,
  `:215 expectPlantedPanelRejected(screenId)`; pattern `sites/__tests__/coldFoundation.test.tsx:198-215` (stub client
  via `vi.fn`, `<MemoryRouter><App ... coldFoundation={...}/>`), `settledScreen` from `test/settled`.
- Panel titles: `frontend/docs/architecture/v69-rendered-panels.json` `cold` :268, `cold-evidence` :582,
  `cold-evidence-analysis` :596, `cold-financials` :606, `cold-assumptions` :620.
- Window params: `sites/coldAssessmentClient.ts:190 NO_WINDOW`, `:193-197 coldWindowSearch`, `:202 coldWindowFromParams`.
- Plug points (none has a cold branch yet): `shell/SiteDetailFrame.tsx:95-160` (overview render prop ~:113 receives
  only the ID); `shell/SiteEvidenceFrame.tsx:95` site resolved, `localView` `?view=analysis` :112, render :116-126;
  `shell/SiteAnalyticsFrames.tsx:621 SiteFinancialsFrame`, overview/assumptions switch ~:688-691. Existing cold
  branch pattern `SiteAnalyticsFrames.tsx:165` and `:471` (`site.site_type === "COLDCHAIN" && client !== undefined`),
  `coldLinks()` :126-135.
- Dev 14: `coldLinks().analysis` (`SiteAnalyticsFrames.tsx:133`, `siteEvidenceAssessmentHref`) is rendered as a Link
  at `sites/ColdAssessmentViews.tsx:178`; replace with labelled text + `Analysis view not available for this cold record`
  until the Q-R9 integration proof exists.
- Dev 17: `sites/ColdAssessmentViews.tsx:382-383` label is `Stock loading / batch` -> restore `Loading / batch`
  (`Not established` when none); fix detector `tools/w1-fidelity-evidence.mjs:170`
  (`!document.body.textContent.includes("Loading")`) to match the real loading element or exact sentences
  `COLD_ASSESSMENT_LOADING`/`COLD_FINDING_LOADING` (`ColdAssessmentViews.tsx:71-72`). Similar detectors:
  `tools/layout-evidence.mjs:5442`, `tools/s302-claim-limit-evidence.mjs:65`.
- Capture tool: `node tools/w1-fidelity-evidence.mjs <out-dir> <mock-id>[:<case>]=<app-url> ...`; mock URL derived
  from the app origin (`/mockups/v69/index.html#/<id>`); CDP port env `ASSETOPS_CDP_PORT`; `W1_REVISION` env.
- Next exact steps: (1) `sites/coldSiteClient.ts` typed client for the five reads (shapes in spec "Five API reads" +
  Run-5 additions); (2) `sites/coldSiteViews.tsx` five views with the spec "Commit-4 copy ledger" copy only, plus
  `w2-cold-site.css`; (3) COLDCHAIN branches at the plug points; (4) Dev 14 + Dev 17; (5)
  `sites/__tests__/coldSiteViews.test.tsx` stocked/empty/refused(403)/503/pending per route + planted panel;
  (6) self-check + height table; (7) 1440/390 captures on ports 9700-9750/6100-6150, then drop fixtures, stop servers.


Branch `task/W2-04-cold-site-evidence-money`. Nothing is merged. Private DB `assetops_w204_test`; environment in
the scratchpad file `w204env.sh` (PYTHONPATH, `ASSETOPS_TEST_DATABASE_URL`, `ASSETOPS_GUARD_PYTHON`, `PY`, cd
`backend`).

- Spec commit 1: `11abf439` (0023 schema), `07e51a0d` (Q1-Q10 alignment), `527d5342` (rule-8 policy and probes).
- Spec commit 2: `bf3dd9aa` (derivation, store, worker, Q10 guard, tests), `cc6f83bf` (Q10 inserts-unseen probes).

## Run 5 (this run): spec commit 3 built (five cold Site reads); commit 4 next

- `c3178afd` (one spec commit):
  - `analytics/cold_site_reads.py:ColdSiteReadService` (pure; no SQLAlchemy) and `cold_site_api.py:build_cold_site_router`
    (`/overview`, `/evidence`, `/evidence/analysis`, `/financials`, `/financial-assumptions`), mounted in
    `main.py:create_app` after the W2-03 router; the consequence store from `build_cold_consequence_store`, disposed at shutdown.
  - `ColdReadService` (assessment adapter) gains caller-connection reads: `within`, `selection_on`, `envelope_on`,
    `temperature_on`, `backup_on`, `current_findings_on`, `basis_revisions_on` (a cold run stores its exact
    `signal_binding_revision` IDs in `analytic_run.binding_set_revision_ids`), `accepted_on`, `source_facts_on` and
    `source_contacts_on` (the latest diagnostic per gateway received at or before `min(known_at, to)`).
  - The consequence store gains `cold_heads_on` (the highest revision per exact selected FindingRevision and kind) and
    `cold_pending_on` (overlapping work with no SUCCEEDED attempt).
  - Source contact follows ruling line 41 (`source_contact`). Money reason and limits use `SCREEN_WORDING`/`screen_sentences`.
    A `known_at` later than the watermark, or a time finer than microseconds, is 422 `COLD_TIME_INVALID`.
- Evidence on `c3178afd`:
  - `test_w204_cold_reads.py` 16 passed (12 pure contact cases, 1 pure refusal test, excursion, late-reading pending then
    historical, missing-probe plus an empty window).
  - Adjacent run (new file + `test_w204_cold_worker.py` + `test_w203_cold_reads_postgres.py`): 25 passed, 0 failed,
    0 skipped, 6m41s (before an `_open` -> `_selected` rename the architecture check required); after the rename the new file alone: 16 passed, 48 s.
  - Rule-8 cold probe set with `--seam`: all 55 cold probes and controls (W2-03 and W2-04) were run: 46/46 CAUGHT, 9/9 controls ALLOWED, "tree restored", exit 0, 762 s. `tools/check-architecture.ps1`: passed (70 s, with `ASSETOPS_GUARD_PYTHON` set).
- Built but needing a ruling (the spec does not give these, so each is a reading, not a decision):
  1. Capability predicates. `TEMPERATURE_POINT` needs >=1 known point. `EXCURSION_BOUNDS` needs the policy, >=2 points,
     coverage >=0.8 and no gap >10 min. `BACKUP_START_RESULT` needs an observed success or failure chain.
     `TRANSFER_POSITION` needs an observed TRANSFER step. `COOLING_RESPONSE` needs an accepted `compressor_state` and
     >=2 points. `PRODUCT_EXPOSURE` needs an eligible excursion (OBSERVED/BOUNDED, exposure Finding) plus bounds.
     LIMITED means partial; CONTRADICTORY comes from a contradictory W2-03 state or step. `required_roles` are in
     `REQUIRED_ROLES`. The coverage of the event claims (backup/transfer) is null-valued.
  2. `latest_chain_id` is the `correlation_id` of the chain with the latest anchor. `causal_strip` shows that chain's steps.
  3. `last_accepted_at` is the latest accepted `source_time` (the same fact `fact_age` uses), not `decided_at`.
  4. Source rows are the selected runs' bound `(source_id, role)` channels, in `cold-roles-1` order.
  5. Contact-limitation sentences for the five UNKNOWN causes (`CONTACT_*` constants) are implementer wording.
  6. Money is WITHHELD while the read is `PENDING_RECOMPUTE` or overlapping cold work has no success. The reason is
     `New evidence is waiting to be assessed` (or the `COLD_RECOMPUTE_FAILED` sentence when the last attempt failed).
     If a group has more than one head, the latest created is used. Heads are selected by the exact FindingRevision
     selected at the cutoff, without `created_at <= known_at`, because money is derived after its Finding.
  7. `known_at` is compared only when a watermark exists. Analysis rows all have `record_target_state:'UNAVAILABLE'`,
     `link:null` and `Analysis view not available for this cold record`: this commit has no route proof for the Site
     Evidence exact record.
- Exact questions (these pieces are left out or null; everything else is built):
  - Q-R1 `/overview.needs_attention`: what are the five `code` values (pending recompute, probe gap, observed start
    failure, unknown transfer, missing policy) and their `text` wording? The key is omitted.
  - Q-R2 `/overview` `cooling` and `maintenance`: what is the field shape of each card-specific capability gap? Omitted.
  - Q-R3 `/overview.objective.text`: what is the wording? Omitted; policy, room, `as_of` and `limitation` are present.
  - Q-R4 `/financials.not_included[].text` for `STOCK_VALUE_UNDECLARED`, `EXPOSURE_RULE_UNAPPROVED`,
    `SPOILAGE_UNPROVED` and `REPAIR_COST_ABSENT`: what is the wording? Null for now (`SOURCE_GATE_WITHHELD` uses its ruled sentence).
  - Q-R5 `/financials.consequences[].exact_basis`: is it a string or an object, and with which fields? Omitted.
  - Q-R6 `/evidence.links.foundation`: the cold Foundation route accepts only `at`, so it cannot carry
    `from,to,known_at`. Should it be `?at={to}`, or omitted? Omitted.
  - Q-R7 `/evidence/analysis.claim_rules[].requirement`: what is the wording? Omitted.
  - Q-R8 Should a source row carry `contact_at` (the ruling's "null contact time")? It is not in the spec shape. Not added.
  - Q-R9 May analysis rows become `PROVED` with a Site Evidence record link? That needs an integration test mounting
    `evidence_api` against the cold replay.
- Next: commit 4 (frontend five routes plus the retro corrections), after the Q-R answers; then commit 5.

## Run 4: rulings applied, commit 3 surveyed but not built (stopped at context budget)

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

## (Superseded by Run 5) spec commit 3 plan

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
