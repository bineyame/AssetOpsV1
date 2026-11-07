# DD-1b2b pre-flight (builder, Claude, 2026-11-07)

Worktree `AssetOpsV1-dd1b2`, branch `task/DD-1b2-finish-rehearsal` at `e7a9f494b`. Card: `build-sheet-DD-1.md` "DD1b2-R6". No product code written, nothing built, no DB written or dropped, no `npm ci`. The only DB access was one read-only session (`default_transaction_read_only = on`) listing `pg_database` and `pg_stat_activity`. **MEASURED** = a grep, a query or an offline computation I ran; **READ** = code read.

## 1. R6 §1 corrections: both CONFIRMED

**(1) No screen renders the mill thread's Action ref. CONFIRMED.**
- MEASURED (grep over `frontend/src`, `*.ts`/`*.tsx`, tests and fixtures excluded): the only chain URL builders are `sites/chainClient.ts:72` and `:81`, both `/chain/why`. No file builds or fetches `/chain` (site list) or `/threads/{id}`; `threads` occurs in no non-test source file.
- READ: `/chain/why` carries no Action ref. `chain/why.py:241-246` emits an action node from `a["id"]`, `code` and `verification` only. `actions_of` (with the wrong `ref`, `site_chain.py:143`) reaches the wire only through `chain_api.py` (`/chain`, `/threads`), and inside the backend through `why.py:288`, which drops the ref.
- READ: `routeFor` returns null for THREAD (`shell/operatorSiteRoutes.ts:581-584`).
- So the 404 is a wrong `ref` on the API wire, as R6 says. O1 still goes in.

**(2) The scan looks back 5 days from wall time, so S-1's study decides recurrence. CONFIRMED, with one sharpening.**
- READ: `SCAN_BOUND = timedelta(days=5)` (`mini_decisions/worker.py:46`). The scan reads heads with `window_start >= _scan_at - 5 d` (`:155-156`, `store.py:350`). `_scan_at` is `store.db_now` unless `jobs.test_clock_override` is set (`:113-115`).
- MEASURED (grep, `test_clock_override\s*=` outside tests): the only setter is `tools/demo_combined_mill.py:97`, which runs `reconcile` and then `run_pending(..., scan=False)` (`:102-103`). `drain_mini` runs the mini-depth worker, not this one. So the first scan is the first tick's `opportunity` stage (`scheduling/tick.py:461`, `run_pending` scan default True, `worker.py:271-272`), at DB wall time.
- MEASURED (offline `resolve_story`, b22 baseline, wall 2026-11-07 14:00Z): S = 2026-11-05, so S-3 = today − 5 and S-1 = today − 3. Kobo PV hours are local 08:00-13:00 (+03), so `window_start` runs from 05:00Z to 10:00Z (diagnosis §1).
- **Sharpening:** a study ending S-3 is queued if *any* S-3 head is inside the bound at the first tick. The last head (10:00Z) falls outside once the tick runs after **10:00Z on S+2** (today, if step 6 starts today). Step 6 cannot reach its first tick before then, because steps 2-5 come first. So S-3 is report-only, as ruled.
- S-1's heads (05:00-10:00Z, today − 3) stay inside the bound until today + 2 at 05:00Z. Any tick in this unit queues S-1's study.
- READ: in the whole list S-3 is kind `late`, with `received_at` S-1 12:30 and `assess: build` (`demo-story-days-v3.json:47-50`). That is in the past at build time, so its evidence and mini jobs land before `drain_mini`, and the heads exist.

## 2. Measured state for the planned actions

- `pg_database`, MEASURED: of the spent DBs, `assetops_demo3_dd1b2p_test`, `..._dd1b2q_test` and `..._dd1b2r_test` exist; `m` and `n` do not. 0 sessions on any `dd1b2%` DB. `assetops_demo3_dd1b2_test` and `..._dd1b2c_test` do not exist yet.
- Folders, MEASURED: `var/demo3_dd1b2{m,n,p,q,r}` exist (97 + 143 + 306 + 306 + 328 MB). `var/demo3_dd1b2` and `var/demo3_dd1b2c` do not.
- `frontend/node_modules`: absent (MEASURED). `npm ci` is needed before tsc, vitest and serve.
- Whole list, MEASURED offline: 54 runs, of which Kobo 48 (47 delivering, one `missing`), Cold 3, EV 3. The trim was 32.
- Free RAM, MEASURED now (Win32_OperatingSystem, with `check-all` running on main): **3.0 GB free of 15.7 GB**.

## 3. Questions (batched; each has my recommendation)

