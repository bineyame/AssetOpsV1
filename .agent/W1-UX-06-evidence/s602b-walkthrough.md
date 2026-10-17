# Walkthrough: Action Plan, Evidence and Verification (`s602b_verification_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432. Nothing else: `prepare` builds its own code copy and data.

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s602b_w1ux06","--work","var/s602b_w1ux06"
.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py @T links --web-port 5570
.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py @T serve --port 9070 --web-port 5570 --case guardrail
```
`prepare` takes about 5 minutes and ends with "Prepared. Next: serve, then capture." It makes five databases (the replay plus one per test case). To see another test case, Ctrl+C `serve` and start it again with `--case target_miss`, `--case inconclusive` or `--case withdrawn`; the two web windows keep running.
Second window (the replay, a real Lab run):
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9070"; npm.cmd run dev -- --port 5570 --strictPort
```
Third window (the test cases):
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9071"; npm.cmd run dev -- --port 5571 --strictPort
```

## 3. Ports and addresses
API 9070 and 9071, web 5570 (replay) and 5571 (test case). Mock: `http://localhost:5570/mockups/v69/index.html#/<id>`. IDs are from the final run's `links`; a fresh `prepare` prints new ones. Plan and Evidence addresses for the test cases are not printed: open the printed Verification address and click the "Plan" or the second "Evidence" tab (the Action's tab row, not the Site menu).

| Screen and state | Address | Mock |
| --- | --- | --- |
| Plan, sampled pass (current / exact) | http://localhost:5570/sites/KOBO-001/actions/f89ba10f-aecf-4213-a6eb-b6fb3f554783/plan , ...plan?plan_revision_id=10b2966b-80c3-4af3-ba45-84cc0faf3114 | `#/action-plan` |
| Evidence, sampled pass | http://localhost:5570/sites/KOBO-001/actions/f89ba10f-aecf-4213-a6eb-b6fb3f554783/evidence | `#/action-evidence` |
| Verification, sampled pass (current / exact outcome) | http://localhost:5570/sites/KOBO-001/actions/f89ba10f-aecf-4213-a6eb-b6fb3f554783/verification , ...verification?outcome_id=34ca961a-069f-405b-8e91-56608edbf9b7 | `#/verification` |
| Guardrail fail (`--case guardrail`) | http://localhost:5571/sites/KOBO-001/actions/93ebef0d-48b9-43ff-8d06-b9ba718b4d2b/verification (+ /plan, /evidence by click) | `#/verification` |
| Withdrawn (`--case withdrawn`) | http://localhost:5571/sites/KOBO-001/actions/38da3f33-8441-454a-bcd0-c2af0981d28c/verification (+ /plan, /evidence by click); hold: http://localhost:5571/sites/KOBO-001/findings/9897b026-68da-432c-880b-81ad1968d83c/recommendation?revision_id=9c825cb0-002a-4fdb-bba8-55e9351f0b28 | `#/verification`, `#/recommendation` |
| Target not met (`--case target_miss`) | http://localhost:5571/sites/KOBO-001/actions/3095d875-6c62-4283-80f6-f3c16a655cfd/verification (+ /plan, /evidence by click) | `#/verification` |
| Could not conclude (`--case inconclusive`) | http://localhost:5571/sites/KOBO-001/actions/da220af2-0504-49bd-920f-c2b989c48e8e/verification (+ /plan, /evidence by click) | `#/verification` |

## 4. What to look for
- Plan (all cases): "Plan fixed before the later readings" with its date, while "How this was worked out" is closed.
- Evidence: sampled pass, guardrail and target miss say "Both windows have their readings"; withdrawn says "Some readings are missing".
- Verification: sampled pass "Target met within the sampled limits"; exact outcome "Earlier version, kept for the record"; guardrail "Trial missed a safety or service limit"; target miss "Target not met"; withdrawn and inconclusive "Could not conclude".
- Withdrawn hold: the recommendation says "Held: late evidence withdrew an earlier trial's result" (no small picture).
- Inconclusive Evidence says "Some readings are missing" (the earlier blank page was fixed in `2d03f626`).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same state. Reload: same state.

## 5. Data label
Sampled pass: simulated readings from two real Lab runs, replayed. The four other cases are authored test examples, not Lab runs. None are field readings.

## 6. Stop and clean up
Ctrl+C in all three windows, then:
```
.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py @T drop
```

## 7. Captured in final run (code `01bdfd9c`)
| Screen | Case | 1440 | 390 | App vs mock / notes |
| --- | --- | --- | --- | --- |
| action-plan | pass, pass exact, guardrail, withdrawn, target_miss, inconclusive | pass | pass | test-case Plan reached by click |
| action-evidence | pass, guardrail, withdrawn, target_miss | pass | pass | |
| action-evidence | inconclusive | rerun at `2d03f626`: pass ("Some readings are missing") | pass (same) | superseded: the `01bdfd9c` run failed 2 + 2 (page crashed: "Objects are not valid as a React child (found: object with keys {code, accepted_evidence_ids})" in `Ref` under `WindowPanel` > `DigDeeper`, `SiteActionVerification.tsx`); fixed by `2d03f626` |
| verification | pass, pass historical, guardrail, withdrawn, target_miss, inconclusive | pass | pass | inconclusive Plan and Verification also re-passed in the `2d03f626` rerun |
| recommendation | withdrawn hold | 1 FAIL: no small visual | 1 FAIL (same) | held state draws no picture |

`w1-ux-01` totals: replay + guardrail 140/140, withdrawn 78/80, target_miss 60/60, inconclusive 42/46 (files `s602b-w1-ux-01-*.txt`), 320/326 overall at `01bdfd9c`. Inconclusive rerun at `2d03f626` (fresh `prepare`, `serve --case inconclusive`, Action `50c7912f-20b2-4786-9c18-aa6b245497c7`): 60/60 (30/30 at 1440, 30/30 at 390; `s602b-w1-ux-01-inconclusive-rerun.txt`), superseding the 42/46; overall with the rerun 338/340. Tool's own `capture` (`s602b-verification-evidence.mjs`, replay and every case): 120/120 (`s602b-capture.txt`). Screenshots: `%TEMP%\w1ux06-final\s602b` (not in git).
