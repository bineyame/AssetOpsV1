"""YAML reading and rendering for the run store.

Translation is this module's job as much as reading is. `OSError`,
`yaml.YAMLError` and `UnicodeDecodeError` are storage vocabulary and must not
escape: each is converted into the run port's error vocabulary before it
crosses the seam.

Documents are located by scanning and parsed before anything is keyed on them,
so a `run_id` never becomes a path. An identity that never touches the
filesystem cannot traverse it - the same rule the two Site stores hold.

## One loader, and it is libyaml's

Every run document is loaded here, with `yaml.load(text, Loader=CSafeLoader)`,
and nowhere else: the inventory, a single read, the fallback scan and the
write-time readback of a staged document all pass through `read_run_record`,
so they cannot disagree about whether the same bytes are a run. That is
`D-2026-09-29-run-store-libyaml`, and three consequences of it are deliberate:

1.  **The C extension is required, and its absence is an import failure.**
    `CSafeLoader` accepts and refuses some documents the pure-Python
    `SafeLoader` does not, so a silent fallback would let two installations
    answer the same store differently. There is no fallback: an installation
    without libyaml cannot import this module, and says why.
2.  **This is not lexical equivalence with the pure-Python loader.** The
    differences found so far are declared and pinned by
    `backend/tests/test_run_store_loader.py`: a literal tab after a colon and a
    tab inside a flow sequence are now accepted; the literal escapes
    `\\uD800` and `\\U00110000` are refused as invalid YAML; flow nesting
    deep enough to exhaust the pure-Python composer's recursion now reaches
    the run parser's own depth bound instead of escaping as `RecursionError`.
    One difference is recorded and NOT accepted: flow nesting a few thousand
    levels deep overflows the compiled parser's native stack and ends the
    process, where the baseline raised `RecursionError`. Whether to bound
    nesting before loading is an open Architect/owner decision (T022B review
    packet). What a run MEANS - its frozen values, identity,
    status and domain refusals - is decided by `parse_run_document`, which did
    not change.
3.  **Only the run store moved.** Site, scenario, execution-artifact and stage
    readers keep their own loaders.

Text is still decoded as UTF-8 before YAML sees it, so the change does not also
introduce a second input encoding, and documents are still written with
`safe_dump`.
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


class LibyamlUnavailable(ImportError):
    """PyYAML is installed without its libyaml C extension.

    An `ImportError` because that is what it is: the run store cannot be
    imported on this installation, which makes the missing extension an
    install-time failure rather than a behaviour discovered on the first read.
    """


try:
    from yaml import CSafeLoader
except ImportError as missing:
    raise LibyamlUnavailable(
        "The run store requires PyYAML's libyaml C extension "
        "(yaml.CSafeLoader), and the PyYAML "
        f"{getattr(yaml, '__version__', '(unknown version)')} installed at "
        f"{getattr(yaml, '__file__', '(unknown location)')} was built without "
        "it. Run documents are read only with libyaml "
        "(D-2026-09-29-run-store-libyaml): the pure-Python loader accepts and "
        "refuses different documents, so it is not a fallback. Reinstall "
        "PyYAML from a binary wheel that bundles libyaml, for example "
        "`python -m pip install --force-reinstall --only-binary=pyyaml "
        "pyyaml`, or build it against the libyaml headers, then check with "
        "`python tools/run-store-evidence.py runtime`."
    ) from missing


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
        document = yaml.load(text, Loader=CSafeLoader)
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
