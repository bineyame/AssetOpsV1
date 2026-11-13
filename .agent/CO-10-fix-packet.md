# CO-10 fix packet: NOT FIXED, ruling premise does not match the data

No code changed, no commit.

Finding (checked with host/tests/test_evhb_generated_days.py helpers on the S-fault day, 2026-11-03):
- The EV-HB generator already emits a c1 state record at EVERY minute from 08:00 (08:00 AUTHORIZING, 08:01-08:15 CHARGING, 08:16 FAULTED...). There is no gap in the heartbeat.
- The 16 min "unknown" comes from backend/assetops_backend/analytics/ev_availability.py:30, CATEGORY = {AVAILABLE, UNPLUGGED -> available; FAULTED, DISABLED -> unavailable}. AUTHORIZING and CHARGING are not in the map, so classify.get(..., UNKNOWN) makes 08:00-08:16 Unknown.
- Emitting "Available" at 08:00 would cover at most the first minute (cadence 1 min; each record spans to the next) and would contradict the c1 session that starts at 08:00 (AUTHORIZING -> CHARGING). Making all 16 min Available would falsify the story.

Options for the Architect (not decided here):
1. Product mapping: classify CHARGING/AUTHORIZING as available-and-occupied (known, in service). Product change in ev_availability.py; affects every EV availability minute and the Available/Unknown figures (CO-*, EV Grow/DATA-4, availability tests).
2. Story/data: start the fault-day c1 session later or have c1 sit AVAILABLE before it (changes sessions/energy, E5/WK-1 pins).
3. Relax the CO-10 pin (ruling says no).
