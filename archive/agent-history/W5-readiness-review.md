# W5-01 / W5-03 build-spec readiness review

Reviewer: independent Claude reviewer (did not author the specs), 2026-10-22.
Tree: `C:\Users\assef\Bineyame\AssetOpsV1-plan2`, `main` at `f0dfeb6f` (clean, read-only apart from this file).
Gate: `.ai/ROLE_CONFIG.md` "Build-Spec Readiness Gate For W5 And W6" and the 13 W3/W4 lessons.
Specs: `.agent/W5-01-build-spec.md` (cited `S1:line`), `.agent/W5-03-build-spec.md` (cited `S3:line`); tasks `tasks/W5-01-cold-depth.md`, `tasks/W5-03-ev-depth.md`.

Tags: **BLOCKER** means a builder would have to decide something or would fail. **NOTE** means it should be fixed or acknowledged but does not stop a build.

## Checks run

| Check | Result |
| --- | --- |
| `powershell -NoProfile -ExecutionPolicy Bypass -File tools/check-all.ps1`, with `.venv\Scripts` first on PATH (pytest 9.1.1, Python 3.12.10) | **11/11 guards PASS, exit 0.** The estate guard self-test passed: 3 tests in 96.7 s. Dependency registry: 12 open of 42. Missing-claim scan: 41 tagged uses, 10 baselined. Screen ledger: 110 screens and 258 panels valid. |
| Mock measurement: a scratch copy of `tools/measure-mock-panels.mjs` with `--no-sandbox`, run on the 7 screens at 1440×1000 and 390×900 | Ran. Every base page and block height in the S1:43-45 and S3:44-47 tables reproduced exactly, and so did scroll widths of 1425/1425 and 390/390. I did not rerun the worst-content pass. All 8 Chrome processes it started were stopped. |
| v69 panel titles (`v69-rendered-panels.json`) | All 14 titled panels in the specs match exactly. |
| Alembic chain | Head is `0030_w4_mini_decisions`, with `down_revision="0029_w4_mini_depth"` (`backend/migrations/versions/0030_w4_mini_decisions.py:26-27`). There is no 0031 or 0032 file. `0032_w5_cold_scenarios` with down `0030` is consistent. |
| Producers | Traced in code, not run. Cold and EV replay chains need a `*_test` DB, and no DB was created. |

---

## W5-01 cold depth (`.agent/W5-01-build-spec.md`)

### Shared contract and all units

1. **BLOCKER: the one-clock rule cannot be met with the named cold producers. The historical cutoff selects nothing.** (S1:51, 55, 59, 65, 71)
   - The spec pins `2026-10-06T20:05:00Z` for "read/pin/injected now" and a historical selector of `19:55:00Z`.
   - The cold selection cutoff is `known = known_at or watermark`, where watermark is `max(ingestion_disposition.decided_at)` (`analytics/adapters/postgres_assessment_store.py:2000-2002`).
   - In the W2-02 cold chain, `decided_at` is wall-clock time. The chain uses `BatchIngestionService(PostgresEvidenceLedger(URL), lambda: datetime.now(timezone.utc))` (`tests/test_w202_cold_replay_postgres.py:222`), and the ledger with no override uses `SELECT clock_timestamp()` (`evidence/adapters/postgres_evidence_ledger.py:525-528`).
   - Effect of `known_at=20:05` or `19:55` on 2026-10-06: it is earlier than the watermark, so `historical=True` (`postgres_assessment_store.py:2047`). It is also earlier than every run cutoff, so no row is selected. Every "current" capture would read HISTORICAL with empty arrays.
   - The merged producer does it differently. `test_late_reading_pending_then_historical` uses window `to=20:05` (`tests/test_w204_cold_reads.py:44`) and takes its historical cutoff from the first response, `cutoff = before["window"]["known_at"]` (`:390`), not from a constant.
   - Fix: restate the clock as window `[19:00, 20:05)`, current reads with no `known_at`, and the historical cutoff equal to the watermark captured before `advance_late()`. Alternatively, rule that C1 adds a decision-clock override to the cold chain, as the EV chain has.

2. **BLOCKER: link Site token and link kind contradict the code.** (S1:21)
   - The spec says "Links use imported Site UUID … `/sites/{site_id}/…`".
   - The UI `site_id` is the public Site code: `"site_id": site.site_code` (`backend/assetops_backend/sites_api.py:212`). Cold UI routes are built from it (`frontend/src/shell/coldSiteRoutes.tsx:21-31`).
   - Existing cold read `links` are API URLs keyed by code, `/api/sites/{code}/cold/...` (`analytics/cold_site_reads.py:178-180`), and the frontend translates them with `coldUiHref`.
   - Fix: state whether the new `links` are API links (and their exact key names) or UI routes, and that the Site token is `site_code`.

