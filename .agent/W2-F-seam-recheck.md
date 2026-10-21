# W2-F seam re-check after the W4-01, W3-01 and W4-02 merges

Read-only check of `tasks/W2-F-structural-fixes.md` and `.agent/W2-F-build-spec.md` against merged `main` at `449e48e1`, in worktree `AssetOpsV1-plan2`. Spec line numbers refer to `.agent/W2-F-build-spec.md`. No checks were run, because this is a seam read, not a build review.

## Result

- **Already fixed by a later slice: none.** All 14 root causes are still in the merged code. W3-01, W4-01 and W4-02 moved some lines but did not change any of the 14 behaviours.
- **24 open questions: 2 Blocker, 12 Should, 10 Nit.**
- Most findings can take the literal fix as written. The exceptions:
  - **H1:** the rule cannot be built from the selected basis that `_capabilities` sees today.
  - **M8:** the route the fix names does not exist, and the proof it asks for cannot be made.
  - **M12:** the multiset change is correct, but it collides with the final W4-03 literal.

## Per-finding seam status

| Finding | Root cause still present? | Cited seam today | Literal fix and test still apply? |
|---|---|---|---|
| H1 | Yes. `cold_site_reads.py:453-456` gives SUPPORTED when there is a compressor role and 2 or more points. `:458-461` gives SUPPORTED when there is an eligible excursion and `bounds_ok`. | `_capabilities` is at `cold_site_reads.py:424-476`. Overview cooling comes from the same capability (`:256,264`, `_cooling` at `:304-311`). The frontend row helpers are at `coldSiteViews.tsx:290-302,786-797`. | **Partly.** The predicate cannot see ordered running or in-band data (B1). Seven side questions are open (S1-S7). The named test files exist. |
| M2 | Yes. `needed()` returns `—` when the list is empty: `ColdFoundationViews.tsx:487-494`, `EvFoundationViews.tsx:520-527`. | Cold rows are at `:505-535,589`. EV rows are at `:568,577`. Commissioning is at `:483` and `:518`. | Yes (N3). |
| M3 | Yes. The strip and tiles depend on `o`/`f`/`e` loading: `coldSiteViews.tsx:774-783` (evidence) and `:1191-1218` (financials). The footer is at `:972-974`. | `SelectedWindowBar` is at `:380-392`, and it takes a read, not a query. | Yes (N7). |
| M4 | Yes. | `ColdAssessmentViews.tsx:422`, not `:420`. Also `src/test/v69PanelTitles.ts:33`. | Yes. The registry override and pinned tests also need changing (N0). |
| M5 | Yes. | Cold: `coldSiteViews.tsx:1184,1195`. EV: `EvSiteViews.tsx:1111,1126`. | Yes (N9). Update the pinned assertions at `evSiteMoneyRoutes.test.tsx:467,497` and `coldSiteViews.test.tsx:773`. |
| M6 | Yes. | Temperature: `ColdAssessmentViews.tsx:288`. Financials: `coldSiteViews.tsx:681-686`. | Yes, for the two screens the fix names. Two more presentations are not covered (S8). |
| M7 | Yes. | `ASSUMPTION_ROWS` is at `coldSiteViews.tsx:161-165`. `AssumptionValues` is at `:1358-1366`. The Assumptions row is at `:1379`. | Yes (N6). |
| M8 | Yes. | `EvSiteViews.tsx:597-599`, not `:590`. The test is still at `evSiteMoneyRoutes.test.tsx:603`. | **No.** `p.routes.sld` does not exist, and the SLD route takes `?at=` only (B2). |
| M9 | Yes. The strip shows the evidence chip and provenance only. | `EvSiteViews.tsx:513-517`. | Partly. The field mapping clashes with stored `claim_level` (S9). |
| M10 | Yes. | `short` is at `EvSiteViews.tsx:147` (uses `:480,1008`) and `EvAssessmentViews.tsx:119` (uses `:341,619,660`). Cold Analysis is CSS clipping, not code: `.cold-site-clip`, `w2-cold-site.css:67-71`, used at `coldSiteViews.tsx:1071`. | Yes (N1). |
| M11 | Yes. | `EvSiteViews.tsx:784`. A second occurrence at `:889-890` is not cited. | Partly (S10). |
| M12 | Yes. | `Subtabs` is at `EvSiteViews.tsx:353-378`, not `:344-357`. | Yes for W2-F itself. It conflicts with the W4-03 final literal (S11, N4). |
| M13 | Yes. | Cold `FindingStatus`: `ColdAssessmentViews.tsx:835-842`. EV `FindingStrip`: `EvAssessmentViews.tsx:612-629`. Pinned tests: `evAssessmentRoutes.test.tsx:431,596,669`. | Partly (S12). |
| M14 | Yes. | `EvFoundationViews.tsx:823-830`. `label()` at `:821-822` already yields `Charger ${slot+1}`. | Yes (N8). |

