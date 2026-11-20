# RC4-F1 review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer (did not author). Branch `task/RC4-F1-database-name`, head `851cd14a6`, worktree
`/opt/assetecon/AssetOpsV1-rc4f1`, diff `main...HEAD`. Read: spec rev 2, rulings D-RC4F1.1-5, packet, mid-build
questions, 3A3 rulings R1, owner guard approval.

## Summary (round 1)

- **Verdict: ACCEPT.** Four Low findings (docs/bookkeeping drift); fix on the branch before merge if convenient,
  none blocks.
- `database_target` matches §2.1 rule for rule and order. 48 bypass probes run as unit calls (no connection), plus
  6 environment probes: **no URL or environment got through with a name different from the one psycopg is handed.**
  Every admitted probe was cross-checked against `get_dialect()().create_connect_args()`, and values carrying
  `dbname=` were checked through `psycopg.conninfo.make_conninfo` (quoted, `dbname` unchanged).
- Sweep: the only RC4 decision (`commercial_upload_settings`, reached from `create_app` line 346) and the backfill
  use `database_target`; `database_name` is deleted, with no caller left. Every backend engine is
  `create_engine(<same URL string>)`. No `psycopg.connect(DATABASE_URL)` in the backend.
- Guard: `$pgReaders` gains exactly one path (`$backendRoot/database_target.py`, matched by `-contains`, so exact
  path only) plus its comment line; nothing else in `tools/checks/` changes.
- Demo: `Demo.env()` pops the six names; `serve_env()` builds on `env()`; every child `Popen` uses one of the two.
- Tests: 136 passed, no DB. Architecture and agent-workflow checks pass.

## Bypass probes (all `database_target(url, {})`, host `rc4.invalid`, nothing connected)

Refused (reason): `?db%6Eame=` (QUERY_KEY dbname: keys are percent-decoded before the allowlist), `?DBNAME=`
(QUERY_KEY DBNAME), `?%20dbname=`, `?dbname%00=`, `?=x`, `#?dbname=` and `\n?dbname=` (QUERY_KEY dbname),
`assetops_test&dbname=…`, `;dbname=…`, `%3Fdbname%3D…`, `%00`, `%0A` and a trailing space (NAME_NOT_PLAIN), a 64-char
name (NAME_NOT_PLAIN; 63 admitted, so no server truncation), `host:1,2` and `h1:1,h2:2` (URL_UNREADABLE),
`:/db` with an empty port (URL_UNREADABLE), `///db?host=` (QUERY_KEY host), upper-case driver, `postgres://`,
`+asyncpg` (DRIVER_NOT_POSTGRES), and a leading space (URL_UNREADABLE). `PGDATABASE=" "` is refused.

Admitted, and the dialect agrees on name and host:
- `?dbname` and `?host=` with no value: `make_url` drops blank values, so the dialect never sees them.
- `?application_name=x%20dbname%3Dassetops_op_x`, `?sslrootcert=x'%20dbname=…`, `?connect_timeout=2%20dbname%3D…`,
  and a password `pw%20dbname%3D…`: psycopg quotes each value (`application_name='x\' dbname=assetops_op_x'`), so
  the `dbname` it hands libpq is still `assetops_test`.
- `u:p@w@host` (host `w@rc4.invalid`) and `dbname=…@host` as the user name: the parse is the same object the
  dialect uses.
- Host `%2Ftmp`, `rc4.invalid%2Cother`, `host%3Dx`, `' '`: `make_url` does not decode the host, so libpq gets a
  literal, unresolvable host name, not a socket path or a host list. A real socket path (`@/tmp/db`) parses as
  host-missing plus `tmp/db` and is refused. The name is exact in every case.
- `ASSETOPS_OP_X`: admitted as itself. libpq does not fold case, and the switch-off check still refuses it through
  `is_operator_name`.
- `PGSYSCONFDIR`, `PGOPTIONS`, `PGUSER`, `PGTARGETSESSIONATTRS` and lower-case `pgdatabase` are admitted. None of
  them can change the database: a service file is read only with a service name, and both `service` and `PGSERVICE`
  are refused. `PGOPTIONS` sets run-time settings, not the database. Lower-case variables are ignored by libpq on
  Linux.

No bypass found.

## Findings

