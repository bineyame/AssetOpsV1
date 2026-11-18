# W3-02 0b re-review of fix r1 (commit d160e751, read via git objects only; nothing run)
n**Coordinator note (2026-10-21):** the stray file is already deleted in the fixer's follow-up commit `914f69e0`, so 0b is ACCEPTED.

## Verdict: REVISE (one mechanical deletion; no Architect ruling needed)

M1, M2, M3, conflict precedence and gap grouping match the rulings. `selected["transaction_time"]` is sound.

- Blocker (Medium, mechanical): `backend/tests/test_tmp_explore.py` is a scratch file added in d160e751. It star-imports the Postgres test module, which re-collects those tests, and it runs 7 slow parametrised cases that assert nothing. Delete it.
- M1: `forbid()` patches `_snapshot`, `_run` and `_connect_engine`. A new test asserts all three raise. Matches the ruling.
- M2: a non-window revision is refused 422 `REVISION_NOT_WINDOW`. The reused-interval fixture asserts the later selected run's membership and that the interval creating run is not consulted for currentness. Matches.
- M3: `historical_day = known_at < transaction_time` is the inverse of `select_dispatch_days_on`'s `live = known_at >= now()`. `now()` is constant inside one transaction, so both reads agree. Day and interval current fields are null, `historical_ceiling` and the IDs are kept, state is UNKNOWN, and `gaps` is empty. Matches.
- Conflict precedence: CONTRADICTORY, then UNKNOWN, then FULL, NONE, LIMITED. A conflict on a non-selected interval is ignored. A contradictory day publishes no ceiling. Matches.
- Gap grouping: grouped on (mini_grid, code, role). Role-less reasons create no group. IDs are unioned and sorted, and historical groups go to `historical_gaps`. Matches.
- Low (non-blocking): `historical_gaps` and `gaps` do not filter on `selected`. This is unreachable on the window path. Gate on `selected` in commit 1 if it matters.

## Fixer's 4 choices
1. Gap Site IDs from the projection's site: mechanical. The projection is one site.
2. Constant `GENERATOR_SUPPORT`: mechanical. It is the W1 capability.
3. Copy "Conflicting records (historical, as of the cutoff)" plus the raw reason: mechanical. The ruling requires "Conflicting records", the exact raw reason and an explicit historical context. The parenthetical is the fixer's wording, and "cutoff" is system vocabulary. Commit 1 may reword it in the client-facing copy pass without an Architect ruling.
4. New `reduce_day` keys `currentness`, `historical_gaps` and `historical_statements`: mechanical. The ruling mandates labelled historical disclosure kept apart from current gaps. Commit 1 maps these keys to the estate wire fields.
