# WK reviewer guide

For a fresh Claude reviewer. Read the spec §1 to §4 and `rulings.md`. Cite the builder's gate run at the same commit,
and rerun only what a finding needs. Standard review (W5). The review is of the tool and its tests. The database run
(§5) is the coordinator's, after the merge. Do not create, clone, connect to or drop any database, and do not start a
serve.

## What to check

1. **Gate on the parent.** `copy` gets the L2 only through `World.current_l2()` and `World.check_state()`. It is
   refused for stale, unchecked and failed parents (T2), and it issues exactly one DDL statement (T3).
2. **Additions are data.** The two statements and the rebuild come from `walk-layer4-v1.json`, and the argv equals
   spec §3.3 (T4). The figures match DDR S5 and S8. The source text says "Emulated".
3. **Census.** Only the two declared tables may differ, and only by the declared counts (T5).
4. **Served and good.** W4 and S2 judge state, freshness, standing and the two figures (T7). W5 reuses
   `world.c4_oracle` unchanged.
5. **Isolation.** `assetops_polish_walk1113_test`, 8990 and 5490 appear only in the protected constants (T12). The
   serve env carries no key folder or switch (T8). `drop` never names the L2 (T10).
6. **Serve shape.** The API and web argv and cwd match spec §3.5, and match `demo_combined.py serve` in mechanism (uvicorn
   `lab_app:app` from `host/`; Vite dev with `ASSETOPS_API_PORT`).

## Plants (each alone, reverted; each must fail the named test)

| # | Plant | Must fail |
|---|---|---|
| PL1 | In `copy`, accept `check_state` `(None, None)` | T2 |
| PL2 | Add `ASSETOPS_PSEUDONYM_KEY_DIR` to the API env | T8 |
| PL3 | Census judge ignores tables outside the two declared | T5 |
| PL4 | Allow label `1113` | T1 |
| PL5 | `DROP DATABASE ... WITH (FORCE)` | T10 |
| PL6 | W4 accepts `fresh.current` false | T7 |
| PL7 | `check` stops at the first FAIL | T6 |
| PL8 | Drop `PROTECTED_PORTS` from the definition reader | T8 |

## Not in scope

The world build and check (DS4), DDR, any product change, the coordinator's run.
