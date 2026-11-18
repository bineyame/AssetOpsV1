# Architect request: W5-02b K3, one remaining cap measurement

Read .agent/W5-02-build-spec.md, K3 rulings 17, 18 and 21, and the v69 mock (cold-work-incidents). Ruling 17 caps the five-row "one `Read full text` open" state at 650 px panel height at 390, with no fallback clipping or row reduction. Ruling 21 removed the narrow Incidents vertical box, so all five rows now show.

The recapture shows cold-work-incidents at 390, five rows, one `Read full text` open: the panel is 664 px against the 650 cap, 14 px over. The page main is 1270 of 1800, and containment, the five rows and no-overflow all pass. The closed panel is 599 px; the opened 160-character title adds about 65 px. Every other capped state passes, for example Maintenance 390 one-open at 526 and Incidents 1440 one-open at 539.

Give one FINAL ruling: either raise the 390 five-row one-open panel cap to an exact value, or name the exact layout change. Cite the mock and the consistency with ruling 18. Append it as ruling 25 to the K3 rulings in .agent/W5-02-build-spec.md. Do not touch product code. Do not commit.
