# DD3b handoff (after DD3b1; parts DD3b2 and DD3b3 not started)

- Done: DD3b1, the v9 pack (D-DD.127) and its parity, on `task/DD3b-mini-plant`. Packet: `packet-DD3b.md`.
- Anchors: `simulator/assetops_simulator/packs/mini_grid.py` from `# --- mini-grid v9` (after v8's model, line
  ~1877): `_lead_context`, `_unit_plant`, `prepare_v9`, `due_v9`, `view_v9`, `decide_v9`, `_unit_events`,
  `commit_v9`, `resolve_v9`, `_resolve_units`, `MINI_GRID_V9_MODEL`. Tests:
  `simulator/tests/world/test_mini_grid_v9.py` (helpers `_v9`, `_second_generator`, `_two_inverters`, `_event`).
- Next (DD3b2): the writer drives v9 where a Site has more than one generator or inverter (D-DD.129); unit events go
  in as one-minute WINDOW forcings `unit-fail@<unit>` / `unit-restore@<unit>`, value 1, dimension COUNT, unit "1"
  (packet Known Deviations 1); each inverter needs a DiscreteInitialValue `inverter-state` AVAILABLE and, on a
  multi-inverter Site, `pv-array-share`; extra generators need GENERATION and FUEL_SUPPLY attachments and their own
  curve keys. Then DD3b3 (notes and leaves) after DD3b2.
- Risks: the Architect may rule the kernel should expose POINT forcings instead (Known Deviations 1); the pack would
  read them unchanged, the writer's shape would change.
