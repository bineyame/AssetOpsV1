# W2-06 pending rulings — commit 2 (pure correlation) — 2026-10-19

Raised by the W2-06 implementer before starting spec commit 2. Commit 1 (0025 schema, domain checks, rule-8
probes) is built and committed on `task/W2-06-ev-assessment` (`cb470909`, `3af70964`, `fc231615`). Commit 2 is
**not started**: the points below are unruled or conflict with a binding source, so this run stops at the commit-1
boundary. All questions for commit 2 are batched here. Sources: `.agent/W2-06-build-spec.md` (incl. "Pre-build
closure"), `.agent/W2-technical-design-ev.md` §§1,3,4,8, `contract-fixtures/w2/ev/*.json` assertions.

## R1 — CONTRADICTORY: manifest vs. 0025 schema vs. spec (conflict)

The `contradictory.json` manifest asserts `end_at=null, supported_kwh=null, energy_complete=null,
unknown_meter_seconds=null`. The spec's 0025 DDL makes `unknown_meter_seconds` an integer `>=0` (built NOT NULL, as
the EV design lists it non-nullable while naming `supported_kwh` nullable), says "Store `supported_kwh` as the exact
sum of SUPPORT deltas", and lets CONTRADICTORY "retain an observed end only as context". The brief requires the
vectors to agree with the manifests. Please rule, for a CONTRADICTORY session revision:
- (a) `end_at`: NULL, or one of the two terminals (earliest? latest?) kept as context.
- (b) meter intervals: are they SUPPORT (clipped to which terminal — 08:30 or 08:31?) or all EXCLUDED, and with
  which reason code?
- (c) stored `supported_kwh`: NULL (manifest) or the SUPPORT sum (spec wording).
- (d) stored `unknown_meter_seconds`: which integer (0? the whole START→latest-terminal span?), or should 0025 make
  the column nullable so NULL matches the manifest? (0025 is committed NOT NULL; a change is a one-line amendment.)

## R2 — start/end bounds values

`ev_session_revision` has `start_earliest/start_latest/end_earliest/end_latest` and the response has
`start_bounds/end_bounds:{earliest,latest}`, but no rule says how they are computed. Options: (A) source time ±
declared `ev-clock-error-bound` (30 s); (B) both equal to the attested source time; (C) NULL unless an uncertainty is
proved. And for INCOMPLETE: is `end_bounds.earliest` the end of the observed active span (R3) with `latest` NULL?
For CONTRADICTORY: earliest/latest = the two distinct terminal times?

## R3 — "observed active span" for INCOMPLETE

"While terminal is missing, only the observed active span is bounded." Which accepted record ends that span: (A) the
end of the latest SUPPORT meter interval of the session; (B) the latest accepted connector state `CHARGING`
observation (+1 minute?); (C) the selected cutoff/window end clipped? This sets INCOMPLETE meter selection and
`unknown_meter_seconds` (late case at the first cutoff: (A) gives 30.000 kWh partial with 0 unknown seconds +
`MISSING_TERMINAL`).

## R4 — exclusion reason mapping

Exclusions must use "the existing enumerated reason", whose vocabulary is EV design §8 `reason_codes`
(`MISSING_START|MISSING_TERMINAL|CONFLICTING_TERMINAL|CONFLICTING_START|CONNECTOR_MISMATCH|METER_GAP|METER_OVERLAP|
METER_INVALID|CLOCK_UNATTESTED|SOURCE_UNVERIFIED|PENDING_RECOMPUTE`). Please pin the code for each case:
meter interval spanning the START/terminal boundary (unsplit); negative/nonfinite or over-power-bound delta; overlap;
SUSPECT quality (record or meter); wrong session ID on a meter; wrong connector/binding; source-gate failure;
clock-unattested; event before START beyond the clock bound. Also: is a SUSPECT *event* CONTEXT (cold precedent:
`analytics/cold.py:271-281` links SUSPECT as CONTEXT) or EXCLUDED, and with which code (no `SUSPECT` code exists)?

## R5 — overlapping meter reports

When two otherwise-valid deltas overlap, "never chosen by event ID": are **both** EXCLUDED with `METER_OVERLAP`
(their span then counts as unknown seconds)?

## R6 — meter `error_bound_kwh` stored per interval

Is it the Foundation `ev-meter-error-bound` (0.001 kWh, "per boundary" in EV design §3), or the per-interval
`2 × meter_error_bound` used in the plausibility test?

