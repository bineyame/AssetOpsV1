# 3C1a packet: the signed-in person on work and domain commands

Implementer (Claude), 2026-11-20. Branch `task/3C1a-person-on-work` (the dispatch's name; spec §0 says
`task/3C1a-person-work`), worktree `.claude/worktrees/3c1a`, base `8c9af447b`. Not merged. `USER_REVIEW_REQUIRED`:
false for the slice; D-3C1.10 (Site manager records readings and completions) is the owner-visible deviation already
ruled.

## Commits

- `e1527f0e6` person step, `PersonActor`, migration `0064_person_on_work`, adapters, `create_app` wiring, both test files.
- `b1c90c80a` routers pass `person=` only on the person path (today's service calls are unchanged; found by the
  `test_own_g3_operational_entry.py` fake).
- Docs commit: state entry, index line, spec status, `specs/INDEX.md`, `mid-build-questions.md` Q1, this packet.

## Done (spec §7)

| # | Answer | Proof |
|---|---|---|
| 1 | Yes. All 10 commands (7 work routes, operational entry, 3 domain) run `person_step` via `WorkGate.command_scope`; actor composed by the server; gate/entry principal still required | `test_each_listed_role_is_admitted…`, `…body_carrying_an_actor…`, `…no_principal_composed…` (15 command rows each) |
| 2 | Yes: 403 `PERSON_ROLE_REQUIRED` + `params.roles`; other Site 403; other tenant = unknown-Site 404 byte for byte (body and headers compared against a scope that lacks the Site) | `…without_a_listed_role_or_at_another_site…`, `…another_tenant…` |
| 3 | Yes: same person, new session, 200 with the same body; second person, same key, the route's 409 | `…replays_after_signing_in_again…` |
| 4 | Yes, except Q1's two migration tests (below) and a pre-existing date failure | regression below; hash proof |
| 5 | Yes on all nine tables (CHECK and FK) | `test_each_table_refuses_a_planted_actor`, `…a_person_of_another_tenant` |
| 6 | Yes: only §4's files, the `# 3C1` words, the tests and the bookkeeping | `git diff --stat 8c9af447b..HEAD`: 16 files |

Interpretation, not a decision on anything open: inside the person step the tenant 404 comes before the feature 403.
This is the same order as today's unknown-Site 404 before the write refusals, so another tenant's person only ever
learns "not found". `PERSON_ROLE_REQUIRED` adds `params` to the work envelope, as spec §2 states. The words are
`person.person_required` and `person.person_role_required`.

## Tests (actual output; logs in `/opt/assetecon/evidence/3C1a/run1/`)

- No database, 12 files (new and regression, including `test_w401_work_api`, `test_w502_domain_intent_api`,
  `test_own_g3_operational_entry` and the 3C0a files): **360 passed, 16 skipped** (45 s). The new file alone: 147
  passed.
- New Postgres file: **7 passed** (38 s).
- Pooled regression, 38 files (spec §4's list, every test file naming the work or domain services or the accounts
  tables, plus the two new files): **503 passed, 3 failed** (23 min 46 s, `pg-regression.log`):
  - 2 failures are Q1 (stopped, see below);
  - `test_r373_request_access::test_mini_linked_request…` hits `WORK_OCCURRED_AT_TOO_OLD` because its fixed date,
    2026-10-18, is now more than 30 days old. It fails the same way on `main` 8c9af447b (`r373-main.log`).
- W6 sweep, the remaining migration tests on these tables (ch2, ch3, ch9b2, w402, w403): **39 passed**.
- Fast check-all: **all 40 guards passed** (82 s), including the architecture seams, configuration-persistence and
  agent-workflow.
- `select-tests --base main`: `full` (`main.py`, the migration). The full suite was not run (the coordinator schedules it).

## Hash identity (R1)

`hashes.py` sends 23 SERVICE commands (all nine tables, every event kind, the entry, the 3 domain commands) through
the services over the same fakes, once on `main` 8c9af447b and once on this branch. The output is identical: hash,
actor, attestation and basis (`hashes-main-base.txt` = `hashes-3c1a.txt`). Separately, the unit tests recompute the
SERVICE hash and the person hash `{kind:USER,id:person:<id>}` from B6.

## Gate proofs (R6, D-3C1.12)

For all 15 rows (10 commands, with each event kind as its own row), with no gate principal composed, or with the
entry principal off for the entry route, the unsigned request and the signed-in person both get 403
`WORK_WRITE_FORBIDDEN`. Today's client USER actor is still 403 `WORK_USER_AUTH_REQUIRED`. The switch is off by
default; `on` makes every command 401 `PERSON_REQUIRED`, through `create_app` too; any other value raises
`ConfigurationError`. With no account service there is no person. An account-store error is 503.

## Plants (each applied in a scratch worktree, then reverted)

No database (`plants-nodb.log`): session in the hash, feature switch bypassed, tenant check removed, Site manager
not bound to its Site, the role table widened, `actor` kept in the person shape, switch ignored. **All 7 fail.**
Database (`plants-db.log`): the actor_id coupling dropped, `person_id` dropped from an adapter INSERT, the upgrade
refusal removed. **All 3 fail.** A fourth database plant (the FK marked `NOT VALID`) passed. That plant was
malformed: `NOT VALID` still checks new rows, so it is not counted.

## Module paths

`assetops_backend` is `…/3c1a/backend/assetops_backend/__init__.py` and `assetops_contracts` is
`…/3c1a/contracts/assetops_contracts/__init__.py`. `fixtures` is a namespace package whose first entry is
`…/3c1a/backend/tests/fixtures`; the editable install also lists the main checkout's `host/fixtures` later on its
path.

## Mid-build questions: 1 (Q1)

Two older migration tests assumed their own migration was head. Ruled yes (rulings.md, Mid-build answers Q1); both
edited, and no other test file:

- `test_3c0a_accounts_postgres.py::test_downgrade_refused_with_an_account_then_down_and_up`: the one TRUNCATE now ends
  `CASCADE` (the referencing tables are empty; every assertion unchanged).
- `test_k2_fuel_records_postgres.py::test_migration_up_down_up_on_empty_table`: downgrade to 0054 first and take
  `at_k2`; the column, index and constraint differences are computed from `at_k2`, expected sets unchanged; the final
  `shape(engine) == up` stays.

Why: both measured "head" as if their own migration were head, false once 0063 adds its FK and column. §4's list
otherwise ran unchanged. After `git merge main` both files: 25 passed (21 s, routed `*_test` database,
`tools/heavy-slot.sh --db`).

## Not verified

The full suite; layout evidence (not run: no UI); `main` merged into the branch, with 3C0a's API test and 3B1's
start-up test re-run (P8, at merge preparation); the renumbering against 3A1 (D-3A1.12).
