# MA-1 mock measurements (v70 addendum)

Command: `node tools/measure-mock-panels.mjs --mock frontend/mockups/v70 <out> portfolio mini cold ev findings-opportunities finding-history verification`
Revision measured: 5bfd7fec4 (branch task/MA-1-mock-addendum). Headless Chrome on file://, no server.

## Page width (no horizontal scroll when docScrollW = clientW)

| Screen | Width | Page height | docScrollW | clientW | Horizontal scroll |
|---|---|---|---|---|---|
| portfolio | 1440 | 2209 | 1425 | 1425 | none |
| portfolio | 390 | 4280 | 390 | 390 | none |
| mini | 1440 | 2325 | 1425 | 1425 | none |
| mini | 390 | 4742 | 390 | 390 | none |
| cold | 1440 | 2351 | 1425 | 1425 | none |
| cold | 390 | 4868 | 390 | 390 | none |
| ev | 1440 | 2345 | 1425 | 1425 | none |
| ev | 390 | 4836 | 390 | 390 | none |
| findings-opportunities | 1440 | 1111 | 1425 | 1425 | none |
| findings-opportunities | 390 | 1716 | 390 | 390 | none |
| finding-history | 1440 | 1001 | 1425 | 1425 | none |
| finding-history | 390 | 1299 | 390 | 390 | none |
| verification | 1440 | 1414 | 1425 | 1425 | none |
| verification | 390 | 2592 | 390 | 390 | none |

## Panels and blocks (top, height, width in px)

### portfolio @ 1440

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| panel | Where management should act first | 755 | 1122 | 836 | 802/802 |
| panel | Outcomes across the estate | 755 | 547 | 309 |  |
| panel | An opportunity beyond reducing cost | 1894 | 223 | 573 |  |
| panel | What changed in this review | 1894 | 223 | 573 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 68 | 16 | 197 |  |
| block | right: Find a screenWindow: Event window6 Oct 2026 · each site’s ev | 59 | 34 | 549 |  |
| block | breadcrumbs: Portfolio | 133 | 15 | 1161 |  |
| block | div: Portfolio Value & Operations | 165 | 61 | 435 |  |
| block | div: Portfolio: Needs attention3 simulated sites · 1 mini-grid /  | 244 | 22 | 440 |  |
| block | claim-link: Assessment scope & periods ↗ | 247 | 15 | 150 |  |
| block | value-card green oc-pfcard: Grow revenueGrow revenueCapture more value | 283 | 413 | 281 |  |
| block | value-card amber oc-pfcard: Optimize cost and efficiencyOptimize cost  | 283 | 413 | 281 |  |
| block | value-card red oc-pfcard: Protect asset and capitalProtect asset and c | 283 | 413 | 281 |  |
| block | value-card neutral oc-pfcard: Assure performance and returnsAssure per | 283 | 413 | 281 |  |
| block | span: 3 | 721 | 16 | 87 |  |
| block | span: 1 | 721 | 16 | 175 |  |
| block | span: 3 | 721 | 16 | 114 |  |
| block | span: 3 | 721 | 16 | 107 |  |
| block | span: 8 | 721 | 16 | 137 |  |
| block | pulse-note: Distinct consequence categories · no combined savings tota | 723 | 12 | 239 |  |
| block | portfolio-side: Outcomes across the estate | 755 | 1122 | 309 |  |
| block | span: 120 kWh | 2133 | 14 | 378 |  |
| block | a: Inspect energy basis → | 2133 | 14 | 91 |  |
| block | span: Other sites lack comparable full-window energy coverage. | 2133 | 14 | 230 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 2161 | 18 | 1161 |  |

