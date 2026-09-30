# T025c - Persisted Lab history, addressed charts and run identity (L1a)

Status: complete
USER_REVIEW_REQUIRED: true

Map: Lab cockpit C2/C6; inspection of accepted A before B.
Depends on: completed T025b, T024 electrical summaries and T022/T023 Lab execution/stage.
Next: T025d, then T026.
Branch: task/T025c-persisted-lab-history-and-charts
Sizing: larger than one focused change; build in the phases below under
`.ai/ROLE_CONFIG.md` rather than adding unreviewed scope.

## Outcome

Run healthy and policy-varied mini-grids in gated Lab, inspect each addressed
day curve and its actual reported samples/gaps, then restart the host and reopen
the same result, run identity and recorded coverage without executing it again.

## Read for detail

- `.ai/PLANNING_HANDOFF_LAB_COCKPIT.md`: history, C2/C6, proof and annotation.
- `D-2026-09-30-lab-cockpit-cadence`, `-history`, `-presentation` in
  `.ai/DECISIONS.md`; `.ai/FEATURE_MAP.md` Lab cockpit C2/C6.
- v4 sections 3, 6-10 and 25; shared checks in `tasks/README.md`.

## Phases

1. **History and readback:** extend the neutral gated Lab projection and
   host-owned execution artifact with the handoff's manifest, addressed state
   samples, resolved intervals, all observation attempts, timeline facts and
   run-bound drawing references. A single-run read exposes recorded coverage
   and exact values in a simple inspector, including old-artifact absences.
   End with a committed handoff at `.agent/T025c-phase-1-handoff.md`.
2. **Charts and identity:** add synchronized addressed chart inspection and the
   run header over that record; prove finish/restart/readback and populated
   layout. End with the full packet and user review. Each phase uses a fresh
   Implementer as `.ai/ROLE_CONFIG.md` requires.

## Acceptance criteria

1. Persist compact, complete per-run history with a declared schema, manifest,
   family coverage and canonical integrity digest distinct from the trajectory
   digest. Keep exact fractions lossless, enums typed, units, StateRefs, address,
   source identity, phase and actual interval/time. Store each record once.
   Strict read rejects damaged/unknown new schemas without overwriting them.
2. A complete run reloads all recorded series, including an observation series
   longer than the current 12-report tail. FAILED reloads its recorded prefix
   and failure location. A lost live session remains INTERRUPTED, with no
   fabricated continuation. Old artifacts disclose each unavailable family
   and retain their existing series; a final snapshot is not a full curve.
3. Charts show PV potential/accepted/curtailed with clipping distinguished;
   each load's demand/served/unserved; battery SOC, reserve and signed power;
   fuel; generator physical and reported state. Separate kW, SOC and litre
   axes; keep a table/exact-value inspector beside the plots.
4. A shared simulation-time selection identifies actual boundaries/intervals.
   State at T is post-event; an interval report at T describes the preceding
   interval, while a control accepted at T governs the following one. The first
   interval's absent sample stays absent. Generator state-at-T remains distinct
   from generator state-for-step. Browsing does not advance execution.
5. Plot each report once at its source time. A missing/suppressed/dropped due
   attempt breaks the reported trace; sparse not-due instants retain cadence.
   Stale last reading keeps its original time and label. Valid zero, null,
   unknown enum and unreported private state remain distinguishable.
6. Header shows run/Site and frozen-input provenance, window, actual timestep,
   simulated position, port-supplied completed/total boundaries, seed, versions,
   execution outcome, recorded coverage and stage status separately. Charts
   and identity reload without a live kernel or host execution session.
7. New history is gated at route, API and UI; no operator view consumes it.
   Stage durability/eligibility remains separately reported. A failed history
   write is inspectable and never claims a durable complete cockpit. Reading
   changes no artifact.
8. Supply `Docs/UI Design/Motivation/LabCockpitNotes.md` beside the two
   Motivation images with the handoff's annotation corrections; keep the images
   intact. Link the companion from both L1 delivery packets.

## Protected seams and proof

Host owns private history; backend sees only neutral gated projections.
Product conclusions continue to read accepted canonical envelopes. Run-bound
addresses and topology references are retained for T025d. An artifact-only
schema addition does not force an execution-contract bump; apply
`D-2026-09-22-contract-version-scope` if frozen execution meaning changes.
Preserve old readers/fixtures and the contract-9 reproduction gate; document
the narrow artifact-byte schema transition in that gate.

Pair visible healthy/policy-varied curves with an independently derived short
window containing a boundary event and reporting gap. Prove distinct loads,
missing versus zero, first-interval timing, exact round-trip, failed prefix,
old/unknown schema behavior and no kernel invocation when reading with the
executor unavailable. Measure demo-window artifact size, single-run payload,
read and render cost; growth is proportional to records, not squared by
boundary count. Runs inventory loads no series and a single-run read scans no
other runs. Run affected contracts/host/frontend tests, physical regression
gates, shared checks and populated browser layout evidence at supported widths
including keyboard selection and non-color gap cues. Use copied/isolated var.

## Scope limits and review

T025d owns SLD overlays, causal timeline, requested/accepted panel and
auto-play. C7's existing stage inspector remains reachable. No re-execution
on read, durable resume, new physical law, public telemetry from truth, Commit,
ingestion, C8 dashboard or C9 authoring is introduced.

The owner reviews whether addressed behavior and evidence loss are legible
after reload. The Reviewer checks record integrity, timing, gate isolation and
that chart values agree with recorded history. Review outcome: pending.

## Review Outcome

Accepted by the owner on 2026-09-30 after a hands-on check in a demo
environment (`.demo/T025c/`, not tracked): completed mini-grid v2 runs on
KOBO-001 were inspected, the host restarted and the runs read back PERSISTED
with their charts, values and identity intact.

Independent review: Codex first review 2026-09-30, RETURN with one blocking
finding (R1, projection-backed cockpit data outside the history digest) and
four carries (`.agent/T025c-codex-review.md`). R1 fixed in 761b1b4/40d9515
(history schema 2, `projection_binding`); Claude verification review ACCEPT
(`.agent/T025c-claude-verification.md`). K2 fixed in ef408a5; C1-C4, K1 and K3
carried to `.ai/MILESTONE_REVIEW_BACKLOG.md`. The full ~1 MB-per-8-hours
single-run history payload and the two-document artifact layout stand, as the
Codex review found acceptable; T025d accounts for live recapture cost.
