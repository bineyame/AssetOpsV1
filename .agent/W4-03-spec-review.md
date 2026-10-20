# Independent spec dry-read: W4-03 mini-grid decisions and work connection (2026-10-20)

Reviewer: a fresh Claude spec reviewer, read-only, worktree `AssetOpsV1-plan2` on main `81a6cc99` ("Merge plan/W4-03-spec"). This follows the ROLE_CONFIG rule, with `.agent/W4-02-spec-review.md` and `.agent/W3-03-spec-review.md` as precedents.

Inputs:
- `.agent/W4-03-build-spec.md` (cited as `S:Lnn`) and `tasks/W4-03-mini-decisions-work.md` (`T:Lnn`);
- `.agent/W4-03-mock-measurements.md` (`M:Lnn`);
- `.agent/post-W2-sequence.md`;
- `.agent/W4-01-build-spec.md` (`W4-01:Lnn`, all closures and Run 1 rulings);
- `.agent/W4-02-build-spec.md` (`W4-02:Lnn`, closures 1–3);
- `.agent/W3-01-build-spec.md` (`W3-01:Lnn`), q1–q4;
- `.ai/ROLE_CONFIG.md:449-455`;
- v69 `screens.js:193-196` (`siteWorkScreen`), `:571-573` (`alternatives`), `:584-589` (`opportunity-finding`), `:712-713` (`scenarios`), `:948-959` (tab rows);
- the merged code.

Method: I read the spec commit by commit as a mid-level implementer would, and checked each named path, symbol, table, column, route, guard and component against the merged tree.

**State of main.** Main ends at `0026_w2_ev_money.py`. W4-01 (`0027`), W4-02 (`0029`) and the W3-01 shared DTO/estate slice are **not merged**. There is no `work/`, `mini_depth/`, `evidence/public_provenance.py` or `estate/`. Every seam the spec takes from those slices is a **prerequisite**, checked here only against their frozen specs. The spec says this itself (S:L3).

**Verified correct**, so not listed below:
- in the DDL: `site(tenant_id,id)` is unique (`0001:78`), `accepted_evidence(tenant_id,site_id,id)` is unique (`0005:211`), `finding(tenant_id,site_id,id)` is unique (`0009:54`), `finding_revision(tenant_id,site_id,id)` is unique (`0009:105`), and `ledger_append_only()` exists (`0005:310`);
- the W4-01 spec's `work_case_scope UNIQUE(tenant_id,site_id,id)` (W4-01:L76), which the `mini_decision_work_link` FK needs (prerequisite);
- the downgrade arithmetic. There are nine tables and four explicit indexes (`mini_scenario_site_order`, `mini_alternative_selected`, `mini_opportunity_head`, `mini_decision_work_case`).
- all 40 layout budgets in S:L218-224. I recomputed each one as `mock + max(24, 10%)`, rounded up, from M:L9-163, and every value matches. The card children (4×281 at 1440; 174 px wide at 390) and the pair widths (735/408) also match M:L73-76 and M:L90.
- the W1 seams that do exist: `FindingIndexService` (`analytics/finding_index.py:231`), `PostgresAssessmentStore.findings/finding` (`postgres_assessment_store.py:1859,1875`), `finding_api.py:development_access` (`:46`) and `ACCESS_BASIS` (`:38`), the W1 legacy `FindingAlternatives` (`FindingDetail.tsx:409`), and the `Other possible explanations (Alternatives)` link (`assessmentAnalysis.tsx:278`).

## Questions

### Blockers

