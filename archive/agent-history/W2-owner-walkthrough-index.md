# W2 owner walkthrough index (app versus mock)

Written 2026-10-20 at W2 close. This is the side-by-side list for the 22 cold-chain and EV charging screens that W2 built. It uses only the captures that already exist; nothing was newly captured. The owner walkthrough is final acceptance for W2, but it does not block later work (owner decision of 2026-10-19).

## How to use

1. Go to the `.agent` folder of the repository. Every capture path below is relative to it.
2. Each evidence folder also has an `index.html` (W2-06 and W2-07 have none, only the pictures). Open it in a browser to see every app and mock pair side by side.
3. Or open files yourself. The mock picture sits next to the app picture with the same name, `-mock.png` instead of `-app.png`. Compare 1440 (desktop) first, then 390 (phone).
4. For each screen, check the one line under "What to check": are the same panels there, in the same order, with similar prominence (size and weight)? Wording and numbers will differ because the app shows real test data and the mock is a drawing.
5. The mock screens live in `frontend/mockups/v69/index.html#/<mock screen>`. Mock screen names are in the second column.
6. An empty or refused capture is correct if it says plainly that data is missing. It is a finding only if a panel is missing, reordered or visibly much smaller or larger than the mock.
7. Note each finding as **structural** or **polish** (see the last section). A short list of screen name plus one sentence is enough.

All data is authored, generated or simulated test data, not field readings.

## The 22 screens and where each is captured

Cold-chain sites are `COLD-LAB-001` (Foundation uses `COLD-001` and `COLD-002`); the EV site is `EV-LAB-001`. The temperature, backup and finding captures come from the W2-03 follow-up folder, which replaced the first W2-03 folder (`W2-03-evidence`, older, not listed). Temperature also appears from W2-04 at a different address (`/performance/temperature`).

