# 0K4b handshake, implementer side

Implementer (Claude), 2026-11-21, pre-flight against `main` `0ead104e9` (spec base `fa13f254f`). No product code
written. Shared round with 0K4a (D-0K4.17); 0K4a's own questions are in `specs/0K4a-dispatch-v8/handshake-I.md`.

Checked and as the spec says: `CANONICAL_UNITS["L/h"]` freezes as `VOLUME_RATE` in `L/min`, value / 60
(`contracts/assetops_contracts/execution_contract.py:467`); `minigrid._coefficient` (`packs/minigrid.py:167`),
`_percentage` (:109), `_one` (:372); `PhysicallyUnacceptable` through `packs/fuel.py:66`; the FUEL-1 catalogue rows and
`STATE_PROPERTY_VALUES` / `MINIGRID_PROPERTY_CARRIERS` (`sites/models.py:275-351`); `tools/demo_combined_kobo.py:138-143`
(3.3 L/h, `GENERIC_DEFAULT`); the Kobo template has no no-load, minimum-load or taper property, so `assumed_site`
appends without a collision; `host/tests/kobo.py` `component` (:83); F1-F8 arithmetic (s = 0.2175, 5.475 L, 7.65 L,
the F6 cap and the F7 taper values all recomputed).

## Implementer questions (I)

**I1. The new catalogue and profile strings fail the SC-1 hand-built ratchet.** §2.3's four `display_name` literals
(`sites/models.py`) and §2.4's three `_need` statements (`runs/profiles.py`) are prose (rule g,
`tools/checks/statement_catalogue.py:398-399`); I ran `ratchet_hits` on those exact literals and each one gives a
fingerprint, so each would be a `HAND_BUILT_NEW` (:965-970). The allow file takes only `SQL`, `HASH` or `CODE` (:56).
D-SC1.34 (`specs/SC-1-statement-composer/rulings.md:524-526`) lets a fingerprint into the baseline only when "the
unit's spec names the text and the reason with a D-ID". The spec names neither. **Default:** a ruling (for example
D-0K4.19) that names these seven strings as Foundation-catalogue and profile data. It would baseline them in
`statement-handbuilt-baseline.json`, in the same class as the 49 (`models.py`) and 93 (`profiles.py`) fingerprints
already there. I would add exactly those seven fingerprints and no others. The same ruling would cover 0K4a's v8
statement strings (0K4a I5).

**I2. The pre-flight's "every v7 Kobo digest test stays green" does not test `assumed_site`.**
`host/tests/test_registered_kobo_execution.py` never applies `assumed_site`, and its only digest is the publication
`content_digest` (:38). No kernel trajectory digest helper exists in `host/` or `host/tests/`. **Default:** run that
file unchanged and record it green. Then add one pre-flight comparison: a v7 `kobo_draft(...)` run executed with and
without `site_edit=assumed_site` gives equal trajectories boundary by boundary (stocks, interval measurements,
discrete states). The packet records it. No edit to the existing file.

**I3. Small differences from the spec, resolved by content.**
- `_need` is at `runs/profiles.py:953`, not 1140-1230.
- §2.1 says the module imports only `fractions`, `packs.minigrid` and `packs.fuel`. It also needs `dataclasses`, and
  `StateHandler` for §2.2's annotation (`kernel.model`, as `mini_grid.py:60` imports it).
- P1-P2 run in `backend/tests/` but import `host/tests/kobo_assumed.py`. I would put `host/tests` on `sys.path` the
  way `backend/tests/test_4a_energy_to_cash_postgres.py:30` does. `kobo_assumed.py` would import only `component`
  from `kobo.py`.

**Default:** as listed. No spec change needed.

**I4. Reusing `_percentage` gives the wrong refusal sentence.** `minigrid._percentage(what)` refuses with "{what} of
{v} % is not a share of a battery" (`packs/minigrid.py:109-117`). §2.2 uses it for the generator minimum load, so a
bad value would read "a minimum generator load of 120 % is not a share of a battery". **Default:** add a local
accept function `_share_of_rating` in `generator_curve.py` that refuses outside [0, 100] with "a minimum generator
load of {v} % is not a share of the generator's rating". F10 asserts that text. `minigrid.py` is not touched.
