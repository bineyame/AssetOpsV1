# W5-02b phase handoff (K2a, K2b, K3a, K3b, K4a, K4b, K5)

Branch `task/W5-02b-cold-site-screens`, from main `5e7c6f2d`. I wrote no code and ran no tests, servers or DBs. The core is read from `task/W5-02a-cold-action-root` (`7d6bbf92`, not merged). The P-IDs continue after the W5-02a batch: P-K2a-1..32 and P-K2b-1..3 are already ruled (U1-U4) and are not reused. Anchors refer to main unless they say `core:`.

## Pre-flight

### General / gates

- **P-G-1 Base and merge boundary.** This branch is from main, which has no domain-work wire, client or `tools/w502_cold_work_cases.py`. K2a cannot reach a persisted positive state without the core. Should core merge to main first? Or should this branch merge `task/W5-02a-cold-action-root`? The spec and task card call K2a/K2b the W5-02a-site merge, K3a/K3b W5-02b and K4a-K5 W5-02c: four merges. This brief puts all seven units on one `W5-02b` branch. Confirm the branch-to-merge mapping. Is it one branch with three reviewed merges, or three branches?
- **P-G-2 W5-03a E2/E3 gate.** The W5-03a ruling (`W5-03-build-spec.md:675`) puts K2a/K2b after W5-03a E1b, E2 and E3 shared UI edits (`SiteAnalyticsFrames.tsx`, `operatorSiteRoutes.ts`, `App.tsx`, navigation guards). `task/W5-03a-ev-selected-depth` holds only its pre-flight, so E2/E3 are not built. Does K2a wait, or may K2a-K3b build now and rebase later? It also conflicts with the task card ("W5-02c must merge before W5-03a"): which order wins?
- **P-G-3 W6-01e (W6 E1+E2) is built first and unmerged.** It edits:
  - `OperatorShellLayout.tsx:58` (Operational records goes live);
  - `operatorSiteRoutes.ts:416`;
  - `navigation-truthfulness.ps1:552` and `navigation-rail-fixtures.ps1`;
  - `operatorSiteTabs`, `siteDetailRoute`, `operatorRouteFrames` and `operatorRailInventory` tests (nine live links);
  - `App.tsx` and the ledger/pilot JSON.

  The spec assumes K4a merges before E2 and that E2 preserves K4a (`W6-01-build-spec.md:114`). Confirm the reverse: E2 merges first and K4a preserves E2's live entry and test counts.
- **P-G-4 Maintenance request href after C2: no producer.** C2 is mounted on main. Its route is `WORK_REQUEST_ROUTE_PATH="/maintenance/requests/:caseId"` (`operatorSiteRoutes.ts:413`, `App.tsx:493`), with `?site_id=` and optional `known_at` (`globalWorkClient.ts:553-572`). So the spec's "after C2" branches are live now. But:
  - core detail `links.work.href` is always null (`core: work/domain_action_index.py:263-280`);
  - W4 Site row `url` is always None (`work/site_index.py:252`).

  Who builds the href?
  - (a) Backend: `domain_action_index.py` / `site_index.py`. These are not on any K2-K5 list, and the backend golden fixtures change.
  - (b) Frontend from `case_id` plus stored Site code. `globalWorkRequestHref` lives in `work/`, and the sites substrate deliberately imports nothing from `shell/` (`siteWorkCases.tsx:120-125`). Importing from `work/` is a new edge; duplicating the literal path is the existing pattern.

  This affects the K3a WR code and the K4a `Inspect maintenance evidence` button.
- **P-G-5 Capture producer for every page unit.** `tools/w502-cold-work-evidence.mjs` does not exist on any branch. `core: tools/w502_cold_work_cases.py` is a library only (`shifted_case`, `corroborate_k0`, ...). It registers the shifted scenario only in a test `FakeScenarios`, and has no seed or serve CLI. A browser capture needs a served API over a private DB holding the ordinary replay, INC, WR, domain Action, intent and case links. The model is `tools/s603_site_work_walkthrough.py prepare|serve|attest|drop` plus `s603-site-work-evidence.mjs`. Name the new seed/serve file, e.g. `tools/w502_cold_work_walkthrough.py`, and its owning unit (K2a?). Confirm it may reuse the test-only `FakeScenarios` registration inside that tool's process. Also name how each capture is produced:
  - 403: a principal without a grant?
  - PENDING: worker not run in the served DB?
  - STALE/UNKNOWN: the run-5 inputs, including UNKNOWN's directly seeded selected fixture?
  - 503: a second API process on an invalid private DB URL.