| # | Mock screen | App route | State shown | App capture 1440 / 390 | Panels the app shows, in order |
|---|---|---|---|---|---|
| 1 | `cold-foundation` | `/sites/COLD-001/foundation` | stocked: full test data | `W2-01-evidence/cold-foundation-stocked-1440-app.png` / `W2-01-evidence/cold-foundation-stocked-390-app.png` | Physical site > Operating interpretation |
| 2 | `cold-foundation` | `/sites/COLD-002/foundation` | cold store with no chamber probe | `W2-01-evidence/cold-foundation-missing-probe-1440-app.png` / `W2-01-evidence/cold-foundation-missing-probe-390-app.png` | Physical site > Operating interpretation |
| 3 | `cold-foundation` | `/sites/COLD-001/foundation` | no site version published | `W2-01-evidence/cold-foundation-no-version-1440-app.png` / `W2-01-evidence/cold-foundation-no-version-390-app.png` | Physical site > Operating interpretation |
| 4 | `cold-readiness` | `/sites/COLD-001/foundation/readiness` | stocked: full test data | `W2-01-evidence/cold-readiness-stocked-1440-app.png` / `W2-01-evidence/cold-readiness-stocked-390-app.png` | Readiness and commissioning evidence > Gateway status · edge-cold-001 > Connected sources > Effect on readiness and confidence |
| 5 | `cold-readiness` | `/sites/COLD-002/foundation/readiness` | cold store with no chamber probe | `W2-01-evidence/cold-readiness-missing-probe-1440-app.png` / `W2-01-evidence/cold-readiness-missing-probe-390-app.png` | Readiness and commissioning evidence > Gateway status · edge-cold-002 > Connected sources > Effect on readiness and confidence |
| 6 | `cold-readiness` | `/sites/COLD-001/foundation/readiness` | no site version published | `W2-01-evidence/cold-readiness-no-version-1440-app.png` / `W2-01-evidence/cold-readiness-no-version-390-app.png` | Readiness and commissioning evidence > Gateway status · edge-cold-001 > Connected sources > Effect on readiness and confidence |
| 7 | `cold-sld` | `/sites/COLD-001/foundation/sld` | stocked: full test data | `W2-01-evidence/cold-sld-stocked-1440-app.png` / `W2-01-evidence/cold-sld-stocked-390-app.png` | Kobo vaccine cold store > What each part does |
| 8 | `cold-sld` | `/sites/COLD-002/foundation/sld` | cold store with no chamber probe | `W2-01-evidence/cold-sld-missing-probe-1440-app.png` / `W2-01-evidence/cold-sld-missing-probe-390-app.png` | Kobo cold store without a chamber probe > What each part does |
| 9 | `cold-sld` | `/sites/COLD-001/foundation/sld` | no site version published | `W2-01-evidence/cold-sld-no-version-1440-app.png` / `W2-01-evidence/cold-sld-no-version-390-app.png` | Kobo vaccine cold store > What each part does |
| 10 | `cold` | `/sites/COLD-LAB-001` | stocked: full test data | `W2-04-evidence/cold-stocked-1440-app.png` / `W2-04-evidence/cold-stocked-390-app.png` | What happened · power → cooling → product conditions > Chamber temperature > Needs attention > Bounded money consequence > Next step |
| 11 | `cold` | `/sites/COLD-LAB-001` | empty: nothing recorded yet, says so | `W2-04-evidence/cold-empty-1440-app.png` / `W2-04-evidence/cold-empty-390-app.png` | What happened · power → cooling → product conditions > Chamber temperature > Needs attention > Bounded money consequence > Next step |
| 12 | `cold` | `/sites/COLD-LAB-001` | refused: read refused, says so | `W2-04-evidence/cold-refused-1440-app.png` / `W2-04-evidence/cold-refused-390-app.png` | What happened · power → cooling → product conditions > Chamber temperature > Needs attention > Bounded money consequence > Next step |
| 13 | `temperature` | `/sites/COLD-LAB-001/performance` | stocked: full test data | `W2-03-followup-evidence/temperature-stocked-1440-app.png` / `W2-03-followup-evidence/temperature-stocked-390-app.png` | Temperature with operating context > Excursion context > How each limit is set |
| 14 | `temperature` | `/sites/COLD-LAB-001/performance` | empty: nothing recorded yet, says so | `W2-03-followup-evidence/temperature-empty-1440-app.png` / `W2-03-followup-evidence/temperature-empty-390-app.png` | Temperature with operating context > Excursion context > How each limit is set |
| 15 | `temperature` | `/sites/COLD-LAB-001/performance` | refused: read refused, says so | `W2-03-followup-evidence/temperature-refused-1440-app.png` / `W2-03-followup-evidence/temperature-refused-390-app.png` | Temperature with operating context > Excursion context > How each limit is set |
| 16 | `temperature` | `/sites/COLD-LAB-001/performance/temperature` | stocked: full test data | `W2-04-evidence/temperature-stocked-1440-app.png` / `W2-04-evidence/temperature-stocked-390-app.png` | Temperature with operating context > Excursion context > How each limit is set |
| 17 | `temperature` | `/sites/COLD-LAB-001/performance/temperature` | empty: nothing recorded yet, says so | `W2-04-evidence/temperature-empty-1440-app.png` / `W2-04-evidence/temperature-empty-390-app.png` | Temperature with operating context > Excursion context > How each limit is set |
| 18 | `temperature` | `/sites/COLD-LAB-001/performance/temperature` | refused: read refused, says so | `W2-04-evidence/temperature-refused-1440-app.png` / `W2-04-evidence/temperature-refused-390-app.png` | Temperature with operating context > Excursion context > How each limit is set |
| 19 | `coldbackup` | `/sites/COLD-LAB-001/performance/backup` | stocked: full test data | `W2-03-followup-evidence/coldbackup-stocked-1440-app.png` / `W2-03-followup-evidence/coldbackup-stocked-390-app.png` | What the chain shows > Reconstructed event chain > Backup event chains > Evidence by causal step |
| 20 | `coldbackup` | `/sites/COLD-LAB-001/performance/backup` | empty: nothing recorded yet, says so | `W2-03-followup-evidence/coldbackup-empty-1440-app.png` / `W2-03-followup-evidence/coldbackup-empty-390-app.png` | What the chain shows > Reconstructed event chain > Backup event chains > Evidence by causal step |
| 21 | `coldbackup` | `/sites/COLD-LAB-001/performance/backup` | refused: read refused, says so | `W2-03-followup-evidence/coldbackup-refused-1440-app.png` / `W2-03-followup-evidence/coldbackup-refused-390-app.png` | What the chain shows > Reconstructed event chain > Backup event chains > Evidence by causal step |
| 22 | `cold-evidence` | `/sites/COLD-LAB-001/evidence` | stocked: full test data | `W2-04-evidence/cold-evidence-stocked-1440-app.png` / `W2-04-evidence/cold-evidence-stocked-390-app.png` | What we can conclude now > Data sources · data quality, not equipment condition > Most useful next evidence |
| 23 | `cold-evidence` | `/sites/COLD-LAB-001/evidence` | empty: nothing recorded yet, says so | `W2-04-evidence/cold-evidence-empty-1440-app.png` / `W2-04-evidence/cold-evidence-empty-390-app.png` | What we can conclude now > Data sources · data quality, not equipment condition > Most useful next evidence |
| 24 | `cold-evidence` | `/sites/COLD-LAB-001/evidence` | refused: read refused, says so | `W2-04-evidence/cold-evidence-refused-1440-app.png` / `W2-04-evidence/cold-evidence-refused-390-app.png` | What we can conclude now > Data sources · data quality, not equipment condition > Most useful next evidence |
| 25 | `cold-evidence-analysis` | `/sites/COLD-LAB-001/evidence` | stocked: full test data | `W2-04-evidence/cold-evidence-analysis-stocked-1440-app.png` / `W2-04-evidence/cold-evidence-analysis-stocked-390-app.png` | Accepted records behind the conclusions > How a claim limit is set |
| 26 | `cold-evidence-analysis` | `/sites/COLD-LAB-001/evidence` | empty: nothing recorded yet, says so | `W2-04-evidence/cold-evidence-analysis-empty-1440-app.png` / `W2-04-evidence/cold-evidence-analysis-empty-390-app.png` | Accepted records behind the conclusions > How a claim limit is set |
| 27 | `cold-evidence-analysis` | `/sites/COLD-LAB-001/evidence` | refused: read refused, says so | `W2-04-evidence/cold-evidence-analysis-refused-1440-app.png` / `W2-04-evidence/cold-evidence-analysis-refused-390-app.png` | Accepted records behind the conclusions > How a claim limit is set |
| 28 | `cold-financials` | `/sites/COLD-LAB-001/financials` | stocked: full test data | `W2-04-evidence/cold-financials-stocked-1440-app.png` / `W2-04-evidence/cold-financials-stocked-390-app.png` | What happened → what it means in money > Assumptions in use > Not included |
| 29 | `cold-financials` | `/sites/COLD-LAB-001/financials` | empty: nothing recorded yet, says so | `W2-04-evidence/cold-financials-empty-1440-app.png` / `W2-04-evidence/cold-financials-empty-390-app.png` | What happened → what it means in money > Assumptions in use > Not included |
| 30 | `cold-financials` | `/sites/COLD-LAB-001/financials` | refused: read refused, says so | `W2-04-evidence/cold-financials-refused-1440-app.png` / `W2-04-evidence/cold-financials-refused-390-app.png` | What happened → what it means in money > Assumptions in use > Not included |
| 31 | `cold-assumptions` | `/sites/COLD-LAB-001/financials/assumptions` | stocked: full test data | `W2-04-evidence/cold-assumptions-stocked-1440-app.png` / `W2-04-evidence/cold-assumptions-stocked-390-app.png` | Financial assumptions |
| 32 | `cold-assumptions` | `/sites/COLD-LAB-001/financials/assumptions` | empty: nothing recorded yet, says so | `W2-04-evidence/cold-assumptions-empty-1440-app.png` / `W2-04-evidence/cold-assumptions-empty-390-app.png` | Financial assumptions |
| 33 | `cold-assumptions` | `/sites/COLD-LAB-001/financials/assumptions` | refused: read refused, says so | `W2-04-evidence/cold-assumptions-refused-1440-app.png` / `W2-04-evidence/cold-assumptions-refused-390-app.png` | Financial assumptions |
| 34 | `cold-finding` | `/sites/COLD-LAB-001/findings/00000002-0000-4000-8000-000000000176` | stocked: full test data | `W2-03-followup-evidence/cold-finding-stocked-1440-app.png` / `W2-03-followup-evidence/cold-finding-stocked-390-app.png` | Bounded conclusion > Operational context > Recommended next step |
| 35 | `cold-finding` | `/sites/COLD-LAB-001/findings/00000002-0000-4000-8000-0000000fffff` | refused: read refused, says so | `W2-03-followup-evidence/cold-finding-refused-1440-app.png` / `W2-03-followup-evidence/cold-finding-refused-390-app.png` | Bounded conclusion > Operational context > Recommended next step |
| 36 | `cold-finding-excursion` | `/sites/COLD-LAB-001/findings/00000002-0000-4000-8000-000000000170` | stocked: full test data | `W2-03-followup-evidence/cold-finding-excursion-stocked-1440-app.png` / `W2-03-followup-evidence/cold-finding-excursion-stocked-390-app.png` | Bounded conclusion > Temperature > Recommended next step |
| 37 | `ev-foundation` | `/sites/EV-LAB-001/foundation` | stocked: full test data | `W2-05a-evidence/ev-foundation-stocked-1440-app.png` / `W2-05a-evidence/ev-foundation-stocked-390-app.png` | Physical site > Operating interpretation |
| 38 | `ev-foundation` | `/sites/EV-LAB-001/foundation` | EV site with a missing role | `W2-05a-evidence/ev-foundation-missing-role-1440-app.png` / `W2-05a-evidence/ev-foundation-missing-role-390-app.png` | Physical site > Operating interpretation |
| 39 | `ev-foundation` | `/sites/EV-LAB-001/foundation` | empty: nothing recorded yet, says so | `W2-05a-evidence/ev-foundation-empty-1440-app.png` / `W2-05a-evidence/ev-foundation-empty-390-app.png` | Physical site > Operating interpretation |
| 40 | `ev-readiness` | `/sites/EV-LAB-001/foundation/readiness` | stocked: full test data | `W2-05a-evidence/ev-readiness-stocked-1440-app.png` / `W2-05a-evidence/ev-readiness-stocked-390-app.png` | Readiness and commissioning evidence > Gateway status · edge-ev-lab-001 > Connected sources > Effect on readiness and confidence |
| 41 | `ev-readiness` | `/sites/EV-LAB-001/foundation/readiness` | EV site with a missing role | `W2-05a-evidence/ev-readiness-missing-role-1440-app.png` / `W2-05a-evidence/ev-readiness-missing-role-390-app.png` | Readiness and commissioning evidence > Gateway status · edge-ev-lab-001 > Connected sources > Effect on readiness and confidence |
| 42 | `ev-readiness` | `/sites/EV-LAB-001/foundation/readiness` | empty: nothing recorded yet, says so | `W2-05a-evidence/ev-readiness-empty-1440-app.png` / `W2-05a-evidence/ev-readiness-empty-390-app.png` | Readiness and commissioning evidence > Gateway status · Gateway not read > Connected sources > Effect on readiness and confidence |
| 43 | `ev-sld` | `/sites/EV-LAB-001/foundation/sld` | stocked: full test data | `W2-05a-evidence/ev-sld-stocked-1440-app.png` / `W2-05a-evidence/ev-sld-stocked-390-app.png` | EV charging lab > What each part does |
| 44 | `ev-sld` | `/sites/EV-LAB-001/foundation/sld` | EV site with a missing role | `W2-05a-evidence/ev-sld-missing-role-1440-app.png` / `W2-05a-evidence/ev-sld-missing-role-390-app.png` | EV charging lab > What each part does |
| 45 | `ev-sld` | `/sites/EV-LAB-001/foundation/sld` | empty: nothing recorded yet, says so | `W2-05a-evidence/ev-sld-empty-1440-app.png` / `W2-05a-evidence/ev-sld-empty-390-app.png` | EV charging lab > What each part does |
| 46 | `ev` | `/sites/EV-LAB-001/ev` | interrupted service day (test data) | `W2-07-evidence/ev-interrupted-1440-app.png` / `W2-07-evidence/ev-interrupted-390-app.png` | What happened on the service day > Charging activity and site power > Needs attention > Bounded money consequence > Next step |
| 47 | `sessions` | `/sites/EV-LAB-001/performance/sessions` | interrupted service day (test data) | `W2-06-evidence/sessions-interrupted-1440-app.png` / `W2-06-evidence/sessions-interrupted-390-app.png` | Session service records > How to read the denominator > Cause remains bounded |
| 48 | `ev-evidence` | `/sites/EV-LAB-001/ev/evidence` | interrupted service day (test data) | `W2-07-evidence/ev-evidence-interrupted-1440-app.png` / `W2-07-evidence/ev-evidence-interrupted-390-app.png` | What we can conclude now > Data sources · data quality, not equipment condition > Most useful next evidence |
| 49 | `ev-evidence-analysis` | `/sites/EV-LAB-001/ev/evidence/analysis` | interrupted service day (test data) | `W2-07-evidence/ev-evidence-analysis-interrupted-1440-app.png` / `W2-07-evidence/ev-evidence-analysis-interrupted-390-app.png` | Accepted records behind the conclusions > How a claim limit is set |
| 50 | `ev-financials` | `/sites/EV-LAB-001/ev/financials` | interrupted service day (test data) | `W2-07-evidence/ev-financials-interrupted-1440-app.png` / `W2-07-evidence/ev-financials-interrupted-390-app.png` | What happened → what it means in money > Assumptions in use > Not included |
| 51 | `ev-assumptions` | `/sites/EV-LAB-001/ev/financial-assumptions` | interrupted service day (test data) | `W2-07-evidence/ev-assumptions-interrupted-1440-app.png` / `W2-07-evidence/ev-assumptions-interrupted-390-app.png` | Financial assumptions |
| 52 | `ev-finding` | `/sites/EV-LAB-001/findings/00000502-0000-4000-8000-00000000025b` | interrupted service day (test data) | `W2-06-evidence/ev-finding-interrupted-1440-app.png` / `W2-06-evidence/ev-finding-interrupted-390-app.png` | Bounded conclusion > Operational context > Recommended next step |

