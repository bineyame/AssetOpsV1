# T025b - Generator policy recipes, reported status and A acceptance

Status: complete
USER_REVIEW_REQUIRED: true

Map: A completion.
Depends on: T025a.
Next: T026 dispatch-capable gateway, then T027 internal architecture demo.
Branch: task/T025b-generator-policy-and-a-acceptance
Sizing: policy/observation extension and integrated A acceptance checkpoint.

## Outcome

On the same Site, inspect separately frozen healthy, prolonged-generator and
changed-policy runs in Lab. See recovered PV/battery capability while Site
policy keeps the generator requested, then explain how a changed stop policy
changes runtime, flows, fuel, reserve and service. Inspect reported generator
status separately from physical state, including missing/delayed reports.

## Read for detail

- Controlling: `.ai/DECISIONS.md`, D-2026-09-29-t025-generator-policy-package.
- `tasks/T025a-healthy-generator-runtime.md` and its delivered review packet.
- `.agent/T025-architect-recommendation.md` and `.agent/T025-implementer-plan.md`
  are supporting context; the decision resolves their questions and conflicts.
- v4 sections 4.3, 5-10, 17, 23 and 25; roadmap sections 3.1-3.3 and 7/A.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Use `mini-grid` v2 for added override/model support; do not edit shipped v1
in place. Own original T025 criteria 7-9, 11-12; criterion 13 for prolonged
and changed-policy runs; the remaining portions of 15 and integrated A review.

## Acceptance criteria

1. A prolonged-runtime recipe authors policy/recovery/load causes only, never
   generator output or an avoidability conclusion. PV and battery capability
   recover while the generator remains requested under the declared stop policy.
2. Control policy remains Site-owned: start at SOC <= frozen start threshold;
   stop only when RUNNING, Site minimum runtime has elapsed and SOC >= effective
   stop threshold. Add no model-owned trigger. Execute frozen `source-priority`
   (Kobo `[pv-array, battery, generator]`) without substitution. Preserve T025a's
   load/headroom-limited generation, fuel-before-energy acceptance and disclosed
   linear fuel law.
3. Extend reverting overrides only to profile-declared numeric CONTROL
   addresses for battery reserve and generator stop threshold. Freeze baseline
   provenance and target/value/window; absolute replacement applies on
   `[start,end)`, then baseline returns. Refuse overlap and unsupported timing;
   adjacent windows are valid. Keep 5-minute generator steps and aligned
   start delay, policy windows and minimum runtime; count actual RUNNING time.
   Preserve older profile behavior and do not edit Foundation for comparison.
4. A separately frozen changed-policy scenario on the same Site produces an
   explainable runtime/flow change. Demonstrate long enough to reach the
   differing stop conditions. Use the decision's demo values: start 35%, stop
   90% versus 60%, minimum runtime 30 min, 40 kW, 0.3 L/kWh, tank 400 L and
   scenario-owned initial fuel 300 L; review them at the hands-on checkpoint.
5. Reserve-violation and constrained-service cases remain visible alongside
   runtime/fuel results. A raised reserve creates no energy or permission for
   illegal discharge. Lower generator runtime alone is not an improvement claim.
6. Typed enum status survives the observation transform, persisted artifact
   and gated Lab projection, retaining T025a's state/trajectory/controller
   typing. A state-at-instant reading at T observes a transition already due at
   T; a newly emitted request is not retroactively observed. Generator power
   describes the completed interval. Reject numeric bias/noise/quantization
   settings for enums. Freeze publication profile 4 when these signals land;
   retain prior profiles/readers and version any changed persisted layout.
7. Public generator status/power comes through the observation path into the
   reported side of gated Lab. Missing/delayed status and stale reporting leave
   physics and local control unchanged. Envelope schema 1 and the fuel-only
   mapping stay; disclose generator status as not yet staged. A mapping
   promising an enum under numeric schema 1 refuses rather than silently
   omitting it or disguising it as a decimal/UNAVAILABLE. T026 owns staging.
8. Same frozen identities reproduce prolonged/changed-policy trajectories;
   initial fuel, SOC, lifecycle/timer state and time-valid effective policy are
   reconstructible. Retain T025a's contract-9 compatibility proofs, including
   execution of old frozen fuel/daytime inputs and `mini-grid` v1 readback and
   behavior. Physical FAILED remains inert at initialization; failure causes
   stay refused until T035.
9. Deliver A's integrated acceptance packet: independent balances, boundary
   timing, request/output separation, changed forcing/policy demonstrations,
   hand-checked energy/fuel and visible reserve/service consequences across
   the complete Lab site.

## Proof

| Case | Expected observation |
| --- | --- |
| Healthy versus prolonged interval | Recovered capability with policy-caused continued request |
| Stop 90% versus 60% | Explained runtime/flow/fuel change through physics |
| Override start/end and adjacent windows | Exact replacement/reversion; overlap refused |
| Low reserve and constrained service | Explicit reserve/service consequences |
| Status sample coincides with due transition | Post-transition enum, no retroactive new request |
| Missing/delayed status report | Report changes; identical physical/control trajectory |
| Repeated frozen runs and old-profile regression | Reproduction and stored readback preserved |

Run simulator/host, setup and frontend tests, shared checks and complete,
populated Lab layout evidence. Compare healthy/prolonged/changed-policy traces
and hand-check generator energy to load and battery, fuel and balances.
Combine this evidence with T025a's packet for the A walkthrough.

## Scope limits

This demonstrates A, not an all-else-equal PairedExperiment or verified
intervention. No Finding, economics or intervention UI. Lab reported values
are not accepted operator history; B remains incomplete. T035 owns the
cause-authored start-failure/recovery/service recipe and product assessment.

## Review

The owner reviews A on the complete Lab site: healthy behavior, cause-authored
prolonged runtime, forcing/policy response, reserve/service consequences and
demo values. Independent review checks the integrated proof packet and truth
boundaries. Synthetic proofs do not establish calibrated fidelity to a plant.
Review outcome: accepted by the owner on 2026-09-29 after the hands-on A walkthrough.

Independent review 2026-09-29: Codex, ACCEPT WITH CARRY, no blocking findings
(`.agent/T025b-codex-review.md`); C1 carried to the milestone backlog.
Owner decisions 2026-09-29: the implementer's demo values are accepted
(decision values plus proposed irradiance, loads, initial SOC 40 %, profile-4
status every 15 min with 40/1000 dropout, 15-min generator power); setup keeps
no preselection when more than one profile is offered - the owner selects by
hand. The owner completed the hands-on A walkthrough successfully on
2026-09-29 in a demo environment (`.demo/T025b/`, not tracked); A is accepted.
