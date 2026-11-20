# RC4-F1: the database a URL really connects to (fix unit, implementer spec)

Status: **in_review** (rev 2: mid-build answers), 2026-11-20. Decisions with reasons: `rulings.md` (D-RC4F1.1 to D-RC4F1.5). Questions during the
build: `mid-build-questions.md`. No separate handshake: the 3A3 handshake raised it (3A3 R1, ON1 R4) and this spec
answers it; a Sonnet reviewer may still ask before code (units of 2 or fewer, `.ai/ROLE_CONFIG.md`).

Architect (Claude). Lane A, a fix to merged code (3A2, `main` 6db81330a). **Merges before 3A3**; 3A3 and ON1 build on
it. Non-screen. **0.5 unit, one commit.** Review depth: discovery (W5), because it is the RC4 boundary (owner RC4: real
operator data only in its own database).

## 1. The hole (class, not instance)

RC4 is decided from the database name in `DATABASE_URL`. 3A2 reads that name with
`adapters/postgres_commercial_store.database_name(url)` = `make_url(url).database`. The psycopg dialect does not
connect to that name in every case (checked on the venv, no connection made):

| URL or environment | `make_url(...).database` | What psycopg is handed |
|---|---|---|
| `.../assetops_test?dbname=assetops_op_x` | `assetops_test` | `dbname=assetops_op_x` (the query wins) |
| `.../?dbname=assetops_op_x` | `''` (not `None`) | `dbname=assetops_op_x` |
| `...@/assetops_test` (no host) | `assetops_test` | no host: libpq takes `PGHOST` or the local socket |
| `...@h1,h2/assetops_test` | `assetops_test` | two hosts, tried in turn |
| `?service=x`, `?host=`, `?hostaddr=`, `?port=` | the path name | the query's target |
| `PGDATABASE`, `PGSERVICE`, `PGHOSTADDR`, `PGPORT` set | the path name | libpq fills or overrides from the environment |

So 3A2's switch-off check admits `.../assetops_test?dbname=assetops_op_x` (emulated or demo data written into an
operator database), and the switch-on check admits `.../assetops_op_x?dbname=assetops_test` (real data written
outside its own database). The class is **"deciding about a database from a name the driver may not use"**. The fix is
one function that names the target exactly as libpq will reach it, and refuses every URL or environment in which that
is not plain from the URL alone.

## 2. Rules

### 2.1 `database_target` (new module `backend/assetops_backend/database_target.py`)

Standard library plus `sqlalchemy.engine.make_url` only. No connection, no dialect import.

```python
DRIVERS = frozenset({"postgresql", "postgresql+psycopg", "postgresql+psycopg2"})
ALLOWED_QUERY = frozenset({"connect_timeout", "sslmode", "sslrootcert", "application_name"})
PG_TARGET_ENV = ("PGDATABASE", "PGHOST", "PGHOSTADDR", "PGPORT", "PGSERVICE", "PGSERVICEFILE")
NAME = re.compile(r"[A-Za-z0-9_]{1,63}")
OPERATOR_PREFIX = "assetops_op"                       # broad detection: any case
OPERATOR_DATABASE = re.compile(r"assetops_op_[a-z0-9_]{1,40}")   # strict admission (moved from composition.py)

@dataclass(frozen=True)
class DatabaseTarget:
    host: str
    port: int | None
    name: str

class DatabaseTargetUnclear(ValueError):
    def __init__(self, reason: str) -> None:       # reason: one of the codes below, plus a key or variable name
        super().__init__(reason); self.reason = reason

def database_target(url: str, environ: Mapping[str, str] | None = None) -> DatabaseTarget: ...
def is_operator_name(name: str) -> bool: return name.lower().startswith(OPERATOR_PREFIX)
```

`database_target`, first failure wins (`environ` defaults to `os.environ`):
1. `make_url(url)` raises: `URL_UNREADABLE`.
2. `drivername` not in `DRIVERS`: `DRIVER_NOT_POSTGRES`.
3. Each query key: not in `ALLOWED_QUERY` is `QUERY_KEY <key>`; an allowed key given twice (a tuple value) is
   `QUERY_REPEATED <key>`. (An allowlist, so a libpq keyword added later is refused until reviewed.)
4. `host` `None` or `""`: `HOST_MISSING`; a `,` in `host`: `HOST_MULTIPLE`.
5. `database` `None` or `""`: `NAME_MISSING`; not `NAME.fullmatch`: `NAME_NOT_PLAIN` (so a name holding `=`, a space
   or a URL, which libpq could expand, is refused; `make_url` has already percent-decoded it).
