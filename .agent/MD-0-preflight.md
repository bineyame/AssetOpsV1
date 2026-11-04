# MD-0 pre-flight (P0-P7) and Architect questions

- Implementer: Claude, 2026-11-04. Branch `task/MD-0-mechanism` (dispatch name; the sheet says `task/MD-0-mechanism-dataset`), cut from main `a07452c63`.
- Sheet: `.agent/build-sheet-MD-0.md` §12. **Status: stopped at pre-flight.** Two blockers need an Architect ruling before code (Q1, Q2). No code is written. The scratch spike test was deleted and never committed.
- Paths: `B/` = `backend/assetops_backend/`, `T/` = `backend/tests/`. Lines are to `a07452c63`.

## P0, cost spike (measured)

- Setup: a pg_harness worker DB through `tools\run-host-tests.ps1`, on `CaseRunner` (roles-2). One 24 h Kobo day: 288 five-minute steps × 7 channels (state, 3 feeders, pv, dis, soc) = **2,016 readings**. The machine was shared with another agent's clone profile.

| Run | Batches | Ingest | Dispatch assess | `chain_snapshots` stage (consume + drain) |
|---|---|---|---|---|
| Hourly delivery (24 per device) | 168 | **172.9 s** | 23.4 s (24 jobs DONE) | 26.1 s (2,130 events consumed in 5 pages, 111 items) |
| Largest legal batches (≤ 256 envelopes per device; `BatchRejected TOO_LARGE` above 256, `contracts/assetops_contracts/ingestion_batch_v2.py:203`) | 13 | **40.0 s** | not timed (my spike's worker clock was before the later decision instants, so 5 jobs stayed PENDING) | 11.4 s (2,030 events) |

- Ingestion cost is mostly per batch (about 1 s per `submit`). Every reading also adds about one outbox event, which matches DD-0.
- **Extrapolated first build, using the 13-batch shape:**
  - Kobo: 13 days × (40 s ingest + about 10 s dispatch + about 11 s consume) ≈ 13 min, plus the critical-load channels roles-4 adds;
  - Cold: 11 channels, about 12 days, similar per-reading cost ≈ 10 min;
  - EV: 2 Tuesdays ≈ 1 min;
  - mini-depth, studies, step a and threads: not measured.
- **Total ≈ 25-30 min.** The sheet's bound is ≤ 3 min (§3) and its split trigger is > 5 min (§11), so the **P0 split condition is met**. Cold and EV are extrapolated by reading count; only Kobo was measured.

## P1, writers and clock seams

| Fact | Writer | Clock seam |
|---|---|---|
| Readings | `BatchIngestionService.submit` (`B/evidence/ledger_service.py:80`) through `PostgresEvidenceLedger(url, test_decision_clock_override=)` (`B/evidence/adapters/postgres_evidence_ledger.py:140`, `_decision_instant` :525-528) | yes |
| `evidence_publication.recorded_at` | ledger :429, `clock_timestamp()` | **NO CLOCK SEAM** |
| Productive price | `tools/demo_combined_kobo.py:137 publish_price(url, recorded_at)` → `B/publish_assumption.py:104 main`; store `B/financials/adapters/postgres_assumption_store.py:106 publish` | yes: `PostgresAssumptionStore(test_recorded_clock_override=)` (:62-68) |
| EV tariff | `tools/demo_combined_ev.py:240 publish_tariff(url, recorded_at)` (same store) | yes |
| Objective MG-1 | `B/declare_objective.py:68 main` → `B/objectives/adapters/postgres_objective_store.py:82 declare`, `recorded_at = clock_timestamp()` (:125); `current(known_at)` filters on it (:159) | **NO CLOCK SEAM** (R4: build-time fact, owner DD-1) |
| Dispatch Findings | `FindingMatcher` (`B/analytics/finding_service.py:36`) | `now=` |
| Cold / EV Findings | written inside the worker transaction: `cold_apply` (`B/analytics/adapters/postgres_finding_store.py:595`), `ev_apply` (:719); there is no separate matcher | worker `clock=` |
| Domain Action and intent | `DomainIntentService.create_action` / `post_intent` (`B/work/domain_intent.py:75,125`). They take no `command_now`; it comes from `PostgresDomainIntentStore(test_db_clock_override=)` (`B/work/adapters/postgres_domain_intent.py:198,223-232`) | yes (store override) |
| Work case, link, COMPLETE | `WorkService.create_case` / `post_event` (`B/work/service.py:162,257`), `post_case_link` (`domain_intent.py:212`); `db_now` from `PostgresWorkStore(test_db_clock_override=)` (`B/work/adapters/postgres_work_store.py:276,307`). COMPLETE also needs a maintenance record already in the case (`record_in_case`, service.py ~:285) | yes |
| s6 accept, apply, VERIFY | `store.accept(recorded_at=)` (`B/actions/adapters/postgres_action_store.py:259`); `ActionService.apply` (`B/actions/service.py:503`, effective time in the body, service clock); `VerificationService(clock=)` `freeze` / `bind_later_selection` / `evaluate` (`B/actions/verification.py:129,137,369,750`). The evaluator writes synchronously; there is no queued job | yes |
| Workers | Dispatch, Cold, EV `clock=`; `MiniDepthWorker` / `MiniOpportunityWorker(test_lease_clock=)` (`B/mini_depth/worker.py:56`, `B/mini_decisions/worker.py:96,164,265`) | yes. DB-trigger enqueues (EV 0025, mini-depth 0029) stamp DB time |

- No fact needs the simulator.
- The Kobo configuration path the demo uses is `tools/demo_combined_kobo.py:76 configure_at`: S3 roles-2, then S6 roles-3, then supply uses, then roles-4 (:106). MD-0 would import it.

## P2, verification: FAILS within "no B/ change"

- **Configuration:** roles-4 is a delta on roles-3 (its `bindings.note`), so it is not a standalone replacement for `DEMO`. The supported path is `configure_at`, which applies roles-2 → roles-3 → roles-4.
- **Evaluator:** VERIFIED needs complete critical-load windows (roles-3 and later). It also needs `source_pair` to PASS (`B/actions/verification_rules.py:664,684-694`). Both windows must resolve to `REGISTERED_SIMULATION` or `AUTHORED_DEMONSTRATION`, the same class in both, with the same authored fixture lineage.
- **Kit batches:** a batch posted with no prior publication resolves **UNKNOWN** (`B/evidence/source_provenance.py:161`; the link is written only at admission, ledger :342-350). So `source_pair` gives UNKNOWN, and **VERIFIED is unreachable from MD-0's batches as the sheet specifies.**
- **The only authored route** is `publish_source` before each submit (`T/test_w402_reads_postgres.py:122-146`). That route requires a fixture id declared in the server registry (`B/evidence/adapters/authored_fixture_specs.py:17-20`; refusal `FIXTURE_UNKNOWN`, `B/evidence/publication.py:173-181`). The fixture id therefore needs either a B/ entry or reuse of another fixture's id. **See Q1.**

## P3, Cold and EV quiet days, and time zones

- **chamber_temp_c** (`B/chain/measure_impls.py:217-251`, threshold 0.8): covered time is selected cold-excursion windows only. Raw readings add no coverage.
- **backup_start_chain** (:254-311, threshold 1.0): covered only by selected cold-start-response windows that hold a backup-role reading and whose `cold_backup_chain` state is not null.
  - With no start, `assess_start_response` gives state `UNKNOWN` (`B/analytics/cold.py:671-672`), a non-null string, so quiet windows look coverable.
  - Cold jobs coalesce with a bridge (ledger :645-661), so a day delivered in large batches should be one window. That is not measured.
- **charging_kwh** (:296-337, threshold 0.8): needs selected ev-session/1 windows.
- **Cold is source-gated:**
  - `gate.permitted` requires a positive class (`B/analytics/adapters/postgres_assessment_store.py:1300-1301`);
  - `failure_finding = OBSERVED_FAILURE and gate.permitted` (`cold.py:648-652`), so **with UNKNOWN provenance no COLD_START_FAILURE Finding is created**.
- **EV is source-gated:** UNKNOWN/MIXED is refused before assess (`B/analytics/ev.py:58-60`, `SOURCE_UNASSESSABLE`), so with UNKNOWN provenance charging_kwh is NO_DATA and no EV_INTERRUPTION exists.
- **Time zones:**
  - Cold is **Africa/Addis_Ababa** (`T/fixtures/w2/cold-lab-001.yaml:7`), not UTC as the sheet §2.1 expected. Cold days are local days, and `days.json` windows need the same R10 treatment as Kobo (Q4).
  - EV is Etc/UTC (`T/fixtures/w2/ev-lab-001.yaml:9`).
- **Bindings:** `republish_corrected_bindings` is not used by the demo (`tools/demo_combined_ev.py:180-182` calls only `install_ev_lab`), and the current bindings file already carries the corrected map.
- **Cases:** the W2-03 `backup-failed` case is 19:00 grid LOST + START_REQUEST, then 19:05 START_RESULT FAILED (`T/fixtures/w2/cold-w203-vectors.json`). The EV vectors `complete` and `interrupted` come from `T/test_w205b_ev_replay_postgres.py:100-134`.

## P4, noon variants: not answered

The survey agent stalled. This is not blocking for Q1/Q2. It will be answered at build time from `backend/conversions/w4-mini-depth-cases-v1.json`.

## P5, provenance

- A Kit batch with no publication is UNKNOWN (`NO_POSITIVE_BINDING`). A published authored batch is `AUTHORED_DEMONSTRATION` on all three Sites; its estate wording is "Prepared example data source" (`B/estate/placement.py:57-58`).
- No read hides AUTHORED_DEMONSTRATION. But Cold, EV and verification all **refuse UNKNOWN**. Mini-depth and studies have no source gate.

## P6, CH-1b stage call

- `B/scheduling/stages.py:273 chain_snapshots(url, {tenant_id, site_id, consume_limit, items})` and `:203 chain_threads(url, {tenant_id, site_id, limit})`. Each builds and disposes its own stores; see `T/test_ch1b_outbox_postgres.py:129-161`.
- Step a is `B/chain/backfill.py:108 _step_a(reader, tenant, site, url, dry_run, services)`. `PROTECTED_DATABASES` is at :29.

## P7, chain_clone

- `settle` (`tools/chain_clone.py:156`) checks the name via `settle_env` → `target_db` (`TARGET_RE`, :33,42).
- It does **not** need a record from `create`: it writes `var/chainclone_<name>/created.json` (`{"files", "dirs"}`) itself in `finally` (:169-176).
- Accepting the mechanism names needs `settle_env` to route the mechanism URL. The work folder record path is keyed `chainclone_<name>`, so a mechanism record would go under a different var path. This is a one-function change.

## D-AW-3 (code reading; measurement blocked)

- `TRANSITIONS` (`B/chain/lifecycle.py:45-56`) has no `(CHANGE_APPLIED, OCCURRENCE)`. `plan_lifecycle` appends the cause to `plan.skipped` as `{"thread_id", "cause", "cause_id", ...}` (:280). `run_lifecycle` returns `"skipped": n, "skipped_causes": [...]` (`B/chain/lifecycle_run.py:117,138,143`). Nothing is written and nothing is raised; later causes still apply (`lifecycle.py:5`).
- The thread therefore stays CHANGE_APPLIED, and the occurrence is still appended to the thread by step b/c.
- **Not measured:** the Cold D6/D13 thread needs COLD_START_FAILURE Findings, which UNKNOWN provenance prevents (P3). It is measurable once Q1 is ruled.

## Architect questions (batched; each has a proposed default)

1. **Q1, provenance (blocker).** As specified, MD-0's Kit batches are UNKNOWN. That kills VERIFIED (P2), every Cold COLD_START_FAILURE Finding, and all EV assessment (P3). Only dispatch, mini-depth and studies survive. Options:
   - **(a)** One B/ registry line in `B/evidence/adapters/authored_fixture_specs.py`, declaring `assetops.mechanism-dataset` v1 with the fixture moved to `backend/conversions/mechanism-v1.json`. Each MD-0 batch is published with `publish_source.main` before submit (the w402 L3 path). Readings become AUTHORED_DEMONSTRATION, "Prepared example data source". Cost: one publish per batch, and publication `recorded_at` is build time (no seam, R4 entry → DD-1).
   - **(b)** Keep "no B/ change", accept UNKNOWN, and ship MD-0 as Kobo dispatch, studies and gaps only. Cold, EV and verification move to a follow-up.
   - **(c)** Reuse an already declared fixture id. Not proposed: it mislabels lineage.
   - **Proposed default: (a).**
2. **Q2, build cost (blocker for the L2m design).** The first build is ≈ 25-30 min (P0), against a sheet bound of ≤ 3 min and a split trigger of > 5 min. The setup_cache key includes the code fingerprint, so every product edit costs one full rebuild on the first L2m test (§7). Removing verification (the pre-ruled split) does not change this order of magnitude.
   - **Proposed default:** keep the 14-day design, deliver with ≤ 256-envelope batches (measured 4× faster than hourly), and treat L2m as a cached module whose first build runs in the background tier. Alternatively, cut the normal days to the minimum the expected states need (Kobo D1-D5 and D10-D14, Cold around D6/D13), which roughly halves the time. Rule which one.
3. **Q3, split.** Both pre-ruled split triggers fire: P2 fails as specified, and P0 > 5 min.
   - **Proposed default:** if Q1 = (a), P2 is re-tested on the authored path and the split is decided by P0 alone, so MD-0b still carries verification and the close variant.
   - If Q1 = (b), the split applies as pre-ruled.
4. **Q4, Cold time zone.** Cold is Africa/Addis_Ababa, not UTC. **Proposed default:** Cold `days.json` windows are local days expressed in UTC, `[d-1 21:00Z, d 21:00Z)`. The collector's Cold window treatment is a labelled keep → CH-5a1 alongside R10.
5. **Q5, objective MG-1** has no clock seam. **Proposed default:** it is declared at build time and named in `expected-mechanism.json` only if a check finding results (R4, owner DD-1).
6. **Q6, work COMPLETE** needs a maintenance record in the case (`B/work/service.py` ~:285). **Proposed default:** ACT-C1 adds the maintenance record through the existing work writer before COMPLETE, at story time D7 09:55. That is a new input with `source: "MD-0 new example content"`.

## Rulings received (MD0-PF, build sheet §14)

- Q1 (a), the registry line, is landed in `7016c0a17`.
- Q3: the split applies, and MD-0 ships without VERIFIED/CLOSED.
- Q4, Q5 and Q6: defaults accepted.
- Q2: pending the owner. The day set is a parameter (`full` / `states`) and batches are capped at 256.
- P4, answered after the rulings: w4 has only `positive` and `missing-conflicting`, so there is no busy variant (see the handoff).
- Build progress: `.agent/MD-0-phase-1-handoff.md`.
