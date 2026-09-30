# T025d - Lab SLD, causal inspection and playback (L1b)

Status: complete
USER_REVIEW_REQUIRED: true

Map: Lab cockpit C1/C3/C4/C5; inspection of accepted A before B.
Depends on: T025c persisted history and the completed T025b runtime.
Next: T026.
Branch: task/T025d-lab-cockpit-inspection-and-playback
Sizing: larger than one focused change; build in the phases below under
`.ai/ROLE_CONFIG.md`.

## Outcome

Play, pause and select one resolved interval in gated Lab. The run-bound SLD,
addressed charts, applied timeline and requested/accepted panel explain the
same recorded state and flow; reload gives the same inspection result.

## Read for detail

- `.ai/PLANNING_HANDOFF_LAB_COCKPIT.md`: C1/C3/C4/C5, timing and proof.
- `D-2026-09-30-lab-cockpit-cadence`, `-history`, `-presentation` in
  `.ai/DECISIONS.md`; `.ai/FEATURE_MAP.md` Lab cockpit C1/C3/C4/C5.
- T025c and `Docs/UI Design/Motivation/LabCockpitNotes.md`; shared checks in
  `tasks/README.md`.

## Phases

1. **Recorded interval inspection:** bind a verified run topology to the
   shared SLD, then expose synchronized SLD, applied timeline and historical
   control/flow inspection. One constrained interval is UI-verifiable. End
   with `.agent/T025d-phase-1-handoff.md` and committed work.
2. **Playback and integrated proof:** add guarded browser play/pause/pacing,
   verify all panels through live, terminal and reload states, then prepare the
   packet and user review. Use a fresh Implementer for this phase.

## Acceptance criteria

1. Reuse the configured SLD substrate through neutral presentation slots;
   compose Lab overlays outside the shared renderer. Bind frozen attachments,
   addressed history and verified run-time topology/presentation context.
   Changed current topology cannot silently receive old values; unsupported
   drawing context says unavailable while numerical inspection remains usable.
2. At the selected completed interval, show accepted source/sink branch flow,
   each addressed load's service, battery direction/state and available
   component values. Shared-bus arrows mean aggregate branch transfer only.
   Potential/curtailed/clipped PV are labelled accounting values, not wires.
   Zero, absent and unmodeled differ; stock instant and flow interval are named.
3. Timeline separates applied scenario/model events, bounded/discrete physical
   transitions and reporting conditions/attempts. It carries phase, origin,
   share, address and span for simultaneous or interval-wide causes. Planned
   events are never labelled applied; reporting gaps are not physical outages.
4. For the selected resolved interval, show controller request and recorded
   reason, accepted output, `limited_by`, effective reserve/provenance, each
   load's service and exact balance. Selection uses historical records, never
   the latest values; a boundary without a resolved interval says so.
5. Browser auto-play sends one guarded Step at a time, waits for its response,
   and changes wall delay only. Pause cancels future requests but displays an
   already accepted step. Navigation, hidden tab, gate loss, terminal state,
   refusal and network error stop scheduling. Timeout or
   `STEP_ALREADY_APPLIED` refreshes the authoritative position and requires
   explicit resume; no catch-up burst or blind retry occurs.
6. Manual Step and Run to end cannot race auto-play; the server's
   `from_boundary` guard protects a second tab. Reload starts paused and may
   resume only while the host retains the live execution. Different pacing
   yields identical physical and observation digests for frozen inputs.
7. The selected history cursor, execution clock, playback state and stage
   status stay distinct. The existing stage inspector remains reachable;
   neither a completed private run nor a full chart claims publication or
   ingestion completeness.

## Protected seams and proof

The shared SLD imports no Lab, simulator, gate or shell type. It does not invent
breaker state, voltage, frequency, weather or source-specific electron paths.
History is a host-owned gated projection, not product evidence. No live
intervention, reset, arbitrary time jump or mutable timestep is added; T029A
owns declare/freeze/new-Draft changes.

Use a short independently derived window with event, reporting gap, constrained
request and charge/discharge reversal. Check event phase against state-at-T,
branch direction, each load address, historical selection and exact balance.
Exercise late/duplicate step, navigation, gate loss, restart and pacing. Prove
reload with executor unavailable does not re-run. Run affected host/contracts/
frontend tests, contract-9 regression, shared checks and populated layout
evidence at supported widths with keyboard-operable cursor and non-color cues.
Measure demo-window read/render cost; use copied/isolated var.

## Scope limits and review

T026 extends actual dispatch reports and stage inspection. C7 enrichment,
C8/C9 and optional T026A remain later work. No paired-run dashboard or new
operator conclusion is part of this slice.

The owner reviews whether one selected interval explains physical behavior
and evidence loss. The Reviewer checks SLD/run binding, timeline causality,
historical controls and guarded playback. Review outcome: pending.

## Review Outcome

Accepted by the owner on 2026-09-30 after a hands-on check: functional
behaviour is OK. The owner found the page poorly organised and flickering
during playback; that is routed to T025e (Lab cockpit organisation and
playback smoothness, frontend only) per `.agent/T025e-architect-guidance.md`
and is not a T025d defect.

Independent review: Codex first review 2026-09-30, ACCEPT WITH CARRIES
(`.agent/T025d-codex-review.md`); C1-C3 carried to
`.ai/MILESTONE_REVIEW_BACKLOG.md`, C3 closing in T025e.