**Q1. R8 done condition: two queues outside it decide O8. (Gap; ruling needed.)**
- O2 is done when dirty = 0, `snapshots` pending = 0 and Kobo mini `deferred` = 0. But the S-1 study is queued and run in the `opportunity` stage, at most 10 jobs per Site per tick (`tick.py:68,461`). Its thread placement then needs the `threads` consumer (`chain_threads` stage, which has its own `deferred`).
- So R8 can stop before RECURRED is placed. If it does, O8 reads "not queued" or "no RECURRED", which is a false §3 **Stop**.
- **Recommend:** add to the done condition live opportunity jobs (PENDING or LEASED) = 0 and `threads` pending = 0, both counted from the DB (`live_opportunity_jobs`; `PostgresEventStore.pending("threads", …)`). Same N/2N logic. If you rule no, I report both counts at each drain and read O8 only when both are 0.

**Q2. O8 and §3 key on the S-1 study only. Studies ending S+0 and S+1 also scan in, and on the whole list they hold S-3 and S-1.**
- The probe queued them with eligible 0 (review H1), but its list had no S-3 or S-1 data. On the whole list their five-day windows include S-3 and S-1.
- So "S-1 eligible 0, does not recur" can coexist with RECURRED placed from the S+0 or S+1 study. §3's table has no row for that.
- **Recommend:** O8(2) measures every queued study (ending S-3, S-1, S+0, S+1). "Recurs" means any of them places RECURRED, with its effective day after S-9. Under the current rows, the S-1 rows keep their stops. A RECURRED placed only by a later study is outcome "Recurs", reported with its source study.

**Q3. How R8 ticks: raw tick or `Demo.tick`?**
- `Demo.tick` runs performance_migration and `prebuild` after every call (`demo_combined.py:539-551`). Per drain iteration that is extra minutes on the 3 h cap.
- **Recommend:** each R8 iteration runs the raw `TICK --no-prebuild` and parses its JSON. After the drain completes it runs performance once and `prebuild` once. O11 reads every `prebuild` log; there are two, one per drain.
- The existing `finish` sequence stays: objectives, S2, `drain_mini`, `tick(2)`, then R8 drain 2, then self-check (F-DRAIN reads after drain 2). Confirm.

