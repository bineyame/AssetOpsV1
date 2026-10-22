# W6-01 build-spec readiness review

Reviewer: fresh Claude reviewer (did not author the spec), 2026-10-22. Read-only dry-read of `.agent/W6-01-build-spec.md` and `tasks/W6-01-global-work-cases.md` against main `5c89d633` in `AssetOpsV1-plan2`, the measurements in `.agent/W6-01-mock-measure.md` (raw `scratchpad/m1/*.json`, injector `scratchpad/worst.mjs`), and v69 `frontend/mockups/v69/screens.js` / `screen-manifest.json`. Gate rules: `.ai/ROLE_CONFIG.md` "Build-Spec Readiness Gate For W5 And W6" and lessons 1-13.

Checks I ran: `node frontend/docs/architecture/check_v69_dependency_registry.cjs` -> `Registry valid: 251 nodes, 43 linked pilot panels` (unchanged tree; this does not check any W6-01 row, because none exists). `tools/check-all.ps1` on the unchanged tree: see the closing note. No DB was created and no server was started.

Tags: **BLOCKER** means a builder would have to decide something, or would find the spec wrong against code. **NOTE** is a correction or clarification that does not stop the build.

## A. Cross-cutting (§1 model, wire, links; §3 ownership; §4 producers)

1. **BLOCKER. §1 "Links": Site route identity is the Site code, not the UUID.** The spec says "Frontend route identity is the stored Site **UUID**, as `operatorSiteRoutes.ts` shows, while API scope is the stored Site code". In code the frontend `siteId` *is* the Site code: `backend/assetops_backend/sites_api.py:212` (`"site_id": site.site_code`), `frontend/src/estate/actionIndex.tsx:102` (`siteDetailHref(row.site_code)`), and `frontend/src/sites/workClient.ts:166-173`, which passes the route `siteId` straight into `/api/sites/{site_code}/work/...`. Backend-built hrefs use the code too: `work/site_index.py:186` (`/sites/{site_code}/findings/...`) and `estate/portfolio.py:168-173`. So every link rule in §1 is wrong as written, along with C1's `GET /api/work/requests/{case_id}?site_id={site_uuid}`, C1's "checks that the UUID Site is authorized", and C2's `/work/requests/{case_id}?site_id={site_uuid}`. Fix: the Architect picks one identity for the detail route (code, which matches every existing route and W3 link) and restates C1/C2.
2. **BLOCKER. §1 "Window and access" plus the A1 tests: the global list access and refusal model contradicts the W3 global-root pattern the spec says to reuse.** W3 estate roots never answer 403 or 404, and a denied Site is silently left out (`backend/assetops_backend/estate_api.py:6-11`). The spec instead requires "wrong tenant/Site/ID is 404 or 403", lists `SITE_SCOPE_FORBIDDEN` 403, has UI copy `No access to this Site.`, and makes A1 prove "401/403/404/409/422/503" on `/api/work/incidents`. The parser is also undecided. "Use the existing W3 parser limits" points at `estate/scope.py:105-148`, which requires `from`/`to` at midnight and refuses with `ESTATE_*` codes and messages. The spec's codes are `WORK_*`, and the W4 parser `work/site_index.py:106-124` has a different `INVALID_WINDOW` message per field. "Default last seven complete UTC days" does not say whether the server defaults an omitted window (neither parser does) or only the UI (`workClient.ts:178-184`). Fix: name the parser, the refusal codes and messages per route, and which statuses a global list can return. Keep 403/404 only for the exact detail route.
3. **BLOCKER. §1 "New read envelope": no row DTO for any of the four roots.** Only the envelope keys are given. The builder has to invent every row field, for example `site_code`, `site_name`, `site_code_key`, the owner/assignee field, linked request code(s) for an incident, `kind`, `source_provenance` (needed for the `Source unverified` labels), lineage fields for plans and records, `trigger_kind`, `next_due_*`, `case_id`/`case_kind` for records, and the root and head IDs. Also:
   - `coverage:{state,reason,sites}` has no `state` literals;
   - `scope` drops W3's `tenant_id` (`estate/index.py:210-215`) without saying so;
   - the detail envelope's "existing `work-case-detail-1` fields verbatim" collides with `schema_version` and `site_code` (`work/detail.py:73-74`);
   - `history.records` duplicates the existing `records` (`detail.py:91-93`);
   - `links` has no shape, and it is not said whether hrefs are backend-built (the W3/W4 pattern) or frontend-built with the helpers.

   Fix: give one literal JSON example per root and for the detail read.