- **P-G-6 EV scope.**
  - U1 says EV remains on W1 until V2.
  - Spec :70 and :76 dispatch "cold/EV" for literals, the default seven-day window, currentness notices and `EV work unavailable`.
  - Today EV has no dispatch. Its Work tab and Action route render W1 (`SiteWorkActions.tsx`, `SiteActionFrame`).

  Does W5-02 change EV Work tabs at all (Actions, Incidents, Maintenance)? Or is everything COLDCHAIN-only, with EV left byte-identical until W5-04?
- **P-G-7 Grouping proposal.**
  - K2a (two runs per the ruling) and K2b form one sub-slice (W5-02a-site).
  - K3a and K3b form one sub-slice. They can be one builder run if the registry edit stays small.
  - K4a, K4b and K5 form one sub-slice. K4b and K5 can share one run.
  - Confirm.

### K2a — Action index and shared scope

- **P-K2a-33 Mixed rows.** W1 union rows carry `state` as the W1 `reduce()` object (`actions/site_index.py:231`); domain rows carry the string `OPEN`. W1 rows have `title`, `owner_label` and `due_at` null and `criterion_summary` null (`core: domain_action_index.py:350-356`). On a cold Site, confirm the W1 row cells:
  - code only;
  - `Not assigned`, `Not set`;
  - the W1 state presenter or a chip;
  - `No success criterion declared`.
- **P-K2a-34 W1 ID on a cold Action route.** A W1 row links to bare `/sites/{c}/actions/{id}`. U2 makes `SiteActionFrame` call domain detail on COLDCHAIN, and a 404 "never falls back to W1". The frame sees only the URL, so a W1 Action on a cold Site dead-ends. How does the frame learn the row domain? Options: a query marker, try W1 on `ACTION_NOT_FOUND`, or dispatch on the path form `/verification` vs bare.
- **P-K2a-35 Detail `domain` location.** Core puts `domain` in `action.domain`, not top-level (`core: domain_action_index.py:240-258`). Confirm the client validates `action.domain==='COLDCHAIN'`, so no wire change is needed.
- **P-K2a-36 Refusal envelope.** The domain API refuses with `{"detail":{code,message}}` (`core: domain_work_api.py:41-42`). A refused detail read also carries top-level `intent:null,results:null`. Confirm the client parses this shape, and that it differs from W4's `workClient` parse.
- **P-K2a-37 Finding revision link.** The cold Finding frame ignores `revision_id`: `SiteAnalyticsFrames.tsx:634-651` never passes it to `ColdFindingFrame`, and `ColdAssessmentViews.tsx:1055` reads by window. U1 offers "own that route/read test or render plain text". Honouring the revision needs `ColdAssessmentViews.tsx` and its client (not listed), and an API that accepts a revision. Rule now: either plain-text origin in K2a, K3a and K4a (`Open source Finding →` too), or add the files.
- **P-K2a-38 Subtab query on mini-grid.** `WORK_SUBTABS` hrefs carry no query today (`SiteAnalyticsFrames.tsx:1564-1568`). Do mini-grid subtabs also gain `from,to,known_at`? That changes `w1f4ChangesWorkStructure.test.tsx:150-165` and the mini behaviour. Or is the query cold/EV only?
- **P-K2a-39 Topbar range picker.** U3 says the topbar range controls `[from,to)` on cold. Which shell component writes `from/to` to the URL, and does it exist on Work routes today? If no picker writes the query, the cold user has no way to change the default seven-day window once the W1 form is hidden.
- **P-K2a-40 Work page subtitle source.** `ChangesWorkPageHeader` (`SiteFoundationChange.tsx:83-102`) uses `SITE_SCREEN_DESCRIPTIONS.sitework` for every type (`V69Layout.tsx:~277`). The mock uses `SITES.cold.subtitle` (`index.html:198`). Name the Foundation field to use, and the literal fallback when it is null.
- **P-K2a-41 Uncoded departure: panel subtitle.** The mock reads `Due dates are not yet set in this example`; the M1 ruling drops "in this example". There is no `MOCK DEVIATION` label or register row. Assign a code (D4?) and a register row.
- **P-K2a-42 Domain notice constant home.** The cold Actions tab renders `Opening a record moves you to its own area; …` (M2). K3a's card creates `WORK_CONTEXT_NOTICE_DOMAIN` in `siteWorkCases.tsx`, but K2a needs it first. The `missing-claim-scan.mjs:70-76` exemption pins `WORK_CONTEXT_NOTICE` references to `siteWorkCases.tsx`. Does K2a add `WORK_CONTEXT_NOTICE_DOMAIN` (and export it) in `siteWorkCases.tsx` now?
- **P-K2a-43 Register owning units.** Both M2 (notice) and M4 (Actions strip) render on the K2a Actions tab, but the register names other units:
  - R01 names `W5-02 K3a M2`;
  - R02 names `W5-02 K3b M4`.

  Correct these to K2a, or rule which unit labels them.
