# Review: K8 code phase (four-Site screens), ruling DIESEL-1-R3p (§9p)

- Reviewer: fresh Claude (independent first review), 2026-11-08.
- Branch `task/DIESEL-K8-four-site-screens` at `ee9c9805f`, merge-base `6913b3454` (main is now `d257bdc68`, R3q).
- Read: §9p (binding), `.agent/review-packet-K8.md`, `git diff main...HEAD`, the captures, and K9's branch (`AssetOpsV1-k9`, `39d4d2aa5`) for item 7.

## Verdict: FIX

One Medium blocks the merge. It is a regression in an existing, unchanged backend test that the packet's adjacent run did not include. The fix is small: a two-exception catch plus one test. The design, the money separation, the re-expectations and the device copy are otherwise correct and match §9p.

## Findings

### M1 (Medium, acceptance gap): `_fuel_rows` raises `KeyError` on fakes whose `__getattr__` uses a dict, which turns an existing test red

- **Where:** `backend/assetops_backend/estate/index.py:224`, `reader = getattr(snap, "fuel_findings", None)`.
- **What is wrong:** `getattr(..., None)` swallows only `AttributeError`. `test_w301_estate_api.py:38-39` `FakeSnapshot.__getattr__` returns `self.reads[name]`, which raises `KeyError` for an unconfigured read.
- **Failure scenario (reproduced):** `test_w301_estate_api.py::test_out_a2_finding_rows_carry_categories` fails on this branch with `KeyError: 'fuel_findings'` at `index.py:224`. On a `git archive main` copy the same file passes, so K8 caused it.
- **Why it matters:**
  - The full suite is red at merge.
  - §9p.2 item 4 requires that "a snapshot without it (test fakes) gives no fuel rows and no error".
  - The packet's "465 passed" adjacent run did not include `test_w301_estate_api.py`.
  - The same module already handles this exact case. `opportunity_read` (`index.py:124-127`) catches `(AttributeError, KeyError)` for this reason.
- **Fix:**
  - Use the `opportunity_read` pattern: `try: reader = snap.fuel_findings` / `except (AttributeError, KeyError): return []`.
  - Add one L0 case with a `KeyError`-raising `__getattr__` fake. Better still, run `select_finding_scope` over `test_w301_estate_api.FakeSnapshot`.
  - Rerun `test_w301_estate_api.py` and the other estate L0 files listed under Checks.

### L1 (Low, intent gap, not a spec deviation): the Portfolio fuel row reads "No action yet" above "Verified"

- **Where:** `frontend/src/estate/EstatePortfolio.tsx:202` renders `row.action_id !== null ? row.action_title : "No action yet"`. Under §9p.2 item 5 the fuel row keeps `action_* = None`.
- **What it shows:** the capture `estate-portfolio-1440.png` shows "No action yet" in bold, with "Verified" under it.
- **Why it matters:** §9p.1 item 7 adds the fuel label so the row does not contradict the Kisiwa board on the demo's main beat. The old "No action agreed yet" text is gone, but a bold "No action yet" next to a verified fix still reads as a half-contradiction.
- **Status:** the card was followed literally, so this is not a K8 defect. **Architect to rule.** The fix would be a frontend fuel-row title, such as the thread words. That touches a file outside §9p.13, so it could ride K8c or the W1 copy pass.

### L2 (Low, layout observation): the longer Kisiwa critical label pushes "Coverage" below the bounded panel's fold at 1440

- **Where:** `frontend/src/sites/MiniPerformance.tsx:1140`. The label is `${feederName(row)} · Critical load`, which now reads "Cold store (ice and fish) feeder delivered power · Critical load".
- **What it shows:** in `kisiwa-service-feeders-story-hour-1440.png` the label wraps to four lines in the bar-label column, and the "Coverage" disclosure is clipped at the bottom of "Where the power went". The Kobo capture (`.agent/W4-02-evidence/service-positive-1440-app.png`) wraps to two lines, and Coverage is fully visible there.
- **Why it is only Low:** the panel is a q12-7 `BoundedPanel` with an internal scroll region (`MiniPerformance.tsx:212-226`), so Coverage is still reachable by scrolling. At 390 it is fully visible.
- **Gap in the packet:** the packet's "no overflow" claim rests only on document `scrollWidth`, which cannot see vertical clipping inside a bounded panel.
- **Fix (optional):** recapture in K8c. If the owner walkthrough finds it, widen the label column or shorten the critical-label suffix.

