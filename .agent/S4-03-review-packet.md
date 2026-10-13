# S4-03 review packet - Finding Evidence and History

**Task:** `tasks/S4-03-finding-evidence-history.md`.
**Branch:** `task/S4-03-finding-evidence-history`.
**Status:** `in_review`, USER_REVIEW_REQUIRED: true.
**Phases 1 and 2:** reviewed ACCEPT. See `.agent/S4-03-phase1-review.md`, `-phase1-fix-rereview.md`, `-phase2-review.md` and `-phase2-fix-rereview.md`.
**This packet covers:** phase 3 (`I-finding-history-ui`), the phase-2 leftovers N1-N4, browser evidence, and the closeout proposals.
**Phase-3 diff:** `26b5e7a..HEAD`.
**Built-state history:** `.agent/S4-03-handoff.md`.

## Outcome delivered

- **History view.** History is a child view of the canonical Finding root, at `/sites/{code}/findings/{id}/history?revision_id=` (`frontend/src/sites/SiteFindingHistory.tsx`). It works as follows:
  - It follows `next_after_revision_no`, 100 per request, until the read reports no next page. It checks the loaded count against `page.total`. It says "incomplete" if a later page fails, and says a new version appeared if the total or latest changes between pages.
  - It lists every stored version oldest first. Each version shows recorded time, transition, state, period, the three minute amounts, whether the amount changed, cited count, source/received/accepted/analysis-finished times, model, and the primary and prior assessment IDs.
  - It marks **Selected** and **Latest** separately (`data-history-selected` / `-latest`, `aria-current`).
  - Each row links to its own History selection, to that exact version of the Finding, and to its Evidence.
- **History states:**
  - An omitted version reads "Latest version at the time of reading", with a pin link.
  - An earlier selection leads with its non-current notice.
  - A closed source leads with "Record only".
  - A non-SUPPORTED latest lifecycle leads in plain words.
  - A single version reads "No earlier versions".
  - BASIS_REFRESHED groups are noted, and each version stays selectable.
  - Late acceptance is noted on the version whose latest cited `accepted_at` is later than the previous version's `recorded_at` (stored times only).
  - Merge, split and recurrence relations link to the other Finding's History.
  - 401/403/404/409/503 each have plain words. An unknown version keeps the address and is never replaced.
- **Accepted rows (phase-1 F1 carry).** Each History row shows "N cited; R of N found as accepted records", with "Check their record trail on the Evidence page". There is no lineage verdict or badge.
- **Navigation.**
  - The Finding sections now read Finding · Evidence · History, and each keeps `revision_id`.
  - Evidence links "See version N in the Finding's history".
  - The S4-01 page's "Where to look next" links History.
- **Placeholders retired.** The backend `UNAVAILABLE.history_tab` and the S4-01 history "Not yet available" text are gone. The baseline entry was removed and the total went from 16 to 15.
- **N1.** The read returns `provenance.cited_evidence_by_role` (`[{role, count, source_ids}]` over the whole cited set, resolved rows only). Evidence's "Cited records by measurement" renders that instead of a page recount.
- **N2.** The Evidence UNCONFIRMED sentence now says "...stay available in this Finding's history".
- **N3.** When the window crosses midnight, the legacy tab says "these days" and "(recorded for an overlapping day)".
- **N4.** `prepare` refuses an existing non-empty `--work` folder that has no marker, before writing anything.

## Files materially changed (phase 3)

- **Frontend.**
  - `frontend/src/sites/SiteFindingHistory.tsx` (new).
  - `findingClient.ts`: `HistoryRevision`, `FindingHistoryBody`, `getFindingHistory`.
  - `SiteFindingEvidence.tsx`: N1, N2, N3 and the History link.
  - `SiteFinding.tsx`: the History link.
  - `shell/SiteAnalyticsFrames.tsx` and `shell/operatorSiteRoutes.ts`: the `history` child view.
  - `test/settled.ts`: the loading sentence.
- **Backend.** `backend/assetops_backend/analytics/finding_read.py`: `cited_evidence_by_role`; `history_tab` removed.
- **Tests.**
  - `frontend/src/sites/__tests__/siteFindingHistory.test.tsx` (new, 17 tests).
  - `siteFindingEvidence.test.tsx` (N1-N3).
  - `backend/tests/test_s4_finding_evidence_history_postgres.py`: whole-set by-role compared with stored rows, and the broken-row sum.