- **P-K2a-44 CSS and disclosure.**
  - The card lists `w1f4-action.css`, which exists and is shared by three modules. U3 says to use `w1f4-changes-work.css`. Confirm K2a does not touch `w1f4-action.css` for the list.
  - U4 says native `<details>`, but `ui` exports a `Disclosure` component. Which one?
  - `DataTable` has no sticky prop (`ui/DataTable.tsx:47-68`), so sticky goes in local CSS on `.data-table__scroll`. `shell-overflow.ps1:276` forbids `overflow:hidden|clip`.
- **P-K2a-45 Placeholder panel structure.** `expectV69Panels("cold-action")` requires both `Declared outcome criteria` and `Related activity` (`v69-rendered-panels.json:884`). Does the K2a placeholder render both panel headings with the placeholder sentence? Or is the panel-structure assertion deferred to K4a (and K2a asserts `cold-work` only)?
- **P-K2a-46 Verification tab form.** It must be a live self-link with `aria-current`, not an `UnavailableEntry`: `navigation-truthfulness.ps1:759-760` `$expectedTabs` already holds one `Verification`, and adding another fails. Confirm.
- **P-K2a-47 Rail state owner.** U2 says the K2a placeholder renders the "rail state". The rail override is K4a's (`NavRail.tsx`, `OperatorShellLayout.tsx`). Until K4a, the rail shows Sites active on `/sites/X/actions/Y`, because NavLink `end:false` (`OperatorShellLayout.tsx:50-62`). Is that interim departure D5 (resolved by K4a) with a register row, or does the override move to K2a?
- **P-K2a-48 Off-list tests (confirm untouched).** `siteFoundationChange.test.tsx:247,251` mounts `/actions/...` through App on MINIGRID. `estateRoots.test.tsx:144,150` holds cold/EV Action href strings. No test renders a COLDCHAIN Work Actions tab or Action route today, so no existing test should break if MINIGRID stays byte-identical.

### K2b — cap and refusal proof

- **P-K2b-4 Seeding five long rows.** The K1a POST needs a SERVICE principal with attestation, and a selected cold Finding at that Site. That requires the P-G-5 tool. Confirm that the five Actions (160-code-point title/owner) are seeded by that tool after the ordinary replay, in one private DB.
- **P-K2b-5 STALE/UNKNOWN browser captures.** The run-5 Postgres batch passed (core `d7ff896c`), so the C4 gate appears closed and these captures become required. Confirm. UNKNOWN uses a directly seeded selected fixture in a separate DB, and PENDING needs the worker deliberately not run, so the capture tool needs three DBs/processes. Is that acceptable, or should captures cover PENDING only?

### K3a — cold case tabs

