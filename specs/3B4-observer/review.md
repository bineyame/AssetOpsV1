# 3B4 review

## Round 1 (discovery, W5): fresh Claude reviewer, 2026-11-21, at `ce9b093d7`

**Summary (verdict ACCEPT WITH FIXES; nothing High or Medium, so nothing blocks).**
- The build matches spec rev 2 and rulings D-3B4.1 to D-3B4.26. There is one mechanism, `STRUCTURE_DEVIATION`, and
  the Finding key names the leaf. 19 + 12 tables cover registry v4's 31 MINI_GRID leaves exactly once. Start-up
  checks each direction against the bridge's signs. Migration 0071 is 0056 plus the two arms, and the tolerance
  table matches the spec. The only guard change is the one `$findingTables` name.
- All four readers are filtered, and so are all five `rows()` selects. I found no fifth reader: every other read
  goes by id, domain, analytic or thread (class A). `_UNSETTLED` is a transient that already exists (see residual
  risk).
- Checks: `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`) and `check-agent-workflow.ps1` pass. Focused pure
  tests: 313 passed. 3B4 and k4a Postgres tests: 27 passed. Plant R3 failed its named test. Plants R1, R2, R7, R9 and
  R10 did not: four lifecycle and permission rules that are implemented correctly have no test that would fail if
  they broke (L1 to L3).
- None of the 12 deviations changes behaviour the spec fixed. Deviation 7 follows from the specified band rule.
- Fixes on the branch (Low, before merge, cheap): L1 to L3 are missing tests. L4 corrects a packet claim.
- Merge notes: gate B, renumbering 0071 if main moves (mechanical; no unmerged branch touches the two CHECKs).
  Every served snapshot goes stale on merge (reason `RULES`), so the observer refuses until they are rebuilt (§ Merge).

### Findings

| # | Sev | Where | What is wrong | Why it matters | Fix | Class |
|---|---|---|---|---|---|---|
| L1 | Low | `backend/assetops_backend/structure/observe/rules.py:150-166` (`transition`); `backend/tests/test_3b4_observer_postgres.py:303` (test 11) | Three rows of spec §4.3's table have no test that can fail. My plants R1 (`UNCONFIRMED` + `RAISED` writes nothing instead of `REOPENED`) and R2 (`UNCONFIRMED` + `INSIDE_TOLERANCE`/`FAVOURABLE`/`NO_GAP` writes nothing instead of `NO_LONGER_SUPPORTED`) each pass all 27 pure and 13 Postgres 3B4 tests. Test 11 ends on `UNCONFIRMED` and never moves the Finding out of it. The "anything else writes nothing" rows (for example `NO_LONGER_SUPPORTED` + not computed) are untested too. | Spec §9 Q4 asks whether each change writes exactly its table transition, and the packet answers yes from test 11. The code is right today, but a regression on these rows would leave a Finding stuck in `UNCONFIRMED` without any test failing. | Add one pure test that walks `rules.transition` over every (held lifecycle, held basis, state) cell of §4.3 against a literal expected table (W2). Optionally, extend test 11 to restore `outstanding` after its `UNCONFIRMED` step and assert `REOPENED`. | missing test |
| L2 | Low | `backend/assetops_backend/structure/observe/service.py:68` (`recorded_at <= known_at`) | Nothing tests the "as known" half of the tolerance read. My plant R7 drops the `recorded_at <= known_at` filter, and all 13 Postgres tests still pass. Test 15 tests only the month half (`2026-09` reads `NONE`). | Spec §9 Q7 says "read by month and as known (test 15)", and the packet answers yes. That evidence covers only the month half. | Add a case where a declaration is recorded after the run's `known_at` (the settable clock of deviation 6 makes this easy) and assert the earlier tolerance applies. | missing test |
| L3 | Low | `backend/assetops_backend/declare_tolerance.py:132` (`person.tenant_id != tenant_id`, `not person.active`) | Nothing tests `PERSON_NOT_FOUND` for a person of another tenant or an inactive person. My plant R9 drops the tenant check, and all 13 Postgres tests still pass, and so does R10, which drops the `active` check. Test 15 exercises only an unknown email. | This guards who may set a tolerance (people set tolerances: design §4 "Who"; D-3B4.22). The code is right today, but a regression that let another tenant's finance lead set this tenant's tolerances would not be caught. | In test 15, onboard one FINANCE person on a second tenant and one deactivated FINANCE person on this tenant, and assert `PERSON_NOT_FOUND` for both. | missing test |
| L4 | Low | `specs/3B4-observer/packet.md` "Acceptance" items 4 and 7 | The packet answers §9 Q4 and Q7 with "yes" and cites tests that do not cover the untested halves found in L1 and L2. | A packet claim is a claim to verify. These two overstate the evidence. | Once L1 and L2 land, the claims are true. Otherwise, name the untested rows. | packet accuracy |

