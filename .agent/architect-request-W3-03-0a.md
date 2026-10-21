# Architect request: W3-03 run-0a review items

Read `.agent/W3-03-build-spec.md` (closures 4–5) and `.agent/W3-03-0a-review.md`.

Rule each item with a literal artifact and a test:
- **L2:** an invalid portfolio `lens` returns 422, not 409. Confirm this, or give the code and body.
- **L3:** no run is assigned the `estateClient.ts` union for portfolio (S1). Assign it to a run, with the exact type.
- **L4:** `site_coverage` repeats per Site when Portfolio uses all three selectors. Give the exact merge rule, or confirm it is harmless.
- **M1:** the planned fix is a private per-Site `_windows_covered` in `select_financial_scope`'s Site coverage, never on the wire. Confirm it, or give the replacement.

Append the result as "Run-0a rulings (r0a)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
