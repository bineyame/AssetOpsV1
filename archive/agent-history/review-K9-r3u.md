# Review: K9 fix round (DIESEL-1-R3u, build sheet §9u)

Reviewer: fresh Claude reviewer (did not author). Branch `task/DIESEL-K9-checks-rehearsal`, diff `d681480be..8b68ff9b2` (code 0be93c2ce, packet 8b68ff9b2). Reviewed together with DIESEL-K6c (R3u cut 4).

## Verdict: FIX

One High finding, which can be fixed in one line. Every R3u item is otherwise implemented as ruled, and the mutations bite.

## Findings

### H1 (High). `pv_values` and `kis4` import `chain_coherence` without putting `tools/checks` on `sys.path`

- **Where:** `tools/demo_combined_rows.py:380` (`pv_values`) and `:441` (`kis4`) both run `from chain_coherence import nonzero_pair_sums`. Neither function does what `kis8_protect` does at `:479`, which is `sys.path.insert(0, .../checks)` before the same import. Nothing at module level adds it either.
- **Failure scenario, observed:**
  - The run used the brief's PYTHONPATH (`backend;contracts;tools;...`, no `tools\checks`): `pytest backend/tests/test_demo_combined_finish_rows.py backend/tests/test_k4a_fuel_finding_rules.py backend/tests/test_k9_finish_callsites.py backend/tests/test_k7_kisiwa_story.py` gives **2 failed, 180 passed**. Both failures are `ModuleNotFoundError: No module named 'chain_coherence'` at `demo_combined_rows.py:380`:
    - `test_pva_reads_the_mill_line_the_trial_case_and_no_sum`, a pre-existing test, so this is a regression;
    - `test_pva_zero_addend_...`.
  - `-k kis4` on `test_k4a_fuel_finding_rules.py` alone gives 3 failed, including the pre-existing `test_kis4_passes_on_a_true_body`. The cause is the same, at `:441`.
  - The run fails the same way under the wrapper-style PYTHONPATH (`tools\run-host-tests.ps1` and the Docker suite put no `tools\checks` on the path).
  - In a full backend run, the only `tools/checks` insert sits inside a test function at `test_demo_combined_finish_rows.py:758`. That function runs after the PV-A tests at `:257`, so the PV-A tests fail there too.
  - The packet's "383 passed" holds only because `tools/checks/test_chain_coherence.py` was collected in the same session, and its rootdir insertion and the `sys.path.insert` at its line 17 hide the gap.
- **Runtime:** in `finish check`, PV-A (`demo_combined_finish.py:975`) and KIS-4 (`:992`) work only because F-COH (`:761`, through `_coh` at `:739`) runs first and inserts the path.
  - A run that selects rows (R3u cut R3u-b) without F-COH would fail PV-A and KIS-4 with `ModuleNotFoundError`.
  - A run where F-COH raises before `:739` would fail them the same way.
  - This is the same class of defect as MILL-5: a function relies on an import it does not do itself.
- **Fix:** do what `kis8_protect` does. Insert `Path(__file__).resolve().parent / "checks"` on `sys.path` before each of the two imports, or once in a small helper that both call.
  - Then run `test_demo_combined_finish_rows.py` and `test_k4a_fuel_finding_rules.py` on their own, without `tools/checks/*` in the session, as the proof.
  - Optionally, extend the new AST guard idea to "a function that imports `chain_coherence` inserts `checks` first".

### L1 (Low, informational). The helper also drops pairs whose currency is None

- **Where:** `tools/checks/chain_coherence.py:1312-1314` (`a[0] is not None`).
- **What changed:** before the change, PV1 (`coh17_values`) and `pv_values` paired two entries whose currency was None (`None == None`). They no longer do.
- **Assessment:** real Assure `verified_values` entries always carry a currency, so no detection is lost on real data. It is also consistent with "same-currency" in the R3u docstring.
- **No change needed.** Noted because it is a small change beyond zero-exclusion.

### L2 (Low). The diagnostic second read can mask the R3u-s1 message

- **Where:** `tools/demo_combined_rows.py:1272-1275` calls `second_read()` inside the `AssertionError` arguments, and `tools/demo_combined_finish.py:1188-1196` defines it.
- **Failure scenario:** the second read (`ctx.get` with `from`/`to`) raises, for example on a non-200 or a parse error. The row then fails with that exception instead of the "R3u-s1" text and its `read_state`/`warnings`.
- **Fix (optional):** wrap the call: `try: second_read() except Exception as e: {"error": repr(e)}`.

## Item-by-item against R3u

