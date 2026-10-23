# W6-01e phase handoff (E1 operational read, E2 Operational records page)

Branch `task/W6-01e-operational-records`, cut from main `b362418b` (W6-01a and W6-01b merged). No code was written.

## Pre-flight

Dry-read against main, `task/W6-01c-request-overview` (built, unmerged) and `task/W6-01d-request-history` (plan only):
- `.agent/W6-01-build-spec.md`: §1 (operational row, Links), §2 `oprecords` rows, §3 E1/E2 cards, §3.1 G4/G6, F1–F6, A1Q2 R3, A2Q1–Q11, X1–X8, CL3-1/3/6/7, R5–R8, §4, the B1–B3, C1–C3 and C4 pre-flight rulings, the Codex retrospective, Q2, and the W6-01c M1 rulings;
- mock `frontend/mockups/v69/index.html:973-987` (`OPREC`, `opRows`, `opRecordsScreen`), `:672` (Evidence `Recurring evidence gaps`), `:1083` (`add('oprecords',…)`), and the `oprecords` entry in `screen-manifest.json:2205`;
- guards `configuration-persistence.ps1` rule 2/8 and HTTP scan, `navigation-truthfulness.ps1:544-556,665-704,755-758`, `navigation-rail-fixtures.ps1:80-95`, `missing-claim-scan.mjs:35-47`, `shell-overflow.ps1`, `site-substrate.ps1`, and `frontend/src/test/panelStructure.ts:48-202`.

Items marked **(blocking)** stop the named unit. The rest are literals a builder would otherwise invent.

### Base

- **P-E-0 (blocking): E1 and E2 depend on unmerged C1–C3 code.**
  - *Card:* "Each subsequent row consumes reviewed and merged predecessors."
  - *Reference:* only `task/W6-01c-request-overview` has these:
    - `Writer.post_operational_record` in `tools/w601_seed.py`;
    - the `SELECT[kind](…, cutoff)` 7-argument call in `global_index.py:423`;
    - `case_operational_records` in `postgres_global_read.py`;
    - the request-detail href builder;
    - `WorkRequestRecord.tsx`, which E2 must promote;
    - C2 changes to `globalWorkClient.ts`, `globalWork.css`, `App.tsx`, `operatorSiteRoutes.ts`, ledger and registry.
  - *Why open:* E1 would otherwise copy or collide with all of it. The pre-flight assumes E starts after W6-01c and W6-01d merge, then merges main again. Please confirm that ordering, and that E1 may reuse C1's `Writer.post_operational_record` and `_CASE_OPERATIONAL` root/head SQL shape rather than duplicate them.

### E1 — operational read

- **P-E1-1 (blocking): selector signature.**
  - *Card:* G4 and the E1 card require `select_operational(rx, tenant_id, sites, request, known_at)`.
  - *Code:* `global_index.py:376` `SELECT` calls `SELECT[kind](gx, tenant_id, sites, request.from_, request.to, k)`. On W6-01c the call adds a seventh `cutoff` argument. The first argument is the `GlobalReadTx` (`gx`), not a per-Site `_ReadTx` (`rx`).
  - *Why open:* the card's names and arity do not fit the dispatcher, and the kind filter must reach the selector. Give the literal signature, for example `select_operational(gx, tenant_id, sites, lo, hi, k, cutoff, kind)`, and say how `SELECT` passes `kind` (a lambda or an extra argument for every kind).

- **P-E1-2 (blocking): `kind` in the request, cursor and token.**
  - *Card:* §1 binds the "route, kind filter" in the cursor. Bad `kind` is `INVALID_CURSOR`; the default is `all`.
  - *Code:*
    - `GlobalWorkRequest` (`global_index.py:79-85`) has no filter field.
    - `KEYS` (`:42`) lacks `kind`.
    - The cursor key set already holds `"filter"` (`:52`). Decode requires `filter is None` (`:193`), and encode and token hard-code `None` (`:424`, `:442`).
    - `test_w601a_global_incidents.py:346-347` pins the exact cursor key set.
    - `test_w601a_global_incidents.py:462` requires `kind=all` on `/incidents` to stay `INVALID_CURSOR`.
  - *Why open:*
    - Should `filter` carry the kind string, with absent and `all` normalised to the same value? Or should `all` be `None`, so incident/maintenance/preventive cursors stay byte-identical?
    - What does a continuation page return when its `kind` differs from the cursor's: 409 `WORK_BASIS_CHANGED` or 422 `INVALID_CURSOR`?
    - Is an explicit `kind=all` admitted on page two when page one omitted it?

