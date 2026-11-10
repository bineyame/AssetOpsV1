"""DIESEL-1 K1 (ruling DIESEL-1-R3c §9c.1) L0: the Kisiwa Site's shipped files, vocabulary and registration flow.

No database. Byte comparisons are made on the files as git stores them: a Windows checkout with
`core.autocrlf=true` writes CRLF for every one of these text files alike, so CRLF is normalised to LF before
comparing (the repository blobs are LF).
"""

from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
for extra in (REPO / "tools", REPO / "host", REPO / "host" / "tests"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from assetops_backend.sites.binding_roles import roles_for  # noqa: E402
from assetops_backend.sites.demo_configuration import FIXTURE_KEYS  # noqa: E402
from assetops_backend.sites.foundation_service import binding_set_at, revision_at  # noqa: E402
from assetops_backend.sites.models import COMPONENT_PROPERTY_DEFINITIONS  # noqa: E402
from assetops_backend.sites.ports import SiteConfigurationInvalid  # noqa: E402
from assetops_backend.sites.site_parsing import parse_site_document, render_site_document  # noqa: E402
from assetops_backend.sites.composition import build_site_template_catalog  # noqa: E402

TEMPLATE = REPO / "config" / "site-templates" / "kisiwa-diesel-hybrid-60kw.yaml"
DRAFT_TEMPLATE = REPO / ".agent" / "DIESEL-D0" / "kisiwa-diesel-hybrid-60kw.draft.yaml"
BINDINGS = REPO / "backend" / "conversions" / "kisiwa-001-bindings.json"
DRAFT_BINDINGS = REPO / ".agent" / "DIESEL-F0" / "kisiwa-001-bindings.draft.json"
SITE_SOURCE = REPO / "backend" / "tests" / "fixtures" / "s1" / "kisiwa-001.yaml"
ROLES4 = REPO / "backend" / "conversions" / "kisiwa-001-minigrid-roles-demo-config.json"
VERIFICATION_V3 = REPO / "backend" / "conversions" / "d-verification-window-v3.json"

IMPORT_AT = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)
INSTALL_AT = datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc)
READ_AT = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
KNOWN_AT = datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _after_template_id(data: bytes) -> bytes:
    return data[data.index(b"template_id:"):]


# ---- 1-3: the shipped template, the promoted bindings, the import record ------------------------------------------

def test_the_shipped_template_parses_and_equals_the_draft() -> None:
    template = build_site_template_catalog().get_template("kisiwa-diesel-hybrid-60kw")
    assert template.template_version == 1
    assert yaml.safe_load(lf_bytes(TEMPLATE)) == yaml.safe_load(lf_bytes(DRAFT_TEMPLATE))
    assert _after_template_id(lf_bytes(TEMPLATE)) == _after_template_id(lf_bytes(DRAFT_TEMPLATE))


def test_the_bindings_are_the_f0r_draft_byte_for_byte() -> None:
    assert lf_bytes(BINDINGS) == lf_bytes(DRAFT_BINDINGS)
    doc = json.loads(BINDINGS.read_text(encoding="utf-8"))
    assert (len(doc["bindings"]), doc["role_set"], doc["declare_signals"]) == (12, "minigrid-roles-2", [])


def test_the_import_record_is_the_render_of_the_shipped_template() -> None:
    from fixtures import site_from_template

    site = site_from_template(TEMPLATE, site_id="KISIWA-001", display_name="Kisiwa island mini-grid",
                              timezone="Africa/Dar_es_Salaam")
    document = copy.deepcopy(render_site_document(site))
    document["foundation"]["valid_from"] = "2026-09-01T00:00:00Z"
    record = parse_site_document(document, source="the Kisiwa import record")
    rendered = yaml.safe_dump(render_site_document(record), sort_keys=True).encode("utf-8")
    assert lf_bytes(SITE_SOURCE) == rendered


# ---- 4: the roles-4 demo configuration ------------------------------------------------------------------------

def test_the_roles4_configuration() -> None:
    doc = json.loads(ROLES4.read_text(encoding="utf-8"))
    assert set(doc) == FIXTURE_KEYS
    assert doc["status"].startswith("SIMULATED DEMO CONFIGURATION")
    assert doc["site_code"] == "KISIWA-001"
    assert doc["bindings"]["role_set"] == "minigrid-roles-4"
    vocabulary = roles_for("minigrid-roles-4")
    assert all(item["role"] in vocabulary for item in doc["bindings"]["add"])
    assert doc["component_properties"]["asset_code"] == "fuel-tank"


