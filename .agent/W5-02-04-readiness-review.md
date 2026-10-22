# W5-02 / W5-04 build-spec readiness review

Reviewer: fresh independent Claude reviewer, 2026-10-22, read only on `main` at `59c2ca89`.
Gate: `.ai/ROLE_CONFIG.md` "Build-Spec Readiness Gate For W5 And W6", "W3/W4 lessons applied to W5 and W6" (rules 1-7) and the 2026-10-22 mock-fidelity rule.
Inputs: `.agent/W5-02-build-spec.md`, `.agent/W5-04-build-spec.md`, `tasks/W5-02-cold-work.md`, `tasks/W5-04-ev-work.md`, `D-2026-10-22-w5-02-w5-04-buildspec`, v69 `screens.js` (`siteWorkScreen`, `SITE_WORK`, `WORK_EMPTY`, `cold-action`, `ev-action`), `.agent/W5-02-04-mock-measurements.md` and `.agent/W5-02-04-mock-shots/`.
Code read against: `frontend/src/sites/{SiteWorkActions.tsx,siteWorkCases.tsx,SiteAction.tsx,actionIndexClient.ts,workClient.ts}`, `frontend/src/shell/{SiteAnalyticsFrames.tsx,operatorSiteRoutes.ts,operatorSiteTabs.tsx}`, `frontend/src/App.tsx`, `backend/assetops_backend/work/{site_index.py,model.py,detail.py}`, `work_api.py`, `actions/adapters/postgres_action_store.py`, `migrations/versions/0016_action_store.py`, `tools/checks/{configuration-persistence.ps1,missing-claim-scan.mjs,navigation-truthfulness.ps1,shell-overflow.ps1}`, `.agent/W6-01-build-spec.md` A2/B2, `.agent/W5-03-build-spec.md` E1, `config/scenarios/cold-backup-failed.yaml`.
No checks were run. This is a spec dry-read; nothing was built.

## Verdict: NOT READY

The backend contract is detailed. The spec still leaves a builder to decide the following: how the shared W1 and W4 components choose cold or EV copy, how the Action route tells a domain Action from a battery Action, how the W4 link wire carries a domain Action, the fixture clock, and the time-shift producer. Several literals have no wire source, the Finding code and the criterion summary among them. Three departures from the mock are unlabelled, and one labelled deviation is not shown to be unavoidable. W5-02 has 33 gaps and W5-04 adds 12 of its own. W5-04 also inherits every shared W5-02 gap, because V1-V4 reuse the K1-K4 contract.

## A. W5-02 (and shared contract consumed by W5-04)

### Backend K1

