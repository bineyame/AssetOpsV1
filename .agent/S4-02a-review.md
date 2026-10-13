# S4-02a fresh Claude review: phase 2 and the slice as a whole

Reviewer: fresh Claude (did not author). Branch `task/S4-02a-site-assumptions`, diff `5159b96..f9ce2e5`. Phase 1 was reviewed
in `.agent/S4-02a-phase-1-review.md`; only its carries C1-C4 are re-checked here.

## Verdict: ACCEPT with carries

The read contract, the Finding bridge, the UI, the gap and the Foundation link meet the packet. I reproduced the
browser evidence (69/69) on the kept stores, and confirmed that the phase-1 fixes are non-vacuous.

One Medium finding (M1) must be fixed on the branch before merge. It is cheap: `tools/layout-evidence.mjs` still has three
five-tab predicates, and the packet attributes their future failures to older slices. A small fix round and a diff check
are enough; no new full review is needed. The Low findings are carries or owner-walkthrough items.

## Checks I ran (as observed)

- **Focused backend.** I used my own scratch DB `assetops_s402a_rev2_test` (since dropped). I ran
  `test_s4_assumption_read_api.py`, `test_s4_assumption_read_postgres.py`, `test_s4_assumptions_postgres.py`,
  `test_s4_assumption_publication.py` and `test_s4_finding_api.py`: **79 passed**. Full backend was not run, as instructed.
- **Non-vacuity, each reverted with `git checkout --`:**
  - Restoring the full provenance into `request_sha256` makes
    `test_replay_from_a_modified_fixture_copy_returns_the_stored_ids` FAIL (M1 proof).
  - Replacing the L1 trigger condition with `IF FALSE` makes
    `test_closing_a_current_row_before_the_series_latest_start_is_refused` FAIL (L1 proof).
- **Frontend.**
  - `npx.cmd tsc --noEmit`: exit 0.
  - Focused vitest (siteFinancials, siteFindingHistory, operatorSiteTabs, siteDetailRoute, siteFoundationRevision,
    overflowContainment): 6 files, 185 passed.
  - Full `npx.cmd vitest run`: **62 files, 1465 passed**. Vitest ran on this machine.
  - The build was not run by me.
- **`tools/check-all.ps1`:** all 9 guards passed. The orphan scan reports 31 tagged / 12 baselined, with the baseline
  unchanged, and the registry and ledger are valid.
- **Browser evidence.**
  - I served the kept DBs `assetops_s402a_evwalk` / `_evempty` (work `s402a-evidence-work`) on 8900/8901 and ran web on
    5400/5401.
  - `node tools/s402a-assumptions-evidence.mjs ... 60bd89cb-...`: **69/69 PASS**.
  - All four servers are stopped.
- **API probes** on the same servers:
  - `/financial-assumptions/latest` returns 422.
  - The v1 ID on the empty store returns 404, never the latest.
  - POST to the write route returns 401 `UNAUTHENTICATED`.
  - The `api_next_page` link with a cutoff returns 422; see L1.
- **`tools/layout-evidence.mjs`** on the same store: 206 PASS plus a run of FAIL lines. They matched the packet's tally
  and attribution *for this store*:
  - the MG-001 Site and Foundation sections read 0 tabs and no diagram (the Site is absent);
  - two Lab/legacy-Kobo preconditions fail.
  - None of the failures on this store is caused by the slice, but see M1 for the stores where they would be.
- **Screenshots.** I compared the current Assumptions page and the bridge at 1440 and 390 with the mock Assumptions page
  at 1440 and 390.

## Focus areas

1. **Phase-1 carries.**
   - **C1 (M1):** landed. `assumptions.py` `PROVENANCE_NOT_DIGESTED` drops `fixture_sha256` / `fixture_version` and the
     authorization prose. The new `fixture_step_sha256` (canonical step JSON) is digested, so editing a step's content is
     still a conflict, as it should be. The replay test uses CRLF, an appended v4 and a bumped version, and it is
     non-vacuous.
   - **C1 (M2):** landed. v2 is `2030-01-01`, `V2_START` is derived from the fixture, and the SUCCESSION test asserts its
     instant is more than one day in the future.
   - **C2 (L1):** landed in 0010, with a test, and non-vacuous. The store closes rows before inserting, so normal
     publication still passes the full suite.
   - **C2 (L2):** listed as D2, not changed.
   - **C4:** satisfied. The snapshot uses `recorded_from <= c AND (recorded_to IS NULL OR c < recorded_to)`, and current
     means `recorded_to IS NULL`. The write route keeps its default; this was tested and probed.
