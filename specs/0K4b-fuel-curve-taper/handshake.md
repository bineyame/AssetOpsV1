# 0K4b handshake

Shared round with 0K4a (D-0K4.17); 0K4a's reviewer questions are in `specs/0K4a-dispatch-v8/handshake.md`.

## Reviewer questions (R)

Fresh Claude reviewer, 2026-11-21, on `main` `0ead104e9`. Read: `spec.md`, `reviewer-guide.md`, D-0K4.1 to D-0K4.18,
`one-figure-change-list.md`, the owner's one-figure file, and the cited code (`execution_contract.py:465-479`,
`packs/minigrid.py:100-180`, `sites/models.py:269-352`, `runs/profiles.py:953-970`, `host/tests/kobo.py:66-160`).

**R1. Done question 2 cannot be decided by any 0K4b test (rule a test can't decide; plant P4 ambiguous).** Gate and
Done 2 ask whether a *frozen* `L/h` value burns correctly in a 5-minute step. Every F test passes the `L/min` literal
`33/600`, so no test runs the contract's conversion (`CANONICAL_UNITS["L/h"] = CanonicalUnit("VOLUME_RATE", "L/min",
1, 60)`). The module never sees `L/h`; its only time factor is the `60 x` in the slope. So plant P4 ("the no-load rate
read as L/h without the /60") has no single reading: dropping the slope's `60 x` fails F2, not F4; multiplying the rate
by `minutes / 60` fails F4. Guide check 2 ("the /60 or x 60 appears in one place") is also unclear about which factor
it means.
*Default:* add **F11**, which freezes `3.3 L/h` through the contract's own canonical conversion (the function that
applies `CANONICAL_UNITS`, not hand division) and passes the result to `fuel_curve`. A 5-minute STARTING step must then
burn exactly `0.275` L. P4 becomes "`fuel_litres` uses `minutes / 60` (reads the L/min input as L/h)", and it must
fail F4 and F11. Guide check 2 then reads "the one `60` in the module is the slope's `60 x no_load / rated`".

**R2. Nothing pins the module's constants, so v8 could change without a version bump (simulator-version
reproducibility).** From 0K4a's merge, `DIESEL_ENERGY_KWH_PER_L = 10`, `TAPER_FLOOR_SHARE = 1/20`, `MIN_SFC_L_PER_KWH`
and the refusal order are part of `mini-grid` v8's behaviour, and of its digests and 0K4d's SIMULATED litres. A later
edit to `generator_curve.py` would silently change every v8 trajectory while leaving v1-v7 byte-equal. N9 would not
catch it.
*Default:* add **F12**, which asserts the three constants as literals (`Fraction(10)`, `Fraction(1, 20)`,
`Fraction(1, 10)`). The module docstring then says "these are `mini-grid` v8's physics: changing one is a new model
version, never an edit". The v8 digest pin is in 0K4a R5.

**R3. Pre-flight item 2 is true whatever the code does.** "`assumed_site` leaves every v7 Kobo digest test green" is
always true, because `test_registered_kobo_execution.py` never calls `assumed_site`. The question that matters is
whether a v7 run's frozen Foundation, and so its digest, changes when the six rows are added. 0K4a's `run7` (N3, N6)
compares v7 and v8 on a site that has `assumed_site` applied, and N9 compares a digest taken without it.
*Default:* the pre-flight prints the v7 digest of `base_run(8)` twice, with and without `assumed_site`, and says
whether they differ and why (whether the frozen Foundation carries every Site property or only the model's needs).
0K4a's N9 then uses the default `site_edit=season_site`.

**R4. In the packet's F3 table, litres per kWh at 0 % load has no value (missing shown as 0).** At 0 % load the
generator burns 3.3 L/h for 0 kWh, so litres per kWh is undefined. A 0, an infinity or a blank would each misread.
*Default:* that cell reads "not defined (no output)". The litres-an-hour column reads 3.3 at 0 %. The table is
headed "assumed (GENERIC_DEFAULT)", with no design value beside it (D-0K4.11).

**R5. P1 names neither the parser nor the import path.** P1 says "a Kobo template document with `assumed_site`
parses through the Foundation parser". The code has two parsers: `sites/parsing.py:parse_site_template` (template
shape) and `sites/foundation_parsing.py:parse_foundation_content` (the site-document Foundation that `assumed_site`
edits through `component(document, id)`). `assumed_site` is also in `host/tests/`, which a `backend/tests` module would
have to import across a test-tree boundary.
*Default:* P1 renders the Kobo template into a site document (`render_site_document(site_from_template(...))`, as
`host/tests/kobo.py:kobo_site` does). It then appends the six rows *inline*, as its own literal (W2: independent of
the fixture), and parses them with `parse_foundation_content`. P2 and P3 use the same path. A separate host-side
assertion checks that `assumed_site` writes the same six rows.

**R6. The minimum-load refusal reuses battery wording.** `daytime._percentage(what)` refuses with "`{what}` of `{v}` %
is not a share of a battery" (`packs/minigrid.py:109-116`). Through `CURVE_HANDLERS`, a bad `generator-minimum-load`
would be refused as "a minimum generator load of 120 % is not a share of a battery". That refusal reaches the
run-refusal detail.
*Default:* add a `_generator_share` acceptor to `generator_curve.py`, with the same `0..100` rule and the text "a
minimum generator load of {v} % is not a share of the generator's rating". F10 asserts that text. `packs/minigrid.py`
stays untouched.