4. **BLOCKER. §1: the window and sort column for plans and operational records is not defined.** Plans and authored records are sorted by `recorded_at desc`. The spec does not say which column decides `[from,to)` membership (`occurred_at` or `recorded_at`, of the root or of the head). `operational_record` is indexed on `occurred_at` (`migrations/versions/0027_w4_work_cases.py:195`), and E2's `When` column shows occurrence. A corrected chain can also have its root and head in different windows.
5. **BLOCKER. §2 Owner for incidents and maintenance and the `wr-overview` header: the source is ambiguous.** "ASSIGN actor/payload" could mean `payload.assignee` (`work/model.py:315`) or the event `actor_id`, which is a service ID such as `service:w401-fixture`. Say: latest selected ASSIGN at the cutoff, `payload.assignee`.
6. **BLOCKER. §3 "One frozen fixture clock" (lesson 4): one instant cannot produce the required states, and the served API cannot pin a read clock.**
   - If every write uses `2026-10-22T12:00:00+00:00`, then "correction/event after known_at", "historical", "cursor changed appends a new row" and "same-time UUID order versus later events" cannot all be produced. The store override is a callable (`work/adapters/postgres_work_store.py:7,279`), so a stepped clock is possible, but the spec does not give the steps.
   - The read clock override is test-only: "no request, env or `main.py` path supplies it" (`work/adapters/postgres_work_read.py:5-6`). An API-backed capture therefore reads at real DB time. Its `As known at` label cannot show the frozen clock, and passing `known_at=2026-10-22T12:00Z` makes every capture `HISTORICAL`.

   Fix: per fixture, give the write-clock sequence (for example +1 s per command), the read mode (pinned in pytest, real DB time in captures) and the screenshot label rule.
7. **BLOCKER. §4 "Producer trace" (lesson 3): states with no producer, and no capture seed.**
   - There is no seed script for the cross-Site, two-tenant capture data. W4 used `.agent/W4-01-evidence/seed.py`: one Site, real DB time.
   - Positive Finding/Action-linked rows: the W4 seed records that a cited link was refused by the acceptance cutoff (`seed.py:5-7`), and "only when W4 store accepts exact IDs" is not a producer.
   - `PARTIAL` ("a selected Site read unavailable") has no producer path on a single REPEATABLE READ connection.
   - `EMPTY_SCOPE` (a principal with zero Sites) has no named access stub.
   - "Forbidden" list captures contradict item 2.

   Fix: name the seed file and its owning unit, and rule each producer-less state as pure-snapshot or an honest limitation.
8. **BLOCKER. §4: no height caps and no UI page size.** The API default is `limit=50` (§1). The mock tables hold 1-8 rows, and W4 used `WORK_PAGE_LIMIT = 5` (`frontend/src/sites/workClient.ts:18`). Caps are listed in section G.
9. **BLOCKER. §3/§4: registry paths are not named for any screen.** The registry has only `incidents` panels 1-2 and `maintenance` panel 1, all `gap` and all requiring W4 nodes (`frontend/docs/architecture/v69-dependency-registry-pilot.json:441-443`). There are no panel rows for `maintenance-preventive`, `wr-overview`, `wr-record`, `wr-history` or `oprecords`, and no W6-01 implementation nodes. The product node `P-work-cases` is `"pending owner"` and governs these screens except `oprecords` (`:181`). §4 itself says Lane A still has to "prepare" the paths. Fix: literal rows, nodes and `requires` per screen and panel, checker run recorded, and a ruling on whether `P-work-cases` needs an owner choice first.
10. **BLOCKER. §3 file ownership (lesson 7): promoting the rail breaks files that no unit owns.**
    - Existing tests: `frontend/src/shell/__tests__/operatorRailInventory.test.tsx:29-31,83-85`, `operatorRouteFrames.test.tsx:269-271`, `w301EstateShellRoutes.test.tsx:155-167` and `frontend/src/estate/__tests__/estatePortfolioRoutes.test.tsx:66`.
    - The guard fixture `tools/checks/navigation-rail-fixtures.ps1:80-85` edits the `unavailable ... "Incidents"` line.
    - `frontend/src/sites/siteWorkCases.tsx:118` `WORK_CONTEXT_NOTICE` ("A global work page and create flow are not available yet.") becomes false once `/incidents` is live, and it has a `REVIEWED_EXEMPTIONS` entry in `tools/checks/missing-claim-scan.mjs`.

    A2, B2 and E2 say only "navigation guard and fixtures". Fix: name every path per unit (`tools/checks/navigation-truthfulness.ps1:550-552`, the fixture file, the four tests, the notice, its exemption, and the registry JSON).
