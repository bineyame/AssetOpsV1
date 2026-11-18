# Review: WD-1m (the mill verdict reads "on example data", using a class stored when the verdict is judged)

Reviewer: independent first review (Claude), fresh context. Branch `task/FUEL-WD1m-mill-example-label` at `8aeecac6f`
(WIP `0bc9c2e14`, merge `c8de79acd`, build `c79fecbce`, packet `8aeecac6f`). Diff `git diff main...HEAD`, 14 files.
Spec: WD-1-R item 4, WD-1m-R, and WD-1m-R2 route (c), in `.agent/build-sheet-FUEL-1.md`.

## Verdict: ACCEPT

There are no High or Medium findings. The two Lows below are about test strength and do not block the merge.

## What I checked

1. **Write path.** Correct.
   - `PostgresActionStore.example_source_class` (`postgres_action_store.py:784-802`) returns None for empty `days` without querying. It bounds `source_time` from the first day to the last day + 1 in Site-local time, filters to the exact used days with `= ANY(:days)`, and requires `received_at <= :k`. It returns `min(p.source_class)`.
   - The class can only be example data. `evidence_publication_class` (migration 0017:68-75) allows only `AUTHORED_DEMONSTRATION` and `REGISTERED_SIMULATION`, and both are in `EXAMPLE_SOURCES`, so `min` over the raw column is the same as `min` over the example classes.
   - The `kind`/origin guard was removed as R2 asked. The caller is the guard.
   - `MiddayShift.evaluate` (`verification_families.py:215-217`) calls the method exactly once. That happens only after `decided`, and after the `prior` replay short-circuit, so a stored verdict never re-runs the 0.6-0.9 s query. `known_at` is `now`, the same value `outcome_rows` stores as `recorded_at`.
   - `outcome_rows` writes `details.source = {"source_class": X}` and never touches `basis`. The L0 test asserts that the `basis` JSON and `basis_sha256` are byte-equal with and without the class.
   - No fakes were needed: I found no in-repo fake store that runs `MiddayShift.evaluate`. The only callers are `VerificationService.evaluate_domain_plan` and `evaluate_site_domain_plans`, and the stage and the demo mill tool reach them through `PostgresActionStore`. There is no `getattr` fallback.
2. **Read path.** Correct.
   - `postgres_chain_read.py` contains no `accepted_evidence` and no `batch_publication_link`. `test_the_board_read_statement_never_scans_evidence` pins this.
   - The lateral `v` selects `o.details->'source'->>'source_class'`, the same form as the trial path.
   - `site_chain.opportunity_actions:178-179` passes the class through only when `known`.
   - `claims.verified_actions` uses only `len(...)` of the list (`claims.py:146`), so no claims wire can gain the key.
   - `mini.py:443-444` fills `OpportunityActionFact.source_class`, and `mini.py:1085` uses `provenance_suffix(a.source_class)`. The rendered text is "ACT-002 verified on example data", which is the existing `VERIFICATION_TEXT["VERIFIED"]` literal, so no new words were added.
3. **MILL-5 and the wire.**
   - `summary_wire` adds `outcome.source_class` (`verification_families.py:470-471`). The frontend type `millVerificationClient.ts:49` is a plain TS type with no strict runtime parse, so the extra key is harmless.
   - `mill_assure` reads the class from the verdict-page body, asserts `in EXAMPLE_SOURCES` on KOBO-001, and builds the expected suffix through `provenance_suffix` by import (no retyped literal).
   - The call site `demo_combined_finish.py:919` fetches the page.
   - Both self-test FAIL cases are present (`test_demo_combined_finish_rows.py`):
     - a plain entry on an example page;
     - a None class on the Kobo page.
4. **Parity and mutations.**
   - Cases 1-6 compare the store method with the `link_rows_on`/`link_of` reference. Case 3 asserts that `classify` gives no positive class. The empty-days case is included.
   - I re-ran the mutation proofs myself, without editing the repo: a scratch pytest file monkeypatches `example_source_class` with a mutated copy of its source. All three mutants were killed:
     - dropping `= ANY(:days)` failed case 4 with `(4, 'REGISTERED_SIMULATION', None, None)`;
     - replacing `received_at <= :k` with `true` failed case 5 with `(5, 'REGISTERED_SIMULATION', None, None)`;
     - an extra mutant I added, Site-local days computed in UTC, failed case 6 with `(6, None, 'REGISTERED_SIMULATION', 'REGISTERED_SIMULATION')`.
   - **Case 7's `DISABLE TRIGGER USER` is safe.**
     - The `ALTER TABLE` runs inside an explicit `c.begin()` whose `finally` always calls `tx.rollback()`. Postgres DDL is transactional, so the trigger state is restored even if an assertion fails inside the block. The asserts sit after the `finally` anyway.
     - It holds an ACCESS EXCLUSIVE lock on `verification_outcome` only for that short transaction. That could only block a concurrent writer on the same DB, and test DBs are single-runner here.
     - It runs against whatever `ASSETOPS_TEST_DATABASE_URL` points at, which is a `*_test` DB by policy, not specifically "the harness clone". That is acceptable. Pointed at a DB the role does not own, the test would error rather than do harm.
5. **Speed.**
   - The board query recorded 0.997 ms against a 50 ms gate, a margin of about 50x. The board plan no longer touches evidence at all: one jsonb field on an index-led lateral, which the L0 structural test pins. The missing 7-run median does not matter at that margin.
   - The verdict-time query took 594-875 ms against a 3 s gate. It runs once per decided verdict and never on reads.
   - I did not re-run the speed harness. It is scratch and not committed.