- **Tools.**
  - `tools/s4-finding-evidence.mjs`: history suite, Q3 proof, closed History, and the N1 claim.
  - `tools/s4_finding_walkthrough.py`: N4, and History links in `links`.
  - `tools/checks/missing-claim-baseline.json`: shrink only.

## Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| 1 Evidence (phases 1-2) | Met. Rerun on the changed view at 1440/390. | Browser: F01-gateway 102 cited / 263 input. By-measurement roles equal the API whole set and sum to 102 (`battery_soc` 17, `feeder_demand` 51, `pcs_discharge_capability` 17, `pv_available_power` 17). Record and page-2 checks pass. |
| 2 History | Met for the stored path. | History lists every version across pages: vitest 205 versions over 3 requests; browser F04 equals the API walked in 2-row pages. Selected and latest are marked separately. Old → new → Evidence → old keeps the exact IDs through keyboard selection, the section link, Back ×2, reload, Forward ×2, and Evidence → History. This passed at both widths. F04 append: v1 cites 42, v2/v3 cite 78; the late note appears only on v2, equal to the stored-time rule. F05: 3 versions, latest NO_LONGER_SUPPORTED leads. F06 links the joined Finding. Mock ActionEvent and recommendation content are omitted (G-04 list). |
| 3 States | Met. | Vitest covers loading/settled, 401, 403, 404 (URL kept), 409 closed, 503, record-only, no-earlier, incomplete, non-supported lead and late append. Browser covers 404, the 409 unpinned read and the pinned Record-only read for History and Evidence (8/8), no-earlier and F05. |
| 4 Missing-claim | Met. | No new absent-capability copy. One baselined legacy string was removed (16 to 15). Runtime states are data states. |
| Q3 (Architect) | Proved. | Vitest Q3 test, and browser claims "Q3 ..." at both widths. An omitted ID is labelled latest at read time, and on reload after an append it moves (vitest). |

## Checks run (actual)

- **Frontend.** `npx vitest run`: 61 files, 1439 passed. `siteFindingHistory` 17/17. `siteFindingEvidence` 29/29. `tsc --noEmit`: 0. `npm run build`: exit 0 (chunk-size warning only).
- **Backend.** On private `assetops_s403p3_test`, `test_s4_finding_evidence_history_postgres.py`, `_api.py` and `test_s4_finding_api.py` gave 26 passed. That run was before the one-line `history_tab` removal. After the removal, `_api.py` + `test_s4_finding_api.py` gave 23 passed. Full pytest was not run (instructed).
- **Browser.** `tools/s4-finding-evidence.mjs`, suite `all`: **110/110**. Suite `closed`: **8/8**. Run on private DB `assetops_s403p3_walk`, API 8898, Vite 5398, CDP 9398. Screenshots are in `%TEMP%\s403p3-evidence\`. Overflow: History 1425/1425 and 390/390 with 141 measured elements; Evidence the same as phase 2. Everything was dropped and stopped by PID afterwards.
- **Mutation proofs.** Each was made on committed code and reverted with `git checkout --`:
  - No paging: 1 fail.
  - Selected mark using is_latest: 1 fail.
  - Late note off: 1 fail.
  - Section links dropping `revision_id`: 2 fails, including Q3.
  - N1 UI page recount: 1 fail.
  - N1 backend aggregate over a 7-row slice: Postgres `{'feeder_demand': 4} != {'feeder_demand': 33}`.
  - N4: `prepare` on a foreign non-empty folder is refused and the folder is untouched.
- **`tools/check-all.ps1`:** all 9 guards passed (missing-claim scan: 3 tagged, 15 baselined; ledger valid).
- **Layout evidence (`tools/layout-evidence.mjs`): not run.** The same precondition as phase 2 applies: it targets MG-001 and Lab runs and never visits the Finding child views. The S4 script's overflow measurements above are the layout evidence for these paths.

## Known deviations

- **Legacy tab not captured in the browser.** KOBO-001 has no readable assessment-keyed page on this stack (candidates `[]`), so the day-level list is covered by vitest only.
- **History layout differs from the mock.** The mock is a compact 3-column table; the app renders one block per version. This is a visual choice for the owner.
- **Times are shown to the minute.** Late notes use exact instants, so on the fixture v1 recorded 15:39 and v2's last acceptance 15:39 look equal, while the note on v2 is correct by seconds.
- **History loads all pages at once (Q6).** It has no page controls.

## Residual risk

- In the fixture, source times (13 Oct) are later than receipt and acceptance times (12 Oct). This is how the fixture was produced, and History shows it as recorded.
- The `?raw` parity test needs `backend/` (carried). Refusal panels print the backend `message` (carried from S4-01). Phase-1 C1 `ASSESSMENT_CITATION` is carried.

## Closeout proposals (not applied)

**Registry: "knowledge cutoff" rewording (C1).** Per `D-2026-10-11-s3-phase-2-selection-and-read`:

| Node | Current text | Proposed text |
| --- | --- | --- |
| `I-S4-03.acceptance_target` | "... accepted-source lineage and knowledge cutoff after reload." | "... accepted-source lineage and the selected revision's stored basis IDs after reload; no arbitrary knowledge_at replay." |
| `I-finding-history-read.acceptance_target` | "Read immutable revisions at knowledge cutoff, ..." | "Read every immutable stored revision in revision order with exhaustive paging, including late-evidence append and no-history state; no knowledge_at replay." |
| `finding-history:1#a.boundary` | "Select exact finding_revision_id and knowledge cutoff; ..." | "Select exact finding_revision_id; its stored basis IDs are the historical anchor; late accepted evidence appends a revision and leaves earlier selection available." |