## R7 — which records a session revision links, and its basis rows

Which accepted records enter `ev_session_evidence` and the session basis: only the session's START/terminal(s)/
same-connector FAULT/CLEAR and its meter deltas, or also same-connector state/power/requested/allocated means and
Site import in `[START, end)` as CONTEXT? (This changes `basis_sha256` and stored rows.) For a session whose START
precedes the window ("context, never a new attempt"), is a revision produced at all in this window's run?

## R8 — basis literal values

The basis outer array is `[foundation_revision_id, binding_revision_id, mapping_profile_id, model_id,
rule_version, from, to, known_at, source_class]`. Please pin: `model_id` (`ev-session/1`?), `rule_version`
(cold uses `MODEL_VERSION="1"`), `mapping_profile_id` (`simulator-lab-gateway-ev/1`, from the effective source
mapping?), and the `source_class` string (S4-05 class, e.g. `REGISTERED_SIMULATION`). With more than one effective
Foundation or binding revision in the window, which ID goes in the single slot?

## R9 — session `reason_codes` content and order

Which codes each state carries (e.g. COMPLETED+gap → `METER_GAP`; INCOMPLETE → `MISSING_TERMINAL` (+`METER_GAP`?);
CONTRADICTORY → `CONFLICTING_TERMINAL`; any excluded record → its code too?), and the array order (lexical? first
occurrence?).

## R10 — ratify commit-1 readings (built; change is cheap if overruled)

- `reason` must be NULL for SUPPORT in both `ev_session_evidence` and `ev_meter_interval` ("required for EXCLUDED
  but permitted for CONTEXT" read as forbidden for SUPPORT).
- Column names not given by the spec: `start_earliest,start_latest,end_earliest,end_latest`, link column
  `revision_id`, meter columns `kwh,error_bound_kwh` (taken from the detail JSON field names).
- `unknown_meter_seconds` NOT NULL (see R1), `ev_session.external_session_id` "nonblank" = `btrim(...) <> ''`.
- Migration tests live in `backend/tests/test_w206_ev_migration_postgres.py` (predecessor naming), not in the three
  spec-named W2-06 files, which are for commits 2-4.

## R11 — canonical serializer and digest column (added after code survey)

- "Use the existing canonical JSON serializer (sorted keys, compact, UTF-8, UTC `Z` with fractional digits preserved,
  Decimal canonical)": no single existing function does all of this. Cold uses
  `assetops_contracts.source_envelope.canonical_json` (no datetime/Decimal handling) after `cold.plain()` and
  `assessment_inputs.iso` (always six fractional digits). `financials/cold_consequence.py:selected_instant` keeps
  fractions only when nonzero. Which instant formatter is binding for the EV basis: `iso` (always `.ffffffZ`) or
  `selected_instant` (fractions only if present)?
- The basis row's `content_sha256`: `accepted_evidence` has no such column; its digest is `envelope_sha256`
  (cold basis uses it). Confirm `content_sha256 := accepted_evidence.envelope_sha256`.

## R12 — where the six-case pure vectors come from

`tools/checks/dependency-direction.ps1` bans `assetops_simulator` imports anywhere under `backend/` (tests
included), so `test_w206_ev_session_rules.py` cannot run the producer. Confirm the W2-03 precedent: pinned vectors in
`backend/tests/fixtures/w2/ev-w206-vectors.json`, generated and kept in sync by a host test (like
`host/tests/test_w203_cold_vectors.py`) from `host/ev_publication.py:ev_reports`, and checked against the
`contract-fixtures/w2/ev/*.json` assertions.

---

# W2-06 pending rulings — run 2 (q2), 2026-10-19

Raised after applying q1. Built this run: `13c6ef33` (q1 R1: 0025 `unknown_meter_seconds` nullable with the exact
`ev_session_revision_unknown_seconds` / `ev_session_revision_quantity_state` text, plus migration tests; R10 ratified
as built, no change). **Stopped before the R12 vector file and spec commits 2–3**: the points below are not fixed by
the build spec or the q1 closure, checked against the code. All are batched here; nothing below was decided.

## Vectors (R12) — blocks commit 2

