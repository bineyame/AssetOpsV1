# Demo script, Thursday 12 November 2026, 14:00 (build E3e, client7)

Refreshed from the client script (DS-1f, branch task/DS-1f-fill 157159d33) and the technical script (DS-1b, branch task/DS-1b-technical 46e468427), which were written against the client4 build (story day 8 Nov). This file is the one to present from today. Every figure and date below was read from the running demo on 12 Nov 2026 between 11:00 and 11:45: the API (127.0.0.1:8990) and the pages as rendered by the web app (localhost:5490). Nothing was written to the database. (Opening the Kobo 11 Nov board, which was not in the prepared list, may have stored one page; no other unlisted page was opened.)

Build: tag demo/2026-11-12-e3e, database assetops_polish_client7_test, story day S = Mon 9 Nov 2026. All times on screen are UTC.

Marker used below: **CHECK** = the live screen contradicts or changes what the old script said. Decide before 14:00 whether to say it, skip it or choose another page. The list is repeated in short at the end of Part A.

## Presenter notes, read first

1. Stay on prepared ranges. The Portfolio and the Site pages are stored and open in under half a second only for the ranges the build prepared: week 3 to 10 Nov (shown as "3 to 9 Nov"), month 12 Oct to 12 Nov, and the single story day 9 Nov, each with the All, Cost, Risks and Opportunities tabs. Any other Portfolio range composes from scratch on first open: 7 to 11 seconds for a week, up to 42 seconds for 22 days, and the page sits on its loading state meanwhile (the second open is instant). Do not change the date range on the Portfolio, and do not accept a suggestion to "try another week" live.
2. Do not pick past "as known at" times off-script. Those pages are not prepared, and historical windows read with a past cutoff can be withheld by design (the screen then says so). Use only the links in the table at the end.
3. Kobo boards are all prepared for 12 Oct to 10 Nov. Cold room and EV boards are prepared for the dates in the table. Kisiwa boards are prepared for 4, 9 and 10 Nov only; any other Kisiwa day costs 3 to 6 seconds on first open. Stay on 4 and 9 Nov.
4. add-dates ran only partly this morning, and the owner chose to present as is. Cold room and the EV depot have 10 Nov. Not added: Kobo 11 Nov, Cold room 11 Nov, Kisiwa 10 Nov. So there is no "yesterday arrives" moment today (see Step 7), and the Kisiwa live tank-dip beat has no valid night (see Step K). Do not run add-dates in the session.
5. The Portfolio week reads Kobo as 6 of 7 days assessed (5 Nov has no readings at all), with 5 of 7 days "complete readings" and 1 partial. Both wordings are on the screen; they count different things. Say "one day, 5 November, never arrived", and do not explain the two counts unless asked.
6. First open of an Opportunities or Findings page can take a second or two. Open the Portfolio, Findings, Kobo 9 Nov and the Cold, EV and Kisiwa pages once before the client joins.

---

# Part A. Client demo script (plain language)

About 33 minutes plus questions, ten steps (step 3b is optional). The banner "Demonstration · example sites and records" is on every screen. Story day S is Monday 9 November.

Four Sites, one view: a solar mini-grid (Kobo), a cold room (GreenHarvest), an EV charging depot (Depot Charging Hub) and an island diesel mini-grid (Kisiwa). Each is judged under the same four business outcomes: Grow revenue, Optimize cost and efficiency, Protect asset and capital, Assure performance and returns. Each problem goes from what the readings show, to an action with an owner, to a check that proves whether it worked.

## Step 0. Opening: four Sites, one place to look (2 min)

Open the Portfolio, week to 9 Nov (it shows "3 to 9 Nov 2026").

What you see
- The four Sites in one view, and the banner. Under the header: "Some Sites have incomplete days", then one line per Site:
  - GreenHarvest Cold Room: complete readings on 0 of 7 days (7 with too few readings, not counted).
  - Depot Charging Hub: complete readings on 1 of 1 day.
  - Kisiwa island mini-grid: complete readings on 7 of 7 days.
  - Kobo mini-grid: complete readings on 5 of 7 days, 1 with partial readings, 1 with no readings received, 5 Nov: no readings.
- "Figures on this page count days with complete readings."

Say
"This is the Portfolio: four Sites, four different businesses, one view. Everything today is example data and the screens say so. Under the title you see how many days of readings stand behind each Site. Kobo has one day, 5 November, where nothing arrived. The product says so rather than guessing."

If asked, why example data? "It lets us show a full month, problems included, without exposing a real Site."

**CHECK.** The old script said Kisiwa may read "0 of 7 days checked" and told you to explain it. It now reads 7 of 7. Drop that explanation. The cold room line (0 of 7, too few readings) is new to the script: say "the cold room reports only a short window each day, so those days are not counted for the weekly figures".

## Step 1. Portfolio: four outcomes, each Site's money on its own line (4 min)