### portfolio @ 390

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| panel | Where management should act first | 1577 | 1308 | 360 | 338/720 |
| panel | Outcomes across the estate | 2900 | 500 | 360 |  |
| panel | An opportunity beyond reducing cost | 3554 | 247 | 360 |  |
| panel | What changed in this review | 3829 | 298 | 360 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 170 | 15 | 181 |  |
| block | right: Find a screenWindow: Event window6 Oct 2026 · each site’s ev | 205 | 30 | 221 |  |
| block | breadcrumbs: Portfolio | 266 | 15 | 360 |  |
| block | div: Portfolio Value & Operations | 298 | 75 | 360 |  |
| block | div: Portfolio: Needs attention3 simulated sites · 1 mini-grid /  | 414 | 49 | 360 |  |
| block | claim-link: Assessment scope & periods ↗ | 478 | 15 | 150 |  |
| block | value-card green oc-pfcard: Grow revenueGrow revenueCapture more value | 510 | 535 | 176 |  |
| block | value-card amber oc-pfcard: Optimize cost and efficiencyOptimize cost  | 510 | 535 | 176 |  |
| block | value-card red oc-pfcard: Protect asset and capitalProtect asset and c | 1054 | 383 | 176 |  |
| block | value-card neutral oc-pfcard: Assure performance and returnsAssure per | 1054 | 383 | 176 |  |
| block | span: 3 | 1463 | 16 | 87 |  |
| block | span: 1 | 1463 | 16 | 175 |  |
| block | span: 3 | 1491 | 16 | 114 |  |
| block | span: 3 | 1491 | 16 | 107 |  |
| block | span: 8 | 1519 | 16 | 137 |  |
| block | pulse-note: Distinct consequence categories · no combined savings tota | 1547 | 12 | 239 |  |
| block | portfolio-side: Outcomes across the estate | 2900 | 637 | 360 |  |
| block | span: 120 kWh | 4141 | 29 | 358 |  |
| block | a: Inspect energy basis → | 4176 | 14 | 91 |  |
| block | span: Other sites lack comparable full-window energy coverage. | 4176 | 14 | 230 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 4204 | 58 | 360 |  |

### mini @ 1440

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| statusbar | Needs attention Confidence: LowⓘAssessed this hour: dispatch only · ot | 304 | 45 | 1161 |  |
| panel | What happened in the selected hour | 1419 | 238 | 1161 |  |
| panel | Operating context | 1674 | 373 | 735 |  |
| panel | Needs attention | 1674 | 373 | 408 |  |
| panel | Bounded money consequence | 2066 | 193 | 735 |  |
| panel | Next step | 2066 | 193 | 408 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 68 | 16 | 197 |  |
| block | searchbox: Find a screen | 59 | 34 | 116 |  |
| block | select: Kobo Mini-grid · Mini-gridGreenHarvest Cold Room · Cold-chai | 61 | 31 | 222 |  |
| block | range-picker: Window: Event window6 Oct 2026 · 14:20–15:20 EAT▾ | 62 | 29 | 327 |  |
| block | avatar: BY | 61 | 30 | 30 |  |
| block | breadcrumbs: Sites›Kobo Mini-grid›Overview | 133 | 15 | 1161 |  |
| block | title-row: Kobo Mini-grid | 165 | 34 | 398 |  |
| block | p: 60 kWp PV · 200 kWh battery · 40 kW genset · residential, cl | 206 | 20 | 398 |  |
| block | tabs : OverviewFoundationHealthPerformanceFindingsWorkFinancialsEvi | 244 | 42 | 1161 |  |
| block | objective: Objective: serve residential, clinic and productive loads w | 367 | 46 | 1161 |  |
| block | ob-board-head: How this site is doing | 413 | 22 | 1161 |  |
| block | ob-sum: Grow revenueGrow revenueCapture more value from existing inf | 446 | 74 | 1156 |  |
| block | ob-body: TargetNo target set yetNo target, so no days are judged yetP | 519 | 362 | 1156 |  |
| block | ob-sum: Optimize cost and efficiencyOptimize cost and efficiencyElim | 891 | 74 | 1156 |  |
| block | ob-body: Generator ran 30 minutes longer than the load needed · seen  | 965 | 267 | 1156 |  |
| block | ob-sum: Protect asset and capitalProtect asset and capitalPreserve a | 1242 | 74 | 1156 |  |
| block | ob-body: Battery and generator condition is not assessed; these are e | 1316 | 296 | 1156 |  |
| block | ob-sum: Assure performance and returnsAssure performance and returns | 1326 | 74 | 1156 |  |
| block | ob-body: One battery report is missing, so 30 minutes stay unclassifi | 1400 | 280 | 1156 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 2277 | 18 | 1161 |  |

