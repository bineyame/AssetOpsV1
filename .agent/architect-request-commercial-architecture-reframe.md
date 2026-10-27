# Architect request: outcome-led commercial capability architecture (HTML rewrite)

You are the AssetOps Architect. The owner's request is saved word for word in `.agent/owner-commercial-architecture-reframe-2026-10-27.md`. Read it in full and follow it exactly. It is the authority here, including its required ten-section structure (§8) and acceptance questions (§9).

## Inputs
- Current `Docs/demo-sprint/commercial-capability-readiness.html` (Claude revision 2, Implementer questions resolved). Keep its verified code findings, but restructure the document; don't add a business introduction to it.
- `Docs/demo-sprint/commercial-capability-readiness.md` (iterations 1–6). Use its 7-per-vertical rankings, buyer distinctions, claim ladder and no-double-counting rule as the starting point.
- `.agent/implementer-effort-view-2026-10-27.md`, `.agent/implementer-questions-commercial-html-2026-10-27.md`.
- `Docs/demo-sprint/integration-pilot-baseline.md`, `simulation-evolution-assessment.md`, `telemetry-integration-plan-claude.html` (revision 3) and `.agent/telemetry-rulings-2026-10-27.md`. Link to them; don't repeat them. Keep the integration and telemetry claims consistent with them.
- The owner's earlier direction and feedback files: `.agent/owner-commercial-capability-*-2026-10-26.md`.
- The code on current main in this worktree. Verify every "exists today" claim against code and cite `file:line`. Mark target-state items clearly as target, not current.

## Output
- Overwrite `Docs/demo-sprint/commercial-capability-readiness.html`. Git keeps the previous revision.
- Self-contained: inline CSS and inline SVG, no external scripts.
- `<title>`: "Commercial Capability Architecture".
- Same visual language as the current file: colour tokens on `:root`, a dark-mode variant, a sticky table of contents, and phone-width layout with tables scrolling inside their own boxes.
- Include the diagrams §9 asks for:
  - the value-delivery loop;
  - the system architecture with its authority boundaries (deterministic, simulation, optimisation, AI-assisted);
  - outcome→driver→capability maps;
  - the portfolio ranking/triage/allocation layer;
  - two or three end-to-end decision examples.
- Put code-level findings, migrations, APIs and test requirements in appendices.
- End with a short list of the owner decisions still open. Carry forward the existing ones (which working decision enters the sprint, the "cost per kWh of feeder demand" wording, cold in Estate) plus any new ones.

## Limits
- Document only. Don't edit product code, tests or `.gitignore`.
- Focused tests are allowed only to verify a claim. Use the project venv `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` with `PYTHONPATH="backend;contracts;simulator;gateway;host;."`.
- No full suites, dev servers or databases.
- No web research.
- Today is 27 October 2026.
- When done, report back in under 200 words: section list, what was carried over, new decisions, and any claim you couldn't verify.
