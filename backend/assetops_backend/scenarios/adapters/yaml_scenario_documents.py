"""Shared YAML reading for the two scenario stores.

The shipped scenario store and the user store hold the same document family in
the same format, so they read it through one function. That matters beyond
tidiness: if the two stores could disagree about what a document is, the
single-identity-space rule between them would be enforced over two different
readings of the same bytes.

Translation is this module's other job. `OSError`, `yaml.YAMLError`, and
`UnicodeDecodeError` are storage vocabulary and must not escape: each is
converted into the scenario port's error vocabulary before it crosses the seam.

Documents are located by scanning and parsed before anything is keyed on them,
so a `scenario_id` never becomes a path. An identity that never touches the
filesystem cannot traverse it, and the identity a record carries is the one its
document declares rather than the one its file name happens to spell.

A duplicate identity *within* one store is detected here, because only this
layer can see two files. The composite detects one across stores.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from assetops_backend.scenarios.identity import scenario_id_key
from assetops_backend.scenarios.models import ScenarioDefinition
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import (
    ScenarioConfigurationInvalid,
    ScenarioIdentityConflict,
    ScenarioStoreUnavailable,
)

#: A stored document larger than this is refused before it is loaded, so a
#: defective or hostile file cannot be expanded in memory first.
MAX_DOCUMENT_BYTES = 256 * 1024

#: Bound on how many documents one store may hold. An unbounded store makes the
#: scenario catalog unopenable rather than merely long.
MAX_DOCUMENTS = 500

DOCUMENT_SUFFIX = ".yaml"


def read_scenario_records(
    root: Path, *, store_name: str, origin: str
) -> tuple[ScenarioDefinition, ...]:
    """Read and strictly validate every scenario document under `root`.

    A missing root is an empty store rather than a failure: the user scenario
    store does not exist until somebody puts a document in it, and that is not
    a reason to refuse to render the catalog.

    Raises:
        ScenarioConfigurationInvalid: a stored document is invalid.
        ScenarioIdentityConflict: two documents in this store declare the same
            identity, including as a case variant.
        ScenarioStoreUnavailable: the store could not be read.
    """
    records: list[ScenarioDefinition] = []
    seen: dict[str, str] = {}

    for path in _document_paths(root, store_name=store_name):
        record = read_scenario_record(path, store_name=store_name, origin=origin)

        key = scenario_id_key(record.scenario_id)
        previous = seen.get(key)
        if previous is not None:
            raise ScenarioIdentityConflict(
                f"Scenario ID {record.scenario_id!r} is declared twice in the "
                f"{store_name} scenario store, in {previous} and "
                f"{path.name}. Scenario identity is globally unique and is "
                "compared without regard to case, so neither document is used."
            )
        seen[key] = path.name

        records.append(record)

    return tuple(records)


def read_scenario_record(
    path: Path, *, store_name: str, origin: str
) -> ScenarioDefinition:
    """Read and strictly validate one scenario document."""
    try:
        size = path.stat().st_size
        if size > MAX_DOCUMENT_BYTES:
            raise ScenarioConfigurationInvalid(
                f"Scenario document {path.name} in the {store_name} store is "
                f"{size} bytes, above the limit of {MAX_DOCUMENT_BYTES}"
            )
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ScenarioConfigurationInvalid(
            f"Scenario document {path.name} in the {store_name} store is not "
            "valid UTF-8"
        ) from error
    except OSError as error:
        raise ScenarioStoreUnavailable(
            f"Scenario document {path.name} in the {store_name} store could "
            "not be read"
        ) from error

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ScenarioConfigurationInvalid(
            f"Scenario document {path.name} in the {store_name} store is not "
            "valid YAML"
        ) from error

    return parse_scenario_document(
        document, source=f"{store_name}:{path.name}", origin=origin
    )


def _document_paths(root: Path, *, store_name: str) -> list[Path]:
    """Return the document paths in one store, in a stable order."""
    try:
        if not root.is_dir():
            return []
        paths = sorted(
            path for path in root.iterdir() if path.suffix == DOCUMENT_SUFFIX
        )
    except OSError as error:
        raise ScenarioStoreUnavailable(
            f"The {store_name} scenario store could not be read: {root}"
        ) from error

    if len(paths) > MAX_DOCUMENTS:
        raise ScenarioConfigurationInvalid(
            f"The {store_name} scenario store holds {len(paths)} documents, "
            f"above the limit of {MAX_DOCUMENTS}"
        )

    return paths
