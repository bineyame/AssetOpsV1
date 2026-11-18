# Architect request: commercial capability assessment, iteration 2 (owner direction applied)

You are the AssetOps Architect. Read `.agent/owner-commercial-capability-direction-2026-10-26.md` in full. It holds the owner's overall direction and answers, word for word, and it is the authority here. The original brief, `.agent/owner-commercial-capability-brief-2026-10-26.md`, still applies, including its stop point: assessment and design only, with no implementation and no five-day plan.

Revise `Docs/demo-sprint/commercial-capability-readiness.md`, `integration-pilot-baseline.md` and `simulation-evolution-assessment.md` (in place, concise) so they answer:

1. **Lead outcomes.** Per vertical, sort the commercial outcomes into three groups:
   - **ready now**: demonstrable end to end today, with the evidence;
   - **ready with reasonable short effort**: name the exact gaps and rough size;
   - **roadmap**: why it can't be made ready short-term, and what it depends on.
   The lead demo outcomes are the first two groups. Judge them against the owner's lifecycle (finding → commercial significance → intervention → independent verification → financial attribution → provenance) and the rule "every capability claimed as available must be demonstrable".
2. **Money claims / financial attribution.** Propose the approach with justification:
   - what the demo may show for modelled opportunity, expected value, technically verified improvement and realised value;
   - how each is labelled;
   - what makes a simulated before/after money comparison honest, given that the simulator generates reality and AssetOps must infer from ingested observations only.
3. **Independent verification in every vertical, and long operating histories.** The owner confirms the need. For mini-grid, cold chain and EV, state what exists (file, test, verified-by-run or not) and what must be built:
   - verification criteria and rules;
   - episode/recurrence;
   - degradation;
   - multi-week/month histories, including the mini-grid forcing window that stops at 475 minutes and the 100,000-minute cap.
   Give sizes and dependencies, and keep it at design level.
4. **Connection profiles.** The owner wants every supported connection profile available for a site within a portfolio, so the general integration scheme is tested before pilot-site variations.
   - Define "supported profile" honestly: today only the simulated canonical gateway/HTTPS path is demonstrated.
   - List the candidate profiles (for example canonical HTTPS batch, EMS/OEM/CSMS export or API, Modbus register poll, CAN frame decode, MQTT, file/offline feed). For each, state its current class (1–5) and what an emulated profile needs: emulator, collector/adapter, mapping, gateway delivery, quality/negative controls.
   - Propose how the profiles attach to demo-portfolio sites. That could be one site per profile, or one site with several, with justification.
   - Show how they reuse the one gateway/ingestion/provenance path without creating new services where the existing architecture suffices.

Update the §11 decision summary accordingly. End with only the decisions that genuinely remain for the owner, if any.

Limits are unchanged:
- Focused tests only, using `PYTHONPATH="backend;contracts;simulator;gateway;host;."` with `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`.
- No full suites, no `vite build`, no dev servers, and no DB creation.
- No product code, test or `.gitignore` edits.
- Do not edit `readiness-assessment.md`, `scenario-options.md` or `five-day-plan.md`.
