# S4-02b phase 1: questions and fail-closed choices (Implementer, 2026-10-14)

The packet and decisions did not settle the points below. For each one, the Implementer took the conservative, fail-closed option and continued. Each item says what the code now does and what would need a ruling to change it.

## Q1. Consequence window column names
The packet's "FindingRevision `window_start/end`" does not exist in migration 0009. The FindingRevision window is `episode_start`/`episode_end`.
- **Built:** the consequence window is exactly the FindingRevision episode window.
- **Enforcement:** the lineage trigger in migration 0011 enforces it.
- **CHECK:** the window CHECK is `window_start <= window_end`, not `<`. The reason: an episode can only be zero-width when the Finding has no Candidate time, and that Finding stores as `NO_CANDIDATE_TIME`. Zero-width Candidate spans contribute no time.
- **Ruling needed:** whether a zero-width window should instead refuse to store at all.

## Q2. Input membership
Each counted power mean must be in the accepted input set (`analytic_run_evidence`) of a cited INTERVAL analytic run. It is not enough for it to be in `assessment_revision.evidence_ids`. The reason: dispatch-3.1 cites power IDs at report times only when no generator-state reading exists there.
- **Rejected alternative:** requiring interval-level citation would refuse every Site that reports both state and power.

## Q3. Which SFC
`SFC_j` comes from the generator component (matched by `component_id == asset_code`) in each reading's **as-accepted** Foundation revision. It does not come from a later Foundation correction. Three conditions apply:
- that revision must be one of the cited runs' `foundation_revision_ids`;
- that revision must be valid over the whole reading interval;
- the reading's binding revision must likewise be valid over the whole interval.

More than one distinct SFC value on that component counts as a conflict.

## Q4. Non-finite decimal upper
Hours are seconds/3600, so `quantity_high` is generally not a finite decimal.
- **Stored:** the exact fraction (`quantity_high_exact`, `num/den`), plus `quantity_high` at 50 significant digits rounded toward +infinity. Rounding up is outward for an upper bound.
- **Amount:** `amount_high = quantity_high × price` is an exact Decimal product, and a CHECK enforces it.
- **Display:** rounding (low down, high up, to the currency minor unit) is left to the phase 2a read.

## Q5. Unavailable quantity ignores price
`QUANTITY_UNAVAILABLE` records `price_state = NOT_EVALUATED`, and its basis excludes the price. A price correction therefore does not append a new unavailable revision.
- **Ruling needed:** whether the owner wants such a revision for history.

## Q6. Idempotency basis versus "A, then B, then A"
The consequence basis includes every price assignment ID that overlaps the window at selection. Assignment IDs are unique per publication. Two `UNPRICED (PRICE_SPANS_WINDOW)` states over different boundaries therefore never share a basis, so an older revision cannot be replayed in place of a newer state. Exact retry still returns the same ID.
- **Remaining case:** a truly identical input state that reappears after a different one would replay the older ID. Phase 2a should treat replay of a non-head revision as `STALE/PENDING` input to recompute, not as current.

## Q7. Parameter version record
`sfc_upper_multiplier` is not an assumption row:
- assumption keys are CHECK-limited to `diesel_price_per_litre`;
- the version is an immutable code constant `fuel_cost.PARAMETER_VERSION` (value, inequality, limitation, scope, formula, SFC rule, source, author/reviewer, date);
- its sha256 is pinned in `conversions/fuel-cost-1-cases-v1.json` and asserted by test;
- every consequence row stores its version, digest and value.

Therefore no `financial_consequence_assumption_revision` link exists for the parameter. The "reviewer" field states that independent review is still pending.

## Q8. CURRENT FindingRevision
`quantify` requires lifecycle `SUPPORTED`. Whether the revision is the latest, and whether its dispatch windows are current (`FindingReadService._currentness`), is left to the phase 2a recompute and read (`STALE/PENDING`). The phase-1 store derives from whatever exact revision it is given.

## Q9. Ordinary Findings will be `QUANTITY_UNAVAILABLE`
**Corrected 2026-10-14 (review M2):** this was wrong. Of the 11 latest FindingRevisions in the S4-02a walkthrough DB, 8 are `POWER_MISSING` (the authored state-only cases), 2 are `FINDING_NOT_SUPPORTED`, and 1 - the registered gateway Finding F01-gateway `[05:15, 09:15)` - has accepted generator power but fails `POWER_COVERAGE_GAP`: its 16 GOOD means are 5-minute means published every 15 minutes, covering one third of Candidate time. Interpolation is forbidden, so none qualified. Owner ruling `.agent/owner-S4-02b-money-demo-2026-10-14.md`: phase 2a adds one labelled authored power-mean case.

The S4 Finding fixtures and walkthrough deliver generator **state** only, never `INTERVAL_MEAN` generator power. Every ordinary Finding is therefore `POWER_MISSING`; the Postgres test proves this for one. A positive amount needs accepted power means.
- **Phase 2a/2b walkthrough:** either deliver power means through the registered gateway path, or report plainly that none qualified (packet "Visible acceptance").

## Q10. Non-GOOD and negative power
A non-GOOD reading is not selected. Coverage then decides whether its time is missing. A GOOD negative mean refuses the whole quantity (`POWER_NEGATIVE`).
