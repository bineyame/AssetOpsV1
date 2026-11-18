# CH-5c2 pre-flight (build sheet CH-5c §8.6, CH5c-R7)

Branch `task/CH-5c2-store-safety` from main `9fe13ae3f` (contains CH-5c `ac29b6f95`). Clone
`assetops_chainclone_ch5c2_test` created from polish, migrated, settled once (tick 90 s, `SKIPPED_STORE_OFF`,
Performance permitted). Survey run: all 23 pre-built requests incl. scope-ids, store off, 23/23 200, with an audit
hook, a statement listener and a profiler (scratch script, not product code).

## 1. §8.6 against the code

| §8.6 item | Code fact | Holds? |
|---|---|---|
| H1 gate reads | `main.py:396-405` `performance_gate` reads `performance_reports.latest` (`evidence/composition.py:112-116`, `var/evidence/migration-performance`) and `legacy_dispatch_claims(assessments.store, …)` (`performance_migration.py:32`); `main.py:551` `finding_index_gate = basis_aware_gate(performance_gate, …)` (so the same files back it); S2 scope via `ComparisonReportFiles` (`legacy_comparison_file.py:25`, `var/evidence/migration`) | yes |
| H2 C1 sites | `estate/coverage.py:387` (plan window, the sheet says 410) and `:411` (30-day); `chain/read.py:245` (`datetime.now`); also `estate/portfolio.py:573` (same window test) | yes, plus `portfolio.py:573` |
| M1 | `chain/response_store.py:133` re-check outside any `try` | yes |
| L1 | `response_store.py:136` tags `race`; adapter `insert` (`postgres_response_store.py:73-79`) returns no rowcount | yes |
| L2 | `postgres_estate_read.py:93`, `postgres_evidence_money_read.py:39` `SELECT now()` | yes |
| L3 | `tools/chain_watermark_guard.py:30-50` `targets` (no schema-qualified, no comma FROM) | yes |
| L4 | 0047 has AFTER TRUNCATE change triggers on inputs (`0047_chain_response.py:127`) but no refusal on `chain_input_change` | yes |
| `valid_until` | **0047 is merged; it cannot be edited in place.** New migration `0048_chain_response_expiry` (down `0047_chain_response`) adds `chain_response.valid_until` and the L4 BEFORE TRUNCATE refusal. CH-9 (`df8562b97`) already re-points to `0048_daylight_enqueue`/`0049_mini_service_v2` on 0047: whichever merges second re-points (mine to `0050` on `0049_mini_service_v2` if CH-9 lands first). | deviation from §8.6 wording, forced |
| F5 | `tools/demo_combined.py:463-470`: TICK (with in-tick prebuild, `scheduling/run.py:82` `prebuild=True`) then `performance_migration run` | yes |
| C5 | `scheduling/stages.py:444-448` already runs the pre-build every tick (unchanged W is a ~50 ms hit) | already true; only the prebuild docstring (`chain/prebuild.py:5-6`) changes |
| code_version residual | `file_code_version.py:46-51` hashes backend, migrations, `config/` only | yes |

## 2. Non-DB input survey (F1), measured on the clone

Files opened or listed while the stored routes composed:

| Input | Count | Class |
|---|---|---|
| `var/evidence/migration-performance/kobo-001/` (scandir + newest report) | 33 | **F2 declared root** (per Site) |
| `var/evidence/migration/kobo-001/` (S2 comparison) | 11 | **F2 declared root** (per Site) |
| `var/assessments/sites/KOBO-001.json` (legacy assessment history, `json_assessment_store.py:26,50`) | 33 | **F2 declared root** (per Site file) |
| legacy evidence inventory (`json_evidence_store.py:57,167,206,220`) and commit store (`json_commit_store.py:34,86`) | 0 on this data | **F2 declared** anyway (§8.6 names them; the Q14 gate path reaches them on other data); `current_store_root` is a path identity, hashed as the root path |
| `config/chain/thread-lifecycle-v1.json`; backend `.py` (traceback/linecache) | 1 each | `code_version` |
| `ASSETOPS_DEMO_FIXTURE_MANIFEST` / `ASSETOPS_FINDING_CASES_MANIFEST` files | (env) | `code_version` (`MANIFEST_ENV`) |
| interpreter / `site-packages` lazy imports (`.pyc`), `tzdata/zoneinfo/*` | ~25 | installed runtime, see Q3 |
| environment | `COMPOSER_ENV` only | `code_version` |
| process memos | `read_scope` memo is per request (`fresh`); `code_version` `lru_cache`; ZoneInfo cache | per request / code |
| network | 23 `socket.connect` to `127.0.0.1:<ephemeral>` | asyncio self-pipe socketpairs of the TestClient loop threads, not the compose thread; psycopg connects in libpq (no Python audit event). See Q3 |

No other file, directory, env or network input. Executed backend module set: 124 modules (saved list; it becomes
the C3 static-guard module set, see Q5).

## 3. Wall-clock survey (C3)

