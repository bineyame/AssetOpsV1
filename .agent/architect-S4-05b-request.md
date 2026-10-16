# Architect request - S4-05b phase 1 questions (2026-10-16)

You are the AssetOps Architect (Codex). The owner wants maximum W1 progress; decide within the Architect's remit. Visible copy remains the owner's W1 checkpoint. Read `.agent/S4-05b-phase-1-handoff.md`, `tasks/S4-05b-producers-reads-walkthrough.md`, `tasks/S4-05-stored-demo-provenance.md`, `D-2026-10-15-s405-stored-demo-provenance`, `.agent/owner-T028-presentation-direction-2026-10-04.md` (owner: product screens read as a real site, no simulator or implementation vocabulary in the default reading; deeper detail in its own layer) and the product-vocabulary scan in `tools/checks/`.

1. Source label: the packet mandates `Simulated data` for REGISTERED_SIMULATION on product screens (Finding, Evidence, Financials), but `simulated` is a banned product-vocabulary term and conflicts with the owner's presentation direction. Choose an interim label and placement (default reading vs the dig-deeper disclosure) that is honest that the data is not from a real site, passes the vocabulary scan or names a scoped exemption, and keep final wording for the W1-conclusion copy task. Do the same for `Demonstration data`, Mixed and Unknown if needed.
2. Behaviour change: a registered Lab run that was only partly sealed can no longer be committed at all (`SOURCE_PUBLICATION_REFUSED`), because S4-05a refuses to publish a stage that is not fully sealed. Before, it released what was sealed. Accept, or rule otherwise.
3. Phase 1 left `demonstration_label.py` in use by `actions/service.py` (not named in the packet). Should phase 2 move Actions off it too?

Write `.agent/architect-S4-05b-answers.md` and one entry `D-2026-10-16-s405b-label` in `.ai/DECISIONS.md` (UTF-8, ASCII hyphens). No code, no packet edits. Print a short summary.
