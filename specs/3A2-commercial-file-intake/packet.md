# 3A2 packet: file intake of an operator's exports

Implementer (Claude, fresh), 2026-11-20. Branch `task/3A2-commercial-file-intake` off `main` `6014ddedc`, worktree
`/opt/assetecon/AssetOpsV1-3a2`. Spec rev 2, rulings D-3A2.1-16. Not merged. Evidence: `/opt/assetecon/evidence/3A2/build-1/`.

## Commits (4 units)

`f1c6c8281` unit 1: migration 0065 (`down_revision 0064_person_on_work`), rows, the scrubbed adapter, basis and Site scope.
`95461c74e` unit 2: pseudonyms, key files, readers, `uploads.py`, settings, words; service and Postgres tests.
`a8298dedf` unit 3: routes, `COMMAND_ROLES`, `create_app` settings check and mount; API tests.
`31f09bb42` unit 4: guard block, mid-build questions, state entry, spec status. (This packet is a fifth, docs-only commit.)

## Module paths (PYTHONPATH = worktree backend, backend/tests, contracts, simulator, gateway, field, host, tools)

`assetops_backend` and `assetops_contracts` load from `/opt/assetecon/AssetOpsV1-3a2/...`. `fixtures.__file__` is
`None` (a namespace package); its first `__path__` entry is the worktree's `backend/tests/fixtures`
(`module-paths.txt`).

## Done (spec §8)

| # | Answer | Shown by |
|---|---|---|
| 1 | Yes: check, submit, accept; nothing in the store before accept; one transaction | svc 1, 2; PG 2 (atomic) |
| 2 | Yes: the §3.4 table; a bad ref keeps 2a's code | svc 3, 4 (hand goldens), 5 |
| 3 | Yes: a refused row never sinks the file; row and field in words | svc 8, 9, 22 |
| 4 | Yes: own month; v2 is REVISED and supersedes | svc 7 |
| 5 | Yes: roles; a person always required; another tenant gets the byte-equal 404 | API 1-3 |
| 6 | Yes, both directions, and `create_app` refuses first | svc 10; API 8 |
| 7 | Yes: 17 + 8 codes worded; no value or ref in answers, rows or errors | svc 3, 15; API 6, 7; PG 4, 7 |
| 8 | Yes: guard and lock proof fail on plants; stale accept refused | plants below; svc 19, 20 |
| 9 | **No, by two lines.** The diff also has `commercial/adapters/file_key_store.py` (inside `commercial/**`) and the guard's `commercial` domain entry outside the writer block | mid-build Q1 |

## Tests (`rev a8298dedf`; code unchanged since)

- No database: `test_3a2_commercial_upload_service.py`, `..._api.py`, `test_3a1_commercial_service.py`,
  `test_3c1a_person_work.py`, `tools/checks/test_estate_guard.py`: **244 passed**, 597 s, rev `31f09bb42` (`nodb.log`).
- Pooled `heavy-slot.sh --db`: `test_3a2_commercial_upload_postgres.py` **39 passed, 0 skipped**, wall 358 s, most of it
  waiting for a slot (`pg-3a2.log`). Regression `test_3a1_commercial_postgres.py`, `test_3c0a_accounts_postgres.py`,
  `test_pg_harness.py`: **46 passed**, 24 s (`regression-db.log`).
- `select-tests --base main`: **full** (main.py, migration), so the focused set plus the regression set above
  stands in for it. The full suite was not run.
- `check-architecture.ps1`: passed (`arch-clean.log`). Fast check-all at `31f09bb42`: "All 41 guards passed", 259 s (`check-all-2.log`).

## Plants (each applied, run, reverted in a detached copy at HEAD; logs `plants-*.log`, `guard-*.log`)

All fail their named tests: V1 (svc 3), V2 (5), V3 (10), V4 (API 2 and `SPEC_ROLES`), V5 in memory (12) and in the
adapter (PG 3: the second accept ends `UploadStale` and not `UploadAlreadyDecided`; that is the negative lock run),
V6 (1, 2), V7 (8, 9), V8 (PG 4, 7: a `DataError` leaves raw), V9 (the guard: `INSERT INTO commercial_upload` in
`uploads.py`, and `UPDATE commercial_upload_decision` in the adapter; the clean guard passes with the under-lock
SELECT, and the old guard refuses the new INSERTs), V10 (API 8), V11 (svc 3), V12 (19a, 19b), V13 (API 8), V14 (19b
only, as expected), V15 (20), V16 (21), V17 (22), V18 (API 9). P2: without `CASCADE`, 3A1's downgrade test fails with
"cannot truncate a table referenced in a foreign key constraint"; with it, the test passes.

## Mid-build questions: 2 (`mid-build-questions.md`)

- Q1: §4 put file I/O, `pathlib` and SQLAlchemy names where guard rule 8 refuses them. I followed the evidence-domain
  precedent: the key files are in an adapter, re-exported by composition, with `key_dir: str | None`, plus one
  guard domain-entry line. Awaiting a ruling.
- Q2: where `commercial_upload.summary` is served (not served now), and which words the access 401/403 carry
  (`person_required`/`role_required`).

## Known deviations and residuals

- Q1 placement above. Process: the brief said tests first. I drafted the code before the tests in the same
  session, and the plants are what prove each test can fail.
- Check-all needs `frontend/node_modules`. The fresh worktree had none, so the first run failed 2 guards
  (`typescript` not found). I linked main's (untracked, git-ignored) for the second run.
- Owner queue Q1, Q2 and Q6 are on their defaults. Residuals (R4): a real export labelled `source-emulated`, and
  writers other than this route. The coordinator creates the demo tenants' keys (Q5) with
  `python -m assetops_backend.commercial.pseudonym_key create`.
- `3A4` collision: whichever merges second decorates the other's methods with `_scrubbed` and reruns svc 21.

## Not verified

Full backend suite; a real `create_app` with a key directory against a database (only the refusal is tested);
the routes through `LocaleMiddleware` in another locale.

USER_REVIEW_REQUIRED: not for this unit (non-screen). Q1, Q2 and Q6 are owner-queue defaults.
