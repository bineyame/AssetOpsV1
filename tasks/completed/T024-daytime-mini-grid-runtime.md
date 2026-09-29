# T024 - Daytime PV, storage and addressed load service

Status: complete
USER_REVIEW_REQUIRED: true

Map: A, first electrical demonstration.
Depends on: T023 and the addressed runtime from T020A1/T021.
Next: T025 completes generator operation and A.
Branch: task/T024-daytime-mini-grid-runtime
Sizing: simulator extension with one daytime operating story.

## Outcome

Lab runs a Kobo-like daytime mini-grid with residential, critical clinic and
productive load profiles. See PV potential/output, battery SOC and power,
served/unserved demand, curtailment and named flows against simulation time.
Changing irradiance or one load profile changes physical service coherently.

The narrow fuel runtime cannot establish dispatch avoidability.
This slice introduces the smallest useful electrical world; T025 adds the
generator lifecycle instead of concealing it inside a monolithic A task.

## Read for detail

- v4 sections 4-10, 16-17 and 25.
- Roadmap sections 3.1-3.2, 7/A and 8.
- FEATURE_MAP A and model-owned need trigger.
- DECISIONS: D-2026-09-22-foundation-value-declaration.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Extend one mini-grid model profile and explicit fixture, not a generic plugin
framework. Use addressed components and declared topology.
Consume irradiance and individual demand/schedule forcings physically.

Introduce time-valid typed Site Controls for source priority and critical-load
priority alongside component reserve/power controls. Keep ControlAssumption
documentary. Freeze effective control values and their provenance at setup.

Build a controller-local view, ControlIntent and deterministic physical
resolver. Evolution uses AcceptedFlowSet; requests remain inspectable separately.
Use rational PV conversion, battery efficiency/energy limits and load allocation
sufficient for the demonstration.

## Acceptance criteria

1. LOAD-RES, LOAD-CLINIC and LOAD-MILL have independent addresses, demand and
   served/unserved results. Changing one profile leaves sibling demand intact.
2. PV potential follows irradiance and configured capability; delivered PV and
   curtailment account for accepted load/storage use.
3. Battery evolution respects capacity, SOC, reserve, PCS charge/discharge
   limits and declared efficiency. Run-start SOC is explicitly initialized.
4. Source and critical-load priorities are typed Site Controls consumed by the
   controller/resolver; component reserve remains a component property.
5. An input declaring a baseline policy resolves from time-valid Foundation/
   Controls. A scenario change is an event over that baseline.
6. The controller consumes declared local inputs and cannot mutate world state.
   Its view is independent of public reporting cadence or sensor gaps.
7. A request for 30 kW with a 22 kW physical limit retains both values; only
   accepted power contributes to stock evolution and later readings.
8. Exact source/sink balance includes served demand, charging/discharging,
   conversion losses, curtailment and unserved load.
   Invariant failure is typed, not hidden by a numerical tolerance.
9. A shortage respects declared critical-load priority and reports residual
   unserved demand. A surplus charges within limits, then curtails.
10. Boundary samples follow v4 section 6 for SOC and preceding-interval power.
    Changing step batching leaves the canonical trajectory unchanged.
11. Lab shows per-load demand/service, aggregate PV/battery state and named
    flows with units, time and requested versus accepted controls.
12. Extend generated device observations for the electrical signals required by
    T026. Their readings remain separate from private accepted-flow objects.
13. If a new physical law needs a Foundation value absent from scenario
    declarations, implement the model-owned need declaration (Option C) here.
    Freeze that addressed answer with provenance and block when absent.
    If no law triggers it, record the examined laws and carry the trigger.
14. Profile conformance proves the newly advertised executable states/roles.
    Fuel-only OPTIONAL limitations do not silently become electrical support.
15. Freeze all new effective inputs and apply relative version moves where
    existing executable behavior changes. Old runs remain unchanged.

## Proof

Demonstrate a healthy sunny interval and three controlled variations:
lower irradiance, larger productive demand and a tighter battery power limit.
For each, inspect accepted flows and assert exact balances and SOC bounds.

| Case | Expected behavior |
| --- | --- |
| Two same-type loads with different profiles | Independent demand/service |
| PV surplus, battery full | Explicit curtailment |
| Demand exceeds capability | Priority-based service and unserved load |
| Requested 30 kW, limit 22 kW | Separate intent and acceptance |
| Reporting dropout | Same physics/controller behavior |
| Missing law-required Foundation property | Input-specific BLOCKED |
| Run-start SOC absent | Honest unresolved initialization |

Use independent energy calculations for at least one charge and one discharge
interval, including losses. Run simulator/host, setup and frontend tests,
shared checks and populated Lab layout evidence.

## Scope limits

Use a generator-stopped daytime baseline in this slice.
Generator start/stop/failure and full healthy reference belong to T025.
Commit, operator metrics and Findings remain later.
No AC network solver, general optimizer or battery electrochemistry.

## Review

The owner changes a forcing and judges the visible physical response.
The Reviewer checks balance, addressing and controller/physics separation.
This advances A; T025 is its completion checkpoint.
Review outcome: accepted on independent review and on owner review 2026-09-29.

**Independent review.** Codex returned R1 (scenario initialization could supply
or mask a model-owned Foundation need), R2 (declared topology neither
constrained execution nor entered the frozen inputs) and R3 (Foundation
validity recorded but not enforced). Fixed in a fresh Sonnet round; R2 took the
coordinator-directed refusal route (single-bus arrangement validated at setup
and frozen). A fresh Claude `assetops-reviewer` verification pass accepted R1-R3
with two low findings, F1 (false "none needed" bus-attachment provenance row)
and F2 (a run-owned test that tested nothing); both were fixed at the owner's
request and accepted on a Sonnet verification pass. Reviews:
`.agent/T024-codex-review.md`, `.agent/T024-claude-verification-round2.md`,
`.agent/T024-claude-verification-round3.md`. Carried: one
array/inverter/battery/PCS, once-per-step controller decisions, baseline-only
priority lists, undirected connections, validity enforced for model needs and
controls only, electrical observations not yet published (T026). The frontend
suite and build after the fix rounds rest on the build's green run; no frontend
code changed after it.

**Owner review, 2026-09-29.** Recorded by the coordinator relaying the owner,
who stated in session: "hands-on verification was done and came out
successful!" The check covered the three shipped Kobo scenarios on
2026-09-30 06:00-18:00 Addis, the overcast reserve override, the proposed demo
values and the battery-first reading, per the packet's user-review focus.
