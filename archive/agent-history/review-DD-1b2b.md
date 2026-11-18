# Review: DD-1b2b (rehearsal finish, O1 link fix, drain, finish rows, after tool, EX-1)

Reviewer: fresh Claude (Opus), independent first review. Branch `task/DD-1b2-finish-rehearsal` at `455a08fd6`, diff `main...HEAD` (main has DD-1b2a at `29efab1d0`). Spec: DD1b2-R6 to R12 in `.agent/build-sheet-DD-1.md`. I did not edit code, write to any DB, tick, prepare, or run a suite.

## Verdict: FIX

The product change (O1) is correct end to end, and nothing in this diff puts product code at risk. Most of the restated R10 rows still assert what the demo needs. Two Medium items block. (1) The F-COH COH-17 allowance is much wider than the ruling. (2) Several owed items are neither closed, dropped nor moved by any ruling. Both are small to fix: one function tightened with its L0, and read-only measurements on the two DBs that are still kept, or an Architect ruling.

## Findings

### M1 (Medium): the F-COH COH-17 exception lets through every COH-17, not only the mill thread on week and month windows
- `tools/demo_combined_rows.py:191`: `if recurs and f["rule"] == "COH-17" and f.get("site_code") in (None, "KOBO-001")`.
- The ruling (R6 O4, entry text at build-sheet `:1559`) allows COH-17 only on the mill thread, only on week and month windows, and only with the named reason. Any other COH finding is a fault.
- `tools/checks/chain_coherence.py` emits COH-17 with `site_code` None for structural faults:
  - "a stamped bundle lacks the summary body" (`:1212`);
  - "a stamped bundle lacks this Why? body" (`:1296`);
  - "a stamped bundle lacks the `/estate/chain` body" (`:1376`);
  - "the `/estate/chain` window is not the requested one" (`:1381`);
  - the generic estate compare at `:1166`.
- Once `recurs` is True, which it is on this build, F-COH puts all of these in `allowed` and passes. COH-17 on any other Kobo thread or window passes too.
- The L0 (`backend/tests/test_demo_combined_finish_rows.py:53`) checks only the Site and the recurs flag. It has no thread or window must-fail case.
- **Failure scenario:** at E3's self-check, an estate `/chain` body comes back for the wrong window, or a Why? body is missing. F-COH reports pass, because the mill thread recurs.
- **Not live on this build:** `allowed_coh17` is `[]` in `var/demo3_dd1b2/check.json`.
- **Fix:** allow only COH-17 whose `site_code` is KOBO-001, whose window is `week` or `month`, and whose subject or row names the mill thread. Attach the `:1559` reason. Add must-fail L0s for a site-less COH-17, a COH-17 on the S window, and a COH-17 on another Kobo thread.

### M2 (Medium): owed items with no closure, drop or move
R11 §3 lists the owed, moved and dropped items. The items below are absent from it, from the packet and from the evidence files. R8 §A says "Nothing is dropped".
- **O8, the clone half.** R6 O8 and §6 step 8 ask for "the same six on the clone after the S+2 add, for S+2". The packet gives only (1), S+2 renewable selections = 6. Not reported: the S+2 study (queued, status, eligible), the thread events, the Grow and Assure rows, the Portfolio counts, and COH-17 for S+2. `dd1b2d` is still kept, so these are read-only reads.
- **O12.** The Grow contributor beside "No potential found yet" on S-8 and S-5 is not captured anywhere. `after.json` has no S-8 board, and its S-5 entry holds the headline only. DS-1's L6 line (R6 §4) depends on this capture.
- **O19.** How E2 runs `test_demo_combined_postgres` is not stated as such. The packet only says the copy line "applies to E2's copy of the E3 build".
- **R8 §A, the F-THREADS step-7 sub-items:**
  - the earnings, ONE-SOURCE and "Why?" price-line recompute ("Kept, asserted", figures on screen);
  - the links with an explicit `known_at`, listed in the packet (also R6 §8);
  - the Portfolio's plain landing for Cold and EV, stated;
  - the Protect "Why?" naming both Cold threads (asserted);
  - the MG-2 line, recorded;
  - "Action agreed" asserted on ACT-002/003. F-THREADS records `thread_states` but asserts nothing (`tools/demo_combined_finish.py` F-THREADS docstring: "reported either way").
- **Failure scenario:** these items go into E3 and DS-1 assumed done. For example, the price line on screen is never recomputed against the stored price, or the L6 line is scripted without the capture it depends on.
- **Fix:** take the reads on `dd1b2` and `dd1b2d` (read-only, tree form) and add them to the packet, or get an Architect ruling that moves each item (to E3, for example) or drops it. Either way, the packet should list each one.

