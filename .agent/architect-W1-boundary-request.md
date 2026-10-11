# Architect request: W1 boundary candidates (2026-10-11)

Owner (verbatim, 2026-10-11, after asking which screens W1 leaves out and how Action screens are split): "ok share with me the revised recommendation for the waves by the architect"

Context the owner raised: W1 (`delivery_plan.waves.W1` in `frontend/docs/architecture/v69-dependency-registry-pilot.json`; proposal `.agent/W1-owner-input-proposal.md`, already Architect-reviewed) contains `finding`, `action-overview`, `verification`, `sitework`, `changes`, `asset`, while closely related mini-grid screens sit in later waves:
- W4: `sitefindings` (Site-scoped FindingIndex list), `finding-history` (FindingRevision/ActionEvent), `action-plan`, `action-execution`, `action-evidence`, `action-history` (other tabs of the same Action as `action-overview`/`verification`).
- W6: Kobo battery tabs `asset-overview`, `asset-performance`, `asset-evidence`.
The owner noticed one Action has two tabs in W1 and four in W4.

Please recommend, with a one-line reason each, which of these should move into W1 (consider what S3–S7 already produce — FindingIndex rows for `mini:3`, Finding revisions after late evidence, Action events and verification evidence in S6 — versus added screen work and unresolved gates), and for any moved screen propose its core panels and 1–5 demo value. Keep the rest where they are or propose a better wave, keeping all 110 IDs allocated exactly once and W2 cold/EV-only.

Amend `.agent/W1-owner-input-proposal.md` in place (add a "Wave boundary review, 2026-10-11" section at the top with the recommendation and a revised one-reply confirmation line) and produce a compact table of the full revised W1–W6 allocation in that file. Keep registry owner fields empty; if the registry allocation must change after owner confirmation, list the exact edit rather than making it. No product code; leave edits uncommitted.
