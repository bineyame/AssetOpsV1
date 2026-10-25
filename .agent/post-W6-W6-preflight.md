# Post-W6 W6-global-Work pre-flight

Read-only pre-flight on main `ad71329d` (worktree `AssetOpsV1-plan2`), 2026-10-25. No code, tests, captures or DB work.
Sources: W6 card and cap docket in `.agent/post-W6-audit/fix-slices.md`, classification rows B18-* / B19-*, the batch 18/19 ledgers and `differences.json`, `.agent/post-W6-R373-rulings.md` and its packet, `.agent/mock-departure-register.md` (R352-R374), the W6-01 build spec, and the current code.

## 0. Baseline facts that change the card's file list

- **Several D3s are server-built links.** Row hrefs come from `backend/assetops_backend/work/global_index.py` (`_site_href` :231, `_select_cases` :265-345, preventive :378), `work/site_index.py` (`_finding_link` :189, `_action_link` :203), `work/operational_index.py` (:38, :83) and `work/global_detail.py` (:91 `site_href`, :104-136 links). The card names only frontend files plus R373's `main.py`/`global_work_api.py`. R352, R353, R359 and R360 cannot be fixed honestly under the current DTO from the frontend alone (Q1).
- **Global rows carry no Site domain.** The list and detail wires have `site_code`, `site_name`, `site_id` only. The Site scope query already selects `site_type` (`adapters/postgres_global_read.py:28,92`), and W3 has `site_home_href(code, domain)` (`estate/evidence_money.py:139`).
- **The default window is frontend.** `defaultGlobalWorkWindow` (`globalWorkClient.ts:643`) returns `[today-7d, today 00:00Z)`. The backend accepts a future exclusive `to` (`global_index.py:110-140`), so the R338-ruled window needs no backend change.
- **R373 is merged.** Q5 copy is live (`globalWorkClient.ts:454`). W502/W504 `SERVE_ENTRY` now mount the global router (Q7). Both tools' `env()` copy `os.environ` (`w502…:592`, `w504…:530`), so setting `ASSETOPS_WORK_CURSOR_KEY_HEX` in the operator shell reaches every serve child. No tool edit is needed.
- **`workRequestShared.tsx` is not in the card but holds most of the B19 fixes.** It holds `stateLabel` :57, `OpenSite` :165, `WorkRequestTabs` :231, `WorkRequestBar` :247 and `WorkRequestRefusal` :279. The same goes for `ui/UnavailableEntry.tsx` (shared; do not edit) and `App.tsx`. R371 needs `App.tsx`, which the card restricts to W2 (Q13).
- **Some W6-01 spec literals are now ruled D3.** The spec's literals (`Event {raw} · meaning not established`, `maintenance record {uuid}`, minutes-only date bar, 1150 px oprecords min-width P-E2-8, tab row "never wraps" W6-01d M1) are now D3. Each change below supersedes a spec literal, so the copy needs a ruling.

## (a) Build plan per D3 item

Each item lists the change, files, tests, and the recapture evidence its unit needs. "BE" marks backend edits that need Q1.

### R352 (B18-03, Medium): cold and EV Finding links on global rows
- **Change:** a cold or EV Finding must not be an anchor while the domain Finding frame ignores `revision_id` (R66/R75, R38 principle). The recommended route (Q2-A) is BE additive `site_domain` on list rows and detail `selected`. The frontend then renders the R66/R75 plain `Finding {id8}` for non-mini rows in `GlobalIncidents.tsx` `FindingsWork` :57, in `GlobalMaintenance.tsx` :114, and in the WR Overview Source cell (`workRequestShared.tsx` `SourceLink` :307), with no false "Link unavailable at this cutoff" suffix. Mini keeps its exact-revision link.
- **Files:** `global_index.py`, `global_detail.py`, `postgres_global_read.py` (pass `site_type`), `globalWorkClient.ts` types and validator, `GlobalIncidents.tsx`, `GlobalMaintenance.tsx`, `workRequestShared.tsx`.
- **Tests:** `test_w601a/b/c` (the parity assert at `test_w601a…:537` stays true under option A), `globalIncidents`/`globalMaintenance`/`workRequestOverview` tests. Each covers a cold row with plain text, an EV row with plain text, and a mini row with an anchor.
- **Evidence:** cold, coldwc, cold all-open, the cold WR Overview, and the `linkcold-finding` landing (should now be absent).

