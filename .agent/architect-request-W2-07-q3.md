# Architect request: W2-07 R8 and C1–C5 (q3)

You are the AssetOps Architect.

## Read first

- `.ai/ROLE_CONFIG.md`: the "implementers never decide" and "Token Efficiency" sections.
- `.agent/W2-07-build-spec.md`: all of it, especially q1 R5 and the basis hash at about line 77.
- Migration `0026` as built.
- On branch `task/W2-07-ev-site-evidence-money` at `33776d1d`, read these two files with `git show`:
  - `.agent/W2-07-pending-rulings.md`: R8 and C1–C5;
  - `.agent/W2-07-phase-handoff.md`: the "Run 4" note.

## Background

Check how the merged W2-04 cold consequence handled pending work (`0023` and the cold store) and mirror it unless that is unsound.

## R8 (High)

A WITHHELD/PENDING_RECOMPUTE consequence, once persisted, stays current forever:
- `ev_persist` reuses an unchanged assessment (`postgres_assessment_store.py:1301-1305`, `:1331-1335`), so no new 0026 work is enqueued;
- the basis-unique constraint (`0026` at about line 69) would replay the WITHHELD row anyway.

Choose A, B or C, or give your own option. Answer with concrete artifacts:
- the literal stored or not-stored outcome;
- the basis-hash rows, if any change;
- the retry mechanism and its trigger or job SQL;
- the read result and its copy;
- the named regression test that proves a later settled run replaces WITHHELD.

Keep the ESTIMATED vectors' literal values unchanged. If they must change, give the new literal values.

## C1–C5

These are readings the builder intends to build: technical cutoff, hash rows, TARIFF_MISSING scope, tariff `recorded_at`, and the `source_gate` value. Implementer readings are defects. Confirm or replace each one with a literal value.

## Then

Dry-read commits 2–3 once more against the code. If nothing else is open, say so in one line.

## Output

Append to `.agent/W2-07-build-spec.md` as "Run 3 rulings (q3)". Write nothing else. Do not commit.