### L3 (Low, acceptance gap, disclosed): two §9p.12 test obligations are met by argument, not by a failing test

1. **"Must fail if the join moves into `site_coverage`/`_mini_grid`" (§9p.12 item 2) is not mutation-proven.**
   - The L0 money test (`test_k8_estate_fuel.py:109-140`) appends `_fuel_rows` through its own wrapper of `portfolio.select_finding_scope`, and the World's money scope is a fake. It cannot see where the real join sits.
   - The Postgres money scope reads non-CURRENT coverage, so it selects no money either way.
   - My own read confirms the separation is real today:
     - `financials.py:417` and `evidence_money.py:463` call `coverage.site_coverage` through their own import, and neither calls `fuel_findings`;
     - the join is at `index.py:183-184`, after the per-Site row loop.
   - A cheap guard would close this: in the Postgres test, wrap the snapshot's `fuel_findings` and assert it is never called from inside `select_financial_scope` (inspect the stack, or call `select_financial_scope` alone and assert zero calls).
2. **The Postgres test asserts provenance `UNKNOWN`/`EMPTY_CITATION_SET`, not the "evidence-backed, not UNKNOWN" state §9p.12 asks for.**
   - K4a's synthetic windows cite no evidence. The evidence-backed state (`REGISTERED_SIMULATION`, 528 ids) is shown only in the clone printout, so it is not automated.
   - This is acceptable as disclosed. The batched `finding_revision_evidence` read path is exercised, but only with an empty result.

## Items checked

### 1. Estate fuel rows

- **Placement:**
  - `_fuel_rows` is called only inside `select_finding_scope`, after each Site's mini rows.
  - It never touches `cov`, `cutoffs` or the token units.
  - The money path (`select_financial_scope`, `site_coverage`, `_mini_grid`, `finding_index`) is untouched. Fuel money can reach no total by construction.
  - `portfolio.py:918` objectives and `money`/`selected_lines` come from `m_sites`/`m_lines_all` only.
- **Gate:** `domain == MINI_GRID and cov["state"] in (CURRENT, HISTORICAL, PARTIAL)`, per §9p.2 item 4.
- **Row fields:**
  - every mini key, in mini order (the L0 test asserts the key order);
  - `lens_flags` `["RISK"]`, categories `PROTECT_ASSET`/MOVES/`MG-8`, `fuel_finding_ref` link, private keys as specified;
  - `str(f.lifecycle)` is safe because `FuelFinding.lifecycle` is a `str` (`model.py:89`).
- **Price rules:** `_fuel_consequence` matches item 6 exactly: None → UNPRICED/null; UNPRICED → its id; PRICED and not CURRENT → UNKNOWN with no amounts; PRICED and CURRENT → `fuel_text.money` two-place amounts; the `basis` literal equals `mini.FUEL_BASIS` (asserted).
- **Action column:**
  - `place(..., label=None)` defaults byte-equal;
  - the label is mechanism-gated on `UNEXPLAINED_FUEL`;
  - Cold and EV rows are unchanged (mutation-proven, see below).
- **Single connection:**
  - `EstateSnapshot.fuel_findings` uses `self._c` for the store call and for the one batched evidence `SELECT`;
  - `fuel_findings_on` opens no transaction, and `fuel_findings` delegates through `_read`;
  - the Postgres test's `Pool` checkout listener saw exactly 1.
- **Module list:** `stored-composer-modules-v1.json` +2 (`actions.verification_rules`, `fuel_balance.finding_text`), in alphabetical position. `test_ch5c2_clock_guard.py` is green.
- **Observation, harmless:** `site_work_rows`/`_many` (`portfolio.py:720-770`) now include fuel rows, but no product caller uses them; I grepped `assetops_backend`, `tools` and `host`.

### 2. Device copy

- **Kobo byte-equal:**
  - Kobo's served names are "Residential feeder", "Health clinic" and "Grain mill" (`kobo-mini-grid-60kw.yaml`), so `/clinic|health/i` keeps `MINIGRID_OBJECTIVE`;
  - the CRITICAL label "Health clinic"/"Health post" keeps `CLINIC_FEEDER_LABEL`.
- **Kisiwa literals** are exact in the tests and on screen:
  - "Objective: serve Households, Cold store (ice and fish) and Water pump while protecting the battery reserve.";
  - "Cold store (ice and fish) feeder delivered power".
