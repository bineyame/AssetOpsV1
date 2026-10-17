# Owner decision: full mockup left menu (2026-10-17)

Owner (verbatim): "Show the full mockup menu, with unbuilt items greyed out as "not available yet". That needs an Architect ruling plus a small slice, about half a day."

Context: the coordinator reported that the app's left rail shows only Sites (group "OPERATE") and Findings, while the v69 mockup rail (`frontend/mockups/v69/screens.js:940,964-967`) has 11 roots in six groups: OPERATIONS (Portfolio, Sites, Assets), INTELLIGENCE (Findings), WORK (Actions, Incidents, Maintenance, Operational records), ASSURANCE (Evidence), BUSINESS (Financials), ADMIN (Settings), plus a workspace footer linking the Simulator Lab. Earlier rules keep unbuilt roots off the rail (navigation-truthfulness guard `tools/checks/navigation-truthfulness.ps1`). Applied: Architect ruling, then slice W1-UX-07, before the combined W1 walkthrough.
