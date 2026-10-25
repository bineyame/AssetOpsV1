# post-W6 W1-a: independent review

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review4`, branch `task/post-W6-W1-a`,
head 7e1cdb73. Diff `git diff main...HEAD -- ':!.agent'` (31 files). Governing: `post-W6-W1-rulings.md` cross-card 1-5,
6-29, 48-63; W3 closeout ruling 1 for the cap-probe question.

## Verdict

**ACCEPT with findings fixed on the branch.** Every Q1-Q18 ruling is implemented as ruled, with the copy verbatim,
the links correct and the guards intact. One Medium finding (M1) has to be closed before merge: the worst-case cap
proof for "Where to look next". This is the Q38 question the coordinator asked about. The remaining findings are Low.

## Findings

### M1 (Medium, acceptance gap under cross-card 4): worst-case closed caps unmeasured; a W3-style probe is needed

`frontend/src/sites/SiteFinding.tsx:967-974`, `:1050-1065`, and recapture `index.md:122-125`.

- **What is wrong.** Cross-card 4 states the worst cases explicitly:
  - Where to look next 650/1000: "one item and five long related titles".
  - What limits 450/800: "added link and five 160-character limit rows".
  - Revision history 850/2000: "five long related rows and local times".
  - Q5's role table: "five 160-character closed role rows".

  Q15's fallback (Related Findings behind its count disclosure) can only be decided by measuring that worst case. The
  recapture measured only producible content. The worst real case for Where to look next at 1440 is **613 against
  650**, which leaves 37 px.
- **Why the worst case is real.** Related Findings is an unbounded list. `recurred_by`, `split_parts`, `merged_from`
  and `merged_into` are arrays. Each item is a fixed label of about 30-35 characters, rendered as an inline list. So
  five related rows are a real product state, even though no reviewed producer emits one. Five links of that length
  wrap onto two or three more lines in the 1440 column, which plausibly takes the panel past 650. If it does, the
  ruled Q15 fallback applies and is not built.
- **What the ruling allows.** Q38 allowed an honest gap at the time. W3 closeout ruling 1 has since accepted a
  capture-only, labelled synthetic DOM probe on the real mounted page as cap proof where producers cannot emit the
  rows. That is exactly this situation.
- **Fix.** Use the W3 ruling-1 method on the mounted `finding` page (start from s404 `late-stale`, the tallest case)
  at 1440 and 390:
  - Clone the real Related Findings `<li>` to five rows, and also run a 160-character label variant to meet the
    ruling's wording.
  - Clone the What limits rows to five at 160 characters.
  - Clone the finding-history version rows to five, with long related text.
  - Clone the evidence-analysis "How each limit is set" role rows to five at 160 characters.

  Assert that every intended field changed. Record the panel heights, clipping and overflow, and label the output as
  synthetic layout evidence. If Where to look next goes over its cap, apply the Q15 count-disclosure fallback and
  recapture. If faithful content still cannot fit, return the measurements to the Architect before merge.

  The packet also contradicts itself, and the probe would settle it. Packet "Results" and `index.md:134` both say
  "Capture gaps: none", but the packet's next paragraph records the five-long-row case as a capture gap.

### L1 (Low, test gap): no test for a stale cost response arriving after the selection changes

`frontend/src/sites/__tests__/siteFinding.test.tsx:~960-1010`.

Q12 rules that "stale responses cannot replace a new selection". `useFindingCost` (`SiteFinding.tsx:~753-776`) does
this correctly: it uses an `active` flag and compares each answer's `key` with the current version. No test drives
it, though. In the packet's list, "stale" means the PRICED-but-STALE currentness case, not a race. When I reverted
`SiteFinding.tsx`, the cost tests that still passed were the negative ones. So if someone later removes the key check,
nothing catches it.

**Fix:** add a test with deferred cost promises. Select version A, switch to version B, then resolve A's PRICED answer
after B is selected. Assert that A's amount never appears.

### L2 (Low, needs an Architect note): three of the builder's choices that the rulings do not cover

Each choice is defensible. Each should be noted to the Architect, not changed here.

1. **Q10 (`SiteFinding.tsx:~666`).** The status period is Site-local, but the What happened description
   (`Period covered · {periodWords}`) and the panel prose stay in UTC. One page shows the same period in two zones.
   The ruling names only the status period, so this is within scope.
2. **Q12 (`SiteFinding.tsx:~790`).** The amount also requires `currentness === "CURRENT"`. That is the same rule as
   Financials' `shown` (`FindingConsequence.tsx:730`), and the formatting is the same as its `range()`. So this is
   sound and consistent; the ruling said only "PRICED".
3. **Cross-card 1 (`LedgerSiteEvidence.tsx:~95`, `EXTRA_EAT_ZONES`).**
   - What it does: the wrapper keeps a three-zone label override (Asmara, Djibouti, Mogadishu → EAT), because the
     canonical `siteTime.ts` must stay byte-identical to W2-EV.
   - Why it matters: it is a label table, not a second time algorithm. But it means a Site in one of those zones
     reads "EAT" on Evidence and "GMT+3" on Finding pages, which use `findingTime.ts` → `siteTime.ts` with no
     override.
   - Fix: W2-EV should add the three zones to the canonical table and delete the override. Record this in the W2-EV
     rebase note.

Related copy point, Low: with an invalid (not missing) zone, the fallback suffix reads "(site time zone not recorded)"
(`SiteFinding.tsx:~587`). That is slightly untrue, because a zone was recorded but could not be read. A neutral
wording such as "site time zone unavailable" would be accurate in both cases.

### L3 (Low, register category): R386 is filed as D6

`.agent/mock-departure-register.md:484`.

- **What is wrong.** R386, the global error-boundary backlog row required by Q47, is filed as **D6 technical
  constraint**. It is not a mock departure or a platform constraint.
- **Why it matters.**
  - It contradicts the D6 narrative ("No unresolved D6 ruling was found").
  - It meets the rule at line 211, "each open D1/D2/D4/D5/D6 row must show `MOCK DEVIATION Dn`", even though there is
    no element to label.
- **Fix.** Ask the Architect for the category. A non-D backlog marker, or a note that this row is exempt from the
  labelling rule, would do.

All other rows are correct:
- R387-R395 match their G1 (b) dispositions, and each has its `MOCK DEVIATION` source label with the right number
  (checked at head).
- The table format matches the shell rows R378-R382.
- There are no collisions: main ends at R382, and R383-R385 are left for W1-b.

### L4 (Low, capture bookkeeping)

1. **Exempt list.** `index.md:128` lists finding `open` under "Exempt" because the script exempts "cases named
   open/expanded". Here `open` is the Finding lifecycle case with closed disclosures, not an expanded view. Its values
   (613/716/308/414) are within the caps, so the result is unchanged. The exempt list should not include it.
2. **Q1 shared crumb.** Q1 asks for a "shared crumb representative", and the handoff (line 41) lists "SiteDetails
   crumb" among the Q40 pairs. The capture brief dropped it, and no non-mini `SiteDetails` pair was captured. The 12
   `mini` pairs do exercise the same `SiteDetailFacts` trail. Either capture one shared SiteDetails pair, or record in
   the packet that mini is the only `SiteDetails` reach at 1440/390.

## Rulings checked (implemented as ruled unless noted)

- **Q1:** the crumb is `Sites › {site} › Overview`, with the Site crumb linked (`siteHref` from `SiteDetailFrame`).
  Cold and EV frames are untouched.
- **Q2/Q48:** the footer `View detail →` link is on Service, Fuel, Renewable, Dispatch (selected `utc_date`) and
  Battery (`siteAssetsHref`).
  - Dispatch tone: amber only for current `CANDIDATE_AVOIDABLE`. A current read with another level gets the gray
    `--assessment` border (`#abb5c6`). A card with no read has no border.
  - Battery keeps its no-condition value, with no tone.
