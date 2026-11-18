# PERF-02 review packet: build once, copy per test (A) and slice test selection (C)

Branch `task/PERF-02-build-once-copy`, built from PERF-01 (d4fe44a5) and merged with main 05f80711. Builder: the
Architect (Claude), working under the owner's approval in `.agent/owner-perf-approval-2026-10-29.md` ("approve" A, B
and C). No product code or assertion changed. B (PERF-03) has not been started.

## What changed

- **T1/T2 `backend/tests/setup_cache.py`.** Wraps the cold and EV chain builder steps and the W4 mini-grid
  set-up/ingest/reconcile after collection. The first build of a step with given inputs runs live and is saved. Every
  later test with the same inputs gets its own copy:
  - the database, as `CREATE DATABASE ... TEMPLATE assetops_sc_<code><mode>_<key>_test`;
  - the files, with the old tmp path rewritten;
  - the objects, unpickled with new engines;
  - the gateway and central app, started lazily on first use;
  - the UUID counter.
  Saved set-ups are kept between runs by code fingerprint, in a named volume plus databases on `postgres-test`.
  `tools/sweep-setup-cache.py` keeps the newest three fingerprints. The cache refuses a step, which then runs live,
  when:
  - a non-UUID monkeypatch is active;
  - a repository function has been rebound by direct assignment;
  - the test wrote to the database since its previous op (review M1);
  - another session holds the database;
  - the state does not pickle.
  `-Cache on|off|verify` selects the mode, and the mode is part of the saved database names (review M2).
  `CaseRunner` is not cached: it shares live store state, and a trial failed its fences.
- **T3.** The collected node IDs come from the run itself (`collected.txt`). The separate collect-only pass, about
  80 s, is gone.
- **Runner.** The runner copies what the suite reads into the container's own filesystem, in about 5 s. Reading
  through the bind mount had failed with `Errno 12 Cannot allocate memory`. Review H1 added `frontend/docs` to the
  copy.
- **Memory guard.** It now counts 700 MB of Postgres growth when the cache is on, and uses 340 MB per worker
  (measured).
- **C `tools/select-tests.py`.** Static import-graph selection for slice checks. The full suite is selected for
  migrations, the harness, data, the runner, `tools/` and non-code frontend files (review M3/M3b).
  `tools/validate-test-selection.py` checks the selection against the last 10 merged code slices
  (`.agent/PERF-02-evidence/selection-validation.md`):
  - every changed test and every recorded failing test was selected;
  - 4 of the 10 slices selected the full suite, 2 selected none, and 4 selected 159-168 of 250 files.
- **Docs.** `backend/TESTING.md`: build once / copy per test, slice selection, merge policy. `.ai/ROLE_CONFIG.md`:
  slice-end selection; merges run the full fast tier with the cache.

## Results

All runs: Docker runner, test-only server, fast tier unless stated; 5 workers, chosen by the memory guard (recorded
in `run-options.txt`). Evidence is in `.agent/PERF-02-evidence/<run>/`.

| run (code) | wall | summed test s | result | cache |
| --- | ---: | ---: | --- | --- |
| PERF-01 baseline, 4 workers, all tiers | 74.2 min | 17,204 | 4133 + 2 known | - |
| PERF-01 fast tier, 5 workers | 57.2 min | 16,203 | 4130 + 2 known | - |
| **PERF-02 cold** 20261029-182418 (a138d7f4) | **36.0 min** (2158 s) | 10,458 | 4130 passed, 2 known w303 failures, 0 skipped | 485 hits, 50 misses, 285 live |
| **PERF-02 warm** 20261029-190123 (8420a9b5; same fingerprint) | **33.9 min** (2033 s) | 9,780 | the same | 535 hits, 0 misses, 285 live |
| slow tier 20261029-194414 | 3.8 min | - | 3 passed | - |
| frontend, threads | 239 s | - | 3451 passed, 3 failed (`w1f4VerificationStructure`, already failing on main) | - |

**Proof.**
- cold and warm each, with the slow tier added, against the PERF-01 baseline: identical collected IDs (4135),
  identical cases and pass list (the 2 known w303 failures), 0 skips (`proof_passes: true`, in each run's
  `report.md`).
- Two back-to-back runs (cold, then warm) gave the same pass list.
- Measured copy cost per hit: median 0.39 s, p90 1.44 s.
- Peak memory: VM used 2,473 MB, Postgres 1,250 MB, min Windows free 2,939 MB.

