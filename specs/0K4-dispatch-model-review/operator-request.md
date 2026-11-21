# Operator data request

Architect (Claude), 2026-11-21 (D-0K4.18). No operator data request existed. This file is it. It starts with the
general mini-grid asks of the design pack and adds Kobo's items from the 0K4 review (owner default 4). The coordinator
sends it and records what arrives. Nothing in the build waits on it except the final check against Kobo's own records
(D-0K4.14).

## General mini-grid asks (by reference)

`Docs/demo-sprint/product-direction-layer4/design-appendix.md` §5 lists them: EMS export, meter register, billing export,
settlement statements, fuel records, budget, and one asset's contract set.

## Kobo: what we ask for, what each settles, and which assumed value it replaces

| # | Item | Form we can take | What it settles | Replaces (until then, labelled `GENERIC_DEFAULT`) |
|---|---|---|---|---|
| 1 | At least **61 consecutive days of 5-minute readings**: solar (PV available power, or inverter output and irradiance), each feeder's load, generator on/off and output, battery state of charge | EMS export (CSV or one-sheet XLSX through a source profile, 3A6); 5-minute means, not 15 (D-0K3.2) | The baseline calibration (generator kWh within 5 %, starts within 10 %, SOC within 5 points) and the replay of every setting on Kobo's own season | Declared season v2 (0K4c) |
| 2 | The **fuel log** over the same days: deliveries, tank dips, any refuels | The operator's fuel records | The litres the generator really burned, against the fuel curve and the fuel balance | — |
| 3 | The **controller settings**: start and stop charge, reserve, minimum run, start delay, minimum generator load, generator support, and whether it cycle-charges or load-follows | A screenshot or export of the controller's settings page, with the date it was set | That the model runs Kobo's own control rules; whether v8's cycle charging applies (D-0K4.3) | Minimum load 30 %; cycle charging |
| 4 | The **generator's model and fuel sheet** (litres an hour at 0, 25, 50, 75 and 100 % load), and the maker's limit on starts | The maker's data sheet | The fuel curve's two points (no-load rate, full-load consumption) and the starts part of the admission rule | No-load 3.3 L/h; SFC 0.3 L/kWh; 6 starts a day |
| 5 | The **battery's chemistry and warranty floor** (lowest state of charge the warranty allows; required full-charge interval) | The battery maker's sheet or warranty | The charge taper, the full-charge part of the admission rule, and the floor shown beside any lower reserve | LFP: taper from 95 %, a full charge every 7 days |

When an item arrives, its value goes on Kobo's Foundation with basis `MANUFACTURER_DATASHEET` or `SITE_TEST` (the same
property keys, D-0K4.4 to D-0K4.6), and the study is rerun: the figure changes, its label changes, and no second
figure appears beside it (D-0K4.11).