6. **Goldens.**
   - No committed golden carries a stored mill outcome, a mill verdict-page wire, or a Kobo board mill entry. I searched `backend/tests/fixtures`, `tools` and `frontend/src` JSON for the mill rule id, `DOMAIN_VERDICT`, `outcome_recorded_at` and the mill text. The only hit is a route-ref fixture (`frontend/src/shell/__fixtures__/route-refs.json:166-172`), which holds a path and no wire body.
   - The existing `summary_wire` tests in `test_ch9b3_mill_verdict.py` and `test_out_c2_board.py` still pass. "No golden changed" is therefore consistent.
7. **Residual risk.**
   - **Verdicts stored before this unit show plain until E3.** This is acceptable for the demo. E3 rebuilds the demo data, `verification_outcome` is append-only, and a backfill was explicitly ruled out.
   - **It fails loudly, not silently.** MILL-5 now asserts an example class on Kobo, so if the rebuild did not produce one, the finish check FAILS instead of passing on a plain line.
8. **Test strength.** The tests are generally strong: the mutants above were killed, and the L0 board test fails if `mini.py` reverts to `provenance_suffix(None)`, because its `REGISTERED_SIMULATION` leg expects the suffix. The exceptions are the Lows below.

## Findings

### Low 1: case 7's "old verdict without `details.source`" leg cannot fail on the class path

- **Where:** `backend/tests/test_wd1m_mill_source_postgres.py:232-251` (the `verdict` fixture, `publish=False`).
- **What is wrong:** The stored class is already `None` before the key is removed, so `before` and `after` are both None. The leg cannot tell "reads NULL because the key is missing" from "reads NULL because the stored value is NULL".
- **Failure scenario:** a regression that falls back to a default when `details.source` is absent would not be caught by this leg. One example is `coalesce(o.details->'source'->>'source_class', <a class from elsewhere>)`. Another is a later change that recomputes the class for old verdicts.
- **Fix:** run this case on `published_verdict`, so that `before == "REGISTERED_SIMULATION"` and, after `details - 'source'`, `after is None`.

### Low 2: the cutoff gate on the pass-through is untested

- **Where:** `backend/assetops_backend/chain/site_chain.py:178-179`, `"source_class": ... if known else None`.
- **What is wrong:** No test pins this gate. `test_a_mill_not_judged_as_known_reads_not_yet_verified_with_the_pending_chip` uses a fake that does not carry a class.
- **Failure scenario:** none today. An unknown outcome renders as PENDING, and the PENDING text has no `{suffix}`, so dropping `if known` changes nothing on screen. It would matter only if a later text gains a suffix on a non-final state.
- **Fix (preference-level):** add `source_class="REGISTERED_SIMULATION"` to that fake's chain row, and assert that the fact's `source_class is None` when the outcome is after the cutoff.

## Residual risk not named in the packet

- **The actual Kobo demo data is unproven to yield an example class.** The packet's "REGISTERED_SIMULATION" comes from the test seed. The demo mill is judged at `mill["evaluate_at"]` story time (`tools/demo_combined_mill.py:290`). The class will only appear if two things hold:
  - the Kobo used-day batches are linked to a publication (the Kobo builder publishes registered Lab runs through `RegisteredGatewayPublisher`);
  - their `received_at` is at or before that story time.
  If either fails, E3's MILL-5 FAILS loudly by design. Expect to look there first if E3's finish check trips.
- **The branch is behind `main` by five or more commits.** `git diff HEAD...main` touches none of the files in this unit (only `actions/verification_rules.py`), so I expect no conflict, but the merge needs a re-run of the focused tests.

## Checks I ran

All runs used python `AssetOpsV1-plan2\.venv`, with PYTHONPATH set to the worktree. I confirmed that the imports resolve to `AssetOpsV1-wd1m\backend\assetops_backend` and `AssetOpsV1-wd1m\tools\demo_combined_rows.py`. Free RAM was 3.58 GB.

- **L0:** `pytest tests/test_ch9b3_mill_verdict.py tests/test_demo_combined_finish_rows.py tests/test_mb1_opportunity_board.py tests/test_ch9b1_origin_readers.py tests/test_out_c2_board.py -q` gave **102 passed** in 7.3 s.
- **Postgres** (`assetops_wd1m_test` only): `pytest tests/test_wd1m_mill_source_postgres.py tests/test_ch9b3_mill_verdict_postgres.py -q` gave **11 passed** in 88.9 s.
- **Mutants:** a scratch file outside the repo ran three mutants plus a re-run of the three WD-1m tests, giving **6 passed** (all three mutants killed) in 128 s.
- **Guards:** `tools/check-architecture.ps1` was run without `-ExecutionPolicy` and exited 1. The failures do not come from this unit, but the guard is **not verified green** on this branch.
  - **Rule 8, three messages:** the guard found no `INSERT INTO ev_consequence_*` in `financials/adapters/postgres_consequence_store.py`. This diff does not touch `financials/`, so I treat these as not caused by WD-1m. I did not re-run the guard on `main` to prove they are already there.
  - **`chain-structure.ps1` did not run:** the worktree has no `.venv` and `ASSETOPS_GUARD_PYTHON` was not set.
  - **Not run:** `check-agent-workflow.ps1`.
  - **Before merge:** the coordinator should run guards V/N with `ASSETOPS_GUARD_PYTHON` set.
- **Not run:**
  - the full suite (per the dispatch; the implementer's full-suite evidence is not in the packet, and the demo sprint has no full suite until E2);
  - the frontend (no frontend code changed);
  - the speed harness (scratch, not committed);
  - layout evidence (not layout-sensitive: the change is one suffix on an existing line).
