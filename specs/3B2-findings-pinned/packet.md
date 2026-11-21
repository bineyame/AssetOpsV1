# 3B2 packet: Findings pinned to their factors

Branch `task/3B2-findings-pinned`, base main `c69e72f61`; unit commit `fb3c418de`. Spec rev 2, rulings D-3B2.1-15.
Non-screen, 2.5 units. Mid-build questions: **0**.

## Module paths (spec §0)

```
/opt/assetecon/AssetOpsV1-3b2/backend/assetops_backend/__init__.py /opt/assetecon/AssetOpsV1-3b2/contracts/assetops_contracts/__init__.py
```

## Files changed

- `backend/assetops_backend/structure/pins.py` (new): `Pin`, `DOMAIN_OF_STRUCTURE`, `PINS`, `PENDING_PINS`, `pin_of`,
  `pinned_category`, `Divergence`, `parity`. Imports `registry` and `outcomes.outcome_map` (module, read at call time).
- `backend/assetops_backend/structure/check.py`: imports `pins` and `outcome_map`; `PIN_CODES`, `_is_total`,
  `check_pins`; `check_all()` calls `check_pins()` only when `registries is None`; `__all__` gains the two names.
  `CODES` and the per-registry checks are unchanged.
- `backend/tests/test_3b2_findings_pinned.py` (new): T1-T5, 60 tests. Import path `from assetops_backend.structure
  import pins` (D-3B2.15).
- Bookkeeping: this packet, spec status, `specs/INDEX.md`, `.ai/state/data.md` + `index-2.md`.

## Acceptance (spec §7)

1. Each stored mechanism resolves: two in `PINS` (`candidate_l`, `unexplained_l`), three in `PENDING_PINS` (3B6).
   `STRUCTURE_PIN_MISSING` refuses one left out (P2).
2. Start-up refuses a pin to a missing factor or row (`STRUCTURE_PIN`) and to a sum (`STRUCTURE_PIN_TOTAL`: `diesel_l`,
   `cost_to_serve`, `metered_kwh`, `billed_kwh`); `fuel_cost` (product) is accepted.
3. `parity()` returns exactly D-3B2.4's `UNEXPLAINED_FUEL` PROTECT/RISK vs OPTIMIZE/COST; T3 holds it as a literal.
4. T4's literal snapshot (written from `39e1682de`; `git diff 39e1682de c69e72f61 -- outcomes/` is empty) covers 6 keys
   x 3 domains; `git diff main -- backend/assetops_backend/outcomes/` is empty; `test_out_a1_outcome_map.py` passes
   unchanged.
5. Diff is the §7.5 list plus bookkeeping. No served text (D-3B2.8): no `messages.CATALOGUE` key, sentence or word map.

## Checks (actual output)

- Tests first: collection error (`pins` absent) before the module existed.
- Mutation proofs on the real code, each reverted with `git checkout --` (start-up line, then the test file):
  P1 `unexplained_l`->`diesel_l`: `ConfigurationError: STRUCTURE_PIN_TOTAL MINI_GRID/diesel_l`, 9 failed.
  P2 drop `EV_INTERRUPTION`: `STRUCTURE_PIN_MISSING -/EV_INTERRUPTION`, 10 failed.
  P6 `cost_to_serve`: `STRUCTURE_PIN_TOTAL MINI_GRID/cost_to_serve`, 9 failed. P6 `fuel_cost`: start-up passes, 3
  failed (T1/T3/T5 tables). Missing factor `nope_l`: `STRUCTURE_PIN MINI_GRID/nope_l`, 12 failed.
  P3 `candidate_l` home Protect P1: start-up passes, 4 failed (T3 new divergence). Wire edit MG-8->MG-2: 3 failed (T4).
- Focused + regression, no DB (`env -u DATABASE_URL -u ASSETOPS_TEST_DATABASE_URL`): 3B2, 3B1, out_a1, health,
  3B3 evaluate and window-price, 3B7a seam and snapshot, 5b attribution: **313 passed, 1 skipped**, 18.3 s.
- Postgres (`heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1`, `assetops_test`): 3B3 read, 3B7a snapshot,
  5b attribution postgres: **14 passed**, 41 s (73 s wall with slot).
- `pwsh -NoProfile -File tools/check-all.ps1` (`ASSETOPS_GUARD_PYTHON` set): **All 40 guards passed**, 81.4 s;
  architecture seams (module roots, dependency direction, simulator gate, configuration persistence) pass.
- `tools/select-tests.py --base main`: 286 of 553 files selected; not run (full/selected suites are the
  coordinator's to schedule).
- Layout evidence: not run (non-screen).

## Known deviations and implementer choices

- `STRUCTURE_PIN_MISSING` has no structure key (the mechanism is in neither table), so its text is
  `STRUCTURE_PIN_MISSING -/<mechanism>`, using 3B1's `-` placeholder (`STRUCTURE_CATALOGUE <key>/-`). Spec §3 writes
  `<key>/<mechanism>`; review whether `-` is acceptable.
- `pinned_category` looks up the registry directly (a pin with no registry raises `KeyError`); start-up guarantees
  every pin resolves.

## Review focus

D-3B2.12 total detection (`_is_total`), the start-up-only branch in `check_all` (D-3B2.10, P5), and T4's literal.

USER_REVIEW_REQUIRED: not stated in the spec; no screen or wire changes, so none expected before merge.
