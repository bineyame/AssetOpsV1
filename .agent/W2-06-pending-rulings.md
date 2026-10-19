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