| R3u item | Result |
|---|---|
| U1 helper `nonzero_pair_sums` in `chain_coherence.py` with the ruled signature and docstring | Matches (`:1312`). |
| U1 site 1, UF1 | `:1350`, `nonzero_pair_sums(pairs)`. Matches. |
| U1 site 2, PV1 | `:1298-1299`, via `_amounts`. Matches. |
| U1 site 3, `pv_values` | `demo_combined_rows.py:380-383`. Matches in logic. **H1** applies to the import. |
| U1 site 4, KIS-4 (fuel and dispatch high, fuel and fuel) | `:439-449`. Zero dispatch values now reach the helper. The helper excludes them. `stored` still drops zero. Equivalent to the earlier pre-filter. **H1** applies to the import. |
| U1 tests: rehearsal shape (0.00 low, 119.57/180.43) gives no finding; planted 134.70 is found; PV1 and `pv_values` pairs; KIS-4 zero `amount_high` | All present (`test_chain_coherence.py:1041-1061`, `:1129-1149`; `test_demo_combined_finish_rows.py:260-267`; `test_k4a_fuel_finding_rules.py:359-368`). |
| U4 `import psycopg` first in `mill5`, plus an AST test that fails on the rehearsal shape | Matches. The guard also flags a module-level import, which is a strictness extra and harmless. |
| U5 KIS-6 reads `verdict.state`, and the message reports the state | Matches. The tests cover dict VERIFIED (reaches the card claim and H2 return), INEFFECTIVE with `threads.verified` 1 (existing break "3"), and a null verdict. |
| U7 KIS-OV pin: Protect `NEEDS_ATTENTION` and MG-8 `{NEEDS_ATTENTION, PRIMARY_FINDING_OPEN}`, no lead assert; on failure `read_state`, `warnings` and a second read by the local `from`/`to` pair; stop R3u-s1 | Matches. Shape checked against the product: `board.py:888` emits `outcomes: [{key, label, state, reason}]`, and MG-8 is the key used in `mini.py:525`. The test fails on the packet's UNKNOWN/PRODUCER_NOT_SETTLED shape. |
| U8 KIS-7 item 3 asserted again (unpriced d1, differing amount) and the R3s2 report-only form reachable | Matches. It asserts by default. `item3_report_only=True` or `KIS7_ITEM3_REPORT_ONLY` restores the quoted R3s2 text. |

## Question 2: is the zero-addend rationale sound?

Yes.
- A two-place sum `x + 0.00` equals `x`, and `x` is already printed legitimately on its own. So matching `x + 0` cannot tell "added" from "shown", and excluding it loses no detection a value-matching check could make.
- A real total of a non-zero amount with a genuinely zero line is numerically the non-zero amount. Its "addition" is invisible to any value-based check, before or after the change.
- A total involving two non-zero amounts is still caught through the non-zero pair, even if a zero line is also present.
- The Architect correctly rejected the wider rule ("drop any sum equal to a listed amount").

## Question 6: Kobo, Cold and EV unchanged

K9 has no backend or config diff (`git diff d681480be..HEAD --stat`), so `code_version` and product output are unchanged.

## Question 7: merge order K9 → K10 → K6c

`git merge-tree --write-tree` predicts no textual conflict for each pair: K9+K10, K9+K6c, K10+K6c. There is no semantic clash with K9. K10's settled Assure only affects the KIS-OV lead, which the pin deliberately does not assert.

## Checks run

These are pure tests: plan2 venv, absolute PYTHONPATH under the k9 worktree, no DB.
- The packet's file set (`tools/checks/test_chain_coherence.py`, `tools/checks/test_fuel_wording.py`, plus `test_demo_combined_finish_rows.py`, `test_k4a_fuel_finding_rules.py`, `test_k9_finish_callsites.py` and `test_k7_kisiwa_story.py`): **383 passed**. This matches the packet.
- The backend files only, with no `tools/checks` test in the session: **2 failed, 180 passed** (H1).
- `-k kis4` on `test_k4a_fuel_finding_rules.py` alone: **3 failed, 5 passed** (H1).
- With the wrapper-style PYTHONPATH (no `tools`), `test_demo_combined_finish_rows.py` alone: **2 failed, 52 passed** (H1).

Mutations ran on a scratch copy of `tools/` and the test files; no repo file was edited. The scratch baseline had 11 failures caused by the scratch location (fixture paths outside the repo). The mutations below caused failures beyond that baseline:
- The helper's zero check removed: the UF1, PV1 and helper tests failed, and `test_pva_zero_addend_...` failed.
- KIS-6 back to the whole-dict compare: `test_kis6_counts_cells_...` failed.
- The KIS-OV MG-8 reason check removed: `test_kis_ov_pins_the_s5d_protect_row_and_mg8_entry_r3u` failed.
- The KIS-7 item-3 raise disabled: `test_kis7_expectations_from_data_pass_and_each_break_fails` failed.
- `mill5`'s local import removed: both psycopg AST tests failed.

**Not verified:**
- `finish check` on the clone, and the served shape of the second read (§9u.2 step 3).
- The full backend suite. Its failure on H1 is inferred from collection order, not run.
