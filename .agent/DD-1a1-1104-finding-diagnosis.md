# DD-1a1: why the 11-04 Finding goes UNCONFIRMED / NO_INTERVAL with complements

This is a diagnosis only. No product code changed. Build head `23d90e251`. I rebuilt both sides with
`tools/dd1a1_fullday_probe.py`:
- `without`: `assetops_dd1a1d11without_test`, 8 runs, 264 s.
- `with`: `assetops_dd1a1d11with_test`, 33 runs, 966 s.

The failure reproduces exactly. With complements there are 13 Finding revisions and the 11-04 Finding ends at rev 5
UNCONFIRMED. Without complements there are 6 revisions.

## Cause

The cause is the 11-05 Site-day's Part A night complement. It runs under epoch `day-8` and its readings fall inside
the **UTC** dispatch window of 11-04. That window already holds the 11-04 Site-day's epoch `day-7`. Rule cohort-4's
`_multi_epoch` therefore marks the 11-04 window AMBIGUOUS. An AMBIGUOUS run writes no interval assessments, so the
matcher finds no interval over the episode.

1. **Dispatch windows are UTC days.** See `backend/assetops_backend/analytics/dispatch_read.py:80-82` (`day_window`)
   and `analytics/assessment_worker.py:70-78`. Kobo's local day D runs over [D-1 21:00Z, D 21:00Z). So UTC window
   11-04 = [11-04 00:00Z, 11-05 00:00Z) contains local 11-04 from 00:00Z to 21:00Z, and local **11-05** from 21:00Z
   to 24:00Z.
2. **Each Site-day takes its own epoch.** See `tools/demo_story_days.py:259-265` (DD1a1-R5 "Day edges"). Part A
   (`kobo-night-early-until-0255`) has source times 11-04 21:00Z to 23:55Z, epoch `day-8`, sequence 98..444, and is
   received at 11-05 01:00Z. It is the 11-05 Site-day's run, but it lies **inside** the 11-04 UTC window. It is not in
   the bracket, so R5's "a neighbour epoch seen only in the bracket is not a candidate" (`cohort.py:63-66, 83-84`)
   does not apply.
3. **cohort-4 refuses to blend the two epochs.** See `analytics/cohort.py:95-103` and `:109-114`. Selection seq 60,
   run `e8b4fef8`, has cohort AMBIGUOUS: "a source reports in this window under more than one sequence epoch
   (…@day-7, …@day-8, …)". It has 0 INTERVAL revisions, and its window revision is rev 6 INDETERMINATE.
4. **The matcher then takes the "no cluster" path.** `_Site.intervals` (`analytics/finding_episode.py:279-280`)
   reads intervals only from the selected run, via `dispatch_read.py:147,174`. That list is empty, so there is no
   cluster. `_unsupported_write` (`finding_episode.py:583-621`) then returns UNCONFIRMED because the window is
   INDETERMINATE, and it adds `NO_INTERVAL` at `:614-615`.

Epochs present in the 11-04 UTC window, with complements (`accepted_evidence`, grouped by `received_at`):

| epoch | received | source time | seq | rows |
|---|---|---|---|---|
| day-7 | 11-04 04:00 | 00:00 to 02:55Z (11-04 night-early) | 37..240 | 444 |
| day-7 | 11-04 12:00 | 03:00 to 11:00Z (trial-before story) | 73..564 | 1197 |
| day-7 | 11-04 18:00 | 11:05 to 16:55Z (afternoon) | 170..800 | 875 |
| day-7 | 11-04 22:00 | 17:00 to 20:55Z (night-late) | 241..960 | 592 |
| **day-8** | 11-05 01:00 | **21:00 to 23:55Z (11-05 Part A)** | 98..444 | 444 |

Without complements, only the `day-7` trial-before rows are present (3:00 to 11:00Z, 1197 rows), so the window
stays SELECTED_UNIQUE throughout.

## The 13 revisions against the 6

`f.anchor_start`, revision number, transition, lifecycle, primary run, run cutoff, cohort status, created at.

| Finding | rev | without | with: trigger (delivery, epoch) and current intervals |
|---|---|---|---|
| 10-21 | 1 | OPENED, run cutoff 10-21 12:06 | same. Story run `overuse`, day-3, interval `…T04:05` CANDIDATE_AVOIDABLE |
| 10-21 | 2 | BASIS_REFRESHED at the 11-04 14:01 tick | afternoon complement, received 10-21 18:00, day-3. Same interval, SELECTED_UNIQUE |
| 10-21 | 3 | n/a | night-late complement, received 10-21 22:00, day-3. Same, SELECTED_UNIQUE |
| 10-21 | 4 | n/a | 11-04 14:01 tick. Same, SELECTED_UNIQUE |
| 10-28 | 1-4 | 2 revisions | 4 revisions, with the same pattern as 10-21 (day-4, all SELECTED_UNIQUE) |
| 11-04 | 1 | OPENED, run `0a38159f` cutoff 11-04 12:06 | OPENED, run `ddb22fc7`. Trial-before story, received 11-04 12:00, day-7, seq 41. Intervals `T02:05` NECESSARY (from night-early) and `T04:05` CANDIDATE_AVOIDABLE |
| 11-04 | 2 | BASIS_REFRESHED, run `98a78b1a` (11-04 14:01 tick) | BASIS_REFRESHED, run `ac112d5f` (tick, seq 54). Same two intervals |
| 11-04 | 3 | n/a | 11-04 afternoon complement, day-7, received 11-04 18:00. Assessed at 11-05 12:08 after the trial chain (seq 57, run `512f2774`; window LIMITED). Interval `T04:05` rev 2 still current. Created 11-05 12:09 |
| 11-04 | 4 | n/a | 11-04 night-late complement, day-7, received 11-04 22:00. Seq 58, run `10e32c93`; window COMPLETE; `T04:05` rev 2 still current. Created 11-05 12:11 |
| 11-04 | 5 | n/a | **11-05 Part A, day-8, received 11-05 01:00, source 11-04 21:00Z.** Seq 60, run `e8b4fef8`, **AMBIGUOUS** (day-7 + day-8). 0 intervals, window rev 6 INDETERMINATE, so **UNCONFIRMED / INDETERMINATE / NO_INTERVAL**, created 11-05 12:13. Part B (day-8, received 11-05 04:00, source from 11-05 00:00Z) re-runs the window at seq 62 and reselects `e8b4fef8` unchanged |

