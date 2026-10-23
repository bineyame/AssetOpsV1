# W6-01d phase handoff (C4 request History)

Branch `task/W6-01d-request-history`, cut from main `c8978edf` (includes W6-01a). No code was written.

## Pre-flight

The builder dry-read these against the base it will build on:
- the C4 card, §2 `history` row, F3/F4/F5 (`wr-history`), A2Q3/A2Q6, X2/X3/X4/X6/X7/X9, CL3-1/CL3-7, R6/R7, the retrospective's R8 correction, the B1–B3 pre-flight rulings and Q2, and the C1–C3 pre-flight rulings, all in `.agent/W6-01-build-spec.md`;
- the built W6-01b code on `task/W6-01b-maintenance` (`6718657b`);
- the W6-01c plan on `task/W6-01c-request-overview` (`21720fa4`). Its pre-flight list is there, and C2/C3 code is not built yet;
- the mock: `frontend/mockups/v69/index.html:966-971` (`wrHeader`, `WR_TABS`, `wrHistory`), `:1090-1124` (`tabRow`, `breadcrumbs`), and the `wr-history` manifest entry;
- the guards: `tools/checks/navigation-truthfulness.ps1:736-830`, `missing-claim-scan.mjs` PATTERNS, `site-substrate.ps1:33-45`, `frontend/src/test/panelStructure.ts`.

Mock `wr-history` is `wrHeader()` (the five `mheader` rows) followed by `panel('History', table(['Time','Event','By'], 5 rows))`. It has no panel sub-line, no notice and no pager. Its rows are: `6 Oct 19:20 | Raised from INC-203 | Night operator`; `6 Oct 19:35 | Assigned to maintenance lead | Operations manager`; `6 Oct 21:40 | Site visit started | Technician`; `6 Oct 22:55 | Marked completed · witness test outstanding | Technician`; `7 Oct | Verification pending | —`.

Blocking items are marked **(blocking)**.

### Base and files

- **P-C4-1 (blocking): C4 depends on unbuilt C2/C3 shapes.**
  - *Card:* Lane B owns `workRequestShared.tsx`. C2 "owns `globalWorkClient.ts` detail types for the entire C1 wire". `globalWorkClient.ts` is not on the C4 list.
  - *Reference:* only `task/W6-01c-request-overview` exists, and it holds the plan with no C2/C3 code.
  - *Why open:* C4 needs these from C2:
    - the detail read hook or state machine;
    - the no-fetch query validation;
    - the `mheader`;
    - the breadcrumb;
    - the `Open site` action;
    - the date bar;
    - the detail refusal copy;
    - the tab row.

    If C2 leaves any of these in `WorkRequestOverview.tsx` instead of `workRequestShared.tsx`, C4 must edit or move code in `WorkRequestOverview.tsx` (and possibly `WorkRequestRecord.tsx`), and neither file is listed. The same applies if `GlobalWorkDetailResult` lacks the typed `events[].payload` variants or `history.revisions`.
  - *Needed ruling:* require C2 to export these parts from `workRequestShared.tsx` and the full types from `globalWorkClient.ts`, or add those files to C4.

- **P-C4-2 (blocking): promoting the History tab breaks C2 and C3 tests that are not on the C4 list.**
  - *Card:* "promote History tab and remove its `$expectedTabs` entry". The C3 ruling says C3 "retain[s] its Verification/History unavailable assertions" in `workRequestOverview.test.tsx`.
  - *Reference:* the C3 ruling (`W6-01-build-spec.md:656`). `workRequestRecord.test.tsx` will presumably assert History unavailable too.
  - *Why open:* when the History tab goes live on every request page, those assertions fail. This is the same gap as P-C3-5.
  - *Needed ruling:* add `frontend/src/work/__tests__/workRequestOverview.test.tsx` and `frontend/src/work/__tests__/workRequestRecord.test.tsx` to C4 Lane B, with the replacement assertion. The likely assertion is a live `/history?site_id=…[&known_at=…]` href while Verification stays unavailable.

- **P-C4-3 (blocking): the B2 `Pager` cannot be reused, and `globalWorkParts.tsx` is import-only.**
  - *Card:* X7 says History pages client-side with "Previous/Next in component state, and the same `Showing` line". P-X-1 makes the parts import-only.
  - *Reference:* `globalWorkParts.tsx:170-212` on the B2 branch. `Pager` takes `body: GlobalWorkBodyBase` (it uses `total_count`, `rows`, `next_cursor`) plus `trail`/`cursor`/`onPage(cursor, trail)`, and computes `a` from `trail.length`.
  - *Why open:* a client-side pager needs its own component. The rulings must name:
    - its file (`WorkRequestHistory.tsx` or `workRequestShared.tsx`);
    - its accessible name. B2 uses `Incident pages`/`Maintenance pages`; the proposal is `History pages`;
    - whether it keeps the `data-global-work-pager`/`-showing`/`-previous`/`-next` hooks and `link-button` buttons;
    - the `Showing` formula: `a = pageIndex×5+1`, `b = a+rows−1`, `N` = the merged row count;
    - whether Previous is hidden on page 1 and Next on the last page, without a disabled state (as in A2Q10).