- **P-K3a-1 The W6 premises are stale.**
  - The Manage link is already live for every Site type (`siteWorkCases.tsx:271-276`, text `Manage in Incidents|Maintenance` without `→`).
  - `WORK_MANAGE_UNAVAILABLE_STATUS` exists nowhere.
  - `WORK_CONTEXT_NOTICE` on main is `Case history is stored with this site. Incidents and Maintenance can be managed globally. The create flow is not available yet.` (:118-119).

  Confirm the following:
  - Cold gets the mock `Manage in {kind} →` and `WORK_STRIP_DETAIL_DOMAIN`, while mini-grid keeps its text with no arrow.
  - The "before the W6 root is mounted" branch is dropped.
  - The missing-claim exemption stays unchanged.
- **P-K3a-2 Props.** `SiteWorkCases` receives no Site type or timezone (`siteWorkCases.tsx:52-62`). The frame passes only `decisions` (`SiteAnalyticsFrames.tsx:1718`). Confirm that adding `site` (type + timezone) props is in scope. (Both files are on the list.)
- **P-K3a-3 Asset label.** The wire has only the composite `asset_label="GEN-CR-01 · GENERATOR"` (`work/site_index.py:241-258`); there is no type field. Mapping `GENERATOR → backup generator` means either parsing the suffix in the client or adding `asset_type` to the wire (a backend file not on the list, which touches the W4 goldens). Rule which.
- **P-K3a-4 Uncoded departures in the Maintenance row.** There is no label or register row for any of these:
  - The mock Activity cell is a `Completed` chip only (blue); the spec adds the activity text.
  - Outcome is an `Unverified` badge only; the spec adds `outcome_note`.
  - Next evidence: the mock reads `Witnessed automatic-start test`; the app shows `No next evidence recorded`. Only a panel-contract `claim_limit` is planned.
  - The WR target is mock `workverification`; the spec uses the Overview.
- **P-K3a-5 Uncoded departures in the Incident row and across screens.**
  - The mock INC code links to `incident`; the app keeps plain text because there is no Incident detail route.
  - Finding codes `F-118 · F-119` become `Finding {id8}`. This also applies to the K2a Source column and the K4a status line.

  Only a panel-contract reason exists. Assign codes (D1) and register rows.
- **P-K3a-6 Adapted banner.** The cold mock shows `Cold-room operating capabilities and consequence vocabulary within the stable Site shell.` (`index.html:684`) on all cold Site screens. The spec never mentions it. Is it rendered by the shell today for cold, or is it a D3 omission K3a must restore?
- **P-K3a-7 Currentness source.** Name the field that drives the cold notice on the case tabs: the W4 list envelope `status`, or `coverage`. Does the W4 `[data-work-status]` label (`siteWorkCases.tsx:262-269`) go for cold only, with mini tests :224/:567 unchanged?
- **P-K3a-8 Month format.** `Intl` en-GB `month:'short'` yields `Sept` for September. Accept, or pin a month table?
- **P-K3a-9 Guards.** `navigation-truthfulness.ps1` and `missing-claim-scan.mjs` need no edit for K3a, because no new `UnavailableTab` is added and no literal matches a pattern. Confirm they stay as read-only proof, not edits.

### K3b — case captures and registry

- **P-K3b-1 Ledger promotion mechanics.** The four rows are `coverage:'deferred', task:null`, with non-null `to_candidate.architecture_decisions` and no `registry_dependencies` (`v69-screen-ledger.json:1698,1732,1764,2634`). There are no pilot `panels` entries for these screens. `check_v69_ledger.py:95-102` allows `registry_dependencies` only with pilot panels. Confirm the following:
  - No pilot `panels` are added.
  - `follow_on` and `tier` change to the exact values below, which the spec does not give.
  - The exact `remaining_work`/`acceptance` strings (spec: "keep existing nonempty").
- **P-K3b-2 Which unit promotes `cold-action`.** Spec :88 says K3b updates "the four cold rows", but `cold-action` panels are K4-built. Does K3b promote `cold-action` before its page exists?
- **P-K3b-3 `A-cold-work-projections` closure unit.** The node requires `A-cold-excursion-rules`, `A-action-index` and `A-maintenance-index` (pilot :160). Does it close at K3b or K4b? State the evidence path, and whether those ancestors are already resolved.
- **P-K3b-4 Conflicts with W6-01e JSON edits.** W6-01e edits the ledger (oprecords ~:3569) and pilot (:464-466). These are text conflicts only; the merge order follows P-G-3.

