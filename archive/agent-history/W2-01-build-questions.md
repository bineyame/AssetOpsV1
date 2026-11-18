# W2-01 build questions (implementer stopped before coding, 2026-10-17)

Verbatim summary of the implementer report (questions A-I plus W2-02 carries):

A. Topology vocabulary for cold relations: node roles for COLD_ROOM, TEMPERATURE_PROBE, COMPRESSOR, TRANSFER_SWITCH; medium values for the probe link and cooling link; whether these live in `topology.connections` or a separate relation list (`models.py:232,247`: TOPOLOGY_NODE_ROLES electrical + FUEL_STORAGE; CONNECTION_MEDIA = {AC,DC,FUEL}); cycle/duplicate-edge check is new code.
B. EVENT roles in `cold-roles-1` (backup_request/result, transfer_result, door_event, manual_temperature): declared signal unit (SIGNAL_UNITS closed, no event unit); binding source_unit/canonical_unit for events other than the manual log (v4 events carry null unit). The design adds `Role.value_kind EVENT` only in W2-02 text (§4 line 102).
C. The 13 cold properties: which component type carries each (room/compressor/generator/probe); PHYSICAL or CONTROL; new UNIT_RANGES for kWh/degC, kW/degC, kWh/min, degC (range and sign/limit).
D. Commissioning: no record exists; confirm W2-01 always serves `commissioning.state=UNCONFIRMED` with empty `evidence_ids`.
E. Contact: S7 gives CURRENT|STALE|UNKNOWN, design wants RECENT|STALE|NEVER; confirm CURRENT->RECENT and UNKNOWN (no diagnostic) -> NEVER.
F. `bindings[].cadence` has no stored source (gateway has `declared_cadence_seconds`); confirm source or fixed 5-minute value.
G. Routes: no `cold-*` paths; mock maps cold screens onto the Foundation tab per Site type (`screens.js:605`); confirm `/sites/:id/foundation`, `/foundation/sld`, `/foundation/readiness` switch to cold views for COLDCHAIN.
H. Primary probe: room->probe link marks the room's primary chamber probe; exactly one per room; ambient probe has no room link.
I. Dynamic titles for `cold-readiness:2` and `cold-sld:1`: confirm mini-grid rules (`Gateway status · {gateway or "No gateway selected"}`; `{site name} · {topology type if stated}`) and add to APPROVED_TITLE_CHANGES.
W2-02 carries: W2-00 review Low 2 role check - `grid-meter/event` (POWER_LOSS/RESTORED) has no role in cold-roles-1; `generator-controller/start-event` serves backup_request and backup_result. Mock "Mapped / Not mapped" wording fails the vocabulary scan (in-panel copy).
Code anchors: `sites/models.py:26-50,88-171,232-262`, `foundation_parsing.py:361-444,1060-1199`, `foundation_content.py:210-311`, `binding_roles.py:41-130,163-207`, `binding_service.py:225-392,448-652,658-776`, `evidence/gateway_access.py:290-330`.
