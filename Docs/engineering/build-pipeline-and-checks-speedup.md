# Build pipeline and checks: what to cut, what to run in parallel, what to keep

Architect evaluation, 2026-11-18. Branch `task/build-pipeline-speedup`. Owner request (verbatim): `owner/owner-build-pipeline-speedup-request-2026-11-18.md`. It feeds the speed-up asked for in the two-week conversion plan (`Docs/go-to-market/two-week-conversion-plan.md`, branch `task/gtm-documents`).

**This is a recommendation. Nothing has been changed:** no pipeline, check, test or code. Under W1 and W3 the owner approves first. Every open question has a default in §8.

**How figures are labelled.**
- **Measured** means timed on this VPS today, 2026-11-18. The machine has 8 vCPU and 22 GB. The walkthrough server and `lab_app` were running in the background, so the load average was about 2.
- **Recorded** means the figure is taken from a log or packet, which is named.
- **Estimate** means a forecast, and its assumptions are stated.

Nothing heavy was run: no full suite, no database build, no recapture.

---

## 1. In plain words, for the owner

- **One guard step takes most of the guard time.** The guard command (`check-all`) took **9 min 50 s** when measured today. **7 min 44 s of that (79%)** is one step: the estate-guard *self-tests*. Those tests check that the database-writer guard still catches violations. They do not check your change. An Architect ruling of 4 Nov already said to run them "only when a slice edits `configuration-persistence.ps1`", but `check-all` still runs them every time.
- **The guards run one after another, although they are independent.** Run four at a time and skip the self-tests when the guard itself has not changed, and `check-all` drops from about 10 minutes to **about 40 seconds**. With the self-tests (when the guard did change) it takes about 2–2.5 minutes. That is an estimate from the per-guard timings measured today.
- **Today the guard command is queued, and the queue costs more than the guards.** Since 12 Nov the coordinator has run `check-all` centrally, one branch at a time. Parallel runs had starved the machine, at more than 20 minutes each. A typical slice runs it two or three times: on the branch, after merging `main`, and on `main`. At a 40-second `check-all`, builders can run it themselves again, and the queue disappears.
- **One check is silently not checking on this machine (a defect).** In a worktree, the "chain graph check" reads `main`'s code instead of the branch's. `check-all` joins `PYTHONPATH` with the Windows separator `;`. Today I showed that the import then resolves to `/opt/assetecon/AssetOpsV1/backend`. Fix it first. It costs nothing and it is an honesty fix.
- **Some guards protect a plan that has ended.** Several guards still check the v69 registries, the screen ledger and the S1–S7 queue table. The v69 mock-up no longer governs (owner O2), and the S1–S7 queue is built. They cost about 1 second, but they force bookkeeping edits on slices. Example: SR-12b had to "list the new readiness gap in the screen ledger". The one piece of them that still matters is the honest-gap catalogue, because the "not available yet" scan reads it. Keep that piece and retire the rest.
- **The demo database build takes about 2 hours, and half of that is waiting in line.** The build has two big Site steps and one big check: Kobo 29 min, Kisiwa 20 min, and a self-check of 25 min (recorded, walk1113 build). They all run one after another. Two Sites side by side, plus the 54 read-only self-check rows four at a time, take it to about 1 h 20 min. Copying a database already built and verified instead of rebuilding it takes about 15 minutes, when the code that produces the data has not changed. Whether a copy counts as the "clean, good DB" your walkthrough rule requires is your decision (§8, OD-4).
- **What stays untouched:**
  - fresh reviews;
  - money and honesty checks;
  - database safety;
  - your port and walkthrough rules;
  - "no full suite unless you ask" (§9).

  Reviews catch real defects on almost every slice. Examples are AP-1 REJECT, the SR-83 and WALK-perf Mediums, and about 110 fix-round commits since 8 Nov.

**Expected effect:**
- **Per slice** (estimate): about **155 → 112 minutes** from build start to merge, or −28%.
- **Per demo database rebuild:** about **2 h → 1 h 20 min**. If a verified copy can be reused, about **15 min**.

**Effort:** about 1.25 lane-days for the guard changes and about 2 lane-days for the database changes.

---

## 2. What was already done (not redone here)