### R353 (B18-04, Medium): EV Site link opens the generic page
- **Change:** BE `links.site.href` becomes `site_home_href(code, site_type)` on all four roots: `global_index.py:320,378` and `operational_index.py:83`. It also applies to the WR detail Site link (`global_detail.py:91,130`), used by `Open site` and the crumb's "site:". Keep `_site_href` for the `/work/incidents` and `/work/maintenance` tab links: EV work tabs already land correctly (B18-17). This is independent of W2-EV's bare `/sites/:id` EV redirect, which is a safety net (Q3).
- **Tests:** `test_w601a/b/c/e` site-href asserts (`test_w601a…:218` changes for EV only); frontend DTO tests unchanged.
- **Evidence:** ev and evwc on incidents and maintenance, the EV WR Open site, and a `linkev-site-overview` landing that now shows `/sites/EV-LAB-001/ev`. Preventive and oprecords EV rows are a producer gap (W504 writes none), so BE tests only there.

### R354 (B18-05, Low): page two opened from a URL shows a false range
- **Change:** in `globalWorkParts.tsx` `Pager` :180-220, when `cursor !== null && trail.length === 0` the offset is unknown. Show an honest caption without a range (Q6 copy) and keep Previous going to page one. The Next path is unchanged. The fix applies to all four list roots through the shared Pager. History's client pager is unaffected.
- **Tests:** add a URL-opened page-two case to `globalIncidents`, `globalMaintenance` and `operationalRecords` tests, plus preventive. Existing "Showing 6–6 of 6" Next-click asserts stay.
- **Evidence:** page-two (incidents, maintenance, oprecords) at both widths.

### R356 (B18-07, Low): oprecords table scrolls horizontally at 1440
- **Change:** in `globalWork.css:392-405`, replace `min-width: 1150px` at ≥761 px with fixed-layout column widths that sum to no more than the 1440 table client width (1105 px). Keep the 390 inner horizontal scroller. Text wraps inside cells. This supersedes P-E2-8 (Q16 widths).
- **Tests:** jsdom cannot see layout, so the proof is a capture with `scrollWidth <= clientWidth` at 1440 on positive, worstcase and the five-160-char probe.
- **Lesson 15:** rows grow taller, and oprecords has no docket cap (Q15).

### R357 (B18-08, Low): no Incidents breadcrumb
- **Change:** add `<Breadcrumbs trail={[{ label: "Incidents" }]} />` before `PageHeader` at `GlobalIncidents.tsx:198`, as Maintenance does at :258.
- **Tests:** `globalIncidents.test.tsx` crumb assert.
- **Evidence:** all incidents pairs; h1 y should match its siblings (44).

### R359 (B18-10, Low): WR codes plain on Incidents
- **Change:** BE incident rows add `linked_requests: [{label: code, href: /maintenance/requests/{id}?site_id={code}[&known_at=explicit cutoff]}]`. `gx.linked_request_codes` at `global_index.py:322` also has to return ids. `linked_request_codes` and `basis` stay unchanged, so there is no cursor or digest change. In `GlobalIncidents.tsx:66-70`, render each code with `LinkOrText`. The INC-code half is D1: extend R73/R85 to `incidents` with a visible label (Q4).
- **Tests:** `test_w601a` linked fixture, `globalIncidents.test.tsx` (link plus text fallback), `globalWorkClient.test.ts` validator.
- **Evidence:** the `linked` incidents case, plus a new WR landing captured from the incident row.

### R360 (B18-11, Low): INC link pins `known_at` on a current read
- **Change (Q5 default, BE):** `site_incidents`, and the `site_maintenance` fallback, carry `known_at` only for an explicit inbound cutoff. `select_incidents` must pass `cutoff` (`global_index.py:249-254`). This matches P-C1-5 (maintenance detail) and P-E1-6 (operational case links), and supersedes A1Q Q8 for these two hrefs.
- **Tests:** `test_w601a…:302-304` asserts both the implicit and explicit cutoff forms; `test_w601b` fallback.
- **Evidence:** incidents positive and historical, plus link landings for current (no historical notice) and historical.

