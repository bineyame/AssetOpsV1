# 3B2: Findings pinned to their factors (implementer spec)

Architect (Claude), 2026-11-20. Rev 1, spec handshake step 1.

- **Lane:** B. The schedule order is `3B1`, `3B3`, then `3B2`.
- **Structure:** P3B (approved 20 Nov) and `decision-loop-specification.md` §4 ("The pin").
- **Decisions:** `rulings.md` (D-3B2.1 to D-3B2.5).
- **Reviewer guide:** `reviewer-guide.md`.

Non-screen. 2.5 units. Discovery review (W5), because this is a mechanism on a protected seam.

## 0. Before you start

- **Branch.** `task/3B2-findings-pinned` off `main`. It depends only on `3B1` (merged). Worktree:
  `/opt/assetecon/AssetOpsV1-3b2`. Code starts when the handshake has no open question.
- **Python.** The shared `.venv` imports `main`. Set this tree first and check the module paths:
  ```bash
  cd /opt/assetecon/AssetOpsV1-3b2
  export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
  PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
  $PY -c "import assetops_backend, assetops_contracts; print(assetops_backend.__file__, assetops_contracts.__file__)"
  ```
  The packet records this output.
- **Read:**
  - `rulings.md`;
  - `backend/assetops_backend/outcomes/outcome_map.py` (`ENTRIES`, `categories_for` and `lens_flags`);
  - `outcomes/catalogue.py`;
  - `structure/registry.py`, `check.py` and `expressions.py`;
  - `backend/tests/test_out_a1_outcome_map.py`;
  - the manifest's `home_categories.findings`;
  - `specs/3B1-structure-registry/rulings.md` (D-3B1.7 to D-3B1.9 and "Review round 1 answers").
- **Databases.** None: nothing here reads a store.
- **Collisions.**
  - `3B3` (lane B, before this unit) adds `structure/evaluate.py` and the read. This unit adds `structure/pins.py` and
    extends `check.py`. Merge `main` after `3B3` merges.
  - Lanes A and C do not touch `structure/` or `outcomes/`.

## 1. Outcome and why

Every stored Finding mechanism names the factor it observes, through one registry row per mechanism, read at query
time. This adds no Finding column (§4 of the design).

Two things follow:
- the Finding enters the structure, so the bridge, the observer (`3B4`) and the site board (`3B5`) can place it on its
  factor;
- its category becomes its factor's home category (OD-21).

The outcome map's literal stays in this unit: removing it would change what screens show (D-3B2.3). Instead, a parity
test lists every difference between the literal and the registry, and the Architect rules each one. Gate question
(`delivery-plan.md` §3, step 3B): does every stored Finding mechanism resolve to the factor it observes, through one
registry row?

## 2. The pins (`structure/pins.py`)

Pin is a frozen dataclass: `Pin(mechanism: str, structure_key: str, factor_id: str)`.
`PINS: Mapping[str, Pin]` is a `MappingProxyType` that holds today's stored mechanisms on structures that have a
registry:

| Mechanism | Structure key | Factor (design §4) |
|---|---|---|
| `GENERATOR_SUPPORT_CANDIDATE` | MINI_GRID | `candidate_l` |
| `UNEXPLAINED_FUEL` | MINI_GRID | `unexplained_l` |

`PENDING_PINS: Mapping[str, str]` holds mechanism → structure key for mechanisms whose registry does not exist yet. It
says which slice pins them: `COLD_START_FAILURE` and `COLD_EXCURSION` (COLD_CHAIN), and `EV_INTERRUPTION`
(EV_DEPOT_CAPTIVE). `3B6` moves them into `PINS` (D-3B2.2).

Functions:
- `pin_of(mechanism) -> Pin | None`.
- `pinned_category(mechanism) -> str | None`: the home category of the pinned factor's row.
  - Its source is `registry.REGISTRIES[pin.structure_key].row(pin.factor_id).home.category`.
  - It returns `None` for a pending or unknown mechanism, and `None` for a pin whose row's home is `ABOVE` or
    `CALENDAR`.

## 3. The start-up check (extends `structure/check.py`)

`check_pins(pins=None, registries=None)` is called by `check_all()` after every registry passes. It reads
`pins.PINS` and `registry.REGISTRIES` at call time.

It raises `StructureError` with text `"<CODE> <structure_key>/<factor_id>"`. For a mechanism-level fault the factor
position holds the mechanism: `STRUCTURE_PIN <key>/<mechanism>`. The checks run in this order:

| Code | When |
|---|---|
| `STRUCTURE_PIN` | the pin's structure key has no registry, or its factor has no row |
| `STRUCTURE_PIN_TOTAL` | the pinned row is a node whose expression is only a sum or difference of factors (`Bin` with `+` or `-` over `Ref`s and literals all the way down): "never a parent total whose change its children explain" |
| `STRUCTURE_PIN_DUPLICATE` | a mechanism appears in both `PINS` and `PENDING_PINS` |
| `STRUCTURE_PIN_UNKNOWN` | a mechanism of `PINS` or `PENDING_PINS` is not a key of `outcome_map.ENTRIES` (as `FINDING:<m>`) |
| `STRUCTURE_PIN_MISSING` | a `FINDING:` key of `ENTRIES` is in neither `PINS` nor `PENDING_PINS` (`FINDING:UNMAPPED` excepted) |