No acceptance gap: every rule above is implemented as the spec says, and I checked each by reading the code. These
are missing tests, not wrong behaviour.

### Known deviations, judged

| # | Verdict |
|---|---|
| 1 `structure_apply` returns `(transition, finding_id, revision_id)` | Accept. Internal signature only. The table it implements is unchanged, and it saves a second read. |
| 2 money dimension (`tariff`, `productive_tariff`, `diesel_price`) | Accept. Spec §5.3 already lists these three as money leaves. `money_dimension` uses the same rule as the evaluator's currency check, so `CURRENCY_MISMATCH` covers `MONEY/KWH` and `MONEY/L` consistently. |
| 3 advisory lock in the Finding store | Accept. The SQL and key are the spec's (§5.1). It is called first inside the Site's transaction. Configuration-persistence rule 2 forbids the service from issuing SQL itself. |
| 4 3C1a's role table gains the two keys | Accept. The spec requires the `COMMAND_ROLES` edit. The route-command set excludes `structure.` because these keys belong to a command line, not a route, the same treatment `commercial.` gets. |
| 5 `show` prints one JSON array line | Accept. The spec says "one JSON line" and leaves the container open. |
| 6 F3 clock set to now | Accept. Test-only. A fixed past clock would hide every declaration, because `recorded_at` is the database's `clock_timestamp()`. It does leave the as-known filter untested (L2). |
| 7 `candidate_l` 340 also revises `unexplained_l` | Accept. This follows directly from the specified rule: the band is 2 % of the actual `diesel_l`, which includes `candidate_l`, and the basis includes the band. Behaviour is as specified; the spec's test step named one leaf only. |
| 8 plants split into a/b/c | Accept. This is more coverage, not less. |
| 9 `accounts` accepted and unused | Accept. It matches the spec's signature. |
| 10 Finding store has no `dispose` | Accept. This is unchanged from before. A command's engine ends with its process. |
| 11 k4a `test_b1` compared at 0056 | Accept. It still compares 0056's widening exactly (an upgrade to `MIGRATION` after the downgrade), then returns to head and asserts the head shape equals the pre-downgrade shape. 3B4's test 10 covers the head CHECKs. |
| 12 test 1b sets `sys.path` inside `-I` | Accept. The module under test is still the first import of a fresh interpreter (`sys` is built in). The real cycle fails it: plant P21 in the packet, log `/opt/assetecon/evidence/3B4-observer/unit4/plants.out`. |

None of the 12 changes behaviour the spec fixed.

### What I checked against the spec

- **§2.1 and §2.3, the tables and start-up.** `OBSERVED` (19) and `NOT_OBSERVED` (12) equal spec §2.1 in registry
  order. `check_observed` runs code by code in `OBSERVE_CODES` order. A node in `OBSERVED` is skipped by `COVER`'s
  leaf loop and caught by `LEAF` (D-3B4.16). `DIRECTION` refuses `{-1}`+DOWN, `{1}`+UP and both signs. `KIND`
  refuses an unreached leaf outside Protect. `check_all()` calls it after `check_pins()` only on the no-argument
  path. Import discipline (D-3B4.20): `observe/rules.py` imports only `registry`, `expressions` and
  `attribution.rules`. `observe/__init__.py` is a docstring. `TARGET_RULE` is imported inside the function. My
  plant R3 (`delivered_kwh` UP) fails test 1, and `check_at_start()` raises
  `ConfigurationError: STRUCTURE_OBSERVE_DIRECTION MINI_GRID/delivered_kwh`.