3. **BLOCKER: file ownership misses files the cards must edit.** (Lesson 7; S1:51, 55)
   - C1 must reuse `cold_site_api.opened`, but `opened` is a closure nested inside `build_cold_site_router` (`backend/assetops_backend/cold_site_api.py:65`). It cannot be imported without editing `cold_site_api.py`, which C1 does not own. Rule: refactor it in C1, or duplicate the gate.
   - C2 must replace the `Cooling` unavailable tab, which lives in `frontend/src/sites/ColdAssessmentViews.tsx:782`. C2 lists `coldSiteViews.tsx` instead. The guard fixture names the same file: `$cold = "frontend/src/sites/ColdAssessmentViews.tsx"` (`tools/checks/navigation-rail-fixtures.ps1:143`).
   - C1's "router test" names no file, and no `backend/tests/*router*` or `test_main*` exists.

4. **BLOCKER: registry rows are not given as literals.** (Lesson 1; S1:59, 69)
   - C3 and C5 name only `(screen,index) title`.
   - The pilot registry has no rows for `cooling`, `cold-health` or `cold-scenarios` (`frontend/docs/architecture/v69-dependency-registry-pilot.json` `panels[]`).
   - Each new row needs `area`, `requires` (node IDs, some of them new), `status` and `reason`. The area must equal the brief area, `cold-chain` (`check_v69_dependency_registry.cjs:281-282`).
   - None of these values, and no new node IDs for the read, UI or comparator, are specified. The check-all pass on the current tree does not cover rows that do not exist yet.

### C1: selected cold depth read

5. **BLOCKER: the context rows have no source role, and their literals contradict the producer.** (S1:19, 29-31)
   - Five context rows are "Observed only with exact accepted row", but no row names its role.
   - Only `door_event` exists, as a CONTEXT link (`analytics/cold.py:55, 517`). There is no ambient, loading or defrost role. "Continuous power" could mean `grid_power_event` or nothing.
   - The C1/C2 positive producer, `cold-backup-failed.yaml:23-30`, forces `DOOR_OPEN` at 19:10 and `DOOR_CLOSE` at 19:11. That would make `Door-open duration` read Observed.
   - The fixed literals still say `loading and door context is missing` and `Loading and door records missing`.
   - Fix: map each row to a role (or to "always Unknown") and make the header and card copy conditional on that mapping.

6. **BLOCKER: the derivation of some Cooling DTO fields is unspecified.** (S1:19)
   - No rule is given for `observed_restart_at`, `observed_return_to_policy_at`, or the "selected accepted compressor/probe points".
   - The mapping from the capability (`LIMITED`/`CONTRADICTORY`/`UNAVAILABLE`, `cold_site_reads.py:79-84`) to `recovery_state` (`LIMITED`/`CONTRADICTORY`/`UNKNOWN`) is also not stated.
   - W2-F S2 says the start chain stores only first steps. A non-null `observed_restart_at` therefore risks implying an ordered recovery.
   - Fix: give the source column or step for each field, or rule them always null for W2 producers.

7. **NOTE: the provenance selection token is not named.** (S1:17)
   - `public_provenance` resolves revision-ID selections (`cold_envelope_selection`, `evidence/public_provenance.py:154`), not evidence-ID sets.
   - Fix: name the function to call. Reusing `envelope_on`'s `source_provenance` DTO is the obvious one.

### C2: Cooling page

8. **BLOCKER: header and card copy cover only one recovery state.** (S1:29-30)
   - `Comparison limited` and `Confidence: Low` are fixed.
   - There is no literal for `recovery_state=CONTRADICTORY` or `UNKNOWN`, which covers the empty window and an unassessed capability. The existing Overview shows `Contradictory` and `Unknown` chips for these (`frontend/src/sites/coldSiteViews.tsx:491`).

9. **NOTE: the Cooling breadcrumb differs from its sibling subtabs.**
   - The spec crumb is `… › Performance › Cooling`.
   - The sibling Temperature and Backup pages end at `Performance` (`ColdAssessmentViews.tsx:766`).
   - Fix: confirm this is intentional and that siblings stay unchanged (lesson 6).

