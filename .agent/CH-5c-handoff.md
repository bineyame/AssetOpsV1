# CH-5c handoff 3: partial. u1 and u3 are built; u2 is part-built. Resume at "Next"

Builder 3 stopped at about 105k context. Branch `task/CH-5c-perf`, worktree `AssetOpsV1-ch5c`. The spec is the sheet:
§8 (CH5c-R4) plus **§8.4 (CH5c-R5, the Architect's ruling on W3 and over-invalidation)**. The scratch env is
`...\scratchpad\ch5c\env.sh`; the A bundles are `bA` and `bB`. `frontend/node_modules` is a junction to plan2's
(untracked).

## Commits (on top of handoff 2's `b38bcaf45`, `e59cdf35b`)
- `f4124039e` u3:
  - the Portfolio body carries `scope_disclosure.sites[].selected_revision_count`;
  - its `source_provenance` keeps scalar fields only (`estate/portfolio.py` `disclosure_provenance`);
  - the ids travel in a private `_scope_ids` key, split off by `split_scope_ids` in `estate_portfolio_api.py`;
  - `GET /api/estate/portfolio/scope-ids` serves `{schema_version: estate-portfolio-scope-ids-1, window, sites}`;
  - on the frontend: `estateClient.portfolioScopeIds` (optional), a `Disclosure onOpen` prop, and in
    `EstatePortfolio.tsx` `ScopeDisclosure`/`ScopeIdsList`. One read happens on the first open, keyed by request.
    The loading state is `Assessment IDs…`; the error state shows the refusal copy.
- `36d0e08de` u2:
  - **the W6 guard** `tools/chain_watermark_guard.py`:
    - `targets`, `resolve` (views through `pg_rewrite`/`pg_depend`), `triggered` (from `pg_trigger`) and `check`;
    - a CLI over `assetops_backend/chain/prebuilt.py` (`config/chain/prebuilt-routes-v1.json`: 20 requests,
      generated from the story calendar) plus each Portfolio's scope-ids;
  - **R5-2:** in `0047`, `_PARENT` Site-scopes the `event_consumption` trigger through `event_outbox`. `site` is
    scoped by its own id. `tenant` and TRUNCATE stay tenant-wide;
  - **Q5:** `watermark.code_version` hashes `alembic_head()` and `COMPOSER_ENV`;
  - **tests:**
    - `test_ch5c_watermark_postgres.py` adds the real-table INSERT/UPDATE flips, a DELETE (a Site-less `tenant`
      row, because `site` rows refuse DELETE), the event_consumption Site scope, the out-of-order UPDATE, a late
      outbox row, non-vacuity by dropping a trigger and rolling back, and code_version env sensitivity;
    - `test_ch5c_w6_guard_postgres.py` covers a planted table, a dropped trigger, an unknown relation, a view, and
      the R5-2 pin that `_UNSETTLED` reads `event_consumption`.

## Tests run (localised; `ASSETOPS_TEST_DATABASE_URL=...55432/assetops_test`)
- watermark plus W6: **14 passed**, 12 s.
- `test_w303_portfolio_api`, `test_cov_partial_portfolio`, `test_cov_partial_postgres`: **20 passed**.
- `test_w303_portfolio_scope_snapshot_postgres`: 7 passed, **3 failed, all pre-existing.** The failures are lines
  343, 635 and 700, where `link_ref` is missing from the expected dicts. CH-5a2a `1c3e3a075` added `link_ref`
  after the test was last updated (`e8f26789a`). They are not in the scope disclosure. The run takes 13 min.
- frontend `estatePortfolio.test.tsx` plus `src/ui`: **179 passed**. `tsc --noEmit` is clean
  (`frontend\node_modules\.bin\tsc.cmd`).

## Facts for the packet
- **Tenant-wide change rows:**
  - `tenant` (its own id, NULL Site);
  - TRUNCATE on any input (NULL tenant and NULL Site);
  - every input without a `site_id` column. List them with `SELECT ... information_schema.columns` over
    `INPUT_TABLES`.
- **Q5 settings:**
  - hashed: `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX`, `ASSETOPS_WORK_CURSOR_KEY_HEX`,
    `ASSETOPS_ACTION_DEMO_GRANTS`, `ASSETOPS_DEMO_FIXTURE_MANIFEST` and `ASSETOPS_FINDING_CASES_MANIFEST` (a
    manifest is hashed by its content too);
  - not hashed: `DATABASE_URL` and `ASSETOPS_SERVER_TIMING`, which is a header.
- **Replica mode:** no `session_replication_role` in `backend/assetops_backend` or `tools`. Tests use `_replica`,
  which skips the cic triggers, and that is harmless.
- **R4 (P3):** the engines use psycopg 3 (`postgresql+psycopg`). Its default `prepare_threshold` is already 5.
  The read engines are:
  - `estate/adapters/postgres_estate_read.py:82`;
  - `chain/adapters/postgres_chain_read.py:144`;
  - `analytics/adapters/postgres_assessment_store.py:264,2104,2794`.

  Measure on the clone with `connect_args={"prepare_threshold": 0}` injected, against the default. If the gain is
  under 5%, drop it and report (Q6). Not measured yet.

## Next
1. **`chain/response_store.py`**, following R5-1:
   - **(a)** One short RR transaction runs `read_watermark` first, then the admitted Site set (`site` rows of the
     tenant filtered by `access`, or the board's one Site), then `SELECT body, etag FROM chain_response WHERE
     (route, request_key, watermark, code_version)`. Close it.
   - **(b)** Compose as today; its read scope is created after (a). There is no cross-request cache.
   - **(c)** Re-read the watermark in a new short transaction. If it equals W, `INSERT ... ON CONFLICT DO NOTHING`
     on the write engine in its own transaction; log any failure and never fail the request. If it differs, serve
     without storing and log the race.
   - **The served bytes are the stored bytes.** Serialise once, as FastAPI `JSONResponse` does
     (`json.dumps(jsonable_encoder(body), ensure_ascii=False, allow_nan=False, separators=(",", ":"))`), and return
     a `Response` with `ETag` = `etag` = sha256(route, request_key, W, code_version).
   - **`request_key`:** canonical JSON of the route, the sorted admitted Site ids, and the **parsed** request
     (`estate.scope.parse_request` fields: window, `known_at`, lens and limit defaulted, cursor), so that the
     frontend's `lens`-less, `limit=N` Portfolio hits the pre-built key. For the board, normalise `date` against
     `from`/`to` as the coherence `date` equivalence does (`chain_coherence.py:405`).
   - **Watermark Sites:** estate routes use every tenant Site (the Portfolio spans all of them); the board uses its
     own Site.
2. **Wiring** inside `perf.route`:
   - Portfolio and scope-ids: `estate_portfolio_api.py`. Store the full composed body once, split per sub-route, or
     key each separately;
   - outcome summary and board: `outcome_api.py:188/209`;
   - Findings index: `estate_api.py:67`, which also needs `perf.route` (Q7).
3. **Pre-build** after the tick's Site loop (`scheduling/tick.py` ~361):
   - same code path; no lease; runs only when a watermark moved;
   - prunes to the latest 3 per (route, request_key);
   - reports its seconds against the ≤50% rule.
4. **The stored-equals-fresh tests** (Q4: replace only `known_at` and `selection_token`), plus the **R5-1(e)** L2
   test: a change-log write committed between compose reads gives a served body and nothing stored.
5. **L3 on `assetops_chainclone_ch5c_test`** (still at 0044). Check first for lane-2 heavy processes.
   1. `alembic upgrade head`, then settle. Record the settle seconds before and after, which is the trigger cost.
   2. Run the guard CLI (`--database-url $CLONE --work $S/work`), expecting ok and `event_consumption_read` true.
   3. A/B against `bA`, including the scope-ids versus the main ids (§8.3), and COH with 0 new.
   4. Run the 3-mode probe and the Portfolio size (≤100 KB, or report the floor).
   5. Time the watermark statement against the 50 ms stop.
   6. **Idle-tick stability (R5-2):** two ticks with no new data must move no pre-built watermark. If one moves,
      STOP and report the table and the columns written.
   7. The re-warm seconds after `late_fill`, and R4.
6. Run the guards (`tools/check-all` with `-Python <plan2 python>`), write `.agent/review-packet-CH-5c.md` with
   the W1 Known Deviation, the tenant-wide table list and the pre-existing scope-snapshot failures, then
   `tools/chain_clone.py drop ch5c`.

## Risks
- **The guard's `targets` is regex-based.** SQL functions that read tables internally are not seen. False
  "unresolved" names may appear on the clone; fix them with a narrow rule and never a blanket skip.
- **`recompute_job` lease and attempt updates** are UPDATE writes on an input. They are the likeliest idle-tick
  flip.
- **Bash heredocs in this tool collapse `\\`.** Write Python edit scripts with the Write tool.
