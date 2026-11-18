# Architect request - W2-05a QE-QG (2026-10-18). Brief rulings; edit `.agent/W2-05a-build-spec.md` in place; amend `D-2026-10-18-w2-05-buildspec`. No code.

From the W2-05a commit-2 implementer (branch task/W2-05a-ev-foundation, handoff `.agent/W2-05a-phase-handoff.md` there):
- QE: `ev-meter-cadence` is a connector property, but the Site import role binds the import meter. Which value gives the Site import binding's `cadence_seconds`: one connector's (which), the minimum across connectors, or null?
- QF: the two old W2-00 EV channels are labelled with EV roles but excluded from the `simulator-lab-gateway-ev/1` profile table, so an `ev-roles-1` publication cannot bind them. Confirm or correct.
- QG: publication does not refuse a c1 device bound to the c2 connector (only the fixture test checks it). Should `validate_bindings` refuse it, and with which code?
Print a 3-line summary.
