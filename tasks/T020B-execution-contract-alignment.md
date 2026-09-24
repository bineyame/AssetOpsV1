# T020B - Reachable Fuel Loss readiness and boundary contract

Status: planned
USER_REVIEW_REQUIRED: true

Map: A starter.
Depends on: T020A and T020A1.
Next: T021, then T021A.
Branch: task/T020B-execution-contract-alignment
Sizing: boundary-changing; declarative contract and reachable setup.

## Outcome

Create a READY Fuel Loss Draft through the normal Lab setup form using a new
compatible Site. Read its frozen inputs, unsupported optional disclosures and
contract version in Runs detail without writing a fixture record by hand.

The kernel needs one coherent executable contract before implementation.
This task settles declared semantics; T021 proves the runtime implements them.

## Read for detail

- v4 sections 2, 6, 8, 10 and 24.
- Starter handoff: Readiness, Timing and Contract Versions.
- DECISIONS: D-2026-09-22-forcing-state-requirements,
  D-2026-09-22-kernel-step-semantics,
  D-2026-09-22-contract-version-scope.
- CODE_STATE T020: reachable READY and readiness disclosure.
- Shared checks and exclusions: tasks/README.md.

## Deliver and acceptance

1. Fuel-profile demand and irradiance declarations are consistently OPTIONAL.
   They remain recorded as unsupported optional inputs in the frozen run and UI.
   Their electrical consumption is assigned to T024, not implied by READY.
2. The fuel profile supports dispatched generator power as a forcing input.
   It resolves the Foundation properties and dynamic initialization from the
   addressed contracts produced by T020A/T020A1.
3. Reporting availability/cadence support resolves from the publication profile.
   Preserve T020's already-built PUBLICATION_PROFILE answerer and labels.
4. Conflicting execution requirements for the same addressed state/role refuse
   the authored document or setup with a clear reason.
   Resolution cannot silently select REQUIRED.
5. Window ramps interpolate linearly between declared endpoints.
   A forcing outside its declared window is unavailable, not held or extrapolated.
   Boundary membership is explicit for the half-open run/forcing intervals.
6. Publish the v4 boundary cycle as the execution contract:
   apply events at T; sample post-event stock/discrete state at T and preceding
   interval measurements; build controller view/intent; resolve physical
   acceptance; evolve [T,T+dt); check invariants.
7. Interval-rate/energy readings timestamped T describe [T-dt,T).
   At run start they are unavailable unless historical input is declared.
   State and interval signals cannot share an undocumented timing convention.
8. BOUNDED_AND_RECORDED changes continue from the bounded value with an
   inspectable record; preserve REFUSED_AT_PARSE and FAIL_RUN distinctions.
9. Keep controller-local input semantics independent from sparse/noisy public
   reporting; no observation cadence becomes controller cadence by default.
10. Contract version advances relative to the version after T020A1 for changed
    boundary/requirement outcomes. Old frozen runs retain their old identity.
11. A new compatible fixture plus shipped Fuel Loss document reaches READY by
    the normal form/API path; its stored readback matches the displayed inputs.
12. Retire fixture-only READY proof as the primary product-path demonstration.
    Keep the readiness support disclosure until T021's kernel conformance
    actually proves the advertised supported set.

## Proof

| Case | Expected result |
| --- | --- |
| Shipped scenario + compatible new fixture | READY through form/API |
| Unsupported OPTIONAL demand/irradiance | Recorded and visible, not blocking |
| Same input declared REQUIRED and OPTIONAL | Refusal with conflicting input |
| Unsupported REQUIRED input | BLOCKED with correct profile reason |
| Reporting capability absent | Publication-specific explanation |
| Old frozen Draft after version change | Old contract identity unchanged |
| Mid-window ramp declaration | Unambiguous expected interpolation |
| Initial interval signal | Unavailable absent explicit history |

Contract tests should protect the declared rules and parser/setup outcomes.
They are not a substitute for T021's independent numerical execution proof.
Keep projection helpers declarative; calculating time-dependent world values
belongs to the kernel.

Run relevant scenario/run tests, form/detail tests and shared checks.
Run layout evidence using the real product-path READY Draft; record its fixture
identity and preserve user data.

## Scope limits

No running clock, causal trajectory, observations or operator evidence yet.
Reported-observation execution_requirement narrowing remains T021A after T021.
Do not add the fifth answerer again or introduce an absolute forecast of future
contract versions.

## Review

The owner creates and opens a READY Draft and can see what the fuel profile
does not model. The Reviewer checks conflict refusal and timing declarations.
Review outcome: pending.
