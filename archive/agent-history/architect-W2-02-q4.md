# Architect request - W2-02 Lab cold-choice UI (2026-10-17). Brief; edit `.agent/W2-02-build-spec.md` in place; amend `D-2026-10-17-w2-02-buildspec`. No code.

Implementer (handoff `.agent/W2-02-phase-2-handoff.md`, branch task/W2-02-cold-producer) built `GET /api/simulator-lab/cold-scenarios?site_id=` and its client. The spec says the client "offers the returned cold scenarios" after Site selection, but `RunSetupFrame.tsx` builds its form from the legacy scenario detail (404 for cold by spec); the v69 mock has no screen for this.
1. Render cold choices inside `RunSetupFrame` after the Site picker (~line 690), or on a separate cold run-setup route?
2. On pick: create the run directly with the document's fixed interval, seed, one-minute timestep and profiles shown read-only, or prefill the existing form?
3. Exact copy for the empty and unavailable (503) states.
Also confirm: freezing the registered binding set's `signal_mappings` into the cold run identity (as the existing registered path does) is acceptable.
Print a 3-line summary.
