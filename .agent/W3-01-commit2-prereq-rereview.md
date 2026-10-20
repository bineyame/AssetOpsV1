# W3-01 commit-2 prerequisite fix r1: re-review of 15dae742

## Verdict: ACCEPT (no High/Medium findings)

Read via git objects only; no tests run (worktree in use). Builder's "13 passed, check-all 10/10" is cited, not re-verified.

- M1: `_dispatch_day_on` now treats PENDING/LEASED as outstanding, normalized to PENDING. DONE uses `min(selected_at)` over all selections for tenant/site/job, not day-limited. `<= k` is finished, `> k` is outstanding as PENDING, and no selection is `JOB_STATE_AT_CUTOFF_UNKNOWN`. FAILED stays unavailable. All as ruled. Live branch (`all_jobs=not live`) is unchanged.
- Early assertions: available True, selection None, run_id None, status PENDING, unavailable_reasons [], one job with status PENDING, and a RECOMPUTE_OUTSTANDING reason naming the job id (`dispatch_read.py:81` emits "RECOMPUTE_OUTSTANDING: job <id> <status>"). Matches the ruling.
- New `test_dispatch_days_on_done_empty_job_is_unavailable`: non-vacuous. It forces DONE, asserts the update hit >=1 row, asserts zero selections, then asserts available False, status None, selection None and JOB_STATE_AT_CUTOFF_UNKNOWN. The old early-vector assertions were inverted rather than dropped, so both the reconstruct path and the refusal path are proved.
- L1/L2/L3: the L1 as-of rule is in the docstring and code comment; L2 is disclosed in the handoff, with a note to carry it to the commit-2 packet; L3 needs no change. Low note: the unavailable-reason string still says "no stored record shows its state", which is accurate only for DONE-empty and FAILED. Cosmetic.
