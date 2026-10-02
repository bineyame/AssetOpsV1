# T026 - Dispatch-capable evidence

Status: planned; confirmed 2026-10-02 against T025e-T025g, build not started
USER_REVIEW_REQUIRED: true

Map: B extension beyond initial fuel staging.
Depends on: T023 (stage), A in T025a/T025b (status signal, profile 4), T025c-e
(history, cockpit, live follow), T025f/g (template v2; run binds scenario+site).
Next: T025h (floats, gates nothing), then T027.
Branch: task/T026-dispatch-capable-evidence
Sizing: evidence contract; three phases per `.ai/ROLE_CONFIG.md`.
Planner: Claude under `D-2026-09-30-planner-claude-until-reset` (Planner bound
to Claude until the Codex reset); owner-accepted outcome, scope and ACs kept.

## Outcome

Inspect staged PV, BMS, generator, meter and time-valid policy evidence for the
healthy and prolonged-runtime worlds, including one reporting gap and one
delayed publication.

This closes the evidence C actually needs to assess capability and operating
constraints. It deliberately stops short of gateway-failure realism.

## Thinned on purpose

This slice was `Dispatch-capable evidence and gateway recovery` and carried the
full outage, buffering, recovery, retry, duplicate, out-of-order,
buffer-exhaustion and noise/bias set. `Docs/queue-review-feedback-verbatim.md`
asked for exactly the evidence the first Finding needs and no more; T026A owns
the rest (`D-2026-09-24-queue-resequenced-for-demo`). Do not re-expand this
slice. If T023's publication path already makes an outage/recovery case nearly
free, include it and report that T026A shrank by that much. Building buffering
in order to demonstrate it is the thing this thinning refuses.

## Read for detail

- v4 sections 3, 6, 11-12, 17 and 25; roadmap 3.2-3.3 and 7/B-C; FEATURE_MAP B;
  `tasks/README.md` shared checks; T025e ACs 1-2 and 7-12.
- CODE_STATE T023, T025b, T025c, T025e-g only; `D-2026-09-22-contract-version-scope`, `D-2026-09-30-lab-cockpit-history`
  (with its chart clarification), `D-2026-09-30-lab-cockpit-presentation`,
  `D-2026-09-30-t025e-live-follow`, `D-2026-10-01-run-binds-scenario-to-site`.

## Preconditions from built state

- **Worlds.** Healthy = `kobo-mini-grid-evening`, prolonged runtime =
  `kobo-mini-grid-prolonged` (shipped v2). Scenarios name no site; each Draft
  picks its site at run setup. Tests build the site in process from the current
  Kobo template; nothing names KOBO-001, MG-001 or any `var/` site.
- **The owner's KOBO-001 cannot show this slice**: it lacks T025a's generator
  properties and status signal (prolonged is BLOCKED against it). The hands-on
  review uses a site the owner creates from the current template. No agent
  edits `var/`.
- **Versioning.** A shipped scenario or template change bumps version and pin
  (`backend/tests/content_fingerprint.py`); a scenario bump also edits
  `test_every_shipped_scenario_is_v2_superseding_v1` and rewords that
  document's `site_contract.description` (backlog T025g F3). A new
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

Prove that the gap and the delay change reporting/publication only, with an
identical world trajectory and identical controller decisions under the same
physical inputs. Prove cockpit reload exposes the added reports and
policy/record markers while the stage inspector retains distinct source and
publication times. A shipped run stages a real `INTERVAL_MEAN` and a real
`UNAVAILABLE` envelope. The contract-9 gate stays unedited and green.

## Phases

A fresh Implementer per phase; never resume one. Each phase ends with committed
work and `.agent/T026-phase-N-handoff.md` (what landed, file anchors, next, open
risks). The next phase starts from that file, not from re-reading the code.

1. **Contract and gateway (AC1-AC9, AC11-AC12).** Envelope/stage schema,
   profile and mappings, operational-record family, the two imperfections, the
   absorbed gateway and parser carries; simulator, contract and host tests. The
   handoff states the contract-version reading and the measured stage size and
   per-step write cost at the 8 h window. On screen, only stage content changes.
2. **History (AC13 host side).** New attempts and markers in persisted history,
   family classification, prefix proof, history schema move, delta wire.
3. **Lab and frontend (AC10, AC13 screen side, AC14, AC15)**, the absorbed
   timeline carry, layout evidence, then full suites and the packet.

Rely on facts earlier packets verified (T023 identity rules, T025e prefix and
delta proofs, the contract-9 gate); re-run only what a phase changed. Run suites
**serially**, never host and frontend together (T025e C9); full suites and the
packet are phase 3's. Layout evidence runs on a copy of `var/`.

## Named stops

- **Contract version.** Expected no move: a new profile version, schema moves
  and an artifact addition widen off every valid frozen Draft (precedents
  T023, T025b, T025c). A change to what an existing frozen Draft or profile
  3/4 does stops for the Architect and owner before it is written.
- **Template content.** New template devices or signals mean template v3:
  stop before the bump (the T025f `supersedes`/valid-from carry needs an
  Architect ruling; every existing site becomes BEHIND).
- **Stage format.** A whole-stage rewrite per step that misses the Step or tick
  budgets stops with the measurement: append-only is a persisted-format change.

## Absorbed carries (`.ai/MILESTONE_REVIEW_BACKLOG.md`)

- T024 electrical observations not published (AC1); T023 interval/unavailable
  envelopes proved on fixtures only (Proof): both closed.
- T025b enum mapping check skipped when all attempts miss: validate enum
  compatibility first; all-dropped and all-suppressed cases.
- T023 R2 (corrupt stage gives HTTP 500) and R3 (trailing newline accepted):
  fixed where AC5 extends the same parser.
- T023 stage rewritten whole per step: measured in phase 1 (stage-format stop).
- T025d C2 (timeline shows unreached declared gaps as applied): fixed, since
  AC13 adds gap and delay markers to that timeline.
- T025e C2 conditionally (AC15), and C3 if AC15 adds a chart panel or region.
- T023 stage buttons scale with the stage: above about 500 envelopes in a
  shipped run, the inspector selects by signal and time.

Still carried: T023 shared message ids (T027), T025d C1 (refresh path is
unchanged), T025e C1/C4-C9, T025g F4/F6 and residual risks.

## Scope limits

Commit and ingestion receipt time remain T027.
Gateway outage, buffering, recovery, retry, duplicate and out-of-order release,
buffer exhaustion and numeric bias/noise are T026A.
The operational family stays at override/command records here; fuel delivery
and hand-dip records and their completeness rules are T030.
Picker compatibility is T025h, purpose assumptions T025i; Full Replay and broad
source-health UI remain deferred as recorded in README.
This is still stage inspection, not an operator dispatch conclusion.

## Review

First review is **discovery** (new source family, schema moves), by whoever
`.ai/ROLE_CONFIG.md` binds then; before the Codex reset a fresh Claude
`assetops-reviewer`, and nothing waits for Codex (a Claude-only review joins
Codex's retrospective list). The report names its reviewer.

The owner follows one sample through the delayed case and identifies the two
timestamps. The Reviewer checks that C's required evidence has real owners and
that nothing from T026A was smuggled back in.
Review outcome: pending.