SQL clock functions actually executed in compose (statement listener): `SELECT now()` (estate, evidence-money read
instants), `SELECT clock_timestamp()` (mini_depth `read.py:347,407`, work reads `postgres_work_read.py:383`,
`postgres_global_read.py:182`, `postgres_domain_action_index.py:193`, assessment `postgres_assessment_store.py:966`),
and **one predicate**: `objectives/adapters/postgres_objective_store.py:163`
`recorded_at <= coalesce(CAST(:k AS timestamptz), now())` (live `k` NULL). Not executed but in compose modules:
`chain/adapters/postgres_thread_sources.py:189` (`now()` select-list read instant).

Python wall-clock reads in executed modules that a stored compose can reach: `chain/read.py:245`;
`actions/site_index.py:164` (`read_at = self.clock()`, output field); `actions/verification.py:149,379,547,784,903,964,982`
(`self.clock()`; 982 is a covering-ids comparison); `analytics/adapters/postgres_assessment_store.py:2200`
(`window_to > self.clock()` picks FUTURE_NOTE: a wall-clock comparison); `analytics/service.py:151`;
`sites/cutover.py:209`; `gateway_api.py:109` (health document). The rest of the 96 repo hits are writers (stores,
workers, services' write paths, `evidence_migration._now`, `performance_migration.py:75`).

Read-instant comparisons downstream (all against the bound read instant `k`/`read_at`): `estate/index.py:257-270`,
`work/site_index.py:342-356`, `work/detail.py:101-103`, `work/global_index.py:467-491`,
`work/domain_action_index.py:214-217,386-399`, `work/link_coverage.py:109`, `mini_depth/read.py:350,420-421`. These
are `known_at > read_at` refusals and `historical = known < read_at` labels, which are constant for a live request
(`known` None), so they register nothing; the real expiring comparisons are the data-time ones (plan windows,
`verified_at + 30 d`, `window_to`, objective `recorded_at`).

## 4. Questions (batched, each with the default I will build if not overruled)

- **Q1. DB read instants vs C1's "only through `read_scope.clock()`".** Many compose reads capture their instant
  from the DB (`now()`/`clock_timestamp()`, list in §3), not Python. *Default:* keep those captures (they are the R3
  snapshot instants) as the named allowlist of read-instant captures; C1 governs comparisons: every comparison of a
  clock-derived value goes through `within`/`since` with `at` = that captured instant. Python `datetime.now` in
  compose modules is replaced by `read_scope.clock()`.
- **Q2. SQL cutoffs `col <= :k` on write-time columns** (`recorded_at`, `created_at`, `selected_at`, set by the DB
  clock at write) are clock-derived comparisons in SQL, in dozens of reads. *Default:* not rewritten: for a live
  request every visible row's write time is ≤ its commit ≤ the snapshot ≤ the read instant (after L2), so the
  predicate cannot change without a write, and a write moves W. Named residual: a fixture that writes a future
  write-time. The C4 sweep includes every seeded timestamp as a candidate, so it would catch one on the seed.
- **Q3. F4 allowlist beyond §8.6's list.** *Default:* also allow the interpreter and `site-packages` trees
  (`sys.prefix`, `sys.base_prefix`: lazy `.pyc` imports, `tzdata`), since they are installed code, not data. The hook
  is scoped by the compose contextvar, so loop-thread socketpairs are outside it; `socket.connect` inside compose
  fails unconditionally (psycopg's DB connect raises no Python audit event, so "other than the DB" is vacuous).
- **Q4. Objective predicate (`postgres_objective_store.py:163`).** *Default:* the live read binds
  `read_scope.clock()` instead of `now()`, fetches the head per key in Python over revisions, and registers a future
  `recorded_at` through `within(recorded_at, <max>, at)`; historical `k` unchanged. The listener guard then passes.
- **Q5. C3 static-guard module set.** The W6 listener has no module set today. *Default:* the W6 CLI also records the
  executed backend modules; the set is committed as `config/chain/stored-composer-modules-v1.json` (so
  `code_version` hashes it); the CLI fails on an executed module missing from it; the L0 static guard reads it.
- **Q6. F2 roots for tests.** Tests monkeypatch `EVIDENCE_STORE_ROOT` (`test_out_b4_board_postgres.py:120-125`).
  *Default:* `file-inputs-v1.json` names roots symbolically (`{evidence}/migration-performance/{site_key}`,
  `{evidence}/migration/{site_key}`, `{assessments}/sites/{site_code}.json`, `{evidence}` legacy per-Site files,
  `{commits}`), resolved at read time from the adapters' root constants, so `F` follows a patched root. Estate routes
  hash every tenant Site's roots.
- **Q7. Size.** The clock part (Q1, Q4 and the C1 rewrites in §3: coverage, portfolio, chain/read, assessment-store
  FUTURE_NOTE, verification 982, objectives) is larger than the sheet's list. *Default:* build all of it; if the
  C1 rewrite sites exceed the §3 list I record the excess as a Known Deviation rather than widen silently.

## 5. Plan once answered
0048 migration; F2 port + term in W, (a)/(c); F4 hook; C1 helpers + rewrites; `valid_until` from registered
boundaries; M1, L1-L4, `code_version` host/contracts; F5 stage flag; store default on; L0/L2 tests, guards proved
non-vacuous; one clone pass (pre-build, `fresh`, idle tick, sweep); drop clone; packet.
