# Architect request: S4-02 batched rulings (2026-10-14)

Role: Architect (Codex). Context: S4-02a and S4-02b are merged to main (`a6c6a849`), owner S4-02 checkpoint passed (conditional). Governing decision `D-2026-10-13-s4-bounded-financial-basis`; prior answers `.agent/architect-S4-02-answers.md`, `.agent/architect-A-S4-financial-answers.md`. Rule each question briefly with justification; say whether it needs a code change, and in which slice; flag any item where you want the owner to weigh in. Owner-facing summary in plain language at the end.

## Q1 (S4-02a phase-1 review L2, deviation D2)
A SYSTEM `SUCCESSION` whose `valid_from` equals the start of the open-ended current assignment is refused (409), although the packet says SUCCESSION may truncate the open assignment containing `valid_from`. Sources: `.agent/S4-02a-phase-1-review.md` (L2), `tasks/S4-02a-site-assumptions.md` contract item 2, `backend/assetops_backend/financials/assumptions.py`. Keep the refusal (that case is a CORRECTION/replacement), or permit it?

## Q2 (S4-02b phase 2a Q2)
Accepting new evidence enqueues no consequence recompute work; a consequence whose inputs changed reads STALE until another trigger (price publication or FindingRevision insert). Sources: `.agent/S4-02b-questions-2.md` Q2, `.agent/S4-02b-phase-2a-review.md`, migration `backend/migrations/versions/0011_financial_consequences.py`. Should evidence acceptance (or Finding re-evaluation only) enqueue work? Which slice owns it?

## Q3 (S4-02b phase 2b Q11)
The "Demonstration data" label is derived from the authored spec's declared Site and day (KOBO-001, 2026-10-23), not from stored authorship; not tenant-scoped; fails closed to "Source not confirmed". Sources: `.agent/S4-02b-questions-3.md` Q11, `.agent/S4-02b-review.md`, `.agent/S4-02b-fix-rereview.md` I5, `backend/assetops_backend/demonstration_label.py`. Should provenance/authorship be recorded at ingestion (batch/publication level), and when must that land (before any real-Site pilot; before W1 exit)?

## Q4 (S4-02b phase 2b Q12)
No Site-level consequence list read exists; fuel cost versions are listed per Finding on Financials > Overview, each linking its exact price version; Assumptions lists price versions only. W1 portion `assumptions:3#a` covers consequence versions at a chosen cutoff (see `frontend/docs/architecture/v69-dependency-registry-pilot.json` panel `assumptions:3`). Sources: `.agent/S4-02b-questions-3.md` Q12, `.agent/S4-02b-review.md` registry closeout notes. Does the per-Finding version history satisfy `assumptions:3#a`, or does it need a Site-level read (and which slice)? State exactly what the registry closeout may promote.

Write only `.agent/architect-S4-02-batch-answers.md`. If a ruling should become a decision record, draft its text in that file under "Draft DECISIONS entry"; do not edit `.ai/DECISIONS.md` or anything else; do not commit.