1. **K1, test file list.** `backend/tests/test_w4_work_{site_index,detail}.py` do not exist. These existing tests will be touched or broken and are not named: `test_w401_site_indexes_postgres.py`, `test_w401_work_read_postgres.py`, `test_w401_work_api.py`, `test_w401_work_service_postgres.py` and `test_w403_work_links_postgres.py`, all by the W4 link union, plus `test_s6_site_action_index{,_postgres}.py` by the W1 writer change. Name each file and the assertion that changes.
2. **K1, rule-8 registration literals.** The card only says "rule-8 INSERT-only corpus/allowlist". These are missing: the writer variable and path (is `adapters/postgres_domain_intent.py` the writer of all three tables, including `domain_action_case_link`?); its `$pgWriters`, `$pgWritesSeen` and `$pgDriverSeen` entries; the owned-table list with the INSERT-only check and per-table anti-vacuity; and the probe names in `tools/writer_guard_probes.py`, which is not in the file list. `adapters/postgres_domain_action_index.py` needs a `$pgReaders` line, which is not stated. `domain_work_api.py` lacks the HTTP-scan token sentence (no `register_publication` ... `runs.source_publication`), which is the A1Q W5S-9 class.
3. **K1, `action_code` format and collision.** The domain `action_code` format is not given. W1 enforces `CHECK (action_code ~ '^ACT-[0-9]{6,}$')`, so state whether the domain code uses the same format and CHECK. "W1's writer must reject a code already in `domain_action` if sequence allocation is ever bypassed" is conditional. State whether K1 changes `postgres_action_store.py` and adds a test, or whether a 0033 trigger on the W1 `action` table does it. The file list implies the writer; the sentence implies neither.
4. **K1, domain Action in the W4 `Link` shape.** W4 `_action_link` returns `{action_id, action_event_id, label: "Action {id[:8]}", href: selected_action_links(...)}`. Its lineage and fence come from the W1 Action fence (`sai1`, `link_fence`, `link_selections` with kind `ACTION`). These are not specified for a domain link: `action_event_id` (null?), `label` (the code or `Action {id8}`), `href` (which route), the link lineage state, the fence token, and their effect on the list `status`, `selection_token` and cursor. `work/link_coverage.py` and the W3 closure-2 case selected-ID and citation set (`case_basis`) are also affected. Neither is in the file list.
5. **K1, cold selection reads.** "The caller-connection repeatable-read adapter selects exact Finding, W4 case/record and W5-01 cold evidence" names no method. Adapter isolation forbids the work adapter from importing analytics adapters. Name the read: either SQL inside `postgres_work_read.py`/`postgres_domain_intent.py` against named tables, or an injected `ColdReadService` method wired through `work/composition.py`. W5-01b (`0032`) is not on main, so its table and method names cannot be checked yet.
6. **K1, union index DTO values.** The keys are listed, but these values are not:
   - the index `status` enum and how it is computed for a union of battery and domain rows;
   - the `coverage.state` and `coverage.reason` values, and the `window.bounds` literal;
   - the `origin.label` literal, the `origin.href` format and the `links.action`/`links.history` formats for each kind;
   - the type of row `state`: the W1 state object, or the string `OPEN`;
   - the type and content of `criterion_summary`. The cold spec gives no literal; the mock shows `Start requested → generator runs → power → cooling`.
7. **K1, union index validation and refusals.** These are missing:
   - the window rule: whole UTC days or any instants, and the maximum span, which is 31 days in both W1 and W4;
   - `INVALID_WINDOW`, `INVALID_LIMIT` and `INVALID_CURSOR` and their messages. The refusal order lists only the intent codes.
8. **K1, command validation.** These are missing:
   - the maximum lengths of `title` and `owner_label`, which the 160-character caps need;
   - the `due_at` bounds and the `declared_at` bounds;
   - the code for the same idempotency key with a different body on Action create and on case-link;
   - the `ACTION_NOT_FOUND` message literal;
   - an explicit code-to-message map for the four cold messages, which is currently implied by order only.
9. **K1, the detail read DTO cannot feed the Action page.** The Related activity sentence needs the WR code and the `COMPLETED` request state and needs to know that a record exists. `domain-action-intent-read-1` carries only `links.work:{label,href}`. These are also missing:
   - the `links.work` target. W6 request detail is not mounted; is it the Site Maintenance tab?
   - which case link is used when there are several;
   - the content of `results[].evidence_ids`;
   - the `source_provenance` ID sets;
   - the rule that chooses `PENDING_RECOMPUTE`, `STALE_SOURCE` or `UNKNOWN`, and which selected source drives it.
10. **K1, unit size (rule 8).** K1 carries all of the following: a migration with three tables, three commands, a detail read, a union index, the W4 adapter union, a W1 writer change, the producer and guard registration. That will not fit one builder run of at most three commits with a reading index of at most four sections. Split it, for example K1a storage, commands and guard; K1b detail read and union index; K1c W4 link union and producer.

### Frontend K2 (Site Actions tab)