### mini @ 390

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| statusbar | Needs attention Confidence: LowⓘAssessed this hour: dispatch only · ot | 515 | 114 | 360 |  |
| panel | What happened in the selected hour | 3013 | 523 | 360 |  |
| panel | Operating context | 3554 | 286 | 360 |  |
| panel | Needs attention | 3859 | 370 | 360 |  |
| panel | Bounded money consequence | 4247 | 190 | 360 |  |
| panel | Next step | 4455 | 193 | 360 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 170 | 15 | 181 |  |
| block | select: Kobo Mini-grid · Mini-gridGreenHarvest Cold Room · Cold-chai | 205 | 31 | 222 |  |
| block | range-picker: Window: Event window6 Oct 2026 · 14:20–15:20 EAT▾ | 247 | 29 | 181 |  |
| block | avatar: BY | 246 | 30 | 30 |  |
| block | breadcrumbs: Sites›Kobo Mini-grid›Overview | 307 | 15 | 360 |  |
| block | title-row: Kobo Mini-grid | 339 | 29 | 360 |  |
| block | p: 60 kWp PV · 200 kWh battery · 40 kW genset · residential, cl | 375 | 40 | 360 |  |
| block | tabs : OverviewFoundationHealthPerformanceFindingsWorkFinancialsEvi | 455 | 42 | 360 |  |
| block | objective: Objective: serve residential, clinic and productive loads w | 647 | 64 | 360 |  |
| block | ob-board-head: How this site is doing | 712 | 22 | 360 |  |
| block | ob-sum: Grow revenueGrow revenueCapture more value from existing inf | 745 | 199 | 355 |  |
| block | ob-body: TargetNo target set yetNo target, so no days are judged yetP | 944 | 813 | 355 |  |
| block | ob-sum: Optimize cost and efficiencyOptimize cost and efficiencyElim | 1767 | 199 | 355 |  |
| block | ob-body: Generator ran 30 minutes longer than the load needed · seen  | 1966 | 641 | 355 |  |
| block | ob-sum: Protect asset and capitalProtect asset and capitalPreserve a | 2616 | 184 | 355 |  |
| block | ob-body: Battery and generator condition is not assessed; these are e | 2800 | 665 | 355 |  |
| block | ob-sum: Assure performance and returnsAssure performance and returns | 2810 | 184 | 355 |  |
| block | ob-body: One battery report is missing, so 30 minutes stay unclassifi | 2994 | 519 | 355 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 4666 | 58 | 360 |  |

### cold @ 1440

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| statusbar | Degraded Confidence: High Potential product exposurePower → backup → c | 304 | 44 | 1161 |  |
| panel | What happened · power → cooling → product conditions | 1408 | 274 | 1161 |  |
| panel | Chamber temperature | 1701 | 373 | 735 |  |
| panel | Needs attention | 1701 | 373 | 408 |  |
| panel | Bounded money consequence | 2092 | 193 | 735 |  |
| panel | Next step | 2092 | 193 | 408 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 68 | 16 | 197 |  |
| block | searchbox: Find a screen | 59 | 34 | 116 |  |
| block | select: Kobo Mini-grid · Mini-gridGreenHarvest Cold Room · Cold-chai | 61 | 31 | 222 |  |
| block | range-picker: Window: Event window6 Oct 2026 · 19:00–20:00 EAT▾ | 62 | 29 | 327 |  |
| block | avatar: BY | 61 | 30 | 30 |  |
| block | breadcrumbs: Sites›GreenHarvest Cold Room›Overview | 133 | 15 | 1161 |  |
| block | title-row: GreenHarvest Cold Room | 165 | 34 | 496 |  |
| block | p: Produce cold room · 2–4°C policy · hybrid: 15 kWp solar, 30  | 206 | 20 | 496 |  |
| block | tabs : OverviewFoundationHealthPerformanceFindingsWorkFinancialsEvi | 244 | 42 | 1161 |  |
| block | objective: Objective: keep the chamber at 2–4°C through power, cooling | 366 | 46 | 1161 |  |
| block | ob-board-head: How this site is doing | 412 | 22 | 1161 |  |
| block | ob ob-later: Grow revenueGrow revenueCapture more value from existing  | 444 | 76 | 1161 |  |
| block | ob-sum: Optimize cost and efficiencyOptimize cost and efficiencyElim | 528 | 74 | 1156 |  |
| block | ob-body: None of the visits fixed the backup generator’s automatic st | 602 | 283 | 1156 |  |
| block | ob-sum: Protect asset and capitalProtect asset and capitalPreserve a | 895 | 74 | 1156 |  |
| block | ob-body: Backup did not start by itself; cooling stopped until it was | 969 | 337 | 1156 |  |
| block | ob-sum: Assure performance and returnsAssure performance and returns | 1316 | 74 | 1156 |  |
| block | ob-body: Loading and door records are not connected, so stock impact  | 1389 | 264 | 1156 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 2303 | 18 | 1161 |  |

