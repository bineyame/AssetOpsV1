# Review DD-1b2a: the mill step (independent first review)

Reviewer: fresh Claude, 2026-11-07. Branch `task/DD-1b2-finish-rehearsal` at `2c69bbd6f`. Range: code and tools since `3d1871142` (pre-flight), no product change after `e513401e0` except the declared mill-tool literal.

## Verdict: FIX

**The code is sound. I found no defect in the seam rule, the store seam, the mill tool or `after_children`.** What blocks is two statements in the evidence, one High and one Medium. Both are about what the client will see on the Grow path, and DD-1b2b and DS-1 would otherwise inherit them as measured facts. The fix is paper plus one cheap measurement, not code in this piece, unless the Architect rules otherwise on M1.

## Findings

### H1. "No recurrence" and "'Seen again' is dead, MEASURED" come from the probe's shorter day list, and the whole list will probably recur

`.agent/review-packet-DD-1b2a.md:126,132`; adopted in `.agent/build-sheet-DD-1.md:1972-1973` (R4 section 4).

**What is wrong.** The probe found no later study with an eligible day, and that is true of the probe. But the probe list leaves out S-3 and S-1 (`.agent/DD-1b2-probe-days.json`: 18 entries, neither present). The clone holds no reading on those days, only the 11 closing rows on 11-01 (my query). The tick's scan queues a study ending on any local day that has a renewable head at or after wall now minus 5 days (`mini_decisions/worker.py` `enqueue_from_selections`, `SCAN_BOUND`; `store.py:341-352`). So the clone could only queue studies ending S+0 and S+1, which is what `samples.after-tick-2.studies` shows. The whole list builds S-1, and S-3 too if its hours fall inside the bound.

