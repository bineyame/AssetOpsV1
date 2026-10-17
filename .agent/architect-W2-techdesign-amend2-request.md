# Architect request - final W2 design amendments (2026-10-17)

You are the AssetOps Architect (Codex). Read `.agent/W2-techdesign-rereview.md`. EV is ACCEPT; cold has R-M1 and R-M2. Edit in place, concise, no hedges.
- R-M1 (cold, carries to EV via W2-00): keep the message conflict target on every accepted-evidence insert; catch event and session-start collisions with a savepoint and re-read in the fixed order message -> event -> session; state which code wins on a double collision; restate the rule-8 guard regex and probes to match.
- R-M2: defer the cold vendor peer to the pilot gate exactly as EV does (or name format/units/module/refusals) - recommend defer for demo speed.
- Fold Lows L1-L6: fix the cold `normal` case so "no Finding" has a clear margin and specify post-restore behaviour; one half-open window convention in both docs (and the 13-reading count); EV money worker is `financials/recompute.py`; money work completion follows the fuel path's append-attempt pattern; widen the `finding_revision` domain CHECK in EV too; remove "ONE per attempt"; EV connector state after fault clear; name the module for hold/drop/fault transform variants.
Update `D-2026-10-17-w2-techdesign-cold`/`-ev` (amended). No code. Print a short summary.