### R361 (B18-13, Low): refusal blocks lack a live region
- **Change:** add `role="alert"` to `RefusalBlock` (`globalWorkParts.tsx:100`) and to the WR `WorkRequestRefusal` (`workRequestShared.tsx:279`). Add `role="status"` to the loading and EMPTY_SCOPE blocks (Q8). Copy stays as is (the classification accepts it).
- **Tests:** role asserts on each list test and on the WR refusal test.

### R364 (B19-03, Low): the WR tab row clips History at 390
- **Change:** at ≤760 px, `.work-request-tabs` (`globalWork.css:189-202`) wraps instead of scrolling. Drop the nowrap/min-width rule there and keep `useCurrentTabInView`, which is harmless. Do not change the shared `UnavailableTab`. The Verification-tab state gets a D1 register row (Q9).
- **Tests:** layout only, captured at 390 on every wr-* pair: four tabs visible, no inner tab scroller.

### R366 (B19-05, Low): UUID and short-ID labels on WR pages
- **Change:** (1) The History COMPLETE row (`WorkRequestHistory.tsx:117-121`) maps `maintenance_record_id` to its position in `work_detail.records` (copy in Q10). The UUID moves into a "Stored record ID" disclosure. (2) Action labels become their stored `ACT-…` code. W1 and domain Actions both have codes (`postgres_action_store.py:294`; cold-action shows ACT-000001). This needs a BE label lookup (Q10 scope). (3) Finding: no public code exists, so `Finding {id8}` stays and R65/R74 D1 extend to wr-* and the global lists.
- **Tests:** `workRequestHistory`, `workRequestOverview`, `test_w601c` label tests.

### R367 (B19-07, Low): refusal shells
- **Change:** in `WorkRequestFrame` (`workRequestShared.tsx:372-416`), when `failure !== null`, render no page panels. That means the `children` panels are not rendered, so Work done, Lifecycle and the claim-bearing `LIFECYCLE_NOTE` go too; Record and History do the same. The single refusal block remains. Reload shows only for `WORK_STORE_UNAVAILABLE` and on a loaded body. `OpenSite` renders nothing without an href. The no-site sentence becomes "Choose a request at a site.". The detail 503 sentence drops the duplicated "Reload." (Q11). Pages: `WorkRequestOverview.tsx:121-141`, `WorkRequestRecord.tsx`, `WorkRequestHistory.tsx`.
- **Tests:** one case per refusal code, plus no-site and malformed id, on all three tests: no panels, Reload present or absent, no Open site element.
- **Evidence:** all 10 B19 refusal cases at both widths, with heights reduced.

### R368 (B19-08, Low): `<div>` inside `<p>`
- **Change:** `WorkRequestRecord.tsx:116` changes `<p className="work-record-outcome">` to `<div>`; keep the CSS class.
- **Tests:** `workRequestRecord.test.tsx` asserts no `validateDOMNesting` console error (spy on `console.error`).
- **Evidence:** console clean on all wr-record pairs.

### R370 (B19-10, Low latent): raw VERIFICATION_WINDOW and OPEN_VERIFICATION
- **Change:** add a `VERIFICATION_WINDOW` entry in `STATE_LABEL` (`workRequestShared.tsx:50`) and an `OPEN_VERIFICATION` label in `eventText` (`WorkRequestHistory.tsx:106`). Other unknown kinds get a plain fallback with the raw code in a disclosure (Q12 copy; supersedes W6-01 spec :662).
- **Tests:** pure typed-DTO tests only. This is a producer gap: no writer enters VERIFICATION_WINDOW.

### R371 (B19-12, Low): unknown request section lands on the unshelled catch-all
- **Change (Q13 default):** add a route inside the operator shell, `${WORK_REQUEST_PATH_PREFIX}/:caseId/*`, ahead of the `*` route at `App.tsx:551`. It renders a shelled "This address is not served" panel with a link to that request's Overview, preserving `site_id` and `known_at`. No silent redirect. `navigation-truthfulness.ps1` and the registry need the matching entry. Align with W5-EV-Work R350.
- **Tests:** a route test for the four B19 link-check addresses (`/overview`, `/evidence`, `/execution`, `/records`).
- **Evidence:** the link-check landings.

