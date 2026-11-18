# Review packet: FUEL-1 A1, fuel-cost-2 and the declared no-load fact

- Spec: `.agent/build-sheet-FUEL-1.md` §4.1 (commit f63b46a01), with §1 for context; owner decisions `.agent/owner-fuel-scope-2026-11-07.md` (generic 3.3 L/h, labelled; example tank left alone).
- Branch `task/FUEL-A1-fuel-cost-2`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-a1`, cut from main `f63b46a01`. DB: base `assetops_a1_test` on 127.0.0.1:55432 (run-owned clones `assetops_a1_pt*_test`).
- Build commit: `972dc747f`. USER_REVIEW_REQUIRED: no (nothing visible yet; A3 makes it visible).

## Outcome delivered

- A new reviewed model, `fuel-cost-2` (`backend/assetops_backend/financials/fuel_cost_v2.py`). `fuel_cost.py` (fuel-cost-1) is byte-unchanged.
  - Immutable `PARAMETER_VERSION` `fuel-cost-2/sfc-upper-multiplier-and-no-load/v1`, value 1.10 on both terms, author "Claude Architect (FUEL-1)".
  - The formula: `high = 1.10 x [sum_loaded P h SFC + sum_idle h r]`.
  - `LIMITATIONS` has five lines: v1's lines 1, 2 and 4, a new line 3, and the new fifth line, worded as the sheet gives them.
  - The technical digest adds the model id, r, the basis and the idle flags.
- **Selection** (`fuel_cost_v2.quantify`): fuel-cost-1 runs first. fuel-cost-2 applies iff fuel-cost-1 is AVAILABLE and some counted reading's Foundation revision declares the rate. Otherwise the fuel-cost-1 `Quantity` and `Consequence` come back unchanged, so they are byte-equal.
  - Four new refusals, in the sheet's order: `NO_LOAD_RATE_MISSING`, `NO_LOAD_RATE_CONFLICT`, `NO_LOAD_RATE_INVALID` and `NO_LOAD_RATE_BASIS_MISSING`.
- **Vocabulary** (`sites/models.py`):
  - `generator-no-load-fuel-rate` (L/h, PHYSICAL);
  - `generator-no-load-fuel-rate-basis`, a state property with values `GENERIC_DEFAULT | MANUFACTURER_DATASHEET | SITE_TEST`;
  - both carried by `GENERATOR` through `MINIGRID_PROPERTY_CARRIERS`. The parser still refuses SFC in L/h.
- **Store** (`postgres_consequence_store.py`):
  - `load_input_on`'s single Foundation query also aggregates the two properties into `fuel_cost_v2.FoundationRevision`, a subclass of the v1 class.
  - `append` writes the model columns from `fuel_cost_v2.model_columns(c_)`, plus the three new columns.
- **Recompute** (`recompute.derive`) and the **currentness re-derive** (`consequence_read.select_consequence_on`) both call the selection.
- **Migration `0053_fuel_cost_2`** (A1 and A2):
  - `model_id IN ('fuel-cost-1','fuel-cost-2')`;
  - `no_load_fuel_rate_l_per_h` (> 0, finite), `no_load_fuel_rate_basis` (one of the three bases) and `idle_seconds` (>= 0), all nullable;
  - `fuel_cost_1_no_idle`: a `fuel-cost-1` row has all three NULL;
  - the trial table's `formula` admits `/2`, and its reason CHECK adds `IDLE_SECONDS_UNKNOWN` and `NO_LOAD_RATE_DIFFERS`.
  - Downgrade refuses while any v2 row exists, then restores the 0011 and 0037 CHECKs.

## Pre-flight (code reality, batched before code; no blocking question)

Readers of the literal `fuel-cost-1`, with their dispositions. **No reader filters rows on `model_id`, so the stop condition does not apply.**

| Reader | Disposition |
|---|---|
| `B/finding_api.py:328` `QUANTITY_SOURCE`, `:352` PRICED reason | The bridge now shows the stored row's `model.model_id` in `quantity_source` and in the PRICED sentence (`_priced_reason`). `QUANTITY_SOURCE` stays only as the default when no row exists. A v1 row's bytes are unchanged |
| `B/site_overview/read.py:39` `MONEY_LABEL` | Becomes `money_label(model_id)`, set from the stored row's model in `_money`. The constant is kept as the no-row default. v1 bytes are unchanged |
| `B/outcomes/outcome_map.py:164` `"price": "model.fuel-cost-1"` | Unchanged. It is a contribution descriptor, not a row filter and not shown copy. Changing it would move CH digests and the `test_ch6_contributions` pin. Left for A3 or the Architect if the descriptor should name both models |
| `B/mini_depth/rules.py:636` | A comment only. The mini-depth projection uses `fuel_cost.MULTIPLIER` (1.10, the same value). Unchanged |
| `B/financials/recompute.py` | `derive` now selects (`fc2.quantify` / `fc2.consequence`) |
| `B/financials/consequence_read.py:109` `parameter_is_reviewed` (found in pre-flight, not listed in the sheet) | Compared with the reviewed digest of the row's own model (`REVIEWED_PARAMETER_SHA256`). Without this change a v2 row would read as unreviewed. For v2 rows only, the read's `model` block also gains the rate, basis and idle seconds; a v1 row's block is unchanged (asserted) |
| `B/financials/consequence_read.py:351` currentness re-derive (found in pre-flight) | Selects as the recompute does. Otherwise a stored v2 head would always read STALE |
| `tools/s402c_late_power_walkthrough.py:62` | Unchanged. A dev walkthrough over fixtures that declare no rate, so it is fuel-cost-1 by selection |
| Frontend (`financialsClient.ts`, `FindingConsequence.tsx`, tests) | Display the server's strings. No change |

## Acceptance (sheet §4.1)

| Item | Status |
|---|---|
| Vocabulary: rate in L/h, PHYSICAL; basis state with the three values; both on GENERATOR | Done. Parser tests in `test_fuel_cost_v2.py::TestNoLoadVocabulary` |
| fuel-cost-2 in a new module; `fuel_cost.py` untouched | Done (`git diff main -- backend/assetops_backend/financials/fuel_cost.py` is empty) |
| Selection iff a counted reading's revision declares the rate; otherwise v1 is byte-equal | Done. `test_no_rate_selects_fuel_cost_1_byte_equal` covers both a v1 and a v2 Foundation class; `test_s4_fuel_cost.py` is green and unchanged |
| v1 checks in order, then the four new refusals | Done. `test_new_refusals` (5 cases) and `test_conflicting_basis_is_a_conflict` |
| Loaded intervals exactly as v1; `CountedInterval` v2 subclass with `idle`, `no_load_l_per_h`, `no_load_basis` | Done |
| `LIMITATIONS_V2` text; digest with model id, r, basis and idle flags | Done (`test_limitations_v2`, `test_technical_digest_names_rate_basis_and_idle_flags`) |
| Migration 0053 as specified; downgrade restores; single head | Done (`TestMigration0053`, 4 tests: CHECK names fire, single head, refused downgrade, empty down/up restores the shape) |
| Store reads both properties and writes the new columns; recompute selects | Done. L2 round trip on `assetops_a1_test` (`TestStoreRoundTrip`, 3 tests) |
| Idle-only 200 min at 3.3: `high_exact == 11/10 x 200/60 x 33/10` (12.1 L) | Done (`test_idle_only_200_minutes_at_3_3`) |
| `test_s4_fuel_cost.py` and `test_s4_consequence_*` unchanged and green | See Checks |

## Checks run (Python `AssetOpsV1-plan2\.venv`, PYTHONPATH pinned to the worktree; `assetops_backend.__file__` verified to resolve to `AssetOpsV1-a1\backend`)

All of these ran at the build commit `972dc747f`.

| Run | Command (from `backend/`) | Result |
|---|---|---|
| New L0, vocabulary pins and v1 model | `pytest tests/test_fuel_cost_v2.py tests/test_s4_fuel_cost.py tests/test_w402_roles_properties.py tests/test_w205a_ev_vocabulary.py tests/test_component_properties.py` | 258 passed, 6 s |
| Contract stop check, reads, contributions | `pytest tests/test_scenario_execution_contract.py tests/test_execution_contract_alignment.py tests/test_s4_consequence_read.py tests/test_s4_consequence_cause_dispatch.py tests/test_s4_consequence_history.py tests/test_s5_overview_read.py tests/test_s4_fuel_cost.py tests/test_component_properties.py tests/test_w201_cold_vocabulary.py tests/test_ch6_contributions.py` | 342 passed, 0 skipped. **The vocabulary moved no scenario, run-contract or handover digest, so the stop condition does not apply** |
| New L2 on `assetops_a1_test` | `pytest tests/test_fuel_cost_v2_postgres.py` | 7 passed, 57 s |
| Existing consequence Postgres tests on `assetops_a1_test` | `pytest tests/test_s4_consequence_store_postgres.py tests/test_s4_consequence_recompute_postgres.py tests/test_s4_consequence_history_postgres.py tests/test_s4_assumption_read_api.py` | 55 passed, 0 failed, 346 s |
| Guards (`ASSETOPS_GUARD_PYTHON` = plan2 venv) | `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` | Both passed, exit 0 |

- Not run, per the ruling: no full suite, no prepare, no baseline build, no `test_demo_combined_postgres`, no frontend run (no frontend change).
- Size: about 0.85 units, inside the 1.1 cap.

## Known deviations and interpretations (for the reviewer)

1. **Branch and worktree names.** The sheet names none for A1, so I followed MV-1's pattern (§2.6): `task/FUEL-A1-fuel-cost-2` and `AssetOpsV1-a1`. The DB `assetops_a1_test` is the one the sheet names.
2. **`NO_LOAD_RATE_CONFLICT` is read as "more than one distinct (rate, unit) across all counted readings' declaring revisions, or more than one distinct basis".**
   - This reading makes the singular `no_load_fuel_rate_l_per_h` column well defined.
   - The conflict, invalid and basis checks apply to every declaring revision of a counted reading, loaded or idle (fail-closed). `MISSING` applies only to idle readings.
3. **Unrecognised basis.** A basis value outside the three counts as `NO_LOAD_RATE_BASIS_MISSING`. The parser already refuses such a value, so this path is reachable only through stored data.
4. **The basis property's kind is PHYSICAL.** The sheet gives its unit (`state`) but not its kind.
5. **The three new columns are written only when the v2 quantity is AVAILABLE.**
   - A v2 refusal row stores NULLs (its model id is `fuel-cost-2`).
   - The migration enforces only the sheet's CHECK (v1 ⇒ all NULL). It adds no "v2 AVAILABLE ⇒ NOT NULL" CHECK.
6. **When fuel-cost-1 itself is unavailable, the row stays `fuel-cost-1` with v1's reason.** "Counted readings" exist only once v1 succeeds. This is the literal selection rule.
7. **`PARAMETER_VERSION["reviewer"]` is `.agent/review-A1.md (FUEL-1 A1 review)`.** The sheet says "reviewer = the A1 review file", but that file's name is not fixed yet.
   - If the review file has another name, correct the string **before merge**: it is inside the immutable parameter digest.
8. **The `test_fuel_cost_v2_postgres.py` idle round trip is partly synthetic.** It reads two of the persisted Finding's five 20 kW means as 0 kW in memory.
   - The PowerSite pipeline cannot produce real 0 kW Candidate readings: dispatch classifies a 0 kW mean as OFF.
   - Real Kobo idle mornings arrive in A3 with its scratch prepare.

## Residual risk

- A3 and its Kobo scratch prepare are the first real exercise of idle readings through dispatch. Whether those mornings' 0 kW means fall inside observed Candidate time is A3's measurement, not A1's.
- The `outcome_map` descriptor `model.fuel-cost-1` still names v1 only (pre-flight table).

## User-review focus

None for A1, which has no visible change. The reviewer should check deviation 2 (the conflict scope) and deviation 7 (the reviewer string inside the digest).