- **Non-demo template objective** ("Objective: serve Distribution load while protecting the battery reserve."): **acceptable, not a finding.**
  - R-LOAD's own wording ("any other Site's words are built from its own load names") requires it.
  - It is more truthful than v69's sentence, which claimed clinic and productive loads that the hybrid template does not have.
  - The capital "D" is the verbatim Foundation name, as §9p.5 specifies.
  - It is correctly recorded as a deviation (packet item 4).
  - No other test or tool asserts the old sentence for non-Kobo Sites (grepped).

### 3. Re-expectations

- **CO-6:**
  - `_kisiwa_present` is cached, with one `SELECT 1 FROM site WHERE site_code_key = lower(%s)`;
  - `expected_site_codes` matches §9p.7;
  - `objective_site_count == 3` and `double_count_violations` are kept, and `kisiwa_present` is returned;
  - `body["objectives"]` holds one entry per authorized Site (`portfolio.py:918`), so Kisiwa appears iff it is in the dataset. Three-Site gives 3, four-Site gives 4.
- **CH5D1-O1:**
  - `optimize_card(..., allowed=(KOBO, KISIWA_SITE))`;
  - the one-priced path is byte-for-byte;
  - the two-or-more path's text and detail are rebuilt with the same `card_text("cost.sites"/"cost.site")`, `sites_text` and `COST_SMALL` as `site_outcomes/read.py:794-815` `_optimize_card`, in summary Site order, with `claim is None`.
- **COH-1:** +3 routes, sorted and unique. The self-test proves the matcher is not vacuous.
- **COH-7a:** `SUMMARY_SITE_TZ` and the merged lookup, as specified.
- **Three-Site green:** proven by `expected_site_codes(False)` and the one-priced-with-Kisiwa-allowed case.

### 4. Out-of-list files

- **`findingIndex.tsx` (+2 lines):** confirmed. Without it the fuel row reads "Finding detail unavailable". The early return is limited to `kind === "FUEL_FINDING"` and still requires `linkFor(ref)`. It is not a K5 file.
- **`portfolioWords.ts` (+1 entry):** confirmed (coordinator ruling 1). It is byte-equal to the backend title. Without it, "Mechanism not recorded" would show.
- **Postgres coverage forcing:** confirmed as sound and test-scoped.
  - It wraps only `estate.index.site_coverage`. The money path imports `site_coverage` from `coverage` under its own name, so it stays real.
  - The first real-coverage read keeps the gate provable.
- **"Join moved into `site_coverage`", not mutation-proven:** accepted as disclosed. The compensating assertions plus my code read hold today. See L3 for a cheap guard.

### 5. Mutations

I re-ran these myself on `git archive` scratch copies. No repo file was edited.

| Mutation | Result |
|---|---|
| `_fuel_consequence(..., True)` (PRICED on HISTORICAL/PARTIAL) | 2 failed (`test_consequence_cases` PARTIAL, HISTORICAL) |
| gate becomes `if domain == MINI_GRID:` | 3 failed (`UNKNOWN`/`PENDING_RECOMPUTE`/`STALE_SOURCE` gate cases) |
| label not mechanism-gated (`if True`) | 1 failed (`test_cold_row_with_a_verified_thread_keeps_its_action_words`) |
| `**SUMMARY_SITE_TZ` dropped from the COH-7a lookup | 2 failed (both COH-7a Kisiwa cases) |
| `feederName` non-clinic branch returns `row.load_label` | 1 failed (feederName case) |
| `minigridObjective` regex becomes `/clinic/i` | 1 failed (`minigridObjective` case, through "Health post") |

### 6. Captures

- **What §9p.9(a) requires and the captures show:**
  - the Kisiwa Service CRITICAL feeder name;
  - estate Findings, all and Risks: one fuel row, linked, Protect, 119.57–180.43 USD, lens Risk;
  - the Portfolio row: Monitor / "Change verified: watch for it coming back" / "Verified", with the mechanism line;
  - the Protect fuel line: "shown on its own and never added to any other money".
- **Overflow and wording:**
  - every capture has document `scrollWidth` ≤ the viewport at 390;
  - the 390 tables scroll inside their own regions, which is the existing pattern;
  - no theft words (theft, stolen, steal, pilfer, siphon, "missing fuel") in any capture JSON.