- **Q3:** `Single line diagram →` to `siteFoundationViewHref(id,"sld",window.end)`. A null `at` gives the bare route.
- **Q4:** the labels are local ("Finding reason {n}"). `ProductStatus.tsx` is unchanged.
- **Q6:** `isIntervalRevision` refuses a `WINDOW` scope, and also any scope whose `result.segments` is not an array or
  whose interval is not an object. The refusal happens before `selected.result.segments` is indexed.
  - The title, body and "Open this day" copy are verbatim. The link removes `revision` and `block`.
  - There are no hooks after the early return.
  - A valid interval from another day still passes through to the labelled stored notice.
- **Q7:** Analysis is live at `?revision_id=…&view=analysis`, with `aria-current` through `current="analysis"`.
  `LocalViews` is removed from `SiteFinding` only; it is still used elsewhere, so it is kept. The helper is removed on
  Evidence and History, and kept on Recommendation for W1-b (Q44).
- **Q8/Q13:** one `Inspect financial assumptions →` link, after the recommendation button (and also in the
  no-recommendation branch). The aside is removed.
- **Q9:** `Open site` on every section.
- **Q10:** shown in the local format with a closed "UTC time" detail. The stored and query instants are unchanged.
- **Q11:** `Inspect evidence →` in the panel head. At 390 the panel measured 562 against 600, so it did not need to
  move to the foot.
- **Q12:** one `getFindingFinancials` read per resolved version.
  - No read is made without a resolved version.
  - Every non-priced state shows "Not available" with a reason that names the state. A mismatched revision is
    refused case-insensitively.
  - The note is verbatim. The link goes to the Financials overview at that finding and revision.