| Work | Outcome | Source |
| --- | --- | --- |
| OPS-01 to OPS-04 | Per-worker template databases, `pytest -n`, DELETE cleanup, 4 workers, `synchronous_commit` off. Full suite 80 → 46–50 min | `backend/TESTING.md` "Timing" |
| PERF-01 | Test-only Postgres server (fsync off), slow tier, memory-sized workers, vitest threads. 74.2 → 57.2 min | `archive/agent-history/PERF-01-packet.md` |
| PERF-02 | Build once, copy per test (set-up cache) and `tools/select-tests.py`. 57.2 → 36.0 cold / 33.9 warm | `archive/agent-history/PERF-02-packet.md` |
| PERF-02 options O1–O4, O6 and PERF-03 (ingest batching, owner-approved "B") | **Not built.** Estimated 33.9 → about 15–16 min warm | `archive/agent-history/PERF-02-packet.md` "Options for the owner" |
| Demo-sprint test policy | No full suite until the end-game unless the owner asks. Slices use the L0–L4 ladder of localised tests | `.ai/RULES.md` §7; `archive/agent-history/architect-handoff-demo-plan-2026-11-04.md` |
| WALK-perf | Warm only on change; performance gate inside compose | merge `f37b0ad9f`; `archive/agent-history/WALK-perf-ruling-2026-11-14.md` |

The backend suite is already fast where it runs. This evaluation therefore concentrates on what runs **around every slice today**: the guards, the guard queue, focused tests, live checks and the demo database.

---

## 3. What runs around a change, from spec to merge

<!--diagram:pipeline-->

The stages below are the ones in use on the VPS since 12 Nov (`.agent/lane-rules-vps-2026-11-12.md`, `.agent/coordinator-handoff.md`).

1. **Spec and pre-flight.** The Architect specifies; the builder dry-reads the spec and batches its questions.
2. **Build.** The builder runs focused tests (L0–L2), then Postgres files when the database is free (one heavy job at a time). It runs focused vitest files, and `tsc` when types change.
3. **Fresh review**, then a fix round and a verification re-review when needed (W5).
4. **Central `check-all`**, one branch at a time. It runs again after `main` is merged in, and on `main` after the merge.
5. **Live check on the demo database.** For range or data work this is a parity or live HTTP check (owner rule D-SR.9: output for every range, on every Site type).
6. **Merge.**
7. **When the demo database must change:** fast-forward the build tree, apply migrations, prebuild and warm. A fresh prepare takes about 2 h.
8. **At milestone or final review:** recapture, the register reconcile and the full suites. The full suites run only when the owner asks.

---

## 4. Inventory: what each item protects, what it costs, what it caught

### 4.1 The guard command, `check-all` (21 guards)

Measured today with `pwsh -NoProfile -File tools/check-all.ps1 -Python .venv/bin/python`:
- **589.6 s wall**, 133% CPU;
- peak resident memory **1.24 GB**, the largest single process;
- all 21 passed.

Each guard was then timed on its own, using GNU `time` for wall time and peak RSS.

Recorded under load: 957 s "under load ~10", and "parallel runs starved the machine: >20 min each" (`.agent/lane-rules-vps-2026-11-12.md`). On the laptop it was about 7 minutes.

<!--diagram:guardtimes-->