2. **Read API.** All of the following hold:
   - half-open selection on both axes, tested at `V2_START - 1µs` / `V2_START` and at `r3 - 1µs` / `r3`;
   - exact-ID stability after a later CORRECTION;
   - complete bounded pagination;
   - Site and tenant scoping (`OTHER-001` and `FOREIGN-001` return 404);
   - 401/403 before any lookup, an unknown Site gives 404, and a missing or failing store gives a typed 503;
   - a malformed ID gives 422 and an unknown ID gives 404, and neither falls back to the latest;
   - naive instants are refused.
3. **Finding bridge.**
   - `consequence_state(quantity_available=False)` always returns `QUANTITY_UNAVAILABLE` with null amount, currency and
     price.
   - It holds the exact FindingRevision: a foreign revision returns 404 through `_choose`, and the UI rewrites the
     address to pin it.
   - The Evidence link is that version's S4-03 Evidence.
   - The closed gate refuses the latest revision and serves a pinned revision as audit-only.
   - No mock number appears in the DOM.
4. **UI.**
   - The tab flips, and the two routes are as the packet names them.
   - The default reading is plain language, with IDs only inside "Record details"; the browser measures 0 UUIDs.
   - Reload, back/forward and keyboard Enter all pass.
   - `G-assumptions-human-edit` renders through `<MissingClaim>`, and the registry `mock_gaps` entry matches the
     `gapCatalogue.ts` mirror (the guard passes).
   - No untagged "not available yet" literal was added.
   - The Scenarios subtab is absent, as the evidence claims.
   - The Foundation link targets `/sites/{site}/financials/assumptions`, and `G-foundation-financial-assumptions` stays
     open and tagged.
5. **Deviations.**
   - **D1, the registry edit, is acceptable.** The packet requires a "catalogue entry and placement mirror", and the
     mirror guard makes a `mock_gaps` entry mandatory. Only that one entry was added, with no node, status or ledger change.
     The Planner's "this plan does not edit the registry" contradicts its own gap requirement; this is a wording fix
     for the Planner, not a defect.
   - **The four frontend test edits and the two `layout-evidence` claim edits are legitimate.** They update the
     rendered-tab inventory, and both the order and the exact-list predicates stay strict. The edit is incomplete,
     though; see M1.
   - D3-D6 are acceptable as described.
6. **Evidence tool.** I reran it: 69/69. Its non-vacuity mode is described but I did not rerun it.
7. **Owner walkthrough.**
   - The commands are exact absolute paths, use `npm.cmd`, private DBs `assetops_s402awalk` / `assetops_s402aempty`
     and ports 8870/8871/5370/5371, and include a `drop` cleanup.
   - The language is plain, and it names what to decide (the disabled-edit wording, "Not calculated").
   - I ran its `links` command on the kept evidence DBs, and it printed correct links.
   - I did not run `prepare` against the owner DB names.

## Findings

### Medium

**M1. `tools/layout-evidence.mjs` still asserts the five-tab row in three claims, and the packet attributes their
failures to older slices.**

The slice updated the Site-page claim (`:1800`) and the two T027 Evidence claims (`:4571`, `:4667`). Three
predicates still require `Overview|Foundation|Performance|Findings|Evidence`:
- `:1893-1894`, Foundation views. The label still says "Overview, Foundation, Evidence", but the predicate is the
  five-tab T028 list, so it passed before this slice on a store with MG-001.
- `:4774-4775`, T027 Site Overview on KOBO.
- `:5046-5047`, T028 Performance on KOBO.

**Failure scenario.** On the next store that has MG-001 or a legacy Kobo Site (the V-01a/b or S3 stores), these claims
FAIL because Financials now renders: 12 Foundation-view failures plus the KOBO sections. The packet's line ("All 28
failures are fixture preconditions or claims older than this slice ... the T011A claim") will lead the next reader to
dismiss them as stale. A real future tab regression would then hide in that known-failing set.

On the Finding-case store these sections fail for other reasons or do not run. So the slice did not cause any failure
in the recorded 206/28 run, but it did leave latent failures behind.