What you see (week 3 to 9 Nov)
- Grow revenue: "At least 142.00 USD estimated income, from days with complete readings, not billed or collected". Lines: Depot Charging Hub 4.50 USD over 1 of 1 day; Kobo 137.50 USD over 5 of 7 days with complete readings, 1 with partial readings; Kisiwa not known yet. Site status: cold room Not measured yet, depot Watch, Kisiwa "No target for this outcome", Kobo On track.
- Optimize cost and efficiency: "0.00 to 15.13 USD possible extra fuel cost. At Kobo mini-grid, not added across sites. Modelled from the stored record and the declared price, not a saving." Cold room, Kisiwa and Kobo: Needs attention; depot Not measured yet.
- Protect asset and capital: "2 found on days with complete readings. Service disruptions recorded as findings, 8 early warnings counted separately, loss not priced." Kisiwa line: "Unexplained fuel on the night of 3 Nov: about 95.7 to 144.3 L, 119.57 to 180.43 USD at your declared price (a modelled range, shown on its own)." Cold room and depot Needs attention; Kisiwa and Kobo Watch.
- Assure performance and returns: "3 confirmed, from days with complete readings". Lines: Kobo ACT-001 "about 3.3 L, 4.12 USD less diesel in the one-hour trial (modelled, not metered)"; Kobo ACT-005 "about 17.00 USD a day more in estimated sales to productive users (your declared price)". "Each result's money is shown on its own and never added together." "Evidence gap at 1 site." Cold room and Kobo Watch.
- Summary tiles: 3 priority sites, 1 opportunity (Kobo daytime solar), 1 site with evidence gaps, 1 accepted action, 8 warnings not yet priced. 21 findings in all ("See all 21 findings").
- "Where management should act first" (top three): two Kisiwa "Generator may have been on longer than needed" rows (9 Nov 17:40 to 19:05 and 9 Nov 22:55 to 10 Nov 00:15), then the cold room temperature finding (from 9 Nov 16:15, Unpriced). See CHECK below.
- Charging figure: at the foot of the Portfolio, "Depot Charging Hub delivered 15 kWh in selected records; $4.50 at the recorded tariff, before costs (a what-if)". The data is there (15 kWh, 4.50 USD); I could not see the footer in the page text I rendered, so look for it at the foot of the page before the session. If it is not visible, the same 4.50 USD is the depot line on the Grow card.

Say
"Four outcomes: grow revenue, cut cost, protect assets, assure returns. Each Site's money stays on its own line. We never add a diesel estimate to sales income, and confirmed results are never combined into one total. Only like-for-like estimated income from different Sites is added, in one currency, and each Site's line stays visible. Every number can be traced to its Site and its days."

If asked
- "Why only Kobo on the cost card?" Only Kobo has a priced fuel record behind it; the card says "At Kobo mini-grid, not added across sites".
- "What is the 4.50 dollars?" 15 kWh delivered at the recorded tariff of 0.30 USD per kWh, before costs. A what-if, not money billed.
- "Why no grand total?" Different kinds of money with different certainty. Keeping them apart is what makes each one defensible.

**CHECK, Kisiwa dominates the Act-first list.** With Kisiwa now fully assessed (7 of 7 days), its 15 "Generator may have been on longer than needed" findings (all "No action agreed yet", Act now) are 15 of the 21 findings and fill the top of the list. The old script had Kisiwa unassessed, so this never appeared. Do not open the Kisiwa generator rows. Say: "Kisiwa's generator rows are a daily pattern we would review with you; its story today is the fuel night, which we come to in a moment." If a viewer asks, the Kisiwa board for 9 Nov shows 165 minutes longer than needed that day (objective MG-2 missed).

## Step 2. Kobo: a recurring generator problem, an action, a check (4 min)

Open the Kobo board for 9 Nov, then the finding, then the check page (links in the table).

What you see
- Optimize row: "Generator stayed on 200 minutes longer than needed" (200 min avoidable, 30 min unclear), "0.00 to 15.13 USD possible extra fuel cost on this day: generator on for 200 minutes delivering no power, up to about 12.1 L, counted at a generic idle fuel rate of 3.3 L/h, not measured". Fuel price: Declared at 1.25 USD per litre.
- The finding "Generator may have been on longer than needed": on 9 Nov 2026, 04:35 to 07:55 (UTC), "Open: 3 h 20 min of generator time possibly avoidable". "What limits this conclusion: only the possibly avoidable blocks are counted, as a bounded estimate from the site records, not proof of wasted fuel."
- Earlier interventions: ACT-001, Battery reserve trial, "Verified on example data". "Estimated effect of the trial (not money saved): about 3.3 L less diesel in the trial hour, 4.12 USD at 1.25 USD per litre. Goal before the trial: missed; after: met, checked over 09:00 to 10:00 on 10 Nov."
- The check page (ACT-001, Verification): target change 60 min to 0 min, critical service 0 kWh, reserve breaches 0 min, "Final outcome Verified". Earlier window 9 Nov, later window 10 Nov (06:00 to 07:00 UTC, which is 09:00 to 10:00 on the Site clock). Rule fixed in the plan before the later window was read.

Say
"The readings showed the generator on while solar and the battery could carry the load. One change to the battery reserve setting, then a check on the same hour the next day: no generator time, no customer left without power. The screen calls it Verified. The saving is an estimate per hour and says so."

If asked, "Is 4.12 USD the saving?" Per trial hour, modelled from a generic idle rate, not a fuel meter. The screen says this.

**CHECK, two things on the 9 Nov board.** (a) The Optimize row also reads "Before the change on 10 Nov, after the change: not judged yet, no day with complete readings since 10 Nov". It sits beside the Verified line and can look contradictory. Answer if asked: the trial hour was verified; the board's longer follow-up is still waiting for full days of readings. (b) The 9 Nov day carries "This result may miss newer readings" (readings arrived after the answer was worked out) and 9 Nov is a partial-readings day (Grow estimated income reads 0.00 USD over 0 of 1 day with complete readings). Skip the grey banner; do not claim the day is fully checked. The 10 Nov board (links below) reads "Fix verified, monitoring (ACT-001), 7 more days with complete readings to close" and is a cleaner place to end the step.

Presenter only, Kobo's first days: if a Kobo board shows a green monthly target and a day without readings, that is correct. Say "The monthly target was already reached; this day's readings had not arrived yet. Both are on the screen."

## Step 3. Kobo: growth from daytime solar (3 min)

