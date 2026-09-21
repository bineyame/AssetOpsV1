"""YAML reading and rendering for the run store.

Translation is this module's job as much as reading is. `OSError`,
`yaml.YAMLError` and `UnicodeDecodeError` are storage vocabulary and must not
escape: each is converted into the run port's error vocabulary before it
crosses the seam.

Documents are located by scanning and parsed before anything is keyed on them,
so a `run_id` never becomes a path. An identity that never touches the
filesystem cannot traverse it - the same rule the two Site stores hold.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.parsing import parse_run_document
from assetops_backend.runs.ports import (
    RunConfigurationInvalid,
    RunStoreUnavailable,
)

#: A stored run larger than this is refused before it is loaded, so a
#: defective or hostile file cannot be expanded in memory first.
MAX_DOCUMENT_BYTES = 256 * 1024

#: Bound on how many runs one store may hold. Drafts are cheap to create and
#: overlapping ones are deliberately allowed, so the store is the one place
#: that can say enough.
MAX_DOCUMENTS = 2_000

DOCUMENT_SUFFIX = ".yaml"


def document_paths(root: Path) -> list[Path]:
    """The run document paths in the store, in a stable order."""
    try:
        if not root.is_dir():
            return []
        paths = sorted(
            path for path in root.iterdir() if path.suffix == DOCUMENT_SUFFIX
        )
    except OSError as error:
        raise RunStoreUnavailable(
            f"The run store could not be read: {root}"
        ) from error

    if len(paths) > MAX_DOCUMENTS:
        raise RunConfigurationInvalid(
            f"The run store holds {len(paths)} documents, above the limit of "
            f"{MAX_DOCUMENTS}"
        )

    return paths


def read_run_records(root: Path) -> tuple[SimulationRun, ...]:
    """Read and strictly validate every run document under `root`.

    A missing root is an empty store rather than a failure: no run has been
    set up yet, and that is not a reason to refuse to answer.
    """
    return tuple(read_run_record(path) for path in document_paths(root))


def read_run_record(path: Path) -> SimulationRun:
    """Read and strictly validate one run document."""
    try:
        size = path.stat().st_size
        if size > MAX_DOCUMENT_BYTES:
            raise RunConfigurationInvalid(
                f"Run document {path.name} is {size} bytes, above the limit "
                f"of {MAX_DOCUMENT_BYTES}"
            )
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise RunConfigurationInvalid(
            f"Run document {path.name} is not valid UTF-8"
        ) from error
    except OSError as error:
        raise RunStoreUnavailable(
            f"Run document {path.name} could not be read"
        ) from error

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise RunConfigurationInvalid(
            f"Run document {path.name} is not valid YAML"
        ) from error

    return parse_run_document(document, source=f"run store:{path.name}")


def serialize_run_document(document: dict[str, object]) -> bytes:
    """Render a run document mapping as the bytes the store holds."""
    return yaml.safe_dump(
        document, sort_keys=False, allow_unicode=True, default_flow_style=False
    ).encode("utf-8")
