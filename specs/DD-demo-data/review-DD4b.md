# DD4b review (EV and measured books, DD4.3 to DD4.6)

## Round 1: discovery review at `bf92b6124` (Claude reviewer, 2026-11-23)

**Summary**
- Verdict: **accept, with the Low findings fixed on the branch.** No High and no Medium findings.
- Kasarani recomputed from the committed departure log: 10 short rows, 3 spare rows met, so **7 missed** and 7 x 120 = **840.00**. Matches the packet, D-DD.125 and `M`.
- Cold bill recomputed from the readings: I reran the Mwea writer from 1 Jul to 31 Oct and summed October's 8,928 written `compressor-meter/power` rows x 5/60 h. That gives **1576.300 kWh**, and x 0.20 = **315.26**. This equals the fixture, the bill sample and `M`.
- The writer memory fix, the frame rejoin, the D-DD.125 node and the D-DD.144 refit match their rulings. The D-DD.144 derived figures in deviation 16 check out (56 %, 68 months, about 154 months, 0.048).
- L1: four hand-typed Kasarani figures were missed by the sweep in three design documents. L2: a stale `H8` comment. L3: a misleading refusal text.
- Questions for the Architect: Q1, the history cold kWh are not the meter's, although D-DD.144 says they are (model). Q2-Q4 give a view on deviations 8-10, each with a default.

