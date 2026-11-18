# Architect reply to your answers on questions 2 and 3 (2026-10-27)

From the Architect (Claude). Your answers: `.agent/owner-answers-open-questions-1-2026-10-27.md`. Question 1 (a) is recorded.

## Question 2: you are right. Withdrawn.

The source is already a data element on screen. The Evidence screen shows each source's origin, and Finding and cost screens show the checked source ("Generated test data", "Source unverified"). Nothing new needs building.

**Example.** On the test Site's Evidence screen, the October Modbus readings show as "Demonstration data". The words "emulated interface; values from a simulator run" go in the demo script and written record.

## Question 3: mostly right, with one gap.

**Where you are right.** Financially they are the same: neither is a real reading. I also overstated the risk. Simulated data already produces cost figures, labelled "generated test data". And in October no money is at stake, because the emulated controller has no generator signal.

**The gap.** "Registered simulation" is a receipt, not just an origin. It proves these exact readings are what one recorded simulator run produced, so the figure can be reproduced.
- The emulated route has no receipt yet. Values pass through a fake controller, an unverified register map, rounding and averaging. Nothing proves what arrived equals what the run produced.
- They also prove different things: the simulation shows the analysis works; the emulated read shows the connection works.

**Example.** The run says solar output was 4.20 kW. A wrong scale in the register map delivers 0.42 kW. Under the simulation stamp, a cost figure would carry that error with nothing on screen showing the reading changed in transit.

**Revised recommendation.** Keep (c) for October. Later, add one "emulated interface" label that counts like simulated data for test cost figures (your point), provided it names the run, the map version, and a check that values arrived unchanged.

---
**For agents**
- Q2 withdrawn. TEL-07 stays terminal plus claim record, no screen code; the runbook may cite existing Evidence screen labels.
- D1 stays (c). D5(d) unchanged.
- TEL-09 amended: the emulated-interface class may be a positive, money-eligible test class only when it binds one registered run ID and identity digest plus the profile SHA-256, and a test proves read-back values equal the run's values; otherwise UNKNOWN. Ladder: simulation R0, emulated read R2.
