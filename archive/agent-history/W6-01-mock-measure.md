# W6-01 mock measurements (v69 mock, headless Chrome, 2026-10-22)

Helper ran unmodified: `node tools/measure-mock-panels.mjs <dir> incidents maintenance maintenance-preventive wr-overview wr-record wr-history oprecords` (Chrome at default path worked). Heights in px. Rows = row count and min-max row height (single-line rows are the min). Wrap = rows taller than the minimum. Overflow = tableScroll>tableClient (panel-local) / document scrollWidth>clientWidth.

Raw JSON: `C:/Users/assef/AppData/Local/Temp/claude/C--Users-assef-Bineyame-AssetOpsV1/97bcb271-5a17-44b6-83b8-6d194dc45f39/scratchpad/m1/mock-measure.json` (baseline), `C:/Users/assef/AppData/Local/Temp/claude/C--Users-assef-Bineyame-AssetOpsV1/97bcb271-5a17-44b6-83b8-6d194dc45f39/scratchpad/m1/worst-case.json` (variants), screenshots beside them. Worst-case variants were injected into the live DOM by `scratchpad/worst.mjs` (no mock file edited); refusal copy used: "This actor cannot change work at this site." (longest refusal in section 2).

## incidents @ 1440

Baseline: h1 "Incidents", page 1001, docScrollW 1425/1425

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| cards | Open incidents / High severity / Awaitin | 113 | - | - | - |  |
| panel | Incident cases | 183 | 1121/1121 | 33 | 1r 51 | 0 |
| panel | Case boundaries | 99 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1001 | no | 113 | Incident cases: 183 / T83 / 1r 51<br>Case boundaries: 99 |
| titles200 | 1001 | YES 3272 | 128 | Title TTTTTTTTTTTTTTTTTTTTTTTT: 203 / T83 / 1r 51<br>Title TTTTTTTTTTTTTTTTTTTTTTTT: 119 |
| actor128 | 1001 | no | 113 | Incident cases: 245 / T144 / 1r 97 / hscroll<br>Case boundaries: 99 |
| text4000 | 1538 | no | 113 | Incident cases: 528 / T83 / 1r 51<br>Case boundaries: 552 |
| uuid | 1001 | no | 113 | Incident cases: 194 / T94 / 1r 62<br>Case boundaries: 99 |
| refusal | 1001 | no | 113 | Incident cases: 183 / T83 / 1r 51<br>Case boundaries: 99 |

## incidents @ 390

Baseline: h1 "Incidents", page 1139, docScrollW 390/390

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| cards | Open incidents / High severity / Awaitin | 248 | - | - | - |  |
| panel | Incident cases | 248 | 594/320 OVER | 33 | 1r 97 | 0 |
| panel | Case boundaries | 142 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1139 | no | 248 | Incident cases: 248 / T129 / 1r 97 / hscroll<br>Case boundaries: 142 |
| titles200 | 3600 | YES 2583 | 278 | Title TTTTTTTTTTTTTTTTTTTTTTTT: 250 / T129 / 1r 97 / hscroll<br>Title TTTTTTTTTTTTTTTTTTTTTTTT: 162 |
| actor128 | 1139 | no | 248 | Incident cases: 248 / T129 / 1r 97 / hscroll<br>Case boundaries: 142 |
| text4000 | 4090 | no | 248 | Incident cases: 1536 / T129 / 1r 97 / hscroll<br>Case boundaries: 1805 |
| uuid | 1280 | no | 248 | Incident cases: 388 / T270 / 1r 238 / hscroll<br>Case boundaries: 142 |
| refusal | 1139 | no | 248 | Incident cases: 230 / T129 / 1r 97 / hscroll<br>Case boundaries: 99 |

## maintenance @ 1440

