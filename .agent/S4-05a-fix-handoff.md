# S4-05a fix round handoff

- L2: `source_provenance.py` `consequence_revision`: Finding part UNKNOWN (incl. EMPTY_CITATION_SET) -> consequence
  UNKNOWN, finding-part reasons first, then non-duplicate union reasons; never positive/MIXED. Tests: pure
  `test_unknown_finding_part_makes_the_consequence_unknown_never_positive`, PG
  `test_unknown_finding_makes_its_consequence_unknown_even_with_bound_power_inputs`; both fail on the old code
  (proved by restoring it), 22 pass on the fix. Rule recorded in review packet and phase-2 handoff (S4-05b contract).
- L1: `tools/checks/configuration-persistence.ps1` rule 8 (`$provName`/`$provVerb`) refuses UPDATE/DELETE FROM/TRUNCATE
  with schema-qualified, quoted names, and verb-on-one-line / table-on-next. Probes (temp file, removed): split,
  schema-qualified, quoted+schema each refused by the "insert-only" message; split DELETE FROM / TRUNCATE are refused
  by the generic second-writer rule (which `continue`s before rule 8, so rule 8 is a backstop there). Clean tree:
  `check-architecture.ps1` passes (temporary .venv junction removed; private DB dropped).
- Note: check-architecture is slow (~2 min failing, 30+ min clean under machine contention).