| # | Guard | Protects | Wall (s) | Peak MB | Recent catch (evidence) | Class |
| --- | --- | --- | ---: | ---: | --- | --- |
| G1 | Estate guard self-tests (17 tests; each copies `tools/`, `backend/`, `config/` and `contracts/`, then runs the writer seam) | That the database single-writer guard still **fails** on a violation | **464.3** | about 430 per test | No catch since 1 Nov. Writer-adding slices must edit its probe anchor (`a8c948551`, `1d2b9fb33`) | **Essential, but only when the guard changes.** Run it when `configuration-persistence.ps1`, `_common.ps1`, `sql_statements.py` or `test_estate_guard.py` changes, and at milestone |
| G2 | Architecture seams (14 modules) | Protected seams: dependency direction, the simulator gate, single writer per table, shared range, the shell | 90–116 | 1,090 (dependency direction) | SR-12a: a rejections route skipped the cutover gate (`a1ec625d9`). PR-2a: an inline SVG broke shell overflow (`7ed585600`) | **Essential** |
| G2a | of which dependency direction | Import layering | 30.8 | 1,090 | (the seam as a whole) | Essential. Its slowest module; tune later |
| G2b | of which configuration persistence (rule 8, writer guard) | **Database safety**: one writer per table, insert-only provenance | 17.2 | 427 | SR-12a, UP-1 (`6fdd4d62a`) | Essential |
| G2c | of which navigation truthfulness | No link to a page that does not exist | 15.8 | 879 | (none since 1 Nov) | Essential |
| G3 | Navigation truthfulness, standalone | **The same module as G2c, run a second time** | 16.3 | 891 | No catch of its own | **Duplicate: remove** |
| G4 | Agent workflow | Start-path files exist; T-packet status words | 0.4 | 110 | (none) | **Stale.** It requires `.ai/ACTIVE_CONTEXT.md`, `PROJECT_RULES.md`, `WORKFLOW.md` and `PLANNING_GUIDANCE.md`, which declutter retires. It will block declutter step 4. Rewrite it for the new start path |
| G5 | v69 dependency registry | The v69 pilot registry, plus S1–S7 queue rows parsed from `tasks/README.md` | 0.2 | 68 | SR-12b had to "list the new readiness gap in the screen ledger" (`c133f0b6d`): bookkeeping | **Stale**, except the gap catalogue |
| G6 | Delivery checker fixtures (`delivery_next_work`) | S1–S7 next-work selection | 0.2 | 74 | (none) | **Stale.** The coordinator sequences the work now |
| G7 | Mock-gap catalogue fixtures | The honest-gap catalogue that "not available yet" copy uses | 0.2 | 59 | `f6ddce198`: a gap registered and rendered through MissingClaim | **Essential (honesty).** Keep it |
| G8 | Missing-claim scan, plus its fixtures | **Honesty**: every missing source shown as "not available yet" | 1.7 + 4.0 | 210 | `f6ddce198` | Essential. Run the fixtures only when the scanner changes |
| G9 | Evidence width fixtures | The capture tool's width check | 0.3 | 77 | (none) | Low value per slice. Run it when `tools/evidence-checks.mjs` changes |
| G10 | Mock-deviation labels and client vocabulary | **Mock fidelity and honesty**: no unlabelled departure, no system words | 0.4 | 86 | Labels added in PR-2a, SR-4c and UQ-FI-3 | Essential |
| G11 | v69 screen ledger | The v69 manifest and ledger | 0.05 | 16 | (none) | **Stale.** v69 is not authority (owner O2) |
| G12 | Chain coherence fixtures (183) | **Money and claim coherence** rules | 1.9 | 67 | CO and COH rule changes | Essential |
| G13 | Event register | Declared recompute triggers | 1.1 | 65 | (none since 1 Nov) | Essential (cheap) |
| G14 | Fuel wording | **Owner K9**: no theft or siphon wording | 4.6 | 63 | (none since 1 Nov) | **Essential (owner-ruled)** |
| G15 | Chain graph check | The declared outcome chain graph | 0.6 | 56 | (none) | Essential, **but vacuous in worktrees on Linux** (see §4.5) |
| G16, G17 | Perf budget fixtures; period read parity self-test | Range-read budget; byte parity of stored reads | 0.1 | 22 | Introduced by ANY-1 | Essential (cheap) |
| G18 | Frontend hard-wiring ratchet | No new hard-wired links or literals | 0.1 | 59 | SR-8 (`3482d604e`), SR-5 (`36aafc311`) | Essential (cheap) |
| G19, G20 | Style ratchet, plus fixtures | UI tokens, no raw hex or fonts | 0.3 | 66 | UP-1 post-merge fixes (`4bd198065`) | Essential (cheap) |

Where the 590 s goes:

| Part | Seconds | Share |
| --- | ---: | ---: |
| G1 estate self-tests | 464 | 79% |
| G2 architecture seams | about 90 | 15% |
| G3 duplicate navigation check | 16 | 3% |
| Everything else together | about 20 | 3% |

### 4.2 Tests

| Item | Protects | Time and memory | How often now | Catches | Class |
| --- | --- | --- | --- | --- | --- |
| Focused backend files (L0–L2) | The changed behaviour; money files on money changes | Seconds to minutes per file. Postgres files wait for a database slot | Every build | Most build-time defects | **Essential** |
| `tools/select-tests.py` | Picks the slice-end backend set | 6.1 s, 41 MB (measured) | Rarely used in the sprint (L0–L4 replaced it) | Measured on 5 recent merges it picked **274–510 of 510 files** (54–100%). `tools/` and data changes force everything. It also suggests a frontend run for a docs-only change | **Low value as built.** Its selection is too coarse to save time. Replace with a coverage map later (§6, L3) |
| Full backend suite | Whole-product regression | Recorded 33.9 min warm / 36.0 cold, 5 workers, laptop (PERF-02). Last full run 1 Nov: `-Tier all` 4,737 passed / 0 failed. **Never run on the VPS** | Owner rule: only on request | End-game safety net | Essential at milestone. Not per slice (owner rule kept) |
| Slow tier (incl. the `demo_combined` build test, 2.0–2.35 h) | Real-clock and build behaviour | Recorded 3.8 min, plus the build test | Milestone | (none) | Milestone only |
| Full frontend vitest (190 files) | UI regression | Recorded 218–356 s on the laptop | Milestone; focused files per slice | SR-4 broke 25 tests in files nobody ran (lane-rules lesson) | Focused per slice, with the Site-href file set. Full at milestone |
| `tsc --noEmit` | Types | **34.9 s, 1.26 GB** (measured) | Per slice that touches types | Routine | Essential, and cheap |
| `vite build` | Bundle builds | Recorded 6–17 s | Before a demo serve | Rare | Keep at serve time |
| Host tests (`field/`, `host/`, `gateway/`) | Field and gateway packages | Recorded TEL acceptance: 9–12 min each | When those packages change | TEL slices | Essential when the package changes |