Open Findings, Opportunities tab (week 3 to 10 Nov), then the daytime solar opportunity.

What you see
- "Daytime solar unused at Kobo mini-grid", state "Seen again". "Seen on 3 of 3 well-observed days, 6 Nov to 10 Nov. Not judged yet: 2 of the 5 study days have no reading." Size: not worked out yet.
- Portfolio: ACT-005, "about 17.00 USD a day more in estimated sales to productive users (your declared price)".
- Kobo board, Grow row (9 Nov): "660 kWh so far this month, on 6 of 9 days with complete readings" (target, at least 300 kWh a month: met). Potential: "Not judged yet: 2 of the 5 study days have no reading". Estimated income on the day: 0.00 USD over 0 of 1 day with complete readings, 1 partial. "Spare solar on 3 of 3 well-observed days, 2 of the last 5 days without complete readings". Price: Declared at 0.25 USD per kWh.

Say
"Kobo has solar going unused at midday. Moving the mill to midday turns that into sales, about 17 USD a day at the price you declare. Target, potential and earnings are kept apart so you can see which is which."

Presenter only: open the opportunity from Findings, Opportunities or from the Portfolio Grow card. Never take the board's "Productive-use what-if" link; it leads to a different page. If asked "how big is the opportunity?", the screen says "Size not worked out yet": we show only what the readings support.

## Step 3b. Kobo: fuel burnt while the generator idles (2 min, optional)

Kept, because the idle-fuel line is present on this build. Kobo 9 Nov board, cost row: "0.00 to 15.13 USD possible extra fuel cost on this day: generator on for 200 minutes delivering no power, up to about 12.1 L, counted at a generic idle fuel rate of 3.3 L/h, not measured", "200 min avoidable, 30 min unclear", fuel price declared at 1.25 USD per litre.

Say "Here is the diesel burnt while the generator idles. It sits on its own line: we do not add it to estimated sales or to other savings."

## Step 4. GreenHarvest cold room: the backup generator did not start (3 min)

Open the cold room board for 9 Nov (the whole day) or the analysed period 9 Nov 16:00 to 17:05.

What you see
- Analysed period 9 Nov 2026, 16:00 to 17:05. "Service affected, confidence partial, Stock may be at risk." Objective: keep the chamber between 2 and 4 C.
- Protect: "Cold room temperature outside its policy band", "Chamber temperature: Peak 4.9 C against a 4 C limit"; "Backup start: automatic start failed; started by hand". Objectives missed: stock kept saleable (above 4 C in this window) and cooling continuity (automatic start failed).
- Optimize: "3 repair visits in 60 days without a result", visits 16 Oct, 29 Oct and 9 Nov, "the automatic start failure is still open". Earlier work: WR-007 starter battery replaced and WR-008 control relay reset (both "Did not fix it"), WR-006 starter and control inspection (Not yet verified).
- "Witnessed backup start test overdue since 5 Nov." Compressor coil cleaning due 18 Nov.
- ACT-002, Witness automatic-start test, state Open (owner Maintenance lead, as in the previous script; not re-read on this build).
- On the Portfolio, "Backup generator did not start when the grid failed" is listed twice, from 6 Nov and from 9 Nov 16:00. Both read Pending (an action is agreed, not yet done). The temperature row reads "No action agreed yet", which is correct.

Say
"Twice the grid failed and the backup did not start. The technician has been out three times in 60 days. The next action is a witnessed start test, with an owner."

Presenter only: if a start-failure row on the Portfolio reads "No action agreed yet", stop; the Portfolio disagrees with the board (checked and consistent this morning: both start-failure rows Pending, ACT-002 in hand, temperature row open). If asked "what did it cost?", the temperature finding is Unpriced: the stock value is not available yet. The Portfolio shows whether someone is acting; the action itself is on the Site's Work page.

## Step 5. EV depot: a charging interruption (2 min)

Open the depot board for 3 Nov. The full day (00:00 to 24:00) or the 08:00 to 16:00 charging window.

What you see
- "Observed EV charging interruption", 3 Nov 2026, session started 08:01, connector fault 08:16, session aborted 08:16. "1 interrupted, 0 unknown of 1 session." 15 kWh delivered before the abort, complete meter record.
- Connector status: "Connector c1 was out of service for 7 h 44 min" and "Connector c1: 7 h 44 min out, 16 min unknown". The evidence tab says "16 min of connector status is missing" (Connector status missing 3 Nov 08:00 to 08:16).
- Money on the board: 4.50 USD over 1 of 1 day (15 kWh at 0.30 USD per kWh), a what-if, not billed. For comparison the normal days 20 Oct and 27 Oct read 9.00 USD (30 kWh).
- ACT-003, Investigate connector c1, state Open; the early-warning list also has "Connector inspection overdue" (PM-013) and "Charger fault and overdue inspection".

Say
"A charger dropped a session for about a quarter of an hour. The action is to investigate it, and it is done only when a full session is witnessed with no repeat fault."

Then, as the status line: "Out of service from 08:16 for the rest of the charging day; the first 16 minutes have no status reading; repair still pending." That sentence is the presenter line; it is not printed on the screen. The screen says "7 h 44 min out, 16 min unknown", which is the same fact with the 8-hour window (7 h 44 min out plus 16 min unknown equals the 8 hours from 08:00 to 16:00).

**CHECK.** The old note about "Connector c1 versus Investigate connector 2" no longer applies: the action now reads "Investigate connector c1". Remove that note. A technical viewer comparing 7 h 44 min with an 8 h window will see the 16 minutes unknown; the line above answers it. (The self-check CO-10 pinned "0 minutes unknown" and fails against this wording; Architect ruling pending.)