**Q1 — report → accepted evidence ID.** R12 asks the host test to build the vectors from `ev_reports` and the six
manifests and to "assert exact evidence IDs". The manifests pin `accepted_evidence_ids` and `envelope_sha256` per
disposition, in batch-external-ID order (`test_w205b_ev_replay_postgres.py:330 batches`, ordered by publication
`recorded_at`), but nothing pairs an ID with its report, and the gateway V4 envelope (provisioning site/gateway/
source IDs, case epoch, per-source sequence, published_at) is not in the manifest. Which mechanism?
(A) host test rebuilds each gateway V4 envelope (`gateway/assetops_gateway/service.py:139 _envelope_v4`, a private
function, plus the 05b provisioning/epoch/sequence values) and matches `envelope_sha256` to take each ID;
(B) the W2-05b Postgres chain test also writes the vector file (accepted envelope + ID + digest), i.e. a backend,
not host, source; (C) vectors use report-key-derived IDs and the exact manifest IDs are asserted only in commit 3's
replay store test.

**Q2 — vector content.** Which expected outputs each case pins beyond the manifest's ten assertion keys: per-record
use/reason, interval rows (`kwh`, `error_bound_kwh`), `reason_codes`, bounds, `fault_evidence_id`, Finding support
IDs, and whether `basis_sha256` is pinned (it depends on Foundation/binding IDs, mapping profile and source class).

## Commit 2 — pure correlation

**Q3 — use of an eligible linked record.** R4/R7 fix exclusion reasons and "Site import CONTEXT only", not
SUPPORT vs CONTEXT for eligible GOOD/in-force/attested records. Rule the use for: START (per state, incl.
CONTRADICTORY and INCOMPLETE); the sole END/ABORT; a same-session contemporaneous FAULT on OBSERVED_ABORT, and on
COMPLETED/INCOMPLETE; CLEAR; meter deltas; connector state, connector power, requested power, allocated limit.
Is a CONTEXT row's `reason` NULL when it is merely context (no exclusion)?

**Q4 — scope of the 30 s straddle rule.** R4: a record whose uncertainty straddles START is EXCLUDED
`CLOCK_UNATTESTED`. Every case has a GOOD connector `state` (STATE_AT_INSTANT) at exactly 08:01:00 = START, and
`INTERVAL_MEAN` power/request/limit reports starting at or near START. If the rule covers measurements, every session
gains `CLOCK_UNATTESTED` and COMPLETED-complete cannot be `[]` (R9). Does it apply to EVENT-family records only?
Does a symmetric rule apply near the terminal?

**Q5 — "source interval intersects the observed span".** For STATE_AT_INSTANT (point `source_time`): include iff
`START <= t < end`, or `<= end`? INTERVAL_MEAN `[a,b)` vs `[START,end)`: half-open overlap? Which span applies to
CONTRADICTORY (no `end_at`; meters EXCLUDED): `[START, end_bounds.latest)`, or none? INCOMPLETE with no meter
(zero-length span, R1): link no state/power context?

**Q6 — `supported_kwh` scale.** Reports carry `"4"`, `"5"`, `"1"`; the exact Decimal sum is `30`, the manifests
say `"30.000"` and R1 says `"0.000"` "with the fixture scale". Is the stored numeric and the vector value quantized
to the connector's Foundation `ev-meter-resolution` (0.001), or the exact sum stored and the scale applied only on
read? Same question for `ev_meter_interval.kwh`.

**Q7 — fractional uncovered time.** `unknown_meter_seconds` is an integer; with microsecond source times the
uncovered union can be fractional. Floor, ceil or half-even? (No fixture case hits it; commit 2 needs a rule.)

**Q8 — `mapping_profile_id` source.** No column stores an effective mapping profile; the only link is the code
table `V4_EV_MAPPING_PROFILE_ID/VERSION` for `ROLE_SET_EV_1` (`sites/binding_service.py:220`). Read it from that
table through the effective `ev-roles-1` binding set, from the run's registered publication profile, or elsewhere?
Exact string form `"{id}/{version}"`?

**Q9 — names (ratify).** Pure module `backend/assetops_backend/analytics/ev.py` beside `cold.py`; host test
`host/tests/test_w206_ev_vectors.py`, regenerate with `ASSETOPS_W206_WRITE_VECTORS=1` (W2-03 precedent).

## Commit 3 — writer, recompute, Finding

