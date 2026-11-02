# Review packet: WALK1-3 (declared productive-use price and estimated productive-use sales at Kobo)

Branch `task/WALK1-3-productive-use-price` from main `daa523b29` (WALK1-2 merged). WALK1-1 is not merged. Spec:
`.agent/build-sheet-WALK1.md` §4 (plan2 worktree), §8 register ids R677-R680, §9 D-W1-2. Folded in: WALK1-2 review
L1 (EV "gross" wording) and L3 (`finding-history` G1 capture). USER_REVIEW: none for this slice; the owner walkthrough
resumes after G1.

## Outcome delivered

Grow outcome MG-1 → driver: measured use by declared productive users → evidence: accepted `feeder_demand` readings ×
declared price → estimate. On a priced day Kobo's Grow row reads "estimated productive-use sales" beside an amount,
with the subline "{kwh} kWh used by {names} in {h} measured hours, at the declared price of {p} {cur} per kWh · not
billed or collected". Nothing is stored. Which loads are productive is declared in the Site configuration.

## Files materially changed

- `backend/migrations/versions/0040_walk1_productive_price.py`: widens the key and unit CHECKs. Adds
  `financial_assumption_revision_productive_positive`. The downgrade refuses while a productive-use row exists. The
  assignment table has no key CHECK, so it needs no change.
- `financials/assumptions.py`: adds `PRODUCTIVE_PRICE_KEY`. It gets the same positive and ISO 4217 rule as the EV
  key (`PER_KWH_KEYS`). The refusal text is now "A price per kWh must be greater than zero." for both keys.
- `sites/models.py`: adds the `supply-use` state property (PHYSICAL) with three values, carried on LOAD.
- `site_outcomes/productive_use.py` (new, pure): exact Decimal kWh over GOOD intervals clipped to `[lo, hi)`, plus the
  union of measured seconds. Non-GOOD readings and non-finite values are gaps.
- `mini_depth/read.py`: adds `productive_users` and `productive_readings`. These answer pre-flight E5: the SQL lives in
  the read-only mini-depth reader, a named `$pgReaders` entry, and reuses `store._ACCEPTED`.
- `site_outcomes/mini.py`: adds the three `MiniPorts` fields (defaults: none declared), `_productive_sales` (the §4.4
  table), Grow contributor order, headline precedence, the MG-1 reading and `COPY`.
- `site_outcomes/read.py`: B4 binding only. The `summary` code is untouched, so there is no overlap with WALK1-1.
- `tools/demo_combined_kobo.py`: supply uses at install + 25 min, and the productive price published beside diesel
  (same instant). New fixture `backend/conversions/demo-productive-price-publications.json`.
- `tools/demo_combined_finish.py`: G1 rows WK-1 (EV "estimated charging income" + amount), WK-2 (Kobo S Grow
  `headline_money`) and WK-3 [IDX] (Portfolio `summary.count_basis` not null).
