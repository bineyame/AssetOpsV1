# Architect request: W1-a review follow-ups

You are the AssetOps Architect. The W1-a review (`../AssetOpsV1-review4/.agent/post-W6-W1-a-review.md`, branch `task/post-W6-W1-a`, head 3fd3df6d; packet `.agent/post-W6-W1-a-packet.md` there) raised points needing your ruling. Rule exactly:

1. **R386 category.** The global error-boundary backlog row (Q47) is filed as D6 "technical constraint", which conflicts with the D6 narrative and the labelling rule at `.agent/mock-departure-register.md` line ~211 (in review4). Give the correct category/treatment (or say it should be a backlog entry outside the register) and exact row text.
2. **Q10 mixed zones.** The Finding status period is shown in Site time, while the "What happened" description period stays in UTC (labelled), so one page shows the same period in two zones. Accept, or rule that the description also uses Site time (with exact format).
3. **Timezone fallback copy.** "(site time zone not recorded)" is shown also when a zone is recorded but invalid. Give exact copy for the invalid case (or a single copy for both).
4. **Q12 currentness.** The builder made the cost card require the cost to be current (matching Financials' rule); a priced but out-of-date version reads "Not available". Confirm or correct.
5. **EAT zones.** `LedgerSiteEvidence` keeps an `EXTRA_EAT_ZONES` override (Asmara, Djibouti, Mogadishu → "EAT") because canonical `sites/siteTime.ts` must stay identical to W2-EV 3c533f0f; Finding pages via `siteTime.ts` would show "GMT+3" for those zones. Confirm the plan: W2-EV folds the three zones into the canonical table on its rebase and deletes the override.

Write numbered rulings to `.agent/post-W6-W1-a-closeout-rulings.md`. Do not edit product code or `.gitignore`.
