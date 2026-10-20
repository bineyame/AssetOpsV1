# Architect request: W3-01 q9 (golden manifest and verification count)

Read `.agent/W3-01-build-spec.md` (all rulings through q8) and `.agent/W3-01-pending-rulings.md` q9.

Code: branch `task/W3-01-estate-claim-action-roots` at `e39556b5`.

1. The golden manifest `w301-estate-golden`. Every replay generates new UUIDs, and each domain runs in its own DB, so an exact-ID file cannot match a later run. Rule the exact replacement: for example a structural golden with ID placeholders, re-derived from public reads at test time and compared on shape, counts, states and tokens. Give the literal file schema and the test that consumes it.
2. The "awaiting verification" count is always 0 in the real S6 chain. Either confirm that as honest, giving the copy and the test assertion, or name the fixture path that produces a non-zero count.

Append the result as "Run 9 rulings (q9)" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
