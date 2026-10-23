# Architect request: W5-F1 correction cards for the D3 departures on built screens

You are the AssetOps Architect (Codex). Read `.agent/mock-departure-register.md`, specifically the D3 rows R22, R37 and R38, along with the departure rule and mock-fidelity rules in `.ai/ROLE_CONFIG.md`. These three are on screens already merged to main. R23/R24 are already corrected in the planned W5-02/W5-04 specs; confirm that in one line.

Write `.agent/W5-F1-build-spec.md`: one small correction slice with at most 3 units, built at the level of a full build spec. Each unit card gives:
- the exact file list, including tests that will break;
- literal markup, copy and CSS;
- the producer and clock for captures;
- tests;
- the v69 element it restores (`cold-health` for R22: remove the added Data sources panel and repoint the Foundation link to the existing `cold-evidence` source panel; `cold-performance` for R37: restore the Loading / batch row in mock order; `cold-evidence-analysis` for R38: show labelled references or an unavailable state until the exact destination is proved);
- guard checks against the real `tools/checks/*`.

Then do a readiness self-check: an implementer dry-read against main, listing any decision left open. The list must be empty. Mark rows R22, R37 and R38 in the register with status "correction planned: W5-F1". Add a decision line `D-2026-10-23-w5-f1-d3-corrections` to `.ai/DECISIONS.md`.

Write only those files. Do not commit. End your output with the units and anything left open.
