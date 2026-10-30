OUT-A A6 captures (capture-only; no product code changed). Brief: .agent/OUT-A-capture-brief.md.
Spec: AssetOpsV1-plan2/.agent/build-spec-outcome-sprint-2026-10-29.md §A.7 items 2-7, 10.

Product SHA: runs 1-3 at a1733184; runs 4-6 at 8b4c52dc (main merge brought tooling only; product code identical).
Python: AssetOpsV1-outA/.venv, PYTHONPATH per tasks/OUT-A-category-labels.md; assetops_backend resolved to
  C:\Users\assef\Bineyame\AssetOpsV1-outA\backend\assetops_backend\__init__.py
Capture: tools/capture-outa.mjs (headless Chrome over CDP 9611, 1440x1000 and 390x900, full page; app + v70 mock).
  Evidence: shots/raw-evidence.json (`runs` array, one per targets file); logs/capture-*.log.

Producers, DBs, ports
- Runs 1-3: tools/s602b_verification_walkthrough.py + s602b_test_scoped_cases.py, work var/s602b_outa.
  DBs assetops_s602b_outa_audit (replay, API 8966, Vite 5466) and assetops_s602b_outa_audit_{target_miss,guardrail,
  inconclusive,withdrawn,estate} (case API 8967, Vite 5467).
- Runs 4-5: tools/w502_cold_work_walkthrough.py --work var/w502b_outa --tag outa, prepare --modes positive.
  DB w502b_positive_outa_test. APIs positive 8971 (pid 21452), forbidden 8976 (pid 9500), unavailable 8977 (pid 25208).
  Vite 5471 (pid 900, ASSETOPS_API_PORT=8971). Chrome pids 19064, 26200.
- Run 6: tools/w504_ev_work_walkthrough.py --work var/w504a_outa --tag outa (prepare has no mode filter: positive,
  zero, worstcase ready; unknown unavailable). DBs w504a_{positive,zero,worstcase,unknown}_outa_test.
  APIs positive 8981 (pid 21424), zero 8982 (15356), worstcase 8983 (22652), forbidden 8986 (17868),
  unavailable 8987 (11436). Vite 5481 (pid 30604, ASSETOPS_API_PORT=8981). Chrome pid 18744.

