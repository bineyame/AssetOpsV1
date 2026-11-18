# Architect request: commercial capability, integration and simulation readiness (assessment only)

You are the AssetOps Architect. The owner's brief is in `.agent/owner-commercial-capability-brief-2026-10-26.md`. Read it in full and follow it exactly as written. It is the authority for this task, and this file only adds where things are and the machine limits.

Locations:
- The earlier assessment artifacts (iteration 4, awaiting owner review) are `Docs/demo-sprint/readiness-assessment.md`, `scenario-options.md` and `five-day-plan.md` in this worktree. Earlier owner demo-sprint files are `.agent/owner-demo-sprint-*.md`. Write the three new documents in `Docs/demo-sprint/`. Do not edit the three existing documents.
- Hardware Integration Pack: `C:\Users\assef\Bineyame\AssetOpsHardwareIntegrationPack\` (`01_Simulation_Emulation_Ingestion_and_Protocols.md`, `03_Architect_Technical_Readiness_and_Pilot_Gates.md`, `04_Scope_Decision_Register_and_Risks.md`; `00_README...`, `02_...` and `05_...csv` are context if useful). Read it only. Do not modify it.
- Recent built state: `.ai/ACTIVE_CONTEXT.md`, `tasks/README.md`, `.ai/MILESTONE_REVIEW_BACKLOG.md` and `.agent/mock-departure-register.md`. A final whole-product recapture is running separately at main, and you do not need it.

Machine limits (16 GB, another heavy job is running):
- Verification is focused only: single test files or small `-k` selections (backend `pytest` or `npx.cmd vitest run <file>`). No full suites, no `vite build`, no dev servers, no Docker DB creation. If a test needs a DB you cannot reach, record it as a blocker ("test present but not executed").
- Benchmarks: run only short, small samples (a few simulated days, under ~5 minutes and ~2 GB). Extrapolate to 60–90 days, and label the results as estimates versus observed. Propose the full benchmark as a later test.

Rules:
- No product code, test or `.gitignore` edits.
- End `commercial-capability-readiness.md` with the brief's §11 decision summary, then a short request for owner review. The other two documents link to it.