If asked, "What is the income?" Only the what-if: 4.50 USD for 15 kWh at the recorded tariff, before costs. The depot's board shows no income estimate beyond that.

## Step K. Kisiwa island: unexplained fuel overnight (6 min)

The tank balance, night of 3 Nov (6 pm to noon):
- In the tank at 6 pm: 869.2 L. Delivered overnight: none recorded. Burnt by the generator for the power it made: 39.1 to 47.8 L. In the tank at noon: 705.8 L. Left unexplained: about 95.7 to 144.3 L.
- "The tank sensor sent no readings from 00:45 to 02:30" (105 minutes).

Open: Kisiwa Fuel, night of 3 Nov; then the unexplained-fuel finding; then the ACT-004 check; then the Kisiwa board for 4 Nov and for 9 Nov; then the Service page for 6 Nov (links below).

What you see
- Fuel page, "Fuel balance: unexplained fuel": opening 869.2 L, recorded deliveries none recorded, modelled expected use 39.1 to 47.8 L (122.3 kWh at 0.355 L/kWh, 10 % either way), residual 95.7 to 144.3 L, "above the 40 L the check flags". Earlier nights 31 Oct to 2 Nov read "accounted for within the margin".
- Finding: "About 95.7 to 144.3 L left the tank on the night of 3 Nov (6 pm to noon) that the generator's modelled use and the recorded deliveries don't explain." "Worth about 119.57 to 180.43 USD at your declared 1.25 USD per litre (a modelled range that includes the stated margin)." "This does not say why the fuel left the tank."
- ACT-004, "Seal the tank cap, sign the dip log at every shift change, and put the tank sensor on its own protected power supply", owner Site lead. Work done and recorded 5 Nov 15:05 (tank cap sealed; sensor moved to its own protected supply). Final outcome "Fuel stayed accounted for": 3 of 3 nights, judged on the nights of 5, 6 and 7 Nov (each within minus 24.3 to 24.3 L, sensor reading all night).
- Kisiwa board, morning after (4 Nov): "About 95.7 to 144.3 L unexplained on the night of 3 Nov".
- Kisiwa board, story day (9 Nov): "No objective declared" on Grow; "Productive use not assessed: no productive-use equipment declared for this site". Declared targets: MG-2, "Supply cost per kWh: no generator time longer than needed", Missed (165 min longer than needed on this day, 165 min avoidable, 25 min unclear); MG-5, "Reliable service: all critical demand served", Met (0 kWh not served over the whole day). Two of two objectives are shown on the Assure card as "1 of 2 declared objectives met". Optimize Needs attention; Protect Watch.
- Service page, 6 Nov 09:00 to 10:00 UTC: "Service assessment: Unknown. Delivered is measured, needed is not": the power was delivered; the screen does not claim what customers needed.
- Portfolio, Protect: Kisiwa line for the 3 Nov night (see Step 1).

Say
"Every night the tank is balanced: what was in it, what came in, what the generator burnt for the power it made, and what is left. On 3 November, about 96 to 144 litres left the tank that none of that explains, worth about 120 to 180 dollars at your diesel price. The screen does not say why. The action: seal the tank, sign the dip log, keep the sensor powered. The check looked at the three nights after the change, 5, 6 and 7 November, and on all three the fuel stayed accounted for."

If asked
- "So someone took it?" The screen does not say why fuel left; it says it is unexplained and gives the margin it allowed for. The sensor gap from 00:45 to 02:30 is shown too.
- "Does Kisiwa use power productively?" No productive-use equipment is declared, so the screen says not assessed, not that it was checked.
- "Is Fuel stayed accounted for an opinion?" A rule was fixed before the check: three fully checked nights after the change, each within the stated margin, sensor reading all night. The generator's use is modelled, as the screen says.
- "What does Kisiwa serve?" Households, the cold store (ice and fish) and the water pump, while protecting the battery reserve.

**CHECK, live tank-dip beat: do not run it as written.** The links output offers "Fuel, added night 2026-11-10" and a dip of 402 L taken 11 Nov 06:00. Kisiwa 10 Nov was not added this morning, so the night list on the Fuel page ends at the night of 9 Nov and the 10 Nov night does not exist. Saving a dip against it would be saving against a night with no data. Do not do the live beat. Say instead: "Records marked Prepared example record came with the example site. A record entered through the form is listed as entered by the site admin." Showing the existing dips (REC-000024, 489 L at 18:00 on 9 Nov; REC-000025, 446 L at 06:00 on 10 Nov, listed under that Fuel page) is safe. A dip on a story night could change the story; do not save one. This removes about 2 minutes: step K is about 4 to 5 minutes.

## Step 6. Findings: every Site, one list, read three ways (2 min)

Open Findings, week 3 to 10 Nov. "Confirmed findings 21." Tabs: All findings, Cost, Risks, Opportunities. "Lens is how a finding is read, not a second object. State is a filter."

What you see
- Cost lens: 16 rows (Kobo generator 1, Kisiwa generator 15). Risks: 5 rows (cold room temperature 1, backup did not start 2, EV interruption 1, Kisiwa unexplained fuel 1). Opportunities: 1 (Kobo daytime solar).
- Banner: "So far: 3 of 4 sites fully analysed, 1 site with incomplete days" (the cold room). "So far because findings on incomplete days are not shown."

Say "This is the Monday list. All four Sites, filed as cost, risk or opportunity. Click Risks and you see what could hurt assets or service."

If asked, "Why Not assessed for priority?" Priority is not worked out for these yet; the screen says so rather than guessing.

