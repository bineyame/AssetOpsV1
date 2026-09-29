# Planner Handoff - Lab Cockpit

Architect recommendation, 2026-09-30. Planning output, not task activation or
owner approval. Read with FEATURE_MAP's Lab cockpit entries and
`D-2026-09-30-lab-cockpit-cadence`, `-lab-cockpit-history` and
`-lab-cockpit-presentation` in DECISIONS. The Planner owns task ids, task files
and `tasks/README.md`; none is changed by this handoff.

## Authority, Timing And Recommendation

The owner explicitly commissioned consideration of
`Docs/lab-cockpit-proposal.md` (aeb4c99). It is an authorized additional planning
input despite the older routing documents' "only two sources" wording. It is
not an adopted decision. Simulator v4 remains the mechanism authority; the
corrected mini-grid roadmap and subsequent queue decisions retain the demo
order A, B, C, D, H, E, F, G, I. The proposal adds a way to inspect those
outcomes, not a new source of physics or product evidence.

The two Motivation images guide Lab presentation after content exists;
operator surfaces retain v6.9. The untracked technical walkthrough was read as
explanatory context, especially sections 4-7, 14-22 and 27-28. Its illustrative
numbers, schemas and timestep are not implementation requirements. It remains
untracked and untouched; this handoff does not depend on distributing it.

Use the owner's supplied state: T001-T025b are complete and merged, A has been
accepted, and T026 is next. The proposal's September 29 "after T025" means now.
Do not reopen A's acceptance or plan the already completed electrical work.

### Recommendations on proposal section 8

| Requested decision | Architect recommendation and reason | Decision owner/status |
| --- | --- | --- |
| 1. L1/L2/L3 or everything after T036 | Adopt the split. C1-C6 make existing physical behavior inspectable before expert feedback; C7 enrichment, C8 and C9 do not justify delaying that feedback. Split L1 into two vertical slices below because history/readback and cockpit interaction have different risks. | PROPOSED; owner chooses the investment and resulting delay to B/C. |
| 2. Before T026 or parallel | Put both L1 slices before T026, sequentially. T026 changes publication profiles, typed observations, gateway and the same host/projection seams; apparent frontend separation is insufficient. The shared checkout also permits only one editor. Parallel delivery needs explicitly isolated worktrees and an agreed history contract, with no clear present benefit. | PROPOSED; owner chooses priority. Existing queue remains in force until amended. |
| 3. Persistence or re-execution | Persist compact, complete Lab history with the execution artifact. Render old results without invoking a kernel. Matching frozen inputs alone cannot make a future kernel/profile implementation reproduce an old artifact. Re-execution remains an explicit new experiment, not a read operation. | Architect technical recommendation; proposed for the new slices. No owner choice of serialization library is needed. |
| 4. L2 shared check | Adopt a conditional per-slice rule: new runtime/reporting facts get an appropriate cockpit view and reload proof in their owning slice. Pure analytics/economics slices state that no cockpit data changed. This avoids both drift and a requirement for a new chart for every field. | PROPOSED with cadence; Planner incorporates the short rule below. |
| 5. Mockup corrections | Record a textual annotation beside the images, linked from cockpit tasks; retain the originals. The corrections below apply settled timing, evidence and intervention rules and need no new domain choice. | Architect recommendation; annotation included here, Planner assigns its delivery to L1. |

The outstanding owner question is whether to prioritize these two L1 slices
before T026 and adopt L2, or keep the current T026 start and move L1 later.
This handoff is complete whichever priority the owner selects. L3 breadth is a
later feedback choice, not a prerequisite decision now.

## What Exists And What Must Be Added

Grounding is deliberately limited to the relevant contracts and adapters:

- `.agent/T022-review-packet.md`, limitation "Criterion 12", records a final
  projection rather than the whole trajectory. This was correct for T022.