**Q10 — enqueue site vs "No accepted-evidence writer change".** Cold enqueues inside the S2 writer
(`evidence/adapters/postgres_evidence_ledger.py:501-507 _coalesce_job`). An `ev_charging` branch there conflicts
with the readiness gate's "No accepted-evidence writer change". Is that branch allowed (job IDs via
`gen_random_uuid()` like cold, so W2-05b's counter-pinned accepted IDs do not shift), or must the enqueue live
elsewhere (a 0025 trigger, or a worker-side scan of new accepted rows)?

**Q11 — EV work window.** Cold: five-minute-aligned bracket of accepted source times merged with selected windows
within a ten-minute bridge (`postgres_assessment_store.py:783 cold_windows`, ledger `_COLD_BRIDGE`). For EV rule the
alignment unit, coalescing width, merge with selected `ev-session/1` windows, and the late-terminal extension (how
the START is found — accepted START by tenant/site/connector/`session_id` inside the ledger transaction?). This
fixes the idempotency window and the read's "latest selected window" (manifests use 08:00–09:00).

**Q12 — config-change enqueue.** "Effective Foundation/binding/mapping/source-gate change" enqueues `ev_charging`,
but no existing hook enqueues cold on these. Which module (Foundation publish, binding publish, S4-05 link write)
and which windows (every selected EV window overlapping the new revision's validity)?

**Q13 — worker wiring.** Add `build_ev_assessment_worker` beside `analytics/composition.py:109`; is any runner
started in commit 3, or is it test-driven only as cold is?

**Q14 — EV `assessment_revision` / `analytic_run` values.** `assessment_key` literal; window `claim_level`; the
`result` JSON document shape; `evidence_ids` content (all run inputs or linked only); `configuration_sha256` input;
`role_coverage` and `watermarks` content; and the exact form of the run `input_sha256` ("all selected accepted
inputs and exact configuration": same row form as the session basis over all window rows?).

**Q15 — EV `finding` / `finding_revision` values.** Exact `title`; `claim_level` (OBSERVED?) for SUPPORTED and for
NO_LONGER_SUPPORTED; `matcher_version`; `claim` JSON (commit 4's detail `claim` keys?); exact `limitations`
sentence(s) ("component cause and unmet demand are unknown"); `finding_revision.basis_sha256` = session basis or run
input; `cited_evidence_sha256`; `finding.anchor_start` (START time?) and `anchor_assessment_revision_id`.

# W2-06 pending rulings — run 3 (q3), 2026-10-19

Run 3 landed `27ceef76` (commit 2b, pure `analytics/ev.py` + state-table tests) and `0eeb57ef` (commit 3a, enqueue
trigger + `ev_enqueue_configuration`). Stopped before the vector fixture (2a) and the writer/worker (3b). Unruled
points, all at once:

## Vectors / pure correlation (block 2a and the 3b replay tests)

- **P1 clock attestation source (blocking).** The W2-05b EV replay chain records no `source_clock_attestation`
  (only W2-03 cold's test records one via SYSTEM_ATTESTER `record_clock_attestation`). Honestly derived, every
  vector row is `clock_attested=false`, so under R4 every record is EXCLUDED `CLOCK_UNATTESTED`, contradicting the
  q2 table (SUPPORT/null, `[]`). Options: (A) producer records the SYSTEM simulated attestation per EV lab source as
  cold does (consumes held uuid4s: shifts pinned W2-05b IDs/manifests, or runs after the manifest comparison with a
  later `recorded_at`); (B) keep `false` and revise the expected table; (C) other. 3b's `ev_inputs` reads the same
  source, so this also fixes the writer's input.
- **P2 binding identity check.** Row `binding_revision_id` is a per-binding ID, not the binding-set revision (c1 rows
  in `complete` carry two IDs, neither the manifest set revision). `ev.py` compares to the set revision, so all rows
  would be `SOURCE_UNVERIFIED`. Options: input carries the set of effective binding IDs of the set revision; or
  compare set revision only.
- **P3 run-input use/reason for unlinked or doubly linked rows.** Q14 run SHA rows are `[id,envelope,use,reason]`
  for all window inputs incl. orphan/context, but no use/reason is ruled for a record linked to no session, or
  linked with different uses by two sessions. `ev.run_input_sha256` currently takes caller-supplied rows.
- **P4 `policy` key names** inside `configuration_sha256` (ratings, resolution/error, clock bound, cadences) are not
  fixed; caller-supplied today.
- **P5 ratify implementer readings in `ev.py`:** 30 s straddle applied only in `[START-30s,START)`; two FAULTs both
  within 30 s of ABORT -> neither supports, no Finding; non-GOOD START creates no session; second accepted START
  linked CONTEXT `CONFLICTING_START`; orphan = terminal with no START for that connector+session; negative/nonfinite
  delta gets no `ev_meter_interval` row (DDL forbids it) but still a session-evidence EXCLUDED `METER_INVALID` link.
- **P6 vector-file shape:** (a) `first_cutoff` written as the 13 expected keys plus `known_at` and
  `accepted_evidence_ids` (rows carry no `received_at`; without the ID list the 09:00 set cannot be rebuilt) — or
  13 keys only; (b) `finding_support_evidence_ids` table order START,FAULT,ABORT vs ID-sorted; (c) `source_id` =
  ledger source UUID vs envelope external source ID; (d) `unit` = `normalized_unit` vs `original_unit` (identical
  here); (e) no `expected` key exists for non-interval record uses (contradictory ENDs CONTEXT, fault-case c1
  FAULT/CLEAR context) — add a key or leave to rule tests; (f) write per case + per-case byte compare + whole-file
  check vs one whole-file write.

## Enqueue wiring (blocks the rest of 3a; 3b can proceed without it)

- **P7 publish-path wiring vs guards.** Q12 says call `ev_enqueue_configuration` on the publishing connection from
  `evidence_publication`/`batch_publication_link` append, `PostgresFoundationStore.publish_configuration` and
  `BindingService.publish`. But (i) the evidence ledger may not import analytics (`tools/checks/dependency-direction.ps1:365-372`)
  and those rows have no validity span — options: 0025 trigger on `batch_publication_link` like 0023's cold trigger,
  injected callable, or a span ruling; (ii) `sites/adapters` may not import `analytics.adapters` and the Foundation
  store does not know the Site type — options: pass via `FoundationService`'s existing `then` hook, constructor
  parameter on store/`FoundationService`/`BindingService` wired in `main.py`, or Site-type check in SQL in the store;
  (iii) `BindingService.publish` (`sites/binding_service.py:720`) has no transaction hook today.
- **P8 ratify 3a readings:** missing ACCEPTED disposition at deferred firing -> no enqueue (not raise; raising breaks
  w200's raw-SQL copy); "enqueue each selected window separately" read as a merge never joins two distinct selected
  windows nor exceeds 31 days, bridge comparison inclusive; "change instant" = `valid_from`; `cause` text is not
  stored (`recompute_job` has no column); a session row dirties selected windows overlapping the session's full
  accepted extent, not only START..new row. Out-of-brief edit: `test_w200_source_events_postgres.py` now excludes
  `ev_charging` from its no-dispatch-job assertions, asserts EV START enqueues, and clears EV jobs before its 0020
  downgrade refusal steps.

## Not started

3b: `ev_inputs/ev_persist/ev_sessions/ev_windows/ev_watermark/ev_still_mine/ev_complete`, `PostgresFindingStore.ev_apply`,
`EvAssessmentWorker`, `build_ev_assessment_worker`, `test_w206_ev_store_postgres.py`. Depends on P1-P4.

# W2-06 pending rulings — run 4 (q4)

Run 4 sub-run A landed `255ccbae` (q3 P2-P5 in pure `analytics/ev.py` + 63 rule tests) and `a3138bfb` (q3 P1
attestation in `test_w205b_ev_replay_postgres.py:Chain.attest`; six manifests byte-unchanged). Spec commit 2 (R12
vectors) is NOT landed: the parked producer `.agent/W2-06-2a-wip/W2-06-2a-wip.patch` is updated to P1 (clock proof
from `_attestations` at the committed disposition watermark over the full measurement interval) and P6 (sorted
Finding support IDs and first-cutoff IDs, actual first watermark). A write-mode trial on a private DB passed 6/6 with
every vector row `clock_attested=true` and the six manifests unchanged; the trial file was discarded. Blocking points:

- **Q4-1 first-cutoff `known_at` is not reproducible (blocks pinning).** P6 requires `first_cutoff.known_at` = the
  actual first committed disposition watermark, and ordinary mode to byte-compare the whole file. The W2-05b chain's
  `ingestion_disposition.decided_at` is the database `clock_timestamp()` (`PostgresEvidenceLedger._decision_instant`;
  the chain sets no `test_decision_clock_override`), so the trial wrote `2026-10-19T14:32:53.211221Z`; every run
  differs and the byte comparison can never pass. Options: (A) fix the chain's S2 decision clock with
  `PostgresEvidenceLedger.test_decision_clock_override` at a ruled instant sequence (manifests carry no `decided_at`;
  `received_at` stays the ingestion clock) — the ruling must name the instants; (B) pin `known_at` as a symbolic
  marker and assert the real watermark per run; (C) other.
- **Q4-2 P2 identity data is absent from the vector rows (blocks the backend pure vector test).** P2 makes
  `ev._source_reason` require the row's `binding_set_revision_id`, `role`, `device_id`, `signal_id` and the selected
  set's member rows (`EvInputs.binding_members`). Q1 fixes the row key set "exactly" (none of those four keys) and
  the case keys (no member list), so the pure test cannot build valid inputs: every row would be
  `EXCLUDED/SOURCE_UNVERIFIED`. (A trial that synthesized members from the rows reproduced all six `expected` objects
  exactly, so this is the only gap.) Options: (A) add the four accepted-row keys to each record and a case-level
  `binding_members` array (the selected set's `signal_binding_revision` rows: id, set id, role, asset, source,
  device, signal, valid_from, valid_to); (B) another source for the member rows; (C) other.
- **Q4-3 confirm whole-file write mechanics (reading, not yet built).** "Writes once ... byte-compares the whole file
  once ... no subset run may skip" read as: one non-parametrized test that runs all six chains, writes the whole file
  once under `ASSETOPS_W206_WRITE_VECTORS=1`, byte-compares once otherwise, with per-case assertions inside (adds
  about 2.5 minutes), instead of the parked per-case writes inside `test_six_registered_replays`. Also: render
  `first_cutoff.end_bounds` as JSON `null` (the R12 cell "end/end bounds null") while pure `EvSession.end_bounds`
  is `(None, None)`; and `known_at` text via `financials.fuel_cost.iso` (six fractional digits).

# W2-06 pending rulings — run 8 (commit 5 builder), 2026-10-19

Commit 5 is built with an interim answer in each slot below; none changes data, routes or the backend. Each needs an
Architect ruling (confirm the interim, or pick another option). Captures: `.agent/W2-06-evidence/`.

| # | Slot not fixed by spec / r5 / r6 | Interim built | Options |
| --- | --- | --- | --- |
| P1 | `sessions` panel 1 subtitle (mock: "120 kWh is the summed metered energy in complete records ..."); the ledger names no copy and r5 forbids mock aggregates | `Energy summary · Not available yet` (inline gap, `UnavailableInline`) | (a) keep gap; (b) a ruled sentence over `denominator` fields only; (c) drop the subtitle slot |
| P2 | `sessions` strip claim link `Inspect session lineage` (no proved evidence target) | in-place gap `Inspect session lineage · Not available yet` in the strip action slot (r5 null-link rule) | (a) keep; (b) omit until a target is proved |
| P3 | "short" ID form (session external IDs are 67-char `ev-<sha>`; Finding/record UUIDs) | external session IDs over 12 chars: first 11 + `…`; UUIDs: first 8; full value as accessible name and in the panel disclosure | (a) keep prefix; (b) suffix; (c) other length |
| P4 | Bounded conclusion big claim: ledger `Session {id} stopped after an observed connector fault.` vs r5 stocked sentence | r5 sentence when SUPPORTED with START/FAULT/ABORT; ledger kWh line and limit line kept below it | (a) keep; (b) ledger sentence first, r5 sentence as prose |
| P5 | Big claim for a non-supported (withdrawn) Finding or claim without exact START/FAULT/ABORT | the Finding's first stored limitation, else `Unknown` | (a) keep; (b) fixed sentence |
| P6 | `sessions` table and panels 2/3 body when currentness is `UNKNOWN` (no selection) | panel 1: server `currentness.limitation`; panels 2/3: `Unknown`; cards `Unknown`; no zero counts | (a) keep; (b) a ruled sentence |
| P7 | Pending (`PENDING_RECOMPUTE`) rows and Finding link | prior rows and `Open Finding →` stay visible under the strip's pending sentence; strip word `Evidence pending`, cards `Pending recompute`, Finding strip `Evidence pending` | (a) keep; (b) hide the Finding link while pending |
