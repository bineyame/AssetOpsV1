"""Shipped scenarios: pinned content per version, and no site named (T025g AC5).

`D-2026-10-01-run-binds-scenario-to-site`, Versioning: any content change to a
shipped scenario bumps its `scenario_version` (`supersedes` set, new valid-from).
The pin is the same mechanism as T025f's template guard
(`content_fingerprint`): changed content at a pinned
`(scenario_id, scenario_version)` fails and tells the author to bump the
version, and a new version fails until its pin is added here.

The rule itself: a scenario names no site. `target_site` is retired from
shipped documents (legacy acceptance is for documents the owner already holds,
never for what ships), so a shipped document carrying it fails.

Version 1 of each shipped scenario is not pinned: v2 is the first version this
guard governs, and v1 survives only in git and in persisted runs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from content_fingerprint import content_fingerprint

from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import (
    SHIPPED_SCENARIO_ROOT,
)

#: (scenario_id, scenario_version) -> SHA-256 of the canonical parsed document.
PINNED_SCENARIO_FINGERPRINTS: dict[tuple[str, int], str] = {
    # S3-01 phase 3 (review F5): the s3-dispatch-cases-v1 ordinary Necessary
    # interval fixture, a new id at version 1.
    ("kobo-s3-dispatch-necessary-run", 1): (
        "ad889dbe1fffb4b9736660bb61ec9d986a1a409992b1bdc5fa94c6407cc05f14"
    ),
    # S3-01 phase 1 (`D-2026-10-11-s3-dispatch-interval-assessment`): the
    # s3-dispatch-cases-v1 degraded-reporting fixture, a new id at version 1.
    ("kobo-s3-dispatch-degraded-reporting", 1): (
        "830c9c44134874cac4016a8a008be5c60fa617dcce47f1950e91562f42c8e75e"
    ),
    # S2-01c phase 3 (`D-2026-10-09-s2-publication-clock-post-run-release`):
    # a new scenario id, so the delayed-publication v1 above stays selectable.
    ("kobo-daytime-post-run-publication", 1): (
        "70cce87a57a623555821954fed2a089c5ef9768cec4862a6bd41d434df80adcb"
    ),
    # S2-01c (`D-2026-10-09-s2-simulated-publication-clock`).
    ("kobo-daytime-delayed-publication", 1): (
        "130e42fcdefdbaa70f38201e74254165f96a9cd04440e3c951f641d0bcabe9ad"
    ),
    # T026: a new scenario id at version 1, naming no site.
    ("kobo-mini-grid-degraded-evidence", 1): (
        "0fc92f6dda17664c17e6550dea1d5c4c881016333433d656b970e1f85e82e06e"
    ),
    ("fuel-loss-event", 2): (
        "37eb209e9edf796df7dc432d734cdd6e08ca6e058decca11807c226ccd0d6039"
    ),
    ("kobo-daytime", 2): (
        "477695f81914ee74c794b9ee893cca018fdf31ca5b8aab54effbfcff84ea2346"
    ),
    ("kobo-daytime-larger-mill", 2): (
        "f6d03d90acddf1fe8d6d94d15459c1cf1598bb60267f7bcb8e6b73b0ca38c139"
    ),
    ("kobo-daytime-overcast", 2): (
        "a224b9c13e4a3240eaa6036be5d6b509d5946ea28dea3be8f568d8509719a5fc"
    ),
    ("kobo-mini-grid-evening", 2): (
        "0b150abc996bcc50b2384e64fb74405312a70d5196dca0dfacd903cf41e77726"
    ),
    ("kobo-mini-grid-prolonged", 2): (
        "bd5ccc88f92d6305b334a0d5a34a3a437127b0ff03c4199292f39fafa5ae7b05"
    ),
    ("kobo-mini-grid-reserve-trial", 1): (
        "4e146c98622b3b6850fe8513984779d96b392028517ba9c4b4ba2f43a39bedb0"
    ),
    # SCN-kobo-reserve-matters
    ("kobo-mini-grid-reserve-matters", 1): (
        "515f0292c3c5046133223ce4aefd21db8a2b752c5f0e40c189116180c935aa0c"
    ),
    ("kobo-mini-grid-stop-60", 2): (
        "730b3e81bd4e5c3b1602fb62a3a45dff76668522d896ab37e5020c66f1866ebf"
    ),
    # E2 FR-A: the ten scenarios first shipped as version 1 by the DD-1a1 / DD-1a2 slices (merges eae5174b7 and
    # 1dd3b1862). Each file is unchanged since its slice: every commit that touches it is a DD-1a1 or DD-1a2 commit.
    # Introducing commit, per entry, is listed in FIRST_SHIPPED_AS_V1 below.
    ("kobo-mill-midday", 1): (
        "e1094acd9998d1d144e10072279902b7ef92720da0021056b8e50c7fb855f4a2"
    ),
    ("kobo-night-early-after-before-mill", 1): (
        "a78723d4287813a5c07ab800b3a86b6d655c072daae8e3dc4df247ba9441744c"
    ),
    ("kobo-night-early-from-0300", 1): (
        "916020ef35409f0c2aaf0c93254902a941008dfeb2f9ef19983a28f30089c555"
    ),
    ("kobo-night-early-until-0255", 1): (
        "98b1206c33011b93a1eccb0dcd4fe689af85037243e8fdb698abd7571cd7b58c"
    ),
    ("kobo-night-early-until-0300", 1): (
        "7da4a7f56a73af9bf1b77574de607e7f7dbea80d7571fc204ed8c33beeb0f730"
    ),
    ("kobo-night-early", 1): (
        "9bddb9a056d3a19c4baa1faad0c14288d153f8e3195449f29b1d634a6ae3940f"
    ),
    ("kobo-rest-before-mill", 1): (
        "1e4ce10c7defe4e23a209e66d9a9fe53130468d06df1087410571ce642bebc2e"
    ),
    ("kobo-rest-mill", 1): (
        "42d180e1ba99cac3c84494359e61990180c97f7697f54e2467b2dd33a1ddf9c5"
    ),
    ("kobo-steady-before-mill", 1): (
        "f39bee89b4882ea9278b73a67e24cbb39cb07a76b1753377902e99f6ae094462"
    ),
    ("kobo-steady-day", 1): (
        "5b5ee65a488285867f8d5f422a3bd0281337ec3c5f8e5deb52e898df7fd23feb"
    ),
}

#: E2 FR-A: scenarios first shipped as version 1 after the T025g v2 bump, by the DD-1a1 and DD-1a2 slices. The rule
#: "every other shipped scenario is v2 superseding v1" stays strict for the original 14. The value is the commit that
#: introduced the file (`git log --diff-filter=A -- config/scenarios/<id>.yaml`).
FIRST_SHIPPED_AS_V1: dict[str, str] = {
    "kobo-mill-midday": "9c0a3f510",  # DD-1a1 R4
    "kobo-night-early-after-before-mill": "5a5211639",  # DD-1a2
    "kobo-night-early-from-0300": "97e91b8f1",  # DD1a1-R7a
    "kobo-night-early-until-0255": "a02f72ff3",  # DD1a1-R7b
    "kobo-night-early-until-0300": "97e91b8f1",  # DD1a1-R7a
    "kobo-night-early": "870e33119",  # DD-1a1 (DD1a1-R2)
    "kobo-rest-before-mill": "5a5211639",  # DD-1a2
    "kobo-rest-mill": "8b68aaa14",  # DD1a1-R16
    "kobo-steady-before-mill": "5a5211639",  # DD-1a2
    "kobo-steady-day": "17e69a295",  # DD-1a1 (partial)
}

#: Keys that would name a site, or choose sites by lineage, in a shipped
#: scenario. `target_site` is the retired one; a template hint was ruled out by
#: the same decision ("No template hint").
SITE_NAMING_KEYS = ("target_site", "site_id", "template_id")


def shipped_documents() -> list[tuple[Path, dict[str, Any]]]:
    """Every shipped legacy timeline document.

    W2-02: `schema: cold-scenario/1` documents are a separate strict type with their own digest
    (`test_w202_cold_scenario.py`); they carry no legacy version/fingerprint pin. W2-05b: neither do
    `schema: ev-scenario/1` documents (`test_w205b_ev_scenarios.py`).
    """
    paths = sorted(SHIPPED_SCENARIO_ROOT.glob("*.yaml"))
    documents = [
        (path, yaml.safe_load(path.read_text(encoding="utf-8"))) for path in paths
    ]
    return [(path, doc) for path, doc in documents if doc.get("schema") not in ("cold-scenario/1", "ev-scenario/1")]


def fingerprint_failure(
    path_name: str,
    scenario_id: str,
    scenario_version: int,
    digest: str,
    pins: dict[tuple[str, int], str],
) -> str | None:
    """The failure message for one shipped document, or None when it holds."""
    pinned = pins.get((scenario_id, scenario_version))
    if pinned is None:
        return (
            f"{path_name}: shipped scenario {scenario_id!r} version "
            f"{scenario_version} has no pinned fingerprint. If this is a new "
            f"version, add ({scenario_id!r}, {scenario_version}): {digest!r} "
            "to PINNED_SCENARIO_FINGERPRINTS."
        )
    if pinned != digest:
        return (
            f"{path_name}: shipped scenario {scenario_id!r} changed content at "
            f"unchanged scenario_version {scenario_version}. Bump "
            "scenario_version, set supersedes and a new version_valid_from, and "
            "pin the new version: runs reference scenario versions, so an "
            "in-place edit changes what an existing version means."
        )
    return None


def site_naming_failure(path_name: str, document: dict[str, Any]) -> str | None:
    """A shipped scenario that names a site at its top level, or None."""
    named = [key for key in SITE_NAMING_KEYS if key in document]
    if not named:
        return None
    return (
        f"{path_name}: a shipped scenario names no site "
        f"(D-2026-10-01-run-binds-scenario-to-site), but this one carries "
        f"{named}. The site is chosen at run setup; describe what a site must "
        "honour in site_contract.description instead."
    )


def test_the_shipped_scenarios_were_found() -> None:
    documents = shipped_documents()
    # The original 14 plus the ten first shipped as v1 by DD-1a1 / DD-1a2 (FIRST_SHIPPED_AS_V1).
    assert len(documents) == 14 + len(FIRST_SHIPPED_AS_V1), [path.name for path, _ in documents]


def test_every_shipped_scenario_matches_its_pinned_fingerprint() -> None:
    failures = [
        message
        for path, document in shipped_documents()
        if (
            message := fingerprint_failure(
                path.name,
                document["scenario_id"],
                document["version"]["scenario_version"],
                content_fingerprint(document),
                PINNED_SCENARIO_FINGERPRINTS,
            )
        )
        is not None
    ]
    assert not failures, "\n".join(failures)


def test_no_shipped_scenario_names_a_site() -> None:
    failures = [
        message
        for path, document in shipped_documents()
        if (message := site_naming_failure(path.name, document)) is not None
    ]
    assert not failures, "\n".join(failures)


#: T026: scenarios first shipped after the T025g v2 bump start at version 1.
#: S2-01c: the delayed-publication fixture for the registered virtual clock.
#: S2-01c phase 3: the post-run release fixture.
NEW_SINCE_T025G = {
    "kobo-mini-grid-degraded-evidence",
    "kobo-daytime-delayed-publication",
    "kobo-daytime-post-run-publication",
    "kobo-s3-dispatch-degraded-reporting",
    "kobo-s3-dispatch-necessary-run",
    "kobo-mini-grid-reserve-trial",  # S6-02b
    "kobo-mini-grid-reserve-matters",  # SCN-kobo-reserve-matters
}


def test_every_shipped_scenario_is_v2_superseding_v1() -> None:
    for path, document in shipped_documents():
        version = document["version"]
        if document["scenario_id"] in NEW_SINCE_T025G or document["scenario_id"] in FIRST_SHIPPED_AS_V1:
            assert version["scenario_version"] == 1, path.name
            assert "supersedes" not in version, path.name
            continue
        assert version["scenario_version"] == 2, path.name
        assert version["supersedes"] == 1, path.name
        assert version["version_valid_from"] == "2026-10-01T00:00:00Z", path.name


def test_the_site_naming_guard_fails_on_a_legacy_declaration() -> None:
    """Non-vacuous: the guard trips on the exact shape v1 shipped."""
    document = {
        "scenario_id": "x",
        "target_site": {
            "policy": "DECLARED_SITE",
            "site_id": "KOBO-001",
            "template_id": None,
            "requirement": "r",
        },
    }
    assert site_naming_failure("x.yaml", document) is not None
    assert site_naming_failure("x.yaml", {"scenario_id": "x"}) is None


def test_the_fingerprint_guard_fails_on_an_in_place_edit() -> None:
    """Non-vacuous: one changed word at an unchanged version fails."""
    path, document = shipped_documents()[0]
    document = dict(document)
    document["purpose"] = document["purpose"] + " Edited in place."
    message = fingerprint_failure(
        path.name,
        document["scenario_id"],
        document["version"]["scenario_version"],
        content_fingerprint(document),
        PINNED_SCENARIO_FINGERPRINTS,
    )
    assert message is not None and "changed content" in message