- `host/lab_execution.py:project`, `electrical_view`, `render_projection` and
  `parse_projection` now persist electrical summary steps (T024), generator
  steps/transitions (T025a), and typed reported generator states (T025b).
  Schema selection currently writes 3, 4 or 5 depending on content. Those
  existing series are reusable; the proposal's persistence premise is dated.
- The projection still retains only the latest per-load service, named flows,
  requested/accepted controls and effective controls; private stocks are a
  current view and `recent_reports` is capped at 12. These cannot supply full
  C2/C3 history. Digests are identities, not recoverable series.
- `Execution.boundaries` and the trajectory contracts carry addressed stocks,
  applied events, bounds, discrete transitions and control steps; the host
  generates observations from those boundaries. Capture existing facts here,
  without adding another physical calculation in React or the product backend.
- The host owns `var/executions`; normal run records in `var/runs` do not own
  private truth. Completed/failed projections reload; a running execution
  without its in-memory session reads INTERRUPTED and cannot resume.
- `step` serializes controls with a per-run lock and `from_boundary` guard.
  Stage publication has its own watermark and release blockers. Neither
  progress in the cockpit nor a completed private artifact proves stage or
  ingestion completeness.
- `SiteSingleLineDiagram.tsx` renders the shared configured SLD from its view
  model. `FrozenBusAttachment` already binds component, converter, bus and
  connection ids used by electrical execution. These are the reuse points;
  the screenshot is not a topology source.

## Feature Mechanisms

### One history projection and one persisted result

Extend the neutral Lab contract, served through the existing gated execution
port/routes by the host. A series response may be a separate single-run endpoint
for payload size, but is a projection of the same result, not another truth
store. No backend import of simulator/host; no operator consumer of Lab types.

Persist a compact history section in the host-owned execution artifact. It
contains each record once, not a cumulative LabProjection for every boundary:

| Record family | Required content and use |
| --- | --- |
| Manifest | Run id; frozen input identity; kernel/model/publication/numeric/execution versions; window/timestep/seed; history schema; recorded-through boundary; execution outcome; existing trajectory and observation digests; explicit availability of each history family. |
| State samples | Boundary offset/time, addressed state key, unit, exact value or typed enum, sampling phase. Stocks/discrete state at T are post-event; preserve state-at-T versus generator state-for-step. |
| Resolved intervals | Actual from/to offsets, per-address load demand/served/unserved, named flows with source/sink addresses, mean power/energy, requested and accepted controls, limits, effective control segments/provenance and existing balance results. Retain the segment timing needed for a reserve change. |
| Observation attempts | StateRef/device/signal, actual source time and interval where applicable, reading class/unit, reported value or absence, attempt outcome, suppression reason and reporting metadata. Capture all attempts, not the recent-report tail. Cadence distinguishes not-due from a failed due attempt. |
| Timeline facts | Applied-event entries with origin/share/phase, bounded transitions with requested/accepted/refused quantity, discrete transitions with phase/cause, recorded failure and reporting-gap windows/outcomes. Stable ordering for simultaneous entries retains phase and source identity. |
| Drawing context | Run-bound topology/component references needed to connect the history to the configured SLD, with provenance and explicit unavailable cases described below. |

Exact fractions retain the current lossless serialization at persistence/API
boundaries. Decimal conversion is display-only. Enums stay enums. Units,
StateRef and record identity travel with data; repeated loads never collapse
into one series because they have the same state key. Do not invent a public
signal to expose a private series.

The host derives historical values from the same boundary/observation semantics
used by today's projection. This is a presentation projection of the recorded
execution, not a second resolver or source of independent physical facts.
Existing summary fields may remain compatible views of those facts; new
history and summaries must agree at the last recorded boundary.

Introduce an explicit artifact/history schema change and strict reader. Bind
history integrity to its manifest and existing identities with a canonical
digest, distinct from the kernel trajectory digest; a projected subset cannot
claim to be the full canonical trajectory. Validate record ordering, address/
unit/type, boundary/window membership, declared coverage and integrity.
Keep atomic replacement and write failures inspectable. A failed history write
must not report a durably complete cockpit. Stage durability and eligibility
remain separately reported under the existing watermark rules.