1. **(Blocker) Writes require a USER actor, which W4-01 refuses in development. That leaves no executable authoring path.** S:L47 says that "writes require USER actor ID, `SITE_DECISION_WRITE`, attestation", and that SERVICE "may write only a named rule/job/version for opportunity projection". W4-01 S28 and Run 1 q1 (W4-01:L399, L438-446) reject a development `actor.kind=USER` with 403 `WORK_USER_AUTH_REQUIRED`, because no server-authenticated human principal exists. `SITE_DECISION_WRITE` does not exist anywhere in the backend (grep is empty). So the observable exit's "persisted, authored mini-grid what-if after reload" (T:L13), the Alternatives rows (T:L14) and the fixture's "author a 10 kW × 1 h proposed load … as a labelled test scenario" (S:L230) cannot be written. Rule the following:
   - Is a SERVICE fixture principal allowed to author scenarios, alternatives and decision links? If so, give its literal ID, the attestation regex and the server-stored `authorization_basis` literal, as W4-01 did with `service:w401-fixture` and `SITE_WORK_WRITE:service:w401-fixture`.
   - Is a client `authorization_basis` refused?
   - Which refusal code does a development USER actor get (`DECISION_USER_AUTH_REQUIRED`?), and which code does an attestation mismatch get?
   - Which principal creates the W4-01 Incident and request in the W4-03 fixture: W4-01's `service:w401-fixture`, or a W4-03 one?

   The mutation tables also lack W4-01's length CHECKs and `actor_kind` column (W4-01:L68-71). Say whether to mirror them.
2. **(Blocker) The request bodies for all four POSTs are unspecified.** S:L45-47 names `POST …/financials/scenarios`, `…/scenarios/{id}/revisions`, `…/findings/{finding_id}/alternatives` and `…/work/decision-links`, but gives only the scenario *response* keys. Give literal request JSON for each route, as W4-01 did (W4-01:L280-293). For each route also say:
   - the actor object keys and whether other keys are refused;
   - the field names for kind, name, assumptions, pinned selection and correction reason (scenario); for `alternative_key`, rank, explanation, evidence summary, cited IDs, missing reason, disposition and reason (alternative); and for case ID plus exactly one of scenario/opportunity ID (link);
   - the 201 response body and `schema_version` of the alternative and decision-link POSTs;
   - whether the idempotency hash includes canonical path identity, as W4-01 Q6/Q28 requires (W4-01:L416).
3. **(Blocker) Scenario idempotency and the link table's write columns cannot work as written.**
   - **Scenario create.** A create inserts a new `mini_scenario` root, and the only key is `UNIQUE (scenario_id,idempotency_key)` on the revision (S:L97). A retried create mints a new root UUID, so it never collides and creates a duplicate scenario. W4-01 solved this with a Site-scoped `create_key` and `create_payload_sha256` on the root (W4-01:L72-79). Add the equivalent to `mini_scenario`.
   - **Decision link.** `mini_decision_work_link` (S:L161-171) has no `idempotency_key`, `payload_sha256`, `authorization_basis` or `actor_kind`. S:L47 nevertheless says "all POSTs … compare canonical sorted-key JSON SHA-256; exact retry returns prior IDs".
   - **Opportunity tables.** These have no actor or attestation columns, yet SERVICE must "name a rule/job/version".

   Give the columns and uniques for each.
4. **(Blocker) The opportunity producer has no trigger, study-window rule or job domain.** S:L26 says that an opportunity is "a contiguous 1–5 local-day study" keyed `(tenant,site,first_day,last_day,model_version)`, and S:L45 says the producer is "worker/reconcile owned". The spec never says:
   - which `[first_day,last_day]` studies exist. Is it every rolling five-day window, only an explicitly requested study, or only the fixture's 6–10 Oct?
   - what enqueues a projection. Is it a `mini_depth_selection` insert, a W4-02 job completing, or a `recompute_job.domain` value such as `mini_opportunity`? W4-02 has the closed list `mini_renewable|mini_service|mini_fuel|mini_backup` (W4-02:L144, L216-233).
   - which CLI or schedule runs it, and whether it is behind `tools/schedule-install-gate.py`;
   - what the `model_version` literal is;
   - what status a 1–4-day study gets, since a positive result "requires five distinct completely assessed days".

   Commit 3's "late accepted row appends revision" test depends on all of this.
5. **(Blocker) The opportunity–scenario link has no persisted source.** The opportunity wire carries `scenario_id`, `proposed_load_kw` and `gross_sales_scenario` (S:L50), and the cards and Consequence basis read "authored scenario kW × h" and tariff (S:L192, S:L195). However:
   - `mini_opportunity_revision` is SERVICE-produced and has no scenario column (S:L137-146);
   - a scenario stores only `pinned_mini_revision_ids` (S:L89);
   - no association table links a scenario to an opportunity.

   Is the link derived, for example from the latest PRODUCTIVE_LOAD scenario whose pinned revisions equal the opportunity's selected set? Or is it an authored association, and if so, through which table and command? If more than one scenario matches, which wins? Without this ruling, the cards and Consequence basis cannot be built.
