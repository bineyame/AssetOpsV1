"""Shared YAML reading for the two Site stores.

The shipped Site store and the writable user store hold the same document
family in the same format, so they read it through one function. That matters
beyond tidiness: if the two stores could disagree about what a document is,
the single-identity-space rule between them would be enforced over two
different readings of the same bytes.

Translation is this module's other job. `OSError`, `yaml.YAMLError`, and
`UnicodeDecodeError` are storage vocabulary and must not escape: each is
converted into the Site port's error vocabulary before it crosses the seam.

Documents are located by scanning and parsed before anything is keyed on them,
so a `site_id` never becomes a path. An identity that never touches the
filesystem cannot traverse it.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteStoreUnavailable,
)
from assetops_backend.sites.site_parsing import parse_site_document

#: A stored document larger than this is refused before it is loaded, so a
#: defective or hostile file cannot be expanded in memory first.
MAX_DOCUMENT_BYTES = 128 * 1024

#: Bound on how many documents one store may hold. An unbounded store makes
#: the Sites index unopenable rather than merely long.
MAX_DOCUMENTS = 500

DOCUMENT_SUFFIX = ".yaml"


def read_site_records(root: Path, *, store_name: str) -> tuple[SiteRecord, ...]:
    """Read and strictly validate every Site document under `root`.

    A missing root is an empty store rather than a failure: the shipped Site
    store ships empty and the user store does not exist until the first
    create, and neither is a reason to refuse to render the Sites index.

    Raises:
        SiteConfigurationInvalid: a stored document is invalid.
        SiteStoreUnavailable: the store could not be read.
    """
    records: list[SiteRecord] = []

    for path in document_paths(root, store_name=store_name):
        records.append(read_site_record(path, store_name=store_name))

    return tuple(records)


def document_paths(root: Path, *, store_name: str) -> list[Path]:
    """Return the document paths in one store, in a stable order."""
    try:
        if not root.is_dir():
            return []
        paths = sorted(
            path for path in root.iterdir() if path.suffix == DOCUMENT_SUFFIX
        )
    except OSError as error:
        raise SiteStoreUnavailable(
            f"The {store_name} site store could not be read: {root}"
        ) from error

    if len(paths) > MAX_DOCUMENTS:
        raise SiteConfigurationInvalid(
            f"The {store_name} site store holds {len(paths)} documents, above "
            f"the limit of {MAX_DOCUMENTS}"
        )

    return paths


def read_site_record(path: Path, *, store_name: str) -> SiteRecord:
    """Read and strictly validate one Site document."""
    try:
        size = path.stat().st_size
        if size > MAX_DOCUMENT_BYTES:
            raise SiteConfigurationInvalid(
                f"Site document {path.name} in the {store_name} store is "
                f"{size} bytes, above the limit of {MAX_DOCUMENT_BYTES}"
            )
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise SiteConfigurationInvalid(
            f"Site document {path.name} in the {store_name} store is not "
            "valid UTF-8"
        ) from error
    except OSError as error:
        raise SiteStoreUnavailable(
            f"Site document {path.name} in the {store_name} store could not "
            "be read"
        ) from error

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise SiteConfigurationInvalid(
            f"Site document {path.name} in the {store_name} store is not "
            "valid YAML"
        ) from error

    return parse_site_document(document, source=f"{store_name}:{path.name}")


def serialize_site_document(document: dict[str, object]) -> bytes:
    """Render a Site document mapping as the bytes a store holds."""
    return yaml.safe_dump(
        document, sort_keys=False, allow_unicode=True, default_flow_style=False
    ).encode("utf-8")