11. **K2, branching key for shared copy.** `SiteWorkActions.tsx` serves mini-grid as well. The spec says "no globally changed mini-grid label" but never says what selects the cold copy (`site_type`, row `domain`, or a separate component), or what `coldWorkPresentation.ts` owns as opposed to `SiteWorkActions.tsx`. Each existing literal that conflicts needs a rule:
    - `{code} · Battery reserve trial`;
    - owner `Not recorded` against `Not assigned`;
    - criterion `Not recorded` against `No success criterion declared`;
    - the strip `N Actions created {days}` with the `Read …` item;
    - the empty state `No Actions created at this site in this window` against `No actions at this site`;
    - the notice `Opening an Action moves you to its own page; …` against `Opening a record moves you to its own area; …`;
    - the per-status refusal titles against `Cold work unavailable` with `Retry`.
12. **K2, existing fields with no union source.** The current strip, the `Basis` disclosure and the State cell read fields the union envelope does not have: `read_at`, `fence.*`, `order`, `selection`, `not_included`, `window.membership`, row `selected_event` and `created_at`. State whether the "What this list is based on" disclosure, the `Latest step:` subline and `Read {time}` are dropped, mapped or replaced for cold rows.
13. **K2, paging and default window.** The union default `limit` is 5. The existing UI folds at 4 rows (`SITE_WORK_VISIBLE_ROWS`) with `Show all N Actions`, `First page` and `Next page`. These are missing: the page size the cold page requests, the fold rule, and the default window for cold Actions. The current code shows a choose-window state and reads nothing; W5-04 says "retains its explicit selected window" and W5-02 says nothing.
14. **K2/K3, counts and subtab query.** `useWorkCounts` reads W1 `/action-index` and W4 lists with `knownAt: null`, and the `WORK_SUBTABS` hrefs carry no query. The spec requires the union count and the same `[from,to)` and `known_at` on all three tabs, but assigns no unit to change `useWorkCounts` or `WORK_SUBTABS`. K2's historical capture needs `known_at` in `workScopeFromQuery`, which has none today.
15. **K2, the pre-K4 placeholder.** `Action details are being prepared.` must appear on a domain Action href, but K2 has no domain read client (`domainActionClient.ts` arrives in K4). `SiteActionFrame` today calls the W1 `SiteAction` for every ID. Missing: how K2 detects a domain ID, and what title, breadcrumb and tabs surround the placeholder.

### Frontend K4 (Action page)

16. **K4, dispatch on the shared route.** Missing: the discriminator between a domain Action and a W1 battery Action on `/sites/{site}/actions/{id}`. Options are to try the domain read and fall back to W1 on 404, to add a URL marker, or to use the index href. Also missing: which path is canonical (`/actions/{id}` or `/actions/{id}/verification`), and what each of the six W1 sections (`overview`, `plan`, `execution`, `evidence`, `verification`, `history`) renders for a domain ID. Each reads the battery API and would refuse.
17. **K4, contradictory frame literals.** The ledger row fixes the breadcrumb as `Actions › {code} › Verification · site: {site}`. M3 says the existing Site breadcrumb stays, and that breadcrumb is `Sites › {site} › Findings › Action`. The existing top `OperatorSiteTabs` current is `Findings`. These are also unmapped:
    - the page subtitle: the existing `{site} · an action raised from a finding` against the mock question line;
    - the mock `Open site` header button;
    - the rail item: Actions current in the mock;
    - the `Open` chip tone.
18. **K4, the status-strip subtitle.** `{owner} · {site} · {selected Finding code}` has no literal for a null owner. No source exists for a Finding code: W1 and W4 have no Finding code column, and W4 labels a Finding `Finding {id8}`. The mock's `F-118` cannot be produced. Rule the label, and label it as a MOCK DEVIATION if it differs from the mock.
19. **K4, Related activity.** `Inspect maintenance evidence` is a button in the mock that opens `workverification`. The spec calls it a link and names no target before or after W6-01 B-units.
20. **K4, empty intent.** "Current-result cells are absent" is ambiguous. With `intent:null` there are no criterion rows, so the spec must say whether the table is absent or present as a two-column table, and where `No outcome criteria have been declared for this Action.` sits.
21. **K4, display literals.** The `NOT_TESTED`, `NOT_ESTABLISHED` and `PENDING` labels (`Not tested`, `Not established`, `Pending`) are implied by the mock but not written down. The due date format and time zone for the `Due` cell are not stated.
22. **K4, file list.** `frontend/src/sites/domainActionGraphics.tsx` is listed, but the card says the screen needs no graphic. Remove it; otherwise it needs svg rule-5 registration in `shell-overflow.ps1`.

