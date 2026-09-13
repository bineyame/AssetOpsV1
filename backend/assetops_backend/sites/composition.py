"""The single composition module for Site configuration storage.

This is the one place in the product allowed to import
`assetops_backend.sites.adapters.*`; `tools/check-architecture.ps1` fails the
build on an adapter import from anywhere else. Every other caller receives the
port by injection and cannot name a storage technology even by accident.

Swapping the store is therefore one new adapter module plus one line here.
"""

from __future__ import annotations

from assetops_backend.sites.adapters.yaml_site_template_catalog import (
    YamlSiteTemplateCatalog,
)
from assetops_backend.sites.ports import SiteTemplateCatalog


def build_site_template_catalog() -> SiteTemplateCatalog:
    """Choose the adapter that serves shipped Site templates.

    Read-only by construction: the catalog port has no mutator, and this
    adapter has no write path to the shipped configuration root.
    """
    return YamlSiteTemplateCatalog()