These are the last two checks of `check_all()`, so `check_at_start()` refuses the process on any of them.

## 4. The parity report (`structure/pins.py`)

`parity() -> tuple[Divergence, ...]` produces one entry per pinned mechanism and Site domain. `Divergence(mechanism,
literal_category, registry_category, literal_lens, registry_lens)` compares two readings:
- `literal_category` is the category of `outcome_roles("FINDING:<m>", domain)[0][0]`, as today;
- `registry_category` is `pinned_category(m)`;
- the lenses come from `LENS_OF_CATEGORY` for each category.

The function returns only the entries that differ.

**The expected differences** are ruled in D-3B2.4 and written into the test as a literal:

| Mechanism | Literal (outcome map) | Registry (factor home) | Ruling |
|---|---|---|---|
| `UNEXPLAINED_FUEL` | PROTECT_ASSET (MG-8 "Fuel accounted for"), lens RISK | OPTIMIZE_COST (`unexplained_l`, O1), lens COST | Design §2.0 named change: unexplained litres read under Optimize. The Protect card links the fuel-loss Finding without counting it. The wire changes in `3B5`, not here |

`GENERATOR_SUPPORT_CANDIDATE` agrees (MG-2 OPTIMIZE_COST = `candidate_l` O1), so it is not listed.

## 5. What does not change

- `outcome_map.ENTRIES`, `categories_for`, `lens_flags`, `outcome_roles` and every wire that reads them: no byte
  changes.
- No Finding column and no migration.
- The literal goes, and the categories are read from pins, in one place: `3B5` (screen, held) switches the wire,
  applying D-3B2.4's rulings with the owner's walkthrough (D7).

## 6. Tests (written first)

All in `backend/tests/test_3b2_findings_pinned.py`; no database.

- **T1 Pins against the design and the manifest.**
  - `PINS` equals the design §4 table above, which the test writes as its own literal.
  - Each pinned factor appears as the `factor` of some `home_categories.findings` row whose `heading` maps to the same
    category. This is read from YAML, and the test uses its own map: `grow` → GROW_REVENUE, and so on.
- **T2 Start-up check.** Each §3 code is raised with its full text on a planted copy:
  - a pin to a missing factor;
  - a pin to `diesel_l`, which is a sum: `STRUCTURE_PIN_TOTAL MINI_GRID/diesel_l`;
  - a duplicate between `PINS` and `PENDING_PINS`;
  - a mechanism not in `ENTRIES`;
  - an `ENTRIES` `FINDING:` key left unpinned.

  The real data passes `check_all()`. `create_app()` with a planted bad pin raises `ConfigurationError`.
- **T3 Parity.** `parity()` equals the expected-differences literal of §4 exactly. A new difference, or a vanished
  one, fails the test until the Architect rules on it (W2: the expectation is the ruling, not the code).
- **T4 No wire change.**
  - `categories_for` and `lens_flags` for every `FINDING:` key and domain give the same output before and after.
  - The test compares against a JSON snapshot written by the test file from `ENTRIES` at import, so this is not
    circular: it pins today's function output.
  - `test_out_a1_outcome_map.py` passes unchanged.
- **T5 `pinned_category`.**
  - It returns `OPTIMIZE_COST` for both mini mechanisms.
  - It returns `None` for the three pending mechanisms and for an unknown one.

Commands:
```bash
env -u DATABASE_URL -u ASSETOPS_TEST_DATABASE_URL $PY -m pytest backend/tests/test_3b2_findings_pinned.py backend/tests/test_3b1_structure_registry.py backend/tests/test_out_a1_outcome_map.py backend/tests/test_health.py -q
pwsh -NoProfile -File tools/check-all.ps1
python3 tools/select-tests.py --base main
```

## 7. Done (questions)

1. Does every stored Finding mechanism either resolve to its factor through one pin, or stand in `PENDING_PINS`,
   naming the slice that pins it?
2. Is a pin to a missing factor, or to a total its children explain, refused at start-up?
3. Is every difference between the outcome map and the registry listed, and is each one ruled?
4. Is every byte of today's wire unchanged?
5. Is nothing changed outside these files and the finish bookkeeping?
   - `structure/pins.py`
   - `structure/check.py` (two calls)
   - `structure/__init__.py` (docstring)
   - the test file

Packet: `specs/3B2-findings-pinned/packet.md`, with the module-path output and the mid-build question count.

## 8. Out of scope

- Removing the literal and switching the wire (`3B5`).
- Cold and EV pins (`3B6`).
- The observer's own Findings (`3B4`).
- Non-Finding signals and warnings: they stay in `ENTRIES` until their own slices.