COMPLETED and FAILED results persist their full recorded history, including a
failed prefix and the failure location. Live runs expose their available
in-memory prefix. L1 does not add durable resumable execution: after process
loss, retain the existing INTERRUPTED treatment, with no fabricated history or
resume button. Browser pause/resume applies only to a still-live session.

Old artifacts remain readable as what they contain. Show their existing
electrical/generator series where present; show unavailable history per family
where absent. Do not interpret the final snapshot or 12 reports as a full run.
Unknown/damaged new schemas produce the explicit unreadable state without
overwriting the file. Reading a result never executes it or alters it.

An artifact or API projection addition alone is not an execution-contract
bump. Apply `D-2026-09-22-contract-version-scope` if implementation actually
changes an already-valid frozen document's meaning or execution outcome.
Keep kernel, publication, envelope and artifact versions separate. Preserve
the contract-9 physical/observation reproduction proofs. The existing gate's
artifact-byte expectations need a narrowly documented schema-transition
update for new history writes; preserve fixtures/readers for the old layouts,
not a blanket golden-data rewrite that hides changed physics.

Storage and full single-run reads should grow with boundaries plus samples and
events, not with the square of boundaries. Never load series on the Runs index
or scan other runs to display one. Start with the declared demo windows and
measure payload/read/render cost there. If bounding is necessary, return
explicit range/continuation and coverage; never silently truncate a completed
chart. A database, universal telemetry registry or downsampling service is not
required by this feature. Existing inventory-cost work remains separate.

### C1 - Configured SLD with private runtime overlays

Reuse the existing topology/view-model/geometry substrate. Add explicit
presentation slots for node values and flow annotations; the Lab composes their
content outside the substrate. The shared renderer imports no Lab contract,
simulator, gate or shell and has no Lab/operator mode switch.

Use the run's frozen attachments and addressed records to bind overlays. Render
the modeled configured connections and components, including the three loads,
without hard-coded Kobo ids. The existing renderer needs run-bound drawing
context, not today's possibly changed Site topology. Prefer deriving supported
electrical drawing structure from frozen attachments. Where extra configured
structure/labels require Foundation readback, verify the referenced version
and attachment identities and retain the resolved presentation snapshot with
the result. If that basis cannot be established, show topology unavailable
and retain the numerical views. Never put old values on a silently substituted
current diagram. Do not add physical topology inputs merely to decorate it.

At the selected completed interval, map accepted source/sink flows onto the
verified configured path. Shared-bus arrows show aggregate branch transfer;
they do not claim source-specific electron tracing. Non-network accounting
flows such as potential, curtailed and clipped PV are labelled values, not
invented wires. Battery charge/discharge direction uses accepted flow endpoints,
with the existing signed-power convention stated. Zero flow, absent value and
unmodeled branch are distinct. Stock/discrete values show their instant and
flow values their interval. Breaker state/voltage/frequency are absent unless
an actual model or reported signal provides them.

### C2 - Addressed charts with truthful gaps

Use a shared simulation-time cursor across chart panels, SLD, C3 and C4. It
selects recorded boundaries/intervals; scrubbing does not execute anything.
Live follow follows the last available record; browsing history does not move
the execution clock. Completed and failed runs have the same inspection path.

Minimum panels: PV potential/accepted/curtailed (clipping distinguished), each
load's demand/served/unserved, battery SOC/reserve and signed power, fuel, and
generator physical/reported state. Use kW, SOC and litres in separate unit
panels on a common time axis, not a misleading mixed-unit value axis.

Pair truth and reports only for the same measured quantity/address and temporal
support. A sample at T of interval power describes [T-dt,T), while a controller
acceptance at T governs [T,T+dt). Align by the represented interval, not just
the row timestamp. First-boundary interval absence stays absent. Stocks show
post-event samples; avoid curves implying continuous physics never computed.