### R372 (B19-13, Low): historical date bar shows minutes only
- **Change:** add a seconds formatter beside `globalWorkUtc` (`globalWorkClient.ts:708`). Use it for the historical line in `WorkRequestBar` :260 and the list `StatusLine` historical branch (`globalWorkParts.tsx:170`, Q14). Current lines stay at minutes.
- **Tests:** the `Historical as of …` asserts at `globalIncidents.test.tsx:293`, `globalMaintenance:351`, `globalPreventive:287`, `operationalRecords:463`, plus a WR history test.
- **Evidence:** historical-120001-rev2 and the list historical cases.

### Carried into this card (not D3 IDs but assigned here)
- **Default window (B18-12 → R338):** set the global default to `[today-6d 00:00Z, tomorrow 00:00Z)` in `defaultGlobalWorkWindow`, with one membership line per list (Q7). Tests: the `defaultGlobalWorkWindow` asserts (`globalIncidents.test.tsx:376`, `globalPreventive.test.tsx:298`) plus a current-day row test. Evidence: ev-default-window and evwc-default-window, where today's EV case is now visible.
- **R373 recapture gate:** current-SHA B19 403/200 for mini, cold and EV at both widths. Cold and EV come from the `forbidden` and `positive` walkthrough modes, now 403 through R373 Q7. Mini comes from the reviewed `.agent/W6-01-evidence/C2/api_403.py`.
- **K4 registry chain:** W6 is the owner (fix-slices "Carried Architect closeout"); see Q19.
- **B18-14 explicit ruling (R362 D4):** replace the mock Site options and the `6 Oct 2026 · 16:00 EAT` value (`OperationalRecords.tsx:272-293`) and add a D4 label next to the form. It is not listed as a W6 D3 (Q17).

### Recapture inventory (unit 5)
- **Pairs:** all 380 indexed pairs (186 B18 + 194 B19). Add the 16 B18 and 10 B19 link landings, plus new landings for R353 (EV Site), R359 (WR from incident), R360 (current INC) and R371 (4 addresses).
- **Producers, unmodified:** `tools/w601_seed.py` fixtures served by plain uvicorn; `w502_cold_work_walkthrough.py` and `w504_ev_work_walkthrough.py` prepare/serve/attest/drop, with `ASSETOPS_WORK_CURSOR_KEY_HEX` exported in the operator shell. 403 comes from `C2/api_403.py` and 503 from `C4/api_503.py` or an absent DB. DBs are named `*_test` only and dropped afterwards.
- **Declared gaps:** VERIFICATION_WINDOW; cold and EV preventive and oprecords rows; five 160-char rows on preventive, oprecords and wr-* (capture-only DOM probe instead, Q15); a single list holding all three domains; pending and stale global states.
- **Cap proof:** every docket row plus the Q15 rows, closed and all-open, recorded with SHA and producer.

### Cross-card overlaps
- **W2-EV:** the bare `/sites/:id` EV redirect overlaps R353. W6 fixes the href directly and rebases over W2-EV; recapture EV landings after whichever merges second.
- **W5-cold-Work:** R338 owns the default-window rule. W6 applies it to the global lists only (Q7). Copy should match R338's Site Work membership wording.
- **W5-EV-Work:** R350 (B17-08) is the same unknown sub-tab family as R371, so use one pattern (Q13). The R373 packet's observation 2 (EV positive Site Work detail 503 from the W5-04 `SERVE_ENTRY` shadow) belongs to W5-EV-Work; W6 records it only.
- **W4-mini:** R333 (B13-18) has 390 tab clipping on Site Work tabs. Its mechanism should not diverge from R364 (Q9). There is no shared file unless either card edits `ui/UnavailableEntry.tsx`, which W6 will not.
- **Shell (merged):** aliased recurrences on W6 screens remain: B18-01 `'1 requests'` at `GlobalMaintenance.tsx:221`, raw `c1 · EV_CONNECTOR` and `generator-1 · GENERATOR`, B2-21 Site-local time on WR, B19-17 crumb style (Q18).
- **R374:** the global lists treating an access 401 as an empty 200 is R374's, not W6's.