6. Each variable of `PG_TARGET_ENV` present in `environ` with a non-empty value: `ENVIRONMENT <VARIABLE>`.
7. Return `DatabaseTarget(url.host, url.port, url.database)`.

The reason never holds a value from the URL (it may hold a password); only a key or variable name.

### 2.2 Every RC4 decision uses it (the sweep, D-RC4F1.2)

- `commercial/composition.py` `commercial_upload_settings(database_url)`: `None` stays "no database" (as today).
  Otherwise `target = database_target(database_url)`; `DatabaseTargetUnclear` raises
  `ConfigurationError(f"DATABASE_URL must name one database plainly ({e.reason}).")` whatever the switch says. Then
  today's rule on `target.name`: switch on needs `OPERATOR_DATABASE.fullmatch(name)`; switch off needs
  `not is_operator_name(name)`. `_OPERATOR_DATABASE` is deleted from the composition (imported from
  `database_target`). `create_app` reaches this through its first line (unchanged).
- `adapters/postgres_commercial_store.database_name` is **deleted** (its one caller is the composition). 3A3's
  `refuse_operator_database` and ON1's onboarding use `database_target` (their specs rev 2 say so).
- `chain/backfill.py` (same class, protects the walkthrough databases, not RC4): on a non-dry run with `url` set, the
  protected check reads `database_target(url).name` and also the injected reader's `database_name()`; either
  protected refuses (D-RC4F1.4); `DatabaseTargetUnclear` prints `Database URL is not plain
  (<reason>); nothing was written.` and returns 2. With an injected reader and no `url`, `reader.database_name()` as
  today.
