# K4a re-review (round 2): ACCEPT

Scope: M1, L1 (B11), B10, main merge. Commits eb62b1555, 80328f3e5, 83d7f2ef7 against 979c9da3e.

## M1 closed
- `fuel_balance_persist` (postgres_assessment_store.py ~1500-1562): the held-revision check by (site, analytic, key, revision_no) is first and returns early. An existing analytic_run with the same (site, analytic, model, window_start, window_end, input_sha256) is reused, and no new run or run-evidence rows are written. S10 raises RuntimeError if the held evidence set differs from the window's. The assessment_revision and analytic_run_assessment link rows are always inserted.
- `_insert_fuel_revision` (postgres_finding_store.py ~786): compares only the latest revision (basis and transition), per the 0015 rule.

## B10 / B11
- B10 (A,B,A,B) asserts OPENED, WITHDRAWN, REVISED, WITHDRAWN, then UNCHANGED on a fifth raise. It also checks 4 finding revisions, 2 runs, 4 assessments and 4 links, with the run mapping per revision.
- B11 asserts UNPRICED/NO_PRICE with all price and amount fields NULL. It keeps `price_known_at` = window end, which I judge correct: it records the cutoff the lookup used and is not a price or amount field. This is a reasonable reading of §9n, and no change is needed.

## Checks run
- `test_k4a_fuel_finding_postgres.py` plus `test_k4a_fuel_finding_rules.py` on assetops_k4_test: 38 passed (56 s).
- Mutation run on a scratch copy outside the repo: I replaced the latest-only replay guard with the old any-prior-revision compare. B10 FAILED and B11 passed, as expected. I did not re-run the other two named mutations myself and rely on the packet for them. This is a minor gap.
- Main merge (eb62b1555) brought only `.agent/*.md` files. Nothing unintended.

## Findings
None High or Medium. No new Lows.
