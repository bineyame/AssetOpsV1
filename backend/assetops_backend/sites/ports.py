"""Configuration persistence ports owned by the product domain.

The port is the seam that makes storage replaceable. Its signatures and its
errors speak domain records only: no `Path`, no file handle, no YAML text, no
loader `dict`, and no store-specific exception may cross it. An adapter that
lets `yaml.YAMLError` or `OSError` escape has not implemented the port, and a
service layer that catches either has already lost the seam.

`SiteTemplateCatalog` is a read-only catalog of shipped templates. It is not a
subclass, mode, flag, or parameterization of a Site repository, and no
`SiteRepository` exists yet: creating a Site is a later slice.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from assetops_backend.sites.models import SiteTemplate


class SiteTemplateCatalogError(Exception):
    """Base class for the port's error vocabulary."""


class SiteTemplateNotFound(SiteTemplateCatalogError):
    """No template with the requested `template_id` is in the catalog."""


class SiteTemplateConfigurationInvalid(SiteTemplateCatalogError):
    """A template document exists but is not valid configuration.

    Raised by the strict parser and by adapters that meet undecodable or
    unparseable stored content. The message names the offending field or
    document so a shipped-catalog defect is diagnosable without reading the
    store.
    """


class SiteTemplateStoreUnavailable(SiteTemplateCatalogError):
    """The catalog itself could not be read.

    Distinct from `SiteTemplateConfigurationInvalid`: the content was never
    reached, so nothing is known about whether it is valid.
    """


@runtime_checkable
class SiteTemplateCatalog(Protocol):
    """Read-only access to shipped Site configuration templates.

    Read-only is structural, not a convention: there is no create, update,
    delete, upload, or import method, so no caller can write through this port
    and no adapter has a write path to implement.
    """

    def list_templates(self) -> Sequence[SiteTemplate]:
        """Return every shipped template.

        Raises:
            SiteTemplateConfigurationInvalid: a shipped document is invalid.
            SiteTemplateStoreUnavailable: the catalog could not be read.
        """
        ...

    def get_template(self, template_id: str) -> SiteTemplate:
        """Return one shipped template by its template identity.

        Raises:
            SiteTemplateNotFound: no such `template_id`.
            SiteTemplateConfigurationInvalid: a shipped document is invalid.
            SiteTemplateStoreUnavailable: the catalog could not be read.
        """
        ...
