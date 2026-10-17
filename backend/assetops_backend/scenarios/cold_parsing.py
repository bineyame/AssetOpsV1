"""Strict parser for `cold-scenario/1` documents (W2-02, `D-2026-10-17-w2-02-buildspec`).

A separate document type from the legacy timeline `ScenarioDefinition`: `scenarios/parsing.py` and its
closed key sets accept none of these keys, and this parser accepts none of theirs. The closed object is
canonicalized (sorted keys, no whitespace, UTF-8) and hashed, so YAML comments and formatting do not change
the scenario digest.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from assetops_contracts.source_envelope_v3 import is_canonical_decimal

from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

COLD_SCENARIO_SCHEMA = "cold-scenario/1"
COLD_SITE_CODE = "COLD-LAB-001"
COLD_MODEL_PROFILE = "cold-thermal/1"
COLD_PUBLICATION_PROFILE = "cold-publication/1"
COLD_OBSERVATION_PROFILE = "cold-observation/1"

DOCUMENT_KEYS = (
    "schema", "scenario_id", "version", "site_code", "model_profile", "publication_profile",
    "observation_profile", "seed", "start", "end", "initial_temperature_deg_c", "ambient_deg_c",
    "backup_enabled", "forcings", "observations",
)
FORCING_KEYS = ("at", "kind", "asset", "value")
OBSERVATION_KEYS = ("at", "kind", "device_id", "action", "outcome", "release_at")

#: Forcing kind -> (the one asset it addresses, the one value it carries).
FORCING_KINDS = {
    "GRID_LOSS": ("grid-1", "LOST"),
    "GRID_RESTORE": ("grid-1", "AVAILABLE"),
    "GENERATOR_FAILURE": ("generator-1", "FAILED"),
    "DOOR_OPEN": ("door-1", "OPEN"),
    "DOOR_CLOSE": ("door-1", "CLOSED"),
}
#: Observation kind -> (the one device address it names, the actions it admits).
OBSERVATION_KINDS = {
    "PROBE_REPORT": ("probe-1", ("DROP", "HOLD")),
    "START_RESULT": ("generator-1", ("ADD",)),
}
ADD_OUTCOME = "SUCCEEDED"

_INSTANT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_SCENARIO_ID = re.compile(r"cold-[a-z][a-z0-9-]*")


@dataclass(frozen=True)
class ColdForcing:
    at: str
    kind: str
    asset: str
    value: str


@dataclass(frozen=True)
class ColdObservationFault:
    at: str
    kind: str
    device_id: str
    action: str
    outcome: str | None
    release_at: str | None


@dataclass(frozen=True)
class ColdScenarioDefinition:
    """One immutable `cold-scenario/1` document and its digest."""

    scenario_id: str
    version: int
    site_code: str
    model_profile: str
    publication_profile: str
    observation_profile: str
    seed: int
    start: str
    end: str
    initial_temperature_deg_c: str
    ambient_deg_c: str
    backup_enabled: bool
    forcings: tuple[ColdForcing, ...]
    observations: tuple[ColdObservationFault, ...]
    scenario_sha256: str
    schema: str = COLD_SCENARIO_SCHEMA
    source: str = ""
    origin: str = "SHIPPED"


def canonical_scenario_text(document: Any) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def scenario_digest(document: Any) -> str:
    return hashlib.sha256(canonical_scenario_text(document).encode("utf-8")).hexdigest()


def is_cold_document(document: Any) -> bool:
    return isinstance(document, dict) and document.get("schema") == COLD_SCENARIO_SCHEMA


def parse_cold_scenario_document(document: Any, *, source: str = "<in-memory>",
                                 origin: str = "SHIPPED") -> ColdScenarioDefinition:
    """The closed `cold-scenario/1` document, or `ScenarioConfigurationInvalid` naming the first problem."""

    def fail(message: str) -> ScenarioConfigurationInvalid:
        return ScenarioConfigurationInvalid(f"Cold scenario {source}: {message}")

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

    def exact(value: Any, wanted: Any, where: str) -> None:
        if type(value) is not type(wanted) or value != wanted:
            raise fail(f"{where} must be {wanted!r}")

    keys(document, DOCUMENT_KEYS, "document")
    exact(document["schema"], COLD_SCENARIO_SCHEMA, "schema")
    scenario_id = text(document["scenario_id"], "scenario_id")
    if not _SCENARIO_ID.fullmatch(scenario_id):
        raise fail("scenario_id must be cold-<case>")
    exact(document["version"], 1, "version")
    exact(document["site_code"], COLD_SITE_CODE, "site_code")
    exact(document["model_profile"], COLD_MODEL_PROFILE, "model_profile")
    exact(document["publication_profile"], COLD_PUBLICATION_PROFILE, "publication_profile")
    exact(document["observation_profile"], COLD_OBSERVATION_PROFILE, "observation_profile")
    if type(document["seed"]) is not int or document["seed"] < 0:
        raise fail("seed must be a non-negative integer")
    start = instant(document["start"], "start")
    end = instant(document["end"], "end")
    if not start < end:
        raise fail("start must precede end")
    for key in ("initial_temperature_deg_c", "ambient_deg_c"):
        if not is_canonical_decimal(text(document[key], key)):
            raise fail(f"{key} must be a canonical decimal string")
    if type(document["backup_enabled"]) is not bool:
        raise fail("backup_enabled must be a boolean")

    forcings: list[ColdForcing] = []
    if not isinstance(document["forcings"], list):
        raise fail("forcings must be a list")
    for index, row in enumerate(document["forcings"]):
        where = f"forcings[{index}]"
        keys(row, FORCING_KEYS, where)
        at = instant(row["at"], f"{where}.at")
        kind = text(row["kind"], f"{where}.kind")
        if kind not in FORCING_KINDS:
            raise fail(f"{where}.kind {kind!r} is not a cold forcing kind")
        asset, value = FORCING_KINDS[kind]
        if row["asset"] != asset:
            raise fail(f"{where}.asset {row['asset']!r} is unknown for {kind} (wanted {asset!r})")
        if row["value"] != value:
            raise fail(f"{where}.value {row['value']!r} does not pair with {kind} (wanted {value!r})")
        if not start <= at < end:
            raise fail(f"{where}.at {at} is outside [{start}, {end})")
        forcings.append(ColdForcing(at, kind, asset, value))
    order = [(f.at, f.kind, f.asset) for f in forcings]
    if order != sorted(order):
        raise fail("forcings are not sorted by (at, kind, asset)")
    if len(set(order)) != len(order):
        raise fail("forcings contain a duplicate row")

    observations: list[ColdObservationFault] = []
    if not isinstance(document["observations"], list):
        raise fail("observations must be a list")
    for index, row in enumerate(document["observations"]):
        where = f"observations[{index}]"
        keys(row, OBSERVATION_KEYS, where)
        at = instant(row["at"], f"{where}.at")
        kind = text(row["kind"], f"{where}.kind")
        if kind not in OBSERVATION_KINDS:
            raise fail(f"{where}.kind {kind!r} is not a cold observation kind")
        device, actions = OBSERVATION_KINDS[kind]
        if row["device_id"] != device:
            raise fail(f"{where}.device_id {row['device_id']!r} is unknown for {kind} (wanted {device!r})")
        action = text(row["action"], f"{where}.action")
        if action not in actions:
            raise fail(f"{where}.action {action!r} does not pair with {kind}")
        if action == "ADD":
            exact(row["outcome"], ADD_OUTCOME, f"{where}.outcome")
        elif row["outcome"] is not None:
            raise fail(f"{where}.outcome must be null except for ADD")
        release_at = row["release_at"]
        if action == "HOLD":
            release_at = instant(release_at, f"{where}.release_at")
            if not release_at > at:
                raise fail(f"{where}.release_at must follow at")
        elif release_at is not None:
            raise fail(f"{where}.release_at must be null except for HOLD")
        if not start <= at < end:
            raise fail(f"{where}.at {at} is outside [{start}, {end})")
        observations.append(ColdObservationFault(at, kind, device, action, row["outcome"], release_at))
    order2 = [(o.at, o.kind, o.device_id) for o in observations]
    if order2 != sorted(order2):
        raise fail("observations are not sorted by (at, kind, device_id)")
    if len(set(order2)) != len(order2):
        raise fail("observations contain a duplicate row")

    return ColdScenarioDefinition(
        scenario_id=scenario_id, version=1, site_code=COLD_SITE_CODE, model_profile=COLD_MODEL_PROFILE,
        publication_profile=COLD_PUBLICATION_PROFILE, observation_profile=COLD_OBSERVATION_PROFILE,
        seed=document["seed"], start=start, end=end,
        initial_temperature_deg_c=document["initial_temperature_deg_c"], ambient_deg_c=document["ambient_deg_c"],
        backup_enabled=document["backup_enabled"], forcings=tuple(forcings), observations=tuple(observations),
        scenario_sha256=scenario_digest(document), source=source, origin=origin,
    )