### 4.3 Live checks, captures, audits and the register

| Item | Protects | Time | How often | Class |
| --- | --- | --- | --- | --- |
| Live two-range check or parity on the demo database | **Owner D-SR.9**: output for every range, on every Site type; stored = computed | Recorded 5–30 min per slice | Range and data slices | **Essential (owner-ruled)** |
| Per-slice layout captures (`tools/*-evidence.mjs`) | Mock fidelity at 390 and 1440 px | Minutes | Layout-sensitive slices | Essential for those slices. The 40 older per-slice evidence scripts are history (declutter step 5) |
| Full recapture: 1,414 pairs in 19 batches (`.agent/post-W6-final-recapture/PROGRESS.md`) | No layout regression against the frozen audit | Spread over at least 5 agent sessions. Every batch rebuilt its producer database | Final review only | Milestone only. Combine it and run it in parallel (§5, L6) |
| Register reconcile (`.agent/mock-departure-register.md`) | Every departure labelled, D3 rows closed | Hours, by agent | Final review | Milestone only. Combine it with the recapture pass |

### 4.4 Databases

| Item | Time | How often | Class |
| --- | --- | --- | --- |
| Demo/walkthrough prepare (`tools/demo_combined.py prepare`) | **Recorded 1 h 59 min** (walk1113, `/opt/assetecon/AssetOpsV1-walk/var/polish_walk1113-prepare.log`). A fresh build "about 2 h 45 min"; vps1 "about 3 h" | Each walkthrough, rehearsal or demo DB, 2–3 a fortnight | Essential (owner: a clean, good DB) |
| Add-dates / tick / prebuild / warm on the serving DB | Recorded 1–2 min per tick. Warm 1,672 requests about 117 s, now "warm only on change" (WALK-perf) | Each serve tick | Already fixed |
| Audit DBs (`<prefix>_audit*`), producers' scratch | Minutes to an hour each | Audits and recaptures | Milestone |
| Test template and set-up cache (PERF-02) | Built once per fingerprint | Full suites | Already done |

<!--diagram:prepare-->

### 4.5 Defects found while measuring (fix whatever the speed decision)

- **D-1: the chain graph check is vacuous in worktrees on Linux (class: Windows path conventions left in the guard plumbing after the move to the VPS).**
  - **Where:** `tools/check-all.ps1` line 74 joins `PYTHONPATH` with `";"`.
  - **What happens:** on Linux, the branch's `backend` folder is glued to the next entry into one bad path, so `assetops_backend` resolves through the editable install to **`main`'s** checkout. Reproduced today: the import printed `/opt/assetecon/AssetOpsV1/backend/assetops_backend/__init__.py` for a worktree path.
  - **Sweep (W6):** I searched `tools/*.ps1` and `tools/checks/*.ps1` for `;` path joins and `Scripts\python.exe`.
    - Line 74 is the only silent case.
    - The `.venv\Scripts\python.exe` default in `check-all` fails loudly without `-Python`, so it is safe.
    - `chain-structure.ps1`, `configuration-persistence.ps1` and `run-host-tests.ps1` already try both layouts.
- **D-2: `check-agent-workflow.ps1` enforces the superseded start path** (see G4). It will fail when declutter step 4 moves those files.
- **D-3: `select-tests.py` suggests `npx vitest related` for a change under `frontend/docs/`.** This is minor.

---

## 5. Parallelisation and combination: what each option saves

<!--diagram:checkall-->

