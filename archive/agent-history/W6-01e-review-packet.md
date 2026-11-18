# W6-01e review packet: E1 global Operational records read, E2 Operational records page

Branch `task/W6-01e-operational-records`. Base: main `2dc2e5ed` (W6-01c merge `fdbbccf4`, W6-01d merge `1fd48441`); K4a is
not on main (no `activeLabel` in `frontend/src`), so the E2 rail edit follows the "E2 merges first" branch of P-E2-11.
Commits: E1 `18355b0a`; E2 Lane B `39feb0db`; E2 Lane A `fdd71cfc`; evidence/packet in the closing commit.

## Outcome

- `GET /api/work/operational-records?kind=` returns `global-work-index-1` rows for every authorized imported Site:
  root-occurrence window membership, selected `(recorded_at,id)` head at K, kind filter on the head before count,
  token, sort and page; `kind` normalized into the cursor/token `filter`; old roots keep `filter: null`.
- `/operational-records` page in the mock `oprecords` structure, live rail root (nine links), live REC links in the
  C3 request record notice, and the Evidence-root `Operational records →` example as a real link.

## Files

- E1: `backend/assetops_backend/work/operational_index.py` (new), `work/global_index.py`, `work/adapters/postgres_global_read.py`,
  `global_work_api.py`, `backend/tests/test_w601e_operational_index.py` (new), `tools/w601_seed.py`.
- E2 Lane B: `frontend/src/work/{OperationalRecords.tsx (new),globalWorkClient.ts,globalWorkParts.tsx,globalWork.css}`,
  `frontend/src/work/__tests__/operationalRecords.test.tsx` (new).
- E2 Lane A: `App.tsx`, `shell/{OperatorShellLayout.tsx,operatorSiteRoutes.ts}`, the A2Q11/F1 rail tests (operatorRailInventory,
  operatorRouteFrames, w301EstateShellRoutes, estatePortfolioRoutes, operatorSiteTabs, simulatorLabWorkspaceEntryPoint,
  siteDetailRoute, siteFoundationRoute, sitesIndexRoute, sharedVisualVocabulary), `work/WorkRequestRecord.tsx` +
  test, `estate/EstateEvidence.tsx` + test, `tools/checks/{navigation-truthfulness.ps1,navigation-rail-fixtures.ps1}`,
  `v69-screen-ledger.json` (`oprecords`, `wr-record` interaction), `v69-dependency-registry-pilot.json` (`oprecords:1,3`).
- Evidence: `.agent/W6-01-evidence/E2/{capture.mjs,mock_capture.mjs,run_state.sh,api_empty_scope.py,build_manifest.py,manifest.json,seed-*.json,screenshots/}`.

## Acceptance (P-E-0 … P-E2-12)

| P-ID | Status | Evidence |
| --- | --- | --- |
| P-E-0 | met | base SHAs above; reuses C1 `Writer.post_operational_record` and the `_CASE_OPERATIONAL` root/head shape (`_OPERATIONAL`) |
| P-E1-1 | met, see KD1 | `global_index.py` read(): one `kind == OPERATIONAL` branch calls `select_operational(gx, tenant_id, sites, from, to, k, record_kind, cutoff=...)`; old `SELECT[kind]` call unchanged |
| P-E1-2 | met | `record_kind` last field; `KEYS[...]` adds `kind`; decoder admits string filter only on operational; filter mismatch 409 before selection; `test_kind_cursor_mismatch`, `test_old_route_cursor_filter_stays_null` |
| P-E1-3 | met | `test_correction_head_keeps_root_window` (head kind/body/case; root code/occurrence; C1 root-case membership unchanged after a case-moving correction) |
| P-E1-4/5 | met | `test_non_submitted_and_missing_case_fail_closed` (rolled-back replica-role mutation; also filtered reads) |
| P-E1-6 | met | `test_case_link_by_kind`: incident root-day window, request detail href, explicit cutoff only (`m.iso`), head case after a move |
| P-E1-7/8 | met | full basis in `operational_index.py`; `test_operational_basis_changes_with_head_and_case`, `test_quantity_and_period_end_wire` |
| P-E1-9 | met | `--fixture operational` (7 in-window demo roots, 2026-10-13 KOBO-002 SITE_VISIT, other-tenant SITE_VISIT, correction at `+1s`, `_not_future` DB-time check, stored read-back); stress OPERATOR_LOG (`test_stress_record_body`) |
| P-E1-10 | met | all ten named tests plus two extra |
| P-E2-1 | met | optional `kind` on `GlobalWorkQuery`/`globalWorkHref`; hook `kindOf` validator; API gets `kind` only from `operationalRecords`; three old page tests pass unchanged |
| P-E2-2 | met | `.v69-chips` buttons with `aria-pressed`; invalid/repeated `kind` = `INVALID_KIND` RefusalBlock, no fetch; chips keep window/cutoff |
| P-E2-3/4 | met | card headings, first note, amber fourth card; mock panel description verbatim |
| P-E2-5/6 | met, see KD2 | inert form (two `.input-row`s, two Site options, disabled controls, `UnavailableInline` submit, reason line); two-paragraph prose |
| P-E2-7/8 | met | frame literals, eight columns with px widths (1150), correction disclosure, reading line, ` →` Feeds, blue `Submitted` |
| P-E2-9 | met | `Operational records →` live from the effective window; tests: two inert labels, two links, effective-window test |
| P-E2-10 | met | `linkedRecHref`; `REC_PAGE_PREPARED` and the interim comment removed; ledger literal; current + historical captures |
| P-E2-11 | met | rail line, `$expected`, three W6-01e rail fixtures, nine-link and focus-order pins, A2Q11 literals |
| P-E2-12 | met | 21 capture states at 1440/390 in `manifest.json` (see Checks) |

