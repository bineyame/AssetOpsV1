"""5b: attribution, the gap explained by its drivers (spec `specs/5b-attribution/spec.md`; rulings D-5B.1 to D-5B.15).

`rules` holds the literals and `agree`; `bridge` splits one root's gap from an actual and a target side (pure, unit 1).
`carry` carries a missing cost line at its budget line and `site` bridges one Site (pure, unit 2); `portfolio` adds
the Sites' rows one set at a time (pure), `read` pins one instant per read and `composition` wires it (unit 3).
No existing module is edited, and nothing here writes `structure/read.py` (D-3B7A.10).
"""
