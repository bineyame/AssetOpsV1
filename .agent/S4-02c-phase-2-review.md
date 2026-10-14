# S4-02c phase 2: fresh Claude review (scoped drain and run plan)

Reviewer: fresh Claude (did not build this). Branch `task/S4-02c-evidence-consequence-work`. Diff reviewed:
`0a79be14..81c19ca3` (`29e1218b`, `cc0f9de5`, `81c19ca3`). Judged against:
- packet `tasks/S4-02c-evidence-consequence-work.md`, phase row 2, contract items 3 and 4, carries C4 (worker half) and R2;
- `.agent/S4-02c-plan-fix-rereview.md` N1, N3, N4 and N7;
- `.agent/S4-02c-phase-1-review.md` L1-L3.

I treated the handoff `.agent/S4-02c-phase-2-handoff.md` and `.ai/CODE_STATE.md` "S4-02c phase 2" as claims and
checked them against the code. I also reran the tests and my own mutations.

## Verdict: ACCEPT with carries

The drain, no-op predicate, Site claim and retry schedule are correct against the contract.
- I found no High finding.
- **M1 (Medium):** the CLI change breaks the merged S4-02b walkthrough tool. It is a small fix and must land on this
  branch before merge. It does not block the phase 3 build.
- **L1-L2 (Low):** test gaps and wording.
- **I1-I4 (Info):** residual risks.

## Checks I ran (as observed)

- **Focused suites.** I ran them on scratch DB `assetops_s402crev2_test`, from a `git archive HEAD` copy in my
  scratchpad with `PYTHONPATH` pointed at that copy. The files were `test_s4_evidence_drain_postgres.py`,
  `test_s4_evidence_drain.py`, `test_s4_consequence_cause_dispatch.py`, `test_s4_consequence_read.py` and
  `test_s4_evidence_consequence_work_postgres.py`. Result: **42 passed** in 2:20.
- **R2 as I measured it.**
  - Six ingestion chunks of 48 accepted generator-power means, 581 work rows in total: **0.508, 0.485, 0.554,
    0.535, 0.539, 0.496 s**.
  - Drain in bounded runs of 100: **11.0 s** after the first run. The printed "581 rows" is the total including
    the first run, while the time excludes that run.
- **`tools/check-all.ps1` on the live tree: All 9 guards passed.** Architecture seams and Agent workflow are
  among them.
- **Full backend: not rerun.** None of my findings touch the code paths it would add coverage for. The
  implementer reported 2090 passed, and I have not verified that number.
- **Frontend: not run.** No frontend file changed. A grep of `frontend/src` shows `last_error_code` for
  consequences only in the type at `financialsClient.ts:219`. Nothing renders `no_op_reason`, `NO_WORK_RECORDED` or
  the new error codes.
- **My mutations: 6 killed, 4 survived.** I ran each one against the archive copy, never the live tree. My first
  `-k` selectors were too narrow for mutations 1 and 3, so I reran both against the full two files. The table shows
  the full-file results.

| # | Mutation | Result |
| --- | --- | --- |
| 0 | `evidence_target` drops `e.site_id = :s` (C4) | killed (forged locator test) |
| 1 | due test `<= now` -> `< now` | killed (injected-clock unit test at exactly f+1m) |
| 2 | `deferred` counts the limit overflow | killed (R2 bounded batch, deferred 0) |
| 3 | `backlog` subtracts failed outcomes too | **survived** (see L1) |
| 4 | runner lock key without the Site | **survived** (see L1) |
| 5 | outside-Candidate test uses the episode instead of merged Candidate spans | killed |
| 6 | `accepted` EXISTS ignores `d.decision = 'ACCEPTED'` | **survived** (see L1; practically redundant) |
| 7 | `WORK_SCOPE_MISMATCH` checks the Site only, not the tenant | **survived** (see L1; defensive path) |
| 8 | superseded test `!=` -> `<=` | killed |
| 9 | `claim_site` yields True when not held | killed (second runner / killed runner test) |

- **Cleanup.** I dropped the scratch DB and confirmed it is gone. The live tree is clean.

## Focus points

- **No-op predicate (N1).** `evidence_no_op` (`recompute.py:83-102`) no-ops only in these cases:
  - superseded;
  - a stored role other than `generator_power`;
  - an asset other than `finding.generator_asset_id`;
  - a null or empty interval;
  - no strict half-open overlap with `fc.merge` of the claim's positive-width `candidate_spans`.

  These are the same filters, in the same form, as `quantify`'s examined set:
  - the load is limited by `load_input` (`postgres_consequence_store.py:119-131`: ACCEPTED disposition, role,
    asset, non-null interval);
  - the candidates are then `fuel_cost.py:309-320`: `raw_spans` with `s < e`, `merge`, `_overlaps`;
  - the same `_at`/`_instant` parsing applies.

  Quality is never consulted. Where `quantify` returns early with an empty examined set (for example
  `CANDIDATE_SPAN_UNVERIFIED`), the drain derives and replays, so the no-op is never broader than `quantify`.
