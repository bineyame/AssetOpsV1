# Review packet CH-5c: batched reads, stored route responses, Portfolio trim (OWN-CH5c)

Branch `task/CH-5c-perf` (worktree `AssetOpsV1-ch5c`), base plan2 main `fd03ae6b0`. Spec: build sheet
`AssetOpsV1-plan2\.agent\build-sheet-CH-5c.md` §0-§8.4 (CH5c-R3, R4, R5). Size 5.75 units. USER_REVIEW_REQUIRED:
no task file; per the W1 walkthrough rule the owner sees it in the combined walkthrough. Merge is held for review.

## OPEN ITEM (owner speed goal): the tick's own pre-build is never served in a real demo run

- **What.** `scheduling.run tick` runs the `prebuild` stage (`chain/prebuild.py`) in the tick process. Stored rows
  are keyed by `code_version`, which hashes the cursor keys (Q5). `tools/demo_combined.py` runs the tick with
  `self.env()` (keys popped, `demo_combined.py:275`), while `serve` starts `host/lab_app` with
  `self.env(keys=True)` (`:565`). `tools/chain_clone.py settle_env` pops them the same way (`:125`). Measured:
  `code_version()` is `f220327ded2814bc` in the tick env and `08ce76508669b847` in the serve env (keys from
  `work/keys.json`), so they are **not equal**.
- **Effect in a real demo run (tick plus `lab_app` serve).** Every row the tick pre-builds is a miss for the
  server, so the tick's pre-build is wasted work (37-93 s per data-bearing tick, below). The stored routes are
  still hit, but only through the server's own store-on-miss path. After any watermark move, the first request
  to each route is an uncached compute: Portfolio about 5.0 s cold / 4.2 s warm, summary about 7.6 s / 4.9 s
  (below). The second and later requests at that watermark hit (about 20-60 ms). `demo_combined.prewarm` warms only
  the week Portfolio, once, after the first tick. **So the owner's goal, "fast first request after a tick", is not
  met in a real run.** It is met only when the pre-build runs in the serve env, as `chain_response_probe.py
  prebuild` does. Every L3 number below was measured that way.
- **Second divergence.** `prebuild.run` composes through `assetops_backend.main.create_app()`, while the server
  is `host/lab_app.build_app` (resolved flags, execution, gateway). `code_version` does not hash the factory, so
  a body difference would surface as a stored-vs-served mismatch, not a miss. `fresh` (which composes through
  `lab_app`) showed 23/23 equal on this data, so there is no divergence today, but it is not pinned by a test.
- **Prune interplay.** `_PRUNE` keeps the latest 3 per (route, request_key) **across code versions**
  (`response_store.py:53`). Tick rows under the wrong version can therefore evict the server's own rows after 3
  data-bearing ticks with no visits in between.
- **Smallest fix (proposed; not built: outside the brief).** In `tools/demo_combined.py`, run the `TICK` child
  with the serve env (`self.env(keys=True)`; `py()` gains a `keys` flag). The tick's `code_version` then equals
  the server's, and its pre-build rows are served. Optional hardening, in the same small change:
  - make `prebuild.run` build its client through `lab_app.build_app`, so the factories cannot diverge;
  - add the tick's `code_version` to `report.prebuild` (today `code` there is the stage outcome, `OK`), so a demo
    log shows any mismatch.

  `chain_clone.settle_env` stays keyless on purpose (clone settles are not served). Architect call.

## Outcome delivered
- u1: batched dispatch-day prefetch (R1), R3 key normalisation, R2/R3 parity tests.
- u2/u4: migration `0047_chain_response`:
  - `chain_response`, plus the `chain_input_change` W2 statement triggers on all 83 inputs;
  - `chain/watermark.py` (count terms, `code_version` hashing the alembic head, composer env and file list);
  - `chain/response_store.py`, the R5-1 before/after rule (a)-(e);
  - route wiring for the boards, the summary, the Portfolio with scope-ids, and the Findings index;
  - the `prebuild` tick stage (Q8);
  - the W6 listener guard `tools/chain_watermark_guard.py`.
- u3: the Portfolio carries `selected_revision_count` and scalar provenance. `GET /estate/portfolio/scope-ids` is
  loaded when the ids disclosure opens, with loading and error states.
- Probes: `tools/chain_response_probe.py` (`prebuild`, `fresh`, `watermarks`, `wmtime`) and
  `tools/chain_perf_probe.py --store on|off`.

## Files materially changed
`git diff --stat fd03ae6b0..HEAD`: 35 files, +2241/-87. These are:
- `backend/assetops_backend/{chain/{response_store,watermark,prebuild,prebuilt}.py, read_scope.py,
  estate_portfolio_api.py, outcome_api.py, estate_api.py, main.py, estate/portfolio.py,
  analytics/adapters/postgres_assessment_store.py, scheduling/{tick,stages,run}.py}`;
