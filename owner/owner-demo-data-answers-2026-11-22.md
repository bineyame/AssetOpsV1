# Owner answers, 22 Nov 2026 (verbatim choices) - DD demo-data spec

- Q1 readings span: "1 Jul – 6 Nov (Recommended)".
- Q2 months of books: "Four: Jul–Oct (Recommended)".
- Q3 serving: "One at a time (Recommended)" - one operator on the demo address; the coordinator switches to match the prospect.
- Q6 Kobo kit: "Accept, Kobo at 36 kW (Recommended)" - FG Wilson P50-3 (36 kW prime, its own published fuel curve) and 42 Pylontech US5000 (191.5 kWh usable); unpublished values labelled Assumed with their basis.
- Q4 (first build ~4.4 h, cap 8 h) and Q5 (Kobo battery wear cost Not available yet): Architect defaults stand.
- DD rev 2 Q7, Kobo no-load fuel: "0.62 L/h, Assumed (Recommended)" - fitted to the FG Wilson P50-3 sheet's three stated points; replaces owner-fuel-scope-2026-11-07.md Q2's 3.3 L/h for Kobo's new kit.
- DD rev 2 Q8, demo done: "Yes, after Q11 and Q12 (Recommended)".
- DD rev 2 Q9, bills: "Bills follow the meter (Recommended)" - story figures move with the simulation, checked by direction, never tuned.

## D-DD.76 tank sizes (later the same day)

Asked: "Accept these tank sizes?" (Kobo 2,500 L, Kisiwa 5,000 L, Mto 1,000 L, starting half full; the 400 L was a template placeholder.)
Owner answer: "Accept (Recommended)".

## B-1031 / CN-0412 (later the same day)

Context: simulated honestly, Thika's chamber peaks at 4.05 °C on 6 Oct; B-1031 never exceeds 5 °C, so C-DD6's clause behind credit note CN-0412 fails.
Owner answer: "Change the event (Recommended)" — keep the room's declared physics; the Architect resizes the incident so it really breaches 5 °C, computed from the room model, not tuned.

## D-DD.92 Kobo fuel story (later the same day)

Context: honestly simulated, Kobo's declared plant (60 kW PV, 191.5 kWh battery, 35/90 % dispatch) burns about 628 L in October against the story's 1,180 L; candidate saving about 42 L (bridge about -$52) instead of 330 L (-$412.50).
Owner answer: "Revisit a plant figure" (keep a larger fuel story by correcting a declared plant figure to what the real site has; owner supplies or confirms the figure; nothing fitted to the story).
Follow-up asked: "Kobo plant figures: which can you give real values for?" (solar kWp, start/stop SOC, load profile are template/assumed; generator and battery are from datasheets).
Owner answer: "None: have the Architect propose" (the Architect proposes which template value is weakest and a defensible typical value, labelled Assumed, for the owner to approve).

## D-DD.97 Kobo load and D-DD.98 EV depots (later the same day)

Asked (D-DD.97): evening household peak moved from 16:00-20:00 (test-fixture copy) to start at 18:00, Assumed (Hartvigsson & Ahlgren 2018); October fuel ~634 L, saving ~25 L, bridge ~-$31; no honest figure reaches 1,180 L.
Owner answer: "Approve 18:00 peak (Recommended)".
Asked (D-DD.98): with full buses unplugged and rotated, Kasarani with a charger out ends 2 buses short a night (~7 missed departures, ~$840 penalties) instead of the scenario's 1 (~2, $240); readings stand unless the owner objects.
Owner answer: "Readings stand (Recommended)".

## D-DD.144 cold-chain energy (later the same day)

Asked: keep the rooms and rebuild the scenario's energy model from the metered kWh (1,304 kWh + 0.055 kWh per crate-day; Mwea ~$315, Thika ~$354, Kirinyaga ~$423 and ~+14 %; repair still beats replace by ~+$150 net), +1.0 u to restate everywhere?
Owner answer: "Approve rebuild (Recommended)".

## D-DD.147 / D-DD.148 Kisiwa (later the same day)

Asked (D-DD.147): accept simulated Kisiwa figures (Oct diesel ~904 L vs story 2,400; fuel cost ~1,175 vs 3,120; result ~+1,695 vs -250; Mto ~32 L vs 320)? Owner: "Accept simulated (Recommended)".
Asked (D-DD.148): the 30 Oct failure costs backup, not supply (GEN-KS-02 and the battery carry the evening); "nothing avoidable" becomes "nothing material avoidable" (~20 min after sunrise, ~2-3 L)? Owner: "Accept (Recommended)".

## D-DD.150-152 (23 Nov, early)

Asked (D-DD.151/150): Kisiwa ~a tenth of generator time in Aug/Oct charges the battery while the sun could carry the load (~87 in Oct, no longer "nothing avoidable"); GEN-KS-02 evening load ~70 % not 95 %; Mto's 32 L after the trip projected-avoidable (~40); repair beat unchanged. Owner: "Accept (Recommended)".
Asked (D-DD.152): Kobo may show 12 L unexplained fuel in Jul/Aug (no generator use) until an absolute tolerance floor from a sourced sensor accuracy is built. Owner: "Fix before demo".

## Budget check (23 Nov)

Context given: with simulated fuel, Lakeside's Portfolio headline moved from -$852 behind plan to +$2,135 ahead (fuel $2,007.70 vs target $4,240; actual contribution ~1,443 -> 4,430); the plan side is unchanged and may have been typed on the same old fuel assumptions.
Owner: "have the architect check the budget"
Follow-up asked (DRAFT D-DD.166): replace Lakeside's typed fuel budget with a run-rate rule (Jul-Sep average fuel use + 10 % contingency at the declared price, Assumed); Portfolio headline about -$196.60, Kobo -$389.50, Kisiwa +$312.90, Mto -$120.00; +1.75 u as DD3d.5.
Owner answer: "Approve run-rate rule (Recommended)".
