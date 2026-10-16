# W1-UX plan review (fresh independent Reviewer, 2026-10-16)

Scope: plan review of `tasks/W1-UX-mockup-fidelity.md` and `tasks/W1-UX-01..05` at `fec27edd` (diff `fec27edd~1..fec27edd`), against the owner notes named in the brief, `.agent/planner-W1-ux-brief.md`, v69 `index.html`/`screen-manifest.json`, current code at `fec27edd`, and the unmerged branches `task/S6-03-site-work-list`, `task/S6-02b-verification-ui`, `task/S7-01b-health-ui`. Nothing built; no suites run. The two Architect questions are being ruled separately; neither recommendation is unsafe, so I make no comment on them beyond finding 1 (which concerns the vocabulary map, not Q2).

## Verdicts

| Packet | Verdict | Blocking findings |
| --- | --- | --- |
| W1-UX-mockup-fidelity (umbrella) | RETURN | 3, 4, 5 |
| W1-UX-01 shared presentation | RETURN | 1, 2, 3 |
| W1-UX-02 Site and money | RETURN | 4, 5 |
| W1-UX-03 Evidence and performance | ACCEPT | none |
| W1-UX-04 Actions and work | RETURN | 4 |
| W1-UX-05 Configuration and health | ACCEPT | none |