6. **(Blocker) The typed Site/estate "Opportunity lens union" changes frozen contracts that the spec says it does not change.**
   - **Estate.** W3-01's estate Findings API is a Finding-row contract. Its rows are keyed `finding_id/finding_revision_id`, ordered `(episode_start DESC,finding_id ASC)`, and use `lens_flags`, `links.finding`, and a cursor/token built from `selected_finding_revision_ids` (`estate-selection/2`) (W3-01:L30, L39, L66, L267). Adding a `mini_opportunity` arm needs a discriminator key, a row shape and an order key (`first_day` versus `episode_start`), and changes the cursor/token, the `total_count` basis and the column mapping. S:L18 says that any change to W3's shared contract "is a reviewed versioned amendment, not an ad hoc W4 edit". No amendment is given.
   - **Site.** There is no Site Opportunity lens backend. `FindingIndexService` has no lens concept (`finding_index.py:231-349`), and the Site chips are three `UnavailableChip`s (`SiteFindingIndex.tsx:80-82`). W3-01 B1 keeps them unavailable (W3-01:L126).

   Rule the following:
   - the exact union wire (kind discriminator, opportunity row keys, mapping for the Priority/Confidence/State/Main consequence/Lens columns, merged ordering and cursor);
   - whether the Site `Opportunities` chip is promoted, which removes `Opportunities×1` from the chip multiset (`navigation-truthfulness.ps1:747`). S:L240 lists no chip promotion.
   - whether Site Findings shows opportunity rows;
   - who amends W3-01, and in what order relative to Lane B.
7. **(Blocker) The Alternatives surface is misidentified: on the canonical Finding the tab is not built, and the existing tab is a different, analytic list.** S:L11 and T:L9 say "W1 Alternatives tab already exists"/"already a visible Finding tab". On the canonical Site Finding route, Alternatives is `unavailable: true` (`SiteAnalyticsFrames.tsx:544-550`). `FINDING_CHILD_VIEWS` is `["evidence","history","recommendation"]` (`operatorSiteRoutes.ts:235`), and the guard counts it as `Alternatives×1` (`navigation-truthfulness.ps1:745`). The only visible tab is the legacy assessment page `FindingDetail.tsx:52-57,409`. It renders *analytic* `assessment.alternatives` with their own `status` and gaps.
   - Is `/sites/:siteId/findings/:findingId/alternatives` a new `FINDING_CHILD_VIEWS` entry keyed by `?revision_id=`?
   - Does the legacy analytic list stay on the legacy page, move or merge? Do authored rows sit beside the analytic alternatives or replace them?
   - Does the `assessmentAnalysis.tsx:278` link get retargeted, from which page, and with which revision?
   - The registry carries `analysis:3#b alternatives` as unmapped with proposed gate `A-alternative-comparison` (`v69-dependency-registry-pilot.json:312`). Does this slice close it?
8. **(Blocker) The Work `decision_context` has no read seam.** S:L28 and S:L196 add `decision_context {kind,id,label,url|null}` to the Incident and Maintenance rows. S:L28 and S:L200 forbid altering W4-01's frozen list API and row shape (W4-01:L298, L370), and no W4-03 read route is listed for it (S:L45).
   - Which endpoint returns decision contexts for the listed case IDs, under what wire, in the same `known_at` and snapshot, and is it in the list cursor fence?
   - What does `label` show: `OPP-*` code, scenario name and revision as of `known_at`, or root only? The link pins the root, not a revision.
   - Maintenance has no "Linked findings" column. Where does its context render?
   - What does a case with both a scenario link and an opportunity link show?
