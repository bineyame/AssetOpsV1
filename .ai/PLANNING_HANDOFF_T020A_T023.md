# Planner Handoff - Starter Path To Mini-Grid Runtime

Rewritten 2026-09-24 from v4 and the corrected roadmap. This replaces this
file's late-StateRef recommendation, old Blocks A-C mapping and permissive
backend-side-kernel alternative. The old task files are untouched and must be
recreated by the Planner before implementation.

This file owns only the starter dependency bridge; `.ai/FEATURE_MAP.md`
owns outcomes A-I and the unowned work beyond it. Retain task order under v4
sections 2.1 and 24, allowing a reviewable split around T020A. Delete this
handoff when its guidance has been implemented and the starter path closes.

## Immediate Sizing And Visible Outcomes

| Work | Outcome and required cut |
| --- | --- |
| T020A property carrier | Foundation displays typed physical properties and component control properties alongside documentary `ControlAssumption`; Draft frozen inputs resolve from the configured asset |
| T020A addressed-binding extension | Scenario/profile bindings and frozen initialization carry explicit `StateRef`; two same-type components resolve independently and ambiguous unqualified bindings block |
| T020B contract alignment | The shipped Fuel Loss Draft reaches `READY` through the product path with honest optional-input disclosures and v4 boundary semantics |
| T021 minimal causal kernel | Independently computed fuel trajectory proves removal/retiming causality and profile conformance; directly unlocks T022's visible execution |
| T021A parser narrowing | Remove `execution_requirement` from reported observations; stays after T021 and is not its prerequisite |
| T022 Lab execution/observation | Start, step and inspect a real Draft; see private tank state and generated reading with a declared reporting gap; operator history stays unchanged |
| T023 first gateway staging | Inspect persisted canonical envelopes generated from observations, with exact payload, mapping, identity and source/publication timing; no receipt time or Site-history change |

**Size the carrier first, addressed resolution second. Both belong in the
immediate work**, not a later multi-load milestone. v4 sections 4.2, 5.2, 24
and 27.2 require that distinction; a small current fixture is not grounds to
defer the address contract. Site-scoped typed Controls belong with the first
controller that consumes them, not in T020A.

The narrow fuel kernel remains a useful first causal proof. It does not deliver
roadmap A's PV/load/battery/controller world. After the starter path, assign
that A completion explicitly, then B's full boundary and C's dispatch Finding.
T023 is an early B prerequisite, not the internal demo finish line. No fixed
T024-T038 task ranges are inherited from the superseded feature map.

## Contracts The Recreated Tasks Must Carry

Use short task-local requirements plus these pointers, not a copy of v4.

- **Properties and frozen answers:** extend the existing single-rating carrier.
  Keep semantic `state_key` separate from component identity through
  `SupportedState`, `FoundationBinding`, scenario refs and
  `FrozenInitializationInput` (v4 4.2). An explicit component id selects that
  component; an unqualified component binding resolves only one candidate.
  Dynamic run-start state is scenario/initial-condition owned (v4 10).
- **Existing property transition:** preserve the canonical unimplemented
  corrections: Foundation-owned scenario parameters have no value slot
  (including capacity), the specific-consumption coefficient is L/kWh,
  dispatched output is a forcing, the bound declaration remains while its
  capacity value comes from Foundation, and the contradiction refusal loses
  its producer. Every failure to locate a Foundation value blocks.
  Reasoning: `D-2026-09-22-foundation-value-declaration`,
  `-consumption-coefficient-unit`, `-capacity-bound-source`,
  `-foundation-property-absent-blocks`. Do not mistake these for built code.
- **Template-copy consequence:** a template update leaves existing Sites
  unchanged. Demonstrate with a newly instantiated fixture; preserve the user's
  mg-001/mg-002/mg-003 data. This replaces the old instruction to recreate mg-001.
- **Readiness:** the initial fuel profile may record demand/irradiance as
  unsupported OPTIONAL inputs; the electrical profile later consumes them.
  Refuse conflicting requirements rather than choosing REQUIRED. Reporting
  support belongs to the publication profile. T020 already added its answerer
  label; do not add it again. See the T020 code-state entry and
  `D-2026-09-22-forcing-state-requirements`.
- **Timing:** v4 6 replaces "observe after the step": events at T, post-event
  stock/discrete sample at T plus interval measurement for [T-dt,T), controller
  view/intent, physical acceptance, evolution over [T,T+dt), invariant check.
  Initial interval signals are unavailable without declared historical input.
  Do not conflate controller inputs with sparse/noisy public observations.
- **Runtime:** v4 7-9 and 23 govern accepted flows, bounds, EXACT_RATIONAL,
  BLAKE2b-256 deterministic streams and distinct execution failures. Normalize
  authored floats only at the input boundary. No per-step approximation.
  Introduce stochastic mechanisms when the demonstration consumes them.