## (b) Questions for the Architect (21)

1. **Backend scope.** Authorize production edits in `backend/assetops_backend/work/global_index.py`, `global_detail.py`, `operational_index.py`, `site_index.py` (only if Q10 picks the shared option) and `adapters/postgres_global_read.py`, plus `test_w601a/b/c/e`, for R352/R353/R359/R360/R366. **Default:** authorize additive wire fields and href changes only, with no cursor, basis, digest or schema change. Run focused W6 and R373 backend tests, then one real-Postgres full backend suite at the final revision with keep-awake, a 2x cap and JUnit zero-skip.
2. **R352 mechanism.** (A) Additive `site_domain` (from `site_type`) on list rows and detail `selected`. The frontend renders cold and EV Findings as plain `Finding {id8}` (R66/R75), backend hrefs are unchanged, and A1Q Q7 Site-row parity holds. (B) The backend nulls non-mini Finding hrefs. That breaks the parity test, and the WR Source would print the false "Link unavailable at this cutoff". **Default:** A. Extend it to the WR Overview Source cell (same defect, same cold capture). Lists show a plain label without the version disclosure, to protect clamp height.
3. **R353 extent.** **Default:** use `site_home_href` for `links.site` on all four lists and for the WR detail Site link (`Open site` and the crumb), whether or not W2-EV's redirect lands. Leave work-tab hrefs on `_site_href`.
4. **R359 contract and INC half.** **Default:** additive `linked_requests[{label, href}]` with an explicit cutoff only; `linked_request_codes` and `basis` stay. Extend R73/R85 (D1) screens to `incidents`, with a visible 12 px `MOCK DEVIATION D1 (R73)` line under the Incident cases panel.
5. **R360 location.** Backend: carry `known_at` only for an explicit cutoff on `site_incidents` and `site_maintenance`, superseding A1Q Q8 for those hrefs. Frontend alternative: strip `known_at` when `status === "CURRENT"`. **Default:** backend, to match P-C1-5 and P-E1-6.
6. **R354 caption copy** when the page offset is unknown. **Default:** `Later page · {rows} of {total}`, with Previous going to the first page and no range digits.
7. **Default window and membership copy for the global lists.** **Default:** W6 owns the global half of R338: `[today−6d, tomorrow)` UTC. Add one 12 px line under each control bar:
   - Incidents: "Listed by incident start time."
   - Maintenance: "Listed by the time each request was opened."
   - Preventive: "Listed by the time each plan was first recorded."
   - Operational records: "Listed by the time each record's event happened."

   Explicit windows are preserved.
8. **R361 roles.** **Default:** `role="alert"` on list and WR refusal and 503 blocks; `role="status"` on loading and EMPTY_SCOPE; copy unchanged.
9. **R364 fix and register.** **Default:** wrap the WR tab row at ≤760 px with the full label kept (supersedes W6-01d M1 "never wraps"), with no copy shortening and no shared-component edit. Add a new D1 row for "Verification · Not available yet" on wr-*. W4-mini R333 should use the same wrap rule.
10. **R366 copy and label scope.**
    - COMPLETE row: `Completed · outcome not established · maintenance record {n} · {occurred_at UTC to seconds}`, where n is the 1-based record-root order. If the id is absent from the read: `… · maintenance record not in this read`. The UUID goes in a "Stored record ID" disclosure.
    - Actions: a global-only `ACT-…` label (detail and global lists), with Site Work rows left to W4/W5. The alternative is a shared `site_index._action_link` change, which widens recapture to sitework, cold-work and ev-work.
    - Findings: extend R65/R74 D1.

    **Default:** global-only.
11. **R367 specifics.**
    - **Default:** on any failure, no page panels.
    - Reload only on 503 and on a loaded body (not on 401/403/404/422).
    - Detail 503 sentence: "Work records could not be read." (list copy unchanged).
    - `Open site` is not rendered without an href.
    - No-site: the subtitle "Request details could not be shown." plus the sentence "Choose a request at a site."