**Fix.**
- Update the three predicates and labels to the six-tab list. For `:5047` use `slice(0, 6)`.
- Correct the packet's attribution sentence.
- No rerun on a full store is required to merge, but record the predicate change in the packet.

### Low

**L1. The `api_next_page` link breaks when a cutoff is present** (`financial_read_api.py:81-83`).
- **Cause.** `recorded_at.isoformat()` is interpolated unencoded, so `+00:00` arrives as a space.
- **Observed.** Following the link returned **422** `datetime_from_date_parsing`.
- **Coverage.** The pagination test (`test_s4_assumption_read_postgres.py:98-107`) pages only without a cutoff. The UI
  does not use this link, which is why the severity is Low.
- **Fix.** Build the link with `urllib.parse.urlencode`, and add a cutoff case to the pagination test.

**L2. At 390 px the Site tab row now wraps on every Site page.** With six tabs, "Evidence" drops to a second line under
the active underline; this is visible in `s402a-financials-bridge-narrow.png`. The mock scrolls the row horizontally.
- No claim checks for a one-line tab row, so nothing recorded regresses, and there is no page overflow.
- It is a visible change to every V-01a/b screen at phone width.
- **Owner judgment:** accept the wrap, or have a later layout slice adopt the mock's scrolling row. This is not a merge
  blocker.

**L3. The internal fixture name appears in the default reading.** The Source line reads "AssetOps demonstration fixture
demo-diesel-price-publications v1 (illustrative estimate, not a market quote)". The packet lists this as residual risk,
but it is product-screen text. It also falls under the owner's plain-language and no-simulator-language rules
("fixture", a file slug).
- **Why it matters now.** After C1, `source_reference` is in the digested step. Rewording it is free only while no
  non-scratch DB holds the fixture, which means before the owner's `prepare`.
- **Fix.** Either decide at the owner walkthrough, or reword the step before it (for example, "Illustrative
  demonstration estimate, not a market quote").

**L4. Copy mismatch** (`SiteFinancials.tsx:447`). The text says choose “What this means in money”, but the link on the
Finding page is “What this finding means in money”.

**L5. Cutoff and paging details:**
- A recorded-cutoff read returns `recorded.to` values later than the cutoff. The test acknowledges this
  (`test_s4_assumption_read_postgres.py`, exact-ID test), so a cutoff view's selection is reproducible but its body is
  not byte-identical. The UI does not show the value.
- "Show later versions" replaces the page rather than appending to it, and its position is not in the URL, so a reload
  returns to page 1.
- Neither is reachable with three versions. Note both for S4-02b.

**L6. The G-05 itemization is prose by screen**, in the packet and the `SiteFinancials.tsx` header. It does not use
manifest element or portion IDs (`assumptions:2`, `financials:3`, ...), as the task asks ("listed by manifest
element/portion"). When the G-05 handoff is written, carry it with IDs.

## Residual risk not in the packet

- The foreign-revision state shows "No such price version ... Nothing else is shown in its place" above the current
  price panels. Those panels are labelled as current, not as the substitute, which is correct. Still, a reader may take
  it as a substitution; worth one look in the walkthrough.
- The L1 trigger reads `max(recorded_from)` without its own lock. It relies on the publisher's series lock, which is
  fine for the SYSTEM path only. A future human write path must take the same lock.

## Owner-walkthrough focus

1. The disabled-edit wording.
2. "Not calculated" as a finding's cost.
3. The Source line's fixture wording (L3). Decide before `prepare` if it should change.
4. The wrapped Site tab row at 390 px on all Site pages (L2).
5. Version 1's History line says "from 1 Jan 2026, with no end date" (its authored intent), while the Schedule shows it
   cut at June/July/2030. Check that this reads clearly.

## Registry closeout notes

The handoff's list stands. In addition:
- **`G-assumptions-human-edit`:** set `evidence.reviewed_by` to this review, and `evidence.visual` to
  `%LOCALAPPDATA%/AssetOps/evidence/s402a/s402a-assumptions-current-{desktop,narrow}.png`.
- **`G-foundation-financial-assumptions`:** keep it `open`. Correct its `review_trigger` and `evidence.ui` as the
  handoff says. Resolve it only after the owner accepts the link.
- **`I-S4-02a`:** cite this review and the 69/69 rerun. Name M1 as fixed (or not) before any built status.
- **No W1 panel promotion.** `financials:1/2` stay partial until S4-02b.
