"""C1 RM-2 (D-E5.34): `findings_lenses_supported` is declared by the Site's configuration, never by Finding rows."""
from types import SimpleNamespace

from assetops_backend.sites_api import findings_lenses_supported


def _prop(key: str, value: object) -> SimpleNamespace:
    return SimpleNamespace(property_key=key, value=value)


def _component(kind: str, props: list | None) -> SimpleNamespace:
    return SimpleNamespace(component_type=kind, properties=props)


def _site(site_type: str, components: list) -> SimpleNamespace:
    return SimpleNamespace(site_type=site_type, foundation=SimpleNamespace(components=components))


def test_minigrid_with_a_declared_productive_load_supports_the_lenses() -> None:
    mill = _component("LOAD", [_prop("supply-use", "PRODUCTIVE")])
    assert findings_lenses_supported(_site("MINIGRID", [_component("GENERATOR", None), mill])) is True


def test_minigrid_without_a_productive_load_does_not() -> None:
    homes = _component("LOAD", [_prop("supply-use", "HOUSEHOLD")])
    assert findings_lenses_supported(_site("MINIGRID", [homes, _component("LOAD", None)])) is False


def test_cold_and_ev_sites_never_do() -> None:
    mill = _component("LOAD", [_prop("supply-use", "PRODUCTIVE")])
    assert findings_lenses_supported(_site("COLDCHAIN", [mill])) is False
    assert findings_lenses_supported(_site("EV_CHARGING", [mill])) is False
