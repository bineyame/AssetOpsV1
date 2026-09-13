"""Read-only YAML adapter over the shipped Site store.

The shipped Site store is git-tracked configuration that is read-only at
runtime. This module reads it and does nothing else: it has no write, create,
rename, delete, or temporary-file path, and `tools/check-architecture.ps1`
fails the build if a write-capable call appears in any module that names a
shipped configuration root.

M1 ships zero Sites, so this store is empty on a clean checkout and the Sites
index therefore renders its genuine first-run empty state. The store is not
therefore pointless: it is the other half of the one globally unique `site_id`
space, and the disjointness rule between the two stores is enforced against it
rather than against a fixture Site standing in the product's index.
"""

from __future__ import annotations

from pathlib import Path

from assetops_backend.sites.adapters.yaml_site_documents import read_site_records
from assetops_backend.sites.models import SiteRecord

REPO_ROOT = Path(__file__).resolve().parents[4]

#: The shipped, read-only Site configuration root. Separate from the writable
#: user store and from the template catalog: shipped configuration never lives
#: inside a directory anything writes to.
SHIPPED_SITE_ROOT = REPO_ROOT / "config" / "sites"

STORE_NAME = "shipped"


class ReadOnlyYamlSiteStore:
    """The shipped half of the Site identity space.

    Read-only is structural rather than a convention: there is no method here
    that writes, so no caller can write through it and no adapter has a write
    path to implement.
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = SHIPPED_SITE_ROOT if root is None else root

    @property
    def store_name(self) -> str:
        return STORE_NAME

    def list_sites(self) -> tuple[SiteRecord, ...]:
        return read_site_records(self._root, store_name=STORE_NAME)
