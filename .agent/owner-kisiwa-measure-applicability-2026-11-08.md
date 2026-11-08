# Owner answer on Kisiwa board days / measure applicability (2026-11-08)

Asked through the question dialog after `.agent/build-sheet-DIESEL-1.md` §9s2 (DIESEL-1-R3s2, f34376322) owner question. Question as shown, then answer verbatim.

Q: Kisiwa's board days never count as 'checked'. The system requires every day to have a 'productive use' figure, and Kisiwa has no productive-use loads (only essential services and households). As a result, on Kisiwa's board the unexplained-fuel story still shows fully, but the Grow, Cost and Performance rows read 'Unknown'. The board also says '31 of 31 days are not assessed yet' right next to an assessed fuel finding, and night 1's generator cost reads 'Not known yet'. The fix is a small product rule: a measure that doesn't apply to a site (no such load) is left out instead of blocking every day. It costs about 0.25 units and runs alongside the rehearsal. It may push the schedule just past the tripwire (path about 9.6–9.85 vs 9.75), which the Architect would cover by moving the four-site Kisiwa Overview screenshot to the demo-day build. Should Kisiwa's days count as checked for the demo?
Options offered: Fix it (Recommended) / Leave as is / Defer until after rehearsal.

A (free text): "if the contributing dimensions to growth, whether productive use or otherwise are 0, it should be indicated as such. The component contributor being non existent doesn't mean it is checked.Let the architect weigh in as well."

## Follow-up (after DIESEL-1-R3t, c68aae8b7)

Q (as shown): "Following your answer, the Architect redesigned the Kisiwa fix. Kisiwa has no productive-use equipment (like a mill), so there is nothing to measure there. Proposed: Kisiwa's board says '0 kWh · no productive-use load declared for this site', and clearly says productive use was not assessed. Its days then count only for what Kisiwa actually has: generator, fuel, service and solar. The cost, service and evidence rows then show real results, and night 1's generator cost shows its money. A day only counts if the site setup really says 'none'; missing data is still shown as missing. Cost: about 0.4 units, alongside the rehearsal. Even after moving lower-priority screenshots to demo day, the finish may land up to about a quarter unit past the 9.75 limit. Which do you want?"
Options: Build it (Recommended) / Wording only now / Leave as is.

A: "Build it (Recommended)"

So K10 v2 (R3t) is in scope, accepting the tripwire risk; R3t's cut order applies.

## First answer — coordinator reading
Coordinator reading (for the Architect, not a substitute for the verbatim text): the owner does not accept silently dropping a non-applicable measure so the day reads "checked". A contributor that is zero or absent (e.g. no productive-use load) must be shown explicitly as such (zero / not present), and its absence must not by itself make the day count as checked. The Architect is to weigh in and redesign K10 accordingly.