Plot a reported value once at its own source time. No carried stale value
becomes a fresh point at each execution boundary. Missing/suppressed/dropped
attempts break the reported trace; no interpolation or zero fill across them.
Sparse not-due instants remain sparse samples with stated cadence, rather than
being labelled dropout. Tooltips/inspectors can show a retained last reading
with its original time and STALE quality. Null, valid zero and unknown enum are
different states. No public counterpart means "not reported", not a copy of
truth. Reported traces expand in T026 as actual signal support lands.

### C3/C4 - Causal inspection and requested versus accepted control

Timeline lanes distinguish applied scenario/model events, physical/discrete
and bounded transitions, and reporting conditions/attempts. The ledger is the
authority for "applied"; scheduled frozen events may be shown separately as
planned, never as executed. Include phase and address for simultaneous events.
An interval-wide cause may have several applied contributions: grouping them
visually must retain their spans/shares in inspection. Reporting gaps are not
physical outages. FAILED generator state and FAILED execution are different.

C4 selects the same resolved interval as the charts: controller request and
reason, accepted control/output, resolver `limited_by`, effective reserve and
its provenance, per-load service and exact balance evidence. Present recorded
reasons, not a UI explanation inferred from similar numeric values. At a
boundary with no resolved interval, state that absence. Changing selection
must never combine historical intent with the latest acceptance.

### C5/C6 - Playback and run identity

Auto-play is a browser scheduler issuing one guarded Step at a time, scheduling
the next only after the previous response. Pacing changes wall delay only;
the frozen timestep, seed, physics and ordering stay fixed. Show pacing as a
delay or boundaries per wall-time target, not guaranteed physical "100x".

Pause cancels future requests; an already accepted request may finish and its
returned boundary must still be displayed. Stop scheduling on navigation,
hidden tab, gate loss, terminal status, refusal or network error. After a
timeout or `STEP_ALREADY_APPLIED`, read the authoritative position and require
explicit resume; do not catch up with a burst or blindly retry. Manual Step
and Run to end cannot race auto-play. A second tab stays protected by the
existing server guard. Reload starts paused; it may resume only if the host
still has the live execution. No server wall clock, speed field in identity,
live injection, restart/reset semantics or arbitrary jump execution is added.

Header shows run and Site identity/provenance, frozen window, current simulated
time, declared timestep, completed/total boundaries, seed and version details.
Use the port's boundary counts, including its terminal-boundary semantics;
derive no count from a guessed number of samples. Keep execution status,
playback state, selected historical time and stage/release status distinct.
Wall elapsed, if displayed, is this browser session's elapsed time only.

### C7-C9 - Followers with concrete prerequisites

C7's existing stage inspector remains reachable from the run throughout L1.
T026 extends its dispatch signals and gap/delay inspection; it need not build
a new side-by-side lane. Later C7 enrichment joins a displayed device report
to its actual persisted envelope/mapping identity, source and publication
times. Unpublished reports have no matching envelope. Stage means staged,
not "published to AssetOps"; ingestion receipt/outcome comes only from T027.

C8 requires real release/ingestion outcomes for logs and accepted arrival/
cadence evidence for source health. Its Lab diagnostic view may reference
those public records, while private gateway fault traces stay labelled Lab
diagnostics. Never compute operator Online from playback or a staged message.
T026A supplies additional delivery behaviors if scheduled; broad dashboards
remain feedback-dependent and gate no demo milestone.

C9 contains two different costs: a wizard over existing frozen setup may be
presentation work; New/Edit scenario authoring requires versioned immutable
scenario content, strict validation, save/identity semantics and a separate
planned slice. Neither is a hidden L1 requirement. No empty authoring controls
or general editor is introduced on the strength of the mockup.

## Planner Cuts, Observable Acceptance And Sequencing

L1a/L1b are handoff labels, not allocated task ids. Recommended order, subject
to owner priority confirmation:

`T025b (done) -> L1a -> L1b -> T026 -> T027 -> T028 -> T029 -> T029A -> T034
 -> T030 -> T031 -> T032 -> T033/T035 -> T036 -> feedback-selected L3`

