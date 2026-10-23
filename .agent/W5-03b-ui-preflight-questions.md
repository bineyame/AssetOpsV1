# W5-03b E4/E6 UI pre-flight refresh: open points

Branch `task/W5-03b-ev-health-ui` at main `8270fd3f` (W5-03a, K2, E5 `0034` merged; K3 `task/W5-02b-K3-cold-cases` not merged). Read-only dry read of the E4 and E6 cards, the W5-03b pre-flight rulings (`.agent/W5-03-build-spec.md:767-820`), `.agent/W5-03b-e5-rulings.md`, the E5 API as built, the measurements, the departure register and v69 (`index.html:689-691` ev-health, `:859,862` ev-scenarios). No code, tests or builds.

This file lists only points that are new or still open: 16 in total. The implementer decides none of them. Each point has a recommended option, marked (rec).

## Earlier rulings that still hold unchanged

- **Gate and item 34:** P-G-3 and P-34-1..3 (E5 merged with the clock tests).
- **E4:**
  - P-E4-1/2/9: there is no S7 panel, `SiteHealth.tsx` is not edited, and slots `EvFoundationViews.tsx:631,688` still exist. The destination is covered by point 3.
  - P-E4-3/10.
  - P-E4-5/6: `SiteHealthFrames.tsx:30-79` has only `coldDepth`, and `App.tsx:459` does not pass `evDepth`.
  - P-E4-7 and P-E4-8/12: the display literals override the DTO text. Points 5-7 qualify these.
  - P-E4-11: the executable JSON order governs, `I-W5-ev-depth-read,I-W5-ev-health-ui,D-ev-domain`, as in the precedent at `v69-dependency-registry-pilot.json:478`.
- **E6:**
  - P-E6-3/4/5: `operatorSiteRoutes.ts:255-265`, `App.tsx:384-391`, `EvSiteViews.tsx:61,67-80,360-386` and `evSiteRoutes.tsx:14-61` are as the rulings assumed.
  - P-E6-6/9/10, P-E6-7 and P-E6-8/11.
- **E5 API vs E6 client card.** These match the build:
  - route `GET /api/sites/{code}/ev/financials/scenarios` (`ev_scenarios_api.py:4,44`);
  - `schema_version` `ev-scenarios-1` (`rules.py:26`);
  - the top-level keys, item keys and `authored_basis` keys (`service.py:282-293,86-93`);
  - the `ESCN-%06d` code (`rules.py:70-72`), `kind`, the assumption keys, `DEFINED`/`HISTORICAL`, and the `{error:{code,message}}` refusals.
- **The merged code has no collision with K2** for E4/E6: E4/E6 do not edit `domainActionClient`, `coldWorkPresentation` or the R88 control.

## Gate

**1. K3 is not merged, but E4/E6 are dispatched now.** The K2 lane override (`W5-03-build-spec.md:777`) says E4/E6 routes, nav, registry, captures "and every frontend file wait for reviewed K2 and K3 merges".
- K3 (`git diff main...task/W5-02b-K3-cold-cases`) edits files that E4/E6 also edit or depend on:
  - `v69-screen-ledger.json`;
  - `v69-panel-contracts.json` (see point 9);
  - `test/panelStructure.ts` `SCREEN_LEADING` (see point 4);
  - `SiteAnalyticsFrames.tsx` (2 lines; E4/E6 do not edit it).
- Options:
  - (a) Hold E4/E6 until K3 merges.
  - (b) (rec) Waive the order for E4/E6. E4/E6 leave `panelStructure.ts` and `v69-panel-contracts.json` alone, edit only the `ev-health`/`ev-scenarios` objects in the ledger, and the later of K3 and W5-03b rebases.
  - (c) Build E4 now and E6 after K3.

## E4: EV Health