## Questions an implementer would have to decide alone

### Blocker

**B1. H1: the selected basis that `_capabilities` reads cannot express the ordered recovery rule.**
- The stored chain has exactly one `COMPRESSOR` step and one `PROBE` step:
  - `COMPRESSOR` is the *first* compressor state after the bus.
  - `PROBE` is the first probe after that compressor record (`analytics/cold.py:616-620`).
  - `ColdStep` has no value or outcome (`cold.py:187-191`).
- `_capabilities.steps()` returns states only (`cold_site_reads.py:435-436`).
- The step outcome exists only at read time, joined from the evidence in `backup_chain` (`postgres_assessment_store.py:2113-2118`).
- So, when the compressor reads OFF and then RUNNING, the chain never holds the later RUNNING record. Whether the first post-interruption probe is in band is also not stored.
- The unit harness calls `_capabilities(None, snap)` with no connection (`backend/tests/test_w204_cold_reads.py:458-462`).
- The implementer would have to decide three things:
  - Whether to join the evidence values or later accepted facts inside `_capabilities`. That is a DB read and breaks the harness. The alternative is to change the `cold.py` analytic, which changes stored assessments and needs a recompute.
  - What the "off/failure observation" is: the GRID loss, or a compressor OFF reading.
  - Whether "subsequent in-band reading" means the chain's `PROBE` step or any later accepted probe.
- **Ruling needed:** the data source, the interruption anchor, and the probe rule. Also confirm that this is not a new observed claim (task:7).

**B2. M8: there is no EV SLD route on `EvSiteRoutes`, and the SLD cannot carry window or cutoff.**
- `evSiteRoutes()` defines overview, evidence, analysis, financials, assumptions, sessions and finding, but no `sld` (`shell/evSiteRoutes.tsx:14-24`).
- The Foundation SLD address takes only `at` and `component` (`shell/operatorSiteRoutes.ts:89-102`; `SiteFoundationFrame.tsx:75`).
- So the spec's `sel(p.routes.sld, o!.window)` (spec:32) cannot be written. The required proof that the route "renders the same selected Site/window/cutoff" cannot be met either.
- There are two precedents:
  - Cold Q-R6 uses `at=to` (`cold_site_reads.py:404`).
  - W3-03 labels a target that drops the cutoff `Opens current Site view`.
- **Ruling needed:**
  - Which link to use: `siteFoundationViewHref(siteId, "sld", window.to)`, or a backend `links.sld`.
  - Whether the dropped cutoff is labelled.
  - What the integration assertion proves instead.

### Should

**S1. H1: where the missing-basis copy comes from.**
- The Evidence row's "What is missing" uses only `missing_roles`. When it is empty, it falls back to `Coverage or claim basis incomplete` (`coldSiteViews.tsx:788-789`).
- The exposure row always appends `· Stock identity and value are not declared` (`:795`).
- The spec gives literal Limited-cooling text (spec:15), but it does not say where that text comes from:
  - backend `limitation`, which today is the generic `_limits(snap, analytic)` at `cold_site_reads.py:475`;
  - a new field; or
  - a frontend constant.
- The exposure stock/rule list is described ("explicit … list", spec:25) but not given as literal text.

**S2. H1: the Overview cooling text becomes false.**
- `COOLING_TEXT["LIMITED"]` reads `Cooling response has incomplete compressor or chamber readings` (`cold_site_reads.py:80`). For the stocked fixture both readings exist; what is missing is the ordered recovery.
- The Overview note hard-codes `· Recovery comparison not assessed` in every state (`coldSiteViews.tsx:468`).
- The spec says Overview keeps that phrase "until same ordered recovery" (spec:25), but gives no replacement text for the Full state and no new LIMITED sentence.

