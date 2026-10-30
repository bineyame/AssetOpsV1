# OUT-B pre-flight: batched questions (2026-10-30)

Branch `task/OUT-B-site-outcome-board`, worktree `AssetOpsV1-outB`, head `7b826e97` (slice A head, not yet on main). Spec: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md` rev 2, covering §0, §1, Slice B, "Pre-flight rulings A" and addenda 1-2. No product code has been written.

Backend paths are relative to `backend/assetops_backend/`. "Default" is what I will build if the ruling is silent.

## Checklist results (no question)
- **EOL check:** `git ls-files --eol` shows no `eol=lf` file with `w/crlf`.
- **Register:** R520-R528 are used (slice A). R529-R579 are free.
- **Vocabulary.** I scanned every quoted string and table cell of §1.2, §1.4, addendum 2 and Slice B against `terms` and `w1.terms` (Python copy of `phraseTerm`). I also scanned the mock `explainBoard` text (`outcomes.js:125`).
  - Screen copy: 0 hits.
  - Hits outside screen copy: wire codes, build prose (`RUN_HOURS`, `PENDING`, ...), and "Claim under warranty or repair", which is not shown (R546).
  - Backend data that is rendered verbatim (limitation texts, `cooling.text`, Finding titles) is not covered by this scan. See Q12 and Q20.
- **Missing-claim cues** (`tools/checks/missing-claim-scan.mjs:35-48`).
  - B's only frontend cue literal is the Grow-card fallback. It stays on the existing `G-portfolio-grow-revenue` / `portfolio.outcomes.grow-value` placement, rendered once.
  - These match no cue: "None open", "Nothing proposed yet", "No open action or work", "None recorded", "Not measured yet", "Loading how this site is doing…", "This view is not available for this site", "Some readings could not be loaded; those outcomes show Unknown", "Outcome status is not available right now".
  - Every contributor "Not available yet · …" text is built in the backend.
  - No `mock_gaps` row is needed.
- **Guards.**
  - `<svg>`: only `sites/componentIcons.tsx` may draw icons (`shell-overflow.ps1:89-92`). `OutcomeGlyph` (`componentIcons.tsx:215`) already has every column key (`drives`, `issues`, `can`, `hand`, `prev`, `guard`; union `:186`). B adds no inline `<svg>`.
  - Tables: no bare `<table>`. The matrix and the explainer table are `role="table"` spans.
  - Prop names: no prop named `variant`, `shell` or `isLab` in `sites/` (`site-substrate.ps1:122-126`). No `sites/` import from `shell/`.
  - Missing-data markers: no new `<UnavailableTab>` or `<UnavailableChip>` (closed multiset, navigation-truthfulness).
  - `ui-primitives.ps1` places no restriction on `<dialog>`, `<details>` or `role="table"`.
  - Estate importing from `sites/` is allowed.
  - New hrefs and the new router need no registration.
- **Routes.** Every board href in §B.2 and §B.4 resolves to a mounted route. The capability ids `renewable`, `dispatch`, `fuel`, `service` and `backup` exist (`miniDepthClient.ts:10`, `SiteAnalyticsFrames.tsx:247`).
- **Anchor drift within ±15 lines (noted only).**

  | Spec anchor | Actual line |
  |---|---|
  | `SiteWindowOverview.tsx:1246` | :1245 |
  | `coldSiteViews.tsx:689` / `:686` | :692 / :689 |
  | `EvSiteViews.tsx:621` / `:618` | :617 / :614 |
  | `postgres_assessment_store.py:2346-2347` | :2349-2350 |
  | `ev_site_reads.py:691-695` | :695-701 |
  | `estate/portfolio.py:38` | :40 |
  | `estate/portfolio.py:135-149` | :137-152 |
  | `estate/placement.py:49` | :50 |
- **Anchor drift over 15 lines, wrong symbol, or missing symbol.** These are the substance of the questions below.
  - `estate/portfolio.py`: `:268` DISPLAYED_VALUE is at :291; `:313` OPERATING_COST is defined at :251; `:355-363` `evidence_cell_state` is at :379-387.
  - `EstatePortfolio.tsx:368-431` ObjectivesPanel is at :305-365, used at :683. The `:413` MissingClaim is in OpportunityPanel.
  - `actions/site_index.py:201` is inside `ActionIndexService.read` (:160). `actions/service.py:653` is `_links`; the public method is `action` at :655.
  - `work/domain_action_index.py:413` is inside `index` (:375). `work/site_index.py:349` is inside `WorkIndexService.read` (:309).
  - `work/global_index.py:522` is in `read` (:445). The preventive list is `select_preventive` at :388.
  - `work/model.py:112` is `RESERVED_EVENTS`; `VERIFICATION_WINDOW` is only a literal at :107 and :110.
  - The EV availability route is `GET /api/sites/{c}/ev/availability` (`ev_depth_api.py:33`), not `performance/availability`.
  - `tools/select-tests.py` ALWAYS_FULL (:37-44) lists `main.py` but has **no** `composition.py` pattern (§0.4 says it does). B still selects the full suite through `main.py`.
- **Existing tests B will change** (the old cards are removed):
  - `shell/__tests__/s5SiteWindowOverview.test.tsx`: helpers `objectiveCard()` :408 and `card()` :743; tests at :151, :301, :355, :388, :433, :525, :553, :576, :639, :748, :792, :858, :902, :931, :948.
  - `sites/__tests__/coldSiteViews.test.tsx`: :512, :559, :1256.
  - `sites/__tests__/coldRoutes.test.tsx`: `data-cold-card` at :341, :756, :923.
  - The spec's "EV overview test" does not exist as one file. The EV cards are asserted in:
    - `sites/__tests__/evSiteMoneyRoutes.test.tsx`: :427, :464, :554, :927, :999;
    - `sites/__tests__/evAssessmentRoutes.test.tsx`: :272.
  - `estate/__tests__/estatePortfolio.test.tsx`: :179 `rendersFiveObjectiveRowsForEveryAuthorizedSite`, :505 `objectiveCellsLink…`, :441 `rendersMeasuredPanelHierarchy…`.
  - Each change will be listed in the packet with its reason.
- **Golden or byte-pinned fixtures:** none planned. B adds reads only. If Q10 is answered (a), the mini overview wire widens, and the pinned contracts that cover it must be named. See Q10.

## Questions

### Preconditions and register
1. **Mock measurements are missing.**
   - Spec: §0.5 "Mock measurements first" and the checklist item "Mock measurements file exists".
   - `.agent/OUT-mock-measurements.md` is in neither `-outB`, main nor `-plan2`, and the board's closed-height cap derives from it.
   - **Default:** build B1-B5. Measure caps and capture in B6 only after the coordinator commits the file.
2. **`.venv` junction.**
   - A needed a git-ignored `.venv` junction to `AssetOpsV1-plan2\.venv` so check-all's Python guards run (`OUT-A-phase-handoff.md:10`). `-outB` has none.
   - **Default:** I create the same git-ignored junction, unless the coordinator prefers to.
3. **R535 is cited but has no register row.**
   - Spec §0.5 records "D1 (R535)" for the mini-only Portfolio capture. R535 sits in A's range, and A did not add it.
   - **Default:** B6 adds R535 with the Portfolio capture.
4. **B register IDs.**
   - The spec assigns R541 (D5), R542 (D4), R543 (D2), R544 (D4), R545 (D2), R546 (D1) and R547 (D4).
   - R545 recorded "one generic sentence for the empty Earlier column". Addendum 2 now gives two sentences.
   - R548 "is unchanged", but its gap was withdrawn, so it is unclear what it records.
   - R540 and R549 are not described (B6 says "rows R540-R549").
   - **Default:**
     - R540: v6.9 cards retired (doc §6.4 approved deviation 1);
     - R545: two generic sentences instead of the mock's site-specific ones;
     - R548: the Earlier column shows backend text, not the mock's NAY;
     - R549: the Grow card value text (Q27);
     - R541 to R547 as the spec states.

### Window and wire
5. **Mini window shape (P-B4, P-B5).**
   - The mini overview reads exactly one UTC day: `SiteOverviewRead.read(..., day: date, ..., pinned=...)` (`site_overview/read.py:114`).
   - `selected_day` (`site_overview/route.py:50-73`) returns 422 `PARTIAL_WINDOW`, `NOT_ONE_UTC_DAY` or `CONFLICTING_WINDOW` for anything else. With no parameters it uses `db_today()`.
   - It never selects an hour. The mini page sends only `?date=` plus the Finding pin (`SiteOverview.tsx:134`, `siteOverviewClient.ts:495`).
   - **Default:**
     - the board accepts `date` (or a one-UTC-day `from`/`to`) plus `finding_id`/`finding_revision_id`;
     - it reuses `selected_day` and its 422 codes;
     - it forwards the pin, so "exposure in this hour" (§B.4 Cost headline) is the same pinned money the overview shows.
   - Confirm that the board takes the pin parameters.
6. **Mini depth window.**
   - `MiniDepthRead.read(..., lo, hi, known_at)` (`mini_depth/read.py:338`) accepts only one site-local hour or one to five site-local days (`:57` `INVALID_WINDOW`). The overview window is a UTC day.
   - **Default:** pass the site-local day that contains the overview's `window.start`, under the Site zone rule. If that read refuses, MG-1 and MG-5 are `UNKNOWN` and `read_state` is PARTIAL.
7. **Estate summary window for mini Sites.**
   - The Portfolio window can span many days. The mini overview cannot take it (Q5).
   - The spec's fallback is "each Site's latest assessed window", but no read returns that directly.
   - **Default:** a mini Site uses the UTC day of the Portfolio `to` bound (the day before, if `to` is a midnight). It then picks the hour the same way the overview does with no pin. Cold and EV take the Portfolio `from`/`to` unchanged.
   - Record this in the packet.
8. **Estate summary cost.**
   - Each Site costs about 10-14 reads (§B.3 ports), so N Sites run serially on every Portfolio load. There is no cache.
   - **Default:** accept this for the demo (the s602b estate case has few Sites). The Portfolio fetch runs in parallel and the matrix shows its own loading state.
9. **Cold and EV `known_at`.**
   - Both pages send `from`, `to` and `known_at` (`coldAssessmentClient.ts:199` `coldWindowSearch`) and never `date`. §B.1 names only `from`/`to`.
   - **Default:** the board accepts and forwards `known_at` for every domain. `window.known_at` echoes it.

### Mini composer (B2)
10. **Generator use "{a} min avoidable, {u} min unclear" has no source on the overview.**
    - The overview's `assessment.dispatch_intervals` items carry `revision_id`, `start`, `end`, `window`, `claim_level`, `assessment_key` and `link` (`site_overview/read.py:370-377`). They have no class field and no duration.
    - The stored result has `portions_minutes{candidate, necessary, indeterminate}` (`analytics/dispatch_v3.py:463-468`). The classes are `CANDIDATE_AVOIDABLE`, `NECESSARY` and `INDETERMINATE` (`analytics/dispatch.py:31-33`).
    - Options:
      - (a) widen the overview's interval items with `portions_minutes`. This changes the mini overview wire and may move pinned contracts.
      - (b) add a port to the dispatch read service (`analytics/composition.py` `build_dispatch_read_service`) and read the window's interval results.
    - **Default:** (b). Then a = Σ candidate, u = Σ indeterminate. The Cost subline "Generator stayed on {a} minutes…" uses the same a.
11. **Battery reserve blocks and reserve % have no reachable source.**
    - `BATTERY_AT_RESERVE`/`BATTERY_NEAR_RESERVE` are per-point reasons inside `dispatch_v3.py:291`, and are not on the overview.
    - The reserve % is the Foundation control `battery_reserve_soc` (`analytics/assessment_inputs.py:183`; read at `adapters/postgres_assessment_store.py:297`).
    - I have not found a stored, read-exposed per-block reason count.
    - **Default:**
      - if the Q10 port exposes per-point reasons, count them and take the reserve from the assessment inputs;
      - otherwise the contributor reads "Not available yet · battery reserve readings not read", with null confidence.
    - Please name the source, if one is intended.
12. **Limitation text.**
    - `assessment.limitations` is a list of strings of the form `"CODE: text"` (`dispatch_v3.py:538-552`), not objects.
    - The battery-report code is `PCS_CAPABILITY_UNAVAILABLE` (`analytics/dispatch.py:876/886`). Its plain text is "Battery output not reported" (`analytics/plain.py:84`).
    - The raw text can contain guarded words ("PCS", "load") and the code itself.
    - **Default:** the "Battery reporting" contributor and the Assure subline use the plain text for the code (`plain.py`), never the raw string. A code with no plain text gives "An evidence gap limits this conclusion".
13. **Fuel price.**
    - `financials/assumptions.py:30` is `ASSUMPTION_KEYS = ("diesel_price_per_litre", …)`; there is no value in code.
    - The value is reachable through `AssumptionReadService.series(...)` (`financials/assumption_read.py:59`, built by `financials/composition.py:39`). §B.3 does not list `financials/composition.py`.
    - **Default:** add an `assumptions` port built from `financials/composition.py` (read only; nothing under `financials/**` is edited). The text is "Declared at {price} {currency} per litre" when the selection is PRICED at the window. Otherwise it is "Declared price · see Assumptions".
    - Confirm that a read-only composition import is not a "touch" under §0.2.
14. **Cost headline.**
    - `money.eligibility` is an object: `{version, state, note, …}` (`site_overview/read.py:323-324`).
    - Amounts are set only when `money.state == PRICED` (:338-342).
    - **Default:** the headline is used when `money.state == "PRICED"` and `money.eligibility.state == "ELIGIBLE"`. It is formatted by the backend formatter that produces the Portfolio Optimize value ("$3.31–$3.97", A7). I will name that formatter in B2; I have not yet located it.
15. **"Proposed setting change" option.**
    - Spec: "when an Action change exists" (§B.4 Cost options). No field is named.
    - **Default:** show it when the F-104 Action's detail links carry a Foundation change link (`selected_action_links`, `actions/service.py:230`). Otherwise omit it.

### Status and assembly (B1)
16. **Status effect of `SIGNAL:EVIDENCE_GAP`.**
    - The §1.4 rules only read FINDING, WARNING, OPPORTUNITY and READINESS signals. The evidence gap moves MG-7 (§1.3) but has no rule.
    - B.7 #2 expects Kobo Assure WATCH. If readiness is FULL, that row would read NO_OBJECTIVE.
    - **Default:** Signal kind `EVIDENCE_GAP`, with no status effect; it is listed as an issue only. MG-7 is WATCH only through readiness (rule 5c).
    - Alternative: treat it like rule 5(a), so an open gap gives WATCH.
17. **Which producer read settles which outcome (rule 3, `settled`, PARTIAL).** The spec gives no table, and "coverage not complete" has no named source.
    - **Default:**
      - mini:
        - overview refused: all MG outcomes UNKNOWN;
        - mini_depth refused: MG-1, MG-5;
        - dispatch read refused: MG-2;
        - finding_index refused: every outcome a Finding can move (MG-2);
        - readiness refused or UNKNOWN: MG-7;
      - cold:
        - overview refused: CC-1, CC-6, CC-5, CC-7;
        - findings refused: CC-1, CC-6;
      - EV:
        - overview refused: all measured EV outcomes;
        - availability refused: EV-1;
        - depth refused: EV-4, EV-5;
        - findings refused: EV-1, EV-3.
    - "Coverage not complete" means the overview's own coverage or currentness is not complete. A failed action, work or plan port only degrades its contributor to "Not available yet · …" and does not set UNKNOWN.
18. **Is an Action open, applied, in hand or earlier?**
    - `ActionFact.open` is not defined.
    - The §B.2 earlier rule lists a mini Action with PENDING as "Pending", so a pending ACT-048 would show in both In hand and Earlier of the Cost row.
    - The mock (`outcomes.js:65-67`) shows ACT-048 only in hand on the Cost row. Its Earlier column shows the empty sentence, and the Protect row's Earlier shows only the CHECKED entry ("Pending").
    - **Default:**
      - `applied` = application_state APPLIED or later (§1.4);
      - `open` = `workflow_label` not in ("Verified", "Resolution withdrawn");
      - an open Action goes to In hand only;
      - it goes to Earlier (MOVES categories, plus the CHECKED entry) only once it is applied and verification is not NO_PLAN;
      - a pre-applied ACT-048 therefore matches the mock.
    - Confirm, or rule that the spec's literal reading (both columns) stands.
19. **Must not harm: which names, and the cold Protect row.**
    - F-118 checks CC-3, which is in another category. The cold Protect row would then read "Cost per cooling unit must not be harmed; no check is in place yet".
    - The mock's cold Protect row has no guard, and CC-3 is not measured in B.
    - **Default:**
      - names = the CHECKED outcomes of MOVES Findings that lie in other categories, excluding outcomes NOT_MEASURED in this catalogue version, so the cold Protect row has no guard in B;
      - sentence-case the first letter only;
      - join as "A and B" / "A, B and C". Kobo gives "Reliable service and battery and generator life" (B.7 #3).
20. **Signals in a CHECKED category.**
    - F-108 (evidence gap) is CHECKED on MG-2. The mock's Cost row lists it with no "checked here as a safeguard" suffix (`outcomes.js:64`).
    - **Default:** signals never get the suffix. The order is MOVES Findings by title, then signals (MOVES before CHECKED), then CHECKED Findings.
    - Backend-delivered texts in rows (Finding titles, `cooling.text`) render verbatim and are not vocabulary-filtered. If a producer title trips the w1 scan in a capture or test, I will stop and report.
21. **Domain Action rows.**
    - `work/domain_action_index.py` returns domain rows that are always OPEN (:47, :473), but also W1 rows whose state comes from the store (:441-446). §1.4 assumes cold and EV Actions are never applied.
    - **Default:** cold and EV use domain rows only, and W1 rows are ignored on the board. If W1 rows should count, say which states mean in hand.

### Work, plans and cases
22. **Case kind, href and labels.**
    - Work-index rows have no `kind` field. The read is per kind (`"incidents"`/`"maintenance"`, `work/site_index.py:41`). `url` is always None.
    - The window filter is `[from, to)`, at most 31 days. Requests filter on `created_at`.
    - ASSIGNED is not a state (ASSIGN leads to IN_PROGRESS). VERIFICATION_WINDOW cannot be reached.
    - **Default:**
      - two reads, with kind set from the call;
      - request href `/maintenance/requests/{case_id}`; incident href `/sites/{c}/work`;
      - the In-hand label is "Open" or "In progress";
      - an estate window over 31 days is clamped to the last 31 days for the work read, and the packet says so.
23. **Plans: which asset, which state.**
    - `select_preventive` (`work/global_index.py:388`) yields only DRAFT plans (ACTIVE never appears; any other state raises, :400). It takes a `sites` list, so I call it with the one Site.
    - Cold "plans on the generator asset" and "on the compressor asset" need an asset-type match. Rows carry `asset_id` and `asset_label` = "{asset_code} · {asset_type}".
    - **Default:** match on the Foundation asset type taken from `asset_label`'s type part. I will confirm the exact type tokens for the cold generator and compressor in B3. If they are absent, the contributor reads "No preventive plan recorded".
    - Mini "Generator": any RUN_HOURS plan on the Site.

### Cold composer (B3)
24. **Cold keys the spec names that do not exist** (`analytics/cold_site_reads.py`).
    - **Chamber temperature "Peak {peak}°C".**
      - `temperature_summary` has `latest_deg_c` but no peak (:417).
      - **Default:** take the peak from the excursion Finding read if it carries one. Otherwise the text is "Not available yet · peak temperature not read", and the limit is shown only in the headline.
    - **Cooling recovery.**
      - `cooling` is `{state ∈ LIMITED|UNAVAILABLE|CONTRADICTORY, text, …}` (:374). It has no restart or comparison key.
      - **Default:** when LIMITED, the text is "Restarted with power; comparison incomplete" with confidence "Medium". Otherwise the text is `cooling.text` verbatim with readiness confidence.
    - **Causal strip.**
      - The strip is a list of `{step, state, …}` (:442), with no gap flag.
      - **Default:** a step whose `state` is not an observed state counts as "not recorded". I will name the exact state values in B3.
      - An empty strip gives "Not available yet · no backup event in this window", and the headline reads "partly reconstructed".
    - **Backup start.** `backup_summary.observed_success > 0` gives "Automatic start recorded".
25. **Cold headline minutes.**
    - `episode_bounds` is `{start{earliest, latest}, end{earliest, latest}}`.
    - **Default:** lo = end.earliest − start.latest, and hi = end.latest − start.earliest, both rounded to whole minutes. If lo < 0, lo is set to 0.

### EV composer (B3)
26. **EV keys.**
    - The session counts are in `denominator` (`analytics/ev_reads.py:26` COUNT_KEYS), not in `energy`. `energy` has `complete_kwh`.
    - `needs_attention` items are `{code, text, link}`, with no counts.
    - **Default:**
      - "{kwh} kWh in {n} complete sessions": `energy.complete_kwh` and `denominator.completed`;
      - Protect headline "{i} interrupted · {u} unknown of {n} sessions": i = `fault_aborted`, u = `incomplete`, n = `started`;
      - Session service uses the same i and u;
      - Assure session records use `incomplete`.
    - `consequence_summary` has no eligibility, only `state` and `amount`. The Grow headline uses the amount when it is non-null and `state` is PRICED. Otherwise it reads "Gross tariff estimate not available yet". It uses the same formatter as Q14.
    - Health rows (`analytics/ev_depth.py:184-186`) have **no date**.
      - **Default:** the text is "Fault recorded on {label}" with no date. "Fault on {date}" needs a session-time lookup that the spec does not provide.
    - "Investigate connector {label}": the label is the connector with `known_unavailable_seconds > 0` (`analytics/ev_availability.py:184-196`). Otherwise it is the first `CONNECTOR_FAULT` health row's label, and otherwise the Finding title.
    - Unknown spans are `spans[].state == "UNKNOWN"`.

### Frontend (B5, B6)
27. **Grow card value text.**
    - B6 says "{lead headline …}, e.g. '18–20 kW unused'". The Grow headline is "{low}–{high} kW of daytime solar unused" (§B.4), so the two strings differ.
    - **Default:** the card value is the headline verbatim, with tone `green` when it is set. It falls back to the existing MissingClaim when no Site's Grow row is OPPORTUNITY, or when the summary fails. Detail and basis stay as A built them.
28. **Earlier column wire.** Addendum 2 supersedes three passages: §B.1 "`earlier: null` means … Not available yet", §B.2 "Empty Earlier … `earlier: null`", and the §B.5 table cell.
    - **Default:**
      - `earlier` is always an array on the wire and in the TS type;
      - `earlier_empty_text` is set exactly when the array is empty;
      - "None recorded" appears only when the field is absent.
    - Not-measured rows still have `earlier: []` and `earlier_empty_text: null`, and are not rendered as a column.
29. **Explainer dialog.**
    - No shared primitive exists. jsdom does not implement `HTMLDialogElement.showModal` reliably.
    - **Default:** use a native `<dialog>` with `showModal()` when available and the `open` attribute otherwise. Escape closes it, focus returns to the `i` button, and the close button gets first focus. Tests stub `showModal`.
    - Issue-kind class `gap` and `finding` have no mock CSS (`outcomes.css:37-38`). Both use the neutral token style.
30. **Retired mini cards.**
    - `ObjectiveCards` (`SiteWindowOverview.tsx:631-708`) is the only render of the `OverviewMiniReads` Service, Fuel and Renewable cards on the overview. The H3 tests (:858, :902) assert that every read is named.
    - **Default:** remove the cards per doc §6.4 deviation 1. The mini reads stay fetched only if something else still uses them; otherwise the fetch is dropped. Update the H3 tests to assert the board instead. This is recorded under R540.
31. **Board Postgres tests (B.7 #2).**
    - `test_out_b4_board_postgres.py`, "one per domain on the producer builders".
    - **Default:** reuse the scenario builders that the existing `test_w502_*`, `test_w504_*` and s602b/w403 Postgres tests already use. I will use no producer CLI. Database names use the prefix `assetops_out_b_…_test`, each dropped by its own command.
    - The Kobo case is s602b `estate`; if it lacks a Finding, then w403. I record the actual row states per B.7 #2.
32. **Known failures.** The B gate ignores, by name, the 3 `w1f4VerificationStructure` vitest failures and the 2 `w303` backend failures that A listed (`OUT-A-packet.md:99-108`). Confirm that the same list applies to B's `-Tier all` run.