**CHECK.** The old script said Kisiwa appears as Risk and Kobo as the Cost row. Kisiwa now has 15 Cost rows plus 1 Risk row (the fuel). Click Risks first, then Opportunities; if you open Cost, say "most of these are Kisiwa's daily generator pattern".

## Step 7. Yesterday arrives (3 min): NOT AVAILABLE TODAY

This step needs Kobo's yesterday held back and released live. add-dates was partial; the owner chose to present as is, so Kobo 11 Nov (yesterday) is not added and will not arrive during the session.

What you can still show truthfully: Kobo board for 11 Nov. It reads "We cannot judge this yet. No assessment is selected for this day, so nothing is concluded about it", "Not known yet, no readings received on 11 Nov", month target "660 kWh so far this month, on 6 of 11 days with complete readings". Say: "This is yesterday. No readings yet, and the board says so instead of guessing. When a site's gateway sends its stored readings the day is checked by the same rules as every other day; nobody rebuilds a report." Then move on. Do not say the day has arrived, and do not promise to reload it at questions. (Never present a stand-in picture as before and after of one day.)

Also show, for contrast, the 5 Nov board, "No readings received on 5 Nov" (the same wording, a day that never arrived), and the Portfolio coverage line that says so.

Presenter only, if the day looks empty and the target looks met: "The monthly target was already reached; this day's readings had not arrived yet. Both are on the screen."

## Close: what you get (2 min)

Problems found from data; an action with an owner; a check that proves it; honest gaps said out loud.

Shown today: four Sites under the same four outcomes, each Site's money on its own line. Kobo: generator time cut to zero in the trial hour (Verified), and midday solar as a growth lever. Cold room and EV depot: problems linked to open actions with owners. Kisiwa: unexplained fuel found, a control put in, and the fuel stayed accounted for on the three nights checked after the change. One Findings list across all Sites.

Not available yet, said honestly: cost per Site beyond Kobo's idle fuel (a range, not a saving); income at the EV depot beyond the what-if, and at Kisiwa; priority and confidence on findings (Not assessed); the size of Kobo's daytime solar opportunity (Size not worked out yet); productive use at Kisiwa (not assessed, no equipment declared); the asset list and Settings (Not available yet); the cold room's complete-day readings (today it reports a short window a day).

Suggested next step: a pilot on one or two of the client's own Sites, with an agreed Verified result as the measure of success.

Be ready for (your own answers): pricing; data ownership; connecting real equipment; how many Sites can go live in a pilot. "Simulator Lab" in the menu is where this demonstration's example data is generated.

## Part A: what changed against the old script (short)

Dates moved +1 day: story day 9 Nov; Kobo finding 9 Nov 04:35 to 07:55; trial windows 9 and 10 Nov; cold room failure 9 Nov, visits 16 Oct, 29 Oct, 9 Nov (the old 28 Oct is now 29 Oct), test overdue since 5 Nov, rows from 6 Nov and 9 Nov 16:00; Kisiwa fuel night 3 Nov (not 2 Nov), check nights 5, 6, 7 Nov, service hour 6 Nov. EV day stays 3 Nov. Figures that did not change: 0.00 to 15.13 USD, 4.12 USD, 17.00 USD, 95.7 to 144.3 L, 119.57 to 180.43 USD, 869.2 and 705.8 L, 39.1 to 47.8 L, 4.50 USD, 15 kWh. Figures that changed: Grow income 139.16 to 142.00 (Kobo 137.50 plus depot 4.50); Kobo month target 556.7 kWh on 2 of 8 days to 660 kWh on 6 of 9 days; Kobo coverage "5 of 7 days assessed, 4 and 6 Nov not assessed" to "5 Nov: no readings"; Kisiwa coverage 0 of 7 to 7 of 7; opportunity "1 of 1 well-observed days, 4 of 5 no reading" to "3 of 3, 2 of 5"; warnings 7 to 8; priority sites 2 to 3; findings count 21.

CHECK list in short: (1) Kisiwa's 15 generator findings now dominate the Portfolio top and the Cost lens. (2) Kobo 9 Nov board shows "after the change: not judged yet" and a "may miss newer readings" banner next to Verified. (3) Step 7 cannot run live; Kobo 11 Nov is not added. (4) The Kisiwa live tank-dip beat points at night 10 Nov, which does not exist. (5) EV 7 h 44 min out and 16 min unknown (CO-10, ruling pending). (6) The Portfolio footer 4.50 USD line was not seen in my render; verify on screen. (7) Cold room reads complete readings on 0 of 7 days.

---

# Part B. Technical script (developer edition, plain language)

The mechanism behind each beat. The full code-reference version (file and line anchors, diagrams, the worked Portfolio numbers) is Docs/demo-sprint/demo-script-technical.html on branch task/DS-1b-technical (46e468427). Its line numbers were taken at plan2 main d0bc51009 and its worked examples come from the client4 build; I did not re-verify code references against the E3e code (tag demo/2026-11-12-e3e, 385206cb7). Treat the file and line anchors as approximate and say so if asked. What follows is the figure refresh and the mechanism notes, using the new numbers.

## B0. How the build works (unchanged)

Readings come in through the ingest path as accepted evidence with an outbox event; a scheduled tick (one Site at a time, stages in a fixed order) turns them into assessments, Findings, threads, nightly fuel balance windows and day snapshots; composers build each page from stored rows; a response store keeps each page under a watermark (a count of change rows) and a code version, so an unchanged page is a stored hit. The demo's serve loop ticks every two minutes. Nothing on the product path imports the simulator (guard: dependency-direction).

Today's serving setup: shared range and "period-read kinds" for the mini_depth pages are on in serve. The prebuild stage re-requests the 75 listed routes each tick, so they are hits (all 75 warm, at most 0.42 s). Anything not on the list composes on first open and is stored (second open 0.1 to 0.2 s).

