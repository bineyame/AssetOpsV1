# SC-1a handoff (COMPLETE: units 1-3 built; fix round r1 built; in review)

Branch `task/SC-1a-composer`, worktree `/opt/assetecon/AssetOpsV1-sc1a`, off `main` 8805ee169; mid-build answers
(74e74ca9c, D-SC1.29 to D-SC1.31) merged in. Python: `/opt/assetecon/AssetOpsV1/.venv/bin/python`; PYTHONPATH =
worktree `backend:backend/tests:contracts:simulator`.

## Done

- `5e91634ac` unit 1, `a96e1eaab` unit 2, `53c3ae169` unit 3 (guard, baselines, check-all lines, T12 identifier
  names, `facts.py` dunders as identifiers), then the packet, spec `in_review`, the built-state entry.
- Results and deviations: `packet.md`.

## Next

- Fix round r1 (D-SC1.32 to D-SC1.39) built: `packet.md`, "Fix round r1". Next: the verification re-review (fresh
  Claude reviewer; guide items 2, 10, 14, 15; regenerate both baselines from `main` and compare; rerun the replay).
  Owner approval of the two check-all lines at merge (owner-away rows 5 and 24).
- Any `main` merge that adds backend code: rewrite both baselines from `main` (`--write-baseline --root <scratch>`
  on SC-1a's tree with `main`'s `messages.py` and `locale.py`), rerun the guard and its self-test.

## Risks

- `KEY_INSTANCE` tokens today: `cold`, `kisiwa`, `kobo`, `lab`; a new generic Site code word could hit a key.
