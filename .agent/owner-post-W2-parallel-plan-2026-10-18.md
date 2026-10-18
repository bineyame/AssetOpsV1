# Owner direction - post-W2 parallel sequence (2026-10-18)

Owner question, verbatim: "after w2 completes, what is the best way to parallelize the rest of the waves wihtout any negative impact(consistency, quality) to speed up development"
Owner decision, verbatim: "yes let the architect turn it into the post-w2 sequence once w2 closes"

Coordinator proposal the owner approved (to be turned into a binding sequence by the Architect when W2 closes, checked against the registry dependency checker):
- Two lanes maximum (machine limit: one full suite at a time, Postgres 100 connections).
- Step 1: Lane A = W4 core work-case model (shared Actions/Incidents/Maintenance records, lifecycle, APIs) built alone; Lane B = W3 estate-wide aggregates over existing Site reads. Run OPS-01 backend test-speed alongside.
- Step 2: Lane A = rest of W4 (mini-grid depth + mini-grid work screens); Lane B = W3 finish.
- Step 3: Lane A = W5 cold/EV work; Lane B = W6 assets, settings and global work.
- Guards: shared core first and frozen (changes via Architect); one Architect for both lanes with the same build-spec readiness gate; one owner lane per shared file (migration numbers allocated up front; shared UI files and the registry owned by one lane); identical quality gates (layout rules upfront, side-by-side review with mismatch = High, independent reviews); each lane merges main after every main merge; full suites alternate through one queue.
Trigger: when the last W2 slice merges, run one Architect call to produce the post-W2 sequence (lanes, slice order, shared-file ownership, migration number allocation), then proceed.
