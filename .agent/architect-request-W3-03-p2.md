# Architect request: W3-03 P-2-1, the run-2 readings, and the run-3 readiness (r2)

Read:
- `.agent/W3-03-build-spec.md`, through r1b4;
- `.agent/W3-03-pending-rulings.md`, P-2-1;
- the run-2 readings and measurements in `git show 04474b3c:.agent/W3-03-phase-handoff.md`;
- the missing-claim guard and `mock_gaps` registry, for how other slices registered gaps;
- the v69 `portfolio` mock.

Code: head `04474b3c` on `task/W3-03-portfolio-composition`.

1. **P-2-1.** The ruled text "Review opportunity Finding · Not available yet" and "Inspect physical headroom · Not available yet" fails 2 check-all guards, unless it is registered as a `mock_gaps` gap and rendered through `<MissingClaim>`.
   - Give the exact `mock_gaps` entries (IDs, fields) and the `<MissingClaim>` usage.
   - Or give a replacement that passes the guard.

   The guard must not be weakened.
2. **Readings.** Confirm or replace each of the 11 run-2 readings.
3. **Run-3 readiness.** Run 3 does the pending, empty and refusal captures, the registry panel rows, the review packet and the final review. Dry-read it now for every capture state, its fixture path, the registry rows and the packet contents. Give literals, so run 3 has no open item.

Append the result as "Run-2 rulings (r2)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