### L1 (Low): EX-1's verdict lives only in the JSON, and one O9 key is always None
- `tools/demo_combined_ex1.py:183` returns 0 even when `comparison.passes` is false or `after_not_available` is set (`:179`). A scripted rerun at E3 would exit 0 on a changed board.
- `:71` reads `assure.get("count")`, but the Assure row has `counts`, not `count`. The valid run's `before.S.rows.ASSURE_PERFORMANCE` keys confirm this. So the `assure_count` O9 key is always None == None, and that part of the check is vacuous.
- `:73` takes "Action words" only from item texts that contain "trial" or "ACT-". Action text worded otherwise changes the whole-row diff but is not a failure.
- **In this run:** the valid run's whole-row diff was empty, so the measured claim holds.
- **Fix:** exit non-zero when `passes` is false or after any read that is not AVAILABLE. Read `counts`. Treat any change in an `in_hand` item as an Action-words failure.

### L2 (Low): evidence lineage for the step-7 claims
- **The after tool that ran is not the committed one.** `var/demo3_dd1b2/tree/tools/demo_combined_after.py` differs from `411817ae8`/HEAD: it imports `demo_combined_finish` at module top and sets `KOBO = fin.KOBO`, where the commit imports lazily. The behaviour is equivalent, but the packet says the copy is `411817ae8`.
- **O10 and O16 scripts are not committed.** Their results come from `o10_o16.py` in the session scratchpad and exist only as packet prose.
- **No `perf_budget --story` record was kept** (`--record` was not used). The packet's "0 breaches, 3 NOT MEASURED, 2 NO_BUDGET" cannot be checked, and it does not say which routes were NOT MEASURED. The tool's own docstring says NOT MEASURED "is never a pass".
- **MONEY-B (`tools/demo_combined_finish.py:842`) only reports.** It would pass with money on a steady day. That is as R8 ruled, but no gate remains for E3's self-check.
- **Fix:** recopy, or note the copy that ran. Put the O10/O16 output and the perf record in `.agent/DD-1b2b-rehearsal.json` or beside it. Name the NOT MEASURED routes.

### L3 (Low): the DS-1 carry is a subset
- What the packet carries is accurate:
  - the E2/E3 copy line matches R12 (c) word for word;
  - the serve line matches R11 §1;
  - the add-day timing line matches R11 §2;
  - the `--assess-now` clause matches R9 §2.
- R6 §8 asks for the R6 §4 DS-1 lines "with the measured numbers filled in". Not carried:
  - the full R6 §3 add-day replacement line;
  - the mill route line;
  - the R4 lines with "about 96 / about 22", now allowed by O14;
  - the Q7 "recurs" sentence;
  - the L6 line (which waits on O12);
  - the generator line;
  - R10 §4's two lines (month-start MG-1 and the Depot fault-day income).
- The rulings still hold all of them, so the coordinator can carry them from there.
- **Fix:** one block in the packet listing the full DS-1 set.

### L4 (Low): F-THREADS' `domain_action_index` read covers a window with no Action
- `tools/demo_combined_finish.py:821` reads the Cold failure window (16:00–17:05Z) and the EV fault window (08:00–09:00Z).
- Read-only SQL: ACT-000002 was raised at 17:15Z and ACT-000003 at 09:40Z, both after those windows. So `action_index_rows` is 0 on both Sites.
- The read proves only HTTP 200, which is the letter of R6 O5. R6 O5 also names "day and week boards", which this read does not cover.
- **Fix (optional):** read the Site-local day or the week, and record a row count ≥ 1.

## Focus answers

1. **R10 rows.**
   - Not weakened to pass:
     - **CO-5/SP-1 and SP-2:** UNKNOWN is accepted only with OBJECTIVE_NOT_JUDGED. PRODUCER_NOT_SETTLED, OBJECTIVES_NOT_READ and a None reason all fail, each with an L0.
     - **SP-4:** now a strict set equality against `expected_index_gaps`, plus a non-empty assert. The must-fail L0 removes the night run.
     - **WK-1:** money on a "Not known yet" line fails, and so does a known line with no money.
     - **WK-2c:** the kW and money bars apply to both the node and the chip.
     - **WK-4:** the new branch needs both `complete == 0` and "sales not recorded".
     - **F-CAL:** NO_DATA is asserted on every unbuilt day before today, with a non-vacuous assert.
     - **F-THREADS:** asserts `verification is None` and checks the verdict page for VERIFIED.
   - **F-COH's stored-study expectation** follows R10, with eligible ≥ 1 from the latest revision. Stored `[5, 1, 0, 0]` gives 2, which equals what is served. Residual: the expectation now tracks the product's own stored rows, so it cannot catch a wrongly created study. R10's own measurement of the recurrence covers that for this build.
   - **The exception is the COH-17 allowance (M1).**