**S3. H1: existing assertions contradict the new rule, and the spec does not mark them superseded.**
- `test_w204_cold_reads.py:473` asserts that no chain plus a compressor role gives `COOLING_RESPONSE == LIMITED`. The spec says no chain gives None.
- `:477-481` asserts that an excursion without proved bounds gives `PRODUCT_EXPOSURE == LIMITED`. The spec says no product identity or rule gives None.
- `:247-248` couples cooling state to `COOLING_TEXT`.

**S4. H1: the "partial product basis → Limited" and "Full" exposure states cannot be reached.**
- The cold assumptions read always returns `items: []` and `NOT_SUPPORTED_IN_W2` (`cold_site_reads.py:598-604`). `_capabilities` never reads assumptions.
- So in W2, PRODUCT_EXPOSURE can only be None or Contradictory.
- The implementer would have to decide whether to wire assumptions into `_capabilities`, or to treat Limited as reachable only in the unit harness.
- The required test (spec:25) lists both states.

**S5. H1: a side effect removes the stock prompt.**
- `exposureConsidered` (`coldSiteViews.tsx:755`) is true only when exposure is LIMITED, SUPPORTED or CONTRADICTORY.
- After H1, the stocked fixture is None. That hides `Declare stock identity and value` (`:953-959`), and when no roles are missing the panel collapses to `Next evidence not identified` (`:937-938`).
- That is the opposite of the intent. Key the prompt on whether an excursion exists, not on the capability state.

**S6. H1: which fixture to use.**
- Task acceptance says the "recorded-normal fixture" (task:25).
- `contract-fixtures/w2/cold/normal.json` has no excursion (`high_1915: null`), so exposure is already None there.
- The audit's stocked capture (compressor off at 19:05, 19–23 °C·min) matches `excursion.json` (`start_result_at 19:05`, highs 4.1 and 4.2).
- Name the manifest or manifests for `test_w2f_recovery_and_exposure_truth_across_selected_reads`.

**S7. H1: a new contradiction between screens.**
- The Financials tile and bridge keep the label "Product exposure" with `Unpriced · at least 19 °C-minutes` (`coldSiteViews.tsx:1177,1199-1211`, consequence kind `PRODUCT_EXPOSURE`).
- Evidence will now say Product exposure **None**.
- These are two different claims under the same label, which is the pattern H1 exists to remove. Rule whether the Financials label becomes thermal exposure, or whether it keeps the mock label with a qualifier.

**S8. M6: two presentations the fix does not cover.**
- The cold Finding excursion shows `Exposure size` from the Finding claim `degree_minute_bounds` (`ColdAssessmentViews.tsx:955,994`).
- The cold Overview consequence card uses `consequence_summary.quantity` (low 19, high null; `test_w204_cold_reads.py:239`).
- The spec labels only Temperature and Financials (spec:30). Say whether these two take the excursion-estimate label or the consequence-basis label.

**S9. M9: the field mapping clashes with stored `claim_level` and with M13.**
- EV `status.claim_level` is:
  - `OBSERVED` for complete coverage;
  - `BOUNDED` for an incomplete session or a meter gap;
  - `UNKNOWN` or `CONTRADICTORY` otherwise (`analytics/ev.py:763-770`, projected at `postgres_assessment_store.py:2683-2684`).
- The spec shows stored OBSERVED as "Confidence: Bounded" and stored BOUNDED as "Confidence: Limited" (spec:33). M13 uses the same claim words directly (Bounded is Bounded, spec:37).
- The spec's state table says interrupted gives Limited. Under its own rule, an interrupted fixture with complete coverage would give Bounded.
- The source for `Needs attention` is not named: `findings.count > 0` or `needs_attention` codes.
- `status.state` values are `OBSERVED_SESSIONS`, `NO_SESSIONS_OBSERVED` and `CONTRADICTORY` (`ev.py:771-776`). There is no "abort" state.
- **Ruling needed:** the exact field-to-word table.

**S10. M11: a second site, and which copy wins.**
- `No required role missing` also appears in the `Evidence request details` disclosure (`EvSiteViews.tsx:889-890`). The spec does not mention it.
- The backend already sends a capability `limitation`, for example `Availability is not assessed.` (`ev_site_reads.py:51`).
- The spec gives literal strings and detection predicates ("without an observed connector-state denominator", "without accepted diagnostics and vehicle request"), but does not say which fields test them, or whether the literal or the backend `limitation` wins.

