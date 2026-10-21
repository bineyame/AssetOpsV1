# W3-03 phase handoff

Branch `task/W3-03-portfolio-composition`. Spec: `.agent/W3-03-build-spec.md` closure 4 "Six builder runs" table,
plus closure 5 (S4/S7) on main `44307534`.

## Run 1 = seam run 0a (Lane A, existing estate files) — landed

- `estate/index.py`: public `select_finding_scope(snap, tenant_id, req, scope) -> (per_site, rows)` and
  `select_action_scope(...) -> (per_site, rows)`; rows unfiltered/unsorted/unpaged, moved verbatim. `_findings`,
  `_actions` and `_finding_coverage` consume them. `_fence`/`_cursor` handle `portfolio` (kind + lens + null filter).
- `estate/evidence_money.py`: `select_evidence_scope(...) -> (per_site, rows)` (full canonical order);
  `estate/financials.py`: `select_financial_scope(...) -> (per_site, lines, applicable, groups, exclusions,
  diagnostics)` (full W3-02 order). Roots consume them.
- `estate/scope.py`: `KEYS["portfolio"]`, lens validation, `state` refused as unknown key; cursor keys = Finding keys
  + `kind`; five-part marker in `_marker_ok`/`cursor_after`/`cursor_marker`/`decode_cursor`.
- `estate/coverage.py`: Finding rows add `episode_end` (W1 selected revision; cold/EV selected heads) and
  `mechanism: None`; Action rows add private `_plans`, `_outcomes`, `_outcome_id` (`_verification_window` kept).
- `postgres_estate_read.py::verification`: plans gain `id`, `recorded_at`; both queries ordered `recorded_at, id`.
- Test: `backend/tests/test_w303_estate_cursor.py` (pure).

## Readings (Architect may overturn)

1. "Run 1" read as the first of the six runs, seam run 0a (closure 4 sequence: Lane A takes the branch for 0a first;
   1a needs reviewed 0a selectors). Closure 5 assigns 0a only "preserve `_verification_window` + exact verification
   IDs/times"; S4 and S7 `workflow_label` land in 1a/1b, so not built here.
2. Portfolio row facts exposed by the Finding selector as private keys `_domain` (stored uppercase `site_type`),
   `_episode_end`, `_mechanism`, so Findings root bytes stay identical; 1a maps them to wire `domain`,
   `episode_end`, `mechanism`.
3. Verification IDs reach the Action selector rows through private `_plans` (each `{id, recorded_at, later_start,
   later_end}`), `_outcomes` (`{outcome_id: recorded_at}`, the existing map) and `_outcome_id` (the surviving
   resolution's outcome), also via `_raw`.
4. A Portfolio cursor with nonnull `state_filter` or a `lens` outside the four lenses is a 422 shape error, not 409.
5. Cursor tests live in a new `test_w303_estate_cursor.py` (no file named in the spec for 0a).
6. The frontend `estateClient.ts` Portfolio status union (S1) is not a 0a deliverable; left for 1a/2.

## Next: run 2

Seam run 0b (Lane B): the single persisted 10-06 fixture and exact public root assertions (closure 4 B3/B4, closure 2
Q9 as amended, closure 3). Requires an independent 0a review first (unchanged W3-01/02 golden bytes).

## Run 1 checks

- Focused pure: `test_w303_estate_cursor.py`, `test_w302_estate_cursor.py`, W3-01/02 coverage/API tests: 101 passed.
- Postgres on private `w303a_test` (dropped after): W3-01 golden, index, index-EV, provenance DTO; W3-02 money
  comparability, financials/evidence links, evidence scope snapshot, evidence EV, pinned facades, plus both cursor
  files: 116 passed in 28m04s (golden response bytes unchanged).
- `tools/check-all.ps1`: all 11 guards passed. No full backend suite (run 3 owns the same-revision full suite).
