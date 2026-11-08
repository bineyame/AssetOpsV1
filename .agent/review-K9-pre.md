# Review: DIESEL-K9 pre-rehearsal (wording guard, COH-10 thread, KIS-8/8a, KIS-1/2/6/7, Q1 boards, Q5)

Reviewer: fresh Claude reviewer, independent of the builder. I read the code and ran checks. I did not use a DB or run a prepare, and I edited no code.

- **Branch:** `task/DIESEL-K9-checks-rehearsal` in `AssetOpsV1-k9`.
- **Range reviewed:** `main...8375e3864`, merge commit excluded.
- **Not reviewed:** two later commits that landed on the branch while I was reviewing, `aafbe62b8` (merge of R3r) and `39d4d2aa5` (R3r KIS-OV). Both only add code. The K9 functions cited below keep the same line numbers at `39d4d2aa5`.
- **Spec:** the §8.7 KIS rows, §9o, §9p.18 and §9q (R3q, binding) in `.agent/build-sheet-DIESEL-1.md`; the owner rule in `.agent/owner-missing-fuel-2026-11-07.md`.

## Verdict: FIX

One High finding: **KIS-7 will fail on real four-Site data** because it assumes the wrong Site order. The fix is one line plus a test fixture, and it should be made before the rehearsal. The other findings are Low.

## Findings

### H1 (High, acceptance gap / rehearsal stop). KIS-7 assumes Kobo comes before Kisiwa; the served order puts Kisiwa first

**Where:**
- `tools/demo_combined_rows.py:1163`: `assert codes == ["KOBO-001", KIS_SITE]`.
- `backend/tests/test_demo_combined_finish_rows.py:887`: the L0 fixture reorders the Sites by hand ("Site order: Kobo first").

**What is wrong.** `priced` follows `summary_s["sites"]` in served order, and that order comes from the estate scope:
1. `estate_sites` (`backend/assetops_backend/outcome_api.py:136`) calls `estate.site_list`.
2. That calls `_scope`, which calls `imported_sites` (`backend/assetops_backend/estate/adapters/postgres_estate_read.py:123`).
3. `imported_sites` uses `ORDER BY s.site_code_key, s.id`.

`site_code_key` is the lower-case code, so the served order is `cold-lab-001, ev-lab-001, kisiwa-001, kobo-001`. Kisiwa comes before Kobo.

**Failure scenario.** On the rehearsal DB, Kobo and Kisiwa are both priced on S. `codes` is `["KISIWA-001", "KOBO-001"]`, so KIS-7 fails with "S: priced Sites on S", and §9q.2 item 4 reports that as a stop. The L0 test cannot catch this because it builds the order by hand. My mutation M4 below confirms it: making the check order-insensitive leaves every test green.

K8's re-expected CH5D1-O1 avoids this because it compares sets (`set(codes) <= set(allowed)`). K8's fixture assumes Kobo first too, but there the assumption does no harm.

**Fix.** Assert the set, plus the served order:
- `sorted(codes) == sorted([KOBO, KISIWA])`, and
- `codes == [s["site_code"] for s in summary_s["sites"] if s["site_code"] in {KOBO, KISIWA}]`.

Then put the L0 fixture in served order (drop line 887). R3q's text says "exactly `[KOBO, KISIWA]` in Site order". Its intent is "exactly these two, in Site order", and the literal list is a slip about the order. Record a one-line Architect note so the code is not seen as deviating from the ruling.

### L1 (Low, test gap). KIS-2 "the head cites the latest revision" has no failing L0 body

**Where:** `tools/demo_combined_rows.py:1080`.

Mutation M3 turns the check into `assert True or ...`, and `test_kis2_is_fuel_cost_2_over_the_stored_intervals_exactly` still passes.

§9q.4 item 1 requires the check. Its L0 list doesn't name a fail body for it, so this is Low.

