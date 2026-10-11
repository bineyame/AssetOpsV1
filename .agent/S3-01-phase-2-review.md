# S3-01 phase 2 review: typed seam and durable dispatch assessment

- **Reviewer:** a fresh Claude reviewer (Opus), independent of the phase-2 Implementer. I did not author, fix, commit or merge anything in this slice.
- **Target:** branch `task/S3-01-dispatch-assessment`, diff `733ea8d..ef8aa56` (phase-2 commits `75886d1`..`ef8aa56`).
- **Judged against:** the task phase-2 row and its rule/input contract; `D-2026-10-11-s3-dispatch-interval-assessment`; `D-2026-10-11-s3-phase-1-fixture-and-late-evidence`; and the newer `D-2026-10-11-s3-phase-2-selection-and-read`, which already rules on Q1-Q8 subject to this review. I also used the phase-1 carries F3 and F5, and the packet.

## Verdict

**Accept with findings fixed on the branch.**

The seam, cohort rule, `dispatch-3` analytic, append-only persistence and worker lease/retry/coalescing are sound and well tested. I found no latest-wins, no summing across streams, and no epoch-name heuristic. Candidate needs both capability roles to be bound and accepted. The input hash excludes `knowledge_at` and covers everything else the decision requires.

Two findings should be fixed on the branch before phase 3 builds on them:
- **F1:** a window claim label that reads `COMPLETE` over missing or poor evidence. This is a persisted `dispatch-3` rule.
- **F2:** a test-collection break.

The rest are carries for phase 3 or the Architect.

## Findings

### F1 - Block (fix on branch): window `COMPLETE` despite Indeterminate gap portions

**Where:** `backend/assetops_backend/analytics/dispatch_v3.py:530-535`, and the "Claims" paragraph of `backend/tests/dispatch_3_decision_table.md`.

**What is wrong:** The window claim becomes `LIMITED` only when one of these is present:
- a window limitation (missing role binding, cohort limit, configuration);
- an interval `OPEN_BOUND`.

A segment that is Indeterminate because a reading is MISSING, NOT_GOOD or CONFLICTING does not make the window `LIMITED`, and neither does a generator-state gap. I reproduced this with the test helpers. An interval with a 45-minute PCS-capability reporting gap gave:
- interval `CANDIDATE_AVOIDABLE`, with 45 Indeterminate minutes and confidence LOW;
- window `COMPLETE` with `limitations: []`.

**Why it matters:**
- The task requires that missing or weak-quality evidence "each have an honest state" and that none defaults to healthy.
- `dispatch-2`'s readiness table maps "a coverage gap left a segment Indeterminate" to Limited. `dispatch-3` changes this without recording it as a changed branch, contrary to "record every ... carried/changed branch".
- The fixture hides the problem. The `missing-poor-quality` case (10-03) is persisted as `LIMITED` only because its six-hour bracket reaches the 10-04 same-epoch overlap: its limitations are the 10-04 `feeder_demand` `REPORTS_OVERLAP`/`SEQUENCE_ORDER_INVERTED` spans. Its own 06:00-06:45 gap contributes nothing.
- The label is persisted in `assessment_revision.claim_level`. Fixing it after phase 3 would need a new model version.

**Fix:** Make the window `LIMITED` whenever any interval has a non-observed or Indeterminate segment with a named missing input, and name those spans as window limitations. Alternatively, record the narrower semantics in the `dispatch-3` table as an explicit change from `dispatch-2`, with Architect agreement. Add a unit test where the only defect is an in-interval gap.

### F2 - Block (fix on branch): the no-database backend suite cannot collect the new Postgres test

**Where:** `backend/tests/test_s3_dispatch_assessment_postgres.py:22-37`.

**What is wrong:** `Window` is imported only under `if URL:`, but `WINDOW = Window(...)` runs at module level. Without `ASSETOPS_TEST_DATABASE_URL`, collection raises `NameError`, and `pytest backend/tests -q` stops with "Interrupted: errors during collection".

**Why it matters:** The standing Reviewer check is `pytest backend/tests -q`, and it now cannot run without Postgres. The same break already exists in `test_s2_site_evidence_postgres.py` (NameError on `RECE...`). That one is not in this diff, but this slice repeats the pattern.

**Fix:** Import `Window` unconditionally, or move the constants under `if URL:`. Fixing the S2 file too would be welcome, but is not required by this slice.

### F3 - Carry (Architect, Q4 / phase-3 read): fixture isolation holds only by fixture placement

**Where:** `backend/assetops_backend/analytics/cohort.py:62-71`. Packet Q4 claims the fixture's "readings only ever give named limits, never Candidate or Necessary".

