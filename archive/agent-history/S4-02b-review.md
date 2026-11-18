# S4-02b fresh Claude review: phase 2b and the whole slice (bounded fuel consequence and repricing)

Reviewer: fresh Claude. I did not build this slice. Branch `task/S4-02b-fuel-consequence` at `c0be402`.

- Phase 2b diff: `3793e4d..c0be402`.
- Whole slice: `16ba22d..HEAD`.
- For phases 1 and 2a, I re-checked only the carries.

Judged against:
- `tasks/S4-02b-fuel-consequence.md`;
- `D-2026-10-13-s4-bounded-financial-basis` and its addendum;
- `.agent/architect-S4-02-answers.md`;
- the 2a carries in `.agent/S4-02b-phase-2a-review.md`;
- the owner rulings `.agent/owner-S4-02b-money-demo-2026-10-14.md` and `.agent/owner-S4-02a-acceptance-2026-10-14.md`;
- the packet, handoff, questions (Q10-Q15) and owner walkthrough.

## Verdict: ACCEPT with carries (H1 must be fixed on the branch before the owner checkpoint and before merge)

The backend carries all landed, and none is vacuous. I checked each one by my own mutation:
- M1 closed source gives `AUDIT_ONLY`;
- M2 is protected by a HISTORICAL Postgres test;
- L1 401/403/503;
- L2 completeness half;
- L3 latest filter and skip;
- L4 STALE wording and pending-work scope.

The quantity, price and amount arithmetic is unchanged from 2a and still reproduces:
- 12.65 L;
- 15.82 USD (v1-v3);
- after v4: 16.20 USD, with the same FindingRevision and technical digest.

The UI is plain by default. Identifiers and enum names appear only inside disclosures. The demonstration label shows, and the reload, back/forward, keyboard and Evidence round trip all work.

There is one High finding. The backend now refuses to give an amount for a closed-source (`AUDIT_ONLY`) or `STALE` Finding, but the Financials Overview puts the amount back. It renders the stored head's amount in bold inside the main money panel, directly under the "no current cost" headline. The packet's evidence claims "for the record only, no amount" and "stale ... no current amount", and both pass only because they test a data attribute while the amount is on screen. I reproduced this in my own browser run (screenshots below). The fix is small and confined to the frontend plus the evidence tool, so the slice does not need to be returned. It must land before the owner sees the walkthrough, because step 6 of the walkthrough misdescribes the screen.

## Checks I ran (as observed)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npm.cmd test` (frontend, full) | **62 files, 1476 passed.** It ran on this machine this time; the esbuild sandbox block did not occur |
| `npm.cmd run build` | `✓ built in 6.26s` (chunk-size warning only) |
| Focused S4 backend: `test_s4_fuel_cost`, `test_s4_consequence_read`, `test_s4_consequence_store_postgres`, `test_s4_consequence_recompute_postgres`, `test_s4_power_demo_case_postgres`, `test_s4_assumptions_postgres`, `test_s4_assumption_read_postgres`, `test_s4_assumption_publication`, `test_s4_assumption_read_api` on scratch DB `assetops_s402brev3_a_test` | **141 passed**, 9 warnings, 268 s. This is 2a's 129 plus 12 new 2b tests |
| `tools/check-all.ps1` | **All 9 guards passed.** Orphan scan: 31 tagged, 12 baselined (unchanged); ledger: 110 screens |
| Walkthrough `prepare` on my own DBs `assetops_s402brev3walk` / `assetops_s402brev3empty` (work `s402b-rev3`, code tree from `c0be402`) | Gate open on both. 34 work items, 0 failed. Latest: 1 PRICED, 8 `POWER_MISSING`, 2 `FINDING_NOT_SUPPORTED`, 1 `POWER_COVERAGE_GAP`. This matches the packet |
| `tools/s402b-fuel-cost-evidence.mjs` on my servers (APIs 8908/8909, web 5408/5409, CDP 9408) | **90/90 claims passed.** v4 published, then recompute: 1 appended, 11 replayed; empty-store recompute: 31 appended; close-gate and open-gate both worked. Two of those claims are vacuous (H1) |
| Owner DBs `assetops_s402bwalk` / `assetops_s402bempty` and ports 8872/8873/5372/5373 | Not touched |
| Full backend suite | Not run, per the dispatch. The packet's 2049 is unverified by me |
| `tools/layout-evidence.mjs` | Not rerun. The packet records 206 PASS / 28 FAIL, the same as at S4-02a, with the failures attributed to fixture preconditions outside this surface. The slice-specific 1440/390 overflow claims are in the evidence tool and passed in my run |

