# Architect follow-up: owner's missing-data rule (2026-10-12)

Your round 3 answers (`.agent/architect-V-01a-round3-answers.md`) did not yet address the owner's follow-up, which arrived while you worked (verbatim, in `.agent/owner-V-01a-round2-feedback-2026-10-12.md` "Follow-up"):

"if there is data missing to show yet, it should be stated as such in the UI to avoid drift and highlight things are accepted conditionally for now"

Rule briefly, as an addendum to the same round:
1. Which mock content currently *omitted* from V-01a screens should instead be kept in place with a plain visible "not available yet" state naming what is missing. Candidates: the Sites inventory's Assessment / Top issue / Evidence / Last analysed columns (your earlier ruling said not to fill four columns with identical placeholders — reconcile with the owner's rule, e.g. one compact grouped "Not available yet: …" cell/column or per-column states naming the source); the Sites KPI tiles, type chips and "In setup" panel; SLD breakers/meter/monitoring row/status dots; gateway uptime/completeness/signal/firmware; anything else omitted. Give exact wording patterns and where omission still remains correct (e.g. invented device glyphs that would look like data).
2. How the owner's visual acceptance of panels containing such states is recorded as **conditional** (packet per-panel record, registry/ledger field or note) until the source exists, without marking anything Real.
Append to `.agent/architect-V-01a-round3-answers.md` (section "Addendum: missing-data states and conditional acceptance") and amend the decision; leave uncommitted.
