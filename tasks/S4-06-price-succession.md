# S4-06 — equal-start future price succession

Status: done (merged to main 2026-10-15; review `.agent/S4-06-review.md` ACCEPT; coordinator full suite on `16fd46e3`-equivalent code `3dcfafd4`: 2137 passed, 0 failed/errors/skipped (JUnit), 544 s); in_review (built 2026-10-15 on `task/S4-06-price-succession`; packet `.agent/S4-06-review-packet.md`; activated from main under `D-2026-10-15-owner-absence-work-order`, plan review ACCEPT `.agent/small-followons-plan-review.md`)
Size: S; one build and one fresh independent review
Branch when activated: `task/S4-06-price-succession`, from merged main
USER_REVIEW_REQUIRED: false (non-UI; no owner-facing copy or visual change)
Registry: `I-price-equal-start-succession` (acceptance target)

## Outcome and authority

A server-authorized SYSTEM publication may replace the sole open-ended future Site price exactly at that assignment's `valid_from`. The previous scheduled assignment remains visible at earlier recorded cutoffs; the current validity timeline contains only the replacement from that instant. This implements `.agent/architect-S4-02-batch-answers.md` Q1 and the S4-02a assumption contract. Independent of unmerged LR-01, S5-01, S6-01 and S4-05 branches.

## Code reality and boundary

- `backend/assetops_backend/financials/assumptions.py:193-217`: `plan_assignments` currently requires `only.valid_from < valid_from` and always inserts a left remainder; equality fails. Keep `valid_from >= recorded_at`, exactly one overlap, and open-ended prior requirements.
- `backend/assetops_backend/financials/adapters/postgres_assumption_store.py:99-176`: the sole assumption writer validates SYSTEM, serializes a Site/key with an advisory transaction lock, checks idempotency before expected prior, takes DB time after the lock, closes recorded tenure, then inserts planned assignments in one transaction. Its `snapshot` at `:195-222` selects prior recorded cutoffs.
- `tools/checks/configuration-persistence.ps1:641-645,732-756`: rule 8 confines assumption inserts and the set-once `recorded_to` update to that writer. Preserve this ownership. No migration is expected; if one is needed, re-chain from main head 0013 against then-merged migrations (LR-01 adds 0014/0015 on its branch; S6-01a/S4-05a may add more).

## Build and acceptance

1. Change the planner only for equality with the sole open-ended overlapping assignment: close its recorded tenure and insert the new revision's `[valid_from, infinity)` assignment, with no zero-length left row. Later-start SUCCESSION, INITIAL and CORRECTION retain their reviewed behavior. Keep bounded or multiple overlap and `valid_from < recorded_at` as 409; authorization remains server-side SYSTEM.
2. Real-Postgres proof publishes an INITIAL future price, then a SUCCESSION at exactly its start with the current expected prior. Assert one current assignment, exact boundary continuity, no empty interval, the original scheduled price and assignment at a cutoff before publication, and the replacement at a cutoff after it. Assert revision/assignment IDs and `recorded_to`/`recorded_from` agree with those cutoffs.
3. Retry the identical request/key: return the same publication without another revision/assignment. Reuse its key with changed content, use a stale expected prior, and race two publishers using the same prior: one commits; the other gets 409 and leaves no extra row. Include >1 overlapping and bounded-prior refusal. Verify unchanged earlier-price consequence selection when its window does not cross the new start.

Focused checks: `backend/tests/test_s4_assumptions_postgres.py` and relevant consequence price-selection tests; `tools/check-all.ps1`. On the final revision run one real-Postgres full backend suite using `backend/TESTING.md` (xdist `-n 2 --dist loadfile --no-loadscope-reorder`, JUnit zero skipped/failed, keep-awake, 20-minute cap), then give the reviewer the same-revision evidence. No UI walkthrough or owner checkpoint.

## Architect questions

None required to build. Recommendation: retain the existing SUCCESSION conflict codes and expose the earlier recorded-cutoff assignment through the existing history read; Q1 already decides equality semantics.

## Coordinator note after plan review (`.agent/small-followons-plan-review.md`: ACCEPT)

Implementer carries (Low): add a second scenario with an earlier price so the earlier-price consequence check is non-vacuous; add a case where the replaced open-ended row is a tail left by a CORRECTION (cites an older revision than the series head).
