# Architect request: W5-02b K2, the final open points before merge

You are the AssetOps Architect. Read:
- .ai/ROLE_CONFIG.md ("Mock fidelity", D1-D6)
- .agent/W5-02b-K2-rulings.md
- .agent/W5-02-build-spec.md
- .agent/W5-02b-questions.md (Q18, Q19)
- .agent/W5-02b-phase-handoff.md ("builder readings")
- the v69 mock, frontend/mockups/v69/index.html

The code is on task/W5-02b-cold-site-screens. Read it with `git show task/W5-02b-cold-site-screens:<path>`. The evidence measurements are at .agent/W5-02b-evidence/ on that branch.

Rule on each point:
1. Q18 / F1, the all-disclosures-open cap. With all five long rows opened, the panel measures 907 px at 1440 against a 650 cap, and 1259 px at 390 against 850. The page stays inside its caps, at 1291 and 1805. Every other state is within its caps. The extra height comes from each opened disclosure repeating the full text under a preview that stays visible. Rule exactly one of these, citing what the mock does for an open disclosure:
   (a) a layout change, for example hiding the preview while the disclosure is open;
   (b) a cap exemption for the all-open state;
   (c) something else.
2. Q19 / F7. The `unknown` mode's replay has no COLD_EXCURSION Finding, so its Incident links only COLD_START_FAILURE, which goes against ruling 4. Rule the fixture fix, or record the exception.
3. Builder reading, the ruling 1 form literals. The builder used `From (UTC)`, `To (UTC, exclusive)`, `Apply` and the client's INVALID_WINDOW text. Confirm these or replace them, citing the mock.
4. Builder reading, the duplicate date forms. The old W4 window form inside the panel still shows on cold Incidents and Maintenance, next to the new control. Rule whether K2 removes it now or K3a does.

Append the rulings, numbered 20 onward, to .agent/W5-02b-K2-rulings.md. Update .agent/W5-02-build-spec.md and the register (from R92) if needed. Do not touch product code. Do not commit.