- **P-C4-4: pager placement against the panel guards.**
  - *Card:* R6 puts the list `Showing` line in `.site-date-bar`. C2's date bar holds `As known at`/`Historical as of` and `Reload`.
  - *Reference:* `panelStructure.ts:11,18`. `strayBetweenPanels` and `strayOutsidePanels` reject any block outside the chrome or the panels. The mock has no pager.
  - *Why open:* the pager must sit either inside the `History` panel body (below the table) or in the date bar. Choose one. Also state that `Reload` and page navigation reset the client page to 1, because the page index is not in the URL or in history state.

### Labels, rows and literals

- **P-C4-5 (blocking): does `history.revisions` revision 1 become a row?**
  - *Card:* §2 lists `revision successor Correction`. §1 says `history.revisions` holds "selected correction rows", but the literal §1 detail example includes revision 1 (`supersedes_revision_id:null`).
  - *Reference:* `W6-01-build-spec.md:41,46,90`.
  - *Why open:* revision 1 is written in the same command as CREATED. If it is a row, it duplicates `Created`, and the tie with CREATED is broken only by a random UUID. Rule one of these:
    - render only `supersedes_revision_id != null` as `Correction`;
    - give revision 1 its own label.

    This also fixes the row count: the `detail` first request has 6 rows without revision 1 and 7 with it, and both need page 2.
- **P-C4-6 (blocking): Event-cell content beyond the bare label. This is an unlabelled mock departure.**
  - *Card:* §2 gives labels only (`ASSIGN: Assigned`, …).
  - *Reference:* the mock Event cells carry payload facts: `Assigned to maintenance lead`, `Raised from INC-203`, `Marked completed · witness test outstanding`. Stored payloads exist (`model.py:313-322`): `ASSIGN.assignee` (up to 128), `COMMENT.text` (up to 2000), `CLOSE/REOPEN/CANCEL.reason` (up to 500), and `COMPLETE.maintenance_record_id`. The revision row has `title` and `reason` (500 in `stress`).
  - *Why open:* rule one of these:
    - restore to the mock with literal frames, for example `Assigned to {assignee}`, `Commented: {text}`, `Reopened: {reason}`, `Cancelled: {reason}`, `Completed`, plus the record reference or link, and `Correction: {reason}` with or without the new title;
    - label the bare-label choice `MOCK DEVIATION`.

    Long payloads need the §2 clamp and a named `<details>` summary. §2 offers `Full … event … text`, so confirm `Full event text`. X2 already expects the 500-character reason to be visible in the `Correction` row ("reason stress is the C4 `Correction` row"), so a bare label would contradict X2.
- **P-C4-7: the CREATED row and its source. This is an unlabelled mock departure.**
  - *Reference:* the mock says `Raised from INC-203` (CREATED with its source incident). The card says `CREATED: Created`. C1 provides `links.source_incident` and the outer Finding links.
  - *Why open:* either restore a `Created from {Incident code}` form using `links.source_incident.label`, or label the plain `Created` as `MOCK DEVIATION`.
- **P-C4-8: the mock `Verification pending | —` row and the `Site visit started` row.**
  - *Reference:* the mock rows 3 and 5. No W4 event or verification state supplies them (`OPEN_VERIFICATION` is reserved and never written, and there is no outcome evaluator). Maintenance records (`work_detail.records`) are excluded from C4 by X7.
  - *Why open:* dropping these rows is a departure from the mock with no label. Rule one of these:
    - label the dropped rows `MOCK DEVIATION`;
    - show an honest gap inside the panel;
    - include `work_detail.records` heads as `Maintenance record` rows.
- **P-C4-9: the Time format and its precision. This is an unlabelled mock departure.**
  - *Card:* "Time is recorded UTC", using the §2 format `22 Oct 2026, 12:00 UTC` (`globalWorkUtc`, minute precision, `globalWorkClient.ts:308-322`).
  - *Reference:* the mock `6 Oct 19:20` has no year and no zone.
  - *Why open:*
    - The format change from the mock is unlabelled.
    - Every `detail` and `stress` command is written one second apart inside 11:59–12:00, so all rows show the same minute and the order looks arbitrary.
    - Rule whether History shows seconds, for example `20 Oct 2026, 11:59:03 UTC`. If it does, this needs a new formatter, because the `globalWorkClient.ts` formatter is C2/B2-owned.
    - The occurrence disclosure uses the same format.
