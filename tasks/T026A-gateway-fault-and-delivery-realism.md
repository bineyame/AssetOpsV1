# T026A - Gateway fault and delivery realism

Status: planned (deferred)
USER_REVIEW_REQUIRED: false

Map: B hardening; not a gate on any milestone, C through I.
Depends on: T026 evidence contract and T027 ingestion/receipt semantics.
Delivery order: unscheduled. It holds no position in the queue and is a
prerequisite of nothing. Run it before or after T036 as feedback and time
decide, pull it forward if T028 feedback asks for it, or drop whatever T026
already delivered for free.
Branch: task/T026A-gateway-fault-and-delivery-realism
Sizing: publication-path hardening over an existing contract.

## Why this exists separately

T026 originally carried this behavior in the critical path before the first
Finding. `Docs/queue-review-feedback-verbatim.md` moved it here: gateway
recovery is a useful proof of architecture, but it is not what makes a former
mini-grid operator say the Finding could help them.
See `D-2026-09-24-queue-resequenced-for-demo`.

If T026's implementer reported that part of this already exists, drop those
criteria rather than re-proving them. This task is allowed to end up small.

**It is not a prerequisite of T036.** The polished portfolio demo needs a
healthy site, dispatch loss, fuel, opportunity, battery trajectory, reliability
and verification. It does not need a gateway outage demonstration, and T036's
claim-limited Lab case is served by the gap and delay T026 already delivers.
Round two of `Docs/queue-review-feedback-verbatim.md` removed that gate: a
deferred hardening item must not quietly become a gate on the product demo.
The one case where it does precede T036 is if the client demo deliberately
includes gateway-outage recovery as a proof story, which is a demo-content
choice made at the time, not a standing dependency.

## Outcome

Interrupt the gateway during a run and inspect buffered recovery: preserved
source times, later publication times, explicit loss where the buffer ran out,
and a noisy signal whose imperfection is visible without being invented.

## Read for detail

- v4 sections 3, 6, 11-12 and 25.
- Roadmap section 7/B.
- tasks/T026-dispatch-capable-evidence.md for the contract being hardened.
- Shared checks and exclusions: tasks/README.md.

## Deliver and acceptance

1. Gateway outage buffers eligible reports without changing physics or original
   source times; recovery releases according to the declared profile.
2. Retry and duplicate publication preserve message/content identity.
   Delayed and out-of-order release preserve individual source times, and
   source ordering stays reconstructible after release.
3. Buffer exhaustion or configured loss is explicit and yields a gap. Recovery
   cannot synthesize observations that were never sampled or retained.
4. Gateway/publication timestamps reflect release behavior and stay distinct
   from source time and from ingestion received_at.
5. At least one biased or noisy numeric signal is demonstrable, separately from
   gateway faults, with its imperfection inspectable rather than silent.
6. Discrete status signals support dropout, stale and duplicate behavior
   without numeric noise being applied to the enum.
7. The evidence inspector distinguishes sensor gap, gateway delay and
   publication quality.
8. Ingestion behavior under recovery matches T027: idempotent duplicates,
   explicit identity conflicts, three distinct timestamp meanings.
9. Existing Findings, financials and verification results recomputed over the
   same accepted evidence are unchanged by the added fault machinery.

## Proof

| Fault | Expected stage |
| --- | --- |
| Gateway outage/recovery | Original source time, later publication time |
| Retry/duplicate | Same message/content identity |
| Out-of-order release | Source ordering reconstructible |
| Buffer loss | Explicit missing interval, no backfilled measurement |
| Biased numeric signal | Imperfection visible, not corrected silently |
| Discrete dropout/stale | No invented state, no numeric noise on the enum |

Prove that each fault changes reporting and publication only, with an identical
world trajectory and identical controller decisions under the same physical
inputs. Re-run one existing Finding and one verification over the recovered
evidence and show the conclusion is unchanged.
Run simulator/host, envelope, ingestion and inspector tests and shared checks.

## Scope limits

No general message bus, delivery-guarantee framework or source-health
dashboard. Full Replay stays deferred.
Do not reopen the envelope schema or the operational-record family; this
hardens delivery behavior over the contract T026 and T027 already fixed.

## Review

Independent review only. No new user checkpoint: this proves behavior the
architecture already claims rather than changing a product claim.
Review outcome: pending.
