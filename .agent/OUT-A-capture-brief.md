# OUT-A A6 capture brief (capture-only; no product code changes)

Worktree `C:\Users\assef\Bineyame\AssetOpsV1-outA`, branch `task/OUT-A-category-labels`. Capture the product at the current HEAD. Do not edit anything under `frontend/src`, `backend/` or `host/`. Do not merge.

## What to capture (build spec `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md` §0.5, §A.1 A6 "Captures", §A.7 items 2-7 and 10)
Each at 1440x1000 and 390x900, full page, plus the matching v70 mock screen (`frontend/mockups/v70/`; fall back to v69 if a screen is missing in v70 and say so):
1. Portfolio (`/portfolio`, window of the case) on the s602b `estate` case (`tools/s602b_test_scoped_cases.py build|serve <database-url> <work> estate <port>`; see `:38`, `:51`). Mock: `portfolio`.
2. Kobo Findings (estate Findings list, `/findings` and the Site Findings list) from the s602b replay (`tools/s602b_verification_walkthrough.py ... prepare|serve`). Mock: `findings`, `sitefindings`.
3. GreenHarvest (`COLD-LAB-001`) Findings list and the start-failure Finding page, w502 `positive` (`tools/w502_cold_work_walkthrough.py prepare|serve|drop`). Mock: `sitefindings`, `finding`.
4. Depot (`EV-LAB-001`) Findings list and the interruption Finding page, w504 `positive` (`tools/w504_ev_work_walkthrough.py prepare|serve|drop`). Mock: `sitefindings`, `finding`.
5. ACT-048 Action overview and verification page on the s602b `guardrail` case. Mock: `verification`.

Earlier capture tooling to copy from: `tools/s602b-verification-evidence.mjs`, `tools/layout-evidence.mjs`, `tools/measure-mock-panels.mjs --mock <dir>`, and `.agent/post-W6-W2-cold-recapture/README.txt` (Vite port per API via `ASSETOPS_API_PORT`, Chrome via CDP).

## Per capture, record in `.agent/OUT-A-captures/summary.json` and a short `README.txt`
- URL, width, product SHA, producer/case/DB.
- Page-level horizontal overflow at 390 (`document.documentElement.scrollWidth > clientWidth`): must be false. Prove the measurement is non-empty (scrollWidth/clientWidth numbers recorded).
- Console errors count.
- Category evidence, counted from the DOM: pills per Findings row (solid vs outlined, text), number of Affects lines on each Finding page (`.oc-affectsline`), the "Safeguards checked" line on ACT-048 overview and verification, the four Portfolio cards in order with name, value, detail and basis (`[data-portfolio-card]`).
- Compare with spec §A.7: estate mini rows one solid "Optimize cost and efficiency" + one outlined "Protect asset and capital"; GreenHarvest start-failure solid Protect + outlined Optimize, excursion only solid Protect; Depot interruption solid "Grow revenue" + solid Protect, no outlined; Finding pages exactly one Affects line; Portfolio Grow value "Not available yet", Optimize value equal to the operating-cost card value. Mark each PASS/FAIL with the observed values.

## Rules (binding)
- Databases: only `*_test` databases, or producer scratch databases named `<prefix>_audit*` in container `assetopsv1-postgres-1`. `tools/s602b_test_scoped_cases.py` and `s602b_verification_walkthrough.py` must NOT target a `*_test` DB: name them `assetops_s602b_outa_audit` / `assetops_s602b_outa_audit_<case>`. Never touch any other database.
- Stop processes by PID only (record PIDs). Drop every DB you created and stop every server when done; say so in the README.
- Never use an execution-policy override; never run `tools/check-all.ps1`.
- Only one heavy job on the machine: no test suites while capturing.
- Screenshots go under `.agent/OUT-A-captures/` (force-add with `git add -f`); commit with a message ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- If a producer cannot produce a listed screen, record `not captured` with the exact blocking error; do not change product code to make it work.
- Keep context small: write logs to files, read only failures/summary lines.

## Return
Commit SHA, the capture table (screen, width, overflow, console, category checks PASS/FAIL), anything not captured with its error, and confirmation that DBs were dropped and servers stopped.