**What is wrong:** The default cohort treats non-overlapping epochs of one source as one sequential stream. This is correct for reprovisioning. It also means a labelled fixture epoch that shares a window with an ordinary epoch, without overlapping its span, is silently blended into the default cohort.

I reproduced this with a full-role fixture epoch at 14:00 next to an ordinary epoch at 05:00 in one window. The result was `SELECTED_UNIQUE` with both epochs, and two `CANDIDATE_AVOIDABLE` intervals, one of them from the fixture. `test_out_of_order_reading_marks_its_span` already shows the `ooo` epoch joining `SELECTED_UNIQUE`.

**Why it matters:** `D-2026-10-11-s3-phase-2-selection-and-read` allows a lone fixture stream only "as its actual limited/Indeterminate assessment", and says the product "must never silently present a known fixture as ordinary positive output". The current fixtures are safe only because:
- they sit on their own days (10-06, 10-07);
- they carry two single-role readings.

Nothing in the code enforces either condition.

**Fix:** No phase-2 code change is possible without a central marker, which is ruled out. Before the phase-3 default read ships, record two things:
- in the Q4 answer, that the "never positive" property depends on fixture content and placement;
- as a producer invariant (`tools/s3_dispatch_cases.py`), that a fault-fixture epoch never shares a UTC window and bracket with an ordinary epoch of the same source.

Phase 3 must surface the manifest annotation on any window whose cohort includes a manifest-labelled epoch.

### F4 - Carry (before phase-3 cutover): backdated configuration is detected only when someone runs `reconcile`

**Where:** `backend/assetops_backend/analytics/assessment_worker.py:144-157` and `assess_dispatch.py`.

**What is wrong:** Nothing calls `reconcile` on a Foundation or binding publication or on a model deploy: not `process-jobs`, and not the publication path. A backdated publication therefore leaves no dirty job until an operator runs the CLI.

**Why it matters:** The decision says backdated publications and model changes "enqueue affected windows". Phase 3 plans to derive `CURRENT` from runs plus overlapping jobs (Q7). Without a job, an assessment that a backdated reserve has made stale would read `CURRENT`.

**Fix:** Before cutover, do one of these:
- enqueue from the publication service;
- run `reconcile` within `process-jobs`;
- have the phase-3 read compare the head run's `configuration_sha256` with the current selection.

The packet's "Met" for this row should say "mechanism built; trigger manual".

### F5 - Carry (fixture, before the phase-3 reviewer path): no Necessary interval exists in the evidence

**Where:** `tools/s3_dispatch_cases.py:569` (`physical-necessary` checks only that a `NECESSARY` segment exists). Run evidence: the `physical-necessary` window is `COMPLETE` with interval `CANDIDATE_AVOIDABLE`.

**Why it matters:** The task's reviewer path is "open a Necessary, Candidate and Indeterminate interval after reload", and the decision asks for Necessary cases. No persisted interval anywhere in the ten cases is `NECESSARY`. The analytic can produce one, as `test_near_reserve_is_physical_necessary` shows, but the product fixture does not.

**Fix:** Add a fixture interval whose segments are all Necessary, or get an Architect ruling that Necessary segments inside a Candidate interval satisfy the path.

### F6 - Carry (low): an expired lease is re-leased without an attempts cap

**Where:** `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:184-186`.

**What is wrong:** An expired `LEASED` job is re-leased with `attempts + 1` regardless of `max_attempts`. A job that always outlives its five-minute lease, or that crashes its worker, cycles forever and never becomes `FAILED` with a reason.

**Why it matters:** No output is lost and nothing stale is published, because `_still_mine` refuses the commit. The phase-3 `FAILED` state would never appear for this class of failure, though.

**Fix:** In `lease_job`, mark a job `FAILED` with "lease expired N times" once its attempts reach the cap.

## Focus areas checked

- **Input hash excluding `knowledge_at`:** This is correct for the decision's list of covered fields. The hash covers:
  - window, read range and model version;
  - cohort payload and limits;
  - sorted evidence IDs with their digests;
  - as-accepted (Foundation, binding set, binding) triples;
  - selected control values and validity;
  - selected bindings, role coverage and configuration limits.

  Normalized value, role and asset come from envelope and binding revision, which are both hashed. Excluding the cutoff matches the decision. Its consequence, that a replay at a cutoff is not reproducible under in-flight commits, is now ruled on in `D-...-phase-2-selection-and-read`.