11. **BLOCKER. §2 `wr-overview` tabs and B2/B3/C2/C4 order (lesson 1): unbuilt in-page tabs.** "Verification is disabled `Verification unavailable`" would be rejected by the guard. An unbuilt in-page tab must render through `frontend/src/ui/UnavailableEntry.tsx` ("Not available yet"), cannot be a disabled control, and is part of a closed `$expectedTabs` multiset (`tools/checks/navigation-truthfulness.ps1:719-735,752-753`).
    - W6-01c (C2) merges before W6-01d (C4), so the `History` tab cannot be an "exact local route" in C2. It must be an `UnavailableEntry` plus an `$expectedTabs` entry in C2 and be removed in C4.
    - `Maintenance record` has the same problem between C2 and C3.
    - The B2 `Preventive · scheduled` tab and the `Preventive due in 30 days` card link point at a route that B3 builds later, which matters for per-unit review and guard runs.

    `navigation-truthfulness.ps1` is in none of the B2, B3, C2, C3 or C4 file lists.
12. **BLOCKER. §2 `oprecords` "Record a manual reading" and E2: the form cannot be built as specified.**
    - The POST body needs `kind, body, occurred_at, period_end, unit, quantity, source_document_sha256, case_id, actor{kind,id,attestation}, idempotency_key`, and `MANUAL_READING` requires both `quantity` and `unit` (`work/service.py:453-470`). The form has `Site`, `Reading`, `Value` and `Taken at`: no unit, and no field-to-wire mapping.
    - The `Reading` options are not given (the mock has a select, `screens.js:839`).
    - The actor must be a SERVICE whose attestation names the server principal (`work/model.py:267-278`), so the browser would have to send the service identity, which is the "client-side SERVICE forgery" the spec forbids.
    - No endpoint tells the UI whether a command principal is authorized, so "only enabled for a server-authorized command principal" cannot be decided.
    - The source of the `Site` options is not named.

    Fix: rule the entry as read-only gap copy in W6-01, or specify a server capability read and server-side actor construction.
13. **BLOCKER. §2 `wr-record` notice: the spec says something false about the model.** It says `No linked Operational record` "until exact `case_id` relation exists". The relation exists: `operational_record.case_id` with a scoped FK (`0027_w4_work_cases.py:175,184`), and E2 already links on it. Decide whether C3 shows linked REC codes (the mock notice, `screens.js:823`) or states a reason.
14. **NOTE. §1 "Links", Asset:** "only after W6-03 makes that route live" misstates the code. `SITE_ASSET_ROUTE_PATH` is already mounted (`frontend/src/App.tsx:425`), but as the battery Health frame (`frontend/src/shell/SiteHealthFrames.tsx:100-125`). Plain text is still right. Restate the reason.
15. **NOTE. §2 source labels:** the disclosure copy differs from the existing `SOURCE_WORDS` (`frontend/src/sites/sourceProvenance.tsx:90-107`). The existing statements say "These records were prepared for an example. ..." and MIXED/UNKNOWN say "No current cost is shown.", which does not fit work rows. Name reuse or new literals.
16. **NOTE. §1 Identity:** "latest correction = max `(revision_no,id)`" differs from the merged rule, which takes the last revision by `(recorded_at,id)` (`work/site_index.py:217`, `work/detail.py:65`, `_REVISIONS` order in `postgres_work_read.py`). C1 Site-read parity needs the merged rule.
17. **NOTE. §1 cursor:** "tampering is 422 `INVALID_CURSOR`" cannot be detected with the W4 unsigned base64 cursor (`work/site_index.py:82-103`). A tampered `after` decodes, and the token alone does not bind it. W3 Portfolio uses a MAC (`estate/scope.py:299-341`). Name the pattern.
18. **NOTE. §1 timestamps:** W3 wire time is whole seconds (`estate/scope.py:151-153`) and W4 is microseconds (`work/model.py:192-194`). State which one the global envelope uses.
19. **NOTE. §2 refusal copy:** the new UI strings differ from W4's ("The list changed. Reload the first page.", `siteWorkCases.tsx:271`) and from the backend message ("No access to Site '{code}'.", `work_api.py:174`). `SITE_NOT_FOUND` 404 (`work_api.py:180`) is missing from the refusal list, but a detail read for an unknown Site needs it. Mark the strings as explicitly new or reuse the W4 ones.
20. **NOTE. §3/§4 review marks:** the table marks per-unit review only on A1, B1, C1 and E1. The closing paragraph says every Lane A handoff unit gets per-unit review, which includes A2, B2, B3, C2, C3, C4 and E2 (all touch `App.tsx`). §4 also names a "D1" producer that does not exist.
21. **NOTE. §3 unit size:** each page unit is in practice two dispatches (the Lane B page, then the Lane A integration). State that, so "one builder run" stays true.
22. **NOTE. §1 route versus mock root:** `/work/requests/{id}` sits under no rail root, but the manifest puts `wr-*` under root `Maintenance`. The rail would not highlight Maintenance. Consider `/maintenance/requests/...`.

