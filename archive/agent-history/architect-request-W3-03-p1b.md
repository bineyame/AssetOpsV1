# Architect request: W3-03 P-1b-1..6, required variants with no real producer (r1b3)

Read:
- `.agent/W3-03-build-spec.md`, through r1b2;
- `.agent/W3-03-pending-rulings.md`, P-1b-1 to P-1b-6.

Code: the head of `task/W3-03-portfolio-composition`, including `0f29d4cb` and `271577c6`.

The builder found no real producer for these required variants:
- (a) late cold;
- (d) overlap;
- the non-stale mini-grid marker;
- persisted EV pending;
- the R4 false guard together with a pending line;
- a persisted `origin_revision_selected=true`.

For each, give exactly one of:
- an existing producer or fixture path, with the exact calls;
- a test-only seeding path, with exact rows, through which store API, and why it stays honest;
- a ruling that the variant is covered by a pure or fake-snapshot test, plus that test's name, and why that is sufficient.

Also confirm that applying R1/R2 (in Lane A's cursor area) inside Lane B's commit `271577c6` is acceptable, since it was sequential within one builder.

Append the result as "Run-1b variant rulings (r1b3)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
