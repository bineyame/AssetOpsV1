# Architect request: evidence-grounded demo data strategy (HTML)

You are the AssetOps Architect (Claude). The authority is the owner's request, saved word for word in `.agent/owner-demo-data-strategy-2026-10-28.md`. Read it in full and follow it, including its §6 constraint: plan first, no implementation.

## Owner context
- The owner can't supply a customer export until after the demo, during pilot talks.
- So this strategy replaces "wait for a customer export" (telemetry plan TEL-10; owner Q7 = c) as the way to give demo data real-world grounding before outreach.
- Say explicitly how it changes TEL-10 and the customer-export collector (TEL-06, which is merged). One question to answer: can a public real dataset be replayed through the generic CSV collector or the Modbus emulator?

## Inputs to read first (build on them; don't compete)
- Commercial architecture: `Docs/demo-sprint/commercial-capability-readiness.html`. Its 21 outcomes (7 per vertical), the claim ladder, the beneficiary rule and the no-double-counting rule govern which scenarios matter.
- Telemetry: `Docs/demo-sprint/telemetry-integration-plan-claude.html`, `.agent/telemetry-rulings-2026-10-27.md` and `.agent/build-spec-telemetry-2026-10-27.md`. The merged code is in `field/`: Modbus emulator profiles `-1`/`-2`, the CSV collector, the poller and the BeagleBone plan.
- Simulation and integration: `Docs/demo-sprint/simulation-evolution-assessment.md` and `integration-pilot-baseline.md`.
- Code: `simulator/assetops_simulator/` (observation, the Kobo models, the EV and cold labs), the s602b and walkthrough producers in `tools/`, and the provenance classes in `backend/assetops_backend/evidence/source_provenance.py`. Check what a real public dataset would need in order to be labelled honestly; today there is no positive real-source class.
- No earlier dataset-research file exists in the repo, so research the sources independently.

## Web research
Use WebSearch and WebFetch. For every source, give:
- the URL;
- the licence;
- whether it is downloadable or access-restricted;
- coverage, granularity and the signals it actually contains (verified, not assumed);
- a confidence level.

Mark each claim as **documented fact** or **inference**. Name stronger alternatives where you find them, preferring African and downloadable sources. Don't download large datasets. Small samples are fine only to verify columns, and only into the scratchpad, not the repo.

## Output
One self-contained, well-illustrated HTML file: `Docs/demo-sprint/demo-data-strategy.html`, titled "Demo Data Strategy".
- Use the same visual language as the other demo-sprint HTML files: `:root` tokens, dark mode, a sticky table of contents, phone-width layout, tables that scroll inside their boxes, and inline SVG only.
- Cover the six deliverables in owner §5.
- The backlog must be coding-agent-ready, in the same style as the build specs: tasks, files, acceptance tests and stop conditions. It must be sequenced against the current lanes:
  - commercial: CC-D2 and CC-D1 are next;
  - telemetry: TEL-08 BeagleBone, then TEL-07.
- End with a short list of owner decisions. Each one needs a practical example, a recommendation and the rationale.

## Limits
- Documents only. No product code, tests, DBs or suites.
- Focused read-only checks of the code are allowed.
- The laptop is memory-constrained, and a full test suite is running in parts. Keep your own processes light.
- Don't commit.
- Report back in under 200 words: the recommended sources per vertical, the key gaps, the new owner decisions, and anything you couldn't verify.
