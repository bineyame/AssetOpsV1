# Owner request 2026-11-18 (verbatim): build pipeline and checks speed-up evaluation

> as part of the speednup considerations, let the architect evaluate the build pipeline and checks that happen that are eithe stale, do not have utility in light of speed for demo(managable risk) and consider parallellization  and comination options later(like data processing algorithms)

Context: given while the two-week aggressive conversion plan (`Docs/go-to-market/two-week-conversion-plan.md`, branch `task/gtm-documents`, worktree `/opt/assetecon/AssetOpsV1-gtm`) was being written. That request (verbatim in `.agent/owner-gtm-documents-request-2026-11-18.md`, item 2) asks for "rutheless speedup wihtout compromising product evoliton, convertion potential" with "algorithms for speed and priortization". This evaluation feeds that speed-up. Adopted workflow: D11 (W1–W9) in `.ai/RULES.md`. Earlier owner direction on test speed (2026-10-28): dramatically cut test runtime and memory.

## Owner approval (verbatim), 2026-11-18

After the evaluation (`Docs/engineering/build-pipeline-and-checks-speedup.md`, commit 95f8531e5) recommended fixing defect D-1 regardless and package PIPE-1 (actions A1–A6, A10; owner decisions OD-1 with OD-2, OD-3, OD-5 following), the owner replied:

> go ahead with the D-1 fix and PIPE-1

Not approved by this message: PIPE-2 (A7, A8), OD-4 (verified DB clone as the walkthrough's clean DB), OD-6 (overnight full suite), OD-7.
