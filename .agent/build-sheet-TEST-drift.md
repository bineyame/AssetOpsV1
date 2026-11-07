# Build sheet: TEST-drift (five no-DB backend failures on main)

Branch `task/TEST-drift-main` (cut from main `840d5dade`), worktree `C:\Users\assef\Bineyame\AssetOpsV1-drift`. Investigator commit `ab9883458` (test files only).

## DRIFT-R1: Architect ruling (2026-11-07)

- Architect: Claude (fresh Architect). Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude (2026-10-27). Paths: `B/` = `backend/assetops_backend/`, `T/` = `backend/tests/`.
- Verified in the drift worktree (no DB): with `PYTHONPATH` = `<wt>\backend;<wt>\contracts;<wt>\backend\tests`, the three fixed files pass and exactly the two items below still fail. **`<wt>\contracts` must be on `PYTHONPATH`**: without it, `assetops_contracts` resolves to the venv's editable install (the old `AssetOpsV1` checkout), and `test_ch5a1_scope` fails with an ImportError that is not drift.

### 1. The three fixes in `ab9883458`

| Fix | Ruling |
|---|---|
| `T/test_ch5a1_scope.py`: fake `read(..., prefetched=None)` | **Accept.** Follows the `_window_read` signature that CH-5c u1 (`b38bcaf45`) uses at `B/analytics/adapters/postgres_assessment_store.py:894`. Plain drift. |
| `T/test_ch5c2_clock_guard.py`: drop `PostgresObjectiveStore.declare.work` | **Accept the removal, and close the guard gap it exposed (2.3 below).** Confirmed gap: `scan` flags a clock literal only when the same string also contains SELECT/WHERE/INSERT/UPDATE/VALUES/SET. DD-1b1 (`8a478a6dd`) moved the clock into a default argument, `_insert_statement(recorded_at_sql: str = "clock_timestamp()")` (`B/objectives/adapters/postgres_objective_store.py:47`). The bare default string has no keyword, and the f-string INSERT only interpolates it. So the guard no longer sees this clock at all. Today it is harmless, because the statement is a writer (`declare`) that no stored compose runs. But the same shape inside a composer read would pass unseen. A scan of every listed composer module finds exactly one clock literal used as a default argument: this one. |
| `T/test_out_d2_objectives.py`: expect `outcome-status/4` | **Accept.** `B/outcomes/status.py:16` is `"outcome-status/4"` (CH-6a3 R7, `6cdfdc4aa`). The module docstring at `:1` still says `/3`, which is stale. The round fixes it (2.1). |

### 2. Work for the round

**2.1 Docstring (do this first).** In `B/outcomes/status.py:1`, change `outcome-status/3` to `outcome-status/4`. Change nothing else in that file. The chain-contract goldens carry no code hash (verified: no `code_version`/etag/hash in `T/fixtures/ch5a2_chain_contract/`), so this edit cannot move them. Do it before 2.2 anyway, so the golden is regenerated on the final tree.

**2.2 Golden `estate_week_2026-10-25`: the card is correct; regenerate.**
- **Decision: correct.** The golden is built from the CH-5a1 fixture port (`T/test_ch5a1_board_contract.py`), not a database. In that fixture, Kobo's Optimize row carries a priced `money.possible_extra_fuel_cost` earnings claim (`_money`: `3.31`–`3.97 USD`), and Cold and EV are unpriced. By CH5d1-R §2.1 (`.agent/build-sheet-CH-5d.md`), exactly one priced Site gives:
  - `value.text` = the claim text, byte-equal (`"3.31 to 3.97 USD"`);
  - `value.small` = `COST_SMALL["possible_extra_fuel_cost"]` = `"possible extra fuel cost"`;
  - `detail` = `cost.detail.one` = `"At Kobo · not added across sites"`;
  - `basis_text` = `cost.basis.money`; tone `amber`; `claim` = the node claim unchanged.

  That is exactly the extra card. CH5d1-R stop S2 also allows a byte change on the chain body for `cards.OPTIMIZE_COST` alone. The golden is stale because CH-5d1 was branched before the CH-6a3 regeneration (`9a39194b0`). It is not a product fault.
- **Procedure.** Run in the drift worktree, Windows PowerShell, with the venv python:
  ```
  cd C:\Users\assef\Bineyame\AssetOpsV1-drift\backend
  $env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-drift\backend;C:\Users\assef\Bineyame\AssetOpsV1-drift\contracts;C:\Users\assef\Bineyame\AssetOpsV1-drift\backend\tests"
  $env:ASSETOPS_REGEN_CH5A2_GOLDENS = "1"
  & C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider "tests/test_ch5a2_contract.py::test_chain_body_equals_its_golden"
  Remove-Item Env:ASSETOPS_REGEN_CH5A2_GOLDENS
  & C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_ch5a2_contract.py
  ```
  - Data: the in-file fixture port only, at `known_at=2026-11-03T12:00:00Z`. No DB, no prepare, no mechanism dataset.
  - The regen rewrites all six `T/fixtures/ch5a2_chain_contract/*.json`.
