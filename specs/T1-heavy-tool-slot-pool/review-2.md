# T1 review, round 2 (verification of fix round 1, W5/W6)

Reviewer: fresh Claude reviewer, 2026-11-19. Diff `6aea4669a..48c847dfd` (code `3bca18cfe`, packet `48c847dfd`).

## Summary

- **Verdict: ACCEPT WITH FIXES.** The original M1 defect is fixed. One new Medium (M2) comes from the 2 s
  INT/HUP delay: a group Ctrl-C now cuts any cleanup longer than 2 s short. Fix it on the branch, then run a
  narrow re-review of M2.
- M1 reproduced as fixed: the bash-pooled child has SIGINT restored, and a group INT runs a short `finally`
  (exit 130, slot free). P7c fails with `trap - INT QUIT;` removed (`stdout started`, no `cleanup ran`).
- A signal sent to the wrapper alone is not lost. It reaches the child after 2 s.
- L1, L2 and L4 are fixed. L3 is partly fixed, and its documented gap is acceptable. L5 and L6 appear as gaps
  in the packet only (L-a).
- No regressions: pool self-test 32/32 pass, 23.1 s; inventory 7 pass, 1 todo (`7b`: 5 lines), 0 fail.

## Findings

### M2 (Medium, blocking). The forwarded INT cuts a group Ctrl-C's cleanup short after 2 s

- **Where:** `tools/heavy-slot.sh:257-268` (the 2 s wait, then `kill -"$2"`), and `:270-276` (KILL 5 s later).
- **Reproduced:** the wrapper runs in its own session with default dispositions. The job is a `python3` script
  whose `finally` sleeps d seconds.

  | Signal | d = 0.3 | d = 3 | d = 9 |
  |---|---|---|---|
  | `kill -INT -<pgid>` | cleanup ran | **cleanup INTERRUPTED after 2.0 s** (second KeyboardInterrupt) | **INTERRUPTED after 2.0 s** |
  | `kill -INT <wrapper>` | cleanup ran (2.4 s) | cleanup ran (5.1 s) | **SIGKILLed at 7.1 s**, no output |

- **Why it matters:**
  - The packet says the delay ensures "a second KeyboardInterrupt cannot cut the `finally` short". That holds
    only for cleanup under 2 s.
  - Pytest Postgres teardown (DROP DATABASE in `backend/tests/pg_harness.py`, `setup_cache.py`) and the `--db`
    jobs are the cleanups M1 meant to protect. Unpooled, their cleanup has no time limit.
  - P7c's 0.3 s `finally` does not reach this case.
- **Fix (the Implementer chooses):**
  - Do not forward INT/HUP when the signal already reached the child. For example, skip the forward when the
    wrapper's process group is the terminal's foreground group (`tpgid == pgrp` in `/proc/self/stat`), which
    is the Ctrl-C case.
  - Or wait for the tree for much longer (for example 30 s) before forwarding and before KILL, and state that
    bound in D-T1.15.
  - Add a P7c variant whose cleanup is longer than 2 s.

### L-a (Low). L5 is recorded only in the packet

- **Where:** `packet.md:135`. The durable list is `spec.md:335` ("Documented gaps"), and review-1 named
  `backend/TESTING.md` or spec §5.2 as the place for it.
- **Fix:** add one line there. L6 in the packet is enough.

### L-b (Low, residual). The pwsh wrapper on Linux: Ctrl-C ends the child with no cleanup

- **Where:** `tools/heavy-slot.ps1:130` (INT runs `Stop`, which sends TERM at once).
- **Observed:** a group INT and a wrapper-only INT both gave rc 130 after 0.0-0.1 s. The `finally` wrote
  nothing, even to a file.
- **Why it is Low:** Linux agents use `heavy-slot.sh`. On Windows, Ctrl-C is a console event, not this path.
- **Fix (optional):** forward INT, as the bash half does, or note the limit in D-T1.15.

### L3 gap: accepted

- Bare `pytest`, `npm run typecheck` and `npm run build` are not matched; matching them flags about 20 prose
  mentions. The §6 documents were clean in review-1.
- A line with no backtick that mentions the wrapper anywhere before the pattern still passes. That is the same
  class of gap.

## Checks run

- Pooled `node --test tools/checks/test_heavy_slot_pool.mjs`: 32 pass, 0 fail.
- `node --test tools/checks/test_heavy_slot_inventory.mjs`: 7 pass, 1 todo, 0 fail.
- Mutant P7c, run in a scratch copy of `tools/` with `trap - INT QUIT;` removed: fails.
- Manual SIGINT matrix for the bash and pwsh wrappers, as above. `--status` afterwards: all slots free.

## Not verified

- The Windows branch of `heavy-slot.ps1`.
- Real terminal Ctrl-C with a tty. The tests used a group `kill`, which is equivalent for delivery.
- Stale `/tmp/t1-pool-97TfPe` and `/tmp/t1-pool-BLp4NI` are still present, from before review-1. I did not
  touch them.