**2. The premise of P-E4-4 (a bare route is a 422 refusal) contradicts the merged backend and the E2/E3 precedent.**
- `ev_gate` accepts both bounds omitted. Its docstring says "both omitted selects the latest selected EV window at the cutoff and echoes it" (`ev_assessment_api.py:6-7`). It refuses only a lone bound (`:101-106`). `ev_depth_api.py:29` uses the same gate, so no server 422 exists for the bare case.
- The earlier question assumed "The E1 gate requires paired `from,to`" (`W5-03b-phase-handoff.md:26`). That assumption is false.
- E2/E3 forward a bare window unchanged (`SiteAnalyticsFrames.tsx:249-262`, `EvAvailability.tsx:123`).
- The Health tab href carries no window (`operatorSiteTabs.tsx:74`). Under P-E4-4, the primary EV Health entry would therefore always render as a refusal, and E4 would have to fabricate a client-side 422.
- Options:
  - (a) (rec) Follow the backend and E2/E3: a bare route reads the latest selected window and shows the echoed window. `ev-health-unknown` stays a paired window with no selection.
  - (b) Keep P-E4-4 as a client-synthesized refusal. This needs an Architect literal and a register row, because the server gives no such refusal.
  - (c) Do (a) and also add an R88-style `Window` control to EV Health. This is a new D1 row; R88 covers cold Work only (`mock-departure-register.md:148`).

**3. The Foundation `Evidence › Data sources →` destination in P-E4-1 is a dead fragment.**
- `siteEvidenceHref` resolves to `/sites/{id}/evidence` (`operatorSiteRoutes.ts:111-113`). For an EV Site that route renders the generic `SiteEvidenceFrame`, which has only a COLDCHAIN branch (`SiteEvidenceFrame.tsx:106`; `App.tsx:394-404`).
- `#ev-site-sources-heading` belongs to `EvidenceScreen` (`EvSiteViews.tsx:800,885`), which is served at `/sites/{id}/ev/evidence` (`evSiteRoutes.tsx:17`).
- Options:
  - (a) (rec) Use `siteEvHref(site, "evidence")`, plus the valid paired window, plus `#ev-site-sources-heading`, and assert this in `siteHealthBoundary.test.tsx:559` and `evFoundation.test.tsx`.
  - (b) Keep `siteEvidenceHref` and drop the fragment.
- Note: the existing Foundation `Evidence →` links also use `siteEvidenceHref` (`SiteFoundationFrame.tsx:170`). That predates this slice and is out of E4 scope unless ruled otherwise.

**4. The leading currentness notice fails the exact panel assertion (E4 and E6).**
- The leading allowlist of `expectV69Panels` has no `.notice` (`panelStructure.ts:31-33`).
- `SCREEN_LEADING` admits an optional notice only directly after a `.status-strip` (`:66,105-112`). ev-health has no status strip (`index.html:689`).
- As a result, the R15 notice that P-E4-3 places above the cards is an intruder in every PENDING/HISTORICAL/STALE/UNKNOWN variant, including the `ev-health-unknown` capture. The E6 pending/historical notice above `Financial scenarios` is an intruder in the same way.
- E4 may not edit `panelStructure.ts` (P-E4-1/2/9), and K3 edits `SCREEN_LEADING`.
- The W5-03a precedent asserts exact panels only on CURRENT reads (`evEnergy.test.tsx:115-118`, `evDepth.test.tsx:169-171`).
- Options:
  - (a) (rec) Assert exact `expectV69Panels` only on CURRENT variants. Assert the notice placement directly in the other variants.
  - (b) Let E4/E6 add `SCREEN_LEADING` entries for `ev-health`/`ev-scenarios` after rebasing on K3, with a rule that has no status strip.
  - (c) Move the notices below the panel. This conflicts with P-E4-3 and P-E6-7.

