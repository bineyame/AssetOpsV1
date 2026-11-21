# 0M review

## Round 1: discovery review (W5), 2026-11-21

Reviewer: Claude (fresh, not the author). Branch `task/0M-mto-headroom`, head `fddd920c9`, diff `main...fddd920c9`
(10 files). Read: spec rev 2, rulings D-0M.1-22, reviewer guide rev 2, packet, the whole diff, the manifest's Mto
block, logs in `/opt/assetecon/evidence/0M/`, and 0K2's review for the standard.

**Summary (verdict: ACCEPT WITH FIXES).**
- The code, the fixture and the tool do what spec §2-§4 say. The figures are right: I reproduced the 8-day case through
  the port and got the Architect's probe figures exactly. The 61-day month figures agree with what I found per day.
- Labels hold. Every outcome, the result, the calibration, each printed line and the JSON header carry SIMULATED and
  MODELLED. "Calibrated" is said to mean adapter fidelity. Nothing is served, there is no money, and the diff changes
  no design value (row 37 held).
- Plant: each edit to the Kobo template traces to the manifest's Mto `physical` line. The loads are halved (6,000 / 11,580).
- Refusals come before the port: a case id over the limit, a limit mismatch and a non-kW unit (M4, M5; and H1, which I
  reran myself with zero calls).
- The "guard fails" line is a plant: a scratch import, now reverted, that proves the guard works. The guard did not
  fail on the branch. P6 and P21: accepted (see below).
- **1 Medium:** three of the packet's four plain reasons give the wrong mechanism for their gap (huller litres,
  welder litres, reduced capacity). This is a packet-text fix only. **2 Low.**

### Checks I ran (head `fddd920c9`)

- `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`): "Architecture check passed." Without it the chain guard
  cannot find an interpreter in the worktree, which is an environment issue. `check-agent-workflow.ps1`: "Agent workflow check passed."
- Through the slot pool: `backend/tests/test_0m_headroom_replay.py`, `test_0k1_replay_port_seam.py` and
  `host/tests/test_0m_mto_headroom.py`: **49 passed in 37.2 s**.
- **Own reproduction through the port** (scratch script, `heavy-slot.sh --label 0M-review`, 8-day Mto season, v7):
  - Both runs READY. Site fuel 48.35 L. Calibration failed ().
  - Huller: 2 of 6 days without headroom, 128 of 450 kWh beyond it, +51.40 L.
  - Welder: 6 of 6 days, 180 of 180 kWh, +45.36 L.
  - Reduced capacity: 0.96 L in 8 days.
  - Refusals with a counting port: `ReducedCapacity(<25 kW run>, 30)` and `ReducedCapacity(<full run>, 25)`, each
    `REDUCED_CAPACITY_INVALID` with 0 calls.
  - The figures equal the spec §0 probe (the probe's "74.47 L" baseline and "0.24 L a day" do not match, as the packet
    already notes; figures are outputs).
- I read the per-day diagnostics myself: PV, load and SOC by step, and extra generator kWh per local date.
- Not rerun: the 61-day study, which I read in `study.json` and `run.log`; production code is unchanged between its
  revision `465d095fc` and the head. Also cited, not rerun: 121-test regression (`12b1d0427`), contracts 190, check-all
  40 guards (`5a424ce6e`), plants P1-P26 (logs read).

### Verified against the dispatch

- **Figures.** `study.json` holds every packet figure:
  - huller October: 6 days, 384 kWh, 156.669 L;
  - welder: 1,320 of 1,320 kWh; October 116.39 L / 660 kWh = 0.176 L per kWh;
  - capacity: 14.438 L over 61 days = 0.237 L a day.
  - October comes from the by-month fields (D-0M.15).
- **Dawn.** No-action FAIL, 15 of 61, worst 30.72. The dates are 5 Sep and every fourth day after. At full capacity
  the huller adds no dates. At 25 kW it is at 29 with 14 new, against the reduced replay. The welder clears 13 Sep and
  11 Oct. The packet reads each verdict as absolute and each customer effect as its new dates, and states D-0K2.17's
  cause.
- **Plant.** PV 50, inverters 25 + 25 = 50 (25 with INV-MT-02 failed), battery 150, reserve 30, genset 30 and SFC 0.33
  are the manifest's `physical` line. Huller 15 kW 10:00-15:00 and welder 10 kW 18:00-21:00, 22 days, are
  `MTO-HULLER` and `MTO-WELDING`. The kept values are listed (D-0M.21).
- **"The guard fails on a host.forward_replay import".** This is P17, planted deliberately. `guard-plant.log` shows
  `dependency-direction.ps1` refusing a scratch `from host.forward_replay import HostForwardReplay` at
  `headroom_replay.py:31`. The import is gone at the head, and the guard passes there.
- **P21.** The first M4 stand-in also failed the "full not above" check, so the planted limit check was never the
  only thing standing. `12b1d0427` adds `stated-not-frozen` (frozen 25, stated 30), and the rerun now fails M4 and H1.
  That is a sound fix.
- **P6.** For the welder, headroom is 0 at every welder step with or without the customer, so H3 cannot see the
  plant. H2 (the huller) and M2 both catch it. The reviewer guide was wrong to name H3, and the test coverage is
  fine. I accept it as the recorded deviation.