10. **NOTE: the refusal capture producer is a unit test.**
    - `cooling-refused` names `test_refusal_codes_without_database`, which is a fake-client unit test (`tests/test_w204_cold_reads.py:162`), not a live page producer.
    - Fix: state the live mechanism, such as a foreign Site, a disclosure refusal, or a stopped store.

11. **NOTE: the worst-case 390 card pass did not use the real literals.**
    - The 390 card cap is 360 against a measured worst case of 344.
    - The real values are `Not established` and `Unknown`, and the 51-character note `No ordered compressor-to-policy recovery assessment` is longer than the mock's.
    - A two-column 27px value may wrap. Lesson 2 asks for the actual worst-case slot text.

12. **NOTE: the navigation fixtures need re-anchoring.**
    - Removing `Cooling` requires changing `$expectedTabs` (`tools/checks/navigation-truthfulness.ps1:752-753`).
    - It also requires replacing the negative fixture "the cold Cooling entry is dropped" (`navigation-rail-fixtures.ps1:169-170`), whose anchor string disappears.
    - Fix: state the replacement fixture.

### C3: cold Health

13. **BLOCKER: Health card notes are wrong outside the positive branch, and one state has no copy.** (S1:33)
    - `Backup generator` reads `Needs investigation` or else `Unknown`, with one note: `Failed automatic start observed; part not diagnosed`. That note is false when no failed start is selected.
    - `Temperature sensing` reads `Limited` or else `Unknown`, with `One accepted probe…`. That note is false for zero probes.
    - `condition_state=NOT_CONFIGURED` (S1:19) has no visible literal.

14. **BLOCKER: Health page composition is not stated.** (S1:59)
    - Today `/sites/{id}/health` renders `SiteHealth` for every Site type: `Physical asset condition` and `Data sources · data quality, not equipment condition` plus a notice (`frontend/src/sites/SiteHealth.tsx:291-292, 319-338`; frame `frontend/src/shell/SiteHealthFrames.tsx:59-61`).
    - "Keep S7 two-clock gateway contact separate" does not say whether the gateway Data sources panel stays on the COLDCHAIN page, or in what order.
    - The mock `cold-health` has only cards plus `Condition and evidence`. The page cap of 1200/1550 and the `expectV69Panels` assertions depend on this decision.

15. **NOTE: Health table differs from the mock.**
    - The column `Supported observation` differs from the mock's `Supported assessment` (`frontend/mockups/v69/index.html:691`).
    - The spec adds a third (probe) row; the mock has two.
    - Both may be deliberate, but they are not marked as deviations (lesson 6). The cap still has headroom: 198+45 ≤ 330 and 269+80 ≤ 430.

### C4: authored cold scenario store

16. **BLOCKER: migration columns are not literal.** (S1:65)
    - Column names and types, CHECK and constraint names, and the actor column set are not given. The mini pattern has `actor_kind`, `actor_id`, `attestation`, `authorization_basis` and `supersedes_revision_id` (`mini_decisions/scenarios.py:86-87`; `0030_w4_mini_decisions.py:69-93`).
    - The spec writes `prior`, `actor` and `correction reason`.
    - E5 inherits this "shape of W5-01 C4" (S3:72), so the gap also blocks W5-03b.

17. **BLOCKER: the command DTO and write-side refusal codes are missing.** (S1:65)
    - POST body fields are not given. The mini pattern requires `schema_version`, `idempotency_key`, `actor`, `name`, `kind`, `assumptions` and `pinned_selection` (`mini_decisions/scenarios.py:117-121`).
    - The command `schema_version` literal is not given.
    - The spec does not say whether the authored basis is client-pinned or server-resolved.
    - The POST response status and body are not given.
    - The code for a missing or non-SERVICE principal is not given. Mini uses `DECISION_WRITE_FORBIDDEN` 403 and `DECISION_STORE_UNAVAILABLE` 503 (`mini_decisions_api.py:113, 124`), but "existing cold access/503 codes" names neither.
    - The public scenario code format (`public_no`) is not given.

18. **BLOCKER: the list DTO cannot drive the pending state, and HISTORICAL is undefined.** (S1:65, 69)
    - `cold-scenarios-1` has window/watermark, items and `next_cursor`, but no `selection.state` or currentness.
    - C5 must still show `Underlying evidence is being reassessed…` for the pending capture.
    - When a row is `HISTORICAL` (superseded, or read at an earlier cutoff) is not defined.

### C5: cold Scenarios, navigation and W2-F L1