Baseline: h1 "Maintenance", page 1001, docScrollW 1425/1425

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| cards | Open work / Verification overdue / Preve | 138 | - | - | - |  |
| panel | Corrective work requests | 234 | 1121/1121 | 33 | 2r 51 | 0 |
| notice | Work requests share the managed-task lif | 42 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1001 | no | 138 | Corrective work requests: 234 / T134 / 2r 51 |
| titles200 | 1001 | YES 3272 | 153 | Title TTTTTTTTTTTTTTTTTTTTTTTT: 254 / T134 / 2r 51 |
| actor128 | 1001 | no | 138 | Corrective work requests: 324 / T224 / 2r 79-97 / hscroll |
| text4000 | 1165 | no | 138 | Corrective work requests: 579 / T134 / 2r 51 |
| uuid | 1001 | no | 138 | Corrective work requests: 234 / T134 / 2r 51 |
| refusal | 1001 | no | 138 | Corrective work requests: 234 / T134 / 2r 51 |

## maintenance @ 390

Baseline: h1 "Maintenance", page 1240, docScrollW 390/390

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| cards | Open work / Verification overdue / Preve | 272 | - | - | - |  |
| panel | Corrective work requests | 327 | 696/320 OVER | 33 | 2r 79-97 | 1 |
| notice | Work requests share the managed-task lif | 78 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1240 | no | 272 | Corrective work requests: 327 / T209 / 2r 79-97 / hscroll |
| titles200 | 3600 | YES 2583 | 302 | Title TTTTTTTTTTTTTTTTTTTTTTTT: 329 / T209 / 2r 79-97 / hscroll |
| actor128 | 1240 | no | 272 | Corrective work requests: 327 / T209 / 2r 79-97 / hscroll |
| text4000 | 2528 | no | 272 | Corrective work requests: 1615 / T209 / 2r 79-97 / hscroll |
| uuid | 1257 | no | 272 | Corrective work requests: 345 / T227 / 2r 97 / hscroll |
| refusal | 1246 | no | 272 | Corrective work requests: 309 / T209 / 2r 79-97 / hscroll |

## maintenance-preventive @ 1440

Baseline: h1 "Maintenance", page 1055, docScrollW 1425/1425

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| statusbar | 2 overdueScheduled by calendar or runnin | 44 | - | - | - |  |
| cards | Scheduled items / Overdue / Due in 14 da | 113 | - | - | - |  |
| panel | Preventive plan | 432 | 1121/1121 | 33 | 5r 51-62 | 4 |
| notice | PM-0455 was overdue when the backup star | 42 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1055 | no | 113 | Preventive plan: 432 / T332 / 5r 51-62 |
| titles200 | 1123 | YES 3272 | 128 | Title TTTTTTTTTTTTTTTTTTTTTTTT: 452 / T332 / 5r 51-62 |
| actor128 | 1055 | no | 113 | Preventive plan: 432 / T332 / 5r 51-62 |
| text4000 | 1399 | no | 113 | Preventive plan: 777 / T332 / 5r 51-62 |
| uuid | 1066 | no | 113 | Preventive plan: 443 / T343 / 5r 62 |
| refusal | 1116 | no | 113 | Preventive plan: 432 / T332 / 5r 51-62 |

## maintenance-preventive @ 390

Baseline: h1 "Maintenance", page 1588, docScrollW 390/390

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| statusbar | 2 overdueScheduled by calendar or runnin | 98 | - | - | - |  |
| cards | Scheduled items / Overdue / Due in 14 da | 248 | - | - | - |  |
| panel | Preventive plan | 602 | 588/320 OVER | 33 | 5r 80-97 | 3 |
| notice | PM-0455 was overdue when the backup star | 60 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1588 | no | 248 | Preventive plan: 602 / T484 / 5r 80-97 / hscroll |
| titles200 | 3600 | YES 2583 | 278 | Title TTTTTTTTTTTTTTTTTTTTTTTT: 604 / T484 / 5r 80-97 / hscroll |
| actor128 | 1588 | no | 248 | Preventive plan: 602 / T484 / 5r 80-97 / hscroll |
| text4000 | 2876 | no | 248 | Preventive plan: 1890 / T484 / 5r 80-97 / hscroll |
| uuid | 1623 | no | 248 | Preventive plan: 637 / T519 / 5r 97 / hscroll |
| refusal | 1613 | no | 248 | Preventive plan: 584 / T484 / 5r 80-97 / hscroll |

## wr-overview @ 1440

