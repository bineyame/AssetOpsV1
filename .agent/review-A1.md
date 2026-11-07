# Review: FUEL-1 A1, fuel-cost-2 and the declared no-load fact

- Reviewer: fresh Claude reviewer (did not author the slice).
- Branch `task/FUEL-A1-fuel-cost-2`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-a1`. Diff reviewed: `git diff f63b46a01...HEAD` (build `972dc747f`, packet `87bc6f801`).
- Spec: `.agent/build-sheet-FUEL-1.md` §4.1 (with §1); owner decisions `.agent/owner-fuel-scope-2026-11-07.md`.
- This file's name is `.agent/review-A1.md`. It matches `fuel_cost_v2.PARAMETER_VERSION["reviewer"]` (`.agent/review-A1.md (FUEL-1 A1 review)`), so the immutable parameter digest needs no change before merge.

## Verdict: ACCEPT

No High or Medium findings. Four Low findings follow; none blocks the merge. L1 is worth closing on this branch or in A2, because A3 depends on it.

## What I checked

**Model correctness (`backend/assetops_backend/financials/fuel_cost_v2.py`)**

- **Formula.** Idle litres are `duration_seconds/3600 × r`, and loaded litres are `super().litres` (v1's `P × h × SFC`). The multiplier 1.10 applies once, to the sum of both terms. `low` is 0, and `high` is `fc.to_decimal_ceiling(exact)`, which rounds outward as v1 does.
- **Idle definition.** A reading is idle when `c.mean_kw == 0` over fuel-cost-1's counted intervals. Those intervals are already GOOD, non-negative, contained in observed Candidate time and coverage-complete. So "wholly inside observed Candidate time" is inherited, not re-derived. `Decimal("0.0")` and `Decimal("-0")` both read as idle, which is correct.
- **Selection.** fuel-cost-2 applies only when v1 is AVAILABLE and some counted reading's revision declares a rate. Otherwise the v1 `Quantity`, and through `fc2.consequence`, the v1 `Consequence` object are returned unchanged. This is byte-equal by construction, and `test_no_rate_selects_fuel_cost_1_byte_equal` asserts it.
- **Refusal order.** The order is MISSING (idle readings only), then CONFLICT, INVALID and BASIS_MISSING, as the sheet gives it. A non-numeric or non-finite rate parses to `None` through `fc._decimal` and reads as INVALID. A rate of 0 or a unit other than L/h also reads as INVALID. Every unresolved case fails closed.
- **fuel-cost-1 is unchanged.** `fuel_cost.py` is not in the branch diff. Main has since changed it with MV-1's two keyword arguments, but `fuel_cost_v2.py` does not call `select_window_price`, so there is no conflict.
- **Recompute and currentness pick the same model.** `recompute.derive` (`recompute.py:175-177`) and `ConsequenceReadService` (`consequence_read.py:358-363`) both call `fc2.quantify` / `fc2.consequence` over the same `load_input_on`. That function now reads the rate and basis in its single Foundation query. The code is consistent; see L1 for the missing test.

**Migration 0053**

- The `model_id` CHECK name matches Postgres's auto-name for the inline 0011 CHECK (`financial_consequence_revision_model_id_check`). The new columns have positive/finite, three-value and `>= 0` CHECKs, and `fuel_cost_1_no_idle` covers the v1 case.
- The trial table: `formula IN (/1, /2)`. `REASONS_0037` equals 0037's tuple exactly, plus the two A2 reasons. `result` is jsonb, so A2's additive `priced_total` needs no schema change.
- **Downgrade is safe.**
  - It takes an `ACCESS EXCLUSIVE` lock, then refuses if any fuel-cost-2 row, any `/2` trial row or any new-reason trial row exists. Because the DDL runs in one transaction, a refusal rolls everything back.
  - It then restores both tables' CHECKs. The test confirms that an empty down/up round trip gives back the identical column and constraint shape.
- **Single head.** Main has no `0053` (main is now at `e31ccbbb8`, MV-1 merged, with no migration), and `0053`'s `down_revision` is `0052_verification_plan_domain`.
- No reader filters on `model_id = 'fuel-cost-1'`. I grepped `backend/assetops_backend` and `tools`: the only SQL `model_id` filters are on the cold tables, and the consequence reads use `SELECT *`. The `financial_consequence_power_interval` CHECK is `mean_kw >= 0`, so 0 kW idle intervals insert, which the L2 idle test confirms.

**Judgement calls (packet deviations)**

- Reviewer string (dev. 7): it matches this file.
- Basis kind PHYSICAL (dev. 4): consistent with the precedent `supply-use` (`state`, `PHYSICAL`), pinned in `test_w402_roles_properties.py`. Accepted.
- Extra readers in `consequence_read.py` (`parameter_is_reviewed` per model, the v2-only model-block keys, and the currentness selection): all necessary. Without them a v2 row would read unreviewed and always STALE. A v1 row's model block is unchanged (asserted in `test_no_rate_stays_fuel_cost_1_with_null_columns`).
- `outcome_map.py:164` left as `"model.fuel-cost-1"`: acceptable for A1. It is a contribution descriptor, not a row filter, and changing it would move CH digests. See L4.
- Partly synthetic idle store test (dev. 8): acceptable.
  - The store writes and the `power_interval` rows are real.
  - The PowerSite fixture has power without a `generator_state` status, so `analytics/dispatch.py:260-263` classifies 0 kW as OFF there.
  - Kobo has RUNNING status records (`dispatch.py:253-256`), so its 0 kW means do land in Candidate time. `fuel-story-design-2026-11-07.md` B2 records them as already PRICED at 0 L.
  - The residual risk is therefore A3's measurement, as the packet says.
- Conflict scope (dev. 2), including a basis conflict counting as `NO_LOAD_RATE_CONFLICT`: fail-closed, and it keeps the singular stored rate column well defined. Accepted. See L3 for the user-visible consequence.

**Do the tests bite?** (reasoned from the assertions)

These code breaks would be caught:
- selection always or never v2: the `is_v2` asserts in the byte-equal and idle tests;
- idle litres computed with SFC, or the multiplier left off the idle term: the exact `Fraction` in `test_idle_only_200_minutes_at_3_3`;
- any refusal removed or reordered: `test_new_refusals`, where a removed CONFLICT check would also raise at the tuple unpack;
- the store not reading the rate: the round trip asserts `f.foundations`;
- the wrong columns written: the row asserts;
- a CHECK dropped: the named CHECK matches;
- the downgrade guard removed: the refused-downgrade test.

These would not be caught: see L1 and L2.

## Findings

### L1 (Low, test gap): no test proves a stored fuel-cost-2 head reads CURRENT

- **Where:** `backend/assetops_backend/financials/consequence_read.py:358-363` (currentness re-derive). Untested for v2; nothing outside the two new test files imports `fuel_cost_v2`.
- **Failure scenario:** someone later reverts these two lines to `fc.quantify` / `fc.consequence`, or adds a second re-derive path elsewhere. Every stored fuel-cost-2 head then re-derives to a v1 basis and reads `STALE / TECHNICAL_INPUT_CHANGED`. The bridge shows an amount only for a CURRENT PRICED head (`finding_api.py` `bridge_consequence`), so all idle-fuel money silently disappears from Kobo's screens, and no A1 test fails.
- **Why it matters:** A3's visible copy and the E3 MONEY-B finish rows rely on this invariant.
- **Fix:** in `TestStoreRoundTrip.test_declared_rate_selects_fuel_cost_2_and_round_trips`, after `append`, read the row through `ConsequenceReadService` (the same path `test_s4_consequence_read*` uses) and assert `currentness.state == "CURRENT"`. The bridge's `quantity_source == "fuel-cost-2"` and its PRICED reason could be asserted at the same time. One test, test-only.

### L2 (Low, test gap): some v2 refusal and selection branches are untested

- **Where:** `fuel_cost_v2.py:148-160`, and `finding_api.py:378` / `site_overview/read.py:336` for v2.
- **Untested branches:**
  - a basis value outside the three (dev. 3, `NO_LOAD_RATE_BASIS_MISSING` through stored data);
  - a loaded reading on a non-declaring revision next to a declaring one, which should stay AVAILABLE because MISSING applies only to idle readings;
  - the bridge and overview label naming `fuel-cost-2`.
- **Failure scenario:** a refactor that applies MISSING to every reading would turn a Site's first Finding that spans a Foundation re-publish into QUANTITY_UNAVAILABLE, and no test would flag it.
- **Fix:** add two cases to `test_fuel_cost_v2.py`, and optionally one bridge-dict assertion using a synthetic `result` dict.

### L3 (Low, behaviour note for A3 and the Architect): changing the declared rate or basis refuses a spanning Finding

- **Where:** `fuel_cost_v2.py:147-149`.
- **Behaviour:** the conflict set covers every declaring revision of every counted reading. Suppose a Finding's counted readings span a Foundation re-publish that changes only the basis (GENERIC_DEFAULT to MANUFACTURER_DATASHEET) or the rate. That Finding becomes `QUANTITY_UNAVAILABLE / NO_LOAD_RATE_CONFLICT`, not two priced segments. This is fail-closed and matches the sheet's "more than one distinct rate". The basis half is the builder's extension.
- **Impact on Kobo:** A3 declares one rate once, so Kobo is unaffected.
- **If a later Site re-declares mid-Finding:** this is the rule that will hide its money. Record it for the Architect. No change is needed for A1.

### L4 (Low, follow-up): the outcome-map descriptor names v1 only, and there is a blank-line style nit

- **Descriptor:** `backend/assetops_backend/outcomes/outcome_map.py:164` still says `"model.fuel-cost-1"` (disclosed in the packet). It is not shown copy and not a filter, so it is not wrong today. A3 or the Architect should decide whether the descriptor names the model generically before any client-facing contribution text reads it.
- **Style nit:** `backend/assetops_backend/site_overview/read.py:38-39`. `def money_label` follows `CONTEXT_LIMIT = 500` with no blank lines. The guards pass, so this is cosmetic only.

## Checks I ran (worktree at `87bc6f801`)

- **Interpreter and paths.** Python `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`, with PYTHONPATH pinned to the worktree's `backend;contracts;tools;simulator;gateway;host;field`. `assetops_backend.__file__` resolves to `C:\Users\assef\Bineyame\AssetOpsV1-a1\backend\assetops_backend\__init__.py`.
- **Touched L0 files.** `pytest tests/test_fuel_cost_v2.py tests/test_s4_fuel_cost.py tests/test_w402_roles_properties.py tests/test_w205a_ev_vocabulary.py`: **177 passed**, 2.2 s.
- **Adjacent L0 files** (contract stop check, reads, contributions). `pytest tests/test_scenario_execution_contract.py tests/test_execution_contract_alignment.py tests/test_s4_consequence_read.py tests/test_s5_overview_read.py tests/test_ch6_contributions.py tests/test_component_properties.py`: **248 passed**, 6.2 s. No contract digest moved.
- **New L2 file.** `pytest tests/test_fuel_cost_v2_postgres.py` on base `assetops_a1_test` (127.0.0.1:55432, harness clones), with 4.4 GB free RAM beforehand: **7 passed**, 58 s.
- **Guards.** `tools/check-architecture.ps1`: "Architecture check passed", exit 0. `tools/check-agent-workflow.ps1`: "Agent workflow check passed", exit 0. Both ran with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv and no execution-policy override.

## Not verified by me

- **Existing consequence Postgres files.** `test_s4_consequence_store_postgres.py`, `_recompute_postgres`, `_history_postgres` and `test_s4_assumption_read_api.py` were not rerun. They are outside the "touched files only" scope, and the packet's run takes about 346 s. I am citing the implementer's run: 55 passed, 0 failed, at `972dc747f`. The only later commit is the packet, so that is the same code.
- **No full suite, prepare or `test_demo_combined_postgres`** was run, per the ruling.
- **Frontend.** No frontend file changed. The frontend displays the server's strings, and `financialsClient.ts` types `model_id` as `string`, so the new keys are additive. No layout evidence applies, because nothing in A1 is visible.

## Residual risk not already in the packet

- **Main has moved since the cut.** Main has moved past `f63b46a01` (MV-1 merged, touching `fuel_cost.py`). There is no textual overlap with this diff, but the merge should rerun `test_fuel_cost_v2.py` and `test_s4_fuel_cost.py` on the merged tree.
- **Rate equality across text forms.** Rates compare as Decimal values, so "3.3" and "3.30" from two revisions collapse to one rate. Which text form is stored, and which enters the digest, then follows reading order. This is deterministic, but a later re-publish that restates the same rate as "3.30" could change the technical digest and append a new revision with the same money. Negligible for the demo.