### cold @ 390

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| statusbar | Degraded Confidence: High Potential product exposurePower → backup → c | 549 | 113 | 360 |  |
| panel | What happened · power → cooling → product conditions | 3015 | 660 | 360 |  |
| panel | Chamber temperature | 3693 | 286 | 360 |  |
| panel | Needs attention | 3997 | 336 | 360 |  |
| panel | Bounded money consequence | 4351 | 190 | 360 |  |
| panel | Next step | 4559 | 215 | 360 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 170 | 15 | 181 |  |
| block | select: Kobo Mini-grid · Mini-gridGreenHarvest Cold Room · Cold-chai | 205 | 31 | 222 |  |
| block | range-picker: Window: Event window6 Oct 2026 · 19:00–20:00 EAT▾ | 247 | 29 | 181 |  |
| block | avatar: BY | 246 | 30 | 30 |  |
| block | breadcrumbs: Sites›GreenHarvest Cold Room›Overview | 307 | 15 | 360 |  |
| block | title-row: GreenHarvest Cold Room | 339 | 63 | 360 |  |
| block | p: Produce cold room · 2–4°C policy · hybrid: 15 kWp solar, 30  | 409 | 40 | 360 |  |
| block | tabs : OverviewFoundationHealthPerformanceFindingsWorkFinancialsEvi | 489 | 42 | 360 |  |
| block | objective: Objective: keep the chamber at 2–4°C through power, cooling | 680 | 64 | 360 |  |
| block | ob-board-head: How this site is doing | 745 | 22 | 360 |  |
| block | ob ob-later: Grow revenueGrow revenueCapture more value from existing  | 777 | 151 | 360 |  |
| block | ob-sum: Optimize cost and efficiencyOptimize cost and efficiencyElim | 936 | 184 | 355 |  |
| block | ob-body: None of the visits fixed the backup generator’s automatic st | 1120 | 681 | 355 |  |
| block | ob-sum: Protect asset and capitalProtect asset and capitalPreserve a | 1811 | 199 | 355 |  |
| block | ob-body: Backup did not start by itself; cooling stopped until it was | 2011 | 776 | 355 |  |
| block | ob-sum: Assure performance and returnsAssure performance and returns | 2797 | 199 | 355 |  |
| block | ob-body: Loading and door records are not connected, so stock impact  | 2996 | 525 | 355 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 4792 | 58 | 360 |  |