- **Placement:** built by T021. `contracts/assetops_contracts` holds the shared
  execution and schema contracts, `simulator/assetops_simulator` the kernel and
  packs, `host/execution_adapter.py` the wiring, and the composing tests live in
  `host/tests`. Two dependency rules were added with them: nothing imports host,
  and the contracts import neither side. Both new test roots run with
  `..\.venv\Scripts\python.exe -m pytest` from their own directory, and the
  three editable installs the setup needs are in `README.md`.
- **Observation:** separate transform keyed by
  `(StateRef, device_id, signal_id)`; raw observations stay private and reach
  the Lab through `LabProjection`. Replace authored device readings with
  generated ones. Retire the reconciliation panel and its reference helper
  when their last product caller goes, per
  `D-2026-09-22-reconciliation-panel-retirement`. v4 11.
- **Staging:** strict neutral envelope schema, immutable reloadable content,
  preserved source time, gateway/publication time, message/mapping identity
  and quality. No private causes/oracles or ingestion receipt time.
  The initial allowlist may be narrow; assign the PV/BMS/generator/meter/policy
  extension to B before C. Operational records are distinct from telemetry
  (v4 11-12); delivery/dip completeness belongs to E.

Keep the lexical and semantic control-vocabulary restriction (v4 5.1).
Renamed switching-position or controller-mode enums are not a workaround.

## Contract Versions And Retirements

The built `EXECUTION_CONTRACT_VERSION` is **5** after T020B. Three forecast
transitions happened and they landed as 3, 4 and 5: T020A's Foundation-value
narrowing, T020A1's addressing, and T020B's requirement-conflict refusal plus
reporting-path authority move plus the four declared kernel semantics. The old
forecast of absolute versions stays removed - read the number from
`scenarios/execution.py`, which carries a paragraph per transition, rather than
from any forecast. Follow `D-2026-09-22-contract-version-scope`.

Name version moves for Foundation-value narrowing, addressed frozen bindings,
boundary/requirement alignment and reported-observation narrowing wherever they
alter an already-valid document's outcome. A private TRAJECTORY oracle widening
alone does not move the execution contract. Envelope schema versioning is its
own boundary. Never reinterpret earlier frozen runs under a new contract.

**Reported-observation narrowing (T021A) is the one still outstanding.** Local
Drafts exist at several versions and `refuse_incompatible_execution` is an
equality test on the integer, so every Draft below the current number is refused
execution and stays readable. T021 regenerates rather than executes any Draft it
did not freeze itself, and did: every Draft in both new test roots is created in
process by the real setup service.

**T021 did not move the number and it stays 5**, which is worth recording because
the slice touched the contract module more than any since T018. The `TRAJECTORY`
oracle kind is a pure widening off every executable path, as forecast. The
contract's relocation to `assetops_contracts` moves identical objects - `is` holds
between the backend's re-export and the contract's own. The two new formula
functions are the arithmetic `window-overlap` and `window-ramp` already published,
tested against those statements' own worked examples. And the kernel's refusal to
compose two forcing values for one address is that kernel's behaviour rather than
a contract statement, so it narrows no space a conforming kernel may occupy.

The readiness disclosure's model-profile half is **retired by T021**, whose
conformance test derives the advertised supported set from executable handlers and
requires every advertised pair to have run. The publication profile's
reporting-path half stays, with the observation transform as its condition. Half a
disclosure retiring is the outcome the T020B correction round was written to make
possible; naming only one condition would have retired the whole statement here.

T020's fixture-only READY proof is **retired as the primary demonstration**: the
shipped document reaches `READY` through the form/API path against a Site
instantiated from the shipped template, and
`backend/tests/test_execution_contract_alignment.py` is where that is proved.
The fixture run record in `var/runs` was left in place as user data rather than
deleted. The readiness disclosure **stays** - retire it only when kernel
conformance actually proves the advertised supported set. Correct authored Fuel
Loss expectations against the independent kernel, never tune the kernel to the
old asserted numbers.

## Proof And Review

Pair the visible outcome with the smallest proof protecting the seam:
address resolution/ambiguity; remove/retime a cause; boundary stock versus interval
sampling; kernel-derived support; reporting gap changes readings not physics;
no Draft writes to Site history; staged artifact round-trip/privacy/idempotence.
v4 25 supplies the wider acceptance catalogue.

Run both repository checks and relevant tests. Layout-sensitive work carries
browser evidence under `.ai/WORKFLOW.md`. Use
`D-2026-09-22-milestone-speed-over-purity` for review scope; the Planner chooses
task cuts and user checkpoints around observable product/boundary changes.