## Checks

- Focused backend (real Postgres, private `assetops_w601e_test`, dropped): `test_w601e_operational_index.py` 12 passed
  (154 s); adjacent `test_w601a/b/c` 46 passed (195 s, `-n 2 --dist loadfile`), on E1 `18355b0a`.
- Frontend: `src/work` 117 passed; `src/shell src/estate src/sites src/work src/ui` 112 files / 2664 passed; `tsc -b` clean;
  full `vitest run` 115 files / 2725 passed, exit 0; `npm run build` ok (chunk-size warning only), on `fdd71cfc`.
- Guards: `tools/check-all.ps1` all 11 passed (includes the rail fixture seam, whose three new W6-01e mutations must
  each fail the guard); `check_v69_ledger.py` valid; registry checker exit 0.
- Captures (vite dev + uvicorn, one at a time; Chrome headless), `operational --clock 2026-10-21T12:00:00Z`, real reads
  2026-10-23 ~08:34-08:40 UTC: positive 7 (5 + page two 2), kinds 2/2/3/0, broad SITE_VISIT 1, historical
  (`known_at=2026-10-21T12:00:00Z`: REC-000003 head = OPERATOR_LOG, OPERATOR_LOG 3), zero, empty_scope (test-only
  `api_empty_scope:app`), invalid/repeated kind and invalid window (0 requests), 503, cursor+kind 409, stress
  collapsed/expanded, Evidence root, `wr-record` current/historical, REC target. Document width never exceeds the
  viewport (1425/1425 with scrollbar, 390/390); table scrolls in-panel (1150 px).
- Measured (1440/390): cards 115/281 (cap 150/330); chips 33/73 (40/80); Operational records 631/654 (650/780), stress
  collapsed 280/288; prose 298/223 (330/300); form 298/486 (cap 180/230, KD2). Mock: form 289/443, chips 31/70.
- Full backend suite: not run by this builder (coordinator-scheduled per slice).

## Known deviations

1. KD1 `select_operational` has a trailing keyword-only `cutoff` beyond the P-E1-1 literal: P-E1-6 needs the explicit
   inbound cutoff, and the existing old-root dispatch already passes it as `cutoff` (the ruling's "six-argument" call
   is seven-argument on main). Same semantics as `select_maintenance`.
2. KD2 §2 caps for `Record a manual reading` (180/230) predate P-E2-5's restored form; the mock form itself measures
   289/443, ours 298/486. Architect to amend the cap; no layout change made.
3. Unruled literals chosen: `period_end` second line `Until {date UTC}`; MANUAL_READING second line always
   `Reading: {quantity} {unit}`; the C3 REC href parameter order `from,to,kind[,known_at]` (ruling order), while the
   page's own hrefs use `from,to,known_at,kind`.
4. Non-SUBMITTED and missing-case checks run over the whole selected window before the kind filter (fail closed).
5. `.agent/mock-departure-register.md` is not on the cards: R12/R29-R31 remain `planned` there and R34 is now
   resolved in code; the register status update is for the Architect.

## Residual risk / user-review focus

- Prose font size follows the shared `.prose` class and reads slightly larger than the mock.
- Mock departures for the walkthrough: D4 R29/R30/R31, D1 R12 (labelled in `OperationalRecords.tsx` header).
- USER_REVIEW: UI slice; per owner rule it merges on review ACCEPT and joins the post-W6 walkthrough.
