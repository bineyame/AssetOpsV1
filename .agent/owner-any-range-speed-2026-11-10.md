# Owner question and instruction, 2026-11-10 (verbatim)

On the pre-loaded demo pages:
"why does this have to be done specially for the demo and not a natural way the app works; e.g why a special fast load for demo data only while it should work for any date range i specify(selection at the top of the screen)"

"why was the product built this way with a senior architect direction in the first place?"

"did i not ask for daily summary snapshots ?"

The owner's earlier words, from `.agent/owner-walkthrough-notes-2026-11-01.md` (2026-11-03): "does it not make sense to have a per day snapshot that gets recaculated based on changes?"; "should be stored and recalcualted per event and that trigger should be declaratively designed, perhaps some event register"; "we should make sure the site and portolio data should load quickly, today it is actually really slow"; item 12 "make sure it is performant  and scale path is designed"; item 13 "usage of snapshot is encouraged".

Coordinator proposal, which the owner answered "yes go ahead":
(1) The Architect gives a measured answer against the 2026-11-03 instruction. It covers where the 5–9.5 s goes on a page that was not pre-loaded, which parts could come from day snapshots or other stored daily rows, the smallest proper fix to reach under 2 s for any date range, and whether that fix is needed before the client session.
(2) A backlog item is added now, citing the 2026-11-03 words.

Owner decision, 2026-11-10 (selected option, verbatim label): "Both before client (Recommended)". Option text: build ANY-1 and ANY-2 before the client session, so any date range a CFO picks loads in under 2 s. The client session moves until after both land, about a week after the fix round. The owner walkthrough goes ahead now on the script's dates. This supersedes the conditional part of D-ANY.1: ANY-2 is now demo-critical and comes before the client session.

