# Owner decision: W5/W6 build-spec readiness (2026-10-21)

The owner asked: "why is w4-03 taking this long?"

The coordinator's explanation:
- W4-03 has 12 build units.
- There have been 11 mid-build rounds of Architect rulings on open wire values, labels, copy, links and fixtures, two of them after a dry-read had reported "nothing open".
- Three builders ran out of context.
- Postgres tests take 15–25 minutes per unit.

The coordinator proposed, for W5 and W6:
1. Before any build starts, check each slice's spec against the code for every wording, label, wire value, ID, link target and fixture.
2. Split large slices into two.

Owner decision, verbatim: "yes, apply that to W5 and W6"

Addendum (same day). Owner, verbatim: "lets make sure to adopt best practices and learning for waves 5 and 6 for quality and speed". The coordinator recorded 12 W3/W4 lessons in `.ai/ROLE_CONFIG.md`, under "W3/W4 lessons applied to W5 and W6".
