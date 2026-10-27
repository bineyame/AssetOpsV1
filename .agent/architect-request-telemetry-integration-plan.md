# Architect request: commercially prioritised telemetry integration plan (HTML)

You are the AssetOps Architect. The owner's request is saved word for word in `.agent/owner-telemetry-integration-plan-2026-10-27.md`. Read it in full and follow it exactly. It is the authority here.

## Inputs
- Technical starting point: `C:\Users\assef\Bineyame\AssetOpsHardwareIntegrationPack\modbustcp.html`. Read it in full. Its author is not recorded, so treat its repository claims as hypotheses and verify each one against the code in this worktree (current main).
- Also read the other files in that folder (`00`–`05`, `AssetOps_Demo_Readiness_Sprint_Checklist.md`) as context. Do not modify anything in that folder.
- Existing assessments to reuse rather than repeat: `Docs/demo-sprint/integration-pilot-baseline.md` and `simulation-evolution-assessment.md` (support classes 1–5, gateway path). Also see `commercial-capability-readiness.md` and `.html` for the commercial priorities.
- Repository seams to verify, among others:
  - `host/gateway_publication.py`, plus the gateway runtime / outbox and HTTPS upload code;
  - `backend/assetops_backend/gateway_api.py`, `evidence/ledger_service.py`, `evidence/source_provenance.py`;
  - `contracts/` (DeviceReport V2 and the publication contract);
  - `simulator/assetops_simulator/observation/`;
  - any existing Modbus, OCPP or MQTT code (grep for it).

## Web research
Web search is enabled for this run. Use it for:
- https://www.ammp.io/integrations and AMMP Edge documentation;
- concrete vendor API and gateway documentation for the families you shortlist (for example Victron VRM, SMA/Studer/Deye-type cloud APIs, OCPP/CSMS platforms, and cold-chain logger/controller clouds);
- current approximate prices for the hardware shortlist.

For every external claim:
- cite the URL;
- mark it **documented fact** or **inference**;
- give a confidence level.

If something cannot be verified, say so rather than guessing. Prices are approximate and dated (October 2026).

## Output
One well-illustrated, self-contained HTML document: `Docs/demo-sprint/telemetry-integration-plan.html`.
- Inline CSS and inline SVG diagrams only, with no external scripts.
- Use the same visual language as `modbustcp.html`: colour tokens on `:root`, a dark-mode variant, a sticky table of contents, and phone-width layout with tables scrolling inside their own boxes.
- `<title>`: "Telemetry Integration Plan".
- Cover all seven deliverables in the owner's §5.
- End with the prioritised plan and architectural recommendations, plus a short list of the owner decisions they need (owner §5, "Present your prioritized plan… before beginning substantial implementation").

## Limits
- This is a plan only. Do not implement adapters.
- Focused tests are allowed if they verify a repository claim. Use the project venv `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` with `PYTHONPATH="backend;contracts;simulator;gateway;host;."`.
- Do not run full suites or dev servers, and do not create databases.
- Do not edit product code, tests or `.gitignore`.
- Today is 27 October 2026, so "before October 30" means about three working days.