Where a screen appears several times, the extra rows are other states of the same screen. Screen count: 22 mock screens (12 cold-chain, 10 EV), 52 app captures at each of two widths, each with a matching mock capture.

## What to check, screen by screen

- **cold-foundation**: Two panels side by side: Physical site, then Operating interpretation. Compare size and weight with the mock.
- **cold-readiness**: Four panels in the mock order: readiness evidence, gateway status, connected sources, effect on readiness. Gateway name differs from the mock by design (real test gateway).
- **cold-sld**: Site drawing first, then "What each part does". Check the drawing is as prominent as in the mock.
- **cold**: Five panels: What happened (wide, top), Chamber temperature and Needs attention side by side, then Money consequence and Next step.
- **temperature**: Chart panel large on the left, Excursion context on the right, one wide panel below. Known difference: the app's third panel is "How each limit is set"; the mock's is "Claim boundary".
- **coldbackup**: Four panels: What the chain shows, event chain, Backup event chains, Evidence by causal step; same order and weight as the mock.
- **cold-evidence**: Three panels: What we can conclude now, Data sources, Most useful next evidence.
- **cold-evidence-analysis**: Two panels: Accepted records, then How a claim limit is set.
- **cold-financials**: Three panels: money story, Assumptions in use, Not included. Missing money must read as unknown, not zero.
- **cold-assumptions**: One panel, Financial assumptions; check it fills the page like the mock.
- **cold-finding**: Three panels: Bounded conclusion, Operational context, Recommended next step.
- **cold-finding-excursion**: Three panels: Bounded conclusion, Temperature, Recommended next step.
- **ev-foundation**: Two panels side by side: Physical site, Operating interpretation.
- **ev-readiness**: Four panels as for cold readiness; the empty case shows "Gateway not read".
- **ev-sld**: Site drawing first, then "What each part does".
- **ev**: Five panels as for the cold overview: What happened on the service day, Charging activity and site power, Needs attention, Money consequence, Next step.
- **sessions**: Three panels: Session service records (wide table), How to read the denominator, Cause remains bounded. The mock's table panel is taller.
- **ev-evidence**: Three panels: What we can conclude now, Data sources, Most useful next evidence.
- **ev-evidence-analysis**: Two panels: Accepted records, How a claim limit is set.
- **ev-financials**: Three panels: money story, Assumptions in use, Not included.
- **ev-assumptions**: One panel, Financial assumptions.
- **ev-finding**: Three panels: Bounded conclusion, Operational context, Recommended next step.

