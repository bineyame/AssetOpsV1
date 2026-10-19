# Architect request: W2-07 build questions (q1)

You are the AssetOps Architect. Read these first:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide" and "Token Efficiency".
- `.agent/W2-07-build-spec.md`: all of it, including the reconciliation.
- On branch `task/W2-07-ev-site-evidence-money`, commit `12158d3d`:
  - `.agent/W2-07-pending-rulings.md`, which holds R1–R6;
  - `.agent/W2-07-phase-handoff.md`.

  Read them with `git show task/W2-07-ev-site-evidence-money:<path>`. The code is in that commit.
- The cold equivalent, W2-04 (`.agent/W2-04-build-spec.md` rulings). Check how W2-04 made the diesel/fuel assumption visible at a simulated replay cutoff, since the publisher stamps the real `recorded_at`. Mirror that solution unless it is unsound.

The builder stopped after commit 1. Rule on R1–R6 exactly.

**R2 is High: no tariff is ever visible at the simulated cutoff.** Give:
- the literal mechanism: the fixture channel, `recorded_at`, the visibility predicate, and the tests;
- confirmation that the ESTIMATED vectors (for example `8.33250000`) become reachable unchanged, or their literal new values if they change.

**R5 and R6.** Give a full precedence table and a mixed-window pricing table, with reason codes and copy.

**R1, R3 and R4.** Confirm or replace each, with the literal trigger/test change.

Then dry-read spec commits 2–5 once more against the commit-1 code. Answer any remaining question with concrete artifacts. If none remains, say so in one line.

Append everything to `.agent/W2-07-build-spec.md` as "Run 1 rulings (q1)", amending `D-2026-10-18-w2-06-07-buildspec`. Write nothing else. Do not commit.
