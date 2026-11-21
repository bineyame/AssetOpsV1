# WK reviewer guide

For a fresh Claude reviewer (rev 2, 2026-11-21: handshake round 1 answered, D-WK.10 to D-WK.14). Read the spec §1 to §4 and `rulings.md`. Cite the builder's gate run at the same commit,
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
6. **Walk URL (D-WK.11).** `walk_url` is the only place building the walk URL; `walk_name_ok` refuses the 13 Nov name,
   every `assetops_op*` case and every `assetops_world*` rung (T1); no `World.census`, `World.exists` or `check_name`
   on the walk name (T12).
7. **Clean after the serve (D-WK.13).** Smoke S4 re-runs the census judge (T5).
8. **C4 (D-WK.10).** W5 calls `world.c4_oracle` unchanged; the diff edits nothing in `tools/world.py`.
9. **One figure (D-WK.12).** After the coordinator's smoke, read the PNGs of `/portfolio/month?month=2026-10` and
   `/sites/KOBO-001`: no quantity twice except plan against actual, Kisiwa's budget notice, and statement against
   records while unmatched; Kobo's stop-70 litres and value "Not available yet". A breach is a product finding.
10. **No served English (R5).** `git grep -n source_ref` in the diff and every `*_api.py`: no served read returns it.
11. **Serve shape.** The API and web argv and cwd match spec §3.5, and match `demo_combined.py serve` in mechanism (uvicorn
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
| PL9 | `walk_name_ok` checks only the prefix `assetops_polish_walk` | T1 (`assetops_polish_walk1123`, the 13 Nov name) |
| PL10 | W3 uses `World.census` on the walk name | T12 |
| PL11 | Smoke without S4 | T5 (the after-serve row) |
| PL12 | Smoke's `node` inherits the parent env | T8 |
| PL13 | `serve --tree` accepts `/opt/assetecon/AssetOpsV1-walk` | T8 |

## Not in scope

The world build and check (DS4), DDR, any product change, the coordinator's run.
