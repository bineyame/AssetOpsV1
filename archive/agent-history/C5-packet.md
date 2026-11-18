# E4-C5 review packet: the board reads Cold/EV thread lifecycle at `k`

Card: D-E3b.2, `AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md` (5fd85d7d8), "E3b stop ruling".
Branch `task/E4-C5-board-lifecycle-cutoff`, cut from main 5fd85d7d8. Build commit 84e02c10c.

## Outcome delivered

1. `site_outcomes/read.py` `board()`: `self.s.threads.lookup(..., known_at=lifecycle_cutoff(known_at), visible_at=known_at, day=board_day)`.
   The raw request value is used, as `chain_api.py:185` does. Unchanged: `visible_at` (R-1), `day=board_day`,
   `facts.known_at=cutoff`, every evidence read, the opportunity read and the mini boards (whose cutoff was already the
   request's). The comment cites CH6b2-R2 and D-E3b.1.
   - **Pre-flight result:** no other board-side lifecycle read uses the evidence cutoff. Action reads
     (`_domain_actions`, `domain_actions.index`) already take the request `known_at`. `dated_lead` is evidence-window
     only. `facts.known_at` has no reader in `site_outcomes/` besides the lookup. Nothing else moved.
2. COH-13 (`tools/checks/chain_coherence.py`): new `_stateless_threads`. In a lifecycle-stamped bundle, a board FINDING ref
   thread, or a Portfolio row thread, that has a `state_day` and `state` None is a COH-13 finding, with detail
   "listed Finding with no thread state" (one per window per Finding). It runs before the pair comparison.
3. Tests: a new no-DB file `backend/tests/test_e3b_board_lifecycle_cutoff.py` (a fake `threads.lookup` records its
   kwargs and shows ACTION_IN_HAND only when `known_at` reaches an event 40 min after the evidence cutoff):
   - (a) Cold and (b) EV, live (None) and at an explicit `k`: the lookup `known_at` equals the request value,
     `visible_at` equals the request value, and `window.known_at` stays the evidence cutoff. The board's FINDING thread
     reads ACTION_IN_HAND.
   - (c) Mini (Kobo): the call is unchanged (`known_at`=`visible_at`=request, board day, opportunity extras).
   - The COH-13 fixture test in `tools/checks/test_chain_coherence.py`: a both-None pair fires on both sides.

## Changed assertions (the full list)

- `backend/tests/test_ch5a1_r1_visibility.py::test_board_shows_an_occurrence_created_after_the_story_cutoff`. It was
  `call["known_at"] is not None and call["known_at"] != call["visible_at"]`, which pinned the Cold board state at the
  evidence cutoff. It is now `call["known_at"] == request_known_at`. The `visible_at` assertion is unchanged, so
  occurrence visibility did not move. The docstring and the module docstring were updated to match.
- No other assertion changed. No existing COH fixture relied on a None state: grep found no `"state": null` in any
  fixture bundle, and all 181 chain-coherence tests pass unchanged.

## Proof that the tests fail on main

With `read.py` and `chain_coherence.py` checked out from main (tests at HEAD), then restored with
`git checkout HEAD --` (tree clean afterwards):
- `test_e3b_board_lifecycle_cutoff.py`: 4 failed (all the Cold/EV cases), 1 passed (mini, unchanged by design).
- `test_ch5a1_r1_visibility.py`: 2 failed (the changed assertion).
- `test_chain_coherence.py -k no_thread_state`: 1 failed.

## Checks run (c5 worktree, plan2 venv, one file at a time, at 84e02c10c)

| File | Result |
|---|---|
| test_e3b_board_lifecycle_cutoff.py | 5 passed |
| test_ch5a1_r1_visibility.py | 5 passed |
| test_ch2_threads.py | 28 passed |
| test_ch3_rows.py | 42 passed |
| test_ch5a2_contract.py | 26 passed |
| test_e4_portfolio_lifecycle_cutoff.py | 7 passed |
| test_r4_domain_row_thread_state.py | 6 passed |
| test_demo_combined_finish_rows.py | 63 passed |
| tools/checks/test_chain_coherence.py | 181 passed |
| adjacent: test_ch5a1_board_contract.py / test_ch5b_why.py | 13 / 48 passed |

No full suite was run (demo-sprint policy). `check-architecture` / `check-agent-workflow` were not run.

## Step 4: in-process proof on client3 (read-only)

Script: scratchpad `c5/run_fcoh.py`. It imports `demo_combined_finish` from the c5 worktree and asserts that the
modules load from c5. It runs `f_coh` and `f_coh3` against `assetops_polish_client3_test` with work
`AssetOpsV1-e3b/var/polish_client3`. The bundle temp dir is redirected to the scratchpad, and the work folder is
snapshotted before and after (size+mtime of every file, plus the `tree` and root mtimes): **unchanged: true**. Wall
time was 20 m 17 s, with 336 requests.

- **F-COH: pass.** Allowed: 5 COH-2 (BL-47), 0 COH-17. Unplaced: none.
- **F-COH3: pass** (COH-10 fired 1).
- **COH-13: [] (no findings),** including the new stateless rule. 19 pairs were compared, so the set is non-empty.
- **The 8 E3b pairs are all present and equal:**
  - EV `day:ev:fault:2026-11-03`, Finding 40f8aab8 (week, month): board (ACTION_IN_HAND, 11-03); Portfolio
    (ACTION_IN_HAND, 11-03).
  - Cold `day:cold:failure:2026-11-07`, Finding 4971d884 (week, S, month): board (ACTION_IN_HAND, 11-07); Portfolio
    (ACTION_IN_HAND, 11-07).
  - Cold `day:cold:failure:2026-11-07`, Finding 0be04880 (week, S, month): board (OPEN, 11-07); Portfolio (OPEN, 11-07).
- On both E3b boards, every listed Finding now has a state. EV shows ACTION_IN_HAND ("Pending"). Cold shows
  ACTION_IN_HAND for 4971d884, and OPEN for 0be04880. The second matches D-E3b.1's table: the thread opened at 17:10Z,
  with no Action, and the Portfolio also reads OPEN. So not all 8 pairs are ACTION_IN_HAND: 5 are in hand and 3 agree
  at OPEN.

## Known deviations

- The step-4 DB was accessed only through the product's GET routes and F-COH's SELECT. I did not audit whether any
  GET route writes cache rows. The work folder was proven unchanged.
- `_coh` normally writes its bundle under `ctx.work`. That was redirected to the scratchpad so the client3 tree stayed
  untouched.

## Residual risk / review focus

- COH-13 now fails any listed Finding whose board or Portfolio read has no state, not only paired reads (the card's
  literal wording). On client3 it raised nothing. A future build where a board lists a Finding before its thread's OPEN
  day would fail COH-13. That failure is by design (D-E3b.2).
- The proof for R4.1 on a fresh build (client4) is still owed, per D-E3b.3.

USER_REVIEW: none required for this slice (fresh Claude review; only High or Medium findings block).