**Copy against fresh build (verify, 20261029-193612, 6 files covering the costliest families; 62 passed).**
- 41 comparisons ran: cold `Chain.open` x19, EV `Chain.open` x15, W4 `_setup` x7.
- Row counts were equal in every table in every comparison.
- Content differed only in tables holding values that are random in every fresh build:
  - issued gateway credentials (`gateway`, `gateway_credential`, `gateway_access_event`);
  - IDs from the unpinned `uuid4` (EV `recompute_job`, `source_clock_attestation`; every W4 table, because W4 does not
    pin IDs).
- The UUID counter was equal 41/41.
- Limit: the chain steps after `open` could not be compared. Their key includes the chain's random credential, so a
  verify run, which builds everything live, never repeats a step key. Two fresh builds also differ in those tables, so
  content equality there is not provable without pinning the credential. What proves those steps is the pass list.

**Earlier runs on superseded commits** (reported, not counted):
- cold 39.3 / 38.9 min;
- warm 34.9 min: 4 ENOMEM errors on the bind mount, which led to the in-container copy;
- warm 31.7 min, 0 misses: failed H1; it ran before M1, which now runs more steps live.

**Why warm is 33.9 min and not the estimated 15 min** (measured, warm run, summed test seconds 9,780):
- live chain and W4 steps: 285 steps, 3,230 s. Cold `start_release_upload` alone is 1,754 s, live because the test
  wrote first (M1; for example the w203 attestations) or because a monkeypatch or env var was active.
- `CaseRunner`, not cached: about 2,200 s (1,994 s at 4 workers in PERF-01).
- portfolio, estate and other roots, not cached: about 1,200 s.
- copies: 410 s.
- the remaining about 2,700 s: the tests' own work and the other database tests.
- Every test also runs about 12% slower at 5 workers (CPU-bound: 4 physical cores).

## Options for the owner

Owner's question: "does it really have to be generated for every test?" No. 121 distinct set-ups collapse into
about 15 standard sites:
- 11 replay cases (EV: complete, interrupted, fault, missing-meter, late-record, contradictory; cold: normal,
  excursion, backup-failed, missing-probe, late-reading, contradictory);
- 1 W4 mini-grid site;
- 1 Kobo S4 site, with 70 step variants (CaseRunner);
- the portfolio, with 6 variants.

The rest are steps taken on top of those sites.

All times below are at 5 workers, the guard's pick. "Measured" means the input was measured on this branch;
everything else is an estimate.

| option | what it takes | warm / cold (min) | effort | risk to test meaning | how equivalence is proven |
| --- | --- | --- | --- | --- | --- |
| today (PERF-02) | - | **33.9 / 36.0** (measured) | - | - | done above |
| O1 cache `CaseRunner` (the Kobo S4 site) | fresh store objects on restore, steps keyed as now | -6.7 (2,000 s measured) | 1.5 d | low: shared store caches are rebuilt | pass list + verify on its 295 tests |
| O2 key the 285 live steps instead of refusing | full-content digest (time columns, all rows) as the key after test writes; env values hashed into the key | -8 to -10 (3,230 s live, measured) | 1 d | low-medium: the digest must see every write | pass list + verify |
| O3 standard sites as ops: portfolio, estate | wrap `build_portfolio_fixture` and the estate builders; nested chains already cached | -4 (1,200 s) | 1 d | low | pass list + verify |
| O4 saved snapshots regenerate only on ingest, schema or scenario changes | narrower fingerprint (ingest path, migrations, scenarios, fixtures), not all product code; a nightly verify run checks staleness | cold runs become rare: about 4 of the last 10 code merges would regenerate | 0.5 d | medium: a module outside the list could change a build unnoticed; the nightly verify catches it | nightly `-Cache verify` |
| O5 smaller data windows (hours, not a day) | rewrite scenario fixtures and byte-pinned golden vectors | -2 to -4 (unmeasured) | 4-6 d | high: changes what the tests assert (daily totals, golden files) | new goldens; not equivalent by construction |
| O6 keep live end-to-end replays | already true for misses; add a nightly `-Cache verify` full run that builds every case live | +0 on merges | 0.2 d | none | the nightly run |
| O7 PERF-03 ingest batching (approved B) | product change in the ledger and mini-depth writes, gateway TLS reuse | cold -3 to -5, warm -1 to -3 | 2-3 d | medium (product path): its own review | pass list + per-family row fingerprints before and after |
| **best: O1+O2+O3+O4+O6, then O7** | as above | **about 15-16 warm, about 24 cold, about 21 with O7**; frontend +4 | about 4.5 d + O7 | low-medium | pass list on every merge + nightly verify |

Notes:
- With the best combination, warm plus the frontend (about 19-20 min) meets the under-20 target. A cold run does
  not, which is why O4 matters: it makes cold runs rare.
- O5 is not recommended: it trades test meaning for a few minutes.
- The CPU sets a hard limit (4 cores, every test 12% slower at 5 workers). More workers do not help.
