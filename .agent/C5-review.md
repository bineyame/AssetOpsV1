# E4-C5 review: board reads Cold/EV thread lifecycle at `k`

Reviewer: fresh Claude reviewer (independent of the builder). Diff: `git diff main...task/E4-C5-board-lifecycle-cutoff`
at b1311c080 (build 84e02c10c). Spec: D-E3b.1-3 ("E3b stop ruling", plan2 build sheet).

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. Three Lows, none blocking.

## Questions settled

1. **No future leak.** `read.py:498-501` passes `known_at=lifecycle_cutoff(known_at)`, which is the raw request value
   (`chain/read.py:41-45`). The LOOKUP SQL bounds every event by `coalesce(cause_known_at, recorded_at) <= :k`, and
   `state_on` (`lifecycle.py:192-201`) bounds by the board day. So an event after the viewed `k` never shows. Live
   (`None`) sees all known events, but only those effective on or before the board day.
   - Unchanged: `visible_at=known_at`, `day=board_day`, and `facts.known_at=cutoff` (`:489`). `facts.known_at` has
     no other reader.
   - Mini is unchanged because `board_cutoff(MINI, k, …)` is `k`. So the opportunity read inside `lookup`
     (`postgres_thread_sources.py:246`) gets the same value as before.
   - The evidence ports (`cold_ports` / `ev_ports`, `_domain_actions`, fuel, opportunity) already took the request
     `known_at`.
2. **Consistency.** `threads.lookup` has only one caller in the backend (`read.py:498`). Every other request-time
   thread or lifecycle read uses the request's `k`:
   - Portfolio `attach_threads` (`portfolio.py:154`), as `lifecycle_cutoff(scope["k"])`;
   - claims and `/chain`, through `ChainRequest.k`;
   - mini `ChainThreads` (`read.py:303`).
   The remaining reads at an evidence cutoff are all evidence:
   - `cold_heads_on` (`cold_site_reads.py:259`);
   - EV money (`ev_site_reads.py:348-351`);
   - the estate `evidence_cutoff` callers;
   - `dated_lead`.
   One nuance: a live Portfolio read resolves `k` to its read instant (`index.py:322`), while the board passes `None`.
   Both see every event recorded so far, so they agree.
3. **COH-13 extension.** It is correct, and it matches D-E3b.2 (board or Portfolio).
   - A Finding with no thread gets `thread=None` (`board.py:1135`). The `isinstance(t, dict)` guard skips it, so a
     Finding listed before any thread exists does not false-fail.
   - The rule fires only when a thread exists but has no state on its `state_day`.
   - The builder's in-process client3 proof found COH-13 = [] across 19 pairs (claimed; I did not rerun it).
   - The residual risk is in L2 below.
4. **The changed assertion** (`test_ch5a1_r1_visibility.py:67`) is a legitimate re-pin.
   - The old assertion pinned the cold board's state bound at the evidence cutoff. That is exactly the class of
     assertion D-E3b.2 item 3 allows to change.
   - The `visible_at` assertion is untouched, so occurrence visibility did not move.
5. **Stored responses.** The `request_key` is unchanged (it is built from request parameters).
   - `code_version` hashes every backend source file (`watermark.py` docstring), so the edit to `read.py` changes it.
   - Rows composed by old code are never hit, and `prune` never evicts another version's rows.
   - A fresh prepare/prebuild under the merged code stores new rows.
   - Thread writes reach W through `chain_input_change`, the same as for the Portfolio and `/chain`.

## Findings

1. **Low:** `backend/assetops_backend/chain/adapters/postgres_thread_sources.py:241-243`. The `lookup` docstring still
   says "`known_at` is the board's state cutoff (story time for cold/EV)". That is now false. Fix: describe it as the
   request cutoff `k` (`lifecycle_cutoff`, D-E3b.1).
2. **Low (residual risk):** `tools/checks/chain_coherence.py:1024-1048`. On a historical `k`, a Finding can be visible
   while its thread's OPEN was recorded after `k`, for example when the chain build lags the Finding. Such a Finding
   reads `state` None and now fails COH-13. F-COH collects live (`known_at=None`), so this cannot fire on the demo
   build's F-COH. A future time-travel bundle could hit it. If that happens, rule on it rather than relax the check.
3. **Low (test gap):** `backend/tests/test_e3b_board_lifecycle_cutoff.py:79`. The mini case is parametrized only at an
   explicit `k`. A live (`None`) mini call is not pinned. Mini is unchanged by construction (`board_cutoff`), so the
   gap is cosmetic.

## Checks run (this reviewer, c5 worktree, plan2 venv, one file at a time, 2.3 GB free)

| Check | Result |
|---|---|
| `backend/tests/test_e3b_board_lifecycle_cutoff.py` | 5 passed (1.25 s) |
| `backend/tests/test_ch5a1_r1_visibility.py` | 5 passed (1.16 s) |
| `tools/checks/test_chain_coherence.py` | 181 passed (8.86 s) |
| `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` = plan2 venv) | "Architecture check passed.", exit 0 |

## Not verified

- I did not rerun the other files in the packet's table: ch2_threads, ch3_rows, ch5a2_contract,
  e4_portfolio_lifecycle_cutoff, r4_domain_row_thread_state, demo_combined_finish_rows, ch5a1_board_contract and
  ch5b_why.
- I did not rerun the client3 in-process F-COH/F-COH3 proof (20 min).
- I did not run `check-agent-workflow`.
- No frontend change, so no frontend checks apply.
- I did not reproduce the fail-on-main proof.
- R4.1 on a fresh build (client4) is still owed (D-E3b.3).