### ev @ 1440

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| statusbar | Needs attention Confidence: MediumⓘAssessed: session service, availabi | 304 | 45 | 1161 |  |
| panel | What happened on the service day | 1456 | 238 | 1161 |  |
| panel | Charging activity and site power | 1712 | 356 | 735 |  |
| panel | Needs attention | 1712 | 356 | 408 |  |
| panel | Bounded money consequence | 2086 | 193 | 735 |  |
| panel | Next step | 2086 | 193 | 408 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 68 | 16 | 197 |  |
| block | searchbox: Find a screen | 59 | 34 | 116 |  |
| block | select: Kobo Mini-grid · Mini-gridGreenHarvest Cold Room · Cold-chai | 61 | 31 | 222 |  |
| block | range-picker: Window: Event window6 Oct 2026 · 08:00–16:00 EAT▾ | 62 | 29 | 327 |  |
| block | avatar: BY | 61 | 30 | 30 |  |
| block | breadcrumbs: Sites›Depot Charging Hub›Overview | 133 | 15 | 1161 |  |
| block | title-row: Depot Charging Hub | 165 | 34 | 425 |  |
| block | p: 2 × 60 kW connectors · 80 kW site limit · no stationary batt | 206 | 20 | 425 |  |
| block | tabs : OverviewFoundationHealthPerformanceFindingsWorkFinancialsEvi | 244 | 42 | 1161 |  |
| block | objective: Objective: let depot vehicles charge when scheduled, within | 367 | 46 | 1161 |  |
| block | ob-board-head: How this site is doing | 413 | 22 | 1161 |  |
| block | ob-sum: Grow revenueGrow revenueCapture more value from existing inf | 446 | 74 | 1156 |  |
| block | ob-body: TargetNo target set yetNo target, so no days are judged yetP | 519 | 330 | 1156 |  |
| block | ob ob-later: Optimize cost and efficiencyOptimize cost and efficiencyE | 858 | 76 | 1161 |  |
| block | ob-sum: Protect asset and capitalProtect asset and capitalPreserve a | 943 | 74 | 1156 |  |
| block | ob-body: Connector 2 was out of service for 1 hour; which departures  | 1017 | 337 | 1156 |  |
| block | ob-sum: Assure performance and returnsAssure performance and returns | 1363 | 74 | 1156 |  |
| block | ob-body: One session end and 1 hour of connector status are missing
  | 1437 | 280 | 1156 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 2297 | 18 | 1161 |  |

### ev @ 390

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| statusbar | Needs attention Confidence: MediumⓘAssessed: session service, availabi | 530 | 114 | 360 |  |
| panel | What happened on the service day | 3047 | 587 | 360 |  |
| panel | Charging activity and site power | 3652 | 273 | 360 |  |
| panel | Needs attention | 3943 | 336 | 360 |  |
| panel | Bounded money consequence | 4297 | 233 | 360 |  |
| panel | Next step | 4548 | 193 | 360 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 170 | 15 | 181 |  |
| block | select: Kobo Mini-grid · Mini-gridGreenHarvest Cold Room · Cold-chai | 205 | 31 | 222 |  |
| block | range-picker: Window: Event window6 Oct 2026 · 08:00–16:00 EAT▾ | 247 | 29 | 181 |  |
| block | avatar: BY | 246 | 30 | 30 |  |
| block | breadcrumbs: Sites›Depot Charging Hub›Overview | 307 | 15 | 360 |  |
| block | title-row: Depot Charging Hub | 339 | 63 | 360 |  |
| block | p: 2 × 60 kW connectors · 80 kW site limit · no stationary batt | 409 | 20 | 360 |  |
| block | tabs : OverviewFoundationHealthPerformanceFindingsWorkFinancialsEvi | 470 | 42 | 360 |  |
| block | objective: Objective: let depot vehicles charge when scheduled, within | 662 | 64 | 360 |  |
| block | ob-board-head: How this site is doing | 726 | 22 | 360 |  |
| block | ob-sum: Grow revenueGrow revenueCapture more value from existing inf | 759 | 167 | 355 |  |
| block | ob-body: TargetNo target set yetNo target, so no days are judged yetP | 926 | 799 | 355 |  |
| block | ob ob-later: Optimize cost and efficiencyOptimize cost and efficiencyE | 1734 | 151 | 360 |  |
| block | ob-sum: Protect asset and capitalProtect asset and capitalPreserve a | 1894 | 199 | 355 |  |
| block | ob-body: Connector 2 was out of service for 1 hour; which departures  | 2093 | 726 | 355 |  |
| block | ob-sum: Assure performance and returnsAssure performance and returns | 2829 | 199 | 355 |  |
| block | ob-body: One session end and 1 hour of connector status are missing
  | 3028 | 525 | 355 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 4760 | 58 | 360 |  |