### K4a — domain route and Verification

- **P-K4a-1 Rail guard conflict.** `navigation-truthfulness.ps1:645` requires the exact `<NavRail label="Operator routes" items={operatorRailItems} />`, so adding `activeLabel=` fails it. Its fixtures (`navigation-rail-fixtures.ps1:107-108`) anchor nearby. Rule the replacement regex: e.g. permit only `activeLabel={railActiveLabel(pathname)}` with the pathname pattern. Also rule the matching negative fixture. `:659` forbids `Link`/`to=` in `OperatorShellLayout.tsx` outside the inventory, so the override must render `Link` inside `NavRail.tsx`. Confirm.
- **P-K4a-2 Active styling.** CSS styles only `[aria-current="page"]` (`primitives.css:202`), and nothing styles `.active`. The spec mandates `nav-rail__link active` + `aria-current`. Confirm both are emitted, and that no CSS change is needed.
- **P-K4a-3 No existing active-state test.** `operatorRailInventory.test.tsx` asserts no active state (:93-208). The active-state tests live in `t028Screens.test.tsx:524`, `w302EstateEvidenceShellRoute.test.tsx:131`, `w302EstateFinancialsShellRoute.test.tsx:116` and `w301EstateShellRoutes.test.tsx:172`. None visits `/sites/X/actions/...`. Confirm the new assertions go in `operatorRailInventory.test.tsx`, as the card says.
- **P-K4a-4 Status line Site name.** The mock shows the short `GreenHarvest`; the spec uses the stored display name. This is an uncoded departure. Use W4 `shortName` (mock), or label it D2?
- **P-K4a-5 Inspect button state.** Per P-G-4 the button is enabled with a live href, or disabled with `Maintenance detail is unavailable for this record.`. The mock button is non-primary. Name the class (`button` secondary?).
- **P-K4a-6 Panel-structure test.** Add `expectV69Panels("cold-action")` in `domainActionVerification.test.tsx`, and the `cold-work*` equivalents in K2a/K3a tests. Required (mockup-is-layout-spec)? Confirm.

### K4b — Action captures and ledger

- **P-K4b-1 The 422 capture is unreachable from the UI.** An invalid `known_at` URL "reads nothing" client-side, so the browser never receives the server's 422. Is the 422 capture a component state, or a URL the client passes through?
- **P-K4b-2** The `cold-action` ledger/panel promotion, if not done in K3b (P-K3b-2).

### K5 — closeout

- **P-K5-1 Lineage test.** No test joins accepted envelope rows → selected Finding revision → domain Action → case/record → intent, read back through `GET .../domain-work/actions/{id}`. The `test_w502_cold_scenario_producer.py:244-253` assertion only counts envelopes. Confirm the test file (`test_w502_domain_intent_postgres.py` per the card). Also confirm the exact "no inferred restoration" assertion: results equal the four fixed values, no `VERIFIED`, `evidence_ids:[]`.
- **P-K5-2 Full-suite trigger.** Under tiered testing, K4a touches `tools/checks/*` (rail guards), so W5-02c needs the full suite (the card has it). Does W5-02b also need one? It does if K3a edits no guard (P-K3a-9) and P-G-4 adds no backend change; otherwise yes.

### Uncoded mock departures (need a code and a register row)

| P-ID | Departure |
| --- | --- |
| P-K2a-41 | `in this example` dropped from the panel subtitle |
| P-K2a-43 | Owning units for R01/R02 |
| P-K2a-47 | Interim Sites rail state |
| P-K3a-4 | Maintenance Activity text, Outcome note, Next evidence and WR target |
| P-K3a-5 | Plain INC code; `Finding {id8}` in place of F-codes on all four screens |
| P-K3a-6 | Possible adapted banner |
| P-K4a-4 | Short Site name in the status line |

Only M2 and M4 are labelled today.

## Next

The coordinator sends this batch to the Architect as one request. Code starts only after the rulings merge and P-G-1 to P-G-3 clear.
