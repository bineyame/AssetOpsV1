# T026 - Dispatch-capable evidence

Status: complete (owner accepted 2026-10-02 after hands-on check; Claude review ACCEPT after fix rounds 1-2)
USER_REVIEW_REQUIRED: true

Map: B extension beyond initial fuel staging. Next: T025h (floats), then T027.
Depends on: T023 (stage), T025a/b (status signal, profile 4), T025c-e (history,
cockpit, live follow), T025f/g (template v2; run binds scenario+site).
Branch: task/T026-dispatch-capable-evidence. Sizing: three phases (ROLE_CONFIG).
Planner and Architect: Claude under the Codex-reset exception (ROLE_CONFIG);
owner-accepted outcome, scope and ACs kept.

## Outcome

Inspect staged PV, BMS, generator, meter and time-valid policy evidence for the
healthy and prolonged-runtime worlds, including one reporting gap and one
delayed publication.

This closes the evidence C needs to assess capability and operating
constraints, and stops short of gateway-failure realism.

## Read for detail

- v4 sections 3, 6, 11-12, 17 and 25; roadmap 3.2-3.3 and 7/B-C; FEATURE_MAP B;
  `tasks/README.md` shared checks; T025e ACs 1-2 and 7-12.
- CODE_STATE T023, T025b, T025c, T025e-g only; the contract-version-scope,
  lab-cockpit-history (with chart clarification), lab-cockpit-presentation,
  t025e-live-follow, run-binds-scenario-to-site and 2026-10-02 decisions.

## Preconditions from built state

- **Worlds.** Healthy = `kobo-mini-grid-evening`, prolonged runtime =
  `kobo-mini-grid-prolonged` (shipped v2). Scenarios name no site; each Draft
  picks its site at run setup. Tests build the site in process from the current
  Kobo template; nothing names KOBO-001, MG-001 or any `var/` site.
- **KOBO-001 cannot show this slice** (no T025a generator properties or status
  signal; prolonged is BLOCKED). The owner reviews on a site created from
  template v3 (Named stops). No agent edits `var/`.
- **Versioning.** A shipped scenario or template change bumps version and pin
  (`backend/tests/content_fingerprint.py`); Kobo goes to v3 here. A scenario
  bump also edits `test_every_shipped_scenario_is_v2_superseding_v1` and
  rewords its `site_contract.description` (backlog T025g F3). The new
  degraded-evidence scenario is a new id at v1, pinned, naming no site.
- **Status source stays non-blocking** (T025g AC6b): without a frozen
  `generator-status` mapping, status is recorded absent. Blocking is a
  narrowing: stop.

## Deliver and acceptance

1. Extend the neutral envelope schema, publication profiles and frozen mappings
   for PV output/available capability, BMS SOC/power/discharge capability,
   generator status/power, load/service meter signals and policy records.
   Envelope schema 1 refuses enums (`refuse_an_enum_under_schema_1`), so status
   needs a schema move; stages written under schema 1 stay readable.
2. Distinguish observed output from available capability. Where a profile cannot
   report capability, leave it unavailable; C must not infer it from private
   PV potential or AcceptedFlowSet.
3. Policy evidence identifies version, effective interval and source.
   Component and Site Controls resolve to the operating time they govern.
4. Introduce the first operational-record source family here, narrowly:
   operator-commanded override/command records carrying identity, occurrence
   and effective time and actor/source provenance, with their own missing and
   delayed cases. They are not telemetry and do not inherit its cadence or
   interval semantics. T028 needs both the present and the absent override
   case, so this family cannot wait for T030, which extends it with delivery
   and hand-dip records.
   An absent override record never establishes that no override occurred.
5. Measurements retain StateRef/device/signal mapping and appropriate interval
   semantics. Strict unit, type and schema validation covers each new family,
   including the absorbed parser carries below.
6. Carry exactly two evidence imperfections: normal cadence with one reporting
   gap, and one delayed publication. That is enough for C to show a bounded,
   coverage-limited claim. Numeric bias/noise is T026A.
