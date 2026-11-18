# Owner ruling: S4-02b money demonstration data (2026-10-14)

Context: `.agent/S4-02b-phase-1-review.md` Q9/M2. Today's ordinary demo data yields no positive fuel cost: the only Finding with accepted generator power (F01-gateway) has 5-minute means published every 15 minutes, covering a third of Candidate time, so `fuel-cost-1` correctly fails closed (`POWER_COVERAGE_GAP`; interpolation is forbidden by the decision).

Question offered: "Add a demo case (Recommended)" / "Change gateway publishing" / "Show none qualified".
Owner (verbatim): "go with your recommended option but add a backlog item to ensure both simulated and real sites are supported to in terms of data required for the analysis"

Recorded meaning:
- Phase 2a adds one new, clearly labelled authored S4 demonstration case with back-to-back 5-minute generator power means, delivered through the same registered-credential Batch V2 path, in a new versioned spec (not `s4-finding-cases-v1`, so S4-01/S4-03 evidence stays valid). The checkpoint shows its amount beside the F01-gateway coverage-gap Finding as the honest unavailable example.
- Backlog item (owner): both simulated and real Sites must supply the data the analyses require (for `fuel-cost-1`: generator power means with continuous coverage of Candidate time; in general each analytic's required inputs and cadence), recorded in `.ai/MILESTONE_REVIEW_BACKLOG.md` "Owner: analysis input data for simulated and real Sites (2026-10-14)".
