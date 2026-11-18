# Retired v69 and S1-S7 guard plumbing

Moved here on 2026-11-18 (declutter step 5; `tools/declutter/step5_map.py`).
PIPE-1 A6 made these guards advisory; owner decisions O1 and O2 (2026-11-18) say
the v69 mock and the S1-S7 queue are no longer read. Not run by `tools/check-all.ps1`.

- `check_v69_dependency_registry.cjs`, `delivery_next_work.cjs`,
  `test_delivery_next_work.cjs`, `check_v69_ledger.py`: the retired guards
  (each has a one-line header).
- `v69-subject-area-briefs.json`, `v69-model-homes.json`: data only those guards
  read (JSON has no comment form, so no header).

Still live in `frontend/docs/architecture/`: the registry, panel contracts and
screen ledger JSON, read by the blocking `check_mock_gaps.cjs` (honest-gap
catalogue) and `tools/checks/missing-claim-scan.mjs`.
