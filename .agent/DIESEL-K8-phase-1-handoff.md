# K8 code phase: handoff 1 (PARTIAL; the builder stopped at the context cap)

The binding card is §9p (DIESEL-1-R3p) in `.agent/build-sheet-DIESEL-1.md` (lines 4738-5143). Read §9p.2, §9p.7 and §9p.12 to §9p.15 only.
- Worktree: `C:\Users\assef\Bineyame\AssetOpsV1-k8`.
- Branch: `task/DIESEL-K8-four-site-screens`. The coordinator named it; the card says `task/DIESEL-K8-estate-four-sites`. Record this as a process deviation.
- Main is merged in at 6913b3454 (fast-forward).
- The worktree has `frontend/node_modules` (`npm ci` done).

## Landed: commit ffc23b202 (all §9p code; no tests yet)

**Backend**
- `fuel_balance/adapters/postgres_fuel_balance_store.py`: `fuel_findings_on(c, …)`. `fuel_findings` now delegates to it.
- `estate/adapters/postgres_estate_read.py`:
  - the `fuel=None` kwarg (last) and `dispose`;
  - `EstateSnapshot.fuel_findings(t, s, from_, to, k)` returns `[{"finding", "evidence_ids"}]` (one batched `finding_revision_evidence` query).
- `estate/composition.py`: builds `fuel=build_fuel_balance_store(url)` (function-local import). `keys` gains `"fuel"`.
- `estate/index.py`:
  - the join at the end of the per-Site loop in `select_finding_scope`, gated on `MINI_GRID` and CURRENT/HISTORICAL/PARTIAL;
  - `_fuel_rows`, `_fuel_consequence`, `FUEL_MECHANISM` and `FUEL_CONSEQUENCE_BASIS` (literal, equals `mini.FUEL_BASIS`).
- `estate/portfolio.py`: `FUEL_THREAD_LABEL`. `portfolio_row` passes `label=` to `place` and uses it as `workflow_label`.
- `estate/placement.py`: `place(..., label=None)`.

**Config**
- `config/chain/stored-composer-modules-v1.json` gains `actions.verification_rules` and `fuel_balance.finding_text` (plain sorted list).

**Frontend**
- `sites/SiteWindowOverview.tsx`: `OverviewMiniReads.loadNames?`, `OBJECTIVE_NO_LOADS`, `minigridObjective()`; `ObjectiveLine` takes `loadNames`.
- `shell/SiteDetailFrame.tsx`: `loadNames` from `site.foundation.components` where LOAD.
- `sites/MiniPerformance.tsx`: exported `feederName` (R-LOAD).
- `estate/findingIndex.tsx` `findingLinkLive`: a `FUEL_FINDING` ref is live.
  - **Deviation to record:** the file is outside §9p.13's list. It is needed because the old gate required `kind === "FINDING"`, so the fuel row title would have read "Finding detail unavailable". It is not a K5 file, so S-4 does not fire.

**Tools**
- `demo_combined_rows.optimize_card(..., allowed=)` for one priced Site or two or more.
- `demo_combined_finish.py`: `_kisiwa_present`, `expected_site_codes`; CO-6 uses them and returns `kisiwa_present`; CH5D1-O1 passes `allowed=(KOBO, KISIWA_SITE)`.
- `checks/chain_coherence.py`: `SUMMARY_SITE_TZ` and the merged lookup in `_coh7a_window`.
- `screen_routes.json`: +3 routes.

**Docs**
- `backend/TESTING.md:327`.
- `backend/tests/test_demo_combined_postgres.py:3,9`.

## Pre-flight results (§9p.14)

- **(b) Met.** The served `load_label` is the Foundation `display_name` (`mini_depth/inputs.py:252`). Kobo's names are "Residential feeder", "Health clinic" and "Grain mill" (`kobo-mini-grid-60kw.yaml:188-201`), so Kobo matches R-LOAD.
- **(c) Met.** Stored Kisiwa timezone is `Africa/Dar_es_Salaam` (read from `assetops_demo3_kisiwa_test`).
- **(d)** The Portfolio renders `linkFor(link_refs.finding)` and accepts FUEL_FINDING (`chainRef.ts:43`, `operatorSiteRoutes.ts:611`). The Findings index needed the `findingIndex.tsx` gate change above.
- **(e)** Plain sorted list (`test_ch5c2_clock_guard.py:175`).
- **(g)** Only CO-6:451 (`== [KOBO, COLD, EV]`) and `SITE_CODE`, as the card says. CO-6b, CO-8 and `_boards` are three-Site by design.
- **(a) Not yet run.** Confirm on the clone that `/api/sites/KISIWA-001/overview` is the window summary, not the legacy model.
- **(f) Not yet checked.**
- **Kept-DB facts:** the fuel thread events are OPEN → ACTION_IN_HAND → CHANGE_APPLIED → RESOLVED_MONITORING (VERIFICATION_OUTCOME, 2026-11-02). Kisiwa holds 2 `mini_grid`/dispatch Finding revisions and 1 `fuel_balance` revision.