Measured on this build (E4d, quiet machine): unlisted Kobo board first open 2.2 to 3.6 s; unlisted Kisiwa board 1.6 to 3.4 s (up to 6.9 s under load); unlisted Portfolio week 7 to 11 s; 3-day range 9.6 s; 22-day range 42 s. Hence the presenter notes. The period-read parity run: 100 cases, 0 mismatch, 0 unstable, both with and without the four mini_depth kinds. Self-check: 54 rows, 53 pass, 1 fails (CO-10, see B5).

## B1. Time model (unchanged)

Three clocks: when it happened, when the system recorded it (known at), and the request's cutoff k. Evidence is read up to the Site's evidence cutoff; a thread's lifecycle is read up to k, so an action agreed after the last reading still shows as Pending (D-E4.2). Today the Portfolio reads "Latest information, as of 12 Nov 2026, 08:00", and some Site pages carry their own watermark (Cold room "information up to 12 Nov, 07:45:33"; the EV depot's last committed reading is 10 Nov 16:00). Do not pick past "as known at" times off-script: historical windows read with a past cutoff can be withheld by design (HISTORICAL_CURRENT_CLAIM).

## B2. Portfolio numbers on this build (week 3 to 10 Nov, shown 3 to 9 Nov)

- Coverage: status PARTIAL. Kobo's gap list is one day: 5 Nov, UNASSESSED, reason NO_READINGS, text "6 of 7 days assessed, 1 day not available yet". Kisiwa 7 of 7 checked, no gaps. Day-snapshot totals over the estate: 22 expected days, 13 complete, 1 partial, 7 low, 1 no data.
- Grow income "At least 142.00 USD": Kobo 137.50 USD over 5 of 7 complete days (1 partial) plus Depot 4.50 USD over 1 of 1 day, each rounded then summed, one currency; "At least" because Kisiwa is "not known yet" (declared absent) and Kobo is not fully checked. (Old build: 139.16.) Kobo 9 Nov day alone reads 0.00 USD (9 Nov is a partial day).
- Optimize "0.00 to 15.13 USD": Kobo lead finding, 12,000 s idle (200 min), 3.3 L/h generic default, multiplier 1.10, so 12.1 L times 1.25 USD per litre is 15.125, rounded outward to 15.13; low end 0.00. One priced Site only, so shown as "At Kobo mini-grid, not added across sites".
- Protect "2 found on days with complete readings": cold room and depot threads (ACTION_IN_HAND). Kisiwa's fuel thread is excluded from the count by its mechanism (UNEXPLAINED_FUEL). 8 warnings (old build 7).
- Protect fuel line: night 3 Nov, residual 95.657 to 144.343 L shown 95.7 to 144.3; times 1.25 gives 119.57 to 180.43 USD.
- Assure "3 confirmed": ACT-001 (priced total 4.125 USD, shown 4.12, half-even), ACT-005 ((110.00 minus 42.00) kWh a day at 0.25 = 17.00 USD a day), and Kisiwa's fuel thread (RESOLVED_MONITORING). Never summed; summary.combined_value is null with state NOT_COMPARABLE.
- Pulse tiles: priority sites 3 (cold, depot, Kisiwa; Kisiwa now counts because its 15 generator rows are Act now), opportunity 1, evidence gap sites 1, accepted actions 1, warnings 8.
- Rows: 21 total. Kisiwa generator 15 (Act now, "No action agreed yet"), cold temperature 1 (Act now, No action agreed yet, OPEN), cold start failure 2 (Act now, Pending, ACTION_IN_HAND), EV interruption 1 (Unpriced risk, Pending), Kobo generator 1 (Monitor, Verified, RESOLVED_MONITORING), Kisiwa fuel 1 (Monitor, Verified). The same thread ids and states appear on the Site boards (E4d item 5a: Portfolio and boards agree; coherence rule COH-13, self-check row F-COH).
- Footer: stored line 15.000 kWh times 0.30 = 4.50 USD (estimated, eligible complete intervals), window 3 Nov 08:00 to 16:00 UTC.
- Money rules (unchanged): no combined total of different money kinds; verified results one line each, never summed (outcomes/credit.py, owner rule FUEL-1 A2); only like-for-like estimated income is summed, one currency (OWN-1104 R10; COH-17 checks the total equals the sum of the shown rounded lines).

## B3. Kobo: Finding to Action to verification

Thread lifecycle: OPEN, ACTION_IN_HAND, CHANGE_APPLIED, RESOLVED_MONITORING, CLOSED (after clean days); REOPENED on an ineffective result; RECURRED on a new occurrence. The Kobo thread today is RESOLVED_MONITORING ("7 more days with complete readings to close" on the 10 Nov board). Finding (3 revisions, version d657f613, claim level CANDIDATE_AVOIDABLE): 9 Nov 04:35 to 07:55 UTC, bounded to the candidate segments only; 246 accepted records. Verification plan reserve-trial-verification-1: windows 9 Nov 06:00 to 07:00 UTC versus 10 Nov 06:00 to 07:00 UTC; rule "4 times later seconds at most 3 times baseline seconds"; baseline 3600 s avoidable, later 0; guardrails: critical unserved energy 0 kWh, below-reserve 0 s (five-minute sampled, so not continuous proof), terminal SOC 77.36 percent both, comparability bands (demand 15 kWh within 10 percent, solar 48 kWh within 10 percent, start SOC 63.11 percent within 2 points, 12 of 12 slots, one coherent registered-simulation source per window). Outcome VERIFIED, recorded 10 Nov 13:00 by service:verification-evaluator; states "no causal or savings claim". Fuel effect 3.3 L, 4.12 USD is a per-trial-hour model.