## Related Lab capture (W2-05b)

The EV charging run setup panel on the Lab page: app `W2-05b-captures/app-1440.png` and `app-390.png`, mock `mock-1440.png` and `mock-390.png`. Check the EV panel sits after the cold panel and before "What this workspace is", and has no sideways scroll.

## Mock screens with no app capture

W2 covered exactly the 22 screens above. W2-02 (cold data producer) has no screen and so no capture. These mock screens in the cold-chain and EV families have no capture because they are **not built in W2** (deferred to W5 or later):

- Domain health: `cold-health`, `ev-health`. Not built in W2.
- Site findings lists: `cold-findings`, `ev-findings`. Not built in W2.
- Work: `cold-work`, `cold-work-incidents`, `cold-work-maintenance`, `ev-work`, `ev-work-incidents`, `ev-work-maintenance`. Not built in W2.
- Recommendations and actions: `cold-recommendation`, `ev-recommendation`, `cold-action`, `ev-action`. Not built in W2.
- Scenarios: `cold-scenarios`, `ev-scenarios`. Not built in W2.
- Cooling, availability and energy comparisons: `cooling`, `availability`, `energy`. Not built in W2.

Gaps inside the 22 (no capture for these states): `cold-finding-excursion` has a stocked capture only; the EV screens `sessions`, `ev`, `ev-evidence`, `ev-evidence-analysis`, `ev-financials`, `ev-assumptions` and `ev-finding` have an interrupted-day capture only (no empty or refused); `cold-readiness` and `cold-sld` have no empty or refused case.

## Structural versus polish

- **Structural**: a panel is missing, extra, in a different order, or very different in size or prominence from the mock; or an empty or refused state is hidden. These get fixed before W5.
- **Polish**: spacing, colour, type size, wording, icons, small alignment. These go to the later UI/UX pass and do not block anything.
- If unsure, mark it structural; the coordinator will sort it.
