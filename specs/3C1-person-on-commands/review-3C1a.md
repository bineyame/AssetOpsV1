# 3C1a review: the signed-in person on work and domain commands

## Round 1 (discovery, W5): 2026-11-20, fresh Claude reviewer, head `03692e723`

**Summary (verdict: ACCEPT with Lows).**
- I found no High or Medium findings. All 10 commands (15 rows, counting each event kind) run `person_step` through
  `WorkGate.command_scope`. The actor is composed by the server, and a body carrying `actor` is refused with the
  route's own shape code. The gate principal and the entry principal are still required (R6). The tenant check
  answers the route's unknown-Site 404, built from the same literal.
- Today's path is unchanged. Every service change is guarded by `person is None`. Routers pass `person=` only on the
  person path. SERVICE hashes are byte-identical (builder `hashes-*.txt` compared with `cmp`: equal).
- The migration widens only what §4 names. All nine INSERT lists gain `person_id`, and no read list changes.
- Three Lows: (L1) the new migration test asserts "is head", which is the class Q1 just ruled out; (L2) renumber
  friction; (L3) one evidence line is mislabelled. I reran a real FK-drop plant: it is caught.

### Findings

**L1 (Low; class violation, not an acceptance gap).** `backend/tests/test_3c1a_person_work_postgres.py:150-151`.
- **What is wrong.** `assert MIG.revision == pg_harness.alembic_head()` and `MIG.down_revision ==
  "0062_operator_accounts"` both measure the head as if 0063 were the head.
- **Why it matters.** The Q1 ruling made "a migration test compares at its own revision, never at head" a checked
  class. This test will fail as soon as 3C1b's `action_event` migration, or any later one, lands. The literal also
  breaks on the D-3A1.12 renumber.
- **Fix.** Assert that the revision is in the script history and that it chains from its predecessor:
  `ScriptDirectory.get_revision(MIG.revision).down_revision == MIG.down_revision`, with the predecessor read from
  the script directory and not a literal. Drop the head equality, or keep it only as `MIG.revision` being an ancestor
  of the head.

**L2 (Low; renumber).** `backend/migrations/versions/0063_person_on_work.py:36-37` and
`backend/tests/test_3c1a_person_work_postgres.py:22`.
- **What is wrong.** `DOWNGRADE_REFUSED` and `DISCOVERY_FAILED` hard-code `0063_person_on_work`, and the test loads
  the module by a literal file name.
- **Why it matters.** When 3A1 merges first (its `0063_commercial_records` also revises `0062_operator_accounts`), the
  renumber must touch the file name, `revision`, `down_revision`, these two strings, test lines 22 and 151, and
  `.ai/state/work.md:141`. A missed string leaves a refusal message naming the wrong revision. The tests import the
  constant, so they would not catch that.
- **Fix.** Build both messages from `revision`, and have the test find the module by globbing `*_person_on_work.py`.
  3A1's tables do not overlap the nine tables, so the renumber is otherwise mechanical.

**L3 (Low; evidence accuracy).** `/opt/assetecon/evidence/3C1a/run1/plants-db.log`.
- **What is wrong.** The log line is "D4 tenant FK dropped: exit 0: 1 passed", but the packet says the plant was
  `NOT VALID`.
- **What I checked.** I reran a genuine drop (both the FK ADD and DROP removed from the migration). Two tests fail,
  `…every_table_has_the_column_the_fk…` ("domain_action_case_link") and
  `…refuses_a_person_of_another_tenant` ("DID NOT RAISE"), so the FK is covered.
- **Fix.** Relabel the log line, or note in the packet that D4 was malformed. No code change.

### Checklist (reviewer guide)

- **Scope (§7.6).** 24 files against `7e4acb3eb`: §4's code, the words, two new test files, the two Q1 test edits and
  bookkeeping.
- **No other test file.** Only `test_3c0a_accounts_postgres.py` (adds `CASCADE`) and
  `test_k2_fuel_records_postgres.py` changed among the existing tests. Both match Q1 exactly, no assertion is
  loosened, and the final `shape == up` stays.
- **Probes.**
  - P1, P2, P3, P5, P5b, P5c and P6 are covered per command row in `test_3c1a_person_work.py`.
  - P4 is covered by `test_each_table_refuses_a_planted_actor`.
  - P7: read lists are unchanged.
  - The admitting role follows table order (Tess, FT+SM, is admitted as FT on records).
- **Order.** Read access, then the Site 404, the write grant, store 503, the person (503/401), the tenant 404, the
  feature 403 and the role 403. The tenant check before the feature check means another tenant only ever sees "not
  found".
- **Other writers.** Only the two adapters write the nine tables. `authorize()` still refuses a client USER actor, so
  no existing writer can trip the new CHECK or the upgrade refusal.
- **Harness.** `pg_harness.empty_tables` follows the FK closure, so resets rooted at `operator_account` now also empty
  the nine tables. That is consistent with TRUNCATE CASCADE.

### Checks run (scratch worktree `.claude/worktrees/rev3c1a-r1` at `03692e723`)

- **Module paths.** `assetops_backend`, `assetops_contracts` and `fixtures` all resolve to the scratch tree.
- **No database.** `test_3c1a_person_work.py`, `test_w401_work_api.py`, `test_w502_domain_intent_api.py`,
  `test_own_g3_operational_entry.py`, plus the P8 pair `test_3c0a_accounts_api.py` and `test_3b1_structure_registry.py`
  (3B1 is already merged into the branch): **304 passed, 16 skipped**.
- **`check-architecture.ps1`.** Passed with `ASSETOPS_GUARD_PYTHON` set. Without it, the chain-structure guard
  reports no interpreter, which is environmental.
- **`check-agent-workflow.ps1`.** Passed.
- **Postgres plant**, through `heavy-slot.sh --db` on `assetops_test`: FK dropped gives 2 failed, as described under
  L3. The plant was reverted and the tree is clean.
- **Cited, not rerun:**
  - builder pg-new: 7 passed;
  - pooled regression: 503 passed, with 3 failures (2 are Q1, fixed afterwards: 25 passed after the merge; 1 is the
    r373 fixed date, which also fails on `main`);
  - sweep: 39 passed;
  - check-all: 40/40;
  - plants: 7/7 no-database, 3/3 database.
- **Revisions.** The run1 logs come before merge `0c545cb21` and the Q1 commit. Only the Q1 pair was rerun after
  them, so the full pooled list has not run at head.

### Not verified, and residual risk the packet does not name

- **Pooled regression at head.** I did not rerun the full pooled regression at `03692e723`.
- **The 3A1 renumber** is not exercised.
- **Body read before the gates.** `work_api.py:228`: `post_event` now reads the body before the access and Site
  gates, so an unauthenticated caller's body is parsed. The answer bytes are unchanged.
- **For 3C0b: unsigned callers can tell whether a Site exists.** The person step runs after the Site, grant and
  availability checks. Once the switch is on, an unsigned caller can still tell a real Site (403/503) from an unknown
  one (404) before the 401. Today has the same behaviour, and the spec orders it this way.
- **The 401 header.** `PERSON_REQUIRED` 401 carries `WWW-Authenticate: Bearer` (the route's `_refuse`), although sign-in
  is by cookie. This is cosmetic.
- **Nothing else depends on the switch being off.** `require_person()` is read only in `create_app`. D-3C1.3 paths
  (verification, financial, decision) are untouched by the diff.