**5. The three fixed card positions do not map onto the health DTO.**
- `health.rows` holds one `CONNECTOR` row per Foundation `EV_CONNECTOR`, sorted by `component_id`, labelled with the Foundation `display_name` (fixtures use `Connector c1`/`Connector c2`) (`ev_depth.py:180-198`). The count can be 0, 1 or 3 or more.
- No row carries a fault-stopped session count. A fault row has the first `session_id` and the sorted distinct `fault_evidence_id`s (`ev_depth.py:191-195`).
- P-E4-7 fixes `Connector 1`/`Connector 2`/`Stationary battery` and "a selected count".
- Rulings needed:
  - (i) Card label: the mock literal `Connector N` by sorted position (rec: the Foundation `label`, consistent with the table).
  - (ii) Connector count other than 2: one card per CONNECTOR row plus battery (rec), or the first two only, or the unavailable state.
  - (iii) Source of the fault count: `evidence_ids.length` (rec), or a session count, which would need a second read.
  - (iv) Card set when `foundation_revision_id` is null (rows `[]`).

**6. The battery is always `UNKNOWN`, so `Not applicable`/`None installed` can never show. The register label also disagrees.**
- The backend constant is `BATTERY = {"condition_state":"UNKNOWN","limitation":"Battery configuration is not established by this Foundation."}` (`ev_depth.py:20`), and the client accepts only `UNKNOWN` (`evDepthClient.ts:143,347`).
- R56 is labelled D1 in the register (`mock-departure-register.md:35`) but called "R56 D4" in P-E4-7.
- Options:
  - (a) (rec) Always show `Unknown` gray, with the DTO `limitation` verbatim as the card note, and confirm the label (D1 per the register).
  - (b) Give an Architect literal for the note.

**7. Nothing in the health DTO can prove the Site-meter power-limit claim (R59).**
- The `SITE_METER` tuple is `("UNKNOWN","Sampled import only",None,"Record continuous import and request/limit evidence")`, with only `evidence_ids` (`ev_depth.py:26,200-201`).
- The peak and limit exist only on the Energy read (`observed_peak_import_kw`, `configured_import_limit_kw`). `peak_below_limit` there uses strict `<` on the peak (`ev_depth.py:154-157`).
- Options:
  - (a) (rec) E4 always shows `Power limit not assessed from selected samples` (R59 D4). The positive sentence waits for a reviewed DTO field.
  - (b) E4 also calls `getEnergy` with the same window and asserts the positive sentence only when `peak_below_limit` is `YES`. The Architect must confirm two reads per page and whether `<` or `≤` applies.

**8. There is no numeric cap for the three-row worst case.** The measurements give `panel ≤330/440` only for the two mock rows (`W5-02-04-mock-measurements.md:9`). P-E4-8 says "the three-row/worst-case 36-character ID cap applies" but gives no number, and the `Next evidence` cell can also hold `Session {uuid}` and `Open Sessions →`.
- Options:
  - (a) Keep 330/440 for three rows.
  - (b) (rec) Have the Architect set a three-row cap. Measure the page cap of 1200/1550 with both notices present.

**9. Ledger and panel-contract promotion are unspecified.**
- `ev-health` and `ev-scenarios` are currently `coverage:"deferred"`, `task:null` and tier `Deferred`, and their `v69-panel-contracts.json` rows (`:2221,2844`) are GAP placeholders.
- W5-03a ruling 6 promoted availability/energy: coverage partial, `to_candidate:null`, `unresolved_panels:[]`, tier `Real with honest gaps`, and the six panel-contract fields (`W5-03a-review-rulings.md:15,27`).
- The cold-health and cold-scenarios entries stayed deferred with only `registry_dependencies`.
- The E4/E6 file lists omit `v69-panel-contracts.json`, which K3 also edits.
- Options:
  - (a) (rec) Edit `registry_dependencies` only, following the cold precedent and the current card text.
  - (b) Do the full W5-03a-style promotion, with Architect-supplied literals and the contracts file added to E4/E6 ownership.

