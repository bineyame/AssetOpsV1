"""6h (`specs/6h-named-option-levers/spec.md` §10.2 test 8; D-P6.67): byte-for-byte parity of what is meant to stay
unchanged (6c's difference and evaluation results, Kobo's `generator_stop_reserve` prepare) with the golden captured
from the slice's base commit before any 6h change. A difference is a fault in 6h, never a golden to refresh."""
from __future__ import annotations

import json

from capture_6h_parity import GOLDEN, collect, dump


# Q4 (packet): this one recorded case monkeypatches `difference` with a double that gives Deltas no origins while its
# changed leaf carries `demo-simulated`. D-P6.61's source class now unions the changed leaf's origins, so the double's
# row reads SIMULATED (golden: RECORDED). A real `difference` already carries them, so no real row differs. Only the
# `source_class` of this key is set aside; every other field is still compared. Accepted by D-P6.68.
DOUBLE_SOURCE_CLASS = {"test_6c_evaluate::test_4_a_node_with_no_value_is_named_by_its_own_missing_leaves"}


def _without_source_class(value):
    if isinstance(value, dict):
        return {k: (None if k == "source_class" else _without_source_class(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_without_source_class(v) for v in value]
    return value


def test_8_every_recorded_result_equals_the_base_commits_golden() -> None:
    golden = json.loads(GOLDEN.read_text())
    got = json.loads(dump(collect()))
    assert sorted(got) == sorted(golden)
    for key in sorted(golden):
        if key in DOUBLE_SOURCE_CLASS:
            got[key], golden[key] = _without_source_class(got[key]), _without_source_class(golden[key])
        assert json.dumps(got[key], sort_keys=True) == json.dumps(golden[key], sort_keys=True), key