- **P-C4-10: the By column. This is an unlabelled mock departure.**
  - *Reference:* the mock shows role names (`Night operator`, `Technician`, `—`). The card says "By = stored actor ID" (`service:w401-fixture`).
  - *Why open:* confirm `actor_id` only, with `actor_kind` not shown, and label it `MOCK DEVIATION`. Confirm the 128-character wrap rule applies.
- **P-C4-11: unknown and impossible event kinds.**
  - *Reference:* `model.py:111-112`. `RESERVED_EVENTS` includes `OPEN_VERIFICATION`, which has no §2 label. X9's typed `CLOSE` on a request is impossible in W4.
  - *Why open:* rule one of these:
    - a kind outside the seven makes the 200 malformed (the 503 sentence);
    - such a kind renders its raw code.

    Also confirm whether `history_labels_all_seven` goes through the C2 validator (which may reject `CLOSE` on a request) or through a typed fake client.
- **P-C4-12: where the missing-CREATED check lives.**
  - *Card:* §2 says "Missing CREATED => 503". The C1 ruling puts the 503 in `global_detail.py`.
  - *Why open:* is there also a client-side check, where a 200 with no CREATED event is malformed and gets the 503 sentence? That check lives in the C2-owned validator, or in C4 if it is local. Without one, `test` "refused" covers only the server path.
- **P-C4-13: the occurrence disclosure's cell and row.**
  - *Card:* `<details><summary>Occurrence time</summary>Occurred {formatted occurred_at}</details>`.
  - *Why open:*
    - Which column holds it? Time is assumed.
    - Is it on every row, including `Correction` (using `history.revisions[].occurred_at`)?
    - Does it collapse within the panel cap?
    - This element is not in the mock, so confirm it is covered as a new element (provisional cap 180/300) and is not a `MOCK DEVIATION`.
- **P-C4-14: header, breadcrumb, h1 and loading/refusal literals on History.**
  - *Card:* the C2 ruling gives the literals for Overview only: `Maintenance › {code} › Overview · site: {name}`, `Maintenance › Work request › Overview`, h1 `Work request`, and the subtitles.
  - *Reference:* mock `breadcrumbs(s)` gives `Maintenance › WR-019 › History · site: GreenHarvest` (`index.html:1121`).
  - *Why open:* confirm that History swaps `Overview` for `History` in both forms and otherwise reuses the C2 h1, subtitle, `mheader`, `Open site`, date bar, refusal copy and no-fetch rules unchanged.
- **P-C4-15: DataTable column widths at 390px.**
  - *Reference:* B2 uses literal `MIN_WIDTHS = [220,210,160,120,170,150]` (`GlobalMaintenance.tsx:174`). C4 has no width map.
  - *Why open:* give Time/Event/By min-widths and a page modifier (for example `.global-work--history`) for the 600/690 cap. P-X-1 for B2/B3 added page modifiers to `globalWork.css`.
- **P-C4-16: sort key implementation.**
  - *Reference:* `history.revisions` and `work_detail.events` use six-digit `Z` strings. `Date.parse` drops microseconds.
  - *Why open:* confirm that the merged sort compares the `recorded_at` strings as given, then the lowercase `id`, and does not use `Date`. This is a confirmation only.

### Ledger and registry

- **P-C4-17: the final `wr-overview` interaction literal after C4.**
  - *Card:* P-X-2 says "C4 replaces the History clause with the same rule".
  - *Why open:* the interim C2 sentence (`Maintenance record and History are shown as unavailable until their pages mount.`) after C3's clause replacement has no literal final form. Give the exact post-C4 string. Also say whether the `wr-record` row's interaction (C3: `Linked REC codes are shown; …`) changes, so that the ledger checker gate in P-X-2 is concrete.
- **P-C4-18: low-risk confirmations.**
  - The `wr-history:1` reason becomes `W6-01d selected history is built and awaits independent review.` (registry line 461).
  - The `I-w601d-history-ui` node stays `open`.
  - The `wr-history` panel contract stays `Deferred` (`v69-panel-contracts.json:3791`).
  - `expectV69Panels('wr-history')` expects exactly `History` (`v69-rendered-panels.json:1208`), so the pager and any notice must stay inside it or in the chrome (see P-C4-4).

### Producers, clocks and captures

- **P-C4-19 (blocking): the historical capture cutoff and producer.**
  - *Card:* X3 says C2–C4 historical uses `known_at=2026-10-21T12:00:00Z`. P-B1-1 seeds `detail`/`stress` at `--clock 2026-10-20T12:00:00Z`. The P-C2-11 ruling uses `2026-10-20T12:00:01Z` with a C1 `detail-history` fixture write at `12:00:02Z`.
  - *Reference:* `seed_detail` writes request 1 from 11:59:00 to 11:59:06 (`w601_seed.py:360-372`).
  - *Why open:* X3's cutoff postdates every `detail` write, so it would show nothing historical. Give C4's exact fixture and cutoff. Options:
    - reuse C1 `detail-history` at `12:00:01Z`;
    - an in-sequence cutoff such as `2026-10-20T11:59:04Z`, which hides REOPEN and the Correction.

    Also state which rows the manifest must show as differing.
