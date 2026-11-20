# RC4-F1 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **3**.

## Q1 (§2.2 backfill vs the §4 regression `test_ch2_backfill_cli.py`) - answered (D-RC4F1.4)

- **Conflict.** §2.2 says a non-dry run with `url` set reads `database_target(url).name`, and the reader's name only
  with no `url`. `test_ch2_backfill_cli.py` (a named regression, outside §3's files) patches `database_url` to
  `postgresql://x/y` and injects readers whose `database_name()` is protected; with the URL alone deciding, its two
  `test_protected_databases_are_refused...` rows run on (store touched).
- **Built (default, strictly stronger).** The URL's target name decides as §2.2 says (test 5, plant F6), and the
  injected reader's own name is still checked too: either protected refuses. An unclear URL exits 2 "not plain".
  CH-2's tests pass unchanged.
- **Ask.** Keep both names (as built), or URL only with CH-2's fixture URL changed to a protected name?

## Q2 (§4 test 7 vs §2.2's backlog `RC4-F1-tools`) - answered (D-RC4F1.5)

- **Conflict.** Test 7 scans `tools` for `make_url(...).database`; `tools/sweep-setup-cache.py:28` holds one, and
  §2.2 says that tool is not changed here (backlog `RC4-F1-tools`).
- **Built.** Test 7 exempts that one file by name (`BACKLOG_TOOLS`); a companion test proves the scan sees its read
  (the scan's set is non-empty). Nothing outside §3 changed.
- **Ask.** Confirm the exemption; `RC4-F1-tools` removes it.

## Q3 (§2.1 module vs the persistence seam guard) - answered (D-RC4F1.3; guard edit by the coordinator)

- **Conflict.** §2.1 fixes `backend/assetops_backend/database_target.py` with `sqlalchemy.engine.make_url`, and §3
  says "no new guard"; `tools/checks/configuration-persistence.ps1` rule 8 refuses any `sqlalchemy` import outside
  its listed writers and `$pgReaders` (check-all: 1 of 40 blocking guards fails, on `database_target.py:15`).
- **Stopped.** The guard is not edited (a guard change is not this implementer's call) and no dynamic-import
  workaround is used. The module is built as §2.1 says; check-all stays red on this one guard until ruled.
- **Ask.** (a) add `database_target.py` to `$pgReaders` (no SQL; the write refusal still applies), or (b) move the
  module under an `adapters/` path and admit it there, or (c) parse the URL without SQLAlchemy (then test 2 is the
  only proof of agreement with `make_url`).