**Scenario.** A later edit drops or inverts the check. A head consequence still priced on an older Finding revision would then pass KIS-2 silently.

**Fix.** Add one fail body to the existing loop: `_kis2_body(finding_revision_id="r0")`.

### L2 (Low). KIS-1 accepts a priced subset of nights

**Where:** `tools/demo_combined_rows.py:1049`: `assert prices` only checks that at least one night window was priced.

§9q.3 says "for each of the 10 stored night windows".

**Scenario.** A partial Kisiwa build stores only 3 nights. KIS-1 still reports `windows_priced: 3` as a pass.

**Fix.** Assert the count equals the number of stored nights the story expects: `len(story["kisiwa"]["runs"])`, or the register's night count. A literal 10 also works if the story fixes it.

### L3 (Low). KIS-1 reports "no current revision" as `KisiwaMissing`

**Where:** `tools/demo_combined_rows.py:1013-1014`.

The Site has already been found at that point (`_kisiwa_site`), so "Kisiwa missing" is the wrong diagnosis.

**Scenario.** A Site whose Foundation revisions are all superseded shows "missing: no KISIWA-001 Site". The person reading `check.json` is sent to the wrong cause.

**Fix.** Use a plain `assert current, "no current Foundation revision"`. The carry count (11) is unaffected because the `kis_1` wrapper still raises `KisiwaMissing` when there is no Site.

### L4 (Low, wording-guard scope). The guard misses some served files and some words that imply theft

**Where:** `tools/checks/fuel_wording.py:28` and `:100`.

- **Unscanned files.**
  - `frontend/src/sites/presentationProfiles.json` holds client labels ("Fuel", "Dispatch" and so on). The frontend scope reads only `.ts` and `.tsx`.
  - `frontend/index.html` is not scanned either.
- **Missing words.** H4 says copy must "never imply" theft. `steal*`, `thief`/`thieves`/`thievery` are not in `WORDS`.
- **No false-positive cost.** I grepped `frontend/src`, `backend/assetops_backend` and `config`: none of these words appears there today. Every current hit of the five listed words is in a comment (`MiniPerformance.tsx:1312` and `:1346`, `SiteFuelFinding.tsx:7`), and the guard correctly excludes comments.

**Scenario.** A later label edit puts "Possible theft" in `presentationProfiles.json`. Both the guard and KIS-8's repository scan stay green. KIS-8's served-body half would also miss it, because the profile file is bundled into the frontend, not served by the API.

**Fix.**
- Add `frontend/src/**/*.json` (excluding `src/test/`) and `frontend/index.html` to the scan.
- Add `steal\w*|thie(?:f|ves|very)` to `WORDS`, with one self-test row each.

### L5 (Low, informational). The comment stripper is fooled by `/*` inside a string

**Where:** `tools/checks/fuel_wording.py:29`.

`_BLOCK` treats `/*` inside a string literal as the start of a comment. An example is `App.tsx:539`, which has `path="/maintenance/requests/:caseId/*"`. Today that is harmless because no `*/` follows in that file; I checked, and no code line is blanked.

The stripper uses the same rule as guard 12 (`stripComments`), so this is not a K9 regression. No change is needed before the demo.

## Things I checked and found sound

1. **Wording guard.**
   - **What it scans:**
     - frontend `.ts`/`.tsx` with comments stripped, test files excluded;
     - every non-docstring `str` constant in `backend/assetops_backend`, f-string parts included;
     - every parsed key and value in `config/**/*.json|yaml|yml`;
     - every key and value in served bodies (KIS-8).
   - **Wiring:** it is in `tools/check-all.ps1` as "Fuel wording guard (DIESEL-1 H4)".
   - **False-positive risk:** low (whole-word match, case-insensitive). `python tools/checks/fuel_wording.py` printed "clean (691 files scanned)".
