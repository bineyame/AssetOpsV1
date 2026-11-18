# Architect request: W5-03a fix-round open points

You are the AssetOps Architect. Read .ai/ROLE_CONFIG.md ("Mock fidelity", D1-D6), .agent/W5-03a-review-rulings.md, .agent/W5-03-build-spec.md (W5-03a), the v69 mock frontend/mockups/v69/index.html and .agent/W5-03a-fix-questions.md. The code is on branch task/W5-03a-fix; read it with `git show task/W5-03a-fix:<path>`.

Rule on each of the four points:
1. A SCHEDULED window with zero unknown time: give the exact next-evidence literal, or confirm that only the telemetry sentence shows.
2. Hours format in the chart notes, the bound prose and the next-evidence duration: decimal hours, or durationText.
3. Confirm `unresolved_panels: []` for availability and energy.
4. No ruling needed. Note only.

Cite the mock wherever it applies. Append the rulings, numbered, as "Fix-round rulings" in .agent/W5-03a-review-rulings.md, and update .agent/W5-03-build-spec.md if needed. Do not touch product code. Do not commit.