- **Q14:** `See analysis and alternatives →` foot link. The disclosure is kept.
- **Q15:** the order is Analysis, Evidence, Alternatives, History, Dispatch day, Related. The description and link copy
  are the mock's verbatim (`index.html:461`).
- **Q16:**
  - Evidence and History use the h1 "Finding" when the read is not loaded.
  - Recommendation takes its title from the frame: the record title once loaded, "Finding" on refusal. The frame's
    default is "Finding".
  - A refused selection shows the short disabled tab, with the full reason on the line below it.
- **Q17:** heading `Time ({zone})`, cells `D Mon · HH:MM`, UTC in the `title` and in the detail.
- **Q18:** the lenses sit above the strip and stay disabled. `LensChips` accepts optional hrefs, which no current call
  passes. `Manage in Findings →` goes to `FINDINGS_PATH`.
- **Cross-card 1:** `HEAD:frontend/src/sites/siteTime.ts` = `3c533f0f:…` = blob `2b390038…` (verified with
  `git rev-parse`). `findingTime.ts` and the `LedgerSiteEvidence` helpers delegate to it; the old `zoneClock` and the
  zone table are gone, apart from the L2.3 override.

## Guards (not loosened; still fail on mutation)

- `navigation-truthfulness.ps1`: the expected multiset swaps one entry (Analysis becomes Alternatives) and keeps its
  size. The fixtures were rewritten to mutate the new entry. I ran a manual mutation: I replaced the refused
  `{ id:"alternatives", label:"Alternatives", unavailable:true }` with a gap and ran
  `Invoke-NavigationTruthfulnessCheck`. It failed with 1 failure ("…the W1-plus-W2 inventory is exactly the multiset
  …"). I restored the file afterwards.
- `panelStructure.ts`: adds only the one exact attribute selector `[data-alternatives-finding-unavailable]`. It is
  narrow and was ruled under Q16.

## Checks I ran (at 7e1cdb73)

- **`npx.cmd tsc --noEmit`:** exit 0.
- **`tools/check-all.ps1`:** all 11 guards passed. That includes architecture, navigation truthfulness, agent
  workflow, missing-claim (42 tagged / 10 baselined) and the screen ledger.
- **Targeted vitest:** 14 files, 465 tests, all passed. Vitest did run in this worktree.
  - findingTime, performanceDispatch and siteFinding: 116.
  - s404, s5SiteWindowOverview, siteDetailRoute, siteDetailScreen, measuredTime, miniDecisions, siteFindingEvidence,
    siteFindingHistory, w1f4RecommendationStructure, siteAction and t028Screens: 349.
- **Single-file revert proofs** (each file restored with `git checkout HEAD`; the tree was clean afterwards):

  | File reverted to main | Result |
  |---|---|
  | `PerformanceDispatch.tsx` | 2 Q6 tests fail |
  | `SiteFindingIndex.tsx` + `SiteFindingHistory.tsx` | 10 fail (6 s404, 4 History Q16/Q17) |
  | `SiteFinding.tsx` | 14 fail (Q8, Q10 x2, Q11, Q12 x7, Q14, Q15, W1-F3 order) |

- **Revision check:** between the capture SHA 56d36bf2 and the head, the only frontend changes are comments
  (`MOCK DEVIATION` renumbering) plus one test `waitFor`. Between a054e1ae and the head, only the packet changed. So
  the packet's full-vitest run (3068/3068, a054e1ae) and the captures both apply to the reviewed code.
- **Stray-file check:** `git diff --name-only main...HEAD`, filtered for venv, node_modules, cache, `var/` and
  `dist/`, returns nothing.
- **Recapture coverage:** 98 rows.
  - The 88 indexed pairs: mini 12, dispatch 14, evidence-analysis 16, finding 12, finding-evidence 8,
    finding-history 10, sitefindings 16.
  - 10 Q40 pairs: alternatives, opportunity-finding, recommendation, cold-finding and ev-finding, each at 1440 and 390.
  - Every row has overflowX 0. The only title mismatches are the two expected dispatch window-id refusals.

## Not verified

- **Production build:** not run, as instructed. The packet reports a pass at 56d36bf2.
- **Full vitest:** not rerun. I cite the packet's 3068/3068 at a054e1ae.
- **Captures:** not rerun. I read only `index.md` and `selection.json`; I did not open the screenshots.
- **Backend:** not run. This is a frontend-only slice.

## Residual risk

- The worst-case closed-panel heights (M1) are the main open item.
- The W2-EV rebase must fold the three EAT zones into `siteTime.ts` and delete `EXTRA_EAT_ZONES` (L2.3). Both W2 lanes
  must rerun the mini regression over the Finding hunks.
- The Q16 refusal line now renders on every Finding section, Overview included, whenever the selection refuses. On
  Overview that sits beside `SiteFinding`'s own refusal panel, so the page carries two refusal messages. This is
  acceptable under Q16's wording.