9. **(Blocker) The `status` enum conflicts with W4-02's claim/currentness separation.** S:L30 places PENDING_RECOMPUTE, STALE_SOURCE and HISTORICAL in the same first-match chain as SUPPORTED and LIMITED, and S:L53 says a row's "status is HISTORICAL/PENDING". W4-02 Q7 makes `status` claim-only `SUPPORTED|LIMITED|UNKNOWN` and keeps `currentness.state` separate (W4-02:L152). The example (S:L50) follows W4-02. Rule:
   - the closed `status` enum;
   - the closed `currentness.state`/`job_state` enums;
   - whether the precedence table yields one key or two;
   - how the "No eligible headroom" row (S:L36), with five complete days and zero eligible, appears on the wire: SUPPORTED with `eligible_days:0`, LIMITED, or something else. The chip rule (S:L26, S:L178) depends on this.
10. **(Blocker) The scenario assumption keys, units and calculation are not closed.** S:L22 and S:L174 say "closed keys and finite decimal strings", but no keys are listed. Give the per-`kind` key table. For example, PRODUCTIVE_LOAD would have `proposed_kw`, `duration_hours`, `tariff_per_kwh` and `currency`; give the equivalents for STOP_SOC, TARIFF_ONLY and OTHER, with units and required/optional status. Also rule the following:
    - **`eligible_days > 0`.** Is this an authored input or the pinned W4-02 count?
    - **"Complete guardrails".** Do they mean W4-02's ELIGIBLE decision (which already includes charge and critical-service checks, W4-02:L237), or something more?
    - **Which headroom value.** Is "each selected eligible noon hour" compared using day-row `opportunity_kwh.low`, given that W4-02 rows carry no per-day `headroom_kw` (W4-02:L39, L237)?
    - **When the calculation runs.** Is it computed at write and stored in `calculation jsonb` (whose JSON shape is not given), or at read? What exactly makes `calculation_state=WITHHELD`: is the pinned revision no longer the head selection for its hour at `known_at`? What is the closed `calculation_state` enum?
    - **Pin.** Is the pin a set of `mini_depth_revision` IDs or of `mini_depth_selection` seqs? S:L22 says "selection set", while the column is `pinned_mini_revision_ids`.
11. **(Blocker) The fixture source is superseded by W4-02 closure 2.** S:L230 uses "W4-02 registered KOBO publication v5", and the wire example uses `REGISTERED_SIMULATION` (S:L50). W4-02 closure 2 withdrew v5. It chose the authored path `backend/conversions/w4-mini-depth-cases-v1.json` / `assetops.w4-mini-depth-cases` / `tools/w402_mini_depth_cases.py`, classified **AUTHORED_DEMONSTRATION**. It also allowed "Positive authored replay unavailable", with no synthesized ELIGIBLE (W4-02:L264). Rule:
    - the W4-03 positive source;
    - the expected provenance class;
    - what W4-03 asserts if W4-02 records the positive replay as unavailable. Does the opportunity stay LIMITED, and does the slice still close?

    "Expected $2.50 is asserted only if the fixture's selected lower headroom supports that load" (S:L230) makes a test's expected outcome conditional. Fix the expected result once the W4-02 fixture values are known.

### Should

12. **(Should) The provenance DTO key list is inconsistent with W3-01 and W4-02.** S:L15 and S:L50 list five keys, `{classification,source_ids,evidence_ids,basis_sha256,reasons}`, yet call the DTO "six-key". W3-01 q3 and W4-02 Q18 use `classification,state,source_ids,evidence_ids,basis_sha256,reasons`, with `state==classification` (W3-01:L236, W4-02:L12). Confirm the six keys and correct the example. The example's `selected_source_provenance:{}` contradicts "full selected six-key DTO" (S:L53).
13. **(Should) The `currentness` shape of a composed five-day read is undefined.** S:L50 gives `{state,selected_at,selection_seq}`.
    - Is that the `mini_opportunity_selection.seq` or a W4-02 seq? W4-02 Q6 uses `windows[]` with one integer `selection_id` per local day (W4-02:L150).
    - What makes an opportunity PENDING or STALE at read time: overlapping W4-02 `mini_renewable` jobs on any study noon hour, a newer `mini_depth_selection` for a pinned hour, or an opportunity-projection job?
    - What populates `pending_source_provenance`?
    - Should `mini_opportunity_selection` carry `job_id` like W4-02's selection (W4-02:L216)?