The extra revisions on 10-21 and 10-28 (4 against 2) and 11-04 revs 3 and 4 are honest BASIS_REFRESHED bookkeeping.
Same-epoch complements re-run the window, and the supported facts do not change.

Query used (abridged; the script is outside the repo):
```sql
select s.seq, s.window_start::date, ar.id, ar.knowledge_cutoff, ar.cohort_status, ar.cohort->>'reason',
  (select count(*) from assessment_revision a where a.analytic_run_id=ar.id and a.assessment_key like 'dispatch:interval%'),
  (select e.sequence_epoch||' '||e.received_at||' '||e.source_time from accepted_evidence e where e.id=j.cause_evidence_id)
from analytic_run_selection s join analytic_run ar on ar.id=s.run_id left join recompute_job j on j.id=s.job_id
where s.window_start::date between '2026-11-03' and '2026-11-05' order by s.seq;
```

## Candidate causes, ruled in or out

- **A later complement re-opens or splits the 04:05-07:55 interval: no.** The same-epoch complements on 11-04
  (afternoon, night-late) keep `T04:05` rev 2 current through revs 3 and 4. Only the other-epoch Part A removes it,
  and it does so through the cohort rule, not through interval geometry.
- **A recompute picks a different selection: yes, but only as the means.** Seq 60 selects run `e8b4fef8`, which is
  AMBIGUOUS. That selection is correct under cohort-4.
- **The v16/v17 boundary: no.** Part A is on v16, the same Foundation revision as 11-04. The clash is on the epoch,
  not on the configuration. Any 11-05 night-early under `day-8` would clash, split or unsplit. The R7 split only made
  the run buildable: before R7 it was refused, so this never surfaced.
- **A different cohort for the interval bounds: no.** The bounds are never recomputed. There is no cohort at all.

## The same defect, silently, on 11-03

The 11-04 night-early complement (day-7, source 11-03 21:00Z to 23:55Z) makes UTC window 11-03 AMBIGUOUS from seq 38
onwards (day-5 + day-7, 0 intervals). Without complements, 11-03 is SELECTED_UNIQUE. There is no Finding on 11-03, so
this changes no Finding, but the 11-03 window grade turns INDETERMINATE. Any build with two consecutive built Kobo
Site-days hits this. 10-21 and 10-28 escape only because 10-22 and 10-29 have no run.

## Honest physics or defect

This is a defect in the build shape, not physics. The cohort guard behaves as specified. The defect is R5's day-edge
premise. Its "a neighbour epoch seen only in the bracket" assumes the analytic window equals the Site-local day.
Windows are UTC days, and at UTC+3 the next local day's first three hours lie inside the window itself. A real gateway
would not change epoch at local midnight. R5's own reasoning ("a real gateway changes its sequence epoch only on a
reset") argues against the per-day epoch here.

## Fix options for the Architect (not decided)

1. **One epoch per uninterrupted Site stream, not per Site-day.** Consecutive built Site-days (here 11-03, 11-04 and
   11-05) share one epoch, and the sequence continues across day edges. The epoch changes only where a day without a
   run separates them. That is a real outage or reset, as on 10-25 and 11-02. The change is in
   `tools/demo_story_days.py:259-265`. R5's gateway probe already covers a sequence continued across separately
   sealed runs and a complement received after a later-sequence run. The cross-day case needs the same L2 probe,
   including the late-delivered 11-01 (day-6), which stays separate because 11-02 has no run.
   - Cost: R5's L0 "story-run payloads equal to v1's" fails for 11-04 and 11-05, because their epoch strings change,
     unless the shared epoch applies only when a complement crosses into a neighbour's UTC window.
   - Smallest honest change, and it matches R5's own rationale.
2. **Window dispatch on the Site-local day.** This would change the analytic window calendar
   (`dispatch_read.py:80`, `assessment_worker.py:70`, model `UTC day`). It is an analytics/product change, out of
   DD-1a1 scope.
3. **Leave out the 21:00-24:00Z part of a night-early complement when the previous UTC day carries another epoch.**
   This is a small change, but it leaves local 00:00-03:00 on 11-04 and 11-05 unbuilt. That is a partial story day,
   contrary to CH9-R4 (the same objection R5 raised against its option (c)).
4. **Explicit cohort selection naming both epochs.** R5 already rejected this as option (b), because it asserts one
   stream by an operator act.

Option 1 is the only one that keeps full days and the unchanged cohort rule. It needs a ruling on the "story-run
payloads equal to v1" check.
