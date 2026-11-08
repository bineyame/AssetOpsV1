# Review packet K4a: unexplained-fuel Finding, fuel-residual-1 money (0056), theft strings reworded

- Task: DIESEL-K4a, `.agent/build-sheet-DIESEL-1.md` §9j.1-§9j.9 (ruling DIESEL-1-R3j, 662b2cf91) as amended by §9k (DIESEL-1-R3k, ff3837089).
- Branch `task/DIESEL-K4a-unexplained-fuel-finding`, worktree `AssetOpsV1-k4a`, merged with main at ff3837089. DB: `assetops_k4_test` and its harness clones only.
- USER_REVIEW_REQUIRED: none stated for K4a. Opus first review comes next; the K4b placement work follows.

## Outcome delivered

- **Migration `0056_unexplained_fuel_finding`.** It recreates `finding_domain_subject` / `finding_revision_domain_minutes` as 0025 left them, plus one `fuel_balance` arm each (0025's `_domain_checks` shape). It also adds `fuel_residual_consequence_revision` exactly as §9j.3 specifies: CHECKs, FKs, `UNIQUE (finding_revision_id)`, index and append-only trigger. Downgrade locks the tables and refuses while any `fuel_balance` Finding/revision or consequence row exists.
- **Stores.** Each fuel write goes through the module that already writes that table:
  - `PostgresAssessmentStore.fuel_balance_persist`: the `fuel-balance-1` run and assessment revision for one window revision. It is idempotent on `(site, analytic, "{tank}:{night}", revision)`.
  - `PostgresFindingStore.fuel_apply` with `fuel_held`, `_insert_fuel_finding` and `_insert_fuel_revision`: the cold shape, the claim and limitations of §9j.4, and the consequence call on SUPPORTED.
  - `PostgresConsequenceStore.fuel_residual_append`: exact litres; PRICED amounts = litres x price as `Fraction`; UNPRICED carries the selection's reason; basis digest as §9j.5.
- **Service, composition and CLI.**
  - `fuel_balance/findings_service.py`: `FuelFindingService.raise_night` runs in one transaction on the assessment store's `transaction()` (the cold worker pattern, `assessment_worker.py:250`). It contains `fuel_transition`, the pure form of the §9j.4 table.
  - `fuel_balance/composition.py`: `build_fuel_finding_service(url, *, test_db_clock_override)`.
  - `fuel_balance/worker.py raise`.
- **Wording.**
  - `fuel_balance/finding_text.py` holds the §9j.7 literals verbatim and `finding_lines`.
  - The two "theft" strings in `MiniPerformance.tsx` are reworded, each with the MD-FUEL-K-2 header comment verbatim.
- **Reads.** `FuelFinding` / `FuelFindingReadPort` in `model.py`, and `fuel_findings` / `fuel_finding` on `PostgresFuelBalanceStore` (REPEATABLE READ READ ONLY).
- **Maps.** `SUBJECT_COLUMN["fuel_balance"]` and `SITE_TYPE_OF_DOMAIN["fuel_balance"]`.
- **R3k filters.**
  - `findings_over(..., domain=DOMAIN, analytic_id=DISPATCH_ANALYTIC_ID)` with `AND r.domain = :d AND r.analytic_id = :a`, plus the type-only port line at `finding_read.py:239`.
  - `latest_revisions_overlapping` gains `AND r.domain = 'mini_grid'`.
  - Both docstrings are verbatim from §9k.2. No caller, worker or fake changed.
- **K3 Lows closed.**
  - L1: tfc2 FAILED-at-end case (3300).
  - L2: `rules.py` docstring names `idle_slot` and R3h; the line at `:174` is wrapped.
  - K3's head test is head-agnostic.
- **Finish row KIS-4.** `demo_rows.kis4` (pure) is wired after PV-A in `demo_combined_finish.py`, with pass/fail self-tests.

## Pre-flight answers (original stop, then §9k)

- (a) The cold worker opens `self.store.transaction()` at `assessment_worker.py:250` and passes `c` to `cold_persist` (`:238`) and `cold_apply` (`:242`). `findings_service.py` copies this.
- (b) Readers.
  - The two unfiltered ones are now filtered (R3k).
  - These are safe as before: domain-filtered `index_snapshot`/`episodes`/`_FINDING_HEADS`/estate reads; `work_read._pin` and `site_index` (unknown domain → UNKNOWN); `outcome_map` (NOT_MAPPED); `placement` (UNPRICED_OTHER); id lookups in `chain/lookup.py`; domain-agnostic thread sources.
- (c) `SUBJECT_COLUMN` needs the entry and got it. `SITE_TYPE_OF_DOMAIN` got it as carded; it is keyed by Site domain everywhere and harmless. The other `cold_chain` maps are keyed by job, estate, outcome or action domain and need no entry (listed in the stop report).
- (d) Lifecycle runner: `measures_for` returns `()` for an unknown mechanism and `complete_days` returns an empty set, so nothing raises. A fuel thread never closes on clean days; the SUPPORT_LOST path withdraws it.
- (e) Guards: see the memberships below.
- **S9 list** (`git grep -n "FROM finding_revision" backend/assetops_backend/financials backend/assetops_backend/scheduling`). `scheduling/` has no hits; it reaches Findings only through `findings_over`, now filtered. The hits in `financials/adapters/postgres_consequence_store.py`:
  - `:104`/`:114`, `load_input_on`. By id. Its only `derive()` targets come from FINDING_REVISION_APPENDED (0022 `WHEN mini_grid`), ASSUMPTION (now filtered), or EVIDENCE (no-op `NO_OP_ASSET` for fuel, A9/B9). The other callers (W3-01 Run 6, Trial comparison) pass pinned dispatch ids. Safe.
  - `:319`, `evidence_target`. By the work row's id; feeds `evidence_no_op`, which gives NO_OP_ASSET for fuel. Safe.
  - `:392-395`, `latest_revisions_overlapping`. **Filtered `r.domain = 'mini_grid'` (R3k).**
  - `:428`, `site_history`. Read-only, and only for Findings that already have `financial_consequence_revision` rows (never fuel). Safe.
  - `:497`, `chain()`. The window of one given revision, for its pending-work list. Read-only, no money. Safe.
  - `:526`/`:529`, `selected_on`. By id, read-only. Callers pass dispatch pins. Safe.
  - `:873`/`:877`/`:880`/`:884`/`:901`/`:926`. Cold reads, `r.domain = 'cold_chain'` (or by a cold revision id). Safe.
  - **No fourth money path, so no S9 stop.**

## Files materially changed

- Migration: `backend/migrations/versions/0056_unexplained_fuel_finding.py`.
- Store edits:
  - `analytics/adapters/postgres_assessment_store.py`: `fuel_balance_persist` only.
  - `analytics/adapters/postgres_finding_store.py`: constants, `_fuel_key`, `fuel_held`/`fuel_apply`/private inserts, `findings_over` filter, docstring line.
  - `analytics/finding_read.py:239`: type-only port line.
  - `financials/adapters/postgres_consequence_store.py`: `fuel_residual_append`, `latest_revisions_overlapping` filter.
- `fuel_balance/`:
  - New: `finding_text.py`, `findings_service.py`.
  - Changed: `model.py`, `adapters/postgres_fuel_balance_store.py`, `composition.py`, `worker.py`, `rules.py` (docstring only).
- `chain/threads.py:31`, `chain/read.py:25`.
- Frontend: `frontend/src/sites/MiniPerformance.tsx` (the two strings), `__tests__/miniFuelRoutes.test.tsx` (`:188` retyped, `:191` imports `FUEL_NOTICE`).
- Tools: `tools/demo_combined_rows.py`, `tools/demo_combined_finish.py`, `tools/checks/configuration-persistence.ps1` (membership only).
- Tests:
  - New: `backend/tests/test_k4a_fuel_finding_rules.py`, `backend/tests/test_k4a_fuel_finding_postgres.py`, `host/tests/test_k4a_kisiwa_night4.py`.
  - Edited: `test_tfc2.py` (one case), `test_k3_fuel_balance_postgres.py` (head bookkeeping), `test_out_b2_vocabulary.py` (K4a literals scanned).

## Guard memberships (membership only, never a loosened rule)

- `$consequenceTables` gains `fuel_residual_consequence_revision`. The consequence store stays the sole writer, now of that table too.
- `$fuelTransactionOwner = backend/assetops_backend/fuel_balance/findings_service.py`, declared beside `$coldTransactionOwner` and added to the owner-existence loop. `$coldTransactionOwner` appears in no other list.
- No writer probe was added (S-g not triggered).

## Acceptance criteria

- §9j.3 migration: **met.** B1 checks:
  - up/down/up, with the two CHECKs equal to 0025's flat OR list plus the arm;
  - columns, constraints, index and trigger;
  - downgrade refused with a fuel Finding, and with only a consequence row (which cites a dispatch Finding);
  - UPDATE/DELETE refused;
  - three `fuel_residual_priced` violations fail;
  - a fuel Finding with a generator fails the subject CHECK.
- §9j.4 lifecycle: **met.**
  - A7 runs all five table rows plus the service statuses on fakes; the idempotent rerun writes nothing.
  - B3 on Postgres: OPENED + PRICED → UNCHANGED → WITHDRAWN (no consequence) → a second night as occurrence 2 on the same thread.
  - Two statuses that writing nothing was carded to give, also covered: NO_WINDOW and NO_FINDING.
- §9j.5 money: **met.** A5 shows exact amounts, and 119.57, not 119.62. B3 and C cover PRICED; B3 covers UNPRICED NO_PRICE. No `financial_consequence_revision` row cites a fuel Finding (B3, B8, C).
- §9j.6 service and CLI: **met.** CLI test: one line per night (OPENED, NO_WINDOW); an unknown Site exits 2.
- §9j.7 wording: **met.** A1-A4; vocabulary scan; C rendered lines.
- Threads: **met.** B3/B4: `finding_thread` UNEXPLAINED_FUEL / ASSET / tank / `UNEXPLAINED_FUEL@fuel-finding/1`. R8 unsettled is True before `chain_threads` consumed and False after.
- Reads (B5): **met**, as known before and after the withdrawal.
- K3 Lows L1 and L2, and the head-agnostic edit: **met.**
- KIS-4: **met** as pure logic with pass and fail bodies. It passes on the night-4 database (C). See K4a-DEV-3.
- §9k B7, B8, B9, A9: **met**, with the proofs below.
- Night 4 (C), as stored:
  - band `286971499/3000000`..`144342833/1000000`, |Δ| to F0 = 0;
  - PRICED with Kisiwa diesel v1 (`price_revision_id` equals the re-run and the first diesel revision), price 1.25 USD;
  - `amount_low 286971499/2400000`, `amount_high 180.42854125`.
- Night 4 (C), as rendered: "About 95.7–144.3 L left the tank on the night of 4 Oct (6 pm to noon) …", "The tank sensor sent no readings from 00:45 to 02:30.", "Worth about 119.57–180.43 USD at your declared 1.25 USD per litre (a modelled range that includes the stated margin)". All match §9j.7, so S1 was not triggered.

## Must-fail proofs run by the builder

Each mutation was edited, run and restored with `git checkout --`.

- **B7.** Removed `AND r.domain = :d AND r.analytic_id = :a`. B7 fails: `findings_over` returns the fuel id first (`['82ac…'] == ['88e1…']`).
- **B8.** Removed `AND r.domain = 'mini_grid'`. B8 fails: `assert 1 == 0` on `dispatch_money(fuel finding)`. So without the filter a `financial_consequence_revision` row cites the fuel Finding, which confirms the R3k gap.
- **A-tests with built-in non-vacuity:**
  - A1: half-even `1.25/2.35` → `1.2–2.4`; `money2` vs float `round` on 2.675.
  - A4: the old string is seen by the scan.
  - A6: positive AST cases.
  - A9: a dispatch revision of the same generator is not NO_OP_ASSET.
  - KIS-4: six false bodies each fail.
- **Left for the reviewer.** B2 (drop the 0022 `WHEN`) and B9 by direct `evidence_no_op` (§9k.5) need a migration or a fuel-shaped write that the CHECK forbids; A9 covers B9's assertion.

## Checks run

Python is the plan2 `.venv`. PYTHONPATH is the worktree paths (imports verified to resolve into `AssetOpsV1-k4a`). DB is `assetops_k4_test`.

- L0: `test_k4a_fuel_finding_rules.py` + `test_demo_combined_finish_rows.py`: 55 passed. `test_tfc2.py` + `test_out_b2_vocabulary.py` were also green in batch 1.
- Batch 1: K4a L0+L2, K3 L0/L2, K2, tfc2, fuel_cost_v2 (+pg), w401, CH-2 (×3), vocabulary: **176 passed** (186 s).
- Batch 2: R3k list (domain filter ×2, upstream unit, finding api, finding read pg, recompute pg, cause dispatch, evidence drain ×2), schedule health pg, W2-03 cold ×4, W2-06 EV ×7: **252 passed, 1 failed** (47 min). The failure is `test_s4_schedule_health_postgres.py::TestDatabaseTime::test_skewed_application_clocks_do_not_move_s3_matcher_retry_or_health_times` (`assert assessment_worker.utc_now() > datetime.now(UTC) + SKEW - 1 min`: the clock-skew patch is not live). **It fails identically on main** (plan2 tree, `78a224393`). Pre-existing, not K4a.
- Batch 3: goldens and overview: K4a L2 (12, incl. CLI), ch5a1 ×4, ch5a2, ch5b, ch6, ch6b2, ch6b, ch9b2 reserve byte-equal, mb1, pv1, w301 golden, s5 overview, s4 finding index, s6 site action index: **267 passed, 6 failed**. All 6 are `test_w301_estate_golden_postgres.py` (`public_replay[mini_grid|cold|ev|mixed]`, `clock_plus_30_days[mini_grid|mixed]`). **The same 6 fail on main.** The mini_grid failure text is identical in both trees (scratch compare: "IDENTICAL FAILURE TEXT: True"; `$.summary.claims` has `count.opportunities` that the golden lacks). Pre-existing drift, not the filter, so not S8.
- Part C `host/tests/test_k4a_kisiwa_night4.py`: **4 passed** (348 s).
- Frontend: `miniFuelRoutes.test.tsx` 11 passed; `npm run typecheck` clean; `vite build` built.
- Guards: `tools\check-all.ps1 -Python <plan2 venv>` with `ASSETOPS_GUARD_PYTHON` set: **All 17 guards passed**. These include Architecture seams (`check-architecture`), Agent workflow (`check-agent-workflow`), Navigation truthfulness, Mock deviation labels and client vocabulary, and the estate guard self-tests (15 passed).
- Mutation proofs at HEAD `72f4a41e0`; the tree was restored clean after each one.
- Not run: the full backend/frontend suites and the K3 part C parity (§9j.9: no full suite).

## Known deviations

- **K4a-DEV-1 (§9k.3, required wording).** "dispatch readers and the fuel-cost recompute target read are filtered to their domain; cold/EV Sites no longer offer their Findings to them". `findings_over` on a cold or EV Site now returns `[]` and no longer raises on an open cold Finding. `latest_revisions_overlapping` no longer offers EV Findings to `derive()`, so **EV price publications no longer run fc2 on EV Findings**. No served Cold or EV output or golden reads either function; the six w301 golden failures predate K4a and are identical on main.
- **K4a-DEV-2.** `PostgresFuelBalanceStore.night_window_on(c, t, s, night)`, a third method beside the two carded reads. It does three things on the service's connection: the clock (or test override), the `fuel-finding:` advisory lock, and the night's latest window as known then. This is what lets §9j.6's "one transaction" read the window inside the shared transaction.
- **K4a-DEV-3 (KIS-4 before K7).** On a dataset with no `KISIWA-001` Site the row returns `{"kisiwa": "not in this dataset (K7 adds it)", "checked": 0}` instead of failing. Otherwise every prepare run before K7 would fail its self-check, and the 4-tuple `CHECKS` shape (consumed by `test_demo_combined_postgres.py`) has no skip flag to add. At E3 Kisiwa is present, so the row checks. The E3 reviewer should see `"kisiwa": "present"`.
- **K4a-DEV-4 (A4 scan).** The mandated MD-FUEL-K-2 header comments quote "never infer theft" / "cannot establish theft". The A4 file scan therefore reads `MiniPerformance.tsx` with `//` line comments removed. It asserts that the comment does hold the word, and that an old string in code would be caught.
- `fuel_transition` lives in `findings_service.py`, and the Finding store imports it locally. The service must decide before persisting, and a service may not import an adapter module.
- `test_k3_fuel_balance_postgres.py` head bookkeeping also touched `:214`, `:234` and `:236` (`head(engine) == MIGRATION` → `alembic_head()`). Same §9g.5/§9j.8 B6 class, no behaviour change.

## Residual risk

- The fuel Finding is visible to the generic `/findings/{id}` route only by hand-typed id, as cold and EV Findings are. K5's panel serves it.
- A price correction after a stored consequence does not re-price it (v1, after-the-demo list).
- `fc2 load_input_on` still accepts any revision id if a future caller passes a non-dispatch id (R3k (D), after-the-demo list).

## User-review focus

None for K4a. Reviewer focus:
- the two R3k predicates and their effect on cold/EV (DEV-1);
- the consequence basis digest;
- DEV-2 and DEV-3;
- the night-4 strings.
