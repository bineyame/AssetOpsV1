# DATA-2 packet (D-E5.32)

Outcome: `story_links` (tools/demo_combined.py) adds, per Cold/EV story day with an event window, a second link
"<CODE> analysed period, <kind> day S+Nd (<day>) HH:MM-HH:MMZ" on exactly the day's `start`/`end` from days.json
(Cold 16:00-17:05Z; EV fault hour 08:00-09:00Z, as registered). Days without an event get none; the whole-day link stays.
`prebuilt_routes` derives from `story_links`, so each is a stored board request; its id is
`board.day:<site>:<from ISO>` (distinct from the day's id; ids stay unique).

Tests: test_demo_combined_links.py and test_e4_prebuilt_routes_generator.py each gained one test; both fail on main's
demo_combined.py (verified), pass on the branch. Run singly: links 12, generator 12, finish_rows 69, routes_source 5, all pass.

Deviation/risk: EV window is days.json's 08:00-09:00 (the 4.50 probe window); the 08:00-09:05 second selection is not linked.
Live app display (4.9 C, "Stock may be at risk", USD 4.50) not re-probed here.