def test_the_roles4_configuration_copy_names_no_kobo_load() -> None:
    doc = json.loads(ROLES4.read_text(encoding="utf-8"))
    copies = [doc["component_properties"]["note"], doc["bindings"]["note"]]
    copies += [d["display_name"] for d in doc["bindings"]["declare_signals"]]
    for text in copies:
        for word in ("Clinic", "clinic ", "mill", "Mill", "Kobo"):
            assert word not in text, (word, text)
    lowered = " ".join(copies).lower()
    for word in ("theft", "stolen", "stole", "siphon", "pilfer"):
        assert word not in lowered


# ---- 5: the sensor-accuracy vocabulary ------------------------------------------------------------------------

KISIWA = yaml.safe_load(SITE_SOURCE.read_text(encoding="utf-8"))


def _with(component_id: str, key: str, value, unit: str | None = None) -> dict:
    doc = copy.deepcopy(KISIWA)
    for component in doc["foundation"]["components"]:
        if component["component_id"] == component_id:
            component["properties"] = list(component.get("properties") or []) + [{
                "property_key": key, "value": value, "unit": unit or COMPONENT_PROPERTY_DEFINITIONS[key].unit,
                "source": "SITE", "source_version": 1}]
    return doc


def _props(doc: dict) -> dict:
    site = parse_site_document(doc, source="test document")
    return {(c.component_id, p.property_key): (p.value, p.unit) for c in site.foundation.components
            for p in (c.properties or ())}


class TestSensorAccuracyVocabulary:
    def test_ten_litres_is_accepted_on_the_tank(self) -> None:
        assert _props(_with("fuel-tank", "fuel-level-sensor-accuracy", 10))[
            ("fuel-tank", "fuel-level-sensor-accuracy")] == (10, "L")

    @pytest.mark.parametrize(("key", "value"), [("fuel-level-sensor-accuracy", 10),
                                                ("fuel-level-sensor-accuracy-basis", "GENERIC_DEFAULT")])
    def test_carrier_is_the_fuel_tank(self, key, value) -> None:
        with pytest.raises(SiteConfigurationInvalid, match=f"{key} belongs on a FUEL_TANK"):
            _props(_with("generator", key, value))

    def test_zero_litres_is_refused(self) -> None:
        with pytest.raises(SiteConfigurationInvalid):
            _props(_with("fuel-tank", "fuel-level-sensor-accuracy", 0))

    def test_accuracy_in_another_unit_is_refused(self) -> None:
        with pytest.raises(SiteConfigurationInvalid):
            _props(_with("fuel-tank", "fuel-level-sensor-accuracy", 10, unit="L/h"))

    @pytest.mark.parametrize("value", ["GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_CALIBRATION"])
    def test_each_basis_state_is_accepted(self, value) -> None:
        assert _props(_with("fuel-tank", "fuel-level-sensor-accuracy-basis", value))[
            ("fuel-tank", "fuel-level-sensor-accuracy-basis")] == (value, "state")

    @pytest.mark.parametrize("value", ["SITE_TEST", "generic_default", ""])
    def test_basis_outside_the_state_set_is_refused(self, value) -> None:
        with pytest.raises(SiteConfigurationInvalid):
            _props(_with("fuel-tank", "fuel-level-sensor-accuracy-basis", value))


# ---- 6: the registration flow on the in-memory store ----------------------------------------------------------

def facts(store, tenant_id, site_id, at: datetime, knowledge_at: datetime) -> dict:
    """Declared properties per component and the binding set, at `at` as known at `knowledge_at`."""
    tenant_id, site_id = UUID(str(tenant_id)), UUID(str(site_id))
    revision = revision_at(store.revisions(tenant_id, site_id), at, knowledge_at)
    selected = binding_set_at(store.binding_sets(tenant_id, site_id), at, knowledge_at)
    props = {c["component_id"]: {p["property_key"]: p["value"] for p in (c.get("properties") or ())}
             for c in revision.content["components"]}
    return {"props": props, "role_set": selected.role_set, "bindings": len(selected.bindings)}