### Frontend K3 (Incidents and Maintenance tabs)

23. **K3, conflict with W6-01 over shared copy.** W6-01 A2/B2 (Lane A) rewrite `WORK_CONTEXT_NOTICE` in `siteWorkCases.tsx` to different literals, together with the strip Manage text and their exact `missing-claim-scan.mjs` exemptions. W5-02 instead sets the notice to `Opening a record moves you to its own area; the breadcrumb keeps this site.` It does not say:
    - whether that replaces the shared const for every Site type or adds a cold/EV-only const;
    - how the reviewed `WORK_CONTEXT_NOTICE` exemption is edited;
    - how the edit is ordered against W6 A2/B2.

    The same applies to the strip middle item. The spec wants `Same records and states as the global … list` in place of the existing `WORK_STRIP_DETAIL` `These are work records at this site`. That sentence is untrue while no global root exists.
24. **K3, currentness placement.** Today the W4 list status (`Read as of …`, `Linked evidence is being reassessed`, `No selected source for linked evidence`) is a strip label. The spec adds a separate notice below the strip with different sentences. It does not say whether this applies to all Site types, which would change the mini-grid W4 tests, or only to cold/EV, nor whether the strip label is removed.
25. **K3, case cells.** W4 rows always carry `url: null`, so the spec must say what the case cell links to before and after the W6 detail routes, naming the route constant. `Window` uses `eatWindowText`, which is hard-coded to UTC+3, while the spec says "Site timezone label" with no Site time-zone source. `asset_label` is `{asset_code} · {asset_type}` with the raw enum, against the mock's `GEN-CR-01 · backup generator`. `next_evidence_copy` is the constant `No next evidence recorded`, against the mock's `Witnessed automatic-start test`; that is an honest gap, but it needs a `mock_gaps` entry or a capture note.
26. **K3, routing edits.** "K3 changes routing" and the `App.tsx`/`operatorSiteRoutes.ts` entries do not enumerate any change. The Work routes already render every Site type. List the exact constants and hrefs.

### Shared ownership, registry and producer

27. **K2/K3/K4, existing frontend tests omitted.** `sites/__tests__/siteWorkActions.test.tsx` and `w1f4ChangesWorkStructure.test.tsx` (K2/K3), `siteAction.test.tsx`, `w1f4ActionStructure.test.tsx`, `siteActionVerification.test.tsx` and `w1f4VerificationStructure.test.tsx` (K4), and `shell/__tests__/operatorRouteFrames.test.tsx` and `siteDetailRoute.test.tsx` (route changes) are not listed.
28. **K3/K4, registry and ledger literals.** These need literal text, as W5-01 closure 2 required for its units:
    - the `v69-screen-ledger.json` rows for `cold-work`, `cold-work-incidents`, `cold-work-maintenance` and `cold-action`, all currently `coverage:"deferred"`: their `coverage`, `task`, `data_owner`, `supported_claim` and `unresolved_panels`;
    - the registry node edits: `A-cold-work-projections` and `A-ev-work-projections` are open;
    - `P-work-cases`, which governs `cold-work-incidents`, `cold-work-maintenance` and the EV equivalents and is W6-owned; its owner is unstated.

    K2 renders `cold-work` live while its ledger row stays deferred until K3. State whether that is allowed.