**What those studies would hold (MEASURED by me, in memory, read-only, `frozen_result` on the clone's heads):**

| Study ends | Status | Eligible | Eligible days |
|---|---|---|---|
| 2026-11-02 (S-3) | UNKNOWN | 2 | S-6, S-5 |
| 2026-11-04 (S-1) | UNKNOWN | 1 | S-5 |

S-3 and S-1 read missing here, and a built story-only day is still missing (`_fold_day`), so the eligible counts should not fall on the whole list. Eligible 1 or more is a Source whatever the status (`chain/threads.py:161-162`, `OPP_MIN_ELIGIBLE_DAYS = 1`). `("RESOLVED_MONITORING", OCCURRENCE)` goes to `RECURRED` (`chain/lifecycle.py:55`).

The gap goes back to DD1b2-R section 0 (`build-sheet-DD-1.md:1466`), which checked only the windows ending S+0 and S+1. R2 section 4 had it right: "Recurrence is now likely". **The scan-to-RECURRED step is READ, not run.**

**Why it matters.**
- Q7's "recurs" column is the likely one on the rehearsal: "Seen again" on S-5 and S-1 boards, and the Portfolio counting the mill thread as open.
- The packet's P6 acceptance (line 132) and R4 section 4 tell DD-1b2b the opposite.
- R4 section 4 also makes the COH-17 entry "not expected". On the recurs path it is owed (`build-sheet-DD-1.md:1559`).
- DS-1 and the owner's picture are affected: R2's "Replace the 'Seen again' sentences if P6 measured no recurrence" would remove true lines from the script.

**Fix.**
1. Correct the packet: no recurrence **on the 18-entry list only**; on the whole list it is expected, READ.
2. Architect marks R4 section 4 as not holding and restores Q7's two columns, with COH-17's entry owed if the check fires.
3. Recommended, minutes, not on the kept DBs: a new clone of `dd1b2q`, add-day `normal` on S-1, tick, read the mill thread's events. That turns READ into MEASURED before the 3 h rehearsal. If the Architect would rather let the rehearsal measure it, the packet must say so.

### M1. The "1 verified result" is ACT-001, not the mill. The mill Action is on no board, and the thread's link to it dead-ends

`.agent/review-packet-DD-1b2a.md:127-128,132`; adopted in `build-sheet-DD-1.md:1972`. Against Q7's table, `build-sheet-DD-1.md:1547-1551`.

**What is wrong.** The packet says "So the mill thread counts as 1 verified result (Q7's 'does not recur' column)". That is not what the row counts. MEASURED by me, read-only requests on the clone (`default_transaction_read_only=on`; the one stored-response write failed and was dropped):

| Read | Result |
|---|---|
| Boards S-11, S-8, S-5, S+0, whole body | 0 hits for `ACT-000002`, 0 for "Run the grain mill", 0 for "Target met", 0 for "Checked and working" |
| Assure row, S+0 | "1 verified result", contributor "ACT-001 verified on example data" |
| Assure row, S-11, S-8, S-5 | "No verified result yet" |
| Grow row, S-8 | `issues` empty, `earlier` empty, "Not available yet · no completed work or checked change for this outcome" |
| `GET /api/sites/KOBO-001/threads/<mill thread>` | "Checked and working, monitoring"; ACT-000002 with `verification: null`, `ref` kind `ACTION` |
| `GET /api/sites/KOBO-001/actions/<ACT-000002>` | **404 "No such Action for this Site."** That `ref` maps to this page (`operatorSiteRoutes.ts:591-592`; browser not run) |
| `GET /api/sites/KOBO-001/domain-work/actions/<id>/verification` | 200, VERIFIED, the 42.00 to 110.00 line |
| `GET /api/sites/KOBO-001/work/maintenance` | one `domain-actions` href in the row, the only way into that verdict page that I found |

Why (READ): `site_outcomes/mini.py:475` counts the Mini composer's `actions`, read from the Finding Action index (`mini.py:416`). `is_domain` is set only in `cold.py:225`. Thread lines need a `FindingFact` (`board.py:691-765`), and an opportunity thread has none.

**Why it matters.** R4 section 4 and the dispatch's carried list treat these as "not measured, DD-1b2b captures them". They are now measured on this data, and the expected captures will not appear where Q7 says: "Action, 'Why?', Assure: Target met" and S-8 "Checked and working". R4 section 3's wording says "the full rehearsal will show it", and it will show only on the verdict page. Q7's stop ("Target met stops showing where the Action shows") is not clearly met or missed, because the Action shows on the Work row and the thread page, and the thread page's link 404s. This is a pre-existing surface gap (CH-9b), first exposed here, and **not a defect of this diff**.

**Fix.** Correct packet lines 127-128 and 132. Bring the table above to the Architect as a question, with the size: does the demo path run through Work to the verdict page (a script line), or does the thread link or the board need wiring (code, DD-1b2b)? Add the thread link to the carried list by name. It is not on it.

### Lows (do not block)

- **L1. `.agent/review-packet-DD-1b2a.md:121`: "Nothing is left behind" overclaims.** The clone has `snapshot_dirty` = 31 after tick 2 (231, then 31; days 10-31 to 11-07, my query). Pending events are 0, so "0 stuck" holds, for Kobo only on a Kobo-only clone (`unconsumed` is per Site). P6's boards were read with those 31 outstanding. A third tick probably clears them (DD-0c: 227, 27, 0). This is R8's job in DD-1b2b.
- **L2. Packet lines 1, 7, 40, 57-63, 138 are stale.** The header says "STOPPED ... not yet for review", the outcome says P1 fails, and the acceptance table and "User review" predate R3, R4 and the owner's "Leave it". The result the review is to judge is only in the last section. P1 is not restated as ruled. Items 11, 12 and BL-43/44 are not closed in the table.
- **L3. Packet line 126 lists S-1 as a measured board line.** S-1 is not built on the probe list, so the line was read on an empty day. Same for the Portfolio's "2 of 7 days" (lines 128, and S-3, S-1 will add partial days).
- **L4. Packet line 134 and R4 section 5 name only EV-LAB-001.** `logs/18-prebuild.log` also has three COLD-LAB-001 404s. DD-1b2b must show both. Evidence is the log, not `probe-3.json` (0 hits there).
- **L5. R2 section 2's "`delivered_days`' SQL form via one L2 row" has no test.** No test runs `Demo.delivered_days`; `tools/dd1b2a_seam.py:47-51` holds a copy of the SQL. The two strings match, and I ran it on the clone: 2026-10-26 is not listed. `Demo.delivered_days` itself has not run on this branch. EX-1's add-day exercises it.
- **L6. Not reported in the packet: Grow contributor beside the potential.** S-8 and S-5 read "Spare solar on 4 of 4 well-observed days" with "High", next to "No potential found yet". Both are true by their rules, since the potential is hidden while RESOLVED_MONITORING. A presenter will be asked. Goes to DD-1b2b's capture and DS-1.
- **L7. Packet line 19 cites the Cold path as `:2410`.** It is `host/lab_execution.py:2415`. Cosmetic.

## Your questions

**Seam rule: no defect.**
- *Story-only, Cold, EV.* On the real v3 list (`resolve`, S = 2026-11-05): Cold 3 runs, seam 0; EV 3 runs, seam 0; Kobo's 8 story-only runs seam False, so `keep_observation()` is None and `or day.keep()` gives None as before. `seam` is absent from their payload. Cold reads `day.keep()` and the `:2415` path, untouched. `delivered_days` is shared by Sites, but Cold (16:00Z) and EV (08:00Z) starts sit nowhere near a local midnight, so the `COALESCE` does not move a day.
- *Neighbours.* Every touching pair on the list is seamed to seamed. A story-only run starts at 03:00Z, so S-15's and S-8's closing rows at 21:00Z meet nothing. No split run exists on the v3 list (boundary S+1 00:00).
- *Double-send or conflict.* 0 duplicates by (device, signal, source_time) in 50,964 accepted rows; dispositions all ACCEPTED (my query).
- *Lost reading.* Each of the 13 full days holds 288 interval instants, 0 non-GOOD interval rows, 576 state rows. Only story-only days keep their 11 first-boundary absent rows, as before. Rule 1 drops only rows with no value. The three Findings stand at S-14, S-7, S+0; M1's S-7 is 200 candidate minutes.
- *L0 non-vacuous: yes.* In-memory mutations: dropping rule 1 fails the seam test; dropping rule 3 fails the seam and the non-vacuity tests; widening rule 3 to state rows fails the seam and the one-sender tests. The L0's `produces` models the runs, so the DB rows above are the real proof.

**Evidence against the packet.** I checked the JSON, and these hold:
- P1 LIMITED, 5 of 5 eligible, null headroom and window.
- M2: `MIXED`, the one reason, 10 runs, three fields equal, `run_identity_sha256` differs, 0-2 kW over 3 hours in memory.
- P2 `origin_opportunity_id` set and equal in the link row.
- P3 COMPLETE, 10-23/24/25, no fallback.
- P4 VERIFIED, `TARGET_MET`, later days 10-28/30/31, 42.00 to 110.00, threshold 46.20, 3 days each; the dry run holds the same figures.
- P5 events and days as stated, identical across both ticks.
- P6's S-11 line and earnings. P7's pending 57,472 then 0.
- P8's 3.244.

These do not: "no recurrence" as a whole-build claim (H1), "1 verified result" as the mill (M1), "nothing is left behind" (L1).

**The clone and the copied tool: no difference in code, and no result I can attribute to it.**
- The copied mill tool equals HEAD byte for byte, as do the other eight files I compared (line endings aside).
- `git diff e513401e0 HEAD` outside `.agent` is that tool plus two development tools.
- The only sequence difference is a second `drain_mini` and `backfill-a`: `logs/09` wrote 0 of 92, and P3 was already COMPLETE after one pass on `dd1b2p`.
- The fallback ran on `dd1b2p` only, after the clone.
- `probe-2` and the clone are the same build.

**Unproved until DD-1b2b:**
- The mill tail (freeze, evaluate, `b,c,d`) as one uninterrupted first pass inside `prepare`.
- Three Sites: ACT-000004, ACT-002/003 order, `backfill` across Sites, S2 after the mill.
- The S-28, S-21, S-3, S-1 entries, and with them recurrence (H1).
- Objectives, R8 drain, finish rows.
- The "Target met" label in a browser.
- The eight stuck events on a three-Site build.
- Time and memory.

**Option (b): not in the diff.** `evidence/source_provenance.py` and `mini_decisions/projection.py` are untouched; `store.py` carries only the Q2 clock. Disclosed process slips are not repeated here.

## What I ran

| Check | Result |
|---|---|
| L0: `test_demo_combined_mill`, `test_demo_story_days`, `test_demo_combined_finish_days`, `test_demo_combined_links`, `tools/checks/test_chain_coherence` | 246 passed, 11.8 s |
| L2 and host, own base `assetops_rvdd1b2a_test` (dropped after): `test_mini_opportunity_story_clock_postgres`, `test_s6_verification_publication`, `test_dd1a2_registered_kobo`, `test_dd1a1_stream_probe` | 10 passed, 224 s. **The L2 is not in the packet's list; it passes** |
| Seam-rule mutations, in memory | Above |
| Read-only queries and API reads on `assetops_demo3_dd1b2q_test` | Above. Nothing written to it or to `dd1b2p`, which I did not open |

**Not run:** guards and `check-all` (the coordinator's), full backend suite, prepare, baseline, `test_demo_combined_postgres`, the browser. No frontend file is in the diff, so `tsc`, `npm.cmd test` and the build do not apply to it.

## Residual risk the packet does not name

- The P6 boards are a Kobo-only read with no objectives, so every `kpi` reads "No target set yet". Row states will move on the full build.
- A later study that does get queued has status UNKNOWN, so a RECURRED thread should read with no kW figure, as Q7 says. That has not been rendered on this data.
- The mill step cannot be rerun on the same DB (READ): an unchanged study queues nothing, so `build` stops at `STUDY_NOT_ONE`. A mill stop means a clone, not a rerun. This matters only for the "cheap retry" habit.