T033/T035 remain interchangeable. T026A stays unscheduled, a prerequisite of
nothing. The cockpit adds inspection of accepted A; B/C/D/H retain their
existing completion meanings. Owner feedback at C/D may still redirect later
work. L3 is not promised as one large task or required to complete T036.

| Cut | UI-verifiable result | Minimum acceptance-level evidence |
| --- | --- | --- |
| L1a: persisted history, C2/C6 | Run a healthy and policy-varied mini-grid; inspect addressed day curves and truth/reported gaps; finish, restart the host and reopen the same curves and identity. | One full observation series longer than 12 reports; distinct loads; state versus preceding-interval timing; missing first interval; missing report versus valid zero; exact data round-trip and failed prefix; old artifacts disclose missing families; read with executor unavailable invokes no kernel; gate off hides routes/data. |
| L1b: C1/C3/C4/C5 | Play, pause and inspect one interval across SLD, charts, applied timeline and requested/accepted panel, then reload the result. | A real constrained request differs from acceptance with recorded reason; charging reverses the correct branch; each load stays addressed; event/transition phase agrees with state-at-T; historical selection uses historical flows; duplicate/late step and navigation do not double-advance; different pacing produces identical physical/observation digests. |
| L2: owning-slice additions | Every new observable mechanism is inspectable in the existing cockpit after reload. | A relevant case/record and its gap/absence semantics, with chart/timeline evidence when applicable. Pure product changes need no new Lab implementation. |
| L3: feedback-selected presentation | Audiences can follow actual publication/ingestion or setup work with the missing context feedback identified. | Define outcomes from delivered contracts before creating tasks; no C8/C9 placeholders or schedule commitment now. |

L1a should capture the existing history families needed by L1b in the same
artifact design; it need not render every lane yet. Both slices require user
review of the delivered interaction. A failure of data availability is returned
to its mechanism owner, not repaired by fabricating frontend data. Tables and
exact-value inspection remain available beside charts for verification.

Proof should pair visible behavior with an independently derived short window,
including a boundary event and a reporting gap; screenshots alone cannot prove
physics or isolation. Run the repository workflow/architecture checks and
affected host/contracts/frontend suites plus existing physical regression
gates. Layout-sensitive changes need browser evidence at supported widths with
populated charts/SLD, readable legends/tooltips, keyboard-operable selection
and non-color gap/state distinctions. Use isolated/copied var data and record
the commands/base URL/results; preserve the owner's Sites, runs and scenarios.
Record run size, history payload and single-run read/render measurements; do
not make a new inventory benchmark or general performance programme a gate.

### Amendments the Planner must make

Add to `tasks/README.md` shared checks, once cadence is adopted:

> A slice adding a physical state, accepted flow, reported signal, transition,
> reporting/publication behavior or intervention updates its applicable Lab
> history and chart/SLD/timeline/inspector in the same slice. Show addressed
> identity, time/interval, units, provenance and missingness; prove reload and
> gate isolation. A slice with no new Lab facts records that applicability in
> its packet. This does not create telemetry or operator health from truth.