- **The read cannot be left STALE.** The read's currentness re-derives through `quantify`
  (`consequence_read.py:180-186`). `technical_input_sha256` hashes only `examined_evidence_ids` and the counted
  intervals. A no-opped reading therefore cannot leave the head STALE with `NO_WORK_RECORDED`.
- **Latest-revision scope.** `latest_revision_no` is `max(revision_no)` over the same tenant, Site and Finding
  (`postgres_consequence_store.py:271-276`). That is the 0012 trigger's definition.
- **The superseded test is end-to-end.** The no-op records SUCCEEDED, `[]` and `FINDING_REVISION_SUPERSEDED`. The
  new revision's FRA work appends its own consequence, and the old revision gets no consequence n+1.
- **C4 forged locator.** Both lookups are tenant- and Site-scoped, and the revision lookup also checks
  `r.finding_id = :f`. A miss raises `EVIDENCE_LOCATOR_NOT_IN_SITE` before any derive. The unit Store raises on
  `latest_revisions_overlapping`, `load_input` and `append`, which proves there is no fallback. Mutation 0 is
  killed.
- **`WORK_SCOPE_MISMATCH` cannot leave work stuck.** The runner cannot reach this path, because `pending_work`
  is scoped by tenant and Site, so a run never selects another scope's row. The row is drained normally by its
  own Site's runner. In the database, the scoped FKs also make a forged locator row impossible. Returning it
  unrecorded (`attempt_no` 0) is acceptable for a defensive, programmatic-only path, and nothing retries it
  forever.
- **Runner claim (N3).** The claim is a dedicated connection from the store engine, set to AUTOCOMMIT:
  - it uses `pg_try_advisory_lock(hashtextextended('financial_consequence_runner:'||site, 0))`;
  - it unlocks only when `held`, inside `finally`;
  - if the unlock fails it calls `invalidate()`, then `close()`;
  - it is held through selection and processing (`recompute.py:303-312`).

  Two tests cover it:
  - The `pg_locks` check after a normal run catches a missing unlock. That check matters because session
    advisory locks are re-entrant on a reused pooled connection.
  - The killed-subprocess test proves that a killed runner's lock is released and that the restart drains.

  `run` is the only production caller. `run_pending` (unclaimed) is used only by tests.
- **Retry (N4).**
  - Schedule: `retry_due_at` gives 1, 2, 4, 8, 16, then 16 minutes, with no cap.
  - Inputs: `last_attempt_no` and `finished_at` come from the lateral latest attempt. Selection already excludes
    work with a SUCCEEDED attempt, so the latest attempt is always FAILED.
  - Clock: the injected `now` is compared with the DB `finished_at`. The Postgres test steps f+59s deferred,
    f+1m due, then f+2m and f+4m, without sleeping.
  - Never-attempted work is always due. This avoids app/DB clock skew deferring fresh rows, and I accept it.
  - Uncapped steady state: see I1.
- **L2 starvation is fixed.** Work is ordered by the instant it became eligible: `enqueued_at` if never
  attempted, otherwise the retry time. This is FIFO by eligibility, so a permanently failing row competes once
  per 16 minutes and cannot hold the head of the queue. The Postgres starvation test would fail under the old
  oldest-first order.
- **CLI.**
  - `--tenant` is required on both subcommands, and a non-`demo` tenant exits 2 with a message saying it covers no
    other tenant's Sites.
  - `--limit` must be at least 1 (default 100).
  - The summary line carries the Site scope and all seven counts.
  - A skipped Site exits 0. I accept that, because an overlapping tick is normal operation; see I2.
  - The runbook in `backend/README-db.md` names the timer, owner, cadence, overlap and recovery.
- **The deviations are accepted.**
  - Test-written work rows for the role, asset and outside-Candidate no-ops are acceptable. The trigger cannot
    produce those rows, rule 8 scans only `backend/assetops_backend`, and the guard passed.
  - Skipped exit 0 is accepted, as above.
- **Phase 1 carries.**
  - L1: the race probe is now scoped to `current_database()` and the Site enqueue key. It passed in my run.
  - L3: the downgrade refusal on a no-op reason is now tested.
  - L2: closed, as described above.
- **USER_REVIEW_REQUIRED: false still holds.**
  - (a) No new owner-facing text. The new codes are typed fields only, `REASONS` and `bridge_consequence` are
    untouched, and no component renders them.
  - (b) is untouched in phase 2.

## Findings

### M1 (Medium, regression): the CLI change breaks the merged S4-02b walkthrough tool

`tools/s402b_fuel_cost_walkthrough.py:164` runs `-m assetops_backend.recompute_consequences run --site KOBO-001`
without `--tenant`, and `--tenant` is now required (`recompute_consequences.py:69-70`). I confirmed that
`main(['run','--site','KOBO-001'])` exits 2 ("the following arguments are required: --tenant"), so `tree_py(...,
check=True)` raises.

