# Architect request: W5-cold-Work and W5-EV-Work pre-flight escalations

You are the AssetOps Architect. Two builders pre-flighted against main 14696fda, applying the UI guide (`frontend/docs/architecture/ui-ux-decision-guide.md`) for all minor choices: `.agent/post-W6-W5-cold-preflight.md` and `.agent/post-W6-W5-EV-preflight.md`. Each lists its planned guide-covered choices (no ruling needed unless you see a conflict) and escalation-only questions. Verify code claims as needed. Rule exactly on:

**W5-cold**
1. R338 reach and wording: `defaultWorkWindow` (`workClient.ts`) is shared by cold Work, EV Work and mini Site Work cases. Default: change the shared helper to the seven UTC days incl. today `[today−6d, tomorrow)` for all Site Work; show the filtering-basis note on the cold/EV Window control only: "Listed by the time each Action was raised." plus W6 Q7's Incidents/Maintenance lines; W5-EV aligns EV empty copy. Alternatives: cold-only default, or Site-local days for the mini form. (Note B15-06 cause: maintenance requests filtered by `created_at` while rows show `occurred_at`.)
2. Files outside the card list: `SiteAnalyticsFrames.tsx` and `SiteHealthFrames.tsx` (R338/R339/B15-04); W4 Q10 named the wrong file for B15-04 (it is `DomainActionShell` in `SiteAnalyticsFrames.tsx`, not `SiteWorkActions.tsx`). Default: W5-cold edits only those cold hunks after W2-cold and W4-mini merge; W5-EV follows.

**W5-EV**
3. Files outside the card list: approve `SiteAnalyticsFrames.tsx`, `SiteHealthFrames.tsx`, `EvAssessmentViews.tsx`, the two work presentation files, `tools/w504_ev_work_walkthrough.py` (one-line `details=` fix for the R373 EV case-detail 503) and the w504 backend test expectations. Default: approve, EV-only hunks.
4. R350 cold reach: the Action section dispatch is one shared branch for cold and EV. Default: fix both (W6 "This address is not served" pattern) and add cold link-check recaptures.
5. "Being refreshed" copy is backend-owned (`ev_site_reads.py:36`; shown on energy, EV Overview, EV Financials). Default: one-string backend change to "No stored gross tariff estimate matches the current evidence."

Coordinator allocation (no ruling needed): register blocks W5-cold R460–R469, W5-EV R470–R479. Order: both build after W2-cold and W4-mini merge; W5-cold before W5-EV in shared files.

Write numbered rulings to `.agent/post-W6-W5-rulings.md`. Do not edit product code or `.gitignore`.
