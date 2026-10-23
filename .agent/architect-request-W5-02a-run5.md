# Architect request: W5-02a run 5 STALE/UNKNOWN producer question

You are the AssetOps Architect (Codex). Read the latest Run entry and open question at the end of `MSYS_NO_PATHCONV=1 git show task/W5-02a-cold-action-root:.agent/W5-02a-phase-handoff.md` (head `2dba4236`), then "W5-02a build rulings (K1c)" rulings 2 and 3 in `.agent/W5-02-build-spec.md`, and the producer `tools/w502_cold_work_cases.py` on that branch.

The parser accepts only observation rows before `end`, but the run always publishes the probe reading at `end`, and the window closes 5 minutes later. So the last probe can never be suppressed, and the stale and no-probe inputs both read CURRENT, with only a start-failure Finding. The builder lists three options:
- (a) shorten the end time;
- (b) use W5-01's wider-window route;
- (c) always seed for UNKNOWN.

Rule one, with literal inputs, clocks, the expected states and tests, so that the STALE and UNKNOWN states are produced honestly. Read the real parser and replay code first.

Append "W5-02a build rulings (run 5 STALE/UNKNOWN)" to `.agent/W5-02-build-spec.md`. Write nothing else. Do not commit. End your output with one line saying which option you chose and the files involved.
