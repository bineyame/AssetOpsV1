# W6-01d review — C4 request History

Reviewer: fresh independent Claude reviewer, 2026-10-23. Branch `task/W6-01d-request-history`, head `241960bb`,
diff `git diff main...task/W6-01d-request-history -- backend frontend tools` (merge base `2503a34d`). Read-only
review: no code edited, no browser run.

## Verdict

**REVISE.** The code matches the C4 pre-flight rulings closely and every check I ran passes. One High (unregistered
mock departures, a register/spec fix plus a code label) and one Medium (the current History tab is off-screen at
390) block the merge. Both fixes are small.

## Findings

### H1 — The two gap rows and the completion wording are mock departures with no category code or register row (High, acceptance gap under the departure rule)

- Where: `frontend/src/work/WorkRequestHistory.tsx:37-38` (`HISTORY_GAPS`), `:116-121` (COMPLETE text), header
  comment `:1-18`; `.agent/mock-departure-register.md` (no row); spec C4 pre-flight "Mock mapping" second paragraph.
- What: the mock `wr-history` table (`index.html:971`) has `6 Oct 21:40 | Site visit started | Technician` as row 3
  and `7 Oct | Verification pending | —` as row 5. The build shows `— | Site visit start not recorded | —` and
  `— | Verification pending · no outcome assessment recorded | —`, moved after the last authored row on the last
  page only. The mock's `Marked completed · witness test outstanding` becomes
  `Completed · outcome not established · maintenance record {id}`. The spec rules all of these, but it gives no
  `MOCK DEVIATION` code. The register covers only R19 (Time, D2) and R39 (named people, D4) for `wr-history`. The
  code labels only R19 and R39. The packet acknowledges the gap rows have no register row.
- Why: `.ai/ROLE_CONFIG.md` "Departure categories and register" says every departure carries a code and a register
  row, and an uncategorised one is High. The walkthrough index groups departures from the register, so these would
  not reach the owner.
- Fix (Architect, then builder):
  1. Add register row `R41 | W6-01 C4 | wr-history | Site visit started (row 3) and Verification pending (row 5) | Two in-table gap rows "Site visit start not recorded" and "Verification pending · no outcome assessment recorded" after the last authored row, last page only | D1 | W4 has no site-visit event and no work-outcome assessment | Future site-visit event and work-outcome evaluator | planned`.
  2. Add register row `R42 | W6-01 C4 | wr-history | "Marked completed · witness test outstanding" | "Completed · outcome not established · maintenance record {id}"; witness text only when authored | D4 | Completion alone cannot assert a witness test | W6-01 C4 | planned`. The Architect may instead fold this into R39.
  3. Update the register counts. Add `MOCK DEVIATION (D1, R41)` and `(D4, R42)` to the C4 spec paragraph and as two
     lines in the `WorkRequestHistory.tsx` header comment, beside R19 and R39.
  No behaviour change.

### M1 — At 390 px the current History tab is off-screen (Medium, user-visible defect against the mock)

- Where: `frontend/src/work/workRequestShared.tsx:230-240` (`WorkRequestTabs`).
- What: in `screenshots/page1-390.png`, `page2-390.png` and the other 390 captures, the tab row shows
  `Overview  Maintenance record  Verification · Not available yet`. `History` (the current tab) is scrolled out of
  view. The mock at 390 (`mock-wr-history-390.png`) shows History current and visible. C4 is the first page whose
  current tab is the fourth one, so C4's promotion causes this. The packet's residual-risk list names it.
- Why: the reader cannot see which page they are on. W1-F5b carry 10 already fixed this for other tab rows with
  `frontend/src/ui/useCurrentTabInView.ts`, which `operatorSiteTabs.tsx` and `SiteFindingEvidence.tsx` use. The
  request tab row does not use it.
- Fix: in `WorkRequestTabs`, add `const ref = useCurrentTabInView<HTMLElement>();` and `<nav ref={ref} ...>`, then
  recapture `page1-390` (or one 390 state) showing History visible. `workRequestShared.tsx` is on the C4 card.

### L1 — Manifest text is mis-decoded (Low, evidence quality; does not block)

`.agent/W6-01-evidence/C4/manifest.json` and `screenshots/app-*.json` record `—` as `â€”` and `·` as `Â·` in the
`gaps`, `breadcrumb` and `tabs` fields. The screenshots render correctly, so the error is in the capture-side
decoding of the CDP string (`capture.mjs`), not in the page. Fix it in the next capture round: decode the WebSocket
frames as UTF-8. No recapture is needed for this alone.

## Items the Architect asked about

| Item | Ruling against the spec |
| --- | --- |
| Unknown kinds render as `Event {code} · meaning not established` | **As in spec.** The final C4 pre-flight "Mock mapping" paragraph says: "If a 200 contains an unknown or reserved kind, including `OPEN_VERIFICATION`, render `Event {raw code} · meaning not established` ... it remains an authored row". Only missing or invalid identity or payload fails as 503. The code (`:104`, `historyReadable` `:91-101`) and test (`:331`, `:223-229`) match. The dispatch summary's "read failure" wording is superseded. |
| Optional `accept` prop on the shared C2 frame | **As in spec; within C4 ownership.** `workRequestShared.tsx` is on the C4 Lane B list. The spec requires "C4 adds a local presentation check for `CREATED` so a typed fake bypassing the parser fails closed". The prop is optional and additive. Overview and Record callers are unchanged, and `globalWorkClient.ts` is untouched. The rejected body maps to the existing `WORK_STORE_UNAVAILABLE` refusal, so no new copy is added. |
| Two visible gap rows with no register row | **High (H1).** The behaviour is as specified, but it is an uncategorised departure. The fix is a register/spec label, not a code change. |
| `s404SiteFindingIndex.test.tsx` failure under load | **Not slice-caused; no finding.** I reran it once alone: 37/37 passed. It imports `App`, which the slice changed by one static route import and nothing on its path. The failing case is a `waitFor` on the address after a date change, which is timing-sensitive. Treat it as a pre-existing load flake. |

