# Build sheet MD-0: the mechanism dataset (BASE-1)

- Architect: Claude, 2026-11-04 (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). The rulings in §1 are logged in the plan as **MD0-R**.
- Plan: `Docs/demo-sprint/client-demo-plan.html` §2.5.2, the BASE-1 and FILL-1 rows, §4.1 (L2m/L3m), §4.2 MD-0 row. Brief: `.agent/brief-MD-0-mechanism-dataset.md` (this sheet replaces it).
- **Lane 2, 3 units (est.), with a pre-ruled split** (§11). It builds after **CH-4 and CH-1b** both merge (CH1b-R2 item 4): `late_fill` needs CH-1b's drain. CH-5a1 may pre-flight in parallel, but builds only after MD-0 merges.
- Branch: `task/MD-0-mechanism-dataset`, cut from main after the CH-1b merge. **No migration and no product change.** Every write goes through an existing writer.
- Paths: `B/` = `backend/assetops_backend/`, `T/` = `backend/tests/`, `F/` = `frontend/src/`. Lines are to main `e207f328f` unless marked "(CH-1b)" (`task/CH-1b-events` `e87ffa6a1`).

## 0. Result and boundary

**Observable result.**
- `mechanism_db()` (L2m) gives a test its own copy of a seeded Postgres DB. It holds three Sites over 14 Site-local days of normal, fully checked operation, with the story events written through the product's writers and three declared gap days. Snapshots, Findings, OPP studies, threads, Actions, verification and lifecycle are all derived by the product.
- `python tools/mechanism_dataset.py build` (L3m) creates `assetops_mechanism_test` plus the work folder `var/mechanism/`. Then `chain_coherence.py collect … check --expect expected-mechanism.json` passes, with an **empty expectations list as the target** (§5).
- `late_fill(...)` fills the declared NO_DATA day at the real time. Snapshots go NO_DATA → COMPLETE, detection and threads update, and a `known_at` before the fill still shows the gap.
- A **close variant** (`variant="close"`, its own DB) proves RESOLVED_MONITORING → CLOSED after 7 fully checked days, then CLOSED → RECURRED (OD-P14: closing is proven on MD-0 only).

**Not in this slice.**
- Producer, simulator or scenario changes (DD-1).
- Any change to detection, grading, money, verification, lifecycle, thread placement or copy. A disagreement between the product and §2's expected states is **reported**, never fixed or tuned in MD-0 (§1 R7).
- The demo DB, the polish DB and `assetops_demo3_full_test`.
- Bulk ingestion (a DD-1 item if DD-0b says so).

## 1. Architect rulings (MD0-R; none needs the owner)

| # | Gap (code reality) | Ruling |
|---|---|---|
| R1 | The brief lists "day snapshots via `PostgresSnapshotStore`". Snapshots are derived: `SnapshotBuilder` (`B/chain/builder.py:42-95`) grades from adapter inputs, and the six adapters (`B/chain/measure_impls.py:110-345`) read accepted readings and selected assessments. A row appended directly would carry an `input_fp` that backfill step a, or CH-1b's drain, overwrites from the real inputs. The board would then disagree with the snapshot. | **Snapshots are never written directly.** MD-0 writes the **inputs** (readings through Batch V2 ingestion, then the assessment workers). Snapshots come only from backfill step a (`B/chain/backfill.py:175`) and the CH-1b drain. This answers brief pre-flight 2: seeding inputs first, then running step a, keeps them settled, because a later rebuild sees the same input ids and writes nothing (`builder.py:91-92`). |
| R2 | Calendar and collector are keyed by Site code. `config/chain/operating-calendar-v1.json` holds KOBO-001, COLD-LAB-001 and EV-LAB-001 (EV: TUE 08:00–16:00). `tools/checks/chain_coherence.py:34` `SITE_CODE` maps kobo/cold/ev to those codes. New codes would need a calendar edit, which changes `calendar_version` and so every demo snapshot fingerprint. | **MD-0 uses the demo Site codes inside its own `*_test` DBs.** No config edit. The W4-02 rule "authored content for MG-W402-001 only, never KOBO-001" (`backend/conversions/w4-mini-depth-cases-v1.json` statement) protects the demo DBs. MD-0 DBs are never served as the demo, and this is **enforced** (D-AW-1, Architect call while owner away; owner to review). `seed_database` and `late_fill` read `current_database()` and refuse (`MECHANISM_DB_ONLY`) any name other than `^assetops_mechanism(_close)?_test$` or the pg_harness worker-DB pattern. They always refuse `assetops_polish_*`, `assetops_demo*` and `B/chain/backfill.py:29` `PROTECTED_DATABASES`. An L0 test covers each case (§10.1). `demo_combined.py` builds and serves only `assetops_polish_<name>_test`, so it cannot target a mechanism DB. CaseRunner already posts authored batches into a converted KOBO-001 in test DBs (`T/test_s4_finding_store_postgres.py:79-126`), so this has a precedent. Provenance stays whatever the resolver gives an authored batch (P5). |
| R3 | Inputs vs outputs. | The fixture declares **inputs only**: reading blocks, cadence, the values per channel, command times and study windows. Every value carries a `source` naming the reviewed case it was copied from (§2.1). A value with no reviewed source is listed in the packet as **new example content** and reviewed as data (as OD-P13). Expected **outputs** (grades, Finding counts, thread states, study status, money) live only in the test assertions and `expected-mechanism.json`. They are taken from the design rules in §2.6 and are never written into the fixture. |
| R4 | Story time. CH-3 visibility is `coalesce(cause_known_at, recorded_at) ≤ k` from each cause fact's own recorded time (CH3-R D-b). A fact recorded at build time is hidden at story cutoffs. | **Every fact is written at its story time through the writer's existing clock seam:** `PostgresEvidenceLedger(test_decision_clock_override=…)` and `BatchIngestionService(…, Clock)` (`T/test_s4_finding_store_postgres.py:117-126`), worker `clock=`, the matcher's `now=` (`:173-176`), s6 `store_accept(…, at)` (`T/test_s6_verification_evaluator_postgres.py:189`), and the domain-intent `command_now` (`B/work/adapters/postgres_domain_intent.py:57`; `recorded_at = :now`, `:121-123`). **No row is ever UPDATEd.** A writer with no seam is reported in P1. Its fact is then recorded at build time and named in `expected-mechanism.json` with owner DD-1 (the same fix DD-1 owns for ACT-002/003). |
| R5 | setup_cache. `T/setup_cache.py:74-76` does not cache `CaseRunner`, because it shares the caller's live store and engine, and CH-2 left its seed uncached (`T/test_ch2_thread_store_postgres.py:8-10`). | **One function op that owns its resources.** `mechanism_dataset.seed_database(store, engine, variant)` builds its own `CaseRunner`, workers and stores inside, disposes them all (`pg_harness.dispose`), and returns only a plain manifest (ids by declared anchor). Register it as `("mechanism_dataset", "seed_database")` in `FUNCTION_OPS` (`T/setup_cache.py:77-81`). `mechanism_dataset.py` is a non-test module, so it is already in the code fingerprint (`:119-121`). The op uses **no monkeypatch**: any monkeypatch makes the op live (`:39-41`). Proven with `ASSETOPS_SETUP_CACHE_VERIFY=1` (§10). |
| R6 | Verification. On the s4 Site (minigrid-roles-2), VERIFIED is reached only with the TEST-SCOPED `complete_windows` monkeypatch (`T/test_s6_verification_evaluator_postgres.py:1-14,110`). That is neither a product path nor cacheable. | **Kobo in MD-0 uses the demo's role set, `kobo-001-minigrid-roles-4-demo-config.json`**, which carries the critical-load roles the evaluator needs (`B/actions/verification.py:34,123-126`). MD-0 delivers authored readings for those roles, and the evaluator decides. P2 confirms this before any code. If P2 fails, the pre-ruled split applies (§11): MD-0 ships with ACT-K1 reaching CHANGE_APPLIED, and VERIFIED/CLOSED move to MD-0b. |
| R7 | What a disagreement means. | When the product's derived output differs from the §2.6 expectation, the builder **records it verbatim in the packet and stops that assertion** (`pytest.xfail` with the MD-0 finding id). The Architect then rules it a product defect (owning slice named) or an expectation error. MD-0 never edits a rule. Two such paths are already known and are asserted as the product's current behaviour (§2.6 notes c and e). |
| R8 | The collector needs demo-only work documents. In-process `collect` calls `demo_combined_finish.load` (`tools/checks/chain_coherence.py:1023-1027`), which requires `kobo.json`, plus `cold.json` with a `failure` day `work` and `ev.json` with a `fault_day.work` (`tools/demo_combined_finish.py:573-580`). Collect itself uses only `client`, `story` and `days`. | **DS-R1 fix in MD-0.** In-process collect reads `story.json` and `days.json` directly (as the HTTP branch does, `:1029-1031`) and builds the client with `app_client` (`tools/demo_combined_finish.py:583-589`). No fake work documents are written. |
| R9 | `COH-10` reads the polish thread file `THREADS_FILE` (`chain_coherence.py:31,698,719`). Its ids are polish uuids. | **`check --threads <file>`**, defaulting to `THREADS_FILE`. MD-0's build writes `var/mechanism/expected-threads.json` in the same schema (`chain-coherence-threads/1`). Each Finding id is resolved by its **declared input anchor** (`finding.anchor_start` = the block start), and the grouping comes from the fixture's `threads` declaration. Neither is read from thread output. |
| R10 | Board day for Kobo. `day_windows` takes a Kobo day as its UTC day (`chain_coherence.py:76-78`), because the board reads `?date=`. | **Labelled keep → CH-5a1** (CH5a-R R6, Site-local board day). MD-0's `days.json` writes Kobo entries as UTC days `[dT00:00Z, d+1T00:00Z)`. CH-5a1 changes `day_windows` and `mechanism_dataset.build_work` together. |

