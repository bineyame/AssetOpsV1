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
from assetops_backend.sites.adapters.import_files import (
    check_report_path,
    legacy_documents,
    read_binding_conversion,
    read_import_source,
    write_import_report,
)
from assetops_backend.sites.adapters.postgres_foundation_store import (
    PostgresFoundationStore,
)
from assetops_backend.sites.adapters.yaml_shipped_site_store import SHIPPED_SITE_ROOT
from assetops_backend.sites.adapters.yaml_user_site_store import USER_SITE_STORE_ROOT
from assetops_backend.sites.foundation_records import FoundationStore
from assetops_backend.sites.foundation_service import ImportSource, LegacyDocument
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


def build_foundation_store(database_url: str | None) -> FoundationStore:
    """The product Foundation store: PostgreSQL, the sole writer for imported Sites.

    A missing URL is not defaulted: the store answers as unavailable, so the
    product path fails closed instead of treating every Site as unimported.
    """
    return PostgresFoundationStore(database_url)


def legacy_site_documents() -> tuple[LegacyDocument, ...]:
    """Code, path and digest of every document the legacy YAML Site stores hold."""
    return legacy_documents((SHIPPED_SITE_ROOT, USER_SITE_STORE_ROOT))


def read_site_import_source(path: str) -> ImportSource:
    """One Site document read byte for byte and strictly parsed, for import."""
    return read_import_source(path)


def check_site_import_report_path(report: str, source: str) -> None:
    """Refuse a report path that is the source or inside a Site store."""
    check_report_path(report, source)


def write_site_import_report(path: str, report: str, *, source: str) -> str:
    """Write the import comparison report (review evidence, not configuration)."""
    return write_import_report(path, report, source_text=source)


def read_binding_conversion_fixture(path: str) -> tuple[dict, str, str]:
    """A binding conversion fixture read byte for byte (S1-02)."""
    return read_binding_conversion(path)
