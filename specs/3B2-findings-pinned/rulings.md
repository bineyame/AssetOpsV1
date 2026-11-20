# 3B2 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-8.md`. Handshake
answers go below under "Handshake answers (round 1)".

## D-3B2.1 A pin is a code row keyed by mechanism

- **Ruling.** `PINS` maps each mechanism to its structure key and factor. It is read at query time. No Finding column
  is added.
- **Why.** The design says "one registry row per mechanism … read at query time, so no Finding column is added" (§4).
  A stored column would freeze today's pin into every past Finding.

## D-3B2.2 Cold and EV mechanisms wait in `PENDING_PINS` until 3B6

- **Ruling.** `COLD_START_FAILURE`, `COLD_EXCURSION` and `EV_INTERRUPTION` stay in `PENDING_PINS` until 3B6 brings
  their registries. 3B6 decides their factors. The design names three: "crate-minutes above limit" (no row today),
  "nights without backup cover" and "chargers in service".
- **Why.** A pin must name a row that exists (`STRUCTURE_PIN`). Listing the three as pending keeps the check complete:
  every `FINDING:` key is accounted for.

## D-3B2.3 The literal stays until 3B5

- **Ruling.** 3B2 removes nothing from `outcome_map.ENTRIES` and changes no wire. 3B5 switches the categories to the
  pins.
- **Why.** The switch changes what the screens show (UNEXPLAINED_FUEL's heading), and screen changes wait for the UI
  review (D-BW1.2). The parity report proves the switch is safe before anyone makes it.

## D-3B2.4 UNEXPLAINED_FUEL reads under Optimize (design §2.0)

- **Ruling.** The registry's answer stands: a Finding pinned to `unexplained_l` is OPTIMIZE_COST, lens COST. The Protect
  card links it without counting it. 3B5 applies this, replacing the outcome map's MG-8 (Protect).
- **Why.** This is the design's named change (§2.0: unexplained litres read under Optimize, and the Protect card links
  the fuel-loss Finding without counting it). The owner approved it with the pack.

## D-3B2.5 A pin may not sit on a total its children explain

- **Ruling.** A pin on a node whose expression is only sums and differences is refused (`STRUCTURE_PIN_TOTAL`).
- **Why.** The design pins a Finding "to the most specific factor it observes … never a parent total whose change its
  children explain". Products and functions stay pinnable, because their change is not a plain sum of their
  children's changes.