14. **(Should) The historical head rule for opportunity and scenario revisions is incomplete.** W4-02 requires both `selected_at <= known_at` and `revision.knowledge_cutoff <= known_at` (W4-02:L168). `mini_opportunity_revision` has no `knowledge_cutoff`, and `mini_opportunity_head` orders by `(selected_at DESC,seq DESC)` only.
    - Is `created_at <= known_at` the second predicate?
    - For scenarios: "latest version as of `known_at`" by `recorded_at`, or by `revision_no`?
    - For alternatives: is the current row per `alternative_key` the greatest `version_no` with `created_at <= known_at`?
15. **(Should) List envelopes, the cursor and the window semantics are not given.**
    - Only one opportunity-shaped object is shown, with no `total_count`, `rows`, `next_cursor` or `selection_token`. Give the literal list envelope and `schema_version` for scenarios, alternatives and opportunities, and the separate opportunity **detail** body.
    - Define `selection_token`'s canonical object for each list. Is the query parameter `cursor`, and is `limit` accepted?
    - Alternatives GET has no `from`/`to`, but the cursor requires them (S:L47).
    - What do `from`/`to` filter for scenarios (`recorded_at`? pinned days?) and for opportunities (overlap with `[first_day,last_day]` in Site-local days)?
    - The example window `09:00Z … 2026-10-10T10:00Z` (S:L50) is neither one noon hour nor whole local days, which W4-02 Q4 requires (W4-02:L146). Give the exact `links.renewable` bounds and the meaning of `links.site_work`.
16. **(Should) The alternative identity, rank and review states are undefined.**
    - What is `alternative_key`? Is it authored free text, or a closed set (policy/uncertainty/capability)?
    - S:L47 says "rank policy/uncertainty/capability". Is rank fixed by key (1/2/3) or authored? Only `rank BETWEEN 1 AND 3` is constrained, with no uniqueness, so is the maximum three alternatives per Finding revision?
    - Give the closed `review_state` enum for the row (S:L53). It includes `Needs review for this revision` (S:L189).
    - How is a carry-forward to a new Finding revision expressed: the same `alternative_key`, with `version_no+1` and a new `finding_revision_id`?
    - "`RULED_OUT` requires positive cited counterevidence … and an exact same-window Finding basis" (S:L24). The service can check only that citations are present and that a reasoning field exists. Define "same-window Finding basis" and the refusal code.
    - Is a request to the alternatives API with a cold or EV Finding, or a non-dispatch one, 404 or 422?
17. **(Should) The Work copy and controls contradict W4-01's frozen Site Work mapping.**
    - The status strip unavailable copy is W4-01 `Count unknown · work source unavailable` (W4-01:L345); W4-03 has `Incident count unavailable` (S:L196).
    - The Manage control is W4-01 static text `Manage in … · Not available yet` and never `UnavailableEntry` (W4-01:L345, L400); W4-03 has an `Unavailable` control (S:L198).
    - The notice is W4-01 `Case history is stored with this site. A global work page and create flow are not available yet.` (W4-01:L351); W4-03 has `Record detail is not available yet; this list keeps the site context.`
    - The Maintenance Outcome cell is W4-01 `outcome_note` or `No outcome recorded`, with `Unverified` as a badge in the Activity cell (W4-01:L397); W4-03 has `Outcome`=`Unverified` (S:L197).
    - Next evidence is W4-01 `No next evidence recorded` (W4-01:L370); W4-03 has `No outcome evidence specified`.
    - The work order is W4-01 maintenance `created_at`, not `occurred_at` (W4-01:L319); see S:L47.

    S:L200 says W4-01 owns these mechanics. Rule which copy wins, or record a supersession entry in S:L202-210.