- `tools/demo-combined-evidence.mjs`: L3 adds `finding-history` (the Kobo lead finding's history) to the capture list
  and to `mock-ids`.
- Frontend:
  - `EvSiteViews.tsx` (L1): 7 strings "gross tariff estimate" / "gross estimate" become "estimated charging income".
  - `siteViewModel.ts`: `STATE_PROPERTY_WORDS` and `propertyValueText`, used in both property tables.
  - `estateEvidenceWords.ts`: "Price per kWh for productive users".
- Tests:
  - New: `test_walk1_productive_price_postgres.py`, `test_walk1_productive_sales.py`,
    `test_walk1_productive_producer_postgres.py`, `supplyUseWords.test.ts`.
  - Updated: the head literal in 22 files (0039 → 0040), the w207 CHECK texts and excluded set, the w204
    `below_0026` set, the w205a/w402 registry assertions and the evSiteMoneyRoutes strings.
- Register: R677-R680 added, and R655 extended with the new strings and the L1 rename.

## Pre-flight

- **E4 (cleared)**: No pinned digest changes. The S3 input set (`analytics/assessment_inputs.py:305-361`) and
  `configuration_sha256` (`assessment_worker.py:80-86`; controls are only the reserve and minimum-runtime values,
  `postgres_assessment_store.py:287-328`) are recomputed from the DB. The mini-depth hour digest covers only the
  three depth keys. The trial `FOUNDATION_CHANGED` check (`actions/verification.py:600-605`) reads the live revision
  at apply time. No literal sha appears in `tools/demo_combined*.py` or the S6 tests.
- **E5 (cleared)**: `backend/assetops_backend/mini_depth/read.py` (`MiniDepthRead.productive_users` and
  `productive_readings`).
- **E6 (registered, R678)**: With the estimate shown, Kobo's Grow row reads **Unknown**. The declared MG-1 monthly
  target (300 kWh) is not judged from one day, and Kobo has no spare-solar read. The rule is unchanged, and this is
  pinned in `test_row_state_with_the_estimate_is_unchanged`.
- Pre-G1 data evidence: a read-only `SET TRANSACTION READ ONLY` probe of the new reader against the existing
  `assetops_polish_full_test`, with no writes. Grain mill feeder_demand:
  - S-pattern days (10-02, 10-09, 10-27, 10-29): 168.333… kWh in 8.0 measured hours, 96 readings, which gives
    **42.08 USD** at 0.25.
  - 10-16, 10-23, 10-30 and 10-31: **0 kWh**.
  - This matches the sheet's expectation. No number was tuned.

## Acceptance (sheet §4)

| Item | Status |
|---|---|
| 4.1 migration 0040, CHECKs as 0026, positive, downgrade refusal | Done. Migration test asserts the exact CHECK texts up and down, the refusal and DB rejections (unit, 0, negative) |
| 4.1 assumptions.py key, unit, positive, ISO | Done. Store refusals tested (`VALUE_NOT_POSITIVE`, `CURRENCY_NOT_ISO`) |
| 4.1 frontend label "Price per kWh for productive users" | Done (`estateEvidenceWords.ts`). The EV-only `ROLE_LABEL` map in EvSiteViews is not used for mini keys |
| 4.1 fixture values and source text; published beside diesel | Done; tested |
| 4.2 `supply-use` property, states, LOAD carrier, words | Done. Tests cover acceptance, absence, wrong carrier and bad value; frontend words test |
| 4.2 Kobo additive revision | Done at **+25 min, not the sheet's "e.g. 12 min"** (see deviation 1) |
| 4.3 pure `productive_energy` | Done. Tests cover clipping, gaps, non-GOOD, exact sum, overlap and zero |
| 4.3 ports `productive_users`, `productive_readings`, `productive_price` | Done (deviation 2 on the readings signature) |
| 4.4 table rows, subline, order, precedence, MG-1, COPY | Done. Each row is pinned in `test_walk1_productive_sales.py`, plus failed-port PARTIAL cases |
| 4.5 tests | Done (above) |
| §5 three finish checks | Added (WK-1..3). They are not run here; G1 runs them (WK-3 needs WALK1-1 merged) |
| L1 / L3 | Done |

## Checks run (revision `e22735fa9`, worktree `AssetOpsV1-w1c`, DB `assetops_walk1c_test`)

- `tools/check-all.ps1 -Python <plan2 venv>`: **All 12 guards passed**. This includes architecture, agent workflow,
  mock-deviation labels/vocabulary and the missing-claim scan.
- Frontend:
  - `tsc --noEmit`: exit 0.
  - `vitest run`: **151 files, 3599 tests passed**, 326 s.
  - `vite build`: exit 0.
- Backend scoped Postgres runs, host wrapper `tools/run-host-tests.ps1`, `-n 3 --dist loadfile`, all in the foreground:
  - A, 10 migration/head files incl. w207 and 0040: **152 passed**, 427 s.
  - B, 7 files: 59 passed, **1 failed**: `test_w204_cold_migration.py::TestMigration0023::test_upgrade_preserves_minigrid_money_and_downgrade_drops_only_w204`.
    `below_0026` did not drop the new CHECK. Fixed in `e22735fa9`.
  - C, w204 rerun plus w403, w501-w504: **70 passed**, 550 s.
  - Adjacent, 19 files: assumptions publication/read, b4 board, d4, w402 reads, the three WALK1 files, the EV
    producer, the property registries, b2 mini/vocabulary and b4 read/imports/route: **399 passed**, 350 s.
- Non-vacuity, observed rather than staged:
  - The migration CHECK assertions first failed on the PG-flattened OR text before they were corrected.
  - The producer carry-forward assertion failed at +12 min, which is the finding behind deviation 1.
- **Not run**:
  - The full real-Postgres backend suite. It takes about 46 min, which does not fit the 10-minute foreground cap
    given for this machine.
  - The slow-tier `test_demo_combined_postgres.py`, which runs a 20-25 min prepare.
  - Captures and `layout-evidence` (the backend slice defers captures to G1, Addendum 3 option a).

## Known deviations

1. **Supply-use revision at install + 25 min, not + 12 min.** A component-property change only splits the revision
   in force at its instant (`foundation_service.py:467`, "earlier revisions are split, never rewritten"). At + 12
   min the declaration was confined to `[+12, +20)`, and the + 20 roles-3 revision carried no supply use, so story
   days had no productive user. This was proven by a test failure. + 25 min follows every commissioning revision and
   is still recorded at + 30 min. It is still additive, and no pinned file or digest changes.
2. `productive_readings(asset_ids, lo, hi)` takes the user asset ids rather than the sheet's `(lo, hi)`. The composer
   passes the users it already read, which avoids a second Foundation read.
3. The "Price per kWh" contributor links to `/sites/{c}/financials/assumptions` as specified. That page reads only
   the diesel series (`financialsClient.ts:478`), so the productive price is shown on the board but not on the
   Assumptions page.
4. The new board strings are composed in the backend and carry no review-mode label. This follows the WALK1-2
   R674-R676 precedent; the register rows are the record.
5. The G1 capture count becomes 30 (15 screens × 2 widths), not 28, with `finding-history` added.

## Residual risk

- The end-to-end prepare with the new producer step has not run. G1's rebuild is the first one. The test
  `test_walk1_productive_producer_postgres.py` runs `configure_at` + `publish_price` on real Postgres and checks
  carry-forward, but not the trial and verification chain that follows.
- WK-3 fails on this branch alone, because `count_basis` is WALK1-1's. Merge WALK1-1 first, or expect WK-3 red until
  then.
- Conflicts with WALK1-1:
  - The R655 register line: both slices append to it.
  - `EvSiteViews.tsx`: different lines (WALK1-1 changes only `:237`).
- `.ai/CODE_STATE.md` still names 0039 as the head (WALK1-2 also left `.ai/` untouched). The coordinator should
  update it at merge.

## Reviewer focus

The §4.4 copy (an estimate at a declared price, never billed or collected), deviation 1, the E6 Unknown state beside
the amount (R678), and the read-only SQL in `mini_depth/read.py`.

## Fix round 1 (review-WALK1-3 Addendum 3: M1, M2, L1, L3, L4)

Merged main (253d6e8c2) first: one conflict, the R655 line in the register; both appendices kept (WALK1-3 then WALK1-1).

- **M1.** `productive_energy` groups GOOD clipped spans by asset; any asset whose own spans overlap makes the whole
  result `kwh None` with `conflict_assets` (names). Contributor "Not available yet · {names} has/have conflicting
  readings on this day, so use is not estimated"; no headline money, subline None, MG-1 `MG1_ACTUAL`. Tests: one-asset
  overlap, touching spans still sum, two users overlapping each other still sum, compose text for one and two names.
- **M2.** Client `SeriesQuery.key` (default diesel); the Assumptions page reads `productive_use_price_per_kwh` and
  shows "Price per kWh for productive users", "{p} {cur} per kWh", "Declared", "Valid from" inside the existing
  Financial assumptions panel (no new panel: the v69 panel-structure guard). Undeclared: "Not available yet · no
  price per kWh declared" through new catalogued gap `G-assumptions-productive-price` (gapCatalogue, registry,
  ledger). A failed read says "The price for productive users could not be read, so none is shown and none is
  assumed." (deviation: not the "Not available yet" wording, which the missing-claim scan requires to be catalogued).
  R679 corrected.
