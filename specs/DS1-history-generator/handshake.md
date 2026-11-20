# DS1 handshake (one combined round, RULES §4 items 6-7)

Status: **open**. Code waits until this round is closed.

How the round works:
- The Reviewer (after reading `spec.md`, `reviewer-guide.md` and `rulings.md`) and the Implementer (after a pre-flight
  of `spec.md` against `main`, against the pack at `d9329b582` and against the mock-up at `task/uiux-guide` head) write
  their questions here in one batch, numbered R1… and I1….
- Each question cites the spec section, says what is unclear, and says what answer the writer expects.
- The Architect answers every question once, in `rulings.md` under "Handshake answers (round 1)", and folds the answers
  into `spec.md`.

## Questions the Architect expects (answer these first if you raise them)

1. **§8.1 extraction.** Does extracting `observe_side` change dict insertion order or the `money()` path for October?
   (Expected answer: no. P8 proves it.)
2. **§6.1 `share` on an `anchor` whose October whole is 0.** None exists in the world today. Should it be refused?
   (Expected default: refuse with `HISTORY_BOUND`.)
3. **§4.3 `scope_input`.** Does it include October's `bridge`? (No: the view drops `bridge`.)
4. **§6.1 jitter for `fixed`, `plan_value`, `per_day`.** These use no `R(f)`, so they have no jitter. Confirm.
5. **§7.1 `period_end`.** Is it a date only, or a story-clock instant? (A date, as October's `period_end`.)
6. **§9.4 G3.** Is the Portfolio overview alone the changed screen, or are the Site pages too? (Only the Portfolio
   overview; the Site tiles are unchanged, D5.)
7. **§3 DS1p's `history.json`.** It is produced from the DS1a worktree. Is DS1a merged first? (No: built and reviewed
   first, not necessarily merged.)
8. **§4.5 the fixture `view_v1.json`.** It lives on `main` and is derived from a pack file not on `main`. Is that
   acceptable? (Yes: it is a test fixture under `fixtures/`, regenerated only through `view`, with the pack commit
   named in its packet.)
9. **§8.3 P3 node list.** Which nodes exist per vertical? (Compare those present on both sides; a node absent on one side
   is a failure.)
10. **§10 test location.** Does `simulator/tests/world/` run under the existing `simulator` pytest configuration, or does
    it need a `conftest.py` for `--update-golden`? (Add `simulator/tests/world/conftest.py` with the option.)

## Reviewer questions

(none yet)

## Implementer pre-flight questions

(none yet)