## B. W6-01a: A1 (read) and A2 (`/incidents`)

23. **NOTE. A2 `incidents` panel footer slot:** the mock footer is "States: New → Acknowledged → ... → Closed verified" (`screens.js:516`). The spec's "Context copy" does not say whether it replaces the footer or is a separate notice. Name the slot.
24. **NOTE. A2 Incident and Site cell destinations:** `siteWorkIncidentsHref(siteId, query)` has no query literal. Which window (the one containing `occurred_at`?) and which `known_at`? The same applies to the maintenance fallback "Site maintenance exact window".
25. **NOTE. A2 status copy:** there is no display literal for `PARTIAL`, and no date format for `As known at {known_at}` / `Historical as of {known_at}`.

## C. W6-01b: B1 (read), B2 (`/maintenance`), B3 (`/maintenance/preventive`)

26. **NOTE. B2 unbound mock slot (lesson 6):** the notice "Work requests share the managed-task lifecycle ... Verification window → Verified, Ineffective or Inconclusive" (`screens.js:814`) has no binding. Left as is it implies a verification lifecycle W4 does not have. Give a replacement literal or rule it removed.
27. **NOTE. B3 unbound mock slot:** the notice "PM-0455 was overdue when the backup start failed ..." (`screens.js:818`) has no binding.
28. **NOTE. B1/B3:** plan window membership is the same open question as item 4. The `Trigger` mapping `CALENDAR` → `Calendar`, `RUN_HOURS` → `Running hours` matches `0027:122,138`, and `DRAFT` is the only state written (`service.py:441`). These check out.

## D. W6-01c: C1 (detail read), C2 (overview), C3 (record)

29. **NOTE. C2 Lifecycle:** "Open → In progress → Completed" has no rule for a `CANCELLED` request (reachable through `TRANSITIONS`, `model.py:102,105`).
30. **NOTE. C2 header `Source`:** an exact Incident link has no destination, because there is no incident detail route. Name it (the Site incidents window) or make it plain text.
31. **NOTE. C3 rows:** "correction successor selected by `supersedes_record_id`" does not say whether superseded records still show. Maintenance records have no root or canonical column (`0027:145-162`), so the chain has to be rebuilt from `supersedes_record_id`.

## E. W6-01d: C4 (history)

32. **BLOCKER. C4 `Event` literals:** "mapped command or `Correction`" gives no display text for `CREATED`, `ASSIGN`, `COMPLETE`, `COMMENT`, `CLOSE`, `REOPEN` or `CANCEL`. "Expandable occurred time" has no UI pattern or literal.

## F. W6-01e: E1 (read) and E2 (`/operational-records`)

33. **NOTE. E1/E2 `kind` filter:** the spec does not say whether `total_count` and the `Records in window` card follow the chip filter or stay at full scope, and it gives no query parameter literal.
34. **NOTE. E2 unbound mock slots:** the table footer "What people on site recorded, and the evidence each one feeds" and the form footer "Fills REC-307 when submitted" (`screens.js:838-839`). The `Feeds` case link has no destination for an INC case (no route).

