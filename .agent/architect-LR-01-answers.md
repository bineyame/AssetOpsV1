# Architect answers: LR-01 source-time cohort and money limit (2026-10-15)

Authority: `tasks/LR-01-late-reading-series-and-money-limit.md` Q1-Q4, `D-2026-10-14-s402c-late-sequence-and-s5-money`, `.agent/architect-S4-02c-answers.md`, and `.agent/S4-02c-review.md` F1.

## Q1 - clock proof and limit

**Accept.** Source-time ordering requires a durable, versioned, tenant/Site/source/epoch-scoped attestation from an identified authority, valid for every reading used, with a proven maximum UTC error no greater than 60 seconds. Widen each source or measurement interval by that error. A simulated attestation is explicitly identified and cannot validate a real source; `source_mode` alone is insufficient. Missing, expired, conflicting, or clock-step-affected proof leaves the series limited. Pin the exact attestation version in the new analytic basis; do not alter old runs. The 60-second bound is a ceiling, not a gateway capability claim.

## Q2 - overlap and epoch

**Accept.** Equal or overlapping uncertainty intervals in one channel remain `REPORTS_OVERLAP` and ambiguous. Gateway sequence resolves identity and duplicates, never an overlapping measurement or source-time order. Do not infer continuity across epochs from timestamps. Retain the current ambiguous default and explicit cohort-selection behavior; any automatic epoch continuity requires a separately reviewed public proof contract.

## Q3 - affected windows

**Accept with scope clarification.** On attestation creation, replacement, expiry, or withdrawal, find accepted readings whose clock basis could change, including readings covered by the old or new validity interval. Enqueue every UTC-day window whose six-hour read bracket intersects their source or measurement intervals. The existing job expansion supplies the neighboring continuity days; do not expand the bracket a second time. Use the same bracket for query and requeue. If either bound changes, version and revise both together. Reassess through existing scoped jobs and append-only selections; preserve old IDs and idempotent replay.

## Q4 - Finding and eligibility

**Accept.** Keep `SUPPORTED` only for proven Candidate spans. A material series refusal that truncates the episode yields a new FindingRevision with typed `GENERATOR_SERIES_AMBIGUOUS`, refused span and evidence/assessment links, and `SERIES_LIMIT` as end reason; retain `OPEN_BOUND` only if independently true. Derive the versioned three-state `money_eligibility` from the latest selected window and latest Finding on each read. `PENDING_REASSESSMENT` wins while relevant S3/S4 work or selection staleness remains; after work settles, `WITHHELD_GENERATOR_SERIES` applies to a material unresolved refusal. `ELIGIBLE` passes this gate only: an amount still requires the exact-head `CURRENT PRICED` consequence and existing source/currentness checks. Both S4 Financials and S5 consume the same state and exact lineage. Preserve the recorded 7.5625 USD revision as history without a current-amount label.

## Packet changes for the Planner

1. Make attestation-change requeue cover both old and new validity intervals, affected accepted reading/measurement intervals, and the same six-hour query bracket; name creation, replacement, expiry, and withdrawal in phase 1 proof.
2. Specify the eligibility precedence and that `ELIGIBLE` is only the series/reassessment gate, not a substitute for `CURRENT PRICED` and the existing source/currentness checks. Assert pending, settled-withheld, and eligible cases in phase 2 proof.
3. Make explicit that an epoch may use the existing explicit-selection path, while automatic continuity across epochs is outside LR-01.
