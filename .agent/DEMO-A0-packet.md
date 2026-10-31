# DEMO-A0 packet: assumption-store clock seam (R1)

Branch `task/DEMO-A0-assumption-clock-seam`. 

## Delivered
- `PostgresAssumptionStore(url, *, test_recorded_clock_override=None)`; when set it replaces only the `at` instant
  (was `clock_timestamp()`). `RECORDED_TIME_NOT_LATER` and all money rules unchanged. Docstring mirrors the evidence ledger seam.
- `backend/tests/test_demo_a0_assumption_clock_seam.py`: AST check that no module under `assetops_backend/` (except the store)
  passes or reads the keyword, plus text check on `composition.py`/`main.py`; override at X gives recorded_at/recorded_from == X,
  snapshot at X-1s empty, at X selected; no-override uses server clock (attribute None, instant within now +-30 s);
  override keeps `RECORDED_TIME_NOT_LATER`.
- No `composition.py`/`main.py` change (never wired).

## Checks
- New + s4 assumption tests: 88 passed.
- `-k "s402 or s408 or out_e3 or out_e4"`: 24 passed (113 s).
- Non-vacuity: added a keyword-passing call to `composition.py`, the AST test failed; reverted, tree clean.
- `tools\check-all.ps1` (guard python = plan2 venv): 11/11 guards passed. No full suite (folded into DEMO-A `-Tier all`).

## Residual
"Byte-identical without override" is shown behaviourally (server clock path untouched), not by a golden diff.