**10. A missing-claim reason will go stale.** `tools/checks/missing-claim-scan.mjs:68` names "Health > Data sources (Gateway status header action and Connected sources footer)" as an EV unavailable destination. E4 makes both live, and the file is not in E4's list.
- Options:
  - (a) Add the file to E4 and remove that clause.
  - (b) (rec) Leave it, since stale reason text does not fail the scan, and log a backlog Low.

## E6: EV Scenarios against the E5 API as built

**11. Nullability of `window` and `selection` is not in the client card.**
- `window.{from,to,known_at,committed_watermark}` come from `_ev_plain(snap[...])` and can be null (`postgres_assessment_store.py:3082-3083`). The service branches on null `from`/`known_at` (`service.py:262,268-269`). `selection.assessment_revision_id` is null with no selected head (`postgres_assessment_store.py:3113`).
- The card says "exact keys" and gives no types.
- Options:
  - (a) (rec) Window values are string or null. `assessment_revision_id` is string or null. `session_revision_ids` and `accepted_evidence_ids` are string arrays. A null window with `items:[]` renders the empty block plus the UNKNOWN sentence.
  - (b) Treat any null as the unavailable state.

**12. `next_cursor` has no UI.** GET pages with a default of 50 and a maximum of 100 (`rules.py:30`), and returns `next_cursor` when more rows exist (`service.py:272-281`). Cursor refusals are `EV_SCENARIO_CURSOR_INVALID` and `_BASIS_CHANGED`.
- Options:
  - (a) (rec) Read the first page only. When `next_cursor` is non-null, show a muted line with an Architect-supplied literal and no control.
  - (b) A `Show more` button that follows `next_cursor`.
  - (c) Fetch every page client-side.

**13. Shape of nested `source_provenance`.** Both `selection.source_provenance` and `authored_basis.source_provenance` are the public provenance DTO (`classification, state, source_ids, evidence_ids, reasons, ...`; `public_provenance.py` `public_dto`). E6 displays only `classification`.
- Options:
  - (a) (rec) Validate that it is an object with a string `classification`, and ignore the other keys.
  - (b) Validate the exact `public_dto` key set, which couples the client to S4-05 changes.

## E6: routes, guards and copy

**14. The guard anchors have moved, and the live-assertion pattern needs a choice.**
- `evSiteMoneyRoutes.test.tsx:466,524,561,803-811` are unchanged.
- `navigation-rail-fixtures.ps1:204` is now `:220-222`. That fixture mutates `$evSite` `<UnavailableTab label="Scenarios" />`.
- In `navigation-truthfulness.ps1`, the stale comment is `:748-749` and `$expectedTabs` is `:763`. The cold live pattern has moved from 848-863 to `:869-886`. The EV live-branch pattern for Availability/Energy is at `:852-866`.
- Options:
  - (a) (rec) Model the EV Scenarios live assertion on the EV pattern at `:852-866`: `EvSiteViews.tsx` carries `data-ev-subtab` `scenarios` and renders `<EvScenarios`.
  - (b) Use the cold frames pattern as ruled.

**15. Where the description literal lives.** `SITE_SCREEN_DESCRIPTIONS.coldScenarios` already equals `Financials · scenarios (placeholder)` (`V69Layout.tsx:311`). `EvSiteViews.tsx:345-351` has a per-view `DESCRIPTION` record.
- Options:
  - (a) (rec) Use a local literal in that `DESCRIPTION.scenarios`, which is screen-scoped and leaves V69Layout untouched.
  - (b) Reuse the `coldScenarios` key, whose name is misleading.

**16. The E6 producer clock for `ev-scenarios-historical`.** `scenario_state` is `HISTORICAL` when either:
- the row is superseded (`revision_no < latest_no`); or
- `window.known_at < committed_watermark` (`service.py:270-271,291-293`).

The card's capture uses "correction and saved pre-correction `scenario_at`", which proves the first case only.
- Options:
  - (a) (rec) One capture, as ruled, plus a unit test of the earlier-`known_at` case.
  - (b) Two historical captures.
