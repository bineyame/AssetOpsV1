"""3B7a: the frozen monthly structure snapshot (`specs/3B7a-structure-snapshot/spec.md`; D-3B7A.1 to D-3B7A.12).

One build computes every MINI_GRID Site's evaluated structure (actual and target sides) and the portfolio's
operator-level lines once, at one instant ("as of"), and stores them append-only. The served read returns the frozen
figures with their "as of" and a freshness answer, recomputing nothing. Triggers and the daily run are `3B7b`.
"""