- `backend/migrations/versions/0047_chain_response.py`;
- `config/chain/{prebuilt-routes-v1,watermark-inputs-v1}.json`;
- `frontend/src/estate/{EstatePortfolio.tsx, estateClient.ts}` and `frontend/src/ui/Disclosure.tsx`;
- `tools/{chain_watermark_guard,chain_response_probe,chain_perf_probe}.py`;
- 5 new or changed backend tests, plus `test_w303_*`.

## Acceptance (sheet §4, §8.3, R5)
| Rule | Status | Evidence |
|---|---|---|
| A/B byte-equal except the trim fields | **Pass** | `bA` (main `c08f2e287`, polish clone) vs `bC` (branch, clone at 0047, store off): 85 requests, all 200. 31 files differ, and only in Q4 wall-clock fields (`known_at`, `window.known_at`, `selection_token`) and the u3 trim fields: `portfolio.scope_disclosure.sites[].selected_revision_ids` → `selected_revision_count`, and `source_provenance.{evidence_ids,source_ids,reasons}` → scalars. |
| §8.3 scope-ids equal main ids | **Pass** | week/S/month: 3 Sites each; 2092/479/4466 ids; EQUAL to `bA`'s `selected_revision_ids`. |
| Stored equals fresh after settle | **Pass** | `fresh` 23/23 (masked: Q4 fields only). |
| Stored equals fresh after `late_fill(KOBO-001, D7)` + consume; Kobo moves, Cold does not | **Substitute, see Known Deviations** | A real Kobo-scoped write (`UPDATE site ... KOBO-001`): 18/23 watermarks moved (8 Kobo boards, Portfolio, scope-ids, summary ×3 windows, Findings), 5 did not (3 Cold, 2 EV boards). Re-warm, then `fresh` 23/23. |
| R2/R3 parity, R7 flip cases, three new flips, W5 reset guard | Pass (handoffs 2-4) | `test_ch5c_batch_postgres`, `test_ch5c_watermark_postgres` (14 with W6), `test_ch5c_response_store_postgres` 6 (R5-1(e) race non-vacuous). |
| W6 guard green and non-vacuous | **Pass** | CLI on the clone: 23 requests, 81 tables read, unresolved [], untracked [], `event_consumption_read` True. Non-vacuity in `test_ch5c_w6_guard_postgres` (planted table, dropped trigger). |
| COH 0 new | **Pass** | `chain_coherence.py check`: the NEW set on `bC` is identical to the NEW set on `bA` (main), 11 lines each, uuids normalised. CH-5c adds none. |
| Idle stability (R5-2) | **Pass** | `watermarks --out wm0`; two consecutive settles (tick 57 s, 61 s); `--compare`: 23 requests, **moved {}**; `chain_input_change` 0 rows. Non-empty proof: the Kobo write above moved 18. |
| Portfolio week ≤ 100 KB | **Pass** | 52,072 B. |
| Watermark statement ≤ 50 ms | **Pass** | `wmtime` medians 2.1-2.4 ms (empty log); 2.9-3.3 ms, max 6.5 ms after change rows. |
| Q6 / R4 driver | **Dropped (no gain)** | See timings. |
| EX-3 budgets with uncached named | **Pass (stored)** | Table below. |

## Timings (clone `assetops_chainclone_ch5c_test`, polish data, 5 runs; cold = fresh process)
| Route | stored cold med | stored warm med / max | uncached cold med | uncached warm med | budget |
|---|---|---|---|---|---|
| kobo_board_31oct | 711 | 28 / 30 | 4437 | 2936 | 1000 / 300 / 60 KB (18,042 B) |
| cold_board_failure_night* | 854 | 29 / 44 | 1907 | 807 | 1000 / 300 / 60 KB (20,005 B) |
| ev_board_27oct | 735 | 43 / 51 | 2073 | 921 | 1000 / 300 / 60 KB (14,710 B) |
| summary_week | 718 | 58 / 66 | 7571 | 4863 | (none in EX-3) 13,964 B |
| portfolio_week | 511 | 25 / 33 | 5040 | 4156 | 1000 / 300 / 100 KB (52,072 B) |
| findings_week | 715 | 22 / 22 | 2268 | 1273 | (none) 24,712 B |

\* Not in the pre-built list. Its first cold child was a miss that stored (max 2384 ms); the other 4 hit.
- **Settle (trigger cost):** 0044 72 s (tick 68 s) → 0047 64 s (tick 60 s); idle settles 60 s and 65 s. Every
  settle on this clone was idle: 0 change rows written, so the trigger write cost on a data-bearing tick is not
  measured here.
- **Pre-build:** 44.0 s (20 stored, 3 hit), 18% of the 240 s tick limit.
- **Re-warm after the Kobo write:** 93.3 s (15 stored, 8 hit; 39%), then a second sample of 37.7 s (16%). The
  first sample may have overlapped other machine load (not confirmed).
- **R4 warm medians (ms), default → `prepare_threshold=0` (12 engines injected):**

  | Route | default | `prepare_threshold=0` |
  |---|---|---|
  | kobo | 1920 | 2593 |
  | cold | 603 | 675 |
  | ev | 782 | 697 |
  | summary | 3769 | 3776 |
  | Portfolio | 3368 | 3614 |
  | Findings | 1170 | 1216 |

  That is not a ≥5% gain, so R4 is dropped. No R4 code is on the branch.
