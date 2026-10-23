# Architect request: build the mock departure register (D1–D6)

You are the AssetOps Architect (Codex). Read the new rule "Departure categories and register" in `.ai/ROLE_CONFIG.md` and `.agent/owner-departure-categories-2026-10-23.md`.

Create `.agent/mock-departure-register.md`. Find every `MOCK DEVIATION` (and every KEEP or deviation ruling) in `.agent/W5-01-build-spec.md`, `.agent/W5-02-build-spec.md`, `.agent/W5-03-build-spec.md`, `.agent/W5-04-build-spec.md` and `.agent/W6-01-build-spec.md`, plus any earlier W1–W4 deviations recorded in the specs or `.ai/DECISIONS.md` where a screen is affected.

For each one, add a row with these columns: ID, wave/slice/unit, screen (v69 id), mock element, what is shown instead, category (D1–D6), one-line reason, owning or resolving unit, status (built / planned / resolved).

Classify honestly. In particular:
- if a deviation is really a missed or altered mock element with a feasible faithful alternative, mark it **D3** and propose the correction;
- if it rests on a data source that actually exists in the code (as the withdrawn M5/E5 Site timezone case did), mark it **D3**.

Group the file by category, and add a short summary count at the top. Then append a one-line category code to each `MOCK DEVIATION` label in the specs (for example `MOCK DEVIATION (D1)`).

Write only the register and those label edits in the spec files. Do not commit. End your output with: the counts per category, and every D3 item with its proposed correction.