19. **BLOCKER: the cold `Scenarios` literal is shared, so the one-for-one multiset removal is not possible as written.** (S1:13, 69)
    - The only `<UnavailableTab label="Scenarios" />` outside EV is in `FinancialsSections` (`frontend/src/shell/SiteAnalyticsFrames.tsx:993`).
    - Every non-MINIGRID Site renders it, cold and other types alike (`:1180`, `:1198`, `:1236`).
    - Making cold live means changing the `scenarios` prop rule. The literal stays for the other types, so `$expectedTabs` keeps two `Scenarios`.
    - Separately, the current scenarios route renders `Scenarios are read for mini-grid sites only.` for cold (`:1185-1188`). The card does not name that branch replacement or the UI route, which is presumably `siteFinancialScenariosHref`.

20. **NOTE: the live Scenarios subtab drops the window.**
    - `siteFinancialScenariosHref` carries no query (`frontend/src/shell/operatorSiteRoutes.ts:179-181`), so the live subtab drops `from,to,known_at`, unlike the cold Overview and Assumptions links.
    - Fix: rule whether cold Scenarios keeps the window.

21. **NOTE: several fixtures anchor on the string C5 changes.** Fixtures at `navigation-rail-fixtures.ps1:156-163` anchor on `<UnavailableTab label="Scenarios" />` in `SiteAnalyticsFrames.tsx`, so their anchors may need changing.

22. **NOTE: the vocabulary scan rules for new pages are not stated.**
    - Cold page tests run the W1 vocabulary scan (`frontend/src/sites/__tests__/coldRoutes.test.tsx:269`), and that set rejects raw UUIDs and the word `watermark`.
    - The spec shows UUIDs and IDs but does not require `data-vocabulary-exempt="source-reference"` (`frontend/src/ui/ProductStatus.tsx:204`).
    - It also does not say which set (`w1` or T028) new page tests run. T028 bans `scenario(s)`, `normalization`, `load`, `running`.

23. **NOTE: the expanded basis has no cap.** `Review assumptions →` expands the exact basis, potentially many 36-character evidence IDs, but has no cap or capture. The panel cap applies only to "one row or empty".

24. **NOTE (closed item):** the L1 fix is fully specified. The refused branch is at `ColdAssessmentViews.tsx:1081-1084`, and `StatusBar` takes `label` (`frontend/src/ui/V69Layout.tsx:190-200`).

### W5-01 sizing and other notes

25. **NOTE: unit sizing.** The 5 units are within the cap, the split into W5-01a and W5-01b is correct, and every card is marked for per-unit review. C4 (migration, rules, store, service, API, cursor, idempotency and Postgres tests) is the largest card. It is acceptable only once items 16 and 17 are literal.

26. **NOTE: two state literals diverge from merged constants.**
    - Spec HISTORICAL `Read at an earlier evidence cutoff. This is historical.` versus merged `HISTORICAL_NOTE` `…; newer committed evidence exists.`
    - Spec PENDING versus merged `PENDING_NOTE` (`analytics/cold_reads.py:28-30`).
    - Both are acceptable as new literals, but the spec should say "new".

27. **NOTE: the guard dry-run paragraph is stale.** S1:13 says the estate self-test failed. With the plan2 `.venv` it passes, and check-all is 11/11.

---

## W5-03 EV depth (`.agent/W5-03-build-spec.md`)

### Shared contract and all units

28. **BLOCKER: the fixture clock and historical cutoff are incompatible with the EV chain, and the historical read would be refused.** (S3:54, 58, 62, 66, 72, 80)
    - The spec pins `16:05:00Z` for every read, pin and `now`, and passes a historical cutoff of `15:55:00Z`.
    - The EV chain's decision clock, which sets the watermark, is `FIRST_DECISION=09:00` and then `LATE_DECISION=09:05` (`tests/test_w205b_ev_replay_postgres.py:111-112, 235-238`). Scenario windows are `08:00-09:00` (`config/scenarios/ev-fault.yaml:6-8`).
    - `known_at=15:55` is later than the watermark, so the read is refused with 422 `EV_TIME_INVALID` (`tests/test_w207_ev_site_reads_postgres.py:328`).
    - A `16:05` read of the `08:00-16:00` service window is not covered by the `08:00-09:00` selection, so it reads UNKNOWN.
    - Fix: use the selected scenario window, the watermark `09:00` as the historical cutoff after `advance_late()`, and no `known_at` for current reads.