Why the 9 Nov board looks stale (CHECK above): the day state is STALE_PROJECTION with finding reasons SCHEDULE_STOPPED and SITE_VISIT_STALE; the board shows "may miss newer readings" until the day is analysed again. The follow-up line "after the change: not judged yet" waits for a day with complete readings after the change; 10 Nov is partial. Both are honest limits, not faults, but they sit awkwardly beside Verified.

## B4. Kobo growth and the missing day

Opportunity thread PRODUCTIVE_USE_HEADROOM: state RECURRED ("Seen again", effective 3 Nov, last day 10 Nov), study OPP-000009 over 6 to 10 Nov, 3 assessed of 3 eligible days, headroom "not worked out yet". Outcome map moves MG-1 and is checked against MG-2 and MG-5, so a sales gain is not read in isolation from supply cost and reliable service. Kobo's 5 Nov board: "No readings received on 5 Nov"; day grade NO_DATA; WK-GAP check: missed 5 Nov, partial 9 Nov, complete 3, 4, 6, 7, 8 Nov. The month target counts complete days only: 330 kWh by 5 Nov (3 of 5 days), 660 kWh by 9 Nov (6 of 9 days).

## B5. Cold room and EV

Cold: temperature excursion peak_observed 4.9 C against the 4 C limit, analysed period 9 Nov 16:00 to 17:05 (the board reads the whole window with the evidence from the latest selected window inside it; week read: 7 analysed periods). Start-failure threads 24250aae (both rows) ACTION_IN_HAND; temperature thread 7ff2183c OPEN with no action. "Stock may be at risk" is a frontend word (POTENTIAL_PRODUCT_EXPOSURE), not in the Cold JSON.

EV: 3 Nov fault, 08:01 session start, 08:16 fault and abort; consequence 15 kWh times 0.30 = 4.50 USD (repeated several times on the board); normal days 9.00 USD (30 kWh). Thread e9a9d085 ACTION_IN_HAND. Connector availability: 7 h 44 min out plus 16 min unknown over the 08:00 to 16:00 window; the 16 minutes are the gap before the first status reading. The self-check row CO-10 expects 0 minutes unknown and fails with "7 h 44 min out and 16 min unknown on 3 Nov"; the wording is shown on the board warning and the contributor line, and an Architect ruling is pending. Say this openly if a developer spots it: it is a known open item, not a hidden fault.

## B6. Kisiwa fuel night

Window: 18:00 to 12:00 next day; opening reading searched 17:30 to 18:00, closing 12:00 to 12:30; the product checks the night once the window plus 30 minutes has passed and the tank sensor's data has arrived. For the night of 3 Nov:

    drop          = opening minus closing    869.2 minus 705.8 = 163.4 L
    use_low       = 9/10 of loaded litres    39.1 L
    use_high      = 11/10 of (loaded + idle hours x rate)    47.8 L
    margin        = 2 x a (a = 10 L, generic default)    20 L
    residual_low  = drop + D minus D_tol minus use_high minus margin    about 95.7 L
    residual_high = drop + D + D_tol minus use_low plus margin    about 144.3 L   (D = deliveries = 0)

Low end at or above 40 L, so the state is UNEXPLAINED. Generator use 122.3 kWh times 0.355 L/kWh. Sensor gap 00:45 to 02:30 (105 min). Verification rule fuel-residual-within-band-1: from the action's effective time, the first 3 complete nights decide; a night passes when residual_low is at most 0, residual_high at least 0, and the sensor gap is 0 minutes. Nights 5, 6 and 7 Nov each read minus 24.3 to 24.3 L with readings all night; all pass, so outcome "Fuel stayed accounted for". Action effective after the work request WR-000026 (5 Nov 15:05).

Declared-absent rule: Kisiwa declares no productive-use equipment, so productive_kwh is declared absent on every day: out of the day's grades, never a gap, never priced, never summed. Kisiwa Grow reads "No target for this outcome" and its income "not known yet".

Kisiwa board 9 Nov reads objectives MG-2 (Missed, 165 min) and MG-5 (Met, 0 kWh not served). Cells: Grow no objective declared, Optimize needs attention, Protect watch, Assure no objective declared.

Operational records and live dip: a tank dip saved through the form is a work record written by service:operator-entry; the next tick reassesses the newest night in the base set and writes a new window revision (record ids are part of the input digest). The dip does not move the residual; opening and closing come from the sensor. **Today the beat is off**: the night offered by the links output (10 Nov) is not in the data, because Kisiwa 10 Nov was not added (the owner chose to present as is after the partial add-dates). The latest night present is 9 Nov (a story-adjacent night; dips REC-000024 and REC-000025 exist).

## B7. Findings list and the lens

Lens flags COST, RISK, OPPORTUNITY come from the outcome map's categories per mechanism; they are a view, not a second object. Counts on this build: COST 16, RISK 5, OPPORTUNITY 1 (21 findings plus the one opportunity row; the opportunity is listed separately under Opportunities). The 15 Kisiwa generator findings are one per generator period over 4 to 10 Nov, each a separate Finding with its own thread; none has an action, so they all read No action agreed yet.

## B8. Late data ("yesterday arrives")

The mechanism the beat would show: a write appends an outbox event; the event register maps the event type to Site-local days; snapshot rows for those days are marked dirty; the chain_snapshots stage rebuilds them and appends a revision only if the fingerprint changed; the same write commits a chain_input_change row, moving the watermark, so stored pages for the Site miss and are composed again at the next prebuild. add-dates drives this for a missing date (about 20 minutes per date for all four Sites together, plus the finish check). Not run today: the build is presented as is, with Cold 10 Nov and EV 10 Nov added, and Kobo 11 Nov, Cold 11 Nov and Kisiwa 10 Nov missing. Kobo 11 Nov shows the honest empty-day state (no assessment selected; no readings received).

