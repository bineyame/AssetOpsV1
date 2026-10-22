"""Strict parser for `ev-scenario/1` documents (W2-05b, `D-2026-10-18-w2-05-buildspec`, Run 1 rulings Q1-Q7).

A separate document type from both the legacy timeline `ScenarioDefinition` and `cold-scenario/1`: neither of
those parsers accepts these keys, and this parser accepts none of theirs. The document has no `version` key;
its schema implies scenario version 1. The parsed strict object is canonicalized (sorted keys, no whitespace,
UTF-8) and hashed, so YAML comments and layout do not change the scenario digest.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from assetops_contracts.source_envelope_v3 import is_canonical_decimal

from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

EV_SCENARIO_SCHEMA = "ev-scenario/1"
#: `ev-scenario/1` implies scenario version 1 in the request, catalog and frozen binding (Q6).
EV_SCENARIO_VERSION = 1
EV_SITE_CODE = "EV-LAB-001"
EV_SEED = 20517
#: W3-02 c3b: the one admitted second (Site, seed) pairing, bound to exactly one scenario ID. Every other
#: valid EV scenario ID keeps the (EV_SITE_CODE, EV_SEED) pin.
EV_SECOND_SITE_SCENARIO_ID = "ev-complete-lab-002"
EV_SECOND_SITE_CODE = "EV-LAB-002"
EV_SECOND_SEED = 20518
EV_WINDOW = {"start": "2026-10-06T08:00:00Z", "end": "2026-10-06T09:00:00Z", "end_exclusive": True}
EV_MODEL_PROFILE = "ev-charger/1"
EV_PUBLICATION_PROFILE = "ev-publication/1"
EV_OBSERVATION_PROFILE = "ev-observation/1"
#: The declared per-connector rating of the EV-LAB-001 fixture, bounding REQUEST_KW (Q3).
EV_CONNECTOR_RATING_KW = Decimal("60")

DOCUMENT_KEYS = (
    "schema", "scenario_id", "site_code", "window", "seed", "model_profile", "publication_profile",
    "observation_profile", "forcing", "observations",
)
WINDOW_KEYS = ("start", "end", "end_exclusive")
PROFILE_KEYS = ("profile_id", "profile_version")
FORCING_KEYS = ("time", "kind", "connector", "value")
OBSERVATION_KEYS = ("time", "kind", "connector", "action", "release_at")

#: Connector rank (Q2): c1 before c2 at an equal time.
CONNECTOR_RANK = {"c1": 0, "c2": 1}
#: Forcing kind rank (Q2); governs both parser order and pack application.
FORCING_KIND_RANK = {"PLUG": 0, "AUTHORIZE": 1, "REQUEST_KW": 2, "FAULT": 3, "CLEAR": 4, "UNPLUG": 5}
PLUG_LABELS = ("session-1", "session-2")
AUTHORIZE_VALUES = ("ACCEPT", "DENY")
#: Forcing kinds explicitly outside `ev-scenario/1` (Q3): a document bearing either refuses before Draft.
EXCLUDED_FORCING_KINDS = ("GRID_LOSS", "GRID_RESTORE")
#: Observation kind rank and the actions each admits (Q4).
OBSERVATION_KIND_RANK = {"ENERGY_REPORT": 0, "EV_SESSION_END": 1}
OBSERVATION_ACTIONS = {"ENERGY_REPORT": ("DROP",), "EV_SESSION_END": ("HOLD", "ADD")}
ACTION_RANK = {"DROP": 0, "HOLD": 1, "ADD": 2}

_INSTANT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_SCENARIO_ID = re.compile(r"ev-[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


@dataclass(frozen=True)
class EvForcing:
    time: str
    kind: str
    connector: str
    value: str


@dataclass(frozen=True)
class EvObservation:
    time: str
    kind: str
    connector: str
    action: str
    release_at: str | None


@dataclass(frozen=True)
class EvScenarioDefinition:
    """One immutable `ev-scenario/1` document and its digests."""

    scenario_id: str
    site_code: str
    start: str
    end: str
    seed: int
    model_profile: str
    publication_profile: str
    observation_profile: str
    forcing: tuple[EvForcing, ...]
    observations: tuple[EvObservation, ...]
    scenario_sha256: str
    observation_sha256: str
    version: int = EV_SCENARIO_VERSION
    schema: str = EV_SCENARIO_SCHEMA
    source: str = ""
    origin: str = "SHIPPED"

    @property
    def window(self) -> dict[str, Any]:
        return {"start": self.start, "end": self.end, "end_exclusive": True}


def canonical_text(document: Any) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(document: Any) -> str:
    return hashlib.sha256(canonical_text(document).encode("utf-8")).hexdigest()


def ev_observation_sha256(observations: tuple[EvObservation, ...]) -> str:
    """Q7: SHA-256 of canonical JSON `["ev-observation/1", ordered rows]`, each row the five-key object
    including a null `release_at`."""
    rows = [
        {"time": o.time, "kind": o.kind, "connector": o.connector, "action": o.action,
         "release_at": o.release_at}
        for o in observations
    ]
    return _sha256([EV_OBSERVATION_PROFILE, rows])


def is_ev_document(document: Any) -> bool:
    return isinstance(document, dict) and document.get("schema") == EV_SCENARIO_SCHEMA


def parse_ev_scenario_document(document: Any, *, source: str = "<in-memory>",
                               origin: str = "SHIPPED") -> EvScenarioDefinition:
    """The closed `ev-scenario/1` document, or `ScenarioConfigurationInvalid` naming the first problem."""

    def fail(message: str) -> ScenarioConfigurationInvalid:
        return ScenarioConfigurationInvalid(f"EV scenario {source}: {message}")

    def keys(obj: Any, wanted: tuple[str, ...], where: str) -> None:
        if not isinstance(obj, dict):
            raise fail(f"{where} is not a mapping")
        if set(obj) != set(wanted):
            extra = sorted(set(obj) - set(wanted))
            missing = sorted(set(wanted) - set(obj))
            raise fail(f"{where} keys differ (extra {extra}, missing {missing})")

    def text(value: Any, where: str) -> str:
        if type(value) is not str:
            raise fail(f"{where} must be a string")
        return value

    def instant(value: Any, where: str) -> str:
        value = text(value, where)
        if not _INSTANT.fullmatch(value):
            raise fail(f"{where} must be a UTC instant YYYY-MM-DDTHH:MM:SSZ")
        return value

    def minute(value: Any, where: str) -> str:
        value = instant(value, where)
        if not value.endswith(":00Z"):
            raise fail(f"{where} must fall on a one-minute boundary")
        return value

    def exact(value: Any, wanted: Any, where: str) -> None:
        if type(value) is not type(wanted) or value != wanted:
            raise fail(f"{where} must be {wanted!r}")

    def profile(value: Any, wanted: str, where: str) -> str:
        keys(value, PROFILE_KEYS, where)
        profile_id, version = wanted.split("/")
        exact(value["profile_id"], profile_id, f"{where}.profile_id")
        exact(value["profile_version"], int(version), f"{where}.profile_version")
        return wanted

    keys(document, DOCUMENT_KEYS, "document")
    exact(document["schema"], EV_SCENARIO_SCHEMA, "schema")
    scenario_id = text(document["scenario_id"], "scenario_id")
    if not _SCENARIO_ID.fullmatch(scenario_id):
        raise fail("scenario_id must be ev-<case>")
    if scenario_id == EV_SECOND_SITE_SCENARIO_ID:
        site_code, seed = EV_SECOND_SITE_CODE, EV_SECOND_SEED
    else:
        site_code, seed = EV_SITE_CODE, EV_SEED
    exact(document["site_code"], site_code, "site_code")
    keys(document["window"], WINDOW_KEYS, "window")
    start = instant(document["window"]["start"], "window.start")
    end = instant(document["window"]["end"], "window.end")
    exact(document["window"]["end_exclusive"], True, "window.end_exclusive")
    exact(start, EV_WINDOW["start"], "window.start")
    exact(end, EV_WINDOW["end"], "window.end")
    exact(document["seed"], seed, "seed")
    model = profile(document["model_profile"], EV_MODEL_PROFILE, "model_profile")
    publication = profile(document["publication_profile"], EV_PUBLICATION_PROFILE, "publication_profile")
    observation = profile(document["observation_profile"], EV_OBSERVATION_PROFILE, "observation_profile")

    forcing: list[EvForcing] = []
    if not isinstance(document["forcing"], list):
        raise fail("forcing must be a list")
    plugs = 0
    for index, row in enumerate(document["forcing"]):
        where = f"forcing[{index}]"
        keys(row, FORCING_KEYS, where)
        time = minute(row["time"], f"{where}.time")
        kind = text(row["kind"], f"{where}.kind")
        if kind in EXCLUDED_FORCING_KINDS:
            raise fail(f"{where}.kind {kind!r} is outside {EV_SCENARIO_SCHEMA}")
        if kind not in FORCING_KIND_RANK:
            raise fail(f"{where}.kind {kind!r} is not an EV forcing kind")
        connector = text(row["connector"], f"{where}.connector")
        if connector not in CONNECTOR_RANK:
            raise fail(f"{where}.connector {connector!r} is not a declared connector of {EV_SITE_CODE}")
        value = text(row["value"], f"{where}.value")
        if kind == "PLUG":
            if plugs >= len(PLUG_LABELS):
                raise fail(f"{where} is a third PLUG; this fixture version admits {len(PLUG_LABELS)}")
            if value != PLUG_LABELS[plugs]:
                raise fail(f"{where}.value {value!r} breaks plug order (wanted {PLUG_LABELS[plugs]!r})")
            plugs += 1
        elif kind == "AUTHORIZE":
            if value not in AUTHORIZE_VALUES:
                raise fail(f"{where}.value {value!r} does not pair with AUTHORIZE")
        elif kind == "REQUEST_KW":
            if not is_canonical_decimal(value) or value.startswith("-"):
                raise fail(f"{where}.value must be a canonical non-negative decimal string")
            if Decimal(value) > EV_CONNECTOR_RATING_KW:
                raise fail(f"{where}.value {value} kW exceeds the {EV_CONNECTOR_RATING_KW} kW connector rating")
        else:
            wanted = {"FAULT": "LATCH", "CLEAR": "CLEAR", "UNPLUG": "END"}[kind]
            if value != wanted:
                raise fail(f"{where}.value {value!r} does not pair with {kind} (wanted {wanted!r})")
        if not start <= time < end:
            raise fail(f"{where}.time {time} is outside [{start}, {end})")
        forcing.append(EvForcing(time, kind, connector, value))
    order = [(f.time, CONNECTOR_RANK[f.connector], FORCING_KIND_RANK[f.kind]) for f in forcing]
    for index in range(1, len(order)):
        if order[index] == order[index - 1] or order[index] in order[:index]:
            raise fail(f"forcing[{index}] repeats (time, connector, kind)")
        if order[index] < order[index - 1]:
            raise fail(f"forcing[{index}] is out of (time, connector, kind) order")

    observations: list[EvObservation] = []
    if not isinstance(document["observations"], list):
        raise fail("observations must be a list")
    for index, row in enumerate(document["observations"]):
        where = f"observations[{index}]"
        keys(row, OBSERVATION_KEYS, where)
        time = minute(row["time"], f"{where}.time")
        kind = text(row["kind"], f"{where}.kind")
        if kind not in OBSERVATION_KIND_RANK:
            raise fail(f"{where}.kind {kind!r} is not an EV observation kind")
        connector = text(row["connector"], f"{where}.connector")
        if connector not in CONNECTOR_RANK:
            raise fail(f"{where}.connector {connector!r} is not a declared connector of {EV_SITE_CODE}")
        action = text(row["action"], f"{where}.action")
        if action not in OBSERVATION_ACTIONS[kind]:
            raise fail(f"{where}.action {action!r} does not pair with {kind}")
        release_at = row["release_at"]
        if action == "HOLD":
            release_at = instant(release_at, f"{where}.release_at")
            if not release_at > time:
                raise fail(f"{where}.release_at must follow time")
        elif release_at is not None:
            raise fail(f"{where}.release_at must be null except for HOLD")
        if not start <= time < end:
            raise fail(f"{where}.time {time} is outside [{start}, {end})")
        observations.append(EvObservation(time, kind, connector, action, release_at))
    targets = [(o.time, CONNECTOR_RANK[o.connector], OBSERVATION_KIND_RANK[o.kind]) for o in observations]
    ranks = [(*target, ACTION_RANK[o.action]) for target, o in zip(targets, observations)]
    for index in range(1, len(ranks)):
        if ranks[index] < ranks[index - 1]:
            raise fail(f"observations[{index}] is out of (time, connector, kind, action) order")
        if targets[index] in targets[:index]:
            raise fail(f"observations[{index}] changes a target an earlier row already changes")

    rows = tuple(observations)
    return EvScenarioDefinition(
        scenario_id=scenario_id, site_code=site_code, start=start, end=end, seed=seed,
        model_profile=model, publication_profile=publication, observation_profile=observation,
        forcing=tuple(forcing), observations=rows, scenario_sha256=_sha256(document),
        observation_sha256=ev_observation_sha256(rows), source=source, origin=origin,
    )