| Existing work | Required amendment; preserve its current outcome |
| --- | --- |
| README/routing | Allocate L1 task ids and insert the adopted order; link this handoff and decisions, carry L2 and conditional L3 ownership. Update active/next routing consistently when activating the queue. No automatic change to the current T026 start from this proposal alone. |
| T026 | Consume history contract; expose new reported numeric/enum series and policy/operational effective-time markers with appropriate semantics. Retain T025b's already-built reported-status gap/stale behavior; correct criterion 8's implication that all such observation handling waits for T026A. Keep source versus publication delay in the inspector. Remove now-false pending disclosures when staging support lands. No new gateway reliability scope or full C7 lane. |
| T027 | Keep Commit and acceptance separate in run status; provide Open in AssetOps to the correct Site/window/history context after Commit, with actual release/acceptance outcome shown. A link never implies all records were accepted. Extend gate-off/rebuild proofs to all new Lab routes; operator views use only accepted evidence. |
| T028/T029 | Use the cockpit as optional Lab validation during review, not an input to classification, fuel quantities or money. Their product panels remain evidence-based; no new private series required unless the slice adds an actual runtime fact. Preserve early expert feedback and financial-assumption checkpoint. |
| T029A | Mark declared/applied POLICY_CHANGE and effective/reversion spans from immutable artifact/ledger provenance; select linked interval in C4. Keep declare/freeze/run and fresh-Draft reset rules. Auto-play creates no live intervention channel. |
| T034 | Inspect the relevant pre/post run independently in Lab; verification stays in comparable accepted operational windows. No private chart becomes verification evidence or a requirement for paired-run UI. |
| T030 | Show new physical fuel causes in the private lane and delivery/dip source records in their separate source inspector lane, retaining occurrence/publication/effective meanings. A missing delivery record is not an absent delivery; no theft inference from the timeline. |
| T031 | Headroom is an accepted-evidence conclusion. Reuse existing PV/load charts for Lab inspection; no new cockpit data if no model/reporting facts change. |
| T032 | New addressed load and its frozen topology/intervention appear in each run's SLD/chart/timeline. Links retain experiment/side context; product paired metrics remain accepted comparisons. L2 does not require a general multi-run chart/dashboard. |
| T033 | Add private stress history with its start basis/unknown state and new reported signals. Distinguish the evidence-derived product trajectory; never substitute private accumulation or relabel it measured SoH. |
| T035 | Show start-failure transition/cause privately, reported status separately and each load's service deficit. Distinguish physical generator FAILED from an execution failure or sensor outage. Reuse existing transition display rather than promising that state before the recipe exists. |
| T036 | Use reloadable cockpit records for final gated truth-versus-inference reveal. Join product results by run/window/evidence reference; truth flows only into the Lab comparison. Preserve operator walkthrough with Lab off and the successful plus claim-limited cases. L3/T026A remain optional. |
| T026A (when scheduled) | Add actual delay/retry/outage/buffering outcomes to appropriate diagnostics/inspector, preserving source time and distinct report/publication loss. Do not expand into C8 automatically. |

### Annotation to deliver beside the Motivation images

Use this content for a small linked text companion, not an edited bitmap:

- `SimulatorLab1.png` Step is the run's frozen declared boundary, not an editable
  one-second simulation step. The proposal's universal 15-minute example is
  dated: T024 daytime examples use 15 minutes; T025b mini-grid recipes specify
  5 minutes. Always display the selected run's actual timestep. Speed is
  playback pacing; "100x" promises no supported timing behavior.
- Quick Actions becomes the future declare-intervention-and-create-new-Draft
  workflow owned by T029A. No live injection, environment edit, destructive
  restart or arbitrary time jump is implied. A history cursor only inspects.
- Devices show actual reporting quality/source time in Lab. Operator Online/
  last-seen/source health needs accepted observation/arrival/cadence evidence.
  Gateway staging is labelled staged until real Commit/ingestion provides more.
- Draw configured modeled assets and the three addressed mini-grid loads. The
  pictured cold room and temperature are not default capabilities. T032 may
  explicitly add a cold-room electrical load without adding thermal physics.
- Do not copy live breaker positions, 400 V/50 Hz, weather values, arbitrary
  sample rates or topology from the image when no content contract backs them.
  Reuse the existing two shells; the mockup rail does not add operator routes.
- `ScreenMockups.png` screens 4-5 New/Edit and 8-9 health/log dashboards remain
  followers with the C8/C9 prerequisites above. Existing setup and inspectors
  remain usable; an omitted control does not promise upcoming capability.

## Owner Checkpoint

Only the owner can decide whether the value of early physical inspection
justifies delaying T026 by the recommended two L1 slices and adopting L2.
After implementation, the owner judges whether the cockpit makes behavior and
evidence loss understandable. Automated checks cannot certify that usefulness
or physical calibration. No new approval of A is requested by this handoff.