- **Kisiwa Overview 409: a data/prepare matter, not a K8 defect.**
  - The 409 `AWAITING_EVIDENCE_MIGRATION` comes from `site_overview` `serve`'s imported-Site branch. That branch refuses before any K8 code runs, because the kept DB has no S2 comparison and no persisted `NO_LEGACY_EVIDENCE` cutover basis for Kisiwa's import.
  - K8 changes only how the objective sentence is worded once a summary renders.
  - The UI states the missing state honestly ("Awaiting evidence migration").
  - The rule itself is proven in the rendered-Overview frontend test (`s5SiteWindowOverview` own-loads case).
  - K9's branch already carries the Architect's R3r answer (`39d4d2aa5`: record Kisiwa's no-legacy cutover basis at register, plus a KIS-OV row), which confirms it is fixed in prepare data, not in K8.
  - The objective line on a real Kisiwa screen therefore stays unproven until K8c or K9's rehearsal captures it.

### 7. K9 merge

- **Expected text conflicts:**
  - `chain_coherence.py`: K9 adds `"kisiwa"` to `SITE_CODE` and `LOCAL_DAY_TZ`; K8 adds `SUMMARY_SITE_TZ` on the next line;
  - additive tails of `test_chain_coherence.py`, `test_demo_combined_finish_rows.py`, `demo_combined_finish.py` and `demo_combined_rows.py`.
- **No semantic clash.**
  - After K9, `{SITE_CODE[k]: z for k, z in LOCAL_DAY_TZ.items()}` already maps `KISIWA-001` to `Africa/Dar_es_Salaam`, and `SUMMARY_SITE_TZ` maps it to the same zone. The merged dict is identical, so `SUMMARY_SITE_TZ` becomes redundant but harmless. Keep both lines when resolving, or drop it with its comment. K8's COH-7a self-test stays green either way.
  - K9's `kis6` asserts four Sites in summary, chain and Portfolio objectives. That agrees with K8's CO-6 (`expected_site_codes(True)`; objectives are one per Site).
  - K9's KIS-7 requires the two-priced Optimize path, Kobo then Kisiwa, `claim None`, `cost.sites`. That agrees with K8's CH5D1-O1 two-priced branch (same builders, same order), and K8 stays lenient for three Sites.

## Checks I ran

All runs used the plan2 venv with the k8 PYTHONPATH.

**Backend, focused and adjacent**
- `test_k8_estate_fuel.py`, `test_demo_combined_finish_rows.py`, `tools/checks/test_chain_coherence.py`, `test_ch5c2_clock_guard.py`, `test_w303_portfolio_api.py`, `test_cc_placement.py`, `test_cov_partial_portfolio.py`, `test_ch6b2_portfolio_cards.py`, `test_pv1_value_lines.py`, `test_k4b_protect_fuel.py`, `test_out_b4_imports.py`: **493 passed, 1 skipped** (28 s).
- Twelve estate L0 files (`test_ch6b_estate_chain`, `test_post_w6_w3_estate_links`, `test_w301_estate_api`, `test_w301_estate_coverage`, `test_w302_*`, `test_w303_estate_cursor`, `test_w303_portfolio_reduction`, `test_w303_portfolio_workflow_labels`): **1 failed (M1), 214 passed**.
- 31 further estate/chain/board L0 files: **2 failed, 500 passed, 12 skipped**.
  - The 2 failures are `test_out_b1_board.py::test_mini_protect_battery_outcome_measured_without_warning` and `::test_board_imports_only_outcomes_and_stdlib`.
  - **They also fail on a `git archive main` copy, so they are pre-existing and not K8.** They are still a red-suite risk for E2 and should be routed to the coordinator: MG-8 in the Protect outcomes, and a `chain.vocabulary` import in `board.py`.

**Backend, Postgres**
- `test_k8_estate_fuel_postgres.py` on `assetops_k8_test`: **1 passed** (15 s). Free RAM was 3.9 GB before the run.

**Frontend**
- `npx.cmd vitest run` over `estatePortfolio`, `estateRoots`, `s5SiteWindowOverview` and `miniServiceRoutes`: **166/166 passed**. Vitest did run in this environment.
- `npx.cmd tsc --noEmit`: clean.

**Guards**
- `check-agent-workflow.ps1`: passed.
- `check-architecture.ps1`, run with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv: **passed**.
  - The first run, without that variable, failed. Rule 8's SQL extractor had no Python interpreter, because this worktree has no `.venv`.
  - That failure came from the environment, not from K8.

**Not run:** the full suite and prepare (§9p.12, owner rule). Layout evidence was not rerun; I reviewed the captures only.

## Residual risk not in the packet

- The pre-existing `test_out_b1_board.py` red pair on main (above).
- The fuel rows' inclusion in the unused `site_work_rows*` outputs: a future board caller would see them.
- The estate selection token does not cover fuel rows (§9p.10, already listed).
