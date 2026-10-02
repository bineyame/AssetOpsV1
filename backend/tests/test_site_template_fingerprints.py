"""Pinned content fingerprints for every shipped Site template (T025f).

`D-2026-10-01-run-binds-scenario-to-site`, Versioning: any content change to a
shipped template bumps its `template_version`. T025a and T025b broke that rule
by editing `kobo-mini-grid-60kw` in place at version 1, so two Sites with the
same lineage held different content. This guard makes the rule mechanical.

The digest is SHA-256 over the PARSED document (``yaml.safe_load``), dumped as
canonical JSON with sorted keys. Comments, key order and whitespace are not
content and do not move it; every key and value does.

Changed content at a pinned `(template_id, template_version)` fails and tells
the author to bump the version. A new version fails until its pin is added
here. Old pins may stay: a pin with no shipped document is not an error.

`kobo-mini-grid-60kw` version 1 is deliberately not pinned. It named two
different documents (before and after T025a/T025b), so no single digest is
true of it; version 2 is the first version that means one content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from content_fingerprint import content_fingerprint

from assetops_backend.sites.adapters.yaml_site_template_catalog import (
    SHIPPED_SITE_TEMPLATE_ROOT,
)

#: (template_id, template_version) -> SHA-256 of the canonical parsed document.
PINNED_TEMPLATE_FINGERPRINTS: dict[tuple[str, int], str] = {
    ("hybrid-mini-grid-100kw", 2): (
        "25f0659d0c441b9eff371a89f29b87d0f173a417b37a2a81648a20dc79dae8d7"
    ),
    ("kobo-mini-grid-60kw", 2): (
        "43ede0213293914efaaa14e48fa69f56ab4a07565b8a84e7f90d89f7aae786bf"
    ),
    # T026: the two capability signals and mappings
    # (`D-2026-10-02-template-bump-record`).
    ("kobo-mini-grid-60kw", 3): (
        "d5c404b64136292bac4578b276d7958ba68b838ee6f0f92873992c389938c4a8"
    ),
    ("twin-tank-mini-grid-150kw", 1): (
        "0c271c9fad0138dd38a5e9dc4e64329e2aadbd54a7e07f9997f588abc9577a93"
    ),
}


def template_fingerprint(document: Any) -> str:
    """SHA-256 over the canonical JSON form of a parsed template document.

    The shared `content_fingerprint`, which T025g's scenario guard uses too.
    """
    return content_fingerprint(document)


def fingerprint_failure(
    path_name: str,
    template_id: str,
    template_version: int,
    digest: str,
    pins: dict[tuple[str, int], str],
) -> str | None:
    """The failure message for one shipped document, or None when it holds."""
    pinned = pins.get((template_id, template_version))
    if pinned is None:
        return (
            f"{path_name}: shipped template {template_id!r} version "
            f"{template_version} has no pinned fingerprint. If this is a new "
            f"version, add ({template_id!r}, {template_version}): {digest!r} "
            "to PINNED_TEMPLATE_FINGERPRINTS."
        )
    if pinned != digest:
        return (
            f"{path_name}: shipped template {template_id!r} changed content at "
            f"unchanged template_version {template_version}. Bump "
            f"template_version (and source_version on what changed) and pin "
            f"the new version; Templates copy, so Sites already created from "
            f"version {template_version} keep the content they were given."
        )
    return None


def _shipped_documents() -> list[tuple[Path, dict[str, Any]]]:
    paths = sorted(SHIPPED_SITE_TEMPLATE_ROOT.glob("*.yaml"))
    return [
        (path, yaml.safe_load(path.read_text(encoding="utf-8"))) for path in paths
    ]


def test_every_shipped_template_matches_its_pinned_fingerprint() -> None:
    documents = _shipped_documents()
    assert documents, "the shipped template catalog ships no document"

    failures = [
        message
        for path, document in documents
        if (
            message := fingerprint_failure(
                path.name,
                document["template_id"],
                document["template_version"],
                template_fingerprint(document),
                PINNED_TEMPLATE_FINGERPRINTS,
            )
        )
        is not None
    ]

    assert not failures, "\n".join(failures)


def test_kobo_template_is_version_three_with_the_t025_additions_at_two() -> None:
    """T025f AC1: the T025a/T025b generator properties carry 2; the rest keep 1.

    T026 bumped the template to 3 for two signals and mappings, which carry no
    per-entity provenance; no property moved.
    """
    document = yaml.safe_load(
        (SHIPPED_SITE_TEMPLATE_ROOT / "kobo-mini-grid-60kw.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert document["template_version"] == 3
    signals = {
        (device["device_id"], signal["signal_id"])
        for device in document["foundation"]["devices"]
        for signal in device["signals"]
    }
    assert ("pv-inverter-controller", "available-power") in signals
    assert ("battery-pcs-controller", "discharge-capability") in signals

    added = {
        "start-soc-threshold",
        "stop-soc-threshold",
        "start-delay",
        "generator-rated-power",
    }
    versions: dict[str, int] = {}
    for component in document["foundation"]["components"]:
        for prop in component.get("properties") or []:
            versions[f"{prop['property_key']}@{component['component_id']}"] = prop[
                "source_version"
            ]
    for control in document["foundation"]["site_controls"]:
        versions[f"control:{control['control_key']}"] = control["source_version"]

    at_two = {key for key, version in versions.items() if version == 2}
    assert at_two == {f"{key}@generator" for key in added}
    assert set(versions.values()) == {1, 2}


class TestTheGuardCanFail:
    """The guard is only protection if it refuses the two violations."""

    PINS = {("example", 1): "a" * 64}

    def test_changed_content_at_an_unchanged_version_names_the_bump(
        self,
    ) -> None:
        message = fingerprint_failure("example.yaml", "example", 1, "b" * 64, self.PINS)
        assert message is not None
        assert "'example'" in message
        assert "changed content at unchanged template_version 1" in message
        assert "Bump template_version" in message

    def test_a_new_version_without_a_pin_asks_for_one(self) -> None:
        message = fingerprint_failure("example.yaml", "example", 2, "b" * 64, self.PINS)
        assert message is not None
        assert "has no pinned fingerprint" in message

    def test_the_pinned_content_passes(self) -> None:
        assert (
            fingerprint_failure("example.yaml", "example", 1, "a" * 64, self.PINS)
            is None
        )

    def test_a_comment_is_not_content_but_a_value_is(self) -> None:
        base = yaml.safe_load("template_id: x\ntemplate_version: 1\nvalue: 35\n")
        commented = yaml.safe_load(
            "# a note\ntemplate_id: x\ntemplate_version: 1\nvalue: 35  # why\n"
        )
        edited = yaml.safe_load("template_id: x\ntemplate_version: 1\nvalue: 36\n")
        assert template_fingerprint(base) == template_fingerprint(commented)
        assert template_fingerprint(base) != template_fingerprint(edited)


@pytest.mark.parametrize("template_id", ["kobo-mini-grid-60kw"])
def test_a_superseded_ambiguous_version_is_not_pinned(template_id: str) -> None:
    assert (template_id, 1) not in PINNED_TEMPLATE_FINGERPRINTS