### findings-opportunities @ 1440

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| cards | Open findings / High priority / Low confidence / Awaiting verification | 304 | 113 | 1161 |  |
| panel | Opportunities to grow | 482 | 169 | 1161 |  |
| panel | Opportunities lens | 669 | 316 | 1161 | 1121/1121 |
| notice | Priority, confidence and workflow state stay separate. Opening a findi | 1003 | 42 | 1161 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 68 | 16 | 197 |  |
| block | right: Find a screenWindow: Event window6 Oct 2026 · each site’s ev | 59 | 34 | 549 |  |
| block | breadcrumbs: Findings›Opportunities | 133 | 15 | 1161 |  |
| block | div: Findings | 165 | 61 | 311 |  |
| block | tabs : All findingsCostRisksOpportunities | 244 | 42 | 1161 |  |
| block | chips: All statesOpenRecommendation | 435 | 31 | 1161 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 1063 | 18 | 1161 |  |

### findings-opportunities @ 390

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| cards | Open findings / High priority / Low confidence / Awaiting verification | 432 | 248 | 360 |  |
| panel | Opportunities to grow | 745 | 200 | 360 |  |
| panel | Opportunities lens | 963 | 563 | 360 | 320/629 |
| notice | Priority, confidence and workflow state stay separate. Opening a findi | 1544 | 78 | 360 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 170 | 15 | 181 |  |
| block | right: Find a screenWindow: Event window6 Oct 2026 · each site’s ev | 205 | 30 | 221 |  |
| block | breadcrumbs: Findings›Opportunities | 266 | 15 | 360 |  |
| block | div: Findings | 298 | 56 | 311 |  |
| block | tabs : All findingsCostRisksOpportunities | 372 | 42 | 360 |  |
| block | chips: All statesOpenRecommendation | 698 | 31 | 360 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 1640 | 58 | 360 |  |

### finding-history @ 1440

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| panel | Problem history | 358 | 164 | 1161 |  |
| panel | Revision history | 540 | 243 | 1161 | 1121/1121 |
| block | portfolio-name: Bineyame Operations / Demo estate | 68 | 16 | 197 |  |
| block | right: Find a screenWindow: Event window6 Oct 2026 · 14:20–15:20 EA | 59 | 34 | 507 |  |
| block | breadcrumbs: Findings›F-104›History· site: Kobo Mini-grid | 133 | 15 | 1161 |  |
| block | div: Generator support review | 165 | 61 | 310 |  |
| block | heading-actions: Open site | 165 | 36 | 76 |  |
| block | tabs : OverviewAnalysisEvidenceAlternativesRecommendationHistory | 244 | 42 | 1161 |  |
| block | oc-affectsline: AffectsOptimize cost and efficiencysupply cost per kwh | 304 | 38 | 1161 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 801 | 18 | 1161 |  |

### finding-history @ 390

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| panel | Problem history | 549 | 325 | 360 |  |
| panel | Revision history | 892 | 313 | 360 | 320/320 |
| block | portfolio-name: Bineyame Operations / Demo estate | 170 | 15 | 181 |  |
| block | right: Find a screenWindow: Event window6 Oct 2026 · 14:20–15:20 EA | 205 | 30 | 221 |  |
| block | breadcrumbs: Findings›F-104›History· site: Kobo Mini-grid | 266 | 15 | 360 |  |
| block | div: Generator support review | 298 | 56 | 261 |  |
| block | heading-actions: Open site | 298 | 36 | 76 |  |
| block | tabs : OverviewAnalysisEvidenceAlternativesRecommendationHistory | 372 | 42 | 360 |  |
| block | oc-affectsline: AffectsOptimize cost and efficiencysupply cost per kwh | 432 | 101 | 360 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 1223 | 58 | 360 |  |

