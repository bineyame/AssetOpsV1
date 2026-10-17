# W2-02 build - cold-chain producer, Lab scenarios, gateway v4 (implementer brief)

Worktree `C:/Users/assef/Bineyame/AssetOpsV1-review2`, branch `task/W2-02-cold-producer` (from main with W2-00, W2-01 merged). Simulator + gateway + host + backend.

Binding (make NO design choice; if anything is unspecified, stop and report with exact questions): packet `tasks/W2-02-cold-producer.md` (incl. plan review notes), `.agent/W2-technical-design-cold.md` (W2-02 section, model laws/parameters, scenario forcing tables, the six demo cases, publication profile, host pack selection; §3 W2-01 answers and the W2-02 code pre-check), `D-2026-10-17-w2-design`, `-w2-techdesign-cold`, `-w2-00-answers`, `-w2-01-answers`, `-f5-subtabs-and-contact`. Design line numbers have drifted - find code by name.

Step 0 (W2-01 re-review Lows, `.agent/W2-01-rereview.md`; small, commit first):
1. API tests for the no-gateway-selected and no-gateway-registered branches (`backend/assetops_backend/cold_foundation_api.py:96-97`).
2. `frontend/src/sites/ColdFoundationViews.tsx:111`: drive the gateway/contact status from the backend contact limitations only; a failed health read gets its own title; correct the W2-01 packet note about COLD-002.
3. Recapture the three cold routes at 1440/390 (`tools/w1-fidelity-evidence.mjs`, free ports 9700-9720/6100-6120, separate fixture DB, drop afterwards) so no capture says "Never contacted".

Environment: `.venv` in the worktree; PYTHONPATH `<wt>;<wt>\backend;<wt>\contracts;<wt>\gateway;<wt>\simulator` (+ `<wt>\host` where needed); `ASSETOPS_GUARD_PYTHON` = `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`; Docker Postgres 127.0.0.1:55432 with private `*_test` DBs (create/drop); focused tests serially; ONE full backend suite + simulator + gateway + host suites at the final revision with no other pytest running (copy `var/sites` from `C:\Users\assef\Bineyame\AssetOpsV1\var\sites` and remove afterwards); `tools/check-all.ps1 -Python <that venv>`; `npx.cmd`/`npm.cmd` via PowerShell.

Proof: every packet acceptance test per phase, each demo case's produced evidence asserted through ordinary gateway v4 -> S2 acceptance, rule-8 probes where writers change, JUnit counts for every suite. Packet `.agent/W2-02-review-packet.md` (git add -f). Commit; do not merge. Token-efficient; if near your context limit, stop at a clean commit with a handoff.