1. **Low (acceptance gap, D-RC4F1.4 "code it requires").** `backend/assetops_backend/chain/backfill.py:182-183`:
   the comment still cites "(mid-build Q1)", though the ruling says it cites `D-RC4F1.4` instead. Fix: replace the
   reference.
2. **Low (docs drift).** `.ai/state/data.md` (new RC4-F1 section) still says spec rev 1, "Plants F1-F8" and "Open:
   mid-build Q3 … check-all red on it, unruled". In fact Q1-Q3 are ruled (D-RC4F1.3-5), F9 exists and check-all is
   green. Fix: update the section to rev 2, F1-F9 and the rulings, and drop Q1-Q3 from "Open".
3. **Low (docs drift).** `specs/RC4-F1-database-name/packet.md:3-5` header still reads "Spec rev 1; rulings
   D-RC4F1.1, D-RC4F1.2 … Q3 is open and leaves check-all red", and the Checks table shows the rev-1 red check-all.
   The final-run section below it contradicts this. Fix: update the header and mark the table as rev 1.
4. **Low (bookkeeping, D-RC4F1.5).** No backlog entry `RC4-F1-tools` exists anywhere (grep over `.ai`, `.agent`,
   `owner`, `specs` and `tasks` on main and on the branch finds it only in this spec and its rulings). The ruling
   says that entry gains "remove test 7's `BACKLOG_TOOLS` exemption and its companion test". The companion test
   still forces the removal mechanically, but the walkthrough-tools queue item is untracked. Fix: the coordinator
   adds the entry (it is probably the coordinator's file, not the implementer's).

Process note, not a finding: spec says "one commit"; the branch holds 1f0bdaa3b, a guard commit, a merge, a `wip`
commit (test file only) and 851cd14a6. Squash on merge if one commit is still wanted.

## Checks run (this review)

- PYTHONPATH `<wt>/backend:<wt>/backend/tests:<wt>/contracts:<wt>/simulator`. Module paths were verified: the
  three packages and `database_target.py` resolve under `/opt/assetecon/AssetOpsV1-rc4f1/`. Interpreter: main's
  `.venv` (SQLAlchemy 2.1.8, psycopg 3.3.9). `DATABASE_URL` was unset.
- `tools/heavy-slot.sh -- python -m pytest tests/test_rc4f1_database_target.py test_3a2_commercial_upload_api.py
  test_3a2_commercial_upload_service.py test_ch2_backfill_cli.py test_demo_combined_links.py -q`: **136 passed**,
  13.4 s. This matches the packet's 135 at rev 1 plus test 8.
- `check-architecture.ps1`: the first run failed only because the guard Python was missing (no `.venv` in the
  worktree). With `ASSETOPS_GUARD_PYTHON` set to main's venv: **"Architecture check passed."**
- `check-agent-workflow.ps1`: **passed**.
- Probes: the script lives in the scratchpad and was run as unit calls. It made no connection, and no reason
  contained the password.

Cited, not rerun (builder, same head 851cd14a6): 119 no-DB, 39 Postgres (`--db`, `assetops_test`), fast check-all
41/41, plants F1-F9 each failing its named tests. Plants were not re-applied. I read the plant table against the
tests, and each plant targets code that a test row pins.

## Could not verify

- The plants (not re-run), the Postgres 39 and the full check-all (cited).
- Behaviour against a real libpq connection: by design nothing connected. Agreement rests on
  `create_connect_args` plus psycopg's `make_conninfo` quoting.

## Residual risk the packet does not name

- **Test 7 is instance-shaped.** It catches `make_url(...).database` and the `database_name` import only. It does
  not catch `engine.url.database` (`chain/adapters/postgres_thread_sources.py:126` still reads the name that way;
  this is harmless here because the backfill now also checks the URL target), and it does not catch
  `u = make_url(x); u.database`. A future RC4-style caller written that way would pass test 7. Review must keep
  catching it, and 3A3/ON1 reviews should check that they call `database_target`.
- **Test 8 can be dodged.** It does not see `importlib.import_module("psycopg")` or `__import__`. Rule 8's text
  match in the guard remains the backstop.
- **Start-up only.** The `PG*` refusal is evaluated once, at start-up (`create_app`). libpq reads the environment
  at each connect, so a process that changes `os.environ` later is outside the check (no such code was seen).
- **Host is not checked beyond missing or multiple.** A literal host such as `' '` is admitted. RC4 is by name,
  so this does not affect the boundary.