- **§2.2, the rule.** It runs in the spec's order and inside `Context(prec=34, ROUND_HALF_EVEN)`, with nothing
  quantised and no float. Inside means `abs(gap) <= band`. The band is read from the actual side's `of_factor`.
  `pct == 0` gives band 0 without reading `of_factor`. `NONE` gives 0. A missing `of_factor` actual gives
  `TOLERANCE_NOT_AVAILABLE`. A grep for `or Decimal(0)` and `or 0` in `structure/observe/` is empty. The actual
  side is chosen in `observe_site` only (`site.actual`). The basis covers the listed fields. `pct` is normalised in
  the basis, the declaration id is left out, and no instant or snapshot id enters it.
- **§4.1, migration 0071.** The CHECKs are 0056's literals plus one arm each. There is no bounds CHECK. The table,
  CHECKs, foreign key, index and append-only trigger are exactly as §4.1. The downgrade locks the three tables and
  refuses while any rows exist.
- **§4.2 and §4.3, the stores.** `structure_persist` reuses the run by its basis and numbers assessment revisions
  per key. The Finding and revision columns are as §4.3: title is the code, the minutes and assets are NULL,
  `input_evidence_sha256` is the Site row's digest (D-3B4.21), and there is one primary WINDOW link with no
  evidence row. The claim has exactly the spec's 24 named keys plus `format`, with no bridge value or effect
  (D-3B4.18). `recurs_after_finding_id` is set only when the previous month's latest revision is `SUPPORTED`.
  `tolerance_append` is one plain INSERT using `clock_timestamp()`.
- **§4.4, the readers.** Predicates are present in `_FINDING_SOURCES` (and so in `_BY_ID`, which derives from it),
  `_fence`, `finding_detail`, and all five `rows()` selects. The three child-table selects filter by revision id
  through `domain <> 'structure'`. `chain/threads.py` is unchanged.
- **The fifth-reader sweep.** I swept `finding*` and `analytic_run`/`assessment_revision` readers across
  `backend/assetops_backend`. Every other read is by id or id list, by named domain or analytic, or by thread
  occurrence: estate, mini_decisions, work, consequence, action, evidence, `_index_snapshot`, `episodes`,
  `findings_over`, `_FINDING_HEADS`, `_TRACE_FACTS` and `_PLACEMENT`. `config/chain/event-register-v1.yaml` sends
  `finding.revised` to the `threads` consumer only, so the snapshots consumer never sees a structure revision. The
  only triggers on the written tables are `financial_consequence_dirty` (mini_grid), `cold_consequence_dirty` and
  `ev_consequence_dirty_assessment` (EV analytic): none fires for this domain or analytic. No migration in the
  unmerged 0067 to 0070 branches (3A6, 3A7, 3C2, 3C1b) touches either CHECK.
- **§5, the service and commands.** Refusals are in spec order. `known_at` is read once. Each Site runs in its own
  transaction under the lock. Excluded Sites are passed through. `declare_tolerance` refuses in spec §5.3 order.
  Its money or operational choice comes from the unit dimension. A `SITE_MANAGER` pair admits only on this Site.
  `pct` 0 is accepted. The two `COMMAND_ROLES` keys are at the end.
- **Seams.** `git diff main...ce9b093d7 --stat` shows no change under `structure_snapshot/`, `registry.py`, any row
  file, `sources.py`, `i18n/` or `outcome_map.py`. The guard diff is the one name, and the architecture check
  passes with it.

### Checks I ran (worktree `/opt/assetecon/AssetOpsV1-3b4` at `ce9b093d7`; PYTHONPATH = the worktree's backend, contracts, simulator)