- **L1.** EvEnergy "{amount} {cur} estimated"; "Estimated charging income" in EvEnergy card/tile and the two word
  maps; tests updated; R655 extended.
- **L3.** Zero-use priced day: spare-solar headline leads when it exists; "No productive-use sales on this day" only
  without one. Both branches pinned.
- **L4.** Failed `productive_users` read returns `subline None`; pinned.

Checks (own DB `assetops_walk1c_test`):
- `run-host-tests` (-n 3, loadfile): test_walk1_productive_sales, test_walk1_productive_price_postgres,
  test_out_b2_vocabulary, test_out_b2_mini, test_cov_partial_portfolio, test_idx_gaps_board, test_out_b4_route:
  90 passed, 2 failed, both failing on main 253d6e8c2 as well (`test_board_finding_titles_are_the_frontend_plain_titles`,
  the known MERGED-title one; `test_out_b2_mini::test_pending_finding_index_unsettles_finding_outcomes`, expects no
  `withheld` key in `finding_gaps` after WALK1-1 added it; verified failing in the main worktree).
- vitest: siteFinancials, evEnergy, estateFinancials, supplyUseWords, evSiteMoneyRoutes, src/ui: all passed;
  `tsc --noEmit` exit 0.
- `tools/check-all.ps1`: All 12 guards passed (vocabulary, missing-claim, mock-deviation, dependency registry).
- Not run: full backend/frontend suites, captures.
