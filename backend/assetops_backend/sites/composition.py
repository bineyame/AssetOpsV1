"""The single composition module for Site configuration storage.

This is the one place in the product allowed to import
`assetops_backend.sites.adapters.*`; `tools/check-architecture.ps1` fails the
build on an adapter import from anywhere else. Every other caller receives the
port by injection and cannot name a storage technology even by accident.

Swapping the store is therefore one new adapter module plus one line here.
"""

from __future__ import annotations

from assetops_backend.sites.adapters.composite_site_repository import (
    CompositeSiteRepository,
)
from assetops_backend.sites.adapters.yaml_shipped_site_store import (
    ReadOnlyYamlSiteStore,
)
from assetops_backend.sites.adapters.yaml_site_template_catalog import (
    YamlSiteTemplateCatalog,
)
from assetops_backend.sites.adapters.yaml_user_site_store import (
    WritableYamlSiteStore,
)
from assetops_backend.sites.ports import SiteRepository, SiteTemplateCatalog


def build_site_template_catalog() -> SiteTemplateCatalog:
    """Choose the adapter that serves shipped Site templates.

    Read-only by construction: the catalog port has no mutator, and this
    adapter has no write path to the shipped configuration root.
    """
    return YamlSiteTemplateCatalog()


def build_site_repository() -> SiteRepository:
    """Choose the adapters that serve and store Sites.

    Two stores, one identity space. The shipped store is read-only and ships
    empty; the writable user store is where every Site a user creates lands.
    The composite refuses an identity that resolves in both rather than
    picking one, so there is no overlay and no precedence to reason about
    anywhere above this line.

    Swapping file storage for anything else is one new adapter module plus
    this function, with no change to any caller.
    """
    return CompositeSiteRepository(
        shipped=ReadOnlyYamlSiteStore(),
        user=WritableYamlSiteStore(),
    )
