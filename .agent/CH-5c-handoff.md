# CH-5c handoff 5: L3 done, packet written; resume at the architecture-guard fix

Builder 5 stopped at the context limit. Branch `task/CH-5c-perf`, worktree `AssetOpsV1-ch5c`. Spec: sheet §8, §8.4.
The scratch env is `...\scratchpad\ch5c\env.sh`. The clone `assetops_chainclone_ch5c_test` was **dropped** after
L3. The packet `.agent/review-packet-CH-5c.md` holds every L3 result and timing, and the OPEN ITEM (tick env
`code_version` mismatch with `lab_app`, proposed fix). Do not re-run L3 unless code that bodies depend on changes.

## Done this round (results in the packet)
- `test_s4_schedule_tick_postgres`: 7 passed.
- R4: no gain, dropped.
- L3 settle and upgrade:
  - settle 72 s → 64 s;
  - W6 guard CLI clean;
  - A/B: only Q4 and trim fields differ;
  - scope-ids equal main;
  - COH: NEW set identical to main.
- L3 idle and store:
  - idle ticks: 0 moved;
  - pre-build 44 s; `fresh` 23/23;
  - `wmtime` about 2-3 ms;
  - store on: every cold median ≤ 854 ms and warm max ≤ 66 ms; store off: uncached;
  - Portfolio 52,072 B.
- `late_fill` substitute: a Kobo `site` write moved 18/23 (Cold and EV did not); re-warm 93 s / 38 s; `fresh` 23/23.

## Next (in order)
1. **Fix the architecture guard (red; 2 of 14 check-all guards fail).**
   - The 4 violations:
     - `chain/response_store.py:39` and `chain/watermark.py:27` import sqlalchemy;
     - `chain/watermark.py:23` and `chain/prebuilt.py:7` import `pathlib`.
   - Rule: `tools/checks/configuration-persistence.ps1`. The storage-above-adapter rule, plus the driver writer
     list built at about `:1021` (see `$eventWriter`, `:901`).
   - Move the SQL (`_LOOKUP`/`_INSERT`/`_PRUNE`/`_SITES`, `read_watermark`, the engine) into
     `chain/adapters/postgres_response_store.py`. Move the file reads (`alembic_head`, the file-list hash, the
     manifest hashing, `prebuilt.py`'s config load) into an adapter too, for example
     `chain/adapters/code_version.py`. Leave the domain-facing functions in place, taking a port.
   - Register the new Postgres adapter in the writer list exactly as the existing chain adapters are. Do not
     loosen any rule.
   - Importers to update: `chain/prebuild.py`, `estate_api.py`, `estate_portfolio_api.py`, `main.py`,
     `outcome_api.py`, `migrations/versions/0047_chain_response.py`, `tests/test_ch5c_{response_store,
     w6_guard,watermark}_postgres.py`, and `tools/chain_{watermark_guard,response_probe}.py`.
   - Then re-run `tools/check-architecture.ps1` (pass `ASSETOPS_GUARD_PYTHON` = plan2 python, or check-all
     `-Python`; without it Rule 8 reports false "vacuous" lines), the 3 `test_ch5c_*_postgres` files,
     `test_qw1_perf`, and `test_out_b4_*`. The estate guard self-tests (3 fail) should clear with it; run
     `tools/checks/test_estate_guard.py` (about 13 min).
2. Update the packet's "Checks run" guard line to green. The commit list goes in the packet header.
3. The OPEN ITEM's fix (`demo_combined` tick env) is for the Architect/owner to rule, not to build.
