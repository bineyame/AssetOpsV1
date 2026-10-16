# S3-02a review - selected-assessment capability and claim-limit read

Reviewer: fresh independent Claude reviewer (did not author the slice). Revision reviewed: `f9d02d9e` (head of `task/S3-02a-capability-read`; last code change `37343acc`). Diff: `git diff dee54c8b..f9d02d9e -- ':!.agent'`.

## Verdict: RETURN

One Medium finding (F1) blocks: a window-scope read of a non-current revision still carries per-interval positive ceilings at the top level of `claim_limit`. The rest of the slice is sound: refusal order, the closed-gate 409, the identity seam, exact spans, currentness, the single snapshot, no new writer, and a callable fixture. F1 is a small fix on the branch plus one test.

## Findings

### F1 - Medium - non-current window revision exposes positive interval ceilings
`backend/assetops_backend/analytics/claim_limit_read.py:309-311, 340-341`

`claim_limit["interval_ceilings"]` is attached whatever the currentness is. Each item carries `ceiling` and `support` from `interval_ceiling(...)`, and nothing marks the item as historical. I ran a scratch probe against the fixture. For the stale-selection window revision (currentness `FAILED` at that point) and for the withdrawn late-revision window revision (`HISTORICAL`), both reads returned `claim_limit.ceiling: null` and `historical_ceiling.ceiling: null`, and both still had `interval_ceilings: [{"ceiling": "CANDIDATE_AVOIDABLE", "support": "COMPLETE", ...}]` at the top level of `claim_limit`. The acceptance contract says that pending, failed, stale or changed selection produce no current positive claim, and that a prior revision is read as historical only. The Architect's ruling `D-2026-10-16-s302-capability` says the same. The handoff (`.agent/S3-02a-handoff.md:17`) documents `interval_ceilings` with no currentness caveat, so S3-02b would most likely render these as live Candidate ceilings. `test_window_revision_lists_each_interval_without_a_single_ceiling` reads only a CURRENT window revision, so no test covers this path. The M3 mutation (`current = True`) would not catch it either.

Fix: when `currentness != CURRENT`, move `interval_ceilings` into `historical_ceiling`, or null their `ceiling`/`support` at the top level. Then add a test that reads the stale-selection and the withdrawn late-revision window revisions and asserts that no positive ceiling appears outside `historical_ceiling`. Update the handoff line.

### F2 - Low - window-scope `support` mixes vocabularies
`claim_limit_read.py:313`

For a window revision, `support` is set to `revision["claim_level"]`, which is `COMPLETE`, `LIMITED` or `INDETERMINATE` (`dispatch_v3.py:69-71`). The documented `support` vocabulary is `COMPLETE|LIMITED|NONE`, with the meaning "support for the ceiling". This value is the window claim level. Use a separate key, such as `window_claim_level`, or `NONE`.

### F3 - Low - D3 text matching has no drift guard, and unlabelled unknown text is ignored rather than failed closed
`claim_limit_read.py:47-53, 85-96`

Labelled unknown text fails closed to MISSING. I confirmed this with a probe: an injected `Battery state of charge: brand new problem` gave SOC `MISSING` and support `LIMITED`. Text without a known role-label head is dropped. An injected `something new the rule does not know` inside the Candidate segment left the ceiling `CANDIDATE_AVOIDABLE` / `COMPLETE`, with no reason. Under the pinned `dispatch-3.2` vocabulary this is safe:
- Every point role is always looked up (`dispatch_v3._evaluate` takes PV, DIS and SOC unconditionally), so a problem-free role is genuinely covered.
- The unlabelled texts the model emits are model-limit strings, which appear only on Indeterminate segments, or the `generator state not observed` string, which is handled by the `observed` flag.

`SUPPORTED_MODELS` refuses other model versions. D3 is therefore acceptable as built. What it lacks is a unit test that pins `_PROBLEM_STATUS` to `dispatch_v3._PROBLEM_TEXT` and `LABELS`, so that a text edit without a model bump fails CI rather than silently changing coverage.

### F4 - Low - the Necessary rule basis ignores the binding
`claim_limit_read.py:197`

The rule always requires `(LOAD, PV, DIS)` for Necessary. The `BATTERY_AT_RESERVE` / `BATTERY_NEAR_RESERVE` branch (`dispatch_v3._evaluate`) depends on LOAD, PV, SOC and the reserve control, not on DIS. This fails in the conservative direction: it can withhold a valid Necessary when DIS is missing. It never grants an unsupported one. Choosing the needed roles from the segment `binding` would make the rule exact.

