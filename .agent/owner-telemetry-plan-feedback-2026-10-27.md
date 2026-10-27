# Owner feedback (verbatim), 2026-10-27, on Docs/demo-sprint/telemetry-integration-plan-claude.html (revision 2)

The telemetry plan is directionally approved. The two-track architecture, shared DeviceReport/gateway boundary, repository gap analysis and interval/DC-versus-AC semantic findings are particularly valuable.

Please make these adjustments before implementation:

1. Keep the October scope to a complete Modbus TCP emulator → actual poller → gateway → accepted evidence proof, plus a minimal export collector. BBB deployment follows after the laptop proof is stable and is not a blocker.
2. Do not advertise Victron VRM compatibility from an invented “VRM-shaped” export. Obtain a genuine sample/schema or label it generic/illustrative.
3. Preserve MCU standalone edge deployment as a future option. The invariant is equivalent security, provenance and reliable delivery—not mandatory reuse of the Python gateway.
4. Reject the proposed stale-data heuristic based solely on identical readings. Use defensible freshness and quality indicators.
5. Resolve the battery DC/AC role mismatch before accepting a financial finding from GX telemetry.
6. Keep source-readiness claims precise about the actual tested interface, format, model and environment.
7. Do not purchase the ~$100 kit yet. Specify the minimum next component once the first physical test objective is selected.

Please now translate the bounded scope into concrete, testable implementation tasks, with explicit acceptance gates and stop conditions. Do not broaden the research or architecture effort.

The priority is verified integration credibility, not the number of implemented protocols.
