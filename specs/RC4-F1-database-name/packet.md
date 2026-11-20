# RC4-F1 packet: the database a URL really reaches

Branch `task/RC4-F1-database-name`, base main `e88641e97`, one commit. Spec rev 1; rulings D-RC4F1.1, D-RC4F1.2.
`USER_REVIEW_REQUIRED: false` (non-screen security fix; no semantics change beyond refusing unclear URLs).
Mid-build questions: **3** (`mid-build-questions.md`); Q3 is open and leaves check-all red on one guard.

## Files

- `backend/assetops_backend/database_target.py` (new): §2.1 exactly (rules 1-7, constants, `is_operator_name`).
- `commercial/composition.py`: settings via `database_target`; unclear URL raises
  `ConfigurationError("DATABASE_URL must name one database plainly (<reason>).")` whatever the switch;
  `_OPERATOR_DATABASE` and `import re` removed.
- `commercial/adapters/postgres_commercial_store.py`: `database_name` and the `make_url` import deleted.
- `chain/backfill.py`: non-dry run decides on `database_target(url).name`; unclear prints "Database URL is not plain
  (<reason>); nothing was written." exit 2 (Q1: the reader's own name is still checked too).
- `tools/demo_combined.py`: `PG_TARGET_ENV` literal; `Demo.env()` pops it.
- `backend/tests/test_rc4f1_database_target.py`: tests 1-7 (test 4 asserts the reason too, so F2 fails it).

## Module paths

`PYTHONPATH=<wt>/backend:<wt>/contracts:<wt>/simulator`; `assetops_backend`, `assetops_contracts`,
`assetops_simulator` resolved to `/opt/assetecon/AssetOpsV1-rc4f1/...` (checked).

## Checks (revision = branch head)

| Run | Result |
|---|---|
| Tests first, callers unswitched | 9 failed (tests 4-7), 35 passed |
| No DB: RC4-F1 + 3A2 api/service + CH-2 backfill + demo links | 135 passed, 16.2 s |
| `heavy-slot.sh --db`, base `assetops_test` routed: 3A2 postgres/api/service + RC4-F1 | 157 passed, 85 s wall |
| `check-all.ps1` (fast) | **1 of 40 blocking guards fails**: configuration-persistence rule 8, `database_target.py:15: from sqlalchemy.engine import make_url` (Q3); 93.7 s |

## Plants (applied, run, reverted by `git checkout`; tree clean after)

| # | Failed |
|---|---|
| F1 | 11: test 3 (dbname, service, host, hostaddr, port, options, `/?dbname`), 4 (3 query rows), 5 |
| F2 | 2: test 3 `NAME_MISSING` slash, test 4 `.../` |
| F3 | 8: test 3 six `ENVIRONMENT` + default environ, test 4 `PGSERVICE` |
| F4 | 6: test 4 (5 rows), test 7 |
| F5 | 2: test 3 `HOST_MISSING`, `HOST_MULTIPLE` |
| F6 | 1: test 5 read-only row |
| F7 | 1: test 6 |
| F8 | 2: test 3 `NAME_NOT_PLAIN` (both) |
| F9 | 1: test 8 (`import psycopg` appended to `database_target.py`) |

## Known deviations

- Q1: backfill refuses if either the URL target or an injected reader names a protected database (CH-2 regression
  would otherwise fail; spec reads URL only).
- Q2: test 7 exempts `tools/sweep-setup-cache.py` (backlog `RC4-F1-tools`); a companion test proves the scan sees it.
- Q3 (ruled D-RC4F1.3): guard line added by the coordinator (a577af40b); test 8 `test_8_admission_is_narrow` pins the admission narrow (one driver import, `sqlalchemy.engine.make_url`; no `get_dialect`/`create_engine`/`create_connect_args`/`connect` call).
- Q2 (ruled): test 7 exemption names the full path `tools/sweep-setup-cache.py`.

## Review focus

Rule order and reasons vs §2.1; no URL value in any reason (test 3 password); Q1-Q3 rulings.

## Final run (rev 2)

No DB: RC4-F1 + 3A2 api/service 119 passed. `heavy-slot.sh --db`, base `assetops_test` routed: 3A2 postgres 39 passed. check-all (fast): all 41 guards passed (40 plus the estate self-test it triggered), 252 s.