- **P-E1-3 (blocking): which version the filter and row fields read.**
  - *Card:* the E1 card says "full lineage, filter before `total_count`/cursor". The row has `kind` and `case_id`.
  - *Code:*
    - A correction re-supplies every key (`service.py:384-405`, `OPERATIONAL_KEYS :35-36`), so a head may change `kind` and `case_id`.
    - C1 admits request history by the **root** `case_id`, and shows the **head** `kind` (C1 ruling, "history.operational_records").
    - C3's REC link sends `kind={kind}` from that head.
  - *Why open:*
    - Filter on head `kind` (needed for C3's link to land on its row) or root `kind`?
    - Is the row `case_id`/`case_kind`/`case_code` the head's or the root's? If it is the head's, a corrected record can show a different case on E2 than in C1's request history.

- **P-E1-4: non-SUBMITTED state.**
  - *Card:* the row has `state:'SUBMITTED'`.
  - *Code:* schema `0027_w4_work_cases.py:174` allows `SUBMITTED|ACCEPTED|REJECTED`; the service always writes `SUBMITTED` (`service.py:496`). Preventive raises 503 on non-DRAFT (`global_index.py:343`).
  - *Why open:* a selected head that is not SUBMITTED needs a literal outcome. The builder would choose 503 by analogy, unless you rule otherwise.

- **P-E1-5: case resolution failure.**
  - *Card:* `case_kind`/`case_code` are given, with no source rule.
  - *Code:* `rx.case(case_id, K)` (`postgres_work_read.py:94-96`, `created_at <= :k`). The write checks the case exists in the same transaction (`service.py:486`), so `None` at K should be impossible.
  - *Why open:* confirm that a missing case is 503 `WORK_STORE_UNAVAILABLE`, not `case:null`.

- **P-E1-6 (blocking): `links.case` literals.**
  - *Card:* §1 says `case` "points to request detail only for MAINTENANCE_REQUEST after C2; INCIDENT points to the Site incidents window". X8 sets the label to `case_code`.
  - *Code:* there are three candidate rules:
    - case rows use the **global page window** plus response `known_at` (§3.1 Q8, `global_index.py:316-323`);
    - C1 `source_incident` uses the **incident root occurrence day** plus `known_at` only when explicit (`global_detail.py:41-45` on W6-01c);
    - request detail carries `known_at` only when explicit (P-C1-5). The §1 example and §1 text say `known_at={known_at}` unconditionally.
  - *Why open:* give the literal INCIDENT href (which window, and which `known_at` rule) and the literal request href (explicit-only or the response `known_at`). E2 renders whatever comes back.

- **P-E1-7: token basis fields.**
  - *Card:* A1Q2 R3 says any new row field derived from a stored value enters `basis`.
  - *Code:* the preventive basis is at `global_index.py:361-368`.
  - *Why open:* name the exact operational basis tuple. The proposal is:
    - `(site_id, canonical_record_id, head_id)`;
    - root `code` and `occurred_at`;
    - head `kind`, `body`, `occurred_at`, `recorded_at`, `period_end`, `actor_kind`, `actor_id`, `quantity`, `unit`, `source_document_sha256`, `case_id`, `state`, `supersedes_record_id`, `correction_reason`;
    - the resolved `case_kind` and `case_code`;
    - the selected source IDs.

    Confirm it is sorted by `(site_id, canonical_record_id)`.

- **P-E1-8: wire formats.**
  - *Card:* §1 says list instants are whole UTC seconds and "Decimal quantities are strings".
  - *Code:* P-B1-5 used `m.decimal_text` for `next_due_hours`. `period_end` is an instant with no stated precision.
  - *Why open:* confirm that `quantity` uses `m.decimal_text` and `period_end` uses whole-second `Z`.

- **P-E1-9 (blocking): the `operational` fixture has no recipe.**
  - *Card:* §4 lists `--fixture operational` ("extended B1/E1"). The E1 card names only the X2 `stress` OPERATOR_LOG. E2 needs positive (more than five rows for the pager), filtered, filtered-zero, historical, 503 and long-body captures.
  - *Code:* `tools/w601_seed.py:57-58` has no `operational` fixture. MANUAL_READING requires `quantity` and `unit` (`service.py:468`). Occurrence must be within 30 days of the write clock (`model.py:236-240`).
  - *Why open:* give the literal recipe:
    - Sites and tenant, including an excluded other-tenant row;
    - row count per kind, with one kind absent for the filtered-zero capture;
    - bodies;
    - MANUAL_READING `quantity`/`unit`;
    - which rows name an INCIDENT and which name a MAINTENANCE_REQUEST, which also requires creating those cases;
    - one correction for historical, with its reason and its clocks relative to the existing `historical` +1s…+4s writes, or a new owner if it goes in `historical`;
    - the `--clock`. A2Q3 says `2026-10-21T12:00:00Z` and window 14..21 for list captures; B1 used `2026-10-20T12:00:00Z` (P-B1-1).

    Also give the `stress` OPERATOR_LOG's Site, case (if any) and occurrence.

- **P-E1-10: focused test names.**
  - *Card:* E1 lists topics only ("four kinds, correction root/head, case_id, scope, 31-day window, HMAC/filter/count, 503").
  - *Why open:* B1 and C1 were given literal test names, and E1 has none. The builder will name them, for example `test_kind_filter_before_count_and_cursor`, `test_correction_head_keeps_root_window`, `test_kind_cursor_mismatch` and `test_case_link_by_kind`, unless you rule.

- **Guard note (not open):** `operational_index.py` must not contain `open(` in any form, including comments and names like `reopen(`. `postgres_global_read.py` stays SELECT-only. The E1 card already excludes guard, composition and `main.py` edits.

### E2 — Operational records page

- **P-E2-1 (blocking): `kind` is dropped by the shared parts, and those parts are not on E2's list.**
  - *Card:* A2Q10 lets E2 read `kind`. CL3-6 says a chip resets the trail. The E2 Lane B list has `globalWorkClient.ts` but not `globalWorkParts.tsx`, which B2 owns and C2 keeps import-only.
  - *Code:*
    - `GlobalWorkQuery` (`globalWorkClient.ts:141-146`), `globalWorkApiQuery` (`:209-215`), `globalWorkPageQuery` (`:276-298`) and `globalWorkHref` (`:301-306`) carry only `from/to/known_at/cursor`.
    - `useGlobalWorkPage` (`globalWorkParts.tsx:243,264-270`) builds Show, Reload, pager and first-page hrefs through them, so `kind` is lost on every navigation.
  - *Why open:* either add `globalWorkParts.tsx` and the three existing page tests that assert its behaviour to E2 Lane B, or rule a local wrapper in `OperationalRecords.tsx`. Also name the client method: optional `operationalRecords?(q)` per the P-B2-1 pattern, and `GlobalOperationalRow`/`GlobalOperationalBody` types.

- **P-E2-2: kind chip form (unlabelled change).**
  - *Card:* CL3-6 says the chips are "live" and "the `All` chip href drops `kind`", so they are links.
  - *Mock:* `<div class="chips"><button class="chip active" data-rec-type>` (`index.html:984`).
  - *Code:* the link-chip precedent is `estate/findingIndex.tsx:184` `StateChips` (`ul.v69-chips > li > Link.v69-chip[aria-current]`). `panelStructure.ts:57` admits `.v69-chips` before panel 1. `UnavailableChip` must not be used, because it counts into `$expectedChips`.
  - *Why open:*
    - Confirm links in `.v69-chips`, and whether buttons becoming links needs a `MOCK DEVIATION` label.
    - On the invalid-`kind` state, do the chips keep `from/to/known_at`?
    - Where does `Choose a supported record type.` sit: a `RefusalBlock` with `data-page-refusal`, cards hidden?

- **P-E2-3: card notes and tone differ from the mock with no `MOCK DEVIATION` label.**
  - *Card:* §2 gives values `{total_count}`, `Not established`, `No review workflow`, `Not recorded`. Its notes are `Authored records only`, `No accepted-evidence publication link`, `All stored records are Submitted` and `Requests are not OperationalRecord rows`.
  - *Mock:* notes `Logs, readings, notes and visits`, `Labelled Operator record where used`, `REC-321`, `Closing fuel dip · stock in chamber`, with the fourth card amber (`index.html:983`).
  - *Why open:*
    - The B3 precedent (P-B3-3) kept the mock headings and tone and labelled each changed value. The first mock note is truthful as it stands, yet §2 replaces it.
    - `Requests are not OperationalRecord rows` uses a model name, against the owner's no-system-vocabulary rule.
    - The fourth card's amber tone is unruled.

    Give the final notes and tones, with labels where they deviate.

- **P-E2-4: panel description differs from the mock with no label.**
  - *Card:* §2 footer `Authored records and the cases they name; evidence acceptance is separate.` (A2Q7 puts it in Panel `description`).
  - *Mock:* `What people on site recorded, and the evidence each one feeds`.
  - *Why open:* B2 kept its exact mock footer. Either keep the mock sub-line, or label this replacement.

- **P-E2-5 (blocking): `Record a manual reading` panel structure.**
  - *Card:* §2 says "Replace form with `Recording requires an authorized work service.` and `Manual readings cannot be submitted from this page.` Remove mock `Fills REC-307 when submitted`."
  - *Mock:* a form with Site, Reading, Value and Taken at fields plus a `Submit for review` button, and sub-line `Fills REC-307 when submitted` (`index.html:986`).
  - *Why open:*
    - Removing the form is a mock-element removal and carries no `MOCK DEVIATION` label.
    - The owner rule says to "show an honest gap inside the mock's own structure", for example inert fields with an `UnavailableInline` submit.
    - The description slot is unruled: empty, or one of the two sentences?

    Rule the form treatment, and the element each sentence occupies.

- **P-E2-6: `How records are used` copy.**
  - *Card:* §2 gives one sentence: `People can author records. They remain separate from accepted equipment readings and do not fill missing evidence.`
  - *Mock:* two paragraphs, the first with a bold `Operator record` label, the second `A requested record that is never taken stays a visible gap; it is not filled in.`
  - *Why open:* is this a replacement of both paragraphs, and is it labelled? The second mock paragraph describes requested records, which do not exist.

- **P-E2-7: header literals are missing.**
  - *Card:* none. For comparison, B2 had P-B2-9 and C2 had its header ruling.
  - *Mock:* h1 `Operational records`, subtitle `Operator logs, manual readings, shift notes and site visits`, section `''`, no tab row.
  - *Why open:* give the breadcrumb (plain `Operational records`?), h1, subtitle, root `data-global-work-root="operational-records"`, CSS modifier (`.global-work--oprecords`?) and the `GlobalWorkBar` aria labels (`Operational records window` / `Operational records pages`?).

- **P-E2-8: table cell gaps.**
  - *Card:* X8.
  - *Mock:*
    - Type is plain text.
    - State is a `badge` (blue unless Accepted or Requested).
    - What it says includes the reading value (`198 L`).
    - Feeds is `{text} →`.
  - *Why open:*
    - Type: plain text, or a chip?
    - State tone for `Submitted`: blue, as in the mock?
    - Is MANUAL_READING `quantity unit` (and `period_end`) shown anywhere? The row carries them, and nothing renders them.
    - Does the Record cell show `Correction: {correction_reason}` plus a `<details>` with `supersedes_record_id`, as B3 does for plans? Without it, the historical capture cannot show which head is selected.
    - Feeds arrow: yes or no?
    - The column `minWidth` map for the 650/780 cap is missing (B2 had one).
    - By shows `actor_id` (`service:w401-fixture`) where the mock shows role names. Is this covered by the retrospective's "stored IDs replace illustrative mock values"?

- **P-E2-9: EstateEvidence `Operational records →`.**
  - *Card:* the Codex retrospective adds `frontend/src/estate/EstateEvidence.tsx` and `estateEvidence.test.tsx` to E2 Lane A, with `estateHref('/operational-records', query)`.
  - *Code:* B3 built the Preventive link from the response window, falling back to the query, with `known_at` only when explicit (`EstateEvidence.tsx:359-370`). The Operational records item is `UnavailableLinkEntry` (`:374`). `estateEvidence.test.tsx:308` loops over three unavailable labels, and `:317` expects one link.
  - *Why open:*
    - Confirm the B3 effective-window form, not the retrospective's bare `query`.
    - Confirm the test deltas: two unavailable labels and two links.
    - Name the fixture and window for the Evidence-root 1440/390 capture.

- **P-E2-10 (blocking): C3 REC promotion literals.**
  - *Card:* P-C3-4 says "E2 Lane A additionally owns `WorkRequestRecord.tsx`, `workRequestRecord.test.tsx` and the `wr-record` ledger interaction".
  - *Code (W6-01c):*
    - `WorkRequestRecord.tsx:35` `REC_PAGE_PREPARED` and `:210-224` `RecordNotice` render plain text.
    - The header comment `:12-15` carries the deviation.
    - `workRequestRecord.test.tsx:231-251` assert there is no `/operational-records` anchor.
  - *Why open:*
    - (a) The final `wr-record` ledger `interaction` literal is not given; the interim is `Linked REC codes are shown; the Operational records page opens after W6-01e.`.
    - (b) Confirm that the REC href carries `known_at` only when the page URL was explicit, per P-C1-5. That supersedes CL3-3's `known_at={selected.known_at}`.
    - (c) Confirm that `REC_PAGE_PREPARED` and the header deviation comment are removed.
    - (d) Does `linked_rec_filtered_window_href` already exist on C3, or does E2 add it?
    - (e) Is a `wr-record` recapture with live REC anchors required, using C `detail` at `--clock 2026-10-20T12:00:00Z` and window `[2026-10-18,2026-10-19)`?

    This also depends on P-E1-3: the filter must match the head `kind` in the link.

- **P-E2-11: rail-test literals outside A2Q11.**
  - *Card:* the E2 card plus A2Q11 give the E2 row. The A2Q11 line numbers have drifted.
  - *Code:*
    - `operatorRailInventory.test.tsx`: `UNAVAILABLE_ROOTS` `:28-32` becomes `["Assets","Settings"]`; "exactly eight links" `:93/:101-111` becomes nine; focus-order lists at `:181` and `:208`.
    - `operatorRouteFrames.test.tsx:222-231,273`.
    - `w301EstateShellRoutes.test.tsx:159-168`.
    - `estatePortfolioRoutes.test.tsx:67` becomes `["Assets","Settings"]`.
    - The A2Q11 files sit at `simulatorLabWorkspaceEntryPoint:51`, `siteDetailRoute:105,448`, `siteFoundationRoute:128,135,472`, `sitesIndexRoute:60`, `operatorSiteTabs:388` and `sharedVisualVocabulary:151,209`.
  - *Why open:* the edits are mechanical. Confirm that the focus-order lists and the nine-link count follow the E2 rail order, with no other change. K4a is **not merged** (no `activeLabel` in `frontend/src`). If it merges first, E2 preserves it as the card says.

- **P-E2-12 (blocking): capture matrix and clock.**
  - *Card:* the E2 card lists positive, zero, filtered, historical, read-503 and long body. The retrospective adds Evidence-root. P-E2-10(e) may add `wr-record`. CL3-6 adds an invalid-`kind` state and A2Q6 a cursor-change state, neither listed.
  - *Why open:*
    - Give the full capture list.
    - Give the clock and window: A2Q3 `2026-10-21`/14..21, or the B1 `2026-10-20` clock with 14..21.
    - Name which fixture feeds each capture; this follows P-E1-9.

- **Guard notes (not open):** none of the 13 §2/CL3 E2 strings matches `missing-claim-scan.mjs` PATTERNS. Avoid any note shaped "reading… not assessed". There must be no bare `<table` or `<svg`, and no `type Site…Record`/`Row` name in `frontend/src/work/`. `expectV69Panels("oprecords")` requires exactly `Operational records`, `Record a manual reading` and `How records are used` as `h2` panels, with chips in `.v69-chips` before panel 1. Navigation: `$expected` line 552 becomes `live|Operational records|WORK|/operational-records`, and three W6-01e cases go into `navigation-rail-fixtures.ps1`; the `label typo` case still anchors. No `$expectedTabs` change.

### Summary

There are 22 items: P-E-0, P-E1-1…10 and P-E2-1…12. Ten are blocking: P-E-0, P-E1-1, P-E1-2, P-E1-3, P-E1-6, P-E1-9, P-E2-1, P-E2-5, P-E2-10 and P-E2-12. Unlabelled mock departures are P-E2-2 through P-E2-6 and P-E2-8. The builder waits for the rulings to merge before writing code.