7. Source time and gateway/publication time are separate fields that the
   delayed case makes visibly differ. No ingestion received_at exists in stage
   content; T027 assigns it.
8. A discrete generator status is carried as an enum and is never numerically
   noised. Retain T025b's built reported-status gap/stale behavior; T026A owns
   further gateway dropout, retry and duplicate delivery behavior.
9. Exact canonical payloads and mapping/profile versions survive persistence.
   T023's retry, conflicting-identity and corrupt-artifact rules still hold and
   are not re-proved here.
10. The inspector distinguishes a sensor gap from a publication delay, so C's
    evidence gaps trace to accepted inputs. Broad publication-quality display
    is T026A.
11. Healthy, prolonged-runtime and degraded-evidence runs stage reconstructible
    dispatch datasets. Private recipe labels/oracles stay outside payloads.
12. Expanding the allowlist preserves strict refusal of arbitrary world/trace
    content and leaves Site accepted history unchanged.
13. Record new numeric/enum report attempts and policy/operational effective-
    time markers in T025c's persisted history. After reload, the appropriate
    addressed chart/timeline/inspector shows actual source time, quality,
    absence and publication delay; it does not infer a report from truth.
    T025e history rules: each new family is append, step-owned (with an owner
    rule, like `exposures`) or static, and `test_lab_history_prefix.py` covers
    it; one that fails is sent whole, never client-patched. A delay or late
    record is a new row at the boundary that publishes it, never an edit to a
    sent row; a future effective time is a field, not the key. A new persisted
    family moves the history schema; schema-2 artifacts disclose it as not
    recorded. Derived totals are host-recorded.
14. When staging support lands, remove any Lab disclosure that still says these
    reports or markers await staging (for example
    `GENERATOR_STATUS_REPORTED_NOT_STAGED` and the stage panel's "observed, not
    staged" line), without claiming Commit or acceptance.
15. **Cockpit fit (T025e).** Series join the day curves, markers the Applied
    timeline, inspector and stage detail the existing closed disclosures.
    Nothing above the cockpit grows per tick; no intermediate frames; one
    cursor drives every new view; stage is still re-read only after a control
    and on stop. T025e AC12 still passes with the new rows (deltas <= 32 KB,
    both 50 ms p95 budgets); a missed server budget takes T025e's named
    memoisation stop (backlog T025e C2) after measuring, else is reported.

## Proof

Run one healthy and one prolonged-runtime Draft through the full publication
profile. Record which C-required signals are present, their units and coverage.
Repeat with a discharge-capability gap and a missing override record.

| Fault | Expected stage |
| --- | --- |
| Sensor dropout | No fresh reading |
| Delayed publication | Original source time, later publication time |
| Missing capability | No private-state replacement |
| Missing override record | None observed, not absence of override |
| Policy effective at boundary | Correct version/effective time preserved |

Prove the gap and the delay change reporting/publication only: identical world
trajectory and controller decisions under the same physical inputs. Prove
cockpit reload exposes the added reports and policy/record markers while the
stage inspector keeps distinct source and publication times. A shipped run
stages a real `INTERVAL_MEAN` and `UNAVAILABLE` envelope. The contract-9 gate
stays unedited and green.

## Phases

A fresh Implementer per phase, never resumed. Each phase ends with committed
work and `.agent/T026-phase-N-handoff.md` (landed, anchors, next, risks); the
next phase starts from it, not from re-reading code.

1. **Contract and gateway (AC1-AC9, AC11-AC12).** Envelope/stage schema,
   profile and mappings, operational-record family, the two imperfections, the
   absorbed gateway and parser carries; simulator, contract and host tests. The
   handoff states the contract-version reading and the measured stage size and
   per-step write cost at the 8 h window. On screen, only stage content changes.
2. **History (AC13 host side).** New attempts and markers in persisted history,
   family classification, prefix proof, history schema move, delta wire.
3. **Lab and frontend (AC10, AC13 screen side, AC14, AC15)**, the absorbed
   timeline carry, layout evidence, then full suites and the packet.

Rely on facts earlier packets verified (T023 identity, T025e prefix/delta, the
contract-9 gate); re-run only what a phase changed. Suites run **serially**,
never host and frontend together (T025e C9); full suites and packet are phase
3's; layout evidence runs on a copy of `var/`.

## Named stops (Architect rulings 2026-10-02, Claude under the Codex exception)

- **Contract version: no move, confirmed.** T025g's test of
  `D-2026-09-22-contract-version-scope`: replay an existing frozen Draft on the
  new build. A new profile version, schema moves with prior readers, template
  v3 and a new scenario id reach new Drafts only (T023, T025b, T025c). Stop for
  Architect and owner before: changing what profile 3/4 publishes; adding state
  to an existing model profile's trajectory (existing digests change; derive
  capability in the observation transform or a new profile version); changing
  an existing reporting-path cause; template lineage in `FrozenWorldInputs`;
  any new refusal or block reaching an existing document (AC6b included).
