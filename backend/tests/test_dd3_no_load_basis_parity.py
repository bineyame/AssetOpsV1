"""DD3a (D-DD.67, D-DD.68): the no-load basis has one vocabulary; the change only admits DATASHEET_FIT.

The goldens in `fixtures/dd3_no_load_basis_parity.json` were generated on main 80661e824 before the change.
`python tests/test_dd3_no_load_basis_parity.py --write` regenerates them (only ever run on main).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_fuel_cost_v2 import PRICE, finding, foundation  # noqa: E402

from assetops_backend.chain.vocabulary import NO_LOAD_BASIS_WORDS  # noqa: E402
from assetops_backend.financials import fuel_cost as fc  # noqa: E402
from assetops_backend.financials import fuel_cost_v2 as fc2  # noqa: E402
from assetops_backend.sites.models import STATE_PROPERTY_VALUES  # noqa: E402
from assetops_backend.site_outcomes.mini import COST_IDLE  # noqa: E402

GOLDEN = Path(__file__).parent / "fixtures" / "dd3_no_load_basis_parity.json"
READINGS = [(0, 60, "20", "F1"), (60, 120, "0", "F1"), (120, 150, "12.5", "F1")]


def _cases() -> dict:
    out = {}
    for basis in ("GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST"):
        f = finding(READINGS, [foundation("F1", basis=(basis,))])
        out[basis] = json.loads(fc.canonical_json(fc2.quantify(f)))
    out["MISSING_BASIS"] = json.loads(fc.canonical_json(fc2.quantify(
        finding([(0, 60, "0", "F1")], [foundation("F1", basis=())]))))
    f = finding([(0, 60, "20", "F1"), (60, 90, "0", "F1")], [foundation("F1", no_load=(), basis=())])
    out["NO_RATE"] = json.loads(fc.canonical_json(fc2.quantify(f)))
    assert fc2.quantify(f) == fc.quantify(f)
    return out


def _snapshot() -> dict:
    return {
        "quantify": _cases(),
        "PARAMETER_SHA256": fc2.PARAMETER_SHA256, "FORMULA_VERSION": fc2.FORMULA_VERSION,
        "words": {str(k): v for k, v in NO_LOAD_BASIS_WORDS.items()
                  if k in ("GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST", None)},
        "COST_IDLE": COST_IDLE.format(h="200 minutes", l="12.1", basis=NO_LOAD_BASIS_WORDS["GENERIC_DEFAULT"], r="3.3"),
    }


def test_existing_bases_are_byte_equal_to_main() -> None:
    assert json.loads(GOLDEN.read_text()) == json.loads(json.dumps(_snapshot()))


def test_one_vocabulary_for_every_reader() -> None:
    values = STATE_PROPERTY_VALUES["generator-no-load-fuel-rate-basis"]
    assert set(fc2.NO_LOAD_BASES) == set(values)
    assert set(NO_LOAD_BASIS_WORDS) - {None} == set(values)


def _fit_quantity(basis: str = "DATASHEET_FIT"):
    f = finding([(0, 60, "0", "F1"), (60, 90, "12", "F1")], [foundation("F1", no_load=(("0.62", "L/h"),), basis=(basis,))])
    return f, fc2.quantify(f)


def test_datasheet_fit_is_available_at_its_rate() -> None:
    _, q = _fit_quantity()
    assert fc2.is_v2(q) and q.state == "AVAILABLE"
    assert str(q.no_load_l_per_h) == "0.62" and q.no_load_basis == "DATASHEET_FIT"


def test_datasheet_fit_idle_words() -> None:
    text = COST_IDLE.format(h="60 minutes", l="0.7", basis=NO_LOAD_BASIS_WORDS["DATASHEET_FIT"], r="0.62")
    assert "datasheet-fitted idle fuel rate of 0.62 L/h, not measured" in text
    assert "no-load" not in text and "load" not in text.replace("loaded", "")


def test_unknown_basis_still_refuses() -> None:
    _, q = _fit_quantity("GUESSED")
    assert q.reason == "NO_LOAD_RATE_BASIS_MISSING"


if __name__ == "__main__":
    if "--write" in sys.argv:
        GOLDEN.write_text(json.dumps(_snapshot(), indent=1, sort_keys=True) + "\n")