**S11. M12: the multiset depends on build order between W2-F and W4-03.**
- Today the guard literal is `Alternatives, Scenarios, Cooling, Recommendation, Recommendation, Availability, Energy / site power` (`tools/checks/navigation-truthfulness.ps1:747-748`).
- The single `Scenarios` is the shared `FinancialsSections` tab (`SiteAnalyticsFrames.tsx:746`), used by mini and cold.
- W2-F correctly adds a second `Scenarios`.
- W4-03 B4 fixes the final literal with **one** `Scenarios`: `Scenarios, Cooling, Recommendation×2, Availability, Energy / site power, Analysis` (`W4-03-build-spec.md:539-546`). Its Q24 at `:383-392` is stale.
- Whichever of W2-F or W4-03 unit 6a/6b lands second breaks the guard. Neither spec names the order.
- **Ruling needed:**
  - The W2-F literal is the current list plus `Scenarios`.
  - The W4-03 final literal is `Scenarios, Scenarios, Cooling, Recommendation, Recommendation, Availability, Energy / site power, Analysis` if W2-F merges first.
- W4-02 did not touch this multiset; its tabs go through `RENDERABLE` (`W4-02-build-spec.md:158`).

**S12. M13: confidence repeats the evidence phrase, and the words do not match.**
- The cold strip already prints `evidence {claimWord(claim_level)}` (`ColdAssessmentViews.tsx:839`). `Confidence: {claimWord(claim_level)}` would show the same field twice.
- The spec says to keep "evidence coverage/source" as a separate phrase, but the cold Finding has no named coverage field.
- `claimWord("UNKNOWN")` returns `Not established`, not `Unknown` (`coldAssessmentWords.ts:34-41`).
- In the EV mapping, `Limited` has no `claim_level` source (EV levels: OBSERVED, BOUNDED, UNKNOWN, CONTRADICTORY).

### Nit

- **N0. M4 has more to change than the spec says.**
  - Delete the `"temperature:3": "How each limit is set"` override and its deviation-18 comment (`frontend/src/test/v69PanelTitles.ts:32-33`).
  - Update the pinned title tests at `coldRoutes.test.tsx:318,351,430-431,496,513,590,594,659`. Line 431 asserts that `Claim boundary` is absent.
  - Update the doc comment at `ColdAssessmentViews.tsx:62`.
- **N1. M10 details.**
  - No DTO has `finding_code`; a grep over the backend and frontend finds nothing. So the Finding label is always the full UUID.
  - The EV session display is `external_session_id` (`evAssessmentClient.ts:66,133`).
  - The prefix format is not given (`F-…` or `F …`).
  - The cold fix is a CSS change (`w2-cold-site.css:67-71`), which the spec does not name.
- **N2. Line drift.**
  - H1 is at `:458-461`.
  - M4 is at `:422`.
  - M8 is at `:597-599`.
  - M12 is at `:353-378`.
  - M14 is at `:823-830`.
- **N3. M2 wording.**
  - The spec says "may say `Nothing further recorded`". Say whether it is required.
  - The role-gap text is the readiness message string (`m.message`, `ColdFoundationViews.tsx:497-500`), not a role label.
- **N4. M12 guard mechanics.**
  - The guard counts source literals, so the entry must be one literal `<UnavailableTab label="Scenarios" />` inside the financial branch of `Subtabs`. A computed label in the `items` loop trips "non-literal label" (`navigation-truthfulness.ps1:794-803`).
  - The fixtures define only `$ev = EvAssessmentViews.tsx` (`navigation-rail-fixtures.ps1:130`). The negative fixture "EV Scenarios dropped" needs a new `EvSiteViews.tsx` module variable.
- **N5. Stale wording in the spec.**
  - The baseline (spec:3, "before W3-01's unmerged changes") and the ordered handoff (spec:9) are out of date. W4-01 and W3-01 are both on `main`.
  - Restate the baseline as `main` at the merge after W4-02.
