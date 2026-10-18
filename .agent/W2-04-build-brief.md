# W2-04 build - cold Site, evidence and money screens (implementer brief)

Worktree `C:/Users/assef/Bineyame/AssetOpsV1-review2`, branch `task/W2-04-cold-site-evidence-money` (from main with W2-00..W2-02 merged).

Binding (make NO design choice; if genuinely unspecified, stop at a clean commit with exact questions): `.agent/W2-04-build-spec.md` (executable contract incl. its "Readiness gate" section; follow its commit order), packet `tasks/W2-04-cold-site-evidence-money.md`, `D-2026-10-18-w2-04-buildspec`, `D-2026-10-18-w2-03-answers` (window-end freshness; fuel trigger mini-grid-only, cold money owned here in 0023), `D-2026-10-18-w2-mockup-authority` (W2 mock screens binding). W2-00..W2-03 are merged.

Builder runs: one spec commit per run, each ending with a phase handoff `.agent/W2-04-phase-handoff.md` naming exact remaining steps.

UI phase rules (upfront, mandatory): mock is the layout spec (`D-2026-10-17-mockup-layout-spec`, `.agent/architect-W1-fidelity.md`); `expectV69Panels` for every route W2-04 owns (per the spec's panel maps) (stocked/empty/refused) + planted-panel failure; 1440/390 side-by-side captures with `tools/w1-fidelity-evidence.mjs`; self-check before review: state line said once (status strip only); one disclosure per panel; no leftover labels/h3s; no raw IDs/enums/backend text; no contradictions; every mock row/column/chip present (unknowns "Not assessed"/"Not recorded"); mock tables/lists kept; never hide a material limit; no tall wrapped rows at 390; each panel <= ~1.3x mock height at 1440 or a stated honest reason (app-vs-mock height table in the packet).

Environment: worktree `.venv`; PYTHONPATH `<wt>;<wt>\backend;<wt>\contracts;<wt>\gateway;<wt>\simulator;<wt>\host` (Git Bash: `C:/...` paths separated by `;`); `ASSETOPS_GUARD_PYTHON` = `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`; Docker Postgres 127.0.0.1:55432 with private `*_test` DBs (create/drop); focused tests serially; ONE full backend suite + host suite at the final revision with no other pytest running (copy `var/sites` from `C:\Users\assef\Bineyame\AssetOpsV1\var\sites`, remove afterwards; 75-min cap); full `npm.cmd test`; `tools/check-all.ps1 -Python <that venv>` via `powershell -ExecutionPolicy Bypass -File`; rule-8 probes; `npx.cmd`/`npm.cmd` via PowerShell.

Packet `.agent/W2-04-review-packet.md` (git add -f). Commit; do not merge. Token-efficient (read only what the spec names); if near your context limit, stop at a clean commit with a phase handoff naming exact remaining steps.