All blocking findings are text fixes to the plan; none needs re-planning the slice split.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 239 nodes, 11 linked pilot panels`, exit 0. Five `I-W1-UX-0x` nodes added with `task` fields and `outside_ranking` entries; README rows present.
- `tools/check-agent-workflow.ps1`: `Agent workflow check passed.`
- Code reality: all 19 cited component files exist at `fec27edd` and every cited line range is within file length. Spot-checked content: most anchors hit the named seam (e.g. `SiteAction.tsx:451` "Application" panel, `assessmentAnalysis.tsx:242-257` method/revision facts, `EvidenceClaimLimit.tsx:300` claim-limit panel, `ReadinessOverview.tsx:264,512`). Two are imprecise (finding 6).
- Coverage: registry `delivery_plan.owner_inputs.W1.approved_manifest_ids` has 27 IDs; minus `lab` = 26; the inventory has exactly those 26 rows. Pending-branch screens exist: S6-02b adds `SiteActionVerification.tsx`, `recommendationVerification.tsx`, `verificationWords.ts` (Plan/Evidence/Verification); S6-03 adds `SiteWorkActions.tsx`; S7-01b adds `SiteHealth.tsx`, `SiteBattery.tsx`. UX-04/05 defer to re-inventory at merge, which is adequate.
- Slice size: each packet has two phases and is frontend-only with an Architect stop for absent labels. Acceptable (see finding 9 on UX-04 effort).
- Walkthrough tools named in the umbrella exist in `tools/`; S6-02b/S6-03/S7-01b tools exist on their branches (`s602b_verification_walkthrough.py`, `s603_site_work_walkthrough.py`, `s701_health_walkthrough.py`).

## Findings

### 1. Medium (honest state) - W1-UX-01: example map collapses guardrail failure and overstates VERIFIED
`tasks/W1-UX-01-shared-presentation.md:9` maps `INEFFECTIVE` -> "The trial did not meet its goal" and `VERIFIED` -> "The measured trial met its goal and safety limits". Under `D-2026-10-16-s6-verification` (`.ai/DECISIONS.md:4155`) and `tasks/S6-02b-verification-ui.md:15`, `INEFFECTIVE` covers both a target miss and a measured reserve/service `GUARDRAIL_FAIL` (a reason, not an outcome), and S6-02b's accepted interim wording distinguishes "Target not met" from "Trial missed a safety or service limit" with metric/value/threshold/unit. A shared map keyed on the outcome enum alone would render a safety failure as an ordinary goal miss in every consumer. The VERIFIED sentence also drops two qualifiers the contract requires: the reserve guardrail is a "five-minute sampled guardrail, never continuous physical SOC proof" (`S6-02a-verification-core.md:15`), and only demo-source evidence may support a labelled demo verdict with "no savings or realized benefit". "Met its safety limits" is a stronger positive claim than the read proves.
Why it matters: the shared layer is what every later slice consumes; an error here propagates to Action, Verification, Recommendation and Changes.
Fix: key the outcome vocabulary on (outcome, reason) and source class, not the enum alone; keep the S6-02b guardrail-fail and target-miss sentences verbatim as the floor; VERIFIED wording must carry "sampled" guardrail scope and the demo/policy-trial label where the source is demo; add matrix cases for INEFFECTIVE+GUARDRAIL_FAIL, INEFFECTIVE target-only, INCONCLUSIVE with known failure, and demo-source VERIFIED.

### 2. Medium - W1-UX-01: scan extension breaks unmigrated screens; no ratchet plan
`W1-UX-01:13` extends `productVocabulary.json` with new terms (enum/reason-code shapes, "rule ID", "model version", raw IDs) and scans "every W1 product route", but phase 2 migrates only three cards. Existing tests assert zero violations on screens UX-02..05 will not touch until later (e.g. `frontend/src/shell/__tests__/s5SiteWindowOverview.test.tsx:217-218`, `frontend/src/sites/__tests__/siteAction.test.tsx:146-148`, and the other ~13 consumers of `scanProductVocabulary`). Adding terms globally either fails those tests on UX-01's branch, or pressures the implementer to exempt or weaken. The current scanner is also phrase-only (`frontend/src/test/productVocabulary.ts:57-64`), so "reason-code shapes" needs a new pattern mechanism the packet does not specify.
Fix: specify a ratchet. For example, UX-01 adds the new term families and pattern support behind a per-route opt-in (or a versioned "W1-UX" term set that each screen test adopts when its slice migrates it), proves the term set with mutation tests, and each of UX-02..05 turns it on for its own routes. Then the umbrella's final audit requires every W1 route to be on the full set before the combined walkthrough.

### 3. Medium (honest state) - W1-UX-01 and umbrella: limits can move into the closed disclosure, and the disclosure exemption is undefined
`W1-UX-01:7` puts "decision basis" into the closed "How this was worked out" disclosure. `W1-UX-01:13` scopes scan exemptions to "exact source-owned reference values and disclosure content". The current guard allows only the three exclusions in `D-2026-10-04-plain-language-analysis-views`, one single-value element at a time, and explicitly refuses exempting a container (`productVocabulary.ts:12-16`, `:116-121`). Exempting "disclosure content" wholesale reverses that rule, and it needs an Architect amendment of that decision. Together these let a stale/pending/limited/unknown explanation migrate into a collapsed region where nothing tests that it is still visible. "Show scope and limit near the headline" is stated but not tested.
Fix: (a) define the disclosure scan rule precisely: disclosure content is scanned against a narrower technical list, never skipped, and the single-value rule still holds for exemptions; route the change to D-2026-10-04 to the Architect. (b) Add a common acceptance test in UX-01 (and require it in each of UX-02..05): for every non-positive state (unassessed, pending, stale/non-current, unknown, refused, withheld money, proved-zero), the plain-language state sentence and its scope/as-of bound render outside the collapsed disclosure, with the disclosure closed.

### 4. Medium (honest state) - UX-02, UX-04, umbrella: watermark and cutoff moved to detail conflicts with proved-zero and as-of guarantees
`W1-UX-02:7` moves "cursor/watermarks" into `DigDeeper`, and the same packet keeps "S4-04 proved-zero watermark". Umbrella rows `sitefindings` and `sitework` (`W1-UX-mockup-fidelity.md:27,38`) say "cursor/watermark to detail". `W1-UX-04:9` moves "exact cutoff" to `DigDeeper`. A zero or current claim is only honest with its as-of bound visible; a "No open Findings" or "No active work" line without the watermark time reads as an unbounded positive.
Fix: state that the plain as-of time ("as of <time>") of any zero, current or historical selection stays in the default reading beside the claim. Only opaque cursor tokens and raw IDs move to detail. Cover this with the test in finding 3(b).

### 5. Medium - umbrella and UX-02: combined walkthrough is not mapped to screens, and the `sites` lead question overstates the read
(a) Walkthrough: `W1-UX-mockup-fidelity.md:54` gives an ordered tool list but no screen -> tool -> route map, so it cannot be checked that all 26 screens are reachable. It omits `tools/s405_provenance_walkthrough.py` (S4-05b, the walkthrough that triggered this pass, and whose "interim source labels" UX-03 revisits) and `tools/s502_overview_finding_list_walkthrough.py` (S5-02 Overview Finding list, a UX-02 surface). It names an unspecified "S1 owner fixture" where `tools/v01a_foundation_walkthrough.py` exists. No packet owns producing the ordered list before the owner session.
Fix: add a 26-row table (screen ID, tool, prepare/serve flags, route, which state it demonstrates: supported/limited/stale/proved-zero), add the S4-05b and S5-02 tools, name the Foundation tool, and assign authorship (for example, the UX-05 closeout or the coordinator) with an explicit gate before the walkthrough is scheduled.
(b) `sites` lead: umbrella row 15 and `W1-UX-02:7` use "Which site needs attention?", while the mock's question is "Which site should I open?" (`screen-manifest.json`, `sites`). "Needs attention" implies a per-site condition ranking the read cannot supply (`sites:2` and estate health are gaps), which contradicts the same row's "No estate health inference". Fix: use the mock question, or another phrasing that does not imply ranking.

### 6. Low - two inventory anchors point at refusal states, not the named seam
`SitesIndex.tsx:108-132` is the unavailable/empty panels; the inventory table starts at `:133` (the registry anchor is `:134`). `SiteFindingHistory.tsx:145-171` is the refusal-words map, not the history timeline. Fix: re-anchor. This is non-blocking because implementers re-inventory.

### 7. Low - existing per-screen word maps are not inventoried for consolidation
Word maps already exist in `dispatchWords.ts`, `findingWords.ts`, `findingPresentation.tsx:33,329`, `actionPresentation.tsx:21,53,64`, `EvidenceClaimLimit.tsx:39-128`, `SiteFinancials.tsx:43`, `FindingConsequence.tsx:34,63,400`, `OverviewFindingList.tsx:262`, and S6-02b adds `verificationWords.ts`. UX-01 asks for "one" map but does not say whether it absorbs, wraps or coexists with these. Without that, a parallel map is likely. Fix: list them and state the migration rule (shared map owns cross-screen states; screen maps keep domain-specific words and are read through it).

### 8. Low - layout proof tool and the not-run rule are not named
The packets require 1440/390 app-versus-mock screenshots but do not name the mechanism. A precedent exists (`MOCK = (id) => .../mockups/v69/index.html#/${id}` in `tools/v01a-foundation-evidence.mjs:137` and `tools/v01b-lab-evidence-evidence.mjs:222`). Fix: name the per-slice evidence script pattern, and require a skipped capture to be recorded as `not run` with its blocking precondition.

