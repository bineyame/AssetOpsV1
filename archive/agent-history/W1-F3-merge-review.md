# W1-F3 merge review (5ed3162b + cceb882b)

Verdict: ACCEPT

Checks run (this machine):
- `npx.cmd tsc --noEmit` in frontend: exit 0.
- `npx.cmd vitest run panelStructure statusbar Structure siteFinding siteFinancials s404 siteOverviewScreen`: 11 files, 340 tests passed (includes panelStructure.test.ts 9/9, finding/history/financials/finding-index, overview). Full suite 2133 is the implementer's figure; not rerun.
- No test file was changed by conflict resolution (`git diff --cc 5ed3162b` on tests is empty), so no assertion was altered by the merge. The follow-up cceb882b touches only 4 src files.
- Callers: StatusBar `items` is used by exactly the three F3 callers (SiteFinding, FindingConsequence, SiteFindingIndex); F2/F4/W2-01 callers (SiteWindowOverview, SiteOverview `other`, SitePerformance, PerformanceDispatch, SiteEvidence, LedgerSiteEvidence) use the lead mode, unchanged. Disclosure `variant="tech"` callers (F2/F4/W2-01) get the same class as before; `variant="inline"` only in SiteFindingHistory, now `disclosure--tech disclosure--inline`. All `ProductStatus inline` callers share one renderer. V69Notice is a pure alias of Notice (LedgerSiteEvidence).
- CSS: compared selector sets of both parents against the merge. Nothing from main is missing. From F3, the only selectors absent are the intended removals (`.status-strip__state ...` retargeted to `.product-status--inline`, `.status-strip--line .product-status__label`, `.v69-state-line .product-status__label` folded into a combined selector) plus `.v69-prose p + p` and `.dispatch-blocks li` / `.exact-references--tech` which are present in the merged file in reformatted/merged form (grep confirmed lines 2951, 4797-4817).
- Screenshots (finding f01 1440, mini p01 390): statusbar chip strip renders as one line with the date right-aligned; layout matches expectation, no visible regressions.

Not verified: frontend production build and layout-evidence rerun (sandbox/Chrome); relied on the screenshots only.

Behaviour changes judged acceptable:
- Statusbar role group -> status with aria-label kept: a live region on a static strip is low risk; tests pass.
- "next" separator " . " (aria-hidden) -> plain space: no visual loss in the inline renderer; tests pass.

Findings (none blocking):
1. Low: in the finding screenshot, the "What happened" state line begins with a stray leading " ·" before "Source unverified." (likely the inline bound/next separator when the label is empty or hidden). Cosmetic; check whether it predates the merge and tidy in the UX pass.
