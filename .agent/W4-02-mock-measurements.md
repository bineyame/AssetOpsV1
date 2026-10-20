# W4-02 mock measurements (v69, tools/measure-mock-panels.mjs, main)

Heights/widths in px; budget rule per W3-02 closure: max = mock + max(24px,10%).

## renewable @ 1440 (page 1300px, scrollW 1425/1425)

| kind | title | top | h | w | extra |
|---|---|---:|---:|---:|---|
| statusbar | Watch Confidence: Mediumⓘ Lens: OpportunitySolar left unused on 3 of 5 | 354 | 45 | 1161 |  |
| cards | PV capability / PV used / Usable headroom / Recurring opportunity | 417 | 113 | 1161 | children h 113x281 113x281 113x281 113x281 |
| panel | From physical headroom to an opportunity | 548 | 244 | 735 |  |
| panel | Productive-use evaluation | 548 | 244 | 408 |  |
| panel | Eligible and excluded windows | 810 | 364 | 1161 | cols Day / period:247, Opportunity:196, Constraint check:515, Decision:163; rows 51/51/51/51/51 |
| notice | Opportunity is an evidence-backed capacity estimate. A paired load-add | 1192 | 42 | 1161 |  |

## renewable @ 390 (page 2114px, scrollW 390/390)

| kind | title | top | h | w | extra |
|---|---|---:|---:|---:|---|
| statusbar | Watch Confidence: Mediumⓘ Lens: OpportunitySolar left unused on 3 of 5 | 523 | 114 | 360 |  |
| cards | PV capability / PV used / Usable headroom / Recurring opportunity | 655 | 264 | 360 | children h 126x174 126x174 126x174 126x174 |
| panel | From physical headroom to an opportunity | 937 | 272 | 360 |  |
| panel | Productive-use evaluation | 1227 | 241 | 360 |  |
| panel | Eligible and excluded windows | 1486 | 438 | 360 | cols Day / period:89, Opportunity:92, Constraint check:121, Decision:77; rows 80/62/62/62/62; table scroll 379>320 |
| notice | Opportunity is an evidence-backed capacity estimate. A paired load-add | 1941 | 78 | 360 |  |

## service @ 1440 (page 1328px, scrollW 1425/1425)

| kind | title | top | h | w | extra |
|---|---|---:|---:|---:|---|
| statusbar | Service assessment: UnknownDelivered power is observed; requested-serv | 354 | 44 | 1161 |  |
| cards | Delivered load / Interruptions seen / Clinic (critical) / Unserved ene | 416 | 113 | 1161 | children h 113x281 113x281 113x281 113x281 |
| panel | Where the power went | 547 | 240 | 1161 |  |
| panel | Delivered power by addressed load | 805 | 262 | 1161 | cols Load:189, Role:166, Observed power:194, Required-service evidence:424, Assessment:149; rows 51/51/51 |
| panel | What is supported | 1085 | 177 | 735 |  |
| panel | What unlocks a service conclusion | 1085 | 177 | 408 |  |

## service @ 390 (page 1939px, scrollW 390/390)

| kind | title | top | h | w | extra |
|---|---|---:|---:|---:|---|
| statusbar | Service assessment: UnknownDelivered power is observed; requested-serv | 523 | 98 | 360 |  |
| cards | Delivered load / Interruptions seen / Clinic (critical) / Unserved ene | 639 | 264 | 360 | children h 126x174 126x174 126x174 126x174 |
| panel | Where the power went | 921 | 256 | 360 |  |
| panel | Delivered power by addressed load | 1195 | 296 | 360 | cols Load:74, Role:74, Observed power:111, Required-service evidence:166, Assessment:86; rows 62/62/62; table scroll 511>320 |
| panel | What is supported | 1508 | 142 | 360 |  |
| panel | What unlocks a service conclusion | 1668 | 177 | 360 |  |

## fuel @ 1440 (page 1477px, scrollW 1425/1425)

| kind | title | top | h | w | extra |
|---|---|---:|---:|---:|---|
| statusbar | Fuel balance: evidence limitedIllustrates the minimum balance terms; n | 354 | 44 | 1161 |  |
| cards | Opening evidence / Recorded deliveries / Expected use / Residual | 416 | 129 | 1161 | children h 129x281 129x281 129x281 129x281 |
| panel | Fuel balance at a glance | 563 | 271 | 1161 |  |
| panel | Balance bridge | 852 | 332 | 1161 | cols Term:268, Evidence basis:379, Treatment:474; rows 45/45/45/45/44 |
| notice | A fuel residual is unexplained inventory movement with uncertainty. It | 1202 | 42 | 1161 |  |
| panel | Inspect existing generator fuel interpretation | 1262 | 149 | 1161 |  |

## fuel @ 390 (page 2125px, scrollW 390/390)

| kind | title | top | h | w | extra |
|---|---|---:|---:|---:|---|
| statusbar | Fuel balance: evidence limitedIllustrates the minimum balance terms; n | 523 | 71 | 360 |  |
| cards | Opening evidence / Recorded deliveries / Expected use / Residual | 612 | 264 | 360 | children h 126x174 126x174 126x174 126x174 |
| panel | Fuel balance at a glance | 894 | 287 | 360 |  |
| panel | Balance bridge | 1199 | 526 | 360 | cols Term:94, Evidence basis:115, Treatment:111; rows 62/97/80/80/97 |
| notice | A fuel residual is unexplained inventory movement with uncertainty. It | 1742 | 78 | 360 |  |
| panel | Inspect existing generator fuel interpretation | 1839 | 192 | 360 |  |

## backup @ 1440 (page 1274px, scrollW 1425/1425)

| kind | title | top | h | w | extra |
|---|---|---:|---:|---:|---|
| statusbar | Backup readiness: UnknownGenerator operation alone is not a witnessed  | 354 | 44 | 1161 |  |
| cards | Outages in window / Start success / Last witnessed test / Critical ser | 416 | 113 | 1161 | children h 113x281 113x281 113x281 113x281 |
| panel | Backup event chains | 547 | 183 | 1161 | cols When:234, Grid:63, Start requested:151, Generator:108, Power to load:140, Load response:138, Outcome for service:183, Result:105; rows 51 |
| panel | Backup readiness evidence | 748 | 287 | 1161 | cols Required step:317, Available evidence:415, Current claim:389; rows 45/45/45/44 |
| panel | Operating evidence | 1053 | 155 | 735 |  |
| panel | Next evidence | 1053 | 155 | 408 |  |

## backup @ 390 (page 2084px, scrollW 390/390)

| kind | title | top | h | w | extra |
|---|---|---:|---:|---:|---|
| statusbar | Backup readiness: UnknownGenerator operation alone is not a witnessed  | 523 | 98 | 360 |  |
| cards | Outages in window / Start success / Last witnessed test / Critical ser | 639 | 232 | 360 | children h 110x174 110x174 110x174 110x174 |
| panel | Backup event chains | 889 | 265 | 360 | cols When:62, Grid:46, Start requested:112, Generator:80, Power to load:103, Load response:102, Outcome for service:136, Result:77; rows 114; table scroll 719>320 |
| panel | Backup readiness evidence | 1172 | 428 | 360 | cols Required step:98, Available evidence:126, Current claim:102; rows 80/80/80/79; table scroll 326>320 |
| panel | Operating evidence | 1618 | 177 | 360 |  |
| panel | Next evidence | 1813 | 177 | 360 |  |