Cleanup (logs/*-drop.log): w502 drop and w504 drop stopped every recorded API PID and dropped their DBs; Vite 900 and
30604 stopped with Stop-Process -Id; Chrome is killed by capture-outa.mjs (child PID). s602b drop
(--db assetops_s602b_outa_audit --work var/s602b_outa) dropped all six assetops_s602b_outa_audit* DBs. Afterwards:
0 matching DBs in assetopsv1-postgres-1, no listener on 5466/5467/5471/5481/9611/89xx, var/ work folders removed.

Windows used
- GreenHarvest COLD-LAB-001: list 2026-10-29T16:00Z..17:05Z (the w501 assessed window). Run 4's list capture used the
  2-day work window and rendered "No cold assessment for this window" (no rows); its PNGs were deleted, run 5 supersedes.
  Finding page: finding cefe3a64-... revision b20fa037-... (COLD_START_FAILURE).
- Depot EV-LAB-001: evidence window E 2026-10-06T08:00Z..09:00Z; finding a6d14b5a-... revision 8b54a9bc-...

Per-capture table (from shots/raw-evidence.json). 1440 scrollWidth 1425 = vertical scrollbar, not overflow.
No page-level horizontal overflow at 390 anywhere.
| run | name | width | ready | scrollWidth/clientWidth | console | category check |
|---|---|---|---|---|---|---|
| 1 | portfolio-estate | 1440 | False | 1425/1425 | 1 | PASS cards ['GROW_REVENUE', 'OPTIMIZE_COST', 'PROTECT_ASSET', 'ASSURE_PERFORMANCE'] Grow='Not available yet' Optimize='No supported value' (operating-cost equality not checkable: no operating-cost value exists in this case); mini row: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 1 | portfolio-estate | 390 | True | 390/390 | 0 | PASS cards ['GROW_REVENUE', 'OPTIMIZE_COST', 'PROTECT_ASSET', 'ASSURE_PERFORMANCE'] Grow='Not available yet' Optimize='No supported value' (operating-cost equality not checkable: no operating-cost value exists in this case); mini row: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 1 | findings-estate-case | 1440 | True | 1440/1440 | 0 | PASS Generator support candidate unconfirmed by th: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 1 | findings-estate-case | 390 | True | 390/390 | 0 | PASS Generator support candidate unconfirmed by th: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 1 | findings-kobo-replay | 1440 | True | 1440/1440 | 1 | PASS Generator support merits review: bounded cand: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 1 | findings-kobo-replay | 390 | True | 390/390 | 0 | PASS Generator support merits review: bounded cand: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 1 | sitefindings-kobo-replay | 1440 | True | 1440/1440 | 1 | N/A no Finding rows rendered |
| 1 | sitefindings-kobo-replay | 390 | True | 390/390 | 1 | N/A no Finding rows rendered |
| 2 | portfolio-estate | 1440 | True | 1425/1425 | 1 | PASS cards ['GROW_REVENUE', 'OPTIMIZE_COST', 'PROTECT_ASSET', 'ASSURE_PERFORMANCE'] Grow='Not available yet' Optimize='No supported value' (operating-cost equality not checkable: no operating-cost value exists in this case); mini row: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 2 | portfolio-estate | 390 | True | 390/390 | 0 | PASS cards ['GROW_REVENUE', 'OPTIMIZE_COST', 'PROTECT_ASSET', 'ASSURE_PERFORMANCE'] Grow='Not available yet' Optimize='No supported value' (operating-cost equality not checkable: no operating-cost value exists in this case); mini row: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 2 | sitefindings-kobo-estate-case | 1440 | True | 1440/1440 | 0 | PASS Generator support review: not confirmed · Ve: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 2 | sitefindings-kobo-estate-case | 390 | True | 390/390 | 0 | PASS Generator support review: not confirmed · Ve: solid "Optimize cost and efficiency" + outlined "Protect asset and capital" |
| 3 | act048-overview-guardrail | 1440 | True | 1440/1440 | 1 | PASS Affects lines=1; Affects Optimize cost and efficiency supply cost per kWh Safeguards checked Protect asset and capital reliable service, battery and generator life |
| 3 | act048-overview-guardrail | 390 | True | 390/390 | 0 | PASS Affects lines=1; Affects Optimize cost and efficiency supply cost per kWh Safeguards checked Protect asset and capital reliable service, battery and generator life |
| 3 | act048-verification-guardrail | 1440 | True | 1425/1425 | 0 | PASS Affects lines=1; Affects Optimize cost and efficiency supply cost per kWh Safeguards checked Protect asset and capital reliable service, battery and generator life |
| 3 | act048-verification-guardrail | 390 | True | 390/390 | 0 | PASS Affects lines=1; Affects Optimize cost and efficiency supply cost per kWh Safeguards checked Protect asset and capital reliable service, battery and generator life |
| 4 | sitefindings-greenharvest-w502 | 1440 | True | 1440/1440 | 1 | N/A no Finding rows rendered |
| 4 | sitefindings-greenharvest-w502 | 390 | True | 390/390 | 0 | N/A no Finding rows rendered |
| 4 | finding-greenharvest-startfailure-w502 | 1440 | True | 1440/1440 | 0 | PASS Affects lines=1: solid "Protect asset and capital cooling continuity, stock kept saleable" + outlined "Protect asset and capital compressor life" + outlined "Optimize cost and efficiency cost per cooling unit" |
| 4 | finding-greenharvest-startfailure-w502 | 390 | True | 390/390 | 0 | PASS Affects lines=1: solid "Protect asset and capital cooling continuity, stock kept saleable" + outlined "Protect asset and capital compressor life" + outlined "Optimize cost and efficiency cost per cooling unit" |
| 5 | sitefindings-greenharvest-w502-assessed | 1440 | True | 1440/1440 | 1 | PASS Backup generator did not start when the grid : solid "Protect asset and capital" + outlined "Optimize cost and efficiency"; Cold room temperature outside its policy band: solid "Protect asset and capital" |
| 5 | sitefindings-greenharvest-w502-assessed | 390 | True | 390/390 | 0 | PASS Backup generator did not start when the grid : solid "Protect asset and capital" + outlined "Optimize cost and efficiency"; Cold room temperature outside its policy band: solid "Protect asset and capital" |
| 6 | sitefindings-depot-w504 | 1440 | True | 1440/1440 | 1 | PASS Observed EV charging interruption: solid "Protect asset and capital" + solid "Grow revenue" |
| 6 | sitefindings-depot-w504 | 390 | True | 390/390 | 0 | PASS Observed EV charging interruption: solid "Protect asset and capital" + solid "Grow revenue" |
| 6 | finding-depot-interruption-w504 | 1440 | True | 1425/1425 | 0 | PASS Affects lines=1: solid "Protect asset and capital buses ready for service" + solid "Grow revenue charger use" + outlined "Protect asset and capital charger life" |
| 6 | finding-depot-interruption-w504 | 390 | True | 390/390 | 0 | PASS Affects lines=1: solid "Protect asset and capital buses ready for service" + solid "Grow revenue charger use" + outlined "Protect asset and capital charger life" |

Superseded rows: run 1 portfolio-estate (1440 ready=False; recaptured in run 2, same PNG names overwritten);
run 4 sitefindings-greenharvest-w502 (wrong window; see above). run 1 sitefindings-kobo-replay rendered no rows
(finding-index 409 on the replay DB); the Kobo Site Findings category evidence is run 2 sitefindings-kobo-estate-case.

Console messages (all are Chrome resource-load logs, no JS errors/exceptions):
run 1 portfolio-estate 1440: [log] Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:5467/favicon.ico
run 1 findings-kobo-replay 1440: [log] Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:5466/favicon.ico
run 1 sitefindings-kobo-replay 1440: [log] Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:5466/api/sites/KOBO-001/finding-index?domain=mini-grid-dispatch&from=2026-10-13T00%3A00%3A00Z&to=2026-10-14T00%3A00%3A00Z
run 1 sitefindings-kobo-replay 390: [log] Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:5466/api/sites/KOBO-001/finding-index?domain=mini-grid-dispatch&from=2026-10-13T00%3A00%3A00Z&to=2026-10-14T00%3A00%3A00Z
run 2 portfolio-estate 1440: [log] Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:5467/favicon.ico
run 3 act048-overview-guardrail 1440: [log] Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:5467/favicon.ico
run 4 sitefindings-greenharvest-w502 1440: [log] Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:5471/favicon.ico
run 5 sitefindings-greenharvest-w502-assessed 1440: [log] Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:5471/favicon.ico
run 6 sitefindings-depot-w504 1440: [log] Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:5481/favicon.ico

Judgement against §A.7
- #2 estate mini rows: PASS (solid Optimize + outlined Protect on Portfolio, estate Findings, Kobo Site Findings).
- #3 GreenHarvest: PASS. Start-failure row solid "Protect asset and capital" + outlined "Optimize cost and efficiency";
  excursion row only solid "Protect asset and capital".
- #4 Depot interruption row: PASS. Solid "Protect asset and capital" + solid "Grow revenue", no outlined pill.
- #5 Cold and EV Finding overview: PASS, exactly one .oc-affectsline each. Observation (no criterion covers it): the
  line also carries outlined "Also check" pills: cold start-failure adds outlined "Protect asset and capital /
  compressor life"; Depot interruption adds outlined "Protect asset and capital / charger life".
- #6 ACT-048 overview + verification: PASS ("Safeguards checked ... reliable service, battery and generator life").
- #7 Portfolio: four cards in order Grow, Optimize, Protect, Assure; Grow "Not available yet". Optimize shows
  "No supported value" ("No selected operating-cost consequence"); equality with an operating-cost card value is not
  checkable in this case (no operating-cost value exists), not FAIL.
- #10: captures at 1440 and 390, no 390 page overflow: PASS.