- `tools/demo_combined.py` `Demo.env()`: after `out = dict(os.environ)`, pop every `PG_TARGET_ENV` name (a literal
  tuple in the tool, equal to the backend's; test 6 compares them). The demo sets its own `DATABASE_URL`, so a `PG*`
  variable in the coordinator's shell can neither redirect it nor stop it with rule 6.

Not changed here (same class, lower stakes, queued as backlog `RC4-F1-tools`): the walkthrough tools that guard
their own scratch database names (`tools/s3*`, `s4*`, `s6*`, `s7*`, `w5*`, `sweep-setup-cache.py`,
`dd1a2_mill3_dry_run.py`, `mechanism_dataset.py`). They build their URL from a `--db` name with no query, so the
query hole needs a hand-edited URL; none can reach an operator database or real data.

## 3. Code

| File | Holds |
|---|---|
| `backend/assetops_backend/database_target.py` | §2.1 (new) |
| `backend/assetops_backend/commercial/composition.py` | settings through `database_target`; `_OPERATOR_DATABASE` removed |
| `backend/assetops_backend/commercial/adapters/postgres_commercial_store.py` | `database_name` deleted |
| `backend/assetops_backend/chain/backfill.py` | the protected check (§2.2) |
| `tools/demo_combined.py` | `env()` pops `PG_TARGET_ENV` |

No migration, one guard line (`database_target.py` in rule 8's `$pgReaders`, D-RC4F1.3; the coordinator adds it), no
new guard, no message catalogue change (the settings refusal is a start-up `ConfigurationError`).

## 4. Tests (no database; every URL uses host `rc4.invalid` port 1 except where the host is the point)

`backend/tests/test_rc4f1_database_target.py`:
1. **Admitted:** `postgresql+psycopg://u:p@rc4.invalid:1/assetops_test`, the same with `?connect_timeout=2`,
   `?sslmode=disable&application_name=x`, `postgresql://u:p@rc4.invalid/assetops_op_pilot1` (port `None`),
   `.../assetops%5Fop_x` (name `assetops_op_x`). Each returns the expected `DatabaseTarget`.
2. **Agreement (independent check, W2):** for each admitted URL of test 1,
   `make_url(u).get_dialect()().create_connect_args(make_url(u))[1]` has `dbname == target.name` and `host ==
   target.host` (the dialect is instantiated, never connected).
3. **Refused, one per reason** (each asserts the reason exactly): `not a url` (`URL_UNREADABLE`); `sqlite:///x.db`
   (`DRIVER_NOT_POSTGRES`); `.../assetops_test?dbname=assetops_op_x` (`QUERY_KEY dbname`); `?service=op`
   (`QUERY_KEY service`); `?host=other` (`QUERY_KEY host`); `?hostaddr=10.0.0.1` (`QUERY_KEY hostaddr`); `?port=5`
   (`QUERY_KEY port`); `?options=-csearch_path%3Dx` (`QUERY_KEY options`); `?connect_timeout=2&connect_timeout=3`
   (`QUERY_REPEATED connect_timeout`); `postgresql+psycopg://u:p@/assetops_test` (`HOST_MISSING`);
   `...@h1,h2/assetops_test` (`HOST_MULTIPLE`); `.../?dbname=assetops_op_x` (`QUERY_KEY dbname`: rule 3 before 5);
   `postgresql+psycopg://u:p@rc4.invalid:1/` (`NAME_MISSING`); `postgresql+psycopg://u:p@rc4.invalid:1`
   (`NAME_MISSING`); `.../dbname%3Dassetops_op_x` (`NAME_NOT_PLAIN`); `.../assetops test` (`NAME_NOT_PLAIN`); a plain
   URL with `environ={"PGDATABASE": "assetops_op_x"}`, then each other `PG_TARGET_ENV` variable alone
   (`ENVIRONMENT <VAR>`); `environ={"PGDATABASE": ""}` is admitted. Every URL in this test uses the password
   `s3cret`, and no reason contains it.
4. **Settings matrix** (extends 3A2's `test_8`, same `_env` helper, in this file): switch off with
   `.../assetops_test?dbname=assetops_op_x`, `.../?dbname=assetops_op_x`, `.../` (empty name) and `PGSERVICE=x` set:
   each `ConfigurationError` "DATABASE_URL must name one database plainly"; switch on with
   `.../assetops_op_x?dbname=assetops_test`: the same; 3A2's `test_8_settings_allowed` and `_refused` rows still pass
   unchanged (they are re-run, not copied).
5. **Backfill:** `chain.backfill.main` with `DATABASE_URL` `.../assetops_polish_full_test?connect_timeout=2` and a
   stub reader whose `database_name()` answers `"other"`: not dry run, exit 2 "read-only" (the URL decides, not the
   reader); with `.../x_test?dbname=assetops_polish_full_test`: exit 2 "not plain".
6. **Demo:** `tools/demo_combined.py`'s `PG_TARGET_ENV` tuple equals `database_target.PG_TARGET_ENV`; `Demo.env()`
   (built as `backend/tests/test_demo_combined_links.py` builds its `Demo`) with `PGDATABASE`, `PGHOST`,
   `PGSERVICE` set by `monkeypatch` holds none of the six names.
7. **No caller left:** an AST scan of `backend/assetops_backend` and `tools` finds no `make_url(...).database`
   attribute read and no import of `database_name` from `postgres_commercial_store`. One exemption, by path:
   `tools/sweep-setup-cache.py` (backlog `RC4-F1-tools`), with a companion test that the scan sees its read (D-RC4F1.5).
8. **Narrow admission (D-RC4F1.3):** `database_target.py`'s only driver import is `from sqlalchemy.engine import
   make_url`, and it calls no `get_dialect`, `create_engine`, `create_connect_args` or `connect`.

Regression beside them: `test_3a2_commercial_upload_api.py` (all), `test_3a2_commercial_upload_service.py`,
`test_ch2_backfill_cli.py`, `test_demo_combined_links.py`, check-all. No Postgres file is needed: nothing connects.

## 5. Planted violations (plant, run, revert; each must fail)

| # | Plant | Must fail |
|---|---|---|
| F1 | Drop the query allowlist (rule 3) | 3 (`dbname`, `service`, `host`, `hostaddr`, `port`, `options`), 4 |
| F2 | Treat `""` as a present name | 3 (`NAME_MISSING` slash case), 4 (`.../`) |
| F3 | Skip the environment rule 6 | 3 (`ENVIRONMENT`), 4 (`PGSERVICE`) |
| F4 | Keep `make_url(url).database` in `commercial_upload_settings` | 4, 7 |
| F5 | Drop the host rule 4 | 3 (`HOST_MISSING`, `HOST_MULTIPLE`) |
| F6 | Backfill reads `reader.database_name()` when `url` is set | 5 |
| F7 | `Demo.env()` keeps `PGDATABASE` | 6 |
| F8 | Drop `NAME.fullmatch` | 3 (`NAME_NOT_PLAIN`) |
| F9 | Add `import psycopg` to `database_target.py` | 8 |

## 6. Done (questions; each can fail)

1. Does `database_target` name exactly the database the psycopg dialect is handed for every admitted URL (tests 1,
   2), and refuse every unclear URL or environment with its reason and no secret (test 3)?
2. Does every RC4 decision on `main` go through it, with `database_name` gone (tests 4, 7)?
3. Does the backfill's protection use the same target, and can the demo never inherit a `PG*` target (tests 5, 6)?
4. Does each plant of §5 fail its named test, and is nothing changed beyond §3's files and the test file?

Packet: `specs/RC4-F1-database-name/packet.md` (module paths, plant runs, mid-build count).
