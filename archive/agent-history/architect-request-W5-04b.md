# Architect request: W5-04b review items A1-A4 (A3 binds W5-04c V4a)

Read:
- .ai/ROLE_CONFIG.md
- .agent/W5-04-build-spec.md
- .agent/W5-04-readiness-rulings.md (1-68)
- .agent/W5-04b-review.md (V3a/V3b ACCEPT, Lows L1-L3, items A1-A4)
- .agent/mock-departure-register.md
- the v69 mock (ev-work-incidents, ev-work-maintenance, ev-action)

W5-04b is now merged to main. W5-04c (V4a/V4b/V5) is built on task/W5-04c-ev-action and will rebase next.

Rule on each item:
- A1: confirm that the walkthrough file and its producer test are owned by V3b, following the V2b M1 precedent.
- A2: give the size cap for a refused case panel. The reviewer recommends 360/590.
- A3: extend ruling 67 to the case-row Action link inside `UTC and IDs` on ev-work-incidents and ev-work-maintenance, so it carries the page's from, to and explicit known_at. Assign the change and its test to V4a in siteWorkCases.tsx. Also fold in L1: R113 should name both case screens, so that V4a closes R113 on them too. State whether V4a should also add an Incident Finding link to the producer, so the R75 disclosure gets captured (L2).
- A4: confirm the post-wave UI-pass items: "1 incidents" grammar and the raw asset label.

Append the rulings, numbered from 69, to .agent/W5-04-readiness-rulings.md. Apply them to .agent/W5-04-build-spec.md and to the R113 row. Do not touch product code. Do not commit.
