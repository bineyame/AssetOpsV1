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

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, checked against `main` at 39e1682de. Spec is now rev 2. One answer per question;
the question's number is in the title.

## D-3B2.6 The snapshot is a literal, and the outcomes diff is empty (R1)

- **Ruling.** T4's snapshot is a literal committed in the test file, written once from today's `main` (the output of
  `categories_for` and `lens_flags` for every `FINDING:` key of `ENTRIES` and `FINDING:UNMAPPED`, over the three
  domains `mini_grid`, `cold_chain`, `ev_charging`). The test file never builds it from `ENTRIES`. The reviewer's first
  check also runs `git diff main -- backend/assetops_backend/outcomes/` and requires it empty.
- **Why.** Built from `ENTRIES` at import, the snapshot moves with an edit to an entry, so it proves nothing about the
  literal 3B2 promises not to touch. A committed literal plus an empty diff of `outcomes/` is the independent check.

## D-3B2.7 A pin has one domain; `parity()` compares only that one (R2)

- **Ruling.** A pin has one structure key, hence one domain. The map is a literal in `pins.py` and again in the test:
  `MINI_GRID` -> `mini_grid`, `COLD_CHAIN` -> `cold_chain`, `EV_DEPOT_CAPTIVE` -> `ev_charging` (the `catalogue.py`
  values, lower case). `parity()` has one entry per pinned mechanism, compared in that domain only.
- **Why.** `outcome_roles(..., "cold_chain")` for a mini mechanism returns `((), ())`; comparing it with the registry
  would report a divergence that is not one. Today only `mini_grid` pins exist.

## D-3B2.8 3B2 adds no served text (R3; D-SC1.28)

- **Ruling.** 3B2 adds no `messages.CATALOGUE` key, no sentence and no word map. The `STRUCTURE_PIN*` strings are
  start-up codes that reach `ConfigurationError` only, like 3B1's. `Divergence` and `Pin` are code records and are
  not served. The Protect wording in D-3B2.4 is Architect prose: `3B5`/SC-1 carry it as a statement when they switch
  the wire. A diff that adds served text is a High finding. So D-SC1.28 does not bite: 3B2 can build and merge without
  SC-1a.
- **Why.** Text waits for the statement composer (D-SC1.28); nothing here is shown to a user.

## D-3B2.9 T1 also checks the manifest row's structure (R4)

- **Ruling.** Accepted. T1 asserts the matching `home_categories.findings` row's `site` maps to the pin's structure
  key, through a literal site-to-structure map in the test (`Kobo`, `Kisiwa`, `Mto` -> `MINI_GRID`).
  - Neither mini pin is a cold or EV row, so a pin cannot match a row of another structure.
- **Why.** The check is cheap, and the row is where the design places the Finding.

## D-3B2.10 Pin checks run only on the start-up path (I1)

- **Ruling.** `check_all(registries=X)` is unchanged when `X` is given: it checks only `X` and runs no pin check.
  `check_all()` (no argument, the `check_at_start` path) checks the registries, then calls `check_pins()`.
  `check_pins(pins=None, registries=None, pending=None, entries=None)` reads the real `PINS`, `REGISTRIES`,
  `PENDING_PINS` and `outcome_map.ENTRIES` at call time when an argument is `None`; T2 calls it directly with planted
  copies, and `create_app()` with a planted pin for the start-up case.
- **Why.** 3B1's tests plant registries with no `MINI_GRID` and would hit `STRUCTURE_PIN` against the real `PINS`.
  Pins belong to the real catalogue, so they are checked against the real registries.

## D-3B2.11 `structure/` may import `outcomes.outcome_map` (I2)

- **Ruling.** Allowed, read-only, in `pins.py` and `check.py` only, at module level, reading `ENTRIES` through the
  module at call time (`outcome_map.ENTRIES`, never a copy).
  - **Guard evidence.** `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON=.venv/bin/python`) printed
    "Architecture check passed." on a probe worktree with `from assetops_backend.outcomes import outcome_map` added to
    `structure/check.py`. Its modules are dependency-direction (simulator, host and contracts only) and chain-structure
    (chain rows); none restricts `structure/` to `outcomes/`.
  - **Precedent.** `structure/registry.py` already imports `outcomes.catalogue` (`CATEGORIES`).
  - **No cycle.** `outcome_map` imports only `outcomes.catalogue`; `catalogue` imports nothing from `structure/`; none
    of `outcomes/` imports `structure/` (a grep returns nothing, and importing `outcome_map` loads no `structure`
    module).
  - `pins.py` imports `registry` and `outcome_map`; `check.py` imports `pins`; `pins.py` never imports `check.py`.
- **Why.** The check must know the `FINDING:` keys, and a parameter would only move the same read elsewhere. The guard
  and the import graph allow it. No guard is changed (no authorisation widened).

## D-3B2.12 Which expressions are totals (I3)

- **Ruling.** `STRUCTURE_PIN_TOTAL` is raised when the pinned row is a node whose parsed tree contains only `Bin` with
  `+` or `-`, `Neg`, `Ref` and `Num`. A bare `Ref` (an alias) counts as a total. Any `Call`, any `*` or `/` anywhere in
  the tree makes the row pinnable. A leaf has no expression and is pinnable.
- **Live rows.** `diesel_l`, `metered_kwh`, `billed_kwh` and `cost_to_serve` are totals; `fuel_cost` is a product and
  pinnable. T2 plants `diesel_l` (the spec's case) and one product row that stays accepted.
- **Why.** The design refuses a parent total "whose change its children explain"; only a plain sum or difference is
  one. A product's change is not a sum of its children's changes.

## D-3B2.13 `PIN_CODES` is separate from `CODES` (I4)

- **Ruling.** The five pin codes stay out of `check.CODES` (3B1's per-registry order). `check.py` exports
  `PIN_CODES`, in the §3 order, for T2 to iterate. `__all__` gains `check_pins` and `PIN_CODES` only. The §7.5 "two
  calls" reads: one call from `check_all`, one import (`pins`, with `outcome_map` read through it).
- **Why.** `CODES` is registry-level and 3B1 tests may count it; the pin codes are mechanism-level.

## D-3B2.14 The spec's stale text is corrected; pins on stated nodes are allowed (I5)

- **Ruling.** Spec §0 and §7.5 are corrected (rev 2): 3B3 and 3B7a, 4b and 5a/5b have merged; the worktree starts from
  current `main`; `structure/__init__.py` is not touched (its docstring is not a deliverable). No change of scope for
  stated nodes: a pin on a stated node (`fuel_cost`, a product) is not refused; a stated sum would be refused as a
  total by D-3B2.12, which is correct. `registry.py` v3 is read, not changed.
- **Why.** The pin check reads rows and expressions, and a stated key changes neither.

## D-3B2.15 Keep the name `pin_of` (I6)

- **Ruling.** The names stay (`Pin`, `PINS`, `PENDING_PINS`, `pin_of`, `pinned_category`), because the design says
  "pin". The collision is with `selected_finding_pin` and a `pin_of` parameter in the W5xx stores and with
  `k0_byte_equal_pins.PINS` in tests. The test imports them as `from assetops_backend.structure import pins`, and the
  packet lists that import path. No other module imports `pins` by bare name.
- **Why.** A rename for a name clash in other modules adds churn to a unit whose scope is small; the import path
  settles it.