## G. Height caps the Architect must set (from `.agent/W6-01-mock-measure.md`)

Mock baseline heights in px, 1440 / 390. Rows are mock rows. The Architect has to set each cap together with the UI page size (item 8).

| Screen | Panel or table | 1440 | 390 | Worst measured (variant) | Cap or rule needed |
|---|---|---|---|---|---|
| incidents | cards | 113 | 248 | 128 / 278 (titles200 labels) | card cap |
| incidents | Incident cases (1 row) | 183, row 51 | 248, row 97, table 594/320 hscroll | 390 uuid row 238; 1440 actor128 table hscroll | panel cap for N rows; wrap for `Owner`/UUID cells |
| incidents | Case boundaries | 99 | 142 | fixed copy | cap |
| maintenance | cards | 138 | 272 | 153 / 302 | cap |
| maintenance | Corrective work requests (2 rows) | 234 | 327, table 696/320 | 1440 actor128 324, hscroll | panel cap; Owner wrap |
| maintenance | notice | 42 | 78 | - | cap once item 26 is ruled |
| maintenance-preventive | status strip | 44 | 98 | - | cap |
| maintenance-preventive | cards | 113 | 248 | 128 / 278 | cap |
| maintenance-preventive | Preventive plan (5 rows) | 432 | 602, table 588/320 | 390 uuid 637 | panel cap |
| wr-overview | header (`mheader`) and tab row | not measured | not measured | - | measure and cap |
| wr-overview | Work done / Lifecycle | 286 / 286 | 338 / 161 | text4000: 1042 at 1440, 2001 at 390 | narrative clamp or scroll rule |
| wr-record | Maintenance record · activity (6 rows) | 438 | 716 | text4000: 3383 at 1440, **43825** at 390 | clamp the 4000-char `Detail` cell (C3 says "capped within scroll panel" with no number) |
| wr-history | History (5 rows) | 332 | 402 | text4000: **12032** at 390; actor128 at 390 hscroll | cap; wrap for `By` |
| oprecords | cards | 113 | 263 | - | cap |
| oprecords | Operational records (8 rows) | 540 | 1069, table 601/320 | actor128 at 1440: 1084, hscroll; text4000 at 390: **57954** | `What it says` clamp; `By` wrap; page size |
| oprecords | Record a manual reading / How records are used | 289 / 289 | 443 / 188 | - | cap |

35. **BLOCKER (part of item 8). 390 and 1440 document overflow.** `titles200` overflows the document at **both** widths: scrollWidth 3272/3367 at 1440 and 2583 at 390. The source is unbroken 200-character text in `h1`/`h2`. On `wr-*` pages the `h1` is the stored revision title, which is user data and can be 200 characters (`0027:56`). "Long codes, titles and reasons wrap" is not enough for unbroken strings. Specify `overflow-wrap:anywhere` (or an equivalent) for the h1, title, code, actor (128) and UUID cells, and a 390 table `min-width` with panel-local scroll. The mock scroll widths are 588-696 px.
36. **NOTE. The measurement leaves several worst cases unmeasured (gate lesson 2):**
    - The `text4000` injection selects only headers matching `Detail|What it says|Narrative|Activity|Event|Body` (`scratchpad/worst.mjs`). The **incidents table missed it**, as did the maintenance and preventive tables: their table heights are unchanged (T83, T134 and T332 at 1440; T129, T209 and T484 at 390). Only the panel prose grew.
    - The `titles200` selector `tbody tr td:first-child strong` matches no mock cell, because the mock cells hold `<a>`. So **no table measured a 200-character title row**, and every titles200 table height equals its baseline.
    - The header, the tab rows, the `oprecords` chips and the preventive status-strip text with long content were not measured.

    Re-measure these before the caps are set.

## Verdict

**NOT READY.** 16 BLOCKERs: items 1-13, 32, 35, plus item 8, which carries section G's caps. The rest are NOTEs. The §4 gate also still records "Readiness status: not passed" for height caps and producers, and both remain open.

Closing note on `tools/check-all.ps1`: on the unchanged tree (`5c89d633`), `All 11 guards passed`, exit 0. This proves nothing about W6-01 literals, because none are implemented yet.