29. **BLOCKER: EV file ownership misses the files that hold the multiset entries.** (Lesson 7; S3:58, 62, 76)
    - `Availability` and `Energy / site power` are in `frontend/src/sites/EvAssessmentViews.tsx:572-573`. E2 lists `EvSiteViews.tsx` instead, and E3 lists neither.
    - The EV `Scenarios` entry is in `frontend/src/sites/EvSiteViews.tsx:380`. E6 lists `SiteAnalyticsFrames.tsx`, whose literal is the shared non-EV one (item 19).
    - E3 lists only "navigation guard fixtures", but it must also edit `$expectedTabs` in `tools/checks/navigation-truthfulness.ps1:752-753`.
    - Guard fixture paths: `navigation-rail-fixtures.ps1:144-145, 176-182`.

30. **BLOCKER: routes are missing for two new pages and one link.** (S3:35, 62, 76)
    - E2 names `/sites/{site_id}/performance/availability`. E3 names no Energy route, and E6 names no EV Scenarios route.
    - EV Financials lives at `/sites/{id}/ev/financials`, while mini and cold use `/financials/scenarios` (`operatorSiteRoutes.ts:234-246, 179`).
    - E4 links the fault row to the "exact selected Session detail", but there is no Session-detail UI route. The repo has only `sitePerformanceHref(siteId,"sessions")` (`frontend/src/shell/evSiteRoutes.tsx:21`), and searching for any `sessions/` UI path finds nothing.
    - As written, that link is dead. Fix: name a real destination or make it text.

31. **BLOCKER: registry rows are not literal.** (Lesson 1; S3:62, 66, 76) This is the same gap as item 4, for `availability`, `energy`, `ev-health` and `ev-scenarios`, area `ev`, which have no rows today. Required fields, node IDs and reason text are missing.

### E1: observed EV selected-depth read

32. **BLOCKER: the hold rule depends on a concept that does not exist.** (S3:19)
    - Each transition's effective end is "the next valid transition or the declared state validity end".
    - No such declaration exists in the Foundation or the binding roles. The only related value is the freshness cadence `ev-status-cadence` (`backend/assetops_backend/sites/ev_foundation.py:55-63`; `sites/binding_roles.py:222`).
    - Without a literal rule, the builder cannot compute `known_available_seconds`.
    - Separately, lab-published states exclude `AVAILABLE` and `DISABLED` (`backend/assetops_backend/runs/profiles.py:2080`). A positive "known available" span can therefore only come from `UNPLUGGED`.

33. **BLOCKER: an explicit no-battery Foundation cannot be expressed.** (S3:21, 34-35)
    - `stationary_battery=NOT_APPLICABLE` and `Not applicable` / `Not configured` require "the selected explicit no-battery Foundation".
    - The EV Foundation has no battery component type or property. Its edge types are `AC_BUS`, `METER`, `EV_CHARGER` and `EV_CONNECTOR` (`ev_foundation.py:49-52`), and its property keys are listed at `:55-73`.
    - The state is therefore unproducible, and E4's test "battery `Not applicable` only with explicit Foundation" has no producer. Fix: rule it always Unknown, or define the declaration.

34. **BLOCKER (sizing, a judgement against lesson 8): E1 is too large for one builder run.**
    - It adds a new interval algorithm (schedule clipping, transition spans, union, conservation) and three versioned DTOs.
    - It also carries about 20 Postgres test conditions, and its reading index includes "W2-06/07 read code": `ev_site_reads.py` alone is more than 900 lines, plus the store.
    - Fix: split into E1a (availability calculation and read) and E1b (energy and health read).

35. **NOTE: the EV STALE state has no producer.** EV `currentness_state` never returns `STALE_SOURCE` (`analytics/ev_reads.py:49-56`; asserted by `tests/test_w206_ev_reads_postgres.py:429-440`). The STALE literal (S3:27) needs a ruling: a pure-component test, or an honest "not produced".

36. **NOTE: Site token and link kind are not stated.** As in item 2, the spec does not say whether `links` are API or UI links, or that the Site token is the code. It is less explicit than W5-01, but a builder must still choose.

### E2: Availability page