- **Template v3: bump, no stop.** The two capability signals and mappings are
  new template content: `kobo-mini-grid-60kw` v3, pinned. Not UNAVAILABLE on
  v2: an unconfigured signal is not a reporting path (`reporting_inputs`), so an
  envelope would invent one. Override records are not template signals; the
  frozen gateway mapping declares their source against existing components. A
  template bump is version, pin and header note, no `supersedes`/valid-from
  (`D-2026-10-02-template-bump-record`). Existing sites read BEHIND, truly.
- **Delayed publication: scenario cause, profile answers**
  (`D-2026-10-02-delay-is-a-reporting-path-cause`). As with the fuel gap, the
  degraded scenario declares a reporting-path window and delay; the profile
  declares whether it can model it (else BLOCKED naming it). Value and source
  time never change; a delay that would reorder publications is refused (T026A).
- **Stage format: stop kept, not pre-decided.** Over budget, first write the
  same document less often (at the history write, stage first, never after a
  control or stop). Only if that misses does append-only (a stage schema move
  with a prior reader T027 must parse) stop for the owner.

## Absorbed carries (`.ai/MILESTONE_REVIEW_BACKLOG.md`)

- Closed: T024 electrical observations unpublished (AC1); T023
  interval/unavailable envelopes proved on fixtures only (Proof).
- T025b enum check skipped when all attempts miss: validate enum compatibility
  first; all-dropped and all-suppressed cases.
- T023 R2 (corrupt stage gives HTTP 500), R3 (trailing newline accepted): fixed
  where AC5 extends the parser. T023 whole-stage rewrite: measured in phase 1.
- T025d C2 (unreached declared gaps shown as applied): fixed with AC13's
  markers. T025e C2 conditionally (AC15); C3 if AC15 adds a chart panel/region.
- T023 stage buttons: above about 500 envelopes in a shipped run, the
  inspector selects by signal and time.

Still carried: T023 shared message ids (T027), T025d C1 (refresh path is
unchanged), T025e C1/C4-C9, T025g F4/F6 and residual risks.

## Scope limits

Commit and ingestion receipt time remain T027. Thinned on purpose: gateway
outage, buffering, recovery, retry, duplicate and out-of-order release, buffer
exhaustion and numeric bias/noise are T026A
(`D-2026-09-24-queue-resequenced-for-demo`); do not re-expand. An
outage/recovery case T023 makes nearly free may be included, reporting T026A's
shrinkage; building buffering to demonstrate it is refused. Fuel delivery and
hand-dip records and their completeness rules are T030. Picker compatibility is
T025h, purpose assumptions T025i; Full Replay and broad source-health UI stay
deferred (README). This is still stage inspection, not an operator dispatch
conclusion.

## Review

First review is **discovery** (new source family, schema moves) by whoever
`.ai/ROLE_CONFIG.md` binds then: before the Codex reset a fresh Claude
`assetops-reviewer`, nothing waiting for Codex (Claude-only reviews join Codex's
retrospective list, as do these Architect rulings). The report names its
reviewer. The owner follows one sample through the delayed case and identifies
the two timestamps. The Reviewer checks that C's required evidence has real
owners and that nothing from T026A was smuggled back in. Outcome: pending.
