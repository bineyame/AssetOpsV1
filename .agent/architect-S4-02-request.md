# Architect request: S4-02b fuel-cost-1 bound (2026-10-13)

Role: Architect (Codex). Branch `plan/S4-02-refine` (from main `2c87037`). Write only `.agent/architect-S4-02-answers.md`. Do not edit packets or the registry (a parallel fix round is editing the packets), and do not commit.

Context, already verified (do not re-derive):
- `D-2026-10-13-s4-bounded-financial-basis` (your A-S4-financial decision) governs.
- The Codex Planner split S4-02 into `tasks/S4-02a-site-assumptions.md` and `tasks/S4-02b-fuel-consequence.md`.
- A fresh Claude plan review, `.agent/S4-02-plan-review.md`, gave ACCEPT with carries.
- Two items need you, batched into this one call.

1. **Q1** in `.agent/planner-S4-02-questions-2026-10-13.md`: ratify `sfc_upper_multiplier = 1.10` as a versioned, conditional `fuel-cost-1` model parameter (option A), require a calibrated source (B), or use a conditional point rate (C). State the provenance its version must record. The plan review notes that option C collides with the SCENARIO basis (decision review L6).
2. **C4** in `.agent/S4-02-plan-review.md` (lines 74-84): the proposed `quantity_high = Σ(P_i,max × T_i,high × SFC × 1.10)` is not a bound.
   - (a) dispatch-3.1 Candidate segments have only `[start,end)`; `T_i,high` does not exist, and interval `upper_minutes` includes unassessed edges (`backend/assetops_backend/analytics/dispatch_v3.py:105-125, 443-462`).
   - (b) One accepted power mean can straddle segment edges (segment cuts come from state reports, power-interval ends and control changes, :340-347, :382-383), so `max mean × segment duration` can under-bound energy.

   Choose between:
   - **(i) fail-closed containment.** `T_i` = stored CANDIDATE `[start,end)` with `observed: true`. A segment is quantifiable only if every covering good power interval lies wholly inside contiguous Candidate time; otherwise the whole consequence is `QUANTITY_UNAVAILABLE`.
   - **(ii) Σ over distinct covering intervals of `mean_j × |interval_j|`.** Each interval is counted once. This is valid because power ≥ 0, but it includes non-Candidate time inside straddling intervals.
   - **(iii) Another rule you specify.**

   Say which unavailable fixtures S4-02b must add, including a straddling interval.

For each item, give the ruling, the exact formula and wording the S4-02b packet must carry, and whether the owner should weigh in. If the ruling changes the decision, draft a short `.ai/DECISIONS.md` addendum inside the answers file; the coordinator records it.
