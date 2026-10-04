# Architect brief: T028 capability-readiness decisions (Codex Architect, 2026-10-04)

You are the AssetOps Architect (Codex; `.ai/ROLE_CONFIG.md`). Under the owner's
2026-10-04 rule ("Decision Requests Go To The Active Architect" in that file)
you decide, record your justification, and say whether you want the owner to
weigh in.

Target: branch `task/T028-dispatch-finding-and-evidence` (HEAD `1f46d75`), task
`tasks/T028-dispatch-finding-and-evidence.md` (AC20), packet
`.agent/T028-review-packet.md` ("Open owner decisions (phase 3a)"), rules in
`backend/tests/dispatch_decision_table.md` ("Capability readiness"), code
`backend/assetops_backend/analytics/declaration.py` (`score_readiness`).
Owner text verbatim: `.agent/owner-T028-closeout-2026-10-04.md`.

Decisions to take:
1. Readiness window: site-wide (as built) or the page's selected window. The
   owner asked to understand whether readiness describes a site operational
   condition or setup; your record should answer that in plain words.
2. Readiness gap rule: the owner deferred the rule itself and asked that it
   become configurable through a "gap impact type". Decide what that means,
   whether any of it belongs in T028 or in a later slice (name it), and what
   T028 should state meanwhile.

Already verified (do not re-run): full suites backend 1465, host 616,
simulator 244, frontend 1097; build; both checks; layout 560 PASS / 5 FAIL.

Constraints: do not edit code, tests or task files; do not merge. Write your
decision record to `.agent/T028-architect-readiness-decisions.md` (decision,
justification, consequences for T028 and later slices, any implementation
change you require before review, and whether you want the owner to weigh in).
If a durable decision is warranted, draft its `.ai/DECISIONS.md` entry text in
that file; the coordinator commits it.
