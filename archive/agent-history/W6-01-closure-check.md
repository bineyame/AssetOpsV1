# W6-01 readiness closure check

Reviewer: fresh Claude reviewer (did not author the spec or the first review), 2026-10-22, in `AssetOpsV1-plan2`. Spec files `.agent/W6-01-build-spec.md` and `tasks/W6-01-global-work-cases.md` are byte-identical at `37ad9ba8` (the named base) and HEAD `f938516f`. Nothing committed, no DB created, no server started.

## Verdict: NOT READY. 10 open items (4 BLOCKER, 6 NOTE).

All 15 BLOCKERs and 21 NOTEs from the first review (the review says 16 and 20; its numbered list 1-36 contains 15 and 21, and I checked all 36) are closed by a literal artifact, except where an item below says otherwise. The four BLOCKERs below are new, introduced or left open by the closure: a builder would have to decide a literal, or the spec contradicts merged code.

## Checks run

- `tools/check-all.ps1` with plan2 `.venv\Scripts` first on PATH: `All 11 guards passed`, exit 0 (architecture seams, estate guard self-tests 3 passed, navigation truthfulness, agent workflow, dependency registry, delivery and mock-gap fixtures, missing-claim scan and fixtures, evidence width, screen ledger). These do not test W6-01 literals.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 262 nodes, 51 linked pilot panels`. Rows exist for `incidents:1,2`, `maintenance:1`, `maintenance-preventive:1`, `wr-overview:1,2`, `wr-record:1`, `wr-history:1`, `oprecords:1,2,3` with the `I-w601*` nodes the spec names.
- Measurements: `.agent/W6-01-mock-measure-2.md` (browser run, all caps judged there).
- Not run: no backend or frontend tests (no code exists for W6-01), no implementation capture.

## Review item closure (36 items)

Code claims spot-checked against merged code are marked (v).

| Item | Closed by | Result |
|---|---|---|
| 1 identity = Site code | section 1 Identity; `/maintenance/requests/{id}?site_id={code}` | Closed (v) `sites_api.py:212` returns `site.site_code`. |
| 2 parser, access, refusals | section 1 Parser; refusal table | Closed (v) messages match `estate/scope.py:29-36` and `work/model.py:42-58`. The `INVALID_CURSOR` text is the estate wording by choice. |
| 3 row DTO | four row tables and examples | Closed. See OI-3 for the detail example. |
| 4 plan/record window | root `occurred_at`, head at cutoff | Closed. |
| 5 owner | latest ASSIGN `payload.assignee` | Closed (v) `work/model.py:315`. |
| 6 clocks | section 4 write-clock steps | Closed in structure; occurrence literals open, see OI-6. |
| 7 producers, seed | `tools/w601_seed.py`, fixtures list | Closed; capture harness ownership is OI-9. |
| 8 caps and page size | `limit=5`, cap table, measure-2 | Closed except the header row, see OI-5. |
| 9 registry | section 4 Registry paths | Closed (checker passes). The owner-status sentence is OI-9. |
| 10 unowned files | A2/B2/E2 lists | Partly closed, see OI-2 (Site Work strip and its test are still unowned). |
| 11 unbuilt tabs | C2/C3/C4 `$expectedTabs` handling | Closed for wr tabs. The B2 card is OI-4. |
| 12 manual reading form | read-only replacement copy | Closed. |
| 13 record notice | REC codes or `No linked Operational record.` | Closed (v) `operational_record.case_id` exists (`0027`). |
| 14 Asset text | section 1 Links | Closed. |
| 15 provenance words | four new literals | Closed (v) differ from `SOURCE_WORDS` (`sourceProvenance.tsx:90-107`) deliberately. |
| 16 revision rule | `(recorded_at,id)` | Closed (v) `work/detail.py:65` `revisions[-1]`. |
| 17 cursor | HMAC, `ASSETOPS_WORK_CURSOR_KEY_HEX` | Closed (v) pattern at `estate/scope.py:299-341`. Key documentation is in OI-7. |
| 18 timestamps | whole seconds | Closed for lists; contradicted for detail, see OI-3. |
| 19 refusal copy | refusal table and UI copy | Closed. |
| 20 review marks | section 3 intro | Closed. |
| 21 unit size | two dispatches per unit | Closed. |
| 22 route root | `/maintenance/requests/...` | Closed. |
| 23 incidents footer | slot replaced, literal | Closed. |
| 24 fallback queries | `siteWorkIncidentsHref`/`siteWorkMaintenanceHref` | Closed (v) both exist, `operatorSiteRoutes.ts:312,317`. |
| 25 status copy, date format | section 2 | Closed. |
| 26, 27 unbound notices | replacement literals | Closed. |
| 28 plan membership | section 1 | Closed. |
| 29 CANCELLED lifecycle | `Cancelled · work stopped` | Closed. |
| 30 header Source | exact Finding link or plain Incident plus `Open Site incidents` | Closed. |
| 31 record corrections | chain walk, earlier-versions disclosure | Closed. |
| 32 history labels | seven labels plus `Correction`, occurrence disclosure | Closed. |
| 33 operational `kind` | filter before count, card agrees | Closed. |
| 34 oprecords slots | footer literal, form removed | Closed. |
| 35 overflow | anywhere rule, panel scroll | Closed, measured (no document overflow after the rule). |
| 36 unmeasured cases | measure-2 | Closed by this run, except header cap (OI-5) and chips (OI-10). |

## Open items

### BLOCKER

**OI-1. Global incidents and maintenance sort order is undefined.** The spec gives a sort and tie-break only for plans and operational records (section 1: head `recorded_at desc, site_code_key, site_id, canonical_root_id`). For incidents and maintenance it names none, yet the cursor binds "last sort tuple" and A1 tests "same-time UUID tie". The merged Site list sorts by `occurred_at` (incident) or `created_at` (request), descending (`work/site_index.py:199-210`), and a cross-Site list needs a Site tiebreak. A builder must invent it. Fix: state the tuple, for example `(sort_time desc, site_code_key asc, site_id asc, case_id asc)`.

**OI-2. The Site Work strip and notice become false claims and their change is not owned.** `siteWorkCases.tsx:259-260` renders `Manage in Incidents · Not available yet` (and Maintenance) through `WORK_MANAGE_UNAVAILABLE_STATUS` (`:120`), and `WORK_CONTEXT_NOTICE` (`:118`) says "A global work page and create flow are not available yet." Once `/incidents` (A2) and `/maintenance` (B2) are live these are untrue. The spec says only "update reviewed `WORK_CONTEXT_NOTICE` and its exemption" in A2, with no replacement literal, and does not mention the strip. Tests pin the strings (`frontend/src/sites/__tests__/siteWorkCases.test.tsx:175,211,388,452`); that file is in no unit list, and B2 lists neither `siteWorkCases.tsx` nor `missing-claim-scan.mjs` although the Maintenance strip changes there. Both strings also have reviewed exemptions (`tools/checks/missing-claim-scan.mjs:70-82`). Fix: per unit (A2, B2), give the replacement strip text (link or still-unavailable for the create flow) and notice literal, and add the test file and the exemption edits to A2 and B2.

**OI-3. Detail wire time contradicts the "unchanged" nested body.** The spec keeps `work-case-detail-1` "unchanged as nested `work_detail`", but that body emits six-digit instants (`work/model.py:192` `iso`, used at `work/detail.py:75-98`: `2026-10-20T09:11:00.000000Z`). Section 1 says all instants use whole-second W3 form and the literal detail example prints `2026-10-20T09:11:00Z` inside `work_detail`, `events`, `history.revisions`. A test pinned to the example fails against the unchanged selector, and the `history.*` fields have no stated format. Fix: say nested `work_detail` keeps six digits (correct the example), and state the format of `selected.known_at`, `history.revisions[].*_at` and `history.operational_records[].*_at`. The format `As known at` shows after UI formatting is not affected.

**OI-5. Request header cap does not hold at 390 and is ambiguous.** See `W6-01-mock-measure-2.md`. The mock itself is 430 px at 390 for h1 + subtitle + `mheader` against a 390 cap; worst realistic `mheader` alone is 394; with a 200-char stored title the block is 363 at 1440 and 844 at 390 (cap 250). Fix: define the header as the h1 block plus `mheader` and set 380 / 860 (or clamp the h1 to three lines with a `Full title text` disclosure and cap the block near 380 / 600), and cap the `mheader` at 400 at 390.

### NOTE

**OI-4. B2 Preventive card is specified two ways.** Section 2 says the Preventive card is "plain text until B3"; the B2 card says the tab and card are `UnavailableEntry` with `Not available yet` and an `$expectedTabs` entry. `frontend/src/ui/UnavailableEntry.tsx` exports only `UnavailableTab` (a `li` in a tab row) and `UnavailableChip`. A card with its own "Not available yet" literal in `frontend/src/work/` fails the missing-claim scan (`/not available yet/i`, only the component file is exempt), and a tab plus a card could count twice in the guard's multiset (`navigation-truthfulness.ps1:752-831`). Rule the card as plain text without that phrase, or name the component, and say how many multiset entries B2 adds.

**OI-6. Fixture occurrence times and capture window are not given.** Write clocks are `11:59:00Z`-`12:00:02Z` on 22 Oct, but no fixture gives `occurred_at` values; the default window ends at today's 00:00 UTC, so a row occurring on the clock day is outside it, and captures run at real DB time on whatever day they are taken. The spec also never says the global pages read `from`, `to`, `known_at` from `location.search`, though its own links rely on it. Fix: occurrence offsets relative to `--clock` (for example 1 to 5 days earlier), and the page query contract; captures pass an explicit window.

**OI-7. Small undecided items in the read.** (a) Status when the scope is empty and `known_at` is explicit and earlier: `EMPTY_SCOPE` or `HISTORICAL`. (b) The selected-ID set for the `source_provenance` of preventive and operational rows (`basis_sha256` depends on it; the example shows UNKNOWN with `sha256:example`). (c) `ASSETOPS_WORK_CURSOR_KEY_HEX` is documented only by analogy; `backend/README-db.md:42-44` documents the estate key and is in no A1 list, nor is the test and capture environment that must set it.

**OI-8. Detail route wording.** Section 1 says `GET /api/work/requests/{case_id}` "remains the API path". No such route is merged: the merged detail is `GET /api/sites/{site_code}/work/cases/{case_id}` (`work_api.py:174`). C1 builds it new in `global_work_api.py`. Also the refusal table gives every route the 401 text `Sign in to read estate records.` while the merged work routes say `Sign in to read work.` (`work_api.py:74`). State the route as new and the 401 text per route.

**OI-9. Process gaps.** (a) Capture harness scripts, the evidence directory and review packets (the W4 pattern: `.agent/W4-01-evidence/{seed.py,capture.mjs}`) are in no unit list, although the lists are "exhaustive". (b) `P-work-cases` stays `pending owner`; the spec records the Architect recommendation as not owner accepted but does not state that building proceeds under it with merge conditional on the owner walkthrough (the owner-absent rule); say so in one sentence.

**OI-10. Chips and new controls have no cap.** The oprecords chip row is uncapped (mock 31 / 70; suggest 40 / 80). The new control bar, pager, status line, empty and refusal blocks cannot be measured on the mock and have no cap rows either; the first capture must measure and record them.

## Residual risk the spec does not name

- The measured caps assume every table cell is wrapped in a block that carries the three-line clamp; `line-clamp` on the `td` element itself does not work. Tests that only assert the class would miss it.
- Record panel row count is unbounded (no page size); only the vertical scroll rule bounds it.
- Measurement used my reading of the CSS rules; the A2 capture is the first proof against real markup.