- **One rule of each, nothing modelled, independence.** `headroom_replay.py` imports 0K2's helpers and copies none of
  them. Its arithmetic is sums, differences, the headroom `max`, the reduced `min` and one ratio. The host test's reader
  builds steps by fixed offset, months by its own loop and burns from `fuel_start_l`; it calls no helper of the code
  under test.

### Is "1,320 of 1,320 kWh beyond headroom" real?

It is true by construction, not a discovery. The declared season has PV equal to 0 from 18:00 local. In my run the
last step with PV above 0 is 17:55, and the most PV at any welder step is 0.0. So the same-step headroom of D-0M.6 is
0 at every welder step, whatever the weather. The design assumed the same thing ("every evening kWh is diesel").
Near the equator this is close to physical, but it is a property of the inputs and the definition, not of the replay.
It also does not mean diesel: see M1.

### Findings

**M1 (Medium, acceptance gap: honest plain reasons, spec §5 packet; `packet.md` lines 54-61).** Three of the four
plain reasons name a mechanism the replay does not show. My per-day reading of the 8-day replay gives:

| | 1 Sep | 2 Sep | 3 Sep | 4 Sep (overcast) | 5 Sep | 6 Sep | 7 Sep | 8 Sep (overcast) |
|---|---|---|---|---|---|---|---|---|
| Huller, extra generator kWh | 0.0 | 0.0 | 0.0 | 76.6 | 2.5 | 0.0 | 0.0 | 76.6 |
| Welder, extra generator kWh | 0.0 | 0.0 | 0.0 | 68.8 | -0.1 | 0.0 | 0.0 | 68.8 |
| 25 kW limit, extra generator kWh | 0.0 | 0.0 | 0.0 | 0.0 | 2.9 | 0.0 | 0.0 | 0.0 |
| PV clipped above 25 kW | 100 kWh | 100 kWh | 100 kWh | 0 | 100 kWh | 100 kWh | 100 kWh | 0 |

On clear days the daily maximum SOC is 100 % in the baseline, with either customer and at 25 kW. On overcast days it
is 69.8 %, and PV peaks at 16.5 kW. The 61-day month figures fit the same pattern:
- huller: Sep 130.56 L over 5 overcast weekdays and Oct 156.67 L over 6, which is 26.1 L a day both months;
- welder: 18.7 and 19.4 L a day on the same days.

So:
- *Huller litres.* The packet says the diesel goes to refilling the battery "on days that had headroom". In fact
  days with headroom cost about 0. On each overcast weekday the huller costs about its whole day, 76.6 kWh of
  generator energy for 75 customer kWh, because that day's "headroom" PV was charging a battery that never fills.
  The 157 L against the design's 68 L is mostly the design's own logic (a day without headroom costs the whole day
  in diesel) applied to 6 days instead of 3.
- *Welder litres.* The packet says the battery "carries about half" of every evening. In fact:
  - on clear days the battery carries the whole evening, and spilled PV refills it the next day, at no extra diesel;
  - on overcast weekdays the generator makes about 2 to 2.3 times the customer's kWh (start at 35 %, run to 90 %;
    9 extra starts over 61 days).
  The 0.18 L per kWh is the average of 0 and about 0.7.
- *Reduced capacity.* The packet says the clipped PV "would have charged the battery". In fact the battery still
  fills on clear days, so most of the 100 kWh clipped each clear day would have been spilled anyway. On overcast
  days PV never reaches 25 kW. The small cost falls on the clear day after an overcast day.

Why it matters: the owner judges whether to replace the design values with these reasons beside them (row 37), and
the welder's manifest disposition rests on "every evening kWh is diesel". Fix: rewrite the three reasons in the
packet (and in the one-line state entry if it repeats them). No code change and no new run are needed; a per-date
line in the tool is optional. The figures themselves are not in question.

**L1 (Low, labelling; `packet.md` table, welder row).** Say beside "1,320 of 1,320" that this holds by construction:
the season has no PV from 18:00 local, so same-step headroom is 0 for an evening customer. Also say that "kWh beyond
headroom" is a same-step reading that ignores the battery's shift in time, so it is not the diesel figure. It sits
below the diesel figure for the huller and above it for the welder.

**L2 (Low, preference; spec §4 "The 61-day study").** The spec says "two site runs and 7 replays". The run made 1 site
run and 6 replays, which is spec §2.2's own `2 + 2k`; the packet explains why. When the spec is next touched, align
it. Nothing to do on this branch.

### Residual risk the packet does not name

- Every Mto gap comes from a weather calendar with two day types: overcast every fourth day, and clear days that
  fill the battery to 100 %, both with the loads halved. A customer costs about nothing on clear days and about its
  whole day on overcast ones. So each figure scales almost linearly with the overcast count, and the welder's and
  reduced capacity's low figures depend on the battery still filling at half load.
- `study.json` has no per-date extra figures. My "clear days cost about 0" rests on the 8-day per-day reading and the
  61-day month-per-day ratios, not on a 61-day per-date print.

### Design values beside the study (for the owner; no verdict)

On a day without headroom the huller costs about its whole day in diesel, just as the design assumes. The study
counts twice the design's bad days because its simulated weather is overcast every fourth day. Two figures are much
lower: the welder (about half the design's diesel) and one failed inverter (almost nothing). On clear days the
battery still fills and carries the evening, and on overcast days the sun never reaches the reduced limit.