## Other checks requested

- **Every changed file is on the card: yes.** The 11 files under backend/frontend/tools are: `WorkRequestHistory.tsx`,
  `workRequestShared.tsx`, `globalWork.css`, the three test files (Lane B), `App.tsx`, `operatorSiteRoutes.ts`,
  `navigation-truthfulness.ps1`, the registry JSON and `v69-screen-ledger.json` (Lane A). No backend change. No edit
  to `globalWorkClient.ts`, `globalWorkParts.tsx`, the Overview or Record pages, `missing-claim-scan.mjs` or
  `operatorRouteFrames.test.tsx`.
- **Shared shell and `GlobalWorkDetailResult` are reused: yes.** The page uses `WorkRequestFrame` for the
  breadcrumb, heading, `Open site`, tabs, date bar, mheader and refusal. It imports `GlobalWorkDetailBody`,
  `WorkCaseDetailEvent` and `isKnownWorkCaseEvent` from C2, and `Clamp` and `SCROLL_TABLE` from B2. B2's `Pager` is
  not reused.
- **Revision 1 is omitted: yes.** `historyRows` filters `supersedes_revision_id !== null` (`:142-143`). The test is at
  `:211`.
- **The 5-row pager sits inside the panel: yes.** It renders inside `Panel`, below the `DataTable` (`:276`, `:283`),
  with `aria-label="History pages"`, `link-button`, `Showing a–b of N`, and Previous/Next hidden rather than disabled.
  `page2-1440`/`page2-390` show it inside the card.
- **The historical capture at `11:59:04Z` shows revision 1: yes.** The manifest `historical` state has API revision 1,
  `revision_id b4020ad7…`, `COMPLETED`, and 4 rows (CREATED, ASSIGN, COMMENT, COMPLETE). Current has revision 2,
  `IN_PROGRESS` and 6 rows.
- **A missing CREATED event fails closed: yes.** It fails on the client through the typed fake (`historyReadable` via
  `accept`), on the client through a fetched malformed 200 (C2 parser), and on the server
  (`test_w601c_request_detail.py`, which passed in my run).
- **Time and actor-ID departures are labelled: yes.** The header carries `MOCK DEVIATION (D2, register R19)` and
  `(D4, register R39)`, and both register rows exist.
- **Lane A literals: match.** The ledger `wr-overview` and `wr-history` interactions match the spec text. The registry
  reason is exact. One `"History"` was removed from `$expectedTabs`, with a dated comment.

## Side-by-side with the v69 `wr-history` mock (1440 and 390)

Same order: breadcrumb, h1 with `Open site`, subtitle, tabs, mheader (five cells), then one `History` panel with
`TIME | EVENT | BY`. The departures are the date bar (C2, shared), the year-and-seconds Time with the occurrence
disclosure (R19), `Name not recorded` with `Stored actor` (R39), the gap rows and completion text (H1), and the
in-panel pager. Spacing and prominence match. At 390 the table scrolls inside the panel with the hint, and the
document does not overflow. The current tab is hidden (M1).

## Checks run

- `npx.cmd vitest run --minWorkers=1 --maxWorkers=2` on `workRequestHistory`, `workRequestOverview` and
  `workRequestRecord`: 3 files, 55 passed.
- `s404SiteFindingIndex.test.tsx` alone: 37 passed.
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `tools/checks/navigation-truthfulness.ps1`: exit 0.
- `check_v69_dependency_registry.cjs`: exit 0.
- `pytest backend/tests/test_w601c_request_detail.py`: 15 passed in 170.7 s, on private `assetops_w601d_rv_test`,
  which I dropped afterwards (0 remaining).
- Not verified: the full frontend suite and `vite build` (not rerun), and the browser captures and
  `layout-evidence` (no browser was run, so I relied on the screenshots and manifest).

## Shared plumbing touched

`tools/checks/navigation-truthfulness.ps1` is in the `tools/checks/*` class. Under the tiered-testing rule that
requires a full backend suite before merge. The packet records none ("dispatch rule"). The coordinator should run it
or record an explicit waiver; no backend test reads this guard. The slice also touches the shared frontend modules
`App.tsx`, `operatorSiteRoutes.ts` and `workRequestShared.tsx`. These are covered by the packet's wider vitest run
(2645 passed, 1 load flake) and my focused reruns. It does not touch `main.py`, composition, seed tools, conftest,
migrations or `globalWorkClient.ts`.

## Residual risk

- jsdom has no layout, so a unit test cannot prove the M1 fix. It needs a 390 capture.
- The spec's "browser assertion of malformed-200" is met by a jsdom test with a stubbed `fetch`, not by a real
  browser. That is a reasonable reading, but the Architect may want to confirm it.
