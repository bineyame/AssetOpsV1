# W3-02 commit 3 review: Financials read/API and Lane A items

Reviewer: independent Claude reviewer (did not author). Date: 2026-10-21.
Branch `task/W3-02-estate-evidence-money-basis`, head `edcd8fce`. I read the code through git and ran tests in my own detached worktree (`AssetOpsV1-c3rv`, PYTHONPATH set to its backend/contracts/gateway/simulator/host). The tests used a private DB, `assetops_w302c3rv_test`, which I created and then dropped.

Range reviewed: Lane B `54625bdc`, `a7df5a33`, `f9ef4034`, `181f62c6`, `fefa5ab4`, `6f065647`; Lane A `1ba3306a` and `f1e49236`; `edcd8fce`; plus the `settled.ts` conflict resolution in merge `ed11e07e`.
Authority: `main:.agent/W3-02-build-spec.md`. That covers closures 1-5, the shared group-key amendment, closure 2 N3, the 0c and c1 rulings (c1-q1 estate basis), and c3, c3b and c3c.

## Verdict: REVISE

The core is sound and the N3 proof is real. However, there is one user-visible coverage gap (M1), and one implementer-flagged deviation that has never been ruled (M2). Both need closing before commit 4.

## What was verified (no finding)

- **Eligibility order.** `financials.py:decide` follows closure 2 Q6 top to bottom: HISTORICAL, then PENDING, then UNKNOWN_SOURCE / MIXED_SOURCE, then WITHHELD (failed gate, W1 AUDIT_ONLY/STALE/WITHHELD_GENERATOR_SERIES, EV WITHHELD/STALE_BASIS, cold WITHHELD), then UNKNOWN (BASIS_NOT_PROVEN), then UNPRICED, then ELIGIBLE. CONFLICT is applied afterwards, and only to provisionally ELIGIBLE lines. A withheld line that overlaps is never relabelled CONFLICT, and this is tested.
- **Groups.**
  - The partition key is the six fields. The state order is UNKNOWN_COVERAGE, then INELIGIBLE (including ASSUMPTION_UNKNOWN), then OVERLAPPING_BASIS, then SINGLE_LINE, then COMPARABLE.
  - On OVERLAPPING_BASIS, a proven collision gives the group reason OVERLAPPING_BASIS and missing proof gives BASIS_NOT_PROVEN. Involved lines carry the line reason OVERLAPPING_BASIS (c3-q2(3)).
  - Equal technical and cited arrays within one line are not treated as a collision.
  - The amount is the Decimal sum of the raw stored bounds, for COMPARABLE only. `estate_total` is always null and `estate_total_state` is always NO_ESTATE_TOTAL.
- **Coverage, sentinels and register lines.**
  - Closure 3 Q19/C1 sentinel and partition behaviour holds. Only the three mock categories get sentinels; RECORDED_REPAIR does not (c3-q2(1)).
  - An EV `STALE_BASIS` or pending guard makes the category uncovered. It never becomes a line, token revision or candidate. Only an older stored head is shown, withheld.
  - c1-q1 is respected: HISTORICAL comes only from `snap.basis_historical`, which a cursor freezes from `page_one_mode` (`index.py:99`). The EV facade's `historical_label` is ignored, and a W2 HISTORICAL pin on a live basis stays ELIGIBLE (c1 r1 M1).
- **Shared `group_key`.** `evidence_money.py:group_key_for_partition` hashes exactly the six wire fields as sorted-key compact UTF-8 JSON, keeps nulls, and returns lowercase `sha256:`. It is used for every nonempty group and exclusion; sentinels get `null`. The named test checks byte identity and that changing any one field changes the key.
- **Currency.**
  - The line amount requires a three-letter upper-case currency.
  - The partition separates currencies.
  - MIXED_CURRENCY is diagnostic only. There is no conversion and no merged group.
  - Amounts are strings: the EV facade uses `plain()`, W1 uses `_text`, and a test asserts no floats.
- **c3-q2(5) and (6).** The W1 fingerprint uses `PRICE_UNIT` (`currency/L`) with the selected `price.value` and `price.state`. `limitations` comes from the exact selected head and is joined with `; ` (Lane A `1ba3306a`, persisted test at two cutoffs plus null with no head). W1 citations are the Finding citations plus `power_evidence_ids`. The Financials token includes every pinned EV window's session revision IDs, so a change to the sessions alone fences the cursor, with or without a head.
- **Persisted two-EV-Site COMPARABLE proof** (`test_w302_money_persisted_ev_comparable_same_values`). It is real and non-vacuous:
  - It uses one `*_test` DB with two imported Sites, `install_second_ev_site` (via `import_site`, `plan_requests` and `BindingService.publish`), and two Drafts that assert READY.
  - Both run the live gateway, accepted replay, EV assessment, `golden_tariff` and the W2-07 money worker. There are no direct INSERTs.
  - Each line's Site, consequence, tariff, session and accepted-evidence IDs are matched to scoped DB rows. The tariff revisions are distinct but the fingerprints are equal, the ID sets are pairwise disjoint and nonempty, and the overlap groups are distinct.
  - There is exactly one COMPARABLE group, and its low and high equal the Decimal sum of the stored heads. No exclusions, and the estate total is null.
  - The c3c traversal assertions are applied exactly as ruled.
