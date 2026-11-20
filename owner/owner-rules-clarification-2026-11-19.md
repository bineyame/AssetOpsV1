# Owner clarification 2026-11-19 (verbatim): four RULES entries credited to the owner

Context: the coordinator listed four rules in `.ai/RULES.md` that cite the owner but have no owner file behind them:
1. full suites only when the owner asks;
2. port 5490 / Docker / port 8990;
3. no fallback DB;
4. the range rule, which is missing the limit for setup facts.

The owner answered:

> regrding the first point, it is to avoid expensive full test that holds back progress, so regression or smoke test or isolated test could be used then full test for key milestones. the second point is not to interfe with tests or affect my valiodation, it could be qualified as such. third point, walkththrough on a clean, good DB. for the fourth , i confirm that that setup facts are not manged by date range for now(may introduce version later but not a priority)
