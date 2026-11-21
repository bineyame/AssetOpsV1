# 0K4e handshake

## Reviewer questions (R)

Fresh Claude reviewer, 2026-11-21, on `main` `0ead104e9`. Read: `spec.md`, `reviewer-guide.md`, D-0K4.10 and
D-0K4.11, `one-figure-change-list.md`, the owner's one-figure file, and the cited code: `dispatch_v3.py` 150-342,
`postgres_assessment_store.py:309-340`, `claim_limit_read.py:39-130`, `stored_declaration.py:40-150`,
`assessment_worker.py:80-200`, `structure/litres/rules.py`. I recomputed E1 to E3 by hand: need 120 kWh, held 95 kWh
and 133 kWh, 1.1 x 120 = 132. The spec's figures are right.

**R1. The method signature contradicts its call.** §2.2 declares `_Index.energy_to_cover(t, feeders_at_t)`, but §2.3
calls `index.energy_to_cover(t_meas)`. §2.2's body re-reads the loads at each step (`self.assets(LOAD, s)`), so the
second argument is unused, or it was meant to fix the feeder set at `t`. Those two readings give different `need`
when a load binding starts or ends during the walk.
*Default:* one argument, `energy_to_cover(t)`. The feeders are re-read at each `s`, as §2.2's body says, so a feeder
bound later in the night counts from its binding on. The decision table's 3.3 row says so.

**R2. No test pins which way the interval-mean fallback runs (a rule a test can't decide).** `lookup_asset` matches a
mean whose `interval_end == s`, so the value at `s` describes `(s - 5 min, s]`. The walk adds `(load - pv) x 5/60` for
the slot at `s`, and the fallback uses `interval_start < s <= interval_end`. E5 holds every value constant, so swapping
the fallback to `interval_start <= s < interval_end` still gives E1's 120 kWh, and P5 does not catch it either.
*Default:* keep the spec's convention. Add **E5b**: 15-minute load means of 10 kW, then 20 kW, across one interval
boundary, with PV 0, and a literal `need` that differs by one slot's 5/6 kWh under the swapped convention. Add plant
**P10**, the swapped inequality, which must fail E5b.

**R3. Readiness and claim-limit coverage cannot see the new Indeterminate reasons (unknown read as covered).**
`claim_limit_read.segment_roles` (108-130) assigns each `missing` text to a role by the text before ":". The two new
texts are "battery energy capacity or PCS efficiency not configured; ..." and "energy to solar cover not evidenced
(PV available power: ... at ...); ...". Neither maps to a role, so `role_coverage`, and the stored readiness built on
it (`stored_declaration.py`, AP-1 plain labels), report every role COVERED on a segment that 3.3 left Indeterminate.
The spec changes only `SUPPORTED_MODELS`.
*Default:* add no new role, and do not attribute the walk's later gap to this segment's PV role (it is at another
time). Add a test that pins this behaviour: a 3.3 segment Indeterminate for either reason reads COVERED in
`segment_roles`. The decision table's 3.3 row then states that role coverage is per instant, and that an energy-walk
or configuration Indeterminate is a limit of the model, not an input gap. If the Architect wants readiness to name
it, that is a separate queued item.

**R4. The fixture producer and the database for E9 to E11 are not named (DB names, runnability).** The pre-flight and
E9 rely on "the DS1 Kobo history producer" loaded into a `*_test` database. `tools/world_history.py` (DS1/DS1b) writes
files (`generate`, `records`, `exports`), not a database. The spec names no loader, database name or runtime for a
31-day October history.
*Default:* use the existing load path that `test_3a3_load_emulated.py` and the 3A3 fixtures use, in a run-owned
database named by `backend/TESTING.md` (`..._pt<run>_<tag>_test`), through `tools/heavy-slot.sh --db`. If no fixture
loads a full October in under a few minutes, E9 to E11 run on a declared shorter range, such as 3 days that include
an overcast night, and the packet names that range. Either way the packet names the database, and nothing outside
`*_test` is touched. Any other choice is a mid-build question before commit 2.

**R5. No bound on the walk's cost, and the coordinator runs it on demo databases.** `lookup_asset` scans the
channel's full row list on every call (`found = [r for r in rows if ...]`). The walk makes about three lookups for each
of up to about 430 five-minute slots (window plus 6 h), for every battery-support point. Reassessing a month is then
roughly points x slots x rows, inside a reconcile pass that §5 hands to the coordinator as a heavy job, one at a time.
*Default:* build the walk once per window as a backward pass over the 5-minute grid: per slot, the next cover time and
the suffix sum of need, exact in `Fraction`. `energy_to_cover(t)` then reads it in constant time. The packet reports
E9's assessment wall time on 3.2 and on 3.3. A ratio above 2x is a mid-build question. The same exact figures are
required, so E1 to E6 decide it.

## Architect answers (2026-11-21)

Answered in the spec's rev 2 and the rulings (`specs/0K4-dispatch-model-review/rulings.md` for 0K4, `rulings.md` for
1a). R1 default (D-0K4.23). R2 D-0K4.23: E5b redesigned (the proposed case cannot fail: a reading ending at a slot is read before any fallback), plant P10. R3 default (D-0K4.23; E14; readiness queued Q10). R4 D-0K4.23 (I5's `CaseRunner` world in R4's run-owned database). R5 D-0K4.23 (memoised per-slot recurrence).
