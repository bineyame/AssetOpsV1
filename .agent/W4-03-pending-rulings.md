# W4-03 pending rulings

## PR-1 (raised in unit 1; does not block unit 1; needed before unit 4)

S1 asks the OPPORTUNITY stage to carry "counters", but the S4/closure-1 catalog delta for 0030 lists only the
altered stage CHECK and no `schedule_site_head` columns. W4-02 added `mini_processed/mini_deferred/mini_failed`
as new columns in 0029. Unit 1 added no counter columns.

Question: should 0030 add `opportunity_processed/opportunity_deferred/opportunity_failed` (integer NOT NULL
DEFAULT 0) to `schedule_site_head`, with the downgrade dropping them? Or should unit 4 report OPPORTUNITY
counts without persisted columns? If the answer is columns, unit 4 amends 0030 and its catalog test, which is
possible because the branch is not merged.
