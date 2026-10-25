# Architect request: demo-sprint assessment (owner brief)

You are the AssetOps Architect. The owner's brief, verbatim, is `.agent/owner-demo-sprint-brief-2026-10-25.md` in this worktree. Do exactly what it asks: assessment and planning only, no feature implementation. Write the three documents under `docs/demo-sprint/` (`readiness-assessment.md`, `scenario-options.md`, `five-day-plan.md`). Because your final chat response is not shown to the owner directly, also put the section-12 direct answers (questions 1-10) at the end of `five-day-plan.md` under a heading "Architect recommendation", and end that section with the explicit request for the owner's review before implementing.

Coordinator context (facts to check, not requirements):
- This worktree is main at its current head. Post-W6 UI fix cards still unmerged on branches (do not wait for them; note where they matter): `task/post-W6-W6-global` (global Work lists, small backend link changes), `task/post-W6-W2-EV` (EV Site screens), W2-cold (cold Site screens, worktree `../AssetOpsV1-ops04`), `task/post-W6-W4-mini` (mini Work, Scenarios, Site tabs). Three more cards (W5-cold-Work, W5-EV-Work) not started. The register is `.agent/mock-departure-register.md`; audit index `.agent/post-W6-audit/`.
- Owner earlier: "We need to be able to bootstrap sites and portfolios based on story we want to present to our clients across the 3 verticals" (mini-grid, cold chain, EV). Several producer gaps were deferred to this story bootstrap (cold/EV authored scenarios, EV depth states, linked VERIFICATION_WINDOW/CANCELLED, populated estate lenses, populated Alternatives) — see `.agent/post-W6-W2-cold-rulings.md`, `post-W6-W2-EV-rulings.md`, `post-W6-W3-estate-rulings.md` "producer-gap" decisions.
- Owner's standing UI bar: `.agent/owner-ui-ux-guidance-2026-10-25.md` and `frontend/docs/architecture/ui-ux-decision-guide.md` if present.
- Hardware pack: `C:\Users\assef\Bineyame\AssetOpsHardwareIntegrationPack` (files 01, 03, 04 are `.md`; also 00, 02, a checklist and a CSV catalog template exist — read if useful).
- Tests: you may run fast, read-only checks (unit tests, scripts with `--help`); do not run the full backend suite, captures, or create databases.

Do not edit product code, tests or `.gitignore`. Keep documents concise per the brief.