- **Acceptance (STOP if any fails):**
  - `git diff --stat` shows only `estate_week_2026-10-25.json` among the goldens.
  - `git diff` of that file adds only the `cards.OPTIMIZE_COST` object, with the literals above plus `basis_text`, `days_line: null`, `missing: false`, `tone: "amber"` and the claim. If the other five files, any other key, or the order of the other cards change, stop and report. Do not commit those changes.
  - The non-regen run of the whole file passes.

**2.3 Clock guard (`T/test_ch5c2_clock_guard.py`, test-only).**
- **(a) `financials.recompute` → allowlist, no product change.**
  - **Decision:** `_utc_now` (`B/financials/recompute.py:213-214`) is reached only through `ConsequenceRecomputeWorker.__init__`'s default `clock`, which only `ConsequenceRecomputeWorker.run` reads (`:302`). That is the scheduled recompute writer (tick/CLI, under the Site claim). The module is in the composer set because `B/financials/consequence_read.py:39` imports `derive`, `ConsequenceStore` and `PriceStore`, and `derive`/`window_price` read no Python clock.
  - **Can stored and fresh responses differ through it? No.** No stored compose constructs or runs the worker, so a stored response cannot depend on this wall-clock value.
  - Switching to `read_scope.clock()` would be wrong: `read_scope` is the compose read-instant seam, not a writer's clock.
  - **Change:** add `PY_CLOCK_ALLOWLIST: dict[tuple[str, str], str]` keyed `(module, enclosing qualname)`, with one entry:
    - key `(_B + "financials.recompute", "_utc_now")`;
    - reason `_WRITER + " (the recompute worker's default clock; only ConsequenceRecomputeWorker.run reads it; derive reads none)"`.
  - Make `scan` return the qualname with each Python hit. Keep the violation text format `python clock {module}:{line} {owner}.{attr}` so `test_planted_python_clock_fails` stays byte-equal.
  - In `violations`, skip a Python hit whose `(module, qual)` is in `PY_CLOCK_ALLOWLIST`.
  - Extend `test_allowlist_has_no_stale_entry` to the Python allowlist as well.
- **(b) Default-argument clock literals → flagged.**
  - In `scan`, collect the ids of `str` constants that are function or lambda argument defaults (`args.defaults` + non-None `args.kw_defaults`).
  - Such a constant that matches `CLOCK_SQL` is a SQL clock hit even without a statement keyword. It is recorded under the function's qualname: the existing `visit` already gives `_insert_statement`.
  - Re-add the allowlist entry under its new key, `(_B + "objectives.adapters.postgres_objective_store", "_insert_statement")`, with reason `_WRITER + " (default recorded_at of the objective declaration INSERT; called only by PostgresObjectiveStore.declare)"`.
- **Non-vacuity, in the same file:**
  - a planted `def f(c, at="now()"): ...` gives `["sql clock m:1 in f"]`;
  - the same `datetime.now()` planted in `_utc_now` of a module key that is *not* allowlisted still fails.
- **STOP:** if the default-argument scan flags anything other than the one `_insert_statement` hit across the listed modules, report it. A pre-check by the Architect found exactly one.
- The `Never` fallback (section 3) needs no change.

### 3. Fallback finding: test fake, not a fault

The log line "the batched window read fell back to per-Site reads (AssertionError)" comes from `SiteOutcomeBoardService.contained_many` (`B/site_outcomes/read.py:534-543`). The fake `Estate` in `T/test_ch5a1_board_contract.py:213-220` defines `site_selected_windows` only. Its `__getattr__` returns a `Never` call for any other attribute. So `hasattr(estate, "site_selected_windows_many")` is True, the call raises `AssertionError` ("is not a board read"), and the documented fallback (`summary.window_fallback`, logged) reads each Site's windows through `site_selected_windows`. The fallback does not change the body, so it plays no part in the golden diff.

On Postgres the real port has the batch. CH-6b1 L2/L3 cover it, and this sheet does not touch them. **No change.** Teaching the fake the batch is optional hygiene. It is not demo-critical, and it is not in this round.

### 4. Who, size, gates

- **Who:** one small **Sonnet** fix round on `task/TEST-drift-main` in the drift worktree. The round does 2.1, then 2.2, then 2.3, each as its own commit. 2.3 is code, so it is not mechanical, and the round should not be split.
- **Then:** a fresh Sonnet reviewer checks the diff against this ruling, in particular the 2.2 golden-diff acceptance and the 2.3 non-vacuity tests. Merge on ACCEPT, by the coordinator.
- **Tests for the round (no DB):** with the `PYTHONPATH` above, run `T/test_ch5a1_scope.py`, `T/test_ch5c2_clock_guard.py`, `T/test_out_d2_objectives.py` and `T/test_ch5a2_contract.py`. Also grep `T/` for any other `outcome-status/3` literal. No suites, prepares or DB.
- **Size: 0.25 unit:** docstring and regen ≈ 0.05; guard allowlist, default-argument scan and tests ≈ 0.2.
- **Owner:** nothing to decide. Inform only: five no-DB failures on main were test drift or stale goldens. One guard gap (clock literals in default arguments) is closed. No product behaviour changes.
