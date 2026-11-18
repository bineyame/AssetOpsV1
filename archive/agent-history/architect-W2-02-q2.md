# Architect request - W2-02 commit (2) questions (2026-10-17). Brief answers; edit `.agent/W2-02-build-spec.md` in place; record in `D-2026-10-17-w2-02-buildspec` (amend). No code.

Implementer finished spec commit (1) (branch task/W2-02-cold-producer, handoff `.agent/W2-02-phase-1-handoff.md` on that branch).
A. Confirm interpretation: the spec says the first conversion is historical v3-compatible (W2-01 snapshot hashes unchanged) and also that cold rows carry v4 metadata. Implementer attaches v4 metadata only on the published revision (origin != CONVERSION), so COLD-001 conversion bytes are unchanged and the 00:01 revision is a real change. Confirm or correct.
B. "Add the six to the Lab choices only for the registered fixture": the scenarios endpoint takes no Site, scenarios name no Site, the frontend lists the catalog unfiltered. Specify the exact endpoint/field/filter that presents the cold scenarios only for COLD-LAB-001 (and whether the legacy catalog list keeps excluding them).
C. Cold run request: `RunSetupRequest` names model profile id and version. Should a cold run request still name them (freeze path checks against the document), or does the document's profile triple decide?
Print a 3-line summary.
