# Review packet: K8 code phase (four-Site screens), ruling DIESEL-1-R3p (§9p)

- **Card:** `.agent/build-sheet-DIESEL-1.md` §9p (binding).
- **Branch:** `task/DIESEL-K8-four-site-screens`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k8`.
- **Builders:** three. Builders 1 and 2 each stopped at the context cap; see `.agent/DIESEL-K8-phase-1-handoff.md` and `-phase-2-handoff.md`.
- **USER_REVIEW_REQUIRED:** no. The card merges on review ACCEPT (W1 rule, §9p.9). The four-Site captures are deferred (see the end of this packet).

## Commits (since main 6913b3454)

| Commit | Content |
|---|---|
| ffc23b202 | All §9p code: the estate fuel join, the fuel Action column, W6 modules +2, R-LOAD device copy, the CO-6/CH5D1-O1/COH-1/COH-7a re-expectations, the K7-F L3 docs |
| 22e71b9a1 | Frontend tests |
| 24b72af05 | L0 tests and self-tests |
| cbddf1d31 | Coordinator ruling: `MECHANISM_WORDS.UNEXPLAINED_FUEL`, with its test |
| d730041f1 | `backend/tests/test_k8_estate_fuel_postgres.py` |
| ea6988a2f, 15cb16315 | Phase handoffs |

## Items and evidence

| §9p item | Delivered | Evidence |
|---|---|---|
| 9p.2 estate fuel join | `index.py` `_fuel_rows`. It runs after coverage and is gated on MINI_GRID and CURRENT/HISTORICAL/PARTIAL. `PostgresEstateRead(fuel=)` and `EstateSnapshot.fuel_findings` read on the one estate connection. | L0 items 1-5 and 8 (`test_k8_estate_fuel.py`, 21 passed). The Postgres test has one fuel row with a stored-row consequence and exactly one pool checkout. On the clone, the in-process read is below. |
| 9p.2 money untouched | The join lies outside `site_coverage`/`_mini_grid`. | L0 item 2 (equal money keys; `double_count_violations == []`). Postgres: no fuel id, revision id or consequence id in `money.groups` or `selected_lines`. Clone: `double_count_violations []` and `selected_lines` 0. |
| 9p.2 item 5, Action column | `FUEL_THREAD_LABEL`; `place(..., label=)` | L0 item 6. Clone, story week: "Verified", MONITOR / VERIFIED_WATCH_RETURN. |
| 9p.2 item 7, W6 modules +2 | `stored-composer-modules-v1.json` | `test_ch5c2_clock_guard.py` green |
| 9p.3 Assure | Inside-window count | L0 item 7 |
| 9p.5 R-LOAD device copy | `minigridObjective`, `feederName`, `SiteDetailFrame` `loadNames` | Frontend tests; Kisiwa captures (below) |
| 9p.7 re-expectations | CO-6 `expected_site_codes`, `optimize_card(allowed=)`, `SUMMARY_SITE_TZ`, +3 routes | `test_demo_combined_finish_rows.py` (three-Site and four-Site cases); `test_chain_coherence.py` |
| 9p.8 docs | `TESTING.md:327-328`; `test_demo_combined_postgres.py:3,9` | diff |
| Coordinator ruling 1 | `portfolioWords.ts` `UNEXPLAINED_FUEL: "Unexplained fuel overnight"`. It is byte-equal to `site_outcomes/mini.py:172` `FINDING_TITLE_BY_MECHANISM[UNEXPLAINED_FUEL]["SUPPORTED"]`. | `estatePortfolio.test.tsx` fuel-row case: the `<small>` mechanism line reads the title, never "Mechanism not recorded"; 66/66 passed. |
| Coordinator ruling 2 | The Postgres test forces Finding coverage to CURRENT for that Site only; money coverage stays real; the read is pinned to 2027-01-20. | See "Postgres test" below. |

### Clone in-process read (`assetops_k8_audit_kisiwa`, story week 2026-10-31 to 2026-11-07)

```
coverage [CURRENT]; finding rows 1, fuel rows 1; risks lens fuel rows 1
FUEL ROW title "Unexplained fuel overnight", SUPPORTED, lens ["RISK"], consequence PRICED 119.57-180.43 USD,
  source_revision_id 22d88684-..., basis UNEXPLAINED_FUEL_AT_DECLARED_PRICE,
  links.finding /sites/KISIWA-001/fuel-findings/c6aecaea-5c98-42f6-8015-52c22790e7c7, link_refs.finding.kind FUEL_FINDING
