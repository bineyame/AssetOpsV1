# RC4-F1 rulings

Architect (Claude), 2026-11-20. Raised by the 3A3 handshake (R1, High) and the ON1 handshake (R4); applied by
`spec.md` rev 1.

## D-RC4F1.1 One function names the database a URL reaches; anything unclear is refused

- **Ruling.** `database_target(url, environ)` returns the host, port and database name exactly as libpq will reach
  them, and refuses (`DatabaseTargetUnclear`) a URL whose query holds any key outside a short allowlist
  (`connect_timeout`, `sslmode`, `sslrootcert`, `application_name`), whose host is missing or multiple, whose name is
  missing, empty or not a plain identifier, or an environment that sets any of `PGDATABASE`, `PGHOST`, `PGHOSTADDR`,
  `PGPORT`, `PGSERVICE`, `PGSERVICEFILE`. Reasons name keys and variables, never values.
- **Why.** `make_url(url).database` is the path's name, but the psycopg dialect lets the query's `dbname` win, an
  empty name falls to the environment, and libpq fills an absent host, port or name from `PG*` variables or a
  service file. RC4 must judge the database actually reached, and the only way to know it without connecting is to
  refuse every form in which the URL alone does not say it. An allowlist (not a list of known bad keys) keeps a
  libpq keyword added later out until reviewed. Refusing the six variables outright, rather than only when they could
  take effect, is one rule anyone can check by reading the environment; the demo strips them (D-RC4F1.2) so the cost
  is nil. Rejected: resolving the dialect's connect arguments at run time (it imports the driver into a pure check
  and still misses the environment); it is kept as the test's independent check instead.

## D-RC4F1.2 Every decision about a database by its name uses it (sweep)

- **Ruling.** `commercial_upload_settings` (3A2; reached by `create_app`), 3A3's `refuse_operator_database`, ON1's
  onboarding and `chain/backfill.py`'s protected-database check all decide on `database_target(...).name`;
  `postgres_commercial_store.database_name` is deleted; `tools/demo_combined.py` strips the six `PG*` variables from
  its children. RC4-F1 merges before 3A3.
- **Why.** W6: the hole is the class "deciding about a database from a name the driver may not use", and each place
  that decides must ask the same function or the hole reopens at the next caller. The backfill protects the
  walkthrough databases, not real data, but is product code with the same reading; one line. The walkthrough tools
  that guard their own scratch names build the URL from a `--db` name with no query, cannot reach an operator
  database, and are not demo-critical: queued as backlog `RC4-F1-tools`, not changed now.

## Mid-build answers (round 1)

Architect (Claude), 2026-11-20. Answers `mid-build-questions.md` Q1 to Q3; `spec.md` rev 2 applies them.

### D-RC4F1.3 (Q3) `database_target.py` is a named non-connecting reader in rule 8; the parse stays `make_url`

- **Ruling.** Option (a). `backend/assetops_backend/database_target.py` is added to `$pgReaders` in
  `tools/checks/configuration-persistence.ps1`, on its own line with the comment `# RC4-F1 (D-RC4F1.3): parses a URL
  with make_url only; never connects. The SQL-write refusal still applies to it.` The module keeps `from
  sqlalchemy.engine import make_url` exactly as built. A new test pins the admission narrow.
- **Why.** Rule 8's intent is that the driver is imported only where the guard names it, and every named module is
  still refused any SQL write; naming this file keeps both. Option (c) is rejected: the module's whole job is to
  agree with the dialect, and the dialect reads the URL through `make_url`; a hand parser is a second reading that
  can differ (percent-decoding, query tuples, bracketed hosts) and reopens the class this unit closes. Option (b) is
  rejected: rule 8 is global, so an `adapters/` path still needs a guard line, and adapter isolation (only a
  composition imports adapters) would then refuse its callers (`commercial/composition.py`, `chain/backfill.py`,
  3A3, ON1). The module belongs to no configuration domain, so rule 2 does not reach it.
- **Code it requires.**
  1. **Guard edit (coordinator; the implementer's session may not edit the guard):** the `$pgReaders` line above,
     appended after the CH-1a entry. Nothing else in the guard changes. check-all must then pass all 40.
  2. **Implementer, test 8** in `backend/tests/test_rc4f1_database_target.py` (`test_8_admission_is_narrow`): an AST
     scan of `database_target.py` finds exactly one import naming `sqlalchemy`, `psycopg` or `alembic`, and it is
     `ImportFrom(module="sqlalchemy.engine", names=[make_url])`; and no call whose name is `get_dialect`,
     `create_engine`, `create_connect_args` or `connect`.
  3. **Plant F9:** add `import psycopg` (or a `create_engine(...)` call) to the module: test 8 fails.
  4. `spec.md` §3 "no new guard" now reads "one guard line (D-RC4F1.3), no new guard".

### D-RC4F1.4 (Q1) The backfill refuses when either name is protected

- **Ruling.** Keep both, as built: with `url` set the URL's target name and the injected reader's own
  `database_name()` are both checked, and either protected refuses; an unclear URL exits 2 "not plain" before either.
  `test_ch2_backfill_cli.py` stays unchanged.
- **Why.** Strictly stronger than §2.2: the URL still decides (test 5 and plant F6 hold, since a reader answering
  `"other"` cannot admit a protected URL), and a reader that names a protected database is never overridden by a
  harmless-looking URL. Changing CH-2's fixture would weaken a merged regression for no gain.
- **Code it requires.** None beyond the build. The comment in `chain/backfill.py` cites `D-RC4F1.4` in place of
  "mid-build Q1". `spec.md` §2.2's backfill line is amended to say both names are checked.

### D-RC4F1.5 (Q2) Test 7 exempts one path, tied to backlog `RC4-F1-tools`

- **Ruling.** Confirmed, with one change: the exemption names the repo-relative path `tools/sweep-setup-cache.py`,
  not a basename, so a file of the same name elsewhere is still scanned. The companion test stays: when
  `RC4-F1-tools` fixes the tool, the companion fails and forces the exemption's removal in that same change.
- **Why.** §2.2 keeps the walkthrough tools out of this unit; an exemption that cannot outlive its reason is the
  honest form of that.
- **Code it requires.** `BACKLOG_TOOLS = frozenset({"tools/sweep-setup-cache.py"})`, compared against
  `path.relative_to(REPO).as_posix()` in `_sources()`. The backlog entry `RC4-F1-tools` gains "remove test 7's
  `BACKLOG_TOOLS` exemption and its companion test".
