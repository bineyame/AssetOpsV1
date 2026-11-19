# DD-1: split map

`.agent/build-sheet-DD-1.md` (342 KB, 2641 lines, sha256 `77385b95596923eb`) moved here on 2026-11-18 (declutter step 4) and was split by its own headings, verbatim and in order, into `spec.md` 11 KB, `rulings.md` 59 KB, `rulings-2.md` 58 KB, `rulings-3.md` 56 KB, `rulings-4.md` 49 KB, `rulings-5.md` 56 KB, `rulings-6.md` 50 KB. Open the part a citation names; an old `file:line` citation maps through the table (old lines -> part lines). Proof: `python tools/declutter/split_specs.py --verify`.

| # | Old lines | Part | Part lines | Section |
| --- | --- | --- | --- | --- |
| 1 | 1-16 | `spec.md` | 1-16 | Build sheet DD-1: the B-22 baseline with the story injected, fill-a... |
| 2 | 17-31 | `rulings.md` | 1-15 | Why it is split (DD1-R S1) |
| 3 | 32-47 | `rulings.md` | 16-31 | 1. Rulings (DD1-R) |
| 4 | 48-56 | `rulings.md` | 32-40 | 2. Pre-flight (both parts; batch the answers, then stop) |
| 5 | 57-64 | `spec.md` | 17-24 | 3. Tests |
| 6 | 65-75 | `rulings.md` | 41-51 | 4. DS-R1 and OL-1 |
| 7 | 76-82 | `spec.md` | 25-31 | 5. Size |
| 8 | 83-89 | `spec.md` | 32-38 | 6. Review focus |
| 9 | 90-123 | `spec.md` | 39-72 | Build units (split 2026-11-05) |
| 10 | 124-134 | `spec.md` | 73-83 | Scope cut (SCOPE-1) |
| 11 | 135-157 | `rulings.md` | 52-74 | DD0c-R: rulings on the DD-0c probe results |
| 12 | 158-174 | `rulings.md` | 75-91 | DD1a1-R: rulings on the DD-1a1 pre-flight |
| 13 | 175-245 | `rulings.md` | 92-162 | DD1a1-R2: the Kobo night profile (supersedes DD1a1-R Q2 and its sto... |
| 14 | 246-292 | `rulings.md` | 163-209 | DD1a1-R3: the steady-night gate result, and the Kobo initial values |
| 15 | 293-311 | `rulings.md` | 210-228 | DD1a1-R4: `mill-midday` is BLOCKED on mini-grid v6 |
| 16 | 312-345 | `rulings.md` | 229-262 | DD1a1-R5: complements make every full day cohort AMBIGUOUS (amends Q6) |
| 17 | 346-369 | `rulings.md` | 263-286 | DD1a1-R6: on the Kobo `degraded` day, the outage lasts the rest of ... |
| 18 | 370-424 | `rulings.md` | 287-341 | DD1a1-R7: split the trial-after night at the reserve change's instant |
| 19 | 425-463 | `rulings.md` | 342-380 | DD1a1-R8: one epoch per unbroken Site stream, not per Site-day (ame... |
| 20 | 464-502 | `rulings.md` | 381-419 | DD1a1-R9: the frozen baseline and continuous data; a baseline "move... |
| 21 | 503-519 | `rulings-2.md` | 1-17 | DD1a1-R10: R6 assertion 7 restated as deterministic assertions; the... |
| 22 | 520-542 | `rulings-2.md` | 18-40 | DD1a1-R11: Q8 cost, projected full-day prepare against the 3 h cap |
| 23 | 543-583 | `rulings-2.md` | 41-81 | DD1a1-R12: the mill-day probe; the dusk start state, other days' pr... |
| 24 | 584-611 | `rulings-2.md` | 82-109 | DD1a1-R13: the Cold failure day with full days, and the steady-afte... |
| 25 | 612-640 | `rulings-2.md` | 110-138 | DD1a1-R14: Cold full days are withdrawn (amends Q4); every compleme... |
| 26 | 641-679 | `rulings-2.md` | 139-177 | DD1a1-R15: step back. Cut complements only where the generator is S... |
| 27 | 680-716 | `rulings-2.md` | 178-214 | DD1a1-R16: after the R15 stops, Kobo goes hybrid: full days only wh... |
| 28 | 717-915 | `rulings-2.md` | 215-413 | DD1a2-R: rulings on the DD-1a2 pre-flight (Architect, Claude, 2026-... |
| 29 | 916-981 | `rulings-3.md` | 1-66 | DD1a2-R2: G1 failed on "0 L" on the `steady-before` night: accept t... |
| 30 | 982-1032 | `rulings-3.md` | 67-117 | DD1a2-R3: review H1: the live day after the trial is `normal`, not ... |
| 31 | 1033-1190 | `rulings-3.md` | 118-275 | DD1b1-R: rulings on the DD-1b1 pre-flight (Architect, Claude, 2026-... |
| 32 | 1191-1281 | `rulings-3.md` | 276-366 | DD1b1-R2: the Q6 probe failed; one read fix, whole-day links, per-S... |
| 33 | 1282-1402 | `rulings-3.md` | 367-487 | DD1b1-R3: the re-probe failed because R2's own read fix asked for 3... |
| 34 | 1403-1453 | `rulings-4.md` | 1-51 | DD1b1-R4: review M1, the live Cold add, and H1's class of fault (Ar... |
| 35 | 1454-1672 | `rulings-4.md` | 52-270 | DD1b2-R: rulings on the DD-1b2 pre-flight (Architect, Claude, 2026-... |
| 36 | 1673-1820 | `rulings-4.md` | 271-418 | DD1b2-R2: the P1 stop: the blank rows come from our own day-edge ru... |
| 37 | 1821-1889 | `rulings-4.md` | 419-487 | DD1b2-R3: second P1 stop: the study is LIMITED, `SOURCE_CLASS_MIXED... |
| 38 | 1890-1991 | `rulings-5.md` | 1-102 | DD1b2-R4: R3's kill conditions, whether the figure stands beside th... |
| 39 | 1992-2070 | `rulings-5.md` | 103-181 | DD1b2-R5: review H1 and M1 (Architect, Claude, 2026-11-07) |
| 40 | 2071-2186 | `rulings-5.md` | 182-297 | DD1b2-R6: DD-1b2b consolidated owed list (Architect, Claude, 2026-1... |
| 41 | 2187-2227 | `rulings-5.md` | 298-338 | DD1b2-R7: rulings on the DD-1b2b pre-flight (Architect, Claude, 202... |
| 42 | 2228-2304 | `rulings-5.md` | 339-415 | DD1b2-R8: gaps before the one rehearsal (Architect, Claude, 2026-11... |
| 43 | 2305-2347 | `rulings-6.md` | 1-43 | DD1b2-R9: P0's COH-2 stop and two notes (Architect, Claude, 2026-11... |
| 44 | 2348-2423 | `rulings-6.md` | 44-119 | DD1b2-R10: the rehearsal's 12 self-check failures, the recurrence r... |
| 45 | 2424-2492 | `rulings-6.md` | 120-188 | DD1b2-R11: CO-2 at the rerun, EX-1's changed boards, and what is st... |
| 46 | 2493-2508 | `rulings-6.md` | 189-204 | DD1b2-R12: the second gate on a copy (Performance comparison), from... |
| 47 | 2509-2601 | `rulings-6.md` | 205-297 | DD1b2-R13: closing the DD-1b2b review (M1, M2, L1-L4) (Architect, C... |
| 48 | 2602-2641 | `rulings-6.md` | 298-337 | DD1b2-R14: R13's two failed asserts on `dd1b2` (Architect, Claude, ... |
