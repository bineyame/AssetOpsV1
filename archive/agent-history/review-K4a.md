# Review K4a: unexplained-fuel Finding, fuel-residual-1 money (0056), R3k filters, theft strings

- Reviewer: Claude (Opus), fresh context, first review. Not the author.
- Branch `task/DIESEL-K4a-unexplained-fuel-finding`, HEAD `ee86b5dea`, diff `main...HEAD` (26 files).
- Judged against `.agent/build-sheet-DIESEL-1.md` §9j.1-§9j.9 and §9k, and the owner decisions `owner-missing-fuel-2026-11-07.md` and `owner-fuel-scope-2026-11-07.md`.

## Verdict: FIX

There is one Medium finding. When a night's window digest returns to an earlier value, the raise path crashes. I reproduced this on Postgres. The rest of the slice is sound:

- the lifecycle table, the money, the two R3k predicates, migration 0056, the wording and the theft rewording all match the card;
- B7 and A7 kill their mutations (I re-ran both);
- the pre-existing failures are confirmed on main.

The two Lows are optional.

## Findings

### M1 (Medium): a returning window digest (A -> B -> A) crashes `raise_night`, and a fourth revision would leave the Finding stuck

- `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:1508-1530`: `fuel_balance_persist` checks idempotency only by `(site, analytic, "{tank}:{night}", revision_no)`. It then INSERTs an `analytic_run` whose key is `analytic_run_basis_unique (site_id, analytic_id, model_version, window_start, window_end, input_sha256)`, from `0007:64`.
- `backend/assetops_backend/analytics/adapters/postgres_finding_store.py:789-791` (`_insert_fuel_revision`): the replay guard asks whether *any* revision of the Finding has this `basis_sha256` and `transition`.

**Scenario.** K3 appends a new window revision whenever the digest differs from the *latest* revision (`fuel_balance/service.py:116`). The digest covers the in-window fuel records (root, head, recorded_at). So the following is a normal operational path:

1. A delivery is recorded in night N (digest B, WITHIN_MARGIN).
2. It is then corrected to the next night, so it leaves N's window.
3. The window returns to digest A, UNEXPLAINED again.

**What happens:**
- First raise: OPENED.
- Second raise: WITHDRAWN.
- Third raise: `fuel_transition` correctly decides SUPPORT_CHANGED. `fuel_balance_persist` then tries to insert a second `analytic_run` with digest A, and the insert fails with `UniqueViolation analytic_run_basis_unique`.

**Reproduced.** I wrote a scratch test that imports the B module's `kobo` fixture and drives `assetops_k4_test` through UNEXPLAINED(A) -> WITHIN_MARGIN(B) -> UNEXPLAINED(A). The third `raise_night` raised `sqlalchemy.exc.IntegrityError: duplicate key value violates unique constraint "analytic_run_basis_unique"`. The test file is at `...\scratchpad\probe\test_review_returning_basis.py`, outside the repo.

**Impact:**
- The CLI dies with a traceback instead of printing a line and exiting 2.
- K7's prepare (accept -> assess -> raise) would abort.
- The Finding stays NO_LONGER_SUPPORTED while the stored window says UNEXPLAINED.

**The second defect, behind the first.** Suppose only the run insert is fixed. A fourth revision B (WITHIN_MARGIN again) then hits the all-revisions replay guard, because rev 2 already holds `(B, NO_LONGER_SUPPORTED)`. `_insert_fuel_revision` returns None and the service reports UNCHANGED. The Finding stays SUPPORTED, priced, and visible, while the window says it is explained. This is exactly the LR-01 defect that `0015_finding_returning_basis.py` fixed for dispatch: "the matcher's replay guard now compares only with the Finding's latest revision".

**Origin.** The card itself says "(`analytic_run_basis_unique` already makes the run unique)" and "(`finding_revision_basis_unique` and the "cites `W.id`" rule)" (§9j.4). The second of those constraints was dropped in 0015. The builder followed the card literally, so this is a spec-induced gap, not builder carelessness.

