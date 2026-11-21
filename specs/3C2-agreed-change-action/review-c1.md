# 3C2 review, commit 1 (discovery, W5)

Reviewer: Claude (fresh, did not author the work), 2026-11-21. Branch `task/3C2-agreed-change`, head `44c01781a`,
worktree `/opt/assetecon/AssetOpsV1-3c2`. Diff read: `git diff 166942e7d...44c01781a`, narrowed to 3C2's files (the
range also carries main's DS3, 3B6, 4a and 0K1 merges via `0c342a260`; those were not reviewed here).
Judged against spec rev 3, rulings D-3C2.1 to D-3C2.15, reviewer guide rev 2, packet, handoff, MB1.

## Summary (round 1)

- **Verdict: ACCEPT WITH FIXES** (two Medium, F1 and F2, fixed on the branch before merge; three Low).
- The code matches the spec: rule order §2.3, owner cover by `OWNER_COVER` over held grants, one clock read, the
  re-run before the due check, the lock plus the index catch, tenant-scoped reads, no S6-01a table touched, no served
  text beyond argparse chrome. Forged requests of my own were all refused (below).
- D-3C2.15 holds: the agreed block is appended to `actions/composition.py` and calls no S6-01a code;
  `agreed_composition.py` is a two-line re-export importing no adapter; DDR G10's call works (test 8).
- **F1 (Medium):** 0069's TRUNCATE trigger breaks `test_pg_harness.py::...truncate_cascade_reaches` (I ran it: 1
  failed) and the harness's `ASSETOPS_TEST_CLEANUP=truncate` mode. The packet says truncate mode "already" refuses
  on `chain_input_change`; on main it does not.
- The held guard block is minimal, changes no existing rule, and is **required**: without it the persistence guard
  fails four times on the agreed adapter (run below). The packet's line saying `42de02e06` "is not on this branch"
  is wrong (L1): it is on the branch, and that is why check-all is green.
- **F2 (Medium):** no test proves the adapter's reads are tenant-scoped; two plants of mine (tenant filter removed
  from `for_tenant` and from `site`) pass every 3C2 test.
- Plants: 14 unit plants and 6 guard plants all caught; 2 Postgres plants not caught (F2). P7/P21/P24/P25 not rerun.

## Owner paragraph (the held guard change, `42de02e06`)

The held change (30 lines in `tools/checks/configuration-persistence.ps1`) adds one rule to the check that
watches which code may write to the database: only the new agreed-change store may write the `agreed_action` table,
it may do so with one plain INSERT only, and no code anywhere may update, delete or empty that table. It is copied
from the blocks earlier stores got (3C0a accounts, 3B7a snapshots) and changes no existing rule: every line is new,
and the one edit to a shared list adds the new store on its own line, as each earlier store was added. It is needed:
I ran the check with the block removed and it fails four times on the new store ("database driver imported" three
times and "a second product database writer"), so 3C2 cannot merge as built without it. I also checked that it
catches what it should: an UPDATE in the store, an upsert, an INSERT from another module and a TRUNCATE elsewhere were
each refused. **Recommendation: approve.** Declining would mean redesigning where 3C2 writes, not trimming the
check.

## Findings

### F1 (Medium, blocking; regression) The TRUNCATE trigger breaks the harness's cascade proof and its truncate mode

- **Where.** `backend/migrations/versions/0069_agreed_action.py:53-54` (the trigger, correct per D-3C2.13) against
  `backend/tests/test_pg_harness.py:163` and `backend/tests/pg_harness.py:400` and `:413-415`.