29. **K1/K5, the time-shifted cold producer is not traced (rule 3).** The W2 cold source is the registered `config/scenarios/cold-backup-failed.yaml`, with fixed `start: '2026-10-06T19:00:00Z'` and pinned version and SHA. No existing path replays it at `[D+19h,D+20h)` through ordinary ingestion while shifting Foundation effective times. The spec calls this a "new mode" but does not design it: a generated scenario or a run override, how the Foundation is republished, and which call returns `K0`. Rule this before K1 or choose another anchor. The 30-day W4 backdate limit from 2026-10-06 runs out on 2026-11-05.
30. **K1/K5, producer payload literals.** None of these are given: the Action `title`, `owner_label` and `due_at`; the INC/WR `title`, `narrative`, asset, `activity` and `outcome_note`; the intent basis IDs. Without them the capture content cannot be checked against the mock: `Witness automatic-start test`, `Maintenance lead`, `Backup response failure`, `Grid lost, automatic start failed, chamber above policy`, `Starter and control inspection`.
31. **K2-K4, producers for distinct states.** These are missing: separate producers for `PENDING_RECOMPUTE`, `STALE_SOURCE` and `UNKNOWN` ("late accepted cold evidence advances to K3 for pending/stale tests" does not say which state results), and the producer for the 503 capture.
32. **All pages, worst-case slots (rule 2).** "Full long text available by wrap/disclosure" leaves the choice per slot to the builder. No input maximum lengths are set (see 8), and the measurement file has no worst-case 390 px measurements.
33. **K2/K4, unlabelled mock departures.** These are High under the mock-fidelity rule:
    - (a) The Actions empty body. The mock has `No accepted recommendation or evidence request has been raised here yet.`; the spec has `No Action was created here in the selected window.`
    - (b) Related activity. The mock has `Starter/control inspection WR-019 is complete. …`; the spec drops the WR title (`{WR code} is complete. …`). A mock-faithful alternative is `{WR title} {WR code} is complete. …`.
    - (c) The Finding code label (item 18).

## B. W5-04 (EV-specific, in addition to items 1-32)

34. **V1/V5, clock conflict (rule 4).** W5-03 E1 pins the EV selection to `EvReplayBuilder.decision_clock` 2026-10-06T09:00/09:05, with window `[08:00,09:00)` and `cutoff` later than the watermark refused as 422 `EV_TIME_INVALID`. W5-04 instead shifts EV to `[D+8h,D+16h)` "through ordinary ingestion", while domain Action `recorded_at` and `K1`/`K2` are DB wall time. The intent detail read at `known_at=K2` must select W5-03 sessions. The spec does not decide which clock governs, or how a session selection is read at a wall-clock cutoff. The shifted EV replay has no existing path: `config/scenarios/ev-fault.yaml` and the others have fixed dates.
35. **V2, criterion summary.** `Complete a witnessed charging session; no repeat fault` has no wire source: it is not in the intent body and no derivation rule exists. It also differs from the mock `A complete witnessed session and no repeat fault`, and that difference is an unlabelled deviation.
36. **V2, client and presenter ownership.** K2 puts the union read in `actionIndexClient.ts`/`coldWorkClient.ts`; V2 names `actionIndexClient.ts` and `domainActionClient.ts`, which is created in K4. Missing: which module holds the union read and validator, the split between `evWorkPresentation.ts` and `coldWorkPresentation.ts`, and the branching key (shared with item 11).
37. **V4, status chip.** "Status chip actual W1 state" is wrong for a domain Action, which has no W1 state; its state is the domain `OPEN`. The null-owner literal for `{owner} · {site}` is also missing.
38. **V1, session basis validation.** The read method that resolves "public selected W2/W5-03 session at the cutoff" is not named. Missing: whether `session_ids` may be empty, and the refusal for a session at another Site.
39. **V1, the criterion-length DB check.** V1 "alters the intent's criterion-length DB check from exactly four", but K1 defines no DB check, only service validation. Fix the check's name and expression in K1, or drop the V1 alteration.
40. **V1, conditional file and broken tests.** "`main.py` only if K1's router mount needs EV registration" is conditional; decide it. The K1 tests that assert the cold-only CHECK (`test_w502_domain_intent_postgres.py`) are not listed. Neither is the downgrade-with-EV-rows test.
41. **V3, submitted-case mode literals.** Missing: the Incident and WR title, narrative, asset, activity and outcome note for mode `K4`, and whether both an Incident and a WR are submitted.
42. **V2/V3/V4, refusal surface.** `EV work unavailable` with `Retry` against the preserved W4 refusal constants: which page uses which (shared with item 11).
43. **V4, Action page frame.** It inherits items 16-17. The `ev-action` mock is a global-Actions screen with one `Verification` tab, the `Open site` button and the breadcrumb `Actions › ACT-061 › Verification · site: …`.
44. **V2/V3, notice and strip.** These inherit the W6-01 conflict in items 23-24 for EV Sites.
45. **V5, registry and ledger.** The `ev-work*` and `ev-action` ledger rows and `A-ev-work-projections` have no literal edits (shared with item 28).

