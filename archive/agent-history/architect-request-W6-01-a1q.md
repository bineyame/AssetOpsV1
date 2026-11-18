# Architect request: W6-01 A1 builder questions

You are the AssetOps Architect. The A1 builder stopped before writing code. Its questions Q1-Q9, with file:line, are in `.agent/W6-01a-phase-handoff.md`.

- **Q1-Q2:** A1's file list conflicts with check-all rule 8.
  - Only the files listed in `$pgReaders` may import sqlalchemy (`tools/checks/configuration-persistence.ps1:833`, `:900-904`).
  - Only `work/composition.py` may import work adapters (same file, `:8`, `:168-176`).
  - Amend A1's card: add the exact files, the guard-list edit, and the composition wiring.
- **Q3-Q9:** rule each one with a literal answer.

Also check the remaining W6-01 unit cards and the W5-01 and W5-03 unit cards (`.agent/W5-01-build-spec.md`, `.agent/W5-03-build-spec.md`) for the same guard-ownership class of gap. Any unit adding a new pg reader, adapter, router or route must list the guard files and composition files it has to edit. Amend those in place too.

Update the cards in place, add rows to the closure tables, and append amendment lines to the two decisions. Write nothing else. Do not commit.