**Q4. R8's N: summed or per Site?**
- The tick drains up to 200 dirty rows **per Site** (`tick.py:75,526`). "ceil((dirty + pending)/200) + 2" summed over three Sites over-counts N, which is safe but loose.
- **Recommend:** N = max over Sites of the per-Site formula. This is the literal R8 formula applied per Site, and the counts are logged per Site.
- Alternatively, sum (looser, R6's literal wording). Either way it is not tuned.

**Q5. What does the 10800 s cap cover?**
- O3 puts mill, drain, finish rows, F-PERF and EX-1 timings in `manifest.json`. EX-1 runs on the clone after the prepare (step 8), and F-PERF could run inside the self-check or in step 7.
- **Recommend:** the cap bounds `prepare` only: children, after_children, both drains and `finish` with its self-check. F-PERF runs in step 7, from the private tree, timed into `manifest.json` under `post`. EX-1 is timed into its own evidence file and copied into the packet.
- O17's "wall ≤ 10800 s" applies to prepare + F-PERF. EX-1 is reported, not capped.

**Q6. Projection against the 3 h cap (risk, for information; no number moved).**
- Kobo: 47 delivering runs × about 105 s per run (the U3 figure behind `kobo_expected_seconds`) ≈ 82 min. Cold 5 min, EV 3.5 min.
- After the children: whole-list `drain_mini` (21 days × about 34 jobs, unmeasured at this size), backfill a and b,c,d, mill, two R8 drains (N unmeasured), objectives/S2/`tick(2)`, self-check, F-PERF (30 cold processes).
- **My unmeasured estimate is 120-160 min.** Under the cap, but not by much, and complement runs may not match the 105 s figure. On a cap hit I stop per §7, with per-step timings.

**Q7. Memory floor (risk; one ask).**
- 3.0 GB free now, with `check-all` running on main. The floor is 2 GB.
- **Recommend:** I start step 6 only when no other `check-all`, pytest or prepare is running (checked by process list, with PIDs reported) and free RAM is ≥ 4 GB. If free RAM does not reach 4 GB, I report and wait rather than start.
- **Ask:** does the coordinator hold other heavy jobs off for the 2-3 h, or should I poll and wait?

**Q8. Time of day for step 6 (risk).**
- Kobo's local midnight is 21:00Z. If the prepare crosses it, `site_today` moves to S+3 mid-run, which adds a NO_DATA day to F-CAL's set and moves the boards' "today".
- **Recommend:** start step 6 only if it can end before about 20:30Z under the cap. That means a start by about 17:30Z; otherwise the run starts the next morning. A next-morning run shifts S by a day, which is harmless because all reads are S-relative.
- EX-1's add needs ≥ 11:00Z on S+2 (O9), which then falls the following day. Confirm the latest start time, or say to ignore this.

**Q9. Scoped tests in step 5: Postgres modules.**
- `test_ch9b*` includes four `*_postgres.py` modules. O2's L2 needs a base DB too.
- **Recommend:** both run through `tools\run-host-tests.ps1` on base `assetops_dd1b2b_test`. The harness clones `<stem>_pt<run>_*_test` and drops at session end; I drop the base after.
- Confirm that `test_ch9b*` means the L2s too, or L0 only.

**Q10. Guard letters "A, W, N, V, M".**
- My mapping, from `tools/check-all.ps1:55-66`: A = Architecture seams; W = Agent workflow; N = Navigation truthfulness; V = the v69 dependency registry and screen ledger; M = mock deviation labels and client vocabulary. The missing-claim scan and its fixtures run in addition. Correct me if V or M means something else.
- I will also run `tools/checks/test_perf_budget.py`, since O4 changes `perf_budget.py`.

**Q11. O13 browser screenshots: tool.**
- **Recommend:** a scratchpad CDP script on the local Chrome, after the pattern of `tools/layout-evidence.mjs:120-132`, against `demo_combined.py serve`.
- Ports: the defaults are API 8990 and web 5490 (`demo_combined.py:57`). I will pass `--port 8991 --web-port 5491` so I do not collide with anything served from main.
- If Chrome is unavailable, O13 is recorded as not run, with the precondition.

**Q12. O7 text: what the "…" keeps.**
- **Recommend:** keep the ST-3 cell up to "(WN-6/7)." and replace everything from "The headroom opportunity is a thread" to the end of the cell with R6's text, capitalised "The headroom…". Confirm.

**Q13. O4 F-PERF `--story` is a new flag.**
- `perf_budget.py` today has `--fixture`, `--database-url`, `--work`, `--runs`, `--store`, `--report`, `--record` (`:178-185`); there is no `--story`. I build it per DD1b2-R Q9 (an optional date mapping from `<work>/story.json`, fixture path unchanged), with an L0 in `test_perf_budget.py`. The same goes for `chain_perf_probe.py:35-42`, if F-PERF calls it. No question unless you object.

**Q14. Mill-step failure inside step 6 (§6 note): confirming the rule.**
- If the mill step fails, I stop and ask, because recovery needs a second whole-list run and the owner's go.
- No pre-mill clone; `--stop-before-mill` stays development-only and is not used.

**No conflicts found between R6 and R-R5** beyond Q1 and Q2. O6 "WK-2c on S-11" is the board day: the pinned study is S-19 to S-15 (`demo-combined-story-v1.json:19`).

## 4. Planned order (after rulings)

| Step | What | DB / folder |
|---|---|---|
| 1 | Drop `assetops_demo3_dd1b2p_test`, `..._dd1b2q_test`, `..._dd1b2r_test` (0 sessions, `WITH (FORCE)` not needed). Delete `var/demo3_dd1b2m`, `n`, `p`, `q`, `r`. `npm ci` in `frontend` | drops only |
| 2 | O1: `chain/refs.py` (`DOMAIN_VERDICT`, `domain_verdict_ref`, `href_for`), `chain/site_chain.py:143`, `sites/chainRef.ts`, `shell/operatorSiteRoutes.ts` `routeFor`, `shell/__fixtures__/route-refs.json`, `__tests__/routeRefs.test.ts:15`, `test_ch5a2_refs.py`, new `test_dd1b2b_action_ref.py`. Commit | none |
| 3 | O2 `Demo.drain()` and `tick --until-drained`, O3 `--cap-seconds` and timings; L0 plus L2 on base `assetops_dd1b2b_test` (dropped after). Commit | L2 base |
| 4 | O4-O6, O9 (`tools/demo_combined_ex1.py`), O14-O16 rows and tools, L0s; O7 text. Commit (prepare archives HEAD) | none |
| 5 | Guards A W N V M, missing-claim scan and fixtures; scoped pytest; `tsc --noEmit`; vitest `routeRefs.test.ts`, `millVerification.test.tsx`. Possible handover point | none |
| 6 | Keep-awake on, 30 s sampler (scratchpad), stall monitor; `demo_combined.py --db assetops_demo3_dd1b2_test --work var/demo3_dd1b2 prepare --cap-seconds 10800` (no `--days`, no `--sites`) | `assetops_demo3_dd1b2_test`, `var/demo3_dd1b2` |
| 7 | O8, O10, O11, O13 (serve on 8991/5491), O14, O15, O17, F-PERF; finish-row faults fixed in the tool, then `demo_combined_finish.py check` rerun on the same DB | `dd1b2` |
| 8 | Clone `CREATE DATABASE assetops_demo3_dd1b2c_test TEMPLATE assetops_demo3_dd1b2_test` (serve stopped by PID, 0 sessions), copy `var/demo3_dd1b2` to `var/demo3_dd1b2c`; EX-1 after 11:00Z; O8's six for S+2 | `dd1b2c` |
| 9 | O18 commit, packet, `.agent/DD-1b2b-rehearsal.json`; both DBs kept until the review verdict | both |