## 2. The fixture: `backend/tests/fixtures/mechanism/mechanism-v1.json`

### 2.1 Top level

```json
{"schema": "assetops.mechanism-dataset", "version": 1,
 "label": "MD-0 mechanism dataset (authored test inputs; not Site truth, not a scenario)",
 "story": {"S": "2026-10-31T00:00:00Z", "days": {"D1": "2026-10-19", "D14": "2026-11-01"}},
 "sites": {"kobo": {...}, "cold": {...}, "ev": {...}},
 "variants": {"main": {...}, "close": {...}},
 "gaps": [...], "threads": [...], "late_fill": {...}}
```

- **Days.** D*n* = 2026-10-18 + *n*: D1 Mon 19 Oct … D13 Sat 31 Oct (= S) … D14 Sun 1 Nov. The Tuesdays are D2 (20 Oct) and D9 (27 Oct). The estate windows are then (`chain_coherence.py:55-64`): `week` = 25 Oct–1 Nov (D7–D13), `S` = D13, and `month` = 3 Oct–3 Nov.
- **Time zones.** Kobo is Africa/Addis_Ababa (UTC+3). Cold and EV take whatever `install_cold_lab`/`install_ev_lab` set (P3 records it; UTC expected).
- **Every value has a `source`.** Values copy reviewed cases:
  - `backend/conversions/s4-finding-cases-v1.json` `reading_rules` (5-min step, three feeders at 10 kW) and the F01 block (pv 40, dis 20, soc 80);
  - `backend/conversions/w4-mini-depth-cases-v1.json` variants (noon renewable hours);
  - the d-verification-window manifests (critical-load channels);
  - the W2-03/W2-04 cold rule cases and the W2-06 EV vectors (`T/ev_depth_cases.py`).
  - Values with no reviewed source are tagged `"source": "MD-0 new example content"`.
- **Schema rules (L0).**
  - Every value has a `source`.
  - No block crosses a declared gap.
  - EV blocks fall only on declared Tuesdays inside 08:00–16:00.
  - There are no outcome ids (`MG-\d`, `CC-\d`, `EV-\d`) and no output keys (`grade`, `state`, `status`, `eligible_days`, `minutes`).

### 2.2 Mini-grid: `KOBO-001` (24 h, roles-4)

