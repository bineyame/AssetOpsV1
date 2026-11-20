# Owner direction 2026-11-19 (verbatim): vertical factor map

The owner asked:

> from the briefs, which file is the architect wokring on to ensure the industry researched  needle movers for each vertical are mapped into clear factors that would then make to site and portfolio level

## The coordinator's answer (the owner approved it)

The trace is `outcome-lever-capability-traceability.csv`: 454 rows running objective → lever → capability → factor → model → demo option. It has four gaps:
- Its factor column is free text, not registry factor IDs.
- No check reads it.
- The recreated documents do not cite the brief's L2.2–L2.4 lever catalogues.
- The old narrative documents are due for retirement.

Proposed:
1. A short vertical factor map, one section per vertical. Each researched needle mover gets a factor ID, a home category, a site read, a portfolio roll-up, and the Findings, decisions and plan items that act on it. Levers not in scope now stay visible with the brief's L2.7 reason. Cold and EV worked structures sit beside Kobo's.
2. A mechanical check:
   - every brief lever is in the map;
   - every mapped factor exists in the registry;
   - every factor has a home category and a site or portfolio read;
   - the CSV's factor column uses the same IDs.
3. The CSV is kept as the data behind the map, with its wording cleaned and linted.
4. Nothing is retired until its content has moved.

The owner answered:

> yes, have the architect add the vertical factor map
