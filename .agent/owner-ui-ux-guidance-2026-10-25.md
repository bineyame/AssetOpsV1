# Owner guidance: modern UI/UX for UI decisions (2026-10-25)

Owner, verbatim: "for UI/UX related question, it is important to take inspiration from modern UI guidelines and techniques, this is for the architect as well as the implementer"

Applies to: the Architect (rulings on copy, layout, caps, fallbacks) and Implementers (choices where rulings are silent, pre-flight recommended defaults).

How to apply:
- When a UI question is open (the v69 mock is silent, a cap fallback is needed, a phone layout, empty/loading/error states, long-content handling, navigation, disclosure, tables), ground the answer in current mainstream guidance and practice: e.g. WCAG 2.2 accessibility, platform design systems (Material 3, Apple HIG, GOV.UK / USWDS design systems, Carbon, Atlassian), Nielsen Norman Group usability heuristics, and responsive-table/data-dense dashboard patterns.
- Name the guideline or pattern relied on in the ruling or the pre-flight default (one line is enough), and prefer the option a modern product would ship (clear hierarchy, progressive disclosure, readable type at 390 px, visible focus, scroll affordances, plain-language copy, no raw codes on screen).
- The v69 mock stays the layout spec where it speaks; modern guidance shapes how gaps, fallbacks and departures are resolved, and the quality of what is proposed to the owner for D2 decisions.
