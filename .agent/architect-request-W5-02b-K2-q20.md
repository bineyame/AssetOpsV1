# Architect request: W5-02b K2, Q20 (final F1 ruling)

Read .agent/W5-02b-K2-rulings.md (rulings 2 and 20), .agent/W5-02b-questions.md (Q20), .agent/W5-02-build-spec.md, .agent/W5-02-04-mock-measurements.md and the v69 mock (frontend/mockups/v69/index.html, cold-work). The evidence is on branch task/W5-02b-cold-site-screens under .agent/W5-02b-evidence/.

After ruling 20, the all-disclosures-open state measures 819 px at 1440 (cap 650) and 1083 px at 390 (cap 850). The page stays within its caps (1203/1629). Each row at 1440 is 137 px: the 160-character title wraps to 3 lines in the 340 px Action column, and the Owner wraps to 4-5 lines in the 240 px Owner column. Every other state passes.

Give a FINAL ruling that will not cause another loop. Choose exactly one:
(a) Column widths and wrapping that match the mock's cold-work table. Give exact px values or the CSS rule, and state the cap the builder must meet.
(b) Exempt the all-open state from the panel cap and keep the page caps, because opening every disclosure is a user-driven expansion. Record why.
(c) Something else, with exact values.

Cite what the mock does. Append the ruling to .agent/W5-02b-K2-rulings.md as ruling 24, and update .agent/W5-02-build-spec.md ruling 2 if the caps change. Do not touch product code. Do not commit.