2. **O1 end to end: correct.**
   - `refs.py`: the kind is added, `href_for` gives `/sites/{s}/domain-actions/{id}/verification` with no query, and `domain_verdict_ref` is added.
   - `site_chain.action_wire_ref` keys on DOMAIN_INTENT plus `origin_opportunity_id`. The loader selects that column (`postgres_chain_read.py:86`).
   - Frontend: the Ref union, the `routeFor` case to `siteMillVerificationHref`, and a route registered at `App.tsx:501`. The shared fixture row is added.
   - Cold and EV refs stay ACTION. That is measured in `check.json` F-THREADS: ACT-000002 and ACT-000003 are ACTION, and the mill ref is DOMAIN_VERDICT.
   - No other enumeration of Ref kinds exists outside these files.
3. **EX-1 guards.**
   - The tree-form guard has a must-fail L0.
   - The S2 then Performance reruns use Demo children. A failed child raises, and the AVAILABLE assert runs on S and S+1 before the add.
   - The whole-row compare has L0s for a `read_state` change, a new Finding, the Assure headline and a trial line.
   - Gaps are in L1: exit 0, the vacuous `assure_count`, and the narrow Action-word filter.
   - The valid run (`.agent/DD-1b2b-rehearsal.json` run 2) confirms the packet: AVAILABLE before and after, an empty diff, add 58.9 s, tick 180.1 s, 1 tick, S+2 selections 6.
4. **Owed list.**
   - Closed with evidence or a ruling: O1, O2, O3, O4, O5 (partly), O6, O7, O9, O10, O11, O13 (moved, R11), O14, O15, O16, O17 (dropped, R11), O18, O20.
   - Not closed: O8 (the clone half), O12, O19 and the R8 §A sub-items (M2).
   - **Measured claims I checked against the evidence files all match:**
     - manifest wall 3584.9 s of 10800, with the step timings as in the packet;
     - drain-1: 3 ticks, N=4, done, all counts 0;
     - drain-2: 1 tick, N=2, done, all counts 0;
     - all three prebuild logs end `"requests": 23 ... "non_200": {}`;
     - O14: 96.4 / 22.4;
     - O8 studies and thread events;
     - `check.json`: 31 pass, CO-2 fails with STALE_PROJECTION;
     - O16 by my own read-only SQL: 11 rows on 3 findings (4/4/3), all PRICED, AVAILABLE, quantity 0, price 1.25, amount 0.00 USD.
   - The tree copies of `demo_combined_finish.py` and `demo_combined_rows.py` are byte-identical to HEAD. `demo_combined_after.py` is not (L2).
5. **Carry lines.** Accurate where present; the DS-1 set is incomplete (L3).
6. **Regression risk.**
   - The product change is two small functions plus the frontend case.
   - The Ref change applies only to DOMAIN_INTENT Actions that have an origin opportunity, and only the mill Action has one.
   - `test_ch9b1_origin_readers` raises its allowlist count for `site_chain.py` from 3 to 4. That is the declared new reader of `origin_opportunity_id` (R8 D).
   - The `demo_combined.py` changes are tooling only (drain, manifest-in-finally, cap). `EXPECTED_SECONDS["mill"/"drain"]` are not used by the cap formula, which is inert and as ruled.

## Checks I ran
- **pytest (plan2 venv, worktree PYTHONPATH, no DB URL set):**
  - files: `test_dd1b2b_action_ref.py`, `test_dd1b2b_drain.py`, `test_dd1b2b_drain_failure.py`, `test_demo_combined_ex1.py`, `test_demo_combined_finish_days.py`, `test_demo_combined_finish_rows.py`, `test_demo_combined_mill.py`, `test_ch9b1_origin_readers.py`, `tools/checks/test_perf_budget.py`;
  - result: **81 passed, 4 skipped** in 4.5 s;
  - the 4 skips are the L2 cases in `test_dd1b2b_drain.py`, because `ASSETOPS_TEST_DATABASE_URL` was not set.
- **`npx.cmd tsc --noEmit`** in `frontend`: exit 0.
- **`npx.cmd vitest run`** on `routeRefs.test.ts` and `millVerification.test.tsx`: **67 passed** (2 files). node_modules was present, and vitest ran in this session.
- **Read-only SQL on `assetops_demo3_dd1b2_test`** (`default_transaction_read_only=on`): the `domain_action` rows and `financial_consequence_revision`.

## Not verified
- **Not run, under the dispatch's limits:**
  - `test_ch5a2_refs.py`, which consumes the touched fixture. Its expected path is identical to the one `test_dd1b2b_action_ref.py` asserts and that passed.
  - The guard scripts (`check-architecture`, `check-agent-workflow`), which need `-ExecutionPolicy`.
  - The drain L2s.
  - O10's `delivered_days` read, which needs the tree-form backend. I did not rerun it.
  - The O13 browser path (moved to E3).
  - CO-2 under `serve` (E3).
- No full suite on this revision is cited in the packet. None was required (R6 §6 bars it).

## Residual risk not named in the packet
- `dd1b2d` carries extra writes. It is fine as a disposable clone, but it should be dropped after the verdict, as planned.
- On demo day, F-COH's stored-row expectation cannot tell a correct second occurrence from a spurious one. Only R10's one-time measurement stands behind "Recurs".