Even with `--tenant` added, the tool would still fail. `:165-167` parses every `{` line and reads
`i["succeeded"]`, and the new summary line (`recompute_consequences.py:98-101`) has no `succeeded` key, so the
tool raises `KeyError`.

**Why it matters:**
- This is S4-02b's documented reviewer and owner walkthrough (`.ai/ACTIVE_CONTEXT.md:33`).
- `tools/s402b-fuel-cost-evidence.mjs:254-255` drives it through `walk("recompute")`, so that evidence harness
  breaks with it.
- The packet asks to reuse the S4-02b tools as walkthrough bases.
- No test covers these tools, which is why the suite stays green.

**Fix (on this branch, before merge):**
1. Pass `--tenant demo` in the tool.
2. Keep only the per-item lines (those with `work_id`), or read the summary line's counts.
3. Update the stale invocation in the `tools/s402b_power_cases.py:14` docstring.

### L1 (Low, test gaps): four of my mutations survive

- **`backlog` is never asserted after a run with a failed item (mutation 3).** Assert
  `counts()["backlog"] == 1` on the first failing run in the retry test.
- **The runner key is never shown to be per-Site (mutation 4).** Assert the key text, or show that a claim on
  Site A does not skip a run on Site B. Item 4 keys the claim by Site, and a constant key would silently
  serialize every Site.
- **No Postgres test reaches `EVIDENCE_NOT_ACCEPTED` (mutation 6).** The `d.decision = 'ACCEPTED'` term is
  effectively redundant, because only an ACCEPTED disposition at the same batch and ordinal carries that
  `accepted_evidence_id`. The unit test covers the code path, so this is Info-level.
- **No test covers a tenant-only mismatch (mutation 7).** It is a defensive path, because Site IDs are globally
  unique.

### L2 (Low, wording): the R2 print mislabels its count

`test_s4_evidence_drain_postgres.py:458` prints "{drained} rows ... after the first run". `drained` includes the
first run's 100, but the timer excludes it. The handoff phrased this correctly ("remaining 481 rows ... 14.2 s").
Suggested label: "N rows (incl. first run); remaining drained in Xs".

### I1 (Info, residual): the uncapped 16-minute steady state grows attempts without bound

A deterministic failure keeps failing on every retry. Examples are `EVIDENCE_NOT_ACCEPTED`,
`EVIDENCE_LOCATOR_NOT_IN_SITE`, or `RECOMPUTE_FAILED` from a code defect. Each such row appends about 90 FAILED
attempts per day indefinitely. `pending_work` then runs a `count(*)` and a lateral lookup over them for every
pending row on every tick, and loads every pending row of the Site.

This matches the contract (no terminal cap, pending stays visible) and is fine at today's scale. It belongs
beside R2 as a named risk: pending work has no alert or terminal state. Past about 1600 permanently failing rows
per Site at `--limit 100`, those rows alone would take all of each run's capacity. FIFO-by-eligibility ordering
still keeps new work's delay bounded, but the backlog would grow.

### I2 (Info, residual): a hung runner shows only as "skipped" with exit 0

A runner that is hung rather than killed keeps its session alive and holds the claim. Every later tick then
reports `"skipped": true` and exits 0, and Task Scheduler's "Do not start a new instance" hides it further. The
runbook should say that `skipped` repeated across ticks is the alarm signal. Alternatively, a
`statement_timeout`/`idle_session_timeout` or a run deadline would bound it. This is not a contract gap.

### I3 (Info): app/DB clock skew shifts retry timing only

`now` is the app clock and `finished_at` is the DB clock (N4 by design). Skew moves a retry earlier or later by
the skew amount. Never-attempted work is unaffected, because it is always due.

### I4 (Info, carried from phase 1 I1): concurrent overlapping ingestion chunks are still unmeasured

The handoff says so. Keep it named for phase 3 and closeout.

## Carries for phase 3

- **M1:** fix the S4-02b walkthrough tool's CLI call and summary-line parsing, and update the stale docstring.
  This is a merge gate. If phase 3 does not rerun the S4-02b walkthrough, at least run its `recompute` path once
  on a private DB.
- **L1:** add the backlog-after-failure and per-Site-key assertions. The other two are optional.
- **L2:** fix the label (optional).
- **Phase 3 contract items still open:**
  - Use `run(...)` or the CLI for the walkthrough drain.
  - N2 (publish the price before Leg B).
  - N5 (assert the Leg A precondition, otherwise stop and report).
  - C5 (exact before/after IDs).
  - N7 (state in the artifact that the wrong-asset no-op is proved by these Postgres tests, not in the variant).
- **Merge and deploy:** phases 1 and 2 must still not merge or deploy before the phase 3 review.
