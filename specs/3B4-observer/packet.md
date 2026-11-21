# 3B4 review packet (units 1-3; partial)

Task: `specs/3B4-observer/spec.md` rev 2 (rulings D-3B4.1-26, reviewer guide rev 2). Branch `task/3B4-observer`, base
main `17775a4d5`. **Stopped at the end of unit 3; the `check.py` edit (spec §2.3: `OBSERVE_CODES`,
`check_observed`, its call in `check_all`), tests 1, 1b and 3, and unit 4 wait for 4a and 3B6 to merge** (D-3B4.25;
neither is an ancestor of `main` yet). `USER_REVIEW_REQUIRED: false`.

## Outcome

For a closed month's served, current snapshot, `observe_structure run` compares each of MINI_GRID's 19 observed
leaves with its target per Site and writes a Finding in today's store (domain `structure`, mechanism
`STRUCTURE_DEVIATION`, its leaf in its key) only for an adverse deviation strictly outside the leaf's tolerance;
re-runs on unchanged figures write nothing, changes revise or withdraw on record. `declare_tolerance` records a
Site's tolerance, by the finance lead (money leaves) or the Site's own manager (operational), with person and time.
Codes and JSON only; no route, no screen, no served text (`git diff main...HEAD -- backend/assetops_backend/i18n`
is empty).

## Commits

| Commit | Unit |
|---|---|
| `acd4b18b4` | 1: `structure/observe/rules.py`, `observe.py`; tests 2, 4-9 (pure) |
| `9a76b83d6` | 2: migration `0071_structure_finding`, `structure_persist`, `structure_held`/`structure_apply`/tolerances, the four reader predicates, the one guard name |
| `8dad430c7` | 3: `service.py`, `composition.py`, `observe_structure.py`, `declare_tolerance.py`, two `COMMAND_ROLES` keys, `structure_lock`; Postgres tests 10-15 |
| (this commit) | packet, spec status, `specs/INDEX.md` row, built-state entry |

## Gates

- **Gate A.** `main`'s head is `0066_structure_snapshot`; 0067-0070 are held by unmerged 3A6, 3A7, 3C2 and 3C1b, so
  the file is `0071_structure_finding` with `down_revision = "0066_structure_snapshot"` (self-contained: it reads
  nothing of 0067-0070). **Gate B at merge:** if `main`'s head moved, renumber on top of it and run `alembic heads`
  (one head); `test_10_single_head_on_0066` pins the parent and fails until it is updated.
- **Gate 4a/3B6.** `git merge-base --is-ancestor` is false for both today; the `check.py` commit is not made.

## Acceptance (spec §9)

