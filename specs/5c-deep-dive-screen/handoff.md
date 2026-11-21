# 5c handoff (unit 1 done; units 2 and 3 next)

Builder (Claude), 2026-11-21, branch `task/5c-deep-dive-screen`, head 37e823259 (main fa13f254f merged at f3a995997).

## Unit 1: done
- `deep_dive/{tables,words,view}.py` and `i18n/statements/en/deep_dive.py`; `words.py` and `view.py` are in the
  guard's `ADOPTED` (`tools/checks/statement_catalogue.py:41`); `python tools/checks/statement_catalogue.py` is OK.
- Tests: `backend/tests/test_5c_deep_dive_view.py` (tests 1 to 7 plus every-variant case rendering; 136 passed),
  cases `backend/tests/statement_cases/deep_dive.py`, fixture `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json`.
- Plants P1, P2, P4, P6, P9, P11, P13 to P17 each fail their test: `/opt/assetecon/evidence/5c/unit1/plants.txt`.
- Focused tests on the host: `bash tools/heavy-slot.sh --wait-seconds 3000 -- bash -c 'cd backend &&
  PYTHONPATH=$PWD:$PWD/../contracts:$PWD/../simulator /opt/assetecon/AssetOpsV1/.venv/bin/python -m pytest
  -p no:cacheprovider tests/<file> -q'`.

## Literals that differ from spec 3.5 (each from a rule; the packet lists them)
- PF2/D-4A.12: the revenue stop text and `not_available.rows` follow 4a's records (billing export, feeder meter,
  meter register, meter reads, loss band; no tariff-sheet or billing-adjustments row).
- PF5 "when" in tile4; PF8 `headline` is `{"text","evidence"}` (A: ["Estimated"]); D-3A7.16 `standing.details` and the
  assure drawer lines `[text, *details]`; A2 reads "so they cannot be compared"; PF12 SITE_SETUP words.
- KD1 (World H): the Diesel price driver has `detail` null (a price does not sum across Sites, so the portfolio row has
  no actual or target; section 3.2's rule gives null) and word "Modelled, not yet reconciled" (its effect is Modelled
  litres times the price difference). Spec 3.5 H's literal said "Actual $1.25 per L · Target $1.25 per L",
  "Emulated". The code follows the rule.
- KD2: the fixture was written from World A's run after every value was compared with section 3.5; test 3 asserts
  each section 3.5 literal by hand as well, so the fixture cannot drift without test 3 failing.
- L5 lead vector added (P14 survived L1 to L4).

## Next
- Unit 2 (spec section 4; tests 8, 9), then unit 3 (section 5; tests 10 to 15), then the packet.