- **Different-currency test.** Both lines are matched to persisted rows with KES and USD and an equal rate. There are two SINGLE_LINE groups with null amounts, no COMPARABLE group, a MIXED_CURRENCY diagnostic naming exactly both line keys, and a null total.
- **Test-only scenario and drift test.**
  - The fixture lives only under `backend/tests/fixtures/w3/scenarios/`.
  - The drift test proves a line-for-line match with shipped `ev-complete` except the three ruled lines, and that no `config/scenarios` copy exists.
  - Only the second chain receives the injected repository, which is passed to both `RunSetupService` and `StoreEvInputs`. The first chain keeps the shipped repository and its golden manifests.
- **`ev_parsing.py` admission.** `(EV-LAB-002, 20518)` is selected if and only if `scenario_id == "ev-complete-lab-002"`; every other ID keeps the `(EV-LAB-001, 20517)` pin. The validated Site and seed are returned. No other field, window, digest or rule changed. The parser test refuses other IDs (`ev-complete`, `ev-complete-lab-003`, `ev-lab-002`, ...) and mismatched Site or seed in both directions.
- **`select_consequence_on` limitations.** The field is additive (null with no head; `[]` if stored null), taken from the same `selected_on` row on the caller's connection, with no new transaction. Old keys and cutoff semantics are unchanged. Currentness is basis-at-K, not compared with now, so live page two does not relabel W1 lines.
- **Refusal nulls, 503 and mount.**
  - `EXTRAS["financials"]` puts `groups`, `exclusions` and `diagnostics` (all null) inside `detail` for 401, 422 and 503.
  - `test_w302_financials_composition_mount_no_db_503` asserts `create_app()` serves the route on the already mounted router, with the exact key set and nulls.
  - The empty-scope vector matches the ruled `/2` token and access basis.