## C. The 8 labelled MOCK DEVIATIONs

| ID | Ruling | Reason |
| --- | --- | --- |
| M1 (Due-date note) | **Challenged, avoidable** | The mock note is the panel subtitle, under the heading; the existing code renders it as a footer `ChartNote`, and the slot is not stated. A mock-faithful alternative was not considered: render `Due dates are not yet set` when no row on the page has `due_at`, which is the fixture state, and omit it otherwise. Only "in this example" is mock prose. |
| M2 / E1 (global create promise) | Accepted, unavoidable | No user create flow exists, and both alternatives are dishonest. The notice literal still conflicts with W6-01's `WORK_CONTEXT_NOTICE` plan (item 23). |
| M3 / E2 (W1 Action tabs and Site breadcrumb kept) | **Challenged, avoidable** | The stated reason is false for a domain Action. The W1 Plan, Application, Evidence and History sections read the battery-only Action API, so a domain ID has nothing there to strand; they would show refusals. The mock-faithful alternative is a single `Verification` section with the mock breadcrumb, `Open site` button and status strip, using the existing `Breadcrumbs`/`PageHeader` primitives. It also removes the contradiction in item 17. |
| M4 / E4 (global Actions parity) | Accepted in principle | The W3 global Actions root reads only the W1 `action` table. However, "the explicit domain-limited sentence" is never given as a literal, and the ledger's "Three scope strips" row still says `Same records and states as the global Actions list` / `Manage in Actions →` "only if mounted". `ACTIONS_PATH` is mounted, so a builder following the ledger would render the link M4 forbids. Give the literal and fix the ledger row. |
| E3 (`Pending` cells) | Not a deviation | It renders exactly what the mock shows. Relabel it as a sourcing note. |

These unlabelled departures count as High: items 33(a)-(c) and 35, plus the unmapped `Open site` button, page subtitle and rail state on both Action screens (items 17 and 43).

## D. Preconditions, not gaps

- `0032_w5_cold_scenarios` (W5-01b) and `0034_w5_ev_scenarios` (W5-03b) are not on main. Both specs correctly abort until their exact parent merges.
- W6-01 A2/B2 has not merged. Item 23 requires an explicit order between the two slices.

## Recheck (2026-10-22, against `537667b8`)

This recheck reads the closure contracts, the current unit cards (K1a-K5 and V1a-V5) and the closure maps in both specs against main. It was read only, and no checks were run. Where a closure names code, I confirmed it exists: `link_coverage.coverage_of`/`worst`/`_PRECEDENCE`/`_REASON`, `EvReadService.sessions_on`/`findings_on`/`_snapshot`, the existing `cold_snapshot` injection into `postgres_work_read.py`, `case_basis` in `work/service.py`, and the W6-01 unit table.

### Verdict: NOT READY (four Medium items; 29 and 34 deferred)

All 45 original gaps are closed or deferred: 29 and 34 can only be verified after W5-01b and W5-03b merge. The new text introduces four Medium items that a builder would hit, plus some Lows. Each Medium needs a one-line Architect ruling.