| Check | Result |
|---|---|
| `ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python pwsh -NoProfile -File tools/check-architecture.ps1` | `Architecture check passed.` (106 s) |
| `pwsh -NoProfile -File tools/check-agent-workflow.ps1` | `Agent workflow check passed.` |
| heavy-slot: pytest `test_3b4_observer.py`, `test_3b1_structure_registry.py`, `test_3b2_findings_pinned.py`, `test_3c1a_person_work.py` | 313 passed |
| heavy-slot `--db`: `run-host-tests.ps1 -- test_3b4_observer_postgres.py test_k4a_fuel_finding_postgres.py` (harness `*_test` only) | 27 passed |
| My plants: each applied alone on a throwaway detached worktree at `ce9b093d7`, then reverted; the worktree was removed afterwards | R3 fails (test 1 plus start-up DIRECTION); R1, R2, R7, R9 and R10 pass everything (L1 to L3) |

R10 (drop the `not person.active` check) also passes every test, so it joins L3.

The full regression is not rerun (TESTING.md). I cite the implementer's same-revision unit-4 run at `552b58d79`,
whose code equals head (`ce9b093d7` changes only the packet and docs): 916 passed, 10 failed, 1 skipped. The 10
failures (`test_s4_schedule_tick` 4, `test_s4_schedule_health` 3, `test_ch1b_fix` 2, `test_ch1b_outbox` 1) are, by
name, the same 10 as `units1-3/base-main.log` on main. Caveat: that baseline was taken on main `17775a4d5`, not
`2ef8e9769`. They are the schedule tests that call `_fence`, and the fence change is a no-op while no structure
revision exists, so I accept them as environmental.

**Not verified:** the full suite and check-all (cited, not rerun); the packet's plants P1 to P23 (cited from their
logs; I ran my own instead); behaviour on a real served snapshot (F3 uses fake snapshot and store fakes, as the
spec fixes).

### Residual risk the packet does not name

- **Board "not loaded" after a run.** Each observer revision emits a `finding.revised` event. Until the threads
  stage consumes it, `chain_read._UNSETTLED` makes `findings_settled` false, and the Site board shows its
  not-loaded link suffix. This already happens for any command-written Finding (fuel balance, for example) and it
  clears at the next scheduled threads stage, but the walkthrough DB will see it right after an observer run.
- **Inputs read outside the lock.** Tolerances and observations are computed before the Site transaction takes the
  advisory lock (spec §5.1's order). Two runs at once could commit in an order the later inputs would not choose.
  The run is one analyst's manual command, so the risk is Low.
- **App clock against database clock.** `known_at` is the app's clock and `recorded_at` is the database's. A
  declaration made seconds before a run is missed if the database clock runs ahead of the app's. Same machine
  today.
- **Future observer-table edits stale every snapshot.** `check.py` now imports `observe/rules.py`, so both sit in
  the snapshot code-digest closure (`structure_snapshot/adapters/code_digest.py`, root
  `structure_snapshot.composition`). Any later edit to `OBSERVED` or `NOT_OBSERVED` also marks every served
  snapshot `RULES`.

### Merge notes (operational, stated plainly)

- **Gate B.** If any of 0067 to 0070 (3A6, 3A7, 3C2, 3C1b) merges first, rename the file to the next number. Then
  set `down_revision` to the new head, change the `REFUSED` text's number, update `test_10_single_head_on_0066`'s
  pinned parent, and run `alembic heads` (one head). None of those migrations touches `finding_domain_subject` or
  `finding_revision_domain_minutes`, so 0071's 0056 literals stay correct.
- **Served snapshots go stale.** The snapshot code digest covers `structure/check.py`, which this branch changes.
  After merge, every structure snapshot built before the merge reads `freshness.current = false` with reason
  `RULES`. In practice:
  - every screen or read that serves those snapshots shows them as not current;
  - `observe_structure run` refuses each such month with `SNAPSHOT_NOT_CURRENT` (exit 3).

  The fix is to run `build_structure_snapshot build --tenant <slug> --month <YYYY-MM> --by person:<id>` for every
  served tenant-month on each database that holds snapshots, the walkthrough DB included. Run it after deploying
  the merged code and before any `observe_structure run`. No data is lost; the stale state lasts only until the
  rebuild.