**Fix (small; the coordinator may want an Architect nod because it refines §9j.4's literal idempotency rule):**
- (a) In `fuel_balance_persist`, reuse an existing `analytic_run` with the same basis key. Then insert the new `assessment_revision` and the `analytic_run_assessment` link under it, and keep the by-revision-number check first.
- (b) In `_insert_fuel_revision`, compare only with the Finding's *latest* revision, the house rule since 0015. The `fuel_transition` "latest cites W.id" check already covers the idempotent rerun, so the guard is redundant for that case anyway.
- (c) Add an L2 case, A -> B -> A -> B, asserting REVISED and then WITHDRAWN. B3's synthetic `input_sha256` includes the clock, so it can never produce a returning digest. That is why the current tests miss this.

### L1 (Low): "price as known at the window end" is untested; a mutation to `known_at = now` survives

- `backend/assetops_backend/fuel_balance/findings_service.py:90` passes `w.window_end` as the price `known_at`. The code is correct.
- I mutated it to `now` (the raise instant) on a scratch copy and ran all of `test_k4a_fuel_finding_postgres.py` and `test_k4a_fuel_finding_rules.py`: **36 passed**. The mutation survives.
- Part C would survive it too. Kisiwa diesel v1 is published long before night 4, so both cutoffs select the same revision.
- **Failure it would miss:** a price declared after the night but before the raise would wrongly price the night. The card says the night is priced "as known at the window end", so that night should be UNPRICED `NO_PRICE`.
- **Fix:** add one B case that publishes the price after `window_end` and before the raise, and asserts UNPRICED `NO_PRICE`. Optional, because the code is right today.

### L2 (Low): DEV-3 can pass vacuously at E3

- `tools/demo_combined_finish.py:957-959`: KIS-4 returns `{"kisiwa": "not in this dataset (K7 adds it)", "checked": 0}` when there is no `KISIWA-001` Site.
- Before K7 this is the right call. Failing would break every prepare, and the 4-tuple `CHECKS` shape has no skip flag.
- When Kisiwa is present the row really checks. `kis4` asserts at least one SUPPORTED Finding, a consequence per SUPPORTED revision, exact litres and amounts, the price re-run, no dispatch citation, and no sums.
- **The risk:** at E3, a prepare that silently lost Kisiwa (a renamed code, or a skipped K7 step) would report KIS-4 as passing. Only a human reading `"kisiwa": "present"` would notice.
- **Fix:** record a carry for K7's card. Once K7 merges, KIS-4 should fail when Kisiwa is absent, either by flipping the branch or by keying it on the prepare's site list. No K4a code change is needed.

## Check-by-check

### 1. Finding and lifecycle

- `fuel_transition` (`findings_service.py:28-44`) is §9j.4's table in first-match order.
- `fuel_apply` and `_insert_fuel_finding` / `_insert_fuel_revision` write every column the card pins:
  - `generator_asset_id` NULL, the tank as `subject_asset_id`, NULL minutes;
  - title, claim keys, limitations order, `support_sha256`, cold's `cited_evidence_sha256` rule;
  - the `finding_revision_assessment` / evidence links.
- The thread identity is `SUBJECT_COLUMN["fuel_balance"] = "subject_asset_id"`, giving `(tenant, site, UNEXPLAINED_FUEL, ASSET, tank)`. B3/B4 proves occurrence 2 on one thread and R8's unsettled True to False transition.
- The cutoff:
  - The window is read with `recorded_at <= known_at` (`night_window_on`).
  - The price is read at `window_end`.
  - The reads filter revisions by `created_at <= known_at`.
- Concurrency: the advisory lock is taken before the held-Finding read on a READ COMMITTED connection (`transaction()` is a plain `begin()`), so a second raise sees the first one's commit.
- The returning-basis path fails (M1).

### 2. Money

- `fuel_residual_append` stores exact `fmt` litres and `Fraction(residual) x Fraction(str(price))` amounts. It sets `price_known_at = window_end` and builds the basis digest exactly as §9j.5 specifies.
- The row goes in its own table: append-only, `UNIQUE (finding_revision_id)`, and written only on SUPPORTED.
- A5 kills the "display litres" mutation (119.62 vs 119.57).
- A3 maps all six reasons to the three literals, with no digit in an UNPRICED line.
- B3 and the Part C test assert that no `financial_consequence_revision` row cites a fuel Finding (C: 4 passed per the packet; not re-run, see below).
- A6's AST no-sum guard is non-vacuous.
- The price-cutoff test is missing (L1).

### 3. R3k filters

- Both predicates are present, with the §9k.2 docstrings verbatim. The `finding_read.py:239` port line is type-only.
- I grepped `financials/` and `scheduling/` for `finding_revision` myself:
  - `scheduling/` has no hits.
  - `financials/consequence_read.py:271/301` use `finding_provenance` by an id that comes from a consequence row.
  - Every hit in `postgres_consequence_store.py` falls into one of these groups: by id (`load_input_on`, `evidence_target`, `chain`, `selected_on`); keyed on Findings that already have `financial_consequence_revision` rows (`site_history`); cold-only; or the now-filtered `latest_revisions_overlapping`.
- The packet's S9 list is complete. Its line numbers for the later hits are the pre-K4a numbers (for example, `site_history` is now at `:466`, not `:428`). That is cosmetic.
- The fuel Finding's NULL generator makes `evidence_no_op` return NO_OP_ASSET (A9, B9).

### 4. Migration 0056

- It chains `0055 -> 0056`. The two CHECKs are 0025's text plus one arm each; B1 compares the `pg_get_constraintdef` text against the downgraded text plus the arm.
- The table, constraints, index and trigger are verbatim from §9j.3.
- The downgrade locks, refuses on a fuel Finding or revision or any consequence row, and then restores the 0025 CHECKs.
- K3's head test is head-agnostic: `alembic_head()` at `:187`, `:214`, `:234`, `:236`. These are bookkeeping edits only.

### 5. Wording

- The `finding_text.py` literals are byte-equal to §9j.7.
- Both `MiniPerformance.tsx` strings match §9j.7, each with the MD-FUEL-K-2 comment verbatim. The comment's v69 citation is correct: v69 `index.html:627-628` holds "never infer theft" and "cannot establish theft".
- `git grep -i "theft|stolen|siphon|pilfer|stole"` over `frontend/src`, `backend/assetops_backend`, `config` and `contracts` (tests excluded) finds only those two comments and the `finding_text.py` docstring.
- **DEV-4 is fair.** It strips only whole lines that begin with `//`. Trailing `//` comments, `/* */` and JSX `{/* */}` comments are still scanned, so the scan is stricter, not looser. The test proves that the comment does contain the word and that an old string in code would be caught. The only blind spot is a template-literal line beginning with `//`, which is negligible. `miniFuelRoutes.test.tsx:191` now compares against the imported constant (as carded), so A4 is the real guard on that text.

### 6. DEV-3

Safe for now, and it does check fully at E3 when Kisiwa is present. See L2 for the risk at E3.

### 7. Test strength (mutations re-run by me on scratch copies; no repo file edited, worktree clean after)

| Mutation | Tests run | Result |
|---|---|---|
| m1: remove `AND r.domain = :d AND r.analytic_id = :a` from `findings_over` | B7 | **killed** (fuel id returned with the dispatch id) |
| m2: delete the "held, cites W" idempotent row of `fuel_transition` | L0 rules file | **killed** (both A7 tests) |
| m3: price `known_at = now` instead of `window_end` | B + L0 (36 tests) | **survived** (L1) |

- I did not re-run the builder's B8 mutation proof. B8's assertion (`dispatch_money(fuel) == 0` after an assumption publish) is direct, and the m1 result shows the harness discriminates.

### 8. Pre-existing failures

- `test_s4_schedule_health_postgres.py::TestDatabaseTime::test_skewed_application_clocks_do_not_move_s3_matcher_retry_or_health_times` **fails on main**: plan2 at `4f6a5cae4`, read-only, on an `assetops_k4_test` harness clone, with `assessment_worker.utc_now()` not skewed. It fails the same way on the K4a branch. Pre-existing.
- I did not re-run the six w301 golden failures; I am relying on the packet's identical-text comparison for those.

## Checks run

All runs used the plan2 venv python, with `PYTHONPATH` pointing at the k4a worktree (imports verified to resolve into `AssetOpsV1-k4a`) and the DB `assetops_k4_test` (harness clones only). Free RAM was 4.0 GB before the runs.

- `test_k4a_fuel_finding_rules.py`, `test_tfc2.py`, `test_out_b2_vocabulary.py`: 39 passed.
- `test_k4a_fuel_finding_postgres.py`: 12 passed (40 s).
- Adjacent tests (`test_s4_finding_domain_filter.py`, `test_s4_finding_domain_filter_postgres.py`, `test_s4_schedule_upstream_unit.py`, `test_s4_consequence_cause_dispatch.py`, `test_s4_evidence_drain.py`, `test_k3_fuel_balance_postgres.py`) plus the schedule-health case: 34 passed, 1 failed. The failure is the pre-existing schedule-health case above.
- Scratch M1 probe: failed with `analytic_run_basis_unique`, as described.
- `tools\check-architecture.ps1`: passed. `tools\check-agent-workflow.ps1`: passed. Both were run directly, with no `-ExecutionPolicy`.
- `npx.cmd tsc --noEmit` (k4a frontend): exit 0.

**Not run:**
- Part C (`host/tests/test_k4a_kisiwa_night4.py`): it already passed per the packet (4 passed, 348 s), and the dispatch said to skip it.
- The full suites, `check-all.ps1` (which includes guard V), the frontend vitest/build, B8 and the w301 goldens.