TEMPLATE_GENERATOR_PROPERTIES = {"specific-fuel-consumption", "minimum-runtime", "start-soc-threshold",
                                 "stop-soc-threshold", "start-delay", "generator-rated-power"}


def assert_registered_facts(found: dict) -> None:
    props = found["props"]
    assert props["fuel-tank"]["fuel-level-sensor-accuracy"] == 10
    assert props["fuel-tank"]["fuel-level-sensor-accuracy-basis"] == "GENERIC_DEFAULT"
    assert props["generator"]["generator-no-load-fuel-rate"] == 4.9
    assert props["generator"]["generator-no-load-fuel-rate-basis"] == "GENERIC_DEFAULT"
    assert TEMPLATE_GENERATOR_PROPERTIES <= set(props["generator"])
    assert {code: props[code].get("supply-use") for code in ("load-clinic", "load-res", "load-mill")} == {
        "load-clinic": "ESSENTIAL_SERVICE", "load-res": "HOUSEHOLD", "load-mill": "HOUSEHOLD"}
    assert (found["role_set"], found["bindings"]) == ("minigrid-roles-4", 15)


def test_register_in_on_the_in_memory_store() -> None:
    from foundation_fakes import InMemoryFoundationStore
    import demo_combined_kisiwa as kis

    store = InMemoryFoundationStore()
    result = kis.register_in(store, IMPORT_AT, INSTALL_AT)
    assert result["periods"][-1]["role_set"] == "minigrid-roles-4"
    assert result["recorded_at"] == "2026-09-29T10:00:00Z"
    assert_registered_facts(facts(store, result["tenant_id"], result["site_id"], READ_AT, KNOWN_AT))


# ---- 7: the model pin -----------------------------------------------------------------------------------------

def test_the_model_pin_is_executable_and_kobo_stays_on_v6() -> None:
    from execution_adapter import EXECUTABLE_MODELS
    from assetops_backend.runs.profiles import MODEL_PROFILES
    import demo_combined_kisiwa as kis

    pin = (kis.RUN_PROFILE["model_profile"]["profile_id"], kis.RUN_PROFILE["model_profile"]["profile_version"])
    assert pin == ("mini-grid", 7)
    assert pin in {(m.model_profile_id, m.model_profile_version) for m in EXECUTABLE_MODELS}
    assert pin in {(m.model_profile_id, m.model_profile_version) for m in MODEL_PROFILES}
    v3 = json.loads(VERIFICATION_V3.read_text(encoding="utf-8"))
    assert '"profile_id": "mini-grid"' in json.dumps(v3) and v3_model(v3) == ("mini-grid", 6)


def v3_model(document) -> tuple[str, int]:
    pending = [document]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if value.get("profile_id") == "mini-grid":
                return value["profile_id"], value["profile_version"]
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    raise AssertionError("no mini-grid pin in the v3 manifest")


# ---- DATA-1 (D-E5.30): one Kisiwa recording session ------------------------------------------------------------------

def test_data1_every_night_publish_gets_one_epoch_and_one_gateway_dir(tmp_path: Path) -> None:
    """D-E5.30: both publish paths (the story `build` and `add-day`'s `_publish_night`) go through `publish_night`,
    never `_publish_and_accept` directly; every night it calls gets one epoch and the one `work/kisiwa-gateway`."""
    import inspect
    from types import SimpleNamespace

    import demo_combined_kisiwa as kis

    for fn in (kis.build, kis._publish_night):
        source = inspect.getsource(fn)
        assert "publish_night(rp, " in source and "_publish_and_accept" not in source, fn.__name__
    calls: list[tuple] = []
    rp = SimpleNamespace(_publish_and_accept=lambda tmp, run, epoch, received, *, gateway_dir=None, keep=None:
                         calls.append((tmp, epoch, gateway_dir)) or {})
    received = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    for k in range(1, 11):  # the story's ten nights, then two added ones
        kis.publish_night(rp, tmp_path / "kisiwa-replay" / f"r{k:02d}", tmp_path, object(), received)
    for ymd in ("20261107", "20261108"):
        kis.publish_night(rp, tmp_path / "kisiwa-replay" / f"add-{ymd}", tmp_path, object(), received)
    assert {(epoch, gw) for _, epoch, gw in calls} == {("kisiwa-gw-1", tmp_path / "kisiwa-gateway")}, calls[:2]
    assert len({tmp for tmp, _, _ in calls}) == 12
