# Architect request: W5-01b Q-C5c-1/2 and the remaining 503 Low

You are the AssetOps Architect (Codex). Read the latest Run entry in `MSYS_NO_PATHCONV=1 git show task/W5-01b-cold-scenarios:.agent/W5-01b-phase-handoff.md` (head `ffc444c5`), "W5-01b build rulings (Q-C5b)" in `.agent/W5-01-build-spec.md`, the mock-fidelity rules and "W3/W4 lessons" in `.ai/ROLE_CONFIG.md` (spec literals must be checked against the real guards), `tools/checks/shell-overflow.ps1` rule 5, and the v69 `cold-scenarios` mock.

1. **Q-C5c-1.** Your ruled literal `<svg>` info icon fails rule 5, because it bars `<svg>` in a page module. Rule a guard-compliant form that keeps the mock's icon: reuse an existing icon module or component (cite it), or register the module. Give the exact file list, markup and test.
2. **Q-C5c-2.** At 390 the expanded one-row panel is 876 px against a 560 cap, because the narrow Basis cell wraps almost one letter per line. Rule a mock-faithful 390 layout with literal CSS and markup, check it against the mock at 390, and name a layout assertion.
3. **The 503 Low.** A stored revision 1 missing `from`/`to` still drops from the list instead of returning 503. Ruling 5 said 503. Say exactly where the check goes (the list or the selected read) and give the test.

Check every literal against the real guard files before writing it. Append "W5-01b build rulings (Q-C5c)" to `.agent/W5-01-build-spec.md`. Write nothing else. Do not commit. End your output with one line per item.
