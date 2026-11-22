"""0K4a (spec §2.7, D-0K4.19): v8's profile words are SC-1 statements served through `served_text`.

No database. Every expected sentence is written here by hand (W2). W2's literal is the sha256 of every profile's
summary on `main` (`ec8e64d3f`, which carries 0K4b), computed before v8 existed: the seam passes a legacy `str`
unchanged, so every other profile serves byte-equal text.
"""
from __future__ import annotations

import hashlib
import json

from assetops_backend.runs.profiles import MINI_GRID_V8_MODEL, MODEL_PROFILES
from assetops_backend.simulator_lab_api import run_profile_summary

CYCLE_CHARGING = (
    "As the previous mini-grid version, except that the generator runs as a cycle charger: while it runs it carries "
    "the load and charges the battery, the battery helps only above what solar and the generator give, the generator "
    "is held at its minimum load by charging and then by curtailing solar, fuel follows its declared curve, and "
    "charging tapers near full."
)
FUEL_TANK_VOLUME_CURVE = (
    "The fuel in the tank, initialized by the scenario, moved by the generator's fuel curve while it starts or runs "
    "and by any frozen declared cause, such as a recorded operational action."
)
NEEDS = {
    "generator-no-load-fuel-rate": "Litres an hour the generator burns while starting or running at no output.",
    "generator-minimum-load": "Site policy: the least share of its rating a running generator is held at.",
    "battery-charge-taper-start": "The state of charge above which the battery accepts less than its charge limit.",
}
#: sha256 of `json.dumps([run_profile_summary(p) for p in MODEL_PROFILES], sort_keys=True, ensure_ascii=False)` on
#: `main` ec8e64d3f (11 profiles, before v8).
MAIN_SUMMARIES = "ede3a067032bea6e32168da0a4d529ae71fa8f471058a4d6d97504d086c3d712"


def test_w1_v8_serves_its_statements_as_text() -> None:
    summary = run_profile_summary(MINI_GRID_V8_MODEL)
    assert (summary["model_profile_id"], summary["model_profile_version"]) == ("mini-grid", 8)
    assert summary["statement"] == CYCLE_CHARGING
    states = {item["state_key"]: item["statement"] for item in summary["supported_states"]}
    assert states["fuel-tank-volume"] == FUEL_TANK_VOLUME_CURVE
    for key, sentence in NEEDS.items():
        assert states[key] == sentence, key
    assert all(isinstance(item["statement"], str) for item in summary["supported_states"])
    assert isinstance(summary["statement"], str)
    json.dumps(summary)  # served: plain JSON


def test_w2_every_other_profile_is_byte_equal_to_main() -> None:
    others = [p for p in MODEL_PROFILES if p is not MINI_GRID_V8_MODEL]
    assert len(others) == 11 and len(MODEL_PROFILES) == 12
    text = json.dumps([run_profile_summary(p) for p in others], sort_keys=True, ensure_ascii=False)
    assert hashlib.sha256(text.encode()).hexdigest() == MAIN_SUMMARIES