- **P-C4-20: the capture set and states.**
  - *Card:* "captures at both widths from B1 `detail` and `stress` (reason row)"; the tests cover "historical/refused".
  - *Why open:* list the required 1440/390 captures. Candidates:
    - `detail` page 1;
    - `detail` page 2;
    - the CANCEL request;
    - the `stress` Correction row, collapsed and expanded;
    - the occurrence disclosure expanded;
    - historical;
    - which refusals. Candidates are the C2 test-only 403 composition (P-C2-11), the no-fetch 404, and a 503 producer. A missing-CREATED 503 exists only as C1's rollback-scoped SQL fixture, so which 503 producer is captured?

    Also confirm the capture write clock (`2026-10-20T12:00:00Z`, per P-B1-1, rather than A2Q3's `2026-10-21`), and the R8 replacement manifest sentence.
- **P-C4-21: the `stress` history composition.**
  - *Reference:* the stress request writes CREATED, ASSIGN (128-character owner), a record, and a revision with a 500-character reason (`w601_seed.py:289-293`). It writes no COMPLETE.
  - *Why open:* confirm that the expected rendered rows are `Created`, `Assigned`, `Correction` (3 rows, no pager), and that the 128-character assignee shows only if P-C4-6 restores payload text.

### Guards (checked, no conflict expected)

- **P-C4-22 (confirmation): the `$expectedTabs` literal.**
  - *Reference:* `navigation-truthfulness.ps1:755` currently ends with `"Analysis"` (B3 removed Preventive).
  - *Why open:* C2 appends `"Maintenance record","Verification","History"`, and C3 removes the first. C4 removes `"History"` and adds a dated comment line. This holds only if C2 renders `History` from exactly one literal `<UnavailableTab label="History" />`. Confirm.
  - No `missing-claim-scan.mjs`, `site-substrate.ps1` or `shell-overflow.ps1` conflict was found for the card literals, provided that tables use `DataTable`, no `<svg>` is used, and no `Site…Row` names appear.

Counts: 22 items. Blocking: P-C4-1, 2, 3, 5, 6, 19. The builder starts code only after the rulings merge, and after W6-01b and W6-01c have merged to main and this branch has been updated from main.

## Run C4 (2026-10-23, builder)

Base `d798029e`. Commits `f756d86e` (Lane A), `f7122095` (Lane B), `09536c95` (By-cell layout), then the evidence/packet commit. Packet `.agent/W6-01d-review-packet.md`; evidence `.agent/W6-01-evidence/C4/`.

- Built to the C4 pre-flight rulings: the History page in the shared C2 frame; revision 1 is omitted; rows are sorted by the exact recorded_at string, then the lowercase ID; there is a five-row in-panel `History pages` pager; the two in-table gaps sit on the last page; Time uses UTC seconds with an `Occurrence time` disclosure; By shows `Name not recorded` with a `Stored actor` disclosure; `Raised from {INC}` uses its href; an unknown kind is an authored row with `meaning not established`; a missing CREATED event or a missing known payload fails closed as the 503 sentence (`WorkRequestFrame` `accept`).
- Tests: history 17 and Overview+Record 38 passed. The wide frontend set (`src/work src/shell src/sites src/estate src/ui`) gave 2645 passed and 1 failed, the load-sensitive S4-04 date test in `s404SiteFindingIndex.test.tsx`, which passes alone. `tsc` and `vite build` exit 0. Backend `test_w601c_request_detail.py` gave 15 passed. check-all 11/11.
- Guard proofs: removing `accept` fails the typed missing-CREATED test; re-adding `"History"` to `$expectedTabs` fails navigation-truthfulness. Both were reverted.
- Captures: 11 states at 1440/390 plus the mock pair. Collapsed History panel max 467/490 (cap 600/690); pager 29; disclosures 16; the 390 table is 750 px and scrolls within 318 px; document width equals the viewport. Historical `11:59:04Z`: revision 1, COMPLETED, 4 rows, against current revision 2, IN_PROGRESS, 6 rows. The DBs `assetops_w601_c4{,linked,stress}_test` and `assetops_w601d_c4f_test` were dropped. Vite was stopped by PID 17732. uvicorn and Chrome were stopped by the driver.
- Open for Architect: there is no register row for the two gap rows. ACTIVE_CONTEXT, CODE_STATE and task status were left for closeout, because they are not on the card.