### 9. Low - baseline and effort ambiguity
`W1-UX-01:3` branches from "merged W1 UI baseline", but `I-W1-UX-01` requires only `A-S5-overview`. State whether UX-01 waits for S6-02b, S6-03 and S7-01b; otherwise verification and health vocabulary lands in UX-04/05, not the shared layer. UX-04 covers nine screens, including the 1420-line `SiteActionVerification.tsx`, so registry effort `M` is likely under-sized (consider `L`).

### 10. Low - `PENDING_REASSESSMENT` example wording implies active processing
"New readings are being checked" asserts that work is in progress; the state means a reassessment is due. The packet already requires entries to be reviewed against the typed source. Flagged only so the reviewer of UX-01 checks it.

## Residual risk not named in the packets

- UX-04 restyles S6-02b's guardrail and withdrawn-outcome presentation shortly after S6-02b merges. The fail-closed tests in `siteActionVerification.test.tsx` (549 lines on the branch) are the only guard; the UX-04 reviewer should diff that test file and treat any weakened assertion as blocking.
- Visual "headline plus visual" cards invite derived graphics (bars, timelines) whose geometry can imply a value the read did not give (for example a zero-length bar for unknown). UX-01's matrix should include an unknown-value visual case that renders as a distinct "not known" mark, not zero.
