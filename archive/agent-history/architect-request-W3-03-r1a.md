# Architect request: W3-03 run-1a question and readings (r1a), plus a 1b/2 dry-read

Read:
- `.agent/W3-03-build-spec.md`, closures 4–5, r0a and r0b;
- `.agent/W3-03-pending-rulings.md`, Q-1a-1;
- the eleven run-1a readings in `git show 450f5f9f:.agent/W3-03-phase-handoff.md`.

Code: `450f5f9f` on `task/W3-03-portfolio-composition`, in `estate/portfolio.py`, `estate_portfolio_api.py` and `estate/composition.py`.

1. **Q-1a-1.** The S9 tie-break needs the selected Action event's `recorded_at`, but Lane A's `coverage.py` rows don't carry it. The interim fallback is `action_id` ascending. Give the exact fix: the field, the owning lane and the run, or confirm the fallback with a test.
2. Confirm or replace each of the eleven readings with a literal artifact and a test.
3. Measured for r0a L4: one snapshot, with 12 `site_coverage` calls plus 1 Action call. Confirm this is acceptable, or give the exact change.
4. Dry-read runs 1b and 2 (the B4 rows and the page) against the code at `450f5f9f`, specifically for:
   - copy strings;
   - mock slots without a source;
   - missing IDs or fields;
   - link targets;
   - the `estateClient.ts` type (L3).

   Give literals for anything open.

Append the result as "Run-1a rulings (r1a)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
