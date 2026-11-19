# OWN-GAPS: split map

`.agent/build-sheet-OWN-GAPS-2026-11-08.md` (524 KB, 5772 lines, sha256 `ac24bc280a343f12`) moved here on 2026-11-18 (declutter step 4) and was split by its own headings, verbatim and in order, into `spec.md` 59 KB, `rulings.md` 52 KB, `rulings-2.md` 57 KB, `rulings-3.md` 59 KB, `rulings-4.md` 57 KB, `rulings-5.md` 59 KB, `rulings-6.md` 57 KB, `rulings-7.md` 58 KB, `rulings-8.md` 56 KB, `rulings-9.md` 5 KB. Open the part a citation names; an old `file:line` citation maps through the table (old lines -> part lines). Proof: `python tools/declutter/split_specs.py --verify`.

| # | Old lines | Part | Part lines | Section |
| --- | --- | --- | --- | --- |
| 1 | 1-11 | `spec.md` | 1-11 | Build sheet OWN-GAPS (2026-11-08): Kisiwa add-day, automatic diesel... |
| 2 | 12-261 | `rulings.md` | 1-250 | Revision 2 — pre-flight rulings 2026-11-08 |
| 3 | 262-401 | `rulings.md` | 251-390 | Revision 1 — owner answers 2026-11-08 |
| 4 | 402-418 | `spec.md` | 12-28 | 1. Shared rules (all three items) |
| 5 | 419-670 | `spec.md` | 29-280 | 2. G2 — the automatic diesel-night check (product, scheduler) |
| 6 | 671-927 | `spec.md` | 281-537 | 3. G3 — saving operational records from the screen (product) |
| 7 | 928-1097 | `rulings.md` | 391-560 | 4. G1 — the owner's `add-dates` tool (demo tool) — Rev 1, replaces ... |
| 8 | 1098-1176 | `rulings.md` | 561-639 | 5. Sequencing ruling — SUPERSEDED by Revision 1 (R1.3); kept as his... |
| 9 | 1177-1197 | `rulings.md` | 640-660 | 6. Owner questions — ANSWERED 2026-11-08 (Revision 1, R1.1); kept a... |
| 10 | 1198-1292 | `rulings-2.md` | 1-95 | 7. Q7 audit (Rev 1): is any date, story or Site logic hard-coded in... |
| 11 | 1293-1799 | `rulings-2.md` | 96-602 | Revision 3 — G2 test rulings (2026-11-08) |
| 12 | 1800-1962 | `rulings-2.md` | 603-765 | R4 — DS-1a residual rulings (2026-11-09) |
| 13 | 1963-2160 | `rulings-3.md` | 1-198 | R5 — G1 rehearsal F-THREADS (2026-11-09) |
| 14 | 2161-2302 | `rulings-3.md` | 199-340 | R6 — G1 resume run: CO-2, WK-6 and the tree rebuild (2026-11-09) |
| 15 | 2303-2545 | `spec.md` | 538-780 | E2 fix-round scope (2026-11-09) |
| 16 | 2546-2752 | `rulings-3.md` | 341-547 | FR-A stop rulings (2026-11-09) |
| 17 | 2753-2796 | `rulings-3.md` | 548-591 | E3 stop rulings (2026-11-09) |
| 18 | 2797-2987 | `rulings-3.md` | 592-782 | E4 stop rulings (2026-11-09) |
| 19 | 2988-3090 | `rulings-4.md` | 1-103 | E4 L2 ruling (2026-11-09) |
| 20 | 3091-3211 | `rulings-4.md` | 104-224 | E3b stop ruling (2026-11-10) |
| 21 | 3212-3253 | `rulings-4.md` | 225-266 | Any-range speed ruling (2026-11-10) |
| 22 | 3254-3430 | `rulings-4.md` | 267-443 | E5 rulings (2026-11-10) |
| 23 | 3431-3458 | `rulings-4.md` | 444-471 | DS-1f anomaly rulings (2026-11-10) |
| 24 | 3459-3558 | `rulings-4.md` | 472-571 | Kobo gap-pattern ruling (2026-11-10) |
| 25 | 3559-3652 | `rulings-4.md` | 572-665 | Kobo days amendment (2026-11-10) |
| 26 | 3653-3673 | `rulings-5.md` | 1-21 | v3 fallback ruling (2026-11-10) |
| 27 | 3674-3727 | `rulings-5.md` | 22-75 | Money snapshot ruling (2026-11-10) |
| 28 | 3728-3783 | `rulings-5.md` | 76-131 | Portfolio lens ruling (2026-11-10) |
| 29 | 3784-3863 | `rulings-5.md` | 132-211 | Findings cards ruling (2026-11-10) |
| 30 | 3864-3926 | `rulings-5.md` | 212-274 | Non-Kobo Site pages ruling (2026-11-10) |
| 31 | 3927-3988 | `rulings-5.md` | 275-336 | D-E5.38 to D-E5.40: Portfolio coverage counts UTC days (CO-6, WK-GA... |
| 32 | 3989-4062 | `rulings-5.md` | 337-410 | D-E5.41 to D-E5.44: DATA-12 review rulings (Architect, Claude, 2026... |
| 33 | 4063-4103 | `rulings-5.md` | 411-451 | D-E5.46 Day-gap words state the data fact; "not analysed yet" only ... |
| 34 | 4104-4167 | `rulings-5.md` | 452-515 | D-E5.47 An infrastructure read failure is never stored and never sh... |
| 35 | 4168-4195 | `rulings-5.md` | 516-543 | D-ANY.5 ANY-1 Phase 1 review M1/M2: period-row knowledge time is tr... |
| 36 | 4196-4239 | `rulings-5.md` | 544-587 | D-E5.48 DATA-11 Cold epochs and the EV depot's sparse look (Archite... |
| 37 | 4240-4258 | `rulings-5.md` | 588-606 | D-E5.49 EV fault day over the full recorded day: c1 stays out of se... |
| 38 | 4259-4322 | `rulings-5.md` | 607-670 | D-ANY.6 Tonight's speed build for the Thursday 12 Nov technical dem... |
| 39 | 4323-4342 | `rulings-6.md` | 1-20 | D-PRICE.1 Prices typed on screen are saved as "Entered by site admi... |
| 40 | 4343-4381 | `rulings-6.md` | 21-59 | D-OPEN.1, D-ANY.7, D-HON.1, D-F05.1 Batched rulings (Architect, Cla... |
| 41 | 4382-4400 | `rulings-6.md` | 60-78 | D-ANY.8 Order of the remaining any-range speed work for 17 Nov (Arc... |
| 42 | 4401-4412 | `rulings-6.md` | 79-90 | D-ANY.9 AR-4: Portfolio consequence money, receipt-less productive ... |
| 43 | 4413-4423 | `rulings-6.md` | 91-101 | D-PRICE.2 PR-3 server half: Site name in the first-price summary, d... |
| 44 | 4424-4443 | `rulings-6.md` | 102-121 | D-ANY.10 AR-4 client4 evidence: the `before_build` mismatch and the... |
| 45 | 4444-4457 | `rulings-6.md` | 122-135 | D-PRICE.3 PR-2a price page: old addresses, EV subtabs, rows per Sit... |
| 46 | 4458-4492 | `rulings-6.md` | 136-170 | D-17N.1-7 The owner's 17 Nov expectations: 2 s, modern UI, performa... |
| 47 | 4493-4510 | `rulings-6.md` | 171-188 | D-ANY.11 DISP-1: the remaining dispatch-day lookups are Finding mon... |
| 48 | 4511-4588 | `rulings-6.md` | 189-266 | D-UP.1-11 UP-1 pre-flight questions Q1-Q9 and the guard fix (Archit... |
| 49 | 4589-4635 | `rulings-6.md` | 267-313 | D-WARM.1-6 WARM-1 packet questions (Architect, Claude, 2026-11-12, ... |
| 50 | 4636-4648 | `rulings-6.md` | 314-326 | D-PRICE.4 PR-3 form half: the "Applies from" date exemption, extra ... |
| 51 | 4649-4766 | `rulings-6.md` | 327-444 | D-DATA.1-6 DATA-17N packet Q1-Q6: diagnostics clocks, due dates, th... |
| 52 | 4767-4819 | `rulings-7.md` | 1-53 | D-SR.1-8 Site pages on the shared date range, SR-4 (Architect, Clau... |
| 53 | 4820-4877 | `rulings-7.md` | 54-111 | D-SR.9-12 Data in the range means output for the range, on every Si... |
| 54 | 4878-4919 | `rulings-7.md` | 112-153 | D-SR.19-30 SR-5 and SR-6/7/8 pre-flight rulings (Architect, Claude,... |
| 55 | 4920-4962 | `rulings-7.md` | 154-196 | D-SR.31-38 Every tab follows the range; SR-10 to SR-14 (Architect, ... |
| 56 | 4963-5000 | `rulings-7.md` | 197-234 | D-SR.40-46 and D-WARM.8: SR-4 tests and builder calls, unlisted rou... |
| 57 | 5001-5010 | `rulings-7.md` | 235-244 | D-SR.47 SR-8 Q2-Q5 (Architect, Claude, 2026-11-12 night, owner-dele... |
| 58 | 5011-5019 | `rulings-7.md` | 245-253 | D-SR.48 SR-8 Q6: the range shows the stored "every eligible hour" h... |
| 59 | 5020-5031 | `rulings-7.md` | 254-265 | D-SR.49 SR-6a Q1-Q5 and guard policy (Architect, Claude, 2026-11-12... |
| 60 | 5032-5041 | `rulings-7.md` | 266-275 | D-SR.50 SR-5: the range names retired Findings; Postgres cases with... |
| 61 | 5042-5068 | `rulings-7.md` | 276-302 | D-SR.51-54 SR-10 builder interpretations, the kill switch, the rebu... |
| 62 | 5069-5079 | `rulings-7.md` | 303-313 | D-SR.55 SR-10k Q1-Q4 (Architect, Claude, 2026-11-12 night, owner-de... |
| 63 | 5080-5094 | `rulings-7.md` | 314-328 | D-SR.56 SR-6 review M2 and L1: the local-day grade on UTC days, and... |
| 64 | 5095-5113 | `rulings-7.md` | 329-347 | D-SR.57 SR-4c review L2, L3 and the two-declarer risk (Architect, C... |
| 65 | 5114-5136 | `rulings-7.md` | 348-370 | D-SR.58 SR-11 Q1-Q3 (Architect, Claude, 2026-11-12 night, owner-del... |
| 66 | 5137-5168 | `rulings-7.md` | 371-402 | D-SR.59 SR-4a+b review H-1, L-1, L-4: short ranges on the mini dept... |
| 67 | 5169-5191 | `rulings-7.md` | 403-425 | D-SR.60 SR-11: start successes stay the hour-card sum; D-SR.58 Q2's... |
| 68 | 5192-5201 | `rulings-7.md` | 426-435 | D-SR.61 SR-4: negative-offset zones use the range's date strings ev... |
| 69 | 5202-5225 | `rulings-7.md` | 436-459 | D-SR.62 SR-8 parity: the one-day read follows the stored measure's ... |
| 70 | 5226-5242 | `rulings-7.md` | 460-476 | D-SR.63 The rows-on switch for the 17 Nov build (Architect, Claude,... |
| 71 | 5243-5274 | `rulings-7.md` | 477-508 | D-SR.64-68 SR-4 live check (F1-F3, the migration 409) and the SR-8 ... |
| 72 | 5275-5289 | `rulings-7.md` | 509-523 | D-SR.69 KOBO-001 10-31: a story gap; the SR-10/11 head gate on NO_D... |
| 73 | 5290-5346 | `rulings-7.md` | 524-580 | D-SR.70-72 SR-10/11 parity findings: pre-data days, the precise hea... |
| 74 | 5347-5367 | `rulings-7.md` | 581-601 | D-SR.73 Estate "Current view" label after SR-4; R339 / ruling 71 / ... |
| 75 | 5368-5407 | `rulings-8.md` | 1-40 | D-SR.74 Lane G: SR-12b Q1-Q3 and WARM-1 gate refusals (Architect, C... |
| 76 | 5408-5419 | `rulings-8.md` | 41-52 | D-SR.75 AP-1 analytics readiness port sized; database stays Postgre... |
| 77 | 5420-5455 | `rulings-8.md` | 53-88 | D-SR.76 Lane K SR-8/SR-10 page questions (Architect, Claude, 2026-1... |
| 78 | 5456-5468 | `rulings-8.md` | 89-101 | D-SR.77 Lane H SR-5 questions; AP-1 size corrected (Architect, Clau... |
| 79 | 5469-5494 | `rulings-8.md` | 102-127 | D-UQFI.6-10 UQ-FI builder questions (Architect, Claude, 2026-11-13,... |
| 80 | 5495-5514 | `rulings-8.md` | 128-147 | D-SR.78 AP-1 builder questions (Architect, Claude, 2026-11-13, owne... |
| 81 | 5515-5541 | `rulings-8.md` | 148-174 | D-UP.12 UP-1 review L2: a stale FAILED job must not pin "Not analys... |
| 82 | 5542-5565 | `rulings-8.md` | 175-198 | D-UQFI.11-12 UQ-FI-3 builder questions (Architect, Claude, 2026-11-... |
| 83 | 5566-5603 | `rulings-8.md` | 199-236 | D-SR.79 AP-1 review H1 and Lows: where the stored readiness table g... |
| 84 | 5604-5618 | `rulings-8.md` | 237-251 | D-MB.1-2 MB-1 packet questions (Architect, Claude, 2026-11-13, owne... |
| 85 | 5619-5642 | `rulings-8.md` | 252-275 | D-UQFI.13-18 UQ-FI-2 session-2 questions (Architect, Claude, 2026-1... |
| 86 | 5643-5667 | `rulings-8.md` | 276-300 | D-SR.80 AP-1 parity: what replaces it, the Kisiwa 409, merge timing... |
| 87 | 5668-5687 | `rulings-8.md` | 301-320 | D-SR.81 CO-10 "16 min unknown": a reported charging state is known ... |
| 88 | 5688-5705 | `rulings-8.md` | 321-338 | D-SR.82 A range before the Site was imported reads its days, not 40... |
| 89 | 5706-5726 | `rulings-8.md` | 339-359 | D-SR.83 Kisiwa/Kobo Overview and Finding-index reads become stored,... |
| 90 | 5727-5746 | `rulings-8.md` | 360-379 | D-SR.83a The Overview's wall-clock fields go through the read-insta... |
| 91 | 5747-5772 | `rulings-9.md` | 1-26 | D-SR.83b The stored Overview carries schedule facts, not schedule c... |