### Closure table

| Gap | Status | Note |
| --- | --- | --- |
| 1 | Closed | K1a/K1c name the S6 and W4 tests and the assertions that change. |
| 2 | Closed | `$domainIntentWriter`, `$pgWriters`/`$pgWritesSeen`/`$pgDriverSeen`, `$pgReaders`, the three tables and the four probes are all given. The HTTP-scan token list is partial, but "none of the forbidden tokens" is binding (Low). |
| 3 | Closed except for one point | The grammar and two-way triggers are fixed. See R-4: the W1 "existing code-collision refusal" does not exist. |
| 4 | Closed | `DOMAIN_ACTION` link kind, `action_event_id:null`, label, href, fence and token. See R-5 for the W6 seam. |
| 5 | Closed | The injected `ColdReadService._snapshot`/`envelope_on` port matches the existing W4 `cold_snapshot` injection pattern. It waits on the 0032 names. |
| 6 | Closed | Enums match `_PRECEDENCE` and `coverage_of`; label, href and summary mapping are given. |
| 7, 8 | Closed | |
| 9 | Closed except for one point | The `links.work` key set, selection, results, provenance and status are fixed. The W6 unit is misnamed (R-2). |
| 10 | Closed | |
| 11-16 | Closed | Branching by `site.site_type`, the client and presenter split, the W1-only field omission, five rows with a fold at four, the default window, query preservation, the placeholder via `domainActionClient.getDetail`, the canonical `/verification` path and section redirects. |
| 17 | Closed except for one point | Breadcrumb, subtitle, `Open site`, chip and one tab are fixed. "Global rail selects Actions" has no file owner (R-3). |
| 18-22 | Closed | Finding label `Finding {id8}` as an honest gap in the cell, missing intent without a table, result labels, UTC due date, no graphics file. |
| 23, 24 | Closed | Domain-only `WORK_CONTEXT_NOTICE_DOMAIN`/`WORK_STRIP_DETAIL_DOMAIN`; W6 A2 then B2 then K3a; mini-grid untouched. |
| 25 | Closed except for one point | UTC window, generator label and the Next-evidence gap are fixed. The W6 detail routes named do not match W6-01 (R-2). |
| 26-28 | Closed | Route constants, `App.tsx` unchanged, test lists, ledger, panel-contract and registry literals. |
| 29 | **Deferred** | The generated test-only scenario copy and Foundation shift are specified. Whether existing scenario registration accepts a generated path must be traced on merged W5-01b. |
| 30, 31, 32 | Closed | |
| 33 | Closed | The mock Actions empty body, `{WR title} {WR code}` and the Finding label gap are restored. |
| 34 | **Deferred** | The fixed E1 vector is kept, and a separate private shifted replay records both clocks. The selector at the last watermark no later than K2 must be verified on merged W5-03b. |
| 35-45 | Closed | The EV summary now uses the mock literal and comes from the validated keys. `OPEN`/`Not assigned`, the session port, the named CHECK, `main.py` unchanged, both INC and WR payloads, the refusal split, one Verification tab and the ledger literals are all fixed. |

### Remaining and new items

