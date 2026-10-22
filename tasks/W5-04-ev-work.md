# W5-04 EV Work and intervention

Status: planned; build instructions in [`.agent/W5-04-build-spec.md`](../.agent/W5-04-build-spec.md). Architect decision `D-2026-10-22-w5-02-w5-04-buildspec`.

## Order and ownership

After reviewed and merged W5-03b, deliver v6.9 `ev-work`, `ev-work-incidents`, `ev-work-maintenance`, and `ev-action` in three independently reviewed merges. W5-04a (V1–V2) extends the domain Action root and immutable intent to EV, adds the Action Site tab, and publishes `0035_w5_ev_work` with exactly `0034_w5_ev_scenarios` as parent. W5-04b (V3) delivers the Incident and Maintenance tabs. W5-04c (V4–V5) delivers the EV Action verification screen and closeout. W5-02's `0033_w5_cold_work` is the preceding work contract; W5-03b's `0034` is the immediate migration parent.

W4-01's merged `backend/assetops_backend/work/`, `work_api.py`, `frontend/src/sites/siteWorkCases.tsx` and `workClient.ts` own Incident/Maintenance identities and list projection. W1's `SiteWorkActions.tsx`, `SiteAction.tsx` and `SiteAnalyticsFrames.tsx` supply the Action UI and route; its persisted battery trial identity cannot hold an EV Action. W5-02 adds the domain Action root and exact W4 case-link relation. W6-01 owns global Work roots, navigation and request detail. W5-04 adds EV-specific persisted intent and honest EV Work presentation. `ev-findings`, `ev-recommendation`, and the `sessions` performance page retain their W2/W5-03 ownership; links are selected, not reimplemented here.

## Observable acceptance

- The Site Action is rooted in a persisted, selected EV Finding and names a diagnostic review/witnessed session criterion. The W2 fault-ended SES-011 and incomplete SES-012 remain observations; neither automatically opens an Incident, Maintenance request, or verification success.
- EV Incidents and Maintenance show the mock's complete zero states only when the W4 lists return successful zeros. A real submitted case appears with the same W4 identity and state. A global manage link is live only when its W6-01 root exists; no create flow is claimed.
- `ev-action` shows the three immutable plan criteria with `Pending` current results. A reset, investigation, completed session or configured schedule alone does not establish no recurrence or preserved availability. Missing connector status remains Unknown.
- Captures at 1440/390 cover positive Action, zero cases, an explicitly submitted case, pending/stale link, historical and refusal from named producers and one pinned clock. No mock SES/ACT/INC identifier is stored as evidence by display coincidence.

## Gates

Independent review of each unit, one real-Postgres full suite per sub-slice, `tools/check-all.ps1` after route/registry changes, and the readiness/owner gates in `.ai/ROLE_CONFIG.md`. Stop capture processes and drop private `*_test` DBs. The attached spec leaves no design choice to the implementer.
