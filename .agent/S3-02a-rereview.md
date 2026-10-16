# S3-02a re-review - fix round 1

Reviewer: fresh independent Claude reviewer (did not author the slice or the fix). Revision: `00658f55` (head of `task/S3-02a-capability-read`). Diff: `git diff a96c6e35..00658f55`.

## Verdict: ACCEPT

F1 is closed, and no new blocking finding was raised.

## Prior findings

- **F1 (Medium): closed.** In `claim_limit_read.py:340-346`, `interval_ceilings` is now attached at the top level of `claim_limit` only when `current`. Otherwise it goes under `historical_ceiling.interval_ceilings`. When the read is not current, `historical_ceiling` is always a dict (`:336`), so that assignment cannot fail. When the read is not current, the top-level `ceiling`, `support`, `supported_minutes` and `statement` are null and `current_positive_claim` is false. All four non-current states (STALE_PROJECTION, FAILED, PENDING, HISTORICAL) go through the same `current` boolean. No other path emits per-interval ceilings, and the UNASSESSED path (`:250`) has neither key. A CURRENT read is unchanged. The new test `test_non_current_window_revisions_have_no_top_level_interval_ceilings` covers both the stale-selection and the withdrawn late-revision window revisions, and also asserts that the CURRENT window read keeps top-level `interval_ceilings` with `historical_ceiling` null. The samples test asserts the same absence on the two new samples.
- **F3 (Low): addressed.** `test_s3_claim_limit_vocabulary.py` pins `MODEL_VERSION == "dispatch-3.2"` and the exact `_PROBLEM_TEXT` code set. For each code it checks that the first matching needle, which is what `_status_of` returns, gives the expected status. If the text is edited without a model bump, the needle no longer matches and the test fails. A re-ordered or wrong needle also fails, because the test checks the expected status. The test is genuinely tied to `dispatch_v3`. `test_labels_map_to_roles` is close to a tautology, because `_LABEL_ROLE` is derived from `LABELS`. It is harmless, and label drift propagates automatically anyway.
- **F2 (Low): handoff accurate.** Window `support` is `revision["claim_level"]` (`:313`), which is COMPLETE, LIMITED or INDETERMINATE, as the handoff now says. It is shown only when the read is CURRENT. The handoff also correctly says it is a separate vocabulary from interval support.
- **F5 (Low): handoff accurate.** The note that no ingested case yields NECESSARY matches the fixture.
- **F4 (Low):** not addressed. It is conservative, as stated in the prior review, so it does not block.

## Fail-open check

The change only moves data from the positive (top-level) position to the historical position. It adds no new path that could set `ceiling`, `current_positive_claim` or top-level `interval_ceilings` when the read is not CURRENT.

## Note (non-blocking)

- `.ai/CODE_STATE.md:5635` still says "Window revisions list `interval_ceilings`" with no currentness caveat. The handoff is the S3-02b contract source and is correct. The CODE_STATE line can be aligned at closeout.

## Checks run (this reviewer, at `00658f55`, serial)

- `pytest backend/tests/test_s3_claim_limit_vocabulary.py backend/tests/test_s3_capability_read_postgres.py backend/tests/test_s3_claim_limit_postgres.py -q` ran on the private base DB `assetops_s302arr_test` (Docker Postgres 127.0.0.1:55432), using the main venv python with `PYTHONPATH` set to the worktree's `backend;contracts;gateway;simulator`. Result: 27 passed in 31.3 s. The first attempt errored on connection only, because the base DB did not exist yet. After I created it, the run was clean. The DB was dropped afterwards (`DROP DATABASE ... WITH (FORCE)`), and no `assetops_s302arr*` databases remain.
- `tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON` set to the main venv: passed.
- Not run: the full suite (not requested; the change is confined to one branch in the read and to tests), the adjacent S3 and Performance cutover tests (the packet reports 89 passed), and mutation checks (I relied on the packet's report). No frontend changes are in scope.