- **R-1 (Medium; K4a and V4a): the guard will reject new copy.** `Maintenance detail is not available yet.`, the text next to the disabled `Inspect maintenance evidence` button, matches `missing-claim-scan.mjs` pattern `/not available yet/i`. Neither card lists `tools/checks/missing-claim-scan.mjs`, `frontend/src/ui/gapCatalogue.ts` or a registry `mock_gaps` placement. Rule one of these:
  - a catalogued `<MissingClaim>` placement with a literal gap ID and placement;
  - a reviewed exemption naming the const and decision;
  - reworded copy.

  (K3a's "contains no guarded phrase" covers only the Work notice.)
- **R-2 (Medium; K1b, K3a, K4a, V3a, V4a): wrong W6 unit, and a route that does not exist.** The spec says "after W6 B3 use its mounted request Overview href". In W6-01, B3 is the Preventive page; request Overview is **C2** (`WorkRequestOverview.tsx`). K3a also says to use "W6's Incident detail route for INC". W6-01 has no Incident detail unit (A1/A2 are the global Incidents list only). State C2 as the WR trigger, and either keep INC case cells as plain text with no W6 trigger or name the owner of an Incident detail route.
- **R-3 (Medium; K4a and V4a): the rail-state rule has no file owner.** "Global rail selects Actions" on `/sites/{site}/actions/{id}/verification` cannot happen with the current `NavRail` `NavLink` path matching, which marks Sites. It needs edits to `frontend/src/ui/NavRail.tsx` or `frontend/src/shell/OperatorShellLayout.tsx`, which W6 Lane A owns, plus their rail tests. Neither file is in K4a or V4a. Name the files, the mechanism and the order with W6, or label the rail state as a deviation.
- **R-4 (Low-Medium; K1a): the W1 refusal does not exist.** `postgres_action_store.py` "maps conflict to its existing code-collision refusal", but the W1 store has none: its only `IntegrityError` path is `action_event_idempotency_unique`. K1a's two-direction test needs the code, HTTP status and message for a W1 acceptance that collides.
- **R-5 (Medium; K1c and the W6-01 seam): unsatisfiable order and unlisted W6 tests.** K1c says "W6's global read must consume this W4 union before it merges". W6 A1, A2 and B2 merge before K3a and probably before K1c, and the W6-01 spec has no matching amendment. If W6 A1 or B1 merge first, K1c changes `postgres_work_read.py` underneath `test_w601a_global_incidents.py`/`test_w601b_global_maintenance.py`, which are not in K1c's file list. State the actual order and add those tests to K1c, or amend W6-01.
- **R-6 (Low): short or full Site name.** The ledger strip says `Scoped to {short site} · …` (the mock shows the first word, as W4 `shortName` does); the shared Site UI section says `Scoped to {site} · {n} actions`. Pick one for Actions.
- **R-7 (Low; rule 5, consolidated cards): stale ledger rows remain.** The ledger rows still say: Action root `scope chip Open or actual reduced W1 state` and `{selected Finding code}`; Incidents `Site timezone label`; empty intent "current-result cells are absent". The override clause makes the closure text win, but a builder still reads contradictory rows. Edit them in place.
- **R-8 (Low): where the Next-evidence gap is recorded.** K3a says "a `mock_gaps` entry `No witnessed automatic-start test is recorded as next evidence.`". The Registry section says gaps go in panel-contract reasons, "not an invented ledger key", and the given `claim_limit` literal does not contain that sentence. Pick one.
- **R-9 (Low): mini-grid default window.** "With no `from/to`, use W4's last seven complete UTC days … on all three tabs" does not say whether mini-grid Actions keeps its choose-window state, as "Mini-grid retains every W1 literal" implies.
- **R-10 (Low, unlabelled): Window column time zone.** The cold Incident `Window` cell gains an explicit `UTC` label where the mock shows `6 Oct · from 19:11`, implicitly in the page's EAT range. Label it, or note it as presentation only.

### M4/E4 replacement literal and ledger row

These are now right. The strip keeps the mock's three slots: `Scoped to …`, then `Cold-chain Actions recorded at this site` / `EV Actions recorded at this site`, then plain `Global Actions does not include cold-chain Actions yet.` / `… EV Actions yet.` There is no href. The ledger scope-strip rows now defer the Actions cell to M4/E4 and keep the W6 mounted-root rule for Incidents and Maintenance only, so the earlier contradiction is gone. The alternatives are recorded. The "does not include … yet" sentence is not matched by the missing-claim patterns, so it needs no catalogue entry, though it is a soft missing-capability phrase (Low, no change required). M1, M3/E2 and E3 are restored to the mock as I recommended. M2/E1 stays a valid labelled deviation.
