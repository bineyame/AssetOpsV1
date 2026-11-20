# 4b2 packet: the money leaves (providers)

Implementer (Claude), 2026-11-20. Branch `task/4b2-money-providers` off `main` `e88641e97` (4b1 merged); worktree
`/opt/assetecon/AssetOpsV1-4b2`. Spec `spec.md` rev 3 §3 to §5; rulings D-4B.3 to .9, .12 to .15, .18; guide rev 3.
Mid-build count: **1** (Q2, open, default applied). Not merged.

**Module paths** (`PYTHONPATH` = worktree `backend`, `contracts`, `simulator`): `assetops_backend` →
`/opt/assetecon/AssetOpsV1-4b2/backend/assetops_backend/__init__.py`, `assetops_contracts` → `.../contracts/...`,
`assetops_simulator` → `.../simulator/...`. Interpreter `/opt/assetecon/AssetOpsV1/.venv/bin/python`.

## Files

- `backend/assetops_backend/structure/money.py` (new): `CommercialLeafSource`, `COST_STATUSES`, `CHARGE_RECORD`,
  `RECEIPT_RECORD`, `READ_AS`; §3.3's two orders of judgement; one month read per context object (D-4B.12).
- `structure/sources.py`: `PROVIDED_ELSE_ASSUMED` (sixth), the six `SOURCE_STATE` changes, `STATED_STATE`;
  `ProductLeafSource` gives the five new PROVIDED leaves `NOT_CONNECTED` with `filled_by` (`COMMERCIAL_LEAVES`).
- `structure/composition.py`: commercial reads built third; disposes all built stores on failure and on `dispose()`.
- `backend/tests/test_3b3_structure_evaluate.py`: T6 table and body only (P2).
- New: `backend/tests/fixtures/money_leaves_lakeside.json` (batch E generated from DS1b, verbatim),
  `backend/tests/test_4b_money_leaves.py`, `test_4b_money_leaves_postgres.py`,
  `simulator/tests/world/test_4b_fixture_parity.py` (test 5; deviation 1).
- `specs/4b-money-leaves/`: this packet, `mid-build-questions.md` (Q2), spec status; `.ai/state/data.md` + index.

## Done questions (spec §6)

1. Yes (4b1, unchanged; S9 in the regression run).
2. Yes: Kobo October revenue 3458.00, collected 3180.00, outstanding 278.00, contribution 883.00 (= the pack's
   `derived-values.json`), each with evidence, sources, origins (test 1, Postgres 1 and 2).
3. Yes: every absent value names `READ_AS` with a true cause (tests 1, 2, 6, 7, 12; test 10 checks 20+ of them);
   a recorded 0 only when its kind is held for the month.
4. Yes: `cost_to_serve`/`contribution` carry `(observed-financial, source-emulated)`, weakest `source-emulated`.
5. Yes: test 3 (k of n with `out` per factor). 6. Yes: tests 1, 2, 6, 8, 11, 12. 7. Yes: test 9 (and a probe:
   one `site_month` and one `latest_revisions` per Site read, none reused).
8. Yes, plus deviation 1's simulator test file.

## Checks (revision `8bb488bae`; evidence `/opt/assetecon/evidence/4b2/`)

- Red first: tests on main's code: 16 failed, 1 passed (test 5).
- No database, focused + regression (`test_4b_money_leaves`, `test_3b3_structure_evaluate`, `test_4b1_stated_nodes`,
  `test_3a4_commercial_months`, `test_3b1_structure_registry`, `test_3b3_window_price_selection`): **268 passed**, 5 s.
- Simulator `tests/world/test_4b_fixture_parity.py`: 1 passed.
- Postgres, `heavy-slot.sh --db` + `run-host-tests.ps1`: `test_4b_money_leaves_postgres`,
  `test_3a4_commercial_months_postgres`, `test_3b3_structure_read_postgres`: **17 passed**, 59 s wall (`pg-run.txt`).
- `check-architecture.ps1`, `check-agent-workflow.ps1`, fast `check-all.ps1`: see "Final checks" below.
- Plants (`plants.txt`; each planted, run, reverted with `git checkout`): V7 → tests 1, 3; V8 → 1, 3; V9 → 2;
  V10 (prefer declared / fallback on mixed currency / fallback in open month) → 1 / 6 / 2; V11 → 2, 7, 9-probe;
  V12 → 7; V13 → 9; V14 float / ambient → 11a / 11b; V15 (compose includes all Sites) → 3; V17 divide / fallback →
  12 / 12; V19 → 1, 7, 10; V20 → 13; batch E changed → simulator test 5.

## Known deviations

1. **Test 5 lives in `simulator/tests/world/test_4b_fixture_parity.py`**, not the backend file:
   `dependency-direction.ps1` bans `assetops_simulator` imports under `backend/` (first check-all failed on it).
   Same shape as 5a test 10. Outside done Q8's list by one file.
2. **Mid-build Q2 (open, default applied):** migration 0063 refuses `entered_by` `"test:4b"`; the Postgres file ingests
   the same steps as `"service:test-4b"`. No figure depends on it.
3. Currency rule 4 runs only on money rows (`productive_kwh` has no currency, §3.4).

## Residual risk / review focus

- `READ_AS` takes `filled_by`/`stated_by` from the registry rows, plus the two literals; test 10 pins it to a literal.
- `outstanding` uses CHARGE AMOUNT lines only; a quantity-only CHARGE month gives `−Σ receipts` (spec literal).
- Overlap with the 5a units 2-3 lane (`/opt/assetecon/AssetOpsV1-5a2`): no code file shared (it touches
  `structure/targets/*`, `test_5a_*`); likely text conflicts only in `.ai/state/data.md` and `.ai/state/index-2.md`.

USER_REVIEW_REQUIRED: not stated in the spec; non-screen. Q2 is for the Architect, not the owner.
