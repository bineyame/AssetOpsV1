# 3B2 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Read against main at 39e1682de (spec rev 1 is from 20 Nov; 3B3, 3B7a, 4b, 5a, 5b, 4d have merged since).

**R1 (done). T4 is circular as written (spec §6 T4; reviewer guide first check 2).** The snapshot is "written by the
test file from `ENTRIES` at import", then compared with `categories_for` / `lens_flags` read from the same `ENTRIES`.
That detects a change to the functions, not an edit to `ENTRIES` (the literal 3B2 promises not to touch): edit an
entry and snapshot and output move together. Expected answer: the snapshot is a literal committed in the test file
(or JSON beside it), written once from today's `main`, and the guide's first check also runs
`git diff main -- backend/assetops_backend/outcomes/` and requires it empty.

**R2 (done). Does `parity()` loop over domains that a mechanism cannot be in (spec §4)?** "One entry per pinned
mechanism and Site domain": `outcome_roles(..., "COLD")` for a MINI mechanism returns `((), ())`, so the literal
category is `None` against the registry's `OPTIMIZE_COST`, a spurious divergence on two of three domains. Expected
answer: a pin has one structure key, hence one domain (MINI_GRID -> MINI); `parity()` compares only that domain, and
the spec states the structure-key-to-domain map (written as a literal in the test too).

**R3 (done). D-SC1.28: does 3B2 add served text?** It adds a start-up refusal string (`STRUCTURE_PIN <key>/<m>`), the
`Divergence` fields and the D-3B2.4 ruling prose ("the Protect card links it without counting it"). I read all three
as codes or Architect-side prose, not served text (the refusal goes to `ConfigurationError` at start-up, like the
3B1 codes). Expected answer: the spec says so in one line: 3B2 adds no `messages.CATALOGUE` key, no sentence, no
word map; a diff that does is a High finding; D-3B2.4's Protect wording is for 3B5/SC-1 to carry as a statement.

**R4. T1 against the manifest is weak for the one pin that changes (spec §6 T1).** It asks only that some
`home_categories.findings` row has the pinned `factor` with a matching heading. `kobo-unexplained-fuel` (optimize,
`unexplained_l`) passes, so T1 holds and T3 carries the real weight. Expected answer: also assert the manifest row's
`site` domain is the pin's structure (Kobo is MINI_GRID), so a pin cannot match a row of another structure. Not (done);
the spec may decline.

## Implementer pre-flight questions

Checked against main at 39e1682de.

**I1 (done). `check_all(registries=...)` and the new check (spec §3).** `check_all` takes an optional `registries`
(3B1 tests plant copies). The spec has `check_all()` call `check_pins` "after every registry passes" but not which
registries it receives. If a planted `registries` without MINI_GRID reaches `check_pins` against the real `PINS`, it
raises `STRUCTURE_PIN` and breaks the 3B1 tests that plant registries. Expected answer: `check_all(registries=X)`
passes `X` through and runs the pin checks only when `registries is None` (the start-up path), or runs them with
`pins=None` and the same `X` and a rule for a key absent from `X`. Say which; T2 and the 3B1 file depend on it.

**I2 (done). Layering: `structure/check.py` would import `outcomes.outcome_map` (spec §3, last two codes).**
Today `structure/` imports nothing from `outcomes/` (3B1 reads the catalogue only through `registry`/`check`, and I
find no `outcomes` import in `structure/`). `check-architecture.ps1` is the guard; I have not run it with the import.
Expected answer: the import is allowed (read-only, call time, in `pins.py`/`check.py` only), or `pins.py` takes
`ENTRIES` keys through a parameter that `check_all` fills from `outcome_map`. Also confirm no import cycle
(`outcomes/outcome_map` -> `catalogue`; neither imports `structure`).

**I3 (done). Which `Expr` shapes count as "only a sum or difference" (spec §3, D-3B2.5).** `expressions.py` has `Num`,
`Ref`, `Bin`, `Neg` and `Call`. The spec names `Bin` `+`/`-` over `Ref`s and literals. Open: `Neg(Ref)` and a
`Bin +` over a `Neg` (sum, difference?), `Call` (not pinnable, as with products?), and a leaf (no expression, never a
total). Expected answer: pinnable unless the whole tree is `Bin(+|-)`/`Neg`/`Ref`/`Num`; any `Call`, `*` or `/` makes
it pinnable; a leaf is pinnable. The live rows: `diesel_l` and `metered_kwh` are totals; `fuel_cost` is a product.

**I4. `CODES` and the 3B1 tests (spec §3).** `check.CODES` is the ordered tuple of per-registry codes, and 3B1 tests
may assert its contents or count. The five pin codes are mechanism-level, run after registries, and are not in
`_CHECKS`. Expected answer: they stay out of `CODES`; a separate `PIN_CODES` tuple is exported so T2 can iterate it,
and `__all__` gains `check_pins` and `PIN_CODES` only. The spec's "two calls" in §7.5 then means one call from
`check_all` and the import.

**I5. Stale wording in §0 and §7.5.** The spec says 3B3 "adds `structure/evaluate.py`", "merge `main` after 3B3
merges", and lists `structure/__init__.py` (docstring) as changed. All merged; `structure/` now also holds
`litres/`, `attribution/`, `targets/`, `money.py`, `read.py`, and `registry.py` is at v3 (4b1 stated nodes). Does the
pin check need anything about stated nodes (a pin on a stated node such as `fuel_cost`: pinnable, a product)? Expected
answer: no change to scope; the worktree starts from current `main`; pins on stated nodes are not refused by 3B2.

**I6. Name collision: "pin".** `pin_of` is already a parameter and `selected_finding_pin` a helper in the W5xx
domain-intent stores (a different meaning: a Finding the user selected). A new `structure.pins.pin_of` and
`PINS` (also `k0_byte_equal_pins.PINS` in tests) invites a wrong import. Expected answer: keep the spec's names (the
design says "pin") and have the packet list the import path in the test; or rename the function `factor_pin_of`.
Spec's choice; not (done).