### verification @ 1440

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| statusbar | ACT-048 · Verification window Provisional target passFinal outcome pen | 358 | 44 | 1161 |  |
| cards | Target change / Reserve breaches / Critical service / Final outcome | 611 | 113 | 1161 |  |
| panel | Target and guardrails evaluated together | 742 | 336 | 1161 | 1121/1121 |
| panel | Activity evidence | 1096 | 252 | 735 |  |
| panel | Outcome evidence | 1096 | 252 | 408 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 68 | 16 | 197 |  |
| block | right: Find a screenWindow: Event window6 Oct 2026 · 14:20–15:20 EA | 59 | 34 | 507 |  |
| block | breadcrumbs: Actions›ACT-048›Verification· site: Kobo Mini-grid | 133 | 15 | 1161 |  |
| block | div: Reduce extended generator support | 165 | 61 | 436 |  |
| block | heading-actions: Open site | 165 | 36 | 76 |  |
| block | tabs : OverviewPlanExecutionEvidenceVerificationHistory | 244 | 42 | 1161 |  |
| block | oc-affectsline: AffectsOptimize cost and efficiencysupply cost per kwh | 304 | 38 | 1161 |  |
| block | fix-line: F-104 Seen on 24 of the last 30 days · same generator | 432 | 18 | 1131 |  |
| block | done: Seen6 Oct | 458 | 38 | 221 |  |
| block | done: Action agreed6 Oct | 458 | 38 | 221 |  |
| block | current: Change madeDate not set in this example | 458 | 38 | 221 |  |
| block | todo: Checked and working, monitoringDate not set in this example | 458 | 38 | 221 |  |
| block | todo: Closed after 7 clean daysDate not set in this example | 458 | 38 | 221 |  |
| block | div: OwnerSite controls lead | 523 | 69 | 232 |  |
| block | div: Due / SLAWindow close · not set | 523 | 69 | 232 |  |
| block | div: StateVerification window | 523 | 69 | 232 |  |
| block | div: SourceF-104 | 523 | 69 | 232 |  |
| block | div: Success criterion≥25% less avoidable generator time; no rese | 523 | 69 | 232 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 1366 | 18 | 1161 |  |

### verification @ 390

| Kind | Title | Top | H | W | Table client/scroll |
|---|---|---|---|---|---|
| statusbar | ACT-048 · Verification window Provisional target passFinal outcome pen | 612 | 71 | 360 |  |
| cards | Target change / Reserve breaches / Critical service / Final outcome | 1160 | 264 | 360 |  |
| panel | Target and guardrails evaluated together | 1442 | 522 | 360 | 320/481 |
| panel | Activity evidence | 1982 | 252 | 360 |  |
| panel | Outcome evidence | 2252 | 246 | 360 |  |
| block | portfolio-name: Bineyame Operations / Demo estate | 170 | 15 | 181 |  |
| block | right: Find a screenWindow: Event window6 Oct 2026 · 14:20–15:20 EA | 205 | 30 | 221 |  |
| block | breadcrumbs: Actions›ACT-048›Verification· site: Kobo Mini-grid | 266 | 15 | 360 |  |
| block | div: Reduce extended generator support | 298 | 84 | 360 |  |
| block | heading-actions: Open site | 402 | 36 | 76 |  |
| block | tabs : OverviewPlanExecutionEvidenceVerificationHistory | 456 | 42 | 360 |  |
| block | oc-affectsline: AffectsOptimize cost and efficiencysupply cost per kwh | 516 | 80 | 360 |  |
| block | fix-line: F-104 Seen on 24 of the last 30 days · same generator | 713 | 18 | 330 |  |
| block | done: Seen6 Oct | 739 | 33 | 330 |  |
| block | done: Action agreed6 Oct | 776 | 33 | 330 |  |
| block | current: Change madeDate not set in this example | 813 | 33 | 330 |  |
| block | todo: Checked and working, monitoringDate not set in this example | 850 | 33 | 330 |  |
| block | todo: Closed after 7 clean daysDate not set in this example | 887 | 33 | 330 |  |
| block | div: OwnerSite controls lead | 947 | 54 | 179 |  |
| block | div: Due / SLAWindow close · not set | 947 | 54 | 179 |  |
| block | div: StateVerification window | 1001 | 54 | 179 |  |
| block | div: SourceF-104 | 1001 | 54 | 179 |  |
| block | div: Success criterion≥25% less avoidable generator time; no rese | 1054 | 87 | 179 |  |
| block | screen-foot: Illustrative mockup data · proposal for implementation ·  | 2516 | 58 | 360 |  |
