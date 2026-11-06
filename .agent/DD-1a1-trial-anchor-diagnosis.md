# DD-1a1 trial-anchor KeyError: diagnosis

Crash: `tools/demo_combined_kobo.py:433` `h.findings()[act["finding_anchor_day"]]` -> `KeyError: '2026-11-04'`
("with" complements build). `h.findings()` keys by `anchor_start.date()` in UTC
(`backend/tests/test_s6_action_store_postgres.py:92-95`). Diagnosis only; no product code changed.
DBs: `assetops_dd1a1b4_test` (without), `assetops_dd1a1b4w_test` (with); dropped after capture.

## Cause

Not a day-key or timing mismatch. The "with" build has **no Findings at all** (not only 11-04):

| DB | Findings | anchors (UTC) |
|---|---|---|
| without | 3 | 2026-10-21 04:35, 2026-10-28 04:35, 2026-11-04 04:35 (`GENERATOR_SUPPORT_CANDIDATE`) |
| with | 0 | none |

Every full day's `dispatch` window analytic run is **cohort AMBIGUOUS**:

- `analytic_run.cohort_status`: without 15 SELECTED_UNIQUE / 0 AMBIGUOUS; with 13 SELECTED_UNIQUE / 20 AMBIGUOUS.
- The 11-04 window run is SELECTED_UNIQUE (members `day-25` only) at cutoff 04:06, after the night-early run.
  After trial-before (cutoff 12:06) it is AMBIGUOUS: "a source reports the same time span under more than one
  sequence epoch (...@day-25, ...@day-26 for all 6 sources); no coherent default cohort; select one explicitly".

Mechanism (rule cohort-4, `D-2026-10-15-lr01-source-time-cohort`):

1. DD1a1-R Q6 gives each complement "its own run, with its own epoch" (`tools/demo_story_days.py:205-212`,
   fresh `day-<n>` per run). 11-04: night-early `day-25` (21:00-03:00), trial-before `day-26` (03:00-11:00),
   steady-afternoon `day-27`, night-late `day-28`.
2. Adjacent segments both emit the shared edge sample. `accepted_evidence` source_time: `day-25` 11-03 21:00 ..
   11-04 03:00; `day-26` 11-04 03:00 .. 11:00 (same on 10-21: `day-9` ends 03:00, `day-10` starts 03:00).
   `_overlaps` is closed-interval (`backend/assetops_backend/analytics/cohort.py:58-59`), so `_clashing`
   (`cohort.py:117-132`) fires -> AMBIGUOUS (`cohort.py:86-94`).
3. Even with half-open segment ends, `_multi_epoch` (`cohort.py:95-103`, `:109-114`) makes any window that sees one
   source under two epochs AMBIGUOUS, by design ("central evidence does not attest that they are one physical stream").

Assessment heads (latest revision per key):

| day | without | with |
|---|---|---|
| 11-03 window | LIMITED (rev 2) | INDETERMINATE (rev 5, cohort reason above) |
| 11-04 window | COMPLETE (rev 2) | INDETERMINATE (rev 2) |
| 11-04 interval | `...:2026-11-04T04:05` CANDIDATE_AVOIDABLE | only `...:2026-11-04T02:05` NECESSARY (rev 1, night-early run alone, 02:05-03:00) |
| 11-05 window | COMPLETE (rev 1) | not reached (crash) |

The overrun interval (04:05-07:55, the trial-before hours) is never assessed in "with" because the window it
sits in has no default cohort. `site_day_snapshot` has no rows for 11-03..11-05 in either DB (built later, at tick),
so snapshot grades are not a factor.

Citations ("without"): each Finding's primary assessment is the `dispatch:interval:...T04:05` CANDIDATE_AVOIDABLE
revision plus the `dispatch:window` COMPLETE revision, 246 evidence rows, all from one epoch (10-21 `day-3`,
10-28 `day-4`, 11-04 `day-7`). "With": no Finding revisions, so no citations.

## Honest physics or defect

Defect in the DD-1a1 build shape, not physics. A full day with steady complements still contains the same
04:05-07:55 generator-support interval; the analytics never see it because the cohort guard correctly refuses to
blend unattested epochs. The guard is behaving as specified; Q6's "own epoch per complement" collides with cohort-4.
It also means Q6's required "trial metrics equal with and without complements" check cannot pass as built, and the
10-21/10-28 Findings are lost too (would break the board story, not just the trial).

## Fix options for the Architect (not decided)

Moving the anchor or keying by local/other day does **not** help: there is no Finding on any day in "with".

1. **One sequence epoch per Site-day stream** (story run and its complements share the epoch, sequence numbers
   continue across segments), and make segment ends half-open so the shared edge sample is emitted once.
   Amends Q6 ("own epoch"); keeps own run and `received_at`. Risk: gateway sequence/duplicate rules across
   separate runs under one epoch must accept the continuation; needs a probe.
2. **Explicit cohort selection** (`analytic_run_selection`, `SELECTED_EXPLICIT`) naming all of a day's epochs,
   plus half-open ends. `_clashing` still blocks overlapping epochs (`cohort.py:74-77`), so ends must not share a
   sample. Adds an operator/producer act per window; semantically asserts "one stream", which cohort-4 says central
   evidence cannot attest - an architecture-level ruling.
3. **No complements on Finding/trial days** (10-21, 10-28 overuse; 11-04 trial-before; 11-05 trial-after, which the
   later-run evaluation also needs CURRENT). Smallest code change, but those days read partial, contrary to CH9-R4
   / DD-1a acceptance ("full-day story day ... grades COMPLETE").
4. **Change cohort-4** (treat abutting epochs of one source as successive and blendable). Product/analytics rule
   change under `D-2026-10-15-lr01`; out of DD-1a1 scope.

Option 1 is the only one that keeps both full days and the unchanged trial chain without a cohort-rule change.
