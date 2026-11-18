# OUT-A pre-flight: batched questions and findings

- Slice: A, `task/OUT-A-category-labels`.
- Worktree: `C:\Users\assef\Bineyame\AssetOpsV1-outA`, at main `287a63a7`.
- Spec: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md` rev 1, read in §0, §1, Slice A and the pre-flight checklist.
- No product code was written.
- Backend paths are relative to `backend/assetops_backend/`. Frontend paths are relative to `frontend/src/`.

**Questions for the Architect: Q1–Q15.** The findings and confirmations section has no questions in it.

## Questions (need a ruling before code)

**Q1. The EV-1 label fails the vocabulary guard.** §1.2 EV table and §0.3 state that every copy string is already reworded to pass the guard. They are not all reworded.
- The EV-1 label "Buses ready to run" matches the T028 term `run` (`productVocabulary.json:10`). No gloss removes it, and the term applies on every route.
- A5 renders it in the EV Finding page Affects line ("buses ready to run, charger use"). That would fail the w1 scan (A.7 #8) and A1 test 5.
- Every other A copy string passes; I checked them with a Python port of the scanner.
- **Please rule a reworded label**, for example "Buses ready for service", and its R520 wording.

**Q2. The Affects line drops checked outcomes the mock shows.** §1.3 item rules, against mock `outcomes.js:33-34`.
- The mock's `affectsPill` (list form) filters out checked categories that are already moved. Its `affectsLine` (page form) does not filter: `catPills(a[1],true)` renders every checked category.
- Effect on the mock pages:
  - F-118 shows "Also check · Protect asset and capital (compressor life) · Optimize cost and efficiency (cost per cooling unit)".
  - F-130 shows "Also check · Protect asset and capital (charger life)".
- Under the spec's single wire, which drops these at the source:
  - F-118's line loses compressor life;
  - F-130 has no "Also check" at all.
- **Choose one:**
  - (a) keep the spec, and record a deviation (which R-ID?);
  - (b) the wire keeps the overlapping CHECKED items and the list component filters them, as the mock does. This changes the item rules and A1 test 2 for F-130.

**Q3. Order inside a pill and between pills.** §1.3 says "canonical category order" and "catalogue order". Mock `byCat` (`outcomes.js:27`) keeps first-appearance order of the moved/checked list.
- Differences from the mock:
  - F-130 pills: the mock shows Protect then Grow (EV-1 first); the spec gives Grow then Protect.
  - F-118 small text: the mock reads "cooling continuity, stock kept saleable"; the spec reads "stock kept saleable, cooling continuity".
- Is canonical/catalogue order intended? If so, which R-ID records it (R525 covers only illustrative ids)?

**Q4. Lower-casing turns "kWh" into "kwh".** A.3 "Pill small text … lower-cased"; A5 test example.
- Mock `byCat` uses `toLowerCase()`, which produces "supply cost per kwh".
- The A5 example assertion keeps "supply cost per kWh".
- **Rule one of:**
  - (a) lower-case only the first character; or
  - (b) lower-case fully and change the example.
- Recommendation: (a). It keeps the unit correct, and it is a copy-only deviation.

**Q5. The domain token is ambiguous.** §1.2 "domain uses the stored Site-type tokens of `estate/coverage.py` (`MINI_GRID`, `COLD`, `EV`)".
- At `estate/coverage.py:25` the constants are `MINI_GRID, COLD, EV = "mini_grid", "cold_chain", "ev_charging"`. Those are coverage domains.
- The *stored Site-type* tokens are the keys of `DOMAIN_OF_SITE_TYPE` (`:26`): `MINIGRID`, `COLDCHAIN`, `EV_CHARGING`.
- What each call site holds:
  - `estate/index.py` holds the coverage domain (`:115`).
  - The Portfolio row's `r["_domain"]` holds the stored Site type (`index.py:134`, `portfolio.py:172`).
- **Proposed:** `outcomes/` copies the three coverage values ("mini_grid", "cold_chain", "ev_charging"), and `portfolio_row` maps `_domain` through `DOMAIN_OF_SITE_TYPE`. Please confirm.

**Q6. The estate Findings golden has no regeneration tool.** A2 "regenerated with the tool that made them, never hand-edited".
- `/api/estate/findings` (`estate-finding-index-2`) is pinned as whole normalised bodies, 23 times, in `backend/tests/fixtures/w3/w301-estate-golden.json`.
- The check is `test_w301_estate_golden_postgres.py`: `:116` enforces formatting, and `:701`/`:707` replay it. There is no write flag in the test or under `tools/`.
- Adding `categories` to every row breaks it.
- **Choose one:**
  - (a) allow a scripted, reviewable edit that inserts the computed `categories` object per row (a one-off script in the scratchpad, diff in the packet);
  - (b) add a `ASSETOPS_WRITE_W301_GOLDEN` regeneration path to the test (test-file change, in scope?);
  - (c) another route.

**Q7. Cold and EV Finding frames have no child tabs.** A.7 #5 and A5 "on all child tabs" / "at least one child tab".
- `ColdFindingFrame` (`sites/ColdAssessmentViews.tsx:1148-1197`) and `EvFindingFrame` (`sites/EvAssessmentViews.tsx:951-993`) render only Overview plus an `<UnavailableTab label="Recommendation"/>`.
- A cold or EV child address renders a gap from `shell/SiteAnalyticsFrames.tsx:773-775`, outside the frame.
- So for cold and EV, criterion #5 can only be met on the overview. Is "overview only" acceptable for cold and EV? Or should the child-address gap (`:773-775`) also show the line, which needs the frame's read?

**Q8. The inline SVG icon is blocked by a guard.** A4 `OutcomeIcon` is to be an inline SVG in the new `sites/outcomeCategories.tsx`.
- `tools/checks/shell-overflow.ps1:338-450` fails any `<svg` in non-test `.tsx` outside an allow-list (`:89-92`).
- The allow-list includes the icon modules `ui/RailIcon.tsx` and `sites/componentIcons.tsx`.
- §0.2 forbids editing `tools/checks/*`.
- **Proposed:** put the four category paths in `sites/componentIcons.tsx` (already allow-listed, `width={size}`), and have `OutcomeIcon` wrap it. Please confirm the file, or rule another location.

**Q9. The Portfolio card copy differs from the mock, with no register row.** A6 table, against `outcomes.js:144-151`.
- Protect basis:
  - spec: "Counted from Findings · early warnings counted separately";
  - mock: "Measured events and early warnings, counted separately · loss not priced".
- Protect detail:
  - spec: "Measured events · loss not priced";
  - mock: "Cold-room exposure · interrupted charging · …".
- Assure detail: the spec reads "evidence gaps at {n} sites"; the mock reads "at **all** 3 sites".
- Grow detail:
  - spec: "Site income and sales are not recorded";
  - mock: "… · site income not recorded".
- Grow tone: the spec says `neutral`, the mock `green`.
- These read as honest A-stage wording, but none has an R-ID. Confirm they fall under R524, or name the rows.

**Q10. Plurals in card copy.** A6.
- With n = 1 the cards read "1 sites disrupted" and "evidence gaps at 1 sites". Is a singular form wanted ("1 site disrupted", "at 1 site")? The golden fixture has `evidence_gap_site_count: 1` (`estate/__tests__/portfolioFixtures.ts:161`).
- With n = 0, the Protect card reads "0 sites disrupted" in tone `neutral`. Confirm that wording, or rule a zero sentence.

**Q11. `category_counts` null: whole object or each value?** A2 says "`null` per value unless `finding_known`". A.4 says "`category_counts` null".
- **Proposed:** the object is always present with all four keys, and both counts in each are `null` when `finding_known` is false. The frontend treats a missing object the same as nulls. Please confirm.

**Q12. Reusing `ValueCard`.** A6: "the existing `ValueCard` (`EstatePortfolio.tsx:121-156`) and `cardValue` (`:99`) are reused for the value cell".
- `ValueCard` renders a whole card:
  - label, number and basis;
  - its own `Link`/`div`;
  - `data-portfolio-card={card.key}`.
- It is not a value-cell component, and it cannot host `.oc-pfdef` or `.oc-sitedots`.
- **Proposed:**
  - `CategoryCards` builds its own card markup and reuses only `cardValue` for the Optimize and Assure values.
  - Links go through `estateHref(destination, window)`, so `/findings/opportunities`, `/findings/risks` and `/evidence` keep the date window like the existing cards.
  - Each card carries `data-portfolio-card` set to the category key.
- Confirm. Also confirm the tone union in `estateClient.ts:241` (`amber|blue|neutral`) widens to add `red` for the frontend-built Protect card. `.value-card.red` already exists (`estate/estatePortfolio.css:26`).

**Q13. The mini Site Finding index has no row-level mechanism.** A2.
- `analytics/finding_index.py` has no mechanism key anywhere (`_rows` `:349-395`). The spec says to use `finding_episode.MECHANISM` with domain MINI.
- The spec says `outcomes/` must not import `analytics`. That rule says nothing about `analytics` importing `outcomes`, and §0.6 permits it.
- **Confirm:** a constant mapping for every row, even a row whose stored revision has another mechanism? Today none can, because `DOMAINS` has the one entry at `:41`.

**Q14. The `Category not mapped` test needs a fixture source.** A.7 #2.
- `estate/coverage.py:154`/`:266` carry `mechanism` with `.get`, so a null mechanism is only reachable through a fake snapshot.
- **Proposed:** a fake-snapshot unit test in `test_w301_estate_api.py`, with no Postgres row. Per ROLE_CONFIG lesson 3, please confirm a pure or fake test is acceptable here.

**Q15. Validation tier against TESTING.md.**
- §0.4 says A runs no full backend suite. `backend/TESTING.md` "At every merge to main" requires the full fast tier in Docker.
- I will follow §0.4 and the tiered memory policy: selected tests only, and the merge-time full run is left to the coordinator's safety net after C. Please confirm.

## Findings and confirmations (no question unless noted)

**Environment**
- **E1.** `var/sites` was **not** copied as intended. The YAMLs sit at `AssetOpsV1-outA/var/*.yaml`, while main has `var/sites/*.yaml`. The coordinator should move them to `var/sites/` before any producer or capture run.
- **E2.** Spec §0.1 names the worktree `AssetOpsV1-out` and PYTHONPATH `-out`. The real worktree is `-outA`, so PYTHONPATH will use `-outA`.
- **E3.** The spec file is only in `AssetOpsV1-plan2\.agent\`, not on main. The task file will link to that absolute path, unless the coordinator commits the spec to main.
- **E4.** `git ls-files --eol` shows no `eol=lf` file with `w/crlf`.
- **E5.** Register IDs R520–R579 are unused (count 0). The highest is R502.

**A1 (catalogue and map): no questions beyond Q1–Q5.**
- P-A1: `estate/coverage.py:25`, values "mini_grid", "cold_chain", "ev_charging" (see Q5).
- `COLD_MECHANISMS` at `analytics/adapters/postgres_finding_store.py:40` equals the spec's `COLD_KIND_MECHANISM` exactly.
- I walked the map tests against §1.3 (F-104, F-118, F-130), and they hold under the stated rules.

**A2 (mini and estate reads)**
- `estate/index.py:126-139` is `rows.append` in `select_finding_scope` (`:101`).
- P-A2: `r["mechanism"]` is present for all domains via `coverage.py:154` (mini) and `:266` (cold and EV), as `.get`, so it may be None.
- Other anchors:
  - `portfolio_row` `:164-196`: `r["_mechanism"]` at `:174`, `_domain` at `:172`.
  - summary `:541-551`: `finding_known` at `:539`, `members` at `:521-522`.
  - `finding_index._rows` `:349-395`.
  - `finding_read.finding()` return `:399-452`, with `"mechanism": selected["mechanism"]` at `:406`. The spec's `:114` is a key tuple; the drift is noted.
- Golden fixtures:
  - none contains `estate-portfolio-1` or `site-finding-index-1`;
  - the only affected golden is the w301 estate golden (Q6).

**A3 (cold, EV and Action reads)**
- Cold: `_item` dict at `postgres_assessment_store.py:2343-2354`, and detail `:2372-2394` reuses it (`:2383`). The kinds are only `EXCURSION` and `START_RESPONSE`.
- EV:
  - list `items.append` `:3295-3305`;
  - detail `:3345-3369`, which reuses the row with `_` keys dropped (`:3366`);
  - `analytics/ev.py:32` `MECHANISM`.
- P-A3, Action:
  - The Action read `ActionService.action()` `actions/service.py:653-698` has **no** origin mechanism.
  - `rule_inputs()` (`postgres_action_store.py:137-193`) selects `fr.mechanism` only for the currentness-selected revision, and the Action read never calls it.
  - So I will take the spec's fallback, `actions/reserve_trial.py:39` `MECHANISM`, with domain MINI, and record it in the packet.
- `action_api.py:267`/`:287` are the verification plan and outcome routes. The Action read is `:212-221`. This is consistent with "gain nothing".
- P-A3 test files:
  - cold: `test_w203_cold_reads_postgres.py`, `test_w204_cold_reads.py`;
  - EV: `test_w206_ev_reads_postgres.py` (`:184`, `:194`);
  - Action read: `test_s6_action_records_postgres.py`. No `test_s6_action_read*.py` exists.
- Byte-pinned fixture: `backend/tests/fixtures/s6_action_api_contract.json`, with full equality at `test_s6_action_records_postgres.py:173`. Regenerate with `ASSETOPS_WRITE_S6_CONTRACT=1` on that file.
- `s6_verification_api_contract.json` is shape-compared. If the verification route embeds the Action body, regenerate with `ASSETOPS_WRITE_S6_VERIFICATION_CONTRACT=1`; I will confirm at build time.
- No fixture pins the cold or EV Finding bodies.

**A4 (components and lists): no questions beyond Q2–Q4 and Q8.**
- All list anchors are within ±2 lines.
- Types:
  - `estateClient.ts` `:66`, `:184-216`, summary `:318-329`;
  - `FindingIndexRow` `sites/findingIndexClient.ts:50`;
  - `ColdFindingItem` `coldAssessmentClient.ts:137`;
  - `EvFindingItem` `evAssessmentClient.ts:113`;
  - mini detail `FindingDetailBody` `sites/findingClient.ts:189`;
  - `ActionBody` `sites/actionClient.ts:307`.
- Tokens: `--text-muted`/`--text-secondary` (#617087 is the mock's), `--accent-weak`, `--border-subtle`.
- Test files differ from the spec's globs. The actual files are:
  - estate list: `estate/__tests__/estateRoots.test.tsx`;
  - mini Site list: `shell/__tests__/s404SiteFindingIndex.test.tsx`;
  - EV list: `sites/__tests__/evFindingIndex.test.tsx`;
  - cold list: `sites/__tests__/coldFindingIndex.test.tsx`.

**A5 (pages)**
- P-A5:
  - Mini: `CanonicalMiniFinding` (`shell/SiteAnalyticsFrames.tsx:834`) fetches the detail at `:871`, but keeps only `{revisionId, title}` (`MiniSelection` `:822-825`, set at `:883`). The child tabs (`:1013-1080`) are separate components. I will widen `MiniSelection` to keep `categories` and render the line before the view switch (`:1013`), so there is no new fetch.
  - Cold and EV: see Q7.
  - Action: `ActionVerification` renders inside `SiteAction`'s switch (`:248-267`), so a line above `:229` covers every view. The refusal early-returns (`:188-211`) show no line, consistent with A.4.
- Path drift: `operatorSiteRoutes.ts` is `shell/`, not `sites/`.
- Frame tests:
  - cold: `sites/__tests__/coldRoutes.test.tsx`;
  - EV: `sites/__tests__/evAssessmentRoutes.test.tsx`;
  - mini: `sites/__tests__/siteFinding.test.tsx`;
  - Action: `siteAction.test.tsx` and `siteActionVerification.test.tsx`.

**A6 (cards and tool)**
- P-A6:
  - `site-substrate.ps1` allows estate → sites imports; precedent at `estate/findingIndex.tsx:11`.
  - No guard targets new `.css` files.
  - A name like `CategoryCards` avoids the single-definition patterns.
- P-A6, tests asserting five cards, all in `estate/__tests__/estatePortfolio.test.tsx`. Each changes because the card set changes:
  - `rendersContextFiveCardsPulseAndSelectedRows` (`:55`, order `:64-71`);
  - `rendersUnpricedCardAndEmptyRisksLensNotAssessed` (`:108`);
  - `appendsOnlyFindingRowsOnLoadMore` (`:278` `toHaveLength(5)`);
  - `rendersEmptyPendingHistoricalAndSourceConflict` (`:368-373`, WITHHELD operating card);
  - `noLineCardUsesExactShortLiteralFromApiAndFallback` (`:380-383`);
  - `rendersMeasuredPanelHierarchyAndScrollContainers` (`:461`, which still holds if `data-portfolio-cards` is kept).
- `summary.evidence_gap_site_count` already exists: backend `portfolio.py:545`, frontend `estateClient.ts:322`.
- `tools/measure-mock-panels.mjs`: v69 is hard-wired at `:11`, and the arguments are positional (`:12-14`). I will add `--mock <dir>` with the positional shape unchanged.
- Mock anchor drift: `portfolio.js:27` holds `affectsPill`, not `:31`. The other mock anchors are OK.