18. **(Should) The Site Work layout budgets conflict with W4-01.** W4-01 caps these panels at `floor(1.30 × mock)`. For example, the Incidents panel is 410, with a stocked five-row cap of 460 at 1440 (W4-01:L329-338, L400), and W4-01 measured 354 for the 390 Incidents panel. W4-03 applies `mock + max(24,10%)` = 348 at 1440 and 370 at 390 to the same panels (S:L222-223), from a 336 measurement (M:L126). A W4-01-conformant stocked list can fail W4-03's budget. Which rule and measurement bind the deepened lists?
19. **(Should) The opportunity page header, breadcrumb and tabs are unmapped.** The mock title is `Productive-use headroom at Kobo`, the breadcrumb `Findings › F-109 › Overview · site: Kobo Mini-grid`, a single `Overview` tab, and a heading action `Open site` (`screens.js:584`, `:948`; M:L79-82). S:L191-195 maps only the body. Give the title source, the breadcrumb trail (Site-rooted or the Findings root, given the `/sites/:siteId/opportunities/:id` route), the tab row, the `Open site` target and the `SITE_SCREEN_DESCRIPTIONS` text.
20. **(Should) Card notes for two opportunity cards are missing.** The mock has `Separate five-day study` under Eligible days and `Grain-mill scenario` under Proposed load (`screens.js:586`). S:L192 gives notes only for Usable headroom and Gross sales. Give the literal note for both, including the no-scenario variant. Also say whether Gross sales is **per eligible window** or a total; the mock's $2.50 is 10 kWh × $0.25, per window.
21. **(Should) The money wire type and rounding are unspecified.** For `gross_sales.amount`, `energy_kwh` and the tariff value, say whether each is a decimal string, as in W3-01 B7 (W3-01:L130), or a JSON number. Also give the currency format (ISO 4217?), the tariff unit literal (`currency/kWh`, as in `financials/assumptions.py:30-32`?), display rounding (`$2.50`) and the display of a non-USD currency. Does a scenario tariff relate to the existing Financials Assumptions store (`diesel_price_per_litre`, `ev_gross_tariff_per_kwh`), or is it deliberately independent?
22. **(Should) The scenario rows, drawer and create UI are left to the implementer.** On S:L184-185:
    - `Open scenario` "links only to an implemented detail drawer … otherwise `Scenario detail unavailable`". Is the drawer in scope or not?
    - `Create scenario` appears "only when reviewed POST UI exists". Is a create form in scope?

    The same question applies to Alternatives authoring and the decision-link command. The row shape (S:L53) lacks `scenario_state` (S:L30) and the public number/code shown in the `Scenario` column (S:L184). The scenario code prefix is not given; only `OPP-` is. S:L53's `url` field has no route. Rule each item.
23. **(Should) The populated Scenarios table has no layout or column spec.** The mock has only an empty block (`screens.js:712`). S:L184 adds a five-column table but gives no column widths, no 390 min-width or sticky column, and no row cap, so the 348 px panel budget is unenforceable. The mock subtitle `Placeholder · to be designed with the owner` is superseded (S:L206) without replacement subtitle copy. The mock empty body's `for example a different stop setting, stock value or tariff` is dropped (S:L183) without a supersession entry.
24. **(Should) Scenarios promotion conflicts with a shared tab occurrence.** `Scenarios×1` is one source occurrence in the Financials subtab row, which is shared by the generic (mini) and cold frames (`SiteAnalyticsFrames.tsx:663-690`; `coldSiteRoutes.tsx:52`). S:L240 promotes "only the mini `scenarios`", keeping cold/EV unavailable. Removing the one occurrence makes cold live, and keeping it leaves mini unavailable. Rule the component split and the resulting multiset. The guard counts literal source occurrences (`navigation-truthfulness.ps1:727-747`).
25. **(Should) The W4-02 renewable CTA replacement has no mapping rule.** S:L209 replaces W4-02's `Opportunity decision unavailable` destination (W4-02:L182) "with its exact ID link". A renewable page selects 1–5 local days. Which opportunity does it link to: an exact `[first_day,last_day]` match only, or any study that overlaps? What happens with no match or more than one match? Is this edit to W4-02's page and test in W4-03 commit 4?
26. **(Should) `Managed Action` has no source.** S:L195 says "exact linked W1 Action ID/event if separately accepted". No table links an opportunity to a W1 Action, and W1 Actions are created from a Finding recommendation (`action_api.py:152`). Is the cell always `Not yet accepted` in W4-03?
27. **(Should) The error table is incomplete against W4-01, W4-02 and W1.**
    - There is no `PERFORMANCE_CUTOVER_CLOSED` 409. W1 FindingIndex and W4-02 Q12 apply it (W4-02:L164; registry `A-finding-index`).
    - There is no `INVALID_LIMIT` (W4-01:L390).
    - A non-head predecessor uses `DECISION_BASIS_CHANGED`, which W4-01 reserves for cursors; W4-01 uses `WORK_CORRECTION_CONFLICT` (W4-01:L390).
    - There is no 422 for a foreign or out-of-scope cited evidence/Finding/case ID in a POST body (W4-01 `WORK_LINK_SCOPE_INVALID`). S:L16 says that foreign IDs are 404.
    - The `INVALID_KNOWN_AT` copy differs from W4-02 (`Select a knowledge time at or before this read.`, W4-02:L162).
    - A non-MINIGRID Site has no case. W4-02 returns 200 UNKNOWN with `SITE_ROLE_UNSUPPORTED` (W4-02:L158).

    Give the code, HTTP status and copy for each.