- **What.** `test_pg_harness.py::...::test_delete_cleanup_empties_exactly_the_tables_truncate_cascade_reaches` runs
  `TRUNCATE foundation_revision, source, gateway, asset, site_import, site, tenant CASCADE` (rolled back) to compare
  the cascade with the DELETE closure. The cascade now reaches `agreed_action` and its trigger raises: I ran the file
  on this head, 1 failed, 20 passed (`RestrictViolation: agreed_action rows are append-only`). The same happens to
  every S1-store module under `ASSETOPS_TEST_CLEANUP=truncate` (`pg_harness.py:415`), and the harness docstring's
  "no TRUNCATE triggers exist" becomes false. The packet and handoff say truncate mode "would refuse the same way (as
  `chain_input_change` already does)"; the harness test's roots do not reach `chain_input_change` on main, so this
  is new with 3C2.
- **Why it matters.** The merge-gate full suite fails; `select-tests` selects the whole suite for a migration, and
  the packet's regression set did not include `test_pg_harness.py` (see L2).
- **Fix.** Keep the trigger. In `test_pg_harness.py` run the rolled-back TRUNCATE under `SET LOCAL
  session_replication_role = replica` (the cascade notices are emitted before triggers; confirm the `cascaded` set
  still fills), do the same in `pg_harness.empty_tables`' truncate branch, and correct its docstring. Log the two
  files as a Known Deviation (outside spec §0's list, same reason as the 3C0a edit), correct the packet and handoff
  sentence, and rerun `test_pg_harness.py` on Postgres.

### F2 (Medium, blocking; missing test) Tenant scoping of the adapter's reads is not proven by any test

- **Where.** `backend/assetops_backend/actions/adapters/postgres_agreed_action_store.py:22` (`_SITE`) and `:40`
  (`_FOR_TENANT`'s `WHERE a.tenant_id = :t`); `backend/tests/test_3c2_agreed_actions_postgres.py` tests 7d and 8.
- **What.** The code is correct, but no Postgres test records an agreed Action, or looks up a Site, in a second
  tenant. Plants run through a pytest plugin on this head: `for_tenant` with the tenant filter replaced by a no-op,
  6 passed; `site` with the tenant filter replaced, 6 passed. The unit test's `for_tenant(w.other) == ()` exercises
  only the memory store.
- **Why it matters.** This read is what 5c shows a signed-in executive (unit 2); a lost tenant filter would show one
  operator another operator's agreed changes, and nothing would fail. The dispatch names tenant scoping as a check.
  (The `site` plant is partly backstopped by the `(tenant_id, site_id)` foreign key, but as exit 3, not
  `SITE_NOT_FOUND`.)
- **Fix.** In test 8 (or a new 8b), record one Action for `other-op` (Zara agrees, Zara owns, operator-wide) and
  assert Lakeside's read is unchanged and other-op's read holds only Zara's; in 7d assert `adapter.site(other_op,
  "KOBO-001") is None`. Show both plants failing in the packet.

### L1 (Low) The packet says the held guard commit is not on the branch

`packet.md`, "Checks after D-3C2.15": "The held writer block commit `42de02e06` is not on this branch, so its guard
lines are not exercised here." It is an ancestor of `44c01781a` and is the reason check-all's persistence guard
passes. Without it the guard fails four times. Correct the sentence so the owner is not told the build is green
without the block.

### L2 (Low) No `select-tests` output in the packet

Spec §5 asks for `select-tests` before review, and `backend/TESTING.md` asks the packet to cite it. With a new
migration it selects the whole suite. The full Postgres suite is not required by policy here, but the packet should
cite the selection and say which subset ran. That subset is how F1 was missed.

### L3 (Low) The accounts engine is not disposed

`actions/composition.py` `build_agreed_actions`: `dispose` closes only the agreed store's engine; the
`build_account_service(url)` store's pool stays open until the process exits. That is harmless for one command run.
For unit 2's long-lived 5c composition it is one more pool (BL-71's connection budget). Optional: dispose both.

### Checked and clean (not findings)

- Authority: `action.agree` is `(EXECUTIVE,)`; `created_role` from the creator's grants; creator tenant by slug and
  `active`; owner by tenant id, `active`, `owner_covers` over `(role, grant_site)`. Forged requests of mine, run
  against the service with the memory stores (12 cases): another tenant's slug with Lakeside's executive, Zara on a
  Lakeside Site, Zara naming Peter as owner, SQL in `--factor`, `%` as a Site code, U+200B and U+0085 in a title,
  2026-02-30, the technician and the analyst as creator: all refused with the right code. Email case folds to the
  same person. Zara's read of Lakeside is empty.
- D-3C2.1: the adapter's SQL names only `agreed_action`, `operator_account`, `site` (test 5); `agreed.py` imports no
  S6-01a module.
- D-3C2.15: the block is appended after S6-01a's code, calling none of it (imports and `__all__` lines added at the
  top, unavoidable). `agreed_composition.py` is a docstring, one import and `__all__`. Test 8 runs DDR G10's
  `build_agreed_actions(url).service.for_tenant(...)`.
- Migration 0069: byte-equal to spec §2.1, depends only on 0005, 0062 and site tables, so gate B changes
  `down_revision` and the hand pair only. Downgrade refuses with rows and never drops `ledger_append_only()`.
- 3C0a downgrade test: legitimate. The test empties account tables to reach 0062's downgrade, and the cascade now
  reaches `agreed_action`, whose trigger correctly refuses. Replica mode is scoped (`SET LOCAL`, reset before the
  next INSERT). It hides no product problem, since the real downgrade path goes through 0069's own refusal.
- 3C1a role test: still asserts `COMMAND_ROLES == SPEC_ROLES` over the full table; only the work-route set excludes
  `action.*`, as it excludes `commercial.*`. Nothing is weakened.
- No served text: refusals are bare codes, state is `OPEN`/`OVERDUE`; argparse `help`, `description` and `epilog` are
  static chrome under SC-1 §3.8 (g).
- Merge with current `main`: conflicts only in `.ai/state/data.md` and `.ai/state/index-2.md` (docs). Gate B still
  pending (3A7 not on main; main's head is `0067_source_profile`).

## Checks run (reviewer, this revision)

- `pwsh -NoProfile -File tools/check-architecture.ps1` (worktree): passed. `tools/check-agent-workflow.ps1`: passed.
- Unit: `test_3c2_agreed_actions.py` + `test_3c1a_person_work.py`: 201 passed.
- Postgres (`heavy-slot.sh --db`, `run-host-tests.ps1`): `test_3c2_agreed_actions_postgres.py` +
  `test_3c0a_accounts_postgres.py`: 23 passed. Downgrade and schema modules (3A6, 3A2, 3A1, 3B7a, UP1, CC schema,
  OUT-D1 schema, ANY-1, CH-1a): 103 passed. `test_pg_harness.py`: **1 failed**, 20 passed (F1).
- Guard, scratch copies of the head: with `42de02e06`, exit 0. Without it, exit 1 with four failures on the agreed
  adapter. Plants with the block: UPDATE in the adapter, ON CONFLICT upsert, INSERT from the account store, TRUNCATE
  from the Action store, an `INSERT ... SELECT` in a new module: all exit 1 with the expected message.
- Unit plants (scratch copy, each reverted): P1, P2, P12, P13, P18, P22, P23, P27, plus creator tenant ignored,
  owner tenant ignored, title not stripped, factor-known check skipped, Site-scoped executive grant counted: all
  caught.
- Postgres plants of mine (pytest plugin, no file edits): two tenant-filter plants, neither caught (F2).
- Not rerun: the implementer's P7, P21, P24, P25. My scratch-tree attempt was refused by the slot pool, which pools
  only real checkouts. Reading tests 6, 7b and 7c, each asserts the mechanism directly; I accept the packet's
  results. Not run: the full suite (not required here), frontend (no UI).
- Residual risk the packet does not name: tenant leaks undetected until F2 lands; the accounts pool (L3); gate B and
  the docs merge conflicts still ahead. `R-AUTH` is stated in the packet.