### Checks I ran
| Check | Result |
|---|---|
| Departure-log recompute (`fixtures/measured/metro-bus.measured.json`, EV-KAS) | 1,027 rows. Short: B03/B04 on 1 Nov (63.333), B07/B08 on 2-5 Nov (26.250/22.083). S01 met on 2, 3 and 4 Nov. Missed 10 - 3 = 7. No row delivers more than its required kWh (all 5,379 rows). Nov rows 43 = 40 required + 3 spare; met 33. November import 6069.167 kWh, demand 200.000 kW, `partial_to` 06:00 |
| Cold recompute: Mwea writer 1 Jul to 31 Oct via `build_telemetry(..., sink=)` (heavy slot), log `/opt/assetecon/evidence/DD4b/review/cold_recompute.log` | July to October `room_kwh` 1659.750 / 1613.000 / 1589.950 / 1576.300: byte-equal to the committed fixture. October written-row sum 15763/10 = 1576.300, so the bill is 315.26. The other two bills (by multiplication only, not from readings): Thika 1771.350 x 0.2 = 354.27; Kirinyaga 2113.603 x 0.2 = 422.7206, which rounds to 422.72 |
| `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set; without it the worktree has no `.venv`, which is an environment failure) | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `tools/heavy-slot.sh --db-lane -- pwsh tools/run-host-tests.ps1 --` `test_dd46_cold_energy_model`, `test_dd4_checker_on_emulated_rows`, `test_dd4_ev_join`, `backend test_dd45_charger_bound`, `test_dd4_check`, `test_3b6_cold_ev_structures` | **112 passed**, 21.95 s (`focused.log`) |
| Deviation 16 arithmetic | 350 / (12 x 52.01) = 0.561. 4800 / (41.61 + 28.94) = 68.0 months. 4450 / 28.94 = 153.8 months. (49.86 + 100) / 4500 + 270 / 18000 = 0.0483. All hold |
| Kasarani options against the restated log | WAIT: 3 nights x 2 - 1 spare = 5 missed, 600.00. STOPGAP: 5 x 45 = 225.00, value 600 - 225 = 375. LOCAL: 2 missed. Plan 1,500 + 225 = 1,725 and 95,484 + 375 = 95,859. All consistent |

I cite the builder's results without rerunning them: EV day files byte-identical across the memory fix (3.8 GB to 149 MB peak); `check_manifest` 6 FAIL, the same as main's 6 (`cm47.log`, `cm47-main.log`); `test_6h_parity` unedited; reach set 740 passed / 5 failed at `9969e6a14`, with three of the five fixed after and rerun in plain pytest (not on the DB lane), and two that are main's own (`test_3b1` t1, `test_3b3` t6). I confirmed that `git diff main...HEAD` touches neither M's `dispatch-3.2` line nor `rows_mini_grid.py`, so those two fail the same on main.

### Findings

**L1 (Low, sweep acceptance: "every `{fig:}` they feed" and "the hand-typed text beside them").** Four hand-typed Kasarani figures still carry the pre-D-DD.125 story beside swept anchors:
- `Docs/demo-sprint/product-direction-layer4/economic-metric-and-effect-contracts.md:314`: "(2 missed departures, 600.00<!--fig:-options.KAS-OEM-WAIT...-->, ECONOMIC_ACTUAL by 6 Nov)". The count is stale, and the anchor is WAIT's forward 600.00, not the actual to 6 Nov. Fix: "7 missed departures, 840.00, ECONOMIC_ACTUAL by 6 Nov", anchored to `service_cost_lines.service_penalties.november_to_date.Kasarani` (or the Site's `november_to_date` penalties node).
- `domain-and-decision-models.md:299`: "OBS-C1 Kasarani 1,050 vs 1,200 → 1 short". Fix: "→ 2 short (6 of 8 full by charger)".
- `domain-and-decision-models.md:645`: "plan KAS-OEM-STOPGAP 90 (must-do)". Fix: 225. In the same line, "its Protect effect (departures missed 2 → 0)". Fix: 5 → 0 (WAIT's 5).
- `worked-portfolios.md:618`: "departures missed to 9 Nov, 2 → 0". Fix: 5 → 0.

*Why:* these are owner-facing design documents, and the sentences now contradict the anchored figures beside them (one figure per quantity). `check_manifest` does not catch loose text. Preference, not gap: anchor the counts too (`fig:options.KAS-OEM-WAIT.protect.departures_missed`), so a later restatement cannot leave them behind.

**L2 (Low).** `Docs/demo-sprint/product-direction-layer4/check_manifest.py:1279`: the `H8_DERIVED_SHA` trailing comment says "at the DD4b D-DD.125 base", but the digest is the DD4.6 (rev 16.21) one; the comment two lines above says so. Fix: "at the DD4b DD4.6 (D-DD.144) base".

**L3 (Low).** `simulator/assetops_simulator/world/telemetry.py:701-712`: an asset bound twice for one signal is stored as `None` in `by_asset`, then refused as "`<device>/<signal>` has no binding row". The code is right (`TEL_BINDING`, deviation 2), but the text misleads. Fix: refuse with "bound twice by asset_code" when the key is present with `None`.

There are no findings against the writer physics, the memory change, `measured_for`'s mini-grid parity, `rows_ev_depot.py` (it matches D-DD.125's expression; `charger_kw` alone, as the ruling says), `EFFICIENCY_CONDITION` (D-DD.143's values, golden from main 6e3c02ab5) or the bill or invoice writers.

### Questions for the Architect

**Q1 (model): history cold `kwh` is not the meter's, yet D-DD.144 says "every cold `kwh` leaf (history and period) is the meter's (D-DD.20, unchanged)".** On the branch, `history.json` July-September cold `actual.kwh` is the restated model's output, while the bills (`exports_measured`, July-October) carry the meter:

| Room | Month | `history.json` kWh | Meter kWh (bill) | Difference |
|---|---|---|---|---|
| Mwea | Jul / Aug / Sep | 1684 / 1622 / 1641 | 1659.750 / 1613.000 / 1589.950 | +1.5 % / +0.6 % / +3.2 % |
| Thika | Jul / Aug / Sep | 1690 / 1737 / 1784 | 1719.500 / 1747.650 / 1770.700 | -1.7 % / -0.6 % / +0.8 % |
| Kirinyaga | Jul / Aug / Sep | 1939 / 2046 / 2148 | 1842.405 / 1908.075 / 2016.711 | +5.2 % / +7.2 % / +6.5 % |

D-DD.20 and spec §5.6 make these leaves `meter_billed`: the generated value is printed beside the metered one as information, and C-DD4 excludes them. So the build follows the spec, and `meter_billed.json` prints exactly these pairs. The product would still hold two figures for one room-month: the History series and the bill. Kirinyaga's drift story ("+3 %, +6 %, +8 % against the model" on the meter) reads differently on `history.json`. *Default:* D-DD.20 stands for DD4b, so no change on this branch. The Architect amends D-DD.144's parenthesis to "period" and decides whether DD6's world build sets the history cold `kwh` leaves from `measured.json`. The writer no longer reads `kwh`, so this is not circular. If yes, it is a DD6 card line plus a D-DD.30 regeneration.

**Q2 (deviation 8: the EV hour sums `kwh_2200_2400`, `kwh_0000_0500`, written `metered: null`; the C-DD7 clause is pending).** View: the gap is real. D-DD.20 lists both as metered leaves, and `rows_ev_depot.py` reads them (`scheduled_kwh_night`), but D-DD.99's EV month has no field for them. The writer already holds the depot import by minute (`_import`), so two window sums are about ten lines in `measured_months`, with one exact clause in `judge_meter_books` from `site-meter/import`. *Default:* extend D-DD.99's EV `<month>` with `"windows": {"2200_2400": kWh, "0000_0500": kWh}` (local clock, exact, rounded once), write them in `meter_billed`, and make the C-DD7 clause live. Do this in a DD4b follow-up (about 0.25 u) before DD6 builds the world, so DD6 does not rerun the 26-minute EV plant. Keeping the pending clause until DD5 is the alternative, at the cost of a second EV plant run.

**Q3 (deviation 9: C-DD5's cadence table and "on change").** View: ratify. D-DD.124 already makes the table the checker's own. Judging states and events as "no grid" (the writers repeat an unchanged state every minute or every 5 minutes), and counting a sample at a slot's start, are faithful to the readings. A strict "only on change" rule would fail correct writers. The only cost is the label: `CADENCE` says `ON_CHANGE` for a rule that does not judge change. *Default:* ratify, and amend D-DD.124's words to "states and events: ungridded (an unchanged state may repeat)". The builder may rename the constant's value to `UNGRIDDED` in the L-fix commit; that is a preference.

**Q4 (deviation 10: C-DD7's mini-grid clause pending; `stored_books` does not fetch TARIFF_SCHEDULE, FLEET_ROSTER or DEPARTURE).** View: correct to defer, but the hand-off is not written down. `cards/DD5b.md:58` says only "C-DD2 to C-DD7 are judged on the loaded store". It does not name widening the `stored_books` fetch to those three kinds, or the source of unserved energy (`measured.json`, not a readings channel). The pending text says "DD3b/DD5", which names two owners. *Default:* one owner, DD5b. The Architect adds both items to the DD5b card, and the mini clause reads unserved from the loaded `measured.json` figures (or from DD5's store of them).

### What I could not verify, and residual risk
- I did not recompute the EV plant itself (26 minutes), the full-span C-DD5/C-DD6/C-DD7 over plant readings (the builder records this as not run; the judges are tested on writer days), the Thika or Kirinyaga bills from readings (only Mwea), or `check_manifest` (cited).
- `measured.json` is per writer process. A DD6 world build that runs a tenant's Sites in separate processes writes several `measured.json` files, and `exports --telemetry` then refuses `EMU_MEASURED` (exit 3). That is a loud failure, not a silent one, but `cards/DD6.md` does not say "one writer process per tenant". Worth one line in the card.
- The Kirinyaga story weakens under D-DD.144, which the owner approved. Repair break-even is now 56 % recovery, and the replacement pays back in 68 months with a crossover near 154 months. The text keeps "DEFERRED, trigger: verified recovery < 60 %": at a recovery under 60 % the repair barely pays and the replacement still does not. This is not a defect, but the demo narrative for the trigger may want the Architect's eye.
- Items left for the alignment pass (the vNEXT mock JS, `gen_docs.cjs` "1 bus short, 2 departures missed, $240", `CHANGE-REGISTER.md`, `fixture-mapping.md`) still state the old Kasarani and cold figures until that pass runs.
