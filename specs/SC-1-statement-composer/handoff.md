# SC-1a handoff (COMPLETE: units 1-3 built; in review)

Branch `task/SC-1a-composer`, worktree `/opt/assetecon/AssetOpsV1-sc1a`, off `main` 8805ee169; mid-build answers
(74e74ca9c, D-SC1.29 to D-SC1.31) merged in. Python: `/opt/assetecon/AssetOpsV1/.venv/bin/python`; PYTHONPATH =
worktree `backend:backend/tests:contracts:simulator`.

## Done

- `5e91634ac` unit 1, `a96e1eaab` unit 2, `53c3ae169` unit 3 (guard, baselines, check-all lines, T12 identifier
  names, `facts.py` dunders as identifiers), then the packet, spec `in_review`, the built-state entry.
- Results and deviations: `packet.md`.

## Next

- Review round 1: ACCEPT WITH FIXES (`review.md`). Architect answers D-SC1.32 to D-SC1.39 (`rulings.md`, "Review
  answers (round 1)"; spec rev 3; reviewer guide rev 3) on `task/SC-1a-review-answers`. Next: merge that branch, then
  a fix round of 0.75 units per D-SC1.39 (fresh implementer), then a verification re-review (guide items 2, 10, 14,
  15). Owner approval of the two check-all lines at merge (owner-away rows 5 and 22).
- Coordinator: merge `main` into the branch to clear the inherited index-check failure (doc conflicts in
  `.ai/decisions/index-rulings-15.md` and `specs/OWNER-AWAY/decisions-2026-11-21.md`: keep both sides' rows), then
  delete and rewrite both baselines from `main` (`git archive <main> backend config`, lay SC-1's mechanism files and
  `statement_cases/` over it, `--write-baseline --root <scratch>`), and rerun the guard and its self-test.

## Risks

- Any `main` change to `messages.CATALOGUE` changes its single word-map fingerprint (rule i) until the fix round
  (D-SC1.37 removes it): rewrite the baselines.
- `KEY_INSTANCE` tokens today: `cold`, `kisiwa`, `kobo`, `lab`; a new generic Site code word could hit a key.