Baseline: h1 "Starter and control-circuit inspection", page 1001, docScrollW 1425/1425

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| panel | Work done | 286 | - | - | - |  |
| panel | Lifecycle | 286 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1001 | no | - | Work done: 286<br>Lifecycle: 286 |
| titles200 | 1001 | YES 3367 | - | Title TTTTTTTTTTTTTTTTTTTTTTTT: 306<br>Title TTTTTTTTTTTTTTTTTTTTTTTT: 306 |
| actor128 | 1001 | no | - | Work done: 286<br>Lifecycle: 286 |
| text4000 | 1517 | no | - | Work done: 1042<br>Lifecycle: 1042 |
| uuid | 1001 | no | - | Work done: 301<br>Lifecycle: 301 |
| refusal | 1001 | no | - | Work done: 265<br>Lifecycle: 265 |

## wr-overview @ 390

Baseline: h1 "Starter and control-circuit inspection", page 1357, docScrollW 390/390

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| panel | Work done | 338 | - | - | - |  |
| panel | Lifecycle | 161 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1357 | no | - | Work done: 338<br>Lifecycle: 161 |
| titles200 | 3600 | YES 2583 | - | Title TTTTTTTTTTTTTTTTTTTTTTTT: 358<br>Title TTTTTTTTTTTTTTTTTTTTTTTT: 181 |
| actor128 | 1357 | no | - | Work done: 338<br>Lifecycle: 161 |
| text4000 | 4076 | no | - | Work done: 2001<br>Lifecycle: 1217 |
| uuid | 1387 | no | - | Work done: 368<br>Lifecycle: 161 |
| refusal | 1375 | no | - | Work done: 295<br>Lifecycle: 161 |

## wr-record @ 1440

Baseline: h1 "Starter and control-circuit inspection", page 1001, docScrollW 1425/1425

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| panel | Maintenance record · activity | 438 | 1121/1121 | 33 | 6r 51 | 0 |
| notice | This record is also listed in Operationa | 42 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1001 | no | - | Maintenance record · activity: 438 / T338 / 6r 51 |
| titles200 | 1027 | YES 3367 | - | Title TTTTTTTTTTTTTTTTTTTTTTTT: 458 / T338 / 6r 51 |
| actor128 | 1001 | no | - | Maintenance record · activity: 438 / T338 / 6r 51 |
| text4000 | 3919 | no | - | Maintenance record · activity: 3383 / T2939 / 6r 484 |
| uuid | 1001 | no | - | Maintenance record · activity: 438 / T338 / 6r 51 |
| refusal | 1035 | no | - | Maintenance record · activity: 438 / T338 / 6r 51 |

## wr-record @ 390

Baseline: h1 "Starter and control-circuit inspection", page 1640, docScrollW 390/390

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| panel | Maintenance record · activity | 716 | 320/320 | 33 | 6r 62-133 | 5 |
| notice | This record is also listed in Operationa | 42 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1640 | no | - | Maintenance record · activity: 716 / T616 / 6r 62-133 |
| titles200 | 3600 | YES 2583 | - | Title TTTTTTTTTTTTTTTTTTTTTTTT: 736 / T616 / 6r 62-133 |
| actor128 | 1640 | no | - | Maintenance record · activity: 716 / T616 / 6r 62-133 |
| text4000 | 44749 | no | - | Maintenance record · activity: 43825 / T42419 / 6r 7064-7065 |
| uuid | 1710 | no | - | Maintenance record · activity: 787 / T687 / 6r 97-133 |
| refusal | 1701 | no | - | Maintenance record · activity: 716 / T616 / 6r 62-133 |

## wr-history @ 1440

Baseline: h1 "Starter and control-circuit inspection", page 1001, docScrollW 1425/1425

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| panel | History | 332 | 1121/1121 | 33 | 5r 44-45 | 4 |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1001 | no | - | History: 332 / T255 / 5r 44-45 |
| titles200 | 1001 | YES 3367 | - | Title TTTTTTTTTTTTTTTTTTTTTTTT: 352 / T255 / 5r 44-45 |
| actor128 | 1001 | no | - | History: 332 / T255 / 5r 44-45 |
| text4000 | 2742 | no | - | History: 2267 / T2190 / 5r 431-432 |
| uuid | 1001 | no | - | History: 332 / T255 / 5r 44-45 |
| refusal | 1001 | no | - | History: 332 / T255 / 5r 44-45 |

