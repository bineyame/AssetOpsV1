# K8 code phase: handoff 2 (PARTIAL; builder 2 stopped at the context cap)

Read handoff 1 (`.agent/DIESEL-K8-phase-1-handoff.md`) and §9p first. Worktree, branch and PYTHONPATH are unchanged.

## Landed since ea6988a2f

- **22e71b9a1 (frontend tests)**
  - `s5SiteWindowOverview.test.tsx`: the Site is a local `withLoadNames(KOBO_LOAD_NAMES)` copy of `HYBRID_MINI_GRID_SITE`. The shared fixture is unchanged; it is used in 209 places. Added:
    - an own-loads case (Kisiwa names: the exact data-driven sentence, plus W1 and default vocabulary scans clean);
    - `minigridObjective` cases.
  - `miniServiceRoutes.test.tsx`: `feederName` cases ("Health post", "Health clinic", "Cold store (ice and fish)", non-critical).
  - `estateRoots.test.tsx`: a fuel row in the Risks lens. Its title is an `<a>` to `/sites/KISIWA-001/fuel-findings/<id>`, it shows `41.25–57.75 USD`, it never shows "Finding detail unavailable", and the vocabulary scan is clean. This is the coordinator's pass/fail proof for the `findingIndex.tsx` deviation.
  - `estatePortfolio.test.tsx`: a fuel row shows `$41.25–$57.75`, "Monitor / Verified; watch for a return", workflow "Verified", and the link to its fuel page.
  - Results: s5 63/63, the three others 103/103, `tsc` clean.
- **24b72af05 (L0 and self-tests)**
  - `backend/tests/test_k8_estate_fuel.py`: §9p.12 items 1-8, 21 passed. It also checks that the key order matches a mini row, and that a cold Site never reads fuel.
  - `test_demo_combined_finish_rows.py`: `test_r3p_expected_site_codes_read_from_data` and `test_r3p_optimize_card_two_priced_sites_listed_never_summed`, which covers the four §9p.7 cases plus a single-priced case with Kisiwa allowed.
  - `tools/checks/test_chain_coherence.py`: COH-1 fuel, fuel-verdict and mill-verdict hrefs; COH-7a Kisiwa Dar day passes and the UTC day fails. Sorted and unique was already covered by `test_screen_routes_file_is_the_app_route_list`.

## Mutation proofs (all run after commit; restored with `git checkout`; `git status` clean)

| Mutation | Failed |
|---|---|
| index.py gate becomes `if domain == MINI_GRID:` | gate test [UNKNOWN, PENDING_RECOMPUTE, STALE_SOURCE] |
| portfolio.py label gate becomes `if r.get("_thread")` | `test_cold_row_with_a_verified_thread_keeps_its_action_words` |
| `VERIFIED_CLASS = ("CLOSED",)` | `test_assure_counts_the_verified_fuel_thread_only_inside_the_window` |
| `SUMMARY_SITE_TZ` dropped from the `_coh7a_window` lookup | COH-7a pass and fail cases (both) |
| fuel-findings and fuel-verification routes removed from `screen_routes.json` | the two COH-1 cases |
| `ObjectiveLine` gets `minigridObjective(undefined)` | the own-loads overview case |
| `feederName` regex becomes `/clinic/` | the feederName case, plus 2 existing service tests |
| `findingIndex` FUEL_FINDING line removed | the estateRoots fuel-row case |

**Not mutation-proven:** "the join moves into `site_coverage`/`_mini_grid`" (item 2). The World's `select_financial_scope` is a fake, so at L0 money cannot see Finding rows. The L0 test does assert equal money keys, `double_count_violations == []`, and no fuel id in the money keys. The real-money proof belongs in the Postgres test below.

## Found: a client wording gap (not fixed; needs a coordinator or Architect ruling, S-7-like)

The Portfolio fuel row renders **"Mechanism not recorded"**: `frontend/src/estate/portfolioWords.ts:193` `MECHANISM_WORDS` has no `UNEXPLAINED_FUEL` entry. That is untrue, because the mechanism is recorded. The file is outside §9p.13. The fix is one map entry, but its wording needs a ruling. Seen in the estatePortfolio test's rendered text.

## Pre-flight (f)

**Met.** `test_k4a_fuel_finding_postgres.py` exposes `Fuel`, the `kobo` fixture, `PRICED_NIGHT` (2027-01-10) and the re-exported `store`/`engine` fixtures, and `run_fixture` (from `test_s4_assumptions_postgres`) prices the night. All of these are importable as they are (module-level, under `if URL:`).

**Caveat for the Postgres test:** the `kobo` Site has no settled mini selection for the January 2027 window, so estate coverage is not CURRENT, and the join's gate gives **no** fuel row. Options:
- (i) wrap `index.site_coverage` and force `state=CURRENT` for that Site only (the money scope's own `site_coverage` in `evidence_money.py:463` stays real). Record this in the packet;
- (ii) use `test_w301_estate_index_postgres` `mini` (CaseRunner F03 on 2026-10-11, CURRENT) and raise the fuel Finding on the same Site for night 2026-10-10. It is UNPRICED, because the published price is later.

Prefer (i). Also pin the estate `read_at` after the virtual clock (2027-01-20) with `test_w301_estate_index_postgres.pin_read_at`, or the cutoff hides the Finding.

## Remaining (in order)

1. `backend/tests/test_k8_estate_fuel_postgres.py` on `assetops_k8_test`, as §9p.12 describes plus the caveat above. Connection count: look for an existing engine-connect counting pattern (`test_w303_portfolio_api.py:345` counts snapshots, not connections). If none exists, skip that assertion and say so.
2. Kisiwa clone captures and pre-flight (a): handoff 1, item 3, and the coordinator's capture list (K6b fuel verdict, K5 fuel pages, the board's Protect fuel line, objective and feeder copy, the estate fuel row, plus the in-process print). Check free RAM ≥ 2.5 GB before every heavy step.
3. `.agent/review-packet-K8.md`. Deviations to record:
   - the branch name;
   - `findingIndex.tsx` (the test above);
   - non-demo templates' objective line. Before: `Objective: serve residential, clinic and productive loads while protecting the battery reserve.` After, for the hybrid template ("Distribution load"): `Objective: serve Distribution load while protecting the battery reserve.` The twin-tank template's after line is the same rule over its LOAD names; read them from its yaml;
   - the "Mechanism not recorded" gap;
   - L0 money is a fake (above).
4. `tools\check-all.ps1 -Python <plan2 venv python>`, after checking RAM.

## Size

About 0.70 of 0.95 so far (code 0.45 + tests 0.25). The Postgres test, captures and packet are about 0.2 more. S-8 is not near.
