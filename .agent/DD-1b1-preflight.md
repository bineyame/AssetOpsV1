# DD-1b1 pre-flight: story-time Actions and clock seams

Base `51f5ad22c`, branch `task/DD-1b1-story-time-actions`. No code written. **Rulings needed: Q1-Q7; the build is stopped.**
Scope read: sheet R6, R7, line 116-117, SCOPE-1 line 129 (R9 is BL-11, not built), MD-0 P1 table.

"Polish" below is a read-only query of `assetops_polish_full_test` (built 2026-11-02, before B-22). It shows the clock mechanics, not the v3 values. Anything marked **read, not run** comes from reading code only.

## P4 answer: the seams, checked against the code

| Fact | Writer and clock today | Seam |
|---|---|---|
| `evidence_publication.recorded_at` | `postgres_evidence_ledger.py:429`, SQL `clock_timestamp()`. Line number correct | **New.** Reached by `demo_combined_kobo.py:287` and `runs/registered_release.py:61` (`self._ledger()`) |
| Objective `recorded_at` | `objectives/adapters/postgres_objective_store.py:126` (sheet says :125), SQL `clock_timestamp()` | **New.** `declare_objective.main(argv, store=)` already takes a store, but prepare calls it as a subprocess (`demo_combined.py:439`) |
| Domain Action, link, intent | `PostgresDomainIntentStore(test_db_clock_override=)` (`postgres_domain_intent.py:221`) | Exists. `build_domain_intent_store` (`work/composition.py:142`) does not pass it |
| Case, record, COMPLETE | `PostgresWorkStore(test_db_clock_override=)` (`postgres_work_store.py:276`) | Exists. `build_work_store` (`composition.py:36`) does not pass it |
| Cold, EV assessment | `build_cold_assessment_worker` / `build_ev_assessment_worker(url, **kw)`, `clock=` (`analytics/composition.py:113,123`) | Exists. The demo children do not use it (Q1) |
| Opportunity enqueue | `enqueue_opportunity_job`, `test_clock_override` (`postgres_assessment_store.py:478`) | Exists. Prepare's tick runs in a subprocess without it (Q4) |

Guard registration: no guard under `tools/checks/` mentions the override names, so R7 should not edit a guard. The estate guard self-tests stay out unless that changes. COH-3 pair counting (Q6) touches `chain_coherence.py` and its test.

P5 is dropped (R9 backlogged).

## Questions

### Q1. R6 cannot work on the demo path unless the Cold and EV workers also run at story time (sheet gap, added wiring)

- A domain Action's Finding pin is read at `command_now` (`domain_intent.py:106`; `selected_finding_pin` → `_ReadTx._pin(..., known_at)`, `composition.py:95`).
- The Cold and EV workers run on wall time (`test_w206_ev_store_postgres.py:81`, `run_worker` with no clock; `test_w502` `run(built)`).
- Polish confirms it: Cold and EV `analytic_run_selection.selected_at` and `finding_revision.created_at` are all 2026-11-02 18:42-18:43, for story windows of 10-20 to 10-31. Kobo's are at story time.
- So a story-time `command_now` comes before the selection it must pin, and `create_action` should refuse `DOMAIN_INTENT_LINK_INVALID` (**read, not run**).
- MD-0's ACT-C1/E1 avoid this because their workers take `clock=`.

Options:
- **(a) Recommended.** In the demo children only, run the Cold and EV workers with the existing `clock=` at `received_at + 5 min`, the Kobo child's rule (`demo_combined_kobo.py:380`). Cold and EV Findings and selections then carry story time. This is wider than R6 names, and it changes the build-time fact on those rows. `select_exact` (EV) must follow; whether its `_project` honours the clock is checked first in the build.
- (b) Story `raised_at` only, with `recorded_at` left at build time. COH-3 becomes non-vacuous because it reads `raised_at`, but the thread causes key on `recorded_at` and `occurred_at` (`lifecycle_run.py:63-68`), so ACTION_ACCEPTED lands on the build day. This fails R6.

Size: (a) is about +0.25 on R6. The process-local swaps of `build_work_store`, `build_domain_intent_store`, `now_utc` and `_db_now` follow the children's existing pattern. Standalone w502 and w504 are unchanged.

### Q2. The story instants for ACT-002 and ACT-003 (no ruling gives them)

Today `raised` is `k0 + (db_now − k0) / 7` (`w502_cold_work_walkthrough.py:190`) and `_db_now` (`w504:220`), both derived from build time. The strict order K0 < Action < last link < intent (`w502:260`) must hold.

**Recommended, all authored offsets from the day's own decision instant:**
- Cold (K0 = 17:05Z, S+0): worker 17:10, Action `raised_at` and `recorded_at` 17:15, then one story clock stepping 1 s per command for cases, links and intent.
- EV (decision 09:00Z, late 09:05Z, on the fault Tuesday): worker 09:10, Action 09:15, intent one step later.
- `occurred_at` values are unchanged (Cold 16:11-16:42). The fixture WR's work therefore keeps its existing place before the Action is raised, and is recorded after it, as it is on polish.
- Cold's visits and plan, and EV's `write_work`, go through the same clock. They share the service, and their reach-back stays inside the 30-day limit. **Alternative:** leave them at build time, which needs a second service for Cold.

### Q3. ACT-003 has no case, so it has no APPLIED cause (sheet says "APPLIED and case causes" for both; code differs)

`declare_and_work` (`demo_combined_ev.py:153`) posts only the Action and intent. The `write_work` visits are unlinked and predate the fault. `_attest` (`w504:386`) is not on the demo path. On polish, Cold has the only linked COMPLETE row.

