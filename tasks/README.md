# Task queue

The live queue is short: no task packet in this folder is open. Current work and
its specs are in [.ai/NOW.md](../.ai/NOW.md); new specs go to `specs/<ID>/` with
a row in [specs/INDEX.md](../specs/INDEX.md) (`.ai/RULES.md` §9). Direction:
[.ai/START_HERE.md](../.ai/START_HERE.md).

History in this folder:

- The S1-S7 queue tables (built; no longer machine-read since declutter step 5
  retired the S1-S7 delivery checker): [archive/site-first-2026-10/queue-tables.md](archive/site-first-2026-10/queue-tables.md).
- The S1-S7 narrative: [archive/site-first-2026-10/README.md](archive/site-first-2026-10/README.md).
- The packets at this folder's root are finished slices (built-state history,
  not instructions); `completed/` and `archive/` hold older ones.