37. **BLOCKER: two capture producers do not exist.** (Lesson 3; S3:58)
    - `availability-status-gap` cites an "existing late/missing-status vector", but there is no status-gap scenario: the EV scenarios are complete, contradictory, fault, interrupted, late-record and missing-meter (`config/scenarios/`).
    - `availability-no-schedule` cites "E1's schedule test". That test, `test_objective_resolves_selected_foundation_schedule` (`tests/test_w207_ev_site_reads_postgres.py:442-505`), calls the pure `objective_windows` with dicts and persists nothing. The persisted variant there, a Wednesday read, is "declared, no occurrence" with no selection, so it reads UNKNOWN, not "schedule absent".
    - The fallback "accepted-state test builder" is a new, unspecified producer.

38. **NOTE: the EV pending literal diverges from the merged constant.** Spec `New evidence is being assessed. Earlier selected results may change.` versus merged `PENDING_NOTE` `…The previous result may change.` (`analytics/ev_reads.py:29`). The spec calls the HISTORICAL and UNKNOWN literals "merged" but does not mark this one as new.

### E3: Energy page

39. **NOTE: Energy fields verified.** `complete_kwh`, `partial_kwh`, `unknown_seconds` and `supported_kwh` exist (`backend/assetops_backend/ev_site_reads.py:535-547`; `analytics/ev.py:278`), and so does `ev-site-import-limit` (`ev_foundation.py:66`). The bridge table at 390 already scrolls internally in the mock (table 320/328). The cap is satisfiable.

### E4: EV Health

40. **BLOCKER: Health page composition is not stated.** This is the same issue as item 14, on the shared `SiteHealthFrames.tsx` and `SiteHealth.tsx`. The table differs from the mock in the same way as item 15: `Supported observation` against the mock's `Supported assessment`, and three rows against two (`index.html:691`).

### E5: authored EV scenario store

41. **BLOCKER: the baseline entity is undefined.** (S3:70)
    - "The selected W2-07 complete metered-energy revision" names no table.
    - W2-07 has `ev_consequence_revision` (states `ESTIMATED`, `UNPRICED`, `WITHHELD`; `0026_w2_ev_money.py:48-60`) and `ev_session_revision`. There is no "metered-energy revision", so the refusal "no exact selected metered-energy revision" cannot be implemented as written.

42. **BLOCKER: migration, command DTO, write refusal codes, pending source and HISTORICAL rule are all inherited from C4.** Items 16-18 apply unchanged ("shape of W5-01 C4", S3:72), and C4 does not fix them.

43. **NOTE: `0033_w5_cold_work` is fixed by the wrong spec.**
    - The parent ID is set by W5-03, not by a W5-02 spec. No `.agent/W5-02-build-spec.md` exists, and `post-W2-sequence.md:18` says only `0033`.
    - Fix: the W5-02 spec must adopt the exact name.

### E6: EV Scenarios page

44. **NOTE: E6's other gaps are covered above.** Ownership is item 29, the route item 30, the pending DTO item 42, the expanded-basis cap item 23, and vocabulary and IDs item 22.

### W5-03 sizing and other notes

45. **NOTE: unit sizing.**
    - Six units, split into W5-03a and W5-03b. W5-03b has two pages plus a pipeline, within the cap.
    - E2-E4 and E6 are marked "per-unit review" in their headings, but the packet (`tasks/W5-03-ev-depth.md:26`) says they are reviewed before sub-slice merge. The two statements should agree.

46. **NOTE: the guard dry-run paragraph is stale.** S3:13 says the default `.venv` is absent. It exists, and check-all passes 11/11 with it.

---

## Summary

| Spec | BLOCKER items | NOTE items |
| --- | --- | --- |
| W5-01 | 1, 2, 3, 4, 5, 6, 8, 13, 14, 16, 17, 18, 19 (**13**) | 7, 9, 10, 11, 12, 15, 20, 21, 22, 23, 24, 25, 26, 27 (14) |
| W5-03 | 28, 29, 30, 31, 32, 33, 34, 37, 40, 41, 42 (**11**) | 35, 36, 38, 39, 43, 44, 45, 46 (8) |

Recurring themes:
- Clocks and producers do not match the merged replay chains (items 1 and 28).
- Ownership misses the files that actually hold the unavailable-tab multiset (items 3, 19, 29).
- Registry rows and scenario schema/DTO are not literal (items 4, 16-18, 31, 41-42).
- State-conditional copy is missing (items 5, 8, 13).
- Health page composition is unstated (items 14, 40).
- Two EV concepts have no backing in code: the state validity end and the explicit no-battery declaration (items 32-33).

## Verdict

**NOT READY.** The Architect should close the 24 BLOCKERs above and fold the rulings into consolidated unit cards (lesson 5). A Sonnet check should then confirm none remain before C1 or E1 is dispatched.
