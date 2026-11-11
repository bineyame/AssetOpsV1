# Owner decisions, 2026-11-11 morning (verbatim)

"yes tag it and add the backlog item, lets go with option B for now. Also, lets proceed with the items for today right away, and i want my walkthrough comment items to start building. THe client demo will be on 17-Nov"

Context (coordinator):
- "tag it": tag the E3d demo build's commit (5cc98edfa) as a named demo build; tag every demo build from now on.
- "the backlog item": move the build's working files (e.g. the file-backed legacy S2 comparison report) out of the frozen code copy `var/<work>/tree`, so the tree is code only.
- "option B": copy the merged known-defect marker file `tools/demo_combined_finish.py` (D-E5.40, main e571fb807) into the E3d build's frozen tree `var/polish_client6/tree/tools/` as a one-off owner-approved exception to R6.3 ("never replace or edit a build's tree"), so add-dates' finish check reports CO-6/WK-GAP as known defects instead of FAIL.
- Client demo date: 2026-11-17 (Tuesday). Supersedes the ~1–8 Dec window and the Architect's 8 Dec recommendation.
