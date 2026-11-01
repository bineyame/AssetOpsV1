# POLISH-PC fix round handoff (whole-diff review REVISE)

Review: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\review-POLISH-whole-diff.md` (M1-M3, L1-L5, item 8).
Worktree `C:\Users\assef\Bineyame\AssetOpsV1-polC`, branch `task/POLISH-PC-final-gate`, head `84a2914ab`. Not merged.

## Coordinator instruction (verbatim)

Do one final fix round in the polC worktree. Each wording change below follows rulings already made, so they need no
new ruling. List every change old→new in the packet.

Frontend:
- M1. Make `ExactReferences` (`ui/ProductStatus.tsx:190-213`) render its id rows inside Technical details. Either tag it
  `data-technical-details` with the summary "Technical details", or route through `WorkedOut`/`TechnicalReferences`. All 18
  Site callers must then keep ids, codes and raw timestamps only inside a tagged region. Spot-check `SiteFinding`,
  `SiteFindingHistory`, `SiteAction` (:648-654, :896, :1093) and `SiteRecommendation`. Correct R656's wording.
- M3. Change `verificationWords.ts:213` to "Example data" and `:215` to "Prepared example data". Make the Verification
  footnote say "example data" so the page uses one term. Update the pins. Also widen the strict lab-name rule so that
  "Lab trial data" counts.
- L1, frontend part. Use lower-case "finding" in running text on the demo path: the "Open the Finding →" link on the Kobo
  board, the Portfolio panel subtitle "Selected Findings across accessible Sites", and the strings in `findingWords.ts`,
  `SiteFinding.tsx` and `actionPresentation.tsx` that render as prose. Headings and titles may stay title-case.
- L3. In `estateEvidenceWords.ts:16` and `estateFinancialsWords.ts:19`, replace "Potential product exposure" with the cold
  wording "Stock may be at risk". Make the Portfolio "Not established" consistent with "Not known yet".

Backend copy constants:
- L1, server part. In `placement.py:25,39,62`, change "Finding" to "finding" and "Findings" to "findings".
- L2. In `site_outcomes/ev.py:45`, change "Gross tariff estimate not available yet" to "Charging income estimate not
  available yet". In `ev_site_reads.py:31,37,42`, change "gross tariff estimate/scenario" to "charging income estimate"
  wording. Update the pins.

Tools and records:
- L4. Add a `-\d{6,}` stored-code rule in `tools/demo-combined-vocabulary.mjs`.
- L5. Align the stale fixtures: `estatePortfolio.test.tsx:853`, `portfolioFixtures.ts:144` and
  `tools/s405-provenance-evidence.mjs:36`.
- M2. Rewrite R625, R628, R631 and R634 so they describe what the product shows now, or close them if they no longer
  apply. Fix R08's status cell. Re-verify every R625–R662 row's text against the final captures, not only the ids and statuses.

Item 8 (cold start). Make `demo_combined.py serve` pre-warm the estate. After the first tick, it requests the Portfolio
outcome-summary for the story week once, and prints a "ready:" line only when that request returns. Update the runbook so
the presenter waits for "ready:" and never restarts serve once the client has joined. Add a pure or light test if you can.

Then, one at a time:
1. Scoped tests for every touched file, plus `tsc`.
2. Rebuild, because the server copy changed. The finish check must be 17/17.
3. Strict 28-capture run with 0 counted hits. Use the new pre-warm and confirm `portfolio-week` settles on the first run.
4. One full `npx vitest run`.
5. check-all (12).

A `-Tier all` isn't needed for copy-only backend changes. Do run the backend test files that pin these strings.
Memory is tight, so run each heavy job alone.

## How the previous rounds ran these (reuse)

- Python: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`. PYTHONPATH (Windows form, `;`):
  `<wt>\backend;<wt>\contracts;<wt>\tools;<wt>\simulator;<wt>\gateway;<wt>\host;<wt>\field` with `<wt>` = this worktree.
  From Git Bash use backslash Windows paths in PYTHONPATH or imports fail at collection.
- Pure pytest: `python -m pytest backend/tests/<files> -q -p no:cacheprovider`. Postgres pin tests:
  `powershell -NoProfile -File tools\run-host-tests.ps1 -- backend/tests/<file> -q -p no:cacheprovider`.
- Rebuild (owns its DB here; no drop needed): `& $py tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full prepare`
  (1000-1250 s, run in background, log to %TEMP%). Expect "self-check: 17 pass, 0 fail".
- Serve: same args with `serve` (API 8990); Vite from `frontend/`: `$env:ASSETOPS_API_PORT="8990"; npm.cmd run dev -- --port 5490 --strictPort`.
- Capture: `$env:DEMOB_STRICT="1"; $env:ASSETOPS_CDP_PORT="9493"; node tools/demo-combined-evidence.mjs capture <wt>\var\polish_full .agent\POLISH-PC-captures`
  (about 300-360 s; last line "vocabulary: 0 counted hit(s) …"; exit 1 on an unsettled capture or counted hit).
  Review mode: `DEMOB_REVIEW_LABELS=1 DEMOB_ONLY=wr-overview,kobo-board-S`, out `.agent\POLISH-PC-captures\review-mode`.
- Stop serve/Vite by PID with `taskkill /PID <pid> /T /F` (the serve python launcher and the npm process), check ports free.
- Vocabulary lists: `tools/demo-combined-vocabulary.mjs` `ID_KINDS` (line 14) and `WORD_KINDS` (line 24; Addendum 14
  added `test data wording`). Self-tests: `node --test tools/checks/test_mock_deviation_labels.mjs`. Prove each new rule
  fires (scan a sample string with a scratch .mjs importing `scan`, `WORD_KINDS`/`ID_KINDS`).
- check-all: `powershell -NoProfile -File tools\check-all.ps1 -Python <plan2 venv python>` (about 400 s).
- Packet: `.agent/POLISH-PC-packet.md` (add a "Whole-diff fix round" section with the old→new table and results);
  runbook `.agent/POLISH-runbook.md`; register `.agent/mock-departure-register.md` (commit `.agent` with `git add -f`).
  Read packet/register with `newline=""` in Python: a stray CR once came from `\r` in "tools\run-…".
- Commit messages end with "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Never write .py with
  PowerShell Set-Content. No `-ExecutionPolicy Bypass`. Test DBs only; never touch `assetops_demo3_full_test`.