28. **(Should) The module, API and writer file names are not named.** S:L18 says `mini_decisions/` owns writes. Give the module files (rules, store, read, projection, worker), the API file and router builder name, the mount point in `main.py` (does it reuse the `performance_api` gate?), and the exact rule-8 writer path and table list (S:L240), as W4-01 and W4-02 did. Give also the `selected_hours`/`result` JSON keys for `mini_opportunity_revision` (S:L174) and the trigger names for the downgrade.
29. **(Should) Commit sizing exceeds one builder run.**
    - Commit 2 carries rules plus three APIs, provenance and refusals.
    - Commit 3 carries the worker, late selection and a cross-lane estate union.
    - Commit 4 carries three pages, the W1 Alternatives delta, the W4-02 CTA change and the budgets.

    W4-02's equivalent was re-cut into seven units (W4-02:L196). Propose separating: alternatives from scenario/opportunity APIs; the producer/worker from the index union; and the Scenarios+Alternatives pages from the Opportunity page. Also state that no commit calls an unmerged W4-01, W4-02 or W3-01 seam.
30. **(Should) The panel-structure test, registry nodes and catalog counts are not named.** The mockup-is-layout-spec rule needs an automated ordered-title assertion through `frontend/src/test/panelStructure.ts`/`v69PanelTitles.ts` (both exist), and reviewed per-screen panel paths (post-W2-sequence:L9). Name both. Name also the registry nodes to close: `A-alternative-comparison`, the W4 `FinancialScenario` and `RenewableOpportunityWindow` nodes, or others. The spec should also give the exact `0030` catalog delta (PK/UNIQUE/explicit index/FK/trigger counts, as W4-01:L471 did), not just "assert exact delta".

### Nits

31. **(Nit) Alternatives 1440 geometry.** The 1440 column widths 459/360/302 and row heights 45/45/44 (M:L44) are not restated in S:L214. Only the narrow widths are.
32. **(Nit) Alternatives breadcrumb and tabs.** The mock uses the global `Findings › F-104 › Alternatives · site:` trail and an `Analysis` tab (`screens.js:959`; M:L48). The canonical Site Finding uses a Site trail and has no Analysis section (`SiteAnalyticsFrames.tsx:545-563`). S:L186 says "retain their reviewed routes". Confirm that the Site trail stays and that Analysis is absent.
33. **(Nit) Shared public-number sequence.** `mini_decision_public_no_seq` is shared by scenarios and opportunities (S:L76), so `OPP-` numbers have gaps whenever scenarios are created. Confirm this is intended, and give the `OPP-` derivation (`lpad(public_no,6)`?).
34. **(Nit) Exact pair FK.** `mini_alternative_revision` could reference `finding_revision(tenant_id,site_id,finding_id,id)`, as W4-01 does (W4-01:L129), to make the Finding/revision pair a SQL boundary as well as a service check. Confirm whether that unique exists on merged base, and whether to use it.
35. **(Nit) Test counts.** Focused test-count deltas are not stated (S:L234-238). Record them as collected, per the W4-02 Q32 precedent, and say whether `test_scope_403_404_and_store_503` is parametrized.
36. **(Nit) Downgrade lock order.** S:L174 says "child-to-parent order" without naming the order. List the nine tables in lock order.
