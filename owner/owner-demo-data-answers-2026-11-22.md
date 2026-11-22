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