- **Bitemporal selection at the cutoff (Q1):** Foundation and binding sets are scoped by tenant and Site, use `recorded_at <= K < superseded_at`, and overlap the read range. Overlapping Foundation revisions produce a named configuration limit. Readings keep their as-accepted revision IDs separately. This is safe and matches the Architect's ruling. Two cases fail closed (`UNBOUND`/`MISSING`), never to Candidate:
  - a reading's accepted role is no longer bound at the cutoff;
  - two selected binding sets bind one role to different assets (`MULTIPLE_BINDINGS`).
- **Cohort and ambiguity:**
  - Overlapping epochs of one source give `AMBIGUOUS` and no intervals.
  - An explicit choice uses only the named members, under a suffixed key.
  - Same-epoch overlap gives `REPORTS_OVERLAP`/`SEQUENCE_ORDER_INVERTED` spans, and generator-series ambiguity makes the window `INDETERMINATE`.
  - Values are never summed across streams: load sums only over distinct bound feeder assets.
  - Equal-rank distinct values at one lookup are `CONFLICTING`.
  - Clash grouping by (gateway, source) is sufficient, because `source.gateway_id` is part of the immutable source identity (migrations 0001/0005).
  - The sequence-inversion check orders by sequence, ties broken by source time from the query's `ORDER BY`, so ties cannot produce a false inversion.

  See F3 for the sequential-epoch caveat.
- **Candidate gating:** Row 5a needs `load`, `pv` and `dis`. Row 5b also needs `soc` and `reserve`. Each comes from an effective binding at t and a GOOD accepted reading. Under roles-1 the window is `LIMITED` with `MISSING_ROLE` spans and never yields Candidate, as both the unit test and case 10-01 show. Minimum runtime only downgrades Candidate.
- **Worker:**
  - The lease uses `FOR UPDATE SKIP LOCKED`.
  - `_still_mine` re-reads `(status, attempts)` `FOR UPDATE` in the persisting transaction, and a lost lease commits nothing (tested).
  - No event is lost in either race order. S2's coalescing `SELECT ... status='PENDING' ... FOR UPDATE` either locks the PENDING job first, so the lease skips it and later sees the evidence, or it re-checks after the lease and creates a new PENDING job.
  - The store's `enqueue` uses the same advisory-lock key as the ledger (`site || ':' || domain`).
  - Persisting is serialized per Site by a separate advisory lock, so `revision_no` cannot race.
  - Retry and back-off, and FAILED with `last_error`, are tested.
- **Append-only:** All four tables have `ledger_append_only` triggers and same-Site composite foreign keys. DELETE is refused (tested). A revision is appended only when the basis differs from the latest one under that key. The run-to-revision link records reuse.
- **Stated deviations:** The late-central proof changes only the window revision in the fixture, but the Postgres test proves interval-level reassessment. That is acceptable. The same-epoch-overlap, minimum-runtime and no-projection deviations are accurate and fail closed.
- **Guard rule 8:** The fourth writer is confined to its own tables, plus `recompute_job` inserts and status/window updates. Other modules may not write the assessment tables. I did not re-run the Implementer's non-vacuity mutation.

## Checks I ran

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `tools/check-all.ps1` | All 6 guards passed |
| `pytest backend/tests -q` (no DB URL) | **Interrupted: 2 collection errors**. One is `test_s3_dispatch_assessment_postgres.py` NameError `Window` (F2); the other is the existing `test_s2_site_evidence_postgres.py` |
| `pytest test_s3_dispatch_v3_analytic.py` | 16 passed |
| `pytest test_s3_dispatch_assessment_postgres.py` on an isolated, newly created `assetops_s3p2review_test` (dropped afterwards) | 8 passed |
| Analytic probe script (scratchpad; helpers from the unit test module) | Reproduced F1 (window `COMPLETE` with 45 Indeterminate minutes) and F3 (fixture epoch blended, giving Candidate) |
| Manifest/run evidence read | Per-case results confirm F1's masking (10-03 limitations come from 10-04) and F5 (no `NECESSARY` interval) |

**Not run or not verified by me:**
- the full Postgres backend suite (1795);
- host, gateway and simulator suites;
- the producer `run`/`verify`, the guard non-vacuity mutation, and any concurrent in-flight-acceptance race beyond the sequential test.

There is no frontend or layout surface in phase 2. I did not touch the owner's servers or `var/`.

## Residual risk not named in the packet

- F1 masking: the 10-03 case's honest-state evidence depends on a neighbouring day's defect.
- F3: fixture isolation is a property of where the producer places data, not of the code.
- F4: configuration staleness has no automatic trigger.
- `explicit` runs and their cohort-suffixed keys are never reconciled, and the suffix includes the other present members (alternatives). An explicit key therefore changes when a new stream appears in the window. Phase 3 should treat explicit selections as point-in-time.
