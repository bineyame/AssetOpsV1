"""6h (`specs/6h-named-option-levers/spec.md` §10.2 test 8; D-P6.67): byte-for-byte parity of what is meant to stay
unchanged (6c's difference and evaluation results, Kobo's `generator_stop_reserve` prepare) with the golden captured
from the slice's base commit before any 6h change. A difference is a fault in 6h, never a golden to refresh."""
from __future__ import annotations

import json

from capture_6h_parity import GOLDEN, collect, dump


def test_8_every_recorded_result_equals_the_base_commits_golden() -> None:
    golden = json.loads(GOLDEN.read_text())
    got = json.loads(dump(collect()))
    assert sorted(got) == sorted(golden)
    for key in sorted(golden):
        assert json.dumps(got[key], sort_keys=True) == json.dumps(golden[key], sort_keys=True), key
    assert dump(got) == GOLDEN.read_text()
