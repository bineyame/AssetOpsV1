# P6: each change valued against doing nothing (proposal for the owner)

**DRAFT, awaiting owner P6.** Architect (Claude), 21 Nov 2026. This proposal is for your day-14 sitting. Nothing is built from it until you approve it.

## What exists today, and what it gives

The deep-dive shows an executive their month against their own target, with the gap split by heading and every figure labelled by its source. When the team agrees a change, it is recorded under the executive's name, with an owner and a due date. It then appears under "Actions in hand". The screen does not value that change. It says so in its "Decisions" panel ("Not available yet") and in the plan-value tile.

The season re-run built this week (spike K) replays a season's readings under each generator setting at Kobo, and checks every setting against doing nothing on four service checks: no more unmet demand, no more dips below the reserve, starts within the maker's limit, and a full battery charge at least once a week. On the simulated season, all 14 settings pass. That shows the settings do no harm, but it does not say which setting to choose.

## What is added: the choice, in money, against doing nothing

```
 Kobo · Generator stop setting                   Simulated: re-run on a simulated season, not yet on Kobo's own readings
 ┌────────────────────────────┬──────────────┬──────────────┬───────────────────────────────┐
 │ Option                     │ Fuel a month │ Over 12 mo.  │ Why                           │
 ├────────────────────────────┼──────────────┼──────────────┼───────────────────────────────┤
 │ Doing nothing (stop 90 %)  │ —            │ —            │ the comparison                │
 │ Stop at 70 %               │ 212.8 L less │ [value]      │ recommended / acceptable / …  │
 │ Stop 90 %, reserve 25 %    │  59.7 L less │ [value]      │ dawn: 11 of 61 days below 35 %│
 └────────────────────────────┴──────────────┴──────────────┴───────────────────────────────┘
 Chosen by: [the executive, by name and date]        Verified: [after the 14-day trial]
```

1. **What the executive sees.** One decision for each problem. Doing nothing always comes first, as the comparison. Every setting that was tried is listed, with:
   - the fuel it saves;
   - the extra work it puts on the battery;
   - its value over 12 months, net of its one-off cost;
   - for a rejected setting, the reason it was rejected.

   The early-morning battery readings appear beside each setting as information. The system recommends one setting. A person chooses (or chooses none), and the choice is kept under their name.
2. **How a setting is valued.** The month is worked out twice from the same factors that make up contribution: once with the setting, once without it. The value is the difference, carried over 12 months, less the one-off cost of making the change. Each quantity has one figure, worked out by the model and labelled by its source. It reads **Simulated** until the re-run uses the operator's own readings. No figure is typed in by hand. A missing input reads "Not available yet", naming the record that would fill it. For Kobo today the fuel saved can be shown, but the 12-month value reads "Not available yet" until someone states the battery wear cost.
3. **How the chosen change is verified later.** The prediction is frozen when the choice is made. The setting is changed through an Action with an owner. Then 14 comparable days before the change are set against 14 days after it:
   - did generator running after the battery was full fall as predicted?
   - did the four service checks hold?

   The money check follows when the fuel invoices arrive. Working and money are reported separately and never merged (units 6d, 6e, then 8a).

## The defaults you can accept, each with its alternative

| # | Question | Default (proposed) | Alternative |
|---|---|---|---|
| 1 | Who chooses | The operator's executive, by name and date; "none" is a valid choice | Also the finance lead |
| 2 | Battery wear cost, which Kobo has not given | "Not available yet": fuel saved is shown, the 12-month value is not | You state a typical battery wear cost for now, labelled "assumed" (as you accepted for the battery type). Kobo's value then shows (+0.5 unit) |
| 3 | Twelve months from a 61-day re-run | 12 × the re-run's average month, saying so | Monthly figure only, until a full year has been re-run |
| 4 | Choosing among settings that all pass | The highest value. Among settings within 10 % of it, the one nearest today's setting. The dawn readings are shown but never decide | The dawn readings break near-ties; or no recommendation, and the executive picks from the top three |
| 5 | Some settings cannot be valued (an input is missing) | No recommendation until every passing setting has a value | Recommend among the valued settings, saying some were not valued |
| 6 | The one-off cost of a change | Stated by the site manager or finance lead, with its basis; doing nothing costs 0 | Taken from contractor quotes only (unit 6g) |
| 7 | When nothing beats doing nothing | It says so: "Doing nothing is worth more than any setting tried" | None |

The mock-up's Kobo decision still shows the old figures (+$2,916.00 as a design estimate, and the reserve setting rejected at dawn). Under your one-figure rule and the service checks you accepted, those figures become the model's own figures, and the reserve setting becomes "passes; dawn readings shown". That restatement is unit 0K4m's.

**Size and order:** 6a, the records (3 units), then 6c, the valuation (3 units). Unit 6c also needs spike K's service-check code (0K4d), which is in review. The specs are `specs/6a-decision-records/spec.md` and `specs/6c-option-evaluator/spec.md`, both drafts.
