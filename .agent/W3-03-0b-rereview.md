# W3-03 0b re-review (e21a9355): ACCEPT
- H1 fixed: pin_snapshots unwraps `_real`, so a re-pin subclasses the original class. New test_repin_moves_the_snapshot_clock asserts `Snap(...).read_at == second != first`. Old code nests Pinned2(Pinned1); Pinned1.__init__ passes first() to the real class, so read_at == first and the assertion fails. Non-vacuous. Root loop also asserts known_at == iso(frozen).
- M1 (single cold line plus 3-category set), M2 (cold_consequence_revision row and stored finding head), L1 (action count == 0), L2 (docstring/comment), L3 (builder docstring) fixed.
- Not run (reasoning/git only): the Postgres test itself; the literal kind "PRODUCT_EXPOSURE" in the M2 check is unverified.