### F5 - Low - D2 means no ingested Necessary case exists for S3-02b
`backend/tests/test_s3_claim_limit_postgres.py:165-192`

Necessary, open bound, cohort, configuration and absent lineage are proven by mutating a real snapshot. That is acceptable proof of the read's logic. However, the manifest that S3-02b's walkthrough uses has no ingested Necessary interval, so the walkthrough cannot show a Necessary ceiling from public evidence. This should be stated in the S3-02b packet.

## Focus items judged

- **Refusal order** (`claim_limit_api.py:46-85`). The order is identity 401/403, then Site scope 404, then 503 with no DB, then 422 request validation, then the gate 409, then the read refusals. This matches `performance_api.open_scope` and the Finding seam. The router's default gate is `finding_api.no_gate` (closed), so it fails closed if wiring is omitted. `main.py` passes `performance_gate`. A closed gate returns 409 `PERFORMANCE_CUTOVER_CLOSED` with `capability`/`claim_limit` null, whether or not a revision is given. This is tested in `test_closed_cutover_gate_is_409_never_unassessed`. A malformed request returns 422 ahead of the gate, which leaks nothing.
- **401/403/404.** These go through `finding_api.Access` / `development_access`, and `test_identity_boundary` covers them. A foreign Site's revision is 404, because `_revision_detail` filters on tenant and Site.
- **Exact spans.** Spans merge only when they are adjacent and have the same status (`:136`). POOR_QUALITY and CONFLICTED subspans are kept between COVERED spans, and the test proves it. A missing or conflicted subspan cannot collapse into a positive claim, because `interval_ceiling` withholds when any role needed by the claim-carrying segment is not COVERED. The model makes the ends of a Candidate segment both Candidate, which gives two-point coverage.
- **Current vs historical.** For interval scope this is correct: `currentness` is CURRENT only when the exact revision is in `snap.run.revisions` and `derive_status` is CURRENT. Otherwise `ceiling`, `support`, `supported_minutes` and `statement` are null and only `historical_ceiling` is set. With no revision, the read is UNASSESSED with no ceiling. Window scope has the exception in F1.
- **One REPEATABLE READ snapshot.** `claim_limit_snapshot` runs `_window` and `_revision_detail` on one connection inside `_snapshot` (REPEATABLE READ). The extracted helpers are the same SQL as before.
- **Rule 8.** The diff adds no INSERT, UPDATE or DELETE, only moved SELECTs. The architecture guard passes.
- **Fixture.** `s3_claim_limit_records.build(runner, url)` is callable in-process and returns the ID manifest. D1 (S4 `CaseRunner` path instead of the TLS producer DB) is acceptable: it is still sealed Batch V2 through S2 ingestion and the real worker, with no simulator truth.
- **Residual: generator-state evidence is matched by time** (`claim_limit_read.py:105`). The window is inclusive at both ends, so a status report at a shared segment boundary is listed under both adjacent segments. Generator readings outside the revision's own pinned set are not matched for interval scope. This affects only the displayed Evidence IDs. GEN status comes from the segment's `observed` flag, so it cannot create coverage or a ceiling. It is acceptable for now. S3-02b should not present GEN IDs as exact per-segment attribution.

## Checks run (this reviewer, at `f9d02d9e`, private DB `assetops_s302arev_test`, serial)

- `pytest backend/tests/test_s3_capability_read_postgres.py backend/tests/test_s3_claim_limit_postgres.py -q`: 24 passed, 39.2 s.
- `pytest backend/tests/test_s3_dispatch_read_postgres.py backend/tests/test_s3_performance_cutover.py -q`: 36 passed, 39.3 s.
- Scratch probes (scratchpad only, not committed), run against the module fixture: they confirmed F1 and the F3 behaviour.
- `tools/check-architecture.ps1`: it first failed because Rule 8 could not find a Python interpreter (the worktree has no `.venv`). It passed with `ASSETOPS_GUARD_PYTHON` set to the main venv.
- `tools/check-agent-workflow.ps1`: passed.
- I did not rerun the full suite. The implementer's run at `37343acc` gave 2412 passed, 0 failed, 0 skipped, 17:30. The later commits touch only `.agent` and the packet, so the run applies to the reviewed code.
- Not run: `tools/writer_guard_probes.py`. I relied on the packet's `--seam` exit 0, and the diff adds no writer. No frontend changes are in scope.
- The private DB was dropped afterwards.
