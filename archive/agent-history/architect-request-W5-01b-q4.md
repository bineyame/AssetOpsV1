# Architect request: W5-01b review H1 and Lows

You are the AssetOps Architect (Codex). Read the review with `MSYS_NO_PATHCONV=1 git show task/W5-01b-cold-scenarios:.agent/W5-01b-review.md`, then P-C5-15 and the C5 rulings in `.agent/W5-01-build-spec.md`, the mock-fidelity rules in `.ai/ROLE_CONFIG.md`, and the v69 `cold-scenarios` mock.

1. **H1.** The `Scenarios created through {scenario_at}` line (`frontend/src/sites/ColdScenarios.tsx:306-308`, shown in every state including empty) is not in the mock. P-C5-15 ruled it without a `MOCK DEVIATION` label, and the same ruling restores the empty state exactly. Prefer RESTORE TO MOCK: drop the line, or move its information into a mock element that already exists. KEEP it only with a `MOCK DEVIATION` label, the reason and the alternatives considered. Give the literal code and test change.
2. **Lows.**
   - Retry after a page-2 409 resends the stale cursor. Rule the literal retry behaviour, for example a reset to page 1, and its test.
   - The page mixes date formats. Rule one format per element, in line with the mock.

Append "W5-01b build rulings (review H1)" to `.agent/W5-01-build-spec.md`. Write nothing else. Do not commit. End your output with one line per item.