- **`settled.ts` merge** (`ed11e07e`). This is a correct union: main's `the site's mini-grid assessment` plus the branch's `evidence across the estate`. Nothing else changed.

## Findings

### High

None.

### Medium

**M1. Pending cold consequence work does not make product-exposure coverage unknown, so a pending Site reads as a complete NO_LINES absence.** This is user-visible.
- Where: `backend/assetops_backend/estate/financials.py:208-213` (`windowed_lines`, cold branch).
- What is wrong: `read["withheld"]` from `ColdSiteReadService.money_on` is true when overlapping consequence work is pending at K (`cold_site_reads.py:214`). The code uses it only to mark existing lines PENDING; `covered` is left true.
- Contrast with EV: the equivalent states (a `STALE_BASIS` head not yet computed, or the pending guard) set `covered = False`, as c3-q2(2) requires ("a stale or pending selected cold/EV window, including EV STALE_BASIS or pending guard, makes its applicable category's full-scope coverage unknown").
- Probe result on the branch's fake snapshot: `MoneySnapshot(cold=[], cold_withheld=True)` gives the POTENTIAL_PRODUCT_EXPOSURE group `('NO_LINES', ['NO_LINES'])`. With heads present, the group is `INELIGIBLE` rather than `UNKNOWN_COVERAGE`.
- Why it matters: while the first cold exposure is still being computed, the Financials page states as a complete fact that no product exposure is recorded. That is the false completeness closure 3 forbids.
- Fix: in the cold branch, set `covered = False` when `read["withheld"]`. Extend `test_w302_money_historical_pending_and_no_gap_rows` to assert the product sentinel `UNKNOWN_COVERAGE` / `["NO_LINES","UNKNOWN_COVERAGE"]` with no heads, and `UNKNOWN_COVERAGE` with heads. Alternatively, obtain an Architect ruling that pending cold work is not a coverage gap.

**M2. The second-chain repository composition departs from the c3b text and is unruled.**
- Where: `backend/tests/test_w302_money_comparability_postgres.py:170-190` (`second_scenario_repository`).
- What is wrong: c3b names `CachedScenarioRepository(ReadOnlyYamlScenarioStore(root))`. The implementer found that this construction raises `AttributeError`, because the shipped store has no `get_scenario`. They used `CachedScenarioRepository(CompositeScenarioRepository(shipped=ReadOnlyYamlScenarioStore(root), user=UserYamlScenarioStore(<empty temp>)))` instead.
- They flagged it as "Applied, please confirm" in `.agent/W3-02-pending-rulings.md` c3b-q2 item 1. c3c ruled only item 2, and the file now marks c3b-q2 "RESOLVED" without confirming item 1.
- Why it matters: the N3 proof depends on this harness. It is test-only and matches the production composition, so I see no technical defect, but it is an open ruling.
- Fix: the Architect confirms item 1 (no code change expected), or names another construction. Correct the RESOLVED line so that it does not imply item 1 was ruled.

### Low

- **L1. A HISTORICAL-guard window with no head is labelled PENDING.** `financials.py:229-234`: when the EV pin is HISTORICAL with no derivable as-of basis but some stored history, `_select_as_of` returns the transient guard `HISTORICAL_CURRENT_CLAIM` with no head. `forced` treats every non-`STALE_BASIS` guard as pending, so the older head is shown as `PENDING` ("Updating"), although nothing is updating. Suggest treating only `em.ERROR_PENDING` as pending, and `HISTORICAL_CURRENT_CLAIM` without a head as WITHHELD or UNKNOWN. This is an edge case, and coverage is already unknown.
- **L2. EV fingerprint unit and price kind are hard-coded.** `financials.py:268-269` uses unit `"kWh"` and price kind `"GROSS_TARIFF_PER_KWH"`. The economic unit is `ev_money.TARIFF_UNIT` (`currency/kWh`, fixed by the `0026` CHECK), which mirrors c3-q2(5)'s W1 `currency/L`. This is correct today, because the CHECK makes the unit constant, but using the constant would keep the two domains symmetric.
- **L3. Diagnostics list every line, not only those in other partitions.** `compare` builds diagnostic `line_keys` from all lines in the category that have a non-null field value, including lines that share the same value. In a multi-window EV estate, DIFFERENT_WINDOW (and DIFFERENT_ASSUMPTION alongside MIXED_CURRENCY) will list every line. This is acceptable under the spec wording, but it is noisy for commit 4's display.
- **L4. An eligible line in an INELIGIBLE group inherits other lines' reasons.** Its exclusion entry falls back to the group's reasons (for example `PENDING` from a partition-mate), so the line appears to carry a reason it does not have. Consider adding a partition-level reason that says so explicitly.
- **L5. Mini-grid prior heads are dropped while recompute is pending or stale.** For a mini-grid Site in PENDING_RECOMPUTE or STALE_SOURCE, prior heads are not listed, because W3-01 `_mini_grid` returns no rows outside CURRENT/HISTORICAL (reading 6). Cold and EV, by contrast, list the prior head as PENDING, as closure 1 describes. Coverage does become UNKNOWN_COVERAGE, so nothing is falsely totalled. Ask the Architect to confirm this asymmetry when commit 4's copy is written.
- **L6. Stale references in docstrings and fixture text.** The `test_w302_money_api.py` docstring cites a non-existent `test_w302_money_persisted_postgres.py`. The comment in `test_w302_money_comparability_postgres.py:135-137` still says the parser pins EV-LAB-001 and that "Commit 3 not done (N3)". The `ev-lab-002.yaml` Foundation summary still says "W2-05a".

## Checks I ran (at `edcd8fce`)

- **Focused tests.** Command: `pytest tests/test_w302_money_api.py tests/test_w302_money_comparability_postgres.py tests/test_w205b_ev_scenarios.py tests/test_w302_evidence_api.py tests/test_w302_pinned_facades_postgres.py::test_select_consequence_on_carries_the_selected_head_limitations -q`, run on the private DB. Result: **126 passed, 0 skipped, 0 failed** (JUnit tests=126 skipped=0 failures=0 errors=0), 188.6 s. This includes both persisted two-EV-Site tests, the drift test, the parser test and the Financials 503 mount test.
- **First attempt.** It failed at import only because the venv's editable `assetops_contracts` resolved to the main worktree. With the worktree's packages on PYTHONPATH, it passed. This was an environment problem, not a product failure.
- **M1 probe.** A scratch test, outside the repo, against the branch fake snapshot. Result as quoted above.
- **`tools/check-agent-workflow.ps1`:** passed.
- **`tools/check-architecture.ps1`:** without a repo `.venv` in my worktree, rule 8 refused to run ("no Python interpreter", followed by vacuity messages). That is environmental. A rerun with `ASSETOPS_GUARD_PYTHON` set to the venv Python **passed** (exit 0).
- **`npx.cmd tsc --noEmit`** (frontend at head): exit 0.
- **Not run:** `npm.cmd test` and `npm.cmd run build` (the known sandbox limitation; the commit-3 frontend change is c2d words plus the `settled.ts` merge). The full backend suite is not due until commit 4, and I found no full-suite evidence for `edcd8fce` in the handoff; the handoff's last numbers predate the c3c change.

## Residual risk not named in the packet

- There is no Postgres test of a cold or W1 line under pending work or a stale Site. The pending, historical and coverage interactions are proven only on the fake snapshot.
- The COMPARABLE proof covers EV only. W1 COMPARABLE across two mini-grid Sites is unproven. The spec requires only the EV proof.
- A user-saved scenario with ID `ev-complete-lab-002` would also be admitted for EV-LAB-002. This is harmless while no such Site exists in production, but the admission is keyed on ID alone, exactly as ruled.
