# W3-03 closure 4 check (main 4d5c0365; spec L337-399)

Result: 31 CLOSED, 2 OPEN (S4, S7). Items not listed below are CLOSED.

OPEN
- S4: F is stated exactly; E and M are prose ("unresolved/contradictory readiness", "unproved applicable Site/category") with no state-by-state table. A builder must choose the COMPLETE/PARTIAL/UNKNOWN boundaries for E and M.
- S7: "`workflow_label` (or `plan_active` boolean)" leaves the wire field to the builder. Pick one name, type and the exact label strings.

Spot-checks
- B3 CLOSED. Window [10-06,10-07), known_at omitted, `pin_read_at` and a frozen read clock, P01 `power_estate` producer, `mixed_replay` without its F03 KOBO import, and `two_ev_sites` are all named. These exist on main: `mixed_replay` (golden:278), `power_estate` (index:499), `pin_read_at` (:392), `install_second_ev_site` (money:192), `two_ev_sites` (money:219, a fixture), `imported_before` (:93). The stop-and-return rule covers a producer that fails. Residual: composing the `power_estate`/`two_ev_sites` pytest fixtures without their DB reset is left to the builder, but it is bounded by that rule.
- B1/B2 CLOSED. Four selectors are named with signatures, `_findings/_actions/_evidence/financials_body` are the existing consumers (found at index:164,223, evidence_money:428, financials:387), Lane A is the sole editor, and the handoff order is stated (B -> A 0a -> review -> B 0b/1a/1b -> A mount -> A nav -> B run 3). Small note: current bodies also take `admit`; the selectors take a prebuilt `scope` (`_scope` at index:77), which is consistent.
- B4 CLOSED. The exact (Finding, revision) join is kept. The 10-06 cells show `No accepted Action` / `Recommendation not accepted`. Workflow words are proved in a separate [11-01,11-03) persisted test, and the origin-revision-not-selected state has fixed copy.

Read index: all six runs have a "read only these sections" column, but it points at closure and section names, not line ranges. It is usable (each closure has headed subsections), and run 3's "closure 1 disclosures/progress" is the coarsest. The Lnn ranges from the re-check table (L1a etc.) were dropped.

New questions: (1) S7 field choice above. (2) The frozen clock is max(power.runner.now+1min, db_now, cold/EV recorded+1us). If cold/EV freeze at db_now before power, an earlier-than-head read is possible, so assert head <= frozen before the Portfolio read (the spec already says to). No other new questions.
