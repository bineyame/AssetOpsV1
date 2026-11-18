# W2 EV technical design review - D-2026-10-17-w2-techdesign-ev

Reviewer: fresh Claude reviewer (independent, not the author). Target: `.agent/W2-technical-design-ev.md` at c5fce044, judged against `.agent/architect-W2-techdesign-ev-request.md` and the owner's bar ("not leave too much to the implementer architecturally and technically"). Checklist: cold review c8405733. I made read-only spot checks against the code and ran no suites.

## Verdict: RETURN (targeted amendment)

Much of the design is concrete: the 0024-0026 table shapes, the session state machine, the allocation rule, the meter-sum and boundary-split rules, the tariff gate and the Finding key. But it repeats all five failure types from the cold review. It also builds by reference on the unamended cold design: its parent is 04170b25, so cold M1-M3 are inherited, not resolved. Six Medium findings follow. All of them can be fixed in place.

## Findings

**M1 - Finding and assessment rows for EV are still dispatch-shaped, and the domain literals are unnamed.** (cold M1 repeated)
- `0009_finding_store.py:80-84,102`: `episode_start/end`, `candidate_minutes`, `necessary_minutes` and `indeterminate_minutes` are NOT NULL, as are `support_sha256` and `cited_evidence_sha256`. `0007:48-50`: `analytic_run.cohort_status/cohort_sha256/cohort` are NOT NULL. Design §1 (line 15) never maps them for `ev-session/1`, so the EV fault-abort Finding cannot be written without an implementer choice.
- Line 12 says "domain CHECK permitting EV" and "retain DISPATCH requirements". No EV literal is named for `finding.domain` or `recompute_job.domain`. The stored value is `'mini_grid'` (`analytics/finding_episode.py:78`), not `DISPATCH`. "If 0022 already added the generic columns, only widen" is a hedge, because cold 0022 is still under RETURN.
- Fix: give an exact EV value or a nullable relaxation for every NOT NULL dispatch column of `finding_revision` and `analytic_run`. Name one domain literal per table, with the CHECK keyed on `'mini_grid'`. Drop the conditional.

**M2 - The S2 refusals and the v4 contract change are undecided.** (cold M2 repeated, plus a new item)
- Line 48 reuses `EVENT_ID_CONFLICT`, and cold §1 still says `MESSAGE_ID_CONFLICT`. The existing kind is `MESSAGE_CONFLICT` (`0005:239`). The decision value, the conflict reference and the CHECK change are still unspecified.
- Line 11 says "connector ID must match the bound asset in S2 acceptance". The refusal code is not named, and neither are the codes for a bad `INTERVAL_DELTA` (wrong unit, non-positive interval, negative value).
- Line 39 adds **optional** `session_id,connector_id` keys to the v4 MEASUREMENT payload, so a v4 cold payload "without those keys remains readable". That contradicts W2-00's exact-key, explicit-null canonical rule and its `UNKNOWN_FIELD`/`MISSING_FIELD` refusals (cold §1). It also changes v4 after W2-00 ships. Likewise, `INTERVAL_DELTA` changes the "No new measurement class" rule in cold §1.
- Fix: decide one option. Either fold both keys, explicit null, and `INTERVAL_DELTA` into W2-00 v4 before it ships, or define schema 5. Name the S2 rejection kinds and the `conversion_kind` for `INTERVAL_DELTA`. Also, `ENVELOPE_MEASUREMENTS` is shared with v3 (`source_envelope.py:110`, imported at `source_envelope_v3.py:63`), so state that v4 gets its own allowlist.

**M3 - Rule-8 writer ownership is missing for seven new tables.** (cold M3 repeated)
- `tools/checks/configuration-persistence.ps1:620-680` pins nine writers to closed table lists. The design adds `ev_session`, `ev_session_revision`, `ev_session_evidence`, `ev_meter_interval`, `ev_consequence_revision`, `ev_consequence_session` and `ev_consequence_evidence`, and names no writer and no guard edits.
- Line 58 requires the session revision to append "atomically with `assessment_revision` and any FindingRevision". Those tables belong to two different writers (`postgres_assessment_store.py`, `postgres_finding_store.py`), so the transaction owner is an architectural choice.
- The EV consequence trigger path is also absent. The fuel path uses migration-trigger dirty rows in `financial_consequence_work` (rule 8 comment, 0011/0012). The design does not say what enqueues EV consequence work, or which worker writes it.
- Fix: name the owning adapter for each table, the transaction boundary, the consequence work trigger, and the exact `$*Tables` edits.