`finding-history:1#a` is a reviewed mapping, so its closeout reviewer must note the boundary change.

**After the independent review and the owner checkpoint:**

- Set `I-finding-evidence-read`, `I-finding-history-read`, `I-finding-evidence-ui`, `I-finding-history-ui` and `I-S4-03` to delivered. Use as evidence this packet, the reviews and commits `6ac76f3`, `c4ea8f4`, `3dc9806` and `65cc5c7`. Anchors:
  - `finding_api.py:142-209`
  - `finding_read.py` `evidence()` / `history()`
  - `SiteFindingEvidence.tsx`
  - `SiteFindingHistory.tsx`
- Move `finding-evidence:1#a`, `finding-evidence:2#a` and `finding-history:1#a` to proven only with the reviewer's evidence. Panels stay partial: Coverage/Use gaps; Alternatives/Recommendation/ActionEvent are G-04.

**Ledger (`v69-screen-ledger.json`):**

- `finding-history`:
  - `coverage`: deferred → bounded.
  - `task`: `S4-03`.
  - `follow_on`: null.
  - `supported_claim`: "Every stored FindingRevision in order with exact selection, late-append note and links to that version's Finding and Evidence; no workflow or knowledge_at replay."
  - `interaction`: "Select a version (address keeps revision_id), open it or its Evidence; reload/back keep it."
  - `unknown_or_empty`: "One version reads 'No earlier versions'; refusals and closed source in plain words."
  - Keep the G-04 gap for ActionEvent.
- `finding-evidence`: the same shape, with gap IDs `G-finding-evidence-coverage` / `-use` kept.

**G-04: mock content omitted** (no catalogue entry, no copy):

- `finding-history:1` row "Recommendation prepared / No automatic controller change" (ActionEvent).
- `finding-history:1` row "Delayed SOC evidence accepted" as a separate event row. It is represented as a per-version late note (Q5).
- Mock tabs "Alternatives" and "Recommendation" (index.html:1106).
- The `finding-evidence:1` illustrative device rows (GEN-001, BMS-001, PCS-001, INV-001/MTR-001), listed in phase 2.

## User-review focus

- Is the History block-per-version presentation acceptable against the mock's table at 1440/390?
- Is the late-acceptance note wording clear?
- Check the Q3 navigation yourself in `.agent/S4-03-owner-walkthrough.md`.

New questions for the Architect are in `.agent/S4-03-questions-2.md`: Q4 (carry R1, M4 shape), Q5 and Q6.