## B9. Guards and the self-check

54 self-check rows on this build: 53 pass, 1 fails (CO-10 EV unknown minutes, ruling pending). New rows pass: WK-GAP, WK-FILL, KISIWA-COHORT, F-COH, F-COH3, KIS-2, KIS-4, KIS-6, KIS-7, KIS-11, KIS-OV. Parity: 100 cases, 0 mismatch, 0 unstable, with and without the four mini_depth kinds. Prebuild: 83 requests, all hits across the last ticks; change marks unchanged between ticks (stored 0, race 0).

## B10. Known limits to state

- Unlisted ranges and days compose on first open (numbers in B0).
- The prebuild duration is not readable from the serve log (the log line is truncated at code_version); the 120 s bound is inferred from tick timing.
- Rendered-page items verified here only through the pages in a headless browser and the API, not on screen with a person: the Portfolio footer line, the "n of m days analysed" money label, and lens chips (this script's author rendered the Portfolio, Kobo, Cold, EV, Kisiwa and Findings pages; the footer line did not appear in the text I captured).
- A technical viewer may notice: Kobo day 9 Nov is a partial day; Cold room reads 0 of 7 complete days; the EV 16 minutes unknown (CO-10).
- Code references in the DS-1b html were not re-verified against E3e.

---

# Links (this build, web localhost:5490; all prepared, warm)

Use these exact links, not today's date. Prefix each with http://localhost:5490.

| Step | Page | Path |
|---|---|---|
| 0, 1 | Portfolio, week to S | /portfolio?from=2026-11-03T00:00:00Z&to=2026-11-10T00:00:00Z |
| 6 | Findings, week | /findings?from=2026-11-03T00:00:00Z&to=2026-11-10T00:00:00Z |
| 3 | Findings, Opportunities tab | /findings/opportunities?from=2026-11-03T00:00:00Z&to=2026-11-10T00:00:00Z |
| 2, 3, 3b | Kobo board, day S (9 Nov) | /sites/KOBO-001?date=2026-11-09 |
| 2 | Kobo board, 10 Nov (trial after) | /sites/KOBO-001?date=2026-11-10 |
| 2 | Kobo finding | /sites/KOBO-001/findings/18a6e5e9-3d0e-4da5-bd39-1e275d57c568 |
| 2 | ACT-001 verification | /sites/KOBO-001/actions/e4d17e1a-b561-4fe1-92d5-6fcd60b03135/verification |
| 7 | Kobo board, 5 Nov (no readings) | /sites/KOBO-001?date=2026-11-05 |
| 7 | Kobo board, 11 Nov (yesterday, empty) | /sites/KOBO-001?date=2026-11-11 |
| 4 | Cold room board, failure day 9 Nov | /sites/COLD-LAB-001?from=2026-11-09T00:00:00Z&to=2026-11-10T00:00:00Z |
| 4 | Cold room, analysed period | /sites/COLD-LAB-001?from=2026-11-09T16:00:00Z&to=2026-11-09T17:05:00Z |
| 4 | Maintenance (optional) | /maintenance?from=2026-10-12T00:00:00Z&to=2026-11-12T00:00:00Z |
| 5 | EV depot board, fault day 3 Nov | /sites/EV-LAB-001/ev?from=2026-11-03T00:00:00Z&to=2026-11-04T00:00:00Z |
| 5 | EV depot, charging window | /sites/EV-LAB-001/ev?from=2026-11-03T08:00:00Z&to=2026-11-03T16:00:00Z |
| K | Kisiwa Fuel, night of 3 Nov | /sites/KISIWA-001/performance/fuel?night=2026-11-03 |
| K | Unexplained-fuel finding | /sites/KISIWA-001/fuel-findings/459c169f-79f9-47de-9cbf-fae025a4502e |
| K | ACT-004 fuel verification | /sites/KISIWA-001/domain-actions/f9889904-516b-4c65-9494-6f56af6c3fc5/fuel-verification |
| K | Kisiwa board, morning after (4 Nov) | /sites/KISIWA-001?date=2026-11-04 |
| K | Kisiwa board, day S (9 Nov) | /sites/KISIWA-001?date=2026-11-09 |
| K | Kisiwa Findings, story nights | /sites/KISIWA-001/findings?from=2026-10-31T00:00:00Z&to=2026-11-11T00:00:00Z |
| K | Kisiwa Service, 6 Nov 09:00 to 10:00 UTC | /sites/KISIWA-001/performance/service?from=2026-11-06T09:00:00Z&to=2026-11-06T10:00:00Z |

Do not use: Kisiwa Fuel night 2026-11-10 and the 402 L live dip (night does not exist); any other Kisiwa day; any other Portfolio range.

# Checklist before the client joins

1. Open the Portfolio week once and wait for all four cards. Scroll to the foot and confirm the "$4.50 at the recorded tariff" line is visible (or note the depot line on the Grow card).
2. Open once each: Kobo 9 Nov, Findings, Cold 9 Nov, EV 3 Nov, Kisiwa Fuel 3 Nov.
3. Confirm on screen: Portfolio start-failure rows read Pending and the temperature row reads "No action agreed yet"; EV row reads Pending.
4. Decide on the CHECK items above; at minimum, skip the live tank dip, skip Step 7's "arrival", and avoid opening Kisiwa's generator rows.
5. Do not change the date range; do not run add-dates in the session.