## Tests run on ffc23b202

- **Backend: green.** `test_w303_portfolio_api`, `test_cc_placement`, `test_cov_partial_portfolio`, `test_ch6b2_portfolio_cards`, `test_pv1_value_lines`, `test_k4b_protect_fuel`, `test_out_b4_imports`, `test_ch5c2_clock_guard`, `test_demo_combined_finish_rows` and `tools/checks/test_chain_coherence.py`: **465 passed, 1 skipped**.
  - Run from `backend/tests` with plan2 venv python.
  - `PYTHONPATH` = k8 `backend;contracts;tools;tools\checks;simulator;host`.
  - `test_screen_routes_file_is_the_app_route_list` passes with the +3 routes.
- **Frontend: 13 FAILED in `src/shell/__tests__/s5SiteWindowOverview.test.tsx`.** The other 7 files (estate, miniServiceRoutes, chainScreenRoutes) pass, 179 tests in all.
  - **Cause:** the frontend tests go through `SiteDetailFrame`, whose Site fixture uses the hybrid template's LOAD name "Distribution load". The objective now reads "Objective: serve Distribution load while protecting the battery reserve." The W1 rendered-text check rejects the word "load", and the H3 test expects `MINIGRID_OBJECTIVE`.
  - The card assumed tests pass no components ("undefined gives MINIGRID_OBJECTIVE, every existing caller and test byte-equal"). That is untrue for fixtures that render through `SiteDetailFrame`. Real Kobo stays byte-equal ("Health clinic").
  - **Next step options (only test files are in scope):**
    - (i) make that test file's mini-grid Site fixture carry Kobo's LOAD names ("Residential feeder", "Health clinic", "Grain mill"). Check whether the fixture is shared before editing it;
    - (ii) if the fixture is shared with many tests, stop and ask the Architect. Rendering "Distribution load" for a non-demo template is a new honesty question (the W1 check bans "load"), and it is S-7-like.
  - `tsc` printed nothing (clean).

## Remaining (in order)

1. Fix the s5SiteWindowOverview fixture (above) and re-run that file.
2. Write the §9p.12 tests:
   - `backend/tests/test_k8_estate_fuel.py`, L0 items 1-8. Call `index.select_finding_scope` directly with `monkeypatch.setattr(index, "site_coverage", …)` and a fake snap (`fuel_findings`, `finding_provenance`), with `req=SimpleNamespace(from_=…, to=…)` and `scope={"sites": [...], "k": …}`. For the Portfolio, use `test_w303_portfolio_api.World` with its `select_finding_scope` delegating to the real one. Assure: `chain.claims.estate_count_claims` with a fake req. Store parity: fake connection.
   - `backend/tests/test_k8_estate_fuel_postgres.py`: `assetops_k8_test` only, importing the `test_k4a_fuel_finding_postgres.py` helpers.
   - Additions to `test_demo_combined_finish_rows.py` (`expected_site_codes`, the four `optimize_card` cases).
   - Additions to `tools/checks/test_chain_coherence.py` (COH-7a Kisiwa Dar versus UTC; COH-1 fuel hrefs; the sorted and unique route file).
   - Frontend: `minigridObjective` cases, `feederName` cases ("Health post", "Health clinic", "Cold store (ice and fish)"), and an estate fixture fuel row (interval, "Verified", `/fuel-findings/` link).
   - Prove each named guard non-vacuous by mutation, after committing.
3. Clone captures (§9p.9 a):
   - check free RAM ≥ 2.5 GB first;
   - `CREATE DATABASE assetops_k8_audit_kisiwa TEMPLATE assetops_demo3_kisiwa_test` (no open connections to the template);
   - alembic upgrade to head;
   - read-only backend and vite;
   - captures at 1440 and 390: Kisiwa overview objective, Service CRITICAL feeder, estate Findings (all and Risks), Portfolio fuel row "Verified";
   - the in-process print of the fuel row, `category_counts.PROTECT_ASSET`, money lengths and `double_count_violations`;
   - drop the clone.
   - The K5 packet (`.agent/review-packet-K5.md:106-136`) has the serve recipe (`uvicorn lab_app:app` from `host`, cursor keys).
4. Packet `.agent/review-packet-K8.md`, then a final `tools\check-all.ps1 -Python <plan2 venv python>` with RAM ≥ 2.5 GB, then report to the coordinator.

## Size so far

About 0.45 of K8 code's 0.95 (S-8 stop at 1.1).