2. **Q1 boards (R3q §9q.1) match the ruling exactly.**
   - `KISIWA_BOARD_DAYS = ((-5, "fuel-morning"), (0, "S"))`.
   - The gate needs both `"kisiwa" in sites` and `story["kisiwa"]`.
   - The day is Dar es Salaam local, `[D-1 21:00Z, D 21:00Z)`; the estate window is the enclosing UTC midnights; ids and `date=` are as specified.
   - `day_windows` skips `kisiwa` explicitly. The `day_windows` diff is only that skip, so the three core Sites stay byte-equal.
   - L0 tests 1-4 are present. Test 1 uses the real `story_links` and test 2 the real `resolve`.
3. **Three-Site safety.**
   - `kisiwa_day_windows` returns `[]`, and COH-10 adds the `kisiwa-fuel` thread only when `kisiwa.json` exists.
   - Every new row (KIS-1/2/6/7/8) raises `KisiwaMissing` without Kisiwa, and only then. KIS-8a's earlier skip is now a raise. The carry test counts 11 raises.
   - Non-KIS rows are unaffected.
4. **No forced values.**
   - KIS-6 reads `want` from `kisiwa.json["verdict"]`, and the INEFFECTIVE body passes with `want == 0`.
   - KIS-2's tolerance is zero: exact `Fraction`, and `to_decimal_ceiling` is imported, not re-implemented. `idle_seconds` is reported, not asserted to 0.
   - KIS-1 checks every current revision. Filtering on `superseded_at is None` matters: mutation M1 (no filter) fails the test, which shows the in-memory `register_in` store really holds superseded rows.
   - KIS-1's no-load and accuracy values are read from `demo_combined_kisiwa.NO_LOAD` and `ROLES4` and checked against the §8.7 literals. Price v1 is read from the fixture file.
   - The KIS-2 SQL columns exist:
     - `finding_revision.domain` (migration 0022);
     - `financial_consequence_revision.site_id`, as Kobo's `_consequence_heads` already uses;
     - `financial_consequence_power_interval.duration_seconds integer` (migration 0011). This makes `int()` exact.
5. **Builder deviations: both confirmed.**
   - **(a) Four-Site bundle built in the test from `clean_full`.** It gives the same coverage as a committed fixture directory and is easier to review. V4 and V2 Kisiwa fail cases are present, and the test asserts the compared count grew, so the Site-set guard did not skip the window.
   - **(b) Assure card read from the week outcome-summary.** The Portfolio page draws its cards from `GET /api/estate/outcome-summary`: `frontend/src/estate/PortfolioOutcomes.tsx:91` reads `summary?.cards?.[key]`, and `/api/estate/chain` carries the same `summary["cards"]` (`chain_api.py:352`). So `cards.ASSURE_PERFORMANCE.claim.value` is the Portfolio Assure card.
6. **K8 merge (`AssetOpsV1-k8`, `task/DIESEL-K8-four-site-screens`, read only).**
   - **Textual conflict:** only in the `LOCAL_DAY_TZ`/`SUMMARY_SITE_TZ` hunk. Keep the union as the packet says. `_coh7a_window` then maps KISIWA-001 to `Africa/Dar_es_Salaam` from both maps, which is harmless.
   - **CO-6:** K8 reads `body["objectives"]` site codes and checks them against `expected_site_codes`. KIS-6 reads the same list, so they agree, and CO-6's `objective_site_count == 3` is not repeated.
   - **CH5D1-O1:** K8 compares sets; KIS-7's order-strict check is H1.
   - **COH-1 and COH-7a:** no overlap with K9's code.
   - **`test_demo_combined_finish_rows.py`:** the two branches add tests in different places (K8 around line 635, K9 from line 730).
   - **Dependency:** see readiness risk 1.

## Mutations I ran myself

I ran these on a scratch copy of `tools/` and the row test file, outside the repo, then restored. No repo file was edited.

