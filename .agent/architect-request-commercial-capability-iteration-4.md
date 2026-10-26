# Architect request: commercial-capability-readiness.md, iteration 4

You are the AssetOps Architect. The authority for this task is the owner's feedback, word for word, in `.agent/owner-commercial-capability-feedback-2-2026-10-26.md`. Read it in full and follow it exactly, including its section 9 scope and exclusions and its section 10 decision summary.

Earlier owner files still apply where they don't conflict:
- `owner-commercial-capability-brief-2026-10-26.md`
- `owner-commercial-capability-direction-2026-10-26.md`
- `owner-commercial-capability-feedback-2026-10-26.md`

Edit only `Docs/demo-sprint/commercial-capability-readiness.md`, with targeted revisions rather than a rewrite. Keep it concise and scannable: tables plus short reasoning.

Where the owner asks you to "examine the existing implementation", do the examination yourself. That covers portfolio/estate services and UI (section 4), and episode, Finding, Action and verification (section 5). Cite actual files, functions and tests, and keep the evidence-status classes.

Focused tests are allowed where they help: the project venv `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` with `PYTHONPATH="backend;contracts;simulator;gateway;host;."`, or `npx.cmd vitest run <file>` in `frontend`. Do not run full suites, dev servers or DB creation. Do not edit product code, tests or `.gitignore`.

End with the section 10 answers and then the bounded owner decisions, each with a recommended default and its consequences.