- **(a) Recommended.** ACT-003 stays ACTION_ACCEPTED ("Action agreed"), as MD-0's ACT-E1 does (`build-sheet-MD-0.md:92`). ACT-002 carries APPLIED and the case cause. No new story content (SCOPE-1). F-THREADS (DD-1b2) then expects these two states.
- (b) Add a linked EV case with ASSIGN and COMPLETE from the w504 literals. The EV thread then reads "Change made". This is new shown story content, about +0.25, and backlog-class unless the demo script needs it.

### Q4. R7's third item rests on a premise the code contradicts (sheet/code mismatch)

MD0-S3 Q3 and R7 say the DB-trigger enqueues stamp DB time. They pass `decided`, the disposition's `decided_at`, which is already story time under `test_decision_clock_override`:
- EV: `0025:365,371,378,438`.
- Mini-depth: `0029:258`. The configuration paths take the writer's `p_at`.
- Polish: Cold, EV, dispatch and mini `available_at` and `created_at` are at story time.
- The only build-time jobs are `mini_opportunity` (4 rows, 2026-11-02 18:46), queued by the tick's scan. `0049` uses `now()` once, in a migration backfill.

Also, a job's `available_at` does not date a study. Reader and worker clocks do, so R7's stated aim ("studies carry story time") is not reached through this seam.

- **(a) Recommended.** No migration and no trigger edit. An L2 test pins that `available_at = created_at = decided_at` with the ledger override set, and DB time with it unset, for one EV and one mini row. Opportunity studies stay a declared R4 build-time fact (`build-sheet-MD-0.md:379`) and get a backlog line.
- (b) Story-date the opportunity scan: run it in process in prepare with `test_clock_override` and `test_lease_clock`, at about +0.25. Needed only if a story-time mill Action must exist (Q5).

### Q5. Who records the mill Action? (possible scope hole; not added here)

DD1a2-R Q8 says "No Action is recorded (that is DD-1b)". `origin_opportunity_id` appears only in tests, and `demo_combined_kobo.py` has no mill Action. R6 and the DD-1b1 acceptance name only ACT-002 and ACT-003, while DD-1b2's acceptance expects "the mill Action's verification state from CH-9b3".

**Recommended:** not in DD-1b1. Please name the owner. If it is story-dated, `opportunity_revision_selected` at `command_now` makes Q4(b) a precondition (**read, not run**).

### Q6. The refusal's shape, and how COH-3 non-vacuity is proved without a prepare

Refusal:
- **Recommended.** New constructor params in the existing style: `PostgresEvidenceLedger(test_publication_clock_override=)` and `PostgresObjectiveStore(test_recorded_clock_override=)`.
- Setting either on a URL whose database does not match `^assetops_polish_.*$|^.*_test$` raises at construction, through one shared helper. Unset, the SQL text stays literally `clock_timestamp()`, the helper is not called, and composition never passes it.
- The existing overrides used by R6 are not given the check. Their wiring lives in the children, whose parent already enforces `DB_RE` (`demo_combined.py:53`), and the children gain the same helper call. **Alternative:** add the refusal to every existing `test_*` override, which touches a dozen stores and is not recommended.

Proof:
- COH-3 returns findings only, so "evaluated at least one pair" cannot be seen from its output.
- **Recommended.** Add a small `coh3_pairs(bundle)` beside `coh3_action_on_board` (`chain_coherence.py:466`) with a test in `test_chain_coherence.py`.
- Add one L2 on a scratch `*_test` DB: the Cold child's failure day and the EV child's fault day only (not `demo_combined.py prepare`, no finish rows, no polish), then a tick, the board reads, and the pair count and finding list. Capped at twice its first measured time, one heavy job at a time.
- This is the same class as the DD-1a2 dry run. **Please confirm it does not count as a "demo prepare".** F-COH3 on the whole build stays in DD-1b2.
- If COH-3 then reports a real finding (the board does not link the Action), I stop and report rather than change the product.

### Q7. Story values for the two new seams, and what MG-1's date changes

Publication:
- **Recommended.** Each child passes the day's `received_at`, the same instant as its decision seam. `source_provenance.py:6` states that it reads no date, so no read should change (the test pins this).

Objective:
- The fixture has lines for all three Sites (`demo-objectives.json`), R7 names only MG-1, and one writer serves them all.
- `current(known_at)` applies only on a `known_at` board read (`site_outcomes/read.py:209`). Live board reads have no `known_at` and do not change. Reads with `known_at` that today show no objective will show one.
- **Recommended.** All lines per Site at `install_at + price_after_install_hours` (Kobo: `price_recorded_at`; Cold and EV: the same offset from their own install). A small tools helper calls `declare_objective.main(argv, store=...)` in place of the subprocess. **Alternative:** MG-1 alone, leaving MG-2, MG-5 and the Cold and EV lines at build time, which gives mixed dates on one board.

## Shown-state change to accept with these rulings

- `demo_combined_ev.py:162-164` records POLISH R645: the Action is dated after every story window "so the fault-window board does not list it".
- R6 reverses that. The Cold and EV S+0 boards and their Portfolio rows will list ACT-002 and ACT-003. That is the intended I-09 fix, but it visibly changes those boards, and any finish row or capture expecting the old state falls to DD-1b2.
- Please confirm R6 overrides R645.

## Not a question

- R9 is out. Acceptance's tick clause and §3 L0's R9 shape do not apply.
- `I-09` register entries in `expected-today.json` are not touched here. DD-1b2's F-COH owns the reconcile.
- Size as recommended: 1.25 + 0.25 (Q1) = 1.5. Q3(b) and Q4(b) would each add 0.25.