| Option | How | Saving (estimate, with assumptions) | Memory | Risk and containment |
| --- | --- | --- | --- | --- |
| **P1. Self-tests run only when their guard changes** | `check-all` runs a guard's fixture or self-test step only if the guard's own files differ from `main` (git diff of named paths), and always with `-Full` (milestone, `main` after merge) | −464 s per run when the writer guard is unchanged, which is most slices. A writer-adding slice edits `configuration-persistence.ps1` and so still runs them | none | A self-test skipped on a slice that did not touch the guard cannot catch anything new: the guard code is the same. Containment: `-Full` on `main` after every merge |
| **P2. Guards run in parallel** | A pool of 4 processes. The 14 architecture modules become separate jobs. Results are reported in the fixed order, failures in full | 110 s → about 35–45 s. The critical path is the dependency-direction module (31 s). The work is about 150 CPU-seconds | Peak about 3.1 GB at 4-way (the sum of the four largest measured peaks: 1.09 + 0.89 + 0.57 + 0.54). 14 GB available | Guards are read-only and independent. A failing guard still fails the run |
| **P3. Remove the duplicate** | Drop the standalone navigation-truthfulness call. G2 already runs the module | −16 s | − | None: same function, same inputs |
| **P4. Estate self-tests in parallel** (when they do run) | `pytest -n 4` on `test_estate_guard.py` (each test uses its own temp copy) | 464 s → about 120–140 s | About 1.7 GB (4 × 430 MB) | Isolation is already per test (a temp folder) |
| **P5. End the central queue** | Builders run the fast `check-all` themselves (as before 12 Nov), with at most 2 at once (a `flock` slot). The coordinator keeps one `-Full` run on `main` after each merge | Queue wait: recorded 10–20 min per slice in the busy days of 12–13 Nov (estimate from the handoff's queue scripts) | 2 × 3.1 GB | The original reason (starvation at more than 20 min a run) goes away at 40 s and 3 GB. Containment: the 2-slot cap |
| **P6. A builder runs `check-all` before review, not after merging main** | Builders run the fast mode at the end of the build, so post-merge guard fix rounds shrink. UP-1 had 3/21 failing after merge, fixed in a separate round | One fewer fix round on some slices (estimate: 1 in 10) | − | None |
| **P7. Combine the recapture and the register reconcile, and run them in parallel** | One pass per producer database. Producer databases come from a template clone (as PERF-02 does for tests). 2–3 browser contexts at once. Classify against the register while capturing (the brief already compares) | Milestone only. Estimate: the recapture's elapsed time halves (unmeasured) | Each browser about 0.5–1 GB, each producer DB server-side | Owner rule: one heavy job at a time on the shared DB. Containment: browser contexts in parallel against **one** producer DB |
| **P8. Snapshot verified databases instead of rebuilding** | After a prepare passes its self-check, keep it as `CREATE DATABASE … TEMPLATE`, keyed by a fingerprint of the data-producing code, migrations, scenarios and config. A new audit or rehearsal DB is a clone | 2 h → about 15 min (a clone takes a minute or two, then the parallel self-check takes about 7 min). This applies only when the fingerprint matches | Disk: one more copy of the DB | Stale data if the fingerprint is too narrow. Containment: a wide fingerprint (all product code, as PERF-02), and the self-check runs on every clone. Using a clone for the **walkthrough** DB is an owner decision (OD-4) |
| **P9. Parallel self-check rows** | The 54 read-only self-check rows run in a pool of 4 connections | 1,474 s → about 400–450 s (estimate: rows are independent reads; the slowest row is unknown) | 4 DB sessions | Rows must stay read-only. A row that writes stays serial |
| **P10. Independent Sites side by side in prepare** | Kobo (1,725 s) and Kisiwa (1,195 s) build in two processes | −about 1,195 s per prepare | About 2× the prepare's memory (unmeasured) | Precondition: the story clock, ID sequences and the single-writer rule allow two Sites at once. Not yet shown. **Later** |
| **P11. Caching** | Dependencies: `node_modules` are already shared by symlink, and the test venv and pip cache are already cached. Builds: `tsc --incremental` (34.9 s → a few seconds when warm; estimate). DB templates: P8 | `tsc`: −25–30 s per run (estimate) | − | `tsc` incremental is standard. The cache lives in the worktree |
| **P12. Sharding the full backend suite** | Already sharded by xdist (`--dist loadfile`, workers from free memory) | On the VPS (8 vCPU against the laptop's 4 cores), 6–8 workers is an estimate of about 20–25 min warm. **Unmeasured**: the owner rule keeps it unrun | 340 MB per worker plus Postgres | Owner rule: only on request |

**What is not worth doing.**
- Merging the small guards into one process saves under 5 s.
- Sharding vitest across machines: there is one machine.
- Smaller data windows in tests (PERF-02 O5): this changes what tests assert. Already rejected.

---

## 6. Later: data-processing paths (ranked; not designed here)

These are the product's own paths whose runtime slows building, database preparation or the demo. Ranked by expected gain × confidence ÷ effort. None of them changes a figure: each one must reproduce the same rows (a row fingerprint before and after) and passes a discovery review (W5), because each touches a product path.

| Rank | Path | Today (source) | Opportunity | Expected gain | Preconditions |
| --- | --- | --- | --- | --- | --- |
| L1 | Self-check (`demo_combined_finish.py`, 54 rows) | 1,474 s per prepare (recorded) | Run the read-only rows in a pool of 4 | −17 min per prepare | Rows proven read-only. Connection budget |
| L2 | Prepared demo databases | About 2 h per DB | Template snapshot per data fingerprint (P8) | −1 h 45 min per rebuild when the fingerprint matches | Owner OD-4 for the walkthrough DB. Wide fingerprint |
| L3 | Test selection | 54–100% of files picked | A coverage map from one full run (`--cov-context=test`) gives test → product files. Select by changed files | Postgres slice-end runs shrink to tests that really executed the change (estimate: 5–20% of files) | One full run with coverage (owner consent). Rebuild the map at milestone. The full suite stays the net |
| L4 | Drain after Site builds (snapshots, threads) | 817 s for 7 ticks; 817 snapshots pending at start (recorded) | Recompute snapshots per Site in one batch per tick instead of one at a time. Process Sites concurrently inside the single writer | −5–8 min per prepare (estimate) | Rule 8: one writer per table stays one writer. Parallelism is inside it |
| L5 | Ingest path: evidence ledger and mini-depth writes; gateway TLS reuse (PERF-03, owner-approved "B", never built) | Kobo 72 runs in 1,725 s (24 s a run). Tests: cold −3–5, warm −1–3 min (PERF-02 estimate) | Batch inserts, reuse connections | −20–30% of the Site-build time (estimate) | Product-path change. Pass list plus per-family row fingerprints |
| L6 | Recapture generators (`tools/s*_walkthrough.py`, the batch producers) | Every batch rebuilt its own producer DB | One template per producer, cloned per batch; 2–3 browser contexts | About half the recapture time (estimate) | Producers run unmodified (the recapture brief's rule) |
| L7 | Kisiwa night replay | 10 nights in 1,193 s (119 s a night, 5× Kobo's run cost; recorded) | Profile first: the cause is unknown | Unknown until profiled | A py-spy profile (PERF-01 did this for tests) |
| L8 | Two Sites side by side in prepare (P10) | 1,725 + 1,195 s in sequence | Two processes | −20 min per prepare | Story-clock and sequence independence shown |
| L9 | Test set-up cache, the rest (PERF-02 O1–O4, O6) | 33.9 min warm (recorded) | Cache `CaseRunner`, key the 285 live steps, standard sites as cache operations, a narrower fingerprint plus nightly verify | → about 15–16 min warm (PERF-02 estimate) | It matters only once full suites run again |
| L10 | Dependency-direction guard | 30.8 s, 1.09 GB (measured) | Parse imports once (a Python AST, as `select-tests.py` does) instead of regex in PowerShell | −25 s from the guards' critical path | Same rule set. A self-test proves the same failures |

Already fixed and not repeated:
- the Performance gate's `count(*)` per request (WALK-perf, "gate inside compose");
- redundant re-warming every tick ("warm only on change");
- Portfolio and Site range recomputation from raw readings (stored period and day rows: ANY-1 and SR-*).

---

## 7. The recommendation

### 7.1 Ranked actions

Score = (hours saved per fortnight × confidence) ÷ effort in lane-days, the same shape as the two-week plan's A1 score.

Hours saved assume **30 slices a fortnight**, a planning assumption: the sprint ran 105 slice merges in 10 days, so the real figure may be higher. Each slice is assumed to run `check-all` 2.5 times.

A defect fix (D-1) ranks first whatever its score, because a check that does not check is an honesty problem.

Rank otherwise follows the score, with two adjustments:
- A4 sits directly below A3, because A3 needs it.
- A6 sits above A7 and A8, because it belongs to the first slice.

<!--diagram:ranking-->

| Rank | Action | Saves | Conf | Effort (lane-days) | Score | Risk and containment | When |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | **A1. Fix D-1** (the `PYTHONPATH` separator in `check-all`) | 0 h. It makes the chain graph check real in worktrees | 1.0 | 0.1 | defect | None | Now |
| 2 | **A2. Estate self-tests only when the writer guard changes** (P1, applies the 4 Nov ruling) | 7.7 min × 75 runs ≈ **9.6 h** | 1.0 | 0.25 | 38 | A guard edit always triggers them. `-Full` on `main` after every merge | Now |
| 3 | **A3. End the central queue: builders run fast `check-all`, 2 at a time** (P5, P6) | ≈ 15 min queue wait × 30 ≈ **7.5 h** elapsed | 0.7 | 0.25 | 21 | Starvation. Contained by the 2-slot cap and a 3 GB peak | Now, after A2 and A4 |
| 4 | **A4. Guards in parallel, 4 at a time** (P2), plus the estate self-tests at `-n 4` when they run (P4) | 70 s × 75 ≈ **1.5 h**. It also enables A3 | 0.8 | 0.5 | 2.4 | Memory: 3.1 GB measured-sum peak | Now |
| 5 | **A5. Remove the duplicate navigation check** (P3) | 16 s × 75 ≈ **0.3 h** | 1.0 | 0.05 | 6.7 | None | Now |
| 6 | **A6. Retire the stale v69 and S1–S7 guard plumbing**: G5 (keep the gap catalogue), G6, G11. Move them to advisory now; delete them in declutter step 5 | Bookkeeping edits, about 2 a fortnight × 20 min ≈ **0.7 h**, plus one less source of false blocks | 0.8 | 0.5 | 1.1 | Losing the gap catalogue would weaken honesty. Contained: G7 and G8 stay blocking | Now (advisory); remove later |
| 7 | **A7. Parallel self-check rows** (P9, L1) | 17 min × 2.5 prepares ≈ **0.7 h**, on the walkthrough's critical path | 0.7 | 0.75 | 0.65 | A row that writes would race. Contained: run only rows proven read-only in the pool | Now, if a DB build is due in the fortnight |
| 8 | **A8. Verified DB snapshots for audit and rehearsal DBs** (P8, L2) | 1 h 45 min × 2 ≈ **3.5 h** | 0.7 | 1.25 | 2.0 | Stale data. Contained: wide fingerprint plus self-check on the clone. Walkthrough DB only if the owner agrees (OD-4) | Now, if a DB build is due; else later |
| 9 | **A9. Rewrite the agent-workflow guard for the new start path** (D-2) | Prevents a false block in declutter step 4 | 1.0 | 0.25 | (blocker) | None | With declutter step 4 |
| 10 | **A10. `tsc --incremental`** (P11) | 25 s × 30 ≈ **0.2 h** | 0.8 | 0.1 | 1.6 | Cache in the worktree only | Now (cheap) |
| 11 | A11. Coverage-map test selection (L3) | Postgres slice-end time −50–80% (estimate) | 0.5 | 1.5 | − | Needs one full run (owner) | Later |
| 12 | A12. Independent Sites in parallel in prepare (L8) | 20 min per prepare | 0.5 | 1.5 | 0.3 | Independence not shown | Later |
| 13 | A13. PERF-02 O1–O4 and O6, then PERF-03 (L9, L5) | Full suite 34 → about 16 min | 0.7 | 4.5 + 2.5 | − | Runs only when full suites run | Later (with E2) |
| 14 | A14. Recapture combined and parallel (P7, L6) | About half of the final recapture | 0.6 | 1.0 | − | One heavy DB job at a time | Later (final review) |
| 15 | A15. Windows-only tools off the Linux path (keep-awake, Windows memory sampler, host runner, the CRLF rule in RULES §7) | Agent confusion, not machine time | 1.0 | 0.25 | − | None | Declutter step 5 |

**Now (inside the two-week plan, after approval).** Ship A1–A6 and A10 as one tooling slice, `PIPE-1`. It is about 1.25 lane-days, one fresh review and a mechanical check, and it carries a self-test showing each skipped self-test still runs when its guard changes. Add A7–A8 as `PIPE-2` (about 2 lane-days) only if a walkthrough, rehearsal or demo database build falls inside the fortnight. The two-week plan currently defers "applying the pipeline and check speed-ups until their evaluation is approved". This document is that evaluation.

**Later:** A11–A15, and the data-path items L3–L10.

### 7.2 Cycle time per slice, before and after

<!--diagram:cycle-->

The model is a typical small or medium slice: one build, one review, a fix round on about half of slices, and a live check where data is touched. The build and review times are the observed agent pace, and they do not change. Elapsed minutes are estimates, except where a step's time was measured or recorded.

| Step | Before (min) | After (min) | Source |
| --- | ---: | ---: | --- |
| Build with focused tests | 40 | 40 | Observed pace; unchanged |
| Fresh review | 30 | 30 | Unchanged (W5) |
| Fix round plus re-review (average; about half of slices) | 25 | 23 | Fewer post-merge guard rounds (P6) |
| `check-all`: 2.5 runs, plus queue wait | 45 (2.5 × 10–16 min loaded, plus about 15 min queue) | 2 (2.5 × about 40 s, no queue) | Measured 589.6 s quiet; recorded 957 s loaded; estimate for after |
| Live check or parity (data slices) | 15 | 15 | Unchanged (owner D-SR.9) |
| **Total** | **≈ 155** (range 130–185) | **≈ 110** (range 100–125) | −28% |

Demo database: **about 2 h → about 1 h 20 min** with A7 and later A12. With A8 and a matching fingerprint it is **about 15 min**.

---

## 8. Owner decisions (W3: defaults applied pending your answer, except where your own rule is at stake)

| ID | Question | Architect default | Applied now? | Weigh in? |
| --- | --- | --- | --- | --- |
| OD-1 | Approve `PIPE-1` (A1–A6, A10) as one tooling slice in this fortnight? | **Yes** | No. Approval first (W1) | Yes |
| OD-2 | Run the estate self-tests only when the writer guard changes, plus a full run on `main` after every merge? | **Yes.** It applies the Architect ruling of 4 Nov | With OD-1 | Optional |
| OD-3 | End the coordinator's central `check-all` queue (builders run the fast mode, 2 at a time)? | **Yes**, once A2 and A4 are in. The queue rule was a coordinator rule (12 Nov), not yours | With OD-1 | Optional |
| OD-4 | May a **clone of a verified build** (same code fingerprint, self-check passed on the clone) count as the "clean, good DB" for a walkthrough? | **No change until you say so.** Clones are used for audit and rehearsal DBs only; walkthrough DBs are still prepared fresh | Default only | **Yes, your rule** |
| OD-5 | Retire the v69 and S1–S7 guard plumbing (G5 except the gap catalogue, G6, G11)? Advisory now, deleted in declutter step 5 | **Yes** | With OD-1 | Optional |
| OD-6 | Allow one full backend suite on the VPS, at night on a quiet machine, to measure the VPS baseline, record a coverage map (A11) and catch drift since 1 Nov (17 days without a full run)? | **No change**: full suites only when you ask. Recommended for you to consider, because the end-game run will otherwise meet every accumulated failure at once | No | **Yes, your rule** |
| OD-7 | Build `PIPE-2` (parallel self-check, verified snapshots) now or later? | **Now only if** a DB build falls in the fortnight | Default | Optional |

---

## 9. Guardrails that are never relaxed

- **Honesty labels.** The missing-claim scan, the mock-deviation and client-vocabulary guard, and fuel wording (K9) stay blocking on every slice. Data without a source is "not available yet".
- **Money correctness.** Chain coherence, the money test files on money changes, discovery review for any money figure (W5), and the row fingerprints required by every data-path change in §6.
- **Database safety.** The writer seam (rule 8) runs on every slice; only its self-tests move to "when changed". Only `*_test` and `<prefix>_audit*` databases are used. One heavy database job at a time. No bare `docker compose up`.
- **The owner's port and walkthrough rules.** Never touch 5490 or 8990, Docker during task work, or the walkthrough DB. Walkthroughs run only on a clean, good DB. No fallback DB.
- **No full suite unless the owner asks** (OD-6 asks; it does not assume).
- **Reviews.** A fresh review on every slice and W5 depth by risk. No speed-up here removes a review.
- **A guard change must be shown to fail on a real violation** (RULES §7). `PIPE-1` proves each conditional self-test still runs when its guard changes.

---

## 10. How this was measured

- `check-all`: run once under `/usr/bin/time -v`. Result: 589.6 s, 1,238,576 KB peak RSS, 21/21 passed.
- Each guard: timed separately with `/usr/bin/time -f "%e %M"`. Each architecture module was dot-sourced in its own `pwsh`.
- `tsc --noEmit`: timed in `frontend/`.
- `select-tests.py`: run on merges `f37b0ad9f`, `5e1a37e39`, `972dced4a`, `e818a3040` and `b4f17871e`.
- The `PYTHONPATH` defect: reproduced with a `;`-joined path and printing `assetops_backend.__file__`.
- Recorded figures: the prepare log `/opt/assetecon/AssetOpsV1-walk/var/polish_walk1113-prepare.log` (read only), `backend/TESTING.md`, `archive/agent-history/PERF-02-packet.md`, `.agent/lane-rules-vps-2026-11-12.md`, `.agent/coordinator-handoff.md` and the packets cited above.
- Merge counts: `git log main` since 8 Nov.
- No database was touched. No process was left running.
