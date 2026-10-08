# Architect answers to S1-01 Implementer questions (2026-10-08, verbatim)

Relayed by the owner. Text below is verbatim.

1. Yes. The layout check should allow the required Publish reserve change
     button on imported KOBO-001's Foundation screen, without allowing unrelated
     enabled actions. Lab run and Commit checks for imported Kobo are
     inapplicable until S2 restores the registered Lab path. The separate MG-001
     layout failure still needs diagnosis.

  2. Yes. Keep the Implementer's period-local rule: a new reserve value applies      from its effective time to the end of the period containing it. If that         period has no end, the value remains in effect; later scheduled periods         retain their values. The UI should show the resulting period so a bounded       change does not appear permanent.

# Owner review routing (2026-10-08, verbatim)

"for now use fresh codex reviwer and codex will review S1-01 and S1-02 together to save quota."

Coordinator reading: a fresh Claude reviewer reviews S1-01 now; Codex reviews
S1-01 and S1-02 together later.
