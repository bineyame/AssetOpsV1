# W1-F5a build - Health, Asset, page titles, 390 rail (implementer brief)

Worktree `C:/Users/assef/Bineyame/AssetOpsV1-review5`, branch `task/W1-F5a-health-shell` (from main with F1 + F2 merged). Frontend only.

Scope (F5 row of `.agent/architect-W1-fidelity.md` + carries 1 and 5 of `.agent/W1-F5-carries.md`):
- v69 screens `health` and `asset`: rebuild to the mock's panels/order/titles/prominence (`frontend/docs/architecture/v69-rendered-panels.json`, `frontend/src/test/v69PanelTitles.ts`); separate source contact from condition; physical battery condition/capacity test and RUL read are missing - state them honestly "not available yet" in mock form.
- Carry 1: per-screen page titles/headers per the mock on all W1 Site screens (use F1's `SitePageHeader` / `SITE_SCREEN_DESCRIPTIONS`); keep wording plain.
- Carry 5: at 390 px the left rail must collapse like the mock (not stack ~600 px above content).
Out of scope (F5b, after F3/F4 merge): tab/subtab rows, lens chips, all-26 audit.

Binding: owner verdict `.agent/owner-W1-walkthrough-verdict-2026-10-17.md`; contract `.agent/architect-W1-fidelity.md`; F1 API `.agent/W1-F1-handoff.md`. Pre-review self-check (recurring review defects): state line said once (status strip only); one disclosure per panel; no leftover answer-card labels/h3s; no raw IDs/enums/backend text; no contradictions; every mock row/column/chip present (unknowns "Not assessed"/"Not recorded"); mock tables/lists kept; never hide a material limit; no tall wrapped rows at 390; each panel <= ~1.3x mock height at 1440 (app-vs-mock height table in packet).

Proof: `expectV69Panels` for `health`/`asset` (stocked/empty/refused) with a planted-panel failure; `npx.cmd tsc --noEmit`; full `npm.cmd test` once (known flakes siteFoundationChange, siteFinancials S4-08, s404SiteFindingIndex - rerun alone); `tools/check-all.ps1`; side-by-side 1440/390 captures with `tools/w1-fidelity-evidence.mjs` on free ports in 9600-9620/6000-6020 (drop fixtures, stop servers). Packet `.agent/W1-F5a-review-packet.md` (git add -f). Commit; do not merge. Never weaken an assertion. Token-efficient; if near context limit, stop at a clean commit with a handoff.