| Day(s) | Declared input (cadence: the binding's 5-min step) | Story purpose |
|---|---|---|
| **Normal** D1–D3, D5, D6, D8–D10, D12–D14 | 00:00–24:00 local. Generator `STOPPED` at every step. Three feeders at 10 kW. Daylight block 06:00–18:00: pv 40, dis 20, soc 80 (F01 values). Night blocks: pv 0, dis 20, soc 80. Critical-load requested equals delivered (P2 names the reviewed source). | Fully checked, 0 candidate minutes |
| **Noon profile** | The 12:00–13:00 local hour (`MIDDAY_WINDOW_LOCAL`, `B/chain/policy.py:27`) uses the w4 `positive` variant (spare solar) on **D12 and D13**, and the w4 excluded/busy variant on every other delivered day (P4 names the exact variant ids) | 2 eligible days in the second study window, 0 in the first |
| **Overrun** D4 and D11 | The normal day, plus generator `RUNNING` 08:00–09:00 local, using the F01 block shape (stop before/after, pv 40, dis 20, soc 80) | One thread with 2 occurrences (story order D4, D11) |
| **D7** | **Nothing delivered** (declared gap `GAP-K7`, NO_DATA). The `late_fill` target (§4). | NO_DATA → filled |
| **Studies** | `MiniOpportunityWorker.reconcile("KOBO-001", start, end)` (`B/mini_decisions/worker.py:164`), then `run_pending` (`:265`), for two declared 5-day windows (`STUDY_DAYS = 5`, `B/mini_decisions/projection.py:29`): **W1 = D1–D5** and **W2 = D10–D14** | W1: decided, 0 eligible, so it is not placed (CH4-R R1). W2: 2 eligible, single source, so SUPPORTED by `frozen_result` (`projection.py:163-194`) |
| **ACT-K1** (`reserve-trial-1`) | D11 13:00 local: recommendation, then accept (`store_accept(…, at)`). D11 14:00: apply, with the change effective D12 00:00 local (`s6_action_records.EFFECTIVE` shape). D13 01:00 local: SYSTEM VERIFY freeze, bind and evaluate (`evaluate`/`bind`, `T/test_s6_verification_evaluator_postgres.py:65-73`) | VERIFIED on D12; RESOLVED_MONITORING |
| **Price and objective** | The productive-use price from `backend/conversions/demo-productive-price-publications.json`, effective before D1. Objective MG-1 from `demo-objectives.json`. Both go through their publish/declare writers (P1), with the `source` naming the file | Money and objective paths on normal days (CH-6) |

### 2.3 Cold room: `COLD-LAB-001` (24 h)

| Day(s) | Declared input | Story purpose |
|---|---|---|
| **Normal** D1, D2, D4, D5, D7–D12, D14 | 00:00–24:00. Chamber temperature at the binding cadence, inside the reviewed normal band. Grid present, reported at the cadence of the grid/backup-role bindings (`BACKUP_ROLES`, `B/chain/measure_impls.py:33`). P3 decides which readings make `chamber_temp_c` and `backup_start_chain` COMPLETE on a quiet day. | Fully checked |
| **Failure** D6 and D13 | The normal day, plus at 02:00 a grid loss → backup start requested → generator fails to start (`OBSERVED_FAILURE`, the W2-03 failure case shape) → grid restored at 02:40 | One `COLD_START_FAILURE` thread with 2 occurrences |
| **D3** | Chamber and backup readings 00:00–12:00 only (declared gap `GAP-C3`; 50% is ≥ 0.25 and < 0.80, so PARTIAL under `config/chain/coverage-policy-v1.json`) | PARTIAL |
| **ACT-C1** (domain) | D6 06:00: `DomainIntentService.create_action` (`B/work/domain_intent.py:75`) from the D6 Finding's revision, `command_now` = story time. D6 06:05: `post_intent` (`:125`). D6 09:00: a work case created and linked (`post_case_link`, `:212`; `WorkService.create_case`, `B/work/service.py:162`). D7 10:00: case event `COMPLETE` (`post_event`, `:257-285`) | ACTION_ACCEPTED on D6, ACTION_APPLIED on D7 (`B/chain/lifecycle_run.py:62-67`) |

### 2.4 EV depot: `EV-LAB-001` (TUE 08:00–16:00)

| Day | Declared input | Story purpose |
|---|---|---|
| D2 (Tue 20 Oct) | Eight 1-hour sessions 08:00–16:00, each the `complete` vector (`T/ev_depth_cases.py`). Readings are accepted, but **no EV assessment job is run** (declared gap `GAP-E2`, PENDING through `pending_jobs(ctx, ["ev_charging"])`, `measure_impls.py:318`) | PENDING |
| D9 (Tue 27 Oct) | Eight sessions, with session 3 (10:00–11:00) using the `interrupted` vector (faulted status), the rest `complete` | One `EV_INTERRUPTION` thread, 1 occurrence |
| **ACT-E1** (domain) | D9 11:30: create_action plus intent, at story time | ACTION_ACCEPTED on D9 |
| Other days | Nothing (not Tuesdays, so NOT_EXPECTED; `grading.period_bounds`, `B/chain/grading.py:43-56`) | NOT_EXPECTED, not a gap |
| Tariff | `demo-ev-tariff-publications.json` through its publish writer (P1) | EV money |

`GAP-E2` is PENDING only until a tick runs the job. A slice that ticks MD-0 sees D2 graded. That is the designed path and is asserted in §10 L2m test 6.

### 2.5 Close variant (`variants.close`, Kobo only, its own DB)

- Normal days D1–D14 as in §2.2, with no D7 gap.
- Overrun on **D2** and **D13**.
- ACT-K2: accept and apply on D2, effective D3, verified on D3 (§2.2 timings, one day earlier).
- Expected (§2.6): RESOLVED_MONITORING on D3. CLOSED on **D10**, the 7th fully checked day after D3 (D4–D10; `close_after_clean_complete_days.default = 7`, `config/chain/thread-lifecycle-v1.json`; `B/chain/lifecycle.py:239-248`). RECURRED on D13 (`TRANSITIONS`, `lifecycle.py:44-56`).
- No studies. Cold and EV are not installed.

### 2.6 Expected states (assertions only; from the design §4.4 table and the CH-3/CH-4 rules)

| Thread (fixture `threads[].name`) | Occurrences | State on D13 (S), `known_at` = D14 end | Notes |
|---|---|---|---|
| `kobo-generator` | D4, D11 | RESOLVED_MONITORING since D12; "fully checked days to close" = 7 − 2 (D13, D14) | a |
| `kobo-headroom` | W2 only (OPP placed from its eligible days, D12–D13; CH4-R R2) | OPEN | b |
| `cold-start-failure` | D6, D13 | CHANGE_APPLIED since D7. The D13 occurrence has no transition from CHANGE_APPLIED, so it is skipped and reported by `plan_lifecycle` | c |
| `ev-interruption` | D9 | ACTION_IN_HAND since D9 | d |
| close: `kobo-generator` | D2, D13 | RESOLVED_MONITORING D3 → CLOSED D10 → RECURRED D13 | e |

Notes:
- **a.** VERIFIED requires P2.
- **b.** W1 is never placed (`skipped_ineligible: 1`).
- **c.** This is the first normal-data exposure of an occurrence during CHANGE_APPLIED. The packet records the skip report verbatim, and the Architect rules it (the likely owner is CH-6/post-demo verdict work). MD-0 changes no rule.
- **d.** No case is completed.
- **e.** It proves both the OD-P14 close and the recurrence after a close.

**Grades:** every expected Site-day of every measure is COMPLETE except `GAP-K7` (NO_DATA, all Kobo measures), `GAP-C3` (PARTIAL, both Cold measures) and `GAP-E2` (PENDING). EV non-Tuesdays are NOT_EXPECTED. A noon-headroom day graded otherwise is reported (threshold 1.0, `B/chain/measures.py:49-51`).

## 3. Seeding: `backend/tests/mechanism_dataset.py` (new)

```python
FIXTURE = Path(__file__).parent / "fixtures" / "mechanism" / "mechanism-v1.json"
def load(path=FIXTURE) -> dict                       # parse + validate (the L0 schema rules, §2.1)
def seed_database(store, engine, variant="main") -> dict   # the setup_cache op (R5); returns the manifest
def late_fill(url, site_code, day, kind="normal", now=None) -> dict    # §4
def build_work(url, out: Path, variant="main") -> None     # §6: story.json, days.json, keys.json, expected-threads.json
@pytest.fixture mechanism_db / mechanism_close_db   # (in a conftest-free module: tests import and call `fresh(variant)`)
```

**Seed order** (one pass, each step at its declared story time; R4):

| # | Fact | Writer (product or reviewed test seeder) |
|---|---|---|
| 1 | Kobo Site, registration, roles-4 demo configuration, battery reserve and runtime controls | `converted_enabled` (`T/test_s2_evidence_ledger_postgres.py:146-149`), `apply_demo_configuration` (`B/sites/demo_configuration.py:127`), and the s4 `setup` steps (`T/test_s4_finding_store_postgres.py:94-100,146-160`). The roles-4 document replaces `DEMO` (P2) |
| 2 | Cold and EV Sites | `install_cold_lab` (`B/sites/cold_lab.py:53`), `install_ev_lab` (`B/sites/ev_lab.py:52`, plus `republish_corrected_bindings`, `:120`, if the demo applies it; P3), and gateway enable (`T/test_s2_evidence_ledger_postgres.py:138`) |
| 3 | Price, tariff and objective | Their publication writers (P1 names them; the demo prepare's publication step is the reference) |
| 4 | Readings, day by day, D1→D14 | `Kit` envelopes (`T/test_s2_evidence_ledger_postgres.py:65-137`) sealed per Site binding set, then `BatchIngestionService.submit` with the decision clock at the block end + 5 min (`T/test_s4_finding_store_postgres.py:117-126`). Rows come from `block_rows` (`:56-76`), generalised to the declared channels per Site |
| 5 | Assessments | `DispatchAssessmentWorker` (`B/analytics/assessment_worker.py:107`), `MiniDepthWorker` (`B/mini_depth/worker.py:56`, `reconcile` as `T/test_w402_reads_postgres.py:57-63`), `ColdAssessmentWorker` (`:217`), `EvAssessmentWorker` (`:309`). Each runs `run_pending` with the clock at the day's end + 10 min. GAP-E2's job is left unrun |
| 6 | Findings | `FindingMatcher.match` (`B/analytics/finding_service.py:36`) for dispatch. The Cold and EV matchers come through `build_finding_matcher` (`B/analytics/composition.py:70`) or their own paths (P1) |
| 7 | OPP studies | `MiniOpportunityWorker.reconcile` + `run_pending` (§2.2). Never `store.insert_opportunity_*` directly |
| 8 | Actions | s6 harness (`T/test_s6_action_store_postgres.py:119-131`, `store_accept` `T/test_s6_verification_evaluator_postgres.py:189`) for ACT-K1/K2; `DomainIntentService` / `WorkService` for ACT-C1/E1 |
| 9 | Verification | `bind`/`evaluate` then the evaluator job (`T/test_s6_verification_evaluator_postgres.py:65-73,141`) |
| 10 | Derived chain | `python -m assetops_backend.chain.backfill --steps a,b,c,d` equivalent in process: step a (`B/chain/backfill.py:175`), then `run_threads(reader, store, t, None, ("b","c","d"))` (`:33`). Then one in-process run of the CH-1b `chain_snapshots` and `chain_threads` stages, so the outbox is consumed (P6 names the call) |

- **Determinism.** UUIDs are not held (no monkeypatch, R5). Identity is by **declared anchor**: the manifest maps each `threads[].events[]` anchor to its Finding/OPP id via `finding.anchor_start` / study window. "Seeding twice gives identical rows" is asserted on a **key-normalised dump**: every table listed in §10 L2m test 2, with uuids replaced by their anchor or ordinal and clock columns dropped, as in `T/test_ch2_thread_store_postgres.py:43-55`.
- **Bounds.** The seed takes ≤ 3 min on first build (est.; measured in P0). A cache hit restores in seconds.

## 4. `late_fill(url, site_code, day, kind="normal", now=None)` (FILL-1 proof)

- Refuses unless `(site_code, day)` is a declared `gaps[]` entry whose `fill` is `true`. Only `GAP-K7` is fillable. The refusal uses `DAY_HAS_EVIDENCE` / `DUPLICATE_DAY` wording from FILL-1, with the same codes, raised as `ValueError(code)`.
- Writes the day's declared readings (`kind` = `normal` or `overrun`, from §2.2) through step 4. The **decision clock is the real clock** (no override), so `recorded_at` is now, while source times stay on D7.
- Runs step 5 for that day, step 6, then step 10.
- Returns `{"day", "kind", "readings", "events", "recorded_at", "snapshots": {measure: grade}}`.
- Tests take `k_before` = the DB `clock_timestamp()` just before the call.

## 5. `tools/checks/fixtures/chain_coherence/expected-mechanism.json` (new)

```json
{"schema": "chain-coherence-expected/1",
 "basis": "MD-0 L3m: assetops_mechanism_test built by tools/mechanism_dataset.py build (variant main), collected in process, not ticked",
 "rule": "Entries only for a declared gap day (GAP-K7, GAP-C3, GAP-E2) or a R4 writer-without-clock fact, each naming the owning slice. Any other finding is a regression. The list may only shrink.",
 "expectations": []}
```

- The target is an **empty list**.
- An entry is allowed only if its window contains a declared gap day, or it is a P1 build-time fact (R4). It carries `register: "MD-0:GAP-K7"` (etc.) and the owning slice (PC-1 → CH-5a2 for "on the days checked" wording, DD-1 for clock seams).
- Every other finding stops the slice and goes to the Architect.

## 6. L3m: `tools/mechanism_dataset.py` (new)

```
python tools/mechanism_dataset.py build [--variant main|close]   # creates assetops_mechanism_test / assetops_mechanism_close_test
python tools/mechanism_dataset.py drop  [--variant ...]          # drops only that DB and its var/ folder
```

- **Guards.**
  - The DB name is fixed per variant and must match `^assetops_mechanism(_close)?_test$`.
  - `build` drops only that name.
  - It refuses `assetops_polish_full_test`, `assetops_demo3_full_test` and any name outside the pattern.
  - The work folder is `var/mechanism/` (close: `var/mechanism_close/`) with a marker file. `drop` removes only a folder carrying the marker.
- **Steps.**
  1. Create the DB.
  2. `alembic upgrade head`.
  3. `seed_database` (the same function as L2m, with real engines on the DB URL).
  4. `build_work`.
- **`build_work` writes:**
  - `story.json`: `{"S": "2026-10-31T00:00:00Z", "code": "mechanism-v1", "sites": [...], "label": ...}`;
  - `days.json`: `{"days": [...]}`, one entry per expected Site-day: `{"site", "kind": "normal|overrun|failure|interruption|gap", "day", "start", "end", "assess": "build"}` (R10 for Kobo; Cold `[d00:00Z, d+1 00:00Z)`; EV `[d08:00Z, d16:00Z)`);
  - `keys.json`: fresh random hex for `KEY_NAMES` (`tools/demo_combined.py:64,391`);
  - `expected-threads.json` (R9).
- **Then the slice runs:**
  ```
  python tools/checks/chain_coherence.py collect --work var/mechanism --database-url <mech url> --out <scratch>/mech-bundle
  python tools/checks/chain_coherence.py check --bundle <scratch>/mech-bundle --threads var/mechanism/expected-threads.json --expect tools/checks/fixtures/chain_coherence/expected-mechanism.json
  ```
- MD-0's own L3m is **not ticked**. Slices that need a settled board run `chain_clone.py settle`-style one tick. That needs `settle` to accept the mechanism name: add `assetops_mechanism(_close)?_test` to `tools/chain_clone.py`'s accepted names (`:104-156`) and nothing else (P7).

## 7. How later slices use it (ladder additions, plan §4.1/§4.2)

| Slice | L2m (`mechanism_db()`) | L3m (`assetops_mechanism_test`) |
|---|---|---|
| CH-5a1 | Reader SQL and the request ledger (max 1 read per argument) over a full 14-day Site; `site_cutoff`; `readiness_of` over COMPLETE days | Board/summary/Portfolio A/B **on both** polish clone and mechanism. Perf probe and R3 profile also on mechanism (normal-data payload sizes). Updates R10 |
| CH-5a2 | Lens and progress truth on real threads (4 mechanisms); COH-17 claim equality | COH-1/5/8 + COH-17 = 0 with `expected-mechanism.json`; the PC-1 "on the days checked" texts appear **only** in the GAP-K7/C3/E2 windows |
| CH-5b | "Why?" trace ≤ 50 ms on the Kobo thread | ETag 304 |
| CH-6 | Portfolio week D7–D13: Kobo 6 of 7 (GAP-K7), Cold 7 of 7, EV 1 Tuesday. Money only over COMPLETE days. MG-1 judged on ≥ 3 COMPLETE days. Verdict from ACT-K1 | Coherence 0 |
| CH-9 | Daylight-window headroom on D12/D13 (eligible) vs the busy days | — |
| DD-1 | `late_fill` parity: the same assertions as the FILL-1 add-day proof | — |
| CH-5c | — | Perf on mechanism (normal-size reads) |

**Rules for every later slice.**
- A slice that changes a derived output on MD-0 lists it as old → new in its packet. The Architect accepts it, or it is a regression.
- `expected-mechanism.json` only shrinks.
- The fixture changes only by an Architect ruling (new event = new reviewed input with its `source`).
- Rebuild cost: the setup_cache key includes the code fingerprint, so the first L2m test after a product edit rebuilds (§3 bound). L3m is rebuilt once per slice at its head.

## 8. Files

| File | Change |
|---|---|
| `backend/tests/fixtures/mechanism/mechanism-v1.json` | new (§2) |
| `backend/tests/mechanism_dataset.py` | new (§3, §4, §6 `build_work`) |
| `backend/tests/setup_cache.py:77-81` | add `("mechanism_dataset", "seed_database")` to `FUNCTION_OPS` (R5) |
| `backend/tests/test_md0_fixture.py` | new, L0 |
| `backend/tests/test_md0_mechanism_postgres.py` | new, L2m |
| `tools/mechanism_dataset.py` | new, L3m (§6) |
| `tools/checks/chain_coherence.py:1012-1031` | in-process collect without `demo_combined_finish.load` (R8); `check --threads` (R9, `:698-719`) |
| `tools/checks/test_chain_coherence.py` | cases for R8/R9, and `expected-mechanism.json` loads |
| `tools/checks/fixtures/chain_coherence/expected-mechanism.json` | new (§5) |
| `tools/chain_clone.py:104-156` | accept the two mechanism names in `settle` only (P7) |

No `B/` file changes. If P1 finds that a needed writer exists only inside a tool or test module, MD-0 imports it. It never copies the SQL.

## 9. DS-R1, OL-1 and mock deviations

| Item | Touched how | Resolution |
|---|---|---|
| In-process collect needs the demo's Cold/EV work docs (`chain_coherence.py:1023-1027`) | Edited | **Fixed** (R8) |
| `COH-10` bound to the polish thread file (`:31,719`) | Edited | **Fixed** (R9): `--threads` |
| Kobo board day = UTC day (`:76-78`) | Mirrored in `build_work` | **Labelled keep → CH-5a1** (R10) |
| Calendar keyed by demo Site codes | Used, not edited | **Labelled keep → SWEEP-DS** (R2) |
| `chain_clone.settle` accepts only `chainclone_*` names | Edited (one pattern) | **Fixed** for mechanism names (P7) |
| The occurrence during CHANGE_APPLIED is skipped (§2.6 c) | Exposed, not edited | **Reported** to the Architect (R7) |

**OL-1.** The fixture names no outcome id (an L0 assertion), and `mechanism_dataset.py` imports nothing from `outcomes/`. No ratchet baseline change.

**Mock deviations.** None: no screen or copy changes.

## 10. Acceptance, tests and guards

1. **L0** `tools\run-host-tests.ps1 -- backend/tests/test_md0_fixture.py`:
   - schema and every §2.1 rule;
   - the D*n* ↔ date map;
   - EV blocks only on D2/D9 inside 08:00–16:00;
   - the gaps do not overlap W1/W2, the overrun days or ACT days;
   - `late_fill` refuses an undeclared day and a declared non-fillable day.
   - `MECHANISM_DB_ONLY`: the name check accepts the two mechanism names and a pg_harness worker name, and refuses `assetops_polish_full_test`, `assetops_demo3_full_test`, `assetops_polish_client_test` and a bare `assetops_test`. Pure function over the name.
2. **L2m** `tools\run-host-tests.ps1 -- backend/tests/test_md0_mechanism_postgres.py`:
   1. **Grades:** `grade_counts` per Site-measure equal §2.6 (all COMPLETE except the three gaps; EV non-Tuesdays NOT_EXPECTED).
   2. **Idempotent:** `seed_database` twice (two fresh DBs) gives identical key-normalised dumps of `accepted_evidence`, `finding`, `finding_revision`, `mini_opportunity_revision`, `action_event`, `domain_action`, `verification_outcome`, `site_day_snapshot`, `finding_thread*`, `chain_action_thread`. Backfill rerun writes 0 and consume rerun consumes 0.
   3. **Threads and states:** §2.6 per thread, including `skipped_ineligible: 1` (W1), occurrences in story order, and Action links (`chain_action` view: 1 MINI_TRIAL, 2 DOMAIN_INTENT).
   4. **Story time:** at `known_at` = D11 23:59 local, `kobo-generator` is ACTION_IN_HAND, not RESOLVED (R4).
   5. **Late fill (normal):** `late_fill(KOBO-001, D7)`:
      - the three Kobo measures go NO_DATA → COMPLETE;
      - a D7 dispatch selection exists with 0 candidate minutes;
      - the Finding set and thread states are unchanged;
      - at `k_before` D7 is still NO_DATA;
      - consume leaves 0 unconsumed.
   6. **Late fill (overrun),** in its own DB copy:
      - one new Finding;
      - `kobo-generator` gains an occurrence whose story order is D4, D7, D11;
      - lifecycle segments stay by story time (CH3-R);
      - `occurrence_no` is append order. The packet records the order as the product gives it (R7).
   7. **PENDING resolves:** run the EV job once, and D2 goes PENDING → COMPLETE.
   8. **Close variant:** `mechanism_close_db()` matches §2.6 e, including "fully checked days to close" = 0 on D10.
   9. **Cache:** with `ASSETOPS_SETUP_CACHE_DIR` set and `ASSETOPS_SETUP_CACHE_VERIFY=1`, the second test is a hit and verify reports no difference. The packet reports the miss time and the hit time.
3. **L3m:**
   - `python tools/mechanism_dataset.py build`, then collect, then `check --threads … --expect expected-mechanism.json` → pass with 0 unexpected;
   - the same for `--variant close`;
   - then `drop` both.
   - The packet records build time, DB size (`pg_database_size`) and the check summary line.
4. **Existing, scoped:** `tools/checks/test_chain_coherence.py`, `backend/tests/test_ch2_thread_store_postgres.py`, `backend/tests/test_ch3_lifecycle_postgres.py`, and every module importing a touched test helper (the packet lists them).
5. **Guards** (plan §4.3): A (`tools\check-architecture.ps1`) and W, run directly with no execution-policy flag. The estate guard self-tests do not run (no `configuration-persistence.ps1` edit).

## 11. Size, units and the pre-ruled split

**3 units (est.):**
- **u1:** fixture, L0, harness core and Kobo (steps 1, 3–10 for Kobo).
- **u2:** Cold and EV (steps 2, 4–8), gap days, idempotency, the setup_cache op and L2m tests 1–4 and 7.
- **u3:** `late_fill` (tests 5–6), the close variant (test 8), `tools/mechanism_dataset.py`, the R8/R9 tool edits, `expected-mechanism.json`, L3m and the packet.

**Why it could exceed 3, and what then happens** (decided now, so there is no second ruling round):
- If **P2 fails** (no product path to VERIFIED from authored roles-4 readings), or the **P0 spike** puts the first build over 5 min:
  - MD-0 ships u1–u3 without VERIFIED/CLOSED (ACT-K1 ends at CHANGE_APPLIED; test 8 and the `close` variant are removed);
  - **MD-0b (1 unit)** follows on lane 2 before CH-9, carrying the verification path and the close variant.
  - Lane 2 grows by 1 unit, and G4 by 1.
  - CH-5a1 is unaffected, because it needs only MD-0.
- If **P3** finds that a Cold or EV measure cannot be COMPLETE on a quiet day from readings alone (for example, no start-response window without a start), that measure's normal days are declared as their honest grade, with the reason, in `gaps[]`, and the Architect rules. No reading is invented to force a window.

## 12. Pre-flight (answer from code, batch them all, then stop)

- **P0, cost spike.** In a scratch `*_test` DB, time one Kobo 24 h normal day through steps 4–5 (readings at the 5-min step for every roles-4 channel), plus one Cold and one EV day. Report readings per day and seconds per day, and extrapolate the first build. This decides the §11 split.
- **P1, writers.** The writer (`path:line`) for each fact kind in §3, with its clock seam:
  - price, tariff and objective publication;
  - Cold and EV Finding matchers;
  - work case create, link and COMPLETE (`recorded_at` source);
  - the s6 VERIFY command.
  - Name any fact that cannot be written without a simulator run, or without a clock seam (R4). **Do not invent a writer.**
- **P2, verification.** Can `apply_demo_configuration` take `kobo-001-minigrid-roles-4-demo-config.json` on the converted Site? Does the evaluator give VERIFIED from authored before/after readings with no monkeypatch? Name the reviewed source of the critical-load values.
- **P3, Cold/EV quiet days.** The readings that make `chamber_temp_c`, `backup_start_chain` and `charging_kwh` COMPLETE over the declared hours (window creation rules of `cold-excursion`, `cold-start-response` and `ev-session/1`). Also the installed time zones, and whether `republish_corrected_bindings` is part of the EV install the demo uses.
- **P4, noon variants.** The exact `w4-mini-depth-cases-v1.json` variant ids for an ELIGIBLE and an EXCLUDED noon hour on a roles-4 Site, and whether they apply to KOBO-001's bindings unchanged.
- **P5, provenance.** The label the shared provenance resolver gives MD-0's batches, and whether any read refuses or hides authored evidence on KOBO-001, COLD-LAB-001 or EV-LAB-001.
- **P6, CH-1b stage call.** The in-process entry for one `chain_snapshots` + `chain_threads` stage run on one Site after CH-1b merges (`path:line`).
- **P7, `chain_clone`.** Whether `settle`'s name check is the only change needed for a mechanism DB, and whether `settle` requires a `created_record` from `create` (`tools/chain_clone.py:140-156`). If it does, MD-0's `build` writes the same record shape.

## 13. Review focus

- No row is written except through a named writer. No direct snapshot, thread or OPP insert, and no UPDATE.
- The fixture holds inputs only, each with its `source`. No expected output sits in the fixture.
- No product, rule, config or copy change. Disagreements are reported, not fixed (R7).
- The L3m tool drops only its own names, and refuses the protected DBs.
- The cache op is proven with VERIFY. The rebuild time is in the packet.

## 14. Pre-flight rulings (MD0-PF, Architect 5, Claude, 2026-11-04; owner back, so material items are recommendations)

The pre-flight is `C:\Users\assef\Bineyame\AssetOpsV1-md0\.agent\MD-0-preflight.md`. P0–P7 are accepted as build facts.

| Q | Ruling |
|---|---|
| Q1 provenance | **(a), technical ruling.** Add one registry entry, `assetops.mechanism-dataset` v1, in `B/evidence/adapters/authored_fixture_specs.py:17-20`. The fixture moves to `backend/conversions/mechanism-v1.json`, and each batch is published with `publish_source` before submit (the `test_w402_reads_postgres.py:122-146` path). This **amends §0 and §13's "no product change"** for that one declarative line. No rule, gate or copy changes. The readings then honestly read as AUTHORED_DEMONSTRATION ("Prepared example data source"). (b) would test less than the demo needs, because Cold, EV and VERIFIED all refuse UNKNOWN. (c) mislabels lineage and is refused. The publication `recorded_at` having no clock seam is an R4 entry and goes to DD-1. The seed's `MECHANISM_DB_ONLY` refusal (D-AW-1) still applies. |
| Q2 build cost | **Owner decision. The recommendation is in the coordinator reply.** Until the owner rules, build the fixture with the day set as a parameter (`full` 14 days, or `states` minimal) and deliver in batches of up to 256 envelopes (legal under the contract, same path, measured about 4× faster than hourly). |
| Q3 split | **Pre-ruled split applies (§11).** P0 is over 5 min whatever Q1 says. MD-0 ships without VERIFIED/CLOSED. **MD-0b (1 unit)** carries verification, re-tested on the authored path (P2), and the close variant. |
| Q4 Cold time zone | **Default accepted.** Cold `days.json` entries are Addis local days expressed in UTC, `[d-1 21:00Z, d 21:00Z)`, written so by MD-0 now. The collector's board-query canonicalisation stays with CH-5a1 (R10). This supersedes the §6 text "Cold `[d00:00Z, d+1 00:00Z)`". CH5a1-R Q8 is amended to match (CH-5a1 changes only the collector and `day_windows`). |
| Q5 MG-1 | **Default accepted.** It is declared at build time and named in `expected-mechanism.json` only if a check finding results (R4 → DD-1). |
| Q6 work COMPLETE | **Default accepted.** ACT-C1 adds a maintenance record through the existing work writer before COMPLETE, at story time D7 09:55, with `source: "MD-0 new example content"`. That is an input, reviewed as data. |
| D-AW-3 | Cannot be measured until MD-0b has Cold Findings. Code reading confirms the cause is skipped silently (`B/chain/lifecycle.py:45-56`, `lifecycle_run.py:117-143`). The recommendation goes to the owner (coordinator reply). |

## 15. Scope ruling MD0-S2 (Architect 5, 2026-11-04): Kobo-first MD-0. The owner is back, so this is flagged for owner confirmation

**Context.** After two passes (`f631ba8f1`, `cf7976887`; `AssetOpsV1-md0\.agent\MD-0-phase-2-handoff.md`), Cold and EV turn out to need test-only V4 event envelopes and simulated clock attestations, which would re-implement their producer paths in test code. That is well beyond 3 units, and it is the kind of test-only producer the honesty rules distrust.

**Ruling: option (a), Kobo-first.**
- **MD-0 = KOBO-001 only.**
  - Normal and event days, gap GAP-K7, `late_fill`, ACT-K1 to CHANGE_APPLIED (VERIFIED/CLOSED stay in MD-0b, MD0-PF Q3), the noon spare-solar remap so studies have eligible days, the cache fingerprint including `tools/demo_combined_kobo.py`, `seed_database`, L2m tests, `tools/mechanism_dataset.py` and `expected-mechanism.json` (Kobo entries only).
  - **Plus one Kobo recurrence day after ACT-K1's apply.** This is the D-AW-3 record: the lifecycle mechanism is the same for every Site type, so Kobo proves it. It goes in the base variant only. The close variant (MD-0b) has no such day.
- **Size:** 3.5 units in total, about 1.5 already spent and about 2 remaining. MD-0b stays 1 unit (verification and close, on Kobo).
- **Cold and EV are removed from MD-0.**
  - Their mechanism cases run on the polish clone (event data, L3), as before.
  - Their normal-data proof moves to DD-1's real baseline (the finish-check rows and the DD-1 L3 coherence), on the honest producer path.
  - Every later sheet's Cold/EV L2m/L3m cases are void and read "on the DD-1 build" instead: CH-5a1 E1's GAP-C3, GAP-E2 and EV non-Tuesday lines, CH-5c, CH-6.
  - The no-longer-needed Cold/EV test envelope code is not written.
- **Why not (b).** A short `demo_combined` prepare would need DD-1's steady-day scenarios (OD-P13, not built), a build of tens of minutes, and no controlled gap or late states. It would also move DD-1 ahead of CH-5a1 and leave lane 1 idle longer.
- **Why not (c).** It produces about 3 more units of test-only producer code for Sites whose honest data arrives at DD-1 anyway.
- **Trade-off for the owner.** Cold and EV are proven on full normal data only at DD-1, after the shared reader rather than before it. The mechanisms are Site-type-agnostic, and Kobo carries every mechanism state, so the risk is in Cold/EV adapters and grades, not in the mechanisms.

**CH-5a1 start.**
- CH-5a1 may cut from main **now**, build, and run L0/L1/L2 and the polish-clone L3.
- Its Kobo L2m/L3m cases run after MD-0 (Kobo) merges, by merging main into the branch **before the review packet**.
- Its `build_work` Kobo R10 edit is made after that merge.
- MD-0 must merge before CH-5a1 goes to review.

## 16. Phase-3 rulings MD0-S3 (Architect 5, 2026-11-04; handoff `AssetOpsV1-md0\.agent\MD-0-phase-3-handoff.md`)

- **Q1, how MD-0 is used: a template DB, not an in-suite seed.**
  - **Measured.** The `states` seed takes about 904 s (21,126 readings in 133 batches, already about 159 per batch). Lever L1 is therefore moot. Shrinking `states` further would drop expected states.
  - **Ruling.**
    1. On each main merge, a background job runs `tools/mechanism_dataset.py build --variant states --budget 540`, in parts, into the template `assetops_mechanism_tpl_test`. It holds **inputs only**: seeded readings, configuration, Actions and work facts, with no derived rows. It is tagged with the fingerprint of the **input writers**: the evidence ledger and publication, s6, work and domain intent, the seed modules, `backend/conversions` and `tools/demo_combined_kobo.py`.
    2. A slice's L2m does not seed. It runs `CREATE DATABASE … TEMPLATE assetops_mechanism_tpl_test` (seconds), then the **derive step with the branch's own code** (backfill a–d and the stages, about 1–2 min), then its tests.
    3. If the branch changes an input writer, the template fingerprint mismatches and the tool **refuses** the stale template, so the slice rebuilds it (about 15 min, rare). A stale input is never used.
    4. The full 14-day L3m build runs at the gates (G3, G4) and on demand, not per merge.
  - **Owner.** The goal of option C is unchanged: fast per slice (about 2 min) and long builds only in the background. The coordinator should **inform** the owner; no re-decision is needed. The full build per merge drops to per gate, which is the one change the owner should hear.
- **Q3, opportunity studies at DB lease time: revert the worker edit.**
  - It is an untested product change, outside MD-0's scope.
  - Instead, the harness passes the existing `test_lease_clock` seam with DB now for the opportunity worker only. The packet records "studies recorded at build time" as an R4 build-time fact.
  - **Why polish works.** The demo prepare runs its workers on real time; only the readings carry story timestamps. So jobs that DB triggers enqueue at DB time are always due there. Polish also records its studies at build time.
  - The honest fix is a story-time `available_at` on the DB-trigger enqueues (0025 EV, 0029 mini-depth, the opportunity enqueue). That goes to **DD-1b R7** as a clock seam.
- **ACT-K1 applied 25 against a reserve of 20.** The rule is reserve − 5, within 15..90. The builder traces the source of each value (fixture, configuration, recommendation read) and takes the Action from the product's own recommendation for the seeded configuration. **No value is chosen to fit.** If the demo configuration itself gives 20, report it.
- **Unbound `requested-power` channels** (residential, mill). Use the demo's own `configure_at` bindings (roles-2 to roles-4). If the demo does not bind them either, dropping them is the honest product state. List them in the packet, with their effect on `productive_kwh`.

## 17. Review-finding rulings MD0-S4 (Architect 6, Claude, 2026-11-04; packet `AssetOpsV1-md0\.agent\review-packet-MD-0.md` at `5452abe29`)

**F2 root cause (measured, fixture-fidelity defect, not a product defect).**
- MD-0 writes every channel as a `STATE_AT_INSTANT` point: `kit.envelope` hard-codes `measurement="STATE_AT_INSTANT"`, `interval_start=None`, `interval_end=None` (`backend/tests/test_s2_evidence_ledger_postgres.py:100-101`), called from `mechanism_dataset.py:248`. The row shape is copied from `s4-finding-cases-v1.json reading_rules` (a dispatch-analytic test shape), not from the producer.
- The real producer emits power channels as `INTERVAL_MEAN` with `interval_start` = span start and `interval_end` = source time (`simulator/assetops_simulator/gateway/mappings.py:109-126`, `gateway/publish.py:199-203`); only state, SoC and fuel are points.
- Every chain coverage basis counts intervals only: `productive_readings` drops rows without both bounds (`B/mini_depth/read.py:396`); dispatch coverage reads only run evidence with both bounds (`B/chain/adapters/postgres_chain_inputs.py:51-54`); headroom is the renewable hour minus its gaps, and that hour has no interval inputs on a normal MD-0 day.
- Measured, SELECT only: template `assetops_mechanism_tpl_test` has `feeder_demand` 8,568 points and 360 intervals, and `pv_available_power` and `pcs_discharge_capability` almost all points. The intervals that exist are the 60 s noon-remap rows (D12/D13, so 3,600 of 86,400 s gives LOW). The polish build (real producer path) has every power role as a 300 s interval (`feeder_demand` 2,328, `generator_power` 776, and so on), and its clone grades Kobo story days PARTIAL, PARTIAL and COMPLETE (`CH-5a1-preflight.md:206`), PARTIAL only because the story days are 8 h. So real continuous data does not grade NO_DATA, and DD-1 is not affected.
- **Product note (Medium, not High, post-demo/SWEEP-DS):** the V3 authored path accepts a point on a power channel (the binding declares no measurement; only V4 checks it, `B/evidence/ledger.py:438`), and `dispatch_v3` accepts instants as a fallback (`B/analytics/dispatch_v3.py:183-187`), while chain coverage does not. A source sending point power would get Findings on NO_DATA days. No real producer does this. The fix is to reject point power at ingestion or to give one shared rule for both readers; owner informed, no demo change.

**F5 root cause (code-traced, high confidence; confirm with the assertion below). Harness clock defect.**
- On the late path the ledger stamps `decided_at` and the job's `available_at` with the DB `clock_timestamp()` at commit (`B/evidence/adapters/postgres_evidence_ledger.py:14-20, 667-670`). The harness sets the worker clock to `deliverer.latest`, which is the host `datetime.now()` taken before `submit` (`mechanism_dataset.py:262-264`, then `494-497`, `436-439`). The lease needs `available_at <= now` (`B/analytics/adapters/postgres_assessment_store.py:356-358`), so the D7 job is never due, D7 is never assessed, and no Finding can result. Host/Docker clock skew makes it worse.
- It goes unnoticed because `assert all(o.status == "DONE" ...)` passes on an empty list (`mechanism_dataset.py:439`, `501`).

**Ruling R1: option (a), make the generator producer-shaped. Technical; 1 unit fix round.**
1. Power channels go out as `INTERVAL_MEAN`, 300 s, `interval_end` = source time, on the producer's channel and role table (`mappings.py:108-126` against KOBO-001's roles-4 bindings). State, SoC and fuel stay points. Use or extend the w402 `cases._envelope` interval path; do not add a third envelope writer.
2. Add only the channels that a Kobo measure or analytic reads and MD-0 lacks. Pre-flight lists them, citing the reader. Each value is either derived from the existing block values by a rule stated in the fixture, or labelled "MD-0 new example content" and reviewed as data. No value is chosen to reach a grade.
3. Add an L1 shape-parity test: for each (device, signal) MD-0 emits, the measurement kind and interval length must equal the producer mapping's. This is the guard against the next drift.
4. F5: on `real_clock`, the worker and matcher clocks come from `_db_now(engine)` after delivery (the existing seam). `settle_day` asserts at least one DONE dispatch outcome for the delivered day, and `late_fill` asserts no PENDING dispatch job left for that day.
5. Acceptance: normal full days grade COMPLETE on `productive_kwh` and `avoidable_gen_min`, and `noon_headroom_kw` grades as the renewable hour honestly supports. The late D7 overrun opens a Finding. GAP-K7 stays NO_DATA/PENDING before the fill. Any grade that still misses is reported, never tuned.
- **Why not (b)** (a short `demo_combined` prepare into the template): it needs DD-1a's steady 24 h scenarios (OD-P13, not built). It costs about 430 s per 24 h Kobo day (DD-0 profile; about 70 min for 10 days). It loses the controlled placement of the gap, the late overrun, ACT-K1 and the recurrence. It duplicates DD-1, which BASE-1 already makes the real-producer baseline. (b) is the right *second* proof and is already planned as DD-1.
- **Why not (c)** (keep the points and count instants in the measures): that changes product rules to fit a fixture. Refused.

**R2 fingerprint.** The template holds per-day assessment, Finding, depth and study outputs, so their writers are inputs. Add `B/analytics/` (assessment worker, `dispatch_v3`, finding episode, service and store), `B/mini_depth/`, `B/mini_decisions/` and the opportunity worker package to `input_writer_files`. `B/chain/` stays out (derive). The cost is a background rebuild (about 8 min) when a slice edits them, which is correct.

**R3 COH-7a ×2 (Kobo week and month summary window).** Not added to `expected-mechanism.json` now. Re-run L3m after R1: the narrowed windows are consistent with the Site cutoff falling back to the few days that have data. If they persist, record them with owner **CH-6**, the same owner as the Cold/EV twins in `expected-today.json`, unless CH-5a1's R7 `site_cutoff` closes them first. The CH-5a1 packet must state which.

**R4 ACT-K1 reserve-20 control.** Remove it. An inert record that contradicts the demo configuration (30, `config/site-templates/kobo-mini-grid-60kw.yaml:100-101`) is a trap for CH-6 and MD-0b, which read the control in force. Verify by query, before and after, that the D4/D11 Findings pin 30 and that ACT-K1 still applies 30 → 25.

**R5 merge.** MD-0 does **not** merge as-is. Its purpose (BASE-1: mechanisms on normal, fully checked data) is unmet, and CH-5a1's Kobo L2m/L3m expectations (R5 `readiness_of` over day grades, settledness, COH-5) would be written against NO_DATA days. One fix round (R1–R4), then a fresh-Claude re-review. Classify it as discovery: the F5 cause is unproven until the assertion runs. Then merge.

**R6 CH-5a1.** Keep building on lane 1: L0/L1/L2 and the polish-clone L3 are unaffected. Do not write Kobo L2m/L3m expected values from the current template; those values are void. After the MD-0 fix merges, merge main into CH-5a1 before its packet (as §15), then make the R10 `build_work` edit. Expected delay to CH-5a1's review is about one MD-0 fix round, plus about 8 min for the template, about 4 min for L2m and about 3 min for L3m.

## 18. Re-review rulings MD0-S5 (Architect 6, Claude, 2026-11-04; review `review-MD-0.md` at `510acfa7c`)

**M2: option (A).** This restores what §2 already specifies: an excluded or busy noon on every delivered day except D12/D13. Missing evidence was never meant to produce that result.

1. **All-day channels, 300 s interval means, derived from existing block values by producer identities:**
   - `pv_power` = min(`pv_available`, the sum of the feeder loads + the charge request);
   - `storage_charge_requested_power` = 0;
   - the clinic critical requested and delivered power both equal the clinic feeder value.
   - These are written in the fixture as rules with a `source`. They are not literals.
2. **The busy noon:** 12:00–13:00 local on every delivered day except D12/D13, including the overrun, recurrence and late-fill shapes.
   - `storage_charge_requested_power` takes the block's declared `dis` value (20 kW), labelled "MD-0 new example content: battery recharging at noon".
   - The product excludes on any positive charge request (`CHARGE_OBLIGATION_ACTIVE`, `B/mini_depth/rules.py:352-353`), so no value is fitted to a threshold.
   - D12/D13 keep the w4 `positive` remap.
3. **Expected:**
   - `noon_headroom_kw` COMPLETE on every delivered day;
   - EXCLUDED on the busy days, ELIGIBLE on D12/D13;
   - W1 with 0 eligible days and not placed, W2 with 2 (as §2.6);
   - D7 after the late fill also COMPLETE.
   - Report any other constraint code or outcome as found. Do not adjust it.
4. **Invariant:** the dispatch Findings (D4, D11, D14 and the late D7) are unchanged by the new channels. Assert it.

**M1: fingerprint scope (import-traced, not a hand list).**
- Hash every repo file loaded as a module during the input build (`sys.modules` filtered to the repo after the build), except `B/chain/**`.
- Add the data directories read as files: `backend/conversions/`, `backend/migrations/`, `fixtures/`, `config/site-templates/`, and `contracts/`.
- Store the file list in the tag. `check` re-hashes that list plus the directories.
- A new import can only arrive by editing a file already in the list, so the scheme is closed.
- This covers M1's misses (`fixtures/s1/kobo-001.yaml`, the s1/s2/s6 writers, `demo_combined.py`, `pg_harness.py`). Read-only modules the seed never loads stay out, so slices that only touch reads keep the fast path.
- Do not use "the whole backend minus `chain/`": every CH-5a1/CH-6 read edit would force an 8–15 min rebuild.

**Lows: all in this round.**
- L1: assert both core measures are present on every delivered day and on D7 after the fill.
- L2: compute the fingerprint at build start, store it in the resume state, and refuse a resume if it changed.
- L3: as stated.
- L4: drop the unused `seed_database` setup_cache op.
- L5: name owners. F1 (PENDING on undelivered days after D6, not only GAP-K7) goes to CH-5a1 R5 `readiness_of`. F2b and F4 are closed by M2 (A); remove their xfails if the tests now pass, and report if they don't.

**Receipt finding:** Low, logged for SWEEP-DS. Plain-language reasons are needed for `OUTSIDE_FOUNDATION_PERIOD` and `OUTSIDE_BINDING_PERIOD`; the COMPLETED semantics stay as they are.

**Re-review:** a fresh Claude reviewer, verification class (named items). Anything unexpected escalates.

## 19. MD0b-R (Architect 7, Claude, 2026-11-04; packet `AssetOpsV1-md0b\.agent\review-packet-MD-0b.md` at `e1e05a46d`)

- **Timing deviation (Known deviation 1): accepted.** The §2.2 freeze, bind and evaluate times cannot be met under the product's freeze, pin-stability and minimum-runtime rules. The re-timed windows are recorded in the fixture with their source. Outcome days still match §2.6.
- **`generator_power` derived channel (Known deviation 2): accepted** as MD0-S4 R1.2. Its rule is the status at the mean's source time, and the review checks it against `verification_rules.py:371-536`.
- **A1, COH-8.**
  - Under CH-5a2a B6, `origin_selected` is the same thread and segment, any revision, so the refreshed origin Finding passes.
  - Add the main ×2 and close ×1 entries to `expected-mechanism.json` with `register: "MD0b-R:A1"` and owner `CH-5a2a`. CH-5a2a deletes them.
- **A2, COH-6 ×4 (close).**
  - This is a product disagreement: the board reads eligibility and the lens reads studies, which is CH4-R R7's keep. It is not a fixture fault.
  - Keep the days. Add the entries with `register: "MD0b-R:A2"` and owner `CH-6a`.
- **§5 rule text** gains a third allowed kind: "an Architect-ruled finding naming its MD0b-R (or later) item and owner". The list still only shrinks.
- **A3.** CH-6b R16 builds its own L0 and L2-synthetic case (CH-6 sheet, R16 revision MD0b-R). MD-0 is unchanged.
- **Cost.**
  - `ensure` builds only the main template by default. The close template is built on demand:
    - when the slice diff touches `B/chain/lifecycle*.py`, `B/chain/threads.py`, the thread store adapter, `config/chain/thread-lifecycle-v1.json`, `variants.close`, `backend/tests/mechanism_dataset.py` or `tools/mechanism_dataset.py`;
    - at E1/E4;
    - in the post-merge background job.
  - The close L2m test is skipped only by an explicit `--variant` selection that the runner prints, never silently. The zero-skip rule holds, because the test is simply not selected.
  - The fingerprint is not narrowed.
  - Fold Known deviation 5 (drain in its own part) into the same edit, so there is one rebuild. Report the per-step seed timings for the tiering proposal.
- **Fix round:** about 0.25 unit. Then a fresh-Claude re-review, then merge. It does not wait for CH-5a2a.