1. Raised only when adverse and strictly outside tolerance (tests 4, 5, 11): yes; every other state writes nothing
   (test 11's re-run, rebuilt and tolerance steps).
2. Directions agree with the bridge's signs (test 2): yes. Start-up refusal of planted tables (test 3): **pending the
   `check.py` commit**.
3. Unknown is not zero (tests 5, 6, 6b): yes; `grep -n "or Decimal(0)\|or 0" backend/assetops_backend/structure/observe/`
   is empty.
4. Re-run and rebuilt snapshot write nothing; each change writes exactly the table's transition (test 11): yes.
5. Domain `structure`, pinned by key, claim in the leaf's unit, the 25-key set a literal (tests 9, 11): yes.
6. No reader shows, counts or chokes on a structure Finding (test 13, sweep below): yes.
7. Tolerance only by the finance lead (money) or the Site's manager (operational), with person and time, read by
   month and as known (test 15): yes.
8. One guard name, one migration, no served text: yes. Plants: see below. Mid-build count: 0.

## The §4.4 sweep, re-run on the branch

Grep of spec §0 (b) plus the child tables (`finding_revision_assessment`, `finding_revision_evidence`,
`finding_merge`) over `backend/assetops_backend`: 17 files; the SQL grep alone names 14 (estate and `mini_decisions`
included), and the child-table names add `finding_read.py` and the two provenance modules, where they occur only in
prose and method names (the SQL is in the ledger adapter, by revision id).

| Reader | Class |
|---|---|
| `analytics/adapters/postgres_finding_store.py` `_fence`, `finding_detail`, `rows()` (five selects) | §4.4 table: predicates added (P13, P17, P18, P19) |
| `chain/adapters/postgres_thread_sources.py` `_FINDING_SOURCES` (+ `_BY_ID`) | §4.4 table: predicate added (P12) |
| `thread_sources._FINDING_LIFECYCLE`; `work/adapters/postgres_work_read.py` `_pin` | §4.4 note: unchanged, harmless |
| `postgres_finding_store.py` other statements (`index_lineage_on`, the dispatch and fuel writers) | A: by id or named domain |
| `analytics/adapters/postgres_assessment_store.py` (cold :2322/:2723/:2847, EV :3388/:3748, `structure_persist`) | A: named domain (`cold_chain`, `ev_charging`, `:d`) or by id |
| `actions/adapters/postgres_action_store.py` | A: by Finding or revision id, or by an Action's origin |
| `chain/adapters/postgres_chain_read.py` `_FINDING_HEADS`, `_TRACE_FACTS`, titles | A: by thread occurrence, named domain/analytic, or id list |
| `estate/adapters/postgres_estate_read.py` :178/:240/:248/:318/:426 | A: id lists; :318 by a dispatch selection's assessment revision |
| `mini_decisions/store.py` :186/:299/:307 | A: by revision or Finding id |
| `work/adapters/postgres_work_read.py`, `postgres_work_store.py`, `postgres_domain_intent.py`, `postgres_domain_action_index.py` | A: by revision id list, Finding id or Action origin |
| `financials/adapters/postgres_consequence_store.py` | A: named domain (`mini_grid` :394, `cold_chain` :911) or by id |
| `fuel_balance/adapters/postgres_fuel_balance_store.py` :358 | A: `domain = 'fuel_balance'` |
| `evidence/adapters/postgres_evidence_ledger.py` :1032/:1121 | A: by revision id |
| `analytics/finding_read.py`, `evidence/public_provenance.py`, `evidence/source_provenance.py` | no SQL: names in prose or method names; reads go by revision id |

Triggers: `financial_consequence_dirty` is `mini_grid` only (0022); the EV assessment trigger is `ev-session/1`
only; `chain/threads.py` is unchanged.

## Plants (reviewer guide; scratch copy, serial, one DB slot)

Each plant applied alone to a scratch copy at `8dad430c7` (pure ones in a copied tree; Postgres ones in a throwaway
`git worktree`, so the slot pool accepts it), its named test run, then reverted. All 21 fail as required:

| Plant | Test | First failing assertion |
|---|---|---|
| P6 `<` for inside | 5 | Kisiwa `unexplained_l` `RAISED`, not `INSIDE_TOLERANCE` (band 20 = gap) |
| P7 target's `of_factor` | 4 | band `14.000`, not `23.6` |
| P8 `None` band as 0 | 5 | `RAISED`, not `TOLERANCE_NOT_AVAILABLE` |
| P9 carried actual | 6b | Kisiwa `om` `NO_GAP`, not `ACTUAL_NOT_AVAILABLE` |
| P10 basis over the claim | 11 | the rebuilt snapshot writes `SUPPORT_CHANGED` |
| P11 `UNCONFIRMED` for inside | 11 | `necessary_l` `UNCONFIRMED`, not `NO_LONGER_SUPPORTED` |
| P12 thread-sources predicate | 13 | `KeyError: 'structure'` from the threads stage |
| P13 `finding_detail` predicate | 13 | detail returned for a structure id |
| P14 other Site's manager | 15 | `SET` written, not `PERSON_ROLE_REQUIRED` |
| P15 `money` key in the claim | 11 | key set differs from the 25-key literal |
| P16 no `MONTH_OPEN` | 14 | `DID NOT RAISE ObserveRefused` (both open cases) |
| P17 fence counts structure | 13 | revision count 5, not 0 more |
| P18a/b `finding`/`finding_revision` unfiltered | 13 | `findings` / `revisions` list not empty |
| P19a/b/c assessments/evidence/merges unfiltered | 13 | `assessments` / `evidence` / `merges` hold a structure link |
| P20a command refuses 0 | 15 | `PCT_INVALID` for `0` |
| P20b band 0 reads `of_factor` | 5 (pct 0) | band `None`, not `0` |
| P22 basis drops `target_evidence` | 7 | basis unmoved by `target_evidence` |
| P23 portfolio digest | 11 | `input_evidence_sha256` is not the Site row's |

Logs: `/opt/assetecon/evidence/3B4-observer/units1-3/plants.out`, `plants-pg.out`.

P1-P5 and P21: **pending the `check.py` commit** (they need `check_observed` and test 1b).

## Tests run

All at `8dad430c7` (k4a's fix after it), `ASSETOPS_TEST_PYTHON` = the shared venv, through
`tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- <files>`; logs under
`/opt/assetecon/evidence/3B4-observer/units1-3/`.

| Run | Files | Wall | Result |
|---|---|---|---|
| Focused | `test_3b4_observer.py`, `test_3c1a_person_work.py` (pure) | 14 s | 161 passed, 13 skipped (the Postgres file without a URL) |
| Focused Postgres | `test_3b4_observer_postgres.py` | 18 s | 13 passed |
| Regression | 30 files: 3B4, 3C1a, the 12 S4 Finding/money files, 3B1, 3B2, 3B3, 5b, k4a, 3B7a x3, ch1b x3, ch2 x2, ch3, ch5a1 | 1078 s | 684 passed, 11 failed, 1 skipped |
| Baseline | the 4 failing files on a throwaway worktree of `main` `17775a4d5` | 470 s | the same 10 fail on main: `test_s4_schedule_tick` (4), `test_s4_schedule_health` (3), `test_ch1b_outbox` (1), `test_ch1b_fix` (2), environmental ("No product database is configured" in the schedule stages); pre-existing, not 3B4 |
| Branch re-run | the same 4 + k4a, after the k4a fix | 481 s | the same 10, k4a all pass |
| Guards | `check-architecture.ps1` (98 s) pass; `check-agent-workflow.ps1` pass; `check-all.ps1` fast (252 s): 1 of 41 failed: `specs/INDEX.md` over its 8000-byte cap (fixed: row shortened, 7976 bytes) and `D-DS3.23` unresolved in `.agent/backlog-post-demo.md` (on `main` since `17775a4d5`, not 3B4) |

The 11th regression failure was 3B4's: `test_k4a_fuel_finding_postgres.py::test_b1_migration_up_down_up_on_empty_tables`
compared head's CHECKs with 0055's plus the fuel arm; 0071's structure arm breaks that at head (deviation 11).

## Runbook line (spec §5.2)

After `build_structure_snapshot build --tenant <slug> --month <YYYY-MM> --by person:<id>` for a closed month, run
`python -m assetops_backend.observe_structure run --tenant <slug> --month <YYYY-MM>`.

## Known deviations

1. `structure_apply` returns `(transition, finding_id, revision_id) | None`, not `UUID | None`, so the service fills
   `Written` without a second read.
2. "Money unit" in observe step 3 and §5.3 means a unit with a money *dimension* (`MONEY`, `MONEY/KWH`, `MONEY/L`):
   the evaluator requires a currency on `MONEY/KWH` leaves, so `tariff`, `productive_tariff` and `diesel_price` are
   money leaves (finance lead) as §5.3 lists them.
3. The advisory lock is `PostgresFindingStore.structure_lock(c, site_id, month)`, called first in the Site's
   transaction: the service may not import the driver (configuration-persistence rule 2), so the one statement sits
   in the store. Same key as spec §5.1.
4. `test_3c1a_person_work.py`'s literal `SPEC_ROLES` gains the two keys and its route-command set excludes the
   `structure.` prefix (as it does `commercial.`): the spec's `COMMAND_ROLES` edit would otherwise fail it.
5. `declare_tolerance show` prints one JSON line holding an array of the per-leaf objects, in `OBSERVED` order.
6. F3's clock: a settable clock set to now before each run, not a fixed instant. `recorded_at` is the database's
   `clock_timestamp()`, so a fixed past clock would hide every declaration (`recorded_at <= known_at`).
7. Test 11's `candidate_l` 340 writes `SUPPORT_CHANGED` for `candidate_l` **and** `unexplained_l`: `diesel_l` =
   necessary + candidate + unexplained + extra, so `unexplained_l`'s 2 % band moves (23.8 from 23.6). The rule is as
   specified; the spec's step named only one leaf. Test 12 counts two revisions per such change.
8. Reviewer-guide plants split where one plant covers several statements: P18 a/b (`finding`, `finding_revision`),
   P19 a/b/c (assessments, evidence, merges), P20 a/b (command refuses 0; band 0 reads `of_factor`). Test 13 writes
   one raw `finding_merge` and one raw `finding_revision_evidence` row on structure revisions (the latter with
   `session_replication_role = replica`, no evidence row existing) so the last two `rows()` lists are not vacuous.
9. `observe_structure.main` takes `accounts` for the spec's signature and does not read it (the run names no person).
11. `test_k4a_fuel_finding_postgres.py` `test_b1`: 0056's widening is now compared at 0056 (`command.upgrade(config,
   MIGRATION)` after the downgrade), then head; it compared at head, which 0071 widens again.
10. `Wiring.dispose` disposes the snapshot service and the assessment store; `PostgresFindingStore` has no `dispose`
   (unchanged), so a command's Finding-store engine ends with the process.

## Residual risks

- **R-FENCE-FUEL** (D-3B4.9): the dispatch fence still counts fuel, cold and EV revisions; only `structure` is left out.
- **R-NO-OPPORTUNITY** (D-3B4.4): no opportunity Findings (no record of a customer's opportunity exists).
- **R-ASSUMED-TARGET** (D-3B4.5): with no tolerance set, every adverse deviation against 5a's target is raised,
  including assumed targets (leak at zero); the operator narrows it by tolerance (owner Q1, OWNER-AWAY row 27).
- Snapshots will serve with reason `RULES` once `check.py` changes (code digest), so analysts rebuild after merge.

## Review focus

The lifecycle table first-match (`rules.transition`), the basis never over the claim (`service._site`), the Site-row
digest (D-3B4.21), the five `rows()` selects, the SITE_MANAGER binding in `declare_tolerance.admitting_role`.