FUEL PROVENANCE state REGISTERED_SIMULATION (528 evidence ids)   <- evidence-backed, not UNKNOWN
PORTFOLIO FUEL ROW workflow_label "Verified", MONITOR / VERIFIED_WATCH_RETURN, mechanism UNEXPLAINED_FUEL
category_counts.PROTECT_ASSET {"open_findings": 1, "sites_with_primary_finding": 1}
money.groups 1, selected_lines 0, double_count_violations []
```

The one-day window 2026-10-31 to 2026-11-01 gives "Pending" (ACTION_IN_HAND), COMPARE_VALUE / PRICED_SINGLE. The thread is read as of that window, which is the intended reading.

### Postgres test (`test_k8_estate_fuel_postgres.py`, `assetops_k8_test`)

The test first reads with the real coverage: no fuel row (the gate). It then forces coverage to CURRENT and checks:
- exactly one pool checkout per read;
- the row's fields, the stored consequence (41.25-57.75 USD) and its basis;
- the Portfolio has the row, and its money holds no fuel id.

Result: 1 passed, 11 s.

`source_provenance` is honestly UNKNOWN / EMPTY_CITATION_SET, because K4a's synthetic windows cite no evidence. The evidence-backed state is shown on the clone above. **Connection count:** no existing engine-connect counting pattern exists, so the test adds a global `Pool` `checkout` listener for the one read.

## Mutation proofs (all run after commit, restored with `git checkout`, `git status` clean)

Builder 2 (handoff 2):

| Mutation | Failed |
|---|---|
| index.py gate becomes `if domain == MINI_GRID:` | L0 gate test [UNKNOWN, PENDING_RECOMPUTE, STALE_SOURCE] |
| portfolio.py label gate becomes `if r.get("_thread")` | `test_cold_row_with_a_verified_thread_keeps_its_action_words` |
| `VERIFIED_CLASS = ("CLOSED",)` | `test_assure_counts_the_verified_fuel_thread_only_inside_the_window` |
| `SUMMARY_SITE_TZ` dropped from the `_coh7a_window` lookup | COH-7a pass and fail cases |
| fuel-findings and fuel-verification routes removed from `screen_routes.json` | the two COH-1 cases |
| `ObjectiveLine` gets `minigridObjective(undefined)` | the own-loads overview case |
| `feederName` regex becomes `/clinic/` | the feederName case, plus 2 existing service tests |
| `findingIndex` FUEL_FINDING line removed | the estateRoots fuel-row case |

Builder 1 ran no mutations (code only).

Builder 3:

| Mutation | Failed |
|---|---|
| `MECHANISM_WORDS.UNEXPLAINED_FUEL` removed | `estatePortfolio.test.tsx` fuel-row case (1 failed, 65 passed) |
| index.py gate removed (`if domain == MINI_GRID:`) | Postgres test, at the real-coverage step (the fuel row appears) |
| index.py gate inverted (`not in (CURRENT, HISTORICAL, PARTIAL)`) | Postgres test, at the real-coverage step (the row appears with UNKNOWN coverage; the forced step would lose it) |

**Not mutation-proven:** "the join moves into `site_coverage`/`_mini_grid`" (§9p.12 item 2).
- **Why:** at L0 the World's `select_financial_scope` is a fake. In the Postgres test the money scope reads real coverage, which is not CURRENT for the fixture Site, so money cannot select either way.
- **Compensating assertions:**
  - L0: equal `selected_lines`/`money`/`value_cards`/`footer`/`combined_value*` with and without the fuel Finding, and `double_count_violations == []`;
  - Postgres: no fuel finding, revision or consequence id anywhere in `money.groups`/`selected_lines`;
  - clone (real CURRENT coverage, real money): `selected_lines` 0, `double_count_violations []`.

## Captures (clone `assetops_k8_audit_kisiwa`, 1440 and 390)

**Setup**
- Clone: `CREATE DATABASE assetops_k8_audit_kisiwa TEMPLATE assetops_demo3_kisiwa_test`, after confirming 0 open connections on the template.
- Alembic `upgrade head`, from 0057 to 0058.
- Serve: `uvicorn lab_app:app` (no schedule loop, no ticks) with the kept work dir's cursor keys, plus the K8 vite dev server. Both are read-only.
- Headless Chrome over CDP.
- After capture: both servers were killed by PID and the clone dropped. The template is unchanged (0 connections, still present).

**Files**
- Folder: `.agent/K8-captures/`.
- Each capture is `<name>-<width>.png`.
- Text and measurements are in `captures.json`, `captures-kisiwa-service-feeders-story.json` and `captures-kisiwa-overview-story.json`.
- Every capture has `scrollWidth` 1425 at 1440 and 390 at 390 (no horizontal scroll).

| Capture | Path | What it shows |
|---|---|---|
| K6b fuel verdict | `k6b-fuel-verdict` | VERIFIED: "Fuel stayed accounted for", 3 of 3 nights, ACT-001, source "Unexplained fuel overnight, 31 Oct" |
| K5 fuel night 4 and 6 | `k5-fuel-night4`, `k5-fuel-night6` | Fuel night mode (31 Oct; 2 Nov) |
| K5 fuel Finding | `k5-fuel-finding` | The fuel Finding page |
| Kisiwa Service, story hour | `kisiwa-service-feeders-story-hour` | CRITICAL card "Cold store (ice and fish) (critical)", 4 kW. The bars read "Cold store (ice and fish) feeder delivered power · Critical load", "Water pump" and "Households". |
| Kisiwa Service, default (today) | `kisiwa-service-feeders` | No selected assessment for 8 Nov (no readings that day) |
| Kisiwa Overview, default and 3 Nov | `kisiwa-board-overview`, `kisiwa-overview-story-day` | "Awaiting evidence migration" (see pre-flight (a)). The objective line cannot render. |
| Estate Findings, all and Risks | `estate-findings-all`, `estate-findings-risks` | One row: "Unexplained fuel overnight" (link), Protect asset and capital, Confirmed, 119.57–180.43 USD, lens Risk. Never "Finding detail unavailable". |
| Portfolio, story week | `estate-portfolio` | See below |

The Portfolio capture shows:
- the row "Unexplained fuel overnight" with mechanism line **"Unexplained fuel overnight"** (never "Mechanism not recorded"), `$119.57–$180.43`, Monitor "Change verified: watch for it coming back", and "No action yet / Verified";
- the Protect card's fuel line: "Kisiwa island mini-grid · Unexplained fuel on the night of 31 Oct: about 95.7–144.3 L, 119.57–180.43 USD at your declared price (a modelled range, shown on its own)", plus "Unexplained fuel is shown on its own and never added to any other money";
- "Fixes confirmed · 1".

**Not capturable on the clone**
- **The Kisiwa Overview objective line.** The Kisiwa Overview API answers 409 (pre-flight (a)). The objective rule is proven only by the frontend tests: the own-loads case, plus `minigridObjective` with Kisiwa names giving the exact literal.
- **The Kisiwa "board".** Kisiwa Site boards belong to K9 (`SITE_CODE`, §9p.7). The Protect fuel line was captured on the Portfolio, where `PortfolioOutcomes` renders it (§9p.11).
- **Known and deferred:** the Service table shows the Kisiwa template's device ids "load-clinic", "load-mill" and "load-res" beside the right names. That is MD-KIS-K1-1; template v2 is deferred (§9p.6, §9p.10).

## Pre-flight (a)

**Met: `SERVICE_FEEDERS` never reaches a Kisiwa screen. No §9p stop, and S-5 does not fire.**

- **What the API answers.** On the clone, `GET /api/sites/KISIWA-001/overview` (no date, `date=2026-10-31`, `date=2026-11-04`) answers **409 `AWAITING_EVIDENCE_MIGRATION`**. Kisiwa is an imported Site, so `site_overview/route.py` `serve` takes the imported branch (scope found). It refuses because the kept DB has neither a passing S2 Evidence comparison nor a persisted `NO_LEGACY_EVIDENCE` cutover basis for Kisiwa's import. The legacy model, which holds `evidence/overview.py`'s `SERVICE_FEEDERS`, is never reached.
- **What the screens show.** No API body and none of the 22 captures contains "Clinic feeder", "Mill feeder", "residential-meter", "clinic-meter" or "mill-meter".
- **Finding for the coordinator and K9.** This is not a K8 code issue and not in §9p.13's files. In the kept Kisiwa DB, the Kisiwa Site Overview tab reads "Awaiting evidence migration", so the R-LOAD objective line is never shown there. If the demo walks the Kisiwa Overview, the rehearsal prepare needs Kisiwa's cutover basis, or the evidence migration, recorded. The Architect should rule on that.

## Deviations

1. **Branch name:** `task/DIESEL-K8-four-site-screens`, which the coordinator named. The card names `task/DIESEL-K8-estate-four-sites`.
2. **`frontend/src/estate/findingIndex.tsx`** is outside §9p.13. `findingLinkLive` accepts a `FUEL_FINDING` ref; the old `kind === "FINDING"` gate would have rendered "Finding detail unavailable". It is not a K5 file, so S-4 does not fire. Proof: the `estateRoots.test.tsx` fuel-row case, which failed when the line was removed.
3. **`frontend/src/estate/portfolioWords.ts`** is outside §9p.13 (coordinator ruling 1). It adds one `MECHANISM_WORDS` entry so the fuel row no longer reads "Mechanism not recorded".
4. **The objective line on non-demo templates changes.** Before, every template read: `Objective: serve residential, clinic and productive loads while protecting the battery reserve.` After:
   - Hybrid template (LOAD "Distribution load"): `Objective: serve Distribution load while protecting the battery reserve.`
   - Twin-tank template (`twin-tank-mini-grid-150kw.yaml`, LOADs "Residential feeder" and "Grain mill feeder"): `Objective: serve Residential feeder and Grain mill feeder while protecting the battery reserve.`
   - Kobo stays byte-equal, because "Health clinic" matches `/clinic|health/i`.
   - The `s5SiteWindowOverview` test uses a local Kobo-named copy of the shared fixture (shared in 209 places, unchanged).
5. **Postgres coverage forcing** (coordinator ruling 2). This is test-scoped only:
   - it wraps `estate.index.site_coverage`, forcing CURRENT for the fixture Site's MINI_GRID coverage;
   - `evidence_money.py:463` `site_coverage` is not wrapped;
   - `pin_read_at` (from `test_w301_estate_index_postgres`) pins the read to 2027-01-20.
   A first read with real coverage keeps the gate mutation-provable (removed and inverted both fail).
6. **"Join moved into `site_coverage`" is not mutation-proven.** The compensating assertions are listed above.
7. **Read-only sed/grep through Bash:** builders 1 and 2 used read-only `sed`/`grep` through Bash, against the coordinator's Write/Edit-only rule. Builder 3 did not.

## Checks

**Builder 3**
- `tools\check-all.ps1 -Python <plan2 venv>` at d730041f1: **All 17 guards passed**. These include:
  - architecture, navigation truthfulness and agent workflow;
  - chain coherence (169 passed);
  - the frontend hard-wiring ratchet (totals api 12, href 24, lit 70, cmp 51, code 3);
  - the estate guard self-tests (15 passed in 19 min, slowed because another builder's check-all ran beside it).
- `test_k8_estate_fuel_postgres.py` on `assetops_k8_test`: 1 passed.
- `estatePortfolio.test.tsx`: 66/66.

**Builders 1-2 (handoffs)**
- Backend adjacent files: 465 passed, 1 skipped.
- `test_k8_estate_fuel.py`: 21 passed.
- Frontend: s5 63/63, and 103/103 across the three other files.
- `tsc` clean.

**Not run:** the full suite and prepare (§9p.12).

**Left in place:** the DB `assetops_k8_test` (scratch `*_test`) is kept for the reviewer's rerun. The clone is dropped.

## Size

Against K8 code's 0.95 (S-8 stops above 1.1):

| Work | Size |
|---|---|
| Builders 1-2 (code 0.45, tests 0.25) | about 0.70 |
| Builder 3: mechanism words | 0.01 |
| Builder 3: Postgres test and mutations | 0.06 |
| Builder 3: clone captures and in-process evidence | 0.09 |
| Builder 3: packet | 0.02 |
| **Total** | **about 0.88** |

That is within 0.95, and S-8 does not fire.

## Deferred

The four-Site capture phase moves to K9's rehearsal DB as `task/DIESEL-K8c-captures` (§9p.9 b, 0.25). It covers:
- the four-Site Portfolio, estate Findings (all and Risks), and the Sites list and navigation;
- the all-26 recapture;
- K4b's Protect line on the four-Site Portfolio.

The rehearsal DB and work folder are kept until it is done.

## Residual risk

- The selection token does not cover fuel rows (§9p.10, after the demo).
- Cold and EV rows still read "No action agreed yet" next to domain Actions. This is pre-existing and listed in §9p.10.

## Fix round (review-K8.md M1, L3)

- **M1.** `estate/index.py` `_fuel_rows` now reads `snap.fuel_findings` inside `try/except (AttributeError, KeyError)` and returns no rows (same pattern as `opportunity_read`). Before, `getattr(snap, "fuel_findings", None)` let a fake snapshot's `KeyError` escape. New L0 test `test_k8_m1_snapshot_whose_fuel_lookup_raises_keyerror_or_attributeerror_yields_no_fuel_rows` in `test_w301_estate_api.py` covers both exceptions.
- **L3 join placement.** `test_k8_estate_fuel_postgres.py` wraps `portfolio.select_financial_scope` with a spy snapshot that records any `fuel_findings` access, and asserts the wrapper ran (non-vacuous) and recorded no touch. Mutation (committed code first): added `getattr(snap, "fuel_findings", None)` to `select_financial_scope`; the test failed with `AssertionError: select_financial_scope reached the fuel reader`; reverted with `git checkout`.
- **L3 provenance.** The evidence-backed provenance state is proven only in the Kisiwa clone printout; the K4a fixture cites no evidence, so the Postgres test asserts UNKNOWN/EMPTY_CITATION_SET. The K8c capture phase on the rehearsal DB will confirm the evidence-backed state.
- **Tests.** `test_w301_estate_api.py`, `test_k8_estate_fuel.py`, `test_k8_estate_fuel_postgres.py` (on `assetops_k8_test`): 34 passed. L1 and L2 untouched.