## wr-history @ 390

Baseline: h1 "Starter and control-circuit inspection", page 1243, docScrollW 390/390

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| panel | History | 402 | 320/320 | 33 | 5r 44-62 | 4 |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1243 | no | - | History: 402 / T325 / 5r 44-62 |
| titles200 | 3600 | YES 2583 | - | Title TTTTTTTTTTTTTTTTTTTTTTTT: 422 / T325 / 5r 44-62 |
| actor128 | 1313 | no | - | History: 473 / T396 / 5r 62-97 / hscroll |
| text4000 | 12872 | no | - | History: 12032 / T11955 / 5r 2384-2385 |
| uuid | 1348 | no | - | History: 508 / T431 / 5r 79-80 |
| refusal | 1303 | no | - | History: 402 / T325 / 5r 44-62 |

## oprecords @ 1440

Baseline: h1 "Operational records", page 1335, docScrollW 1425/1425

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| cards | Records in window / Feeding evidence / I | 113 | - | - | - |  |
| panel | Operational records | 540 | 1121/1121 | 33 | 8r 51 | 0 |
| panel | Record a manual reading | 289 | - | - | - |  |
| panel | How records are used | 289 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 1335 | no | 113 | Operational records: 540 / T440 / 8r 51<br>Record a manual reading: 289<br>How records are used: 289 |
| titles200 | 1424 | YES 3272 | 128 | Title TTTTTTTTTTTTTTTTTTTTTTTT: 560 / T440 / 8r 51<br>Title TTTTTTTTTTTTTTTTTTTTTTTT: 309<br>Title TTTTTTTTTTTTTTTTTTTTTTTT: 309 |
| actor128 | 1879 | no | 113 | Operational records: 1084 / T984 / 8r 80-168 / hscroll<br>Record a manual reading: 289<br>How records are used: 289 |
| text4000 | 9429 | no | 113 | Operational records: 6182 / T5737 / 8r 713<br>Record a manual reading: 2742<br>How records are used: 2742 |
| uuid | 1424 | no | 113 | Operational records: 630 / T530 / 8r 62<br>Record a manual reading: 289<br>How records are used: 289 |
| refusal | 1396 | no | 113 | Operational records: 540 / T440 / 8r 51<br>Record a manual reading: 289<br>How records are used: 289 |

## oprecords @ 390

Baseline: h1 "Operational records", page 2569, docScrollW 390/390

| kind | title | h | table scroll/client | thead | rows | wrap |
|---|---|---|---|---|---|---|
| cards | Records in window / Feeding evidence / I | 263 | - | - | - |  |
| panel | Operational records | 1069 | 601/320 OVER | 33 | 8r 80-168 | 7 |
| panel | Record a manual reading | 443 | - | - | - |  |
| panel | How records are used | 188 | - | - | - |  |

Worst-case variants (page h, doc overflow, cards h; panel h / table h / rows / table hscroll):

| variant | page | docOver | cards | panels |
|---|---|---|---|---|
| baseline | 2569 | no | 263 | Operational records: 1069 / T969 / 8r 80-168 / hscroll<br>Record a manual reading: 443<br>How records are used: 188 |
| titles200 | 3600 | YES 2583 | 293 | Title TTTTTTTTTTTTTTTTTTTTTTTT: 1089 / T969 / 8r 80-168 / hscroll<br>Title TTTTTTTTTTTTTTTTTTTTTTTT: 463<br>Title TTTTTTTTTTTTTTTTTTTTTTTT: 208 |
| actor128 | 2569 | no | 263 | Operational records: 1069 / T969 / 8r 80-168 / hscroll<br>Record a manual reading: 443<br>How records are used: 188 |
| text4000 | 63829 | no | 263 | Operational records: 57954 / T56548 / 8r 7064-7065 / hscroll<br>Record a manual reading: 1749<br>How records are used: 3257 |
| uuid | 2728 | no | 263 | Operational records: 1228 / T1128 / 8r 132-168 / hscroll<br>Record a manual reading: 443<br>How records are used: 188 |
| refusal | 2571 | no | 263 | Operational records: 1069 / T969 / 8r 80-168 / hscroll<br>Record a manual reading: 443<br>How records are used: 129 |