- `alembic upgrade` 0044→0047 on the clone: 2 s.

## Facts the sheet asks for
- **Tenant-wide change rows:**
  - `tenant` (its own id; NULL Site and NULL tenant), the only one of the 83 inputs without `site_id`;
  - TRUNCATE on any input (NULL tenant, NULL Site; harness-only);
  - `event_consumption` NULL only for outbox rows without a Site (R5-2, via `_PARENT`);
  - `site` is scoped by its own id.
- **Q5 env hashed in `code_version`:** `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX`, `ASSETOPS_WORK_CURSOR_KEY_HEX`,
  `ASSETOPS_ACTION_DEMO_GRANTS`, `ASSETOPS_DEMO_FIXTURE_MANIFEST` and `ASSETOPS_FINDING_CASES_MANIFEST` (manifests
  are hashed by content too), plus the alembic head and the file list. Not hashed: `DATABASE_URL`, and
  `ASSETOPS_SERVER_TIMING` (a header only). `ASSETOPS_RESPONSE_STORE=off` disables the store; tests default to off
  (`backend/tests/conftest.py`), and the store tests build it explicitly.
- **Owned `link_ref` test fix (latent CH-5a2a regression on main).** `test_w303_portfolio_scope_snapshot_postgres`
  fails 3 tests on plan2 main `fd03ae6b0` (expected `evidence_prompt` dicts lack the `link_ref` that CH-5a2a
  `1c3e3a075` added). `2cfcb90c5` and `7549dcc4a` add literal refs, plus kind/view pins; no assertion is weakened.
  On the branch, all pass.

## Checks run (localised only, per the owner; no full suite, no demo prepare, no `test_demo_combined_postgres`)
- `test_s4_schedule_tick_postgres`: **7 passed**, 266 s (re-run after the tick ctor change).
- Earlier, handoff 4: store 6; w303 API/cov 18+1 skipped; w301 11; out_b4 21; tick timing/drain/mini 44; watermark,
  W6 and qw1 22; w303 snapshot 3 fixed.
- Guards: `tools/check-all.ps1 -Python <plan2 python>` (987 s): **12 of 14 pass; 2 FAIL.**
  - **Architecture seams** (`configuration-persistence.ps1`) fails on 4 lines:
    - storage technology above the adapter layer: `chain/prebuilt.py:7` (`pathlib.Path`),
      `chain/response_store.py:39` (sqlalchemy), `chain/watermark.py:23` (`Path`) and `:27` (sqlalchemy);
    - a database driver imported outside the writer list (`configuration-persistence.ps1:1021`), for
      `response_store.py` and `watermark.py`.
  - **Estate guard self-tests** fail 3 of 15 (`test_pg_reader_import_allowed`,
    `test_trial_comparison_writer_registered`, `test_event_page_writes_accept_multi_row_values_only`). They assert
    a clean architecture run on this tree, so they are expected to clear with the fix.
  - **NOT FIXED in this round** (context limit). The fix moves the SQL and file IO into `chain/adapters/` and
    adds the new adapter files to the guard's writer list, following the `postgres_event_store.py` pattern
    (`:901`). It does not loosen the guard. See the handoff.
  - Passing: navigation, agent workflow, dependency registry, delivery fixtures, mock-gap, missing-claim (×2),
    evidence width, mock deviation labels, screen ledger, chain coherence fixtures 103, event register 12.

## Known deviations
- **W1:** the uniform W2 triggers also sit on the DB append-only tables (R5-2 accepted: one mechanism). W1
  count-only terms are not used separately.
- **`late_fill(KOBO-001, D7)` not run at L3.**
  - `late_fill` refuses the chain clone by design (`require_mechanism_db`: `MECHANISM_DB_ONLY`), and the polish
    data has no declared D7 gap.
  - The L2m path needs a mechanism template for this checkout. The 0044 template `tpl_b2120e5d` is
    `TEMPLATE_STALE` (b2120e5d ≠ 84b3b775, because this branch changes input writers).
  - Rebuilding it is lane 2's heavy build, which could publish or prune lane 2's templates, so it was not done.
  - Substitute: the real Kobo `site` write above (watermark scope, re-warm, stored equals fresh).
  - L2m under `late_fill` remains open for a mechanism-template rebuild on this branch.
- R4 dropped (Q6).
- **Architecture guard red** (see Checks run). The branch is not review-ready until it is green.

## Residual risk
- The open item above.
- The guard's `targets` is regex-based; SQL functions that read tables internally are not seen.
- The `chain_input_change` count grows without pruning (W5). `wmtime` was measured only on a near-empty log.
- `ScheduleTick` callers other than the CLI get no pre-build (default off).

## Review focus
The open item (code_version env). The R5-1 before/after rule in `response_store.serve`. The W6 completeness
(`pg_trigger`). That the u3 provenance scalars (`source_provenance` ids → scalars) consume nothing rendered.
