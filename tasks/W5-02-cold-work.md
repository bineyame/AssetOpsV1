# W5-02 Cold Work and intervention

Status: planned; build instructions in [`.agent/W5-02-build-spec.md`](../.agent/W5-02-build-spec.md). Architect decision `D-2026-10-22-w5-02-w5-04-buildspec`.

## Order and ownership

After reviewed and merged W5-01b (`0032`) **and** W6-01b (B1), deliver the v6.9 `cold-work`, `cold-work-incidents`, `cold-work-maintenance`, and `cold-action` screens in four independently reviewed merges. W5-02a-core (K1a, K1b, K1c) creates persisted cold Action, immutable success intent, selected W4/W6 links and the ordinary cold fixture producer at `0033_w5_cold_work`, whose parent is exactly `0032_w5_cold_scenarios`. W5-02a-site (K2a, K2b) delivers the Action Site tab and its captures after core merges. The expanded pre-flight makes these five backend and three Site builder runs; the named subunits and P-ID closure table are in the build spec. W5-02b (K3a, K3b) delivers the Incident and Maintenance tabs after W6-01 A2/B2 shared notice and guard edits merge. W5-02c (K4a, K4b, K5) delivers the Action verification screen and closeout. Reviews precede dependent units. W5-02c must merge before W5-03a; W5-03b uses `0033_w5_cold_work` as its exact parent.

The shared Incident/Maintenance identities and list APIs and two Site pages already exist in `backend/assetops_backend/work/{model.py,site_index.py,detail.py}`, `backend/assetops_backend/work_api.py`, `frontend/src/sites/{siteWorkCases.tsx,workClient.ts}`, and `frontend/src/shell/operatorSiteRoutes.ts` (W4-01). W1's battery-specific Site Action list and Action UI root already exist in `frontend/src/sites/{SiteWorkActions.tsx,SiteAction.tsx}` and `frontend/src/shell/SiteAnalyticsFrames.tsx`. W6-01 owns global Incident/Maintenance/request routes and the rail; this slice only links to them when merged. The cold route adds domain data and presentation, not a second Incident or Maintenance identity. The named `incident`, `workverification`, `cold-findings` and `cold-recommendation` screens stay with their W4/W6/W2/W5-01 owners; this task may link to them but does not claim their panels.

## Observable acceptance

- A scoped, persisted cold Action links the selected F-118 revision, an operator-attested INC case and WR request. The completed WR inspection remains **Unverified**. A W2 cold failure observation does not itself create an Incident, a maintenance record, or a successful Action.
- The three Site Work tabs use the union Site Action and W4 case rows at the same selected Site/window/cutoff, show counts from the full selected set, and preserve selected links. Empty means a successful complete zero; denial, changed cursor, stale linked evidence and store failure remain distinct.
- `cold-action` shows four immutable declared criteria, source Finding and related WR activity. No observed automatic-start outcome or cooling restoration is asserted without later accepted evidence under the declared conditions. The current capture says `Not tested`, `Not tested`, `Not established`, `Pending`.
- Desktop 1440 and narrow 390 captures cover positive, zero, pending/stale link, historical and refusal, with producer and clock in the build spec. Each page unit owns its captures. No private Lab truth, hard-coded mock IDs, or status from a mock row enters product state.

## Gates

Per-unit independent review; one same-revision real-Postgres full suite for the schema/shared-plumbing core merge under `.ai/ROLE_CONFIG.md` tiered testing; scoped backend regression, full frontend vitest and `tools/check-all.ps1` at each merge. Full suites run on a quiet machine. Owner wave-start and final visible acceptance remain per `.ai/ROLE_CONFIG.md`. The build spec's independent readiness dry-read must close against merged W5-01b/W6-01b before K1a; readiness item 29 must pass its named K1c producer test before K2a. Builders stop capture processes and drop their private `*_test` DBs.