- **N6. M7:** the "both declared → product display" and "historical → selected historical values" states cannot be reached, because assumptions items are always `[]`. Allow a frontend-only synthetic DTO test, and give the product format and currency.
- **N7. M3: invalid-window refusals.** When the URL window is itself invalid (`ColdAssessmentViews.tsx:138`, `invalid-window`), say whether the requested date line is printed or suppressed.
- **N8. M14:** "slot identity from selected Foundation topology" amounts to the slot index. The diagram uses `Charger ${j+1}` (`SiteSingleLineDiagram.tsx:1609`), and `label()` already gives it.
- **N9. M5: cold bridge rows span two reads.** The start row comes from `findingsRead` (`coldSiteViews.tsx:1178-1183`). Say what the chip shows when the financials read loads but the findings read is refused.

## Commit sizing and "read only these sections" index

Units 2-5 are each one builder run. **Split unit 1 in two:**
- **1a** is the backend H1 change, after the B1 ruling.
- **1b** is the cold frontend truth work.

The reason: H1 now needs a DB read or an analytic change, plus test rewrites. Packing that together with four frontend findings is too much for one run.

The units overlap on M5, M10 and M13. Assign them like this:
- unit 1b: cold M13;
- unit 2: cold M5 and cold Analysis M10;
- unit 3: the EV overview timeline M10;
- unit 4: EV M5, EV Analysis and Finding M10, M11, M12, and EV M13.

| Commit | Findings | Read only |
|---|---|---|
| 1a backend truth | H1 backend | spec:11-17, 25; audit:19-27; `cold_site_reads.py:35-55,77-83,250-311,424-476`; `cold.py:187-206,576-640`; `postgres_assessment_store.py:2098-2135`; `test_w204_cold_reads.py:206-250,405-482`; `contract-fixtures/w2/cold/{normal,excursion}.json`; B1, S2-S4, S6 |
| 1b cold truth UI | H1 UI, M4, M6, M7, cold M13 | spec:11-17, 25, 28, 30, 31, 37; audit:19-27, 45-63, 93-97; `coldSiteViews.tsx:108-125,161-165,285-310,455-500,681-686,743-800,930-975,1169-1240,1350-1400`; `ColdAssessmentViews.tsx:280-295,415-435,835-842,950-1000`; `coldAssessmentWords.ts:30-45,90-97`; `src/test/v69PanelTitles.ts:25-35`; `coldRoutes.test.tsx` (title assertions at N0); S1, S5, S7, S8, S12, N0 |
| 2 cold frame and counts | M3, cold M5, cold M10 | spec:13, 27, 29, 34; audit:35-44, 50-54, 75-81; `coldSiteViews.tsx:205-230,315-395,501-520,743-790,965-975,1006-1080,1169-1240`; `ColdAssessmentViews.tsx:112-160`; `w2-cold-site.css:60-75`; `coldSiteViews.test.tsx:760-780`; N1, N7, N9 |
| 3 EV config and overview | M2 (cold and EV), M8, M9, M14, EV timeline M10 | spec:26, 32-34, 38; audit:29-34, 64-74, 98-101; `ColdFoundationViews.tsx:478-600`; `EvFoundationViews.tsx:515-580,770-860`; `EvSiteViews.tsx:140-150,270-300,470-520,585-600`; `shell/evSiteRoutes.tsx`; `operatorSiteRoutes.ts:76-102`; `evSiteMoneyRoutes.test.tsx:595-610`; `SiteSingleLineDiagram.tsx:1600-1612`; B2, S9, N3, N8 |
| 4 EV evidence, money, Finding | EV M5, EV Analysis and Finding M10, M11, M12, EV M13 | spec:29, 34-37; audit:50-54, 75-97; `EvSiteViews.tsx:350-380,730-800,870-900,1000-1012,1100-1135`; `EvAssessmentViews.tsx:115-122,335-345,610-665`; `evAssessmentClient.ts:110-150`; `ui/UnavailableEntry.tsx`; `navigation-truthfulness.ps1:718-827`; `navigation-rail-fixtures.ps1:125-175`; `W4-03-build-spec.md:539-546`; pinned tests at `evSiteMoneyRoutes.test.tsx:467,497` and `evAssessmentRoutes.test.tsx:431,596,669`; S10, S11, S12, N4 |
| 5 integration | none new | task:23-28; spec:40-42; audit whole; `backend/TESTING.md`; `tools/layout-evidence.mjs` usage; the 22-screen list at audit:103-128 |
