# Owner inspection checklist

**Status: Not approved: awaits owner inspection.** Open `index.html` (double-click, or `python3 -m http.server 8790 --bind 127.0.0.1` in this folder and browse to `http://127.0.0.1:8790/`). Use **Review notes** in the top bar to leave a note per screen; **Export review notes** saves them with the full screen inventory.

## A. Decisions for the owner

1. **Default landing page**: decision home (`#/decide-lakeside`) instead of the v7.0 Portfolio. Accept / keep v7.0 default.
2. **Menu label** "Portfolio" shown as "Operations view". Accept / revert.
3. **Optimize card period note** on the Operations view ("one generator finding's exposure on the last day of the selected window, not a total for the period"). Accept wording / prefer hiding the figure on multi-day windows.
4. **Two demo estates side by side** (v7.0 screens: Kobo / GreenHarvest / Depot; decision screens: Lakeside / Harvest / Metro). Accept for now / re-base the v7.0 screens on the Layer 4 operators in a later revision.
5. **Role emphasis** reorders and highlights panels only (numbers fixed). Are the role orders right? (CEO: what to do first; COO: crews; CFO: coverage; CCO: demand.)
6. **Plain-language rewrites** of manifest reasons (CHANGE-REGISTER §5.7). Accept.
7. **Proposed verification tests** for Harvest (Kirinyaga repair) and Metro (Embakasi schedule), marked "Proposed in this mock-up" because the manifest has a plan only for Kobo. Accept / ask the Architect to add them to the manifest.
8. **Pilot page**: price not shown; four-week outline labelled "Proposed". Accept / supply wording.
9. **Review notes storage** separate from v7.0 notes. Accept / share one store.
10. **Open audit items** O1–O7 in `browser-audit.md` (phone menu, tab fade, screen-reader test). Which must be fixed before approval?
11. **Super-off-peak and depot maintenance** now in the EV figures (plan $38,520.80, actual $41,705.12, $32.03 per departure). Accept.

## B. Things to click (about 15 minutes)

1. Decision home: switch **View as** CEO → COO → CFO → CCO; check the numbers never change.
2. Click any underlined money figure; check the evidence drawer (records, arithmetic, coverage, provenance); press Escape.
3. **Why off plan**: check the steps reconcile from plan to actual and the "not explained yet" steps are visible; click a step to reach the site.
4. Site economics: Mto (energy to cash), Mwea vs Kirinyaga (room or equipment), Embakasi (peak share).
5. Comparators: Kobo generator (rejected reserve option and its failed safeguard; replay figures marked "Design value"), Mto inverter (contract rights, 21-day deadline, do nothing "cover lost after 27 Nov"), Embakasi (cheapest bill rejected because 3 buses leave short), Thika (insurance below deductible), Kasarani (3-night stop-gap, $90 in total, restore 9 Nov).
6. **Plan and budget** (Lakeside): set the budget ($5,000 / $6,500) and the letter-of-intent answer (Yes / No). Check all four cases: $5,000+Yes claim and wait +$6,096; $5,000+No claim and wait, huller lost, +$2,556; $6,500+Yes claim and wait still +$6,096; $6,500+No buy now +$3,546 (against +$2,556). The alternative inverter path is always shown beside the chosen one. More budget never lowers the result.
7. **Proof it worked**: three separate "Not yet" answers.
8. **Pilot request**: submit the form; only an example toast appears.
9. Switch **Operator** to Harvest Cold Network and Metro Bus Depots and repeat 1 and 3 (coverage now shows 97.8% and 99.3%). On **Plan and budget** they show a single budget case: the budget and letter-of-intent controls exist only for Lakeside.
10. Menu **Operations view**: the v7.0 Portfolio with the new banner and Optimize period note; open two or three other v7.0 screens to confirm they still work.
11. Phone width: narrow the browser to about 390 px; check the decision home and a comparator (options become cards).
12. Read `walkthroughs.md` and try one seven-minute run.