My scratch DBs and work folder were dropped afterwards, and the tree was clean (only the coordinator's unrelated `.agent/coordinator-handoff.md` edit remains).

### Mutations I ran myself

Each mutation was applied to committed code and reverted with `git checkout --`.

| Mutation | Result |
| --- | --- |
| B1 `consequence_read.py` `if not source_open:` becomes `if False:` | killed (1 failed) |
| B2 `finding_api.py` bridge always passes `source_open=True` | killed (`test_m1_the_source_gate_is_passed_to_the_read_and_bridge`) |
| B3 `demonstration_case` always returns None | killed |
| B4 STALE never uses the "queued" wording | killed |
| F1 `Headline` drops the `c.currentness === "CURRENT"` check | **survived (30/30), see L1** |
| F2 history marks the head current without checking currentness | killed (4 failed) |
| F3 main bridge table always `current={true}` | killed (5 failed) |
| F4 pinned panel's "same fuel amount" test inverted | killed (1 failed) |
| F5 `audit_only` notice removed from the Financials bridge | **survived (30/30), see L2** |

The implementer's claim that "headline ignores currentness" was killed does not hold for my form of the mutation (F1). The test at `siteFinancials.test.tsx:574` uses `state: "STALE"`, so the state check alone hides it.

## Findings

### H1 (High, fix on branch before owner checkpoint): non-current states show the stored amount in the main money panel; the evidence "no amount" claims are vacuous

- **Where.**
  - `frontend/src/sites/FindingConsequence.tsx:445-451`. `FindingBridge` renders `BridgeTable rev={head}` and `HowWorkedOut` whenever a stored head exists, whatever the bridge state is.
  - `FindingConsequence.tsx:195-204`. The amount row prints `<strong>0.00 to X USD</strong>` for any PRICED revision; when `current` is false it adds "Recorded for this version; not the current cost".
  - The unit test enshrines this: `frontend/src/sites/__tests__/siteFinancials.test.tsx:539-571` expects `data-bridge-amount="recorded"` for STALE, HISTORICAL and AUDIT_ONLY.
  - The evidence claims are vacuous: `tools/s402b-fuel-cost-evidence.mjs:248` and `:303` assert only the outer `data-financials-amount="none"` attribute (the headline gate). They do not check the panel text.
- **Observed** in my run, screenshots `%TEMP%\claude\s402brev3-shots\s402b-audit-only-{desktop,narrow}.png` (the implementer's `s402b-audit-only-desktop.png` shows the same):
  - The closed gate shows "Audit material only ... not a current claim" and the headline "For the record only: no current cost".
  - Directly below that, "From finding to money: the stored version, not a current cost" shows **"0.00 to 16.20 USD"** in bold, at 1.28 USD per litre.
  - STALE (`s402b-stale-narrow.png`) shows the headline "Out of date: no current cost", then a bold **"0.00 to 15.82 USD"**. Two panels further down, "Price in use" shows 1.28 USD.
- **Why it matters.**
  - The 2a review's M1 asked that the closed-source bridge "return that typed state with no amount". The backend does this (`bridge_consequence`, tested), but the UI fetches the consequence read and restores the amount in the same panel.
  - The dispatch criterion is "no number shown for any non-CURRENT/PRICED state". The task requires that a lagging projection be "never a zero or old amount presented as current". The amount is labelled, but it is the most prominent figure in the panel, directly under a headline that says there is no current cost, and next to a "Price in use" that differs from it. That is exactly the misreading this contract exists to prevent, and the owner's client-facing guidance says money must not be over-read.
  - The packet's acceptance table ("audit-only captured ... no amount") and walkthrough step 6 ("For the record only: no current cost") tell the owner something the screen contradicts. That makes the walkthrough inaccurate for this step. Step 5 does mention the labelled stored figure for STALE.
- **Fix.** This is the conservative fix; any final copy goes to the owner.
  1. In the main "What this finding means in money" panel, when the bridge is not CURRENT PRICED, show no amount:
     - the amount row reads "No current cost";
     - the price row shows no stored price as if applied;
     - add a pointer to "Fuel cost versions" for the recorded figures.
     Alternatively, move the stored-version table into a closed disclosure titled for the record. Recorded amounts stay where the task requires them: the version list and the explicitly opened pinned version panel, both labelled "kept for the record".
  2. Under `AUDIT_ONLY`, also suppress amounts in the version list and the pinned panel unless the coordinator rules otherwise. The 2a carry and this dispatch both say "no amount anywhere" for the closed-source state. The S3 audit statement already says the revision is not a current claim.
  3. Change the evidence claims at `:248`, `:303` and the HISTORICAL claim to assert that `[data-financials-bridge]` innerText has no `\d+\.\d\d USD` (and, for AUDIT_ONLY, the whole `main`). Update `siteFinancials.test.tsx:539-571` to match.
  4. Correct walkthrough steps 5 and 6 to describe what is then shown.
- This is not an acceptance gap in the backend; it is a UI regression of a reviewed carry.

### L1 (Low, test gap): the Headline currentness guard is unprotected

- **Where.** `FindingConsequence.tsx:371`. Mutation F1 survives.
- **Why it matters.** The backend never sends `state: PRICED` with a non-CURRENT currentness today, so this is defence in depth. But it is the guard the packet cites.
- **Fix.** Add a case in which the bridge has `state: "PRICED"` with an amount and `currentness: "STALE"`, and assert that no headline amount is shown.

### L2 (Low, test gap): the closed-source notice on Financials is untested

- **Where.** `FindingConsequence.tsx:443`. Mutation F5 survives.
- **Fix.** Assert the `audit_only.statement` in the AUDIT_ONLY test case.

### L3 (Low): the demonstration label fails open

- **Where.**
  - `backend/assetops_backend/demonstration_label.py:29-33`. An unreadable or missing spec silently returns no declared cases.
  - `:51-53`. An open episode (`end` None) is never labelled.
- **Why it matters.** Either case shows authored demonstration money with no label, which is the one direction the owner ruling forbids.
- **Fix.** Make spec-load failure loud: raise, or have a test assert the shipped spec parses with at least one case. Decide whether an open episode on a declared day should be labelled; it should be. See also Q11.

### L4 (Low): the two reads can disagree on one screen

- **Where.** `FindingConsequence.tsx:524-536`; the test at `siteFinancials.test.tsx:555` asserts it.
- **What happens.** With the bridge UNAVAILABLE ("Could not be read") but the consequence read CURRENT, the version list labels a version "the current fuel cost" with its amount, while the headline says it could not be read. The same applies to the general race between the two independent reads (cost-per-read residual).
- **Fix.** Mark a history entry current only when the bridge's currentness is also CURRENT, or derive the headline from the consequence read.

### L5 (Low): the consequence history UI has no pager

- **Where.** `FindingConsequence.tsx:553-559`.
- **What happens.** The read pages at 200 (`PAGE_LIMIT`). The UI says "Showing N of total" but offers no "Show later versions", unlike Assumptions.
- **Why it is Low.** It is unreachable at demonstration scale. It is noted because the packet asks for "complete paged history".

Nothing else found. In particular, the 2b scan of new frontend copy shows no untagged "not available" literal. The orphan guard passes unchanged. Typed runtime states (`QUANTITY_WORDS`, `PRICE_WORDS`) are runtime reasons, not absent-capability copy.

## Carry verification (2a review)

| Carry | Landed | My evidence |
| --- | --- | --- |
| M1 closed source: AUDIT_ONLY, no amount | **Backend yes; UI no (H1)** | `consequence_read.py:160-164`; route test `test_m1_a_closed_source_gate_never_presents_an_amount_as_current`; B1 and B2 killed |
| M2 HISTORICAL test | yes | `test_m2_a_superseded_finding_revision_reads_historical_with_no_current_amount` (a real second FindingRevision through the test-scoped model upgrade); I verified the B1 path; the 2a mutation is now covered per the packet and my suite run |
| L1 401/403/503 | yes | `TestConsequenceRouteCarries` |
| L2 completeness half | yes | UNPRICED clone matched on its own message (`test_s4_consequence_store_postgres.py:330-337`) |
| L3 latest filter and skip | yes | `TestPhase2bCarries::test_l3_*`; the skip test counts attempt rows |
| L4 STALE wording and scope | yes | B4 killed; `test_l4_pending_work_lists_only_work_that_touches_this_finding` |
| Carry 3 frontend types | yes | `financialsClient.ts` unions; the old `SiteFinancials.tsx:481` wording is gone |
| Carry 4 walkthrough gate | yes | Each DB has its own code tree, so each keeps its own source gate (`tree_of`); `close-gate`/`open-gate` work without restarting `serve` (verified) |
| Carry 5 Q2 to Architect | open, batched | |
| Carry 6 no merge before 2b | satisfied by 2b | |

## Whole-slice acceptance

| Criterion | Status |
| --- | --- |
| Bridge quantity → price → amount, range from zero, currency, plain "modelled, not a measured saving" | Met for CURRENT PRICED; the exact default sentence is rendered |
| IDs, digests, formula and `MODELLED_CONDITIONAL` only in disclosures | Met (visible-text UUID scan 0 in my run; the opened disclosure holds them) |
| No simulator language on product screens | Met inside `main`. The "Open Simulator Lab" workspace-utilities link in the top bar is pre-existing shell chrome |
| Typed no-amount states | Typed and worded. **The amount is suppressed only in the headline (H1)** |
| Old/new after v4, same FindingRevision and quantity | Met: two versions, same `technical_input_sha256`, 15.82 then 16.20; the pinned version says "fuel amount is the same" |
| Reload, back/forward, keyboard, Evidence round trip | Met (claims passed in my run) |
| Assumptions shows the used price, source, SYSTEM actor and earlier versions | Met for price versions. Consequence versions are on Overview (Q12) |
| Ordinary Findings qualifying | 0 of 11 (8 / 2 / 1), stated plainly; the positive amount comes only from labelled P01-power. Reproduced |
| G-05 itemization by manifest element | Present in the packet and in the `SiteFinancials.tsx` header (`financials:3#a/3#b`, `assumptions:2#a`, extra cards, maintenance line, Scenarios, cash flow, FX, extrapolation; `mini:4#a` stays with S5-01) |
| Human edit disabled; no "Scenario" label (L6) | Unchanged and met |

## Q10-Q15 rulings

| Q | Ruling | Note |
| --- | --- | --- |
| Q10 `AUDIT_ONLY` as a fifth state | **Acceptable** | Keeps "earlier version" distinct from "source not open"; precedence is correct (`consequence_read.py:160`). Its UI must carry no amount (H1) |
| Q11 demonstration label derived from spec Site and day | **Acceptable for this slice; Architect/Planner batch; not a merge blocker once L3 is fixed** | See below |
| Q12 consequence versions on Overview, not Assumptions | **Architect batch; gates `assumptions:3#a` promotion** | See below |
| Q13 STALE and PENDING kept separate | **Acceptable** | Wording follows the actual pending work (L4 verified). Owner question 4 |
| Q14 `PRICE_SPANS_WINDOW` not staged | **Acceptable** | Covered by the Postgres `test_a_correction_inside_the_window_appends_an_unpriced_revision` and the frontend case. The walkthrough's "price changes part-way through" reason text is not walked visually; say so to the owner |
| Q15 pinned view keeps the head panel | **Acceptable** | It makes the old/new comparison explicit. Once H1 is fixed, a STALE head panel no longer competes with the pinned figure |

**Q11 in detail.**
- **Why it is acceptable now.**
  - It is presentation-only and changes no state or amount (B3 shows only the label test fails).
  - It is Site- and day-scoped, and the spec days are tested clear of the S4 case days.
  - A false positive would label a non-demo KOBO-001 Finding wholly inside 2026-10-23 UTC as authored demonstration data. That is untrue but under-claims; it never presents demo money as real.
- **What is unsafe.** Only the fail-open cases in L3. Fix them on the branch.
- **Limits that must be stated plainly.**
  - The label is not tenant-scoped.
  - 2026-10-23 is nine days away. If the Lab's live KOBO-001 gateway produces S4 Findings on that UTC day in any database, they will carry a false "written by the AssetOps team" statement.
- **Architect/Planner item.** Record authorship (a batch or source label) at ingestion, and retire the date heuristic before any non-demonstration tenant, or before live Lab data can land on a declared day. Link it to the owner backlog item "analysis input data for simulated and real Sites".

**Q12 in detail.**
- The manifest claim for `assumptions:3#a` is "prior assumption and consequence revisions at selected cutoff".
- What is built:
  - price versions at a recorded cutoff on Assumptions;
  - consequence versions per Finding version on Overview, by exact ID, with no recorded-cutoff selection.
- The task text also places consequence revisions in "the Assumptions History view".
- Either the Architect rules that Overview plus exact-price links satisfy the claim, or `assumptions:3#a` is promoted only for its price portion and the consequence-at-cutoff part goes to G-05 or a later read.

## Owner-walkthrough focus items

- **Steps 5 and 6 must be corrected after H1.** As built, the closed-source view shows a bold recorded amount, and the walkthrough does not say so. Re-walk the copy on the owner DBs only after the fix.
- The tool itself is correct and repeatable:
  - private code trees per DB keep the gates independent;
  - DB-name and work-name guards refuse the template, `*_test` DBs and other slices' folders;
  - `links` prints the exact IDs, and the printed IDs match the walkthrough (stable across template copies).
  - My own prepare-and-evidence run on fresh copies reproduced every state.
- The owner should explicitly see and approve:
  1. the final money sentence;
  2. that the stored figure does **not** appear for out-of-date or closed-source states (after the H1 fix);
  3. the demonstration label text and the 0 of 11 explanation;
  4. that `PRICE_SPANS_WINDOW` is tested, not walked.
- Q5 and Q6 are carried S4-02a items (the version-1 "no end date" wording, the 390 px tab wrap). Both are unchanged and were previously accepted for now.

## Registry closeout notes for S4-02 (for the coordinator)

These apply only after the H1 fix, its focused re-review, and the owner checkpoint.

- **May resolve:**
  - `I-financial-store` (migration 0011, append-only rows, link tables, durable work);
  - `D-financial-basis` (fuel-cost-1 bounded and unavailable public-input fixtures, whole-window price, repricing, old/new lineage);
  - `I-financial-read` and `I-consequence-history-read` (`/financial-consequences`, exact and foreign-ID refusal, paging, typed states);
  - `I-financial-ui` (once H1 is fixed);
  - `I-S4-02b`, then `I-S4-02`.
- **W1 core portions:**
  - `financials:1#a` and `financials:2#a`: promote, with evidence = this review, the re-review and the evidence tool claims at 1440/390.
  - `assumptions:1#a`: already supported by S4-02a; promote with the S4-02 closeout.
  - `assumptions:3#a`: **conditional on the Q12 Architect ruling**. If not ruled sufficient, promote the price-history portion only, and itemize consequence-at-cutoff for G-05.
- **Do not claim:** non-core `financials:3#a/3#b` or `assumptions:2#a` (itemized for G-05), or `mini:4#a` (S5-01). Ledger claims must not state Real ordinary-data money: 0 of 11 ordinary Findings qualify, and the positive amount is labelled demonstration data.
- **Keep open:** `G-foundation-financial-assumptions` (S4-02a ruling); the Q2 and Q11 authorship items in the Architect batch; the owner backlog item on analysis input data.

## Residual risk not named in the packet

- The evidence tool's state claims key on data attributes, so any copy that leaks a figure under a typed state passes. H1 fix 3 closes this for money; consider the same text-level assertion for future money slices.
- The demonstration date heuristic will mislabel live KOBO-001 data on 2026-10-23 UTC if any is produced (Q11).
- Two independent reads per view (bridge and consequences) can disagree momentarily (L4). Each fresh derivation is per read (2a "cost per read").