12. **R370 copy** (supersedes W6-01 spec :662).
    - State: `Verification open · outcome not established`.
    - Event OPEN_VERIFICATION: `Verification opened · outcome not established`.
    - Other unknown kinds: `Unrecognised event · meaning not established`, with the raw code in a "Stored event code" disclosure.

    **Default:** as written; DTO tests only; backend P-B1-11 list 503 unchanged.
13. **R371 route.** **Default:** authorize one `App.tsx` route, `/maintenance/requests/:caseId/*`, inside the shell: a shelled not-served panel plus a link "Open this request's overview" (preserving `site_id`/`known_at`), with the matching navigation-guard and registry entry. No redirect. W5-EV-Work R350 uses the same pattern.
14. **R372 extent.** **Default:** seconds on every historical line (WR bar and all four list status lines); current lines stay at minutes.
15. **Missing caps and method (Lesson 15).** The docket has no row for `maintenance-preventive` (both widths), `oprecords` (all three panels, both widths), incidents "Case boundaries", or any wr-* panel at 390.
    - **Default:** use the W6-01 spec caps where they exist (preventive 600/690; oprecords table 650/780; WR History 600/690 at 390). Otherwise use the current-SHA worst closed peak × 1.15, rounded up to 50, which the Architect ratifies at closeout.
    - Worst case is five rows with 160 characters in every variable text field (W3 caps2 ruling 1). Use the capture-only DOM probe (W3 closeout ruling 1) where producers cannot emit it.
    - All-disclosures-open is exempt with zero clipping.
    - Fallback: the existing inner table scroll (the R355 pattern), with every row reachable by scroll and none removed. Confirm this inner scroll satisfies "never hide a row".
16. **R356 widths.** **Default:** at ≥761 px, fixed layout Record 90 / Type 110 / Site 150 / When 130 / By 120 / What it says 270 / Feeds 140 / State 90 (1100 px), with cells wrapping. Retune against the mock's measured columns if those differ by more than 10 %. The 390 px table keeps its own scroller.
17. **Registered D1/D2/D4 labels and the B18-14 form.** These are not in the W6 D3 list.
    - **Default:** W6 adds visible adjacent labels for R355, R358, R362, R363, R365 and R369, following the W2-EV Q31 precedent.
    - W6 builds the B18-14 ruling: Site options come from the response `scope.sites` (code and name) or an empty placeholder; the time input is empty with the placeholder "Event time"; submission stays disabled (R12); the D4 label sits next to the form.
18. **Shell-alias recurrences on W6 screens.**
    - **Default:** W6 fixes `'1 requests'` to "1 request"/"{n} requests" (`GlobalMaintenance.tsx:221`).
    - Raw asset labels become "EV connector c1" and "Backup generator · generator-1" (R89), with the raw `code · TYPE` in the existing disclosure if any. This covers maintenance and wr-overview.
    - B2-21 Site-local time on WR pages stays UTC under R369 (D2, verified) and is recorded as a residual.
    - Crumb style is verified by recapture only.
19. **Registry chain.** **Default:**
    - Resolve `A-work-cases` and `A-maintenance-index` with W4-01 and W6-01 evidence, and `A-cold-work-projections` with W5-02 plus this card's evidence.
    - Leave `A-ev-work-projections` open: its predecessor `A-ev-session-rules` is still open in the pilot registry.
    - Put exact producer and consumer contracts in the packet. Confirm, or say whether `A-ev-session-rules` should be resolved and by whom.
20. **Producers, env and gaps.** **Default:**
    - Export a fresh random `ASSETOPS_WORK_CURSOR_KEY_HEX` in the operator shell for every serve (inherited by W502/W504 children and plain uvicorn), with no tool edit.
    - Gaps are declared as in the inventory above.
    - Mini 403 comes from the reviewed `C2/api_403.py`.
    - The EV `positive` Site Work detail 503 shadow (R373 packet observation 2) goes to W5-EV-Work.
21. **Register numbering and status.** Main uses up to R382; W1-b uses R383-R385 and W1-a R386-R395 on unmerged branches. **Default:** new W6 rows start at R396 (Q9's Verification-tab D1 first). D3 rows R352-R372 move to resolved only after review and paired recapture.