**M4 - The scenario contents cannot produce each case without implementer choices.** (cold M4 repeated)
- Lines 41-48 are qualitative only. They give no forcing times, no connector, no request kW, no dropped slot, and no hold or release time.
- Two scenarios still offer alternatives:
  - `late-record`: "END **or** one meter report";
  - `contradictory`: "START/END claims ... **or** overlapping meter intervals".
- Line 37's sanity guard forbids a duplicate START or a simultaneous END and ABORT in `ev-charger/1`. The `contradictory` case therefore cannot come from the model. The design does not say which layer produces it: an observation-profile fault, or a second source.
- Fix: give a forcing table for each scenario (UTC time, connector, kind, value), the initial state, and the expected public outcome (state, `energy_complete`, Finding yes/no). Pick one mechanism for each case.

**M5 - Response fields are named but have no shape.** (cold M5 repeated)
- Line 66 and lines 70-76 leave these without a shape:
  - the `currentness.state` vocabulary;
  - `source_provenance` and `limitations`;
  - overview `status.state`, `objective`, `findings`, `needs_attention`, `consequence_summary` and `site_power.coverage`;
  - `capabilities[].claim` (no enumerated claim IDs) and `coverage`;
  - `readiness.state`, `commissioning.state` and `contact.state`;
  - session `start_bounds/end_bounds` and the `reason_codes` vocabulary;
  - `links`.
- Fix: enumerate the vocabularies and give the inner fields, or cite the exact W1 or part-1 read model each one reuses.

**M6 - The vendor-format peer is put in scope, but its format is unnamed.** (request item, owner bar)
- Line 99 puts `vendor-format-ev-peer/1` in W2-05b but does not name the raw format: OCPP 1.6J Start/Stop/MeterValues, a CSV export, or something else. It also leaves open the cumulative register unit (Wh or kWh), the fixture location, the module owner, and the exact refusal codes. The implementer would be choosing the vendor contract.
- The recommendation itself is defensible, because the cumulative-to-delta conversion is real risk worth exercising. But it adds work to W2-02 and W2-05b against the W1 demo-speed priority, and the design does not weigh that trade-off for the owner.
- Fix: either name the raw format and its field mapping, or recommend deferring the peer to the pilot gate. State the cost either way.

## Low (non-blocking)
- L1: The screen mapping is sound, and the owner flag is honest. But the v69 mock already contains EV-extrapolated screens, which can serve as content references: `ev-foundation`, `ev-readiness`, `ev-sld`, `ev-finding`, `ev-findings`, `ev-evidence*` and `ev-financials` (`screen-manifest.json:1095-1645`). §7 cites only lines 471-504. The design should cite each one, and say that the mock `energy` and `availability` screens are not promoted even though Overview carries `energy` fields.
- L2: The `ev_session` UNIQUE omits `tenant_id`, unlike the composite-key convention. `ev_consequence_revision` has two uniques per window but no succession rule for `revision_no`.
- L3: `overlap_group=site/window/tariff` is a template with no exact string format.

## Checks against the request
- Concrete enough: Foundation/topology and readiness codes (§2), the simulator state and allocation (§3 model), meter-sum and currentness rules (§4), tariff selection and gates (§5), error envelope and pagination (§6), and the per-slice proof list (§8).
- Open choices remain: B2 data model (M1, M3), the source contract (M2), B4 scenarios (M4), B7 reads (M5), and the vendor scope (M6).
- Fail-closed rules are sound:
  - no pro-rating;
  - no zero fill or power substitution;
  - quantity null rather than zero;
  - no lost sales;
  - a single tariff across the window, otherwise UNPRICED;
  - aborted sessions price delivered energy only.
- Code-checked as correct:
  - the closed model registry (`host/execution_adapter.py:127-143`);
  - btree_gist is already available for the GiST exclusion (0001/0002/0010);
  - the fuel-only consequence CHECK is avoided;
  - `0001:66` already permits the EV site type.

## Not verified
I ran no suites and no registry checker. I did not trace binding-role `value_kind` support for EVENT or `INTERVAL_DELTA` roles (cold L1 likely applies).