| # | Mutation | Result |
|---|---|---|
| M1 | KIS-1 `current = list(revisions)` (no `superseded_at` filter) | `test_kis1_...` FAILS (caught) |
| M2 | KIS-6 H2 check becomes `assert True or not lines` | `test_kis6_...` FAILS (caught) |
| M3 | KIS-2 head-cites-revision becomes `assert True or ...` | passes: **not caught** (L1) |
| M4 | KIS-7 order-insensitive | passes, as expected, which shows the order is untested (H1) |
| M5 | `kisiwa_day_windows` local midnight in UTC instead of Dar es Salaam | `test_kisiwa_day_windows_are_the_boards_story_links_opens` FAILS (caught) |
| M6 | Gate drops `story.get("kisiwa")` | `test_without_kisiwa_nothing_more_is_collected_...` FAILS (caught) |
| M7 | `stole` removed from `WORDS` | two `test_fuel_wording` tests FAIL (caught) |

## Checks run

All runs used plan2's `.venv` python with the absolute k9 PYTHONPATH, and no DB.

- `pytest tools/checks/test_fuel_wording.py backend/tests/test_demo_combined_finish_rows.py backend/tests/test_k7_kisiwa_story.py backend/tests/test_k9_finish_callsites.py`: **157 passed** in 19.5 s.
- `pytest tools/checks/test_chain_coherence.py`: **172 passed** in 13.1 s, matching the packet.
- `python tools/checks/fuel_wording.py`: clean, 691 files.

**Not verified:**
- `tools/check-all.ps1` (I cite the packet's run: 18/18 on 70639ecac, 1502 s);
- every DB-backed path: the KIS-1/KIS-2 SQL against a live schema, `PostgresFoundationStore.revisions`, `price_selection`;
- any served body.

## Rehearsal-readiness risks (fix or watch before the 2-hour build)

1. **Run the rehearsal on a tree with K8 merged.** Without K8:
   - CO-6 asserts three Site codes and fails on four;
   - COH-10's `kisiwa-fuel` thread finds no Portfolio row, because the fuel Finding reaches the Portfolio only through K8's `_fuel_rows` (`estate/index.py`). It fails with "no Portfolio row shows a Finding of thread kisiwa-fuel";
   - COH-5 RISK needs K8's `lens_flags`.

   The packet names the textual conflict but not this order dependency.
2. **KIS-7 Site order (H1):** a certain failure until fixed.
3. **KIS-7 Kisiwa priced on S.** The S summary prices Kisiwa only if a dispatch-Finding consequence falls in Kisiwa's S local day, because mini Sites use `window_day` (DAY). If no Kisiwa dispatch episode falls on S, KIS-7 fails as a stop (by ruling). Check `board_summary.S.KISIWA-001` / the S board's OPTIMIZE_COST earnings on the clone before the build.
4. **KIS-2 lifecycle and heads.** Every Kisiwa dispatch Finding's latest revision must be SUPPORTED, and its head consequence must cite that revision. A Finding that is NO_LONGER_SUPPORTED or MERGED, or one that has a newer revision with no recomputed consequence (pending `financial_consequence_work`), fails the row. A clone query over `finding_revision` (domain `mini_grid`, analytic `dispatch`, KISIWA-001) against `financial_consequence_revision` heads would settle this in a minute.
5. **KIS-6 verified count.** `threads.verified == 1` needs the fuel thread's verified state to take effect inside `[S-6d, S+1d)`. If the evaluate day falls after S+1d on the real calendar, the count is 0 against VERIFIED and the row fails. Confirm the evaluate instant from `kisiwa.json` and the calendar.
6. **KIS-1 effective-from filters.** The real prepare must write the no-load and accuracy revisions with `valid_from >= register[...effective_from]`. The L0 test uses the real `register_in`, which is good evidence, but any later Foundation revision the prepare adds (for example R3r's cutover-basis work in `39d4d2aa5`, which I did not review) must carry both properties and stop 90. Otherwise "every current revision" fails.
