# Post-W6 audit, batch 07: W2 cold Site

IDs: `cold-findings`, `cold`, `cold-evidence`, `cold-evidence-analysis`, `cold-financials`, `cold-assumptions`. Branch `audit/batch-07` at main `b0387120` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review6`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows.

Machine-readable record: `batch-07.json` (60 pairs). Side-by-side view: `index.html`. Difference source: `differences.json` (written by `tools/differences.py`).

## Run record

- **Producer (reviewed, unmodified).** `.agent/W2-F-evidence/seed.py` (the W2-F unit-5 capture seed: W2-02 cold replay -> attestation -> release upload -> W2-03 worker -> W2-04 drain, ordinary replay paths only). Run twice: `cold excursion` (site `00000002-...0002`) and `cold normal` (site `00000001-...0002`), with `PYTHONPATH` set to this worktree's `backend;gateway;simulator;contracts;host` (the shared `.venv` otherwise imports another tree's package).
- **Database.** `assetops_audit_b07_test` in `assetopsv1-postgres-1` (rule (a): `assetops_audit_bNN*_test`). Created before seeding (the harness resets in place), reset by the seed itself between phases, dropped with `WITH (FORCE)` after capture; confirmed absent. No producer `_audit` DB was needed, so nothing batch 6 holds was touched. `pg_database` was checked first.
- **Servers.** API `host/` `uvicorn lab_app:app` on 127.0.0.1:18701 (`DATABASE_URL` = the audit DB), restarted for the normal phase; Vite `--port 5187 --strictPort` with `ASSETOPS_API_PORT=18701`; Chrome CDP 9527. Windows PIDs 22708, 27972 (API) and 17348 (Vite) were stopped by PID.
- **Capture.** `tools/capture-b7.mjs` is `capture-b3.mjs` with only the CDP port and profile prefix changed (capture-only: navigate, wait, screenshot, measure DOM). Targets: `tools/targets-excursion.json`, `tools/targets-normal.json` (written by `tools/mk_targets.py`, with the same windows as W2-F `capture.mjs`). Claims: excursion 288/288, normal 72/72. Logs are in `logs/`.
- **Cases.** Excursion, for all six IDs: stocked (`2026-10-06T19:00Z`-`20:05Z`), no-selection (the same hours on 10-05), refused (from > to) and no-window (bare route). Normal: stocked window, for all six IDs. 30 cases x 2 widths = **60 pairs** (12 required representative pairs plus 48 further states).

## Inventory reconciliation against `frontend/src/App.tsx`

| ID | Mounted route | Status |
| --- | --- | --- |
| `cold-findings` | `SITE_FINDINGS_ROUTE_PATH` -> `SiteFindingsFrame` (no cold props) | mounted, but it renders the mini-grid index (B7-01) |
| `cold` | `SITE_DETAIL_ROUTE_PATH` | mounted |
| `cold-evidence` | `SITE_EVIDENCE_ROUTE_PATH` | mounted |
| `cold-evidence-analysis` | `SITE_EVIDENCE_ROUTE_PATH` `?view=analysis` | mounted |
| `cold-financials` | `SITE_FINANCIALS_ROUTE_PATH` | mounted |
| `cold-assumptions` | `SITE_FINANCIAL_ASSUMPTIONS_ROUTE_PATH` | mounted |

**Spec route-table error:** the spec names W2-03 as the owner of `cold-findings`. However, `W2-owner-walkthrough-index.md:112` records it as not built in W2, `post-W2-sequence.md:18` reassigned it to W5-02, and `W5-02-build-spec.md` never builds it. The cold Findings API exists (`cold_assessment_api.py:129`, `GET /api/sites/{code}/cold/findings`) but no UI consumes it as an index.

## Mandatory carried UI-pass checks

| Item | Result on batch-07 screens |
| --- | --- |
| `.prose` / panel sentences 14 px vs mock 12 px | Seen on the cold Overview (7 paragraphs), the Analysis "How a claim limit is set" panel, and the Financials "Not included" bullets (which drive 1.87x at 390). Cite B1-07/B2-03. |
| Tall dark header at 390 on short pages | cold-evidence-analysis no-selection (136 px) and refused (241 px); cold-assumptions refused (231 px). Every other 390 pair is 92 px. Cite B1-02/B2-04. |
| `1 incidents` plural | Not applicable. |
| Raw `c1 · EV_CONNECTOR` | Not applicable. The nearest analogues are `REC {UUID}` and `degC` (B1-53, B7-08). |
| One generic window error | Analogue: the refused cold reads repeat "The selected window is not a valid UTC window of at most 31 days." for a reversed window (B7-11). |
| 390 Window control (R88/R112) | There is no window control at all: selection is by URL only (B7-02). R88 is the nearest ruling. |

## Existing D3 rows R22/R23/R24/R37/R38/R60

**R38** (`cold-evidence-analysis`, exact record links): **verified closed**. Every record shows `REC {UUID} · Record page unavailable` with no anchor. R23/R24 (site-local time) give the precedent cited for the UTC lines (B2-21/B3-04). R22/R37/R60 do not touch these screens.

## Earlier W2 structural findings (W2-F), rechecked at this SHA

H1, M3, M5, M6, M7 and M10 are all still closed on these screens (details in B7-12). No W2-F finding reopened.

## Layout checks

- App page horizontal overflow is 0 on all 60 pairs. No clipped text, no console errors, no crashes.
- 390: the Site tab row is a horizontal scroller (521 px in 358 px). The Evidence and Analysis tables scroll inside their panels (820 and 970 px in 318 px) and stay readable.
- Panel count, titles and order equal the mock on all 60 pairs. Refused states keep every panel with gap copy, and keep the strip and tiles where the mock has them.
- Panels over 1.3x the mock:

| Screen | Panel | Ratio | Where |
| --- | --- | --- | --- |
| cold | Bounded money consequence | 1.52 | 390 stocked and no-window |
| cold-evidence | What we can conclude now | 1.32-1.36 | 390 |
| cold-evidence-analysis | Accepted records behind the conclusions | 1.47 / 1.31 | 1440 / 390 |
| cold-financials | Not included | 1.87 | 390 |
| cold-findings | Findings at this site | 1.31-1.35 | 390 (wrong content, B7-01) |

  Each one's measured reason is in its difference entry, and each needs a reviewed ruling.

## Differences (proposals)

| ID | Screens | Summary | Proposed disposition |
| --- | --- | --- | --- |
| B7-X1 | all | Cross-cutting citations: B1-01, B1-04, B1-07, B1-02, B2-21/B3-04, B1-53, B3-13/B3-15 analogues. B4-03/B4-04/B5-01/B4-19 do not recur. | cite existing IDs |
| **B7-01 (High)** | cold-findings | Shows the mini-grid dispatch index with "assessments are not released" / "no Performance comparison report" and 0 rows. The cold Findings API returns the current selected Findings. | (c) D3, W2 cold fix slice; correct the spec owner column |
| B7-02 | cold, evidence, analysis, financials, assumptions | No window control at all (URL only); refused states can't be corrected on the page | extend R88 (D1) or the topbar fix |
| B7-03 | cold | Cards have no "View detail" link; the label is the link. Cooling is unlinked although the Cooling page is built, and Maintenance is hard-coded "Not recorded · Work record not available" although cold Work is built. | (c) D3 (R40 expiry not applied to the Overview cards) |
| B7-04 | cold | Timeline labels read "role · Observed" in all-blue tones, not the event and outcome ("Generator · Observed" beside a failed start). "Steps below" sits under the steps. | (c) D3 candidate if the outcome is on the wire; copy D3 Low |
| B7-05 | cold | No "Single line diagram" link on the chamber temperature panel (EV got one in W2-F M8). Repeated "Not observed: transfer to backup." sub-text. No Action in Next step. | D3 Low ×2; D1 for this producer state |
| B7-06 | cold | Strip narrative missing; money panel 1.52x at 390 from the basis line | D1; height ruling |
| B7-07 | cold-evidence | "Configuration at window end" instead of "Portfolio evidence". Generic next-step links where Cooling is now built. Contact always "Unknown". Normal case shows "Next evidence not identified" while a required basis is stated. | D3 Low / D3 / D1+D2 / D3 Low |
| B7-08 | cold-evidence-analysis | R38 closed. Received column is time-only on another date. 3-line UUID cells. 1.47x. | D3 Low; height ruling |
| B7-09 | cold-financials | Close match. F-codes missing (extend R65). "Not included" 1.87x at 390. Label and repeated basis. | (a) R65; ruling / D2 |
| B7-10 | cold-assumptions | Close match. Window line, and a refusal on a site-scoped read. "in W2" subtitle. | D2/D3 Low; B1-53 |
| B7-11 | refused states | One generic invalid-window sentence repeated for a reversed window | D3 Low, carried domainActionClient item |
| B7-12 | all | W2-F re-check: no reopened finding | informational |

## Blockers

None. Pending/historical states are not producible by this producer (W2-F also covered them in jsdom only), so they were not captured.
